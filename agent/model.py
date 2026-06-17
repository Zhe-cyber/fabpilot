"""The model swap point — single source of truth (see DECISIONS.md D-002).

Isolated here so changing the engine's model (e.g. to Fable 5 for a live demo)
is a one-line edit and never leaks across the codebase. Do not hardcode a model
id anywhere else.
"""

MODEL = "claude-opus-4-8"  # reliable workhorse; no dependency on Fable 5
EFFORT = "xhigh"           # recommended for agentic work on Opus 4.7+ / Fable 5
