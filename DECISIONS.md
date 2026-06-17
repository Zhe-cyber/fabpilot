# Decisions Log

> Running record of design decisions and *why*. Feeds the pitch, the live Q&A, and
> the mandatory AI-usage disclosure. Newest at the top. Each entry: what we decided,
> why, and what we rejected.

---

## 2026-06-17 — Phase 0: foundation locked

### D-001 Build a reusable loop engine; FabPilot is its first application
- **Decision:** Two layers — a generic `loop-engine/` (expand → execute → audit →
  act → loop) with FabPilot built on top as the first app.
- **Why:** Serves both goals at once — a personal reusable engine *and* the
  competition deliverable — without them competing for time.
- **Critical constraint:** Build FabPilot's loop *concretely first*, then
  **extract** the reusable core. Abstraction is earned from one real use, never
  designed up front. Protects the competition timeline.
- **Rejected:** Building the generic engine first (classic yak-shave / premature
  abstraction with a single user).

### D-002 Model: Opus 4.8, no dependency on Fable 5
- **Decision:** `claude-opus-4-8`, `effort="xhigh"`, isolated in one swappable
  constant (`agent/model.py`).
- **Why:** Opus 4.8 is the reliable workhorse (~4× less likely to let code flaws
  through than 4.7). Fable 5's availability is contested (reported pulled within
  ~72h of release) and it is costly/slow — unsafe to architect a dependency on for
  a repo judged months out. The constant lets us point at Fable 5 for a demo if
  it's live, without a rewrite.
- **Rejected:** Building on Fable 5 as the core model.

### D-003 The loop's seed is an *anomaly event*, not a build instruction
- **Decision:** For FabPilot, the engine's input is a detected anomaly; the
  expansion produces a maintenance/reroute *decision*, and the agent acts on it.
- **Why:** Track 4 rewards autonomous detect→reason→act on telemetry, not
  general-purpose code generation. "One sentence builds an app" is the wrong
  capability for this track and the most fragile thing to demo live.
- **Rejected:** Making "one-sentence → full build" the product goal (kept only as a
  separate engine demo config).

### D-004 Three-pass review separation
- **Decision:** `scope-guard` (should this feature exist in this tier?) →
  **ponytail** `full`, auto `Stop`-hook (is this the least code?) → `code-reviewer`
  (is it correct?). Ponytail strips logged here.
- **Why:** Each answers a different question; no overlap. Attacks the autonomous
  loop's real failure mode (over-engineering) while keeping correctness gated.
- **Rejected:** Running ponytail *and* Code-Simplifier (they fight); installing the
  Karpathy skill (overlaps scope-guard + the anti-sycophancy directive).

### D-005 Anti-sycophancy as an always-on default + Devil's Advocate on demand
- **Decision:** Standing directive in `CLAUDE.md` (always loaded) for default
  pushback; **Devil's Advocate** plugin for explicit red-team stress-tests of big
  decisions.
- **Why:** A skill only fires when invoked — the always-on behaviour must live in
  CLAUDE.md. Devil's Advocate uses an independent subagent to avoid self-bias.

### D-006 Self-improving skills: lightweight loop now, SkillOpt parked
- **Decision:** Use `skill-creator` + a manual `LESSONS.md` → skill-refinement loop.
  **Park SkillOpt.**
- **Why:** SkillOpt is a research *method* (not a product), needs a labelled
  train/validation eval set we don't have, and its rollout loop is too costly to
  run meaningfully on the Pro plan. The golden-scenario harness (D-008) becomes the
  eval set if we ever revisit SkillOpt.

### D-007 Security: built-in `/security-review` + one STRIDE architecture pass
- **Decision:** Use the built-in `/security-review` on diffs ongoing; do one STRIDE
  pass on the engine's attack surface (see `docs/THREAT_MODEL.md`). No heavy
  multi-phase security toolkit.
- **Why:** An autonomous agent that runs `Bash` and acts on external telemetry has
  a real attack surface (prompt injection, command execution). Threat-modeling it
  is both hygiene and a differentiation/pitch point for a systems/networking entrant.

### D-008 Three engineering essentials baked in from the start
- **Decision:** (1) **Sandbox** the autonomous loop (git worktree or container;
  scope `Bash(...)` rules; isolate `bypassPermissions`). (2) **Cost/decision
  logging** from each `ResultMessage` (`total_cost_usd` + decision). (3) A tiny
  **golden-scenario harness** (3–5 scripted faults → expected actions).
- **Why:** Safety (1), Pro-budget protection + a demo "what it decided & cost"
  panel (2), and a bulletproof, regression-tested demo (3). Each also doubles as
  competition-scoring material.

### D-013 Anomaly detector: frozen-baseline z-score with persistence (2026-06-17)
- **Decision:** Per machine+sensor, learn a healthy baseline (mean/std) from a
  warmup window, **freeze** it, and flag readings > `threshold` sigma. Require
  `persistence` consecutive crossings to fire — and the same number of clear
  readings to re-arm (symmetric) — edge-triggered so the agent loop runs once per
  fault episode, not per tick.
- **Why:** Faults are progressive; a trailing window would absorb the rising trend
  and stop alerting on a visibly degrading machine. Persistence rejects single-
  sample noise spikes (testing caught a real +4.1σ false positive on a healthy
  machine). Symmetric re-arm stops a noisy mid-fault dip from double-invoking the
  costly agent loop. The emitted `seed` string feeds the existing expander/loop.
- **Deferred (YAGNI):** EWMA / adaptive baseline; per-message error handling at the
  MQTT boundary (add when the bus exists, not before).

### D-012 Approach check vs. current practice — validated, two upgrades queued (2026-06-17)
- **Habit adopted:** at each phase boundary, run an "approach check" against current
  official *and* community/industry sources, and log drift or better options here.
  Keeps us deliberately current (and is honest AI-disclosure material).
- **Verdict this round:** our loop maps onto the recognized 2026 agentic pattern
  catalog — **Planning** (expander) + **Tool Use** (executor) + **Reflection**
  (code-reviewer / ponytail-review) — and onto the production checklist:
  **Bounded Execution** (turn/budget caps ✓), **Guardrail Layering** (allow-list +
  permission mode + planned PreToolUse ✓), **Trajectory Logging** (runs/log ✓).
  The minimalist "simplest pattern first, add only on a real failure mode" rule we
  follow via ponytail/scope-guard is explicitly the recommended discipline.
- **Upgrades queued (adopt when we wire real actions — NOT now, YAGNI):**
  1. **Typed custom tools (MCP)** for actions (`schedule_maintenance`, `reroute_job`)
     via `create_sdk_mcp_server`/`@tool`, replacing generic file/Bash tools. Add
     input validation + structured error returns (LLMs call tools with wrong args).
     Kills threat T2 and makes the demo cleaner.
  2. **Structured outputs** for the expander's plan, replacing markdown parsing.
- **Watch item (Microsoft, BUILD 2026):** ~65% of agent failures are *context
  drift*, not model capability. As the loop runs longer, invest in context
  engineering (hierarchical memory / compaction, fuller trajectory logging).
- **Framing to exploit (industry consensus):** "an agent is not a prompt — it's a
  distributed system where the LLM is the planner/executor." Direct fit for a
  networking/systems entrant; use it in the pitch.
- **Reference shelf (community / other companies):** Anthropic *Building Effective
  AI Agents* (patterns); Microsoft Agent Framework 1.0 (open-source, MCP-native);
  muratcankoylan/agent-skills-for-context-engineering; Anthropic-curated skills
  (test-driven-development, systematic-debugging). Reference, not dependencies.

### D-011 Ponytail vendored as a local skill, not a marketplace plugin (2026-06-17)
- **Decision:** Install ponytail (`ponytail` + `ponytail-review`) by copying its
  MIT-licensed SKILL.md files into `.claude/skills/`, not via `/plugin`.
- **Why:** The `/plugin` command wasn't available in the builder's client, and
  community plugins aren't in the default marketplace UI. Local skills load
  automatically (like the existing skills), are version-controlled in our own repo,
  carry no external-marketplace dependency, and are cleaner for a judged portfolio.
  License preserved at `.claude/skills/ponytail/LICENSE`.
- **Note:** Wiring `ponytail-review` into the loop's `Stop`-hook (D-004) is a
  Phase 1 task; the skill itself is now available.

### D-010 Project name: FabPilot (2026-06-17)
- **Decision:** Name the project **FabPilot** (was working title "FabSentinel").
- **Why:** Keeps "Fab" as an instant semiconductor signal for Track 4 judges, but
  "Pilot" foregrounds *autonomous control / action* — the actual scoring moment —
  instead of "Sentinel," which reads as passive watching/alerting.
- **Rejected:** FabSentinel (leans "watch"), Foreman (clashes with the dev tool in
  search), Augur (not obviously manufacturing).

### D-009 Structure & sandbox resolved (2026-06-17)
- **Dedicated repo:** `git init` at the project root (was previously inside the
  home-directory git repo at `C:/Users/yyzhe` — a public-repo exposure risk).
  `.gitignore` added to keep secrets/artifacts out (mitigates T3).
- **Nesting flattened:** the redundant `maic-nexus-system/maic-nexus-system/`
  wrapper is gone; single clean project root.
- **Sandbox = git worktree** for the autonomous loop (enough isolation for a solo
  demo, no Docker overhead). To be wired in Phase 1.
