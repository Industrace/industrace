"""CLI/config entrypoints for the network probe."""

from __future__ import annotations

import argparse
import configparser
import logging
import os
import sys
from pathlib import Path

from probe_models import ProbeConfiguration

logger = logging.getLogger(__name__)


def load_config(config_file: str) -> ProbeConfiguration:
    """Load configuration from a file."""
    config = configparser.ConfigParser()
    config.read(config_file)

    if "main" not in config:
        raise ValueError("Missing required [main] section in config file")

    main_section = config["main"]
    network_section = config["network"] if "network" in config else {}
    analysis_section = config["analysis"] if "analysis" in config else {}
    telecontrol_section = config["telecontrol"] if "telecontrol" in config else {}
    security_section = config["security"] if "security" in config else {}

    probe_id = main_section.get("probe_id", "")
    api_key = main_section.get("api_key", "")
    server_url = main_section.get("server_url", "")
    if not probe_id:
        raise ValueError("Missing required config value: [main] probe_id")
    if not api_key:
        raise ValueError("Missing required config value: [main] api_key")
    if not server_url:
        raise ValueError("Missing required config value: [main] server_url")

    interface_name = network_section.get("interface_name", "eth0")
    promiscuous_mode = config.getboolean("network", "promiscuous_mode", fallback=True) if "network" in config else True
    capture_filter = config.get("network", "capture_filter", fallback=None) if "network" in config else None
    max_packet_size = config.getint("network", "max_packet_size", fallback=1518) if "network" in config else 1518
    buffer_size = config.getint("network", "buffer_size", fallback=65536) if "network" in config else 65536

    enabled_protocols_raw = analysis_section.get("enabled_protocols", "") if "analysis" in config else ""
    enabled_protocols = [p.strip() for p in enabled_protocols_raw.split(",") if p.strip()] if enabled_protocols_raw else []

    sampling_rate = config.getfloat("analysis", "sampling_rate", fallback=1.0) if "analysis" in config else 1.0
    metadata_extraction = config.getboolean("analysis", "metadata_extraction", fallback=True) if "analysis" in config else True
    payload_analysis = config.getboolean("analysis", "payload_analysis", fallback=False) if "analysis" in config else False

    heartbeat_interval = config.getint("telecontrol", "heartbeat_interval", fallback=30) if "telecontrol" in config else 30
    data_transmission_interval = config.getint("telecontrol", "data_transmission_interval", fallback=300) if "telecontrol" in config else 300
    max_retry_attempts = config.getint("telecontrol", "max_retry_attempts", fallback=3) if "telecontrol" in config else 3

    encryption_enabled = config.getboolean("security", "encryption_enabled", fallback=True) if "security" in config else True
    ssl_verify = config.getboolean("security", "ssl_verify", fallback=True) if "security" in config else True

    state_file = str(Path(config_file).with_name(f"{Path(config_file).stem}_state.json"))

    return ProbeConfiguration(
        probe_id=probe_id,
        api_key=api_key,
        server_url=server_url,
        interface_name=interface_name,
        promiscuous_mode=promiscuous_mode,
        capture_filter=capture_filter,
        max_packet_size=max_packet_size,
        buffer_size=buffer_size,
        enabled_protocols=enabled_protocols,
        sampling_rate=sampling_rate,
        metadata_extraction=metadata_extraction,
        payload_analysis=payload_analysis,
        heartbeat_interval=heartbeat_interval,
        data_transmission_interval=data_transmission_interval,
        max_retry_attempts=max_retry_attempts,
        encryption_enabled=encryption_enabled,
        ssl_verify=ssl_verify,
        state_file=state_file,
    )


def create_default_config(config_file: str):
    """Create a default configuration file."""
    config = configparser.ConfigParser()
    config["main"] = {
        "probe_id": "11111111-1111-1111-1111-111111111111",
        "api_key": "your_api_key_here",
        "server_url": "https://your-server.com",
    }
    config["network"] = {
        "interface_name": "eth0",
        "promiscuous_mode": "true",
        "capture_filter": "",
        "max_packet_size": "1518",
        "buffer_size": "65536",
    }
    config["analysis"] = {
        "enabled_protocols": "Modbus,IEC 104,OPC-UA,EtherNet/IP,BACnet",
        "sampling_rate": "1.0",
        "metadata_extraction": "true",
        "payload_analysis": "false",
    }
    config["telecontrol"] = {
        "heartbeat_interval": "30",
        "data_transmission_interval": "300",
        "max_retry_attempts": "3",
    }
    config["security"] = {"encryption_enabled": "true", "ssl_verify": "true"}

    with open(config_file, "w", encoding="utf-8") as f:
        config.write(f)
    print(f"Configuration file created: {config_file}")
    print("Edit this file with your settings before starting the probe")


def main():
    """Probe CLI entrypoint."""
    from network_probe_client import NetworkProbe  # local import avoids circulars

    parser = argparse.ArgumentParser(description="Network Probe Client for IndustracePRO")
    parser.add_argument("-c", "--config", default="probe.conf", help="Configuration file")
    parser.add_argument("--create-config", action="store_true", help="Create default configuration file")
    parser.add_argument("--interface", help="Network interface to monitor")
    parser.add_argument("--server", help="IndustracePRO server URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--probe-id", help="Unique probe ID")
    args = parser.parse_args()

    if args.create_config:
        create_default_config(args.config)
        return

    if not os.path.exists(args.config):
        print(f"Configuration file {args.config} not found")
        print("Use --create-config to create a default configuration file")
        return

    try:
        config = load_config(args.config)
        if args.interface:
            config.interface_name = args.interface
        if args.server:
            config.server_url = args.server
        if args.api_key:
            config.api_key = args.api_key
        if args.probe_id:
            config.probe_id = args.probe_id

        probe = NetworkProbe(config)
        if config.enabled_protocols:
            probe.add_protocol_filter(config.enabled_protocols)
            logger.info(f"Applied protocol filters: {config.enabled_protocols}")
        probe.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by the user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
