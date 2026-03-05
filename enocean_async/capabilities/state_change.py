from dataclasses import dataclass, field
from enum import IntEnum
from time import time
from typing import Any, Callable

from ..address import SenderAddress
from .observable import Observable

type EntityStateChangeCallback = Callable[["EntityStateChange"], None]


class EntityStateChangeSource(IntEnum):
    TELEGRAM = 0
    TIMER = 1


@dataclass
class EntityStateChange:
    """A semantic update emitted by a Capability for one entity.

    ``values`` contains all observable values reported in this telegram (or timer event).
    For a partial update (e.g. a D2-01 measurement response carrying only POWER),
    ``values`` will contain only the observables that were present.
    The unit for any value is always ``observable.unit``.
    """

    device_id: SenderAddress
    entity_id: str
    values: dict[Observable, Any]
    timestamp: float = field(default_factory=time)
    time_elapsed: float = 0
    source: EntityStateChangeSource = EntityStateChangeSource.TELEGRAM
