"""Tests for MAC address normalization."""
from app.services.mac_utils import normalize_mac_address


def test_normalize_mac_colon_format():
    assert normalize_mac_address("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"


def test_normalize_mac_dash_format():
    assert normalize_mac_address("AA-BB-CC-DD-EE-FF") == "AA:BB:CC:DD:EE:FF"


def test_normalize_mac_no_separator():
    assert normalize_mac_address("aabbccddeeff") == "AA:BB:CC:DD:EE:FF"


def test_normalize_mac_invalid():
    assert normalize_mac_address("not-a-mac") is None
    assert normalize_mac_address("") is None
    assert normalize_mac_address(None) is None
