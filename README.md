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

## Where FabPilot fits

Predictive maintenance is a crowded market, so FabPilot is deliberate about what is
genuinely new here — and what isn't.

- **Detection isn't the novelty.** Commercial tools already do sensor-to-work-order.
  The condition-monitoring leader's newest "closed-loop" product
  ([Augury + MaintainX, March 2026](https://www.prnewswire.com/news-releases/augury-and-maintainx-partner-to-deliver-closed-loop-maintenance-execution-for-frontline-teams-302722467.html))
  still **auto-drafts a work order for a human technician to execute** — it automates
  the workflow, not the decision, and it doesn't reroute production.
- **In semiconductors, closed-loop control already exists.** FDC (fault detection &
  classification) can interdict a tool, and run-to-run control auto-adjusts recipes
  between runs. FabPilot does **not** claim to have invented closed-loop action — those
  are proven, per-tool, rule/SPC-based reflexes.
- **What FabPilot demonstrates is the *governed next step*:** an **inspectable reasoning
  layer** (you can audit *why* it acted, not just that a threshold tripped), **bounded
  typed actions** (the agent can only emit validated `schedule_maintenance` /
  `reroute_job` calls — never raw commands), and, at **Tier 1**, **coordination across
  machines over a real message bus**. The wedge is transparency + line-level
  coordination *on top of* proven control — not a claim to replace it.
- **Why "governed", not "autonomous" as a boast.** The 2026 barrier to industrial
  agents is trust and auditability, not raw capability: on IBM's
  [AssetOpsBench](https://arxiv.org/pdf/2506.03828), no agent exceeds ~70% task
  completion, and a plan-ahead orchestration style *regresses* to 46%. FabPilot answers
  that by gating the LLM behind statistical detection, keeping routing deterministic,
  and making every decision inspectable and reversible — a demonstration of the
  *governed path* to autonomy, not a claim to be trusted with a live line today.

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
