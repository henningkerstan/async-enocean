from dataclasses import dataclass
from enum import IntEnum
from typing import Literal

from ..message import EEPMessage


class OperatingModeStatus(IntEnum):
    DISABLED = (0,)
    STANDARD_COMPLIANT = (1,)
    NOT_SUPPORTED = 15


class ServiceInformation(IntEnum):
    NOTHING_TO_REPORT = (0,)
    AIR_FILTER_ERROR = (1,)
    HARDWARE_ERROR = (2,)
    NOT_SUPPORTED = 7


class HumidityControlStatus(IntEnum):
    DISABLED = (0,)
    ENABLED = (1,)
    RESERVED = (2,)
    NOT_SUPPORTED = 3


class RoomSizeReference(IntEnum):
    USED = (0,)
    NOT_USED = (1,)
    RESERVED = (3,)
    NOT_SUPPORTED = 3


class RoomSizeStatus(IntEnum):
    BELOW_25 = 0  # < 25 m²
    FROM_25_TO_50 = 1  # 25...50 m²
    FROM_50_TO_75 = 2  # 50...75 m²
    FROM_75_TO_100 = 3  # 75...100 m²
    FROM_100_TO_125 = 4  # 100...125 m²
    FROM_125_TO_150 = 5  # 125...150 m²
    FROM_150_TO_175 = 6  # 150...175 m²
    FROM_175_TO_200 = 7  # 175...200 m²
    FROM_200_TO_225 = 8  # 200...225 m²
    FROM_225_TO_250 = 9  # 225...250 m²
    FROM_250_TO_275 = 10  # 250...275 m²
    FROM_275_TO_300 = 11  # 275...300 m²
    FROM_300_TO_325 = 12  # 300...325 m²
    FROM_325_TO_350 = 13  # 325...350 m²
    ABOVE_350 = 14  # > 350 m²
    NOT_SUPPORTED = 15  # Not supported


@dataclass
class D20000FanStatusMessage(EEPMessage):
    operating_mode_status: OperatingModeStatus | None
    service_information: ServiceInformation | None
    message_type: Literal["fan status"] = "fan status"
    humidity_control_status: HumidityControlStatus
    room_size_reference: RoomSizeReference
    room_size_status: RoomSizeStatus
    humidity: int | None
    fan_speed: int | None
