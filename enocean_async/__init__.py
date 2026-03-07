"""
An async implementation of the EnOcean Serial Protocol Version 3.
"""

__version__ = "0.5.0"
__date__ = "2026-03-06"

from .address import EURID, BaseAddress, BroadcastAddress, SenderAddress
from .device import Device
from .eep.id import EEP
from .eep.profile import DeviceDescriptor
from .gateway import Gateway
from .semantics.entity_type import EntityType
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
from .semantics.value_kind import ValueKind

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
    "EntityType",
    "Observable",
    "Observation",
    "ObservationCallback",
    "ObservationSource",
    "ValueKind",
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
