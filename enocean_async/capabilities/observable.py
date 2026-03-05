"""Stable semantic observable constants shared across capabilities and EEP definitions."""

from enum import Enum


class Observable(str, Enum):
    """Stable names for observable quantities exposed by devices.

    Each member has two intrinsic properties:
    - Its string value (the semantic id, e.g. "temperature") — used as dict key and in comparisons.
    - ``unit`` — the one canonical physical unit for that quantity (``None`` for dimensionless
      or categorical values). Units are domain-conventional, not necessarily SI base units
      (e.g. °C rather than K, Wh rather than J).

    Observable names are semantic, not unit-encoding: the name says *what* is observed,
    not *how* it is expressed. The unit is always ``observable.unit``.
    """

    def __new__(cls, value: str, unit: str | None = None):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.unit = unit
        return obj

    # Sensor values
    TEMPERATURE = ("temperature", "°C")
    HUMIDITY = ("humidity", "%")
    ILLUMINATION = ("illumination", "lx")
    MOTION = ("motion", None)
    VOLTAGE = ("voltage", "V")

    # Cover / blind control
    POSITION = ("position", "%")
    ANGLE = ("angle", "%")
    COVER_STATE = ("cover_state", None)

    # Window handle
    WINDOW_STATE = ("window_state", None)

    # Switch / dimmer actuator
    SWITCH_STATE = ("switch_state", None)
    OUTPUT_VALUE = ("output_value", "%")
    ERROR_LEVEL = ("error_level", None)
    PILOT_WIRE_MODE = ("pilot_wire_mode", None)
    ENERGY = ("energy", "Wh")
    POWER = ("power", "W")

    # Button / occupancy / contact
    PUSH_BUTTON = ("push_button", None)
    CONTACT_STATE = ("contact_state", None)
    DAY_NIGHT = ("day_night", None)
    OCCUPANCY_BUTTON = ("occupancy_button", None)

    # Room operating panel controls
    FAN_SPEED = ("fan_speed", None)
    SET_POINT = ("set_point", None)
    TEMPERATURE_SETPOINT = ("temperature_setpoint", "°C")

    # HVAC actuator
    VALVE_POSITION = ("valve_position", "%")

    # Metadata
    RSSI = ("rssi", "dBm")
    LAST_SEEN = ("last_seen", None)
    TELEGRAM_COUNT = ("telegram_count", None)
