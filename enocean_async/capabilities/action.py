"""Base class for typed device actions on the send pipeline."""

from dataclasses import dataclass


@dataclass
class Action:
    """Base class for all typed device actions.

    Subclasses declare a class-level ``action_uid`` (ClassVar[str]) matching an
    ``ActionUID`` constant, plus typed fields for every parameter the action requires.
    The corresponding EEP encoder receives the Action instance directly and translates
    its typed fields into raw EEP field values.
    """
