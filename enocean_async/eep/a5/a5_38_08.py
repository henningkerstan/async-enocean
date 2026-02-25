"""A5-38-08: Central command - gateway."""

from ...capabilities.action_uid import ActionUID
from ...capabilities.device_command import DeviceCommand
from ..id import EEP
from ..message import EEPMessage, EEPMessageType, EEPMessageValue
from ..profile import EEPDataField, EEPSpecification, EEPTelegram


def _encode_dim(cmd: DeviceCommand) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=2, description="Dimming"),
    )
    for field_id, raw in cmd.values.items():
        msg.values[field_id] = EEPMessageValue(raw=raw, value=raw)
    return msg


EEP_A5_38_08 = EEPSpecification(
    eep=EEP.from_string("A5-38-08"),
    name="Central command - gateway",
    cmd_size=8,
    cmd_offset=0,
    telegrams={
        2: EEPTelegram(
            name="Dimming",
            datafields=[
                EEPDataField(
                    id="CMD",
                    name="Command",
                    offset=0,
                    size=8,
                    range_enum={2: "Dimming"},
                ),
                EEPDataField(
                    id="EDIM",
                    name="Dimming value",
                    offset=8,
                    size=8,
                    scale_min_fn=lambda _: 0.0,
                    scale_max_fn=lambda _: 255.0,
                ),
                EEPDataField(
                    id="RMP",
                    name="Ramping time",
                    offset=16,
                    size=8,
                    scale_min_fn=lambda _: 0.0,
                    scale_max_fn=lambda _: 255.0,
                    unit_fn=lambda _: "s",
                ),
                EEPDataField(
                    id="EDIMR",
                    name="Dimming range",
                    offset=29,
                    size=1,
                    range_enum={
                        0: "Absolute",
                        1: "Relative",
                    },
                ),
                EEPDataField(
                    id="STR",
                    name="Store final value",
                    offset=30,
                    size=1,
                    range_enum={
                        0: "No",
                        1: "Yes",
                    },
                ),
                EEPDataField(
                    id="SW",
                    name="Switching command",
                    offset=31,
                    size=1,
                    range_enum={
                        0: "Off",
                        1: "On",
                    },
                ),
            ],
        )
    },
    command_encoders={
        ActionUID.DIM: _encode_dim,
    },
)
