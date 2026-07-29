# Network Probe Native Setup (systemd)

This guide runs the Industrace Network Probe as a non-root service with only the Linux capabilities needed for packet capture (`CAP_NET_RAW`, `CAP_NET_ADMIN`).

## 1) Prerequisites

- Linux host (Debian/Ubuntu tested path)
- Access to the target interface/VLAN (SPAN/mirror/tap as needed)
- Probe created in Industrace UI (you already have `probe_id` and `api_key`)

## 2) Install runtime dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv libpcap-dev
```

## 3) Create probe user and directories

```bash
sudo useradd --system --create-home --home-dir /var/lib/industrace-probe --shell /usr/sbin/nologin industrace-probe
sudo mkdir -p /opt/industrace/probe /opt/industrace/probe/logs /etc/industrace /var/lib/industrace-probe
sudo chown -R industrace-probe:industrace-probe /opt/industrace/probe /var/lib/industrace-probe
```

## 4) Deploy probe code and Python environment

From this repository:

```bash
sudo cp -r . /opt/industrace/probe
cd /opt/industrace/probe
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.probe.txt
```

Use either:

- `ExecStart` with system Python (`/usr/bin/python3`) and requirements installed globally, or
- `ExecStart` with venv Python (`/opt/industrace/probe/.venv/bin/python`) if you prefer isolated deps.

The provided `industrace-network-probe.service.example` uses `/usr/bin/python3` for portability. Adjust it if you choose venv execution.

## 5) Configure the probe

```bash
sudo cp /opt/industrace/probe/probe.conf.example /etc/industrace/probe.conf
sudo nano /etc/industrace/probe.conf
```

At minimum set:

- `probe_id` (UUID)
- `api_key`
- `server_url`
- `interface_name`

Recommended:

- keep `promiscuous_mode = true` when needed for mirrored traffic
- use a restrictive `capture_filter` when possible

## 6) Install and start the systemd unit

```bash
sudo cp /opt/industrace/probe/industrace-network-probe.service.example /etc/systemd/system/industrace-network-probe.service
sudo systemctl daemon-reload
sudo systemctl enable --now industrace-network-probe
sudo systemctl status industrace-network-probe
```

Logs:

```bash
journalctl -u industrace-network-probe -f
```

## 7) Security notes

- Prefer systemd service capabilities over `setcap` on `/usr/bin/python3`; setting capabilities on the Python binary grants those caps to all Python programs started from that binary.
- Keep `CapabilityBoundingSet` and `AmbientCapabilities` limited to `CAP_NET_RAW CAP_NET_ADMIN`.
- Run the service as dedicated non-login user (`industrace-probe`).

## 8) Troubleshooting

### Permission denied while sniffing

- Verify interface name with `ip link show`.
- Verify service capabilities:

```bash
systemctl show industrace-network-probe -p AmbientCapabilities -p CapabilityBoundingSet
```

- Ensure traffic visibility from network placement (SPAN/mirror/tap).

### Probe inactive in UI

- Check `probe_id`, `api_key`, `server_url` in `/etc/industrace/probe.conf`.
- Verify connectivity to server:

```bash
curl -v https://your-server.example.com/api/health
```

### Restart after config changes

```bash
sudo systemctl restart industrace-network-probe
sudo systemctl status industrace-network-probe
```
