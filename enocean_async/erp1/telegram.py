from dataclasses import dataclass
from enum import IntEnum

from enocean_async.eep.manufacturer import Manufacturer

from ..address import EURID, Address, BaseAddress, BroadcastAddress
from ..eep.id import EEP
from ..esp3.packet import ESP3Packet, ESP3PacketType
from .errors import ERP1ParseError
from .rorg import RORG


class HashAlgorithm(IntEnum):
    Checksum = 0
    CRC8 = 1


class RepeaterCount(IntEnum):
    Original = 0x0
    OnceRepeated = 0x1
    TwiceRepeated = 0x2
    Invalid3 = 0x3
    Invalid4 = 0x4
    Invalid5 = 0x5
    Invalid6 = 0x6
    Invalid7 = 0x7
    Invalid8 = 0x8
    Invalid9 = 0x9
    InvalidA = 0xA
    InvalidB = 0xB
    InvalidC = 0xC
    InvalidD = 0xD
    InvalidE = 0xE
    ShallNotBeRepeated = 0xF


@dataclass
class ERP1Telegram:
    rorg: RORG
    telegram_data: bytes
    sender: EURID | BaseAddress
    status: int = 0x00

    sub_tel_num: int | None = 0x03
    rssi: int | None = 0xFF
    sec_level: int | None = None
    destination: EURID | BroadcastAddress | None = None

    def data_byte(self, index: int) -> int:
        """Get the byte in the telegram data at the given index, counting from the end of the telegram data (as in the EEP specification).

        Thus, data_byte(i) = telegram_data[len(telegram_data) - 1 - i].
        """
        if index < 0 or index >= len(self.telegram_data):
            raise IndexError("Telegram data index out of range")
        return self.telegram_data[len(self.telegram_data) - 1 - index]

    def bitstring_raw_value(self, offset: int = 0, size: int = 1) -> int:
        """Extract an integer value from a bitstring within the telegram data given by the offset and size in bits (as in the EEP specification)."""

        total_bits = 8 * len(self.telegram_data)

        if offset < 0 or size < 1 or offset + size > total_bits:
            raise ValueError("Invalid offset or length for raw_value")

        # convert the telegram data to a single integer (treating the bytes as a big-endian bitstring)
        data_bits = int.from_bytes(self.telegram_data, "big")

        # calculate how many bits we need to shift right to get the desired bits at the least significant position
        shift = total_bits - (offset + size)

        # create a mask with exactly 'size' bits set to 1 (by shifting 1 left 'size' times and subtracting 1)
        mask = (1 << size) - 1

        # shift right and apply the mask to extract the desired bits
        return (data_bits >> shift) & mask

    def set_bitstring_raw_value(
        self, offset: int = 0, size: int = 1, value: int = 0
    ) -> None:
        """Set an integer value in a bitstring within the telegram data given by the offset and size in bits (as in the EEP specification)."""

        total_bits = 8 * len(self.telegram_data)

        if offset < 0 or size < 1 or offset + size > total_bits:
            raise ValueError("Invalid offset or length for raw_value")

        max_value = (1 << size) - 1
        if value < 0 or value > max_value:
            raise ValueError(f"Value must be between 0 and {max_value} for size {size}")

        # convert the telegram data to a single integer (treating the bytes as a big-endian bitstring)
        data_bits = int.from_bytes(self.telegram_data, "big")

        # calculate how many bits we need to shift right to get the desired bits at the least significant position
        shift = total_bits - (offset + size)

        # create a mask with exactly 'size' bits set to 1 (by shifting 1 left 'size' times and subtracting 1), then shift it to the correct position
        mask = ((1 << size) - 1) << shift

        # clear the bits at the desired position and set them to the new value
        data_bits = (data_bits & ~mask) | ((value << shift) & mask)

        # convert back to bytes and update telegram_data
        self.telegram_data = data_bits.to_bytes(len(self.telegram_data), "big")

    def bitstring_scaled_value(
        self,
        offset: int = 0,
        size: int = 1,
        range_min: int = 0,
        range_max: int = 1,
        scale_min: float = 0.0,
        scale_max: float = 1.0,
    ) -> float:
        """Extract a scaled float value from the telegram data.

        This calculation is given in the EEP specification.
        """

        if range_max == range_min:
            raise ValueError("range_max must differ from range_min")

        if scale_max <= scale_min:
            raise ValueError("scale_max must be greater than scale_min")

        # maximum value that can be represented with 'size' bits is 2^size - 1; due to the parameter checks in bitstring_raw_value, size > 0, hence max_raw >= 1
        max_raw = (1 << size) - 1

        if max(range_min, range_max) > max_raw:
            raise ValueError(f"range min/max cannot exceed {max_raw} for size {size}")

        multiplier = (scale_max - scale_min) / (range_max - range_min)

        raw_value = self.bitstring_raw_value(offset, size)

        return multiplier * (raw_value - range_min) + scale_min

    def __repr__(self) -> str:
        return (
            f"ERP1Telegram(sender={self.sender.to_string()}, RORG={self.rorg.simple_name}, destination={self.destination.to_string() if self.destination else '*'}, "
            f"telegram_data={self.telegram_data.hex().upper()}, "
            f"status=0x{self.status:02X} (hash function: {self.hash_function}, repeater count: {self.repeater_count}), "
            f"sub_tel_num={self.sub_tel_num}, "
            f"rssi={self.rssi}, "
            f"sec_level={self.sec_level})"
        )

    @property
    def is_learning_telegram(self) -> bool:
        """Check if the telegram is a learning telegram (only for 1BS and 4BS telegrams - for other RORGs, will return False)."""

        match self.rorg:
            case RORG.RORG_1BS:
                # for 1BS telegrams, the learning bit is on offset 4
                return self.bitstring_raw_value(4, 1) == 0

            case RORG.RORG_4BS:
                # for 4BS telegrams, the learning bit is on offset 28
                return self.bitstring_raw_value(28, 1) == 0

            case _:
                # for other RORGs, there is no learning bit defined in the specification, so we assume it's not a learning telegram
                return False

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

        destination = None
        if d is not None and d.is_broadcast():
            destination = BroadcastAddress()
        elif d is not None and d.is_eurid():
            destination = EURID.from_number(d.to_number())

        rssi = opt[5] if len(opt) > 5 else None
        sec_level = opt[6] if len(opt) > 6 else None

        return cls(
            rorg=rorg,
            telegram_data=telegram_data,
            sender=sender,
            status=status,
            sub_tel_num=sub_tel_num,
            rssi=rssi,
            sec_level=sec_level,
            destination=destination,
        )

    def to_esp3(self) -> ESP3Packet:
        data = (
            bytes([self.rorg])
            + self.telegram_data
            + bytes(self.sender.to_bytelist())
            + bytes([self.status])
        )
        optional = bytes()
        optional += (
            bytes([self.sub_tel_num]) if self.sub_tel_num is not None else bytes([0x03])
        )
        optional += (
            bytes(self.destination.to_bytelist())
            if self.destination is not None
            else bytes(BroadcastAddress().to_bytelist())
        )
        optional += bytes([self.rssi]) if self.rssi is not None else bytes([0xFF])
        optional += (
            bytes([self.sec_level]) if self.sec_level is not None else bytes([0x00])
        )

        return ESP3Packet(
            packet_type=ESP3PacketType.RADIO_ERP1, data=data, optional=optional
        )

    @property
    def hash_function(self) -> HashAlgorithm:
        """
        Return the HashAlgorithm indicated by bit 7 of self.status.
        Extracts bit 7 from the status byte and returns the corresponding
        HashAlgorithm enum value.
        """

        return HashAlgorithm((self.status >> 7) & 1)

    @property
    def repeater_count(self) -> RepeaterCount:
        """Return lower 4 bits (last 4 bits) of the 8-bit status byte, interpreted as per ERP1 spec as repeater count."""
        return RepeaterCount(self.status & 0x0F)


class FourBSTeachInVariation(IntEnum):
    UnidirectionalProfileLess = 0
    UnidirectionalWithProfileOrBidirectional = 1


@dataclass
class FourBSTeachInTelegram:
    teach_in_variation: FourBSTeachInVariation = 1
    eep: EEP | None = None

    @classmethod
    def from_erp1(cls, erp1: ERP1Telegram) -> "FourBSTeachInTelegram":
        if erp1.rorg != RORG.RORG_4BS:
            raise ValueError("Wrong RORG.")

        if not erp1.is_learning_telegram:
            raise ValueError("Not a learning telegram")

        teach_in_variation = FourBSTeachInVariation(erp1.bitstring_raw_value(24, 1))
        eep: EEP | None = None

        if (
            teach_in_variation
            == FourBSTeachInVariation.UnidirectionalWithProfileOrBidirectional
        ):
            func = erp1.bitstring_raw_value(0, 6)
            type_ = erp1.bitstring_raw_value(6, 7)
            manufacturer_id = erp1.bitstring_raw_value(13, 11)
            manufacturer = Manufacturer(manufacturer_id)
            eep = EEP(0xA5, func, type_, manufacturer)

        return cls(teach_in_variation=teach_in_variation, eep=eep)
