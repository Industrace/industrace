#!/usr/bin/env python3
"""Generate synthetic industrial-looking traffic for local probe testing."""

from __future__ import annotations

import argparse
import random
import sys
import time

from scapy.all import ARP, Ether, IP, Raw, TCP, send, sendp


def _mac(seed: int) -> str:
    return f"02:00:00:00:00:{seed:02x}"


def _modbus_frame() -> bytes:
    return b"\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x0a"


def _opcua_hello() -> bytes:
    return b"HELO" + b"\x00" * 24


def _iec104_frame() -> bytes:
    apdu_length = 10
    return bytes([0x68, apdu_length]) + b"\x00" * (apdu_length + 2)


def build_packets(args) -> list:
    packets = []
    src_plc = _mac(0x10)
    dst_hmi = _mac(0x20)
    src_ip = "127.0.0.1"
    dst_ip = "127.0.0.2"

    for i in range(args.count):
        sport = 40000 + (i % 1000)
        packets.append(
            Ether(src=src_plc, dst=dst_hmi)
            / IP(src=src_ip, dst=dst_ip)
            / TCP(sport=sport, dport=502)
            / Raw(load=_modbus_frame())
        )
        packets.append(
            Ether(src=dst_hmi, dst=src_plc)
            / IP(src=dst_ip, dst=src_ip)
            / TCP(sport=4840, dport=40000 + i)
            / Raw(load=_opcua_hello())
        )
        packets.append(
            Ether(src=_mac(0x30 + (i % 5)), dst="ff:ff:ff:ff:ff:ff")
            / IP(src=f"10.0.0.{10 + (i % 40)}", dst=f"10.0.0.{50 + (i % 40)}")
            / TCP(sport=2404, dport=2404)
            / Raw(load=_iec104_frame())
        )
        if not args.loopback_l3:
            packets.append(
                Ether(src=_mac(0x40 + (i % 5)), dst=dst_hmi)
                / ARP(op=1, psrc=f"192.168.1.{100 + (i % 50)}", pdst="192.168.1.1", hwsrc=_mac(0x40 + (i % 5)))
            )

    if args.shuffle:
        random.shuffle(packets)
    return packets


def _send_packet(pkt, iface: str, loopback_l3: bool) -> None:
    if loopback_l3 and IP in pkt:
        send(pkt[IP], iface=iface, verbose=False)
        return
    sendp(pkt, iface=iface, verbose=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate test traffic for the network probe")
    default_iface = "lo0" if sys.platform == "darwin" else "lo"
    parser.add_argument("--interface", default=default_iface, help="Interface (lo0 on macOS, en0 for Wi-Fi)")
    parser.add_argument("--count", type=int, default=20, help="Iterations per traffic profile")
    parser.add_argument("--interval", type=float, default=0.2, help="Seconds between packet bursts")
    parser.add_argument("--shuffle", action="store_true", help="Randomize packet order")
    parser.add_argument("--loop", action="store_true", help="Keep sending until Ctrl+C")
    args = parser.parse_args()
    args.loopback_l3 = sys.platform == "darwin" and args.interface.startswith("lo")

    packets = build_packets(args)
    mode = "L3/IP (loopback)" if args.loopback_l3 else "L2/Ethernet"
    print(
        f"Sending {len(packets)} packets on {args.interface} via {mode} "
        f"(Modbus:502, OPC-UA HELO:4840, IEC104:2404)"
    )
    print("Tip: probe and generator must use the SAME interface (lo0 on macOS).")

    try:
        while True:
            for pkt in packets:
                _send_packet(pkt, args.interface, args.loopback_l3)
                if args.interval > 0:
                    time.sleep(args.interval)
            if not args.loop:
                break
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
