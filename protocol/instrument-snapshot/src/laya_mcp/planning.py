"""Token-budget preflight: what will be cut, before the answer is computed.

Laya truncates two different things, both silently, and neither is reported in
its result:

*The state.* ``build_sequence`` gives the state whatever room is left after the
instructions and options (``room = max(0, max_len - len(ids) - 1)``) and slices
it to that length **from the front** (``st[:room]`` with ``truncate_left=False``).
So a long document loses its *tail* - which for a contract, a log, or an email
thread is often where the answer was - and the model then answers about the part
that survived, at full confidence, with nothing in the response to say a cut
happened. Upstream's own issue #49 notes the related cost: the state is
re-encoded for every question, so the cut is also paid repeatedly.

That direction is a default, not a law: ``truncate_left`` reverses it, and a
sidecar started with ``--truncate-left`` keeps the tail instead. Every sentence
this module generates about the cut therefore names the end that was actually
kept, and the report carries it as a field (``kept``) as well as in prose, so a
caller never has to infer the direction from a phrase.

*The options.* Each option body is cut to 48 tokens; if the total still does not
leave 16 tokens for the instructions, every option is re-cut to
``max(4, (head_max_len - 16) // option_count)``. A 77-label question therefore
gives each label ~4 tokens, which is the documented cause of the Banking77
collapse (0.425 against Jev's 0.870). Options are never rejected for being
numerous - only silently shortened until they are indistinguishable.

This module computes both, exactly where it can and honestly where it cannot.

**What is exact and what is not.** The option budget is exact: it is pure
arithmetic over ``head_max_len`` and the option count, reproducing
``build_sequence`` line for line. The state budget is a *character* estimate
unless a tokenizer is supplied, because the real number is a token count and this
package will not pretend to tokenize. The estimate is deliberately pessimistic
for two reasons: it divides by the model's own words-per-token ratio, and it
counts the serialized JSON form of a mapping rather than the mapping itself,
which is what actually gets sent.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional, Sequence

from .capability import Capability
from .protocol import Question

#: Tokens per character, used only when no tokenizer is available. English prose
#: runs about 4 characters per token for this family of encoders. Non-Latin
#: scripts are far denser per character, so the estimate is scaled up rather
#: than left to be wrong in the dangerous direction.
_CHARS_PER_TOKEN = 4.0

#: Multiplier applied to the estimated token count. The state estimate is a
#: lower bound on how much room is needed, so the plan reserves more than it
#: thinks it needs and reports an overflow slightly early rather than slightly
#: late. Being wrong in this direction costs a warning; the other direction costs
#: a silently truncated answer.
_SAFETY = 1.15

#: Laya's own floor for "there is enough left for the instructions".
_MIN_INSTRUCTION_TOKENS = 16

#: The per-option ceiling in ``build_sequence`` before the fallback path.
_PER_OPTION_CEILING = 48


def serialized_state_chars(state: Any) -> int:
    """The character length of the state as Laya will actually serialize it.

    Mirrors ``serialize_state``: a ``str`` passes through unchanged, anything
    else is ``json.dumps``-ed with ``ensure_ascii=False``. Counting the object's
    own ``len`` would undercount a mapping by the JSON punctuation, which on a
    small object is a material fraction.
    """
    if isinstance(state, str):
        return len(state)
    try:
        return len(json.dumps(state, ensure_ascii=False))
    except (TypeError, ValueError):
        return len(str(state))


def _looks_non_latin(text: str, sample: int = 4000) -> bool:
    """Whether the text is mostly non-Latin letters.

    Used only to pick a denser characters-per-token ratio. CJK and similar
    scripts are close to one token per character, so treating them as four would
    under-reserve by 4x and produce exactly the silent truncation this module
    exists to prevent.
    """
    head = text[:sample]
    letters = [c for c in head if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if ord(c) < 0x0250)
    return (latin / len(letters)) < 0.5


def _render_options_length(question: Question) -> int:
    """Characters the rendered option text contributes.

    Reproduces ``render_options`` closely enough to size the head: a choice option
    renders as ``"label: description"`` (or just the label when the description is
    ``None`` or empty); a score level as ``"level i: description"``; a noul as its
    two outcome strings or Laya's generic defaults.
    """
    total = 0
    if question.type == "choice":
        criteria = question.criteria
        if isinstance(criteria, Mapping):
            for label, desc in criteria.items():
                total += len(str(label))
                if desc is not None and desc != "":
                    total += len(_render_value(desc)) + 2  # ": "
        elif isinstance(criteria, (list, tuple)):
            for label in criteria:
                total += len(str(label))
    elif question.type == "score":
        criteria = question.criteria or []
        if isinstance(criteria, (list, tuple)):
            for index, level in enumerate(criteria):
                total += len("level 0: ") + len(str(level))
                if index >= 10:
                    total += 1  # extra digit
        elif isinstance(criteria, Mapping):
            for index, level in enumerate(criteria.values()):
                total += len("level 0: ") + len(str(level))
    else:  # noul
        criteria = question.criteria if isinstance(question.criteria, Mapping) else {}
        true_text = criteria.get("true")
        false_text = criteria.get("false")
        total += len("false: ") + (
            len(_render_value(false_text)) if false_text not in (None, "")
            else len("no, the statement does not hold")
        )
        total += len("true: ") + (
            len(_render_value(true_text)) if true_text not in (None, "")
            else len("yes, the statement holds")
        )
    return total


def _render_value(value: Any) -> str:
    """One criterion value as text, mirroring ``render_criterion``."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    except (TypeError, ValueError):
        return str(value)


def request_text(state: Any, questions: Mapping[str, Question]) -> str:
    """Every character of a request that reaches the model.

    The state, each question's instructions, and all the option text - not just
    the state. Laya renders one sequence, so a Chinese question asked about an
    English document is still a Chinese request.
    """
    parts: list[str] = [state if isinstance(state, str) else _render_value(state)]
    for question in questions.values():
        parts.append(_render_value(question.instructions))
        criteria = question.criteria
        if isinstance(criteria, Mapping):
            for label, description in criteria.items():
                parts.append(str(label))
                if description is not None and description != "":
                    parts.append(_render_value(description))
        elif isinstance(criteria, (list, tuple)):
            parts.extend(_render_value(item) for item in criteria)
    return "\n".join(parts)


def script_caveat(
    capability: Capability, state: Any, questions: Mapping[str, Question]
) -> Optional[str]:
    """A warning when the request is in a script this checkpoint cannot read.

    The published caveat covers only half of the problem. Laya's detector names
    seven Latin-script languages and treats everything else as English, and
    ``languages_reliably_detected`` says so - but a Khmer or Chinese request is
    not "another Latin-script language", it is text the encoder has no vocabulary
    for. Upstream measures 0.000 accuracy on Khmer at 0.952 confidence, and the
    response said nothing at all. This is that missing sentence.

    ``english`` and ``typed-decisions`` are both English-encoder checkpoints, so
    only ``multilingual`` is exempt.
    """
    if capability.checkpoint == "multilingual":
        return None
    if not _looks_non_latin(request_text(state, questions)):
        return None
    return (
        f"the request is mostly non-Latin script and `{capability.checkpoint}` cannot read it: "
        "the detector covers en/fr/de/es/pt/it/nl and assumes English for everything else, so "
        "these probabilities are not meaningful - upstream measures 0.000 accuracy on Khmer at "
        "0.952 confidence. Serve the multilingual checkpoint (`laya-mcp serve --model "
        "multilingual`) for non-Latin text, and treat an answer from this one as unusable."
    )


@dataclass
class QuestionPlan:
    """The budget for one question in a batch."""

    question_id: str
    type: str
    option_count: int
    option_tokens_each: int
    """Exact, from the same arithmetic ``build_sequence`` uses."""

    options_compressed: bool
    """True when the fallback path fired, so options were re-cut below 48 tokens.

    This is the signal that a high-cardinality question is degrading. It fires
    for a choice with roughly 4 or more options at the English checkpoint's
    default ``head_max_len`` of 192, which is well inside ordinary use."""

    head_tokens_estimated: int
    state_tokens_estimated: int
    state_room_estimated: int
    would_truncate_state: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetPlan:
    """The budget for a whole batch, with a verdict.

    ``fits`` is the single field most callers should read: it is true when no
    state truncation is expected and no question's options were compressed hard
    enough to be unreadable.
    """

    checkpoint: str
    max_len: int
    head_max_len: int
    exact: bool
    """False when the state figures are a character estimate rather than a token
    count. The option figures are exact either way."""

    truncate_left: bool = False
    """Which end of an oversized state survives: ``False`` keeps the front (Laya's
    default), ``True`` keeps the tail. The server decides this, not the request."""

    questions: tuple[QuestionPlan, ...] = field(default_factory=tuple)

    state_chars: int = 0
    state_tokens_estimated: int = 0

    fits: bool = True
    warnings: tuple[str, ...] = field(default_factory=tuple)
    recommendation: Optional[str] = None

    @property
    def worst_question(self) -> Optional[QuestionPlan]:
        """The question whose options were squeezed hardest."""
        if not self.questions:
            return None
        return min(self.questions, key=lambda q: (q.option_tokens_each, -q.option_count))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["questions"] = [q.to_dict() for q in self.questions]
        payload["warnings"] = list(self.warnings)
        worst = self.worst_question
        if worst is not None:
            payload["worst_question"] = worst.question_id
            payload["tightest_option_tokens_each"] = worst.option_tokens_each
        return payload

    def truncation_report(self) -> Optional[dict[str, Any]]:
        """What was, or would be, cut. ``None`` when nothing was.

        Shaped so it can be dropped straight onto a response as ``truncated``.
        """
        state_cut = any(q.would_truncate_state for q in self.questions)
        squeezed = [q for q in self.questions if q.options_compressed]
        if not state_cut and not squeezed:
            return None
        report: dict[str, Any] = {}
        if state_cut:
            kept, dropped, survives = (
                ("TAIL", "front", "suffix") if self.truncate_left else ("FRONT", "tail", "prefix")
            )
            report["state"] = {
                "estimated": True,
                "state_chars": self.state_chars,
                "state_tokens_estimated": self.state_tokens_estimated,
                # Machine-readable, because the prose below is the only other place
                # the direction appears and a caller should not have to parse it.
                "kept": kept.lower(),
                "note": (
                    f"the state exceeded its token budget and Laya keeps the {kept} of it, "
                    f"discarding the {dropped}; the answer is about the surviving {survives} only"
                ),
            }
        if squeezed:
            report["options"] = {
                "estimated": False,
                "questions": [
                    {
                        "question_id": q.question_id,
                        "option_count": q.option_count,
                        "tokens_each": q.option_tokens_each,
                    }
                    for q in squeezed
                ],
                "note": (
                    "options were re-cut below the 48-token ceiling to fit head_max_len, so "
                    "labels may no longer be distinguishable from one another"
                ),
            }
        return report


def plan_questions(
    capability: Capability,
    state: Any,
    questions: Mapping[str, Question],
    *,
    tokenizer: Any = None,
    truncate_left: bool = False,
) -> BudgetPlan:
    """Plan a batch against a checkpoint's budget, without running it.

    Pass ``tokenizer`` (Laya's own, from a loaded ``Agent``) to replace the
    character estimate with real token counts. Without one the option arithmetic
    is still exact and the state figure is a labelled estimate.

    The per-question head cost is computed for every question independently,
    because Laya does too: each question becomes its own sequence and the state
    is appended to each. A batch of ten questions therefore pays for the state
    ten times, and the binding constraint is the *longest* head, not the sum.
    """
    warnings: list[str] = []

    state_text = state if isinstance(state, str) else None
    if state_text is None:
        try:
            state_text = json.dumps(state, ensure_ascii=False)
        except (TypeError, ValueError):
            state_text = str(state)

    chars = serialized_state_chars(state)
    dense = _looks_non_latin(state_text)
    per_token = 1.0 if dense else _CHARS_PER_TOKEN

    if tokenizer is not None:
        try:
            state_tokens = len(
                tokenizer(state_text, add_special_tokens=False)["input_ids"]
            )
            exact = True
        except Exception:  # noqa: BLE001 - a tokenizer that cannot count is not fatal
            state_tokens = int(chars / per_token * _SAFETY)
            exact = False
            warnings.append(
                "the tokenizer could not count the state, so the state budget is an estimate"
            )
    else:
        state_tokens = int(chars / per_token * _SAFETY)
        exact = False

    plans: list[QuestionPlan] = []
    for question_id, question in questions.items():
        option_count = _option_count(question)
        option_tokens_each = capability.option_token_budget(option_count)
        options_compressed = option_tokens_each < _PER_OPTION_CEILING + 1

        # Head = question-type prefix + instructions + one mask token and the
        # rendered text per option. Laya truncates the instruction text to
        # whatever is left after the options, with a floor of 8.
        instruction_chars = len(str(question.instructions))
        instruction_tokens = int(instruction_chars / per_token) + 3  # "<type> question: "
        options_tokens = option_tokens_each * max(1, option_count)
        head_tokens = options_tokens + instruction_tokens + 2  # CLS + SEP

        if head_tokens > capability.head_max_len:
            head_tokens = capability.head_max_len
            # The instructions get whatever survives, floored at 8 exactly as
            # build_sequence does (`head_ids[: max(8, opt_budget)]`).
            instruction_tokens = max(8, capability.head_max_len - options_tokens)
            if instruction_tokens <= 8 and instruction_chars > 0:
                warnings.append(
                    f"question {question_id!r} leaves only {instruction_tokens} tokens for its "
                    "own instructions, so the question text is being cut"
                )

        # Laya's own budget: max_len minus the head it actually built, minus the
        # trailing SEP, floored at zero.
        room_tokens = max(0, capability.max_len - head_tokens - 1)
        would_truncate = state_tokens > room_tokens

        plans.append(
            QuestionPlan(
                question_id=question_id,
                type=question.type,
                option_count=option_count,
                option_tokens_each=option_tokens_each,
                options_compressed=options_compressed,
                head_tokens_estimated=head_tokens,
                state_tokens_estimated=state_tokens,
                state_room_estimated=room_tokens,
                would_truncate_state=would_truncate,
            )
        )

    squeezed = [p for p in plans if p.options_compressed and p.option_count > 1]
    if squeezed:
        worst = min(squeezed, key=lambda p: p.option_tokens_each)
        if capability.checkpoint != "multilingual":
            warnings.append(
                f"question {worst.question_id!r} has {worst.option_count} options sharing "
                f"{capability.head_max_len} tokens, which is ~{worst.option_tokens_each} tokens "
                "per label; choice accuracy falls off sharply in this range"
            )

    any_truncation = any(p.would_truncate_state for p in plans)
    if any_truncation and not exact:
        warnings.append(
            "the state is close to or over its budget, so its "
            f"{'front' if truncate_left else 'tail'} is likely to be discarded; "
            "raise max_len at startup, shorten the state, or set strict=true to refuse instead"
        )

    recommendation = _recommend(capability, plans, any_truncation, squeezed)

    return BudgetPlan(
        checkpoint=capability.checkpoint,
        max_len=capability.max_len,
        head_max_len=capability.head_max_len,
        exact=exact,
        truncate_left=truncate_left,
        questions=tuple(plans),
        state_chars=chars,
        state_tokens_estimated=state_tokens,
        fits=not any_truncation,
        warnings=tuple(warnings),
        recommendation=recommendation,
    )


def _option_count(question: Question) -> int:
    """How many options Laya will render for this question.

    A ``noul`` always renders exactly two (``render_options`` returns
    ``[false, true]``), which is why a noul never hits the option squeeze.
    """
    if question.type == "noul":
        return 2
    criteria = question.criteria
    if isinstance(criteria, Mapping):
        return len(criteria)
    if isinstance(criteria, (list, tuple)):
        return len(criteria)
    return 0


def _recommend(
    capability: Capability,
    plans: Sequence[QuestionPlan],
    any_truncation: bool,
    squeezed: Sequence[QuestionPlan],
) -> Optional[str]:
    """The single most useful next action, or ``None`` when the plan is fine."""
    if not plans:
        return None
    if any_truncation and squeezed:
        return (
            "raise both `head_max_len` and `max_len` at startup, and split the largest "
            "question into a two-step choice"
        )
    if any_truncation:
        return (
            f"raise `max_len` above {capability.max_len} at startup, shorten the state, or "
            "split the state across several calls"
        )
    if squeezed:
        worst = min(squeezed, key=lambda p: p.option_tokens_each)
        needed = capability.max_options()
        return (
            f"question {worst.question_id!r} has {worst.option_count} options and this "
            f"checkpoint keeps them distinguishable to about {needed}; raise `head_max_len` at "
            "startup, shorten the label text, or shard the choice into two steps"
        )
    return None
