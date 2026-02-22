from dataclasses import dataclass
from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .state_change import StateChange, StateChangeSource

VOLTAGE_UID = "voltage"


@dataclass
class VoltageSensorCapability(Capability):
    """Capability that emits voltage updates for sensors with SVC (supply voltage) field."""

    def _decode_impl(self, message: EEPMessage) -> None:
        if not message.values:
            return
        if message.eepid is None or not message.eepid.to_string() == "A5-07-03":
            return

        svc_value = message.values.get("SVC")
        if svc_value is None or svc_value.value is None:
            return

        self._emit(
            StateChange(
                device_address=self.device_address,
                entity_uid=VOLTAGE_UID,
                value=svc_value.value,
                timestamp=time(),
                source=StateChangeSource.TELEGRAM,
            )
        )
