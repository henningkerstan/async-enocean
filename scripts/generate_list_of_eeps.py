#!/usr/bin/env python3
"""
This script generates a markdown file listing all supported EnOcean Equipment Profiles (EEPs) based on the EEP database in the `enocean_async` library. 
The generated file is named `SUPPORTED_PROFILES.md` and contains a table with the EEP ID and its corresponding name.
"""
from enocean_async.eep.db import EEP_DATABASE

with open("SUPPORTED_PROFILES.md", "w", encoding="utf-8") as file:
    file.write("# List of supported EnOcean Equipment Profiles (EEPs)\n")
    file.write("<!-- This file is auto-generated via a pre-commit hook, do not edit manually. -->\n\n")
    file.write("| EEP | Name |\n")
    file.write("|---|---|\n")

    for entry in sorted(EEP_DATABASE.values(), key=lambda item: item.id.to_string()):
        file.write(
            f"| {entry.id.to_string()} | {entry.name} |\n"
        )
        