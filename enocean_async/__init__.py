"""
An async implementation of the EnOcean Serial Protocol Version 3.
"""

__version__ = "0.4.1"
__date__ = "2026-03-01"

from .address import EURID, Address, BaseAddress, BroadcastAddress, SenderAddress
from .capabilities.action import Action
from .capabilities.commands.base import Command
from .capabilities.commands.cover import QueryCoverPosition, SetCoverPosition, StopCover
from .capabilities.commands.dimmer import Dim
from .capabilities.commands.fan import SetFanSpeed
from .capabilities.commands.switch import (
    QueryActuatorMeasurement,
    QueryActuatorStatus,
    SetSwitchOutput,
)
from .capabilities.observable import Observable
from .capabilities.observation import (
    Observation,
    ObservationCallback,
    ObservationSource,
)
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
from .erp1.errors import ERP1ParseError
from .erp1.rorg import RORG
from .erp1.telegram import ERP1Telegram
from .gateway import Gateway

__all__ = [
    # Addresses
    "Address",
    "BaseAddress",
    "BroadcastAddress",
    "EURID",
    "SenderAddress",
    # Actions, Commands, and vocabulary
    "Action",
    "Command",
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
