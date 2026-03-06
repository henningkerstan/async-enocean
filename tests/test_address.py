from enocean_async.address import Address


def test_conversion():
    for i in range(0, 4294967295, 100000):
        assert Address.from_number(i).to_number() == i
        assert Address.from_string(Address.from_number(i).to_string()).to_number() == i

def test_known_values():
    assert Address.from_number(0).to_string() == "00:00:00:00"

def test_is_eurid():
    assert Address.from_number(0).is_eurid()
    assert Address.from_string("FF:7F:FF:FF").is_eurid()
    assert Address.from_string("FF:80:00:00").is_eurid() == False
    assert Address.broadcast().is_eurid() == False

def test_broadcast():
    assert Address.broadcast().to_string() == "FF:FF:FF:FF"
    assert Address.broadcast().is_broadcast() 
    assert Address.broadcast().is_base_address() == False
