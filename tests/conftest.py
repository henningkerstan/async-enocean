"""Shared fixtures for the enocean-async test suite.

All fixtures are session- or function-scoped and kept deliberately small so
that individual test modules can compose them freely.
"""

import pytest

from enocean_async.address import EURID, BaseAddress
from enocean_async.capabilities.state_change import StateChange
from enocean_async.erp1.rorg import RORG
from enocean_async.erp1.telegram import ERP1Telegram
from enocean_async.esp3.packet import SYNC_BYTE, crc8

# ---------------------------------------------------------------------------
# Address fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def device_address() -> EURID:
    """A typical device EURID (in the EURID range 00:00:00:00 – FF:7F:FF:FF)."""
    return EURID.from_string("01:23:45:67")


@pytest.fixture
def base_address() -> BaseAddress:
    """A typical gateway BaseAddress (in the range FF:80:00:00 – FF:FF:FF:80)."""
    return BaseAddress.from_string("FF:80:00:01")


# ---------------------------------------------------------------------------
# State-change capture
# ---------------------------------------------------------------------------

@pytest.fixture
def state_changes() -> tuple[list[StateChange], callable]:
    """Returns (received_list, callback).

    Pass *callback* as ``on_state_change`` to any Capability; all emitted
    StateChange objects accumulate in *received_list*.
    """
    received: list[StateChange] = []
    return received, received.append


# ---------------------------------------------------------------------------
# ERP1 telegram factories
# ---------------------------------------------------------------------------

@pytest.fixture
def make_4bs_erp1(device_address: EURID):
    """Factory: build a 4BS ERP1Telegram from 4 raw payload bytes."""

    def _make(telegram_data: bytes, rssi: int = 0x55) -> ERP1Telegram:
        assert len(telegram_data) == 4, "4BS payload must be exactly 4 bytes"
        return ERP1Telegram(
            rorg=RORG.RORG_4BS,
            telegram_data=telegram_data,
            sender=device_address,
            rssi=rssi,
        )

    return _make


@pytest.fixture
def make_rps_erp1(device_address: EURID):
    """Factory: build an RPS ERP1Telegram from 1 raw payload byte."""

    def _make(telegram_data: bytes, rssi: int = 0x55) -> ERP1Telegram:
        assert len(telegram_data) == 1, "RPS payload must be exactly 1 byte"
        return ERP1Telegram(
            rorg=RORG.RORG_RPS,
            telegram_data=telegram_data,
            sender=device_address,
            rssi=rssi,
        )

    return _make


# ---------------------------------------------------------------------------
# ESP3 frame helper (used by protocol tests)
# ---------------------------------------------------------------------------

def build_esp3_frame(
    data: bytes,
    optional: bytes = b"",
    ptype: int = 0x02,
) -> bytes:
    """Assemble a valid ESP3 byte frame (sync + header + CRCs)."""
    data_len = len(data)
    opt_len = len(optional)
    header = bytes([
        (data_len >> 8) & 0xFF,
        data_len & 0xFF,
        opt_len,
        ptype,
    ])
    return (
        bytes([SYNC_BYTE])
        + header
        + bytes([crc8(header)])
        + data
        + optional
        + bytes([crc8(data + optional)])
    )
