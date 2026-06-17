---
name: judge-eval
description: >
  Scores the current state of the FabPilot project against the MAIC Nexus
  judging criteria so weaknesses surface while there's still time to fix them. Use
  this skill whenever I ask "how am I doing", "would this score well", "what would
  judges think", before any submission deadline, after finishing a milestone, or on
  a weekly check-in. Also use it proactively at the end of a major build step. Treat
  it like running the judges' scorecard against yourself early and often.
---

# Judge Eval

Run the judges' scorecard against the project *now*, every week, so you fix gaps
while time exists instead of discovering them at submission.

## Important: use the official rubric when available

The exact criteria and weights are set by MAIC Nexus — **find them on the official
site / bootcamp materials and replace the placeholder rubric below the moment you
have them.** Until then, use this evidence-based stand-in for a deep-tech,
investable-startup hackathon:

| Criterion | Weight | What it really asks |
|---|---|---|
| Problem & impact | 20% | Real, important manufacturing problem? Clear who benefits? |
| Technical execution | 25% | Does it actually work end-to-end? Reliable, reviewable? |
| Innovation & AI use | 20% | Is the *autonomy* genuine and non-trivial? Smart use of agents? |
| Demo quality | 15% | Is the live demo clear, dramatic, and convincing? |
| Scalability & feasibility | 10% | Credible path from prototype to real deployment? |
| Pitch & communication | 10% | Told clearly, in English, by a confident presenter? |

## When invoked, do this

1. **Inventory the current state** — what exists and runs today (code, demo,
   deck, summary, video), not what's planned.
2. **Score each criterion** 1–5 with one sentence of evidence and one sentence on
   the gap to a 5. Be honest; a flattering score now costs points later.
3. **Compute the weighted total** and translate it: "today this reads as
   finalist / borderline / not yet."
4. **Rank the top 3 fixes by points-per-hour** — the cheapest moves that raise the
   score the most. For a solo builder this prioritization matters more than the score
   itself.
5. **Flag the silent killers**: is the demo bulletproof? Is the repo public and
   clean? Is the AI-usage disclosure done? These lose easy points if neglected.

## Output format

```
## Judge Eval — <date>
Overall: <weighted>/5 — reads as <finalist / borderline / not yet>

| Criterion | Score | Evidence | Gap to 5 |
...

### Top 3 fixes (by points per hour)
1. ...
2. ...
3. ...

### Silent-killer check
- Demo: ... | Repo: ... | AI disclosure: ...
```

Remember the lesson from past winners: reliable, reviewable execution scored higher
than raw speed. Weight technical solidity accordingly.
