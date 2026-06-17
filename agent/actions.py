"""Typed actions the agent can take on a fault — the 'act' step (DECISIONS.md D-012).

Exposed as in-process SDK MCP tools so the agent calls real, validated functions
(`schedule_maintenance`, `reroute_job`) instead of generic file or shell tools.
Each validates its inputs and returns a structured result — LLMs call tools with
wrong arguments, so bad inputs come back as errors the agent can reason about,
never as silent corruption. In this slice an action records the decision to an
actions log (no real hardware); that log is the demo's audit trail.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from claude_agent_sdk import create_sdk_mcp_server, tool

ACTIONS_LOG = Path("runs/actions.jsonl")
MACHINES = {"M1", "M2", "M3"}  # the known line; reject anything else


def _record(action: str, detail: dict) -> None:
    ACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "action": action, **detail}
    with ACTIONS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _ok(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _err(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


@tool(
    "schedule_maintenance",
    "Schedule maintenance for a machine on the line within a deadline.",
    {
        "machine_id": Annotated[str, "Machine id, e.g. M2"],
        "within_hours": Annotated[float, "Maintenance deadline, in hours from now"],
        "reason": Annotated[str, "Why maintenance is needed (the anomaly evidence)"],
    },
)
async def schedule_maintenance(args: dict) -> dict[str, Any]:
    machine, reason = args.get("machine_id"), args.get("reason")
    if not isinstance(machine, str) or not isinstance(reason, str):
        return _err("machine_id and reason are required strings")
    if machine not in MACHINES:
        return _err(f"unknown machine {machine!r}; known: {sorted(MACHINES)}")
    try:
        hours = float(args.get("within_hours"))
    except (TypeError, ValueError):
        return _err("within_hours must be a number")
    if not hours > 0:  # also rejects NaN (NaN > 0 is False)
        return _err("within_hours must be positive")
    _record("schedule_maintenance", {"machine_id": machine, "within_hours": hours, "reason": reason})
    return _ok(f"Maintenance scheduled for {machine} within {hours}h.")


@tool(
    "reroute_job",
    "Reroute the current job from a failing machine to a healthy one.",
    {
        "from_machine": Annotated[str, "Failing machine id"],
        "to_machine": Annotated[str, "Healthy machine to take over the work"],
        "reason": Annotated[str, "Why the reroute is needed"],
    },
)
async def reroute_job(args: dict) -> dict[str, Any]:
    src, dst, reason = args.get("from_machine"), args.get("to_machine"), args.get("reason")
    if not all(isinstance(x, str) for x in (src, dst, reason)):
        return _err("from_machine, to_machine, and reason are required strings")
    if src not in MACHINES or dst not in MACHINES:
        return _err(f"unknown machine in {src!r}->{dst!r}; known: {sorted(MACHINES)}")
    if src == dst:
        return _err("from_machine and to_machine must differ")
    _record("reroute_job", {"from_machine": src, "to_machine": dst, "reason": reason})
    return _ok(f"Rerouted work from {src} to {dst}.")


ACTION_SERVER = create_sdk_mcp_server(
    name="fabpilot", version="0.1.0", tools=[schedule_maintenance, reroute_job]
)
# How allowed_tools / Claude reference SDK MCP tools: mcp__<server>__<tool>.
ACTION_TOOLS = ["mcp__fabpilot__schedule_maintenance", "mcp__fabpilot__reroute_job"]
