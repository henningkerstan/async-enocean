"""Generic scalar capability driven by observable_uid annotation on EEP fields."""

from dataclasses import dataclass, field
from time import time

from ..eep.message import EEPMessage
from .capability import Capability
from .state_change import StateChange, StateChangeSource


@dataclass
class ScalarCapability(Capability):
    """Generic capability that emits a StateChange for any EEP field annotated with a matching observable_uid.

    This capability reads from the EEP-level observable_uid key that was propagated into EEPMessage.entities by EEPHandler.
    This makes it fully EEP-agnostic.
    """

    observable_uid: str = field(kw_only=True)
    """The entity UID to read from EEPMessage.entities and emit as a StateChange."""

    channel_field_id: str | None = field(default=None, kw_only=True)
    """If set, read this field ID from message.values to populate StateChange.channel."""

    channel_not_applicable: int | None = field(default=None, kw_only=True)
    """Raw channel value that means 'not applicable'; mapped to channel=None in StateChange."""

    def _decode_impl(self, message: EEPMessage) -> None:
        v = message.entities.get(self.observable_uid)
        if v is None or v.value is None:
            return

        channel = None
        if self.channel_field_id is not None:
            cf = message.values.get(self.channel_field_id)
            if cf is not None and cf.raw != self.channel_not_applicable:
                channel = cf.raw

        self._emit(
            StateChange(
                device_address=self.device_address,
                observable_uid=self.observable_uid,
                value=v.value,
                unit=v.unit,
                channel=channel,
                timestamp=time(),
                source=StateChangeSource.TELEGRAM,
            )
        )
