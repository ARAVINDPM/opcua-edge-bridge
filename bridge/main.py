"""CLI: python -m bridge.main --config config/sim.json"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal as os_signal

from . import bridge as bridge_mod
from .bridge import Bridge
from .audit import AuditLog
from .core import Signal, Topics, state_payload
from .mqtt_sink import FakeBroker, PahoSink


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build(cfg: dict, dry_run: bool) -> Bridge:
    topics = Topics(**cfg.get("topics", {}))
    signals = [Signal(**s) for s in cfg["signals"]]
    if dry_run:
        sink = FakeBroker()
    else:
        m = cfg["mqtt"]
        sink = PahoSink(m["host"], m.get("port", 1883), m.get("client_id", "opcua-edge-bridge"),
                        topics.state, state_payload(False, bridge_mod.__version__), topics.cmd_wildcard,
                        m.get("username"), m.get("password"), m.get("tls", False))
    bridge_mod.DEMO_OBJECT = cfg.get("root_object", "Demo")
    audit = AuditLog(cfg.get("audit_log", "logs/audit.jsonl"),
                     publish=lambda line: sink.publish(topics.audit, line))
    return Bridge(cfg["endpoint"], signals, sink, topics, namespace=cfg.get("namespace", bridge_mod.NAMESPACE),
                  heartbeat_s=cfg.get("heartbeat_s", 30.0), publish_interval_ms=cfg.get("publish_interval_ms", 500),
                  audit=audit)


async def run(cfg: dict, dry_run: bool, seconds: float | None) -> None:
    b = build(cfg, dry_run)
    await b.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for s in (os_signal.SIGINT, os_signal.SIGTERM):
        try:
            loop.add_signal_handler(s, stop.set)
        except NotImplementedError:
            pass
    try:
        if seconds:
            await asyncio.wait_for(stop.wait(), timeout=seconds)
        else:
            await stop.wait()
    except asyncio.TimeoutError:
        pass
    finally:
        await b.stop()
        print(json.dumps(b.stats.__dict__))
        if dry_run:
            for t, p, r in b.sink.messages[:15]:
                print(t, p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/sim.json")
    ap.add_argument("--dry-run", action="store_true", help="no broker; print what would be published")
    ap.add_argument("--seconds", type=float, default=None)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    asyncio.run(run(load_config(args.config), args.dry_run, args.seconds))


if __name__ == "__main__":
    main()
