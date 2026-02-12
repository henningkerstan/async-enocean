"""Asynchronous EnOcean Serial Protocol Version 3 (ESP3) implementation."""

import asyncio
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..gateway import Gateway

import serial_asyncio_fast as serial_asyncio

from enocean_async.esp3.response import ResponseTelegram

from .packet import SYNC_BYTE, ESP3Packet, ESP3PacketType, crc8


class EnOceanSerialProtocol3(asyncio.Protocol):
    """
    Minimal asynchronous EnOcean Serial Protocol Version 3 (ESP3).
    - Parses ESP3 frames
    - Emits raw ESP3 packets
    """

    def __init__(self, gateway: "Gateway"):
        self.__buffer = bytearray()
        self.__gateway: "Gateway" = gateway

    def connection_made(self, transport: serial_asyncio.SerialTransport):
        self.__gateway.connection_made()

    def data_received(self, data: bytes):
        """Process the internal buffer to extract complete ESP3 packets and emit them."""
        self.__buffer.extend(data)

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
            self.__gateway.process_esp3_packet(pkt)

            # Remove processed bytes
            del self.__buffer[:total_len]

    def connection_lost(self, exception: Exception | None):
        self.__gateway.connection_lost(exception)

    def eof_received(self, exception: Exception | None):
        pass
