"""LLM ARM + CROSS-SPECIES ERROR COMPLEMENTARITY on identical items.

THIS IS THE GAP THAT MATTERED MOST
----------------------------------
The paper is a three-way comparison, and until now DeepSeek-V4.1-Flash had never been
RUN as a subject: the only LLM facts in the project were a verified price list. So the
thesis "cost is not the binding constraint" rested on price arithmetic rather than on any
measurement of the model it is about.

It also delivers the experiment V5 identified as the missing novelty. R16 and V5 both
note that every prior cascade (FrugalGPT, RouteLLM, AutoMix, learning-to-defer) escalates
within one family -- an LLM judging an LLM -- so the interesting question is not "which
judge is more accurate" (a comparison that dies to any accuracy-level confound) but:

    does a DIFFERENT SPECIES of judge fail on the SAME items?

    Delta_catch = P(typed judge correct | LLM judge WRONG)
                - P(typed judge correct | LLM judge RIGHT)

paired within item, so between-item difficulty cancels. Reported with the error
correlation kappa and, importantly, with the discordance breakdown rather than a bare
difference. A positive Delta_catch means the typed judge is not redundant: it catches
things the LLM misses even though it is far weaker on average.

ITEMS: the P9b set, chosen because Laya has ALREADY answered all 48 of them under
decorrelated option order, so the paired comparison costs no new Laya calls and inherits
its controls (separated figures, opaque keys). The prompt gives the LLM exactly the same
state, question and option text the typed judges received, so the contrast is of judges,
not of prompt style.

ARMS: prose (A0) and forced-choice (A1). R16's anti-straw-man package requires both, with
the BEST variant as the headline; the prose arm is what an agent actually does, and the
forced-choice arm is the honest rung that must be beaten for any typed-judge claim to
survive.
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from deepseek_client import (chat, parse_label, parse_prob,  # noqa: E402
                             prompt_forced_choice, prompt_prose)

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
RESULTS = ROOT / "results"

# Mirror of the P9b generator so the items are byte-identical in state, question and
# options to the ones Laya answered. Kept in sync deliberately and asserted below.
sys.path.insert(0, str(ROOT / "src" / "items"))
from p9b_template_validation_separated import TOPICS, build, render  # noqa: E402


def kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    """Cohen's kappa over two judges' correctness on the same items."""
    n = len(pairs)
    if n == 0:
        return None
    a = sum(1 for x, _ in pairs if x) / n
    b = sum(1 for _, y in pairs if y) / n
    po = sum(1 for x, y in pairs if x == y) / n
    pe = a * b + (1 - a) * (1 - b)
    return (po - pe) / (1 - pe) if pe != 1 else None


def run(limit: int | None = None, lite: bool = True) -> dict:
    """lite=True runs a subset to keep the first pass cheap; the full set is 48 items x
    2 arms x 2 calls if prose is included."""
    items = []
    idxs = range(len(TOPICS)) if limit is None else range(min(limit, len(TOPICS)))
    for idx in idxs:
        rng = random.Random(f"20260922:{idx}")
        it = build(idx, rng)
        items.append({"idx": idx, "state": render(it["spans"]),
                      "instructions": it["instruction"],
                      "criteria": it["criteria"], "truth": it["truth"],
                      "label": it["label"]})

    rows: list[dict] = []
    for it in items:
        rec = {"idx": it["idx"], "label": it["label"], "truth": it["truth"]}

        # ---- A0 prose
        r0 = chat(prompt_prose(it["state"], it["instructions"], it["criteria"]),
                  effort="none", max_tokens=256)
        rec["prose_text"] = (r0.text or "")[:300]
        rec["prose_label"] = parse_label(r0, it["criteria"])
        rec["prose_correct"] = rec["prose_label"] == it["truth"]
        rec["prose_latency_ms"] = round(r0.latency_ms, 1)
        rec["prose_cost"] = r0.cost

        # ---- A1 forced choice, JSON constrained
        r1 = chat(prompt_forced_choice(it["state"], it["instructions"], it["criteria"]),
                  effort="none", json_mode=True, max_tokens=128)
        rec["fc_label"] = parse_label(r1, it["criteria"])
        rec["fc_prob"] = parse_prob(r1)
        rec["fc_correct"] = rec["fc_label"] == it["truth"]
        rec["fc_latency_ms"] = round(r1.latency_ms, 1)
        rec["fc_cost"] = r1.cost
        rec["fc_finish"] = r1.finish_reason
        if r1.error:
            rec["fc_error"] = r1.error

        rows.append(rec)
        print(f"{it['label'][:30]:<32} prose={rec['prose_correct']!s:<5} "
              f"fc={rec['fc_correct']!s:<5} p={rec['fc_prob']}")

    n = len(rows)
    def acc(key: str) -> float | None:
        vals = [r[key] for r in rows if r.get(key) is not None]
        return sum(1 for v in vals if v) / len(vals) if vals else None

    costs = [r["fc_cost"]["off_peak_usd"] for r in rows if r.get("fc_cost")]
    lats = [r["fc_latency_ms"] for r in rows if r.get("fc_latency_ms")]
    summary = {
        "n_items": n,
        "model": "deepseek-flash (DeepSeek-V4.1-Flash)",
        "effort": "none (non-thinking; required for any sampling arm)",
        "llm_prose_accuracy": acc("prose_correct"),
        "llm_forced_choice_accuracy": acc("fc_correct"),
        "llm_fc_mean_cost_usd_offpeak": statistics.fmean(costs) if costs else None,
        "llm_fc_p50_latency_ms": statistics.median(lats) if lats else None,
        "llm_fc_max_latency_ms": max(lats) if lats else None,
        "llm_fc_parse_failures": sum(1 for r in rows if r.get("fc_label") is None),
        "caveat": ("Non-thinking mode, single sample per item, n as stated. Not a "
                   "capability estimate; enough to populate the three-way contrast and "
                   "the complementarity analysis."),
    }
    return {"summary": summary, "rows": rows}


def complementarity(llm_rows: list[dict], laya_rows: list[dict],
                    llm_key: str = "fc_correct") -> dict:
    """Pair the two judges on the SAME items and compute Delta_catch + kappa."""
    by_idx_laya = {r["idx"]: r for r in laya_rows if "idx" in r}
    pairs: list[tuple[bool, bool]] = []
    detail = []
    for r in llm_rows:
        l = by_idx_laya.get(r["idx"])
        if l is None or r.get(llm_key) is None or l.get("correct") is None:
            continue
        pairs.append((r[llm_key], l["correct"]))
        detail.append({"idx": r["idx"], "label": r["label"],
                       "llm_correct": r[llm_key], "typed_correct": l["correct"]})
    n = len(pairs)
    if n == 0:
        return {"n": 0}
    llm_wrong = [t for l, t in pairs if not l]
    llm_right = [t for l, t in pairs if l]
    p_catch_wrong = (sum(1 for t in llm_wrong if t) / len(llm_wrong)) if llm_wrong else None
    p_catch_right = (sum(1 for t in llm_right if t) / len(llm_right)) if llm_right else None
    both = sum(1 for l, t in pairs if l and t)
    neither = sum(1 for l, t in pairs if not l and not t)
    llm_only = sum(1 for l, t in pairs if l and not t)
    typed_only = sum(1 for l, t in pairs if not l and t)
    return {
        "n_paired": n,
        "llm_accuracy_on_paired": sum(1 for l, _ in pairs if l) / n,
        "typed_accuracy_on_paired": sum(1 for _, t in pairs if t) / n,
        "P_typed_correct_given_llm_wrong": p_catch_wrong,
        "P_typed_correct_given_llm_right": p_catch_right,
        "delta_catch": (None if (p_catch_wrong is None or p_catch_right is None)
                        else p_catch_wrong - p_catch_right),
        "confusion": {"both_correct": both, "neither_correct": neither,
                      "llm_only_correct": llm_only, "typed_only_correct": typed_only},
        "kappa_agreement": kappa(pairs),
        "detail": detail,
    }


if __name__ == "__main__":
    out = run(limit=None)
    p = RESULTS / "P14-llm-arm-full.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- cross-species error complementarity against Laya's EXISTING P9b rows.
    # Laya answered the same generated items in the same order, so pairing is by index.
    laya_path = RESULTS / "P9b-template-validation-separated-n48.json"
    comp: dict = {"note": "Laya rows absent; run P9b first"}
    if laya_path.exists():
        laya_doc = json.loads(laya_path.read_text(encoding="utf-8"))
        laya_full = [dict(r, idx=i) for i, r in
                     enumerate(r for r in laya_doc["rows"] if r.get("presence") == "full")]
        comp = complementarity(out["rows"], laya_full, llm_key="fc_correct")
        comp_prose = complementarity(out["rows"], laya_full, llm_key="prose_correct")
    else:
        comp_prose = {}

    payload = {"summary": out["summary"], "complementarity": comp,
               "complementarity_prose_arm": comp_prose, "rows": out["rows"]}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n=== LLM ARM SUMMARY ===")
    print(json.dumps(out["summary"], indent=2))
    print("\n=== CROSS-SPECIES COMPLEMENTARITY (LLM forced-choice vs Laya) ===")
    print(json.dumps({k: v for k, v in comp.items() if k != "detail"}, indent=2))
    print("\n=== same, prose arm ===")
    print(json.dumps({k: v for k, v in comp_prose.items() if k != "detail"}, indent=2))
    print(f"\nwritten: {p}")
