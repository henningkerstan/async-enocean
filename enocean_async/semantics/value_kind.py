"""Value kind classification for Observable members."""

from enum import StrEnum


class ValueKind(StrEnum):
    """Describes the nature of the value produced by an Observable.

    - ``SCALAR``: a continuous numeric measurement (temperature, rssi, power, …).
    - ``BINARY``: a two-state value (motion detected / not, on / off, open / closed).
    - ``ENUM``: a multi-value named set (cover_state, window_state, push_button, …).
    """

    SCALAR = "scalar"
    BINARY = "binary"
    ENUM = "enum"
