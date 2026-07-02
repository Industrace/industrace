"""Packet processing limits for max_packet_size and buffer_size."""

from __future__ import annotations

import threading
from collections import deque
from types import SimpleNamespace

from scapy.all import Raw

from probe_models import ProbeConfiguration
from probe_packet_processing import ProbePacketProcessingMixin


class _FakePayloadPacket:
    def __init__(self, payload: bytes = b"x" * 200):
        self._payload = payload

    def __contains__(self, layer):
        return layer is Raw

    def __getitem__(self, layer):
        return self._payload


class _PacketProbe(ProbePacketProcessingMixin):
    def __init__(self, max_packet_size: int = 1518, buffer_size: int = 128):
        self.config = ProbeConfiguration(
            probe_id="11111111-1111-1111-1111-111111111111",
            api_key="key",
            server_url="https://example.com",
            interface_name="eth0",
            max_packet_size=max_packet_size,
            buffer_size=buffer_size,
            payload_analysis=True,
        )
        self.health = SimpleNamespace(record_packet_seen=lambda: None, record_warning=lambda: None)
        self.stats = {"packets_captured": 0}
        self._sampling_rate = 1.0
        self._stats_batch_packets = 0
        self._stats_batch_bytes = 0
        self._stats_flush_batch_size = 2000
        self._stats_flush_max_seconds = 2.0
        self._last_stats_flush_ts = 0.0
        self._traffic_buckets = []
        self._rate_window_seconds = 60
        self.rate_lock = threading.Lock()
        self.data_buffer = deque()
        self._payload_buffer_bytes = 0
        self._payload_buffer_dropped_count = 0
        self.data_buffer_lock = threading.Lock()
        self.data_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.devices = {}
        self.connections = {}
        self._pending_device_macs = set()
        self._pending_new_connections = 0
        self._connection_ttl_seconds = 900
        self._connection_prune_interval_seconds = 60
        self._last_connection_prune_ts = 0.0

    def _signal_pending_delivery(self):
        return None

    def _maybe_prune_connections(self):
        return None


def test_packet_handler_skips_oversized_packets():
    probe = _PacketProbe(max_packet_size=100)
    seen = []

    probe.health.record_packet_seen = lambda: seen.append(True)
    probe._packet_handler(SimpleNamespace(__len__=lambda self: 200))

    assert seen == []


def test_process_payload_respects_buffer_size():
    probe = _PacketProbe(buffer_size=64)
    probe._process_payload(_FakePayloadPacket(bytes(range(256)) * 4))

    assert probe._payload_buffer_dropped_count == 1
    assert len(probe.data_buffer) == 0
