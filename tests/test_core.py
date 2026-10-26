import json

import pytest

from bridge.core import (CommandError, ExceptionFilter, Sequencer, Signal, Topics,
                         build_payload, parse_command)

T = Topics(prefix="factory", site="lab", device="dev1")
LED = Signal("led_1", "LED_1", dtype="bool", writable=True)
CNT = Signal("sample_01", "SampleVariables/Sample_01", dtype="int")
MEM = Signal("memory_usage", "MemoryUsage", dtype="int", deadband=256)
SIGS = {s.name: s for s in (LED, CNT, MEM)}


def test_topics():
    assert T.data("led_1") == "factory/lab/dev1/data/led_1"
    assert T.cmd_wildcard == "factory/lab/dev1/cmd/+"
    assert T.state == "factory/lab/dev1/state"


def test_first_value_always_published():
    f = ExceptionFilter()
    assert f.should_publish(CNT, 1, now=0)


def test_deadband_suppresses_small_changes():
    f = ExceptionFilter(heartbeat_s=100)
    f.mark_sent(MEM, 48000, now=0)
    assert not f.should_publish(MEM, 48200, now=1)
    assert f.should_publish(MEM, 48300, now=2)


def test_heartbeat_republishes_unchanged_value():
    f = ExceptionFilter(heartbeat_s=10)
    f.mark_sent(LED, False, now=0)
    assert not f.should_publish(LED, False, now=5)
    assert f.should_publish(LED, False, now=10)


def test_bool_change_always_published():
    f = ExceptionFilter(heartbeat_s=100)
    f.mark_sent(LED, False, now=0)
    assert f.should_publish(LED, True, now=1)


def test_payload_fields():
    p = json.loads(build_payload(CNT, 7, 1700000000.0, True, Sequencer().next()))
    assert p["signal"] == "sample_01" and p["value"] == 7 and p["quality"] == "good" and p["seq"] == 1


@pytest.mark.parametrize("raw,expected", [(b'{"value": true}', True), (b'false', False), (b'"on"', True), (b'0', False)])
def test_command_ok(raw, expected):
    sig, val = parse_command(T, SIGS, "factory/lab/dev1/cmd/led_1", raw)
    assert sig is LED and val is expected


@pytest.mark.parametrize("topic,raw", [
    ("factory/lab/dev1/cmd/sample_01", b'5'),        # not writable
    ("factory/lab/dev1/cmd/unknown", b'1'),          # unknown signal
    ("other/topic", b'1'),                           # wrong prefix
    ("factory/lab/dev1/cmd/led_1", b'not json'),     # bad payload
    ("factory/lab/dev1/cmd/led_1", b'"maybe"'),      # bad type
])
def test_command_rejected(topic, raw):
    with pytest.raises(CommandError):
        parse_command(T, SIGS, topic, raw)
