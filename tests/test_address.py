from enocean_async import EnOceanAddress


def test_conversion():
    for i in range(0, 4294967295, 100000):
        assert EnOceanAddress.from_number(i).to_number() == i
        assert EnOceanAddress.from_string(EnOceanAddress.from_number(i).to_string()).to_number() == i

def test_known_values():
    assert EnOceanAddress.from_number(0).to_string() == "00:00:00:00"

def test_is_eurid():
    assert EnOceanAddress.from_number(0).is_eurid()
    assert EnOceanAddress.from_string("FF:7F:FF:FF").is_eurid()
    assert EnOceanAddress.from_string("FF:80:00:00").is_eurid() == False
    assert EnOceanAddress.broadcast().is_eurid() == False

def test_broadcast():
    assert EnOceanAddress.broadcast().to_string() == "FF:FF:FF:FF"
    assert EnOceanAddress.broadcast().is_broadcast() 
    assert EnOceanAddress.broadcast().is_base_address() == False
