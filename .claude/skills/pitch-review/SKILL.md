---
name: pitch-review
description: >
  Drafts and sharpens the pitch deck and the written project summary for
  FabPilot. Use this skill whenever I'm working on the deck, the project
  summary, the elevator pitch, slide content, or any narrative explaining the
  project to judges. Also use it when I ask "is this pitch any good", "how do I
  explain this", or paste deck/summary text for feedback. The pitch and summary are
  worth real points and are the part a solo technical builder most often neglects —
  so lean in whenever narrative or persuasion is in play.
---

# Pitch Review

A technical solo builder usually has the strongest product and the weakest story.
Your job is to close that gap: make the work land with judges who decide fast.

## The narrative spine (every deck and summary follows this)

1. **The problem, made vivid.** Unplanned equipment failure on a line is expensive
   and sudden. One concrete, relatable scene beats statistics.
2. **The gap.** Existing monitoring *alerts* a human, who then reacts — slow, and it
   doesn't scale. (This sets up the wedge.)
3. **The insight.** An AI agent can *decide and act* on telemetry autonomously.
4. **The product.** FabPilot — show the agent detecting, reasoning, and rerouting
   live. Lead with the demo, not the architecture.
5. **Why it's hard / why it's me.** The networking + agentic-systems depth; the
   tiered architecture that scales from one line to a multi-agent / edge fleet.
6. **Scale & what's next.** Tier 0 → Tier 1 → Tier 2 as a credible roadmap.

## When invoked, do this

- If drafting: produce slide-by-slide content (title + 2–4 tight lines + a note on
  the visual) and a tighter written summary. Default to ~8–10 slides.
- If reviewing my draft: give specific edits, not vibes. For each slide say keep /
  cut / rewrite, and supply the rewrite.
- **Cut jargon ruthlessly.** Judges across six industries won't all be networking
  engineers. "MQTT broker" → "the live data feed from the machines." Keep one or two
  technical depth-signals for credibility; translate the rest.
- **Make the agent's autonomy the hero.** The single most differentiating sentence
  is some form of: "It doesn't alert a human — it fixes the line itself."
- **Pressure-test feasibility claims.** Flag anything a sharp judge would poke
  ("you simulated the data — does it work on real telemetry?") and supply the honest,
  confident answer.

## Output format for a full deck

```
## Pitch Deck — FabPilot
**Slide 1 — <title>**
- <line>
- <line>
[Visual: ...]
...
## One-paragraph summary
<120–180 words, problem → insight → product → why-it-scales>
```

## Tone

Confident, concrete, plain English. No hype words ("revolutionary", "game-
changing") — judges discount them. Let the live demo and the autonomy carry the awe.
