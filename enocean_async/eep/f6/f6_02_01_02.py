"""F6-02: Rocker Switch, 2 Rocker - Application Styles 1 & 2.

This module contains F6-02-01 and F6-02-02 profiles, which share identical
telegram structures and only differ in their application-level interpretation.

Profiles in this module:
- F6-02-01: Light and blind control - application style 1
- F6-02-02: Light and blind control - application style 2
"""

from ...capabilities.observable import Observable
from ...capabilities.observers.push_button import f6_push_button_factory
from ..id import EEP
from ..profile import EEPDataField, Entity, SimpleProfileSpecification

# Shared datafields definition for all F6-02-xx profiles
_F6_02_DATAFIELDS = [
    EEPDataField(
        id="R1",
        name="Rocker 1st action",
        offset=0,
        size=3,
        range_min=0,
        range_max=7,
        range_enum={
            0: "a1",
            1: "a0",
            2: "b1",
            3: "b0",
        },
    ),
    EEPDataField(
        id="EB",
        name="Energy bow",
        offset=3,
        size=1,
        range_enum={0: "released", 1: "pressed"},
    ),
    EEPDataField(
        id="R2",
        name="Rocker 2nd action",
        offset=4,
        size=3,
        range_min=0,
        range_max=7,
        range_enum={
            0: "a1",
            1: "a0",
            2: "b1",
            3: "b0",
        },
    ),
    EEPDataField(
        id="SA",
        name="2nd action",
        offset=7,
        size=1,
        range_enum={0: "No 2nd action", 1: "2nd action valid"},
    ),
]

_F6_02_FACTORIES = [f6_push_button_factory()]

_F6_02_ENTITIES = [
    Entity(id="a0", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="a1", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="b0", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="b1", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="ab0", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="ab1", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="a0b1", observables=frozenset({Observable.PUSH_BUTTON})),
    Entity(id="a1b0", observables=frozenset({Observable.PUSH_BUTTON})),
]

# Define all F6-02-xx variants using the shared datafields structure
EEP_F6_02_01 = SimpleProfileSpecification(
    eep=EEP.from_string("F6-02-01"),
    name="Light and blind control - application style 1",
    datafields=_F6_02_DATAFIELDS,
    observers=_F6_02_FACTORIES,
    entities=_F6_02_ENTITIES,
)

EEP_F6_02_02 = SimpleProfileSpecification(
    eep=EEP.from_string("F6-02-02"),
    name="Light and blind control - application style 2",
    datafields=_F6_02_DATAFIELDS,
    observers=_F6_02_FACTORIES,
    entities=_F6_02_ENTITIES,
)
