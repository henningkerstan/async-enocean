from dataclasses import dataclass
from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .state_change import StateChange, StateChangeSource

HUMIDITY_UID = "humidity"


@dataclass
class HumiditySensorCapability(Capability):
    """Capability that emits humidity updates for A5-04-XX sensors."""

    def _decode_impl(self, message: EEPMessage) -> None:
        if not message.values:
            return
        if message.eepid is None or not message.eepid.to_string().startswith("A5-04-"):
            return

        hum_value = message.values.get("HUM")
        if hum_value is None or hum_value.value is None:
            return

        self._emit(
            StateChange(
                device_address=self.device_address,
                entity_uid=HUMIDITY_UID,
                value=hum_value.value,
                timestamp=time(),
                source=StateChangeSource.TELEGRAM,
            )
        )
