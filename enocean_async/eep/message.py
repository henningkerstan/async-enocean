from dataclasses import dataclass
from typing import Any, Dict

from ..address import EURID, BaseAddress
from ..eep.id import EEPID


@dataclass
class EEPMessage:
    """An EEP message represents a message according to a specific EEP profile in a a dictionary of values extracted from the message according to the EEP profile's data fields. It should not be generated manually but using a proper EEPHandler.

    For convenience, it can include the sender's address, the EEPID of the message, and the RSSI (signal strength).
    """

    sender: EURID | BaseAddress | None
    """The sender's address, which can be a EURID or a BaseAddress. This is optional and can be None if the sender is unknown or not relevant."""

    eepid: EEPID | None = None
    """The EEPID of the message. This is optional and can be None if the EEPID is unknown or not relevant."""

    rssi: int | None = None
    """The RSSI (signal strength) of the message. This is optional and can be None if the RSSI is unknown or not relevant."""

    values: Dict[str, Any] = None
    """A dictionary of values extracted from the message according to the EEP profile's data fields. The keys are the data field IDs (e.g., 'R1', 'POS'), and the values are the corresponding values extracted from the message."""

    def __repr__(self) -> str:
        return (
            f"<EEPMessage {self.eepid} from {self.sender.to_string()}: {self.values}>"
        )
