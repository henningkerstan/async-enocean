# ask for base id

import asyncio
import logging
import sys

from enocean_async.eep.f602xx.decoder import F602XXDecoder
from enocean_async.erp1.rorg import RORG
from enocean_async.erp1.telegram import ERP1Telegram
from enocean_async.erp1.ute import UTEMessage, UTEResponseType
from enocean_async.esp3.packet import ESP3Packet, ESP3PacketType
from enocean_async.gateway import Gateway


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG:    "\033[96;1m",   # bright cyan
        logging.INFO:     "\033[95;1m",   # bright magenta
        logging.WARNING:  "\033[93;1m",   # bright yellow
        logging.ERROR:    "\033[91;1m",   # bright red
        logging.CRITICAL: "\033[97;1;41m",  # bright white on red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"



def erp1_callback(erp1: ERP1Telegram):
    print(f"├─ successfully parsed to {erp1}")
   
    if erp1.rorg == RORG.RORG_VLD:
        command = erp1.bitstring_raw_value(4,4)
        print(f"├─ command: {command}")

        if command == 0x01:
            print(f"├─ dim value: {erp1.bitstring_raw_value(8,3)}")
            print(f"├─ I/O channel: {erp1.bitstring_raw_value(11,5)}")
            print(f"╰─ output value: {erp1.bitstring_raw_value(17,7)}")

    elif erp1.rorg == RORG.RORG_RPS:
        try:
            decoded = F602XXDecoder()(erp1)
            print(f"╰─ decoded to {decoded}")
        except Exception as e:
            print(f"╰─ FAILED to decode F6-02-xx: {e}")


async def main(port: str):
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter( "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S" ))

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler]
)

    print(f"Setting up EnOcean Gateway for module on {port}...")
    gateway = Gateway(port)
    gateway.add_esp3_received_callback(lambda pkt: print(f"\nReceived {pkt}"))

    gateway.add_erp1_received_callback(erp1_callback)
    gateway.add_ute_received_callback(lambda ute: print(f"╰─ successfully parsed to UTE message: {ute}"))
    gateway.add_esp3_send_callback(lambda pkt: print(f"Sending {pkt}"))
    gateway.add_new_device_callback(lambda addr: print(f"├─ new device detected with address {addr}"))
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

    gateway.start_learning(timeout_seconds=5)

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
