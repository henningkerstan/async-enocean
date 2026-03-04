"""A5-06-XX: Light sensors."""

from ...capabilities.observable import Observable
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..manufacturer import Manufacturer
from ..message import EEPMessageValue
from ..profile import EEPDataField, SimpleProfileSpecification


def _a5_06_illumination_resolver(
    values: dict[str, EEPMessageValue],
) -> EEPMessageValue | None:
    """Select the illumination value for standard A5-06 variants using the RS range-select field."""
    rs = values.get("RS")
    ill1 = values.get("ILL1")
    ill2 = values.get("ILL2")
    if rs is not None:
        return ill1 if rs.raw == 0 else ill2

    return ill2 or ill1


def _a5_06_eltako_illumination_resolver(
    values: dict[str, EEPMessageValue],
) -> EEPMessageValue | None:
    """Select the illumination value for the Eltako A5-06-01 variant.

    Uses ILL1 (low range) when ILL2 is at its minimum raw value (0), otherwise ILL2 (high range).
    """
    ill1 = values.get("ILL1")
    ill2 = values.get("ILL2")
    if ill2 is not None and ill2.raw == 0:
        return ill1
    return ill2 or ill1


_ILL_FACTORY = [
    lambda addr, cb: ScalarCapability(
        device_address=addr,
        on_state_change=cb,
        observable=Observable.ILLUMINATION,
    ),
]


class _EEP_A5_06(SimpleProfileSpecification):
    def __init__(
        self,
        _type: int,
        ill2_min: float,
        ill2_max: float,
        ill1_min: float,
        ill1_max: float,
    ):
        super().__init__(
            eep=EEP.from_string(f"A5-06-{_type:02X}"),
            name=f"Light sensor, range {min(ill1_min, ill2_min)}lx to {max(ill1_max, ill2_max)}lx",
            datafields=[
                EEPDataField(
                    id="SVC",
                    name="Supply voltage",
                    offset=0,
                    size=8,
                    scale_min_fn=lambda _: 0.0,
                    scale_max_fn=lambda _: 5.1,
                    unit_fn=lambda _: "V",
                ),
                EEPDataField(
                    id="ILL2",
                    name="Illumination",
                    offset=8,
                    size=8,
                    scale_min_fn=lambda _: ill2_min,
                    scale_max_fn=lambda _: ill2_max,
                    unit_fn=lambda _: "lx",
                ),
                EEPDataField(
                    id="ILL1",
                    name="Illumination",
                    offset=16,
                    size=8,
                    scale_min_fn=lambda _: ill1_min,
                    scale_max_fn=lambda _: ill1_max,
                    unit_fn=lambda _: "lx",
                ),
                EEPDataField(
                    id="RS",
                    name="Range select",
                    offset=31,
                    size=1,
                    range_enum={
                        0: "Use ILL1",
                        1: "Use ILL2",
                    },
                ),
            ],
            semantic_resolvers={Observable.ILLUMINATION: _a5_06_illumination_resolver},
            capability_factories=_ILL_FACTORY,
        )


EEP_A5_06_01 = _EEP_A5_06(
    _type=0x01, ill2_min=300.0, ill2_max=30000.0, ill1_min=600.0, ill1_max=60000.0
)
EEP_A5_06_02 = _EEP_A5_06(
    _type=0x02, ill2_min=0.0, ill2_max=510.0, ill1_min=0.0, ill1_max=1020.0
)
EEP_A5_06_05 = _EEP_A5_06(
    _type=0x05, ill2_min=0.0, ill2_max=5100.0, ill1_min=0.0, ill1_max=10200.0
)

EEP_A5_06_03 = SimpleProfileSpecification(
    eep=EEP.from_string(f"A5-06-03"),
    name=f"Light sensor, 10-bit measurement, range 0lx to 1000lx",
    datafields=[
        EEPDataField(
            id="SVC",
            name="Supply voltage",
            offset=0,
            size=8,
            range_max=250,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 5.0,
            unit_fn=lambda _: "V",
        ),
        EEPDataField(
            id="ILL",
            name="Illumination",
            offset=8,
            size=10,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 1000.0,
            unit_fn=lambda _: "lx",
            observable=Observable.ILLUMINATION,
        ),
    ],
    capability_factories=_ILL_FACTORY,
)

EEP_A5_06_04 = SimpleProfileSpecification(
    eep=EEP.from_string(f"A5-06-04"),
    name=f"Curtain wall brightness sensor",
    datafields=[
        EEPDataField(
            id="TEMP",
            name="Ambient temperature",
            offset=0,
            size=8,
            scale_min_fn=lambda _: -20.0,
            scale_max_fn=lambda _: 60.0,
            unit_fn=lambda _: "°C",
            observable=Observable.TEMPERATURE,
        ),
        EEPDataField(
            id="ILL",
            name="Illuminance",
            offset=8,
            size=16,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 65535.0,
            unit_fn=lambda _: "lx",
            observable=Observable.ILLUMINATION,
        ),
        EEPDataField(
            id="SV",
            name="Energy storage",
            offset=24,
            size=4,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 100.0,
            unit_fn=lambda _: "%",
        ),
        EEPDataField(
            id="TMPAV",
            name="Temperature availability",
            offset=30,
            size=1,
            range_enum={
                0: "Temperature unavailable",
                1: "Temperature available",
            },
        ),
        EEPDataField(
            id="ENAV",
            name="Energy storage availability",
            offset=31,
            size=1,
            range_enum={
                0: "Energy storage unavailable",
                1: "Energy storage available",
            },
        ),
    ],
    capability_factories=[
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
    ],
)

EEP_A5_06_01_ELTAKO = SimpleProfileSpecification(
    eep=EEP(rorg=0xA5, func=0x06, type_=0x01, manufacturer=Manufacturer.ELTAKO),
    name="Light sensor (Eltako variant), dual-range 0–100lx / 300–30000lx",
    datafields=[
        EEPDataField(
            id="ILL1",
            name="Illumination",
            offset=0,
            size=8,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 100.0,
            unit_fn=lambda _: "lx",
        ),
        EEPDataField(
            id="ILL2",
            name="Illumination",
            offset=8,
            size=8,
            scale_min_fn=lambda _: 300.0,
            scale_max_fn=lambda _: 30000.0,
            unit_fn=lambda _: "lx",
        ),
    ],
    semantic_resolvers={Observable.ILLUMINATION: _a5_06_eltako_illumination_resolver},
    capability_factories=_ILL_FACTORY,
)

__all__ = [
    "EEP_A5_06_01",
    "EEP_A5_06_01_ELTAKO",
    "EEP_A5_06_02",
    "EEP_A5_06_03",
    "EEP_A5_06_04",
    "EEP_A5_06_05",
]
