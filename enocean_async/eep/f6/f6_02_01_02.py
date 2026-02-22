"""F6-02: Rocker Switch, 2 Rocker - Application Styles 1 & 2.

This module contains F6-02-01 and F6-02-02 profiles, which share identical
telegram structures and only differ in their application-level interpretation.

Profiles in this module:
- F6-02-01: Light and blind control - application style 1
- F6-02-02: Light and blind control - application style 2
"""

from ..id import EEPID
from ..profile import EEP, EEPDataField, EEPTelegram

# Shared telegram definition for all F6-02-xx profiles
_F6_02_TELEGRAM = EEPTelegram(
    name=None,
    datafields=[
        EEPDataField(
            id="R1",
            name="Rocker 1st action",
            offset=0,
            size=3,
            range_min=0,
            range_max=7,
            range_enum={
                0: "a1",
                1: "a0",
                2: "b1",
                3: "b0",
            },
        ),
        EEPDataField(
            id="EB",
            name="Energy bow",
            offset=3,
            size=1,
            range_min=0,
            range_max=1,
            range_enum={0: "released", 1: "pressed"},
        ),
        EEPDataField(
            id="R2",
            name="Rocker 2nd action",
            offset=4,
            size=3,
            range_min=0,
            range_max=7,
            range_enum={
                0: "a1",
                1: "a0",
                2: "b1",
                3: "b0",
            },
        ),
        EEPDataField(
            id="SA",
            name="2nd action",
            offset=7,
            size=1,
            range_min=0,
            range_max=1,
            range_enum={0: "No 2nd action", 1: "2nd action valid"},
        ),
    ],
)


# Define all F6-02-xx variants using the shared telegram structure
EEP_F6_02_01 = EEP(
    id=EEPID.from_string("F6-02-01"),
    name="Light and blind control - application style 1",
    cmd_size=0,
    cmd_offset=None,
    telegrams={0: _F6_02_TELEGRAM},
)

EEP_F6_02_02 = EEP(
    id=EEPID.from_string("F6-02-02"),
    name="Light and blind control - application style 2",
    cmd_size=0,
    cmd_offset=None,
    telegrams={0: _F6_02_TELEGRAM},
)
