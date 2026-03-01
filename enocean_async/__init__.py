"""
An async implementation of the EnOcean Serial Protocol Version 3.
"""

__version__ = "0.4.0"
__date__ = "2026-03-01"

from .address import EURID, Address, BaseAddress, BroadcastAddress, SenderAddress
from .capabilities.action import Action
from .capabilities.action_uid import ActionUID
from .capabilities.cover_actions import (
    QueryCoverPositionAction,
    SetCoverPositionAction,
    StopCoverAction,
)
from .capabilities.dimmer_actions import DimAction
from .capabilities.fan_actions import SetFanSpeedAction
from .capabilities.observable_uids import ObservableUID
from .capabilities.state_change import (
    StateChange,
    StateChangeCallback,
    StateChangeSource,
)
from .capabilities.switch_actions import (
    QueryActuatorMeasurementAction,
    QueryActuatorStatusAction,
    SetSwitchOutputAction,
)
from .device.device import Device
from .eep import EEP_SPECIFICATIONS
from .eep.handler import EEPHandler
from .eep.id import EEP
from .eep.manufacturer import Manufacturer
from .eep.message import EEPMessage, EEPMessageType, EEPMessageValue, EntityValue
from .eep.profile import (
    EEPDataField,
    EEPSpecification,
    EEPTelegram,
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
    # Actions and vocabulary
    "Action",
    "ActionUID",
    "DimAction",
    "ObservableUID",
    "QueryActuatorMeasurementAction",
    "QueryActuatorStatusAction",
    "QueryCoverPositionAction",
    "SetCoverPositionAction",
    "SetFanSpeedAction",
    "SetSwitchOutputAction",
    "StopCoverAction",
    # State changes
    "StateChange",
    "StateChangeCallback",
    "StateChangeSource",
    # Device and gateway
    "Device",
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
