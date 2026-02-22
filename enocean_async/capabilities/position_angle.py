import asyncio
from dataclasses import dataclass, field
from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .state_change import StateChange, StateChangeSource

POSITION_UID = "POS"
ANGLE_UID = "ANG"
COVER_STATE_UID = "COVER_STATE"

# Watchdog timeout in seconds to detect when cover movement has stopped
COVER_WATCHDOG_TIMEOUT = 1.5


@dataclass
class PositionAngleCapability(Capability):
    """Capability that emits position and angle updates for D2-05-00."""

    _previous_position: int | None = field(default=None, init=False, repr=False)
    """Track previous position to derive cover state from movement."""

    _current_cover_state: str | None = field(default=None, init=False, repr=False)
    """Track the current cover state to avoid redundant state change emissions."""

    _watchdog_task: asyncio.Task | None = field(default=None, init=False, repr=False)
    """Watchdog task to detect when cover movement has stopped."""

    def _decode_impl(self, message: EEPMessage) -> None:
        if not message.values:
            return
        if message.eepid is None or message.eepid.to_string() != "D2-05-00":
            return

        if message.message_type.id != 4:
            print(
                f"Received unsupported message type {message.message_type} for PositionAngleCapability"
            )
            return

        current_time = time()

        pos_value = message.values.get("POS")
        ang_value = message.values.get("ANG")

        pos_raw = pos_value.raw if pos_value else None
        ang_raw = ang_value.raw if ang_value else None

        if pos_raw is not None:
            self._emit(
                StateChange(
                    device_address=self.device_address,
                    entity_uid=POSITION_UID,
                    value=pos_raw,
                    timestamp=current_time,
                    source=StateChangeSource.TELEGRAM,
                )
            )

            # Derive cover state from position changes
            cover_state = self._derive_cover_state(pos_raw)
            if cover_state is not None:
                self._emit(
                    StateChange(
                        device_address=self.device_address,
                        entity_uid=COVER_STATE_UID,
                        value=cover_state,
                        timestamp=current_time,
                        source=StateChangeSource.TELEGRAM,
                    )
                )
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
            self._previous_position = pos_raw

        if ang_raw is not None:
            self._emit(
                StateChange(
                    device_address=self.device_address,
                    entity_uid=ANGLE_UID,
                    value=ang_raw,
                    timestamp=current_time,
                    source=StateChangeSource.TELEGRAM,
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
                StateChange(
                    device_address=self.device_address,
                    entity_uid=COVER_STATE_UID,
                    value="stopped",
                    timestamp=time(),
                    source=StateChangeSource.TIMER,
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
