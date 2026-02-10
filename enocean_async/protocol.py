"""Asynchronous EnOcean Serial Protocol Version 3 (ESP3) implementation."""

import asyncio
from typing import Callable

import serial_asyncio_fast as serial_asyncio

from enocean_async.response import ResponseCode, ResponseTelegram

from .address import EURID, BaseAddress
from .common_command import CommonCommandTelegram
from .erp1 import RORG, ERP1Telegram
from .esp3 import SYNC_BYTE, ESP3Packet, ESP3PacketType, crc8
from .version import VersionIdentifier, VersionInfo

type ESP3Callback = Callable[[ESP3Packet], None]
type ERP1Callback = Callable[[ERP1Telegram], None]
type ResponseCallback = Callable[[ResponseTelegram], None]
# type UTECallback = Callable[[UTE], None]


class BaseIDChangeError(Exception):
    pass


class ESP3(asyncio.Protocol):
    """
    Minimal asynchronous EnOcean Serial Protocol Version 3 (ESP3).
    - Parses ESP3 frames
    - Emits raw ESP3 packets
    - Emits ERP1 telegrams
    - Emits UTE teach-in telegrams
    """

    def __init__(self):
        self.transport: serial_asyncio.SerialTransport | None = None
        self.__buffer = bytearray()

        # callbacks
        self.__esp3_receive_callbacks: list[ESP3Callback] = []
        self.__erp1_receive_callbacks: list[ERP1Callback] = []
        self.esp3_send_callbacks: list[ESP3Callback] = []
        self.response_callbacks: list[ResponseCallback] = []

        # UTE callbacks
        # self._ute_callbacks: list[UTECallback] = []

        self.__version_info: VersionInfo | None = None
        self.__base_id_remaining_write_cycles: int | None = None
        self.__base_id: BaseAddress | None = None
        self.__eurid: EURID | None = None

        self.__awaiting_response: bool = False
        self.__response: ResponseTelegram | None = None

    @classmethod
    async def open_serial_port(cls, port: str, baudrate: int = 57600) -> "ESP3":
        """Open a serial connection to the EnOcean gateway and return an instance of EnOceanProtocol."""
        loop = asyncio.get_running_loop()
        protocol = cls()

        try:
            await serial_asyncio.create_serial_connection(
                loop, lambda: protocol, port, baudrate=baudrate
            )
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to EnOcean gateway on {port}: {e}"
            )

        return protocol

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def add_packet_callback(self, cb: ESP3Callback):
        self.__esp3_receive_callbacks.append(cb)

    def add_erp1_callback(self, cb: ERP1Callback):
        self.__erp1_receive_callbacks.append(cb)

    def __emit(self, callbacks, obj):
        """Emit an object to all registered callbacks of the given type."""
        loop = asyncio.get_running_loop()
        for cb in callbacks:
            loop.call_soon(cb, obj)

    # ------------------------------------------------------------------
    # Serial protocol
    # ------------------------------------------------------------------

    def connection_made(self, transport: serial_asyncio.SerialTransport):
        self.transport = transport

    def data_received(self, data: bytes):
        self.__buffer.extend(data)
        self.__process_buffer()

    def connection_lost(self, exc):
        self.transport = None

    def eof_received(self, exc):
        pass

    # ------------------------------------------------------------------
    # process incoming data
    # ------------------------------------------------------------------
    def __process_buffer(self):
        """Process the internal buffer to extract complete ESP3 packets and emit them."""
        while True:
            # find sync byte
            try:
                sync_index = self.__buffer.index(SYNC_BYTE)
            except ValueError:
                self.__buffer.clear()
                return

            # drop garbage before sync
            if sync_index > 0:
                del self.__buffer[:sync_index]

            # need at least sync + header + header CRC
            if len(self.__buffer) < 6:
                return

            # read header
            header = self.__buffer[1:5]
            data_len = (header[0] << 8) | header[1]
            opt_len = header[2]
            packet_type = header[3]

            total_len = 1 + 4 + 1 + data_len + opt_len + 1
            if len(self.__buffer) < total_len:
                return

            # validate header CRC
            if self.__buffer[5] != crc8(header):
                del self.__buffer[:1]
                continue

            # extract data + optional
            data_start = 6
            data_end = data_start + data_len
            opt_end = data_end + opt_len

            data = bytes(self.__buffer[data_start:data_end])
            optional = bytes(self.__buffer[data_end:opt_end])

            # validate data CRC
            if self.__buffer[opt_end] != crc8(data + optional):
                del self.__buffer[:1]
                continue

            # create ESP3Packet and process it
            pkt = ESP3Packet(ESP3PacketType(packet_type), data, optional)
            self.__process_esp3_packet(pkt)

            # Remove processed bytes
            del self.__buffer[:total_len]

    def __process_esp3_packet(self, packet: ESP3Packet):
        """Process a received ESP3 packet. This includes emitting the raw packet to registered callbacks and further processing based on packet type."""
        self.__emit(self.__esp3_receive_callbacks, packet)

        match packet.packet_type:
            case ESP3PacketType.RESPONSE:
                self.__process_response_packet(packet)

            case ESP3PacketType.RADIO_ERP1:
                self.__process_erp1_packet(packet)

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
            print(f"Failed to parse response packet: {e}")
            pass

    def __process_erp1_packet(self, pkt: ESP3Packet):
        rorg: RORG | None = None

        try:
            rorg = RORG(pkt.data[0])
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
                erp1 = ERP1Telegram.from_esp3(pkt)
                self.__emit(self.__erp1_receive_callbacks, erp1)
            except Exception as e:
                print(f"Failed to parse ERP1 packet: {pkt}, error: {e}")
                pass

    # ------------------------------------------------------------------
    # sending
    # ------------------------------------------------------------------
    async def send(self, packet: ESP3Packet) -> ResponseTelegram:
        """Send an ESP3 packet to the EnOcean module and wait for a response."""

        self.__emit(self.esp3_send_callbacks, packet)

        # construct header
        header = bytes(
            [
                (len(packet.data) >> 8) & 0xFF,
                len(packet.data) & 0xFF,
                len(packet.optional) & 0xFF,
                packet.packet_type,
            ]
        )

        # construct the full frame with sync byte, header, data, optional and CRCs
        frame = bytearray()
        frame.append(SYNC_BYTE)
        frame.extend(header)
        frame.append(crc8(header))
        frame.extend(packet.data)
        frame.extend(packet.optional)
        frame.append(crc8(packet.data + packet.optional))

        # send the frame
        self.transport.write(frame)

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

    @property
    async def version_info(self) -> VersionInfo | None:
        """Get the version information of the connected EnOcean module."""
        if self.__version_info is not None:
            return self.__version_info

        if self.transport is None:
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
    async def base_id(self) -> BaseAddress | None:
        """Get the base ID of the connected EnOcean module."""
        if self.__base_id is not None:
            return self.__base_id

        if self.transport is None:
            raise ConnectionError("Not connected to EnOcean module")

        # Send GET ID base id request
        cmd = CommonCommandTelegram.CO_RD_IDBASE()
        response = await self.send(cmd.to_esp3_packet())

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

        if self.transport is None:
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
    async def base_id_remaining_write_cycles(self) -> int | None:
        """Get the remaining write cycles for the base ID of the connected EnOcean module."""
        if self.__base_id_remaining_write_cycles is not None:
            return self.__base_id_remaining_write_cycles

        await (
            self.base_id
        )  # base_id() will fetch the remaining write cycles as optional data
        return self.__base_id_remaining_write_cycles

    @property
    async def eurid(self) -> EURID:
        """Get the EURID of the connected EnOcean module."""
        if self.__eurid is not None:
            return self.__eurid

        self.__eurid = (await self.version_info).eurid
        return self.__eurid

    @property
    async def ready(self) -> None:
        """Wait until the transport is available."""
        while self.transport is None:
            await asyncio.sleep(0.1)
