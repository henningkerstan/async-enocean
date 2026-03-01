"""A5-20-01: Battery powered actuator (BI-DIR), HVAC valve.

Only the inbound direction (actuator → controller, status report) is decoded.
The outbound direction (controller → actuator, command) is not yet implemented.
"""

from ...capabilities.observable_uids import ObservableUID
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..profile import EEPDataField, SimpleProfileSpecification

EEP_A5_20_01 = SimpleProfileSpecification(
    eep=EEP.from_string("A5-20-01"),
    name="HVAC component – battery powered actuator (BI-DIR)",
    datafields=[
        # DB3: current valve position 0–100 %
        EEPDataField(
            id="CV",
            name="Current valve position",
            offset=0,
            size=8,
            range_min=0,
            range_max=100,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 100.0,
            unit_fn=lambda _: "%",
            observable_uid=ObservableUID.VALVE_POSITION,
        ),
        # DB2: status flags (8 individual bits)
        EEPDataField(
            id="SO",
            name="Service On",
            offset=8,
            size=1,
            range_enum={0: "Off", 1: "On"},
        ),
        EEPDataField(
            id="ENIE",
            name="Energy input enabled",
            offset=9,
            size=1,
            range_enum={0: "False", 1: "True"},
        ),
        EEPDataField(
            id="ES",
            name="Energy storage charged",
            offset=10,
            size=1,
            range_enum={0: "False", 1: "True"},
        ),
        EEPDataField(
            id="BCAP",
            name="Battery capacity low (change soon)",
            offset=11,
            size=1,
            range_enum={0: "True", 1: "False"},
        ),
        EEPDataField(
            id="CCO",
            name="Contact cover open",
            offset=12,
            size=1,
            range_enum={0: "False", 1: "True"},
        ),
        EEPDataField(
            id="FTS",
            name="Failure temperature sensor out of range",
            offset=13,
            size=1,
            range_enum={0: "False", 1: "True"},
        ),
        EEPDataField(
            id="DWO",
            name="Detection, window open",
            offset=14,
            size=1,
            range_enum={0: "False", 1: "True"},
        ),
        EEPDataField(
            id="ACO",
            name="Actuator obstructed",
            offset=15,
            size=1,
            range_enum={0: "False", 1: "True"},
        ),
        # DB1: temperature 0–255 raw → 0–40 °C
        EEPDataField(
            id="TMP",
            name="Temperature",
            offset=16,
            size=8,
            range_min=0,
            range_max=255,
            scale_min_fn=lambda _: 0.0,
            scale_max_fn=lambda _: 40.0,
            unit_fn=lambda _: "°C",
            observable_uid=ObservableUID.TEMPERATURE,
        ),
        # DB0.3: LRN bit
        EEPDataField(
            id="LRNB",
            name="LRN Bit",
            offset=28,
            size=1,
            range_enum={0: "Teach-in telegram", 1: "Data telegram"},
        ),
    ],
    capability_factories=[
        lambda addr, cb: ScalarCapability(
            device_address=addr,
            on_state_change=cb,
            observable_uid=ObservableUID.VALVE_POSITION,
        ),
        lambda addr, cb: ScalarCapability(
            device_address=addr,
            on_state_change=cb,
            observable_uid=ObservableUID.TEMPERATURE,
        ),
    ],
)

__all__ = ["EEP_A5_20_01"]
