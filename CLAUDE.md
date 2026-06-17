# FabPilot — Project Memory

> This file is loaded at the start of every Claude Code session. It is the
> single source of truth about this project. Keep it current; when a decision
> changes, change it here.

## What this project is

FabPilot is an **autonomous predictive-monitoring agent for a manufacturing
line**, built for the MAIC Nexus Challenge 2026, Track 4 (Smart Manufacturing &
Semiconductors). An AI agent monitors simulated machine telemetry, detects
anomalies, predicts failures, and acts on its own — scheduling maintenance and
rerouting work — without a human in the loop.

## Goal (read this before optimizing anything)

The objective is a **standout portfolio project and a finalist placement**, not
winning the equity prize. That means: prioritize technical depth, clear
differentiation, code quality, and a memorable live demo over business polish.
When trading off, favour the choice that makes a networking/systems engineer look
impressive and the demo unforgettable.

## Builder context

- Solo entrant; computer systems & networking student.
- Strengths: networking (this is the unfair advantage — lean into MQTT, streaming,
  edge, distributed coordination), Python, JS/CSS. Comfortable in Claude Code.
- ~20 hrs/week. Optimize for steady weekly progress, not heroics.

## Architecture — tiered (build in order; each tier is a complete product)

- **Tier 0 (core, build fully first):** one line of 3–5 simulated machines emit
  telemetry over MQTT → Python ingest + anomaly detection (statistical first:
  rolling z-score / EWMA) → LLM agent interprets, predicts time-to-failure, and
  autonomously schedules maintenance + reroutes → live web dashboard (JS/CSS +
  WebSocket) showing streams and the agent's reasoning.
- **Tier 1 (stretch):** per-machine agents that negotiate rerouting (multi-agent).
- **Tier 2 (stretch):** edge nodes do local detection, escalate only meaningful
  events to a central agent (edge hierarchy / bandwidth efficiency).

Design Tier 0 with clean seams — a message bus, a pluggable detector interface, an
agent that reads from a queue — so Tiers 1–2 add on without a rewrite.

## Tech conventions

- **Language:** Python for backend/agent/sim; JS/CSS for the dashboard.
- **Messaging:** MQTT (e.g. paho-mqtt); a broker like Mosquitto. WebSocket to push
  to the dashboard.
- **Agent:** call the Anthropic API; keep the agent loop explicit and inspectable
  (the reasoning must be *showable* in the demo).
- **Style:** readable over clever. Type hints, small functions, docstrings that say
  *why*. The judges reward reliable, reviewable code over speed — so do I.
- **No secrets in the repo.** The repo will be public during judging.

## What "done" means for any task

- It runs end-to-end and is demoable.
- It's reviewed (run the code-reviewer subagent) before I call it finished.
- The decision and any tradeoff is logged in DECISIONS.md.

## How to work with me on this

- Default to **plan mode** for anything non-trivial: propose the plan, let me
  approve, then build. Don't write large amounts of code unprompted.
- Build one slice at a time. If a task is ballooning, stop and flag scope (see the
  scope-guard skill) rather than gold-plating.
- Keep the README and DECISIONS.md current as we go — they feed the pitch, the
  Q&A, and the mandatory AI-usage disclosure.

## Give it to me straight (this overrides any instinct to agree)

I am a solo entrant with limited hours; flattery costs me time and points. So:

- **Lead with your own assessment, not mine.** If I propose something weak, say so
  plainly and say why — before doing it. Don't reframe a bad idea as a good one.
- **Recommend, don't menu.** When there's a clear best option, name it and commit;
  don't hand me a neutral list of choices to avoid taking a position.
- **Surface risks, costs, and simpler alternatives unprompted** — scope creep,
  wasted spend, fragile demos, security holes, over-engineering.
- **"Don't build this" is a valid answer.** YAGNI beats gold-plating every time.
- **Never manufacture problems to look thorough, and never withhold a real one to
  be agreeable.** If something is genuinely fine, say "this is fine" and move on.
- If you catch yourself just confirming what I said, stop and pressure-test it.

## Key files

- `SYSTEM_GUIDE.md` — the overall competition playbook and timeline.
- `DECISIONS.md` — running log of design decisions and why (create if absent).
- `.claude/skills/` — reusable workflows; `.claude/agents/` — subagents.

## Hard constraints

- All deliverables and the live presentation are in **English**.
- A **public repository** must be accessible during judging.
- The **AI-usage disclosure** is mandatory — document the Claude workflow honestly
  and fully; a sophisticated setup is a strength, not something to hide.
