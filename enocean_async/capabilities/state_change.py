from dataclasses import dataclass, field
from enum import IntEnum
from time import time
from typing import Callable

from ..address import SenderAddress

type StateChangeCallback = Callable[[StateChange], None]


class StateChangeSource(IntEnum):
    TELEGRAM = 0
    TIMER = 1


@dataclass
class StateChange:
    """A semantic update emitted by a Capability."""

    device_address: SenderAddress
    observable_uid: str
    value: any
    unit: str | None = None
    channel: int | None = None
    timestamp: float = field(default_factory=time)
    time_elapsed: float = 0
    source: StateChangeSource = StateChangeSource.TELEGRAM
