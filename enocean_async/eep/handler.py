from ..erp1.telegram import ERP1Telegram
from .message import EEPMessage
from .profile import EEP


class EEPHandler:
    """An EEP handler is responsible for encoding and decoding messages for a specific EEP."""

    def __init__(self, eep: EEP):
        self.__eep = eep

    def decode(self, telegram: ERP1Telegram) -> EEPMessage:
        """Convert an ERP1Telegram into an EEPMessage."""

        msg = EEPMessage(sender=telegram.sender, eepid=self.__eep.id, rssi=0, values={})

        # iterate over the data fields defined in the EEP and extract values from the telegram
        for field in self.__eep.datafields:
            value = None
            # if the field has an enumeration, convert the raw value to its corresponding string representation
            if field.range_enum is not None:
                raw_value = telegram.bitstring_raw_value(
                    offset=field.offset, size=field.size
                )
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

            msg.values[field.id] = value

        return msg

    def encode(self, message: EEPMessage) -> ERP1Telegram:
        """Convert an EEPMessage into an ERP1Telegram."""
        # Not all EEPs will support encoding, so this can be left unimplemented if desired.
        pass

    def __call__(self, telegram: ERP1Telegram) -> EEPMessage:
        """Allow decoder instances to be called like functions."""
        return self.decode(telegram)
