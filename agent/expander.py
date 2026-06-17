"""Expand a one-line seed into a bounded plan — the self-expansion step.

The agent writes its own objective, acceptance criteria, and ordered steps from a
single sentence, so the executor acts on something concrete and reviewable
(DECISIONS.md D-001). Planning only: no tools, no side effects, one turn.
"""

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from agent.model import EFFORT, MODEL

# Lazy on purpose: the plan must be the smallest set of steps that satisfies the
# seed. Speculative steps are exactly what we don't want the executor acting on.
_PROMPT = """You are the planning stage of an autonomous engineering loop.
Expand the one-line SEED into the smallest bounded plan that satisfies it — no
speculative steps (YAGNI). Reply with exactly this structure and nothing else:

## Objective
<one sentence>
## Acceptance criteria
- <testable criterion>
## Steps
1. <imperative step>

SEED: {seed}
"""


async def expand(seed: str) -> str:
    """Return a structured plan for `seed`. Raises if the model produced no plan."""
    result = None
    async for msg in query(
        prompt=_PROMPT.format(seed=seed),
        options=ClaudeAgentOptions(
            model=MODEL, effort=EFFORT, allowed_tools=[], max_turns=1
        ),
    ):
        if isinstance(msg, ResultMessage):
            result = msg
    # Never swallow the SDK's subtype: a cap/error is a failure with a reason,
    # not "no plan". Surface it so the caller knows what actually happened.
    if result is None or result.subtype != "success":
        why = result.subtype if result else "no result message"
        raise RuntimeError(f"expander failed ({why}) for seed: {seed!r}")
    plan = (result.result or "").strip()
    if not plan:
        raise RuntimeError(f"expander returned an empty plan for seed: {seed!r}")
    return plan
