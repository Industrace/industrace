# Network Probe — complete guide

Distributed passive network discovery for **Industrace 2.1+**. Probes observe industrial traffic on a network segment and report metadata (devices, protocols, connections) to the Industrace backend — without storing full packet payloads.

**Status:** MVP shipped in v2.1.0. This document is the single reference for operations, architecture, API, security, and residual backlog.

---

## 1. Overview

### What it does

- **Passive capture** on a network interface (SPAN/mirror/tap placement recommended)
- **Protocol heuristics** for common industrial protocols (Modbus, OPC-UA, EtherNet/IP, etc.)
- **Heartbeat** — probe health and system/network metrics
- **Data transmission** — snapshot of recently discovered devices and connection counts
- **Discovered devices** — list, match against existing assets, onboard as new assets
- **Runtime configuration** pushed from the UI/API without redeploying the client

### Prerequisites

- Industrace **2.1+** with migrations applied (`make migrate`)
- RBAC permission **`network_probes`** on user roles (`make update-roles`)
- Probe host with access to the target interface (`CAP_NET_RAW` / `CAP_NET_ADMIN` or Docker `--privileged`)
- Python 3.8+ or Docker (recommended for production)

### Key files

| File | Purpose |
|------|---------|
| `network_probe_client.py` | Runtime orchestrator (`NetworkProbe`) |
| `probe_cli.py` | Config parsing/generation and CLI entrypoint |
| `probe_runtime_workers.py` | Heartbeat, transmission, remote config workers |
| `probe_packet_processing.py` | Packet sampling and discovery state updates |
| `probe_protocol_analyzer.py` | Industrial protocol heuristics |
| `probe_transmission.py` | Discovery snapshot and payload builders |
| `probe_state_store.py` | Local state persistence (devices, pending delivery) |
| `probe_health.py` / `probe_metrics.py` | Health counters and host metrics |
| `probe_logging.py` | Rotating file + stdout logging setup |
| `retry_policy.py` | Exponential backoff for worker retries |
| `README.md` | Module map and contributor guide |
| `probe.conf` / `probe.conf.example` | Configuration |
| `Dockerfile.probe` | Container image (copies all `*.py` modules) |
| `docker-compose.probes.yml` | Multi-probe compose example |
| `requirements.probe.txt` | Python dependencies |
| `tests/` | Client unit tests (`pytest`) |

---

## 2. Quick start

### Server (Industrace)

1. Upgrade to 2.1+ and run `make migrate`.
2. Run `make update-roles` so roles include `network_probes`.
3. UI: **Network Probes** → create probe → save **API key** immediately (shown once).
4. Optional server env vars (see [Configuration](#3-configuration)).

### Client

1. Copy `probe.conf.example` → `probe.conf` and set `server_url`, `probe_id`, `api_key`.
2. Build and run:

```bash
docker build -f Dockerfile.probe -t industrace-probe .

docker run -d \
  --name network-probe \
  --privileged \
  --network host \
  -v $(pwd)/probe.conf:/app/probe.conf:ro \
  -v $(pwd)/logs:/logs \
  industrace-probe
```

3. Confirm **active** status and recent heartbeat in the UI.
4. Check **Discovered devices** after the first data transmission (default ~5 minutes).

### Native run

```bash
# Dependencies (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y python3 python3-pip tcpdump
pip3 install -r requirements.probe.txt

python3 network_probe_client.py --create-config
# Edit probe.conf, then:
python3 network_probe_client.py -c probe.conf
```

---

## 3. Configuration

### Client (`probe.conf`)

```ini
[main]
probe_id = 11111111-1111-1111-1111-111111111111
api_key = your_api_key_here
server_url = https://your-industrace.example.com

[network]
interface_name = eth0
promiscuous_mode = true
capture_filter =
max_packet_size = 1518
buffer_size = 65536

[analysis]
enabled_protocols = Modbus,OPC-UA
sampling_rate = 1.0
metadata_extraction = true
payload_analysis = false

[telecontrol]
heartbeat_interval = 30
data_transmission_interval = 300
max_retry_attempts = 3

[security]
encryption_enabled = false
ssl_verify = true
```

| Setting | Notes |
|---------|-------|
| `probe_id` | **Required UUID** in heartbeat/transmission payloads and config endpoint path; API key still authenticates the probe |
| `max_packet_size` | Packets larger than this (bytes, full frame) are ignored before analysis |
| `buffer_size` | Max total bytes for the local `data_buffer` when `payload_analysis = true` (not sent to backend) |
| `sampling_rate` | `0.1` = 10% of packets; lowers CPU load |
| `payload_analysis` | Off by default; buffers compressed payloads **locally only** — not included in data transmission (metadata-only MVP) |
| `data_transmission_interval` | 60–3600 seconds (enforced in UI and backend) |
| `encryption_enabled` | **Legacy flag, ignored by client.** Transport security is TLS/HTTPS only |
| `ssl_verify` | Set `true` in production |

**BPF filter examples:**

```text
tcp port 502 or tcp port 4840    # Modbus + OPC-UA
net 192.168.1.0/24               # Subnet only
not host 127.0.0.1
```

### Server (environment)

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROBE_HEARTBEAT_STALE_SECONDS` | `300` | Mark probe `inactive` if no heartbeat within this window |
| `PROBE_RETENTION_DAYS` | `90` | Purge old `probe_heartbeats` and `probe_data_transmissions` |
| `PROBE_RATE_LIMIT_HEARTBEAT` | `120/minute` | Rate limit per API key on heartbeat |
| `PROBE_RATE_LIMIT_DATA` | `30/hour` | Rate limit on data transmission |
| `PROBE_RATE_LIMIT_CONFIG` | `60/hour` | Rate limit on configuration poll |

See also [CONFIGURATION.md](../docs/CONFIGURATION.md) and `.env.example`.

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Industrace Server (2.1+)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ API Routers  │  │ PostgreSQL   │  │ Vue UI                 │ │
│  │ network_     │  │ network_     │  │ NetworkProbes.vue      │ │
│  │ probes,      │  │ probes,      │  │ DiscoveredDevices.vue  │ │
│  │ discovered_  │  │ discovered_  │  │                        │ │
│  │ devices      │  │ devices, …   │  │                        │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────────────────┘ │
│         │                 │                                      │
│  ┌──────▼─────────────────▼──────────────────────────────────┐  │
│  │ NetworkProbeService, probe_auth, mac_utils, rate_limiter   │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────┘
                                │ HTTPS + X-API-Key
┌───────────────────────────────▼───────────────────────────────────┐
│                     network_probe_client.py                        │
│              Orchestrator: threads, locks, HTTP session            │
├───────────────────────────────┬───────────────────────────────────┤
│ probe_packet_processing.py    │ probe_runtime_workers.py          │
│ probe_protocol_analyzer.py    │ probe_transmission.py             │
│ probe_state_store.py          │ probe_remote_config.py            │
└───────────────────────────────┴───────────────────────────────────┘
```

See [`README.md`](README.md) for the full module map and extension points.

### Backend components

| Component | Location | Role |
|-----------|----------|------|
| `NetworkProbe` model | `backend/app/models/network_probe.py` | Probe config, status, API key |
| `DiscoveredDevice` model | `backend/app/models/discovered_device.py` | Devices seen by probes |
| `NetworkProbeService` | `backend/app/services/network_probe_service.py` | CRUD, heartbeat, transmission ingest, stale status, retention |
| `probe_auth` | `backend/app/services/probe_auth.py` | Validates `X-API-Key` (query param deprecated fallback) |
| `mac_utils` | `backend/app/services/mac_utils.py` | MAC normalization and dedup |
| Matching | `backend/app/routers/discovered_devices.py` | Inline hash-map match on MAC/IP vs asset interfaces (no separate `DeviceMatchingService`) |

### Client components

| Component | Role |
|-----------|------|
| `NetworkProbe` (`network_probe_client.py`) | Lifecycle coordinator; sniff / heartbeat / transmission / config threads |
| `ProbePacketProcessingMixin` | Sampling, device/connection updates, optional payload buffer |
| `ProbeRuntimeWorkersMixin` | Heartbeat, data transmission, remote configuration sync |
| `ProtocolAnalyzer` | Industrial protocol detection by port and payload heuristics |
| `probe_state_store` | Best-effort persistence of devices, connections, and pending delivery sets |
| `probe_logging` | Rotating log files (`network_probe.log`, 10 MB × 5 backups) |
| `NetworkDevice` / `NetworkConnection` | In-memory discovery state (`probe_models.py`) |

### Workflows

**Probe registration:** Admin creates probe via UI → server generates API key → client configured with key → first heartbeat sets status `active`.

**Data flow:** Client captures packets → builds device/connection metadata → `POST /data-transmission` → server upserts `discovered_devices` (unique on `tenant_id`, `probe_id`, `mac_address`) → UI lists devices with `possible_matches` computed on read.

**Onboard:** User triggers `POST /discovered-devices/{id}/onboard` → creates asset + interface from discovery data → device status `imported`.

**De-authorize:** Admin `POST /network-probes/{id}/deauthorize` → client receives persistent 401 → stops after two consecutive auth failures.

---

## 5. API contract

Base paths are mounted under `/api` by the FastAPI app. User endpoints require JWT; probe client endpoints require **`X-API-Key`** header.

### Probe management (JWT, permission `network_probes`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/network-probes` | Create probe (returns API key once) |
| `GET` | `/network-probes` | List tenant probes |
| `GET` | `/network-probes/overview` | Aggregated overview |
| `GET` | `/network-probes/{probe_id}` | Probe details |
| `PUT` | `/network-probes/{probe_id}` | Update probe configuration |
| `DELETE` | `/network-probes/{probe_id}` | Delete probe |
| `GET` | `/network-probes/{probe_id}/status` | Probe status summary |
| `POST` | `/network-probes/{probe_id}/deauthorize` | Invalidate API key |

### Probe client (X-API-Key)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/network-probes/heartbeat` | Register heartbeat and metrics |
| `POST` | `/network-probes/data-transmission` | Submit discovery snapshot |
| `GET` | `/network-probes/configuration/{probe_id}` | Poll runtime configuration |

### Discovered devices (JWT)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/discovered-devices` | List with filters; enriches `possible_matches` / `best_match_*` |
| `GET` | `/discovered-devices/{device_id}` | Device details |
| `PUT` | `/discovered-devices/{device_id}` | Update status, notes, `matched_asset_id` (assign/ignore) |
| `POST` | `/discovered-devices/{device_id}/onboard` | Create asset from discovery |

**Not implemented** (do not rely on these): `GET /network-probes/{probe_id}/statistics`, `GET /discovered-devices/{device_id}/matches`.

See [API.md](../docs/API.md) for general REST conventions.

---

## 6. Security

| Topic | Implementation |
|-------|----------------|
| Authentication | `X-API-Key` header on probe endpoints; query `api_key` deprecated |
| Transport | TLS/HTTPS; `ssl_verify` on client; no application-layer payload encryption |
| API key storage | Generated with `secrets.token_urlsafe(32)`; shown once at creation |
| Rate limiting | Per-key limits on heartbeat, data, configuration (`rate_limiter.py`) |
| MAC dedup | Normalized MAC + unique index `(tenant_id, probe_id, mac_address)` |
| Logging | `log_sanitizer.py` redacts API keys from server logs |
| De-authorize | Revokes key; client stops on repeated 401 |
| Retention | Automatic purge of old heartbeat/transmission rows (`PROBE_RETENTION_DAYS`) |
| RBAC | `network_probes` permission gates UI and admin API |

**Best practices:**

1. Use TLS (`ssl_verify = true`) in production.
2. Rotate API keys after de-authorize or compromise.
3. Do not enable `payload_analysis` without authorization.
4. Restrict outbound firewall to HTTPS to the Industrace server only.
5. Use `--privileged` or capabilities only when required for capture.

```bash
# Optional: capabilities instead of full privileged (native)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

---

## 7. Implementation status (MVP)

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | Monorepo `probe/`, models, migrations, RBAC | Done |
| 1 | Backend routers, service, auth, MAC dedup, rate limits | Done |
| 2 | Frontend `NetworkProbes.vue`, `DiscoveredDevices.vue`, i18n en/it | Done |
| 3 | Client hardening (header auth, TLS-only, 429 backoff, 401 stop) | Done |
| 4 | Tests (`test_probe_auth`, `test_network_probe_service`, …), docs, retention | Done |

### Completed checklist (P0–P2)

- API key via `X-API-Key`; client header-only
- MAC normalization and unique constraint; idempotent upsert
- Rate limiting and 429 retry/backoff on client
- Stale probe detection (`PROBE_HEARTBEAT_STALE_SECONDS`)
- De-authorize with persistent 401 client stop
- FE/BE alignment on `data_transmission_interval` (60–3600s)
- Matching optimization (hash map MAC/IP in list endpoint)
- Telemetry retention job
- Backend probe tests (11 tests in `test_network_probe_service.py`)

---

## 8. Residual backlog

Post-MVP improvements — not blocking release 2.1:

| Item | Description |
|------|-------------|
| Payload buffer transmission | `data_buffer` (when `payload_analysis = true`) is kept on-probe for local diagnostics only; not included in HTTP data transmission |
| Bulk ingest/upsert | Batch DB writes on data transmission to reduce roundtrips |
| Discovered devices tests | Router tests for update status, assign, onboard |
| Frontend smoke tests | `NetworkProbes.vue`, `DiscoveredDevices.vue` |

---

## 9. Long-term roadmap

| Idea | Status / notes |
|------|----------------|
| Data retention policy | **Implemented** (`PROBE_RETENTION_DAYS`, purge job) |
| Circuit breaker + retry | Partial: 429 backoff and auth-failure stop on client; full circuit breaker TBD |
| GDPR / DPIA | Documentation and legal review TBD |
| HSM / Vault for API keys | Encryption at rest or external secret store TBD |
| TimescaleDB for telemetry | When heartbeat volume justifies time-series storage |
| HA (LB + DB replica) | Infrastructure / ops when SLA requires |
| eBPF / AF_PACKET capture | High-throughput alternative to Scapy; large effort |

---

## 10. Operations reference

### Docker Compose

```bash
docker compose -f docker-compose.probes.yml up -d
docker compose -f docker-compose.probes.yml logs -f
```

### Monitoring

- **UI:** probe status, last heartbeat, last data received, discovered devices count
- **Logs:**

```bash
tail -f network_probe.log
docker logs -f network-probe
```

### Supported protocols (heuristic)

Modbus (502), IEC 60870-5-104 / IEC 104 (2404), OPC-UA (4840), EtherNet/IP (44818), BACnet (47808), DNP3 (20000), KNX (3671), MQTT (8883), HTTP/HTTPS (80/443). Identification is metadata-based (port and, for IEC 104, APCI start byte `0x68`); not guaranteed.

### Limitations

- Visibility depends on L2 placement; switched networks need mirror port or tap.
- Protocol/vendor detection is heuristic.
- Local client state is best-effort after restart — not a full database.
- Scapy-based capture may not scale to very high throughput without sampling.

---

## 11. Troubleshooting

### Probe shows `inactive` in UI

**Cause:** No heartbeat within `PROBE_HEARTBEAT_STALE_SECONDS` (default 300s).

**Checks:**

- Container/process running: `docker logs network-probe`
- `probe.conf`: correct `server_url`, `probe_id`, `api_key`
- Network path: firewall, TLS, DNS from probe host to server
- API key sent via `X-API-Key` header

### Client stops after de-authorize

**Expected (v2.1+):** two consecutive HTTP 401 responses stop the client. Re-create or re-authorize the probe, update `api_key` in `probe.conf`, restart.

### Discovered devices not appearing

- Probe status must be `active` with recent `last_data_received`
- Default transmission interval is 300s — wait for next cycle
- `data_transmission_interval` must be between 60 and 3600 seconds
- `probe_id` must be a valid UUID string
- Check server logs for HTTP 429 (rate limiting)

### Permission denied on interface

```bash
ip link show
sudo ip link set eth0 promisc on
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

### Server connectivity

```bash
curl -v https://your-server.com/api/health
openssl s_client -connect your-server.com:443
```

### Low performance

- Lower `sampling_rate` (e.g. `0.1`)
- Set `payload_analysis = false` (local payload buffer is not transmitted; it only affects on-probe memory use)
- Increase `buffer_size` when `payload_analysis = true`
- Tighten BPF `capture_filter`

### Interface not found

List interfaces with `ip link show` (Linux) or `ifconfig` (macOS). On macOS use patterns from `probe-test-macos.conf` in the repo.

For general Industrace server issues see [troubleshooting.md](../docs/troubleshooting.md).

---

## Related documentation

- [INSTALLATION.md](../docs/INSTALLATION.md) — server install
- [MIGRATION.md](../docs/MIGRATION.md) — upgrade to 2.1
- [release-notes.md](../docs/release-notes.md) — v2.1.0 Network Probes feature summary

---

*Document version: 2.1 — consolidated from former OPERATIONS.md, DESIGN.md, and implementation plan. Last updated: May 2026.*
