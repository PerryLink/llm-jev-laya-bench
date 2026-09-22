"""PRE-WORK ITEM 7: does the LOW-cardinality end behave differently from the high end?

WHY THIS EXISTS
---------------
Two independent observations suggested the option-count curve is not monotone, which
would be surprising enough to matter for every choice question in the study:

  * P1 found accuracy 0.33 at N=2 but 1.00 at N=5 -- the two-option case was the WORST
    of the small cardinalities, and its AUC was 0.33, i.e. worse than chance.
  * R13 measured `confidence` 0.8055 at N=2 against 0.8690 at N=10, and the shipped
    `temperature_by_options` map gives `choice:2 = 1.906` (heavily sharpened) versus
    `choice:6-10 = 1.000` (untouched). A sharply sharpened 2-way distribution is
    exactly what would produce a confident wrong answer on the easiest possible question.

The practical stake: if two-option questions -- the most common shape in the whole
battery, including every `noul` carried as a choice -- carry a systematic error, then a
large share of planned items sit in the worst regime rather than the safest one.

DESIGN
------
One state, one question, five cardinalities 2/3/5/8/12, eight semantically distinct
options drawn from a pool, with ground truth by construction (the option that matches a
stated figure) and options ORDER-SHUFFLED per item with the truth position recorded
(the P2 lesson). n=8 items per cardinality, so one item moves a rate by 0.125.

The pool options are deliberately of the same TYPE (all figures with units) so that
cardinality, not category heterogeneity, is what varies.
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402


RESULTS.mkdir(parents=True, exist_ok=True)

SCENARIOS = [
    ("pallets shipped in Q3", "units", 4182),
    ("authentication outage duration", "minutes", 47),
    ("invoice amount", "USD", 18400),
    ("late deliveries in March", "parcels", 312),
    ("warranty battery replacements", "cells", 918),
    ("median ticket resolution time", "hours", 26),
    ("customer churn in Q2", "accounts", 384),
    ("warehouse overtime hours", "hours", 1140),
]

# Distractor figures of the same type but clearly different magnitude, so a correct
# answer requires reading, not guessing near a cluster.
DISTRACTORS = [17, 61, 250, 733, 1980, 3600, 4400, 6105, 8200, 12400, 31500, 48000]


def build(level_n: int, label: str, unit: str, truth: int, rng: random.Random) -> dict:
    pool = [d for d in DISTRACTORS if d != truth]
    rng.shuffle(pool)
    vals = [truth] + pool[: level_n - 1]
    order = list(range(len(vals)))
    rng.shuffle(order)
    vals = [vals[i] for i in order]
    keys = [f"o{i+1:02d}" for i in range(len(vals))]
    pairs = list(zip(keys, [f"{v} {unit}" for v in vals]))
    rng.shuffle(pairs)
    truth_key = next(k for k, v in pairs if v == f"{truth} {unit}")
    state = (f"Audit memo. The ledger records several figures for {label}. "
             f"The authoritative entry states {label} = {truth} {unit}.")
    return {"state": state, "criteria": dict(pairs), "truth": truth_key,
            "n": len(pairs), "truth_pos": [k for k, _ in pairs].index(truth_key)}


def run(n_per_cell: int = 8, seed: int = 20260922) -> dict:
    client = LayaClient()
    client.ensure_up()
    rng = random.Random(seed)
    rows: list[dict] = []
    for n in (2, 3, 5, 8, 12):
        for i in range(n_per_cell):
            label, unit, truth = SCENARIOS[i % len(SCENARIOS)]
            it = build(n, label, unit, truth, rng)
            try:
                resp = client.ask(it["state"], {"q": {
                    "type": "choice",
                    "instructions": f"What is the {label}? Choose the authoritative "
                                    f"figure stated in the ledger.",
                    "criteria": it["criteria"]}})
                a = resp["answers"]["q"]
                probs = a.get("probabilities") or {}
                rows.append({"n": it["n"], "correct": a.get("choice") == it["truth"],
                             "chosen": a.get("choice"), "truth": it["truth"],
                             "p_truth": probs.get(it["truth"]),
                             "p_max": max(probs.values()) if probs else None,
                             "confidence": a.get("confidence"),
                             "truth_pos": it["truth_pos"],
                             "type_ok": a.get("type") == "choice"})
            except Exception as exc:
                rows.append({"n": it["n"], "error": str(exc)[:160]})

    by_n: dict = {}
    for n in (2, 3, 5, 8, 12):
        sub = [r for r in rows if r["n"] == n and "error" not in r]
        if not sub:
            continue
        by_n[n] = {
            "n_calls": len(sub),
            "accuracy": sum(1 for r in sub if r["correct"]) / len(sub),
            "chance": round(1.0 / n, 4),
            "mean_p_truth": sum((r["p_truth"] or 0) for r in sub) / len(sub),
            "mean_confidence": sum((r["confidence"] or 0) for r in sub) / len(sub),
            "mean_truth_pos": sum(r["truth_pos"] for r in sub) / len(sub),
            "all_types_ok": all(r["type_ok"] for r in sub),
        }
    accs = {n: v["accuracy"] for n, v in by_n.items()}
    summary = {
        "by_cardinality": by_n,
        "monotone_increasing": all(accs[a] <= accs[b] for a, b in
                                   zip(sorted(accs), sorted(accs)[1:])),
        "n2_accuracy": accs.get(2),
        "n5_accuracy": accs.get(5),
        "low_end_penalty": (accs.get(5) - accs.get(2)) if (2 in accs and 5 in accs) else None,
        "verdict": None,
        "instrument": instrument_record(),
        "caveat": (f"PROBE: {n_per_cell} items per cardinality, single seed. One item "
                   f"moves a cell rate by {1.0/n_per_cell:.3f}, so only a LARGE low-end "
                   f"penalty is interpretable here."),
    }
    if 2 in accs and 5 in accs:
        if accs[2] < accs[5] - 0.25:
            summary["verdict"] = ("LOW-END PENALTY REPRODUCED: two-option questions score "
                                  "materially below five-option ones, so the shipped "
                                  "choice:2 temperature is suspect and `noul`-carried-as-"
                                  "choice items sit in a worse regime than assumed")
        else:
            summary["verdict"] = ("NO MATERIAL LOW-END PENALTY at this n: the P1 N=2 "
                                  "result does not reproduce as a systematic effect")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P8-low-cardinality.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
