# FabPilot / Loop-Engine — Threat Model (STRIDE)

> Architecture-level security pass on the **autonomous loop engine** and FabPilot.
> Done once at design time (Phase 0). Re-run when the architecture changes.
> Scope: the engine that ingests telemetry, reasons with an LLM, runs tools
> (incl. `Bash`), and **acts autonomously** (schedules maintenance, reroutes work).

## Why this matters here
This is not a passive dashboard. It is an agent that (a) consumes **externally
influenced input** (telemetry), (b) can **execute commands**, and (c) **takes
actions without a human in the loop**. That combination is the attack surface.

## Assets
- **A1** The agent's decision authority (it can reroute production / schedule downtime).
- **A2** The host machine running the loop (shell access via `Bash`).
- **A3** Secrets (Anthropic API key, MQTT/broker creds).
- **A4** Integrity of the telemetry stream.
- **A5** The public competition repository.

## Trust boundaries
1. **Sensor/telemetry → ingest** (external, untrusted data crosses here).
2. **Ingest → LLM agent** (untrusted data becomes part of a prompt — injection point).
3. **LLM agent → tool execution** (`Bash`, MQTT publish, actions with real effect).
4. **Repo → public** (anything committed is world-readable during judging).

## STRIDE analysis

| # | Category | Threat | Likelihood | Mitigation |
|---|----------|--------|-----------|------------|
| T1 | **Tampering / Elevation** | **Prompt injection via telemetry** — crafted sensor values/labels steer the agent into a harmful action or shell command. | High (core risk) | Treat telemetry as untrusted data, never instructions. Separate *data* from *instructions* in the prompt. Constrain actions to an allow-list (reroute/schedule only). Human-visible reasoning so a bad decision is caught on screen. |
| T2 | **Elevation of Privilege** | Agent runs arbitrary `Bash` (directly or coerced via T1). | High | Scope tool rules (`Bash(python *)`, etc.); `PreToolUse` hook blocks anything off the allow-list. Run the loop **sandboxed** (worktree/container). Never `bypassPermissions` outside isolation. |
| T3 | **Information Disclosure** | API key / broker creds committed to the **public** repo. | High | Secrets only in env vars / `.env` (git-ignored). Pre-commit secret scan. Confirm `.gitignore` before first commit. (See open item: repo root is currently the home dir.) |
| T4 | **Spoofing** | Rogue client publishes fake telemetry to the MQTT broker. | Med | MQTT auth + TLS (not plaintext/anonymous defaults). Per-client credentials. For the demo, a closed/local broker. |
| T5 | **Denial of Service / cost** | Unbounded loop or injected flood burns the Pro Agent-SDK budget. | Med | Hard `max_turns` + `max_budget_usd` caps per run. Rate-limit ingest. Cost logged per run (D-008). |
| T6 | **Repudiation** | No record of *why* the agent acted — can't audit or explain in Q&A. | Med | Append every decision + reasoning + cost to a run log (`DECISIONS`/run log). Doubles as demo + audit trail. |
| T7 | **Tampering** | Agent edits files it was never meant to touch (orthogonal changes). | Med | `acceptEdits` scoped to the project; sandbox; ponytail/code-reviewer gate before "act". |

## Top 3 to design for now
1. **T1 prompt injection** — the defining risk of an acting agent on external data.
   Data≠instructions, allow-listed actions, visible reasoning.
2. **T2/T3 sandbox + secrets** — isolate execution; keep keys out of the public repo.
3. **T5 budget caps** — non-negotiable on Pro.

## Pitch / disclosure angle
"I threat-modeled my own autonomous agent (STRIDE), treating its own input stream
as an adversary." Few solo entrants do this; it plays to a systems/networking
strength and is honest, concrete AI-usage-disclosure material.
