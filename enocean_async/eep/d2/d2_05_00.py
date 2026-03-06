"""D2-05-00: Blinds control for position and angle, type 0x00."""

from ...capabilities.action import Action
from ...capabilities.commands.cover import (
    QueryCoverPosition,
    SetCoverPosition,
    StopCover,
)
from ...capabilities.observable import Observable
from ...capabilities.observers.cover import cover_factory
from ..id import EEP
from ..message import EEPMessage, EEPMessageType, EEPMessageValue
from ..profile import EEPDataField, EEPSpecification, EEPTelegram, Entity

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


def _encode_set_position(action: SetCoverPosition) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=1, description="Go to position and angle"),
    )
    msg.values["POS"] = EEPMessageValue(raw=action.position, value=action.position)
    msg.values["ANG"] = EEPMessageValue(raw=action.angle, value=action.angle)
    msg.values["REPO"] = EEPMessageValue(
        raw=action.repositioning_mode, value=action.repositioning_mode
    )
    msg.values["LOCK"] = EEPMessageValue(raw=action.lock_mode, value=action.lock_mode)
    chn_val = int(action.entity_id) if action.entity_id.isdigit() else 15
    msg.values["CHN"] = EEPMessageValue(raw=chn_val, value=chn_val)
    return msg


def _encode_stop(action: StopCover) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=2, description="Stop"),
    )
    chn_val = int(action.entity_id) if action.entity_id.isdigit() else 15
    msg.values["CHN"] = EEPMessageValue(raw=chn_val, value=chn_val)
    return msg


def _encode_query_position(action: QueryCoverPosition) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=3, description="Query position and angle"),
    )
    chn_val = int(action.entity_id) if action.entity_id.isdigit() else 15
    msg.values["CHN"] = EEPMessageValue(raw=chn_val, value=chn_val)
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
                    observable=Observable.POSITION,
                ),
                EEPDataField(
                    id="ANG",
                    name="Rotation angle",
                    offset=9,
                    size=7,
                    range_min=0,
                    range_max=127,
                    unit_fn=lambda _: "%",
                    observable=Observable.ANGLE,
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
                    observable=Observable.POSITION,
                ),
                EEPDataField(
                    id="ANG",
                    name="Rotation angle",
                    offset=9,
                    size=7,
                    unit_fn=lambda _: "%",
                    observable=Observable.ANGLE,
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
    observers=[cover_factory()],
    encoders={
        Action.SET_COVER_POSITION: _encode_set_position,
        Action.STOP_COVER: _encode_stop,
        Action.QUERY_COVER_POSITION: _encode_query_position,
    },
    entities=[
        Entity(
            id="cover",
            observables=frozenset(
                {Observable.POSITION, Observable.ANGLE, Observable.COVER_STATE}
            ),
            actions=frozenset(
                {
                    Action.SET_COVER_POSITION,
                    Action.STOP_COVER,
                    Action.QUERY_COVER_POSITION,
                }
            ),
        ),
    ],
)
