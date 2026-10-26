"""Pure bridge logic: no network, fully unit-testable.

Responsibilities
- Map OPC UA variables to MQTT topics (one topic per signal).
- Report by exception: publish only on change beyond a deadband, plus a
  heartbeat so consumers can tell "unchanged" from "stale".
- Build JSON payloads with source timestamp, quality and a sequence number.
- Validate inbound commands against an allow-list of writable signals
  (least privilege: nothing is writable unless configured).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Signal:
    name: str                 # stable signal name used in topics
    browse_path: str          # path below the Demo object, e.g. "SampleVariables/Sample_01"
    deadband: float = 0.0     # absolute deadband for numeric values
    writable: bool = False    # may be written via MQTT command topic
    dtype: str = "auto"       # "bool" | "int" | "float" | "auto"


@dataclass
class Topics:
    prefix: str = "factory"
    site: str = "lab"
    device: str = "nucleo-h753zi"

    @property
    def base(self) -> str:
        return f"{self.prefix}/{self.site}/{self.device}"

    def data(self, name: str) -> str:
        return f"{self.base}/data/{name}"

    def cmd(self, name: str) -> str:
        return f"{self.base}/cmd/{name}"

    @property
    def cmd_wildcard(self) -> str:
        return f"{self.base}/cmd/+"

    @property
    def state(self) -> str:
        return f"{self.base}/state"

    @property
    def audit(self) -> str:
        return f"{self.base}/audit"


@dataclass
class ExceptionFilter:
    """Report-by-exception with deadband and heartbeat."""
    heartbeat_s: float = 30.0
    _last_value: dict[str, Any] = field(default_factory=dict)
    _last_sent: dict[str, float] = field(default_factory=dict)

    def should_publish(self, sig: Signal, value: Any, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if sig.name not in self._last_value:
            return True
        prev = self._last_value[sig.name]
        if now - self._last_sent.get(sig.name, 0.0) >= self.heartbeat_s:
            return True
        if isinstance(value, bool) or isinstance(prev, bool):
            return value != prev
        if isinstance(value, (int, float)) and isinstance(prev, (int, float)):
            return abs(value - prev) > sig.deadband
        return value != prev

    def mark_sent(self, sig: Signal, value: Any, now: float | None = None) -> None:
        self._last_value[sig.name] = value
        self._last_sent[sig.name] = time.monotonic() if now is None else now


class Sequencer:
    def __init__(self) -> None:
        self._n = 0

    def next(self) -> int:
        self._n = (self._n + 1) % 2**32
        return self._n


def build_payload(sig: Signal, value: Any, source_ts: float | None, good: bool, seq: int) -> str:
    return json.dumps(
        {
            "signal": sig.name,
            "value": value,
            "source_ts": source_ts,
            "bridge_ts": round(time.time(), 3),
            "quality": "good" if good else "bad",
            "seq": seq,
        },
        separators=(",", ":"),
    )


def state_payload(online: bool, version: str) -> str:
    return json.dumps({"online": online, "bridge_version": version}, separators=(",", ":"))


class CommandError(ValueError):
    pass


def parse_command(topics: Topics, signals: dict[str, Signal], topic: str, payload: bytes) -> tuple[Signal, Any]:
    """Validate an inbound MQTT command. Returns (signal, coerced value)."""
    prefix = topics.base + "/cmd/"
    if not topic.startswith(prefix):
        raise CommandError(f"not a command topic: {topic}")
    name = topic[len(prefix):]
    sig = signals.get(name)
    if sig is None:
        raise CommandError(f"unknown signal: {name}")
    if not sig.writable:
        raise CommandError(f"signal not writable: {name}")
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise CommandError(f"payload is not JSON: {e}") from e
    value = raw.get("value") if isinstance(raw, dict) else raw
    return sig, coerce(sig, value)


def coerce(sig: Signal, value: Any) -> Any:
    if sig.dtype == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ("true", "false", "on", "off", "1", "0"):
            return value.lower() in ("true", "on", "1")
        if value in (0, 1):
            return bool(value)
        raise CommandError(f"{sig.name}: expected bool, got {value!r}")
    if sig.dtype == "int":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise CommandError(f"{sig.name}: expected int, got {value!r}")
        return int(value)
    if sig.dtype == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CommandError(f"{sig.name}: expected number, got {value!r}")
        return float(value)
    return value
