"""The logit-style readout: internal probabilities instead of a stated number.

WHY THIS TIER MATTERS
---------------------
R16 required four LLM probability readouts and noted that the logit route is only real
because `logprobs`/`top_logprobs` are supported (verified in the API reference). Every
LLM probability in this project so far is VERBALIZED: the model is asked for a number and
states one. The literature is consistent that verbalized confidence and internal
probability diverge, with verbalized confidence running overconfident.

This measures the divergence directly on the same items, which closes two things at once:
  * R16's fourth rung, so the paper's baseline ladder is complete rather than aspirational;
  * a check on whether any earlier LLM calibration number in this paper is an artefact of
    the elicitation method rather than of the model.

METHOD
------
The model answers with a SINGLE LETTER, so `top_logprobs` at that position is a
distribution over the option letters rather than over arbitrary tokens. The prompt
instructs exactly one letter and nothing else.

Reported per item:
  * `logit_p`  -- exp(logprob) of the chosen letter, normalised over the option letters
                  actually present in top_logprobs (so it is a real distribution, not a
                  single token probability)
  * `verbal_p` -- the same item asked in the forced-choice JSON form
  * correctness of each, and the signed difference in P(true) terms

REUSE: the calibration item templates from P19, so the pair is measured on the SAME items
that produced the paper's n=1100 calibration curve.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))
from deepseek_client import (chat, parse_label, parse_prob,  # noqa: E402
                             prompt_forced_choice, prompt_logit)

RESULTS = ROOT / "results"


def build_items(n_per_level: int = 12, seed: int = 20260922):
    """Import P19's generator so the items are identical to the calibration corpus."""
    import random
    from p19_calibration import LEVELS, build_item  # noqa: E402
    rng = random.Random(seed)
    items = []
    for lv in LEVELS:
        for i in range(n_per_level):
            items.append(build_item(i, lv, rng))
    return items


def logit_distribution(resp, criteria: dict) -> tuple[float | None, dict]:
    """Normalise the letter distribution at the answer position.

    `top_logprobs` returns the k most likely tokens at that position, not a full
    vocabulary distribution, so the letters that appear are renormalised among
    themselves. That is the right object here: the question is which OPTION the model
    favours, and any probability mass on non-letter tokens is irrelevant to it.
    """
    if not resp.logprobs:
        return None, {}
    first = resp.logprobs[0] if isinstance(resp.logprobs, list) else None
    if not first:
        return None, {}
    tops = first.get("top_logprobs") or []
    letters = {chr(65 + i): k for i, k in enumerate(criteria)}
    dist: dict[str, float] = {}
    for entry in tops:
        tok = (entry.get("token") or "").strip().upper()
        if tok in letters:
            dist[letters[tok]] = dist.get(letters[tok], 0.0) + math.exp(entry["logprob"])
    if not dist:
        return None, {}
    total = sum(dist.values())
    if total <= 0:
        return None, {}
    dist = {k: v / total for k, v in dist.items()}
    return total, dist


def run(n_per_level: int = 12) -> dict:
    items = build_items(n_per_level)
    rows: list[dict] = []
    for it in items:
        truth = it["truth"]
        rec = {"item_id": it["item_id"], "level": it["level"], "truth": truth}
        # ---- verbalized: the forced-choice JSON form used everywhere else in the paper
        try:
            r1 = chat(prompt_forced_choice(it["state"], it["question"], it["criteria"]),
                      effort="none", json_mode=True, max_tokens=96)
            lab = parse_label(r1, it["criteria"])
            conf = parse_prob(r1)
            if lab and conf is not None:
                rec["verbal_p_true"] = conf if lab == "true" else 1.0 - conf
                # `conf` is the model's stated confidence in the label it chose, which is
                # the quantity comparable with the logit distribution's mode probability.
                rec["verbal_conf"] = conf
                rec["verbal_correct"] = (lab == "true") == truth
        except Exception as exc:
            rec["verbal_error"] = str(exc)[:160]
        # ---- logit: one letter, read off top_logprobs
        try:
            r2 = chat(prompt_logit(it["state"], it["question"], it["criteria"]),
                      effort="none", logprobs=True, top_logprobs=20, max_tokens=8)
            letter = (r2.text or "").strip()[:1].upper()
            keys = list(it["criteria"])
            picked = keys[ord(letter) - 65] if letter.isalpha() and 0 <= ord(letter) - 65 < len(keys) else None
            _, dist = logit_distribution(r2, it["criteria"])
            rec["logit_letter"] = letter
            rec["logit_picked"] = picked
            rec["logit_correct"] = (picked == "true") == truth if picked else None
            rec["logit_p_true"] = dist.get("true") if dist else None
            # mode probability over the OPTION letters -- the internal analogue of the
            # verbalized confidence in the chosen label.
            rec["logit_mode_prob"] = max(dist.values()) if dist else None
            rec["logit_mass_captured"] = round(_, 4) if _ is not None else None
            rec["logit_n_letters"] = len(dist)
        except Exception as exc:
            rec["logit_error"] = str(exc)[:160]
        rows.append(rec)
        print(f"{it['level'][:16]:<18} truth={str(truth):<5} "
              f"verbal={rec.get('verbal_p_true')} logit={rec.get('logit_p_true')} "
              f"({rec.get('logit_n_letters')} letters)")

    both = [r for r in rows if r.get("verbal_p_true") is not None
            and r.get("logit_p_true") is not None]
    diffs = [r["verbal_p_true"] - r["logit_p_true"] for r in both]
    va = [r["verbal_correct"] for r in rows if r.get("verbal_correct") is not None]
    la = [r["logit_correct"] for r in rows if r.get("logit_correct") is not None]
    # THE RIGHT COMPARISON. Averaging P(true) across the corpus mixes the 60% of items
    # whose true label is "false" with the 40% whose label is "true", so it collapses
    # toward the base rate (measured: 0.4023 vs 0.4000) and looks like agreement no
    # matter what the model does. What is actually comparable between a verbalized number
    # and an internal distribution is CONFIDENCE IN THE ANSWER GIVEN, so that is what is
    # summarised: for the verbalized arm, `prob` as stated (it is confidence in the
    # chosen label); for the logit arm, the mode probability of the letter distribution.
    conf_rows = [r for r in rows
                 if r.get("verbal_conf") is not None and r.get("logit_mode_prob") is not None]
    conf_diffs = [r["verbal_conf"] - r["logit_mode_prob"] for r in conf_rows]
    summary = {
        "n_items": len(rows),
        "n_paired": len(both),
        "n_confidence_paired": len(conf_rows),
        "verbal_accuracy": round(sum(1 for x in va if x) / len(va), 4) if va else None,
        "logit_accuracy": round(sum(1 for x in la if x) / len(la), 4) if la else None,
        "mean_verbal_confidence_on_chosen": (round(statistics.fmean(
            r["verbal_conf"] for r in conf_rows), 4) if conf_rows else None),
        "mean_logit_mode_prob_on_chosen": (round(statistics.fmean(
            r["logit_mode_prob"] for r in conf_rows), 4) if conf_rows else None),
        "mean_signed_diff_confidence": (round(statistics.fmean(conf_diffs), 4)
                                       if conf_diffs else None),
        "mean_abs_diff_confidence": (round(statistics.fmean(abs(d) for d in conf_diffs), 4)
                                    if conf_diffs else None),
        "mean_p_true_corpus_level": {
            "verbal": round(statistics.fmean(r["verbal_p_true"] for r in both), 4) if both else None,
            "logit": round(statistics.fmean(r["logit_p_true"] for r in both), 4) if both else None,
            "note": ("reported only to show WHY it is the wrong comparison: it tracks the "
                     "60/40 class mix rather than the model's confidence"),
        },
        "n_logit_failures": sum(1 for r in rows if r.get("logit_p_true") is None),
        "instrument": "deepseek-flash, thinking disabled, logprobs+top_logprobs=20",
        "caveat": ("n=60 paired items by design: this is a METHOD comparison, not a "
                   "capability estimate. Its purpose is to establish whether the paper's "
                   "verbalized-elicitation numbers are method artefacts."),
        "verdict": None,
    }
    d = summary["mean_signed_diff_confidence"]
    if d is None:
        summary["verdict"] = "NO PAIRED CONFIDENCE DATA (inspect logit failures)"
    elif d > 0.05:
        summary["verdict"] = (f"VERBALIZED CONFIDENCE IS INFLATED by {d:+.4f} on average "
                              f"relative to the internal distribution, confirming the "
                              f"elicitation-method concern")
    elif d < -0.05:
        summary["verdict"] = (f"VERBALIZED CONFIDENCE IS DEFLATED by {d:+.4f}; the two "
                              f"readouts disagree in the opposite direction to the usual "
                              f"report")
    else:
        summary["verdict"] = (f"THE TWO READOUTS AGREE within {abs(d):.4f} on confidence "
                              f"in the chosen answer, so the paper's verbalized numbers "
                              f"are not an elicitation artefact on these items")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run(n_per_level=12)
    p = RESULTS / "P23-llm-logprobs.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    print(f"\nwritten: {p}")
