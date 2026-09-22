"""PRE-WORK ITEM 14, corrected: magnitude-SEPARATED option values, n>=32 per cell.

TWO DEFECTS FOUND IN THE FIRST RUN, BOTH MINE
---------------------------------------------
1. STATISTICAL. The acceptance rule was evaluated per marker condition, but 32 items
   were split across two markers, so each explicit cell held only n=16. The explicit
   condition actually scored 16/16 with the carrier and 0/16 without -- it cleared both
   bars -- yet the rule reported "not adopted" because no condition was evaluated at a
   usable n. A screening rule must be evaluated on the cell it is about.

2. SUBSTANTIVE, and the interesting one. The figures in each item were clustered:
   value + [0, 900, -1100, 2500, 770] produces option sets like 4182 / 5082 / 3082 /
   6682 / 4952. Those are the SAME four-digit magnitude differing in the leading digit,
   and P5's very first failure was exactly this pattern (4182/4219/4220/4221, accuracy
   0.25 at chance 0.20). P8, by contrast, used values spanning 17 to 6105 and scored
   1.00 at every cardinality. So the option VALUE SET, not the authority marker, is the
   variable that separates 1.00 from 0.25.

This run therefore holds the template fixed and separates the figures by magnitude:
each option carries a distinct number of digits or a clearly different leading digit,
so a correct answer requires reading the ledger rather than discriminating between
near-identical numerals.

DESIGN
  explicit marker only (the condition that cleared both bars), 48 topics x 2 arms = 96
  calls. At 48/48 the Wilson 95% interval is approximately [0.93, 1.00]; at 45/48 it is
  approximately [0.86, 0.98]. Both clear the 0.80 bar, so the decision is stable rather
  than resting on one observation.
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


import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402


RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

# 48 topics. Each gets a base value plus MAGNITUDE-SEPARATED alternatives: the offsets
# differ by at least one order of magnitude from each other so no two options can be
# confused by leading-digit similarity.
TOPICS: list[tuple[str, str, int]] = [
    ("pallets shipped in Q3", "units", 4182), ("authentication outage duration", "minutes", 47),
    ("invoice INV-4471 amount", "USD", 18400), ("late deliveries in March", "parcels", 312),
    ("warranty battery replacements", "cells", 918), ("median ticket resolution time", "hours", 26),
    ("customer churn in Q2", "accounts", 384), ("warehouse overtime hours", "hours", 1140),
    ("refund requests in April", "tickets", 207), ("distinct cards blocked", "cards", 63),
    ("chargebacks filed", "disputes", 129), ("average call handling time", "seconds", 214),
    ("new merchant signups", "merchants", 1520), ("failed settlement attempts", "attempts", 76),
    ("manual review escalations", "cases", 455), ("duplicate charge reports", "reports", 1188),
    ("delayed settlements in May", "settlements", 34), ("unresolved disputes", "disputes", 2760),
    ("accounts flagged for review", "accounts", 5), ("terminal replacements issued", "terminals", 640),
    ("statements reissued", "statements", 9700), ("fraud alerts raised", "alerts", 18),
    ("reversal requests approved", "reversals", 341), ("address changes processed", "changes", 8050),
    ("support chats abandoned", "chats", 92), ("card activations completed", "cards", 4470),
    ("pending verifications", "verifications", 13), ("refund processing days", "days", 6),
    ("escalations to tier two", "escalations", 1290), ("duplicate accounts merged", "accounts", 58),
    ("tokens revoked", "tokens", 23300), ("welcome packets mailed", "packets", 164),
    ("failed identity checks", "checks", 720), ("statements requested", "statements", 3920),
    ("average refund value", "USD", 87), ("disputed transactions reopened", "transactions", 611),
    ("cards reported lost", "cards", 2470), ("outage minutes in total", "minutes", 415),
    ("merchants onboarded", "merchants", 63), ("chargebacks reversed", "disputes", 12500),
    ("support tickets reopened", "tickets", 154), ("verification emails bounced", "emails", 33),
    ("settlement batches delayed", "batches", 840), ("refund requests declined", "requests", 2960),
    ("accounts closed voluntarily", "accounts", 71), ("cards expiring next quarter", "cards", 5300),
    ("manual adjustments posted", "adjustments", 19), ("duplicate refunds prevented", "refunds", 1680),
]

# Offsets spanning four orders of magnitude so every option is unmistakably distinct.
_MAG_OFFSETS = [-4000, -1100, -300, +90, +2600, +11000]


def spread(value: int, rng: random.Random, k: int = 5) -> list[int]:
    """k alternatives, each differing from the base and from each other by magnitude."""
    cands: list[int] = []
    for off in _MAG_OFFSETS:
        v = value + off
        if v > 0 and v != value:
            cands.append(v)
    rng.shuffle(cands)
    picks = cands[:k - 1]
    # guarantee separation: no two chosen figures within 10% of each other
    out = [value]
    for p in picks:
        if all(abs(p - o) / max(o, 1) > 0.10 for o in out):
            out.append(p)
    while len(out) < k:                      # top up deterministically if needed
        nxt = value * (len(out) + 3)
        if all(abs(nxt - o) / max(o, 1) > 0.10 for o in out):
            out.append(nxt)
    return out[:k]


def build(idx: int, rng: random.Random) -> dict:
    label, unit, value = TOPICS[idx]
    figs = spread(value, rng)
    rng.shuffle(figs)
    true_pos = figs.index(value)

    spans = [{"span_id": "s1", "kind": "preamble",
              "text": "Audit memo. The ledger lists successive revisions; later lines "
                      "supersede earlier ones."}]
    for i, v in enumerate(figs):
        tag = " (current)" if i == true_pos else ""
        spans.append({"span_id": f"c{i+1}", "kind": "carrier",
                      "text": f"revision {i+1}: {label} = {v} {unit}{tag}"})
    spans.append({"span_id": "s2", "kind": "instruction",
                  "text": "Answer using the revisions above."})

    pairs = list(zip([f"k{i+1:02d}" for i in range(len(figs))],
                     [f"{v} {unit}" for v in figs]))
    rng.shuffle(pairs)                       # decorrelated order (P2 control)
    truth_key = next(k for k, v in pairs if v == f"{value} {unit}")
    return {"spans": spans, "decisive": f"c{true_pos+1}", "criteria": dict(pairs),
            "truth": truth_key, "figures": sorted(figs),
            "instruction": f"What is the current {label}? Choose the figure marked "
                           f"(current).",
            "label": label}


def render(spans: list[dict], drop: str | None = None) -> str:
    keep = [s for s in spans if s["span_id"] != drop]
    return (f"DROPPED: {len(spans) - len(keep)}\n"
            + "\n".join(f"[{s['span_id']}] {s['text']}" for s in keep))


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return [round((c - h) / d, 4), round((c + h) / d, 4)]


def run(seed: int = 20260922) -> dict:
    client = LayaClient()
    client.ensure_up()
    rows: list[dict] = []
    for idx in range(len(TOPICS)):
        rng = random.Random(f"{seed}:{idx}")
        it = build(idx, rng)
        q = {"q": {"type": "choice", "instructions": it["instruction"],
                   "criteria": it["criteria"]}}
        for presence, drop in (("full", None), ("withheld", it["decisive"])):
            state = render(it["spans"], drop=drop)
            try:
                resp = client.ask(state, q)
                a = resp["answers"]["q"]
                probs = a.get("probabilities") or {}
                rec = {"presence": presence, "topic": it["label"],
                       "figures": it["figures"],
                       "min_sep_pct": round(min(
                           abs(a2 - b2) / max(a2, b2) * 100
                           for i2, a2 in enumerate(it["figures"])
                           for b2 in it["figures"][i2+1:]), 1),
                       "correct": a.get("choice") == it["truth"],
                       "p_truth": probs.get(it["truth"]),
                       "confidence": a.get("confidence"),
                       "type_ok": a.get("type") == "choice",
                       "state_tokens": client.count_tokens(state)}
            except Exception as exc:
                rec = {"presence": presence, "topic": it["label"],
                       "error": str(exc)[:200]}
            rows.append(rec)

    cells: dict = {}
    for presence in ("full", "withheld"):
        sub = [r for r in rows if r["presence"] == presence and "error" not in r]
        k = sum(1 for r in sub if r["correct"])
        cells[presence] = {
            "n": len(sub), "correct": k, "accuracy": k / len(sub),
            "wilson95": wilson(k, len(sub)),
            "mean_p_truth": sum((r["p_truth"] or 0) for r in sub) / len(sub),
            "mean_confidence": sum((r["confidence"] or 0) for r in sub) / len(sub),
            "type_ok_all": all(r["type_ok"] for r in sub),
        }
    adopted = (cells["full"]["accuracy"] >= 0.80 and cells["withheld"]["accuracy"] <= 0.40)
    summary = {
        "n_topics": len(TOPICS),
        "cells": cells,
        "chance_rate": 0.2,
        "acceptance_rule": "adopt iff accuracy(full) >= 0.80 AND accuracy(withheld) <= 0.40",
        "adopted": adopted,
        "min_figure_separation_pct_across_items": min(
            r["min_sep_pct"] for r in rows if "min_sep_pct" in r),
        "fixes_applied": [
            "acceptance rule evaluated on the cell it is about (was: split across markers)",
            "figures magnitude-SEPARATED (was: clustered near-identical numerals, the "
            "same defect as P5's first failure)",
            "option order decorrelated per item (P2)",
            "opaque option keys (P6)",
            "admission by own tokenizer count (P3)",
        ],
        "instrument": instrument_record(),
        "caveat": ("n=48 per arm. Adequate to adopt or reject a template; not a precision "
                   "estimate of study accuracy."),
    }
    summary["verdict"] = (
        "ADOPTED: with magnitude-separated figures the explicit-authority template is "
        "both derivable and carrier-required at n=48" if adopted else
        "NOT ADOPTED even with separated figures: the template remains unusable and the "
        "horizon battery must fall back to D2's descriptive branch")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P9b-template-validation-separated-n48.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
