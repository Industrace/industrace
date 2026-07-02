"""Protocol analysis utilities for industrial traffic metadata extraction."""

from __future__ import annotations

import logging
import struct
from typing import Any, Dict

from scapy.all import ARP, Ether, ICMP, IP, Raw, TCP, UDP

logger = logging.getLogger(__name__)


class ProtocolAnalyzer:
    """Industrial protocol analyzer."""

    INDUSTRIAL_PORTS = {
        502: "Modbus",
        2404: "IEC 104",
        4840: "OPC-UA",
        44818: "EtherNet/IP",
        47808: "BACnet",
        20000: "DNP3",
        3671: "KNX",
        1883: "MQTT",
        8883: "MQTT",
        80: "HTTP",
        443: "HTTPS",
        21: "FTP",
        22: "SSH",
        23: "Telnet",
    }

    DEVICE_SIGNATURES = {
        "siemens": [b"Siemens", b"S7", b"Simatic"],
        "rockwell": [b"Rockwell", b"Allen-Bradley", b"ControlLogix"],
        "schneider": [b"Schneider", b"Modicon", b"Quantum"],
        "abb": [b"ABB", b"800xA", b"Advant"],
        "honeywell": [b"Honeywell", b"Experion", b"PKS"],
        "emerson": [b"Emerson", b"DeltaV", b"PlantWeb"],
    }

    @staticmethod
    def _normalize_protocol_key(protocol: str) -> str:
        return protocol.upper().replace(" ", "").replace("-", "").replace("_", "")

    @staticmethod
    def _mark_industrial_protocol(analysis: Dict[str, Any], port: int) -> None:
        if port not in ProtocolAnalyzer.INDUSTRIAL_PORTS:
            return
        proto_name = ProtocolAnalyzer.INDUSTRIAL_PORTS[port]
        analysis["industrial_protocol"] = True
        analysis["industrial_info"] = {"port": port, "protocol": proto_name}
        if proto_name not in analysis["protocols"]:
            analysis["protocols"].append(proto_name)

    @staticmethod
    def analyze_packet(packet) -> Dict[str, Any]:
        """Analyze a packet to extract protocol information."""
        analysis = {"protocols": [], "device_info": {}, "industrial_protocol": False}
        try:
            if Ether in packet:
                analysis["protocols"].append("Ethernet")
                if ARP in packet:
                    analysis["protocols"].append("ARP")
                    analysis["arp_info"] = {
                        "op": packet[ARP].op,
                        "src_ip": packet[ARP].psrc,
                        "dst_ip": packet[ARP].pdst,
                    }

            if IP in packet:
                analysis["protocols"].append("IP")
                analysis["ip_info"] = {
                    "src_ip": packet[IP].src,
                    "dst_ip": packet[IP].dst,
                    "ttl": packet[IP].ttl,
                    "protocol": packet[IP].proto,
                }

                if TCP in packet:
                    analysis["protocols"].append("TCP")
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                    if src_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, src_port)
                    elif dst_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, dst_port)
                    if Raw in packet:
                        analysis.update(ProtocolAnalyzer._analyze_payload(bytes(packet[Raw])))
                elif UDP in packet:
                    analysis["protocols"].append("UDP")
                    src_port = packet[UDP].sport
                    dst_port = packet[UDP].dport
                    if src_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, src_port)
                    elif dst_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, dst_port)
                elif ICMP in packet:
                    analysis["protocols"].append("ICMP")
                    analysis["icmp_info"] = {"type": packet[ICMP].type, "code": packet[ICMP].code}
        except Exception as e:
            logger.debug(f"Error analyzing packet: {e}")
        return analysis

    @staticmethod
    def _analyze_payload(payload: bytes) -> Dict[str, Any]:
        """Analyze payload to identify industrial protocols."""
        analysis: Dict[str, Any] = {}
        try:
            if len(payload) >= 8:
                function_code = payload[7]
                transaction_id = struct.unpack(">H", payload[0:2])[0]
                if function_code in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x0F, 0x10]:
                    analysis["modbus_info"] = {
                        "function_code": function_code,
                        "transaction_id": transaction_id,
                    }

            if len(payload) >= 4 and payload[0:4] == b"HELO":
                analysis["opcua_info"] = {"message_type": "Hello"}

            if len(payload) >= 24 and payload[0:2] == b"\x65\x00":
                analysis["enip_info"] = {"command": struct.unpack(">H", payload[16:18])[0]}

            if len(payload) >= 6 and payload[0] == 0x68:
                apdu_length = payload[1]
                if 4 <= apdu_length <= 253 and len(payload) >= apdu_length + 2:
                    analysis["iec104_info"] = {"apdu_length": apdu_length}
                    analysis["industrial_protocol"] = True
                    if "IEC 104" not in analysis.get("protocols", []):
                        analysis.setdefault("protocols", []).append("IEC 104")

            for vendor, signatures in ProtocolAnalyzer.DEVICE_SIGNATURES.items():
                for signature in signatures:
                    if signature in payload:
                        analysis["device_vendor"] = vendor
                        break
                if "device_vendor" in analysis:
                    break
        except Exception as e:
            logger.debug(f"Error analyzing payload: {e}")
        return analysis
