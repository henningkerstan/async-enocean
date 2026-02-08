# ask for base id

import asyncio
import sys

from async_enocean.protocol import ESP3


async def main(port: str):
    print(f"Trying to connect to EnOcean module on {port}...")
    protocol = await ESP3.open_serial_port(port)
    protocol.add_packet_callback(lambda pkt: print(f"Received {pkt}"))
    protocol.add_erp1_callback(lambda erp1: print(f"╰─ successfully parsed to {erp1}"))
    protocol.esp3_send_callbacks.append(lambda pkt: print(f"Sending {pkt}"))
    protocol.response_callbacks.append(lambda resp: print(f"╰─ successfully parsed to {resp}"))

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

    # Keep the event loop running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    first_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg is None:
        print("Usage: python run_core_gateway.py <serial_port>")
        print("Example: python run_core_gateway.py /dev/tty.usbserial-XYZ")
        sys.exit(1)
    asyncio.run(main(first_arg))
