"""Simulated OPC UA server modelled on the eFlex OPC UA SDK demo for the
STM32 NUCLEO-H753ZI (as described in the vendor's quick installation guide).

It is NOT the vendor firmware. It reproduces the *observable* behaviour of the
demo so the bridge can be developed and tested without hardware:

  - SampleVariables: 10 integers that increment once per second
  - LED_1:           writable boolean (on the real board: green LED)
  - IO:              a few mapped digital inputs/outputs
  - CreateSetOfVariables(): method that adds 50 new runtime variables
  - MemoryUsage:     runtime memory value that changes while clients interact

Real board endpoint per guide: opc.tcp://192.168.1.102:4842
Simulator default endpoint:     opc.tcp://127.0.0.1:4842
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import random

from asyncua import Server, ua

NAMESPACE = "urn:demo:eflex-sim"
log = logging.getLogger("eflex-sim")


async def build_server(endpoint: str) -> tuple[Server, dict]:
    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    server.set_server_name("eFlex demo simulator (not vendor firmware)")
    # The real demo offers None + ECC_nistP256. asyncua has no ECC policies,
    # so the simulator offers None only. See docs/SECURITY_NOTES.md.
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    idx = await server.register_namespace(NAMESPACE)
    objects = server.nodes.objects
    demo = await objects.add_object(idx, "Demo")

    samples_obj = await demo.add_object(idx, "SampleVariables")
    samples = []
    for i in range(1, 11):
        v = await samples_obj.add_variable(idx, f"Sample_{i:02d}", 0, ua.VariantType.Int32)
        samples.append(v)

    led = await demo.add_variable(idx, "LED_1", False, ua.VariantType.Boolean)
    await led.set_writable(True)

    io_obj = await demo.add_object(idx, "IO")
    di1 = await io_obj.add_variable(idx, "DI_1", False, ua.VariantType.Boolean)
    do1 = await io_obj.add_variable(idx, "DO_1", False, ua.VariantType.Boolean)
    await do1.set_writable(True)

    mem = await demo.add_variable(idx, "MemoryUsage", 48_000, ua.VariantType.UInt32)
    runtime_obj = await demo.add_object(idx, "RuntimeVariables")

    state = {"runtime_created": 0}

    async def create_set_of_variables(parent):
        base = state["runtime_created"]
        for n in range(base + 1, base + 51):
            await runtime_obj.add_variable(idx, f"Runtime_{n:03d}", 0, ua.VariantType.Int32)
        state["runtime_created"] += 50
        return [ua.Variant(state["runtime_created"], ua.VariantType.UInt32)]

    await demo.add_method(
        idx, "CreateSetOfVariables", create_set_of_variables, [], [ua.VariantType.UInt32]
    )

    nodes = {"samples": samples, "led": led, "di1": di1, "do1": do1, "mem": mem, "state": state}
    return server, nodes


async def tick(nodes: dict, period: float = 1.0) -> None:
    """Increment sample variables once per period; jitter memory usage."""
    while True:
        await asyncio.sleep(period)
        for v in nodes["samples"]:
            await v.write_value(ua.Variant((await v.read_value()) + 1, ua.VariantType.Int32))
        base = 48_000 + 64 * nodes["state"]["runtime_created"]
        await nodes["mem"].write_value(ua.Variant(base + random.randint(0, 512), ua.VariantType.UInt32))


async def serve(endpoint: str, period: float = 1.0, stop: asyncio.Event | None = None) -> None:
    server, nodes = await build_server(endpoint)
    async with server:
        log.info("simulator up at %s", endpoint)
        task = asyncio.create_task(tick(nodes, period))
        try:
            if stop is None:
                await asyncio.Event().wait()
            else:
                await stop.wait()
        finally:
            task.cancel()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoint", default="opc.tcp://127.0.0.1:4842")
    ap.add_argument("--period", type=float, default=1.0)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve(args.endpoint, args.period))


if __name__ == "__main__":
    main()
