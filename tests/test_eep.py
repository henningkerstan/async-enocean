import pytest

from enocean_async import EEP, EnOceanManufacturers


def test_from_and_to_string():
    # EEP uses __str__ for string conversion; no .to_string() method exists.
    assert str(EEP.from_string("F6-02-01")) == "F6-02-01"


def test_wrong_string():
    with pytest.raises(ValueError):
        EEP.from_string("F6-0201")

    with pytest.raises(ValueError):
        EEP.from_string("FZ-06-01")

def test_hash():
    assert EEP.from_string("F6-02-01").__hash__() == hash((0xF6, 0x02, 0x01, None))

def test_repr():
    # __str__ uses manufacturer.name (the Python enum member name, e.g. "ENOCEAN_GMBH"),
    # not the integer value.
    id = EEP(0xF6,0x02,0x01, EnOceanManufacturers.ENOCEAN_GMBH)
    assert id.__repr__() == "EEP(F6-02-01.ENOCEAN_GMBH)"