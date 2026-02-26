"""Typed actions for cover / blind control (D2-05-00)."""

from dataclasses import dataclass
from typing import ClassVar

from .action import Action
from .action_uid import ActionUID


@dataclass
class SetCoverPositionAction(Action):
    """Move a cover to a specific vertical position and rotation angle.

    Both ``position`` and ``angle`` are raw EEP values (0–127, where 127 = 100%).
    """

    action_uid: ClassVar[str] = ActionUID.SET_COVER_POSITION

    position: int
    """Vertical position: 0–127 (maps to 0–100 %)."""

    angle: int = 0
    """Rotation angle: 0–127 (maps to 0–100 %)."""

    repositioning_mode: int = 0
    """REPO field: 0 = directly to target, 1 = up first, 2 = down first."""

    lock_mode: int = 0
    """LOCK field: 0 = no change, 1 = set blockage, 2 = set alarm, 7 = unblock."""

    channel: int = 15
    """CHN field: 0–3 for a specific channel, 15 = all channels."""


@dataclass
class StopCoverAction(Action):
    """Stop cover movement immediately."""

    action_uid: ClassVar[str] = ActionUID.STOP_COVER

    channel: int = 15
    """CHN field: 0–3 for a specific channel, 15 = all channels."""


@dataclass
class QueryCoverPositionAction(Action):
    """Request the current position and angle from a cover actuator."""

    action_uid: ClassVar[str] = ActionUID.QUERY_COVER_POSITION

    channel: int = 15
    """CHN field: 0–3 for a specific channel, 15 = all channels."""
