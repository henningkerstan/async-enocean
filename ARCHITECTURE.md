# Architecture

<!-- This file documents the architecture of the enocean-async library. -->

## Overview

`enocean-async` is an asyncio-based Python library for communicating with EnOcean devices over an EnOcean USB gateway. The library has two symmetric pipelines:

- **Observable pipeline** (receive): raw radio telegrams → typed `EntityStateChange` objects carrying entity state updates like `entity_id="temperature", values={TEMPERATURE: 21.3}`.
- **Action pipeline** (send): typed `Command` subclasses carrying `entity_id` and action-specific parameters → encoded `ERP1Telegram` → radio signal, e.g. `SetCoverPosition(entity_id="cover", position=64)` or `StopCover(entity_id="cover")`.

Each pipeline layers protocol detail away from the application. The gateway orchestrates both.

---

## Entities, Observables, and Actions

These three concepts form the semantic vocabulary of the library.

### Entities

An **entity** is a physical real-world thing within a device — a push button, a cover motor, a relay channel, a temperature sensor. It is the primary unit of identity in the library.

Entities are declared statically in the EEP specification, since the EEP fully defines what physical sub-units a device has. Each entity has:

- A stable string **id** within the device (e.g. `"a0"` for a rocker button, `"cover"` for a cover motor, `"0"` for relay channel 0, `"temperature"` for a temperature sensor).
- A set of **observables** — the quantities this entity reports.
- A list of **actions** — the commands this entity accepts.

```python
@dataclass(frozen=True)
class Entity:
    id: str
    observables: frozenset[Observable]
    actions: frozenset[Action] = field(default_factory=frozenset)
```

Examples as declared in EEP files:

```python
# F6-02: four single-rocker entities + four combined-rocker entities
# Combined presses are distinct telegram types (SA=1 flag), not timing coincidences.
Entity(id="a0",   observables=frozenset({PUSH_BUTTON}))  # rocker A, down
Entity(id="b0",   observables=frozenset({PUSH_BUTTON}))  # rocker B, down
Entity(id="a1",   observables=frozenset({PUSH_BUTTON}))  # rocker A, up
Entity(id="b1",   observables=frozenset({PUSH_BUTTON}))  # rocker B, up
Entity(id="ab0",  observables=frozenset({PUSH_BUTTON}))  # A-down + B-down simultaneously
Entity(id="ab1",  observables=frozenset({PUSH_BUTTON}))  # A-up   + B-up   simultaneously
Entity(id="a0b1", observables=frozenset({PUSH_BUTTON}))  # A-down + B-up   simultaneously
Entity(id="a1b0", observables=frozenset({PUSH_BUTTON}))  # A-up   + B-down simultaneously

# A5-04: two independent sensor entities (separate concerns)
Entity(id="temperature", observables=frozenset({TEMPERATURE}))
Entity(id="humidity",    observables=frozenset({HUMIDITY}))

# D2-05: one cover entity, multiple observables (all describe the same physical thing)
Entity(
    id="cover",
    observables=frozenset({COVER_STATE, POSITION, ANGLE}),
    actions=frozenset({SET_COVER_POSITION, STOP_COVER, QUERY_COVER_POSITION}),
)

# D2-01-00: one relay channel (each D2-01 variant declares its exact channel count)
Entity(
    id="0",
    observables=frozenset({SWITCH_STATE, ERROR_LEVEL, POWER, ENERGY}),
    actions=frozenset({SET_SWITCH_OUTPUT, QUERY_ACTUATOR_STATUS, QUERY_ACTUATOR_MEASUREMENT}),
)
```

The principle for grouping observables into entities: multiple observables belong to the same entity when they describe the **same physical thing** and are not independently meaningful (cover POSITION, ANGLE, COVER_STATE are all facets of one cover motor). Observables belong to separate entities when they are independently meaningful and have separate real-world identities (temperature and humidity are separate sensors on the same chip, but distinct physical quantities).

A fully unique physical thing in the system is the pair `(device_address, entity_id)`.

### Observables

An **observable** is a quantity that an entity reports. It has two intrinsic properties:

- A **unique id** — what it is observing (e.g. `"temperature"`, `"switch_state"`, `"push_button"`).
- A **native unit** — the one canonical physical unit for that quantity (`None` for dimensionless or categorical values).

```python
class Observable(str, Enum):
    def __new__(cls, id: str, unit: str | None = None):
        obj = str.__new__(cls, id)
        obj._value_ = id
        obj.unit = unit
        return obj

    TEMPERATURE   = ("temperature",   "°C")
    HUMIDITY      = ("humidity",      "%")
    ILLUMINATION  = ("illumination",  "lx")
    POWER         = ("power",         "W")
    ENERGY        = ("energy",        "Wh")
    SWITCH_STATE  = ("switch_state",  None)
    PUSH_BUTTON   = ("push_button",   None)
    POSITION      = ("position",      "%")
    COVER_STATE   = ("cover_state",   None)
    ...
```

The `str, Enum` pattern makes each member both an `Observable` instance and a plain `str`, preserving dict-key and equality semantics. The unit is fixed per observable type — if two quantities differ in unit, they are different observables (e.g. `POWER = "W"` and `ENERGY = "Wh"` are separate members).

Observable names are **semantic, not unit-encoding**. The name says *what* is being observed (`TEMPERATURE`, `POWER`), not *how* it is expressed. The unit is available as `Observable.TEMPERATURE.unit` — encoding it redundantly in the identifier (`TEMPERATURE_CELSIUS`, `POWER_WATTS`) would conflate two distinct properties and produce unnecessarily verbose names. The only reason to distinguish by unit in the name would be if the same physical concept existed in two units simultaneously — which cannot happen here since units are canonical and fixed.

An observable update is delivered as part of an `EntityStateChange` (see below).

### Actions

An **action** is a category of command sent _to_ a device — telling a cover to move, a relay to switch, a dimmer to change brightness. Actions are classified by `Action` enum members (`capabilities/action.py`):

```python
class Action(StrEnum):
    SET_COVER_POSITION         = "set_cover_position"
    STOP_COVER                 = "stop_cover"
    QUERY_COVER_POSITION       = "query_cover_position"
    DIM                        = "dim"
    SET_FAN_SPEED              = "set_fan_speed"
    SET_SWITCH_OUTPUT          = "set_switch_output"
    QUERY_ACTUATOR_STATUS      = "query_actuator_status"
    QUERY_ACTUATOR_MEASUREMENT = "query_actuator_measurement"
```

`Action` names things you _send_. `Observable` names things you _receive_. They are separate classifiers: `STOP_COVER` is an action with no direct observable counterpart; `SET_COVER_POSITION` is an action that will eventually produce `POSITION` and `COVER_STATE` updates as the device reports back. The formal link between an action and the observables it affects is declared on the `Entity` — both `observables` and `actions` live together on the entity they belong to.

---

## EntityStateChange

When a capability processes a telegram and produces an update, it emits an `EntityStateChange`:

```python
@dataclass
class EntityStateChange:
    device_address: SenderAddress   # which device
    entity_id: str                  # which entity within the device
    values: dict[Observable, Any]   # all observable values reported in this telegram
    timestamp: float                # wall-clock time
    time_elapsed: float             # duration since last related event (e.g. hold duration)
    source: StateChangeSource       # TELEGRAM or TIMER
```

The complete entity identity is the pair `(device_address, entity_id)`; the `entity_id` is only sufficient within the scope of a device. The `values` dict may be a partial update — a telegram may only carry a subset of an entity's observables (e.g. a D2-01 measurement response carries `POWER` but not `SWITCH_STATE`). The unit for any value is always `observable.unit`.

Examples:

```python
# Cover — all three observables arrive in one telegram
EntityStateChange(entity_id="cover", values={POSITION: 75, COVER_STATE: "open", ANGLE: 0})

# Push button — single observable entity, timer-sourced hold event
EntityStateChange(entity_id="a0", values={PUSH_BUTTON: "hold"}, source=StateChangeSource.TIMER)

# D2-01 actuator status — partial update
EntityStateChange(entity_id="0", values={SWITCH_STATE: "on", ERROR_LEVEL: 0})
```

---

## Command

A command sent to a device is represented as a typed `Command` subclass:

```python
@dataclass
class Command:
    entity_id: str   # which entity within the device to target
    action: Action   # what to do

@dataclass
class SetSwitchOutput(Command):
    state: str       # "on" / "off"

@dataclass
class SetCoverPosition(Command):
    position: int    # 0–127 (maps to 0–100%)
    angle: int = 0

@dataclass
class StopCover(Command):
    pass             # action IS the message; no parameters

@dataclass
class Dim(Command):
    value: int
    speed: int
```

Command parameters are action-specific and typed — there is no generic values dict, because command parameters are not "things being observed." The `entity_id` targets the physical sub-unit; the typed fields provide action-specific inputs.

The gateway send method:

```python
await gateway.send_command(
    destination=device_address,
    command=SetCoverPosition(entity_id="cover", position=64, angle=0),
)
```

---

## DeviceDescriptor

`DeviceDescriptor` is the setup-time description of what a device type exposes and accepts. It is returned by `Gateway.device_descriptor(address)` after calling `add_device()`, before any telegrams arrive:

```python
@dataclass
class DeviceDescriptor:
    eep: EEP
    entities: list[Entity]
```

`entities` always includes three metadata entities added by the gateway regardless of EEP:

```python
Entity(id="rssi",           observables=frozenset({RSSI}),           actions=[])
Entity(id="last_seen",      observables=frozenset({LAST_SEEN}),      actions=[])
Entity(id="telegram_count", observables=frozenset({TELEGRAM_COUNT}), actions=[])
```

An integration (e.g. Home Assistant) uses `DeviceDescriptor.entities` to create platform entities at setup time — without waiting for a single telegram.

---

## Receive pipeline (Observables)

```
Radio signal
    │ serial bytes
    ▼
EnOceanSerialProtocol3
    │ ESP3 framing (sync, CRC, packet type)
    ▼
ESP3Packet
    │ RADIO_ERP1 detection
    ▼
ERP1Telegram      rorg, sender EURID, raw payload bits, rssi
    │ EEP profile lookup → EEPHandler.decode()
    ▼
EEPMessage
  .values    {field_id  → EEPMessageValue}   ← EEP spec vocabulary: "TMP", "ILL1", "R1"
  .entities  {observable → EntityValue}      ← semantic vocabulary: TEMPERATURE, ILLUMINATION
    │ Capability.decode()  (one call per capability in device.capabilities)
    ├── ScalarCapability(observable=TEMPERATURE) → reads entities[TEMPERATURE]
    ├── ScalarCapability(observable=ILLUMINATION) → reads entities[ILLUMINATION]
    ├── CoverCapability → reads entities[POSITION]+entities[ANGLE], infers COVER_STATE
    ├── PushButtonCapability → reads values["R1"], values["EB"], … (raw field access)
    └── MetaDataCapability → reads rssi, generates timestamps
    │ _emit()
    ▼
EntityStateChange(device_address, entity_id, values, timestamp, source)
    │ on_state_change callback
    ▼
Application
```

The `EEPHandler` runs four passes during decode:

| Pass | Purpose |
|------|---------|
| **1 — Raw extraction** | Read every field's raw int from the telegram bitstring into a scratch dict. Done first so interdependent scale functions have full context. |
| **2 — Value decoding** | Apply enum lookup or linear scaling per field → `EEPMessage.values[field.id]` as `EEPMessageValue(raw, value, unit)`. |
| **3 — Observable propagation** | For each field with `observable` set: copy `values[field.id]` → `entities[observable]` as `EntityValue(value, unit)`. Translates spec vocabulary to semantic vocabulary. |
| **4 — Semantic resolvers** | Run `SemanticResolver` callables that synthesise a single observable from multiple fields (e.g., A5-06: pick ILL1 or ILL2 based on range-select bit). |

Note: `EEPMessage.values` contains `EEPMessageValue` (raw int + decoded value + unit), while `EEPMessage.entities` contains the lighter `EntityValue` (decoded value + unit only — raw is not needed at the semantic layer).

---

## Send pipeline (Actions)

```
Application
    │ gateway.send_command(destination, SetCoverPosition(entity_id="cover", position=64))
    ▼
Command subclass instance (typed, with entity_id and validated fields)
    │ EEPSpecification.command_encoders[command.action](command)
    ▼
EEPMessage
  .message_type  ← selects which telegram type to encode
  .values        ← {field_id → EEPMessageValue(raw)} filled in by the encoder
    │ EEPHandler.encode()
    ├── Determine data buffer size from max(field.offset+field.size) + cmd_size
    ├── Allocate zero-filled bytearray
    ├── Write CMD bits at cmd_offset/cmd_size
    └── Write each field's raw value at field.offset/field.size
    ▼
ERP1Telegram(rorg, telegram_data, sender=device.sender, destination=address)
    │ .to_esp3()
    ▼
ESP3Packet
    │ Gateway.send_esp3_packet()
    ▼
Radio signal → Device
```

---

## Layers

### 1. Serial / ESP3 Layer / ERP1 Layer

**Files:** `esp3/`, `erp1/`

`EnOceanSerialProtocol3` (an `asyncio.Protocol`) reassembles byte streams into `ESP3Packet` objects. The gateway routes packets by type: `RADIO_ERP1` → ERP1 processing; `RESPONSE` → matched to a pending `send_esp3_packet()` future.

`ERP1Telegram` provides bit-addressable access to the payload (`bitstring_raw_value`, `set_bitstring_raw_value`) used by both the decode and encode paths.

### 2. EEP Layer

**Files:** `eep/profile.py`, `eep/handler.py`, `eep/message.py`, `eep/a5/`, `eep/f6/`, `eep/d2/`

Every supported EEP is a module-level `EEPSpecification` (or `SimpleProfileSpecification`) instance in `EEP_SPECIFICATIONS`, keyed by `EEP` (the ID struct).

The two key types are:

- **`EEP`** (`eep/id.py`): The 4-tuple identifier — `rorg`, `func`, `type_`, optional `manufacturer`. Used as the dict key in `EEP_SPECIFICATIONS` and as a reference in `EEPMessage.eep`.
- **`EEPSpecification`** (`eep/profile.py`): The full profile — `cmd_size`, `cmd_offset`, `telegrams` dict, `semantic_resolvers`, `capability_factories`, `entities`. The simpler `SimpleProfileSpecification` is a convenience subclass for single-telegram EEPs (no CMD field; wraps datafields into a single `EEPTelegram` at key `0`).

`EEPDataField` is the atomic unit: bit offset, size, scale functions, unit function, enum map, and optional `observable` annotation that bridges the spec and semantic vocabularies.

`EEPSpecification` carries five extension points: `telegrams`, `semantic_resolvers`, `capability_factories` (receive path behaviour), `command_encoders` (send path encoding), and `entities` (static declaration of physical entities).

### 3. Capability Layer

**Files:** `capabilities/`

Capabilities are the behavioural layer. Each subclass interprets a decoded `EEPMessage` for one specific entity and emits `EntityStateChange` objects.

- **`ScalarCapability`** (`scalar.py`): Generic, parameterised by `observable` and `entity_id`. Reads `message.entities[observable]` and emits an `EntityStateChange`. Covers all plain scalar observables (temperature, illumination, motion, voltage, window state, …).
- **`CoverCapability`** (`position_angle.py`): Stateful: takes the received position and angle values, infers `cover_state` from successive position deltas, and runs an asyncio watchdog to emit `stopped` after 1.5 s of radio silence. Emits one `EntityStateChange` with `entity_id="cover"` and `values={POSITION: …, ANGLE: …, COVER_STATE: …}`.
- **`PushButtonCapability` / `F6_02_01_02PushButtonCapability`** (`push_button.py`): Stateful: decodes rocker switch bit patterns into button events (pushed, hold, click, double click, released) using timeouts. Each button emits `EntityStateChange` with its own `entity_id` (`"a0"`, `"b0"`, …).
- **`MetaDataCapability`** (`metadata.py`): Emits RSSI, last-seen timestamp, and telegram count as separate `EntityStateChange` objects. Always prepended to a device's capability list by the gateway.

### 4. Device Layer

**Files:** `device/device.py`, `device/catalog.py`

`Device` is a runtime object (created by `add_device()`) holding the device's address, EEP ID, name, and instantiated `Capability` list. Every incoming `EEPMessage` is forwarded to all capabilities.

### 5. Gateway Layer

**File:** `gateway.py`

The top-level orchestrator. For receiving: serial I/O → packet routing → ERP1 routing → EEP decoding → capability dispatch. For sending: `send_command()` → encoder → `EEPHandler.encode()` → `send_esp3_packet()`.

Layered callbacks for application code:
- `add_esp3_received_callback` — raw packet level
- `add_erp1_received_callback` — parsed telegram (filterable by sender)
- `add_eep_message_received_callback` — decoded EEP message (filterable by sender)
- `add_state_change_callback` — semantic entity state updates from capabilities

#### Auto-reconnect

When the serial connection is lost unexpectedly, the gateway automatically attempts to re-establish it. This is controlled by the `auto_reconnect` parameter. When enabled (default) and the connection is lost, the gateway tries to reconnect for 1 hour. A successful reconnect cancels the task and logs a confirmation. Exhausting all attempts logs a final error and stops retrying.

---

## Key design decisions

### EEP definitions are self-describing

`EEPSpecification.entities` (physical entity model), `capability_factories` (receive behaviour), and `command_encoders` (send encoding) mean the gateway contains zero EEP-specific logic. Adding a new EEP or a new commandable action never requires touching `gateway.py`.

### Entities are physical things, declared in the EEP

Each EEP statically declares its `Entity` list. Entities are physical real-world sub-units (push buttons, relay channels, cover motors, sensor elements). The EEP fully specifies what entities exist — including their observable types and accepted actions — before any telegram arrives.

This is possible because EnOcean EEP variants are fixed: `D2-01-00` has exactly one relay channel; `F6-02-01` has exactly four rocker buttons. Instance count is per-variant, not discovered at runtime.

### Observable carries its native unit

`Observable` is a `str, Enum` whose members carry a `unit: str | None` property. The unit is intrinsic to what is being observed: temperature is always in `°C`, illumination always in `lx`. If two quantities differ in unit, they are distinct `Observable` members. This eliminates all scattered `(Observable, str | None)` unit pairs that previously appeared in factory declarations, `DeviceDescriptor`, and `StateChange`.

### EntityStateChange is entity-centric, not observable-centric

A single telegram updates an entity's state. When a cover reports its position, angle, and state simultaneously, a single `EntityStateChange` with `values={POSITION: 75, ANGLE: 0, COVER_STATE: "open"}` is emitted — not three separate events. The consumer receives one coherent update per entity per telegram. Partial updates (when a telegram only carries some of an entity's observables) are naturally expressed as a `values` dict with fewer keys.

### Two-vocabulary `EEPMessage`

`EEPMessage.values` holds the raw EEP field view (spec field IDs: `"TMP"`, `"ILL1"`), each as an `EEPMessageValue(raw, value, unit)`. `EEPMessage.entities` holds the semantic observable view (`Observable` enum members), each as a lighter `EntityValue(value, unit)` — the raw int is not needed at the semantic layer. Capabilities always read from `entities`, making them EEP-agnostic: `ScalarCapability(observable=TEMPERATURE)` works for A5-02, A5-04, A5-08, or any future temperature-bearing EEP without modification.

### Semantic resolvers bridge multi-field observables

Some EEP profiles spread one observable across multiple fields (A5-06: two illumination ranges + a select bit). `SemanticResolver` callables live in the EEP definition module and run as pass 4 of the decoder. Capabilities remain oblivious to this complexity.

---

## Adding a new EEP

1. Create a module under `eep/<rorg>/` with an `EEPSpecification` or `SimpleProfileSpecification` instance.
2. Declare `entities` — one `Entity` per physical entity, with its `observables` and `actions`.
3. Annotate fields with `observable` where a 1:1 mapping to an observable exists. Add a `SemanticResolver` for multi-field combinations.
4. Populate `capability_factories` with the appropriate factory callables (e.g. `scalar_factory`, `cover_factory`, `f6_push_button_factory`).
5. Optionally populate `command_encoders` if the device accepts commands. Add the corresponding `Command` subclass in `capabilities/<profile>_commands.py`.
6. Register in `eep/__init__.py`'s `EEP_SPECIFICATIONS`.

No changes to `gateway.py`, `device/device.py`, or any capability class are required.
