# FabPilot — Backlog

> The approved work queue. The lead pulls the top **unblocked** item, drives it to a
> reviewed commit, then stops. Nothing gets built that isn't here or explicitly asked
> for — this is the guardrail that lets the team work without freelancing. You re-sort
> priority anytime; the order below is the lead's recommendation, not a mandate.

## Now (top of queue)

- [ ] **Tier 1 · Slice B — integrate reroute into the live pipeline** — *lead.*
  Wire the bus reroute (Slice A, `agent/fleet.py`) to the LLM decision + dashboard:
  when the agent decides M2 needs rerouting, publish a real request → bidders answer →
  the arbiter awards and records via the existing `reroute_job` tool → show the
  request/bid/award on the dashboard.
  *Done when:* the live pipeline triggers a bus reroute with no human, shown in the UI.
  Reviewed. (Naturally exercises Slice A's bus round-trip over a real broker — closes
  the verify-pending-broker caveat below.)

## Later

- [ ] **Deployment / real-data story** — makes it real beyond the sim (D-017 lever 4).
- [ ] **Lightweight knowledge-grounding** for the agent (D-017 lever 5).
- [ ] **Pitch deck + quotable one-liner** — *pitch-review.* README now tells the
  architecture story; the actual deck/summary is still to build.

## Parked (explicit — do not start without re-approval)

- **Reusable SOP / starter-kit extraction** — paused by the builder ("wait a bit messy
  right now"). Revisit when the builder re-initiates.
- **Standalone MCP server extraction** — not now, and **no longer triggered by Tier 1**
  (the scout confirmed Tier 1's distribution lives on the MQTT bus, not the MCP
  transport; in-process `ACTION_SERVER` suffices — D-023). Trigger is only if a
  genuinely separate process ever needs those tools.
- **Git worktree sandbox** (D-009) — decided, not yet implemented. Low priority.

## Done (recent)

- [x] Phase 3 slice 1: quantitative time-to-failure (RUL) + review closeout (D-018).
- [x] Add `practice-scout` teammate (D-019).
- [x] Team charter (`TEAM.md`) + this backlog.
- [x] Public README telling the MCP/MQTT/agent-loop architecture story — reviewed for
  factual accuracy against the code (consumer-first ordering fixed, audit-trail claim
  tightened to the real demo files).
- [x] Live dashboard (`dashboard/`) — SSE streams detect→reason→act to the browser;
  verified end-to-end and reviewed. Fixes from review: a mid-run error now ends
  *visibly* (no frozen page), non-serializable events degrade to text, malformed
  agent actions render safely.
  *Deferred nice-to-haves (only if we touch it again):* late-joining clients get no
  state snapshot (dashboard is single-session); rebuild the agent feed entry from DOM
  nodes instead of innerHTML to remove XSS reasoning entirely (escaping is correct today).
- [x] Golden-scenario harness (`evals/golden_scenario.py`) — locks the deterministic
  sim→detect→forecast backbone (exact anomaly sequence), quarantines the LLM behind
  opt-in `--live`. Reviewed. Review fix: hoisted the scenario into `sim/scenario.py`
  as one shared source so the demo and the test can't drift; guarded `--live` against
  an empty-events crash.
- [x] Tier 1 · Slice A — reroute coordination on the bus (`agent/fleet.py`). Contract-net
  request→bid→award over MQTT; deterministic arbiter (healthier machine wins). Reviewed;
  arbiter logic verified. Review fixes: hardened the arbiter against malformed bids
  (no crash), closed the subscribe race by construction (on_subscribe Events, not
  sleeps), request-publish failure degrades gracefully.
  ⚠️ **Verify-pending-broker:** the over-the-bus round-trip was NOT run live (Docker
  wouldn't start this session). Run `docker compose up -d && python -m agent.fleet` to
  confirm M1/M3 bid and the healthier wins; Slice B will also exercise it.
