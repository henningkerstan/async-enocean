from dataclasses import dataclass
from enum import IntEnum

from .address import EURID, Address, BaseAddress, BroadcastAddress
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
    sender: EURID | BaseAddress
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

        # ERP1 telegrams must have at least 6 bytes of data (RORG + payload + sender + status)
        if len(data) < 6:
            raise ERP1ParseError(f"ERP1 telegram too short: {len(data)} bytes")

        # determine RORG
        try:
            rorg = RORG(data[0])
        except ValueError:
            raise ERP1ParseError(f"Unknown RORG: 0x{data[0]:02X}")

        # determine sender address
        s = Address.from_bytelist(data[-5:-1])
        if s.is_eurid():
            sender = EURID.from_number(s.to_number())
        elif s.is_base_address():
            sender = BaseAddress.from_number(s.to_number())
        else:
            raise ERP1ParseError(f"Invalid sender address: {sender}")

        status = data[-1]
        payload = data[1:-5]

        # parse optional
        sub_tel_num = opt[0] if len(opt) > 0 else None

        destination_bytes = opt[1:5] if len(opt) > 4 else None
        d = Address.from_bytelist(destination_bytes) if destination_bytes else None

        if d is not None and d.is_broadcast():
            destination = BroadcastAddress()
        elif d is not None and d.is_eurid():
            destination = EURID.from_number(d.to_number())

        dBm = opt[4] if len(opt) > 5 else None
        sec_level = opt[5] if len(opt) > 6 else None

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
