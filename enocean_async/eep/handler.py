from enocean_async.address import BroadcastAddress

from ..erp1.telegram import ERP1Telegram
from .message import EEPMessage, EEPMessageValue
from .profile import EEP


class EEPHandler:
    """An EEP handler is responsible for encoding and decoding messages for a specific EEP."""

    def __init__(self, eep: EEP):
        self.__eep = eep

    def decode(self, telegram: ERP1Telegram) -> EEPMessage:
        """Convert an ERP1Telegram into an EEPMessage."""

        msg = EEPMessage(
            sender=telegram.sender, eepid=self.__eep.id, rssi=telegram.rssi, values={}
        )

        if msg.eepid != self.__eep.id:
            return msg  # EEPID mismatch, return message with empty values; TODO: improve this!

        if telegram.destination is not None and not telegram.destination.is_broadcast():
            msg.destination = telegram.destination

        # determine the command/telegram type based on the EEP's cmd_size and cmd_offset, if applicable
        cmd_value = 0

        if self.__eep.cmd_size > 0 and self.__eep.cmd_offset is not None:
            offset = (
                self.__eep.cmd_offset
                if self.__eep.cmd_offset >= 0
                else len(telegram.telegram_data) * 8 + self.__eep.cmd_offset
            )

            cmd_value = telegram.bitstring_raw_value(
                offset=offset, size=self.__eep.cmd_size
            )

        if cmd_value not in self.__eep.telegrams:
            return msg  # unknown telegram type, return message with empty values; TODO: improve this!

        if self.__eep.telegrams[cmd_value].name:
            # print(f"Telegram {cmd_value} identified as {self.__eep.telegrams[cmd_value].name}")
            msg.message_type = self.__eep.telegrams[cmd_value].name
        else:
            msg.message_type = f"Telegram {cmd_value}"

        # iterate over the data fields defined in the EEP and extract values from the telegram
        for field in self.__eep.telegrams[cmd_value].datafields:
            value = None
            # if the field has an enumeration, convert the raw value to its corresponding string representation

            raw_value = telegram.bitstring_raw_value(
                offset=field.offset, size=field.size
            )

            if field.range_enum is not None:
                value = field.range_enum.get(raw_value, f"Unknown({raw_value})")
            elif (
                field.scale_min is not None
                and field.scale_max is not None
                and field.range_min is not None
                and field.range_max is not None
            ):
                value = telegram.bitstring_scaled_value(
                    offset=field.offset,
                    size=field.size,
                    range_min=field.range_min,
                    range_max=field.range_max,
                    scale_min=field.scale_min,
                    scale_max=field.scale_max,
                )
            else:
                value = telegram.bitstring_raw_value(
                    offset=field.offset, size=field.size
                )

            msg.values[field.id] = EEPMessageValue(raw=raw_value, value=value)

        return msg

    def encode(self, message: EEPMessage) -> ERP1Telegram:
        """Convert an EEPMessage into an ERP1Telegram."""
        # Not all EEPs will support encoding, so this can be left unimplemented if desired.
        pass

    def __call__(self, telegram: ERP1Telegram) -> EEPMessage:
        """Allow decoder instances to be called like functions."""
        return self.decode(telegram)
