"""Unit tests for industrial protocol payload heuristics."""

from __future__ import annotations

from probe_protocol_analyzer import ProtocolAnalyzer


def test_opcua_helo_payload():
    analysis = ProtocolAnalyzer._analyze_payload(b"HELO" + b"\x00" * 20)
    assert analysis.get("opcua_info") == {"message_type": "Hello"}


def test_iec104_valid_framing():
    apdu_length = 10
    payload = bytes([0x68, apdu_length]) + b"\x00" * (apdu_length + 2)
    analysis = ProtocolAnalyzer._analyze_payload(payload)
    assert analysis.get("iec104_info") == {"apdu_length": apdu_length}
    assert analysis.get("industrial_protocol") is True


def test_iec104_invalid_length_not_marked():
    payload = bytes([0x68, 0xFF]) + b"\x00" * 4
    analysis = ProtocolAnalyzer._analyze_payload(payload)
    assert "iec104_info" not in analysis
