"""
An async implementation of the EnOcean Serial Protocol Version 3.
"""

__version__ = "0.4.1"
__date__ = "2026-03-01"

from .address import EURID, BaseAddress, BroadcastAddress, SenderAddress
from .device import Device
from .eep.id import EEP
from .eep.profile import DeviceDescriptor
from .gateway import Gateway
from .semantics.instructable import Instructable
from .semantics.instruction import Instruction
from .semantics.instructions.cover import (
    QueryCoverPosition,
    SetCoverPosition,
    StopCover,
)
from .semantics.instructions.dimmer import Dim
from .semantics.instructions.fan import SetFanSpeed
from .semantics.instructions.switch import (
    QueryActuatorMeasurement,
    QueryActuatorStatus,
    SetSwitchOutput,
)
from .semantics.observable import Observable
from .semantics.observation import Observation, ObservationCallback, ObservationSource

__all__ = [
    # Gateway
    "Gateway",
    # Addresses
    "BaseAddress",
    "BroadcastAddress",
    "EURID",
    "SenderAddress",
    # Device
    "Device",
    "DeviceDescriptor",
    "EEP",
    # Receive side
    "Observable",
    "Observation",
    "ObservationCallback",
    "ObservationSource",
    # Send side
    "Instructable",
    "Instruction",
    "Dim",
    "QueryActuatorMeasurement",
    "QueryActuatorStatus",
    "QueryCoverPosition",
    "SetCoverPosition",
    "SetFanSpeed",
    "SetSwitchOutput",
    "StopCover",
]
