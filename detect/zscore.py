"""Z-score anomaly detection for machine telemetry.

Per machine+sensor we learn a healthy baseline (mean, std) from the first
`warmup` readings, then flag any later reading that deviates more than
`threshold` sigma from that *frozen* baseline.

Frozen, not a trailing window, on purpose: the faults we care about are
*progressive*. A trailing window would slowly absorb the rising values into its
own mean and stop alerting on a machine that is visibly degrading. A frozen
healthy baseline keeps the deviation growing as the machine worsens — which is
both correct for wear detection and clear in a live demo. EWMA / adaptive
baselines are the documented upgrade (DECISIONS.md D-013).

Detection requires `persistence` consecutive crossings before firing, so a single
noisy sample can't raise a false alarm — a real fault sustains the deviation, a
noise spike doesn't. It is also edge-triggered: one event per episode, not one per
tick, so the downstream agent loop fires once per fault, not every reading. Each
event also carries a first-order time-to-failure estimate (see detect/forecast.py),
so the agent reasons from a number, not just a deviation. Stdlib only (statistics).

Run:  python -m detect.zscore     # feeds the simulator through the detector
"""

from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field

from detect.forecast import FAILURE_THRESHOLDS, MAX_HORIZON, time_to_failure

SENSORS = ("vibration", "temperature", "current")
UNITS = {"vibration": "mm/s", "temperature": "degC", "current": "A"}

# Every sensor we detect on needs a failure threshold to forecast against. Assert
# it at import so adding a sensor without a threshold fails loudly here, not with a
# KeyError at the first anomaly in a live demo.
assert set(SENSORS) <= FAILURE_THRESHOLDS.keys(), "sensor missing a failure threshold"


@dataclass
class _Baseline:
    samples: list[float] = field(default_factory=list)
    mean: float = 0.0
    std: float = 0.0
    ready: bool = False
    streak: int = 0       # consecutive readings currently over threshold
    cool: int = 0         # consecutive readings currently under threshold
    firing: bool = False  # currently inside an anomaly episode (edge-trigger latch)
    n: int = 0            # count of post-warmup readings (x-axis for the trend fit)
    recent: deque = field(default_factory=lambda: deque(maxlen=8))  # (n, value) recent-trend window


@dataclass
class ZScoreDetector:
    """Learns a healthy baseline per machine+sensor, then flags deviations."""

    warmup: int = 15        # healthy readings used to learn each baseline
    threshold: float = 4.0  # sigma deviation that counts as anomalous
    persistence: int = 3    # consecutive crossings required to fire (rejects noise spikes)
    _baselines: dict[tuple[str, str], _Baseline] = field(default_factory=dict)

    def observe(self, reading: dict) -> list[dict]:
        """Feed one reading; return any anomaly events it triggered (often none)."""
        events = []
        for sensor in SENSORS:
            base = self._baselines.setdefault((reading["machine_id"], sensor), _Baseline())
            value = reading[sensor]

            if not base.ready:
                base.samples.append(value)
                if len(base.samples) >= self.warmup:
                    base.mean = statistics.fmean(base.samples)
                    base.std = statistics.pstdev(base.samples) or 1e-9  # avoid /0
                    base.ready = True
                continue

            z = (value - base.mean) / base.std
            base.recent.append((base.n, value))  # keep the recent trend for forecasting
            base.n += 1
            if abs(z) >= self.threshold:
                base.streak += 1
                base.cool = 0
                if base.streak >= self.persistence and not base.firing:
                    base.firing = True  # rising edge, confirmed by persistence
                    events.append(self._event(reading, sensor, value, z, base.mean, base.recent))
            else:
                base.streak = 0
                base.cool += 1
                # Re-arm only after the signal has stayed clear for `persistence`
                # readings, so a single noisy dip mid-fault can't cause a re-fire.
                if base.cool >= self.persistence:
                    base.firing = False
        return events

    @staticmethod
    def _event(reading: dict, sensor: str, value: float, z: float, baseline: float, recent) -> dict:
        unit = UNITS[sensor]
        threshold = FAILURE_THRESHOLDS[sensor]
        ttf = time_to_failure(list(recent), threshold)
        if ttf is None:
            horizon = f"not yet trending to the {threshold:g} {unit} failure threshold"
        elif ttf == 0.0:
            horizon = f"already at/over the {threshold:g} {unit} failure threshold"
        else:
            horizon = f"~{ttf:.0f} readings to the {threshold:g} {unit} failure threshold"
        seed = (
            f"{reading['machine_id']} {sensor} reading {value:.2f} {unit} is "
            f"{z:+.1f} sigma above its healthy baseline of {baseline:.2f} {unit}; "
            f"{horizon}. Assess the failure risk and act."
        )
        return {
            "machine_id": reading["machine_id"],
            "sensor": sensor,
            "value": value,
            "z": round(z, 2),
            "baseline": round(baseline, 2),
            "ttf_readings": round(ttf, 1) if ttf is not None else None,
            "ts": reading["ts"],
            "seed": seed,  # one-line seed the agent's expander consumes
        }


if __name__ == "__main__":
    import random

    from sim.machine import Machine, run_line

    random.seed(0)
    line = [Machine(f"M{i}") for i in range(1, 4)]
    detector = ZScoreDetector()

    fired = []
    for reading in run_line(line, ticks=40, fault_at=18, fault_machine=line[1]):
        for event in detector.observe(reading):
            fired.append(event)
            print(event["seed"])

    from collections import Counter

    flagged = {event["machine_id"] for event in fired}
    assert flagged == {"M2"}, f"expected only M2, got {flagged or 'nothing'}"
    # Edge-trigger is the slice's headline behaviour: each sensor episode fires
    # exactly once, never re-fires on the same ongoing fault.
    per_sensor = Counter((event["machine_id"], event["sensor"]) for event in fired)
    assert all(count == 1 for count in per_sensor.values()), f"re-fired: {dict(per_sensor)}"
    ttfs = [e["ttf_readings"] for e in fired if e["ttf_readings"] is not None]
    assert ttfs, "no time-to-failure estimate produced"
    # Non-None isn't enough — a wrong-but-present number is the demo-embarrassing case.
    # Every reported horizon must be non-negative and within the credible bound.
    assert all(0 <= t <= MAX_HORIZON for t in ttfs), f"implausible TTF: {ttfs}"
    print(f"# self-check OK: only M2 flagged, once per sensor ({len(fired)} event(s)); TTFs {ttfs}")
