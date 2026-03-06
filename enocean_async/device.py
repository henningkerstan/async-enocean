from dataclasses import dataclass, field

from .address import EURID, BaseAddress, SenderAddress
from .eep.id import EEP
from .semantics.observers.observer import Observer


@dataclass
class Device:
    """Representation of an EnOcean device."""

    address: EURID | BaseAddress
    eep: EEP
    name: str
    sender: SenderAddress | None = None
    telegrams_received: int = 0
    capabilities: list[Observer] = field(default_factory=list)
