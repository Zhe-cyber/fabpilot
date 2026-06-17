# MAIC Nexus Challenge 2026 — Your Claude System

A personal operating system for building a standout T4 (Smart Manufacturing &
Semiconductors) project solo, and placing as a finalist.

Built around one idea: **the model is not your edge — your configuration layer
is.** Everyone in this competition has Claude. The people who stand out have
turned Claude into a disciplined system that knows their project, checks its own
work against the judges' criteria, and frees them to think instead of re-explain.

---

## 1. Who this is built for

- **You:** computer systems & networking student, solo entrant.
- **Goal:** a standout portfolio project + finalist placement (NOT primarily the
  equity prize — that changes the priorities; yours favour technical depth,
  differentiation, and a memorable demo).
- **Stack:** Python (agent + simulation + detection), JS/CSS (dashboard), with
  networking fundamentals as your unfair advantage.
- **Plan:** Claude Pro — Chat, Cowork, and Code all available in the desktop app.
- **Time:** ~20 hrs/week. That is a serious, real budget. Treat it like a part-time
  job with weekly milestones.

---

## 2. The project: a tiered build

**FabPilot** — an autonomous predictive-monitoring agent for a manufacturing line.
The name keeps the semiconductor "Fab" signal while "Pilot" foregrounds the point:
the agent autonomously *controls* the line, it doesn't just watch it.

The whole design is *tiered* so you can stop at a finalist-worthy core and extend
only if time and energy allow. Each tier is a complete, demoable product on its own.

### Tier 0 — Core (your finalist baseline; build this first, fully)
- Simulate one production line of 3–5 machines emitting sensor telemetry
  (vibration, temperature, current draw) over **MQTT**.
- A Python service ingests the streams and runs anomaly detection
  (start statistical: rolling z-score / EWMA; add a light ML model only if easy).
- An **LLM agent** interprets detected anomalies, predicts time-to-failure, and
  **acts autonomously**: schedules maintenance and reroutes the affected job.
  The autonomy is the point — the track rewards agents that decide and act, not
  dashboards that merely alert.
- A web dashboard (JS/CSS + WebSocket) shows live streams and the agent's
  decisions and reasoning in real time.
- **Demo moment:** inject a fault live; judges watch the agent detect it, explain
  its reasoning, and reroute the line — unattended.

### Tier 1 — Stretch: multi-agent orchestration
- One agent per machine/station; agents negotiate to reroute work around a
  bottleneck or failure. Distributed-systems + networking + agentic AI fused.
- **Demo moment:** "kill" a node mid-run; the survivors renegotiate routing live.

### Tier 2 — Stretch: edge hierarchy
- Simulated edge nodes run local detection and escalate *only meaningful events*
  to a central reasoning agent — a bandwidth-efficiency / edge-AI story.
- **Demo moment:** show noise filtered at the edge, only real anomalies bubbling up.

> Architect Tier 0 with clean interfaces (a message bus, a pluggable detector, an
> agent that reads from a queue) so Tiers 1–2 slot in without a rewrite. That is
> what "scalable from small to big" means in practice.

A semiconductor framing (wafer-test yield instead of generic machines) is an easy
swap if you want stronger "national bet" resonance — same architecture.

---

## 3. How the three Claude surfaces fit

You don't pick one; you use each for what it's best at. Skills and memory follow
you across all three, so it feels like one system.

| Surface | Use it for |
|---|---|
| **Claude Code** | Building FabPilot: the simulation, MQTT layer, detector, agent loop, dashboard, and your repo. Your `CLAUDE.md`, skills, and subagents live here. |
| **Claude Cowork** | The submission artifacts: pitch deck, written project summary, demo video script, the AI-usage disclosure. Knowledge-work that isn't raw coding. |
| **Claude Chat** | Thinking, deciding, unblocking, architecture debates, quick checks. Your sounding board (this conversation is an example). |

**Pro plan note:** agentic work in Code and Cowork burns through usage faster than
chat. Watch Settings → Usage, and do heavy autonomous runs in focused blocks rather
than leaving an agent looping in the background.

---

## 4. The configuration layer (what's in this kit)

```
maic-nexus-system/
├── SYSTEM_GUIDE.md        ← you are here
├── CLAUDE.md              ← project memory; copy into your repo root
└── .claude/
    ├── skills/            ← reusable workflows (work in Code, Cowork, and Chat)
    │   ├── scope-guard/   ← keeps you inside the current tier; kills scope creep
    │   ├── judge-eval/    ← scores your work against the judging rubric
    │   ├── pitch-review/  ← sharpens the deck + written summary
    │   ├── demo-script/   ← builds the demo video + live-demo flow
    │   └── qa-drill/      ← fires judge-style Q&A at you, in English
    └── agents/            ← subagents (isolated context; Claude Code)
        ├── code-reviewer.md     ← reviews for the "systematic quality" judges reward
        └── domain-researcher.md ← researches predictive maintenance / fab topics
```

**Setup:** copy `CLAUDE.md` and the `.claude/` folder into your project repo root.
In Claude Code, the memory loads automatically and skills become available as
`/skill-name`. Skills also work in Cowork and Claude.ai when stored in
`~/.claude/skills/` (global) — so you can put the writing/pitch skills there to
reach them everywhere.

---

## 5. How to actually work (the daily loop)

1. **Start in plan mode, not code.** Tell Claude the milestone; let it propose a
   plan; you approve. Prevents the "wrote 600 lines in the wrong direction" trap.
2. **Build the slice.** Keep it to one component at a time (the bus, the detector,
   one agent). Use `scope-guard` if you feel the urge to gold-plate.
3. **Review before moving on.** Run the `code-reviewer` subagent. The judges valued
   reliable, reviewable code over raw speed — bank that quality as you go.
4. **Score against the rubric weekly.** Run `judge-eval` on your current state to
   see where you'd lose points *now*, while there's time to fix it.
5. **Log it.** Keep a `DECISIONS.md` of why you chose things — gold for the pitch,
   the Q&A, and the AI-usage disclosure.

---

## 6. The submission checklist (don't lose easy points)

From the application requirements — confirm against the official page, but plan for:

- [ ] **Working prototype** (Tier 0 complete, demoable end-to-end)
- [ ] **Public code repository** (must be accessible during judging — keep it clean,
      with a strong README; your repo *is* part of the portfolio payoff)
- [ ] **Pitch deck** (PDF) — use `pitch-review`
- [ ] **Written project summary** — use `pitch-review`
- [ ] **Demo video** — use `demo-script`
- [ ] **AI-usage disclosure** (mandatory) — a well-documented, sophisticated Claude
      workflow reads as *serious engineering*, not a shortcut. Don't undersell it.
- [ ] **English** throughout (materials + live presentation)

---

## 7. Timeline (≈20 hrs/week)

**Now → June bootcamp — Foundation & practice.**
Register before the early-bird deadline. Set up this kit on a *throwaway* practice
repo first to get fluent with the skills/subagents before the stakes rise. Lock the
project scope (Tier 0 spec). Stand up the MQTT + simulation skeleton.

**Bootcamp → Online Preliminary — Build Tier 0.**
Complete the core end-to-end. Run `code-reviewer` continuously and `judge-eval`
weekly. Start the README and `DECISIONS.md` early. Produce the prelim artifacts.

**Preliminary → Semi-Finals (Sept, in-person KL) — Harden + start a stretch tier.**
Polish Tier 0 until the demo is bulletproof. If solid and time remains, add Tier 1.
Begin `qa-drill` reps — live Q&A is the solo builder's weak spot; start early.

**Semi-Finals → Finals (≈Nov, in-person KL) — Demo & pitch mastery.**
Most weight shifts to presentation. Daily `qa-drill`. Rehearse the live fault-
injection demo until it's muscle memory and has a fallback if the live run misbehaves.

---

## 8. First move

Lock the Tier 0 spec with Claude in plan mode, then build the MQTT + simulation
skeleton. Everything else hangs off a clean core. Good luck — go stand out.
