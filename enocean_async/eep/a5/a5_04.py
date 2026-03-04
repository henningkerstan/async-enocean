"""A5-04-XX: Temperature and humidity sensors."""

from ...capabilities.observable import Observable
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..profile import EEPDataField, SimpleProfileSpecification

_TEMP_HUM_FACTORIES = [
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.HUMIDITY,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.TEMPERATURE,
    ),
]


class _EEP_A5_04_01_02(SimpleProfileSpecification):
    def __init__(self, _type: int, min_temp: float, max_temp: float):
        super().__init__(
            eep=EEP.from_string(f"A5-04-{_type:02X}"),
            name=f"Temperature and humidity sensor, range {min_temp}°C to {max_temp}°C and 0% to 100%",
            datafields=[
                EEPDataField(
                    id="HUM",
                    name="Humidity",
                    offset=8,
                    size=8,
                    range_min=0,
                    range_max=250,
                    scale_min_fn=lambda _: 0.0,
                    scale_max_fn=lambda _: 100.0,
                    unit_fn=lambda _: "%",
                    observable=Observable.HUMIDITY,
                ),
                EEPDataField(
                    id="TMP",
                    name="Temperature",
                    offset=16,
                    size=8,
                    range_min=0,
                    range_max=250,
                    scale_min_fn=lambda _: min_temp,
                    scale_max_fn=lambda _: max_temp,
                    unit_fn=lambda _: "°C",
                    observable=Observable.TEMPERATURE,
                ),
                EEPDataField(
                    id="TSN",
                    name="Temperature sensor availability",
                    offset=30,
                    size=1,
                    range_enum={
                        0: "Not available",
                        1: "Available",
                    },
                ),
            ],
            capability_factories=_TEMP_HUM_FACTORIES,
        )


EEP_A5_04_01 = _EEP_A5_04_01_02(_type=0x01, min_temp=0.0, max_temp=40.0)
EEP_A5_04_02 = _EEP_A5_04_01_02(_type=0x02, min_temp=-20.0, max_temp=60.0)
EEP_A5_04_03 = SimpleProfileSpecification(
    eep=EEP.from_string(f"A5-04-03"),
    name="Temperature and humidity sensor, range -20°C to 60°C 10bit-measurement and 0% to 100%",
    datafields=[
        EEPDataField(
            id="HUM",
            name="Humidity",
            offset=0,
            size=8,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 100.0,
            unit_fn=lambda _: "%",
            observable=Observable.HUMIDITY,
        ),
        EEPDataField(
            id="TMP",
            name="Temperature",
            offset=14,
            size=10,
            scale_min_fn=lambda _: -20.0,
            scale_max_fn=lambda _: 60.0,
            unit_fn=lambda _: "°C",
            observable=Observable.TEMPERATURE,
        ),
        EEPDataField(
            id="TTP",
            name="Telegram type",
            offset=30,
            size=1,
            range_enum={
                0: "Heartbeat",
                1: "Event triggered",
            },
        ),
    ],
    capability_factories=_TEMP_HUM_FACTORIES,
)


__all__ = ["EEP_A5_04_01", "EEP_A5_04_02", "EEP_A5_04_03"]
