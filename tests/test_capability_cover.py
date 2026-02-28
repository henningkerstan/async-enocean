"""Tests for CoverCapability.

Covers:
- POSITION StateChange emitted on every message with a position entity
- ANGLE StateChange emitted when angle entity is present
- _derive_cover_state: open (pos=0), closed (pos=100), opening, closing,
  stopped (no change), None on first message at mid-position
- Watchdog timer fires "stopped" after COVER_WATCHDOG_TIMEOUT seconds when
  the cover is moving (opening/closing)
- Watchdog is cancelled when a new message arrives
- Messages from a different sender are ignored (inherited from Capability)
- message_type.id must be 4; other IDs are silently ignored
"""

import asyncio

from enocean_async.address import EURID
from enocean_async.capabilities.observable_uids import ObservableUID
from enocean_async.capabilities.position_angle import (
    COVER_WATCHDOG_TIMEOUT,
    CoverCapability,
)
from enocean_async.capabilities.state_change import StateChangeSource
from enocean_async.eep.message import EEPMessage, EEPMessageType, EntityValue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _eurid(s: str = "01:23:45:67") -> EURID:
    return EURID.from_string(s)


def _make_msg(
    sender: EURID,
    position: int | None = None,
    angle: int | None = None,
    message_type_id: int = 4,   # D2-05-00 reply
) -> EEPMessage:
    """Build a minimal EEPMessage suitable for CoverCapability.decode()."""
    entities: dict = {}
    if position is not None:
        entities[ObservableUID.POSITION] = EntityValue(value=position, unit="%")
    if angle is not None:
        entities[ObservableUID.ANGLE] = EntityValue(value=angle, unit="%")
    # CoverCapability only processes messages with message_type.id == 4.
    msg = EEPMessage(
        sender=sender,
        entities=entities,
        values={"dummy": None},  # non-empty so it passes the `if not values` guard
        message_type=EEPMessageType(id=message_type_id, description="reply"),
    )
    return msg


def _make_cap(device: EURID, received: list) -> CoverCapability:
    return CoverCapability(device_address=device, on_state_change=received.append)


def _values_for(received: list, uid: str):
    return [sc.value for sc in received if sc.observable_uid == uid]


# ---------------------------------------------------------------------------
# Position and angle emission
# ---------------------------------------------------------------------------

class TestCoverCapabilityEmission:
    """Basic StateChange emission for POSITION and ANGLE."""

    def test_position_state_change_emitted(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50))
        assert any(sc.observable_uid == ObservableUID.POSITION for sc in received)

    def test_position_value_correct(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=75))
        pos_values = _values_for(received, ObservableUID.POSITION)
        assert pos_values == [75]

    def test_angle_state_change_emitted(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50, angle=30))
        assert any(sc.observable_uid == ObservableUID.ANGLE for sc in received)

    def test_angle_value_correct(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50, angle=45))
        ang_values = _values_for(received, ObservableUID.ANGLE)
        assert ang_values == [45]

    def test_no_angle_when_not_in_entities(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50))  # no angle
        assert not any(sc.observable_uid == ObservableUID.ANGLE for sc in received)

    def test_position_source_is_telegram(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50))
        pos_changes = [sc for sc in received if sc.observable_uid == ObservableUID.POSITION]
        assert pos_changes[0].source == StateChangeSource.TELEGRAM


# ---------------------------------------------------------------------------
# Cover state derivation
# ---------------------------------------------------------------------------

class TestCoverStateDerived:
    """_derive_cover_state encodes direction and boundary conditions."""

    def test_position_zero_emits_open(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=0))
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        assert "open" in cover_states

    def test_position_100_emits_closed(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=100))
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        assert "closed" in cover_states

    async def test_increasing_position_emits_closing(self, device_address):
        # async because the second decode triggers the watchdog (asyncio.create_task)
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=30))  # first message, no watchdog
        received.clear()
        cap.decode(_make_msg(device_address, position=50))  # "closing" → starts watchdog
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        assert "closing" in cover_states

    async def test_decreasing_position_emits_opening(self, device_address):
        # async because the second decode triggers the watchdog (asyncio.create_task)
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=70))  # first message, no watchdog
        received.clear()
        cap.decode(_make_msg(device_address, position=50))  # "opening" → starts watchdog
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        assert "opening" in cover_states

    def test_no_cover_state_on_first_mid_position_message(self, device_address):
        # Without a previous position, state cannot be derived for mid values.
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50))
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        # No direction can be determined from the first message at 50%.
        assert "opening" not in cover_states
        assert "closing" not in cover_states

    def test_unchanged_position_emits_stopped(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=50))
        received.clear()
        cap.decode(_make_msg(device_address, position=50))  # same value
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        assert "stopped" in cover_states


# ---------------------------------------------------------------------------
# Watchdog timer
# ---------------------------------------------------------------------------

class TestCoverCapabilityWatchdog:
    """The async watchdog must fire "stopped" after COVER_WATCHDOG_TIMEOUT
    when the cover is moving, and be cancelled when a new update arrives."""

    async def test_watchdog_fires_stopped_after_timeout(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        # Cause the cover to start moving (closing).
        cap.decode(_make_msg(device_address, position=20))
        cap.decode(_make_msg(device_address, position=40))
        # Advance time past the watchdog threshold.
        await asyncio.sleep(COVER_WATCHDOG_TIMEOUT + 0.1)
        cover_states = _values_for(received, ObservableUID.COVER_STATE)
        assert "stopped" in cover_states

    async def test_watchdog_source_is_timer(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        cap.decode(_make_msg(device_address, position=20))
        cap.decode(_make_msg(device_address, position=40))
        await asyncio.sleep(COVER_WATCHDOG_TIMEOUT + 0.1)
        timer_events = [
            sc for sc in received
            if sc.observable_uid == ObservableUID.COVER_STATE
            and sc.source == StateChangeSource.TIMER
        ]
        assert len(timer_events) >= 1

    async def test_new_message_cancels_watchdog(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        # Start moving.
        cap.decode(_make_msg(device_address, position=20))
        cap.decode(_make_msg(device_address, position=40))
        # Deliver another position update before the watchdog fires.
        await asyncio.sleep(COVER_WATCHDOG_TIMEOUT * 0.3)
        cap.decode(_make_msg(device_address, position=60))
        # Wait for what would have been the first watchdog timeout, then a bit more.
        await asyncio.sleep(COVER_WATCHDOG_TIMEOUT * 0.8)
        # The first watchdog was cancelled; no premature "stopped" should have fired.
        timer_stops = [
            sc for sc in received
            if sc.observable_uid == ObservableUID.COVER_STATE
            and sc.source == StateChangeSource.TIMER
        ]
        # At this point we are still within the second watchdog window, so
        # no timer-sourced stop should have been emitted yet.
        assert len(timer_stops) == 0


# ---------------------------------------------------------------------------
# Message filtering
# ---------------------------------------------------------------------------

class TestCoverCapabilityFiltering:
    """Messages from wrong sender or wrong message_type.id are ignored."""

    def test_ignores_message_from_other_sender(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        other = _eurid("AA:BB:CC:DD")
        cap.decode(_make_msg(other, position=50))
        assert len(received) == 0

    def test_ignores_message_with_wrong_type_id(self, device_address):
        received = []
        cap = _make_cap(device_address, received)
        # message_type.id = 1 ("go to position") should be ignored by CoverCapability
        # which only handles id=4 ("reply position and angle").
        msg = _make_msg(device_address, position=50, message_type_id=1)
        cap.decode(msg)
        assert len(received) == 0
