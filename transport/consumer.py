"""FabPilot consumer service — the central half of the pipeline.

Subscribes to telemetry over MQTT, runs the detector on every reading, and fires
the autonomous agent on each machine's first anomaly. This is what makes the
pipeline genuinely distributed: machines publish (transport/publisher.py), this
separate service ingests, decides, and acts.

paho's network thread only enqueues readings; the async loop pulls from the queue
(off-thread, so it never blocks the event loop), runs detection, and awaits the
budget-capped agent. One agent response per machine episode (cost control).

Run (broker up; publisher in another terminal):
    python -m transport.consumer
"""

from __future__ import annotations

import asyncio
import queue
import sys

from detect.zscore import ZScoreDetector

from agent.respond import respond_to_anomaly
from transport.mqtt_io import HOST, PORT, TOPIC, decode_payload, make_client


async def main(idle_timeout: float = 30.0) -> None:
    """Listen, detect, and let the agent act until the telemetry goes quiet."""
    inbox: queue.Queue[dict | None] = queue.Queue()
    client = make_client("fabpilot-consumer-service")
    client.on_message = lambda c, u, msg: inbox.put(decode_payload(msg.payload))
    # Subscribe on CONNACK so the SUBSCRIBE is sent once the connection is live —
    # avoids a race where readings published before the subscription registers are
    # silently dropped (matters when the consumer starts mid-stream).
    client.on_connect = lambda c, u, flags, rc, props: c.subscribe(f"{TOPIC}/#", qos=1)
    try:
        client.connect(HOST, PORT)
    except (ConnectionRefusedError, OSError) as exc:
        raise SystemExit(f"broker not reachable at {HOST}:{PORT} — run 'docker compose up -d' ({exc})")
    client.loop_start()
    print(f"FabPilot consumer listening on {TOPIC}/# at {HOST}:{PORT} ...")

    detector = ZScoreDetector()
    handled: set[str] = set()
    try:
        while True:
            try:  # off-thread blocking get so the event loop stays free for the agent
                reading = await asyncio.to_thread(inbox.get, True, idle_timeout)
            except queue.Empty:
                print(f"(no telemetry for {idle_timeout:.0f}s — stopping)")
                break
            if reading is None:
                continue  # corrupt payload
            for event in detector.observe(reading):
                if event["machine_id"] in handled:
                    continue  # one response per machine episode
                handled.add(event["machine_id"])
                print(f"\n!!! ANOMALY  {event['seed']}\n--- FabPilot responding ---")
                record = await respond_to_anomaly(event)
                print(
                    f"--- done: {len(record['actions'])} action(s), "
                    f"{record.get('subtype')}, ${record.get('cost_usd')} ---"
                )
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
