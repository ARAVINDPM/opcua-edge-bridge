"""Logs every write command (accepted or not) to a JSONL file and optionally to MQTT."""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable

Publisher = Callable[[str], None]


class AuditLog:
    def __init__(self, path: str | None = None, publish: Publisher | None = None) -> None:
        self.path = path
        self.publish = publish
        self.records: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def record(self, *, topic: str, signal: str | None, requested: Any, previous: Any,
               result: str, reason: str = "") -> dict[str, Any]:
        rec = {"ts": round(time.time(), 3), "topic": topic, "signal": signal,
               "requested": requested, "previous": previous, "result": result, "reason": reason}
        line = json.dumps(rec, separators=(",", ":"))
        with self._lock:
            self.records.append(rec)
            if self.path:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
        if self.publish:
            self.publish(line)
        return rec
