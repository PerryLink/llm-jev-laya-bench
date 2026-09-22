"""The MCP face of laya-mcp.

Five tools, each answering a question a caller actually has. The descriptions
carry as much weight as the code, and in one place they carry more: a decision
model asked to write prose produces nothing useful, and a model that does not know
that will keep trying. So every description says what the tool is *not* for.

**Where the model lives.** By default this process hosts it, because that is the
only thing that works when a harness spawns a stdio server and nothing else is
running. Pass ``--sidecar http://127.0.0.1:8787`` and it forwards instead, which
is the configuration to prefer: a harness spawns one server per session, and
loading a 650 MB checkpoint per session - before the first tool call - is the
single biggest reason a Python-backed MCP server feels slow.

**Tool naming.** ``laya_ask`` is the general tool; ``laya_noul``, ``laya_choice``
and ``laya_score`` are the three primitives as one-question conveniences, because
in practice most calls ask exactly one thing and building a batch of one is
friction. ``laya_plan`` answers "will this fit, and what will be cut?" without
running the model at all.

The SDK is pinned to v1 on purpose (see ``pyproject.toml``): the v2 release
removed the ``FastMCP`` export this module is built on, and a server that breaks
on a transitive major bump is worse than one that pins.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from typing import Any, Mapping, Optional, Sequence

from . import __version__
from .errors import InvalidQuestionError, LayaMcpError, SidecarUnreachableError, from_payload
from .protocol import (
    PRIMITIVES,
    Answer,
    AskRequest,
    AskResponse,
    Question,
)
from .worker import LayaWorker, WorkerConfig

log = logging.getLogger("laya_mcp.mcp")

#: A description shared by every tool, because the misuse it prevents is the same
#: one each time.
_NOT_FOR_PROSE = (
    "Laya answers typed questions and returns probabilities; it does not generate text. "
    "Do not use it to write, summarise or explain anything."
)

_CONFIDENCE_NOTE = (
    "`confidence` is a concentration statistic, NOT the probability that the answer is correct. "
    "It is low whenever the probability is spread across options even when the top option is "
    "right. For a yes/no question branch on `noul` directly."
)

#: The token-budget warning, which every tool that actually runs the model must
#: carry. Laya cuts an oversized state and shortens option text until labels stop
#: being distinguishable, and it reports neither in its own payload. A caller that
#: does not know this will read a confident answer about a fragment as an answer
#: about the whole document. The `laya_ask` description below and the sibling DSH
#: plugin's must agree on this; they did not, and the DSH one was the only place it
#: was written down.
#:
#: Which *end* is cut depends on how the server was started (``--truncate-left``),
#: so the sentence is built rather than fixed: a tool description that promised the
#: wrong end would be worse than one that said nothing, because the caller would
#: trust it.
_BUDGET_NOTE_TEMPLATE = (
    "The checkpoint has a fixed token budget. An oversized state is truncated without "
    "appearing in the answer - {direction} - and a question with many options has its option "
    "text shortened until labels are no longer distinguishable. Read `truncated`, "
    "`budget_summary` and `warnings` on the result before trusting an answer about a large "
    "document or a long option list, or call `laya_plan` first to see what would be cut."
)


def _budget_note(truncate_left: Optional[bool]) -> str:
    """The budget warning, naming the end that is actually discarded.

    ``None`` means this process cannot know: with ``--sidecar`` the model runs
    elsewhere, and asking it would mean a network round-trip while the server is
    being built - which is precisely the handshake latency this server was fixed to
    stop paying. So it points at the field that does know rather than guessing.
    """
    if truncate_left is None:
        direction = "the sidecar decides which end survives, and `truncated.state.kept` reports it"
    elif truncate_left:
        direction = "this server keeps the TAIL of the state and discards the front"
    else:
        direction = "this server keeps the FRONT of the state and discards the tail"
    return _BUDGET_NOTE_TEMPLATE.format(direction=direction)


class Backend:
    """Where answers come from: a local model, or a sidecar over HTTP."""

    def __init__(self, sidecar: Optional[str] = None, config: Optional[WorkerConfig] = None) -> None:
        self.sidecar = sidecar.rstrip("/") if sidecar else None
        self._worker: Optional[LayaWorker] = None
        self._config = config or WorkerConfig()
        self._warm_done = threading.Event()
        self._warm_error: Optional[BaseException] = None

    def _local(self) -> LayaWorker:
        if self._worker is None:
            self._worker = LayaWorker(self._config)
        return self._worker

    @property
    def truncate_left(self) -> bool:
        """Whether this process's own model would keep the tail of an oversized state.

        Only meaningful without a sidecar: with one, the truncation happens in the
        other process and this setting is never consulted.
        """
        return self._config.truncate_left

    def start_warm(self) -> None:
        """Begin loading the model on a background thread.

        The handshake has to be answered *now*. Both harnesses measured here give
        an MCP server 30 seconds to complete `initialize`, and loading a
        checkpoint first costs 19 s uncontended and 275 s while another model owns
        the GPU - so preloading before `server.run()` means the client reports
        "Failed to connect" and never sees the tool list at all. Measured with
        opencode and claude, both of which then time out on a config they had
        parsed correctly.

        Loading on a thread rather than on the loop thread is the whole point.
        Doing this work *on the event loop* hangs - reproduced here, and recorded
        in this file's history - while the identical load from a separate thread
        completes. The handshake and `tools/list` are answered while this runs;
        only a tool call that actually needs the model waits, and it waits on an
        Event rather than on the loop.
        """
        if self.sidecar:
            self._warm_done.set()
            return

        def _load() -> None:
            try:
                self._local().start()
            except BaseException as exc:  # noqa: BLE001 - re-raised on first use
                self._warm_error = exc
            finally:
                self._warm_done.set()

        threading.Thread(target=_load, name="laya-warm", daemon=True).start()

    def wait_warm(self) -> None:
        """Block until the model is up. Cheap and idempotent once it is."""
        if self.sidecar:
            return
        self._warm_done.wait()
        if self._warm_error is not None:
            raise self._warm_error

    def warm(self) -> None:
        """Load the model synchronously on the calling thread.

        Kept for callers that want the old behaviour - a script, or a test that
        would rather fail at startup than at the first call.
        """
        if self.sidecar:
            return
        self._local().start()

    def close(self) -> None:
        """Release the model if this process owns one."""
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def ask(self, request: AskRequest) -> Mapping[str, Any]:
        self.wait_warm()
        if self.sidecar:
            return _post_json(
                f"{self.sidecar}/ask",
                {
                    "state": request.state,
                    "questions": {
                        qid: q.to_laya() for qid, q in request.questions.items()
                    },
                    **({"model": request.model} if request.model else {}),
                    **({"task": request.task} if request.task else {}),
                    **({"lang": request.lang} if request.lang else {}),
                    **({"strict": True} if request.strict else {}),
                },
            )
        response: AskResponse = self._local().ask(request)
        return response.to_dict()

    def plan(self, state: Any, questions: Mapping[str, Question]) -> Mapping[str, Any]:
        self.wait_warm()
        """Plan against the checkpoint's budget, without a forward pass."""
        from .planning import plan_questions
        from .validate import validate_questions

        validate_questions(questions)
        if self.sidecar:
            # The sidecar owns the loaded checkpoint, so ask it for the
            # capability rather than guessing from a config file this process
            # may not even have.
            info = _get_json(f"{self.sidecar}/capabilities")
            checkpoints = info.get("checkpoints") or {}
            if not checkpoints:
                raise InvalidQuestionError("the sidecar reports no loaded checkpoint")
            name, raw = next(iter(checkpoints.items()))
            from .capability import Capability

            capability = Capability(
                checkpoint=name,
                repo=raw.get("repo", "?"),
                subfolder=raw.get("subfolder"),
                encoder=raw.get("encoder"),
                device=raw.get("device", "unknown"),
                requested_device=raw.get("requested_device"),
                degraded=bool(raw.get("degraded", False)),
                max_len=int(raw.get("max_len", 512)),
                head_max_len=int(raw.get("head_max_len", 192)),
                head_layers=raw.get("head_layers"),
                temperature=tuple(raw.get("temperature") or (1.0, 1.0, 1.0)),
                fitted_temperature_buckets=int(raw.get("fitted_temperature_buckets", 0)),
                amp_dtype=raw.get("amp_dtype"),
            )
            plan = plan_questions(capability, state, questions)
            return plan.to_dict()
        worker = self._local()
        worker.start()
        capability = next(iter(worker.capabilities.values()), None)
        if capability is None:
            raise InvalidQuestionError("no checkpoint is loaded")
        return plan_questions(capability, state, questions).to_dict()


def _post_json(url: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """POST and decode, turning an error body into a structured exception."""
    import urllib.error
    import urllib.request

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:  # noqa: S310 - a caller-supplied loopback URL
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            raise LayaMcpError(f"the sidecar returned HTTP {exc.code}") from exc
        # Rebuild the sidecar's own error rather than wrapping it in the base
        # class: the code is the part a caller branches on, and `invalid_question`
        # arriving as `internal` sends them to debug the wrong program.
        raise from_payload(detail, fallback=f"the sidecar returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SidecarUnreachableError(
            f"cannot reach the sidecar at {url}: {exc.reason}",
            hint="start it with `laya-mcp serve`, or run without --sidecar to host the model here",
        ) from exc


def _get_json(url: str) -> Mapping[str, Any]:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SidecarUnreachableError(
            f"cannot reach the sidecar at {url}: {exc.reason}",
            hint="start it with `laya-mcp serve`, or run without --sidecar to host the model here",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        # Up, but not answering with JSON. That is a different fault from "not
        # there", and saying "unreachable" for it would send the caller to check
        # a process that is running perfectly well.
        raise LayaMcpError(f"the sidecar at {url} returned an unusable response: {exc}") from exc


# --------------------------------------------------------------------------- #
# tool construction
# --------------------------------------------------------------------------- #


def _question(
    qtype: str,
    instructions: Any,
    criteria: Any = None,
    boundary: Any = None,
    question_id: str = "q",
) -> Question:
    """Build one question from tool arguments.

    ``boundary`` is the documented spelling for a noul and is folded into
    ``criteria`` here, because that is where Laya reads it. Both spellings are
    accepted for the same reason the sibling Jev integration accepts both: a
    caller that wrote one and had it silently ignored would be misled about what
    the probability refers to.
    """
    if qtype == "noul" and boundary is not None and criteria is None:
        criteria = boundary
    return Question(type=qtype, instructions=instructions, criteria=criteria, id=question_id)


def build_server(backend: Backend, tools: Optional[Sequence[str]] = None):
    """Build the MCP server. Imported lazily so the package works without the SDK."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise LayaMcpError(
            "the MCP SDK is not installed",
            hint="install the extra: pip install 'laya-mcp[mcp]'",
        ) from exc

    # `FastMCP` takes `name` and `instructions` but no `version`; the SDK reports
    # its own server version in the handshake. Passing one is a TypeError, which
    # the protocol test caught and the pure tests could not: they never build the
    # server. `instructions` is the one place to tell a client what this server is
    # for before any tool is called, so it carries the same warning the tool
    # descriptions do.
    server = FastMCP(
        "laya",
        instructions=(
            "Typed decision questions for Laya, a non-autoregressive decision model. It answers "
            "noul (yes/no), choice and score questions and returns probabilities. It does not "
            "generate text. Its `confidence` field is a concentration statistic, not the "
            "probability of being correct."
        ),
    )

    def wanted(tool: str) -> bool:
        return tools is None or tool in tools

    # Computed once, and only from what this process can actually know: with a
    # sidecar the direction belongs to the other process.
    budget_note = _budget_note(None if backend.sidecar else backend.truncate_left)

    if wanted("laya_ask"):

        @server.tool(
            name="laya_ask",
            description=(
                "Ask one or more typed questions about a single piece of state (text, JSON, an "
                "email, a ticket, a document) and get calibrated probabilities back. Each "
                "question is `noul` (yes/no), `choice` (pick one of a fixed set) or `score` "
                "(place on an ordered scale). Use this instead of reading the state yourself "
                "when the answer is a decision rather than a summary.\n\n" + budget_note + " " +
                _NOT_FOR_PROSE + " " + _CONFIDENCE_NOTE
            ),
        )
        def laya_ask(state: Any, questions: dict[str, Any]) -> str:
            """Ask typed questions about one state.

            Args:
                state: The evidence to judge: a string, or any JSON object. Keys
                    become referenceable paths in the question text, so
                    ``{"body": "..."}`` lets a question say "in `body`".
                questions: Question id -> ``{type, instructions, criteria}``.
                    `criteria` is required for `choice` (label -> description) and
                    `score` (an ordered array of levels). For `noul` it is
                    optional and, when given, must be ``{"true": ..., "false":
                    ...}`` describing what each outcome means.
            """
            return _run(backend, state, _batch(questions), strict=False)

    if wanted("laya_noul"):

        @server.tool(
            name="laya_noul",
            description=(
                "Ask ONE yes/no question about a state and get P(true) in [0,1]. This is a "
                "probability, not a decision: 0.51 is a coin toss, and the result includes a "
                "`band` of no/uncertain/yes. Supply `boundary` whenever the line between yes "
                "and no is not obvious - a probability whose boundary is unstated cannot be "
                "read. " + budget_note + " " + _NOT_FOR_PROSE
            ),
        )
        def laya_noul(
            state: Any,
            instructions: str,
            boundary: Optional[dict[str, Any]] = None,
        ) -> str:
            """Ask one yes/no question.

            Args:
                state: The evidence to judge.
                instructions: The question, phrased so yes or no answers it.
                boundary: What "true" and what "false" mean, e.g.
                    ``{"true": "the user is threatening to cancel", "false":
                    "no such threat"}``.
            """
            question = _question("noul", instructions, boundary=boundary)
            return _run(backend, state, {"q": question}, strict=False)

    if wanted("laya_choice"):

        @server.tool(
            name="laya_choice",
            description=(
                "Ask ONE multiple-choice question about a state and get the chosen label plus "
                "the full distribution over the options. Options need descriptions: two bare "
                "labels are often indistinguishable to the model, and the description is what "
                "separates them. Accuracy falls off sharply above roughly 20 options. " +
                budget_note + " " + _NOT_FOR_PROSE
            ),
        )
        def laya_choice(state: Any, instructions: str, options: dict[str, Any]) -> str:
            """Choose one label from a fixed set.

            Args:
                state: The evidence to judge.
                instructions: The question.
                options: Permitted label -> a description of when that label applies.
            """
            question = _question("choice", instructions, criteria=options)
            return _run(backend, state, {"q": question}, strict=False)

    if wanted("laya_score"):

        @server.tool(
            name="laya_score",
            description=(
                "Ask ONE ordered-scale question about a state and get the expected level plus "
                "the distribution. Levels must be passed in ascending order, because position "
                "IS the score. Note that this is Laya's weakest primitive in independent "
                "measurement, so prefer `laya_choice` when the levels can be treated as "
                "unordered. " + budget_note + " " + _NOT_FOR_PROSE
            ),
        )
        def laya_score(state: Any, instructions: str, levels: list[str]) -> str:
            """Place a state on an ordered scale.

            Args:
                state: The evidence to judge.
                instructions: The question, e.g. "How urgent is this request?".
                levels: The rubric in ascending order; the first entry is level 0.
            """
            question = _question("score", instructions, criteria=levels)
            return _run(backend, state, {"q": question}, strict=False)

    if wanted("laya_plan"):

        @server.tool(
            name="laya_plan",
            description=(
                "Check whether a question batch fits the checkpoint's token budget WITHOUT "
                "running the model, and report exactly what would be silently cut. Use it "
                "before a large or high-option-count call: Laya discards the tail of an "
                "oversized state and shortens options until labels are indistinguishable, and "
                "neither is reported in its answer."
            ),
        )
        def laya_plan(state: Any, questions: dict[str, Any]) -> str:
            """Report the token budget for a batch before running it.

            Args:
                state: The evidence that would be judged.
                questions: The same question map `laya_ask` takes.
            """
            try:
                plan = backend.plan(state, _batch(questions))
            except LayaMcpError as exc:
                return json.dumps({"ok": False, **exc.to_dict()}, ensure_ascii=False, indent=2)
            return json.dumps({"ok": True, **plan}, ensure_ascii=False, indent=2)

    return server


def _batch(questions: Mapping[str, Any]) -> dict[str, Question]:
    """Turn the tool's question map into :class:`Question` objects.

    The type is not validated here - the worker does that, once, for every entry
    point, so the MCP surface and the HTTP surface cannot disagree about what is
    legal.
    """
    if not isinstance(questions, Mapping):
        raise InvalidQuestionError(
            "`questions` must be an object keyed by question id",
            hint="a list cannot work: the ids become the keys of the answer map",
        )
    out: dict[str, Question] = {}
    for question_id, definition in questions.items():
        if not isinstance(definition, Mapping):
            raise InvalidQuestionError(
                f"question {question_id!r} must be an object", question_id=str(question_id)
            )
        out[str(question_id)] = Question(
            type=definition.get("type"),
            instructions=definition.get("instructions"),
            criteria=definition.get("criteria"),
            id=str(question_id),
        )
    return out


def _run(backend: Backend, state: Any, questions: Mapping[str, Question], *, strict: bool) -> str:
    """Run a batch and render the result for a model to read.

    Errors are rendered as a JSON body with ``ok: false`` rather than raised. A
    model that receives a structured refusal with a hint can correct itself; a
    model that receives an MCP protocol error usually just retries the same call.
    """
    try:
        payload = backend.ask(
            AskRequest(state=state, questions=questions, strict=strict)
        )
    except LayaMcpError as exc:
        return json.dumps({"ok": False, **exc.to_dict()}, ensure_ascii=False, indent=2)
    rendered = json.dumps({"ok": True, **_trim(payload)}, ensure_ascii=False, indent=2)
    return rendered


def _trace(message: str) -> None:
    """Write a line to stderr when ``LAYA_MCP_TRACE`` is set.

    Straight to the stream rather than through ``logging``, because the question
    this answers is "did this code run at all", and a logger whose level or
    handler is misconfigured answers that with silence - which is exactly the
    ambiguity that made a hung tool call hard to place.
    """
    if os.environ.get("LAYA_MCP_TRACE"):
        print(f"[trace] {message}", file=sys.stderr, flush=True)


def _trim(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Drop fields that cost tokens without informing a model.

    The budget block is the expensive one and it is fully available from
    ``laya_plan``; keeping a summary here means every answer does not carry a
    paragraph of token accounting. ``confidence_semantics`` is kept, because it is
    the one piece of context that stops the number being misread.
    """
    out = dict(payload)
    budget = out.pop("budget", None)
    if isinstance(budget, Mapping):
        out["budget_summary"] = {
            "fits": budget.get("fits"),
            "head_max_len": budget.get("head_max_len"),
            "tightest_option_tokens_each": budget.get("tightest_option_tokens_each"),
            **({"recommendation": budget["recommendation"]} if budget.get("recommendation") else {}),
        }
    return out


def run_stdio(
    *,
    sidecar: Optional[str] = None,
    tools: Optional[Sequence[str]] = None,
    config: Optional[WorkerConfig] = None,
) -> int:
    """Serve MCP over stdio. Blocks until the client disconnects."""
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    unknown = [t for t in (tools or ()) if t not in (*PRIMITIVES_TOOL_NAMES, "laya_ask", "laya_plan")]
    if unknown:
        print(
            f"laya-mcp: unknown tool(s) in --filter: {', '.join(unknown)}; "
            f"known: {', '.join(PRIMITIVES_TOOL_NAMES)}, laya_ask, laya_plan",
            file=sys.stderr,
        )
        return 2

    backend = Backend(sidecar=sidecar, config=config)

    # Start the load, and do NOT wait for it here.
    #
    # Two constraints pull against each other and this is where they are settled.
    #
    # The load must not run on the event loop. FastMCP dispatches a synchronous
    # tool on the loop thread, and `import torch` plus a checkpoint load inside a
    # running loop hangs: reproduced with the MCP SDK in the driver's seat
    # (handshake in 0.4 s, then no response to `tools/call` for 120 s, parked
    # inside the numpy import), while the identical load completes in 8-13 s from
    # a separate thread. That is why this work is on a thread and not in a
    # handler.
    #
    # And the handshake must not wait for it either. Both harnesses measured here
    # - opencode and claude - allow an MCP server 30 seconds to finish
    # `initialize`. Loading first costs 19 s uncontended and 275 s while another
    # model holds the GPU, so a client sees "Failed to connect" and never reaches
    # the tool list, on a config it parsed perfectly.
    #
    # So: run it in the background, answer `initialize` and `tools/list`
    # immediately, and let the first call that actually needs the model wait for
    # it through `Backend.wait_warm`. A failure is re-raised there, which is where
    # it becomes a structured error the caller can read, rather than a server that
    # never appears.
    if sidecar is None:
        backend.start_warm()

    try:
        server = build_server(backend, tools)
        server.run(transport="stdio")
    finally:
        backend.close()
    return 0


#: The tool names a caller may pass to ``--filter``.
PRIMITIVES_TOOL_NAMES = ("laya_noul", "laya_choice", "laya_score")
