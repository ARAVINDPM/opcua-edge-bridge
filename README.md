# opcua-edge-bridge

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ARAVINDPM/opcua-edge-bridge?quickstart=1)

At embedded world 2026 I was given an STM32 NUCLEO-H753ZI with an embedded OPC UA server demo on it. I wanted to see how its data would end up in something like Node-RED. The board is still waiting to be flashed (that's next, see [docs/board.md](docs/board.md)). Until then there's a small Python simulator that behaves like the demo: ten counters, an LED you can switch, a few I/O values.

The bridge subscribes to the OPC UA values and only publishes them to MQTT when they change. Writing back is allowed only for signals marked `writable` in the config. Anything else is refused, and every attempt, accepted or not, goes into `logs/audit.jsonl`. If the bridge dies, the broker's last-will message sets its state to offline, so a dashboard can tell "nothing changed" from "gone".

![demo](docs/img/demo.gif)

## Run it

Click the Codespaces button, or locally (Python 3.10–3.13, Node.js, Mosquitto):

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
./scripts/demo.sh
```

Then open http://localhost:1880. `pytest` runs the tests.

## Not done yet

- Running it on the real board.
- TLS and logins (it's a lab setup).
- The board offers an ECC security policy, but the Python OPC UA client (asyncua) can't use it, so right now the connection runs without security.
- Buffering when the broker is down.

I wrote this with a lot of help from an AI coding assistant. I'm using it to learn the OPC UA side properly.
