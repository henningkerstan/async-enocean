"""EEP (EnOcean Equipment Profile) - Central registry of all supported profiles.

This module imports all EEP definitions organized by RORG (Radio Telegram Type)
and provides them in a single dictionary for easy lookup by EEPID.
"""

from .a5 import (
    EEP_A5_02_0A,
    EEP_A5_02_0B,
    EEP_A5_02_01,
    EEP_A5_02_02,
    EEP_A5_02_03,
    EEP_A5_02_04,
    EEP_A5_02_05,
    EEP_A5_02_06,
    EEP_A5_02_07,
    EEP_A5_02_08,
    EEP_A5_02_09,
    EEP_A5_02_1A,
    EEP_A5_02_1B,
    EEP_A5_02_10,
    EEP_A5_02_11,
    EEP_A5_02_12,
    EEP_A5_02_13,
    EEP_A5_02_14,
    EEP_A5_02_15,
    EEP_A5_02_16,
    EEP_A5_02_17,
    EEP_A5_02_18,
    EEP_A5_02_19,
    EEP_A5_02_20,
    EEP_A5_02_30,
    EEP_A5_04_01,
    EEP_A5_04_02,
    EEP_A5_04_03,
    EEP_A5_07_03,
    EEP_A5_38_08,
)
from .d2 import EEP_D2_05_00, EEP_D2_20_02
from .f6 import EEP_F6_02_01, EEP_F6_02_02
from .id import EEPID
from .profile import EEP

EEP_DATABASE: dict[EEPID, EEP] = {
    EEP_A5_02_01.id: EEP_A5_02_01,
    EEP_A5_02_02.id: EEP_A5_02_02,
    EEP_A5_02_03.id: EEP_A5_02_03,
    EEP_A5_02_04.id: EEP_A5_02_04,
    EEP_A5_02_05.id: EEP_A5_02_05,
    EEP_A5_02_06.id: EEP_A5_02_06,
    EEP_A5_02_07.id: EEP_A5_02_07,
    EEP_A5_02_08.id: EEP_A5_02_08,
    EEP_A5_02_09.id: EEP_A5_02_09,
    EEP_A5_02_0A.id: EEP_A5_02_0A,
    EEP_A5_02_0B.id: EEP_A5_02_0B,
    EEP_A5_02_10.id: EEP_A5_02_10,
    EEP_A5_02_11.id: EEP_A5_02_11,
    EEP_A5_02_12.id: EEP_A5_02_12,
    EEP_A5_02_13.id: EEP_A5_02_13,
    EEP_A5_02_14.id: EEP_A5_02_14,
    EEP_A5_02_15.id: EEP_A5_02_15,
    EEP_A5_02_16.id: EEP_A5_02_16,
    EEP_A5_02_17.id: EEP_A5_02_17,
    EEP_A5_02_18.id: EEP_A5_02_18,
    EEP_A5_02_19.id: EEP_A5_02_19,
    EEP_A5_02_1A.id: EEP_A5_02_1A,
    EEP_A5_02_1B.id: EEP_A5_02_1B,
    EEP_A5_02_20.id: EEP_A5_02_20,
    EEP_A5_02_30.id: EEP_A5_02_30,
    EEP_A5_04_01.id: EEP_A5_04_01,
    EEP_A5_04_02.id: EEP_A5_04_02,
    EEP_A5_04_03.id: EEP_A5_04_03,
    EEP_A5_07_03.id: EEP_A5_07_03,
    EEP_A5_38_08.id: EEP_A5_38_08,
    EEP_F6_02_01.id: EEP_F6_02_01,
    EEP_F6_02_02.id: EEP_F6_02_02,
    EEP_D2_05_00.id: EEP_D2_05_00,
    EEP_D2_20_02.id: EEP_D2_20_02,
}
"""A simple in-memory database of supported EEP profiles. 

For performance reasons, this is implemented as a dictionary mapping EEPID to EEP.
EEP definitions are organized in subfolders by RORG (Radio Telegram Type):
- a5/ - 4BS telegram profiles (A5-xx-xx)
- f6/ - RPS telegram profiles (F6-xx-xx)
- d2/ - VLD telegram profiles (D2-xx-xx)
"""

__all__ = ["EEP_DATABASE", "EEPID", "EEP"]
