"""FabPilot autonomous loop — first slice.

seed -> expand into a plan -> execute it (tool-using, budget-capped) -> log.

Decoupled from MQTT: the seed is any one-line instruction. Run inside a git
worktree sandbox (DECISIONS.md D-009). Bash is left out of the allow-list, so the
SDK denies it by default — the executor can read/write/edit files, nothing more.
Auth and cost draw on the Claude Code login / Pro Agent-SDK credit; set
ANTHROPIC_API_KEY to use the API instead. The per-run budget cap is the backstop.

Run:  python -m agent.loop "Create hello.txt with one line: FabPilot online."
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from agent.expander import expand
from agent.model import EFFORT, MODEL

RUN_LOG = Path("runs/loop_log.jsonl")
MAX_TURNS = 12
MAX_BUDGET_USD = 0.50  # hard per-run cap; protects the Pro Agent-SDK credit


async def run(seed: str) -> dict:
    """Expand `seed`, execute the plan under caps, log cost + decision, return it."""
    plan = await expand(seed)
    print(f"=== PLAN ===\n{plan}\n=== EXECUTING ===")

    record = {"ts": datetime.now(timezone.utc).isoformat(), "seed": seed, "plan": plan}
    try:
        async for msg in query(
            prompt=f"Execute this plan. Do only what it says — be lazy (YAGNI).\n\n{plan}",
            options=ClaudeAgentOptions(
                model=MODEL,
                effort=EFFORT,
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],  # no Bash
                permission_mode="acceptEdits",
                setting_sources=["project"],  # loads CLAUDE.md + the ponytail skill
                max_turns=MAX_TURNS,
                max_budget_usd=MAX_BUDGET_USD,
            ),
        ):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        print("·", block.text.strip()[:200])
            elif isinstance(msg, ResultMessage):
                record |= {
                    "subtype": msg.subtype,  # success / error_max_turns / error_max_budget_usd / ...
                    "decision": msg.result if msg.subtype == "success" else None,
                    "num_turns": msg.num_turns,
                    "cost_usd": msg.total_cost_usd,
                }
    except Exception as exc:
        # Auth/network/transport errors surface as exceptions, not a ResultMessage.
        # Record the truth rather than logging a half-record that looks complete.
        record |= {"subtype": "exception", "decision": None, "error": str(exc)}
    record.setdefault("subtype", "incomplete")  # no terminal message and no exception

    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(
        f"\n=== DONE ({record.get('subtype')}) "
        f"cost=${record.get('cost_usd')} turns={record.get('num_turns')} ==="
    )
    return record


if __name__ == "__main__":
    # Agent output may contain non-ASCII; force UTF-8 so the Windows console
    # (cp1252) can't crash a run on a stray glyph.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # Running this with the default seed is the slice's smoke test.
    seed = " ".join(sys.argv[1:]) or "Create hello.txt with one line: FabPilot loop online."
    asyncio.run(run(seed))
