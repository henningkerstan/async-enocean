from dataclasses import dataclass


@dataclass
class VersionIdentifier:
    main: int = 0
    beta: int = 0
    alpha: int = 0
    build: int = 0

    @property
    def version_string(self) -> str:
        return f"{self.main}.{self.beta}.{self.alpha}{f'b{self.build}' if self.build else ''}"
