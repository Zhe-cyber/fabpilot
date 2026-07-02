# Decisions Log

> Running record of design decisions and *why*. Feeds the pitch, the live Q&A, and
> the mandatory AI-usage disclosure. Newest at the top. Each entry: what we decided,
> why, and what we rejected.

---

## 2026-07-02 — Repo public; official competition facts verified

### D-025 Published the repo; recalibrated the plan to official dates
- **Decision:** Created **github.com/Zhe-cyber/fabpilot** (public) and pushed all
  commits. Verified the official site (maicnexus.com/en) and recalibrated planning to
  its dates, replacing SYSTEM_GUIDE estimates.
- **Official facts (fetched 2026-07-02):** Application **Jun–Aug 2026** (open call,
  300 teams; RM150 fee — **builder not yet registered**, hardest deadline on the
  board). Preliminary **Sept 2026** (online, 3 judges, unified 100-point rubric —
  rubric not public). Semi-final **Oct 2026** (live demo, KL, top 10). Grand Final
  **Nov 2026**. Submission: pitch deck + project summary + **AI-disclosure statement
  (all mandatory)**; demo video and artifact/project link **optional**. Track locked
  at submission.
- **Corrections to prior assumptions:** SYSTEM_GUIDE said semis ~Sept (actually Oct)
  and treated the public repo as a hard requirement (officially it's an *optional*
  artifact link). The repo stays public anyway — it's the portfolio payoff named in
  the project goal, the strongest optional artifact, and the off-machine backup.
- **Priority consequence:** the three *mandatory* artifacts (deck, summary,
  disclosure) are exactly the three not yet started — they outrank further feature
  work until drafted.

---

## 2026-07-02 — Competitive positioning, verified against primary sources

### D-024 The honest wedge: governed autonomy, not "first to close the loop"
- **Decision:** FabPilot's public positioning (README "Where FabPilot fits") leads with
  a *governed next step* framing, not a novelty claim: detection isn't the wedge;
  inspectable reasoning + bounded typed actions + (Tier 1) cross-machine coordination
  over a real bus is. We explicitly concede that closed-loop control already exists
  (fab FDC/R2R; Augury+MaintainX auto-work-orders) and differentiate on transparency
  and line-level coordination *on top of* proven control.
- **Why:** two research passes (domain-researcher + practice-scout) converged: the 2026
  frontier is trust/auditability, not capability. Leading with "autonomous" as a boast
  is the naive tell; leading with "governed, inspectable, bounded" answers the question
  the field is actually asking.
- **Verified against primary sources (per the standing external-reference rule):**
  - ✅ Augury + MaintainX (prnewswire, **2026-03-24**): closed-loop, but a **human
    technician still executes**; no rerouting. Safe to cite.
  - ✅ IBM **AssetOpsBench** ([arXiv 2506.03828](https://arxiv.org/pdf/2506.03828)):
    GPT-4.1 ~**65%** task completion, **no model >70%**, plan-ahead orchestration
    regresses to **46%** — independently supports our "reasoning at decision points,
    deterministic routing" design and the D-023 rejection of heavy orchestration.
- **KILLED — do not resurrect:** a scout-surfaced arXiv paper *"Bounded Autonomy: Typed
  Action Contracts and Consumer-Side Execution"* (id 2604.14723) could **not be
  verified to exist** — the fetch confabulated title/authors rather than reading a real
  page. The bounded-autonomy *concept* is fine to describe as a design principle we
  followed; **never cite that paper.** (Lesson: scout claims that map to a specific
  citation/number get verified before they enter a deliverable.)
- **Rejected:** overclaiming "first to close the loop" (false in fabs and in the PdM
  market); competing on prediction accuracy vs LSTM/physics models (D-017 — we compete
  on the governed loop + networking, not accuracy).

---

## 2026-07-01 — Tier 1: reroute coordination over the bus (contract-net)

### D-023 One-shot request→bid→award, not peer negotiation; MCP trigger detached
- **Decision (scout-driven):** Build Tier 1 as a **trimmed contract-net over MQTT** —
  the failing machine's agent broadcasts a reroute `request`; healthy machines' agents
  publish a `bid` (headroom); a **deterministic arbiter** picks the best and publishes
  the `award`. Slice A (`agent/fleet.py`) is the coordination mechanism; Slice B wires
  it to the LLM decision + dashboard. The LLM decides *that* a reroute is warranted;
  the routing math is plain code.
- **Why:** the practice-scout found strong, consistent 2026 signal that symmetric
  peer negotiation / multi-round haggling is what teams are *walking back* (~10× cost,
  fragile, hallucinates in inter-agent messages). A one-shot contract-net reads as
  genuinely distributed, leans on the networking strength, stays inspectable, and keeps
  LLM cost flat. It's the smallest thing that's real, not a gimmick.
- **Rejected (with the scout's reasons):** symmetric peer negotiation (fragile, no
  upside); full orchestrator-worker (reroute isn't breadth-first — ~15× tokens for
  nothing); blackboard/shared-state (MQTT topics already *are* the shared substrate);
  always-on per-machine LLM loops (budget burn, un-inspectable — same reason D-020
  rejected it for the dev workflow).
- **Standalone-MCP trigger DETACHED from Tier 1:** the backlog assumed Tier 1 would
  force the extraction. After reading the code, the scout confirmed it does not — the
  distribution lives on the bus, and the arbiter + agents share the in-process
  `ACTION_SERVER` fine. Deferred until a genuinely separate process needs the tools.
- **Pitch caveat to bank:** with 3 machines, "multi-agent" is a small claim by count —
  lean the story on *coordination over a real message bus with real bid messages*
  (networking), which is a genuinely different shape from Microsoft's `agentic-factory-hack`
  (a 5-agent *sequential orchestrator*), not a worse copy of it.
- **Verification caveat:** Slice A's arbiter logic is verified; the over-the-bus
  round-trip is NOT yet run live (Docker wouldn't start this session). Committed with an
  explicit verify-pending-broker note; Slice B will exercise it. Review fixes applied:
  arbiter can't crash on a malformed bid; subscribe race closed by construction
  (on_subscribe Events, not sleeps); request-publish failure degrades to "nobody available".

---

## 2026-07-01 — Golden-scenario harness (demo-safety)

### D-022 Lock the deterministic backbone; quarantine the LLM behind --live
- **Decision:** `evals/golden_scenario.py` replays the canned scenario and asserts the
  exact anomaly sequence the sim→detector→forecast layer produces (deterministic under
  a fixed seed). One command, no API, CI-safe, exit 0/1. The agent's reason→act step —
  an LLM, non-deterministic and paid — is deliberately excluded from the golden
  assertion and only exercised via an opt-in `--live` smoke.
- **Why the split:** asserting an LLM in a "must-be-identical" test makes it flaky,
  defeating the purpose. The value is precisely the separation: if a demo misbehaves,
  the harness tells you instantly whether the deterministic backbone broke or the live
  model did.
- **Review fix — single source of truth:** the scenario inputs (seed/ticks/fault) were
  duplicated in both `agent/orchestrate.py` (the demo) and the test. That's the one
  real false-confidence gap — retune the demo, and the test keeps passing green while
  validating a stale scenario. Hoisted them into `sim/scenario.py` (`canned_readings()`)
  that both consume; also guarded `--live` against an empty-events crash. Verified the
  demo dashboard still streams through the refactored path.
- **Rejected (YAGNI):** asserting the agent's specific action choices deterministically;
  a standalone per-assertion count check (already backstopped by the sequence match).

---

## 2026-07-01 — Live dashboard (the showable-reasoning demo)

### D-021 Dashboard streams the pipeline over SSE (stdlib), in-process
- **Decision:** `dashboard/` serves one page that streams detect→reason→act to the
  browser live: machine cards with telemetry + failure-threshold bars, anomalies, and
  the agent's reasoning + actions. Built on `agent.orchestrate.run(emit=...)`, a new
  seam that streams every step without duplicating the pipeline.
- **Transport = Server-Sent Events, not WebSocket.** Data flows one way (server →
  browser), so SSE is the right primitive: **stdlib-only** (`http.server`, no new
  dependency — fits the ponytail/stdlib-first rule), auto-reconnecting, no back-channel
  we'd never use. Raised and chosen over the backlog's loose "WebSocket" wording.
- **In-process pipeline, not MQTT-fed.** For the highest-stakes live moment, one
  command with no broker beats the two-terminal broker dance (and its start-order
  footgun). The MQTT distributed story is told elsewhere; robustness wins here.
- **Reviewed; the fixes were all one theme — make failure *visible*.** A mid-run error
  now ends with a visible error state instead of a frozen "running…" page; events that
  can't serialize degrade to text instead of aborting the run; malformed agent actions
  render safely. Windows SSE-disconnect tracebacks suppressed two ways.
- **Rejected (YAGNI):** the auto-trigger hook, charts library, persistence, auth, and a
  full DOM-node rewrite of the feed (escaping is correct for the current markup).

---

## 2026-07-01 — Team charter, backlog, and working rhythm

### D-020 Charter + backlog + human-gated resume (not token-sensing autonomy)
- **Decision:** Added `TEAM.md` (shared mission/vision/target + roster + collaboration
  protocol so agents act mission-aware, not as blind tools) and `BACKLOG.md` (the
  approved work queue the lead pulls from). The team works in reviewed slices, commits
  at every safe point, and resumes by pulling the next backlog item.
- **Why the rhythm, not a token-sensing loop:** the builder wished for a loop that
  works until tokens burn out and auto-resumes on recharge. The lead **cannot read
  plan quota** — no tool exposes it — so a self-sensing loop would be fiction. Instead
  the *unit of work* (small, reviewed, committed slices off a resumable queue) gives
  the same pause/resume behaviour: quota out = already at a clean commit; quota back =
  next item. Human-gated resume is also the safety rail against freelancing.
- **Dropped:** the auto-trigger hook proposed earlier — once the team-lead-loop was the
  real goal, the hook was the weakest lever and pure noise. YAGNI.
- **Rejected:** a persistent self-collaborating agent swarm for the dev workflow —
  burns budget continuously, fights the tool's on-demand design, and is un-inspectable
  (violates the project's own "reviewable" value). The autonomous multi-agent system
  the builder wants is FabPilot's *product* (Tier 1), not its dev tooling.

---

## 2026-07-01 — Team: add a practice-scout teammate

### D-019 Add a practice-scout agent to own "keep us current"
- **Decision:** New subagent `.claude/agents/practice-scout.md` whose job is to
  scout community/industry agentic-engineering practice (ponytail / Microsoft-engineer
  / Anthropic-official class) and return **Adopt / Watch / Skip** verdicts — not a
  link dump. Fills the one real gap in the team: no existing teammate owned the
  standing "keep us updated to the latest smart approach" instruction
  (domain-researcher scouts *manufacturing*, not *engineering method*).
- **Why:** The "stay current" job was falling on the main loop ad-hoc, so it only
  happened when remembered. A named teammate with a tuned prompt makes it a
  repeatable move at phase boundaries.
- **Guardrails baked in:** must force a verdict per item, must Skip things that suit
  a big team but not a solo builder, and "no change needed" is an explicit valid
  result — so the scout can't become a shiny-object generator.
- **Rejected:** Adding more teammates (tester, security agent, etc.). The rest of the
  roster already covers those via skills / built-in agents; one addition, not a
  reorg. YAGNI.

---

## 2026-07-01 — Phase 3 slice 1 review closeout

### D-018 Clamp the RUL horizon; close the missing review pass
- **Decision:** The quantitative time-to-failure slice (D-017 lever #1) got its
  code-reviewer pass late — the one it had skipped. One real bug fixed: a near-flat
  noise slope could project an absurd horizon (millions of readings), which
  `forecast.time_to_failure` now rejects via a `MAX_HORIZON = 200` bound (returns
  "no ETA" instead). Plus two cheap guards: an import-time assert that every sensor
  has a failure threshold, and a tightened detector self-check that asserts every
  reported TTF is within a sane range, not merely non-None.
- **Why:** An unbounded ETA is the worst *silent* failure here — no crash, just a
  nonsense countdown on screen in front of judges. A bound turns it into an honest
  "not credibly trending yet."
- **Rejected (KISS):** `math.isfinite` input-validation guards and defensive
  commentary the reviewer suggested — speculative gold-plating; current callers
  never pass NaN/negative thresholds. YAGNI.

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

### D-018 Quantitative time-to-failure implemented — roadmap lever #1 (2026-06-17)
- **Decision:** `detect/forecast.py` adds first-order RUL — linear-fit each sensor's
  recent trend and project to a domain failure threshold (ISO 10816 7.1 mm/s for
  vibration, etc.). The detector enriches each anomaly seed with "~N readings to the
  threshold" and a `ttf_readings` field, so the agent reasons from a number, not just
  a deviation. Stdlib only; no ML.
- **Why:** closes the biggest market gap from D-017 cheaply, and makes "predicts
  time-to-failure" literally true. Vibration (the dominant fault signature) shows the
  soonest ETA, so the agent can prioritise correctly.
- **Reviewed (code-reviewer):** guarded `linear_regression` against a constant-x
  crash; shrank the fit window (12→8) and **documented the optimistic bias** (a flat
  pre-fault prefix shallows the slope, so the estimate errs long) as an owned Q&A
  point, with a self-check that demonstrates it.

### D-017 Competitive benchmark + post-backend roadmap (2026-06-17)
- **Why this entry:** the earlier "finalist-grade" self-assessment was uncalibrated
  (placeholder rubric, no external reference). Official MAIC rubric still unavailable;
  this benchmarks against the market and hackathon-finalist bar instead. Re-score
  once the official criteria + entrant profile are in hand.
- **Market bar (real PdM products — Tractian, NodeHub, Factory AI):** wireless
  vibration/temp/acoustic sensors, supervised+unsupervised ML, **LSTM RUL at 85–95%**,
  edge compute, no-code, deployed at customers; reliable horizon 5–15 days. FabPilot
  is behind on quantitative prediction (ours is qualitative LLM text) and is simulated,
  not deployed. We do NOT compete on ML accuracy.
- **Closest reference — Microsoft `agentic-factory-hack`:** a 5-stage specialized
  multi-agent PdM pipeline (anomaly-classify → fault-diagnose → repair-plan →
  maintenance-schedule + parts-order → workflow orchestration), Azure/Foundry/Cosmos,
  MCP, with per-machine **knowledge bases** grounding diagnosis. Implication: "agent
  detects + acts" is NOT novel. Differentiation must come from execution + our angle.
- **Finalist bar (Devpost/Claude/MIT/GitLab):** "feels like a product, not a demo";
  does it work / worth doing / use again next week; production-grade needs
  **evals + guardrails + observability + deployment story**, not a slick UI. FabPilot
  is strong on guardrails/observability already; missing evals, dashboard, deployment.
- **FabPilot's moat (lean in):** real MQTT streaming/distributed pipeline + edge
  (Tiers 1–2) — a networking story the Azure-native references don't tell — and
  laptop+Docker portability (no cloud lock-in).
- **Post-backend roadmap (priority order):**
  1. **Quantitative time-to-failure** (simple trend extrapolation RUL, not LSTM) —
     closes the biggest market gap, makes "predicts failure" literally true.
  2. **Networking/edge/multi-agent differentiation (Tiers 1–2)** — the moat; escapes
     the Microsoft template.
  3. **Eval/golden-scenario harness (D-008) + dashboard** — both are named finalist
     criteria (evals + "feels like a product").
  4. **Deployment/real-data story** — "same MQTT topics map to real PdM sensors".
  5. **Lightweight knowledge-grounding** (small per-machine KB the agent reads) —
     cheaply matches Microsoft's diagnosis credibility.

### D-016 Distributed pipeline: publisher + consumer service over MQTT (2026-06-17)
- **Decision:** Split into two processes — `transport/publisher.py` (machines/edge,
  streams telemetry) and `transport/consumer.py` (central: subscribe → detect →
  agent acts). paho's network thread enqueues readings; an asyncio loop drains them
  off-thread (`asyncio.to_thread`) and awaits the budget-capped agent, so the bus
  never blocks. One agent response per machine episode.
- **Why:** Realizes the real distributed architecture (machines → broker → central
  agent) — the networking differentiation made literal. Verified across two
  processes: M2's fault detected over MQTT, agent scheduled maintenance + rerouted
  ($0.17/run).
- **Reuse:** promoted `mqtt_io._client`/`_decode` to public `make_client`/`decode_payload`.
- **Reviewed (code-reviewer):** subscribe moved into the `on_connect` callback to
  avoid a race that could silently drop early readings; added a broker-unreachable
  guard with an actionable message.

### D-015 MQTT transport: Mosquitto over Docker (2026-06-17)
- **Decision:** Telemetry flows over MQTT (paho-mqtt client, QoS 1) to a Mosquitto
  broker run via `docker compose`, topic `fabpilot/telemetry/<machine_id>`. The
  consumer feeds the same reading-dicts to the existing detector — transport is
  transparent, proving the seam that let detection be built before the bus.
- **Why:** The message bus is the architecture's backbone and the networking
  differentiation. Docker makes the broker reproducible for the judged repo
  (`docker compose up -d`). Verified: 120/120 readings round-tripped, only M2 flagged.
- **Security:** broker bound to `127.0.0.1`; anonymous/plaintext acceptable only
  because it is not network-exposed. Auth + TLS deferred (threat T4).
- **Deferred (YAGNI):** reconnection logic; TLS/auth; wiring the agent to the MQTT
  consumer (next slice — the agent currently runs off the in-process orchestrator).

### D-014 End-to-end spine: typed action tools wired to the detector (2026-06-17)
- **Decision:** The agent's "act" step uses in-process SDK MCP tools
  (`schedule_maintenance`, `reroute_job`) — input-validated, structured errors —
  not generic file/shell tools. `agent/respond.py` runs one budget-capped agent
  call per anomaly with ONLY those tools; `agent/orchestrate.py` connects
  sim → detector → respond (one response per machine episode for cost control).
- **Why:** Realizes the D-012 typed-tools upgrade. The agent can only schedule or
  reroute — nothing else — so threat T2 (shell access) is closed by construction.
  Verified end-to-end: M2's injected fault was detected, the agent assessed
  imminent bearing failure and called both tools; `runs/actions.jsonl` is the audit
  trail. Inputs are coerced/validated so bad LLM args return errors, not crashes.
- **Also:** forced UTF-8 stdout at entry points — the Windows console (cp1252)
  crashed on the sigma symbol in the agent's reasoning.
- **Deferred (YAGNI):** consumer handling of non-success records with partial
  actions; renaming the event `seed` field to `prompt`. Noted, not blockers.

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
