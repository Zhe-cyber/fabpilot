"""Golden-scenario harness — proves the deterministic pipeline behaves identically
every run, so a live demo can't surprise us (D-008 essential #3; BACKLOG).

The sim -> detector -> forecast layer is deterministic under a fixed seed, so we lock
its output down as a *golden* sequence: the same anomalies, in the same order, every
run. The agent's reason->act step is an LLM — non-deterministic and paid — so it is
deliberately NOT part of the golden assertion; asserting an LLM would make this test
flaky, defeating its purpose. That separation is the point: if a demo ever misbehaves,
this tells you instantly whether the deterministic backbone broke or the live model
did. Use --live for an opt-in, paid smoke that the agent actually completes and acts.

Run:  python -m evals.golden_scenario           # deterministic checks, no API, CI-safe
      python -m evals.golden_scenario --live     # + one real agent call (needs auth, ~cents)
"""

from __future__ import annotations

import sys

from detect.forecast import MAX_HORIZON
from detect.zscore import ZScoreDetector
from sim.scenario import FAULT_AT, SEED, TICKS, canned_readings

# Golden anomaly sequence (machine, sensor) in the exact order the detector fires.
# If an *intentional* sim/detector change alters this, update it here on purpose —
# a mismatch means "the backbone changed", which is exactly what we want to catch.
# (Scenario *inputs* live in sim/scenario.py, shared with the demo so they can't
# drift; this is the expected *output* of running it — the golden test's own concern.)
EXPECTED_SEQUENCE = [("M2", "vibration"), ("M2", "current"), ("M2", "temperature")]


def run_scenario() -> list[dict]:
    """Replay the canned scenario through sim -> detector. Deterministic, no API."""
    detector = ZScoreDetector()
    events: list[dict] = []
    for reading in canned_readings():
        events.extend(detector.observe(reading))
    return events


def check_deterministic(events: list[dict]) -> list[tuple[str, bool, str]]:
    """Return (name, passed, detail) for each golden assertion."""
    seq = [(e["machine_id"], e["sensor"]) for e in events]
    machines = {e["machine_id"] for e in events}
    ttfs = [e["ttf_readings"] for e in events]
    return [
        (
            "anomaly sequence matches golden",
            seq == EXPECTED_SEQUENCE,
            f"expected {EXPECTED_SEQUENCE}, got {seq}",
        ),
        (
            "only the faulted machine (M2) fires",
            machines == {"M2"},
            f"flagged {sorted(machines) or 'nothing'}",
        ),
        (
            "every time-to-failure is sane (None or 0..MAX_HORIZON)",
            all(t is None or 0 <= t <= MAX_HORIZON for t in ttfs),
            f"ttfs {ttfs}",
        ),
        (
            "every event carries a non-empty agent seed",
            all(isinstance(e.get("seed"), str) and e["seed"].strip() for e in events),
            "one or more events missing a seed",
        ),
    ]


async def _live_smoke(event: dict) -> tuple[str, bool, str]:
    """Opt-in, paid: prove the agent actually completes and takes an action."""
    from agent.respond import respond_to_anomaly  # lazy: keep the default path API-free

    record = await respond_to_anomaly(event)
    subtype = record.get("subtype")
    actions = record.get("actions", [])
    passed = subtype == "success" and len(actions) >= 1
    return (
        "live: agent completes and acts on the anomaly",
        passed,
        f"subtype={subtype}, actions={len(actions)}",
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    events = run_scenario()
    checks = check_deterministic(events)
    if "--live" in argv:
        if not events:
            # A backbone regression to zero anomalies must not turn a paid run into a
            # bare IndexError — report it as an explicit failure instead.
            checks.append((
                "live: skipped — no anomalies to act on", False,
                "deterministic layer produced 0 events",
            ))
        else:
            import asyncio

            checks.append(asyncio.run(_live_smoke(events[0])))

    width = max(len(name) for name, _, _ in checks)
    all_pass = True
    print(f"# golden scenario: seed={SEED}, {TICKS} ticks, fault M2 @ {FAULT_AT}")
    for name, ok, detail in checks:
        all_pass &= ok
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {name.ljust(width)}"
        if not ok:
            line += f"  -> {detail}"
        print(line)
    print("# RESULT:", "all golden checks passed" if all_pass else "GOLDEN MISMATCH")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
