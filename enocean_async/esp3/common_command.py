from dataclasses import dataclass
from enum import IntEnum

from ..erp1.address import BaseAddress
from .packet import ESP3Packet, ESP3PacketType


class CommonCommandCode(IntEnum):
    """Common command codes for ESP3 packets."""

    CO_RD_VERSION = 3
    """Read the device version information"""

    CO_WR_IDBASE = 7
    """Set base ID"""

    CO_RD_IDBASE = 8
    """ Read ID range base address"""


@dataclass
class CommonCommandTelegram:
    """Common Command Telegram for ESP3 packets."""

    common_command_code: int
    common_command_data: bytes | None = None
    optional_data: bytes = None

    @classmethod
    def CO_RD_VERSION(cls) -> "CommonCommandTelegram":
        """Create a Common Command Telegram to read the device version information."""
        return cls(common_command_code=CommonCommandCode.CO_RD_VERSION)

    @classmethod
    def CO_RD_IDBASE(cls) -> "CommonCommandTelegram":
        """Create a Common Command Telegram to read the base ID."""
        return cls(common_command_code=CommonCommandCode.CO_RD_IDBASE)

    @classmethod
    def CO_WR_IDBASE(cls, id_base: BaseAddress) -> "CommonCommandTelegram":
        """Create a Common Command Telegram to set the base ID."""

        id_base_bytes = id_base.to_bytelist()
        return cls(
            common_command_code=CommonCommandCode.CO_WR_IDBASE,
            common_command_data=id_base_bytes,
        )

    def __post_init__(self):
        if self.optional_data is None:
            self.optional_data = b""

    def to_esp3_packet(self) -> ESP3Packet:
        data_size = (
            1 if self.common_command_data is None else len(self.common_command_data) + 1
        )
        data = bytearray(data_size)
        data[0] = self.common_command_code

        if self.common_command_data is not None:
            data[1:] = self.common_command_data

        return ESP3Packet(
            packet_type=ESP3PacketType.COMMON_COMMAND,
            data=bytes(data),
            optional=self.optional_data,
        )
