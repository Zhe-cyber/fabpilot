"""Estimate time-to-failure from a sensor's recent trend (quantitative RUL).

The market's headline predictive-maintenance capability is a number, not a vibe
(DECISIONS.md D-017): "how long until this fails?". We give a deliberately simple,
defensible answer — fit a line to the sensor's recent readings and project when it
crosses a domain failure threshold. Not an LSTM; an honest first-order
extrapolation that turns the agent's "predict time-to-failure" from qualitative
text into a figure it can reason about. Stdlib only (statistics.linear_regression).
EWMA / ML-based RUL is a documented later upgrade.

Known limitation (own it in Q&A): the fit window can still hold pre-fault flat
readings at the moment an anomaly first fires, which shallows the slope and makes
the estimate err *long* (optimistic). Treat the figure as an order-of-magnitude
horizon for prioritising, not a precise countdown.
"""

from __future__ import annotations

import statistics

# Domain failure thresholds. Vibration: ISO 10816 "unacceptable" zone (~7.1 mm/s).
# Temperature/current: plausible trip points above nominal. Tune per real asset.
FAILURE_THRESHOLDS = {"vibration": 7.1, "temperature": 80.0, "current": 14.0}

# Longest horizon we'll report. A near-flat slope from ordinary noise can project
# millions of readings ahead — technically positive, but not a credible trend. Past
# this we say "no ETA" instead of surfacing a nonsense countdown to the agent/demo.
# ~25x the 8-reading fit window: anything further out is noise, not a timeable fault.
MAX_HORIZON = 200.0


def time_to_failure(points: list[tuple[float, float]], threshold: float) -> float | None:
    """Readings until the trend reaches `threshold`.

    `points` is [(index, value), ...] in observation order. Returns a non-negative
    reading count, 0.0 if already at/over the threshold, or None when there is no
    credible ETA (fewer than 2 points, a flat/declining trend, or a horizon so far
    out — see MAX_HORIZON — that it's noise, not a trend). Uses only the raw points
    and the domain threshold; independent of the detector's z-score baseline.
    """
    if not points:
        return None
    current = points[-1][1]
    if current >= threshold:
        return 0.0  # already in the failure zone, regardless of trend
    if len(points) < 2:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if len(set(xs)) < 2:
        return None  # linear_regression needs variance in x; constant x = no trend
    slope, _ = statistics.linear_regression(xs, ys)
    if slope <= 0:
        return None  # not trending toward failure
    eta = (threshold - current) / slope
    return eta if eta <= MAX_HORIZON else None  # reject noise-driven absurd horizons


if __name__ == "__main__":
    rising = [(i, 2.0 + 0.33 * i) for i in range(11)]  # ~0.33/reading toward 7.1
    eta = time_to_failure(rising, 7.1)
    assert eta is not None and 5 < eta < 8, eta  # from last value ~5.3, ~5.5 readings
    assert time_to_failure([(i, 2.0) for i in range(11)], 7.1) is None  # flat -> no ETA
    assert time_to_failure([(i, 8.0) for i in range(11)], 7.1) == 0.0   # already failed
    assert time_to_failure([(5, 2.0), (5, 3.0)], 7.1) is None           # constant x -> guarded
    tiny = [(i, 2.0 + 1e-6 * i) for i in range(11)]                      # near-flat noise slope
    assert time_to_failure(tiny, 7.1) is None                           # absurd horizon -> no ETA
    # Flat prefix then a rise: the flat points shallow the slope, so the estimate
    # errs long vs the active-fault trend. Owned, documented bias (see module docstring).
    mixed = [(i, 2.0) for i in range(8)] + [(8 + j, 2.5 + 0.5 * j) for j in range(4)]
    biased = time_to_failure(mixed, 7.1)
    assert biased is not None and biased > 0, biased
    print(f"# self-check OK: eta={eta:.1f}; mixed-window eta={biased:.1f} (errs long, by design)")
