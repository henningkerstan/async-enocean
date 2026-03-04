"""Typed commands for central command / dimmer control (A5-38-08)."""

from dataclasses import dataclass
from typing import ClassVar

from .action import Action
from .command import Command


@dataclass
class Dim(Command):
    """Dim a light to a specific value."""

    action: ClassVar[Action] = Action.DIM

    dim_value: int
    """EDIM field: 0–255. Absolute range 0–100 % or relative -100 %–+100 % depending on ``relative``."""

    ramp_time: int = 0
    """RMP field: ramping time in seconds (0 = immediately)."""

    relative: bool = False
    """EDIMR field: False = absolute dimming value, True = relative."""

    store: bool = False
    """STR field: False = do not store final value, True = store."""

    switch_on: bool = True
    """SW field: False = switch off, True = switch on."""
