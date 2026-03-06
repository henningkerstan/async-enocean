#!/usr/bin/env python3
"""
This script generates a markdown file listing all supported EnOcean Equipment Profiles (EEPs) based on the EEP database in the `enocean_async` library.
The generated file is named `SUPPORTED_EEPS.md` and contains a table with the EEP ID and its corresponding name.
"""
from enocean_async.eep import EEP_SPECIFICATIONS
from enocean_async.semantics.observable import Observable
from enocean_async.semantics.observers.cover import CoverObserver
from enocean_async.semantics.observers.metadata import MetaDataObserver
from enocean_async.semantics.observers.push_button import (
    F6_02_01_02PushButtonObserver,
    PushButtonObserver,
)
from enocean_async.semantics.observers.scalar import ScalarObserver

# Mapping of observer classes to their emitted StateChange observable_uids and possible values
_BUTTON_EVENTS = ["pushed", "clicked", "double-clicked", "held", "released"]

OBSERVER_STATE_CHANGES = {
    F6_02_01_02PushButtonObserver: {
        "entities": {
            "a0": _BUTTON_EVENTS,
            "a1": _BUTTON_EVENTS,
            "b0": _BUTTON_EVENTS,
            "b1": _BUTTON_EVENTS,
            "ab0": _BUTTON_EVENTS,
            "ab1": _BUTTON_EVENTS,
            "a0b1": _BUTTON_EVENTS,
            "a1b0": _BUTTON_EVENTS,
        },
    },
    PushButtonObserver: {
        "entities": {
            "{button_id}": _BUTTON_EVENTS,
        },
    },
    CoverObserver: {
        "entities": {
            Observable.POSITION: ["position (0-127)"],
            Observable.ANGLE: ["angle (0-127)"],
            Observable.COVER_STATE: ["open", "opening", "closed", "closing", "stopped"],
        },
    },
    MetaDataObserver: {
        "entities": {
            Observable.RSSI: ["signal strength (dBm)"],
            Observable.LAST_SEEN: ["timestamp"],
            Observable.TELEGRAM_COUNT: ["count"],
        },
    },
}

_SCALAR_ENTITY_DESCRIPTIONS = {
    Observable.TEMPERATURE: "temperature (°C)",
    Observable.HUMIDITY: "humidity (%)",
    Observable.ILLUMINATION: "illumination (lx)",
    Observable.MOTION: "motion detected / no motion / uncertain",
    Observable.VOLTAGE: "voltage (V)",
    Observable.WINDOW_STATE: "window state (open / tilted / closed)",
    Observable.OCCUPANCY_BUTTON: "occupancy button (pressed / released)",
}


def get_state_changes_for_eep(eep):
    """Get formatted list of StateChange observable_uids with their values for a given EEP."""
    if not eep.observers:
        return None

    entity_strings = []
    for factory in eep.observers:
        try:
            dummy = factory(None, None)
            observer_class = type(dummy)

            if isinstance(dummy, ScalarObserver):
                uid = dummy.observable
                desc = _SCALAR_ENTITY_DESCRIPTIONS.get(uid, uid)
                entity_strings.append(f"`{uid}`: {desc}")
            elif observer_class in OBSERVER_STATE_CHANGES:
                entities = OBSERVER_STATE_CHANGES[observer_class]["entities"]
                for observable_uid, values in entities.items():
                    values_str = ", ".join(f"`{v}`" for v in values)
                    entity_strings.append(f"`{observable_uid}`: {values_str}")
        except Exception:
            pass

    return entity_strings if entity_strings else None


with open("SUPPORTED_EEPS.md", "w", encoding="utf-8") as file:
    file.write("# List of supported EnOcean Equipment Profiles (EEPs)\n")
    file.write("<!-- This file is auto-generated via a pre-commit hook, do not edit manually. -->\n\n")
    file.write("All EEPs listed below have three metadata sensors `rssi` (the signal strength in dBm), `last_seen` (the timestamp of the last received telegram), and `telegram_count` (the number of telegrams received since startup) in addition to the listed State Change Events.\n\n")
    file.write("| RORG | FUNC | TYPE | Name | Telegrams | StateChange Events |\n")
    file.write("|---|---|---|---|---|---|\n")

    sorted_eeps = sorted(EEP_SPECIFICATIONS.values(), key=lambda item: str(item.eep))

    for entry in sorted_eeps:
        rorg = f"{entry.eep.rorg:02X}"
        func = f"{entry.eep.func:02X}"
        type_ = f"{entry.eep.type:02X}"

        telegrams_supported = "`0x0` (single message EEP)"
        if entry.cmd_offset is not None and entry.cmd_size > 0:
            telegrams_supported = ""
            for key, telegram in sorted(entry.telegrams.items(), key=lambda item: item[0]):
                telegrams_supported += f"`{key:#x}`: {telegram.name}<br>"

        entity_strings = get_state_changes_for_eep(entry)
        observable_uids_str = "<br>".join(entity_strings) if entity_strings else "—"

        file.write(
            f"| {rorg} | {func} | {type_} | {entry.name} | {telegrams_supported} | {observable_uids_str} |\n"
        )
