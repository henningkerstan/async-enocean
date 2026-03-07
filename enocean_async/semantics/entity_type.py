"""Entity type classification for Entity descriptors."""

from enum import StrEnum


class EntityType(StrEnum):
    """The physical/functional type of a device entity.

    Describes what kind of real-world thing the entity represents, using
    library-semantic names independent of any integration platform vocabulary.
    An integration maps these to its own platform concepts (e.g. HA maps
    ``PUSH_BUTTON`` → ``event`` platform, ``BINARY`` → ``binary_sensor``).

    Computed from an entity's ``observables`` and ``actions`` via
    ``Entity.entity_type``.  No separate declaration needed in EEP files.
    """

    SENSOR = "sensor"  # read-only continuous scalar (temperature, illumination, …)
    BINARY = "binary"  # read-only two-state (motion, contact, switch status, …)
    SWITCH = "switch"  # controllable on/off relay
    COVER = "cover"  # position-controllable cover / blind
    PUSH_BUTTON = "push_button"  # multi-value button events (a0, b1, ab0, …)
    DIMMER = "dimmer"  # controllable dimmer / PWM output
    FAN = "fan"  # fan speed control
    METADATA = "metadata"  # infrastructure: rssi, last_seen, telegram_count
