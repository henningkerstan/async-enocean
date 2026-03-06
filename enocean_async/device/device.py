from dataclasses import dataclass, field

from ..address import EURID, BaseAddress, SenderAddress
from ..capabilities.observers.base import Observer
from ..eep.id import EEP


@dataclass
class Device:
    """Representation of an EnOcean device."""

    address: EURID | BaseAddress
    eep: EEP
    name: str
    sender: SenderAddress | None = None
    telegrams_received: int = 0
    capabilities: list[Observer] = field(default_factory=list)
