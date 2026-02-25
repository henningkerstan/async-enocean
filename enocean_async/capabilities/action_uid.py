"""Stable semantic action UID constants for commands sent to devices."""


class ActionUID:
    """Stable names for actions that can be sent to devices.

    These are the canonical identifiers for things you can command a device to do —
    independent of the EEP spec field IDs. Analogous to ObservableUID but for the
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
