# FabPilot

**An autonomous predictive-monitoring agent for a manufacturing line.**
MAIC Nexus Challenge 2026 · Track 4 (Smart Manufacturing & Semiconductors).

FabPilot watches simulated machine telemetry streaming over a real message bus,
detects anomalies statistically, predicts *how many readings until failure*, and
then **acts on its own** — scheduling maintenance and rerouting work — with no human
in the loop. The agent's reasoning is inspectable at every step, so you can watch it
decide, not just see the result.

---

## Architecture

A clean detect → reason → act pipeline over MQTT, designed so each stage is a
swappable seam:

```
  sim/machine.py            transport/            detect/zscore.py         agent/respond.py
 ┌─────────────┐   MQTT   ┌──────────────┐      ┌────────────────┐      ┌────────────────────┐
 │ 3 simulated │ ───────► │  Mosquitto   │ ───► │  z-score       │ ───► │  Claude agent      │
 │ machines    │  QoS 1   │  broker      │      │  anomaly       │ ───► │  (Agent SDK)       │
 │ (telemetry) │          │ (Docker)     │      │  detection +   │      │  reasons, then     │
 └─────────────┘          └──────────────┘      │  time-to-fail  │      │  calls MCP tools   │
                          publisher/consumer     └────────────────┘      └─────────┬──────────┘
                          are separate services                                    │
                                                                                    ▼
                                                                    schedule_maintenance / reroute_job
                                                                    (typed MCP tools, audit-logged)
```

### What's under the hood (and why it's not a toy)

- **Distributed transport — MQTT (paho + Mosquitto).** Machines *publish*; a separate
  *consumer service* ingests, detects, and acts. It's a genuinely distributed
  pipeline, not one script pretending — `transport/publisher.py` and
  `transport/consumer.py` are independent processes talking over a broker.
- **The agent acts through MCP.** FabPilot runs its own in-process **MCP server**
  (`agent/actions.py`, via `create_sdk_mcp_server`) exposing two *typed, validated*
  tools — `schedule_maintenance` and `reroute_job`. The agent can only take real,
  bounded actions; malformed tool calls come back as structured errors it can reason
  about, never as silent corruption.
- **Statistical detection + quantitative RUL.** A frozen-baseline z-score detector
  (`detect/zscore.py`) flags *progressive* faults and requires persistence to reject
  noise, then a first-order linear extrapolation (`detect/forecast.py`) turns
  "something's wrong" into "~N readings to the failure threshold" — a number the
  agent reasons from. Stdlib only; no ML dependency to justify.
- **Inspectable, budget-capped agent loop.** Built on the **Claude Agent SDK**
  (`agent/respond.py`). Every run is bounded (`max_turns`, `max_budget_usd`) and logs
  its reasoning to `runs/responses.jsonl` and its actions to `runs/actions.jsonl` —
  the audit trail that makes the demo *showable*.

Full rationale for every choice lives in [`DECISIONS.md`](DECISIONS.md).

---

## Quickstart

Requires **Python 3.10+** (uses `statistics.linear_regression`) and **Docker** (for
the broker).

```bash
pip install -r requirements.txt

# 1. Start the MQTT broker (Mosquitto, bound to localhost only)
docker compose up -d

# 2a. Distributed run — two terminals, the real pipeline.
#     Start the consumer FIRST: it subscribes on connect, so telemetry
#     published before it's listening is dropped (no retained messages).
python -m transport.consumer      # terminal 1: ingest → detect → act (start first)
python -m transport.publisher     # terminal 2: machines stream telemetry over MQTT

# 2b. Or the in-process end-to-end run (no broker needed):
python -m agent.orchestrate
```

Set `ANTHROPIC_API_KEY` in the environment (or sign in via Claude Code) for the agent
to run. No secrets are committed — the repo is public.

### Poke at a single stage

```bash
python -m sim.machine        # simulator self-check
python -m detect.zscore      # feed the simulator through the detector
python -m detect.forecast    # time-to-failure estimator self-check
python -m transport.mqtt_io  # publish → subscribe → detect round-trip
```

---

## Repo layout

| Path | What it is |
|---|---|
| `sim/` | Simulated machine line emitting vibration / temperature / current telemetry |
| `transport/` | MQTT publisher, consumer service, and the shared MQTT I/O helpers |
| `detect/` | Z-score anomaly detection + first-order time-to-failure (RUL) |
| `agent/` | The Claude agent: model config, action MCP server, reasoning loop, orchestrator |
| `docs/` | Threat model (STRIDE) and supporting design docs |
| `infra/`, `docker-compose.yml` | Mosquitto broker config |
| `TEAM.md`, `BACKLOG.md`, `DECISIONS.md` | How the project is built, what's next, and why |

---

## Status

**Tier 0 (core) is built and runs end-to-end:** simulate → stream over MQTT →
detect + forecast → agent reasons and acts, all inspectable. Stretch tiers (per-machine
agents that negotiate rerouting; edge-local detection) are on the roadmap — see
[`BACKLOG.md`](BACKLOG.md).

## AI-usage disclosure

FabPilot is built with Claude Code as an explicit, documented workflow — a small team
of specialised agents (review, domain research, practice-scouting) coordinated under a
written charter ([`TEAM.md`](TEAM.md)), with every design decision logged in
[`DECISIONS.md`](DECISIONS.md). The disclosure is deliberately full: a rigorous
AI-assisted process is a strength of this submission, not something to hide.
