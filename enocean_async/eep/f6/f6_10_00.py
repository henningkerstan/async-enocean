from enocean_async.eep.manufacturer import Manufacturer

from ...capabilities.observable import Observable
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..profile import EEPDataField, SimpleProfileSpecification

_WIN_FACTORIES = [
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.WINDOW_STATE,
    ),
]

EEP_F6_10_00 = SimpleProfileSpecification(
    eep=EEP.from_string("F6-10-00"),
    name="Window handle",
    datafields=[
        EEPDataField(
            id="WIN",
            name="Window state",
            offset=2,
            size=2,
            # the EEP spec has a lot of different variants of the window handle state; for brevity and clarity we use the resulting state of the window
            range_enum={
                0: "open",  # was tilted, now open
                1: "tilted",  # tilted open
                2: "open",  # was closed, now open
                3: "closed",  # "window now closed"
            },
            observable=Observable.WINDOW_STATE,
        ),
    ],
    capability_factories=_WIN_FACTORIES,
)

EEP_F6_10_00_ELTAKO = SimpleProfileSpecification(
    eep=EEP(rorg=0xF6, func=0x10, type_=0x00, manufacturer=Manufacturer.ELTAKO),
    name="Window handle (Eltako variant)",
    datafields=[
        EEPDataField(
            id="WIN",
            name="Window state",
            offset=0,
            size=8,
            range_enum={
                0xD0: "tilted",
                0xE0: "open",
                0xF0: "closed",
            },
            observable=Observable.WINDOW_STATE,
        ),
    ],
    capability_factories=_WIN_FACTORIES,
)
