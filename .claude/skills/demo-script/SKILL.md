---
name: demo-script
description: >
  Builds and refines the demo video script and the live on-stage demo flow for
  FabPilot. Use this skill whenever I'm working on the demo video, planning what
  to show judges, scripting a walkthrough, deciding the demo sequence, or worrying
  about the live demo going wrong. Also use it when I ask "what should I show", "how
  do I demo this", or "what if the live demo breaks". The demo carries real scoring
  weight and is the moment judges remember — so engage whenever a demonstration is
  being planned or rehearsed.
---

# Demo Script

The demo is where a monitoring agent stops being a claim and becomes undeniable.
Your job: make the autonomy *visible* and the run *safe*.

## The one rule

Show, don't tell. The peak moment is a judge watching the agent detect a fault,
explain its reasoning on screen, and reroute the line — with no human touching
anything. Build the whole demo around that beat.

## Structure (target 2–3 minutes for video; same arc live)

1. **Hook (10–15s):** the problem in one breath — a line running normally, then the
   stakes ("when a machine fails unplanned, the whole line stops").
2. **The system at a glance (20s):** the dashboard with live telemetry flowing.
   Name the autonomy promise once: "no human in this loop."
3. **The money shot (45–60s):** inject a fault. Narrate what the judges see — the
   anomaly flagged, the agent's reasoning surfacing, the prediction, then the
   autonomous reroute + maintenance schedule. Let a beat of silence land it.
4. **The depth signal (20s):** one sentence on the hard part (networking/streaming/
   agent coordination) for credibility, then the tiered roadmap in a line.
5. **Close (10s):** the line is running again, untouched. "It fixed itself."

## When invoked, do this

- Produce a shot-by-shot script: on-screen action + exact narration + duration.
- Mark the single most important 5 seconds and protect it (clean framing, no
  clutter, readable text).
- For a **live** demo, always design a **fallback**: a pre-recorded clip or a
  deterministic "demo mode" seed so a flaky live run can't sink you. Rehearsal plan
  included. Solo means no one else can save a broken demo — so this is non-optional.
- Keep on-screen text large and legible; judges watch from a distance or on a
  compressed video.

## Output format

```
## Demo Script — FabPilot (<video | live>)
[00:00–00:12] HOOK
  Screen: ...
  Say: "..."
...
### Fallback plan
- ...
### Rehearsal checklist
- [ ] ...
```

## Tone

Calm and confident. The drama comes from the autonomous action, not from
adjectives. Practice until the narration is muscle memory.
