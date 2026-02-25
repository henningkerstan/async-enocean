from dataclasses import dataclass, field
import math
from typing import Any, Callable

from .id import EEP

type TelegramRawValues = dict[str, int]
type ScaleFunction = Callable[[TelegramRawValues], float]
type UnitFunction = Callable[[TelegramRawValues], str]

# Type aliases for capability factories, semantic resolvers, and command encoders.
# Using Any to avoid circular imports (capabilities/ imports from eep/).
type SemanticResolver = Callable[[dict[str, Any]], Any | None]
type CapabilityFactory = Callable[[Any, Any], Any]
type CommandEncoder = Callable[[Any], Any]  # DeviceCommand → EEPMessage


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

    range_min: int = 0
    """Minimum value of the data field's range."""

    range_max: int | None = None
    """Maximum value of the data field's range, defaulting to the maximum representable by the given size in bits (e.g. 2^size - 1)."""

    scale_min_fn: ScaleFunction = lambda _: 0.0
    """Function to compute scale_min based on message values. Defaults to constant 0.0."""

    scale_max_fn: ScaleFunction | None = None
    """Function to compute scale_max based on message values. Defaults to constant 0.0."""

    unit_fn: UnitFunction = lambda _: ""
    """Function to compute unit based on message values. Defaults to empty string."""

    range_enum: dict[int, str] | None = None
    """Enumeration of possible values for the data field, if applicable."""

    observable_uid: str | None = None
    """Semantic entity UID to which this field's decoded value is propagated (e.g. 'temperature', 'illumination').
    When set, EEPHandler copies msg.values[field.id] → msg.values[observable_uid] after decoding."""

    def __post_init__(self):
        if self.range_enum:
            # If an enumeration is provided, range_min and range_max should be derived from the enum keys
            enum_keys = self.range_enum.keys()
            self.range_min = min(enum_keys)
            # Use setter for validation
            self.range_max = max(enum_keys)
        else:
            # If no enumeration, ensure range_max is set based on size if not provided
            if self.range_max is None or self.range_max > (1 << self.size) - 1:
                self.range_max = (1 << self.size) - 1

        if self.scale_max_fn is None:
            self.scale_max_fn = lambda _: float(self.range_max)


@dataclass
class EEPTelegram:
    """An EEP telegram represents a specific type of message defined within an EEP, which may have its own structure and data fields."""

    name: str | None
    """Human-readable name for the telegram, describing its purpose or function."""

    datafields: list[EEPDataField] = field(default_factory=list)
    """List of data fields within the telegram, including the CMD selector field if applicable."""

    @property
    def byte_size(self) -> int:
        """Minimum number of bytes required to hold all data fields (including the CMD field if present)."""
        max_bit = max((f.offset + f.size for f in self.datafields), default=0)
        return math.ceil(max_bit / 8)


@dataclass
class EEPSpecification:
    """A full specification of an EnOcean Equipment Profile (EEP). This contains all information to fully de- and encode messages according to the EEP."""

    eep: EEP
    """Unique identifier for the EEP."""

    name: str
    """Human-readable name/description for the EEP."""

    cmd_size: int = 0
    """Size of the telegram's command/message identifier in bits. If zero, there is only one telegram type."""

    cmd_offset: int | None = None
    """Bit offset of the telegram's command/message identifier within the EEP; either measured from left (if cmd_offset is non-negative) or from right (if cmd_offset is negative)."""

    telegrams: dict[int, EEPTelegram] = field(default_factory=dict)
    """Dictionary of telegrams defined for this EEP, keyed by their command/message identifier, each with its own structure and data fields."""

    semantic_resolvers: dict[str, SemanticResolver] = field(default_factory=dict)
    """Dict mapping observable_uid → resolver function. Each resolver receives the full decoded values dict
    and returns a single EEPMessageValue (or None) to be stored under that observable_uid key."""

    capability_factories: list[CapabilityFactory] = field(default_factory=list)
    """Ordered list of capability factory callables. Each factory takes (device_address, on_state_change)
    and returns a Capability instance. MetaDataCapability is always prepended by the gateway."""

    command_encoders: dict[str, CommandEncoder] = field(default_factory=dict)
    """Dict mapping ActionUID → encoder function. Each encoder takes a DeviceCommand and returns
    an EEPMessage with message_type.id set and values filled with raw field values (field_id → raw int).
    The gateway sets message.sender and message.destination before calling EEPHandler.encode()."""


@dataclass
class SimpleProfileSpecification(EEPSpecification):
    """Simpler variant for profiles with a single telegram type (cmd_size=0, no telegram selector)."""

    def __init__(
        self,
        eep: EEP,
        name: str,
        datafields: list[EEPDataField],
        semantic_resolvers: dict[str, SemanticResolver] | None = None,
        capability_factories: list[CapabilityFactory] | None = None,
        command_encoders: dict[str, CommandEncoder] | None = None,
    ):
        """Initialize a single-telegram EEP.

        Args:
            eep: Unique identifier for the EEP.
            name: Human-readable name/description.
            datafields: List of data fields in the unique telegram that is defined for this EEP.
            semantic_resolvers: Optional dict of observable_uid → resolver for multi-field combinations.
            capability_factories: Optional list of capability factory callables.
            command_encoders: Optional dict of ActionUID → encoder callables.
        """

        super().__init__(
            eep=eep,
            name=name,
            cmd_size=0,
            cmd_offset=None,
            telegrams={0: EEPTelegram(name=None, datafields=datafields)},
            semantic_resolvers=semantic_resolvers or {},
            capability_factories=capability_factories or [],
            command_encoders=command_encoders or {},
        )
