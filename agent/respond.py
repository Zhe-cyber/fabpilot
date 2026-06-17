"""Autonomous response to a detected anomaly — FabPilot's 'reason and act' step.

Given an anomaly event from the detector, the agent assesses the likely failure
and its urgency, then ACTS by calling the typed action tools. Its only abilities
are those tools — no file or shell access — so the worst it can do is schedule
maintenance or reroute a job. Reasoning is streamed so it is showable in the demo;
the actions taken, the reasoning, and the cost are logged. Budget-capped.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from agent.actions import ACTION_SERVER, ACTION_TOOLS
from agent.model import EFFORT, MODEL

RESPONSE_LOG = Path("runs/responses.jsonl")
MAX_TURNS = 8
MAX_BUDGET_USD = 0.50  # hard per-response cap

_SYSTEM = (
    "You are FabPilot, an autonomous maintenance agent for a production line of "
    "machines M1, M2, and M3. You receive one sensor anomaly. Briefly assess the "
    "likely failure and how urgent it is, then ACT with your tools: schedule "
    "maintenance for the affected machine, and if failure looks imminent reroute "
    "its job to a healthy machine. Be decisive and lazy — take only the actions the "
    "situation needs, then stop."
)


async def respond_to_anomaly(event: dict) -> dict:
    """Let the agent reason about `event` and act via the typed tools. Logs + returns."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "machine_id": event["machine_id"],
        "seed": event["seed"],
        "actions": [],
    }
    try:
        async for msg in query(
            prompt=event["seed"],
            options=ClaudeAgentOptions(
                model=MODEL,
                effort=EFFORT,
                system_prompt=_SYSTEM,
                mcp_servers={"fabpilot": ACTION_SERVER},
                allowed_tools=ACTION_TOOLS,  # auto-approves the typed tools; nothing else allowed
                max_turns=MAX_TURNS,
                max_budget_usd=MAX_BUDGET_USD,
            ),
        ):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        print("·", block.text.strip()[:200])
                    elif isinstance(block, ToolUseBlock) and block.name.startswith("mcp__fabpilot__"):
                        # Record only domain actions, not SDK plumbing (e.g. ToolSearch).
                        record["actions"].append({"tool": block.name, "input": block.input})
                        print("→ ACT", block.name, block.input)
            elif isinstance(msg, ResultMessage):
                record |= {
                    "subtype": msg.subtype,
                    "num_turns": msg.num_turns,
                    "cost_usd": msg.total_cost_usd,
                    "reasoning": msg.result if msg.subtype == "success" else None,
                }
    except Exception as exc:
        record |= {"subtype": "exception", "error": str(exc)}
    record.setdefault("subtype", "incomplete")

    RESPONSE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RESPONSE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record
