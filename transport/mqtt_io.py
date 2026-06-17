"""MQTT transport for FabPilot telemetry: machines publish, the line consumes.

The message bus the architecture is built around (CLAUDE.md). Each reading is
published as JSON to ``fabpilot/telemetry/<machine_id>``; the consumer subscribes,
decodes, and feeds the same reading-dicts to the existing detector — so the stream
is identical whether it comes from the in-process generator or over the wire. That
is the clean seam that let detection be built before transport.

Broker: Mosquitto via ``docker compose up -d`` (see docker-compose.yml).
Host/port from env (FABPILOT_BROKER_HOST/PORT), default localhost:1883.

Run (broker must be up):
    python -m transport.mqtt_io     # publishes a line, consumes it back, asserts M2 flagged
"""

from __future__ import annotations

import json
import os
import queue
import time
from collections.abc import Iterable

import paho.mqtt.client as mqtt

TOPIC = "fabpilot/telemetry"
HOST = os.environ.get("FABPILOT_BROKER_HOST", "localhost")
PORT = int(os.environ.get("FABPILOT_BROKER_PORT", "1883"))


def make_client(name: str) -> mqtt.Client:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=name)


def decode_payload(payload: bytes) -> dict | None:
    """Decode a telemetry payload; None means 'arrived but corrupt' (vs. dropped)."""
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def publish_readings(readings: Iterable[dict], host: str = HOST, port: int = PORT,
                     delay: float = 0.0) -> int:
    """Publish each reading to fabpilot/telemetry/<machine_id> (qos 1). Returns count."""
    client = make_client("fabpilot-publisher")
    client.connect(host, port)
    client.loop_start()
    try:
        sent = 0
        for reading in readings:
            info = client.publish(f"{TOPIC}/{reading['machine_id']}", json.dumps(reading), qos=1)
            info.wait_for_publish(timeout=5)  # qos-1 confirmation before moving on
            sent += 1
            if delay:
                time.sleep(delay)
        return sent
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    import random

    from detect.zscore import ZScoreDetector
    from sim.machine import Machine, run_line

    random.seed(0)
    line = [Machine(f"M{i}") for i in range(1, 4)]
    readings = list(run_line(line, ticks=40, fault_at=18, fault_machine=line[1]))

    received: queue.Queue[dict | None] = queue.Queue()
    consumer = make_client("fabpilot-consumer")
    consumer.on_message = lambda c, u, msg: received.put(decode_payload(msg.payload))
    try:
        consumer.connect(HOST, PORT)
    except (ConnectionRefusedError, OSError) as exc:
        raise SystemExit(f"broker not reachable at {HOST}:{PORT} — run 'docker compose up -d' ({exc})")
    consumer.subscribe(f"{TOPIC}/#", qos=1)
    consumer.loop_start()
    time.sleep(0.3)  # let the subscription register before publishing

    sent = publish_readings(readings)

    detector = ZScoreDetector()
    flagged: set[str] = set()
    got = corrupt = 0
    deadline = time.time() + 10
    while got < sent and time.time() < deadline:
        try:
            reading = received.get(timeout=1)
        except queue.Empty:
            continue  # bounded by `deadline`; don't abort on one slow poll
        got += 1
        if reading is None:
            corrupt += 1
            continue
        for event in detector.observe(reading):
            flagged.add(event["machine_id"])
            print(event["seed"])
    consumer.loop_stop()
    consumer.disconnect()

    assert corrupt == 0, f"{corrupt} corrupt payload(s) over MQTT"
    assert got == sent, f"received {got}/{sent} readings over MQTT"
    assert flagged == {"M2"}, f"expected only M2 over the wire, got {flagged or 'nothing'}"
    print(f"# self-check OK: {got}/{sent} readings over MQTT, only M2 flagged")
