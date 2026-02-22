"""D2-05-00: Blinds control for position and angle, type 0x00."""

from ..id import EEPID
from ..profile import EEP, EEPDataField, EEPTelegram

EEP_D2_05_00 = EEP(
    id=EEPID.from_string("D2-05-00"),
    name="Blinds control for position and angle, type 0x00",
    cmd_size=4,
    cmd_offset=-4,
    telegrams={
        1: EEPTelegram(
            name="Go to position and angle",
            datafields=[
                EEPDataField(
                    id="POS",
                    name="Vertical position",
                    offset=1,
                    size=7,
                    range_min=0,
                    range_max=127,
                    unit_fn=lambda _: "%",
                ),
                EEPDataField(
                    id="ANG",
                    name="Rotation angle",
                    offset=9,
                    size=7,
                    range_min=0,
                    range_max=127,
                    unit_fn=lambda _: "%",
                ),
                EEPDataField(
                    id="REPO",
                    name="Repositioning mode",
                    offset=17,
                    size=3,
                    range_enum={
                        0: "Directly to target POS/ANG",
                        1: "Up, then to target POS/ANG",
                        2: "Down, then to target POS/ANG",
                        3: "Reserved",
                        4: "Reserved",
                        5: "Reserved",
                        6: "Reserved",
                        7: "Reserved",
                    },
                ),
                EEPDataField(
                    id="LOCK",
                    name="Set locking mode",
                    offset=21,
                    size=3,
                    range_enum={
                        0: "No change",
                        1: "Set blockage mode",
                        2: "Set alarm mode",
                        3: "Reserved",
                        4: "Reserved",
                        5: "Reserved",
                        6: "Reserved",
                        7: "Unblock",
                    },
                ),
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=24,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                        15: "All channels",
                    },
                ),
            ],
        ),
        2: EEPTelegram(
            name="Stop",
            datafields=[
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=0,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                        15: "All channels",
                    },
                ),
            ],
        ),
        3: EEPTelegram(
            name="Query position and angle",
            datafields=[
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=0,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                        15: "All channels",
                    },
                ),
            ],
        ),
        4: EEPTelegram(
            name="Reply position and angle",
            datafields=[
                EEPDataField(
                    id="POS",
                    name="Vertical position",
                    offset=1,
                    size=7,
                    unit_fn=lambda _: "%",
                ),
                EEPDataField(
                    id="ANG",
                    name="Rotation angle",
                    offset=9,
                    size=7,
                    unit_fn=lambda _: "%",
                ),
                EEPDataField(
                    id="LOCK",
                    name="Locking modes",
                    offset=21,
                    size=3,
                    range_enum={
                        0: "Normal (no lock)",
                        1: "Blockage mode",
                        2: "Alarm mode",
                        3: "Reserved",
                        4: "Reserved",
                        5: "Reserved",
                        6: "Reserved",
                        7: "Reserved",
                    },
                ),
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=24,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                    },
                ),
            ],
        ),
    },
)
