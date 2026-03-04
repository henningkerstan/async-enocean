"""Stable semantic action constants for commands sent to devices."""

from enum import StrEnum


class Action(StrEnum):
    """Stable names for actions that can be commanded to devices.

    These are the canonical identifiers for things you can command a device to do —
    independent of the EEP spec field IDs. Analogous to Observable but for the
    send direction.
    """

    # Cover / blind control (D2-05-00)
    SET_COVER_POSITION = "set_cover_position"
    STOP_COVER = "stop_cover"
    QUERY_COVER_POSITION = "query_cover_position"

    # Central command / dimming (A5-38-08)
    DIM = "dim"

    # Fan control (D2-20-02)
    SET_FAN_SPEED = "set_fan_speed"

    # Electronic switches and dimmers (D2-01)
    SET_SWITCH_OUTPUT = "set_switch_output"
    QUERY_ACTUATOR_STATUS = "query_actuator_status"
    QUERY_ACTUATOR_MEASUREMENT = "query_actuator_measurement"
