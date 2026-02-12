from dataclasses import dataclass
from typing import Any, Dict

from ..eep.id import EEPID
from ..erp1.address import EURID, BaseAddress


@dataclass
class EEPMessage:
    sender: EURID | BaseAddress

    def __repr__(self) -> str:
        return f"<EEPMessage {self.eep} from {self.sender.to_string()}: {self.values}>"
