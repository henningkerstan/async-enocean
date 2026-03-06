"""
An async implementation of the EnOcean Serial Protocol Version 3.
"""

__version__ = "0.4.1"
__date__ = "2026-03-01"

from .address import EURID, Address, BaseAddress, BroadcastAddress, SenderAddress
from .device.device import Device
from .eep import EEP_SPECIFICATIONS
from .eep.handler import EEPHandler
from .eep.id import EEP
from .eep.manufacturer import Manufacturer
from .eep.message import EEPMessage, EEPMessageType, EEPMessageValue, EntityValue
from .eep.profile import (
    DeviceDescriptor,
    EEPDataField,
    EEPSpecification,
    EEPTelegram,
    Entity,
    SimpleProfileSpecification,
)
from .gateway import Gateway
from .protocol.erp1.errors import ERP1ParseError
from .protocol.erp1.rorg import RORG
from .protocol.erp1.telegram import ERP1Telegram
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
    # Addresses
    "Address",
    "BaseAddress",
    "BroadcastAddress",
    "EURID",
    "SenderAddress",
    # Actions, Commands, and vocabulary
    "Instructable",
    "Instruction",
    "Dim",
    "Observable",
    "QueryActuatorMeasurement",
    "QueryActuatorStatus",
    "QueryCoverPosition",
    "SetCoverPosition",
    "SetFanSpeed",
    "SetSwitchOutput",
    "StopCover",
    # State changes
    "Observation",
    "ObservationCallback",
    "ObservationSource",
    "Entity",
    # Device and gateway
    "Device",
    "DeviceDescriptor",
    "Gateway",
    # EEP layer
    "EEP",
    "EEPDataField",
    "EEPHandler",
    "EEPMessage",
    "EEPMessageType",
    "EEPMessageValue",
    "EEPSpecification",
    "EEPTelegram",
    "EEP_SPECIFICATIONS",
    "EntityValue",
    "Manufacturer",
    "SimpleProfileSpecification",
    # ERP1
    "ERP1ParseError",
    "ERP1Telegram",
    "RORG",
]
