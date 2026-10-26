"""MQTT side. `FakeBroker` lets tests run without a broker; `PahoSink` is the
real client (paho-mqtt 2.x) with a Last Will so consumers see the bridge die."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

CommandHandler = Callable[[str, bytes], None]


class Sink(Protocol):
    def publish(self, topic: str, payload: str, retain: bool = False, qos: int = 1) -> None: ...
    def on_command(self, handler: CommandHandler) -> None: ...
    def close(self) -> None: ...


@dataclass
class FakeBroker:
    messages: list[tuple[str, str, bool]] = field(default_factory=list)
    _handler: CommandHandler | None = None
    closed: bool = False

    def publish(self, topic: str, payload: str, retain: bool = False, qos: int = 1) -> None:
        self.messages.append((topic, payload, retain))

    def on_command(self, handler: CommandHandler) -> None:
        self._handler = handler

    def inject(self, topic: str, payload: bytes) -> None:
        assert self._handler is not None, "no command handler registered"
        self._handler(topic, payload)

    def close(self) -> None:
        self.closed = True

    def topics(self) -> list[str]:
        return [t for t, _, _ in self.messages]


class PahoSink:
    def __init__(self, host: str, port: int, client_id: str, will_topic: str, will_payload: str,
                 cmd_filter: str, username: str | None = None, password: str | None = None,
                 tls: bool = False) -> None:
        import paho.mqtt.client as mqtt  # lazy import keeps unit tests dependency-light

        self._mqtt = mqtt
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        if username:
            self._client.username_pw_set(username, password)
        if tls:
            self._client.tls_set()
        self._client.will_set(will_topic, will_payload, qos=1, retain=True)
        self._cmd_filter = cmd_filter
        self._handler: CommandHandler | None = None
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.connect(host, port, keepalive=30)
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        client.subscribe(self._cmd_filter, qos=1)

    def _on_message(self, client, userdata, msg):
        if self._handler:
            self._handler(msg.topic, msg.payload)

    def publish(self, topic: str, payload: str, retain: bool = False, qos: int = 1) -> None:
        self._client.publish(topic, payload, qos=qos, retain=retain)

    def on_command(self, handler: CommandHandler) -> None:
        self._handler = handler

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
