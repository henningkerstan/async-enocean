from dataclasses import dataclass
from typing import Any, Dict

from ..address import EURID, Address, BaseAddress, BroadcastAddress
from ..eep.id import EEPID


@dataclass
class EEPMessage:
    """An EEP message represents a message according to a specific EEP profile in a a dictionary of values extracted from the message according to the EEP profile's data fields. It should not be generated manually but using a proper EEPHandler.

    For convenience, it can include the sender's address, the destination address, the EEPID of the message, and the RSSI (signal strength).
    """

    sender: EURID | BaseAddress | None
    """The sender's address. This is optional and can be None if the sender is unknown or not relevant."""

    destination: Address = BroadcastAddress()
    """The destination address. This will only be different from broadcast, when addressed sending is used (i.e. for VLD telegrams)."""

    eepid: EEPID | None = None
    """The EEPID of the message. This is optional and can be None if the EEPID is unknown or not relevant."""

    rssi: int | None = None
    """The RSSI (signal strength) of the message. This is optional and can be None if the RSSI is unknown or not relevant."""

    message_type: str | None = None
    """The type of the message, which can be used to further specify the kind of message"""

    values: Dict[str, Any] = None
    """A dictionary of values extracted from the message according to the EEP profile's data fields. The keys are the data field IDs (e.g., 'R1', 'POS'), and the values are the corresponding values extracted from the message."""

    def __repr__(self) -> str:
        msg = f"<EEPMessage {self.eepid} ({self.message_type if self.message_type else 'default'}) from {self.sender.to_string()}"
        if self.destination and not isinstance(self.destination, BroadcastAddress):
            msg += f" to {self.destination.to_string()}"

        msg += f": {self.values}>"
        return msg
