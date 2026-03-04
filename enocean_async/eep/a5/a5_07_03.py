"""A5-07-03: Occupancy with supply voltage monitor and 10-bit illumination measurement."""

from ...capabilities.observable import Observable
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..profile import EEPDataField, SimpleProfileSpecification

EEP_A5_07_03 = SimpleProfileSpecification(
    eep=EEP.from_string("A5-07-03"),
    name="Occupancy with supply voltage monitor and 10-bit illumination measurement",
    datafields=[
        EEPDataField(
            id="SVC",
            name="Supply voltage",
            offset=0,
            size=8,
            range_min=0,
            range_max=250,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 5.0,
            unit_fn=lambda _: "V",
            observable=Observable.VOLTAGE,
        ),
        EEPDataField(
            id="ILL",
            name="Illumination",
            offset=8,
            size=10,
            range_min=0,
            range_max=1000,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 1000.0,
            unit_fn=lambda _: "lx",
            observable=Observable.ILLUMINATION,
        ),
        EEPDataField(
            id="PIR",
            name="PIR status",
            offset=24,
            size=1,
            range_enum={
                0: "Uncertain of occupancy status",
                1: "Motion detected",
            },
            observable=Observable.MOTION,
        ),
    ],
    capability_factories=[
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
    ],
)
