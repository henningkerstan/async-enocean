"""EEP (EnOcean Equipment Profile) - Central registry of all supported profiles.

This module imports all EEP definitions organized by RORG (Radio Telegram Type)
and provides them in a single dictionary for easy lookup by EEPID.
"""

from .a5 import EEP_A5_07_03
from .d2 import EEP_D2_05_00, EEP_D2_20_02
from .f6 import EEP_F6_02_01, EEP_F6_02_02
from .id import EEPID
from .profile import EEP

EEP_DATABASE: dict[EEPID, EEP] = {
    EEP_A5_07_03.id: EEP_A5_07_03,
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
