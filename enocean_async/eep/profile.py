from dataclasses import dataclass

from enocean_async.eep.id import EEPID


@dataclass
class EEPDataField:
    """An EEP data field represents a single data point within an EEP, such as a sensor value or a control command."""

    id: str
    """Unique identifier for the data field, typically a short string like 'R1', 'POS' etc."""

    name: str
    """Human-readable name for the data field, providing a descriptive label."""

    offset: int
    """Bit offset of the data field within the EEP."""

    size: int
    """Size of the data field in bits."""

    range_min: int | None = None
    """Minimum value of the data field's range."""

    range_max: int | None = None
    """Maximum value of the data field's range."""

    scale_min: float | None = None
    """Minimum value of the data field's scaled value."""

    scale_max: float | None = None
    """Maximum value of the data field's scaled value."""

    range_enum: dict[int, str] | None = None
    """Enumeration of possible values for the data field, if applicable."""

    unit: str | None = None
    """Unit of the data field, such as '°C' for temperature or '%' for humidity."""


@dataclass
class EEP:
    """Base class for EEP data."""

    id: EEPID
    """Unique identifier for the EEP."""

    name: str
    """Human-readable name/description for the EEP."""

    datafields: list[EEPDataField]
    """List of data fields within the EEP."""
