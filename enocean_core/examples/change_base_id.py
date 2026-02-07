# ask for base id

import asyncio

from enocean_core.address import BaseAddress

from ..protocol import ESP3


async def main():
    print("Starting EnOcean module ...")
    protocol = await ESP3.open_serial_port("/dev/tty.usbserial-EO8FD3C6")
    protocol.add_packet_callback(lambda pkt: print(f"Received {pkt}"))
    protocol.add_erp1_callback(lambda erp1: print(f" - parsed to {erp1}"))
    protocol.esp3_send_callbacks.append(lambda pkt: print(f"Sending {pkt}"))
    protocol.response_callbacks.append(lambda resp: print(f"- parsed to {resp}"))

    await protocol.ready
    print("EnOcean module is ready!")
    print(f"EURID: {await protocol.eurid}")
    print(
        f"Base ID: {await protocol.base_id} (remaining write cycles: {await protocol.base_id_remaining_write_cycles})"
    )
    version_info = await protocol.version_info

    print(f"App description: {version_info.app_description}")
    print(f"App version: {version_info.app_version.version_string}")
    print(f"API version: {version_info.api_version.version_string}")
    print(f"Device version: {version_info.device_version}")

    print(
        "Please enter a new base ID (hex string in range FF:80:00:00 to FF:FF:FF:80):"
    )
    new_base_id_str = input().strip()
    try:
        new_base_id = BaseAddress(new_base_id_str)
        print(
            f"Are you sure you want to change this module's base ID to {new_base_id}? (y/n)"
        )
        confirmation = input().strip().lower()
        if confirmation == "y":
            print(
                f"Are you really sure? After this change, you will only be able to change this module's base ID {await protocol.base_id_remaining_write_cycles - 1} more times. Type 'yes' to confirm."
            )
            final_confirmation = input().strip().lower()
            if final_confirmation == "yes":
                # await protocol.set_base_id(new_base_id)
                # print("Base ID changed successfully!")
                pass
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
    asyncio.run(main())
