"""Device types for A5-04-XX temperature and humidity sensor profiles."""

from dataclasses import dataclass

from ....capabilities.humidity_sensor import HumiditySensorCapability
from ....capabilities.metadata import MetaDataCapability
from ....capabilities.temperature_sensor import TemperatureSensorCapability
from ....eep.id import EEPID
from ...type import DeviceType


@dataclass
class DeviceTypeA5_04(DeviceType):
    """Device type for A5-04-XX temperature and humidity sensor variants."""

    def __init__(self, type_: int, min: float, max: float, ten_bit: bool = False):
        type_suffix = f"{type_:02X}"
        super().__init__(
            eepid=EEPID.from_string(f"A5-04-{type_suffix}"),
            uid=f"a5-04-{type_suffix.lower()}",
            model=f"Temperature and humidity sensor, range {min}°C to {max}°C {'10bit measurement ' if ten_bit else ''}and 0% to 100%",
            manufacturer="Generic",
            capability_factories=[
                lambda addr, cb: TemperatureSensorCapability(
                    device_address=addr,
                    on_state_change=cb,
                ),
                lambda addr, cb: HumiditySensorCapability(
                    device_address=addr,
                    on_state_change=cb,
                ),
                lambda addr, cb: MetaDataCapability(
                    device_address=addr,
                    on_state_change=cb,
                ),
            ],
        )


DEVICE_TYPE_A5_04_01 = DeviceTypeA5_04(type_=0x01, min=0.0, max=40.0)
DEVICE_TYPE_A5_04_02 = DeviceTypeA5_04(type_=0x02, min=-20.0, max=60.0)
DEVICE_TYPE_A5_04_03 = DeviceTypeA5_04(type_=0x03, min=-20.0, max=60.0, ten_bit=True)

__all__ = [
    "DEVICE_TYPE_A5_04_01",
    "DEVICE_TYPE_A5_04_02",
    "DEVICE_TYPE_A5_04_03",
]
