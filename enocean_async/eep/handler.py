from enocean_async.address import BroadcastAddress

from ..erp1.telegram import RORG, ERP1Telegram
from .message import EEPMessage, EEPMessageType, EEPMessageValue, EntityValue
from .profile import EEPSpecification


class EEPHandler:
    """An EEP handler is responsible for encoding and decoding messages for a specific EEP."""

    def __init__(self, eep: EEPSpecification):
        self.__eep = eep

    def decode(self, telegram: ERP1Telegram) -> EEPMessage:
        """Convert an ERP1Telegram into an EEPMessage."""

        msg = EEPMessage(
            sender=telegram.sender,
            eep=self.__eep.eep,
            rssi=telegram.rssi,
            values={},
            entities={},
        )

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

        msg.message_type = EEPMessageType(
            id=cmd_value,
            description=self.__eep.telegrams[cmd_value].name
            if self.__eep.telegrams[cmd_value].name
            else f"Telegram {cmd_value}",
        )

        # iterate over the data fields defined in the EEP and extract values from the telegram
        # First pass: collect all raw values for dependency resolution
        telegram_raw_values: dict[str, int] = {}
        for field in self.__eep.telegrams[cmd_value].datafields:
            telegram_raw_values[field.id] = telegram.bitstring_raw_value(
                offset=field.offset, size=field.size
            )

        # Second pass: decode values with context (for field interdependencies)
        for field in self.__eep.telegrams[cmd_value].datafields:
            raw_value = telegram_raw_values[field.id]
            value = None

            # if the field has an enumeration, convert the raw value to its corresponding string representation
            if field.range_enum is not None:
                value = field.range_enum.get(raw_value, f"Unknown({raw_value})")
            elif field.range_min is not None and field.range_max is not None:
                # Compute scale bounds using callbacks (with full message context)
                scale_min = field.scale_min_fn(telegram_raw_values)
                scale_max = field.scale_max_fn(telegram_raw_values)

                if scale_min is not None and scale_max is not None:
                    value = telegram.bitstring_scaled_value(
                        offset=field.offset,
                        size=field.size,
                        range_min=field.range_min,
                        range_max=field.range_max,
                        scale_min=scale_min,
                        scale_max=scale_max,
                    )
                else:
                    value = raw_value
            else:
                value = raw_value

            # Compute unit using callback
            unit = field.unit_fn(telegram_raw_values)

            msg.values[field.id] = EEPMessageValue(
                raw=raw_value, value=value, unit=unit
            )

        # Third pass: entity UID propagation — copy decoded values to semantic entity keys
        for field in self.__eep.telegrams[cmd_value].datafields:
            if field.observable_uid is not None and field.id in msg.values:
                field_value = msg.values[field.id]
                msg.entities[field.observable_uid] = EntityValue(
                    value=field_value.value, unit=field_value.unit
                )

        # Fourth pass: semantic resolvers — combine multiple fields into a single entity value
        for observable_uid, resolver in self.__eep.semantic_resolvers.items():
            result = resolver(msg.values)
            if result is not None:
                msg.entities[observable_uid] = EntityValue(
                    value=result.value, unit=result.unit
                )

        return msg

    def encode(self, message: EEPMessage) -> ERP1Telegram:
        """Convert an EEPMessage into an ERP1Telegram.

        The message must have:
        - message.sender set to a valid sender address (BaseAddress or EURID) for the gateway
        - message.message_type.id set to the telegram command value (0 for single-telegram EEPs)
        - message.values[field_id] = EEPMessageValue(raw=<int>, ...) for each field to encode

        Raises:
            ValueError: if message.sender is None or the telegram type is unknown.
        """
        if message.sender is None:
            raise ValueError("message.sender must be set before encoding")

        cmd_value = message.message_type.id if message.message_type else 0

        if cmd_value not in self.__eep.telegrams:
            raise ValueError(
                f"Unknown telegram type {cmd_value} for EEP {self.__eep.eep}"
            )

        telegram_def = self.__eep.telegrams[cmd_value]
        datafields = telegram_def.datafields
        buffer_size = telegram_def.byte_size

        rorg = RORG(self.__eep.eep.rorg)
        erp1 = ERP1Telegram(
            rorg=rorg,
            telegram_data=bytes(buffer_size),
            sender=message.sender,
            destination=message.destination,
        )

        # Write CMD bits
        if self.__eep.cmd_size > 0 and self.__eep.cmd_offset is not None:
            cmd_bit_offset = (
                self.__eep.cmd_offset
                if self.__eep.cmd_offset >= 0
                else buffer_size * 8 + self.__eep.cmd_offset
            )
            erp1.set_bitstring_raw_value(
                offset=cmd_bit_offset, size=self.__eep.cmd_size, value=cmd_value
            )

        # Write each field's raw value
        for f in datafields:
            mv = message.values.get(f.id)
            if mv is not None:
                erp1.set_bitstring_raw_value(offset=f.offset, size=f.size, value=mv.raw)

        return erp1

    def __call__(self, telegram: ERP1Telegram) -> EEPMessage:
        """Allow decoder instances to be called like functions."""
        return self.decode(telegram)
