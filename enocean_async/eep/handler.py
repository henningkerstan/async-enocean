from ..erp1.telegram import ERP1Telegram
from .id import EEPID
from .message import EEPMessage


class EEPHandler:
    """Base class for all EEP handlers."""

    def decode(self, telegram: ERP1Telegram) -> EEPMessage:
        """Convert an ERP1Telegram into an EEPMessage."""
        raise NotImplementedError

    def encode(self, message: EEPMessage) -> ERP1Telegram:
        """Convert an EEPMessage into an ERP1Telegram."""
        # Not all EEPs will support encoding, so this can be left unimplemented if desired.
        pass

    def __call__(self, telegram: ERP1Telegram) -> EEPMessage:
        """Allow decoder instances to be called like functions."""
        return self.decode(telegram)
