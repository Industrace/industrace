# Probe Module Guide

This folder contains the network probe client split into small, focused modules.

## Why this structure

The probe started as a single large file. It is now organized by responsibility to make:
- reviews faster,
- bugs easier to isolate,
- features safer to evolve.

The goal is simple: each module does one thing well.

## Module map

- `network_probe_client.py`
  - Runtime coordinator (`NetworkProbe`)
  - Thread lifecycle, shared state, HTTP session, orchestration glue
- `probe_runtime_workers.py`
  - Heartbeat/transmission/config-sync workers
  - Retry pacing and HTTP loop behavior
- `probe_packet_processing.py`
  - Packet sampling pipeline
  - Device/connection updates
  - Optional local payload buffering (`payload_analysis`; not transmitted to backend)
- `probe_protocol_analyzer.py`
  - Protocol heuristics (ports + payload signatures)
- `probe_transmission.py`
  - Discovery snapshot builders
  - Transmission payload serialization
- `probe_state_store.py`
  - Load/save local probe state
- `probe_metrics.py`
  - System and network metrics calculators
- `probe_remote_config.py`
  - Runtime-safe remote configuration application logic
- `probe_models.py`
  - Core dataclasses (`ProbeConfiguration`, `NetworkDevice`, `NetworkConnection`)
- `probe_helpers.py`
  - Small utilities (safe error messages, datetime parsing, capture-filter merge)
- `probe_filtering.py`
  - Protocol-name to BPF filter mapping
- `probe_health.py`
  - Runtime health counters and heartbeat status snapshots
- `probe_logging.py`
  - Rotating file + stdout logging setup
- `retry_policy.py`
  - Backoff helper utilities
- `probe_cli.py`
  - Config parsing/generation and CLI entrypoint

## Data flow (high level)

1. Sniff packet (`scapy`)  
2. Sampling/filtering (`probe_packet_processing.py`)  
3. Protocol analysis (`probe_protocol_analyzer.py`)  
4. Update in-memory discovery state (`devices`, `connections`)  
5. Workers build snapshot (`probe_transmission.py`)  
6. Send heartbeat/data to backend  
7. Persist best-effort local state (`probe_state_store.py`)

## Where to change things

- New protocol heuristic:
  - `probe_protocol_analyzer.py`
- New telemetry field in heartbeat:
  - metrics in `probe_metrics.py`
  - worker send path in `probe_runtime_workers.py`
- New discovery payload field:
  - snapshot/payload in `probe_transmission.py`
  - backend schema/ingest accordingly
- New runtime config key:
  - `probe_remote_config.py`
  - backend config schema and docs
- Changes to thread behavior:
  - `probe_runtime_workers.py`
  - keep `NetworkProbe` in `network_probe_client.py` as coordinator

## Guardrails for contributors

- Prefer adding a new small module over growing `network_probe_client.py`.
- Keep `NetworkProbe` focused on orchestration, not detailed business logic.
- Preserve backward compatibility of public entrypoints (`main`, config loading wrappers).
- Add comments only where behavior is non-obvious (concurrency, retries, data consistency).

## Testing quickstart

Unit tests live in `tests/` and do not require live packet capture. A lightweight Scapy stub is installed by `tests/conftest.py` so pure logic tests run without native Scapy.

```bash
cd probe
pip install -r requirements.probe.txt pytest
python -m pytest tests/ -q
```

Docker packaging smoke check:

```bash
docker build -f Dockerfile.probe -t industrace-probe .
docker run --rm industrace-probe python -c "import network_probe_client; print('ok')"
```

# Network Probe

Distributed passive network discovery for **Industrace 2.1+**. Probes observe industrial traffic on a network segment and report metadata (devices, protocols, connections) to the Industrace backend — without storing full packet payloads.

## Documentation

**[NETWORK_PROBE.md](NETWORK_PROBE.md)** — complete guide: quick start, configuration, architecture, API, security, troubleshooting, and backlog.

## Quick start

1. In Industrace UI: **Network Probes** → create probe → copy **API key** (shown once).
2. Copy `probe.conf.example` → `probe.conf` and set `server_url`, `probe_id`, `api_key`.
3. Run:

```bash
docker build -f Dockerfile.probe -t industrace-probe .
docker run -d --name network-probe --privileged --network host \
  -v $(pwd)/probe.conf:/app/probe.conf:ro industrace-probe
```

4. Confirm heartbeat in the UI; check **Discovered devices** after the first data transmission (default ~5 minutes).

## Key files

| File | Purpose |
|------|---------|
| `network_probe_client.py` | Runtime orchestrator |
| `probe_cli.py` | CLI and config helpers |
| `probe.conf` / `probe.conf.example` | Configuration |
| `Dockerfile.probe` | Container image |
| `docker-compose.probes.yml` | Multi-probe compose example |
| `tests/` | Client unit tests |
| `README.md` | Module map (this file) |
| `NETWORK_PROBE.md` | Full operations guide |

## Related Industrace docs

- [INSTALLATION.md](../docs/INSTALLATION.md) — server install
- [CONFIGURATION.md](../docs/CONFIGURATION.md) — server env vars
- [API.md](../docs/API.md) — REST API overview
- [troubleshooting.md](../docs/troubleshooting.md) — general server issues
