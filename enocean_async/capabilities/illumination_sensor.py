from dataclasses import dataclass
from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .state_change import StateChange, StateChangeSource

ILLUMINATION_UID = "illumination"


@dataclass
class IlluminationSensorCapability(Capability):
    """Capability that emits illumination updates for A5-07-03 sensors."""

    def _decode_impl(self, message: EEPMessage) -> None:
        if not message.values:
            return
        if message.eepid is None or not message.eepid.to_string() == "A5-07-03":
            return

        ill_value = message.values.get("ILL")
        if ill_value is None or ill_value.value is None:
            return

        self._emit(
            StateChange(
                device_address=self.device_address,
                entity_uid=ILLUMINATION_UID,
                value=ill_value.value,
                timestamp=time(),
                source=StateChangeSource.TELEGRAM,
            )
        )
