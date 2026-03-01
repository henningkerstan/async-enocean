"""Stable semantic observable UID constants shared across capabilities and EEP definitions."""


class ObservableUID:
    """Stable names for observable quantities exposed by devices.

    These are the canonical identifiers for things you can observe from a device —
    whether the device is a pure sensor (temperature, illumination) or an actuator
    reporting its own state (position, cover_state, window_state). Independent of
    the EEP spec field IDs (which may vary across profiles: 'TMP', 'TEMP', 'T', …).
    """

    # Sensor values
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    ILLUMINATION = "illumination"
    MOTION = "motion"
    VOLTAGE = "voltage"

    # Cover / blind control
    POSITION = "position"
    ANGLE = "angle"
    COVER_STATE = "cover_state"

    # Window handle
    WINDOW_STATE = "window_state"

    # Switch / dimmer actuator
    SWITCH_STATE = "switch_state"
    OUTPUT_VALUE = "output_value"
    ERROR_LEVEL = "error_level"
    PILOT_WIRE_MODE = "pilot_wire_mode"
    ENERGY = "energy"
    POWER = "power"

    # Button / occupancy
    OCCUPANCY_BUTTON = "occupancy_button"

    # Metadata
    RSSI = "rssi"
    LAST_SEEN = "last_seen"
    TELEGRAM_COUNT = "telegram_count"
