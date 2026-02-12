from .id import EEPID
from .message import EEPMessage


class EEPDecoder:
    """Base class for all EEP decoders."""

    eep: EEPID

    def decode(self, telegram) -> EEPMessage:
        """Convert an ERP1Telegram into an EEPMessage."""
        raise NotImplementedError
