import pytest

from enocean_async import EEPID, EnOceanManufacturers


def test_from_and_to_string():
    assert EEPID.from_string("F6-02-01").to_string() == "F6-02-01"


def test_wrong_string():
    with pytest.raises(ValueError):
        EEPID.from_string("F6-0201")

    with pytest.raises(ValueError):
        EEPID.from_string("FZ-06-01")

def test_hash():
    assert EEPID.from_string("F6-02-01").__hash__() == hash((0xF6, 0x02, 0x01, None))

def test_repr():
    id = EEPID(0xF6,0x02,0x01, EnOceanManufacturers.ENOCEAN_GMBH)
    assert id.__repr__() == "EEP(F6-02-01.11)"