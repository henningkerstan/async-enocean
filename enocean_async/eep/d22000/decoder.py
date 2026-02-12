from enocean_async.eep.d22000.message import D20000FanStatusMessage
from enocean_async.eep.f602xx.message import (
    F602XXMessageButtonPressed,
    F602XXMessageButtonsReleased,
)
from enocean_async.eep.handler import EEPHandler
from enocean_async.erp1.rorg import RORG
from enocean_async.erp1.telegram import ERP1Telegram


class D22000Decoder(EEPHandler):
    def decode(self, telegram: ERP1Telegram) -> D20000FanStatusMessage:
        if telegram.rorg != RORG.RORG_VLD:
            raise ValueError(f"Invalid RORG for D2-20-00: {telegram.rorg}")

        msg = D20000FanStatusMessage(
            sender=telegram.sender,
            operating_mode_status=telegram.bitstring_raw_value(0, 4),
        )
