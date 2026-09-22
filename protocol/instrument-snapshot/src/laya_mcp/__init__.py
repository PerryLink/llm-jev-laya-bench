"""laya-mcp - the installable, honest layer around Laya's typed decisions.

Laya is a fast non-autoregressive "System 1" decision model: it answers typed
questions (``noul``, ``choice``, ``score``) over a state and returns
probabilities, in a single forward pass. It is genuinely good and it is a
research artifact. This package is the part that makes it survive contact with a
server:

* :mod:`laya_mcp.capability` - the checkpoint's real limits, read from its own
  ``rl_agent_config.json`` rather than from the README.
* :mod:`laya_mcp.errors` - every way Laya fails, as a structured error with a
  stable code, instead of a bare ``KeyError``.
* :mod:`laya_mcp.planning` - token-budget preflight. Laya truncates the state
  silently and from the end; this says what would be cut *before* the answer is
  computed.
* :mod:`laya_mcp.validate` - the question validation Laya does not perform.
* :mod:`laya_mcp.calibration` - a persisted temperature store, so fitted numbers
  survive a restart.
* :mod:`laya_mcp.protocol` - the wire contract shared by the sidecar, the MCP
  server, and every harness adapter.

Two things this package deliberately does not do:

* It does not generate text, and it should never be asked to. A decision model
  asked to write prose produces nothing useful.
* It does not present Laya's ``confidence`` as a probability of being correct.
  That number is a normalised-entropy concentration over the option
  distribution: it falls when probability is spread out even when the top option
  is right. See :mod:`laya_mcp.calibration`.
"""

from __future__ import annotations

__version__ = "0.2.1"

from .capability import Capability, read_capability
from .errors import (
    CapacityError,
    DeviceDegradedError,
    ErrorCode,
    InternalError,
    InvalidQuestionError,
    LayaMcpError,
    ModelUnavailableError,
    OutOfMemoryError,
    QuestionTooLargeError,
    SidecarUnreachableError,
    StateTruncatedError,
    UnknownModelError,
    WeightsUnavailableError,
    from_payload,
    translate,
)
from .planning import BudgetPlan, plan_questions, request_text, script_caveat, serialized_state_chars
from .protocol import (
    ANSWER_TYPES,
    PRIMITIVES,
    Answer,
    AskRequest,
    AskResponse,
    Question,
    RoutingInfo,
    Usage,
)
from .validate import validate_questions

__all__ = [
    "__version__",
    # capability
    "Capability",
    "read_capability",
    # errors
    "LayaMcpError",
    "ErrorCode",
    "InvalidQuestionError",
    "QuestionTooLargeError",
    "UnknownModelError",
    "ModelUnavailableError",
    "WeightsUnavailableError",
    "SidecarUnreachableError",
    "OutOfMemoryError",
    "StateTruncatedError",
    "CapacityError",
    "DeviceDegradedError",
    "InternalError",
    "translate",
    "from_payload",
    # planning
    "BudgetPlan",
    "plan_questions",
    "request_text",
    "script_caveat",
    "serialized_state_chars",
    # protocol
    "ANSWER_TYPES",
    "PRIMITIVES",
    "Answer",
    "AskRequest",
    "AskResponse",
    "Question",
    "RoutingInfo",
    "Usage",
    # validate
    "validate_questions",
]
