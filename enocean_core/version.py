from dataclasses import dataclass

from enocean_core.address import EURID


@dataclass
class VersionIdentifier:
    main: int = 0
    beta: int = 0
    alpha: int = 0
    build: int = 0

    def versionString(self) -> str:
        return f"{self.main}.{self.beta}.{self.alpha}{f'b{self.build}' if self.build else ''}"


@dataclass
class VersionInfo:
    app_version: VersionIdentifier
    api_version: VersionIdentifier
    eurid: EURID
    device_version: int
    app_description: str
