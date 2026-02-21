from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Optional

from ..address import Address
from ..eep.message import EEPMessage
from .state_change import StateChange, StateChangeCallback


@dataclass
class Capability(ABC):
    """A capability represents a specific functionality of a device, such as a button, a temperature sensor, or a motion detector.
    It is responsible for decoding EEP messages related to that functionality and emitting state changes accordingly."""

    device_address: Address
    on_state_change: Optional[StateChangeCallback] = None

    def decode(self, message: EEPMessage) -> None:
        """Decode the given EEPMessage according to this capability's logic.

        Only processes messages from the bound device.
        Emits state changes via the on_state_change callback.
        """
        if message.sender != self.device_address:
            return

        self._decode_impl(message)

    def _decode_impl(self, message: EEPMessage) -> None:
        """Implementation of decode logic. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement the _decode_impl method.")

    def _emit(self, state_change: StateChange) -> None:
        """Emit a state change via callback."""
        if self.on_state_change:
            self.on_state_change(state_change)
