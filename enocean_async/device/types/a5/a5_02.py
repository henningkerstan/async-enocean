"""Device types for A5-02-XX temperature sensor profiles."""

from dataclasses import dataclass

from ....capabilities.metadata import MetaDataCapability
from ....capabilities.temperature_sensor import TemperatureSensorCapability
from ....eep.id import EEPID
from ...type import DeviceType


@dataclass
class DeviceTypeA5_02(DeviceType):
    """Device type for A5-02-XX temperature sensor variants."""

    def __init__(self, type_: int, min: float, max: float):
        type_suffix = f"{type_:02X}"
        super().__init__(
            eepid=EEPID.from_string(f"A5-02-{type_suffix}"),
            uid=f"a5-02-{type_suffix.lower()}",
            model=f"Temperature sensor, range {min}°C to {max}°C",
            manufacturer="Generic",
            capability_factories=[
                lambda addr, cb: TemperatureSensorCapability(
                    device_address=addr,
                    on_state_change=cb,
                ),
                lambda addr, cb: MetaDataCapability(
                    device_address=addr,
                    on_state_change=cb,
                ),
            ],
        )


DEVICE_TYPE_A5_02_01 = DeviceTypeA5_02(type_=0x01, min=-40.0, max=0.0)
DEVICE_TYPE_A5_02_02 = DeviceTypeA5_02(type_=0x02, min=-30.0, max=10.0)
DEVICE_TYPE_A5_02_03 = DeviceTypeA5_02(type_=0x03, min=-20.0, max=20.0)
DEVICE_TYPE_A5_02_04 = DeviceTypeA5_02(type_=0x04, min=-10.0, max=30.0)
DEVICE_TYPE_A5_02_05 = DeviceTypeA5_02(type_=0x05, min=0.0, max=40.0)
DEVICE_TYPE_A5_02_06 = DeviceTypeA5_02(type_=0x06, min=10.0, max=50.0)
DEVICE_TYPE_A5_02_07 = DeviceTypeA5_02(type_=0x07, min=20.0, max=60.0)
DEVICE_TYPE_A5_02_08 = DeviceTypeA5_02(type_=0x08, min=30.0, max=70.0)
DEVICE_TYPE_A5_02_09 = DeviceTypeA5_02(type_=0x09, min=40.0, max=80.0)
DEVICE_TYPE_A5_02_0A = DeviceTypeA5_02(type_=0x0A, min=50.0, max=90.0)
DEVICE_TYPE_A5_02_0B = DeviceTypeA5_02(type_=0x0B, min=60.0, max=100.0)
DEVICE_TYPE_A5_02_10 = DeviceTypeA5_02(type_=0x10, min=-60.0, max=20.0)
DEVICE_TYPE_A5_02_11 = DeviceTypeA5_02(type_=0x11, min=-50.0, max=30.0)
DEVICE_TYPE_A5_02_12 = DeviceTypeA5_02(type_=0x12, min=-40.0, max=40.0)
DEVICE_TYPE_A5_02_13 = DeviceTypeA5_02(type_=0x13, min=-30.0, max=50.0)
DEVICE_TYPE_A5_02_14 = DeviceTypeA5_02(type_=0x14, min=-20.0, max=60.0)
DEVICE_TYPE_A5_02_15 = DeviceTypeA5_02(type_=0x15, min=-10.0, max=70.0)
DEVICE_TYPE_A5_02_16 = DeviceTypeA5_02(type_=0x16, min=0.0, max=80.0)
DEVICE_TYPE_A5_02_17 = DeviceTypeA5_02(type_=0x17, min=10.0, max=90.0)
DEVICE_TYPE_A5_02_18 = DeviceTypeA5_02(type_=0x18, min=20.0, max=100.0)
DEVICE_TYPE_A5_02_19 = DeviceTypeA5_02(type_=0x19, min=30.0, max=110.0)
DEVICE_TYPE_A5_02_1A = DeviceTypeA5_02(type_=0x1A, min=40.0, max=120.0)
DEVICE_TYPE_A5_02_1B = DeviceTypeA5_02(type_=0x1B, min=50.0, max=130.0)
DEVICE_TYPE_A5_02_20 = DeviceTypeA5_02(type_=0x20, min=-10.0, max=41.2)
DEVICE_TYPE_A5_02_30 = DeviceTypeA5_02(type_=0x30, min=-40.0, max=62.3)

__all__ = [
    "DEVICE_TYPE_A5_02_01",
    "DEVICE_TYPE_A5_02_02",
    "DEVICE_TYPE_A5_02_03",
    "DEVICE_TYPE_A5_02_04",
    "DEVICE_TYPE_A5_02_05",
    "DEVICE_TYPE_A5_02_06",
    "DEVICE_TYPE_A5_02_07",
    "DEVICE_TYPE_A5_02_08",
    "DEVICE_TYPE_A5_02_09",
    "DEVICE_TYPE_A5_02_0A",
    "DEVICE_TYPE_A5_02_0B",
    "DEVICE_TYPE_A5_02_10",
    "DEVICE_TYPE_A5_02_11",
    "DEVICE_TYPE_A5_02_12",
    "DEVICE_TYPE_A5_02_13",
    "DEVICE_TYPE_A5_02_14",
    "DEVICE_TYPE_A5_02_15",
    "DEVICE_TYPE_A5_02_16",
    "DEVICE_TYPE_A5_02_17",
    "DEVICE_TYPE_A5_02_18",
    "DEVICE_TYPE_A5_02_19",
    "DEVICE_TYPE_A5_02_1A",
    "DEVICE_TYPE_A5_02_1B",
    "DEVICE_TYPE_A5_02_20",
    "DEVICE_TYPE_A5_02_30",
]
