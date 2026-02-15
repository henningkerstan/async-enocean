from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from enocean_async.eep.manufacturer import Manufacturer
from enocean_async.erp1.errors import ERP1ParseError
from enocean_async.esp3.packet import ESP3Packet, ESP3PacketType

from ..eep.id import EEPID
from ..erp1.rorg import RORG
from ..erp1.telegram import ERP1Telegram


class UTEQueryRequestType(IntEnum):
    TEACH_IN = 0
    TEACH_IN_DELETION = 1
    TEACH_IN_OR_DELETION_OF_TEACH_IN = 2
    NOT_USED = 3


class UTEResponseType(IntEnum):
    NOT_ACCEPTED_GENERAL_REASON = 0
    ACCEPTED_TEACH_IN = 1
    ACCEPTED_DELETION_OF_TEACH_IN = 2
    NOT_ACCEPTED_EEP_NOT_SUPPORTED = 3


class CommunicationDuringEEPOperation(IntEnum):
    UNIDIRECTIONAL = 0
    BIDIRECTIONAL = 1


class CommandIdentifier(IntEnum):
    TEACH_IN_QUERY = 0
    TEACH_IN_RESPONSE = 1


class EEPTeachInResponseMessageExpectation(IntEnum):
    RESPONSE_EXPECTED = 0
    NO_TEACH_IN_RESPONSE = 1


@dataclass
class UTEMessage:
    communication_during_eep_operation: CommunicationDuringEEPOperation
    teach_in_response_message_expectation: Optional[
        EEPTeachInResponseMessageExpectation
    ]
    request_type: UTEQueryRequestType | UTEResponseType
    command: CommandIdentifier
    number_of_channels_to_be_taught_in: int
    manufacturer: Manufacturer
    eep: EEPID

    @classmethod
    def from_erp1(cls, telegram: ERP1Telegram) -> "UTEMessage":
        if telegram.rorg != RORG.RORG_UTE:
            raise ValueError(f"Invalid RORG for UTE: {telegram.rorg}")

        if len(telegram.telegram_data) < 6:
            raise ValueError(
                f"Invalid data length for UTE: {len(telegram.telegram_data)} bytes but expected 6 bytes"
            )

        communication_during_eep_operation = CommunicationDuringEEPOperation(
            telegram.bitstring_raw_value(0, 1)
        )

        command = CommandIdentifier(telegram.bitstring_raw_value(4, 4))

        if command == CommandIdentifier.TEACH_IN_QUERY:
            teach_in_response_message_expectation = (
                EEPTeachInResponseMessageExpectation(telegram.bitstring_raw_value(1, 1))
            )

        request_type_value = telegram.bitstring_raw_value(2, 2)
        request_type = (
            UTEQueryRequestType(request_type_value)
            if command == CommandIdentifier.TEACH_IN_QUERY
            else UTEResponseType(request_type_value)
        )

        number_of_channels_to_be_taught_in = telegram.data_byte(5)

        manufacturer_id_lsb = telegram.data_byte(4)
        manufacturer_id_msb = telegram.data_byte(3) & 0b00000111
        manufacturer_id = (manufacturer_id_msb << 8) | manufacturer_id_lsb

        manufacturer: Manufacturer
        try:
            manufacturer = Manufacturer(manufacturer_id)
        except ValueError:
            manufacturer = Manufacturer.Reserved

        eep = EEPID(
            type_=telegram.data_byte(2),
            func=telegram.data_byte(1),
            rorg=telegram.data_byte(0),
        )

        return cls(
            communication_during_eep_operation=communication_during_eep_operation,
            teach_in_response_message_expectation=teach_in_response_message_expectation,
            request_type=request_type,
            command=command,
            number_of_channels_to_be_taught_in=number_of_channels_to_be_taught_in,
            manufacturer=manufacturer,
            eep=eep,
        )

    @classmethod
    def response_for_query(
        cls, query: UTEMessage, response_type: UTEResponseType
    ) -> UTEMessage:
        if query.command != CommandIdentifier.TEACH_IN_QUERY:
            raise ValueError("Could not create response for non-query.")

        return UTEMessage(
            communication_during_eep_operation=query.communication_during_eep_operation,
            teach_in_response_message_expectation=None,
            request_type=response_type,
            command=CommandIdentifier.TEACH_IN_RESPONSE,
            number_of_channels_to_be_taught_in=query.number_of_channels_to_be_taught_in,
            manufacturer=query.manufacturer,
            eep=query.eep,
        )
