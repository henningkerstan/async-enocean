import asyncio
from dataclasses import dataclass, field
import logging
from time import time

from ..eep.message import EEPMessage
from ..eep.profile import CapabilityFactory
from .capability import Capability
from .observable import Observable
from .state_change import EntityStateChange, EntityStateChangeSource

# Watchdog timeout in seconds to detect when cover movement has stopped
COVER_WATCHDOG_TIMEOUT = 1.5

_logger = logging.getLogger(__name__)


@dataclass
class CoverCapability(Capability):
    """Capability that emits position and angle updates for blinds/cover devices."""

    _previous_position: int | None = field(default=None, init=False, repr=False)
    """Track previous position to derive cover state from movement."""

    _current_cover_state: str | None = field(default=None, init=False, repr=False)
    """Track the current cover state to avoid redundant state change emissions."""

    _watchdog_task: asyncio.Task | None = field(default=None, init=False, repr=False)
    """Watchdog task to detect when cover movement has stopped."""

    def _decode_impl(self, message: EEPMessage) -> None:
        if not message.values:
            return

        if message.message_type is None or message.message_type.id != 4:
            return

        current_time = time()

        pos_entity = message.entities.get(Observable.POSITION)
        ang_entity = message.entities.get(Observable.ANGLE)

        pos_value = pos_entity.value if pos_entity else None
        ang_value = ang_entity.value if ang_entity else None

        values: dict = {}

        if pos_value is not None:
            values[Observable.POSITION] = pos_value

            # Derive cover state from position changes
            cover_state = self._derive_cover_state(pos_value)
            if cover_state is not None:
                values[Observable.COVER_STATE] = cover_state
                self._current_cover_state = cover_state

                # Restart watchdog timer if cover is moving
                if cover_state in ("opening", "closing"):
                    self._restart_watchdog()

                if cover_state == "stopped":
                    # If we receive a stopped state from the message, cancel the watchdog
                    if (
                        self._watchdog_task is not None
                        and not self._watchdog_task.done()
                    ):
                        self._watchdog_task.cancel()
            self._previous_position = pos_value

        if ang_value is not None:
            values[Observable.ANGLE] = ang_value

        if values:
            self._emit(
                EntityStateChange(
                    device_id=self.device_address,
                    entity_id="cover",
                    values=values,
                    timestamp=current_time,
                    source=EntityStateChangeSource.TELEGRAM,
                )
            )

    def _restart_watchdog(self) -> None:
        """Cancel existing watchdog and start a new one."""
        if self._watchdog_task is not None and not self._watchdog_task.done():
            self._watchdog_task.cancel()
        self._watchdog_task = asyncio.create_task(self._watchdog_timer())

    async def _watchdog_timer(self) -> None:
        """Watchdog timer that emits stopped state after timeout."""
        try:
            await asyncio.sleep(COVER_WATCHDOG_TIMEOUT)
            # Timeout elapsed, emit stopped state
            self._emit(
                EntityStateChange(
                    device_id=self.device_address,
                    entity_id="cover",
                    values={Observable.COVER_STATE: "stopped"},
                    timestamp=time(),
                    source=EntityStateChangeSource.TIMER,
                )
            )
            self._current_cover_state = "stopped"
        except asyncio.CancelledError:
            pass  # Timer was cancelled due to new message

    def stop(self) -> None:
        """Stop the watchdog task."""
        if self._watchdog_task is not None and not self._watchdog_task.done():
            self._watchdog_task.cancel()

    def _derive_cover_state(self, current_pos: int) -> str | None:
        """Derive cover state from current position and previous position."""

        if current_pos == 0:
            return "open"
        elif current_pos == 100:
            return "closed"

        if self._previous_position is None:
            # First message, determine state from absolute position
            return None  # Unknown state until we see a change, or we can infer from absolute position

        # Position changed, determine direction of movement
        if current_pos > self._previous_position:
            return "closing"
        elif current_pos < self._previous_position:
            return "opening"
        else:
            return "stopped"  # No change in position, state remains the same


def cover_factory() -> CapabilityFactory:
    """Return a ``CapabilityFactory`` that creates a ``CoverCapability``."""
    return CapabilityFactory(
        factory=lambda addr, cb: CoverCapability(
            device_address=addr, on_state_change=cb
        ),
    )
