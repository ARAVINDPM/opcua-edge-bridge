#!/usr/bin/env bash
# One-command demo: broker + OPC UA simulator + Node-RED dashboard + bridge.
# Usage: ./scripts/demo.sh        (Ctrl+C stops everything)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
PY=${PYTHON:-python3}
[ -x .venv/bin/python ] && PY=.venv/bin/python
PIDS=()

cleanup() {
  echo; echo "Stopping demo..."
  for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done
  [ "${STARTED_DOCKER:-0}" = 1 ] && docker compose stop mosquitto >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

port_open() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

wait_port() {
  for _ in $(seq 1 60); do port_open "$1" && return 0; sleep 0.5; done
  echo "Timeout waiting for port $1 ($2). See logs/." >&2; exit 1
}

# 1) MQTT broker: use a running one, else mosquitto, else docker, else amqtt
if port_open 1883; then
  echo "[1/4] MQTT broker already running on :1883"
elif command -v mosquitto >/dev/null; then
  echo "[1/4] Starting mosquitto"; mosquitto -c config/mosquitto.conf > logs/broker.log 2>&1 & PIDS+=($!)
elif command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  echo "[1/4] Starting mosquitto in Docker"; docker compose up -d mosquitto >/dev/null; STARTED_DOCKER=1
elif "$PY" -c "import amqtt" 2>/dev/null; then
  echo "[1/4] Starting amqtt (Python broker)"; "$PY" -m amqtt.scripts.broker_script > logs/broker.log 2>&1 & PIDS+=($!)
else
  echo "No MQTT broker found. Install one: brew install mosquitto" >&2; exit 1
fi
wait_port 1883 broker

# 2) OPC UA simulator of the board demo
echo "[2/4] Starting OPC UA simulator on opc.tcp://127.0.0.1:4842"
"$PY" -m sim.eflex_demo_sim > logs/sim.log 2>&1 & PIDS+=($!)
wait_port 4842 simulator

# 3) Node-RED dashboard (installs its dependencies on first run)
echo "[3/4] Starting Node-RED dashboard"
[ -d nodered/node_modules ] || (cd nodered && npm install --no-audit --no-fund)
(cd nodered && npx node-red -u . -s settings.js > ../logs/nodered.log 2>&1) & PIDS+=($!)
wait_port 1880 node-red
sleep 2

# 4) The bridge itself
echo "[4/4] Starting bridge"
"$PY" -m bridge.main --config config/sim.json > logs/bridge.log 2>&1 & PIDS+=($!)

URL=http://localhost:1880/dashboard
echo; echo "Dashboard: $URL   (Node-RED editor: http://localhost:1880/editor)"
echo "Audit trail file: logs/audit.jsonl   Stop: Ctrl+C"
{ (command -v open && open "$URL") || (command -v xdg-open && xdg-open "$URL"); } >/dev/null 2>&1 || true
wait
