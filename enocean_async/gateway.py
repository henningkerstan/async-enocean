import asyncio
from dataclasses import dataclass
import logging
import time
from typing import Callable, Optional

import serial_asyncio_fast as serial_asyncio

from .address import EURID, BaseAddress, SenderAddress
from .capabilities.action import Action
from .capabilities.metadata import MetaDataCapability
from .capabilities.state_change import StateChange, StateChangeCallback
from .device.device import Device
from .eep import EEP_SPECIFICATIONS
from .eep.handler import EEPHandler
from .eep.id import EEP
from .eep.manufacturer import Manufacturer
from .eep.message import EEPMessage
from .erp1.telegram import (
    RORG,
    ERP1Telegram,
    FourBSTeachInTelegram,
    FourBSTeachInVariation,
)
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
type TeachInCallback = Callable[[FourBSTeachInTelegram], None]


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
        self.__known_device_eeps: dict[EURID | BaseAddress, EEP] = {}
        self.__detected_devices: list[EURID | BaseAddress] = []
        self.__eep_handlers: dict[EEP, EEPHandler] = {}
        self.__devices: dict[EURID | BaseAddress, Device] = {}
        self.__state_change_callbacks: list[StateChangeCallback] = []

        # callbacks
        self.__esp3_receive_callbacks: list[ESP3Callback] = []
        self.__erp1_receive_callbacks: list[ERP1CallbackWithFilter] = []
        self.__ute_receive_callbacks: list[UTECallback] = []
        self.__eep_receive_callbacks: list[EEPCallbackWithFilter] = []
        self.__parsing_failed_callbacks: list[ParsingFailedCallback] = []
        self.__response_callbacks: list[ResponseCallback] = []

        self.__new_device_callbacks: list[NewDeviceCallback] = []

        self.__esp3_send_callbacks: list[ESP3Callback] = []

        # send handling
        self.__send_lock: asyncio.Lock = asyncio.Lock()
        self.__send_future: asyncio.Future | None = None

        # learning
        self.__is_learning: bool = False
        self.__learning_timeout_task: asyncio.Task | None = None
        self.__sender_id_for_learning: SenderAddress | None = None
        self.__allow_teach_out: bool = False

        # logging
        self._logger = logging.getLogger(__name__)

        # auto-reconnect
        self.__reconnect_task: asyncio.Task | None = None
        self.__stopped: bool = False

        self.auto_reconnect: bool = True
        """If True (default), automatically attempt to reconnect when the connection is lost. Set to False to disable reconnection entirely."""

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
        - the sender address of the message is known (by adding it to this gateway as known-device along with its eep), and
        - there is an EEPHandler capable of handling the eep of the sender device."""
        self.__eep_receive_callbacks.append(EEPCallbackWithFilter(cb, sender_filter))

    def add_ute_received_callback(self, cb: UTECallback):
        self.__ute_receive_callbacks.append(cb)

    def add_parsing_failed_callback(self, cb: ParsingFailedCallback):
        self.__parsing_failed_callbacks.append(cb)

    def add_response_callback(self, cb: ResponseCallback):
        self.__response_callbacks.append(cb)

    def add_state_change_callback(self, cb: StateChangeCallback) -> None:
        """Add a callback for capability state changes."""
        self.__state_change_callbacks.append(cb)

    # ------------------------------------------------------------------
    # start and stop
    # ------------------------------------------------------------------
    async def start(self, auto_reconnect: bool = True) -> None:
        """Open the serial connection to the EnOcean module and start processing incoming packets.

        Args:
            auto_reconnect: If True (default), automatically attempt to reconnect when the
                            connection is lost. Set to False to disable reconnection entirely.
        """
        self.__stopped = False
        self.auto_reconnect = auto_reconnect
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
            self._logger.warning(
                f"Failed to connect to EnOcean module on {self.__port} at baudrate {self.__baudrate}: {e}"
            )
            raise ConnectionError(
                f"Failed to connect to EnOcean module on {self.__port} at baudrate {self.__baudrate}: {e}"
            )

    def stop(self) -> None:
        """Close the serial connection to the EnOcean module."""
        self.__stopped = True
        if self.__reconnect_task is not None:
            self.__reconnect_task.cancel()
            self.__reconnect_task = None
        if self.__transport is not None:
            self.__transport.close()
            self.__transport = None
            self._logger.info(
                f"Serial connection to EnOcean module on {self.__port} closed"
            )

    @property
    async def valid_senders(self) -> list[SenderAddress]:
        """Return the list of valid sender addresses for this gateway, which includes the gateway's EURID and the range of Base IDs derived from the gateway's base ID."""
        base_id = await self.base_id
        senders = [await self.eurid, base_id]

        base_id_number = base_id.to_number()
        for i in range(1, 128):
            senders.append(BaseAddress(base_id_number + i))

        return senders

    async def is_valid_sender(self, sender: SenderAddress) -> bool:
        """Check if the sender address is a valid sender for this gateway (i.e. is either the gateway's EURID, or a BaseAddress in the range of the gateway's base ID)."""
        valid_senders = await self.valid_senders
        return sender in valid_senders

    async def start_learning(
        self,
        timeout_seconds: int = 60,
        sender_id: SenderAddress | None = None,
        allow_teach_out: bool = False,
    ) -> None:
        """Start learning mode for pairing new EnOcean devices.

        This method enables the gateway to learn new device configurations. When learning mode
        is active, the gateway will accept teach-in telegrams from EnOcean devices. The learning
        session will automatically terminate after the specified timeout period.

        Args:
            timeout_seconds (int, optional): Duration in seconds before learning mode automatically
                stops. Defaults to 60 seconds.
            sender_id (SenderAddress | None, optional): The sender ID to use for learning mode.
                If not provided, the gateway's base ID will be used.
            allow_teach_out (bool, optional): If True, allows devices to be removed (teach-out)
                during learning mode. Defaults to False.
        """
        self.__is_learning = True
        self.__allow_teach_out = allow_teach_out

        if sender_id is not None and not await self.is_valid_sender(sender_id):
            raise ValueError(
                f"Invalid sender_id {sender_id} for learning mode. Must be a valid sender address for this gateway."
            )

        self.__sender_id_for_learning = (
            sender_id if sender_id is not None else await self.base_id
        )

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

        if not self.__transport:
            self._logger.error(
                "Cannot send: gateway is not connected to an EnOcean module."
            )
            return SendResult(None, None)

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

    async def send_command(
        self,
        destination: EURID | BaseAddress,
        action: Action,
        sender: SenderAddress | None = None,
    ) -> SendResult:
        """Send a typed action command to a registered device.

        Args:
            destination: The device's address (must have been registered via add_device()).
                         Used to look up the correct EEP; not necessarily the RF destination.
            action: A typed Action instance (e.g. SetCoverPositionAction, DimAction).
            sender: Sender address to use. If None, uses the device's registered sender
                    or falls back to the gateway's base ID.

        Returns:
            SendResult with the response and duration.

        Raises:
            ValueError: If the device is unknown, or the action is not supported by its EEP.
            ConnectionError: If not connected to the EnOcean module.
        """
        if destination not in self.__known_device_eeps:
            raise ValueError(f"Unknown device {destination}: call add_device() first")

        eep_id = self.__known_device_eeps[destination]

        if eep_id not in self.__eep_handlers:
            raise ValueError(f"No EEP handler loaded for {eep_id}")

        spec = EEP_SPECIFICATIONS[eep_id]
        if action.action_uid not in spec.command_encoders:
            raise ValueError(
                f"Action '{action.action_uid}' is not supported for EEP {eep_id}"
            )

        # Resolve sender: explicit > device sender > gateway base ID
        if sender is None:
            device = self.__devices.get(destination)
            if device and device.sender:
                sender = device.sender
            else:
                sender = await self.base_id
        if sender is None:
            raise ValueError(
                "Could not determine sender address; pass sender= explicitly or connect first"
            )

        message: EEPMessage = spec.command_encoders[action.action_uid](action)
        message.sender = sender
        message.destination = destination

        erp1 = self.__eep_handlers[eep_id].encode(message)
        return await self.send_esp3_packet(erp1.to_esp3())

    def connection_made(self) -> None:
        pass

    def connection_lost(self, exc: Exception | None) -> None:
        self.__transport = None
        if self.__stopped:
            return
        if not self.auto_reconnect:
            self._logger.error(
                "Connection to EnOcean module lost and auto-reconnect is disabled. You must manually call start() to reconnect."
            )
            return
        self._logger.warning(
            "Connection to EnOcean module lost, attempting to reconnect ..."
        )
        if self.__reconnect_task is not None:
            self.__reconnect_task.cancel()
        self.__reconnect_task = asyncio.create_task(self.__try_to_reconnect())

    async def __try_to_reconnect(self):
        for attempt in range(1, 721):
            await asyncio.sleep(5)
            try:
                self._logger.info(
                    f"Trying to reconnect to EnOcean Module (attempt #{attempt}/720)"
                )
                await self.start()
                self.__reconnect_task.cancel()
                self.__reconnect_task = None
                self._logger.info("Reconnect successfull")
                return
            except Exception:
                self._logger.warning(
                    f"Reconnection attempt #{attempt}/720 failed, retrying again in 5s."
                )
                continue

        self._logger.error(
            "Could not reconnect to EnOcean module after 720 attempts (1 hour). Stopping auto-reconnect."
        )

    # ------------------------------------------------------------------
    # device registry
    # ------------------------------------------------------------------
    def add_device(
        self,
        address: EURID | BaseAddress,
        eep: EEP,
        sender: SenderAddress | None = None,
        name: str | None = None,
    ) -> None:
        """Register a device with its sender address (EURID or Base ID) and its eep.

        This allows the gateway to recognize incoming messages from this device and decode them according to the registered EEP (if a handler for that EEP is found).
        """
        self.__known_device_eeps[address] = eep
        self._logger.info(f"Added device with address {address} and eep {eep}")

        # get the EEP handler for this eep
        if eep not in self.__eep_handlers:
            # try to load
            if eep not in EEP_SPECIFICATIONS:
                self._logger.warning(
                    f"EEP {eep} is not supported. Messages from device {address} will not be decoded."
                )
                return
            else:
                self.__eep_handlers[eep] = EEPHandler(EEP_SPECIFICATIONS[eep])
                self._logger.info(f"Loaded EEP handler for eep {eep}")
        else:
            self._logger.debug(f"EEP handler for eep {eep} already loaded.")

        # build capability list from EEP capability_factories
        eep = EEP_SPECIFICATIONS[eep]
        if not eep.capability_factories:
            self._logger.debug(
                f"EEP {eep} has no capability factories; StateChange processing unavailable for device {address}."
            )
            return

        cb = self.__on_capability_state_change
        capabilities = [MetaDataCapability(device_address=address, on_state_change=cb)]
        for factory in eep.capability_factories:
            capabilities.append(factory(address, cb))

        device = Device(
            address=address,
            eep=eep,
            name=name or str(address),
            sender=sender,
            capabilities=capabilities,
        )
        self.__devices[address] = device
        self._logger.debug(
            f"Initialized device {address} with {len(device.capabilities)} capabilities"
        )

    def __on_capability_state_change(self, state_change: StateChange) -> None:
        """Internal callback for capability state changes."""
        self.__emit(self.__state_change_callbacks, state_change)

    def remove_device(self, address: EURID | BaseAddress) -> None:
        """Deregister a device by its sender address (EURID or Base ID). This removes the device from the registry of known devices, so that incoming messages from this address will no longer be recognized as coming from a known device and will not be decoded as EEP messages."""
        if address in self.__known_device_eeps:
            del self.__known_device_eeps[address]
            if address in self.__devices:
                del self.__devices[address]
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
            self._logger.debug(
                f"Received ESP3 packet of type {packet.packet_type.name}, which is currently not processed by the gateway. Ignoring packet."
            )
            return

        self.__process_erp1_packet(packet)

    def __process_erp1_packet(self, packet: ESP3Packet) -> None:
        """Parse ESP3 RADIO_ERP1 packet into ERP1 telegram and process it."""
        try:
            erp1 = ERP1Telegram.from_esp3(packet)
        except Exception as e:
            self._logger.debug(
                f"Failed to parse ESP3 packet to ERP1 telegram: {packet}. Ignoring packet. Error: {e}"
            )
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
            sender in self.__known_device_eeps.keys()
            or sender in self.__detected_devices
        )

    def __process_response(self, response: ResponseTelegram):
        """Process a received RESPONSE packet. If we are currently awaiting a response, try to parse it and store it for the send() method to retrieve."""
        self.__emit(self.__response_callbacks, response)
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

        self.__process_eep_telegram(erp1)

    def __process_eep_telegram(self, erp1: ERP1Telegram) -> None:
        """Detect EEP ID for ERP1 telegram and decode to EEP message."""
        # There are two options for determining the EEP ID of an incoming ERP1 telegram: either we look it up by the sender address, or by the destination address (if the destination is not a broadcast address).
        # We first check if we have a known device with the sender address, and if not, we check if we have a known device with the destination address.
        # If we cannot find a known device for either the sender or the destination, we cannot determine the EEP ID for this telegram, so we emit a parsing failed message and return.
        # If we can find a known device for either the sender or the destination, we use that device's EEP ID for further processing.
        eep_id: EEP
        if erp1.sender in self.__known_device_eeps:
            eep_id = self.__known_device_eeps[erp1.sender]
        else:
            if erp1.destination is None or erp1.destination.is_broadcast():
                msg = (
                    f"Failed to decode ERP1 telegram to EEP message: sender {erp1.sender} "
                    "is unknown and destination is not specified."
                )
                self._logger.debug(msg)
                self.__emit(self.__parsing_failed_callbacks, msg)
                return

            if erp1.destination not in self.__known_device_eeps:
                msg = (
                    f"Failed to decode ERP1 telegram to EEP message: sender {erp1.sender} "
                    f"is unknown and destination {erp1.destination} is also unknown."
                )
                self._logger.debug(msg)
                self.__emit(self.__parsing_failed_callbacks, msg)
                return

            self._logger.debug(
                f"Sender {erp1.sender} is unknown, but destination {erp1.destination} "
                "is known, using EEP ID of destination for EEP decoding."
            )
            eep_id = self.__known_device_eeps[erp1.destination]

        if eep_id not in self.__eep_handlers:
            self._logger.debug(
                f"Failed to decode ERP1 telegram to EEP message: No EEP handler for {eep_id}."
            )
            self.__emit(
                self.__parsing_failed_callbacks,
                f"Failed to decode ERP1 telegram to EEP message: No EEP handler for {eep_id}.",
            )
            return

        try:
            eep_message = self.__eep_handlers[eep_id](erp1)
            self.__process_eep_message(eep_message)
        except Exception as e:
            self._logger.debug(f"Failed to decode ERP1 telegram to EEP message: {e}")
            self.__emit(
                self.__parsing_failed_callbacks,
                f"Failed to decode ERP1 telegram to EEP message: {e}",
            )
            return

    def __process_eep_message(self, eep_message: EEPMessage) -> None:
        """Emit callbacks for a decoded EEP message."""
        self.__emit_with_sender_filter(
            self.__eep_receive_callbacks, eep_message.sender, eep_message
        )
        self._logger.debug(
            f"ERP1 telegram successfully decoded to EEP message: {eep_message}"
        )
        self.__process_capability_message(eep_message)

    def __process_capability_message(self, eep_message: EEPMessage) -> None:
        """Decode EEP message using device capabilities."""
        if eep_message.sender is None:
            self.__emit(
                self.__parsing_failed_callbacks,
                "Failed to decode capability: sender is not specified.",
            )
            return

        device = self.__devices.get(eep_message.sender)
        if device is None:
            self.__emit(
                self.__parsing_failed_callbacks,
                "Failed to decode capability: no device.",
            )
            return

        for capability in device.capabilities:
            try:
                capability.decode(eep_message)
            except Exception as e:
                self._logger.debug(
                    f"Failed to decode EEP message {eep_message} using capability {capability}: {e}"
                )
                self.__emit(
                    self.__parsing_failed_callbacks,
                    f"Failed to decode EEP message {eep_message} using capability {capability}: {e}",
                )

    async def __send_ute_response(self, response: UTEMessage) -> None:
        try:
            self._logger.info(f"Sending UTE teach-in response message: {response}")
            erp1 = response.to_erp1()
            esp3 = erp1.to_esp3()
            send_result = await self.send_esp3_packet(esp3)

        except Exception as e:
            self._logger.error(f"Failed to send UTE teach-in response message: {e}")
            return

        if (
            send_result.response is None
            or send_result.response.return_code != ResponseCode.OK
        ):
            self._logger.error(
                f"Failed to send UTE teach-in response message. Send result: {send_result}"
            )

        self._logger.info(
            f"Successfully completed bidirectional UTE teach-in for device {response.sender} with EEP {response.eep}."
        )

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
            case (
                UTEQueryRequestType.TEACH_IN,
                UTEQueryRequestType.TEACH_IN_OR_DELETION_OF_TEACH_IN,
            ):
                self._logger.info(
                    f"Received UTE teach-in / teach-in or deletion of teach-in message: {ute_message}"
                )
                if response_expected and self.__is_learning:
                    self._logger.info(
                        "Preparing to send UTE teach-in response message."
                    )
                    # TODO: check if EEP is supported and send appropriate response; for now, we just send a generic "accepted" response without checking the EEP or other details of the message, which is not ideal but should be sufficient for testing purposes
                    response = UTEMessage.response_for_query(
                        ute_message,
                        UTEResponseType.ACCEPTED_TEACH_IN,
                        sender=self.__sender_id_for_learning,
                    )
                    asyncio.create_task(self.__send_ute_response(response))

            case UTEQueryRequestType.TEACH_IN_DELETION:
                self._logger.info(
                    f"Received UTE teach-in deletion query message: {ute_message}"
                )

    def __handle_1bs_teach_in_telegram(self, erp1: ERP1Telegram):
        pass

    def __handle_4bs_teach_in_telegram(self, erp1: ERP1Telegram):
        try:
            teach_in_telegram = FourBSTeachInTelegram.from_erp1(erp1)
            self._logger.info(f"4BS teach-in telegram: {teach_in_telegram}")

        except ValueError as e:
            self._logger.warning(f"Failed to parse 4BS teach-in telegram: {e}")

        learn_type = erp1.bitstring_raw_value(24, 1)

        if learn_type == 0:  # unidirectional profileless
            # todo: this will just add a device
            pass
        else:  # unidirectional with profile
            func = erp1.bitstring_raw_value(0, 6)
            type_ = erp1.bitstring_raw_value(6, 7)
            manufacturer_id = erp1.bitstring_raw_value(13, 11)
            manufacturer = Manufacturer(manufacturer_id)
            eep = EEP(0xA5, func, type_, manufacturer)
            self._logger.info(
                f"4BS learn telegram with EEP A5-{func:02X}-{type_:02X} and manufacturer '{manufacturer}', hence {eep}"
            )
