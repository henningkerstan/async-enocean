# ask for base id

import asyncio
import logging
import signal
import sys

from enocean_async.eep.id import EEPID
from enocean_async.erp1.address import EURID
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
    
CHECKMARK = "\033[92m✓\033[0m"
CROSSMARK = "\033[91m✗\033[0m"
EXCLAMATIONMARK = "\033[93m!\033[0m"
         

async def main(port: str):
    # set up main loop with exit handler
    loop = asyncio.get_running_loop() 
    stop_event = asyncio.Event() 
    loop.add_signal_handler(signal.SIGINT, stop_event.set) 
    loop.add_signal_handler(signal.SIGTERM, stop_event.set)

    # set up logging
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter( "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S" ))
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler]
)

    print(f"Setting up EnOcean Gateway for module on {port}...")
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

    # add some devices - adopt to your own devices and EEPs
    gateway.add_device(EURID.from_string("00:00:00:01"), EEPID.from_string("F6-02-02"))
    gateway.add_device(EURID.from_string("00:00:00:02"), EEPID.from_string("F6-02-01"))

    gateway.start_learning(timeout_seconds=5)

    # Keep the event loop running
    print("Running... Press Ctrl+C to exit.") 
    await stop_event.wait() 

    print("Shutting down...")
    gateway.stop()



if __name__ == "__main__":
    first_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg is None:
        print("Usage: python serial_monitor <serial_port>")
        print("Example: python serial_monitor /dev/tty.usbserial-XYZ")
        sys.exit(1)

    asyncio.run(main(first_arg))
   