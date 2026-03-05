"""Metadata capability providing RSSI and last_seen timestamp."""

from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .observable import Observable
from .state_change import EntityStateChange, EntityStateChangeSource


class MetaDataCapability(Capability):
    """Capability providing metadata about received messages (RSSI and last seen timestamp).

    This capability can be attached to any device type to track:
    - RSSI (signal strength) when available
    - Last seen timestamp for every received message
    - Telegram count (number of messages received)
    """

    def __init__(self, device_address, on_state_change):
        """Initialize the metadata capability."""
        super().__init__(device_address, on_state_change)
        self._telegram_count = 0

    def _decode_impl(self, message: EEPMessage) -> None:
        """Decode metadata from the message."""
        self._telegram_count += 1
        timestamp = time()

        # Emit RSSI if available
        if message.rssi is not None:
            self._emit(
                EntityStateChange(
                    device_id=self.device_address,
                    entity_id="rssi",
                    values={Observable.RSSI: message.rssi},
                    timestamp=timestamp,
                    source=EntityStateChangeSource.TELEGRAM,
                )
            )

        # Always emit last_seen timestamp
        self._emit(
            EntityStateChange(
                device_id=self.device_address,
                entity_id="last_seen",
                values={Observable.LAST_SEEN: timestamp},
                timestamp=timestamp,
                source=EntityStateChangeSource.TELEGRAM,
            )
        )

        # Always emit telegram count
        self._emit(
            EntityStateChange(
                device_id=self.device_address,
                entity_id="telegram_count",
                values={Observable.TELEGRAM_COUNT: self._telegram_count},
                timestamp=timestamp,
                source=EntityStateChangeSource.TELEGRAM,
            )
        )
