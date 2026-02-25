"""D2-05-00: Blinds control for position and angle, type 0x00."""

from ...capabilities.action_uid import ActionUID
from ...capabilities.device_command import DeviceCommand
from ...capabilities.observable_uids import ObservableUID
from ...capabilities.position_angle import CoverCapability
from ..id import EEP
from ..message import EEPMessage, EEPMessageType, EEPMessageValue
from ..profile import EEPDataField, EEPSpecification, EEPTelegram

# Shared CMD field definitions.
# cmd_offset=-4, cmd_size=4: the CMD nibble occupies the last 4 bits of each telegram's buffer.
# Absolute offset = ceil(max_non_cmd_bit / 8) * 8 - 4.
#   Telegrams 1 & 4 have data through bit 28 → 4-byte buffer → CMD at offset 28.
#   Telegrams 2 & 3 have data through bit  4 → 4-byte buffer → CMD at offset  4.
_CMD_AT_OFFSET28 = EEPDataField(
    id="CMD",
    name="Command",
    offset=28,
    size=4,
    range_enum={1: "Go to position and angle", 4: "Reply position and angle"},
)
_CMD_AT_OFFSET4 = EEPDataField(
    id="CMD",
    name="Command",
    offset=4,
    size=4,
    range_enum={2: "Stop", 3: "Query position and angle"},
)


def _encode_set_position(cmd: DeviceCommand) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=1, description="Go to position and angle"),
    )
    for field_id, raw in cmd.values.items():
        msg.values[field_id] = EEPMessageValue(raw=raw, value=raw)
    return msg


def _encode_stop(cmd: DeviceCommand) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=2, description="Stop"),
    )
    for field_id, raw in cmd.values.items():
        msg.values[field_id] = EEPMessageValue(raw=raw, value=raw)
    return msg


def _encode_query_position(cmd: DeviceCommand) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=3, description="Query position and angle"),
    )
    for field_id, raw in cmd.values.items():
        msg.values[field_id] = EEPMessageValue(raw=raw, value=raw)
    return msg


EEP_D2_05_00 = EEPSpecification(
    eep=EEP.from_string("D2-05-00"),
    name="Blinds control for position and angle, type 0x00",
    cmd_size=4,
    cmd_offset=-4,
    telegrams={
        1: EEPTelegram(
            name="Go to position and angle",
            datafields=[
                EEPDataField(
                    id="POS",
                    name="Vertical position",
                    offset=1,
                    size=7,
                    range_min=0,
                    range_max=127,
                    unit_fn=lambda _: "%",
                    observable_uid=ObservableUID.POSITION,
                ),
                EEPDataField(
                    id="ANG",
                    name="Rotation angle",
                    offset=9,
                    size=7,
                    range_min=0,
                    range_max=127,
                    unit_fn=lambda _: "%",
                    observable_uid=ObservableUID.ANGLE,
                ),
                EEPDataField(
                    id="REPO",
                    name="Repositioning mode",
                    offset=17,
                    size=3,
                    range_enum={
                        0: "Directly to target POS/ANG",
                        1: "Up, then to target POS/ANG",
                        2: "Down, then to target POS/ANG",
                        3: "Reserved",
                        4: "Reserved",
                        5: "Reserved",
                        6: "Reserved",
                        7: "Reserved",
                    },
                ),
                EEPDataField(
                    id="LOCK",
                    name="Set locking mode",
                    offset=21,
                    size=3,
                    range_enum={
                        0: "No change",
                        1: "Set blockage mode",
                        2: "Set alarm mode",
                        3: "Reserved",
                        4: "Reserved",
                        5: "Reserved",
                        6: "Reserved",
                        7: "Unblock",
                    },
                ),
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=24,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                        15: "All channels",
                    },
                ),
                _CMD_AT_OFFSET28,
            ],
        ),
        2: EEPTelegram(
            name="Stop",
            datafields=[
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=0,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                        15: "All channels",
                    },
                ),
                _CMD_AT_OFFSET4,
            ],
        ),
        3: EEPTelegram(
            name="Query position and angle",
            datafields=[
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=0,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                        15: "All channels",
                    },
                ),
                _CMD_AT_OFFSET4,
            ],
        ),
        4: EEPTelegram(
            name="Reply position and angle",
            datafields=[
                EEPDataField(
                    id="POS",
                    name="Vertical position",
                    offset=1,
                    size=7,
                    unit_fn=lambda _: "%",
                    observable_uid=ObservableUID.POSITION,
                ),
                EEPDataField(
                    id="ANG",
                    name="Rotation angle",
                    offset=9,
                    size=7,
                    unit_fn=lambda _: "%",
                    observable_uid=ObservableUID.ANGLE,
                ),
                EEPDataField(
                    id="LOCK",
                    name="Locking modes",
                    offset=21,
                    size=3,
                    range_enum={
                        0: "Normal (no lock)",
                        1: "Blockage mode",
                        2: "Alarm mode",
                        3: "Reserved",
                        4: "Reserved",
                        5: "Reserved",
                        6: "Reserved",
                        7: "Reserved",
                    },
                ),
                EEPDataField(
                    id="CHN",
                    name="Channel",
                    offset=24,
                    size=4,
                    range_enum={
                        0: "Channel 1",
                        1: "Channel 2",
                        2: "Channel 3",
                        3: "Channel 4",
                    },
                ),
                _CMD_AT_OFFSET28,
            ],
        ),
    },
    capability_factories=[
        lambda addr, cb: CoverCapability(
            device_address=addr,
            on_state_change=cb,
        ),
    ],
    command_encoders={
        ActionUID.SET_COVER_POSITION: _encode_set_position,
        ActionUID.STOP_COVER: _encode_stop,
        ActionUID.QUERY_COVER_POSITION: _encode_query_position,
    },
)
