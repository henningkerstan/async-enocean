"""Device type for A5-07-03 occupancy/motion sensor profile."""

from ....capabilities.illumination_sensor import IlluminationSensorCapability
from ....capabilities.metadata import MetaDataCapability
from ....capabilities.motion_sensor import MotionSensorCapability
from ....capabilities.voltage_sensor import VoltageSensorCapability
from ....eep.id import EEPID
from ...type import DeviceType

DEVICE_TYPE_A5_07_03 = DeviceType(
    eepid=EEPID.from_string("A5-07-03"),
    uid="a5-07-03",
    model="Occupancy sensor with supply voltage monitor and illumination",
    manufacturer="Generic",
    capability_factories=[
        lambda addr, cb: MotionSensorCapability(
            device_address=addr,
            on_state_change=cb,
        ),
        lambda addr, cb: IlluminationSensorCapability(
            device_address=addr,
            on_state_change=cb,
        ),
        lambda addr, cb: VoltageSensorCapability(
            device_address=addr,
            on_state_change=cb,
        ),
        lambda addr, cb: MetaDataCapability(
            device_address=addr,
            on_state_change=cb,
        ),
    ],
)

__all__ = [
    "DEVICE_TYPE_A5_07_03",
]
