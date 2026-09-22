"""The persistent HTTP sidecar: load the model once, answer many requests.

Why this exists rather than hosting the model inside each MCP stdio process: a
harness spawns a stdio server per session, and importing torch plus loading a
650 MB checkpoint costs seconds to tens of seconds. Paying that per session is
tolerable; paying it per *tool call* is not, and Laya's own default router
(``max_loaded=1``) makes it worse by rebuilding a model on every language switch -
measured upstream at a 7.4 s median reload on CPU.

So the model lives here, and everything else is a thin client. That is also why
the process is designed to be restartable and to report its own health: upstream
issue #52 is a long-running Laya sidecar that grew to 21.7 GB, and the correct
answer to a model server that leaks is to be able to cycle it, not to hope.

**No web framework by default.** The routing needs are a handful of paths over
JSON, and a stdlib ``http.server`` on loopback with a bounded thread pool does the
job without adding FastAPI and uvicorn to a package whose dependency weight is
already dominated by torch. FastAPI remains available for anyone embedding this
in a larger app; this module is the standalone server.

Two deliberate choices worth naming:

* **stdout is not used for logging.** A stdio MCP server that prints a banner to
  stdout fails to handshake, and this package ships both modes. All diagnostics
  go to stderr, unconditionally.
* **The lock is in the worker, not here.** Concurrency is a property of the model,
  so it is enforced where the model is, and HTTP threads simply queue.
"""

from __future__ import annotations

import json
import logging
import signal
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping, Optional, Sequence
from urllib.parse import urlparse

from . import __version__
from .errors import LayaMcpError, translate
from .protocol import PRIMITIVES, AskRequest, Question
from .worker import LayaWorker, WorkerConfig

log = logging.getLogger("laya_mcp.server")

#: Largest request body accepted, in bytes. A state is capped by the model's own
#: token budget long before this, so the limit exists to stop a hostile or
#: mistaken client from making the server allocate without bound.
MAX_BODY_BYTES = 32 * 1024 * 1024


class _Handler(BaseHTTPRequestHandler):
    """One request. Stateless; the worker holds everything."""

    server_version = f"laya-mcp/{__version__}"
    protocol_version = "HTTP/1.1"

    # -- plumbing ------------------------------------------------------------

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        # Route the stdlib's access log to stderr through logging, so a caller can
        # silence it and so nothing ever reaches stdout.
        log.debug("%s - %s", self.address_string(), fmt % args)

    @property
    def worker(self) -> LayaWorker:
        return self.server.worker  # type: ignore[attr-defined]

    def _send(self, status: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_payload(self, exc: LayaMcpError) -> None:
        self._send(exc.http_status, {"ok": False, **exc.to_dict()})

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise ValueError("empty request body")
        if length > MAX_BODY_BYTES:
            raise ValueError(
                f"request body is {length} bytes, above the {MAX_BODY_BYTES} byte ceiling"
            )
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError("request body is not valid UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"request body is not valid JSON: {exc}") from exc

    # -- routing -------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - the stdlib names these
        path = urlparse(self.path).path
        if path in ("/health", "/healthz"):
            health = self.worker.health()
            # A loaded-but-degraded host answers 200 with degraded:true rather
            # than 503: it *will* serve requests, it will just be slow, and a
            # orchestrator that restarts it would gain nothing.
            self._send(HTTPStatus.OK, {"ok": True, **health})
            return
        if path == "/capabilities":
            self._send(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "checkpoints": {
                        name: cap.to_dict() for name, cap in self.worker.capabilities.items()
                    },
                },
            )
            return
        if path == "/version":
            self._send(HTTPStatus.OK, {"ok": True, "version": __version__, "primitives": list(PRIMITIVES)})
            return
        self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        # `/v1/systemone` is the surface TypeSafe's own API and several Laya ports
        # have converged on, so an existing client can be pointed here by changing
        # one base URL. It takes the same body as `/ask`; the compatibility is at
        # the transport and envelope level, not a claim to reproduce every field of
        # a closed API this project has no access to.
        if path not in ("/ask", "/v1/ask", "/v1/systemone", "/plan", "/v1/plan"):
            self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found", "path": path})
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "invalid_question", "message": str(exc)},
            )
            return
        try:
            request = build_request(payload)
        except LayaMcpError as exc:
            self._send_error_payload(exc)
            return
        try:
            if path in ("/plan", "/v1/plan"):
                # The preflight as an endpoint, not just as a field on a response
                # that has already cost a forward pass. Same arithmetic `/ask`
                # uses, so a caller cannot be told two different things.
                self._send(HTTPStatus.OK, {"ok": True, **self.worker.plan(request)})
                return
            response = self.worker.ask(request)
        except LayaMcpError as exc:
            log.info("ask failed: %s", exc)
            self._send_error_payload(exc)
            return
        except Exception as exc:  # noqa: BLE001
            log.exception("unhandled failure in ask")
            # Through the same mapping as everything else, rather than a payload
            # hand-rolled here. The two differed: this one carried no `hint`, so
            # the only failures that reached a caller without a suggested fix were
            # the unanticipated ones - exactly the failures a caller cannot
            # diagnose alone. Routing it also means a recognisable cause is
            # classified even when it escapes as a bare exception, which is how a
            # Windows commit-charge exhaustion was arriving as `internal` (500,
            # not retryable) instead of `out_of_memory` (503, retryable).
            self._send_error_payload(translate(exc))
            return
        self._send(HTTPStatus.OK, {"ok": True, **response.to_dict()})

    def do_DELETE(self) -> None:  # noqa: N802
        """Release the model and reclaim memory, without stopping the process.

        Present because a model server that can leak needs a way to be recycled
        short of a restart; the next request reloads lazily.
        """
        if urlparse(self.path).path not in ("/model", "/v1/model"):
            self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
            return
        self.worker.stop()
        self._send(HTTPStatus.OK, {"ok": True, "released": True})


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    worker: LayaWorker

    def handle_error(self, request: Any, client_address: Any) -> None:  # noqa: D102
        """Keep a client hanging up out of the error log.

        The stdlib handler prints a full traceback for *any* exception raised
        while serving a request. With HTTP/1.1 keep-alive, the single most common
        exception is the client closing its connection between requests, which
        arrives as `ConnectionResetError` (WinError 10054 on Windows) from
        `rfile.readline`. That is not a fault: a client is entitled to disconnect,
        and a liveness probe that opens and drops a socket will do it constantly.

        Left alone, one such disconnect prints roughly twenty lines of traceback,
        which buries the lines that matter and makes a healthy server look broken
        to whoever is reading the log. So a peer disconnect is logged at debug
        level and everything else is handed to the base class unchanged.
        """
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            log.debug("client %s disconnected mid-request: %s", client_address, exc)
            return
        super().handle_error(request, client_address)


def build_request(payload: Any) -> AskRequest:
    """Turn a JSON body into an :class:`AskRequest`.

    Validation of the *questions* happens in the worker, so it happens once for
    every entry point. This only checks the envelope.
    """
    from .errors import InvalidQuestionError

    if not isinstance(payload, Mapping):
        raise InvalidQuestionError(
            f"the request body must be a JSON object, got {type(payload).__name__}"
        )

    if "state" not in payload:
        raise InvalidQuestionError(
            "the request has no `state`",
            hint="`state` is the evidence being judged: a string, or any JSON object",
        )

    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, Mapping):
        raise InvalidQuestionError(
            "`questions` must be an object keyed by question id",
            hint="Laya calls questions.keys(), so a list of questions can never work",
        )

    questions: dict[str, Question] = {}
    for question_id, definition in raw_questions.items():
        if not isinstance(definition, Mapping):
            raise InvalidQuestionError(
                f"question {question_id!r} must be an object, got {type(definition).__name__}",
                question_id=str(question_id),
            )
        questions[str(question_id)] = Question(
            type=definition.get("type"),  # validated by the worker
            instructions=definition.get("instructions"),
            criteria=definition.get("criteria"),
            id=str(question_id),
        )

    return AskRequest(
        state=payload["state"],
        questions=questions,
        model=_opt_str(payload.get("model")),
        task=_opt_str(payload.get("task")),
        lang=_opt_str(payload.get("lang")),
        strict=bool(payload.get("strict", False)),
    )


def _opt_str(value: Any) -> Optional[str]:
    return None if value is None else str(value)


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8787,
    model: str = "english",
    also: Sequence[str] = (),
    device: Optional[str] = None,
    model_root: Optional[str] = None,
    max_len: Optional[int] = None,
    head_max_len: Optional[int] = None,
    calibration_path: Optional[str] = None,
    concurrency: int = 1,
    log_level: str = "info",
    preload: bool = True,
    truncate_left: bool = False,
) -> int:
    """Run the sidecar until interrupted. Returns a process exit code."""
    _configure_logging(log_level)

    if host not in ("127.0.0.1", "localhost", "::1"):
        # Binding a model server to a routable address exposes whatever it is
        # pointed at to the network, and this server has no authentication. Say
        # so once, loudly, rather than silently accepting it.
        log.warning(
            "binding to %s, which is not loopback. This server has no authentication; "
            "anything that can reach the port can send your data to the model. Put it behind "
            "a reverse proxy with auth, or bind 127.0.0.1.",
            host,
        )

    worker = LayaWorker(
        WorkerConfig(
            model=model,
            also=tuple(also),
            device=device,
            model_root=model_root,
            max_len=max_len,
            head_max_len=head_max_len,
            calibration_path=calibration_path,
            concurrency=concurrency,
            preload=preload,
            truncate_left=truncate_left,
        )
    )

    log.info("loading %s (this is the one-time cost)", ", ".join([model, *also]))
    started = time.time()
    try:
        worker.start()
    except LayaMcpError as exc:
        log.error("cannot start: %s", exc)
        return 3
    log.info("ready in %.1fs", time.time() - started)
    for name, capability in worker.capabilities.items():
        log.info(
            "checkpoint %s: device=%s max_len=%d head_max_len=%d fitted_temps=%d",
            name,
            capability.device,
            capability.max_len,
            capability.head_max_len,
            capability.fitted_temperature_buckets,
        )

    server = _Server((host, port), _Handler)
    server.worker = worker
    log.info("listening on http://%s:%d  (POST /ask, GET /health)", host, port)

    stopping = threading.Event()

    def _shutdown(signum: int, _frame: Any) -> None:
        log.info("signal %d received, shutting down", signum)
        stopping.set()
        threading.Thread(target=server.shutdown, daemon=True).start()

    for signal_name in ("SIGINT", "SIGTERM"):
        candidate = getattr(signal, signal_name, None)
        if candidate is not None:
            try:
                signal.signal(candidate, _shutdown)
            except (ValueError, OSError):
                # Not on the main thread, or unsupported on this platform.
                pass

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        server.server_close()
        worker.stop()
    return 0


def _configure_logging(level: str) -> None:
    """Send logs to stderr, never stdout."""
    root = logging.getLogger("laya_mcp")
    root.handlers.clear()
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Laya prints its own warnings with print(), which lands on stdout. Nothing
    # here can intercept that from Python, so the CLI docs point a caller at
    # `--log-level` and the health endpoint instead of pretending it is captured.
