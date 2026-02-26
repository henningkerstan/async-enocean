"""A5-38-08: Central command - gateway."""

from ...capabilities.action_uid import ActionUID
from ...capabilities.dimmer_actions import DimAction
from ..id import EEP
from ..message import EEPMessage, EEPMessageType, EEPMessageValue
from ..profile import EEPDataField, EEPSpecification, EEPTelegram


def _encode_dim(action: DimAction) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=2, description="Dimming"),
    )
    msg.values["EDIM"] = EEPMessageValue(raw=action.dim_value, value=action.dim_value)
    msg.values["RMP"] = EEPMessageValue(raw=action.ramp_time, value=action.ramp_time)
    msg.values["EDIMR"] = EEPMessageValue(
        raw=int(action.relative), value=int(action.relative)
    )
    msg.values["STR"] = EEPMessageValue(raw=int(action.store), value=int(action.store))
    msg.values["SW"] = EEPMessageValue(
        raw=int(action.switch_on), value=int(action.switch_on)
    )
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
