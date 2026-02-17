# ask for base id

import asyncio
import sys

from enocean_async.erp1.address import BaseAddress
from enocean_async.gateway import Gateway

CHECKMARK = "\033[92m✓\033[0m"
CROSSMARK = "\033[91m✗\033[0m"
EXCLAMATIONMARK = "\033[93m!\033[0m"
         
async def main(port: str):
    gateway = Gateway(port)
    
    # callback registration
    gateway.add_esp3_received_callback(lambda pkt: print(f"\nReceived {pkt}"))
    gateway.add_erp1_received_callback(lambda erp1: print(f"├─ {CHECKMARK} successfully parsed to ERP1 telegram: {erp1}"))
    gateway.add_new_device_callback(lambda addr: print(f"├─ {EXCLAMATIONMARK} new device: {addr}"))
    gateway.add_eep_message_received_callback(lambda msg: print(f"╰─ {CHECKMARK} successfully parsed to EEP message: {msg}"))
    gateway.add_ute_received_callback(lambda ute: print(f"╰─ {CHECKMARK} successfully parsed to UTE message: {ute}"))
    gateway.add_response_callback(lambda resp: print(f"╰─ {CHECKMARK} successfully parsed to {resp}"))
    gateway.add_parsing_failed_callback(lambda msg: print(f"╰─ {CROSSMARK} Further parsing failed: {msg}"))
    gateway.add_esp3_send_callback(lambda pkt: print(f"Sending {pkt}"))

    print("Starting gateway...")
    await gateway.start()
    print("EnOcean module is ready!")
    print(f"EURID: {await gateway.eurid}")
    print(
        f"Base ID: {await gateway.base_id} (remaining write cycles: {await gateway.base_id_remaining_write_cycles})"
    )
    version_info = await gateway.version_info

    print(f"App description: {version_info.app_description}")
    print(f"App version: {version_info.app_version.version_string}")
    print(f"API version: {version_info.api_version.version_string}")
    print(f"Device version: {version_info.device_version}")

    print(
        "Enter a new base ID (hex string in range FF:80:00:00 to FF:FF:FF:80): ",
        end="",
    )
    new_base_id_str = input().strip()
    try:
        new_base_id = BaseAddress(new_base_id_str)
        print(
            f"Are you sure you want to change this module's base ID to {new_base_id}? Type 'y' to confirm: ",
            end="",
        )
        confirmation = input().strip().lower()
        if confirmation == "y":
            print(
                f"Are you really sure? After this change, you will only be able to change this module's base ID {await gateway.base_id_remaining_write_cycles - 1} more times. Type 'yes' to confirm: ",
                end="",
            )
            final_confirmation = input().strip().lower()
            if final_confirmation == "yes":
                try:
                    confirmed_base_id = await gateway.change_base_id(new_base_id, safety_flag=0x7B)
                    print("Base ID changed successfully; intended new base ID:", new_base_id, "and actual new base ID after change_base_id command: ", confirmed_base_id)
                except Exception as e:
                    print(f"Failed to change base ID: {e}")
   
            else:
                print("Base ID change cancelled.")
        else:
            print("Base ID change cancelled.")

    except ValueError as e:
        print(f"Invalid base ID: {e}")

    # Keep the event loop running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    first_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg is None:
        print("Usage: python change_base_id.py <serial_port>")
        print("Example: python change_base_id.py /dev/tty.usbserial-XYZ")
        sys.exit(1)
    asyncio.run(main(first_arg))
