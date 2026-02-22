#!/usr/bin/env python3
"""
This script generates a markdown file listing all supported EnOcean Equipment Profiles (EEPs) based on the EEP database in the `enocean_async` library. 
The generated file is named `SUPPORTED_EEPS.md` and contains a table with the EEP ID and its corresponding name.
"""
from enocean_async.capabilities.illumination_sensor import IlluminationSensorCapability
from enocean_async.capabilities.metadata import MetaDataCapability
from enocean_async.capabilities.motion_sensor import MotionSensorCapability
from enocean_async.capabilities.position_angle import PositionAngleCapability
from enocean_async.capabilities.push_button import (
    F6_02_01_02PushButtonCapability,
    PushButtonCapability,
)
from enocean_async.capabilities.temperature_sensor import TemperatureSensorCapability
from enocean_async.capabilities.voltage_sensor import VoltageSensorCapability
from enocean_async.device.types import DEVICE_TYPE_DATABASE
from enocean_async.eep import EEP_DATABASE

# Mapping of capability classes to their emitted StateChange entity_uids and possible values
CAPABILITY_STATE_CHANGES = {
    PushButtonCapability: {
        "entities": {
            "{button_id}": ["pushed", "click", "double-click", "hold", "released"],
        },
    },
    F6_02_01_02PushButtonCapability: {
        "entities": {
            "a0": ["pushed", "click", "double-click", "hold", "released"],
            "a1": ["pushed", "click", "double-click", "hold", "released"],
            "b0": ["pushed", "click", "double-click", "hold", "released"],
            "b1": ["pushed", "click", "double-click", "hold", "released"],
            "ab0": ["pushed", "click", "double-click", "hold", "released"],
            "ab1": ["pushed", "click", "double-click", "hold", "released"],
            "a0b1": ["pushed", "click", "double-click", "hold", "released"],
            "a1b0": ["pushed", "click", "double-click", "hold", "released"],
        },
    },
    PositionAngleCapability: {
        "entities": {
            "POS": ["position (0-127)"],
            "ANG": ["angle (0-127)"],
        },
    },
    TemperatureSensorCapability: {
        "entities": {
            "temperature": ["temperature (°C)"],
        },
    },
    MotionSensorCapability: {
        "entities": {
            "motion": ["motion detected, no motion, or uncertain"],
        },
    },
    IlluminationSensorCapability: {
        "entities": {
            "illumination": ["illumination (lx)"],
        },
    },
    VoltageSensorCapability: {
        "entities": {
            "voltage": ["supply voltage (V)"],
        },
    },
    MetaDataCapability: {
        "entities": {
            "rssi": ["signal strength (dBm)"],
            "last_seen": ["timestamp"],
            "telegram_count": ["count"],
        },
    },
}


def get_state_changes_for_device_type(eepid):
    """Get formatted list of StateChange entity_uids with their values for a given EEPID."""
    device_type = DEVICE_TYPE_DATABASE.get(eepid)
    if not device_type:
        return None
    
    entity_strings = []
    for factory in device_type.capability_factories:
        # Create a dummy instance to get the capability class
        try:
            dummy_capability = factory(None, None)
            capability_class = type(dummy_capability)
            
            if capability_class in CAPABILITY_STATE_CHANGES:
                entities = CAPABILITY_STATE_CHANGES[capability_class]["entities"]
                for entity_uid, values in entities.items():
                    values_str = ", ".join(f"`{v}`" for v in values)
                    entity_strings.append(f"`{entity_uid}`: {values_str}")
        except:
            pass
    
    return entity_strings if entity_strings else None

with open("SUPPORTED_EEPS.md", "w", encoding="utf-8") as file:
    file.write("# List of supported EnOcean Equipment Profiles (EEPs)\n")
    file.write("<!-- This file is auto-generated via a pre-commit hook, do not edit manually. -->\n\n")
    file.write("| EEP | Name | Telegrams | StateChange Entity UIDs |\n")
    file.write("|---|---|---|---|\n")

    for entry in sorted(EEP_DATABASE.values(), key=lambda item: item.id.to_string()):
        telegrams_supported = "`0x0` (single message EEP)"
        if entry.cmd_offset is not None and entry.cmd_size > 0:
            telegrams_supported = ""
            for key, telegram in sorted(entry.telegrams.items(), key=lambda item: item[0]):
                telegrams_supported += f"`{key:#x}`: {telegram.name}<br>"
        
        # Get StateChange entity_uids for this EEP
        entity_strings = get_state_changes_for_device_type(entry.id)
        entity_uids_str = ""
        if entity_strings:
            # Format each entity on its own line for readability
            entity_uids_str = "<br>".join(entity_strings)
        else:
            entity_uids_str = "—"
        
        file.write(
            f"| {entry.id.to_string()} | {entry.name} | {telegrams_supported} | {entity_uids_str} |\n"
        )
        