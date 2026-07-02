"""Runtime-safe remote configuration application helpers."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from probe_models import ProbeConfiguration


def apply_remote_configuration(
    cfg: Dict[str, Any],
    config: ProbeConfiguration,
    protocol_capture_filter: Optional[str],
    set_sampling_rate: Callable[[float], None],
    rebuild_protocol_capture_filter: Callable[[List[str]], None],
) -> tuple[list[str], Optional[str]]:
    """Apply remote configuration values and return changed fields/new protocol filter."""

    changed_fields: List[str] = []
    next_protocol_capture_filter = protocol_capture_filter

    def to_int(v, default):
        try:
            return int(v)
        except Exception:
            return default

    def to_float(v, default):
        try:
            return float(v)
        except Exception:
            return default

    def to_bool(v, default):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on")
        return default

    if "interface_name" in cfg and cfg["interface_name"] and cfg["interface_name"] != config.interface_name:
        config.interface_name = str(cfg["interface_name"])
        changed_fields.append("interface_name")

    if "promiscuous_mode" in cfg:
        new_val = to_bool(cfg["promiscuous_mode"], config.promiscuous_mode)
        if new_val != config.promiscuous_mode:
            config.promiscuous_mode = new_val
            changed_fields.append("promiscuous_mode")

    if "capture_filter" in cfg:
        new_val = cfg["capture_filter"] or None
        if new_val != next_protocol_capture_filter:
            next_protocol_capture_filter = new_val
            changed_fields.append("capture_filter")

    if "sampling_rate" in cfg:
        new_val = max(0.01, min(1.0, to_float(cfg["sampling_rate"], config.sampling_rate)))
        if new_val != config.sampling_rate:
            config.sampling_rate = new_val
            set_sampling_rate(new_val)
            changed_fields.append("sampling_rate")

    if "metadata_extraction" in cfg:
        new_val = to_bool(cfg["metadata_extraction"], config.metadata_extraction)
        if new_val != config.metadata_extraction:
            config.metadata_extraction = new_val
            changed_fields.append("metadata_extraction")

    if "payload_analysis" in cfg:
        new_val = to_bool(cfg["payload_analysis"], config.payload_analysis)
        if new_val != config.payload_analysis:
            config.payload_analysis = new_val
            changed_fields.append("payload_analysis")

    if "heartbeat_interval" in cfg:
        new_val = max(10, min(300, to_int(cfg["heartbeat_interval"], config.heartbeat_interval)))
        if new_val != config.heartbeat_interval:
            config.heartbeat_interval = new_val
            changed_fields.append("heartbeat_interval")

    if "data_transmission_interval" in cfg:
        new_val = max(60, min(3600, to_int(cfg["data_transmission_interval"], config.data_transmission_interval)))
        if new_val != config.data_transmission_interval:
            config.data_transmission_interval = new_val
            changed_fields.append("data_transmission_interval")

    if "max_retry_attempts" in cfg:
        new_val = max(1, min(10, to_int(cfg["max_retry_attempts"], config.max_retry_attempts)))
        if new_val != config.max_retry_attempts:
            config.max_retry_attempts = new_val
            changed_fields.append("max_retry_attempts")

    if "enabled_protocols" in cfg and isinstance(cfg["enabled_protocols"], list):
        new_protocols = [str(p) for p in cfg["enabled_protocols"] if str(p).strip()]
        if new_protocols != config.enabled_protocols:
            config.enabled_protocols = new_protocols
            changed_fields.append("enabled_protocols")
            rebuild_protocol_capture_filter(new_protocols)

    return changed_fields, next_protocol_capture_filter
