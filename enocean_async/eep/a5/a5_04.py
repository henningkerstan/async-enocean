"""A5-02-XX: Temperature sensors."""

from ..id import EEPID
from ..profile import EEP, EEPDataField, EEPTelegram


class _EEP_A5_04_01_02(EEP):
    def __init__(self, _type: int, min_temp: float, max_temp: float):
        super().__init__(
            id=EEPID.from_string(f"A5-04-{_type:02X}"),
            name=f"Temperature and humidity sensor, range {min_temp}°C to {max_temp}°C and 0% to 100%",
            cmd_size=0,
            cmd_offset=None,
            telegrams={
                0: EEPTelegram(
                    name=None,
                    datafields=[
                        EEPDataField(
                            id="HUM",
                            name="Humidity",
                            offset=8,
                            size=8,
                            range_min=0,
                            range_max=250,
                            scale_min=0.0,
                            scale_max=100.0,
                            unit="%",
                        ),
                        EEPDataField(
                            id="TMP",
                            name="Temperature",
                            offset=16,
                            size=8,
                            range_min=0,
                            range_max=250,
                            scale_min=min_temp,
                            scale_max=max_temp,
                            unit="°C",
                        ),
                        EEPDataField(
                            id="TSN",
                            name="Temperature sensor availability",
                            offset=30,
                            size=1,
                            range_min=0,
                            range_max=1,
                            range_enum={
                                0: "Not available",
                                1: "Available",
                            },
                            unit="",
                        ),
                    ],
                ),
            },
        )


EEP_A5_04_01 = _EEP_A5_04_01_02(_type=0x01, min_temp=0.0, max_temp=40.0)
EEP_A5_04_02 = _EEP_A5_04_01_02(_type=0x02, min_temp=-20.0, max_temp=60.0)
EEP_A5_04_03 = EEP(
    id=EEPID.from_string(f"A5-04-03"),
    name="Temperature and humidity sensor, range -20°C to 60°C 10bit-measurement and 0% to 100%",
    cmd_size=0,
    cmd_offset=None,
    telegrams={
        0: EEPTelegram(
            name=None,
            datafields=[
                EEPDataField(
                    id="HUM",
                    name="Humidity",
                    offset=0,
                    size=8,
                    range_min=0,
                    range_max=255,
                    scale_min=0.0,
                    scale_max=100.0,
                    unit="%",
                ),
                EEPDataField(
                    id="TMP",
                    name="Temperature",
                    offset=14,
                    size=10,
                    range_min=0,
                    range_max=1023,
                    scale_min=-20.0,
                    scale_max=60.0,
                    unit="°C",
                ),
                EEPDataField(
                    id="TTP",
                    name="Telegram type",
                    offset=30,
                    size=1,
                    range_min=0,
                    range_max=1,
                    range_enum={
                        0: "Heartbeat",
                        1: "Event triggered",
                    },
                    unit="",
                ),
            ],
        ),
    },
)


__all__ = ["EEP_A5_04_01", "EEP_A5_04_02", "EEP_A5_04_03"]
