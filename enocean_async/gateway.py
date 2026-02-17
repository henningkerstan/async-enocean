import asyncio
from dataclasses import dataclass
import logging
import time
from typing import Callable, Optional

import serial_asyncio_fast as serial_asyncio

from .eep.db import EEP_DATABASE
from .eep.handler import EEPHandler
from .eep.id import EEPID
from .eep.message import EEPMessage
from .erp1.address import EURID, BaseAddress, SenderAddress
from .erp1.telegram import RORG, ERP1Telegram
from .erp1.ute import (
    EEPTeachInResponseMessageExpectation,
    UTEMessage,
    UTEQueryRequestType,
    UTEResponseType,
)
from .esp3.common_command import CommonCommandTelegram
from .esp3.packet import ESP3Packet, ESP3PacketType
from .esp3.protocol import EnOceanSerialProtocol3
from .esp3.response import ResponseCode, ResponseTelegram
from .version.id import VersionIdentifier
from .version.info import VersionInfo

type RSSI = int


@dataclass
class SendResult:
    response: Optional[ResponseTelegram]
    duration_ms: Optional[float]


# callback types
type ESP3Callback = Callable[[ESP3Packet], None]
type ERP1Callback = Callable[[ERP1Telegram], None]
type EEPMessageCallback = Callable[[EEPMessage], None]
type UTECallback = Callable[[UTEMessage], None]
type ResponseCallback = Callable[[ResponseTelegram], None]
type NewDeviceCallback = Callable[[SenderAddress], None]
type ParsingFailedCallback = Callable[[str], None]


@dataclass
class CallbackWithFilter:
    callback: Callable
    sender_filter: SenderAddress | None = None


@dataclass
class ERP1CallbackWithFilter(CallbackWithFilter):
    callback: ERP1Callback


@dataclass
class EEPCallbackWithFilter(CallbackWithFilter):
    callback: EEPMessageCallback


class BaseIDChangeError(Exception):
    pass


class Gateway:
    """EnOcean gateway that connects to a serial port and processes incoming ESP3 packets."""

    def __init__(self, port: str, baudrate: int = 57600):
        """Create an instance of an EnOcean gateway that connects to the supplied port at supplied baudrate (optional) and processes incoming ESP3 packets."""

        # serial connection, transport and protocol parameters
        self.__port: str = port
        self.__baudrate: int = baudrate
        self.__transport: serial_asyncio.SerialTransport | None = None
        self.__protocol: EnOceanSerialProtocol3 | None = None

        # cached information about the connected module (to avoid unnecessary requests for information that doesn't change)
        self.__version_info: VersionInfo | None = None
        self.__base_id_remaining_write_cycles: int | None = None
        self.__base_id: BaseAddress | None = None

        # device and EEP management
        self.__known_devices: dict[EURID | BaseAddress, EEPID] = {}
        self.__detected_devices: list[EURID | BaseAddress] = []
        self.__eep_handlers: dict[EEPID, EEPHandler] = {}

        # callbacks
        self.__esp3_receive_callbacks: list[ESP3Callback] = []
        self.__erp1_receive_callbacks: list[ERP1CallbackWithFilter] = []
        self.__ute_receive_callbacks: list[UTECallback] = []
        self.__eep_receive_callbacks: list[EEPCallbackWithFilter] = []
        self.__parsing_failed_callbacks: list[ParsingFailedCallback] = []
        self.response_callbacks: list[ResponseCallback] = []

        self.__new_device_callbacks: list[NewDeviceCallback] = []

        self.__esp3_send_callbacks: list[ESP3Callback] = []

        # send handling
        self.__send_lock: asyncio.Lock = asyncio.Lock()
        self.__send_future: asyncio.Future | None = None

        # learning
        self.__is_learning: bool = False
        self.__learning_timeout_task: asyncio.Task | None = None
        self.__allow_teach_out: bool = False

        # logging
        self._logger = logging.getLogger(__name__)

        self._logger.info(
            f"Gateway initialized for port {self.__port} at baudrate {self.__baudrate}"
        )

    # ------------------------------------------------------------------
    # callback registration
    # ------------------------------------------------------------------
    def add_esp3_received_callback(self, cb: ESP3Callback):
        """Add a callback that will be called for every received ESP3 packet.

        This is a low-level callback that will be called for every ESP3 packet as they are received from the serial port, before any parsing or processing. This can be useful for debugging or for implementing custom processing of ESP3 packets that is not covered by the built-in functionality of the Gateway class."""
        self.__esp3_receive_callbacks.append(cb)

    def add_esp3_send_callback(self, cb: ESP3Callback):
        """Add a callback that will be called for every ESP3 packet that is sent to the EnOcean module.

        This can be useful for debugging or for implementing custom logging of sent packets."""
        self.__esp3_send_callbacks.append(cb)

    def add_new_device_callback(self, cb: NewDeviceCallback):
        """Add a callback that will be called for every newly detected sender address (EURID or Base ID) from incoming ERP1 telegrams.

        This can be useful for implementing custom handling of new devices."""
        self.__new_device_callbacks.append(cb)

    def add_erp1_received_callback(
        self, cb: ERP1Callback, sender_filter: SenderAddress | None = None
    ):
        """Add a callback that will be called for every received ERP1 telegram. If sender_filter is provided, the callback will only be called for telegrams that have a sender address matching the filter.

        This is a semi-high-level callback that will be called for every received ERP1 telegram after parsing and basic processing, but before any EEP-specific decoding. This can be useful for handling ERP1 telegrams in a custom way, for example by implementing custom decoding for specific RORGs or by handling telegrams from unknown devices."""
        self.__erp1_receive_callbacks.append(ERP1CallbackWithFilter(cb, sender_filter))

    def add_eep_message_received_callback(
        self, cb: EEPMessageCallback, sender_filter: SenderAddress | None = None
    ):
        """Add a callback that will be called for every received ERP1 telegram that could successfully be decoded as an EEP message. If sender_filter is provided, the callback will only be called for messages that have a sender address matching the filter.

        This is a high-level callback that will be called for every received EEP message after parsing, basic processing, and EEP-specific decoding. Prerequisite for this callback to be called for a message are:
        - the sender address of the message is known (by adding it to this gateway as known-device along with its EEPID), and
        - there is an EEPHandler capable of handling the EEPID of the sender device."""
        self.__eep_receive_callbacks.append(EEPCallbackWithFilter(cb, sender_filter))

    def add_ute_received_callback(self, cb: UTECallback):
        self.__ute_receive_callbacks.append(cb)

    def add_parsing_failed_callback(self, cb: ParsingFailedCallback):
        self.__parsing_failed_callbacks.append(cb)

    # ------------------------------------------------------------------
    # start and stop
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Open the serial connection to the EnOcean module and start processing incoming packets."""
        loop = asyncio.get_running_loop()
        try:
            (
                self.__transport,
                self.__protocol,
            ) = await serial_asyncio.create_serial_connection(
                loop,
                lambda: EnOceanSerialProtocol3(self),
                self.__port,
                baudrate=self.__baudrate,
            )

            self._logger.info(
                f"Successfully connected to EnOcean module on {self.__port} at baudrate {self.__baudrate}"
            )
        except Exception as e:
            self._logger.error(
                f"Failed to connect to EnOcean module on {self.__port} at baudrate {self.__baudrate}: {e}"
            )
            raise ConnectionError(
                f"Failed to connect to EnOcean module on {self.__port}: {e}"
            )

    def stop(self) -> None:
        """Close the serial connection to the EnOcean module."""
        if self.__transport is not None:
            self.__transport.close()
            self.__transport = None
            self._logger.info(
                f"Serial connection to EnOcean module on {self.__port} closed"
            )

    def start_learning(
        self, timeout_seconds: int = 60, allow_teach_out: bool = False
    ) -> None:
        """Start learning mode."""
        self.__is_learning = True
        self.__allow_teach_out = allow_teach_out

        self._logger.info(
            f"Learning mode started. Will automatically stop after {timeout_seconds} seconds."
        )
        if self.__learning_timeout_task is not None:
            self.__learning_timeout_task.cancel()
        self.__learning_timeout_task = asyncio.create_task(
            self.__learning_timeout(timeout_seconds)
        )

    def stop_learning(self) -> None:
        """Stop learning mode."""
        self.__is_learning = False
        self._logger.info("Learning mode stopped.")
        if self.__learning_timeout_task is not None:
            self.__learning_timeout_task.cancel()
            self.__learning_timeout_task = None

    async def __learning_timeout(self, timeout_seconds: int):
        try:
            await asyncio.sleep(timeout_seconds)
            if self.__is_learning:
                self.stop_learning()
        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------
    # sending commands and receiving responses
    # ------------------------------------------------------------------
    async def send_esp3_packet(self, packet: ESP3Packet) -> SendResult:
        """Send an ESP3 packet to the EnOcean module and wait up to 500ms for a response (as per ESP3 specification).

        This method is thread-safe and can be called from multiple coroutines concurrently; the send operations will be serialized using an internal lock, and each call will wait for its corresponding response before allowing the next send operation to proceed. The method returns a SendResult object containing the received response (if any) and the duration in milliseconds between sending the request and receiving the response.
        """

        async with self.__send_lock:
            self.__send_future = asyncio.get_running_loop().create_future()

            try:
                # emit to the send callbacks; we do this before sending the packet (WHY?)
                self.__emit(self.__esp3_send_callbacks, packet)
                self._logger.debug(
                    f"Sending ESP3 packet: {packet}. Waiting for response..."
                )

                # start a timer before sending the packet, so that we can measure the time it takes to receive the response after sending the packet
                start = time.perf_counter()

                # send the frame
                self.__transport.write(packet.to_bytes())
                response: ResponseTelegram | None = await asyncio.wait_for(
                    self.__send_future, timeout=0.5
                )

                # stop the timer and calculate duration
                end = time.perf_counter()

                self._logger.debug(
                    f"Received response to sent packet: {response}. Duration: {(end - start) * 1000:.2f} ms"
                )

                return SendResult(response, (end - start) * 1000)

            finally:
                self.__send_future = None

    def connection_made(self) -> None:
        pass

    def connection_lost(self, exc: Exception | None) -> None:
        self.__transport = None

    # ------------------------------------------------------------------
    # device registry
    # ------------------------------------------------------------------
    def add_device(self, address: EURID | BaseAddress, eepid: EEPID) -> None:
        """Register a device with its sender address (EURID or Base ID) and its EEPID.

        This allows the gateway to recognize incoming messages from this device and decode them according to the registered EEP (if a handler for that EEP is found).
        """
        self.__known_devices[address] = eepid
        self._logger.info(f"Added device with address {address} and EEPID {eepid}")

        # get the EEP handler for this EEPID
        if not eepid in self.__eep_handlers:
            # try to load
            if eepid not in EEP_DATABASE:
                self._logger.warning(
                    f"EEP {eepid} is not supported. Messages from device {address} will not be decoded."
                )
                return
            else:
                self.__eep_handlers[eepid] = EEPHandler(EEP_DATABASE[eepid])
                self._logger.info(f"Loaded EEP handler for EEPID {eepid}")
        else:
            self._logger.debug(f"EEP handler for EEPID {eepid} already loaded.")

    def remove_device(self, address: EURID | BaseAddress) -> None:
        """Deregister a device by its sender address (EURID or Base ID). This removes the device from the registry of known devices, so that incoming messages from this address will no longer be recognized as coming from a known device and will not be decoded as EEP messages."""
        if address in self.__known_devices:
            del self.__known_devices[address]
            self._logger.info(f"Removed device with address {address}")
        else:
            self._logger.warning(
                f"Tried to remove device with address {address}, but it was not found in the registry of known devices."
            )

    # ------------------------------------------------------------------
    # Gateway properties and methods
    # ------------------------------------------------------------------
    @property
    async def base_id(self) -> BaseAddress | None:
        """Get the base ID of the connected EnOcean module."""
        if self.__base_id is not None:
            return self.__base_id

        if self.__transport is None:
            raise ConnectionError("Not connected to EnOcean module")

        # Send GET ID base id request
        cmd = CommonCommandTelegram.CO_RD_IDBASE()
        result: SendResult = await self.send_esp3_packet(cmd.to_esp3_packet())
        response = result.response

        if (
            response is None
            or response.return_code != ResponseCode.OK
            or len(response.response_data) < 4
        ):
            return None

        self.__base_id = BaseAddress.from_bytelist(response.response_data[:4])

        if len(response.optional_data) >= 1:
            self.__base_id_remaining_write_cycles = response.optional_data[0]

        return self.__base_id

    async def change_base_id(
        self, new_base_id: BaseAddress, safety_flag: int = 0
    ) -> BaseAddress | None:
        """Change the base ID of the connected EnOcean module. Returns True if successful, False otherwise.

        To prevent accidental changes, this function requires a safety flag to be provided. The safety_flag must be set to 0x7B, otherwise the function will return False without sending the command."""

        if safety_flag != 0x7B:
            raise ValueError(
                "Invalid safety flag. To change the base ID, you must provide a safety flag of 0x7B to confirm that you understand the consequences of this action."
            )

        if self.__transport is None:
            raise ConnectionError("Not connected to EnOcean module")

        base_id_before_change = (
            await self.base_id
        )  # store previous base ID for error message in case the change failed

        if new_base_id == base_id_before_change:
            raise ValueError("New base ID is the same as the current base ID")

        # send WR ID base id request
        cmd = CommonCommandTelegram.CO_WR_IDBASE(new_base_id)
        send_result = await self.send_esp3_packet(cmd.to_esp3_packet())
        response = send_result.response

        # check response for errors; if we got a response, but it indicates an error, we can be pretty sure that the base ID change failed, so we can raise an exception with the error message
        if response is not None and response.return_code != ResponseCode.OK:
            match response.return_code:
                case ResponseCode.NOT_SUPPORTED:
                    raise BaseIDChangeError(
                        "Base ID change is not supported by this module"
                    )
                case ResponseCode.BASEID_OUT_OF_RANGE:
                    raise BaseIDChangeError(
                        "Base ID change failed: provided base ID is out of allowed range (must be in range FF:80:00:00 to FF:FF:FF:80)"
                    )
                case ResponseCode.BASEID_MAX_REACHED:
                    raise BaseIDChangeError(
                        "Base ID change failed: maximum number of allowed base ID changes has been reached"
                    )
                case _:
                    raise BaseIDChangeError(
                        f"Base ID change failed with error code: {response.return_code.name} ({response.return_code.value})"
                    )

        # now either we got a successful response, or no response at all (timeout). In both cases, we should check if the base ID was actually changed by reading it again, because the module might have accepted the command but failed to send a response.
        self.__base_id = None  # reset cached base ID to force re-fetching it
        self.__base_id_remaining_write_cycles = (
            None  # reset cached remaining write cycles as well
        )
        reported_base_id = await self.base_id
        if reported_base_id == new_base_id:
            return reported_base_id
        elif reported_base_id == base_id_before_change:
            raise BaseIDChangeError(
                "Base ID change failed: after sending the command, the base ID of the module is still the same as before"
            )
        else:
            raise BaseIDChangeError(
                f"Base ID change failed: after sending the command, the module reports a different base ID ({reported_base_id}) than the one we tried to set ({new_base_id}) and the one that was set before ({base_id_before_change}), which is very unexpected and likely indicates a communication error or a bug in the module's firmware."
            )

    @property
    async def version_info(self) -> VersionInfo | None:
        """Get the version information of the connected EnOcean module."""
        if self.__version_info is not None:
            return self.__version_info

        if self.__transport is None:
            raise ConnectionError("Not connected to EnOcean module")

        # Send GET VERSION request
        cmd = CommonCommandTelegram.CO_RD_VERSION()
        send_result = await self.send_esp3_packet(cmd.to_esp3_packet())
        response = send_result.response

        if (
            response is None
            or response.return_code != ResponseCode.OK
            or len(response.response_data) < 32
        ):
            return None

        self.__version_info = VersionInfo(
            app_version=VersionIdentifier(
                main=response.response_data[0],
                beta=response.response_data[1],
                alpha=response.response_data[2],
                build=response.response_data[3],
            ),
            api_version=VersionIdentifier(
                main=response.response_data[4],
                beta=response.response_data[5],
                alpha=response.response_data[6],
                build=response.response_data[7],
            ),
            eurid=EURID.from_bytelist(response.response_data[8:12]),
            device_version=response.response_data[12],
            app_description=response.response_data[16:32]
            .decode("ascii")
            .rstrip("\x00"),
        )

        return self.__version_info

    @property
    async def base_id_remaining_write_cycles(self) -> int | None:
        """Get the remaining write cycles for the base ID of the connected EnOcean module."""
        if self.__base_id_remaining_write_cycles is not None:
            return self.__base_id_remaining_write_cycles

        await (
            self.base_id
        )  # base_id() will fetch the remaining write cycles as optional data
        return self.__base_id_remaining_write_cycles

    @property
    async def eurid(self) -> EURID | None:
        """Get the EURID of the connected EnOcean module."""
        return (await self.version_info).eurid

    # ------------------------------------------------------------------
    # Internal packet processing
    # ------------------------------------------------------------------
    def process_esp3_packet(self, packet: ESP3Packet):
        """Process a received ESP3 packet. This includes emitting the raw packet to registered callbacks and further processing based on packet type."""
        self.__emit(self.__esp3_receive_callbacks, packet)

        self._logger.debug(f"Received ESP3 packet: {packet}")

        # handle packet based on type; currently we only process RESPONSE and RADIO_ERP1 packets, other types are ignored
        if packet.packet_type == ESP3PacketType.RESPONSE:
            response: ResponseTelegram
            try:
                response = ResponseTelegram.from_esp3_packet(packet)
            except Exception as e:
                return
            self.__process_response(response)
            return

        if packet.packet_type != ESP3PacketType.RADIO_ERP1:
            return

        # parse to ERP1 telegram; if parsing fails, ignore the packet and return
        erp1: ERP1Telegram
        try:
            erp1 = ERP1Telegram.from_esp3(packet)
        except Exception as e:
            return

        self.__process_erp1_telegram(erp1)

    def __emit(self, callbacks: list[Callable], obj):
        """Emit an object to all registered callbacks of the given type."""
        loop = asyncio.get_running_loop()
        for cb in callbacks:
            loop.call_soon(cb, obj)

    def __emit_with_sender_filter(
        self, callbacks: list[CallbackWithFilter], sender: SenderAddress, obj
    ):
        """Emit an object to all registered callbacks of the given type that have a sender filter matching the sender address."""
        loop = asyncio.get_running_loop()
        for cb in callbacks:
            if cb.sender_filter is None or cb.sender_filter == sender:
                loop.call_soon(cb.callback, obj)

    def __is_sender_known(self, sender: SenderAddress) -> bool:
        """Check if the sender address is known (i.e. if we have an EEP ID for it)."""
        return (
            sender in self.__known_devices.keys() or sender in self.__detected_devices
        )

    def __process_response(self, response: ResponseTelegram):
        """Process a received RESPONSE packet. If we are currently awaiting a response, try to parse it and store it for the send() method to retrieve."""
        self.__emit(self.response_callbacks, response)
        self._logger.debug(f"Processing received RESPONSE packet: {response}")

        if self.__send_future and not self.__send_future.done():
            self.__send_future.set_result(response)

    def __process_erp1_telegram(self, erp1: ERP1Telegram):
        """Process a received ERP1 telegram. This includes emitting it to registered callbacks and further processing based on RORG and learning bit."""
        # emit the raw telegram
        self.__emit_with_sender_filter(self.__erp1_receive_callbacks, erp1.sender, erp1)
        self._logger.debug(f"ESP3 packet successfully decoded to ERP1 telegram: {erp1}")

        # check if sender is known; if not, emit to new device callbacks and add to detected devices list
        if not self.__is_sender_known(erp1.sender):
            self.__detected_devices.append(erp1.sender)
            self.__emit(self.__new_device_callbacks, erp1.sender)
            self._logger.info(f"New device detected with sender address: {erp1.sender}")

        # if it's a UTE telegram, try to parse to UTE message; if parsing fails, ignore the packet and return;
        if erp1.rorg == RORG.RORG_UTE:
            try:
                ute_message = UTEMessage.from_erp1(erp1)
            except Exception as e:
                return

            self.__handle_ute_message(ute_message)
            return

        # handle 1BS teach-in telegrams; for now, we just ignore them (NOT IMPLEMENTED)
        if erp1.rorg == RORG.RORG_1BS and erp1.is_learning_telegram:
            self.__handle_1bs_teach_in_telegram(erp1)
            return

        # handle 4BS teach-in telegrams; for now, we just ignore them (NOT IMPLEMENTED)
        if erp1.rorg == RORG.RORG_4BS and erp1.is_learning_telegram:
            self.__handle_4bs_teach_in_telegram(erp1)
            return

        # if sender is not known, we cannot decode to EEP message, so we return
        if not erp1.sender in self.__known_devices:
            msg = f"Failed to decode ERP1 telegram to EEP message: sender {erp1.sender} is unknown."
            self._logger.debug(msg)
            self.__emit(self.__parsing_failed_callbacks, msg)
            return

        # if we have no EEP handler for the EEP ID of the sender, we cannot decode to EEP message, so we return
        if not self.__known_devices[erp1.sender] in self.__eep_handlers:
            self._logger.debug(
                f"Failed to decode ERP1 telegram to EEP message: No EEP handler for {self.__known_devices[erp1.sender]}."
            )
            self.__emit(
                self.__parsing_failed_callbacks,
                f"Failed to decode ERP1 telegram to EEP message: No EEP handler for {self.__known_devices[erp1.sender]}.",
            )
            return

        # try eep-specific decoding; if it fails, ignore the packet and return
        try:
            eep_message = self.__eep_handlers[self.__known_devices[erp1.sender]](erp1)
            self.__emit_with_sender_filter(
                self.__eep_receive_callbacks, erp1.sender, eep_message
            )
            self._logger.debug(
                f"ERP1 telegram successfully decoded to EEP message: {eep_message}"
            )
        except Exception as e:
            self._logger.debug(f"Failed to decode ERP1 telegram to EEP message: {e}")
            self.__emit(
                self.__parsing_failed_callbacks,
                f"Failed to decode ERP1 telegram to EEP message: {e}",
            )
            return

    def __handle_ute_message(self, ute_message: UTEMessage):
        self.__emit(self.__ute_receive_callbacks, ute_message)

        # if we are not currently in learning mode, we ignore all UTE messages, because they are only relevant during learning mode
        if not self.__is_learning:
            return

        # ignore response messages, we only want to process teach-in query messages during learning mode
        if isinstance(ute_message.request_type, UTEResponseType):
            return

        request_type = ute_message.request_type
        response_expected = (
            ute_message.teach_in_response_message_expectation
            == EEPTeachInResponseMessageExpectation.RESPONSE_EXPECTED
        )

        match request_type:
            case UTEQueryRequestType.TEACH_IN:
                print(f"Received UTE teach-in query message: {ute_message}")

            case UTEQueryRequestType.TEACH_IN_DELETION:
                print(f"Received UTE teach-in deletion query message: {ute_message}")

            case UTEQueryRequestType.TEACH_IN_OR_DELETION_OF_TEACH_IN:
                print(
                    f"Received UTE teach-in or deletion of teach-in query message: {ute_message}"
                )

    def __handle_1bs_teach_in_telegram(self, erp1: ERP1Telegram):
        pass

    def __handle_4bs_teach_in_telegram(self, erp1: ERP1Telegram):
        pass

    def __handle_eep_message(self, msg: EEPMessage):
        for cb in self.callbacks:
            cb(msg)
