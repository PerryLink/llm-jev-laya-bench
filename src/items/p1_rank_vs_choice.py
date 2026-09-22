"""PRE-WORK ITEM 1 (DECISIONS.md): can a high-cardinality `choice` reproduce the
semantics of a `rank` entry point?

WHY THIS TEST EXISTS
--------------------
Decision D1's recommendation to defer a live Jev credential rests partly on the claim
that Jev's primitives have local counterparts. A subagent asserted `laya_rank` mirrors
Jev's `rank`; the main session checked and found NO `laya_rank` — the sidecar's
/version reports only ["noul","choice","score"]. The closest local substitute is a
high-cardinality `choice` whose distribution is read as a ranking.

That substitution is NOT safe to assume, because R13 measured the opposite at N=20:
the choice collapsed to a confident wrong answer (mobile_app 0.9993, confidence 0.9981,
truth billing) with options compressed to 25 tokens each. R13's option ladder was
ALSO one item per rung, so it brackets a ceiling but does not estimate a curve.

WHAT THIS MEASURES
------------------
For N in {2, 5, 10, 15, 20, 25}:
  * argmax accuracy      -- does the top-probability option identify the supported one
  * AUC                  -- is the supported option's probability ABOVE the distractors',
                            which measures ranking signal separately from the argmax
  * win rate             -- P(p supported > max p distractor)
  * p_supported margin   -- absolute probability mass on the correct option
  * option tokens each   -- from the response, to record the compression regime

INTERPRETATION RULE (pre-declared, so the result cannot be spun after the fact):
  If AUC stays high while argmax accuracy falls, `choice` preserves RANKING SIGNAL at
  high cardinality and a shard-then-merge design is viable -> Jev's `rank` is
  constructible locally.
  If AUC itself decays toward 0.5, the primitive loses ordering information entirely
  -> `rank` is genuinely distinct and D1's substitutability argument must be weakened.

GROUND TRUTH BY CONSTRUCTION
----------------------------
Each item names a figure in the state plus 19 unrelated statements. The supported
statement is the one that states that figure; distractors state figures that do not
appear, or are plainly unrelated. Ground truth is authored, not produced by any model.
This is a probe battery, not the study battery, so a small N is appropriate and is
stated as a limitation in the output.
"""

from __future__ import annotations

# Paths resolve through bench_env, which locates the repository root by walking
# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,
# ...). Run `python bench_env.py` to print what was resolved. The aliased imports
# keep this block independent of whatever this module imported above, so it can
# sit at any top-level position.
import sys as _sys
from pathlib import Path as _Path

_p = _Path(__file__).resolve()
while not (_p / "bench_env.py").exists():
    if _p.parent == _p:
        raise RuntimeError(f"bench_env.py not found above {__file__}")
    _p = _p.parent
ROOT = _p
_sys.path.insert(0, str(ROOT))
from bench_env import RESULTS  # noqa: E402


import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient  # noqa: E402


RESULTS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- probe battery
# (state, supported statement, distractor statements)
ITEM_SPECS: list[tuple[str, str, list[str]]] = [
    (
        "Quarterly report. The logistics division shipped 4,182 pallets in Q3, "
        "up from 3,900 in Q2. Warehouse overtime fell 12 percent.",
        "The logistics division shipped 4,182 pallets in Q3.",
        ["The logistics division shipped 3,900 pallets in Q3.",
         "The logistics division shipped 5,240 pallets in Q3.",
         "Warehouse overtime rose 12 percent.",
         "Warehouse overtime was unchanged.",
         "The report covers the fiscal year.",
         "The logistics division shipped 4,182 pallets in Q2.",
         "The report was filed late.",
         "The logistics division closed two warehouses.",
         "Overtime was recorded in hours.",
         "The report covers four divisions.",
         "Q3 shipments exceeded Q2.",
         "The finance division audited the report.",
         "Pallets were counted at dispatch.",
         "The report was signed by the director.",
         "Q2 shipments were lower than Q3.",
         "The division employs 240 staff.",
         "The report was distributed internally.",
         "Shipping costs fell.",
         "The report is quarterly.",
         "Q3 ended in September."],
    ),
    (
        "Incident review. The authentication service returned HTTP 503 for 47 minutes "
        "on 14 March. The root cause was a misconfigured connection pool.",
        "The authentication service returned HTTP 503 for 47 minutes.",
        ["The authentication service returned HTTP 503 for 74 minutes.",
         "The authentication service returned HTTP 500 for 47 minutes.",
         "The root cause was a failed deployment.",
         "The root cause was a misconfigured connection pool.",
         "The incident occurred on 14 April.",
         "The incident was resolved in 47 minutes.",
         "The review covers one incident.",
         "The service is publicly accessible.",
         "The pool size was increased.",
         "The incident was reported by a customer.",
         "The review was conducted by the vendor.",
         "A postmortem was published.",
         "The service returned errors for under an hour.",
         "The incident affected all regions.",
         "The review lists three root causes.",
         "The connection pool was reset.",
         "The incident was detected automatically.",
         "The review is annual.",
         "The service was restored.",
         "The incident had a severity rating."],
    ),
    (
        "Audit finding. Invoice INV-4471 was issued on 2 February for 18,400 USD to "
        "Meridian Supplies. Payment cleared on 27 February.",
        "Invoice INV-4471 was issued for 18,400 USD.",
        ["Invoice INV-4471 was issued for 14,800 USD.",
         "Invoice INV-4471 was issued for 18,040 USD.",
         "Invoice INV-4471 was issued on 2 March.",
         "Invoice INV-4471 was paid to Meridian Supplies.",
         "Payment cleared on 27 March.",
         "Payment is still outstanding.",
         "The invoice was issued to a different vendor.",
         "The invoice number contains four digits.",
         "The audit covers one invoice.",
         "The invoice was disputed.",
         "Payment cleared within the same month.",
         "The invoice was issued in February.",
         "The audit was conducted quarterly.",
         "Meridian Supplies is a registered vendor.",
         "The invoice amount is in USD.",
         "The payment method was a bank transfer.",
         "The audit found no exceptions.",
         "The invoice was approved by a manager.",
         "The audit covers three years.",
         "Meridian Supplies was paid."],
    ),
]


def build_items(seed: int = 20260922) -> list[dict]:
    """Deterministic item set: for each spec, sample distractors at each N level."""
    rng = random.Random(seed)
    items: list[dict] = []
    for idx, (state, supported, distractors) in enumerate(ITEM_SPECS):
        for n in (2, 5, 10, 15, 20, 25):
            k = min(n - 1, len(distractors))
            pool = list(distractors)
            rng.shuffle(pool)
            chosen = pool[:k]
            options = [supported, *chosen]
            # deterministic order, recorded so position is analysable
            rng.shuffle(options)
            options = list(dict.fromkeys(options))  # stable dedupe, keep order
            items.append({
                "item_id": f"RC-{idx:02d}-N{len(options):02d}",
                "spec_index": idx,
                "state": state,
                "supported": supported,
                "options": options,
            })
    return items


def auc_supported_above_distractors(probs: dict, supported: str) -> float | None:
    """P(p_supported > p_distractor) with ties counted as 0.5. None if degenerate."""
    if supported not in probs:
        return None
    ps = float(probs[supported])
    others = [float(v) for k, v in probs.items() if k != supported]
    if not others:
        return None
    wins = sum(1.0 if ps > o else 0.5 if ps == o else 0.0 for o in others)
    return wins / len(others)


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    items = build_items()
    rows: list[dict] = []

    for it in items:
        # Budget assertion BEFORE the call: tokenize it ourselves, never trust the
        # planner's chars/4*1.15 estimate (R13 constraint 1-2).
        state_tokens = client.count_tokens(it["state"])
        q = {
            "supported": {
                "type": "choice",
                "instructions": (
                    "Which single statement is directly supported by the figures "
                    "given in the state? Choose the option whose content the state "
                    "actually states."
                ),
                "criteria": {o: o for o in it["options"]},
            }
        }
        try:
            resp = client.ask(it["state"], q)
        except Exception as exc:
            rows.append({**{k: it[k] for k in ("item_id", "spec_index")},
                         "n_options": len(it["options"]), "error": str(exc)[:200]})
            continue

        ans = (resp.get("answers") or {}).get("supported")
        if not isinstance(ans, dict):
            rows.append({**{k: it[k] for k in ("item_id", "spec_index")},
                         "n_options": len(it["options"]),
                         "error": f"unexpected answer shape: {json.dumps(resp)[:200]}"})
            continue

        probs = ans.get("probabilities") or {}
        chosen = ans.get("choice")
        bs = resp.get("budget_summary") or {}
        rows.append({
            "item_id": it["item_id"],
            "spec_index": it["spec_index"],
            "n_options": len(it["options"]),
            "state_tokens": state_tokens,
            "returned_type": ans.get("type"),
            "chosen": chosen,
            "correct": chosen == it["supported"],
            "p_supported": float(probs.get(it["supported"], float("nan"))),
            "p_max_distractor": max(
                [float(v) for k, v in probs.items() if k != it["supported"]],
                default=float("nan")),
            "auc": auc_supported_above_distractors(probs, it["supported"]),
            "confidence": ans.get("confidence"),
            "tightest_option_tokens_each": bs.get("tightest_option_tokens_each"),
            "truncated": resp.get("truncated"),
            "warnings": resp.get("warnings") or [],
            "latency_ms": resp.get("latency_ms"),
        })
        print(f"{it['item_id']:<14} n={len(it['options']):>2} "
              f"correct={str(rows[-1]['correct']):<5} "
              f"p_sup={rows[-1]['p_supported']:.4f} auc={rows[-1]['auc']}")

    # ------------------------------------------------------------------ summary
    # AUDIT FIX (finding S-1): this bucket list was hard-coded to (2,5,10,15,20,25)
    # while the generator actually renders {2,5,10,15,20,21}. The three N=21 calls
    # therefore fell into NO bucket and vanished from `by_n` silently -- instrument
    # recorded 18 calls, by_n summed to 15. Buckets are now derived from the data, so
    # a mismatch between the intended and rendered option counts cannot hide rows again.
    summary: dict = {"n_items": len(rows), "by_n": {}}
    present = sorted({r["n_options"] for r in rows if r.get("n_options") is not None})
    expected = (2, 5, 10, 15, 20, 25)
    if set(present) - set(expected):
        summary["unexpected_option_counts"] = sorted(set(present) - set(expected))
    for n in sorted(set(expected) | set(present)):
        sub = [r for r in rows if r.get("n_options") == n and "error" not in r]
        if not sub:
            continue
        aucs = [r["auc"] for r in sub if r["auc"] is not None]
        summary["by_n"][n] = {
            "n_calls": len(sub),
            "accuracy": sum(1 for r in sub if r["correct"]) / len(sub),
            "auc_mean": statistics.fmean(aucs) if aucs else None,
            "win_rate": sum(1 for r in sub
                            if r["p_supported"] > r["p_max_distractor"]) / len(sub),
            "p_supported_mean": statistics.fmean(r["p_supported"] for r in sub),
            "option_tokens_each": sub[0].get("tightest_option_tokens_each"),
            "any_truncated": any(r.get("truncated") for r in sub),
        }

    summary["instrument"] = {
        "sidecar_version": client.version(),
        "restart_count": client.restart_count,
        "cold_start_ms": client.cold_start_ms,
        "calls": client.call_count,
        "entry_point": "HTTP 127.0.0.1:8787 (Path A: planner 1024/512)",
    }
    summary["caveat"] = (
        "PROBE BATTERY, NOT THE STUDY BATTERY. 3 authored specs x 6 cardinalities, "
        "one call each. This brackets a ceiling and characterises a curve; it is far "
        "too small to estimate the study's accuracy. Overlapping option subsets are "
        "shared across N levels, so calls are not independent."
    )
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    path = RESULTS / "P1-rank-vs-choice.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {path}")
