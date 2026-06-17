"""Simulated manufacturing machines emitting sensor telemetry.

Transport-agnostic on purpose: a Machine just produces readings. MQTT publishing
is a separate slice (the message bus is a clean seam, per CLAUDE.md). The model is
deliberately simple but physically plausible — one health variable in [0, 1]
drives correlated drift in vibration, temperature, and current draw, the classic
signature of progressive wear (e.g. a degrading bearing). Injecting a fault speeds
the decline so the downstream detector and agent have a real signal to catch.

Stdlib only (random.gauss); no numpy needed at this size.

Run:  python -m sim.machine        # prints a 3-machine line, faults M2 midway
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass

from collections.abc import Iterator


@dataclass(frozen=True)
class Sensor:
    """A sensor's nominal value, how far it drifts at full wear, and its noise."""

    nominal: float
    fault_gain: float  # added to the reading at health == 0
    noise: float       # gaussian sigma


# Plausible bench values. Vibration in mm/s RMS (ISO 10816: ~2 good, >7 severe),
# temperature in degC, current in A.
VIBRATION = Sensor(nominal=2.0, fault_gain=12.0, noise=0.15)
TEMPERATURE = Sensor(nominal=45.0, fault_gain=35.0, noise=0.4)
CURRENT = Sensor(nominal=8.0, fault_gain=6.0, noise=0.1)


@dataclass
class Machine:
    """One machine whose health decays over time and faster under a fault."""

    machine_id: str
    health: float = 1.0
    decay: float = 0.0005       # slow baseline wear per tick, even when healthy
    _fault_rate: float = 0.0    # extra health lost per tick once faulting

    def inject_fault(self, severity: float = 0.02) -> None:
        """Begin accelerated degradation (severity = extra health lost per tick).

        Sets the fault rate; it does not accumulate across calls.
        """
        self._fault_rate = severity

    def tick(self) -> dict:
        """Advance one step and return a sensor reading."""
        self.health = max(0.0, self.health - self.decay - self._fault_rate)
        wear = 1.0 - self.health
        return {
            "machine_id": self.machine_id,
            "ts": time.time(),
            "vibration": self._read(VIBRATION, wear),
            "temperature": self._read(TEMPERATURE, wear),
            "current": self._read(CURRENT, wear),
            "health": round(self.health, 4),  # ground truth for eval; not fed to the agent
        }

    @staticmethod
    def _read(sensor: Sensor, wear: float) -> float:
        # Clamp at 0: vibration/temperature/current are magnitudes, never negative.
        value = sensor.nominal + sensor.fault_gain * wear + random.gauss(0, sensor.noise)
        return round(max(0.0, value), 3)


def run_line(
    machines: list[Machine],
    ticks: int,
    fault_at: int | None = None,
    fault_machine: Machine | None = None,
) -> Iterator[dict]:
    """Tick every machine `ticks` times, optionally faulting one partway through."""
    for t in range(ticks):
        if fault_at is not None and t == fault_at and fault_machine is not None:
            fault_machine.inject_fault()
        for machine in machines:
            yield machine.tick()


if __name__ == "__main__":
    random.seed(0)
    line = [Machine(f"M{i}") for i in range(1, 4)]
    for reading in run_line(line, ticks=30, fault_at=10, fault_machine=line[1]):
        print(json.dumps(reading))
    # self-check: the faulted machine must end clearly degraded while a peer stays
    # near-healthy. Brackets the expected ~0.4 separation, not just "something moved".
    assert line[0].health > 0.98, "unfaulted M1 should stay near-healthy"
    assert line[1].health < line[0].health - 0.3, "fault injection did not degrade M2 enough"
    print("# self-check OK: M2 degraded well below a near-healthy M1")
