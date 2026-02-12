import asyncio
from typing import Callable

import serial_asyncio_fast as serial_asyncio

from .eep.message import EEPMessage
from .erp1.address import EURID, BaseAddress
from .erp1.telegram import RORG, ERP1Telegram
from .esp3.common_command import CommonCommandTelegram
from .esp3.packet import ESP3Packet, ESP3PacketType
from .esp3.protocol import EnOceanSerialProtocol3
from .esp3.response import ResponseCode, ResponseTelegram
from .version.id import VersionIdentifier
from .version.info import VersionInfo

type ESP3Callback = Callable[[ESP3Packet], None]
type ERP1Callback = Callable[[ERP1Telegram], None]
type ResponseCallback = Callable[[ResponseTelegram], None]


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

        # callbacks
        self.__esp3_receive_callbacks: list[ESP3Callback] = []
        self.__erp1_receive_callbacks: list[ERP1Callback] = []
        self.esp3_send_callbacks: list[ESP3Callback] = []
        self.response_callbacks: list[ResponseCallback] = []

        # response handling
        self.__awaiting_response: bool = False
        self.__response: ResponseTelegram | None = None

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------
    def add_packet_callback(self, cb: ESP3Callback):
        self.__esp3_receive_callbacks.append(cb)

    def add_erp1_callback(self, cb: ERP1Callback):
        self.__erp1_receive_callbacks.append(cb)

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
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to EnOcean module on {self.__port}: {e}"
            )

    def stop(self) -> None:
        """Close the serial connection to the EnOcean module."""
        if self.__transport is not None:
            self.__transport.close()
            self.__transport = None

    async def send(self, packet: ESP3Packet) -> ResponseTelegram:
        """Send an ESP3 packet to the EnOcean module and wait for a response."""

        # TODO: prevent sending if not connected or if another send is already awaiting a response

        self.__emit(self.esp3_send_callbacks, packet)

        # send the frame
        self.__transport.write(packet.to_bytes())

        # wait for response
        duration = 0.0
        self.__awaiting_response = True

        while self.__response is None:
            await asyncio.sleep(0.1)

            if (
                duration >= 0.5
            ):  # timeout after 500ms, see EnOcean Serial Protocol (ESP3) - Specification, Section 1.10
                self.__awaiting_response = False
                return None
            else:
                duration

        # got a response, return it and reset state
        self.__awaiting_response = False
        response = self.__response
        self.__response = None
        return response

    def connection_made(self) -> None:
        pass

    def connection_lost(self, exc: Exception | None) -> None:
        self.__transport = None

    @property
    async def base_id(self) -> BaseAddress | None:
        """Get the base ID of the connected EnOcean module."""
        if self.__base_id is not None:
            return self.__base_id

        if self.__transport is None:
            raise ConnectionError("Not connected to EnOcean module")

        # Send GET ID base id request
        cmd = CommonCommandTelegram.CO_RD_IDBASE()
        response: ResponseTelegram = await self.send(cmd.to_esp3_packet())

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
        response = await self.send(cmd.to_esp3_packet())

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
        response = await self.send(cmd.to_esp3_packet())

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

    def process_esp3_packet(self, packet: ESP3Packet):
        """Process a received ESP3 packet. This includes emitting the raw packet to registered callbacks and further processing based on packet type."""
        self.__emit(self.__esp3_receive_callbacks, packet)

        match packet.packet_type:
            case ESP3PacketType.RESPONSE:
                self.__process_response_packet(packet)

            case ESP3PacketType.RADIO_ERP1:
                self.__process_erp1_packet(packet)

    def __emit(self, callbacks, obj):
        """Emit an object to all registered callbacks of the given type."""
        loop = asyncio.get_running_loop()
        for cb in callbacks:
            loop.call_soon(cb, obj)

    def __process_response_packet(self, packet: ESP3Packet):
        """Process a received RESPONSE packet. If we are currently awaiting a response, try to parse it and store it for the send() method to retrieve."""
        self.__emit(self.response_callbacks, ResponseTelegram.from_esp3_packet(packet))

        if not self.__awaiting_response:
            return

        try:
            response = ResponseTelegram.from_esp3_packet(packet)
            self.__response = response
            self.__awaiting_response = False

        except Exception as e:
            self.__response = None
            self.__awaiting_response = False
            pass

    def __process_erp1_packet(self, packet: ESP3Packet):
        rorg: RORG | None = None

        try:
            rorg = RORG(packet.data[0])
        except ValueError:
            return

        # UTE teach-in
        if rorg == RORG.RORG_UTE:
            # try:
            #     ute = UTE.from_esp3(pkt)
            #     self._emit(self._ute_callbacks, ute)
            # except Exception:
            #     pass
            pass

        # Normal ERP1 telegram
        else:
            try:
                erp1 = ERP1Telegram.from_esp3(packet)
                self.__emit(self.__erp1_receive_callbacks, erp1)
            except Exception as e:
                print(f"Failed to parse ERP1 packet: {packet}, error: {e}")
                pass

    def __handle_eep_message(self, msg: EEPMessage):
        for cb in self.callbacks:
            cb(msg)
