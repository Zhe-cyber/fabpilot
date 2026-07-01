"""FabPilot live dashboard — the 'showable reasoning' demo (BACKLOG: dashboard).

Serves one page that streams the detect -> reason -> act pipeline to the browser as
it runs: live machine telemetry, each anomaly, and the agent's reasoning + actions.

Transport is Server-Sent Events, not WebSocket, on purpose: the data flows one way
(server -> browser), SSE is stdlib-only (http.server) and auto-reconnects, and we
never need a back-channel. It runs the in-process spine (agent/orchestrate.run) so
the demo is one command with no broker — robust for a live audience.

The pipeline is async; http.server is threaded. A Broadcaster bridges them: the
pipeline thread publishes JSON events, each SSE connection drains its own queue.

Run:  python -m dashboard.server      # then open http://127.0.0.1:8000
      (makes real, budget-capped agent calls when you click Start)
"""

from __future__ import annotations

import asyncio
import json
import queue
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agent.orchestrate import run

HOST, PORT = "127.0.0.1", 8000
INDEX = Path(__file__).with_name("index.html")


class Broadcaster:
    """Fan-out from the pipeline thread to every connected SSE client."""

    def __init__(self) -> None:
        self._clients: list[queue.Queue[str]] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=1000)
        with self._lock:
            self._clients.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[str]) -> None:
        with self._lock:
            if q in self._clients:
                self._clients.remove(q)

    def publish(self, kind: str, data: dict) -> None:
        """Called from the pipeline thread for each step. Non-blocking."""
        # default=str so an odd (non-JSON) value degrades to text instead of raising
        # here and aborting the whole run.
        msg = json.dumps({"type": kind, **data}, default=str)
        with self._lock:
            clients = list(self._clients)
        for q in clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass  # a stuck client shouldn't stall the pipeline


BUS = Broadcaster()
_run_lock = threading.Lock()  # guards against overlapping pipeline runs


def _start_pipeline() -> bool:
    """Launch one pipeline run in a background thread. False if one is already going."""
    if not _run_lock.acquire(blocking=False):
        return False

    def worker() -> None:
        try:
            BUS.publish("status", {"state": "running"})
            asyncio.run(run(emit=BUS.publish, delay=0.15))
            BUS.publish("status", {"state": "done"})
        except Exception as exc:  # a mid-run failure must end *visibly*, never freeze the page
            BUS.publish("status", {"state": "error", "error": str(exc)})
        finally:
            _run_lock.release()

    threading.Thread(target=worker, daemon=True).start()
    return True


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path == "/":
            self._serve_index()
        elif self.path == "/events":
            self._serve_events()
        elif self.path == "/start":
            started = _start_pipeline()
            self._json({"started": started})
        else:
            self.send_error(404)

    def _serve_index(self) -> None:
        try:
            body = INDEX.read_bytes()
        except OSError as exc:  # the demo's front door — fail with a clear message, not a traceback
            self.send_error(500, f"index.html unavailable: {exc}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q = BUS.subscribe()
        try:
            while True:
                try:
                    msg = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")  # hold the connection open
                    self.wfile.flush()
                    continue
                self.wfile.write(f"data: {msg}\n\n".encode())
                self.wfile.flush()
        except ConnectionError:
            pass  # client closed the tab (covers broken-pipe / reset / abort on Windows)
        finally:
            BUS.unsubscribe(q)

    def log_message(self, *args) -> None:
        pass  # keep the console clean for the demo (pipeline prints its own lines)


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True  # don't let lingering SSE threads block Ctrl+C

    def handle_error(self, request, client_address) -> None:
        # A client closing an SSE tab aborts the keep-alive socket, which stdlib
        # surfaces here (outside the handler). That's normal — don't dump a
        # traceback across the demo console. Re-raise anything that isn't a drop.
        if not isinstance(sys.exc_info()[1], ConnectionError):
            super().handle_error(request, client_address)


def main() -> None:
    server = DashboardServer((HOST, PORT), Handler)
    print(f"FabPilot dashboard on http://{HOST}:{PORT}  (open it, then click Start)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping dashboard")
        server.shutdown()


if __name__ == "__main__":
    main()
