"""End-to-end FabPilot spine: simulate -> detect -> agent reasons and acts.

Runs a line, feeds telemetry through the detector, and hands each machine's first
anomaly to the agent. One response per machine episode — the detector is already
edge-triggered, and this caps how many (paid) agent calls a run makes.

Run:  python -m agent.orchestrate    # makes real, budget-capped agent calls
"""

from __future__ import annotations

import asyncio
import random

from detect.zscore import ZScoreDetector
from sim.machine import Machine, run_line

from agent.respond import respond_to_anomaly


async def main() -> None:
    random.seed(0)
    line = [Machine(f"M{i}") for i in range(1, 4)]
    detector = ZScoreDetector()
    handled: set[str] = set()

    for reading in run_line(line, ticks=40, fault_at=18, fault_machine=line[1]):
        for event in detector.observe(reading):
            if event["machine_id"] in handled:
                continue  # one agent response per machine; cost control
            handled.add(event["machine_id"])
            print(f"\n!!! ANOMALY  {event['seed']}\n--- FabPilot responding ---")
            record = await respond_to_anomaly(event)
            print(
                f"--- done: {len(record['actions'])} action(s), "
                f"{record.get('subtype')}, ${record.get('cost_usd')} ---"
            )


if __name__ == "__main__":
    import sys

    # The agent's reasoning may contain non-ASCII (e.g. the sigma symbol); the
    # Windows console default (cp1252) would crash on it. Force UTF-8.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
