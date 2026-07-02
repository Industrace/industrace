"""Shutdown safety tests for the probe coordinator."""

from __future__ import annotations

import threading

from network_probe_client import NetworkProbe


def test_stop_does_not_join_current_thread():
    probe = object.__new__(NetworkProbe)
    probe.running = True
    probe.sniffing_thread = None
    probe.heartbeat_thread = None
    probe.transmission_thread = None
    probe.configuration_thread = threading.current_thread()

    NetworkProbe.stop(probe)
    assert probe.running is False


def test_stop_joins_other_alive_threads(monkeypatch):
    joined = []

    class FakeThread:
        def __init__(self, name):
            self.name = name

        def is_alive(self):
            return True

        def join(self, timeout=None):
            joined.append((self.name, timeout))

    probe = object.__new__(NetworkProbe)
    probe.running = True
    probe.sniffing_thread = FakeThread("sniff")
    probe.heartbeat_thread = threading.current_thread()
    probe.transmission_thread = FakeThread("tx")
    probe.configuration_thread = FakeThread("cfg")

    NetworkProbe.stop(probe)

    assert ("sniff", 5) in joined
    assert ("tx", 5) in joined
    assert ("cfg", 5) in joined
    assert not any(name == "heartbeat" for name, _ in joined)
