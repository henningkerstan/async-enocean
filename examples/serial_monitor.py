# ask for base id

import asyncio
import sys

from enocean_async.erp1.rorg import RORG
from enocean_async.erp1.telegram import ERP1Telegram
from enocean_async.gateway import Gateway


def erp1_callback(erp1: ERP1Telegram):
    print(f"╰─ successfully parsed to {erp1}")
   
    if erp1.rorg == RORG.RORG_VLD:
        command = erp1.bitstring_raw_value(4,4)
        print(f"  ├─ command: {command}")

        if command == 0x01:
            print(f"  ├─ dim value: {erp1.bitstring_raw_value(8,3)}")
            print(f"  ├─ I/O channel: {erp1.bitstring_raw_value(11,5)}")
            print(f"  └─ output value: {erp1.bitstring_raw_value(17,7)}")


async def main(port: str):
    print(f"Setting up EnOcean Gateway for module on {port}...")
    gateway = Gateway(port)
    gateway.add_packet_callback(lambda pkt: print(f"Received {pkt}"))
    gateway.add_erp1_callback(erp1_callback)
    gateway.esp3_send_callbacks.append(lambda pkt: print(f"Sending {pkt}"))
    gateway.response_callbacks.append(lambda resp: print(f"╰─ successfully parsed to {resp}"))

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

    # Keep the event loop running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        gateway.stop()


if __name__ == "__main__":
    first_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg is None:
        print("Usage: python serial_monitor <serial_port>")
        print("Example: python serial_monitor /dev/tty.usbserial-XYZ")
        sys.exit(1)
    asyncio.run(main(first_arg))
