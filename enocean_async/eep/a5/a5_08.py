"""A5-08-XX: Light, temperature and occupancy sensors."""

from ...capabilities.observable import Observable
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..manufacturer import Manufacturer
from ..profile import EEPDataField, SimpleProfileSpecification

_FULL_FACTORIES = [
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.VOLTAGE,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.ILLUMINATION,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.TEMPERATURE,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.MOTION,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.OCCUPANCY_BUTTON,
    ),
]

_ELTAKO_FACTORIES = [
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.VOLTAGE,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.ILLUMINATION,
    ),
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.MOTION,
    ),
]


class _EEP_A5_08(SimpleProfileSpecification):
    def __init__(self, _type: int, ill_max: float, temp_min: float, temp_max: float):
        super().__init__(
            eep=EEP.from_string(f"A5-08-{_type:02X}"),
            name=f"Light, temperature and occupancy sensor, range 0lx to {ill_max}lx, {temp_min}°C to {temp_max}°C and occupancy button",
            datafields=[
                EEPDataField(
                    id="SVC",
                    name="Supply voltage",
                    offset=0,
                    size=8,
                    scale_min_fn=lambda _: 0.0,
                    scale_max_fn=lambda _: 5.1,
                    unit_fn=lambda _: "V",
                    observable=Observable.VOLTAGE,
                ),
                EEPDataField(
                    id="ILL",
                    name="Illumination",
                    offset=8,
                    size=8,
                    scale_min_fn=lambda _: 0,
                    scale_max_fn=lambda _: ill_max,
                    unit_fn=lambda _: "lx",
                    observable=Observable.ILLUMINATION,
                ),
                EEPDataField(
                    id="TMP",
                    name="Temperature",
                    offset=16,
                    size=8,
                    scale_min_fn=lambda _: temp_min,
                    scale_max_fn=lambda _: temp_max,
                    unit_fn=lambda _: "°C",
                    observable=Observable.TEMPERATURE,
                ),
                EEPDataField(
                    id="PIRS",
                    name="PIR status",
                    offset=30,
                    size=1,
                    range_enum={
                        0: "motion",
                        1: "no motion",
                    },
                    observable=Observable.MOTION,
                ),
                EEPDataField(
                    id="OCC",
                    name="Occupancy button",
                    offset=31,
                    size=1,
                    range_enum={
                        0: "pressed",
                        1: "released",
                    },
                    observable=Observable.OCCUPANCY_BUTTON,
                ),
            ],
            capability_factories=_FULL_FACTORIES,
        )


EEP_A5_08_01 = _EEP_A5_08(_type=0x01, ill_max=510, temp_min=0.0, temp_max=51.0)
EEP_A5_08_02 = _EEP_A5_08(_type=0x02, ill_max=1020, temp_min=0.0, temp_max=51.0)
EEP_A5_08_03 = _EEP_A5_08(_type=0x03, ill_max=1530, temp_min=-30.0, temp_max=50.0)

EEP_A5_08_01_ELTAKO = SimpleProfileSpecification(
    eep=EEP(0xA5, 0x08, 0x01, Manufacturer.ELTAKO),
    name="Light and occupancy sensor, range 0lx to 510lx, Eltako variant (FABH65S, FBH65, FBH65TF, FBH65SB, FBH55SB, FBHF65SB, F4USM61B)",
    datafields=[
        EEPDataField(
            id="SVC",
            name="Supply voltage",
            offset=0,
            size=8,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 5.1,
            unit_fn=lambda _: "V",
            observable=Observable.VOLTAGE,
        ),
        EEPDataField(
            id="ILL",
            name="Illumination",
            offset=8,
            size=8,
            scale_min_fn=lambda _: 0,
            scale_max_fn=lambda _: 510,
            unit_fn=lambda _: "lx",
            observable=Observable.ILLUMINATION,
        ),
        EEPDataField(
            id="PIRS",
            name="PIR status",
            offset=24,
            size=8,
            range_enum={
                0x0D: "motion",
                0x0F: "no motion",
            },
            observable=Observable.MOTION,
        ),
    ],
    capability_factories=_ELTAKO_FACTORIES,
)
