# ask for base id

import asyncio

from ..protocol import ESP3


async def main():
    print("Starting EnOcean module ...")
    protocol = await ESP3.open_serial_port("/dev/tty.usbserial-EO8FD3C6")
    protocol.add_packet_callback(lambda pkt: print(f"Received ESP3 packet: {pkt}"))
    protocol.add_erp1_callback(lambda erp1: print(f"Received ERP1 telegram: {erp1}"))

    await protocol.ready()
    print("EnOcean module is ready!")
    print(f"EURID  : {await protocol.eurid()}")
    print(f"Base ID: {await protocol.base_id()}")

    # Keep the event loop running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    asyncio.run(main())
