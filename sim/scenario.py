"""The one canned scenario the demo and the golden test both run.

Single source of truth on purpose: a golden test that validates a *different*
scenario than the demo actually runs is worse than no test — it passes green while
lying. So both `agent.orchestrate.run` (the demo/dashboard) and
`evals.golden_scenario` consume `canned_readings()` from here. Change the scenario
in one place; both move together.

Stdlib only (random). Deterministic: seeding happens when iteration begins.
"""

from __future__ import annotations

import random
from collections.abc import Iterator

from sim.machine import Machine, run_line

SEED = 0
TICKS = 40
FAULT_AT = 18
FAULT_MACHINE_IDX = 1  # M2, the middle machine of the M1–M3 line


def build_line() -> list[Machine]:
    """The fixed 3-machine line the scenario runs on."""
    return [Machine(f"M{i}") for i in range(1, 4)]


def canned_readings() -> Iterator[dict]:
    """Deterministic telemetry stream: seed the RNG, then fault M2 partway through."""
    random.seed(SEED)
    line = build_line()
    yield from run_line(line, ticks=TICKS, fault_at=FAULT_AT, fault_machine=line[FAULT_MACHINE_IDX])
