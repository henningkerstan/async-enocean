from dataclasses import dataclass


@dataclass
class EEPID:
    """Representation of an EnOcean Equipment Profile (EEP)."""

    def __init__(
        self, rorg: int, func: int, type_: int, manufacturer_id: int | None = None
    ) -> None:
        """Construct an EnOcean Equipment Profile."""
        self.rorg = rorg
        self.func = func
        self.type = type_
        self.manufacturer_id = manufacturer_id  # see https://www.enocean.com/wp-content/uploads/application-notes/new_AN514_EnOcean_Link_Profiles.pdf

    @classmethod
    def from_string(cls, eep_string: str) -> "EEPID":
        """Create an EEP instance from a dash-separated string."""
        parts = eep_string.strip().split("-")
        if len(parts) != 3:
            raise ValueError("Wrong format.")
        rorg = int(parts[0], 16)
        func = int(parts[1], 16)
        type_ = int(parts[2], 16)
        return cls(rorg, func, type_)

    def to_string(self) -> str:
        """Return the EEP as a dash-separated string."""
        return f"{self.rorg:02X}-{self.func:02X}-{self.type:02X}"

    def __repr__(self) -> str:
        return f"EEP({self.to_string()}{'.' + str(self.manufacturer_id) if self.manufacturer_id is not None else ''})"
