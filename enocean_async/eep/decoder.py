from ..erp1.telegram import ERP1Telegram
from .id import EEPID
from .message import EEPMessage


class EEPDecoder:
    """Base class for all EEP decoders."""

    def decode(self, telegram: ERP1Telegram) -> EEPMessage:
        """Convert an ERP1Telegram into an EEPMessage."""
        raise NotImplementedError

    def __call__(self, telegram: ERP1Telegram) -> EEPMessage:
        """Allow decoder instances to be called like functions."""
        return self.decode(telegram)
