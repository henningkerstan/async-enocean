"""D2-01: Electronic Switches and Dimmers with Local Control.

All 23 TYPE variants (0x00–0x16) share the same telegram format; only the supported
command subset differs per device.

Extended commands (CMD 0xF / ECID 0x00–0x02)
---------------------------------------------
The current EEPHandler dispatches on cmd_value only.  ECID sub-dispatch is not yet
implemented, so dimming-limits sub-telegrams are registered under synthetic keys
0xF0 / 0xF1 / 0xF2 for future use.
"""

from dataclasses import dataclass

from ...capabilities.action_uid import ActionUID
from ...capabilities.observable_uids import ObservableUID
from ...capabilities.scalar import ScalarCapability
from ...capabilities.switch_actions import (
    QueryActuatorMeasurementAction,
    QueryActuatorStatusAction,
    SetSwitchOutputAction,
)
from ..id import EEP
from ..message import EEPMessage, EEPMessageType, EEPMessageValue
from ..profile import EEPDataField, EEPSpecification, EEPTelegram

# ---------------------------------------------------------------------------
# Command registry — single source of truth for CMD / ECID IDs and names
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _EEP_D2_01_TelegramName:
    key: int
    name: str


_EEP_D2_01_Commands: dict[int, _EEP_D2_01_TelegramName] = {
    0x1: _EEP_D2_01_TelegramName(0x1, "Actuator set output"),
    0x2: _EEP_D2_01_TelegramName(0x2, "Actuator set local"),
    0x3: _EEP_D2_01_TelegramName(0x3, "Actuator status query"),
    0x4: _EEP_D2_01_TelegramName(0x4, "Actuator status response"),
    0x5: _EEP_D2_01_TelegramName(0x5, "Actuator set measurement"),
    0x6: _EEP_D2_01_TelegramName(0x6, "Actuator measurement query"),
    0x7: _EEP_D2_01_TelegramName(0x7, "Actuator measurement response"),
    0x8: _EEP_D2_01_TelegramName(0x8, "Actuator set pilot wire mode"),
    0x9: _EEP_D2_01_TelegramName(0x9, "Actuator pilot wire mode query"),
    0xA: _EEP_D2_01_TelegramName(0xA, "Actuator pilot wire mode response"),
    0xB: _EEP_D2_01_TelegramName(0xB, "Actuator set external interface settings"),
    0xC: _EEP_D2_01_TelegramName(0xC, "Actuator external interface settings query"),
    0xD: _EEP_D2_01_TelegramName(0xD, "Actuator external interface settings response"),
    0xF: _EEP_D2_01_TelegramName(0xF, "Extended command, see ECID field"),
}

_EEP_D2_01_ExtendedCommands: dict[int, _EEP_D2_01_TelegramName] = {
    0x00: _EEP_D2_01_TelegramName(0x00, "Actuator set dimming limits"),
    0x01: _EEP_D2_01_TelegramName(0x01, "Actuator dimming limits query"),
    0x02: _EEP_D2_01_TelegramName(0x02, "Actuator dimming limits response"),
}


def _cmd(cmd_id: int) -> EEPDataField:
    """CMD field whose single-entry enum is derived from _EEP_D2_01_Commands."""
    c = _EEP_D2_01_Commands[cmd_id]
    return EEPDataField(
        id="CMD", name="Command", offset=4, size=4, range_enum={c.key: c.name}
    )


def _ecid(ecid_id: int) -> EEPDataField:
    """ECID field whose single-entry enum is derived from _EEP_D2_01_ExtendedCommands."""
    e = _EEP_D2_01_ExtendedCommands[ecid_id]
    return EEPDataField(
        id="ECID",
        name="Extended command ID",
        offset=8,
        size=8,
        range_enum={e.key: e.name},
    )


def _io(offset: int = 11, *, not_applicable_at_1e: bool = False) -> EEPDataField:
    """I/O channel field.  Response telegrams use not_applicable_at_1e=True."""
    return EEPDataField(
        id="I/O",
        name="I/O channel",
        offset=offset,
        size=5,
        range_enum={
            **{i: f"Output channel {i + 1}" for i in range(0x1E)},
            0x1E: "Not applicable" if not_applicable_at_1e else "All output channels",
            0x1F: "Input channel",
        },
    )


# ---------------------------------------------------------------------------
# Shared field enumerations
# ---------------------------------------------------------------------------

_DIM_TIMER_ENUM: dict[int, str] = {
    0x00: "Not used",
    **{i: f"{i * 0.5:.1f} s" for i in range(1, 16)},  # 0x01–0x0F → 0.5–7.5 s
}
_OUTPUT_VALUE_ENUM: dict[int, str] = {
    0x00: "0% / OFF",
    **{i: f"{i}% / ON" for i in range(1, 0x65)},
    **{i: "Not used" for i in range(0x65, 0x7F)},
    0x7F: "Output value not valid / not applicable",
}
_UNIT_ENUM: dict[int, str] = {
    0x00: "Energy [Ws]",
    0x01: "Energy [Wh]",
    0x02: "Energy [KWh]",
    0x03: "Power [W]",
    0x04: "Power [KW]",
    0x05: "Not used",
    0x06: "Not used",
    0x07: "Not used",
}
_PILOT_WIRE_ENUM: dict[int, str] = {
    0x00: "Off",
    0x01: "Comfort",
    0x02: "Eco",
    0x03: "Anti-freeze",
    0x04: "Comfort-1",
    0x05: "Comfort-2",
}
_TIMER_ENUM: dict[int, str] = {
    0x0000: "Timer deactivated",
    **{i: f"{i * 0.1:.1f} s" for i in range(1, 0xFFFF)},  # 0x0001–0xFFFE → 0.1–6553.4 s
    0xFFFF: "Does not modify saved value",
}
_MAXV_ENUM: dict[int, str] = {
    0x00: "Reserved",
    **{i: f"{i}%" for i in range(1, 101)},
    **{i: "Reserved" for i in range(101, 128)},
}
_MINV_ENUM: dict[int, str] = {
    **{i: f"{i}%" for i in range(100)},
    **{i: "Reserved" for i in range(100, 128)},
}
_DIMMING_LIMITS_IO_ENUM: dict[int, str] = {
    **{i: f"Output channel {i + 1}" for i in range(0x1E)},
    0x1E: "All output channels",
    0x1F: "Reserved",
}

# ---------------------------------------------------------------------------
# Telegram definitions
# ---------------------------------------------------------------------------

_CMD_0x1_ActuatorSetOutput = EEPTelegram(
    _EEP_D2_01_Commands[0x1].name,
    [
        _cmd(0x1),
        EEPDataField(
            id="DV",
            name="Dim value",
            offset=8,
            size=3,
            range_enum={
                0x00: "Switch to new output value",
                0x01: "Dim to new output value – dim timer 1",
                0x02: "Dim to new output value – dim timer 2",
                0x03: "Dim to new output value – dim timer 3",
                0x04: "Stop dimming",
                0x05: "Not used",
                0x06: "Not used",
                0x07: "Not used",
            },
        ),
        _io(),
        EEPDataField(
            id="OV",
            name="Output value",
            offset=17,
            size=7,
            range_enum=_OUTPUT_VALUE_ENUM,
        ),
    ],
)

_CMD_0x2_ActuatorSetLocal = EEPTelegram(
    _EEP_D2_01_Commands[0x2].name,
    [
        EEPDataField(
            id="d/e",
            name="Taught-in devices",
            offset=0,
            size=1,
            range_enum={
                0: "Disable taught-in devices",
                1: "Enable taught-in devices",
            },
        ),
        _cmd(0x2),
        EEPDataField(
            id="OC",
            name="Over current shut down",
            offset=8,
            size=1,
            range_enum={
                0: "Static off",
                1: "Automatic restart",
            },
        ),
        EEPDataField(
            id="RO",
            name="Reset over current shut down",
            offset=9,
            size=1,
            range_enum={
                0: "Not active",
                1: "Trigger signal",
            },
        ),
        EEPDataField(
            id="LC",
            name="Local control",
            offset=10,
            size=1,
            range_enum={
                0: "Disable",
                1: "Enable",
            },
        ),
        _io(),
        EEPDataField(
            id="DT2", name="Dim timer 2", offset=16, size=4, range_enum=_DIM_TIMER_ENUM
        ),
        EEPDataField(
            id="DT3", name="Dim timer 3", offset=20, size=4, range_enum=_DIM_TIMER_ENUM
        ),
        EEPDataField(
            id="d/n",
            name="User interface indication",
            offset=24,
            size=1,
            range_enum={
                0: "Day operation",
                1: "Night operation",
            },
        ),
        EEPDataField(
            id="PF",
            name="Power failure detection",
            offset=25,
            size=1,
            range_enum={
                0: "Disable",
                1: "Enable",
            },
        ),
        EEPDataField(
            id="DS",
            name="Default state",
            offset=26,
            size=2,
            range_enum={
                0b00: "0% / OFF",
                0b01: "100% / ON",
                0b10: "Remember previous state",
                0b11: "Not used",
            },
        ),
        EEPDataField(
            id="DT1", name="Dim timer 1", offset=28, size=4, range_enum=_DIM_TIMER_ENUM
        ),
    ],
)

_CMD_0x3_ActuatorStatusQuery = EEPTelegram(
    _EEP_D2_01_Commands[0x3].name, [_cmd(0x3), _io()]
)

_CMD_0x4_ActuatorStatusResponse = EEPTelegram(
    _EEP_D2_01_Commands[0x4].name,
    [
        EEPDataField(
            id="PF",
            name="Power failure detection enabled",
            offset=0,
            size=1,
            range_enum={
                0: "Disabled / not supported",
                1: "Enabled",
            },
        ),
        EEPDataField(
            id="PFD",
            name="Power failure detected",
            offset=1,
            size=1,
            range_enum={
                0: "Not detected / not supported / disabled",
                1: "Detected",
            },
        ),
        _cmd(0x4),
        EEPDataField(
            id="OC",
            name="Over current switch off",
            offset=8,
            size=1,
            range_enum={
                0: "Ready / not supported",
                1: "Executed",
            },
        ),
        EEPDataField(
            id="EL",
            name="Error level",
            offset=9,
            size=2,
            range_enum={
                0b00: "Hardware OK",
                0b01: "Hardware warning",
                0b10: "Hardware failure",
                0b11: "Not supported",
            },
            observable_uid=ObservableUID.ERROR_LEVEL,
        ),
        _io(not_applicable_at_1e=True),
        EEPDataField(
            id="LC",
            name="Local control",
            offset=16,
            size=1,
            range_enum={
                0: "Disabled / not supported",
                1: "Enabled",
            },
        ),
        EEPDataField(
            id="OV",
            name="Output value",
            offset=17,
            size=7,
            range_enum=_OUTPUT_VALUE_ENUM,
        ),
    ],
)

_CMD_0x5_ActuatorSetMeasurement = EEPTelegram(
    _EEP_D2_01_Commands[0x5].name,
    [
        _cmd(0x5),
        EEPDataField(
            id="RM",
            name="Report measurement",
            offset=8,
            size=1,
            range_enum={
                0: "Query only",
                1: "Query / auto reporting",
            },
        ),
        EEPDataField(
            id="RE",
            name="Reset measurement",
            offset=9,
            size=1,
            range_enum={
                0: "Not active",
                1: "Trigger signal",
            },
        ),
        EEPDataField(
            id="e_p",
            name="Measurement mode",
            offset=10,
            size=1,
            range_enum={
                0: "Energy measurement",
                1: "Power measurement",
            },
        ),
        _io(),
        EEPDataField(
            id="MD_LSB",
            name="Measurement delta (LSB)",
            offset=16,
            size=4,
            range_min=0,
            range_max=4095,
        ),
        EEPDataField(id="UN", name="Unit", offset=21, size=3, range_enum=_UNIT_ENUM),
        EEPDataField(
            id="MD_MSB",
            name="Measurement delta (MSB)",
            offset=24,
            size=8,
            range_min=0,
            range_max=4095,
        ),
        EEPDataField(
            id="MAT",
            name="Maximum time between actuator messages",
            offset=32,
            size=8,
            range_enum={
                0x00: "Reserved",
                **{i: f"{i * 10} s" for i in range(1, 256)},
            },
        ),
        EEPDataField(
            id="MIT",
            name="Minimum time between actuator messages",
            offset=40,
            size=8,
            range_enum={
                0x00: "Reserved",
                **{i: f"{i} s" for i in range(1, 256)},
            },
        ),
    ],
)

_CMD_0x6_ActuatorMeasurementQuery = EEPTelegram(
    _EEP_D2_01_Commands[0x6].name,
    [
        _cmd(0x6),
        EEPDataField(
            id="qu",
            name="Query type",
            offset=10,
            size=1,
            range_enum={
                0: "Query energy",
                1: "Query power",
            },
        ),
        _io(),
    ],
)

_CMD_0x7_ActuatorMeasurementResponse = EEPTelegram(
    _EEP_D2_01_Commands[0x7].name,
    [
        _cmd(0x7),
        EEPDataField(id="UN", name="Unit", offset=8, size=3, range_enum=_UNIT_ENUM),
        _io(not_applicable_at_1e=True),
        EEPDataField(
            id="MV",
            name="Measurement value",
            offset=16,
            size=32,
            range_min=0,
            range_max=4294967295,
        ),
    ],
)

_CMD_0x8_ActuatorSetPilotWireMode = EEPTelegram(
    _EEP_D2_01_Commands[0x8].name,
    [
        _cmd(0x8),
        EEPDataField(
            id="PM",
            name="Pilot wire mode",
            offset=13,
            size=3,
            range_enum=_PILOT_WIRE_ENUM,
        ),
    ],
)

_CMD_0x9_ActuatorPilotWireModeQuery = EEPTelegram(
    _EEP_D2_01_Commands[0x9].name, [_cmd(0x9)]
)

_CMD_0xA_ActuatorPilotWireModeResponse = EEPTelegram(
    _EEP_D2_01_Commands[0xA].name,
    [
        _cmd(0xA),
        EEPDataField(
            id="PM",
            name="Pilot wire mode",
            offset=13,
            size=3,
            range_enum=_PILOT_WIRE_ENUM,
            observable_uid=ObservableUID.PILOT_WIRE_MODE,
        ),
    ],
)

# Shared external-interface body fields (CMD 0xB and 0xD have the same layout after I/O)
_EXT_IFACE_FIELDS = [
    EEPDataField(
        id="AOT", name="Auto OFF timer", offset=16, size=16, range_enum=_TIMER_ENUM
    ),
    EEPDataField(
        id="DOT", name="Delay OFF timer", offset=32, size=16, range_enum=_TIMER_ENUM
    ),
    EEPDataField(
        id="EBM",
        name="External switch/push button",
        offset=48,
        size=2,
        range_enum={
            0b00: "Not applicable",
            0b01: "External switch",
            0b10: "External push button",
            0b11: "Auto detect",
        },
    ),
    EEPDataField(
        id="SWT",
        name="2-state switch",
        offset=50,
        size=1,
        range_enum={
            0: "Change of key state sets ON or OFF",
            1: "Specific ON/OFF positions: ON=closed, OFF=open",
        },
    ),
    EEPDataField(
        id="n/a",
        name="Not used",
        offset=51,
        size=5,
        range_enum={0: "Not used"},
    ),
]

_CMD_0xB_ActuatorSetExternalInterfaceSettings = EEPTelegram(
    _EEP_D2_01_Commands[0xB].name, [_cmd(0xB), _io(), *_EXT_IFACE_FIELDS]
)

_CMD_0xC_ActuatorExternalInterfaceSettingsQuery = EEPTelegram(
    _EEP_D2_01_Commands[0xC].name, [_cmd(0xC), _io()]
)

_CMD_0xD_ActuatorExternalInterfaceSettingsResponse = EEPTelegram(
    _EEP_D2_01_Commands[0xD].name,
    [
        _cmd(0xD),
        _io(not_applicable_at_1e=True),
        *_EXT_IFACE_FIELDS,
    ],
)

# CMD 0xF / ECID 0x00–0x02 — Dimming Limits (synthetic keys 0xF0/0xF1/0xF2)
_DIMMING_IO = EEPDataField(
    id="I/O", name="I/O channel", offset=16, size=5, range_enum=_DIMMING_LIMITS_IO_ENUM
)
_DIMMING_MAXV = EEPDataField(
    id="MAXV", name="Maximum dimming value", offset=25, size=7, range_enum=_MAXV_ENUM
)
_DIMMING_MINV = EEPDataField(
    id="MINV", name="Minimum dimming value", offset=33, size=7, range_enum=_MINV_ENUM
)

_CMD_0xF_ECID_0x00_ActuatorSetDimmingLimits = EEPTelegram(
    f"{_EEP_D2_01_Commands[0xF].name} / {_EEP_D2_01_ExtendedCommands[0x00].name}",
    [_cmd(0xF), _ecid(0x00), _DIMMING_IO, _DIMMING_MAXV, _DIMMING_MINV],
)
_CMD_0xF_ECID_0x01_ActuatorDimmingLimitsQuery = EEPTelegram(
    f"{_EEP_D2_01_Commands[0xF].name} / {_EEP_D2_01_ExtendedCommands[0x01].name}",
    [_cmd(0xF), _ecid(0x01), _DIMMING_IO],
)
_CMD_0xF_ECID_0x02_ActuatorDimmingLimitsResponse = EEPTelegram(
    f"{_EEP_D2_01_Commands[0xF].name} / {_EEP_D2_01_ExtendedCommands[0x02].name}",
    [_cmd(0xF), _ecid(0x02), _DIMMING_IO, _DIMMING_MAXV, _DIMMING_MINV],
)

# ---------------------------------------------------------------------------
# Master telegram dictionary (shared by all type variants)
# ---------------------------------------------------------------------------
EEP_D2_01_TELEGRAMS: dict[int, EEPTelegram] = {
    0x01: _CMD_0x1_ActuatorSetOutput,
    0x02: _CMD_0x2_ActuatorSetLocal,
    0x03: _CMD_0x3_ActuatorStatusQuery,
    0x04: _CMD_0x4_ActuatorStatusResponse,
    0x05: _CMD_0x5_ActuatorSetMeasurement,
    0x06: _CMD_0x6_ActuatorMeasurementQuery,
    0x07: _CMD_0x7_ActuatorMeasurementResponse,
    0x08: _CMD_0x8_ActuatorSetPilotWireMode,
    0x09: _CMD_0x9_ActuatorPilotWireModeQuery,
    0x0A: _CMD_0xA_ActuatorPilotWireModeResponse,
    0x0B: _CMD_0xB_ActuatorSetExternalInterfaceSettings,
    0x0C: _CMD_0xC_ActuatorExternalInterfaceSettingsQuery,
    0x0D: _CMD_0xD_ActuatorExternalInterfaceSettingsResponse,
    0xF0: _CMD_0xF_ECID_0x00_ActuatorSetDimmingLimits,
    0xF1: _CMD_0xF_ECID_0x01_ActuatorDimmingLimitsQuery,
    0xF2: _CMD_0xF_ECID_0x02_ActuatorDimmingLimitsResponse,  # extended commands (pending ECID dispatch)
}

# ---------------------------------------------------------------------------
# Action encoders
# ---------------------------------------------------------------------------


def _encode_set_output(action: SetSwitchOutputAction) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=0x01, description=_EEP_D2_01_Commands[0x1].name),
    )
    msg.values["DV"] = EEPMessageValue(raw=action.dim_value, value=action.dim_value)
    msg.values["I/O"] = EEPMessageValue(raw=action.channel, value=action.channel)
    msg.values["OV"] = EEPMessageValue(
        raw=action.output_value, value=action.output_value
    )
    return msg


def _encode_query_status(action: QueryActuatorStatusAction) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=0x03, description=_EEP_D2_01_Commands[0x3].name),
    )
    msg.values["I/O"] = EEPMessageValue(raw=action.channel, value=action.channel)
    return msg


def _encode_query_measurement(action: QueryActuatorMeasurementAction) -> EEPMessage:
    msg = EEPMessage(
        sender=None,
        message_type=EEPMessageType(id=0x06, description=_EEP_D2_01_Commands[0x6].name),
    )
    msg.values["I/O"] = EEPMessageValue(raw=action.channel, value=action.channel)
    msg.values["qu"] = EEPMessageValue(
        raw=int(action.query_power), value=int(action.query_power)
    )
    return msg


_COMMAND_ENCODERS = {
    ActionUID.SET_SWITCH_OUTPUT: _encode_set_output,
    ActionUID.QUERY_ACTUATOR_STATUS: _encode_query_status,
    ActionUID.QUERY_ACTUATOR_MEASUREMENT: _encode_query_measurement,
}


# ---------------------------------------------------------------------------
# Semantic resolvers
# ---------------------------------------------------------------------------

_UN_TO_UNIT: dict[int, str] = {
    0x00: "Ws",
    0x01: "Wh",
    0x02: "kWh",
    0x03: "W",
    0x04: "kW",
}
_ENERGY_UN = {0x00, 0x01, 0x02}
_POWER_UN = {0x03, 0x04}


def _resolve_switch_state(values: dict[str, EEPMessageValue]) -> EEPMessageValue | None:
    ov = values.get("OV")
    if ov is None or ov.raw == 0x7F:
        return None
    return EEPMessageValue(raw=ov.raw, value=ov.raw > 0, unit=None)


def _resolve_output_value(values: dict[str, EEPMessageValue]) -> EEPMessageValue | None:
    ov = values.get("OV")
    if ov is None or ov.raw > 100:
        return None
    return EEPMessageValue(raw=ov.raw, value=ov.raw, unit="%")


def _resolve_energy(values: dict[str, EEPMessageValue]) -> EEPMessageValue | None:
    mv = values.get("MV")
    un = values.get("UN")
    if mv is None or un is None or un.raw not in _ENERGY_UN:
        return None
    return EEPMessageValue(raw=mv.raw, value=mv.raw, unit=_UN_TO_UNIT[un.raw])


def _resolve_power(values: dict[str, EEPMessageValue]) -> EEPMessageValue | None:
    mv = values.get("MV")
    un = values.get("UN")
    if mv is None or un is None or un.raw not in _POWER_UN:
        return None
    return EEPMessageValue(raw=mv.raw, value=mv.raw, unit=_UN_TO_UNIT[un.raw])


_BASE_RESOLVERS = {
    ObservableUID.SWITCH_STATE: _resolve_switch_state,
    ObservableUID.ENERGY: _resolve_energy,
    ObservableUID.POWER: _resolve_power,
}
_DIMMER_RESOLVERS = {
    **_BASE_RESOLVERS,
    ObservableUID.OUTPUT_VALUE: _resolve_output_value,
}

_sc = ScalarCapability  # local alias to keep factory lines short


def _factories(dimming: bool) -> list:
    base = [
        lambda addr, cb: _sc(
            device_address=addr,
            on_state_change=cb,
            observable_uid=ObservableUID.SWITCH_STATE,
        ),
        lambda addr, cb: _sc(
            device_address=addr,
            on_state_change=cb,
            observable_uid=ObservableUID.ERROR_LEVEL,
        ),
        lambda addr, cb: _sc(
            device_address=addr,
            on_state_change=cb,
            observable_uid=ObservableUID.PILOT_WIRE_MODE,
        ),
        lambda addr, cb: _sc(
            device_address=addr, on_state_change=cb, observable_uid=ObservableUID.ENERGY
        ),
        lambda addr, cb: _sc(
            device_address=addr, on_state_change=cb, observable_uid=ObservableUID.POWER
        ),
    ]
    if dimming:
        base.append(
            lambda addr, cb: _sc(
                device_address=addr,
                on_state_change=cb,
                observable_uid=ObservableUID.OUTPUT_VALUE,
            )
        )
    return base


# ---------------------------------------------------------------------------
# EEPSpecification factory + all type variants
# ---------------------------------------------------------------------------
def _spec(type_id: int, name: str, *, dimming: bool = False) -> EEPSpecification:
    """All variants share the same telegram format and action encoders."""
    return EEPSpecification(
        eep=EEP.from_string(f"D2-01-{type_id:02X}"),
        name=f"Electronic switches and dimmers with local control – {name}",
        cmd_size=4,
        cmd_offset=4,
        ecid_offset=8,
        ecid_size=8,
        telegrams=EEP_D2_01_TELEGRAMS,
        command_encoders=_COMMAND_ENCODERS,
        semantic_resolvers=_DIMMER_RESOLVERS if dimming else _BASE_RESOLVERS,
        capability_factories=_factories(dimming),
    )


EEP_D2_01_00 = _spec(0x00, "Type 0x00 – 1 channel, switching + dimming", dimming=True)
EEP_D2_01_01 = _spec(0x01, "Type 0x01 – 1 channel, switching")
EEP_D2_01_02 = _spec(
    0x02, "Type 0x02 – 1 channel, switching + dimming + metering", dimming=True
)
EEP_D2_01_03 = _spec(
    0x03, "Type 0x03 – 1 channel, switching + dimming + metering", dimming=True
)
EEP_D2_01_04 = _spec(
    0x04, "Type 0x04 – 1 channel, switching + dimming (configurable)", dimming=True
)
EEP_D2_01_05 = _spec(
    0x05,
    "Type 0x05 – 1 channel, switching + dimming (configurable) + metering",
    dimming=True,
)
EEP_D2_01_06 = _spec(0x06, "Type 0x06 – 1 channel, switching (no local control)")
EEP_D2_01_07 = _spec(
    0x07, "Type 0x07 – 1 channel, switching (no local control) + metering"
)
EEP_D2_01_08 = _spec(
    0x08, "Type 0x08 – 1 channel, switching + dimming (local control)", dimming=True
)
EEP_D2_01_09 = _spec(
    0x09, "Type 0x09 – 1 channel, switching + dimming + pilot wire", dimming=True
)
EEP_D2_01_0A = _spec(0x0A, "Type 0x0A – 1 channel, switching (full feature set)")
EEP_D2_01_0B = _spec(
    0x0B, "Type 0x0B – 1 channel, switching + metering (full feature set)"
)
EEP_D2_01_0C = _spec(
    0x0C, "Type 0x0C – 1 channel, heating module with pilot wire + metering"
)
EEP_D2_01_0D = _spec(0x0D, "Type 0x0D – micro smart plug, 1 channel, no metering")
EEP_D2_01_0E = _spec(0x0E, "Type 0x0E – micro smart plug, 1 channel, with metering")
EEP_D2_01_0F = _spec(0x0F, "Type 0x0F – slot-in module, 1 channel, no metering")
EEP_D2_01_10 = _spec(0x10, "Type 0x10 – 2 channels, switching")
EEP_D2_01_11 = _spec(0x11, "Type 0x11 – 2 channels, switching")
EEP_D2_01_12 = _spec(0x12, "Type 0x12 – slot-in module, 2 channels, no metering")
EEP_D2_01_13 = _spec(0x13, "Type 0x13 – 4 channels, switching")
EEP_D2_01_14 = _spec(0x14, "Type 0x14 – 8 channels, switching")
EEP_D2_01_15 = _spec(0x15, "Type 0x15 – 4 channels, switching")
EEP_D2_01_16 = _spec(
    0x16, "Type 0x16 – 2 channels, dimming with configurable limits", dimming=True
)
