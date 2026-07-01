# FabPilot — Backlog

> The approved work queue. The lead pulls the top **unblocked** item, drives it to a
> reviewed commit, then stops. Nothing gets built that isn't here or explicitly asked
> for — this is the guardrail that lets the team work without freelancing. You re-sort
> priority anytime; the order below is the lead's recommendation, not a mandate.

## Now (top of queue)

- [ ] **Tier 1: multi-agent reroute negotiation** — *lead + domain-researcher + practice-scout.*
  The networking moat (D-017): per-machine agents negotiate a reroute over the bus.
  This is the trigger to extract the `fabpilot` action server into a **standalone MCP
  server** (see D-018 note / MCP discussion) — do it here, where it's load-bearing.
  *Done when:* two agents coordinate a reroute without a human; reasoning is logged
  and showable. Reviewed. Scout-checked before starting.

## Later

- [ ] **Deployment / real-data story** — makes it real beyond the sim (D-017 lever 4).
- [ ] **Lightweight knowledge-grounding** for the agent (D-017 lever 5).
- [ ] **Pitch deck + quotable one-liner** — *pitch-review.* README now tells the
  architecture story; the actual deck/summary is still to build.

## Parked (explicit — do not start without re-approval)

- **Reusable SOP / starter-kit extraction** — paused by the builder ("wait a bit messy
  right now"). Revisit when the builder re-initiates.
- **Standalone MCP server extraction** — not now; trigger is Tier 1 above (premature
  otherwise, per the MCP-level discussion).
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
