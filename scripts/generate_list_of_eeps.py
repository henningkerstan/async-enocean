#!/usr/bin/env python3
"""
This script generates a markdown file listing all supported EnOcean Equipment Profiles (EEPs) based on the EEP database in the `enocean_async` library. 
The generated file is named `SUPPORTED_EEPS.md` and contains a table with the EEP ID and its corresponding name.
"""
from enocean_async.eep import EEP_DATABASE

with open("SUPPORTED_EEPS.md", "w", encoding="utf-8") as file:
    file.write("# List of supported EnOcean Equipment Profiles (EEPs)\n")
    file.write("<!-- This file is auto-generated via a pre-commit hook, do not edit manually. -->\n\n")
    file.write("| EEP | Name | Telegrams |\n")
    file.write("|---|---|---|\n")

    for entry in sorted(EEP_DATABASE.values(), key=lambda item: item.id.to_string()):
        telegrams_supported = "default (only one message type)"
        if entry.cmd_offset is not None and entry.cmd_size > 0:
            telegrams_supported = ""
            for key, telegram in sorted(entry.telegrams.items(), key=lambda item: item[0]):
                telegrams_supported += f"{key:#x}: {telegram.name}<br>"
        file.write(
            f"| {entry.id.to_string()} | {entry.name} | {telegrams_supported} |\n"
        )
        