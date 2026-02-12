from dataclasses import dataclass
from typing import Literal

from ..message import EEPMessage


@dataclass
class F602XXMessageButtonPressed(EEPMessage):
    button: Literal["a0", "a1", "b0", "b1", "ab0", "ab1", "a0b1", "a1b0"]


@dataclass
class F602XXMessageButtonsReleased(EEPMessage):
    pass
