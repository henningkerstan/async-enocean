from dataclasses import dataclass, field
import math
from typing import Any, Callable

from ..capabilities.action import Action
from ..capabilities.observable import Observable
from .id import EEP


@dataclass(frozen=True)
class Entity:
    """A physical real-world sub-unit of a device (push button, relay channel, cover motor, sensor).

    Declared statically in the EEP specification. Each entity has a stable string ``id``
    within the device, a set of ``observables`` it reports, and a set of ``actions`` it accepts.
    A unique physical thing in the system is the pair ``(device_address, entity_id)``.
    """

    id: str
    observables: frozenset[Observable]
    actions: frozenset[Action] = field(default_factory=frozenset)


type TelegramRawValues = dict[str, int]
type ScaleFunction = Callable[[TelegramRawValues], float]
type UnitFunction = Callable[[TelegramRawValues], str]

# Type aliases for semantic resolvers and action encoders.
# Using Any to avoid circular imports (capabilities/ imports from eep/).
type SemanticResolver = Callable[[dict[str, Any]], Any | None]
type ActionEncoder = Callable[[Any], Any]  # Command → EEPMessage


@dataclass
class ObserverFactory:
    """Wraps an observer constructor for use in ``EEPSpecification.observers``.

    Entity metadata (observables, actions) is now declared separately via
    ``EEPSpecification.entities`` rather than on the factory itself.
    """

    factory: Callable[[Any, Any], Any]
    """Callable that takes ``(device_address, on_state_change)`` and returns an Observer."""

    def __call__(self, device_address: Any, on_state_change: Any) -> Any:
        return self.factory(device_address, on_state_change)


@dataclass
class DeviceDescriptor:
    """Setup-time description of what a device type exposes and accepts.

    Returned by ``EEPSpecification.device_descriptor()``.  An integration can obtain
    this immediately after calling ``gateway.add_device()`` — before any telegrams arrive
    — and use it to create all required platform entities.
    """

    eep: EEP

    entities: list[Entity]
    """All entities this device type exposes, including the three metadata entities
    (rssi, last_seen, telegram_count) always added by the gateway.
    """


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

    observable: Observable | None = None
    """Observable type to which this field's decoded value is propagated (e.g. Observable.TEMPERATURE).
    When set, EEPHandler copies msg.values[field.id] → msg.entities[observable] after decoding."""

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

    ecid_size: int = 0
    """Size of the telegram's extended command/message identifier in bits. If zero, there is only one telegram type."""

    ecid_offset: int | None = None
    """Bit offset of the telegram's extended command/message identifier within the EEP; either measured from left (if ecid_offset is non-negative) or from right (if ecid_offset is negative)."""

    telegrams: dict[int, EEPTelegram] = field(default_factory=dict)
    """Dictionary of telegrams defined for this EEP, keyed by their command/message identifier, each with its own structure and data fields."""

    semantic_resolvers: dict[Observable, SemanticResolver] = field(default_factory=dict)
    """Dict mapping Observable → resolver function. Each resolver receives the full decoded values dict
    and returns a single EEPMessageValue (or None) to be stored under that Observable key."""

    observers: list[ObserverFactory] = field(default_factory=list)
    """Ordered list of observer factory callables. Each factory takes (device_address, on_state_change)
    and returns an Observer instance. MetaDataObserver is always prepended by the gateway."""

    encoders: dict[Action, ActionEncoder] = field(default_factory=dict)
    """Dict mapping Action → encoder function. Each encoder takes a Command and returns
    an EEPMessage with message_type.id set and values filled with raw field values (field_id → raw int).
    The gateway sets message.sender and message.destination before calling EEPHandler.encode()."""

    entities: list[Entity] = field(default_factory=list)
    """Physical entities declared by this EEP — one per real-world sub-unit (push button,
    relay channel, sensor element, cover motor). Consumed by ``device_descriptor()``."""

    def device_descriptor(self) -> "DeviceDescriptor":
        """Return a setup-time descriptor of what this device type exposes and accepts.

        Combines ``self.entities`` with the three metadata entities (rssi, last_seen,
        telegram_count) that the gateway always prepends to every device.
        """
        _METADATA_ENTITIES = [
            Entity(id="rssi", observables=frozenset({Observable.RSSI})),
            Entity(id="last_seen", observables=frozenset({Observable.LAST_SEEN})),
            Entity(
                id="telegram_count", observables=frozenset({Observable.TELEGRAM_COUNT})
            ),
        ]
        return DeviceDescriptor(
            eep=self.eep,
            entities=self.entities + _METADATA_ENTITIES,
        )


@dataclass
class SimpleProfileSpecification(EEPSpecification):
    """Simpler variant for profiles with a single telegram type (cmd_size=0, no telegram selector)."""

    def __init__(
        self,
        eep: EEP,
        name: str,
        datafields: list[EEPDataField],
        semantic_resolvers: dict[Observable, SemanticResolver] | None = None,
        observers: list[ObserverFactory] | None = None,
        encoders: dict[Action, ActionEncoder] | None = None,
        entities: list[Entity] | None = None,
    ):
        """Initialize a single-telegram EEP.

        Args:
            eep: Unique identifier for the EEP.
            name: Human-readable name/description.
            datafields: List of data fields in the unique telegram that is defined for this EEP.
            semantic_resolvers: Optional dict of Observable → resolver for multi-field combinations.
            observers: Optional list of observer factory callables.
            encoders: Optional dict of Action → encoder callables.
            entities: Optional list of Entity declarations for this EEP.
        """

        super().__init__(
            eep=eep,
            name=name,
            cmd_size=0,
            cmd_offset=None,
            telegrams={0: EEPTelegram(name=None, datafields=datafields)},
            semantic_resolvers=semantic_resolvers or {},
            observers=observers or [],
            encoders=encoders or {},
            entities=entities or [],
        )
