"""FabPilot publisher — the machines/edge half of the pipeline.

Simulates a production line and streams its telemetry over MQTT, one reading at a
time with a small delay so it behaves like a live feed (not a burst). Run this in
one terminal and the consumer service (transport/consumer.py) in another to see the
full distributed pipeline: machines -> broker -> detect -> agent acts.

Run (broker up):
    python -m transport.publisher
"""

from __future__ import annotations

import random

from sim.machine import Machine, run_line

from transport.mqtt_io import publish_readings


def main(ticks: int = 50, delay: float = 0.1, fault_at: int = 25) -> None:
    random.seed(0)
    line = [Machine(f"M{i}") for i in range(1, 4)]
    readings = run_line(line, ticks=ticks, fault_at=fault_at, fault_machine=line[1])
    sent = publish_readings(readings, delay=delay)
    print(f"published {sent} readings over MQTT")


if __name__ == "__main__":
    main()
