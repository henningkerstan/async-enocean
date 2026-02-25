"""D2-20-02: Fan control, type 0x02."""

from ...capabilities.action_uid import ActionUID
from ...capabilities.device_command import DeviceCommand
from ..id import EEP
from ..message import EEPMessage, EEPMessageType, EEPMessageValue
from ..profile import EEPDataField, EEPSpecification, EEPTelegram


def _encode_set_fan_speed(cmd: DeviceCommand) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=0, description="Fan control message"),
    )
    for field_id, raw in cmd.values.items():
        msg.values[field_id] = EEPMessageValue(raw=raw, value=raw)
    return msg


EEP_D2_20_02 = EEPSpecification(
    eep=EEP.from_string("D2-20-02"),
    name="Fan control, type 0x02",
    cmd_size=7,
    cmd_offset=1,
    telegrams={
        0: EEPTelegram(
            name="Fan control message",
            datafields=[
                EEPDataField(
                    id="CMD",
                    name="Command",
                    offset=1,
                    size=7,
                    range_enum={0: "Fan control message"},
                ),
                EEPDataField(
                    id="RSR",
                    name="Room size reference",
                    offset=10,
                    size=2,
                    range_enum={
                        0: "Used",
                        1: "Not used",
                        2: "Default",
                        3: "No change",
                    },
                ),
                EEPDataField(
                    id="RS",
                    name="Room size",
                    offset=12,
                    size=4,
                    range_enum={
                        0: "< 25m²",
                        1: "25m² - 50m²",
                        2: "50m² - 75m²",
                        3: "75m² - 100m²",
                        4: "100m² - 125m²",
                        5: "125m² - 150m²",
                        6: "150m² - 175m²",
                        7: "175m² - 200m²",
                        8: "200m² - 225m²",
                        9: "225m² - 250m²",
                        10: "250m² - 275m²",
                        11: "275m² - 300m²",
                        12: "300m² - 325m²",
                        13: "325m² - 350m²",
                        14: ">350m²",
                        15: "No change",
                    },
                ),
                EEPDataField(
                    id="FS",
                    name="Fan speed",
                    offset=24,
                    size=8,
                    range_enum={
                        **{i: f"{i}%" for i in range(101)},
                        **{i: "Reserved" for i in range(101, 253)},
                        253: "Auto",
                        254: "Default",
                        255: "No change",
                    },
                ),
            ],
        ),
        1: EEPTelegram(
            name="Fan status message",
            datafields=[
                EEPDataField(
                    id="CMD",
                    name="Command",
                    offset=1,
                    size=7,
                    range_enum={1: "Fan status message"},
                ),
                EEPDataField(
                    id="HCS",
                    name="Humidity control status",
                    offset=8,
                    size=2,
                    range_enum={
                        0: "Disabled",
                        1: "Enabled",
                        2: "Reserved",
                        3: "Not supported",
                    },
                ),
                EEPDataField(
                    id="RS",
                    name="Room size",
                    offset=12,
                    size=4,
                    range_enum={
                        0: "< 25m²",
                        1: "25m² - 50m²",
                        2: "50m² - 75m²",
                        3: "75m² - 100m²",
                        4: "100m² - 125m²",
                        5: "125m² - 150m²",
                        6: "150m² - 175m²",
                        7: "175m² - 200m²",
                        8: "200m² - 225m²",
                        9: "225m² - 250m²",
                        10: "250m² - 275m²",
                        11: "275m² - 300m²",
                        12: "300m² - 325m²",
                        13: "325m² - 350m²",
                        14: ">350m²",
                        15: "No change",
                    },
                ),
                EEPDataField(
                    id="FS",
                    name="Fan speed",
                    offset=24,
                    size=8,
                    range_enum={
                        **{i: f"{i}%" for i in range(101)},
                        **{i: "Reserved" for i in range(101, 253)},
                        253: "Auto",
                        254: "Default",
                        255: "No change",
                    },
                ),
            ],
        ),
    },
    command_encoders={
        ActionUID.SET_FAN_SPEED: _encode_set_fan_speed,
    },
)
