# FabPilot — Backlog

> The approved work queue. The lead pulls the top **unblocked** item, drives it to a
> reviewed commit, then stops. Nothing gets built that isn't here or explicitly asked
> for — this is the guardrail that lets the team work without freelancing. You re-sort
> priority anytime; the order below is the lead's recommendation, not a mandate.

## Now (top of queue)

- [ ] **Surface the architecture story in README + pitch** — *lead + pitch-review.*
  We already use MCP (`create_sdk_mcp_server`), MQTT, and a typed detect→reason→act
  loop and barely say so. Cheapest points on the board.
  *Done when:* README states the MCP/MQTT/agent-loop stack plainly; pitch has a line
  a judge can quote. Reviewed.

- [ ] **Live dashboard (showable reasoning)** — *lead.*
  The demo is the moment judges remember; CLAUDE.md requires the agent's reasoning be
  *showable* live. JS/CSS + WebSocket pushing telemetry streams + the agent's
  decisions.
  *Done when:* a browser page shows live machine streams and each anomaly → the
  agent's reasoning → the action it took. Runs end-to-end. Reviewed.

## Next

- [ ] **Golden-scenario test harness** (D-008 essential #3) — *lead + code-reviewer.*
  A fixed, seeded fault scenario with expected detections/actions, so we can prove the
  system works the same way every time — kills "fragile live demo" risk.
  *Done when:* one command replays a canned scenario and asserts the expected anomaly
  + action sequence. Reviewed.

- [ ] **Tier 1: multi-agent reroute negotiation** — *lead + domain-researcher + practice-scout.*
  The networking moat (D-017): per-machine agents negotiate a reroute over the bus.
  This is the trigger to extract the `fabpilot` action server into a **standalone MCP
  server** (see D-018 note / MCP discussion) — do it here, where it's load-bearing.
  *Done when:* two agents coordinate a reroute without a human; reasoning is logged
  and showable. Reviewed. Scout-checked before starting.

## Later

- [ ] **Deployment / real-data story** — makes it real beyond the sim (D-017 lever 4).
- [ ] **Lightweight knowledge-grounding** for the agent (D-017 lever 5).

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
