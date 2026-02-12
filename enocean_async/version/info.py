from dataclasses import dataclass

from ..erp1.address import EURID
from .id import VersionIdentifier


@dataclass
class VersionInfo:
    app_version: VersionIdentifier
    api_version: VersionIdentifier
    eurid: EURID
    device_version: int
    app_description: str
