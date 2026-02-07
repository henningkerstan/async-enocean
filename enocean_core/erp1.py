from dataclasses import dataclass
from enum import IntEnum

from .address import EURID, BroadcastAddress
from .esp3 import ESP3Packet, ESP3PacketType


class RORG(IntEnum):
    RPS = 0xF6
    ONEBS = 0xD5
    FOURBS = 0xA5
    VLD = 0xD2
    UTE = 0xD4


class ERP1ParseError(Exception):
    pass


@dataclass
class ERP1Telegram:
    rorg: RORG
    payload: bytes
    sender: EURID
    status: int

    sub_tel_num: int | None = None
    dBm: int | None = None
    sec_level: int | None = None

    destination: EURID | BroadcastAddress | None = None

    def __repr__(self) -> str:
        return (
            f"ERP1Telegram(rorg={self.rorg.name}, "
            f"payload={self.payload.hex().upper()}, "
            f"sender={self.sender.to_string()}, "
            f"status=0x{self.status:02X}, "
            f"sub_tel_num={self.sub_tel_num}, "
            f"dBm={self.dBm}, "
            f"sec_level={self.sec_level}, "
            f"destination={self.destination.to_string() if self.destination else None})"
        )

    @classmethod
    def from_esp3(cls, pkt: ESP3Packet):
        if pkt.packet_type != ESP3PacketType.RADIO_ERP1:
            raise ERP1ParseError("Not an ERP1 telegram")

        data = pkt.data
        opt = pkt.optional

        # --- Sanity checks ---
        if len(data) < 6:
            raise ERP1ParseError(f"ERP1 telegram too short: {len(data)} bytes")

        # --- Parse DATA ---
        try:
            rorg = RORG(data[0])
        except ValueError:
            raise ERP1ParseError(f"Unknown RORG: 0x{data[0]:02X}")

        sender = EURID.from_bytelist(data[-5:-1])
        status = data[-1]
        payload = data[1:-5]

        # --- Parse OPTIONAL ---
        sub_tel_num = opt[0] if len(opt) > 0 else None
        dBm = opt[1] if len(opt) > 1 else None
        sec_level = opt[2] if len(opt) > 2 else None
        destination_bytes = opt[3:8] if len(opt) > 7 else None
        destination = (
            EURID.from_bytelist(destination_bytes)
            if destination_bytes is not None
            else None
        )

        return cls(
            rorg=rorg,
            payload=payload,
            sender=sender,
            status=status,
            sub_tel_num=sub_tel_num,
            dBm=dBm,
            sec_level=sec_level,
            destination=destination,
        )
