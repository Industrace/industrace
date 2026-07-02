"""Packet processing mixin for discovery updates and payload buffering."""

from __future__ import annotations

import base64
import gzip
import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from scapy.all import Ether, ICMP, IP, Raw, TCP, UDP

from probe_helpers import mac_from_ip
from probe_models import NetworkConnection, NetworkDevice
from probe_protocol_analyzer import ProtocolAnalyzer

logger = logging.getLogger(__name__)


class ProbePacketProcessingMixin:
    """Packet pipeline extracted from NetworkProbe to keep orchestration lean."""

    def _packet_handler(self, packet):
        """Handle each captured packet."""
        try:
            self.health.record_packet_seen()
            if self.stats["packets_captured"] and self.stats["packets_captured"] % 10000 == 0:
                logger.info(f"Processed packets: {self.stats['packets_captured']}")

            if self._sampling_rate < 1.0:
                try:
                    src_mac = packet[Ether].src if Ether in packet else ""
                    dst_mac = packet[Ether].dst if Ether in packet else ""
                    src_ip = packet[IP].src if IP in packet else ""
                    dst_ip = packet[IP].dst if IP in packet else ""

                    if TCP in packet:
                        l4_proto = "TCP"
                        sport = packet[TCP].sport
                        dport = packet[TCP].dport
                    elif UDP in packet:
                        l4_proto = "UDP"
                        sport = packet[UDP].sport
                        dport = packet[UDP].dport
                    else:
                        l4_proto = "OTHER"
                        sport = ""
                        dport = ""

                    ip_proto = packet[IP].proto if IP in packet else ""
                    pkt_len = len(packet)
                    sample_key = (
                        f"{src_mac}|{dst_mac}|{src_ip}|{dst_ip}|{l4_proto}|{ip_proto}|{sport}|{dport}|{pkt_len}"
                    )

                    digest = hashlib.md5(sample_key.encode("utf-8")).digest()
                    value = int.from_bytes(digest[:4], "big")

                    buckets = 10000
                    threshold = int(self._sampling_rate * buckets)
                    if (value % buckets) >= threshold:
                        return
                except Exception:
                    pass

            bytes_delta = len(packet[IP]) if IP in packet else 0
            self._stats_batch_packets += 1
            self._stats_batch_bytes += bytes_delta

            now_ts = time.time()
            if (
                self._stats_batch_packets >= self._stats_flush_batch_size
                or (now_ts - self._last_stats_flush_ts) >= self._stats_flush_max_seconds
            ):
                with self.stats_lock:
                    self.stats["packets_captured"] += self._stats_batch_packets
                    self.stats["bytes_processed"] += self._stats_batch_bytes
                self._stats_batch_packets = 0
                self._stats_batch_bytes = 0
                self._last_stats_flush_ts = now_ts

            now_sec = int(time.time())
            with self.rate_lock:
                if not self._traffic_buckets or self._traffic_buckets[-1][0] != now_sec:
                    self._traffic_buckets.append([now_sec, 0, 0])
                self._traffic_buckets[-1][1] += 1
                self._traffic_buckets[-1][2] += bytes_delta

                cutoff = now_sec - self._rate_window_seconds + 1
                while self._traffic_buckets and self._traffic_buckets[0][0] < cutoff:
                    self._traffic_buckets.popleft()

            if self.config.metadata_extraction:
                analysis = ProtocolAnalyzer.analyze_packet(packet)
                self._process_packet_analysis(packet, analysis)

            if self.config.payload_analysis and Raw in packet:
                self._process_payload(packet)

            self._maybe_prune_connections()

        except Exception as e:
            logger.debug(f"Error handling packet: {e}")

    def _process_packet_analysis(self, packet, analysis: Dict[str, Any]):
        """Process packet analysis results."""
        try:
            src_mac = None
            dst_mac = None
            if Ether in packet:
                src_mac = packet[Ether].src
                dst_mac = packet[Ether].dst
            elif IP in packet:
                # macOS loopback often delivers IP frames without an Ethernet header.
                src_mac = mac_from_ip(packet[IP].src)
                dst_mac = mac_from_ip(packet[IP].dst)

            if not src_mac or not dst_mac:
                return

            src_ip = packet[IP].src if IP in packet else None
            dst_ip = packet[IP].dst if IP in packet else None
            self._update_device(src_mac, src_ip, packet, analysis)
            self._update_device(dst_mac, dst_ip, packet, analysis)
            self._update_connection(src_mac, dst_mac, packet, analysis)
        except Exception as e:
            logger.debug(f"Error processing packet analysis: {e}")

    def _update_device(self, mac: str, ip: Optional[str], packet, analysis: Dict[str, Any]):
        """Update information for a device."""
        wake_transmission = False
        with self.data_lock:
            if mac not in self.devices:
                logger.info(f"New device discovered: mac={mac} ip={ip}")
                self.devices[mac] = NetworkDevice(
                    mac_address=mac,
                    ip_addresses=[],
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    protocols=[],
                    packet_count=0,
                    byte_count=0,
                )
                with self.stats_lock:
                    self.stats["devices_discovered"] += 1

            device = self.devices[mac]
            device.last_seen = datetime.now()
            device.packet_count += 1

            if ip and ip not in device.ip_addresses:
                device.ip_addresses.append(ip)

            if IP in packet:
                device.byte_count += len(packet[IP])

            for protocol in analysis.get("protocols", []):
                if protocol not in device.protocols:
                    device.protocols.append(protocol)

            if "device_vendor" in analysis:
                device.vendor = analysis["device_vendor"]

            if mac not in self._pending_device_macs:
                wake_transmission = True
            self._pending_device_macs.add(mac)

        if wake_transmission:
            self._signal_pending_delivery()

    def _update_connection(self, src_mac: str, dst_mac: str, packet, analysis: Dict[str, Any]):
        """Update information for a connection (directional flow key)."""
        with self.data_lock:
            if TCP in packet:
                proto = "TCP"
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            elif UDP in packet:
                proto = "UDP"
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
            elif ICMP in packet:
                proto = "ICMP"
                src_port = None
                dst_port = None
            else:
                proto = "OTHER"
                src_port = None
                dst_port = None

            conn_key = (
                f"{src_mac}->{dst_mac}|{proto}|{src_port if src_port is not None else ''}|"
                f"{dst_port if dst_port is not None else ''}"
            )

            if conn_key not in self.connections:
                self.connections[conn_key] = NetworkConnection(
                    source_mac=src_mac,
                    dest_mac=dst_mac,
                    source_ip=None,
                    dest_ip=None,
                    source_port=src_port,
                    dest_port=dst_port,
                    protocol=proto,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    packet_count=0,
                    byte_count=0,
                )
                with self.stats_lock:
                    self.stats["connections_detected"] += 1
                self._pending_new_connections += 1

            conn = self.connections[conn_key]
            conn.last_seen = datetime.now()
            conn.packet_count += 1
            conn.protocol = proto
            conn.source_port = src_port
            conn.dest_port = dst_port

            if IP in packet:
                src_device = self.devices.get(src_mac)
                dst_device = self.devices.get(dst_mac)
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst

                if src_device and src_ip in (src_device.ip_addresses or []):
                    conn.source_ip = src_ip
                if dst_device and dst_ip in (dst_device.ip_addresses or []):
                    conn.dest_ip = dst_ip

                conn.byte_count += len(packet[IP])

    def _process_payload(self, packet):
        """Process and buffer payload when enabled."""
        try:
            if Raw in packet:
                payload = bytes(packet[Raw])
                compressed = gzip.compress(payload)
                encoded = base64.b64encode(compressed).decode("utf-8")

                payload_info = {
                    "timestamp": datetime.now().isoformat(),
                    "src_mac": packet[Ether].src if Ether in packet else None,
                    "dst_mac": packet[Ether].dst if Ether in packet else None,
                    "payload": encoded,
                    "original_size": len(payload),
                    "compressed_size": len(compressed),
                }

                with self.data_buffer_lock:
                    if (
                        self.data_buffer.maxlen is not None
                        and len(self.data_buffer) >= self.data_buffer.maxlen
                    ):
                        self._payload_buffer_dropped_count += 1
                        self.health.record_warning()
                    self.data_buffer.append(payload_info)
        except Exception as e:
            logger.debug(f"Error processing payload: {e}")
