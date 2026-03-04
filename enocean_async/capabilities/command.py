"""Base class for typed device commands on the send pipeline."""

from dataclasses import dataclass


@dataclass
class Command:
    """Base class for all typed device commands.

    Subclasses declare a class-level ``action`` (ClassVar[str]) matching an
    ``Action`` constant, plus typed fields for every parameter the command requires.
    The corresponding EEP encoder receives the Command instance directly and translates
    its typed fields into raw EEP field values.
    """
