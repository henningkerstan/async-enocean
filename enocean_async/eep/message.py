from dataclasses import dataclass, field
from typing import Any, Dict, NamedTuple

from ..address import EURID, Address, BaseAddress, BroadcastAddress
from ..capabilities.observable import Observable
from ..eep.id import EEP


class EntityValue(NamedTuple):
    """A lightweight container for semantic entity values."""

    value: Any
    """The interpreted/scaled value."""

    unit: str | None = None
    """The unit of the value (e.g., '°C', '%', 'lx')."""


@dataclass
class EEPMessageType:
    """Representation of an EEP message type."""

    id: int
    """A unique identifier for the message type."""

    description: str
    """A human-readable description of the message type."""


@dataclass
class EEPMessageValue:
    """Raw and interpreted value for a single EEP data field."""

    raw: int
    """The raw integer value of the data field as extracted from the message."""

    value: Any
    """The interpreted value of the data field according to the EEP profile's data field definition"""

    unit: str | None = None
    """The unit of the interpreted value (e.g., '°C', '%', 'kWh'). Can be dynamic based on message context."""


@dataclass
class EEPMessage:
    """An EEP message represents a message according to a specific EEP profile in a a dictionary of values extracted from the message according to the EEP profile's data fields. It should not be generated manually but using a proper EEPHandler.

    For convenience, it can include the sender's address, the destination address, the eep of the message, and the RSSI (signal strength).
    """

    sender: EURID | BaseAddress | None
    """The sender's address. This is optional and can be None if the sender is unknown or not relevant."""

    destination: Address = BroadcastAddress()
    """The destination address. This will only be different from broadcast, when addressed sending is used (i.e. for VLD telegrams)."""

    eep: EEP | None = None
    """The eep of the message. This is optional and can be None if the eep is unknown or not relevant."""

    rssi: int | None = None
    """The RSSI (signal strength) of the message. This is optional and can be None if the RSSI is unknown or not relevant."""

    message_type: EEPMessageType | None = None
    """The type of the message."""

    values: Dict[str, EEPMessageValue] = field(default_factory=dict)
    """A dictionary of values extracted from the message according to the EEP profile's data fields.

    Keys are EEP field IDs (e.g., 'R1', 'POS'); values are corresponding raw/interpreted pairs.
    """

    entities: Dict[Observable, EntityValue] = field(default_factory=dict)
    """A dictionary of semantically interpreted values keyed by Observable.

    Keys are Observable enum members (e.g., Observable.TEMPERATURE, Observable.POSITION).
    Values are EntityValue tuples containing (value, unit).
    """

    def __repr__(self) -> str:
        msg = f"EEPMessage(sender={self.sender.to_string()}, eep={self.eep}, message_type={self.message_type if self.message_type else 'default'}"
        if self.destination is not None and not self.destination.is_broadcast():
            msg += f", destination={self.destination.to_string()}"

        msg += f", values={self.values}, entities={self.entities})"
        return msg
