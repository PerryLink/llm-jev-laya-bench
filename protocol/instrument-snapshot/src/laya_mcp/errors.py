"""Every way a Laya call fails, as a structured error.

Laya's own validation is close to absent, and what it does raise is not shaped
for a caller. Read from its source (``laya/agent.py`` and ``laya/common.py``),
the failure modes are:

===============================================  =====================================
what the caller did                              what Laya raises
===============================================  =====================================
``type`` not in ``{choice, score, noul}``        ``KeyError`` (``QTYPES[q["t"]]``)
``choice``/``score`` with no ``criteria``        ``KeyError('criteria')``
a question with no ``instructions``              ``KeyError('instructions')``
``score`` whose ``criteria`` is not a sequence   ``IndexError`` / ``TypeError``
too many options for ``head_max_len``            ``ValueError`` (the one real check)
unknown checkpoint name to ``Router``            ``ValueError``
checkpoint not on disk / bad architecture        ``FileNotFoundError`` / ``ValueError``
GPU out of memory                                ``torch.cuda.OutOfMemoryError``
===============================================  =====================================

A ``KeyError`` that reaches an HTTP handler becomes a 500 and a stack trace; the
same ``KeyError`` reaching an MCP tool becomes an opaque protocol error. Neither
tells the caller that *they* passed a bad question type. So every one of these is
translated into a :class:`LayaMcpError` carrying a stable machine-readable
:class:`ErrorCode`, an HTTP status for the sidecar, and a message that names the
offending question id.

The codes are part of the wire contract: a client may branch on them, so they
must not be renamed without a version bump.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional


class ErrorCode(str, Enum):
    """Stable machine-readable failure codes.

    Subclasses :class:`str` so a code serialises as a plain string on the wire
    and compares equal to its literal, which keeps JSON schemas simple.
    """

    INVALID_QUESTION = "invalid_question"
    """The question batch is malformed: bad type, missing instructions, missing
    criteria, or a ``criteria`` shape the primitive cannot use."""

    QUESTION_TOO_LARGE = "question_too_large"
    """Valid in shape, but its options cannot fit the checkpoint's per-question
    option budget. Actionable: raise ``head_max_len``, shorten the option text,
    or use two-step coarse-to-fine selection."""

    UNKNOWN_MODEL = "unknown_model"
    """The requested checkpoint name is not one the router knows."""

    MODEL_UNAVAILABLE = "model_unavailable"
    """The checkpoint exists but cannot be loaded: missing weights, missing
    ``rl_agent_config.json``, or an architecture mismatch. A startup fault, not
    a per-request one."""

    WEIGHTS_UNAVAILABLE = "weights_unavailable"
    """The weights could not be fetched from the Hub - a cold-start network
    problem rather than a bad request."""

    SIDECAR_UNREACHABLE = "sidecar_unreachable"
    """Nothing is answering at the sidecar URL.

    Not an internal fault. It is the ordinary state of a harness that started
    before its ``laya-mcp serve``, and it is retryable because the sidecar may
    still be loading. Reporting it as ``internal`` - which is what happened
    before this code existed - sent the caller looking for a bug in the wrong
    program, and made the one structured error a user is most likely to meet the
    least useful of them."""

    OUT_OF_MEMORY = "out_of_memory"
    """The device ran out of memory. Note that Laya's own recovery is a
    permanent, silent demotion to CPU: see :class:`OutOfMemoryError`."""

    DEVICE_DEGRADED = "device_degraded"
    """Not an exception - a state. Laya fell back to CPU (or to fp32) and never
    returns to the accelerator. Surfaced so a caller is not silently served
    answers an order of magnitude slower than the ones it measured."""

    STATE_TRUNCATED = "state_truncated"
    """The state did not fit its budget and was cut. Raised only when the caller
    asked for strict behaviour; otherwise reported as a warning on the result."""

    CAPACITY = "capacity"
    """The server is at its concurrency or memory ceiling. Retryable."""

    INTERNAL = "internal"
    """A bug here, or a Laya failure we did not anticipate. The original
    exception is preserved on ``cause``."""


#: The HTTP status the sidecar returns for each code. Chosen so a client can act
#: without parsing the message: 4xx means "fix your request", 5xx means "retry or
#: fix the deployment".
_HTTP_STATUS: Mapping[ErrorCode, int] = {
    ErrorCode.INVALID_QUESTION: 400,
    ErrorCode.QUESTION_TOO_LARGE: 400,
    ErrorCode.UNKNOWN_MODEL: 400,
    ErrorCode.STATE_TRUNCATED: 400,
    ErrorCode.MODEL_UNAVAILABLE: 500,
    ErrorCode.WEIGHTS_UNAVAILABLE: 503,
    ErrorCode.SIDECAR_UNREACHABLE: 503,
    ErrorCode.OUT_OF_MEMORY: 503,
    ErrorCode.DEVICE_DEGRADED: 503,
    ErrorCode.CAPACITY: 429,
    ErrorCode.INTERNAL: 500,
}


class LayaMcpError(Exception):
    """Base class for every failure this package raises.

    Carries the things a caller needs to act: a stable :attr:`code`, a message,
    an optional :attr:`question_id` naming which question was at fault, and an
    optional :attr:`hint` with the concrete fix. :attr:`cause` preserves the
    original exception so a traceback is never lost.
    """

    code: ErrorCode = ErrorCode.INTERNAL

    def __init__(
        self,
        message: str,
        *,
        question_id: Optional[str] = None,
        hint: Optional[str] = None,
        cause: Optional[BaseException] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.question_id = question_id
        self.hint = hint
        self.cause = cause
        self.details = dict(details) if details else {}

    @property
    def http_status(self) -> int:
        """The status the sidecar should return for this error."""
        return _HTTP_STATUS.get(self.code, 500)

    def to_dict(self) -> dict[str, Any]:
        """The JSON body sent to a caller.

        Deliberately flat and stable. ``retryable`` is derived rather than
        stored so a code cannot lie about it.
        """
        payload: dict[str, Any] = {
            "error": self.code.value,
            "message": self.message,
            "retryable": self.http_status in (429, 503),
        }
        if self.question_id is not None:
            payload["question_id"] = self.question_id
        if self.hint is not None:
            payload["hint"] = self.hint
        if self.details:
            payload["details"] = self.details
        return payload

    def __str__(self) -> str:  # pragma: no cover - trivial
        parts = [f"[{self.code.value}] {self.message}"]
        if self.question_id:
            parts.append(f"(question {self.question_id!r})")
        if self.hint:
            parts.append(f"hint: {self.hint}")
        return " ".join(parts)


class InvalidQuestionError(LayaMcpError):
    """The question batch is malformed. Corresponds to Laya's ``KeyError``."""
    code = ErrorCode.INVALID_QUESTION


class QuestionTooLargeError(LayaMcpError):
    """The question's options cannot fit the checkpoint's option budget.

    This is Laya's only native validation, and its message does not say what to
    do about it. :attr:`details` carries the numbers that make it actionable.
    """
    code = ErrorCode.QUESTION_TOO_LARGE


class UnknownModelError(LayaMcpError):
    """The requested checkpoint name is not one the router knows."""
    code = ErrorCode.UNKNOWN_MODEL


class ModelUnavailableError(LayaMcpError):
    """The checkpoint cannot be loaded. A startup fault, not a request fault."""
    code = ErrorCode.MODEL_UNAVAILABLE


class WeightsUnavailableError(LayaMcpError):
    """The weights could not be fetched. Cold-start network problem."""
    code = ErrorCode.WEIGHTS_UNAVAILABLE


class SidecarUnreachableError(LayaMcpError):
    """Nothing is listening at the sidecar URL.

    Separate from the base class on purpose: the base defaults to
    :attr:`ErrorCode.INTERNAL`, and "internal" tells a caller to look for a bug
    in this package when the real answer is "the process you were supposed to
    start is not running". 503 makes it retryable, which it is.
    """
    code = ErrorCode.SIDECAR_UNREACHABLE


class OutOfMemoryError(LayaMcpError):
    """The device ran out of memory.

    Worth knowing: Laya handles this itself, and its handling is destructive.
    On a CUDA OOM during placement or inference it prints a warning and moves
    the model to CPU in fp32, in place, permanently - and the ``Agent`` holds no
    flag saying so. A process that hits this once keeps answering, roughly 10-15x
    slower, and nothing in the response admits it. So this package tracks the
    demotion itself (see :class:`~laya_mcp.capability.Capability` and the
    ``device`` field on a response) rather than trusting the library to recover.
    """
    code = ErrorCode.OUT_OF_MEMORY


class StateTruncatedError(LayaMcpError):
    """The state did not fit and was cut.

    Laya truncates the state from the *end* (``truncate_left=False`` in
    ``build_sequence``), so the tail of a long document is what disappears, and
    nothing in the result marks it. A sidecar started with ``--truncate-left``
    reverses that and keeps the tail, which is why the details carried here name the
    end that was kept rather than assuming one. This is raised only in strict mode;
    the default is to answer and report ``state_truncated`` on the response.
    """
    code = ErrorCode.STATE_TRUNCATED


class CapacityError(LayaMcpError):
    """At the concurrency or memory ceiling. Retryable."""
    code = ErrorCode.CAPACITY


class DeviceDegradedError(LayaMcpError):
    """Laya silently fell back to CPU. Retryable only by fixing the deployment."""
    code = ErrorCode.DEVICE_DEGRADED


#: errno values that mean the host refused to hand over memory.
#:
#: 12 is ``ENOMEM`` on both POSIX and Windows. 8 is ``ERROR_NOT_ENOUGH_MEMORY``,
#: and 1455 is ``ERROR_COMMITMENT_LIMIT`` - "the paging file is too small for this
#: operation to complete".
#:
#: The numbers matter because a Windows OSError can carry a raw Win32 code as its
#: ``errno`` when there is no POSIX equivalent to map onto. Measured on this
#: machine: a safetensors load that exhausted Windows' commit charge arrived as a
#: plain ``OSError`` with ``errno=1455`` and ``winerror=None``, and its message was
#: localized - "the paging file is too small" in Chinese, containing no ASCII at
#: all. A classifier keying on the words "out of memory", or on a class name
#: containing ``OutOfMemory`` (a torch CUDA fault is a different type entirely),
#: matches neither, so the failure was reported as a generic internal fault:
#: HTTP 500 with ``retryable: false``, when the honest answer is 503 and
#: retryable. This is why the check below asks the errno first and the words last.
_MEMORY_ERRNOS = frozenset({12, 8, 1455})


def _is_memory_failure(exc: BaseException) -> bool:
    """Whether this is the host declining to commit memory."""
    if isinstance(exc, MemoryError):
        return True
    if getattr(exc, "errno", None) in _MEMORY_ERRNOS:
        return True
    if getattr(exc, "winerror", None) in _MEMORY_ERRNOS:
        return True
    return "OutOfMemory" in type(exc).__name__ or "out of memory" in str(exc).lower()


def translate(exc: BaseException, *, question_id: Optional[str] = None) -> LayaMcpError:
    """Map an exception from Laya onto a :class:`LayaMcpError`.

    The order of the checks matters and mirrors how Laya actually behaves:
    ``KeyError`` is its generic "you gave me something I did not expect" for a
    bad type, a missing ``criteria``, and a missing ``instructions`` alike, so
    the message is inspected to say which.

    Anything already a :class:`LayaMcpError` passes through unchanged, so this
    is safe to call at every boundary.
    """
    if isinstance(exc, LayaMcpError):
        return exc

    if isinstance(exc, KeyError):
        # Laya raises KeyError from QTYPES[q["t"]] for an unknown primitive, and
        # from q["criteria"] / q["instr"] for a missing field. The key is the
        # only thing distinguishing them.
        key = exc.args[0] if exc.args else ""
        if key in ("criteria", "instructions", "type"):
            return InvalidQuestionError(
                f"the question is missing the required field {key!r}",
                question_id=question_id,
                hint=(
                    "a choice and a score both require `criteria`; every question requires "
                    "`type` and `instructions`"
                ),
                cause=exc,
            )
        return InvalidQuestionError(
            f"unknown question type {key!r}",
            question_id=question_id,
            hint="`type` must be one of 'choice', 'score', 'noul'",
            cause=exc,
        )

    if isinstance(exc, ValueError):
        text = str(exc)
        if "exceed head_max_len" in text or "head_max_len" in text:
            return QuestionTooLargeError(
                text,
                question_id=question_id,
                hint=(
                    "the options do not fit the checkpoint's per-question option budget. "
                    "Lower the option count, shorten the option text, raise head_max_len at "
                    "startup, or split into a two-step coarse-to-fine choice."
                ),
                cause=exc,
            )
        if "Unknown model" in text or "unknown model" in text:
            return UnknownModelError(text, cause=exc)
        return InternalError(f"Laya rejected the request: {text}", cause=exc)

    if isinstance(exc, FileNotFoundError):
        return ModelUnavailableError(
            str(exc),
            hint="the checkpoint is absent or incomplete; `laya-mcp doctor` reports what is loadable",
            cause=exc,
        )

    if isinstance(exc, (IndexError, TypeError)):
        # A `score` whose criteria is not a sequence lands here.
        return InvalidQuestionError(
            f"malformed criteria: {exc}",
            question_id=question_id,
            hint="a score's `criteria` is an ordered array of level descriptions; a choice's is a label->description map",
            cause=exc,
        )

    if isinstance(exc, AttributeError):
        # Measured against the real checkpoint: a `choice` with no `criteria`
        # raises `AttributeError: 'NoneType' object has no attribute 'items'` from
        # `render_options` (which calls `crit.items()`), NOT a KeyError. Reading
        # the source suggests KeyError, because `system_one` does `q["crit"]` - but
        # the key EXISTS and its value is None, so the failure happens one call
        # deeper than the source alone implies. Only this exact shape is claimed
        # as a missing-criteria bug; any other AttributeError is left as the
        # internal fault it is.
        if "'NoneType' object has no attribute" in str(exc):
            return InvalidQuestionError(
                "the question's `criteria` is None",
                question_id=question_id,
                hint=(
                    "a choice needs a mapping of permitted labels to descriptions, and a score "
                    "an ordered array of levels; for a noul, criteria is optional"
                ),
                cause=exc,
            )
        return InternalError(f"unexpected AttributeError: {exc}", cause=exc)

    name = type(exc).__name__
    if _is_memory_failure(exc):
        return OutOfMemoryError(
            str(exc) or f"{name} while loading or running the model",
            hint=(
                "the host could not commit the memory this needs. A checkpoint that was "
                "not preloaded is loaded on first use, so the request that names it can be "
                "the one that runs out; preload it at startup with `--model` / `--also`, "
                "or free memory and retry. A host resource limit, not a bad request."
            ),
            cause=exc,
        )

    if "huggingface" in type(exc).__module__ or "ConnectionError" in name:
        return WeightsUnavailableError(
            str(exc),
            hint="the weights are not in the local Hub cache and could not be fetched",
            cause=exc,
        )

    return InternalError(f"unexpected {name}: {exc}", cause=exc)


class InternalError(LayaMcpError):
    """A bug here, or a Laya failure not otherwise anticipated."""
    code = ErrorCode.INTERNAL


#: Every concrete class, keyed by the code it carries.
#:
#: Defined at the end of the module because :class:`InternalError` is declared
#: here, not with its siblings - it is the fallback :func:`translate` returns, and
#: it reads better beside the branch that produces it.
_BY_CODE: Mapping[ErrorCode, type[LayaMcpError]] = {
    cls.code: cls
    for cls in (
        InvalidQuestionError,
        QuestionTooLargeError,
        UnknownModelError,
        ModelUnavailableError,
        WeightsUnavailableError,
        SidecarUnreachableError,
        OutOfMemoryError,
        StateTruncatedError,
        CapacityError,
        DeviceDegradedError,
        InternalError,
    )
}


def from_payload(
    payload: Mapping[str, Any], *, fallback: str = "the upstream server reported a failure"
) -> LayaMcpError:
    """Rebuild an error that arrived as JSON, keeping its code.

    Without this every error crossing the sidecar hop comes back as the *base*
    class, whose code is ``internal``. Measured: asking the MCP server for an
    unknown question type returned ``error: "internal"`` for a response the
    sidecar had labelled ``invalid_question`` with an HTTP 400 - so the one
    worked example in the README ("``KeyError('ranking')`` becomes
    ``invalid_question`` naming the type") was false for every caller that went
    through MCP, which is the primary interface.

    A code that does not survive the hop is not a code. The message, the
    offending question id, the hint and the details all come across too, so the
    rebuilt error is the same error rather than a summary of one.
    """
    raw = payload.get("error")
    try:
        code = ErrorCode(raw)
    except ValueError:
        code = ErrorCode.INTERNAL
    details = payload.get("details")
    return _BY_CODE.get(code, LayaMcpError)(
        str(payload.get("message") or fallback),
        question_id=payload.get("question_id") or None,
        hint=payload.get("hint") or None,
        details=details if isinstance(details, Mapping) else None,
    )
