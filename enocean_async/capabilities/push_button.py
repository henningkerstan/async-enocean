import asyncio
from dataclasses import dataclass, field
from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .state_change import StateChange, StateChangeSource

PUSHED = "pushed"
RELEASED = "released"
CLICK = "click"
DOUBLE_CLICK = "double-click"
HOLD = "hold"


@dataclass
class PushButtonCapability(Capability):
    """Base capability for button devices.

    Provides timing-based state machine behavior for:
    - pushed: Initial press event
    - click: Short press (< hold threshold)
    - hold: Long press - emitted immediately when threshold reached
    - released: Button released
    - double-click: Two clicks within double-click window
    """

    hold_threshold: float = 0.5  # Time to consider press as "hold"
    double_click_window: float = 0.4  # Max time between clicks for double-click
    release_timeout: float = 30.0  # Max time to wait for a release telegram (as te fallback if no release is received)

    _button_press_times: dict[str, float] = field(default_factory=dict)
    _last_click_times: dict[str, float] = field(default_factory=dict)
    _button_held: dict[str, bool] = field(default_factory=dict)
    _hold_tasks: dict[str, asyncio.Task] = field(default_factory=dict)
    _release_tasks: dict[str, asyncio.Task] = field(default_factory=dict)

    async def _emit_hold_event(self, button_id: str, press_time: float) -> None:
        """Emit hold event after threshold is reached."""
        await asyncio.sleep(self.hold_threshold)

        if button_id in self._button_press_times:
            duration = time() - press_time
            self._button_held[button_id] = True

            self._emit(
                StateChange(
                    device_address=self.device_address,
                    entity_uid=button_id,
                    value=HOLD,
                    timestamp=time(),
                    time_elapsed=duration,
                    source=StateChangeSource.TIMER,
                )
            )

    async def _emit_release_timeout(self, button_id: str, press_time: float) -> None:
        """Emit release event if no release telegram arrives within timeout."""
        await asyncio.sleep(self.release_timeout)

        if button_id not in self._button_press_times:
            return

        duration = time() - press_time

        if button_id in self._hold_tasks:
            self._hold_tasks[button_id].cancel()
            del self._hold_tasks[button_id]

        self._emit(
            StateChange(
                device_address=self.device_address,
                entity_uid=button_id,
                value=RELEASED,
                timestamp=time(),
                time_elapsed=duration,
                source=StateChangeSource.TIMER,
            )
        )

        if button_id in self._release_tasks:
            del self._release_tasks[button_id]

    def _button_pressed(self, button_id: str) -> None:
        """Handle a button press and emit a pushed event."""
        current_time = time()
        self._button_press_times[button_id] = current_time
        self._button_held[button_id] = False

        loop = asyncio.get_running_loop()

        # Start hold timer
        task = loop.create_task(self._emit_hold_event(button_id, current_time))
        self._hold_tasks[button_id] = task

        # Reset release timeout timer
        if button_id in self._release_tasks:
            self._release_tasks[button_id].cancel()
            del self._release_tasks[button_id]

        # Start new release timeout timer
        timeout_task = loop.create_task(
            self._emit_release_timeout(button_id, current_time)
        )
        self._release_tasks[button_id] = timeout_task

        self._emit(
            StateChange(
                device_address=self.device_address,
                entity_uid=button_id,
                value=PUSHED,
                timestamp=current_time,
                source=StateChangeSource.TELEGRAM,
            )
        )

    def _button_released(self, button_id: str, current_time: float) -> None:
        """Handle a button release and emit click/doubleclick/release events."""
        press_time = self._button_press_times.get(button_id)
        if press_time is None:
            self._emit(
                StateChange(
                    device_address=self.device_address,
                    entity_uid=button_id,
                    value=RELEASED,
                    timestamp=current_time,
                    source=StateChangeSource.TELEGRAM,
                )
            )
            return

        duration = current_time - press_time

        if button_id in self._hold_tasks:
            self._hold_tasks[button_id].cancel()
            del self._hold_tasks[button_id]

        if button_id in self._release_tasks:
            self._release_tasks[button_id].cancel()
            del self._release_tasks[button_id]

        was_held = self._button_held.get(button_id, False)

        if not was_held and duration < self.hold_threshold:
            last_click_time = self._last_click_times.get(button_id, 0)
            time_since_last_click = current_time - last_click_time

            if 0 < time_since_last_click <= self.double_click_window:
                self._emit(
                    StateChange(
                        device_address=self.device_address,
                        entity_uid=button_id,
                        value=DOUBLE_CLICK,
                        timestamp=current_time,
                        time_elapsed=duration,
                        source=StateChangeSource.TELEGRAM,
                    )
                )
                self._last_click_times[button_id] = 0
            else:
                self._emit(
                    StateChange(
                        device_address=self.device_address,
                        entity_uid=button_id,
                        value=CLICK,
                        timestamp=current_time,
                        time_elapsed=duration,
                        source=StateChangeSource.TELEGRAM,
                    )
                )
                self._last_click_times[button_id] = current_time

        self._emit(
            StateChange(
                device_address=self.device_address,
                entity_uid=button_id,
                value=RELEASED,
                timestamp=current_time,
                time_elapsed=duration,
                source=StateChangeSource.TELEGRAM,
            )
        )

        del self._button_press_times[button_id]
        if button_id in self._button_held:
            del self._button_held[button_id]

    def _decode_impl(self, message: EEPMessage) -> None:
        """Decode button messages into semantic state changes with timing."""
        raise NotImplementedError("Subclasses must implement the _decode_impl method.")


@dataclass
class F6_02_01_02PushButtonCapability(PushButtonCapability):
    """Button capability for F6-02-01/02 rocker switches.

    Handles R1/EB/R2/SA fields from F6-02-01 and F6-02-02 telegrams.
    """

    def _combine_button_ids(self, first_id: str, second_id: str) -> str:
        if "unknown" in (first_id, second_id):
            return "unknown"
        if first_id == second_id:
            return first_id
        pair = {first_id, second_id}
        if pair == {"a0", "b0"}:
            return "ab0"
        if pair == {"a1", "b1"}:
            return "ab1"
        if pair == {"a0", "b1"}:
            return "a0b1"
        if pair == {"a1", "b0"}:
            return "a1b0"
        return "".join(sorted(pair))

    def _decode_impl(self, message: EEPMessage) -> None:
        if not message.values:
            return

        if (
            message.eepid
            and message.eepid.to_string() in ["F6-02-01", "F6-02-02"]
            and "R1" in message.values
            and "EB" in message.values
            and "R2" in message.values
            and "SA" in message.values
        ):
            r1_raw, r1_val = message.values.get("R1", (None, None))
            eb_raw, eb_val = message.values.get("EB", (None, None))
            sa_raw, sa_val = message.values.get("SA", (None, None))
            r2_raw, r2_val = message.values.get("R2", (None, None))

            current_time = time()

            if eb_val == "pressed" and r1_val is not None:
                r1_id = r1_val
                r2_id = r2_val
                if sa_val == "2nd action valid" and r2_val is not None:
                    combo_id = self._combine_button_ids(r1_id, r2_id)
                    self._button_pressed(button_id=combo_id)
                else:
                    self._button_pressed(button_id=r1_id)
            elif eb_val == "released":
                for button_id in list(self._button_press_times.keys()):
                    self._button_released(
                        button_id=button_id, current_time=current_time
                    )
