from dataclasses import dataclass

from ..address import EURID
from .id import VersionIdentifier


@dataclass
class VersionInfo:
    app_version: VersionIdentifier
    api_version: VersionIdentifier
    eurid: EURID
    device_version: int
    app_description: str
