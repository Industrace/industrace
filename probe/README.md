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
| `network_probe_client.py` | Probe client |
| `probe.conf` / `probe.conf.example` | Configuration |
| `Dockerfile.probe` | Container image |
| `docker-compose.probes.yml` | Multi-probe compose example |

## Related Industrace docs

- [INSTALLATION.md](../docs/INSTALLATION.md) — server install
- [CONFIGURATION.md](../docs/CONFIGURATION.md) — server env vars
- [API.md](../docs/API.md) — REST API overview
- [troubleshooting.md](../docs/troubleshooting.md) — general server issues
