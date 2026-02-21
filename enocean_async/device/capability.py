from abc import ABC
from dataclasses import dataclass

from ..eep.message import EEPMessage


@dataclass
class Capability(ABC):
    uid: str

    def decode(self, message: EEPMessage) -> None:
        """Decode the given EEPMessage according to this capability's logic."""
        raise NotImplementedError("Subclasses must implement the decode method.")


class PushButtonCabapility(Capability):
    """A simple capability for a push button device, which can be used for testing and demonstration purposes."""

    def decode(self, message: EEPMessage) -> None:
        pass
