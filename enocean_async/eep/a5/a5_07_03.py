"""A5-07-03: Occupancy with Supply voltage monitor and 10-bit illumination measurement."""

from ..id import EEPID
from ..profile import EEP, EEPDataField, EEPTelegram

EEP_A5_07_03 = EEP(
    id=EEPID.from_string("A5-07-03"),
    name="Occupancy with Supply voltage monitor and 10-bit illumination measurement",
    cmd_size=0,
    cmd_offset=None,
    telegrams={
        0: EEPTelegram(
            name=None,
            datafields=[
                EEPDataField(
                    id="SVC",
                    name="Supply voltage",
                    offset=0,
                    size=8,
                    range_min=0,
                    range_max=250,
                    scale_min=0.0,
                    scale_max=5.0,
                    range_enum=None,
                    unit="V",
                ),
                EEPDataField(
                    id="ILL",
                    name="Illumination",
                    offset=8,
                    size=10,
                    range_min=0,
                    range_max=1000,
                    scale_min=0.0,
                    scale_max=1000.0,
                    range_enum=None,
                    unit="lx",
                ),
                EEPDataField(
                    id="PIR",
                    name="PIR Status",
                    offset=24,
                    size=1,
                    range_min=0,
                    range_max=1,
                    scale_min=0.0,
                    scale_max=0.0,
                    range_enum={
                        0: "Uncertain of occupancy status",
                        1: "Motion detected",
                    },
                    unit="",
                ),
            ],
        )
    },
)
