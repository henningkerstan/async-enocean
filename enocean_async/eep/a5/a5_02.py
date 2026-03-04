"""A5-02-XX: Temperature sensors."""

from ...capabilities.observable import Observable
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..profile import EEPDataField, SimpleProfileSpecification


class _EEP_A5_02(SimpleProfileSpecification):
    def __init__(
        self, _type: int, scale_min: float, scale_max: float, ten_bit: bool = False
    ):
        super().__init__(
            eep=EEP.from_string(f"A5-02-{_type:02X}"),
            name=("10 bit t" if ten_bit else "T")
            + "emperature sensor, range "
            + str(scale_min)
            + "°C to "
            + str(scale_max)
            + "°C",
            datafields=[
                EEPDataField(
                    id="TMP",
                    name="Temperature",
                    offset=14 if ten_bit else 16,
                    size=10 if ten_bit else 8,
                    scale_min_fn=lambda _: scale_min,
                    scale_max_fn=lambda _: scale_max,
                    unit_fn=lambda _: "°C",
                    observable=Observable.TEMPERATURE,
                )
            ],
            capability_factories=[
                lambda addr, cb: ScalarCapability(
                    device_address=addr,
                    on_state_change=cb,
                    observable=Observable.TEMPERATURE,
                ),
            ],
        )


EEP_A5_02_01 = _EEP_A5_02(_type=0x01, scale_min=-40.0, scale_max=0.0)
EEP_A5_02_02 = _EEP_A5_02(_type=0x02, scale_min=-30.0, scale_max=10.0)
EEP_A5_02_03 = _EEP_A5_02(_type=0x03, scale_min=-20.0, scale_max=20.0)
EEP_A5_02_04 = _EEP_A5_02(_type=0x04, scale_min=-10.0, scale_max=30.0)
EEP_A5_02_05 = _EEP_A5_02(_type=0x05, scale_min=0.0, scale_max=40.0)
EEP_A5_02_06 = _EEP_A5_02(_type=0x06, scale_min=10.0, scale_max=50.0)
EEP_A5_02_07 = _EEP_A5_02(_type=0x07, scale_min=20.0, scale_max=60.0)
EEP_A5_02_08 = _EEP_A5_02(_type=0x08, scale_min=30.0, scale_max=70.0)
EEP_A5_02_09 = _EEP_A5_02(_type=0x09, scale_min=40.0, scale_max=80.0)
EEP_A5_02_0A = _EEP_A5_02(_type=0x0A, scale_min=50.0, scale_max=90.0)
EEP_A5_02_0B = _EEP_A5_02(_type=0x0B, scale_min=60.0, scale_max=100.0)
EEP_A5_02_10 = _EEP_A5_02(_type=0x10, scale_min=-60.0, scale_max=20.0)
EEP_A5_02_11 = _EEP_A5_02(_type=0x11, scale_min=-50.0, scale_max=30.0)
EEP_A5_02_12 = _EEP_A5_02(_type=0x12, scale_min=-40.0, scale_max=40.0)
EEP_A5_02_13 = _EEP_A5_02(_type=0x13, scale_min=-30.0, scale_max=50.0)
EEP_A5_02_14 = _EEP_A5_02(_type=0x14, scale_min=-20.0, scale_max=60.0)
EEP_A5_02_15 = _EEP_A5_02(_type=0x15, scale_min=-10.0, scale_max=70.0)
EEP_A5_02_16 = _EEP_A5_02(_type=0x16, scale_min=0.0, scale_max=80.0)
EEP_A5_02_17 = _EEP_A5_02(_type=0x17, scale_min=10.0, scale_max=90.0)
EEP_A5_02_18 = _EEP_A5_02(_type=0x18, scale_min=20.0, scale_max=100.0)
EEP_A5_02_19 = _EEP_A5_02(_type=0x19, scale_min=30.0, scale_max=110.0)
EEP_A5_02_1A = _EEP_A5_02(_type=0x1A, scale_min=40.0, scale_max=120.0)
EEP_A5_02_1B = _EEP_A5_02(_type=0x1B, scale_min=50.0, scale_max=130.0)
EEP_A5_02_20 = _EEP_A5_02(_type=0x20, scale_min=-10.0, scale_max=41.2, ten_bit=True)
EEP_A5_02_30 = _EEP_A5_02(_type=0x30, scale_min=-40.0, scale_max=62.3, ten_bit=True)

__all__ = [
    "EEP_A5_02_01",
    "EEP_A5_02_02",
    "EEP_A5_02_03",
    "EEP_A5_02_04",
    "EEP_A5_02_05",
    "EEP_A5_02_06",
    "EEP_A5_02_07",
    "EEP_A5_02_08",
    "EEP_A5_02_09",
    "EEP_A5_02_0A",
    "EEP_A5_02_0B",
    "EEP_A5_02_10",
    "EEP_A5_02_11",
    "EEP_A5_02_12",
    "EEP_A5_02_13",
    "EEP_A5_02_14",
    "EEP_A5_02_15",
    "EEP_A5_02_16",
    "EEP_A5_02_17",
    "EEP_A5_02_18",
    "EEP_A5_02_19",
    "EEP_A5_02_1A",
    "EEP_A5_02_1B",
    "EEP_A5_02_20",
    "EEP_A5_02_30",
]
