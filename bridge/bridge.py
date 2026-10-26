"""Wires OPC UA (asyncua client subscription) to an MQTT sink."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from asyncua import Client, ua

from .core import (CommandError, ExceptionFilter, Sequencer, Signal, Topics,
                   build_payload, parse_command, state_payload)
from .mqtt_sink import Sink

__version__ = "0.1.0"
log = logging.getLogger("bridge")

DEMO_OBJECT = "Demo"
NAMESPACE = "urn:demo:eflex-sim"


@dataclass
class BridgeStats:
    received: int = 0
    published: int = 0
    suppressed: int = 0
    commands_ok: int = 0
    commands_rejected: int = 0


class _SubHandler:
    def __init__(self, bridge: "Bridge") -> None:
        self.bridge = bridge

    def datachange_notification(self, node, val, data):
        mi = data.monitored_item.Value
        ts = mi.SourceTimestamp.timestamp() if mi.SourceTimestamp else None
        good = mi.StatusCode.is_good() if mi.StatusCode else True
        self.bridge._on_data(node.nodeid, val, ts, good)


class Bridge:
    def __init__(self, endpoint: str, signals: list[Signal], sink: Sink, topics: Topics,
                 namespace: str = NAMESPACE, heartbeat_s: float = 30.0,
                 publish_interval_ms: int = 500) -> None:
        self.endpoint = endpoint
        self.signals = {s.name: s for s in signals}
        self.sink = sink
        self.topics = topics
        self.namespace = namespace
        self.filter = ExceptionFilter(heartbeat_s=heartbeat_s)
        self.seq = Sequencer()
        self.stats = BridgeStats()
        self.publish_interval_ms = publish_interval_ms
        self._client: Client | None = None
        self._node_to_sig: dict = {}
        self._sig_to_node: dict = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._pending: set[asyncio.Task] = set()

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._client = Client(self.endpoint)
        await self._client.connect()
        idx = await self._client.get_namespace_index(self.namespace)
        demo = await self._client.nodes.objects.get_child(f"{idx}:{DEMO_OBJECT}")
        for sig in self.signals.values():
            path = [f"{idx}:{p}" for p in sig.browse_path.split("/")]
            node = await demo.get_child(path)
            self._node_to_sig[node.nodeid] = sig
            self._sig_to_node[sig.name] = node
        sub = await self._client.create_subscription(self.publish_interval_ms, _SubHandler(self))
        await sub.subscribe_data_change(list(self._sig_to_node.values()))
        self.sink.on_command(self._on_command)
        self.sink.publish(self.topics.state, state_payload(True, __version__), retain=True)
        log.info("bridge started: %d signals", len(self.signals))

    async def stop(self) -> None:
        self.sink.publish(self.topics.state, state_payload(False, __version__), retain=True)
        for t in list(self._pending):
            await t
        if self._client:
            await self._client.disconnect()
        self.sink.close()

    # OPC UA -> MQTT
    def _on_data(self, nodeid, value, ts, good) -> None:
        sig = self._node_to_sig.get(nodeid)
        if sig is None:
            return
        self.stats.received += 1
        if not self.filter.should_publish(sig, value):
            self.stats.suppressed += 1
            return
        self.sink.publish(self.topics.data(sig.name), build_payload(sig, value, ts, good, self.seq.next()))
        self.filter.mark_sent(sig, value)
        self.stats.published += 1

    # MQTT -> OPC UA
    def _on_command(self, topic: str, payload: bytes) -> None:
        try:
            sig, value = parse_command(self.topics, self.signals, topic, payload)
        except CommandError as e:
            self.stats.commands_rejected += 1
            log.warning("command rejected: %s", e)
            return
        node = self._sig_to_node[sig.name]
        vtype = {"bool": ua.VariantType.Boolean, "int": ua.VariantType.Int32,
                 "float": ua.VariantType.Double}.get(sig.dtype)
        variant = ua.Variant(value, vtype) if vtype else ua.Variant(value)
        coro = node.write_value(ua.DataValue(variant))
        assert self._loop is not None
        task = asyncio.run_coroutine_threadsafe(coro, self._loop) if not _in_loop(self._loop) \
            else self._loop.create_task(coro)
        if isinstance(task, asyncio.Task):
            self._pending.add(task)
            task.add_done_callback(self._pending.discard)
        self.stats.commands_ok += 1


def _in_loop(loop: asyncio.AbstractEventLoop) -> bool:
    try:
        return asyncio.get_running_loop() is loop
    except RuntimeError:
        return False
