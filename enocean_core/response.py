"""A response is a special form of telegram usually sent by an EnOcean module to the host.

The cases are defined in ENOCEAN SERIAL PROTOCOL (ESP3) - SPECIFICATION, Section 1.9:

 > Case 1 : ESP3 packets of the type RADIO_ERP1, RADIO_SUB_TEL or REMOTE_MAN are bidirectional, that is, after sending a packet (host -> module) it is mandatory to wait for the RESPONSE message, to confirm the telegram has been processed and will subsequently be transmitted.
 After receiving (module -> host) a packet no RESPONSE is required (see RADIO_ERP1 no. <3> and <4>).

 > Case 2 : Only a host sends a ESP3 COMMAND (COMMON, SMART ACK) to an EnOcean module. Each REQUEST is answered with a RESPONSE message (OK, error, etc.). The reverse direction module-to-host is not possible.

 > Case 3 : Only an EnOcean module sends an EVENT to a host.The type of the EVENT defines whether a RESPONSE message is required or not.
"""

from dataclasses import dataclass
from enum import IntEnum

from .esp3 import ESP3Packet, ESP3PacketType


class ResponseCode(IntEnum):
    """Response codes for EnOcean ESP3 packets."""

    OK = 0x00
    ERROR = 0x01
    NOT_SUPPORTED = 0x02
    WRONG_PARAMETER = 0x03
    OPERATION_DENIED = 0x04
    DUTY_CYCLE_LOCK = 0x05
    BUFFER_TOO_SMALL = 0x06
    NO_FREE_BUFFER = 0x07
    BASEID_OUT_OF_RANGE = 0x90
    BASEID_MAX_REACHED = 0x91


@dataclass
class ResponseTelegram:
    """Represents an EnOcean ESP3 response telegram."""

    return_code: ResponseCode = ResponseCode.OK
    response_data: bytes = b""
    optional_data: bytes = b""

    @classmethod
    def from_esp3_packet(cls, packet: ESP3Packet) -> "ResponseTelegram":
        """Create ResponseTelegram from an ESP3 packet."""

        if packet.packet_type != ESP3PacketType.RESPONSE:
            raise ValueError("ESP3Packet is not a response telegram")

        if len(packet.data) < 1:
            raise ValueError("ESP3Packet is not a valid response; no data")

        try:
            return_code = ResponseCode(packet.data[0])
        except ValueError:
            raise ValueError("Invalid response code in ESP3Packet")

        response_data = packet.data[1:]

        return ResponseTelegram(return_code, response_data, packet.optional)
