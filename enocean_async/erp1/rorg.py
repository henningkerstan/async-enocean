from enum import IntEnum


class RORG(IntEnum):
    RORG_RPS = 0xF6
    RORG_1BS = 0xD5
    RORG_4BS = 0xA5
    RORG_VLD = 0xD2
    RORG_UTE = 0xD4
    RORG_MSC = 0xD1
    RORG_ADT_VLD = 0xA6

    @property
    def simple_name(self) -> str:
        return self.name[5:]  # remove "RORG_" prefix
