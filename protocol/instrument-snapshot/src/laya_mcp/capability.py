"""What a checkpoint can actually do, read from the checkpoint itself.

Laya's limits are real and they are not in the README: the state is truncated
from the end, options share a fixed per-question token budget, high-cardinality
``choice`` degrades sharply, and the language detector covers far fewer
languages than the marketing does. Every one of those is derivable from
``rl_agent_config.json`` plus a little arithmetic. This module derives it, once,
at startup, so a caller can be told the truth before it sends anything.

The numbers here are not invented and not copied from documentation. The token
arithmetic reproduces ``build_sequence`` in ``laya/common.py``; the language
coverage reproduces the script table and the Latin-script stopword heuristic in
``laya/lang.py``. When upstream changes, this is the one place to update.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

#: Latin-script languages Laya's detector will actually name. Anything else in
#: Latin script is treated as English. Read from `laya/lang.py`; the heuristic
#: needs at least four words before it will guess at all.
DETECTED_LATIN_LANGUAGES = ("en", "fr", "de", "es", "pt", "it", "nl")

#: The script table in `laya/lang.py` covers these. Non-Latin script detection is
#: reliable; it is the *Latin* case that silently routes to English.
DETECTED_SCRIPTS = (
    "latin", "cyrillic", "arabic", "hebrew", "devanagari", "bengali", "gurmukhi",
    "gujarati", "tamil", "telugu", "kannada", "malayalam", "sinhala", "thai",
    "lao", "myanmar", "khmer", "georgian", "armenian", "ethiopic", "han",
    "hiragana", "katakana", "hangul", "greek",
)

#: Where a Laya checkpoint name maps to a Hub repo and optional subfolder.
#: Mirrors `DEFAULT_MODELS` in `laya/router.py`, reproduced rather than imported
#: so a capability report can be produced without importing torch.
KNOWN_CHECKPOINTS: Mapping[str, tuple[str, Optional[str]]] = {
    "english": ("convaiinnovations/laya", None),
    "multilingual": ("convaiinnovations/laya", "multilingual"),
    "typed-decisions": ("convaiinnovations/laya", "typed-decisions"),
}

#: Aliases the router accepts, from `laya/router.py`.
CHECKPOINT_ALIASES: Mapping[str, str] = {
    "en": "english",
    "laya": "english",
    "default": "english",
    "multi": "multilingual",
    "ml": "multilingual",
    "laya-multilingual": "multilingual",
    "typed": "typed-decisions",
    "typed_decisions": "typed-decisions",
    "decisions": "typed-decisions",
    "laya-typed-decisions": "typed-decisions",
}


def normalise_checkpoint(name: str) -> str:
    """Map an alias onto a canonical checkpoint name.

    Raises :class:`KeyError` for an unknown name so the caller can translate it
    into an :class:`~laya_mcp.errors.UnknownModelError` with the full list.
    """
    key = name.strip().lower()
    key = CHECKPOINT_ALIASES.get(key, key)
    if key not in KNOWN_CHECKPOINTS:
        raise KeyError(name)
    return key


@dataclass(frozen=True)
class Capability:
    """The measured envelope of one loaded checkpoint.

    Every field is either read from the checkpoint's own config or derived from
    it by arithmetic that mirrors the library. Nothing is a constant from a
    README.
    """

    checkpoint: str
    """Canonical checkpoint name: ``english``, ``multilingual`` or ``typed-decisions``."""

    repo: str
    """The Hugging Face repo the weights came from."""

    subfolder: Optional[str]
    """The subfolder within that repo, if the checkpoint is bundled."""

    encoder: Optional[str]
    """The encoder architecture, e.g. ``answerdotai/ModernBERT-large``."""

    device: str
    """The device inference actually runs on *now* - see :attr:`degraded`."""

    requested_device: Optional[str]
    """What was asked for at startup, so a fallback is visible rather than inferred."""

    degraded: bool
    """True when Laya silently demoted itself to CPU.

    Laya catches a CUDA OOM during placement or inference and moves the model to
    CPU in fp32 in place, permanently, printing a warning to stdout. Nothing in
    the result admits it. A process that hits this once serves answers roughly
    10-15x slower forever, so this flag exists to surface it.
    """

    max_len: int
    """Total token budget for one question: instructions + options + state."""

    head_max_len: int
    """The token budget shared by the instructions and the options."""

    head_layers: Optional[int]
    temperature: tuple[float, ...]
    """Per-primitive temperatures, ordered by ``QTYPES``: choice, score, noul."""

    fitted_temperature_buckets: int
    """How many ``(primitive, option-count)`` buckets carry a fitted temperature.

    Zero means the checkpoint ships raw, uncalibrated softmaxes. ``laya`` and
    ``typed-decisions`` ship fitted buckets; ``multilingual`` ships none.
    """

    amp_dtype: Optional[str]

    @property
    def state_budget_tokens(self) -> int:
        """Roughly how many tokens of *state* survive, worst case.

        The exact number depends on the instructions and the rendered options, so
        this is the pessimistic floor: everything the options may consume is
        subtracted. Use :func:`laya_mcp.planning.plan_questions` for the real
        figure against a concrete batch.
        """
        return max(0, self.max_len - self.head_max_len)

    def option_token_budget(self, option_count: int) -> int:
        """Tokens each option gets, reproducing ``build_sequence`` exactly.

        The rule in ``laya/common.py`` is: each option body is first cut to 48
        tokens and prefixed with one mask token; if the running total leaves less
        than 16 tokens for the instructions, every option is re-cut to
        ``max(4, (head_max_len - 16) // option_count)``. So options are *never*
        rejected for being numerous - they are silently shortened, and past a
        point every label is 4 tokens and they stop being distinguishable, which
        is the documented cause of the Banking77 collapse.
        """
        if option_count <= 0:
            return 0
        naive = min(48, max(1, self.head_max_len // option_count)) + 1
        naive_total = naive * option_count
        if self.head_max_len - naive_total < 16:
            per = max(4, (self.head_max_len - 16) // option_count)
            return per + 1
        return naive

    def max_options(self) -> int:
        """Largest option count that still leaves every option distinguishable.

        Defined as the point where each option still gets at least 8 tokens
        (roughly two words beyond its mask token). Past this the model is
        choosing between labels it can no longer read apart, and the honest
        answer is to shard the question rather than to ask it.
        """
        for n in range(1, 512):
            if self.option_token_budget(n) < 8:
                return n - 1
        return 512

    def high_cardinality_warning_at(self) -> int:
        """The option count past which the upstream author advises against a single question.

        The founder's own guidance is that choice questions degrade beyond ~20
        options; that is a judgment about quality, not a hard limit, so it is
        reported separately from :meth:`max_options`.
        """
        return 20

    @property
    def languages_reliably_detected(self) -> tuple[str, ...]:
        """Languages the router will route correctly without an explicit hint.

        Non-Latin scripts are detected reliably by Unicode block. Latin-script
        languages are guessed from stopwords and diacritics over a seven-language
        table, and anything outside it falls through to **English** - which then
        answers confidently and wrongly. So a caller sending Polish, Czech,
        Turkish or Swedish must pass ``lang`` explicitly; there is no warning
        otherwise.
        """
        return ("en (assumed for any unrecognised Latin script)", *DETECTED_LATIN_LANGUAGES[1:])

    def language_caveat(self) -> Optional[str]:
        """A sentence to show a caller when routing may be silently wrong."""
        if self.checkpoint == "multilingual":
            return None
        return (
            "this is the English checkpoint. Only en/fr/de/es/pt/it/nl are detected in "
            "Latin script; every other Latin-script language is routed here as English and "
            "answered confidently. Pass `lang` explicitly for anything else."
        )

    def to_dict(self) -> dict[str, Any]:
        """A JSON-safe view, with the derived numbers included.

        The derived values are what a caller actually needs, so they are computed
        here rather than left as an exercise.
        """
        payload = asdict(self)
        payload["temperature"] = list(self.temperature)
        payload["state_budget_tokens"] = self.state_budget_tokens
        payload["max_options_8_tokens_each"] = self.max_options()
        payload["high_cardinality_advisory"] = self.high_cardinality_warning_at()
        payload["option_tokens_at"] = {
            str(n): self.option_token_budget(n) for n in (2, 4, 8, 12, 20, 30, 50, 77, 100)
        }
        payload["languages_reliably_detected"] = list(self.languages_reliably_detected)
        caveat = self.language_caveat()
        if caveat:
            payload["language_caveat"] = caveat
        return payload


def read_capability(
    model_root: str,
    *,
    checkpoint: str = "english",
    device: str = "unknown",
    requested_device: Optional[str] = None,
    degraded: bool = False,
) -> Capability:
    """Read a checkpoint's config and describe its envelope.

    Deliberately does not need torch. The whole point is that ``doctor`` can
    report what a checkpoint can do without paying the cost of loading it.
    """
    cfg = _load_cfg(model_root)
    if cfg is None:
        repo, subfolder = KNOWN_CHECKPOINTS.get(checkpoint, ("?", None))
        # No config on disk. Report what is known rather than refusing: a missing
        # checkpoint is the caller's next problem, and a capability report that
        # raises is useless for diagnosing it.
        return Capability(
            checkpoint=checkpoint,
            repo=repo,
            subfolder=subfolder,
            encoder=None,
            device=device,
            requested_device=requested_device,
            degraded=degraded,
            max_len=0,
            head_max_len=0,
            head_layers=None,
            temperature=(1.0, 1.0, 1.0),
            fitted_temperature_buckets=0,
            amp_dtype=None,
        )

    repo, subfolder = KNOWN_CHECKPOINTS.get(checkpoint, ("?", None))
    return Capability(
        checkpoint=checkpoint,
        repo=repo,
        subfolder=subfolder,
        encoder=cfg.get("encoder"),
        device=device,
        requested_device=requested_device,
        degraded=degraded,
        max_len=int(cfg.get("max_len", 512)),
        head_max_len=int(cfg.get("head_max_len", 192)),
        head_layers=cfg.get("head_layers"),
        temperature=tuple(float(t) for t in cfg.get("temperature", [1.0, 1.0, 1.0])),
        fitted_temperature_buckets=len(cfg.get("temperature_by_options") or {}),
        amp_dtype=cfg.get("amp_dtype"),
    )


def find_model_root(base: str, subfolder: Optional[str] = None) -> str:
    """Resolve the directory that actually holds ``rl_agent_config.json``.

    ``Agent.__init__`` appends the subfolder itself, so a caller that already
    passed a subfolder path would otherwise get it doubled. This accepts either
    spelling and returns the directory containing the config.
    """
    if subfolder:
        candidate = os.path.join(base, subfolder)
        if os.path.exists(os.path.join(candidate, "rl_agent_config.json")):
            return candidate
    return base


def _load_cfg(model_root: str) -> Optional[dict[str, Any]]:
    path = os.path.join(model_root, "rl_agent_config.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            loaded = json.load(fh)
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None
