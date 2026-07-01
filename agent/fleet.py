"""Tier 1 — fleet coordination: an autonomous reroute negotiated over the bus.

When a machine is predicted to fail, its agent doesn't just pick a replacement — it
broadcasts a reroute *request* on the MQTT bus; every healthy machine's agent answers
with a *bid* (its headroom to take the work); a deterministic arbiter *awards* the job
to the best bid and publishes it back. One round-trip, request -> bid -> award: a
trimmed contract-net, not open-ended negotiation (DECISIONS.md D-023). Multi-round
haggling and per-machine LLM loops are deliberately rejected — fragile and costly for
no demo upside. The LLM decides *that* a reroute is warranted (agent/respond.py); the
routing math here is plain, inspectable code.

The distribution is real: bidders are independent MQTT clients publishing real bid
messages on the bus. That bus coordination — not the agent count (only three
machines) — is the differentiation to lean on.

Run (broker up):  python -m agent.fleet   # M2 requests; M1/M3 bid; healthier wins
"""

from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass

import paho.mqtt.client as mqtt

from transport.mqtt_io import HOST, PORT, decode_payload, make_client

REQUEST_TOPIC = "fabpilot/reroute/request"
BID_TOPIC = "fabpilot/reroute/bid"
AWARD_TOPIC = "fabpilot/reroute/award"


def _valid_bid(bid: object, from_machine: str) -> bool:
    """A bid we can safely award: well-formed JSON of the right shape, for this
    request. Corrupt JSON already decodes to None; this rejects the subtler case of a
    valid JSON object with the wrong shape (a foreign publisher, a version skew) that
    would otherwise KeyError inside `award`."""
    return (
        isinstance(bid, dict)
        and bid.get("for") == from_machine
        and isinstance(bid.get("machine_id"), str)
        and isinstance(bid.get("headroom"), (int, float))
    )


@dataclass
class MachineAgent:
    """A machine's agent on the bus. Its `health` in [0, 1] is its headroom to take on
    rerouted work — a higher value is a safer place to send the job."""

    machine_id: str
    health: float = 1.0

    def bid_on(self, from_machine: str) -> dict | None:
        """This agent's bid to take over `from_machine`'s work, or None if the request
        is its own (the failing machine never bids on itself)."""
        if self.machine_id == from_machine:
            return None
        return {"machine_id": self.machine_id, "headroom": round(self.health, 3), "for": from_machine}


def award(from_machine: str, bids: list[dict]) -> dict | None:
    """Pick the winning bid: most headroom wins; ties break to the lowest machine id so
    a live demo awards the *same* winner every run. Excludes the failing machine
    defensively. None if nobody bid."""
    candidates = [b for b in bids if b.get("machine_id") != from_machine]
    if not candidates:
        return None
    # Defensive .get() so a malformed bid can never crash the arbiter mid-round, even
    # if one slips past _valid_bid — belt-and-suspenders on the critical path.
    candidates.sort(key=lambda b: (-b.get("headroom", -1.0), b.get("machine_id", "")))
    return candidates[0]


def start_bidder(agent: MachineAgent, host: str = HOST, port: int = PORT) -> mqtt.Client:
    """Bring a machine agent online: it listens for reroute requests and bids on any
    that isn't its own. Returns the connected, looping client (caller stops it).

    The bid is published fire-and-forget: this runs on paho's network thread, so it
    must NOT wait_for_publish (that would block the very loop meant to send it).
    """
    client = make_client(f"fabpilot-agent-{agent.machine_id}")
    subscribed = threading.Event()

    def on_request(c: mqtt.Client, _u, msg) -> None:
        req = decode_payload(msg.payload)
        if req is None:
            return
        bid = agent.bid_on(req.get("from_machine"))
        if bid is not None:
            c.publish(BID_TOPIC, json.dumps(bid), qos=1)  # no wait: we're on the loop thread

    client.on_connect = lambda c, u, flags, rc, props: c.subscribe(REQUEST_TOPIC, qos=1)
    client.on_subscribe = lambda c, u, mid, rc, props: subscribed.set()
    client.on_message = on_request
    client.connect(host, port)
    client.loop_start()
    # Block until the subscription is *confirmed* — ready-by-construction, so a request
    # published right after this returns can't race ahead of the bidder's SUBSCRIBE.
    if not subscribed.wait(timeout=5):
        client.loop_stop()
        client.disconnect()
        raise TimeoutError(f"{agent.machine_id} bidder failed to subscribe within 5s")
    return client


def request_reroute(from_machine: str, reason: str, host: str = HOST, port: int = PORT,
                    bid_window: float = 1.0) -> dict:
    """Broadcast a reroute request, collect bids for `bid_window` seconds, award the
    best, and publish the award. Returns {from_machine, to_machine, headroom, bids};
    to_machine is None if nobody bid. Runs on the main thread, so it may wait on publish.
    """
    inbox: queue.Queue[dict | None] = queue.Queue()
    coord = make_client("fabpilot-arbiter")
    subscribed = threading.Event()
    coord.on_message = lambda c, u, msg: inbox.put(decode_payload(msg.payload))
    coord.on_connect = lambda c, u, flags, rc, props: c.subscribe(BID_TOPIC, qos=1)
    coord.on_subscribe = lambda c, u, mid, rc, props: subscribed.set()
    coord.connect(host, port)
    coord.loop_start()
    no_award = {"from_machine": from_machine, "to_machine": None, "headroom": None, "bids": []}
    try:
        # Only broadcast once we're provably listening for answers — otherwise early
        # bids would be dropped and the reroute would silently degrade.
        if not subscribed.wait(timeout=5):
            return no_award
        info = coord.publish(REQUEST_TOPIC, json.dumps({"from_machine": from_machine, "reason": reason}), qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            return no_award  # request never left the client — degrade to "nobody available"
        info.wait_for_publish(timeout=5)

        bids: list[dict] = []
        deadline = time.time() + bid_window
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                bid = inbox.get(timeout=remaining)
            except queue.Empty:
                break
            if _valid_bid(bid, from_machine):
                bids.append(bid)

        won = award(from_machine, bids)
        if won is not None:
            aw = coord.publish(AWARD_TOPIC, json.dumps({
                "from_machine": from_machine, "to_machine": won["machine_id"],
                "headroom": won["headroom"], "reason": reason,
            }), qos=1)
            try:
                aw.wait_for_publish(timeout=5)  # best-effort: the decision is already made
            except (RuntimeError, ValueError):
                pass
        return {
            "from_machine": from_machine,
            "to_machine": won["machine_id"] if won else None,
            "headroom": won["headroom"] if won else None,
            "bids": [b["machine_id"] for b in bids],
        }
    finally:
        coord.loop_stop()
        coord.disconnect()


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # 1) Deterministic arbiter logic — no broker, always runs (the CI-safe core).
    fleet = [MachineAgent("M1", 0.95), MachineAgent("M2", 0.20), MachineAgent("M3", 0.80)]
    assert fleet[1].bid_on("M2") is None, "failing machine must not bid on itself"
    logic_bids = [b for a in fleet if (b := a.bid_on("M2")) is not None]
    winner = award("M2", logic_bids)
    assert winner is not None and winner["machine_id"] == "M1", f"healthier M1 should win, got {winner}"
    print(f"# arbiter logic OK: bids {[b['machine_id'] for b in logic_bids]} -> award M1 (most headroom)")

    # 2) Over-the-bus round-trip — needs the broker; the genuinely distributed part.
    healthy = [MachineAgent("M1", 0.95), MachineAgent("M3", 0.80)]
    clients: list[mqtt.Client] = []
    try:
        for agent in healthy:
            clients.append(start_bidder(agent))
    except (ConnectionRefusedError, OSError) as exc:
        for c in clients:
            c.loop_stop()
            c.disconnect()
        print(f"# bus round-trip skipped — broker not reachable at {HOST}:{PORT} "
              f"(run 'docker compose up -d') [{exc}]")
        raise SystemExit(0)

    try:
        # No sleep needed: start_bidder already blocked until each bidder's SUBSCRIBE
        # was confirmed, and request_reroute waits for its own before broadcasting.
        result = request_reroute("M2", "vibration approaching ISO 10816 severe")
    finally:
        for c in clients:
            c.loop_stop()
            c.disconnect()

    print(f"# bus round-trip: M2 requested; bids from {result['bids']}; awarded -> {result['to_machine']}")
    assert result["to_machine"] == "M1", f"expected reroute to M1, got {result['to_machine']}"
    print("# self-check OK: request -> bids -> award over MQTT, healthier M1 won")
