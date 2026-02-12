from enocean_async.eep.f602xx.message import (
    F602XXMessageButtonPressed,
    F602XXMessageButtonsReleased,
)
from enocean_async.eep.handler import EEPHandler
from enocean_async.eep.id import EEPID
from enocean_async.erp1.rorg import RORG
from enocean_async.erp1.telegram import ERP1Telegram

BUTTON_ACTION_UID_MAP = {
    0x30: "a0",
    0x10: "a1",
    0x70: "b0",
    0x50: "b1",
    0x37: "ab0",
    0x15: "ab1",
    0x17: "a1b0",
    0x35: "a0b1",
}


class F602XXDecoder(EEPHandler):
    def decode(
        self, telegram: ERP1Telegram
    ) -> F602XXMessageButtonPressed | F602XXMessageButtonsReleased:
        if telegram.rorg != RORG.RORG_RPS:
            raise ValueError(f"Invalid RORG for F6-02-XX: {telegram.rorg}")

        action = telegram.telegram_data[0]

        if action == 0x00:
            return F602XXMessageButtonsReleased(
                sender=telegram.sender,
            )
        elif action in BUTTON_ACTION_UID_MAP:
            return F602XXMessageButtonPressed(
                sender=telegram.sender,
                button=BUTTON_ACTION_UID_MAP[action],
            )
        else:
            raise ValueError(f"Unknown action for F6-02-XX: {action}")
