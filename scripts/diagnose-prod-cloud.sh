#!/usr/bin/env bash
# Quick diagnostics for make prod-cloud (Traefik) 404 / routing issues.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE=".env.prod-cloud"
COMPOSE=(docker-compose -f docker-compose.yml)
if [[ -f "$ENV_FILE" ]]; then
  COMPOSE+=(--env-file "$ENV_FILE")
fi

echo "=== Traefik image / version ==="
docker ps --filter name=traefik --format '{{.Image}}  {{.Status}}' || true
docker exec "$("${COMPOSE[@]}" ps -q traefik 2>/dev/null | head -1)" traefik version 2>/dev/null || true

echo ""
echo "=== Traefik Docker provider errors (last 30 lines matching) ==="
"${COMPOSE[@]}" logs traefik 2>/dev/null | grep -E 'error|Error|provider' | tail -30 || true

echo ""
echo "=== HTTP routers (Traefik API :8080) ==="
curl -sS http://127.0.0.1:8080/api/http/routers 2>/dev/null | python3 -c '
import json,sys
try:
    data=json.load(sys.stdin)
except Exception as e:
    print("Cannot read Traefik API:", e)
    sys.exit(0)
if not data:
    print("NO ROUTERS — Docker provider not discovering services (or labels missing)")
else:
    for r in sorted(data, key=lambda x: x.get("name","")):
        print("%s: rule=%s entry=%s status=%s" % (
            r.get("name"), r.get("rule"), r.get("entryPoints"), r.get("status")))
' || echo "Traefik dashboard/API not reachable on :8080"

echo ""
echo "=== Probe without Host header (IP-style access) ==="
code_ip=$(curl -sk -o /dev/null -w '%{http_code}' https://127.0.0.1/ || true)
echo "https://127.0.0.1/ -> HTTP $code_ip"

echo ""
echo "=== Probe with Host: industrace.local ==="
code_host=$(curl -sk -o /dev/null -w '%{http_code}' -H 'Host: industrace.local' https://127.0.0.1/ || true)
echo "Host industrace.local -> HTTP $code_host"

echo ""
echo "=== Frontend container direct (bypass Traefik) ==="
front_id=$("${COMPOSE[@]}" ps -q frontend 2>/dev/null | head -1 || true)
if [[ -n "${front_id:-}" ]]; then
  docker exec "$front_id" wget -q -O - http://127.0.0.1/ 2>/dev/null | head -c 120 || \
    docker exec "$front_id" curl -sS http://127.0.0.1/ 2>/dev/null | head -c 120 || \
    echo "(no wget/curl in frontend image)"
  echo ""
else
  echo "frontend container not found"
fi

echo ""
echo "Done. Expect routers frontend@docker / backend@docker and HTTP 200 on probes."
echo "If NO ROUTERS + 'client version 1.24 is too old' -> need Traefik >= v2.11.31"
echo "If routers exist but IP probe is 404 and Host probe is 200 -> Host() rule too strict"
echo "If both probes 404 but routers on entryPoints [web] only -> accessing HTTPS without websecure routers"
