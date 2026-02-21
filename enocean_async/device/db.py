from enocean_async.eep.manufacturer import Manufacturer

from ..eep import EEP_DATABASE
from ..eep.id import EEPID
from .type import DeviceType

DEVICE_TYPE_DB: dict[str, DeviceType] = {
    **{
        eep_id.to_string(): DeviceType(
            eepid=eep_id,
            model=eep.name,
            manufacturer=eep_id.manufacturer.friendly_name
            if eep_id.manufacturer
            else None,
        )
        for eep_id, eep in EEP_DATABASE.items()
    },
    "Eltako_FABH65S": DeviceType(
        eepid=EEPID(0xA5, 0x08, 0x01, manufacturer=Manufacturer.ELTAKO),
        manufacturer="Eltako",
        model="FABH65S Wireless outdoor occupancy and brightness sensor",
    ),
    "NodOn_SIN-2-RS-01": DeviceType(
        model="SIN-2-RS-01 Roller Shutter Controller",
        eepid=EEPID(0xD2, 0x05, 0x00),
        manufacturer="NodOn",
    ),
}

for _key, _device_type in DEVICE_TYPE_DB.items():
    _device_type.uid = _key
