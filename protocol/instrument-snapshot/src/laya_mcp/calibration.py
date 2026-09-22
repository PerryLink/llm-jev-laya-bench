"""Calibration: what Laya's numbers mean, and how to make them mean more.

Two separate problems, both real, and they are usually conflated.

**Problem one: ``confidence`` is not accuracy.** Laya's ``confidence`` is a
concentration statistic. For ``choice`` and ``score`` it is
``1 - H(p)/log(k)`` - a normalised entropy. For ``noul`` it is
``max(p, 1-p)``, which is a different quantity entirely. Neither is the
probability that the answer is correct. A normalised entropy is *low* when
probability is spread across many options even if the top option is right, and
*high* on a confident wrong answer - which is exactly the failure documented for
the English checkpoint on Khmer: 0.000 accuracy at 0.952 confidence. So a
threshold on ``confidence`` does not mean what it looks like it means. This
module says so once, in one string, and refuses to dress the number up as
something it is not.

**Problem two: the softmaxes are over-confident out of the box.** Reported raw
ECE is 0.466 for the English checkpoint and 0.314 for multilingual, improving to
0.081 and 0.106 after fitting one temperature per ``(question type, option count
bucket)``. The ``laya`` and ``typed-decisions`` checkpoints already ship fitted
temperatures; ``laya-multilingual`` ships *none* (``temperature: [1,1,1]``, empty
``temperature_by_options``). So on multilingual, every probability is raw.

Laya fits temperatures in its own fine-tuning notebook and bakes them into the
checkpoint as ``temperature`` and ``temperature_by_options``. What it does not
do is let you re-fit against *your* data and keep the result. This module is that
store: fit, persist to JSON, reload, and apply on top of whatever the checkpoint
shipped.

**What this module deliberately does not do.** It does not claim to fix an
uncalibrated checkpoint, and it will not invent a temperature. Fitting needs
labelled outcomes, so the only honest thing to do without them is to report which
mode you are in and move on. When you do have labels, :func:`fit_temperature`
uses the same strictly-proper-scoring objective Laya's own training uses, so the
result is comparable to what the checkpoint ships rather than a different
convention.

**And one limit worth stating plainly**: several of these checkpoints are near
chance zero-shot on typed decisions - upstream's own numbers put the base English
checkpoint at 0.362 accuracy against a 0.461 majority-class baseline. No
temperature fixes that. Calibration makes a probability *honest*; it cannot make
a model *right*. If the accuracy is not there, fit on your own domain or do not
deploy it.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional, Sequence

#: The one string that should be shown to anyone about to threshold a confidence.
CONFIDENCE_SEMANTICS = (
    "Laya's `confidence` is a concentration statistic over the option distribution "
    "(1 - H(p)/log k for choice and score; max(p, 1-p) for noul). It is NOT the probability "
    "that the answer is correct: it is low whenever probability is spread out, even when the "
    "top option is right, and it is high on a confident wrong answer. Branch on `noul` "
    "directly, and treat `confidence` as a tie-breaker rather than a probability of correctness."
)

#: Option-count buckets, matching the names Laya's own fitting uses:
#: ``"%s:%s" % (qtype, size)`` where size is one of these labels. Reproduced here
#: so a temperature this module fits lands in the same bucket the library reads.
BUCKET_LABELS = ("2", "3-5", "6-10", "11+")

#: Primitive order, mirroring ``QTYPES`` in ``laya/common.py``.
QTYPE_INDEX: Mapping[str, int] = {"choice": 0, "score": 1, "noul": 2}


def bucket_for(qtype: str, option_count: int) -> str:
    """The temperature bucket a question falls into.

    Reproduces ``temp_bucket`` in ``laya/common.py``: a two-option question is its
    own bucket (that is every ``noul``), then 3-5, 6-10, and 11 or more.
    """
    if option_count <= 2:
        size = "2"
    elif option_count <= 5:
        size = "3-5"
    elif option_count <= 10:
        size = "6-10"
    else:
        size = "11+"
    return f"{qtype}:{size}"


def apply_temperature(probabilities: Sequence[float], temperature: float) -> list[float]:
    """Rescale a distribution by a temperature, in log space.

    ``p_i ∝ p_i ** (1/T)``. Done in log space with the max subtracted, because
    exponentiating a raw probability directly underflows to zero for a small
    ``p`` and a large ``T``. Mirrors the arithmetic in ``Agent.system_one``,
    including its ``max(1e-3, T)`` floor, so applying the same temperature here
    and there gives the same answer.
    """
    if not probabilities:
        return []
    scale = max(1e-3, float(temperature))
    logs = [math.log(max(float(p), 1e-12)) / scale for p in probabilities]
    peak = max(logs)
    exps = [math.exp(v - peak) for v in logs]
    total = sum(exps)
    if total <= 0:
        return list(probabilities)
    return [v / total for v in exps]


def expected_calibration_error(
    confidences: Sequence[float],
    correct: Sequence[bool],
    *,
    bins: int = 10,
) -> float:
    """Expected calibration error: how far confidence is from accuracy.

    The standard equal-width binning: partition by confidence, and average the
    gap between mean confidence and observed accuracy in each bin, weighted by
    the bin's share of the sample. 0 means perfectly calibrated, and the number
    is only as meaningful as the sample is large - a few dozen examples produce a
    figure that moves by 0.1 when one label changes.

    **The boundary convention, stated because it is a real choice.** Bins are
    ``[low, high)``, except the top bin which is closed so that a confidence of
    exactly 1.0 is counted rather than dropped. A consequence worth knowing: a
    confidence sitting exactly on an interior boundary falls into the *upper* bin.
    So two hand-written samples at ``0.9`` and ``0.1`` - both perfectly calibrated
    - score 0.1 rather than 0, because 0.9 lands in ``[0.9, 1.0)`` whose observed
    accuracy is 1.0 while its stated confidence is 0.9. That is the standard
    equal-width definition, and the alternative (closing every bin at its upper
    edge) merely moves the artefact to the other set of boundaries. Real
    confidences are effectively continuous, so hitting a boundary exactly has
    probability zero; this matters mainly for small hand-written test samples,
    which is exactly why it is written down.
    """
    if not confidences or len(confidences) != len(correct):
        return 0.0
    total = len(confidences)
    ece = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        if index == bins - 1:
            # Closed at the top so a confidence of exactly 1.0 is not discarded.
            members = [i for i, c in enumerate(confidences) if low <= c <= high]
        else:
            members = [i for i, c in enumerate(confidences) if low <= c < high]
        if not members:
            continue
        mean_confidence = sum(confidences[i] for i in members) / len(members)
        accuracy = sum(1 for i in members if correct[i]) / len(members)
        ece += (len(members) / total) * abs(mean_confidence - accuracy)
    return ece


def brier_score(probabilities: Sequence[float], correct: Sequence[bool]) -> float:
    """Mean squared error of the probability assigned to the correct outcome.

    Lower is better. Reported alongside ECE because the two disagree in a useful
    way: ECE only looks at the top option, Brier scores the whole distribution.
    """
    if not probabilities or len(probabilities) != len(correct):
        return 0.0
    total = 0.0
    for p, ok in zip(probabilities, correct):
        target = 1.0 if ok else 0.0
        total += (p - target) ** 2
    return total / len(probabilities)


#: The numeric bounds of the default grid, as ``(low, high)``.
TEMPERATURE_GRID_BOUNDS = (0.01, 100.0)

#: The geometric grid :func:`fit_temperature` searches when given none.
#:
#: The exponent range runs *wider* than the bounds on purpose. An earlier version
#: built the range as ``range(-24, 25)`` and then filtered it to
#: ``0.01 <= t <= 100``, which reads as though 0.01 were the floor while the
#: range actually stopped first: the smallest reachable temperature was
#: ``1.2 ** -24 == 0.01258``, and the filter never removed anything. Two real
#: fits then landed on that floor, and the floor was returned as an ordinary
#: result.
#:
#: A fit that lands on the edge of its search space has not found a temperature;
#: it has reported that the optimum is somewhere the search could not reach. On a
#: small sample that usually means "as sharp as possible", which is a statement
#: about the sample, not about the checkpoint. The range therefore now extends
#: past the bounds so that the *bounds* are what bind, and
#: :func:`temperature_is_saturated` lets a caller see when they did.
TEMPERATURE_GRID: tuple[float, ...] = tuple(
    t
    for t in (1.2**step for step in range(-40, 41))
    if TEMPERATURE_GRID_BOUNDS[0] <= t <= TEMPERATURE_GRID_BOUNDS[1]
)


def temperature_is_saturated(
    temperature: float,
    grid: Optional[Sequence[float]] = None,
) -> bool:
    """Whether a fitted temperature sits on the edge of the grid it was fitted on.

    True means the search ran into its own boundary, so the returned value is a
    bound rather than an optimum and should not be quoted as a calibrated
    temperature. Every ``math.isclose`` here is against the grid actually used,
    including a caller-supplied one.
    """
    points = tuple(grid) if grid is not None else TEMPERATURE_GRID
    if not points:
        return False
    low, high = min(points), max(points)
    return math.isclose(temperature, low, rel_tol=1e-9) or math.isclose(
        temperature, high, rel_tol=1e-9
    )


def fit_temperature(
    probabilities: Sequence[Sequence[float]],
    correct_outcome: Sequence[int],
    *,
    grid: Optional[Sequence[float]] = None,
) -> tuple[float, float]:
    """Fit one temperature by minimising negative log-likelihood.

    Returns ``(temperature, nll)``. The objective is the strictly proper scoring
    rule Laya's own training uses, so the fitted value is on the same scale as
    the temperatures the checkpoints ship rather than a different convention.

    A grid search rather than an optimiser, deliberately: the objective is
    one-dimensional, smooth and cheap, and a grid has no failure mode where a
    gradient step diverges and returns a plausible-looking nonsense temperature.
    The grid is geometric so it spends its resolution where temperatures
    actually land.

    A grid search has one failure mode of its own, and this used to have it: the
    optimum can lie outside the grid, in which case the search returns the
    boundary and says nothing. Check the result with
    :func:`temperature_is_saturated` before treating it as a measurement.
    """
    if not probabilities or len(probabilities) != len(correct_outcome):
        raise ValueError("probabilities and correct_outcome must be the same non-zero length")

    if grid is None:
        grid = TEMPERATURE_GRID
    if not grid:
        raise ValueError("grid must contain at least one temperature")

    best_t = 1.0
    best_nll = float("inf")
    for temperature in grid:
        nll = 0.0
        for probs, outcome in zip(probabilities, correct_outcome):
            scaled = apply_temperature(probs, temperature)
            if outcome < 0 or outcome >= len(scaled):
                raise ValueError(f"outcome index {outcome} is outside the distribution")
            nll -= math.log(max(scaled[outcome], 1e-12))
        nll /= len(probabilities)
        if nll < best_nll:
            best_nll = nll
            best_t = temperature
    return best_t, best_nll


@dataclass
class CalibrationEntry:
    """A fitted temperature set for one checkpoint.

    Stored per ``(checkpoint, revision)`` so that upgrading the weights does not
    silently apply temperatures fitted against the previous ones.
    """

    checkpoint: str
    revision: Optional[str] = None
    """A content marker for the checkpoint - a config hash, a commit, a version.
    Temperatures fitted against one set of weights are not valid for another."""

    temperatures: list[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    """Per-primitive, ordered choice / score / noul."""

    by_options: dict[str, float] = field(default_factory=dict)
    """``"<qtype>:<bucket>"`` to fitted temperature."""

    samples: int = 0
    ece_before: Optional[float] = None
    ece_after: Optional[float] = None
    brier_before: Optional[float] = None
    brier_after: Optional[float] = None
    fitted_at: Optional[str] = None
    notes: Optional[str] = None

    saturated_buckets: list[str] = field(default_factory=list)
    """Buckets whose fit landed on the edge of the search grid.

    A bucket named here has a temperature that is a *bound*, not an optimum: the
    data asked for something sharper (or flatter) than the grid could express, so
    the value is an artefact of where the search stopped. Kept on the entry
    rather than only in ``notes`` because a caller deciding whether to apply a
    temperature should not have to parse prose to find out.
    """

    def temperature_for(self, qtype: str, option_count: int) -> float:
        """The temperature to use for a question, preferring a fitted bucket.

        Falls back to the per-primitive value, then to 1.0, mirroring
        ``Agent.system_one``'s
        ``temperature_by_options.get(bucket, temperature[qt])``.
        """
        bucketed = self.by_options.get(bucket_for(qtype, option_count))
        if bucketed is not None:
            return float(bucketed)
        index = QTYPE_INDEX.get(qtype)
        if index is not None and index < len(self.temperatures):
            return float(self.temperatures[index])
        return 1.0

    def is_identity(self) -> bool:
        """True when nothing would change, so applying it is a no-op."""
        return all(abs(t - 1.0) < 1e-9 for t in self.temperatures) and not self.by_options

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CalibrationStore:
    """A small JSON-backed store of fitted temperatures.

    One file, read once at startup and written atomically. Deliberately not a
    database: a handful of floats per checkpoint does not justify one, and a
    plain file can be inspected, diffed and committed by a human.

    A corrupt or unreadable file is not fatal. Fitting temperatures is an
    enhancement; losing them should degrade to the checkpoint's own values and
    say so, never take the server down.
    """

    VERSION = 1

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._entries: dict[str, CalibrationEntry] = {}
        self.load_error: Optional[str] = None
        if path:
            self._load()

    # -- lookup ---------------------------------------------------------------

    @staticmethod
    def _key(checkpoint: str, revision: Optional[str]) -> str:
        return f"{checkpoint}@{revision}" if revision else checkpoint

    def get(self, checkpoint: str, revision: Optional[str] = None) -> Optional[CalibrationEntry]:
        """The entry for a checkpoint, preferring one whose revision matches.

        A revision-specific entry wins; otherwise an unversioned entry for the
        same checkpoint is used, which is what a caller who fitted before
        tracking revisions will have.
        """
        exact = self._entries.get(self._key(checkpoint, revision))
        if exact is not None:
            return exact
        return self._entries.get(checkpoint)

    def put(self, entry: CalibrationEntry) -> None:
        self._entries[self._key(entry.checkpoint, entry.revision)] = entry

    def all(self) -> Mapping[str, CalibrationEntry]:
        return dict(self._entries)

    # -- persistence ----------------------------------------------------------

    def _load(self) -> None:
        assert self.path is not None
        if not os.path.isfile(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError) as exc:
            self.load_error = f"could not read {self.path}: {exc}"
            return

        if not isinstance(raw, Mapping):
            self.load_error = f"{self.path} does not contain a JSON object"
            return
        if raw.get("version") != self.VERSION:
            self.load_error = (
                f"{self.path} is version {raw.get('version')!r}, this build writes "
                f"version {self.VERSION}; ignoring it rather than guessing at the format"
            )
            return

        entries = raw.get("entries")
        if not isinstance(entries, Mapping):
            self.load_error = f"{self.path} has no `entries` object"
            return

        for key, value in entries.items():
            if not isinstance(value, Mapping):
                continue
            try:
                self._entries[key] = CalibrationEntry(
                    checkpoint=str(value.get("checkpoint", key.split("@")[0])),
                    revision=value.get("revision"),
                    temperatures=[float(t) for t in value.get("temperatures", [1.0, 1.0, 1.0])],
                    by_options={
                        str(k): float(v) for k, v in (value.get("by_options") or {}).items()
                    },
                    samples=int(value.get("samples", 0)),
                    ece_before=_opt_float(value.get("ece_before")),
                    ece_after=_opt_float(value.get("ece_after")),
                    brier_before=_opt_float(value.get("brier_before")),
                    brier_after=_opt_float(value.get("brier_after")),
                    fitted_at=value.get("fitted_at"),
                    notes=value.get("notes"),
                    saturated_buckets=[
                        str(b) for b in (value.get("saturated_buckets") or [])
                    ],
                )
            except (TypeError, ValueError):
                # One malformed entry should not discard the rest.
                continue

    def save(self) -> str:
        """Write the store atomically and return the path.

        Written to a temporary file in the same directory then renamed, so a
        crash mid-write cannot leave a half-written store that the next startup
        would refuse to read.
        """
        if not self.path:
            raise RuntimeError("this store has no path; construct it with CalibrationStore(path)")
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(directory, exist_ok=True)
        payload = {
            "version": self.VERSION,
            "written_at": datetime.now(timezone.utc).isoformat(),
            "entries": {k: v.to_dict() for k, v in self._entries.items()},
        }
        handle, temporary = tempfile.mkstemp(dir=directory, prefix=".calibration-", suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, sort_keys=True)
                fh.write("\n")
            os.replace(temporary, self.path)
        except BaseException:
            if os.path.exists(temporary):
                os.unlink(temporary)
            raise
        return self.path


def _opt_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fit_from_examples(
    checkpoint: str,
    examples: Iterable[Mapping[str, Any]],
    *,
    revision: Optional[str] = None,
    min_samples: int = 30,
) -> CalibrationEntry:
    """Fit per-bucket temperatures from labelled examples.

    Each example is ``{"probabilities": [...], "outcome": int, "type": "choice"}``.
    The option count is taken from the distribution's length.

    Buckets with fewer than ``min_samples`` examples keep the identity
    temperature rather than a value fitted on noise. That threshold is a
    judgement, not a law, and it is a parameter so it can be argued with: a
    temperature fitted on five examples will reduce the training loss and make
    the held-out calibration worse.
    """
    grouped: dict[str, list[tuple[list[float], int, str]]] = {}
    for example in examples:
        probs = [float(p) for p in example["probabilities"]]
        outcome = int(example["outcome"])
        qtype = str(example.get("type", "choice"))
        grouped.setdefault(bucket_for(qtype, len(probs)), []).append((probs, outcome, qtype))

    by_options: dict[str, float] = {}
    saturated: list[str] = []
    all_probs: list[list[float]] = []
    all_outcomes: list[int] = []
    # The primitive travels with each distribution. Without it the recalculation
    # below has to guess a bucket, and the only guess available is `choice` -
    # which would score a noul's fitted temperature against the choice bucket and
    # report an improvement that does not exist.
    all_qtypes: list[str] = []
    confidences_before: list[float] = []
    correct_before: list[bool] = []

    for bucket, rows in grouped.items():
        probs = [row[0] for row in rows]
        outcomes = [row[1] for row in rows]
        qtypes = [row[2] for row in rows]
        all_probs.extend(probs)
        all_outcomes.extend(outcomes)
        all_qtypes.extend(qtypes)
        for distribution, outcome in zip(probs, outcomes):
            top = max(range(len(distribution)), key=lambda i: distribution[i])
            confidences_before.append(concentration(distribution))
            correct_before.append(top == outcome)

        if len(rows) >= min_samples:
            temperature, _ = fit_temperature(probs, outcomes)
            if temperature_is_saturated(temperature):
                # Stored unrounded, because the fitted value *is* the grid point
                # and rounding it to six places moves it far enough off the edge
                # that a later `temperature_is_saturated` on the stored number
                # would say no. The flag and the value have to agree.
                by_options[bucket] = temperature
                saturated.append(bucket)
            else:
                by_options[bucket] = round(temperature, 6)

    ece_before = expected_calibration_error(confidences_before, correct_before)
    brier_before = (
        brier_score([p[o] for p, o in zip(all_probs, all_outcomes)], [True] * len(all_outcomes))
        if all_probs
        else None
    )

    ece_after = None
    brier_after = None
    if all_probs:
        recalibrated = [
            apply_temperature(p, by_options.get(bucket_for(qt, len(p)), 1.0))
            for p, qt in zip(all_probs, all_qtypes)
        ]
        confidences_after = [concentration(d) for d in recalibrated]
        correct_after = [
            max(range(len(d)), key=lambda i: d[i]) == o for d, o in zip(recalibrated, all_outcomes)
        ]
        ece_after = expected_calibration_error(confidences_after, correct_after)
        brier_after = brier_score(
            [d[o] for d, o in zip(recalibrated, all_outcomes)], [True] * len(all_outcomes)
        )

    entry = CalibrationEntry(
        checkpoint=checkpoint,
        revision=revision,
        by_options=by_options,
        samples=len(all_outcomes),
        ece_before=ece_before,
        ece_after=ece_after,
        brier_before=brier_before,
        brier_after=brier_after,
        fitted_at=datetime.now(timezone.utc).isoformat(),
        saturated_buckets=saturated,
        notes=(
            "buckets with fewer than "
            f"{min_samples} examples kept temperature 1.0"
            + (
                "; fits that ran into the edge of the grid and are bounds rather "
                f"than optima: {', '.join(sorted(saturated))}"
                if saturated
                else ""
            )
        ),
    )
    return entry


def _bucket_for_len(distribution: Sequence[float]) -> str:
    return bucket_for("choice", len(distribution))


def concentration(distribution: Sequence[float]) -> float:
    """Laya's ``confidence`` for a choice-like distribution.

    ``1 - H(p)/log(k)``, clipped to ``[0, 1]``, matching
    ``confidence_from_probs`` in ``laya/common.py``. Reproduced rather than
    imported so this module works with no torch present.
    """
    if not distribution:
        return 0.0
    k = len(distribution)
    if k <= 1:
        return 1.0
    entropy = 0.0
    for p in distribution:
        if p > 0:
            entropy -= p * math.log(p)
    return max(0.0, min(1.0, 1.0 - entropy / math.log(k)))
