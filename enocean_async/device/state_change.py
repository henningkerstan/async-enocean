from dataclasses import dataclass

from ..address import SenderAddress


@dataclass
class StateChange:
    """A semantic update emitted by a Capability."""

    device_address: SenderAddress
    capability_uid: str
    attribute: str
    value: any
    meta: dict[str, any] = {}
