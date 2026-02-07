import asyncio
from typing import Callable

import serial_asyncio_fast as serial_asyncio

from enocean_core.response import ResponseCode, ResponseTelegram

from .address import EURID, BaseAddress
from .common_command import CommonCommandTelegram
from .erp1 import RORG, ERP1Telegram
from .esp3 import SYNC_BYTE, ESP3Packet, ESP3PacketType, crc8
from .version import VersionIdentifier, VersionInfo

type PacketCallback = Callable[[ESP3Packet], None]
type ERP1Callback = Callable[[ERP1Telegram], None]
# type UTECallback = Callable[[UTE], None]


class ESP3(asyncio.Protocol):
    """
    Minimal asynchronous EnOcean Serial Protocol Version 3 (ESP3).
    - Parses ESP3 frames
    - Emits raw ESP3 packets
    - Emits ERP1 telegrams
    - Emits UTE teach-in telegrams
    """

    def __init__(self):
        self.transport = None
        self._buffer = bytearray()

        # Raw ESP3 packet callbacks
        self._packet_callbacks: list[PacketCallback] = []

        # ERP1 callbacks
        self._erp1_callbacks: list[ERP1Callback] = []

        # UTE callbacks
        # self._ute_callbacks: list[UTECallback] = []

        self.__version_info: VersionInfo | None = None
        self.__base_id: BaseAddress | None = None
        self.__eurid: EURID | None = None

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

    def add_packet_callback(self, cb: PacketCallback):
        self._packet_callbacks.append(cb)

    def add_erp1_callback(self, cb: ERP1Callback):
        self._erp1_callbacks.append(cb)

    # ------------------------------------------------------------------
    # Emit helpers
    # ------------------------------------------------------------------

    def _emit(self, callbacks, obj):
        loop = asyncio.get_running_loop()
        for cb in callbacks:
            loop.call_soon(cb, obj)

    # ------------------------------------------------------------------
    # Serial protocol
    # ------------------------------------------------------------------

    def connection_made(self, transport: serial_asyncio.SerialTransport):
        self.transport = transport

    def data_received(self, data: bytes):
        self._buffer.extend(data)
        self._process_buffer()

    def connection_lost(self, exc):
        self.transport = None

    def eof_received(self, exc):
        pass

    # ------------------------------------------------------------------
    # ESP3 framing + parsing
    # ------------------------------------------------------------------

    def _process_buffer(self):
        while True:
            # find sync byte
            try:
                sync_index = self._buffer.index(SYNC_BYTE)
            except ValueError:
                self._buffer.clear()
                return

            # drop garbage before sync
            if sync_index > 0:
                del self._buffer[:sync_index]

            # need at least sync + header + header CRC
            if len(self._buffer) < 6:
                return

            header = self._buffer[1:5]
            data_len = (header[0] << 8) | header[1]
            opt_len = header[2]
            packet_type = header[3]

            total_len = 1 + 4 + 1 + data_len + opt_len + 1
            if len(self._buffer) < total_len:
                return

            # validate header CRC
            if self._buffer[5] != crc8(header):
                del self._buffer[:1]
                continue

            # Extract data + optional
            data_start = 6
            data_end = data_start + data_len
            opt_end = data_end + opt_len

            data = bytes(self._buffer[data_start:data_end])
            optional = bytes(self._buffer[data_end:opt_end])

            # Validate data CRC
            if self._buffer[opt_end] != crc8(data + optional):
                del self._buffer[:1]
                continue

            pkt = ESP3Packet(ESP3PacketType(packet_type), data, optional)
            self.process_esp3_packet(pkt)

            # Remove processed bytes
            del self._buffer[:total_len]

    def process_esp3_packet(self, pkt: ESP3Packet):
        # Emit raw ESP3 packet
        self._emit(self._packet_callbacks, pkt)

        match pkt.packet_type:
            case ESP3PacketType.RESPONSE:
                self.process_response_packet(pkt)

            case ESP3PacketType.RADIO_ERP1:
                self.process_erp1_packet(pkt)

    def process_response_packet(self, pkt: ESP3Packet):
        print(f"Received response packet: {pkt}")
        try:
            response = ResponseTelegram.from_esp3_packet(pkt)
            self.__response = response
        except Exception as e:
            print(f"Failed to parse response packet: {e}")
            pass

        # try:
        #     response = ResponseTelegram.from_esp3_packet(pkt)
        #     self._emit(self._response_callbacks, response)
        # except Exception:
        #     pass

    def process_erp1_packet(self, pkt: ESP3Packet):
        rorg_byte = pkt.data[0]

        # UTE teach-in
        if rorg_byte == RORG.UTE:
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
                self._emit(self._erp1_callbacks, erp1)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Sending packets
    # ------------------------------------------------------------------

    async def send(self, packet: ESP3Packet) -> ResponseTelegram:
        header = bytes(
            [
                (len(packet.data) >> 8) & 0xFF,
                len(packet.data) & 0xFF,
                len(packet.optional) & 0xFF,
                packet.packet_type,
            ]
        )

        frame = bytearray()
        frame.append(SYNC_BYTE)
        frame.extend(header)
        frame.append(crc8(header))
        frame.extend(packet.data)
        frame.extend(packet.optional)
        frame.append(crc8(packet.data + packet.optional))

        self.transport.write(frame)

        # wait for response
        while self.__response is None:
            await asyncio.sleep(0.1)

        response = self.__response
        self.__response = None

        return response

    async def version_info(self) -> VersionInfo | None:
        """Get the version information of the connected EnOcean module."""
        if self.__version_info is not None:
            return self.__version_info

        if self.transport is None:
            raise ConnectionError("Not connected to EnOcean gateway")

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

    async def base_id(self) -> BaseAddress | None:
        """Get the base ID of the connected EnOcean module."""
        if self.__base_id is not None:
            return self.__base_id

        if self.transport is None:
            raise ConnectionError("Not connected to EnOcean gateway")

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
        return self.__base_id

    async def eurid(self) -> EURID:
        """Get the EURID of the connected EnOcean module."""
        if self.__eurid is not None:
            return self.__eurid

        self.__eurid = (await self.version_info()).eurid
        return self.__eurid

    async def ready(self) -> None:
        """Wait until the EURID is known."""
        while self.transport is None:
            await asyncio.sleep(0.1)
