from dataclasses import dataclass
from enum import IntEnum

from .address import EURID, Address, BaseAddress, BroadcastAddress
from .esp3 import ESP3Packet, ESP3PacketType


class RORG(IntEnum):
    RORG_RPS = 0xF6
    RORG_1BS = 0xD5
    RORG_4BS = 0xA5
    RORG_VLD = 0xD2
    RORG_UTE = 0xD4
    RORG_MSC = 0xD1
    RORG_ADT_VLD = 0xA6

    @property
    def simple_name(self) -> str:
        return self.name[5:]  # remove "RORG_" prefix


class ERP1ParseError(Exception):
    pass


@dataclass
class ERP1Telegram:
    rorg: RORG
    telegram_data: bytes
    sender: EURID | BaseAddress
    status: int

    sub_tel_num: int | None = None
    dBm: int | None = None
    sec_level: int | None = None
    destination: EURID | BroadcastAddress | None = None

    def bitstring_raw_value(self, offset: int=0, size: int=1) -> int:
        """Extract an integer value from a bitstring within the telegram data given by the offset and size in bits (as in the EEP specification)."""
        
        total_bits = 8 * len(self.telegram_data)

        if offset < 0 or size < 1 or offset + size > total_bits:
            raise ValueError("Invalid offset or length for raw_value")
        
        # convert the telegram data to a single integer (treating the bytes as a big-endian bitstring)
        data_bits = int.from_bytes(self.telegram_data, "big")
        
        # calculate how many bits we need to shift right to get the desired bits at the least significant position
        shift = total_bits - (offset + size)

        # create a mask with exatly 'size' bits set to 1 (by shifting 1 left 'size' times and subtracting 1)
        mask = (1 << size) - 1

        # shift right and apply the mask to extract the desired bits
        return (data_bits >> shift) & mask
    

    def bitstring_scaled_value(self, offset: int=0, size: int=1, scale_min: float=0.0, scale_max: float=1.0) -> float:
        """Extract a scaled float value from the telegram data."""

        if scale_max <= scale_min:
            raise ValueError("scale_max must be greater than scale_min")

        raw = self.bitstring_raw_value(offset, size)

        # maximum value that can be represented with 'size' bits is 2^size - 1; due to the parameter checks in bitstring_raw_value, size > 0, hence max_raw >= 1
        max_raw = (1 << size) - 1  

        return scale_min + (raw / max_raw) * (scale_max - scale_min)


    def __repr__(self) -> str:
        return (
            f"ERP1Telegram(RORG={self.rorg.simple_name}, sender={self.sender.to_string()}, destination: {self.destination.to_string() if self.destination else '*'}, "
            f"telegram_data={self.telegram_data.hex().upper()}, "
            f"status=0x{self.status:02X}, "
            f"sub_tel_num={self.sub_tel_num}, "
            f"dBm={self.dBm}, "
            f"sec_level={self.sec_level})"
        )

    @classmethod
    def from_esp3(cls, pkt: ESP3Packet) -> "ERP1Telegram":
        if pkt.packet_type != ESP3PacketType.RADIO_ERP1:
            raise ERP1ParseError("Not an ERP1 telegram")

        data = pkt.data
        opt = pkt.optional

        # ERP1 telegrams must have at least 6 bytes of data (RORG + payload + sender + status)
        if len(data) < 6:
            raise ERP1ParseError(f"ERP1 telegram too short: {len(data)} bytes")

        # determine RORG
        rorg: RORG | None = None
        try:
            rorg = RORG(data[0])
        except ValueError:
            raise ERP1ParseError(f"Unknown RORG: 0x{data[0]:02X}")

        # determine telegram data
        telegram_data = data[1:-5]

        # match RORG and telegram data length
        match rorg:
            case RORG.RORG_RPS:
                if len(telegram_data) != 1:
                    raise ERP1ParseError(
                        f"RPS telegram data must be 1 byte, got {len(telegram_data)} bytes"
                    )

            case RORG.RORG_1BS:
                if len(telegram_data) != 1:
                    raise ERP1ParseError(
                        f"1BS telegram data must be 1 byte, got {len(telegram_data)} bytes"
                    )

            case RORG.RORG_4BS:
                if len(telegram_data) != 4:
                    raise ERP1ParseError(
                        f"4BS telegram data must be 4 bytes, got {len(telegram_data)} bytes"
                    )

            case RORG.RORG_VLD:
                if len(telegram_data) < 1:
                    raise ERP1ParseError(
                        f"VLD telegram data must be at least 1 byte, got {len(telegram_data)} bytes"
                    )
                if len(telegram_data) > 14:
                    raise ERP1ParseError(
                        f"VLD telegram data must be at most 14 bytes, got {len(telegram_data)} bytes"
                    )

            case RORG.RORG_MSC:
                if len(telegram_data) < 1:
                    raise ERP1ParseError(
                        f"MSC telegram data must be at least 1 byte, got {len(telegram_data)} bytes"
                    )
                if len(telegram_data) > 14:
                    raise ERP1ParseError(
                        f"MSC telegram data must be at most 14 bytes, got {len(telegram_data)} bytes"
                    )

        # determine sender address
        try:
            s = Address.from_bytelist(data[-5:-1])
        except ValueError:
            raise ERP1ParseError(
                f"Invalid sender address in ERP1 telegram: {data[-5:-1].hex().upper()}"
            )

        # determine if sender is EURID or Base ID
        if s.is_eurid():
            sender = EURID.from_number(s.to_number())
        elif s.is_base_address():
            sender = BaseAddress.from_number(s.to_number())
        else:
            raise ERP1ParseError(f"Invalid sender address: {sender}")

        status = data[-1]

        # parse optional
        sub_tel_num = opt[0] if len(opt) > 0 else None

        destination_bytes = opt[1:5] if len(opt) > 4 else None
        d = Address.from_bytelist(destination_bytes) if destination_bytes else None

        if d is not None and d.is_broadcast():
            destination = BroadcastAddress()
        elif d is not None and d.is_eurid():
            destination = EURID.from_number(d.to_number())

        dBm = opt[5] if len(opt) > 5 else None
        sec_level = opt[6] if len(opt) > 6 else None

        return cls(
            rorg=rorg,
            telegram_data=telegram_data,
            sender=sender,
            status=status,
            sub_tel_num=sub_tel_num,
            dBm=dBm,
            sec_level=sec_level,
            destination=destination,
        )
