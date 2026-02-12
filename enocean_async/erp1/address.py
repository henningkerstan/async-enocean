"""EnOcean address classes for Home Assistant integration.

This module provides the EnOceanAddress class for handling EnOcean four byte (32 bit) addresses,
including parsing, validation, and conversion between integer and string formats.

For more information on EnOcean addressing, see
  - https://www.enocean-alliance.org/wp-content/uploads/2021/03/EURID-v1.2.pdf
  - https://www.enocean.com/de/faq-knowledge-base/what-is-difference-between-base-id-and-chip-id/
"""


class Address:
    """Implementation of the EnOcean four byte (32 bit) addresses to identify devices.

    # A note about sending addresses
    Each EnOcean device has a unique ID (called *Chip ID*) which it can use
    for sending telegrams. Alternatively, EnOcean gateways can also use a range
    of 128 consecutive addresses for sending, starting at the so-called
    _Base ID_ of the gateway. A gateway's *Base ID* is a four byte address in
    the range FF:80:00:00 to FF:FF:FF:80. The Base ID is a predefined address,
    which can be changed by the user only a few times (at most 10 times for the
    TCM310 chip). The allowed addresses for sending a telegram are thus the
    following 129 addresses:

    - Chip ID (= device ID),
    - Base ID,
    - Base ID + 1,
    - Base ID + 2,
    - ...
    - Base ID + 126, and
    - Base ID + 127.

    All other addresses must not be used for sending (and will be rejected by
    official EnOcean modules). This is meant as a basic security feature. Have a
    look at the EnOcean [knowledge base](https://www.enocean.com/de/faq-knowledge-base/what-is-difference-between-base-id-and-chip-id/) for the official explanation of the differences between chip ID and base IDs.

    Base IDs are always in the range FF:80:00:00 to FF:FF:FF:80.
    """

    def __init__(self, from_value: int | str) -> None:
        """Initialize the EnOceanID from an integer or string."""
        numeric_id = -1
        if isinstance(from_value, str):
            numeric_id = Address.from_string(from_value).to_number()
        if isinstance(from_value, int):
            numeric_id = from_value
        if not isinstance(numeric_id, int):
            raise TypeError(
                "ID must be an integer or a hex string that can be converted to an integer."
            )
        if numeric_id < 0:
            raise ValueError("ID out of bounds (must be at least 0).")
        if numeric_id > 0xFFFFFFFF:
            raise ValueError(
                "ID out of bounds (must be smaller than 0xFFFFFFFF = 4294967295)."
            )
        self.__address = numeric_id

    @classmethod
    def from_number(cls, id: int) -> "Address":
        """Create an EnOceanID instance from an integer."""
        return cls(id)

    @classmethod
    def from_string(cls, id_string: str) -> "Address":
        """Create an EnOceanID instance from a colon-separated string."""
        if not id_string:
            raise ValueError("from_string called with undefined argument")
        parts = id_string.strip().split(":")
        if len(parts) != 4:
            raise ValueError("Wrong format.")
        hex_string = "".join(part.zfill(2) for part in parts)
        return cls(int(hex_string, 16))

    @classmethod
    def from_bytelist(cls, byte_list: list[int]) -> "Address":
        """Create an EnOceanID instance from a list of 4 bytes."""
        if len(byte_list) != 4:
            raise ValueError("Byte list must have exactly 4 elements.")
        numeric_id = (
            (byte_list[0] << 24)
            | (byte_list[1] << 16)
            | (byte_list[2] << 8)
            | byte_list[3]
        )
        return cls(numeric_id)

    @classmethod
    def broadcast(cls) -> "Address":
        """Return the broadcast ID (FF:FF:FF:FF)."""
        return cls(0xFFFFFFFF)

    @classmethod
    def validate_string(cls, id_string: str) -> bool:
        """Check that the supplied string is a valid EnOcean address."""
        parts = id_string.strip().split(":")

        if len(parts) != 4:
            return False

        hex_string = "".join(part.zfill(2) for part in parts)
        try:
            int(hex_string, 16)
        except ValueError:
            return False

        return True

    def to_number(self) -> int:
        """Return the EnOcean address as integer."""
        return self.__address

    def to_string(self) -> str:
        """Return the EnOcean address as colon-separated hex string."""
        s = f"{self.__address:08X}"
        return f"{s[0:2]}:{s[2:4]}:{s[4:6]}:{s[6:8]}"

    def to_json(self) -> str:
        """Return the EnOcean address as JSON string."""
        return self.to_string()

    def to_bytelist(self) -> list[int]:
        """Return the EnOcean address as list of bytes."""
        return [
            (self.__address >> 24) & 0xFF,
            (self.__address >> 16) & 0xFF,
            (self.__address >> 8) & 0xFF,
            self.__address & 0xFF,
        ]

    def is_eurid(self) -> bool:
        """Check if the address is a EURID (EnOcean Unique Radio Identifier)."""
        return 0x00000000 <= self.__address <= 0xFF7FFFFF

    def is_base_address(self) -> bool:
        """Check if the address is a Base address."""
        return 0xFF800000 <= self.__address <= 0xFFFFFF80

    def is_broadcast(self) -> bool:
        """Check if the address is the broadcast address."""
        return self.__address == 0xFFFFFFFF

    def __str__(self) -> str:
        """Return the EnOcean address as string."""
        return self.to_string()

    def __hash__(self):
        return self.__address

    def __eq__(self, other):
        return self.__address == other.__address

    def __repr__(self) -> str:
        return f"EnOceanAddress({self.to_string()})"


class EURID(Address):
    """Representation of an EnOcean device address (EnOcean Unique Radio Identifier / EURID).

    Device addresses are in the range 00:00:00:00 to FF:7F:FF:FF.
    """

    def __init__(self, from_value: int | str) -> None:
        """Initialize the EnOcean device address from an integer or string."""
        numeric_address = -1
        if isinstance(from_value, str):
            numeric_address = Address.from_string(from_value).to_number()
        if isinstance(from_value, int):
            numeric_address = from_value
        if not isinstance(numeric_address, int):
            raise TypeError(
                "Address must be an integer or a hex string that can be converted to an integer."
            )
        if not (0x00000000 <= numeric_address <= 0xFF7FFFFF):
            raise ValueError(
                f"Device address must be in the range 00:00:00:00 to FF:7F:FF:FF, but is {numeric_address:08X}."
            )
        super().__init__(numeric_address)

    def __repr__(self) -> str:
        return f"EURID({self.to_string()})"


class BaseAddress(Address):
    """Representation of an EnOcean base address.

    Base addresses are in the range FF:80:00:00 to FF:FF:FF:80.
    """

    def __init__(self, from_value: int | str) -> None:
        """Initialize the EnOcean base address from an integer or string."""
        numeric_address = -1
        if isinstance(from_value, str):
            numeric_address = Address.from_string(from_value).to_number()
        if isinstance(from_value, int):
            numeric_address = from_value
        if not isinstance(numeric_address, int):
            raise TypeError(
                "Address must be an integer or a hex string that can be converted to an integer."
            )
        if not (0xFF800000 <= numeric_address <= 0xFFFFFF80):
            raise ValueError(
                "Base address must be in the range FF:80:00:00 to FF:FF:FF:80."
            )
        super().__init__(numeric_address)

    def __repr__(self) -> str:
        return f"EnOceanBaseAddress({self.to_string()})"


class BroadcastAddress(Address):
    """Representation of the EnOcean broadcast address (FF:FF:FF:FF)."""

    def __init__(self) -> None:
        """Initialize the EnOcean broadcast address."""
        super().__init__(0xFFFFFFFF)

    def __repr__(self) -> str:
        return "EnOceanBroadcastAddress(FF:FF:FF:FF)"
