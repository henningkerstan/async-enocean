"""Stable semantic observable constants shared across capabilities and EEP definitions."""

from enum import Enum

from .value_kind import ValueKind

_S = ValueKind.SCALAR
_B = ValueKind.BINARY
_E = ValueKind.ENUM


class Observable(str, Enum):
    """Stable names for observable quantities exposed by devices.

    Each member has three intrinsic properties:
    - Its string value (the semantic id, e.g. "temperature") — used as dict key and in comparisons.
    - ``unit`` — the physical unit for that quantity (``None`` for dimensionless
      or categorical values). Units are domain-conventional (IoT / building automation domain),
      not necessarily SI base units (e.g. °C rather than K, Wh rather than J).
    - ``kind`` — the nature of the value: ``SCALAR`` (continuous numeric), ``BINARY``
      (two-state), or ``ENUM`` (multi-value named set).
    """

    def __new__(
        cls, value: str, unit: str | None = None, kind: ValueKind = ValueKind.SCALAR
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.unit = unit
        obj.kind = kind
        return obj

    # Sensor values
    TEMPERATURE = ("temperature", "°C", _S)
    HUMIDITY = ("humidity", "%", _S)
    ILLUMINATION = ("illumination", "lx", _S)
    MOTION = ("motion", None, _B)
    VOLTAGE = ("voltage", "V", _S)

    # Cover / blind control
    POSITION = ("position", "%", _S)
    ANGLE = ("angle", "%", _S)
    COVER_STATE = ("cover_state", None, _E)

    # Window handle
    WINDOW_STATE = ("window_state", None, _E)

    # Switch / dimmer actuator
    SWITCH_STATE = ("switch_state", None, _B)
    OUTPUT_VALUE = ("output_value", "%", _S)
    ERROR_LEVEL = ("error_level", None, _B)
    PILOT_WIRE_MODE = ("pilot_wire_mode", None, _E)
    ENERGY = ("energy", "Wh", _S)
    POWER = ("power", "W", _S)

    # Button / occupancy / contact
    PUSH_BUTTON = ("push_button", None, _E)
    CONTACT_STATE = ("contact_state", None, _B)
    DAY_NIGHT = ("day_night", None, _B)
    OCCUPANCY_BUTTON = ("occupancy_button", None, _B)

    # Room operating panel controls
    FAN_SPEED = ("fan_speed", None, _S)
    SET_POINT = ("set_point", None, _S)
    TEMPERATURE_SETPOINT = ("temperature_setpoint", "°C", _S)

    # HVAC actuator
    VALVE_POSITION = ("valve_position", "%", _S)

    # Metadata
    RSSI = ("rssi", "dBm", _S)
    LAST_SEEN = ("last_seen", None, _S)
    TELEGRAM_COUNT = ("telegram_count", None, _S)
