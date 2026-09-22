"""The question validation Laya does not perform.

Read ``Agent.system_one`` and you will find almost no validation. An unknown
``type`` is a ``KeyError`` from ``QTYPES[q["t"]]``; a missing ``criteria`` is a
``KeyError`` from ``q["crit"]``; a ``score`` whose criteria is a string raises
``IndexError`` or ``TypeError`` depending on the string. None of these name the
offending question, and all of them are indistinguishable from a bug in the
model. The one real check is the option-budget ``ValueError``.

So every check lives here, run before anything reaches Laya, and each raises a
:class:`~laya_mcp.errors.LayaMcpError` carrying the question id and a hint. This
is also where the rules that are *ours* rather than Laya's are enforced - an
option-count ceiling, a score-level count, unique ids - and they are marked as
ours so a future reader does not mistake them for upstream behaviour.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .capability import Capability
from .errors import InvalidQuestionError, QuestionTooLargeError
from .protocol import PRIMITIVES, Question

#: Level counts a ``score`` may declare. Laya itself accepts anything and simply
#: sums ``i * p[i]``, so a one-level scale returns a constant 0 and a fifty-level
#: scale is unreadable. The lower bound is ours (a scale needs two points to be a
#: scale); the upper bound matches this project's own rubric guidance rather than
#: an upstream limit.
MIN_SCORE_LEVELS = 2
MAX_SCORE_LEVELS = 10

#: A hard ceiling on options for one question, independent of the token budget.
#: Chosen to be well above the quality cliff (~20) so it only catches input that
#: is certainly a mistake - a pasted taxonomy, say - while leaving the honest
#: judgement about degradation to :mod:`laya_mcp.planning`.
OPTION_CEILING = 250

#: The only keys a ``noul``'s ``criteria`` may carry. Laya reads exactly these
#: two (``crit.get("false")`` / ``crit.get("true")``) and ignores everything else,
#: so anything else is silently dropped input.
NOUL_OUTCOME_KEYS = ("true", "false")


def validate_questions(
    questions: Mapping[str, Question],
    *,
    capability: Capability | None = None,
) -> None:
    """Validate a batch, raising on the first problem.

    Deliberately raises rather than collecting: a caller that sent three bad
    questions does not need all three messages, it needs the first one and a
    reason. Nothing here mutates the questions.

    When ``capability`` is supplied the option budget is checked too, which turns
    Laya's single ``ValueError`` into a message naming the question, the numbers,
    and the fix.
    """
    if not isinstance(questions, Mapping):
        raise InvalidQuestionError(
            f"`questions` must be an object keyed by question id, got {type(questions).__name__}",
            hint="Laya calls questions.keys(), so a list of questions can never work",
        )
    if not questions:
        raise InvalidQuestionError(
            "no questions were asked",
            hint="send at least one question; a batch with none still pays for a forward pass",
        )

    for question_id, question in questions.items():
        _validate_id(question_id)
        _validate_one(question_id, question, capability)


def _validate_id(question_id: Any) -> None:
    if not isinstance(question_id, str) or not question_id.strip():
        raise InvalidQuestionError(
            f"question ids must be non-empty strings, got {question_id!r}",
            hint="the id becomes a key in `answers`, so it has to survive JSON",
        )
    if question_id.startswith("__"):
        # Reserved so a future implementation can attach metadata to a response
        # without colliding with a caller's id.
        raise InvalidQuestionError(
            f"question id {question_id!r} uses the reserved '__' prefix"
        )


def _validate_one(
    question_id: str,
    question: Question,
    capability: Capability | None,
) -> None:
    if not isinstance(question, Question):
        raise InvalidQuestionError(
            f"question {question_id!r} is a {type(question).__name__}, not a Question",
            question_id=question_id,
        )

    qtype = question.type
    if qtype not in PRIMITIVES:
        raise InvalidQuestionError(
            f"unknown question type {qtype!r}",
            question_id=question_id,
            hint=f"`type` must be one of {', '.join(repr(p) for p in PRIMITIVES)}",
        )

    if question.instructions is None or question.instructions == "":
        raise InvalidQuestionError(
            "the question has no `instructions`",
            question_id=question_id,
            hint="say what is being asked; a bare state with no question returns an arbitrary answer",
        )

    if qtype == "noul":
        _validate_noul(question_id, question)
        return

    if question.criteria is None:
        raise InvalidQuestionError(
            f"a {qtype} question requires `criteria`",
            question_id=question_id,
            hint=(
                "a choice maps each permitted label to an optional description; a score is an "
                "ordered array of level descriptions"
            ),
        )

    if qtype == "choice":
        _validate_choice(question_id, question, capability)
    else:
        _validate_score(question_id, question)


def _validate_noul(question_id: str, question: Question) -> None:
    criteria = question.criteria
    if criteria is None:
        # Legal: Laya substitutes generic defaults. Worth allowing, but the caller
        # should know the probability is then about an unstated boundary.
        return
    if not isinstance(criteria, Mapping):
        raise InvalidQuestionError(
            f"a noul's `criteria` must be a mapping of outcome to description, got "
            f"{type(criteria).__name__}",
            question_id=question_id,
            hint='declare what "true" and what "false" mean: {"true": ..., "false": ...}',
        )
    alien = [k for k in criteria if k not in NOUL_OUTCOME_KEYS]
    if alien:
        # Not merely untidy: Laya reads only `true` and `false`, so any other key
        # is input the caller believes was used and which was dropped.
        raise InvalidQuestionError(
            f"a noul's `criteria` keys ({', '.join(repr(k) for k in alien)}) name no outcome",
            question_id=question_id,
            hint=(
                'a noul boundary says what "true" and what "false" mean; a keyed map of '
                "alternatives is a `choice`"
            ),
        )


def _validate_choice(
    question_id: str,
    question: Question,
    capability: Capability | None,
) -> None:
    criteria = question.criteria
    if isinstance(criteria, Mapping):
        count = len(criteria)
        labels = list(criteria.keys())
        if count == 0:
            raise InvalidQuestionError(
                "a choice declares no options", question_id=question_id
            )
        blank = [k for k in labels if not isinstance(k, str) or not k.strip()]
        if blank:
            raise InvalidQuestionError(
                f"choice options must be non-empty strings, got {blank[:3]!r}",
                question_id=question_id,
            )
    elif isinstance(criteria, (list, tuple)):
        count = len(criteria)
        if count == 0:
            raise InvalidQuestionError(
                "a choice declares no options", question_id=question_id
            )
        if not all(isinstance(c, str) and c.strip() for c in criteria):
            raise InvalidQuestionError(
                "every choice option must be a non-empty string",
                question_id=question_id,
                hint=(
                    "a list of labels is accepted, but a mapping is better: the description is "
                    "what makes one label distinguishable from another"
                ),
            )
    else:
        raise InvalidQuestionError(
            f"a choice's `criteria` must be a mapping or a list, got {type(criteria).__name__}",
            question_id=question_id,
        )

    _check_option_ceiling(question_id, count, capability)


def _validate_score(question_id: str, question: Question) -> None:
    criteria = question.criteria
    if isinstance(criteria, Mapping):
        raise InvalidQuestionError(
            "a score's `criteria` must be an ordered array, not a mapping",
            question_id=question_id,
            hint=(
                "a scale is ordered and a mapping is not; position is the score, so pass the "
                "levels in ascending order as a list"
            ),
        )
    if not isinstance(criteria, (list, tuple)):
        raise InvalidQuestionError(
            f"a score's `criteria` must be an ordered array, got {type(criteria).__name__}",
            question_id=question_id,
            hint="pass the levels in ascending scale order; the first entry is score 0",
        )
    if len(criteria) < MIN_SCORE_LEVELS:
        raise InvalidQuestionError(
            f"a score needs at least {MIN_SCORE_LEVELS} levels, got {len(criteria)}",
            question_id=question_id,
            hint="a single level has no scale to place the state on",
        )
    if len(criteria) > MAX_SCORE_LEVELS:
        raise InvalidQuestionError(
            f"a score accepts at most {MAX_SCORE_LEVELS} levels, got {len(criteria)}",
            question_id=question_id,
            hint="use a coarser rubric, or several questions",
        )
    missing = [i for i, level in enumerate(criteria) if level is None]
    if missing:
        # Position is the score, so a hole renumbers every level after it.
        raise InvalidQuestionError(
            f"score levels {missing!r} are null, which would renumber the rest",
            question_id=question_id,
            hint="describe every level, or use an empty string to hold a position",
        )


def _check_option_ceiling(
    question_id: str,
    count: int,
    capability: Capability | None,
) -> None:
    if count > OPTION_CEILING:
        raise QuestionTooLargeError(
            f"question {question_id!r} declares {count} options, above this project's ceiling "
            f"of {OPTION_CEILING}",
            question_id=question_id,
            hint="shard the options into a hierarchy, or ask several smaller questions",
            details={"option_count": count, "ceiling": OPTION_CEILING},
        )
    if capability is None:
        return
    room = capability.max_options()
    if count > room:
        raise QuestionTooLargeError(
            f"question {question_id!r} declares {count} options but this checkpoint keeps only "
            f"about {room} of them distinguishable",
            question_id=question_id,
            hint=(
                f"each option would receive about {capability.option_token_budget(count)} tokens "
                f"out of head_max_len={capability.head_max_len}. Raise `head_max_len` at startup, "
                "shorten the option text, or shard the choice into two steps."
            ),
            details={
                "option_count": count,
                "distinguishable_max": room,
                "head_max_len": capability.head_max_len,
                "tokens_per_option": capability.option_token_budget(count),
            },
        )
