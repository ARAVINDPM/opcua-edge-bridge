"""End-to-end against the simulator: OPC UA server <-> bridge <-> fake MQTT broker."""
import asyncio
import json
import socket

import pytest
from asyncua import Client

from bridge.bridge import Bridge
from bridge.core import Signal, Topics
from bridge.mqtt_sink import FakeBroker
from sim.eflex_demo_sim import serve


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


async def wait_for_server(endpoint: str, timeout: float = 15.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        try:
            async with Client(endpoint):
                return
        except (OSError, asyncio.TimeoutError):
            if asyncio.get_running_loop().time() > deadline:
                raise
            await asyncio.sleep(0.3)


SIGNALS = [
    Signal("sample_01", "SampleVariables/Sample_01", dtype="int"),
    Signal("led_1", "LED_1", dtype="bool", writable=True),
    Signal("memory_usage", "MemoryUsage", dtype="int", deadband=10_000),
]


@pytest.mark.asyncio
async def test_bridge_end_to_end():
    endpoint = f"opc.tcp://127.0.0.1:{free_port()}"
    stop = asyncio.Event()
    server_task = asyncio.create_task(serve(endpoint, period=0.2, stop=stop))
    await wait_for_server(endpoint)

    broker = FakeBroker()
    topics = Topics(site="test", device="sim")
    b = Bridge(endpoint, SIGNALS, broker, topics, heartbeat_s=60, publish_interval_ms=100)
    await b.start()
    await asyncio.sleep(1.5)

    # birth message, retained
    assert broker.messages[0][0] == topics.state and broker.messages[0][2] is True
    assert json.loads(broker.messages[0][1])["online"] is True

    # counter values arrive and increase
    counts = [json.loads(p)["value"] for t, p, _ in broker.messages if t == topics.data("sample_01")]
    assert len(counts) >= 3 and counts == sorted(counts)

    # deadband suppresses memory jitter (jitter < 10_000)
    assert b.stats.suppressed > 0

    # command: switch LED on via MQTT, verify on the OPC UA server
    broker.inject(topics.cmd("led_1"), b'{"value": true}')
    await asyncio.sleep(0.8)
    async with Client(endpoint) as c:
        idx = await c.get_namespace_index("urn:demo:eflex-sim")
        led = await c.nodes.objects.get_child([f"{idx}:Demo", f"{idx}:LED_1"])
        assert await led.read_value() is True
    led_msgs = [json.loads(p)["value"] for t, p, _ in broker.messages if t == topics.data("led_1")]
    assert led_msgs[-1] is True

    # write to a read-only signal is rejected
    broker.inject(topics.cmd("sample_01"), b'5')
    assert b.stats.commands_rejected == 1

    # audit trail: one written, one rejected; both published on the audit topic
    results = [(r["signal"], r["result"]) for r in b.audit.records]
    assert ("led_1", "written") in results and ("sample_01", "rejected") in results
    written = next(r for r in b.audit.records if r["result"] == "written")
    assert written["previous"] is False and written["requested"] is True
    assert sum(1 for t, _, _ in broker.messages if t == topics.audit) == len(b.audit.records)

    await b.stop()
    assert json.loads(broker.messages[-1][1])["online"] is False and broker.closed
    stop.set()
    await server_task


@pytest.mark.asyncio
async def test_create_set_of_variables_method():
    endpoint = f"opc.tcp://127.0.0.1:{free_port()}"
    stop = asyncio.Event()
    server_task = asyncio.create_task(serve(endpoint, period=0.5, stop=stop))
    await wait_for_server(endpoint)
    async with Client(endpoint) as c:
        idx = await c.get_namespace_index("urn:demo:eflex-sim")
        demo = await c.nodes.objects.get_child(f"{idx}:Demo")
        n = await demo.call_method(f"{idx}:CreateSetOfVariables")
        assert n == 50
        rt = await demo.get_child(f"{idx}:RuntimeVariables")
        assert len(await rt.get_children()) == 50
    stop.set()
    await server_task
