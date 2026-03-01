"""A5-10-XX: Room Operating Panel (4BS telegram)."""

from ...capabilities.observable_uids import ObservableUID
from ...capabilities.scalar import ScalarCapability
from ..id import EEP
from ..profile import EEPDataField, SimpleProfileSpecification

# ---------------------------------------------------------------------------
# Shared enumerations
# ---------------------------------------------------------------------------

_FAN8_ENUM: dict[int, str] = {
    **{i: "Stage Auto" for i in range(210, 256)},
    **{i: "Stage 0" for i in range(190, 210)},
    **{i: "Stage 1" for i in range(165, 190)},
    **{i: "Stage 2" for i in range(145, 165)},
    **{i: "Stage 3" for i in range(0, 145)},
}

_FAN3_ENUM: dict[int, str] = {
    0: "Auto",
    1: "Speed 0",
    2: "Speed 1",
    3: "Speed 2",
    4: "Speed 3",
    5: "Speed 4",
    6: "Speed 5",
    7: "Off",
}

# Types 22-23: only 5 valid steps; 5...7 reserved
_FAN3_2223_ENUM: dict[int, str] = {
    0: "Auto",
    1: "Speed 0 / Off",
    2: "Speed 1",
    3: "Speed 2",
    4: "Speed 3",
}

_BUTTON_ENUM = {0: "Pressed", 1: "Released"}  # OCC, OB, UNOCC — all active-low buttons
_PRESENT_ENUM = {0: "Absent", 1: "Present"}  # TMP_F, SP_F, FAN_F presence flags
_OCC23_ENUM = {0: "Unoccupied", 1: "Occupied"}  # type 23: occupancy state, not button
_SLSW_ENUM = {0: "Night/Off", 1: "Day/On"}
_CTST_ENUM = {0: "Closed", 1: "Open"}
_OED_ENUM = {0: "Enabled", 1: "Disabled"}
_SPM_ENUM = {0: "Auto", 1: "Auto+User", 2: "Override", 3: "User"}
_BATT_ENUM = {0: "OK", 1: "Low"}
_ACT_ENUM = {0: "No action", 1: "User interaction"}

# ---------------------------------------------------------------------------
# Field factories
# ---------------------------------------------------------------------------


def _fan8() -> EEPDataField:
    """8-bit fan speed field (types 01–09, 1F)."""
    return EEPDataField(
        id="FAN",
        name="Fan speed",
        offset=0,
        size=8,
        range_enum=_FAN8_ENUM,
        observable_uid=ObservableUID.FAN_SPEED,
    )


def _fan3(offset: int) -> EEPDataField:
    """3-bit fan speed field (types 18–1D), 8 valid values."""
    return EEPDataField(
        id="FAN",
        name="Fan speed",
        offset=offset,
        size=3,
        range_enum=_FAN3_ENUM,
        observable_uid=ObservableUID.FAN_SPEED,
    )


def _fan3_2223(offset: int) -> EEPDataField:
    """3-bit fan speed field (types 22–23), values 5–7 reserved."""
    return EEPDataField(
        id="FAN",
        name="Fan speed",
        offset=offset,
        size=3,
        range_enum=_FAN3_2223_ENUM,
        observable_uid=ObservableUID.FAN_SPEED,
    )


def _sp8(offset: int) -> EEPDataField:
    """8-bit set point field."""
    return EEPDataField(
        id="SP",
        name="Set point",
        offset=offset,
        size=8,
        range_min=0,
        range_max=255,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 255.0,
        unit_fn=lambda _: "",
        observable_uid=ObservableUID.SET_POINT,
    )


def _sp6(offset: int) -> EEPDataField:
    """6-bit set point field (types 15–16)."""
    return EEPDataField(
        id="SP",
        name="Set point",
        offset=offset,
        size=6,
        range_min=0,
        range_max=63,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 63.0,
        unit_fn=lambda _: "",
        observable_uid=ObservableUID.SET_POINT,
    )


def _tmp_inv() -> EEPDataField:
    """Temperature for types 01–0D: 255→0 raw ↦ 0→40°C (inverted)."""
    return EEPDataField(
        id="TMP",
        name="Temperature",
        offset=16,
        size=8,
        range_min=255,
        range_max=0,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 40.0,
        unit_fn=lambda _: "°C",
        observable_uid=ObservableUID.TEMPERATURE,
    )


def _tmp_fwd() -> EEPDataField:
    """Temperature for types 10–14, 20–23: 0→250 raw ↦ 0→40°C (forward)."""
    return EEPDataField(
        id="TMP",
        name="Temperature",
        offset=16,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 40.0,
        unit_fn=lambda _: "°C",
        observable_uid=ObservableUID.TEMPERATURE,
    )


def _tmp_inv250() -> EEPDataField:
    """Temperature for types 18–1D: 250→0 raw ↦ 0→40°C (inverted)."""
    return EEPDataField(
        id="TMP",
        name="Temperature",
        offset=16,
        size=8,
        range_min=250,
        range_max=0,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 40.0,
        unit_fn=lambda _: "°C",
        observable_uid=ObservableUID.TEMPERATURE,
    )


def _tmp_inv255() -> EEPDataField:
    """Temperature for type 1F: 255→0 raw ↦ 0→40°C (inverted)."""
    return EEPDataField(
        id="TMP",
        name="Temperature",
        offset=16,
        size=8,
        range_min=255,
        range_max=0,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 40.0,
        unit_fn=lambda _: "°C",
        observable_uid=ObservableUID.TEMPERATURE,
    )


def _tmp10_inv() -> EEPDataField:
    """10-bit temperature for types 15–17: 1023→0 raw ↦ -10→41.2°C (inverted)."""
    return EEPDataField(
        id="TMP",
        name="Temperature",
        offset=14,
        size=10,
        range_min=1023,
        range_max=0,
        scale_min_fn=lambda _: -10.0,
        scale_max_fn=lambda _: 41.2,
        unit_fn=lambda _: "°C",
        observable_uid=ObservableUID.TEMPERATURE,
    )


def _tmpsp_inv250() -> EEPDataField:
    """Temperature setpoint for types 18–1D: 250→0 raw ↦ 0→40°C (inverted)."""
    return EEPDataField(
        id="TMPSP",
        name="Temperature set point",
        offset=8,
        size=8,
        range_min=250,
        range_max=0,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 40.0,
        unit_fn=lambda _: "°C",
        observable_uid=ObservableUID.TEMPERATURE_SETPOINT,
    )


def _hum() -> EEPDataField:
    return EEPDataField(
        id="HUM",
        name="Relative humidity",
        offset=8,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 100.0,
        unit_fn=lambda _: "%",
        observable_uid=ObservableUID.HUMIDITY,
    )


def _hum_db3() -> EEPDataField:
    """Humidity in DB3 (offset 0) for types 19, 1D, 21–23."""
    return EEPDataField(
        id="HUM",
        name="Relative humidity",
        offset=0,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 100.0,
        unit_fn=lambda _: "%",
        observable_uid=ObservableUID.HUMIDITY,
    )


def _humsp() -> EEPDataField:
    """Humidity setpoint for type 1D: 0→250 raw ↦ 0→100%."""
    return EEPDataField(
        id="HUMSP",
        name="Humidity set point",
        offset=8,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 100.0,
        unit_fn=lambda _: "%",
    )


def _ill() -> EEPDataField:
    """Illumination in DB3 (offset 0) for types 18, 1B, 1C."""
    return EEPDataField(
        id="ILL",
        name="Illumination",
        offset=0,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 1000.0,
        unit_fn=lambda _: "lx",
        observable_uid=ObservableUID.ILLUMINATION,
    )


def _illsp() -> EEPDataField:
    """Illumination setpoint for type 1C: 0→250 raw ↦ 0→1000 lx."""
    return EEPDataField(
        id="ILLSP",
        name="Illumination set point",
        offset=8,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 1000.0,
        unit_fn=lambda _: "lx",
    )


def _sv() -> EEPDataField:
    """Supply voltage in DB3 (offset 0) for types 1A, 1B."""
    return EEPDataField(
        id="SV",
        name="Supply voltage",
        offset=0,
        size=8,
        range_min=0,
        range_max=250,
        scale_min_fn=lambda _: 0.0,
        scale_max_fn=lambda _: 5.0,
        unit_fn=lambda _: "V",
        observable_uid=ObservableUID.VOLTAGE,
    )


def _lrnb() -> EEPDataField:
    return EEPDataField(
        id="LRNB",
        name="LRN Bit",
        offset=28,
        size=1,
        range_enum={0: "Teach-in telegram", 1: "Data telegram"},
    )


def _occ() -> EEPDataField:
    return EEPDataField(
        id="OCC",
        name="Occupancy button",
        offset=31,
        size=1,
        range_enum=_BUTTON_ENUM,
        observable_uid=ObservableUID.OCCUPANCY_BUTTON,
    )


def _occ23() -> EEPDataField:
    """Occupancy for type 23 (0=Unoccupied, 1=Occupied)."""
    return EEPDataField(
        id="OCC",
        name="Occupancy",
        offset=31,
        size=1,
        range_enum=_OCC23_ENUM,
        observable_uid=ObservableUID.OCCUPANCY_BUTTON,
    )


def _slsw() -> EEPDataField:
    return EEPDataField(
        id="SLSW",
        name="Day/Night switch",
        offset=31,
        size=1,
        range_enum=_SLSW_ENUM,
        observable_uid=ObservableUID.DAY_NIGHT,
    )


def _ctst() -> EEPDataField:
    return EEPDataField(
        id="CTST",
        name="Contact state",
        offset=31,
        size=1,
        range_enum=_CTST_ENUM,
        observable_uid=ObservableUID.CONTACT_STATE,
    )


def _oed(offset: int) -> EEPDataField:
    """Occupancy enable/disable flag."""
    return EEPDataField(
        id="OED",
        name="Occupancy enable/disable",
        offset=offset,
        size=1,
        range_enum=_OED_ENUM,
    )


def _ob(offset: int) -> EEPDataField:
    """Occupancy button for types 18–1D series."""
    return EEPDataField(
        id="OB",
        name="Occupancy button",
        offset=offset,
        size=1,
        range_enum=_BUTTON_ENUM,
        observable_uid=ObservableUID.OCCUPANCY_BUTTON,
    )


def _spm() -> EEPDataField:
    """Set point mode (2-bit) for types 20–21."""
    return EEPDataField(
        id="SPM",
        name="Set point mode",
        offset=25,
        size=2,
        range_enum=_SPM_ENUM,
    )


def _batt() -> EEPDataField:
    """Battery indicator for types 20–21."""
    return EEPDataField(
        id="BATT",
        name="Battery",
        offset=27,
        size=1,
        range_enum=_BATT_ENUM,
    )


def _act() -> EEPDataField:
    """User activity for types 20–21."""
    return EEPDataField(
        id="ACT",
        name="User activity",
        offset=31,
        size=1,
        range_enum=_ACT_ENUM,
    )


def _unocc() -> EEPDataField:
    """Unoccupancy button for type 1F (offset 30)."""
    return EEPDataField(
        id="UNOCC",
        name="Unoccupancy",
        offset=30,
        size=1,
        range_enum=_BUTTON_ENUM,
    )


def _tmp_f() -> EEPDataField:
    """Temperature present flag for type 1F (offset 25)."""
    return EEPDataField(
        id="TMP_F",
        name="Temperature flag",
        offset=25,
        size=1,
        range_enum=_PRESENT_ENUM,
    )


def _sp_f() -> EEPDataField:
    """Set point present flag for type 1F (offset 26)."""
    return EEPDataField(
        id="SP_F",
        name="Set point flag",
        offset=26,
        size=1,
        range_enum=_PRESENT_ENUM,
    )


def _fan_f() -> EEPDataField:
    """Fan speed present flag for type 1F (offset 27)."""
    return EEPDataField(
        id="FAN_F",
        name="Fan speed flag",
        offset=27,
        size=1,
        range_enum=_PRESENT_ENUM,
    )


# ---------------------------------------------------------------------------
# Capability factory helpers
# ---------------------------------------------------------------------------


def _cap(uid: str):
    return lambda addr, cb: ScalarCapability(
        device_address=addr, on_state_change=cb, observable_uid=uid
    )


_CAP_TMP = _cap(ObservableUID.TEMPERATURE)
_CAP_HUM = _cap(ObservableUID.HUMIDITY)
_CAP_SP = _cap(ObservableUID.SET_POINT)
_CAP_TMPSP = _cap(ObservableUID.TEMPERATURE_SETPOINT)
_CAP_FAN = _cap(ObservableUID.FAN_SPEED)
_CAP_OCC = _cap(ObservableUID.OCCUPANCY_BUTTON)
_CAP_SLSW = _cap(ObservableUID.DAY_NIGHT)
_CAP_CTST = _cap(ObservableUID.CONTACT_STATE)
_CAP_ILL = _cap(ObservableUID.ILLUMINATION)
_CAP_VOLT = _cap(ObservableUID.VOLTAGE)

# ---------------------------------------------------------------------------
# Profile builder
# ---------------------------------------------------------------------------


def _spec(
    type_id: int,
    name: str,
    datafields: list[EEPDataField],
    capability_factories: list,
) -> SimpleProfileSpecification:
    return SimpleProfileSpecification(
        eep=EEP.from_string(f"A5-10-{type_id:02X}"),
        name=name,
        datafields=datafields,
        capability_factories=capability_factories,
    )


# ---------------------------------------------------------------------------
# Types 01–0D — 8-bit temperature, inverted (255=0°C, 0=40°C)
# ---------------------------------------------------------------------------

EEP_A5_10_01 = _spec(
    0x01,
    "Room operating panel – temperature sensor, set point, fan speed and occupancy control",
    [_fan8(), _sp8(8), _tmp_inv(), _lrnb(), _occ()],
    [_CAP_FAN, _CAP_SP, _CAP_TMP, _CAP_OCC],
)

EEP_A5_10_02 = _spec(
    0x02,
    "Room operating panel – temperature sensor, set point, fan speed and day/night control",
    [_fan8(), _sp8(8), _tmp_inv(), _lrnb(), _slsw()],
    [_CAP_FAN, _CAP_SP, _CAP_TMP, _CAP_SLSW],
)

EEP_A5_10_03 = _spec(
    0x03,
    "Room operating panel – temperature sensor and set point control",
    [_sp8(8), _tmp_inv(), _lrnb()],
    [_CAP_SP, _CAP_TMP],
)

EEP_A5_10_04 = _spec(
    0x04,
    "Room operating panel – temperature sensor, set point and fan speed control",
    [_fan8(), _sp8(8), _tmp_inv(), _lrnb()],
    [_CAP_FAN, _CAP_SP, _CAP_TMP],
)

EEP_A5_10_05 = _spec(
    0x05,
    "Room operating panel – temperature sensor, set point and occupancy control",
    [_sp8(8), _tmp_inv(), _lrnb(), _occ()],
    [_CAP_SP, _CAP_TMP, _CAP_OCC],
)

EEP_A5_10_06 = _spec(
    0x06,
    "Room operating panel – temperature sensor, set point and day/night control",
    [_sp8(8), _tmp_inv(), _lrnb(), _slsw()],
    [_CAP_SP, _CAP_TMP, _CAP_SLSW],
)

EEP_A5_10_07 = _spec(
    0x07,
    "Room operating panel – temperature sensor and fan speed control",
    [_fan8(), _tmp_inv(), _lrnb()],
    [_CAP_FAN, _CAP_TMP],
)

EEP_A5_10_08 = _spec(
    0x08,
    "Room operating panel – temperature sensor, fan speed and occupancy control",
    [_fan8(), _tmp_inv(), _lrnb(), _occ()],
    [_CAP_FAN, _CAP_TMP, _CAP_OCC],
)

EEP_A5_10_09 = _spec(
    0x09,
    "Room operating panel – temperature sensor, fan speed and day/night control",
    [_fan8(), _tmp_inv(), _lrnb(), _slsw()],
    [_CAP_FAN, _CAP_TMP, _CAP_SLSW],
)

EEP_A5_10_0A = _spec(
    0x0A,
    "Room operating panel – temperature sensor, set point adjust and single input contact",
    [_sp8(8), _tmp_inv(), _lrnb(), _ctst()],
    [_CAP_SP, _CAP_TMP, _CAP_CTST],
)

EEP_A5_10_0B = _spec(
    0x0B,
    "Room operating panel – temperature sensor and single input contact",
    [_tmp_inv(), _lrnb(), _ctst()],
    [_CAP_TMP, _CAP_CTST],
)

EEP_A5_10_0C = _spec(
    0x0C,
    "Room operating panel – temperature sensor and occupancy control",
    [_tmp_inv(), _lrnb(), _occ()],
    [_CAP_TMP, _CAP_OCC],
)

EEP_A5_10_0D = _spec(
    0x0D,
    "Room operating panel – temperature sensor and day/night control",
    [_tmp_inv(), _lrnb(), _slsw()],
    [_CAP_TMP, _CAP_SLSW],
)

# ---------------------------------------------------------------------------
# Types 10–14 — 8-bit temperature forward (0=0°C, 250=40°C) + humidity
# ---------------------------------------------------------------------------

EEP_A5_10_10 = _spec(
    0x10,
    "Room operating panel – temperature and humidity sensor, set point and occupancy control",
    [_sp8(0), _hum(), _tmp_fwd(), _lrnb(), _occ()],
    [_CAP_SP, _CAP_HUM, _CAP_TMP, _CAP_OCC],
)

EEP_A5_10_11 = _spec(
    0x11,
    "Room operating panel – temperature and humidity sensor, set point and day/night control",
    [_sp8(0), _hum(), _tmp_fwd(), _lrnb(), _slsw()],
    [_CAP_SP, _CAP_HUM, _CAP_TMP, _CAP_SLSW],
)

EEP_A5_10_12 = _spec(
    0x12,
    "Room operating panel – temperature and humidity sensor and set point",
    [_sp8(0), _hum(), _tmp_fwd(), _lrnb()],
    [_CAP_SP, _CAP_HUM, _CAP_TMP],
)

EEP_A5_10_13 = _spec(
    0x13,
    "Room operating panel – temperature and humidity sensor, occupancy control",
    [_hum(), _tmp_fwd(), _lrnb(), _occ()],
    [_CAP_HUM, _CAP_TMP, _CAP_OCC],
)

EEP_A5_10_14 = _spec(
    0x14,
    "Room operating panel – temperature and humidity sensor, day/night control",
    [_hum(), _tmp_fwd(), _lrnb(), _slsw()],
    [_CAP_HUM, _CAP_TMP, _CAP_SLSW],
)

# ---------------------------------------------------------------------------
# Types 15–17 — 10-bit temperature, inverted (1023=−10°C, 0=41.2°C)
# ---------------------------------------------------------------------------

EEP_A5_10_15 = _spec(
    0x15,
    "Room operating panel – 10-bit temperature sensor and 6-bit set point",
    [_sp6(8), _tmp10_inv(), _lrnb()],
    [_CAP_SP, _CAP_TMP],
)

EEP_A5_10_16 = _spec(
    0x16,
    "Room operating panel – 10-bit temperature sensor, 6-bit set point and occupancy control",
    [_sp6(8), _tmp10_inv(), _lrnb(), _occ()],
    [_CAP_SP, _CAP_TMP, _CAP_OCC],
)

EEP_A5_10_17 = _spec(
    0x17,
    "Room operating panel – 10-bit temperature sensor and occupancy control",
    [_tmp10_inv(), _lrnb(), _occ()],
    [_CAP_TMP, _CAP_OCC],
)

# ---------------------------------------------------------------------------
# Types 18–1D — 8-bit temperature inverted (250=0°C, 0=40°C) + 3-bit fan
# ---------------------------------------------------------------------------

EEP_A5_10_18 = _spec(
    0x18,
    "Room operating panel – illumination, temperature set point, temperature, fan speed, occupancy",
    [_ill(), _tmpsp_inv250(), _tmp_inv250(), _fan3(25), _lrnb(), _oed(30), _ob(31)],
    [_CAP_ILL, _CAP_TMPSP, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

EEP_A5_10_19 = _spec(
    0x19,
    "Room operating panel – humidity, temperature set point, temperature, fan speed, occupancy",
    [_hum_db3(), _tmpsp_inv250(), _tmp_inv250(), _fan3(25), _lrnb(), _ob(30), _oed(31)],
    [_CAP_HUM, _CAP_TMPSP, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

EEP_A5_10_1A = _spec(
    0x1A,
    "Room operating panel – supply voltage, temperature set point, temperature, fan speed, occupancy",
    [_sv(), _tmpsp_inv250(), _tmp_inv250(), _fan3(25), _lrnb(), _oed(30), _ob(31)],
    [_CAP_VOLT, _CAP_TMPSP, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

EEP_A5_10_1B = _spec(
    0x1B,
    "Room operating panel – supply voltage, illumination, temperature, fan speed, occupancy",
    [_sv(), _ill(), _tmp_inv250(), _fan3(25), _lrnb(), _oed(30), _ob(31)],
    [_CAP_VOLT, _CAP_ILL, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

EEP_A5_10_1C = _spec(
    0x1C,
    "Room operating panel – illumination, illumination set point, temperature, fan speed, occupancy",
    [_ill(), _illsp(), _tmp_inv250(), _fan3(25), _lrnb(), _oed(30), _ob(31)],
    [_CAP_ILL, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

EEP_A5_10_1D = _spec(
    0x1D,
    "Room operating panel – humidity, humidity set point, temperature, fan speed, occupancy",
    [_hum_db3(), _humsp(), _tmp_inv250(), _fan3(25), _lrnb(), _oed(30), _ob(31)],
    [_CAP_HUM, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

EEP_A5_10_1E = _spec(
    0x1E,
    "Room operating panel – supply voltage, illumination, temperature, fan speed, occupancy (alias for 1B)",
    [_sv(), _ill(), _tmp_inv250(), _fan3(25), _lrnb(), _oed(30), _ob(31)],
    [_CAP_VOLT, _CAP_ILL, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

# ---------------------------------------------------------------------------
# Type 1F — 8-bit fan + set point + temperature inverted + presence flags
# ---------------------------------------------------------------------------

EEP_A5_10_1F = _spec(
    0x1F,
    "Room operating panel – fan speed, set point, temperature, occupancy and unoccupancy",
    [
        _fan8(),
        _sp8(8),
        _tmp_inv255(),
        _tmp_f(),
        _sp_f(),
        _fan_f(),
        _lrnb(),
        _unocc(),
        _occ(),
    ],
    [_CAP_FAN, _CAP_SP, _CAP_TMP, _CAP_OCC],
)

# ---------------------------------------------------------------------------
# Types 20–21 — set point + temperature (forward) + SPM + battery + activity
# ---------------------------------------------------------------------------

EEP_A5_10_20 = _spec(
    0x20,
    "Room operating panel – set point, temperature, set point mode, battery, user activity",
    [_sp8(0), _tmp_fwd(), _spm(), _batt(), _lrnb(), _act()],
    [_CAP_SP, _CAP_TMP],
)

EEP_A5_10_21 = _spec(
    0x21,
    "Room operating panel – set point, humidity, temperature, set point mode, battery, user activity",
    [_sp8(0), _hum(), _tmp_fwd(), _spm(), _batt(), _lrnb(), _act()],
    [_CAP_SP, _CAP_HUM, _CAP_TMP],
)

# ---------------------------------------------------------------------------
# Types 22–23 — set point + humidity + temperature (forward) + 3-bit fan
# ---------------------------------------------------------------------------

EEP_A5_10_22 = _spec(
    0x22,
    "Room operating panel – temperature, set point, humidity, fan speed",
    [_sp8(0), _hum(), _tmp_fwd(), _fan3_2223(24), _lrnb()],
    [_CAP_SP, _CAP_HUM, _CAP_TMP, _CAP_FAN],
)

EEP_A5_10_23 = _spec(
    0x23,
    "Room operating panel – temperature, set point, humidity, fan speed, occupancy",
    [_sp8(0), _hum(), _tmp_fwd(), _fan3_2223(24), _lrnb(), _occ23()],
    [_CAP_SP, _CAP_HUM, _CAP_TMP, _CAP_FAN, _CAP_OCC],
)

__all__ = [
    "EEP_A5_10_01",
    "EEP_A5_10_02",
    "EEP_A5_10_03",
    "EEP_A5_10_04",
    "EEP_A5_10_05",
    "EEP_A5_10_06",
    "EEP_A5_10_07",
    "EEP_A5_10_08",
    "EEP_A5_10_09",
    "EEP_A5_10_0A",
    "EEP_A5_10_0B",
    "EEP_A5_10_0C",
    "EEP_A5_10_0D",
    "EEP_A5_10_10",
    "EEP_A5_10_11",
    "EEP_A5_10_12",
    "EEP_A5_10_13",
    "EEP_A5_10_14",
    "EEP_A5_10_15",
    "EEP_A5_10_16",
    "EEP_A5_10_17",
    "EEP_A5_10_18",
    "EEP_A5_10_19",
    "EEP_A5_10_1A",
    "EEP_A5_10_1B",
    "EEP_A5_10_1C",
    "EEP_A5_10_1D",
    "EEP_A5_10_1E",
    "EEP_A5_10_1F",
    "EEP_A5_10_20",
    "EEP_A5_10_21",
    "EEP_A5_10_22",
    "EEP_A5_10_23",
]
