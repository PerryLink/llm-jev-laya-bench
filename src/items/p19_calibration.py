"""Calibration corpus: >=1000 binary items with PROGRAMMATIC ground truth.

WHY THIS IS THE MISSING PIECE
-----------------------------
Result C currently reads "confidence is decoupled from correctness", supported by
handfuls of vivid cases (0.9981 on the one wrong answer; 0.9989 on pure noise). Vivid
cases are not a calibration curve. Both R13 and R12 independently derived the sample
size: about 385 items for a +-0.05 accuracy figure, >=500 for a reliability curve with 10
bins, and >=1000 to compare two judges' ECE. The largest cell anywhere in this project is
n=48, so no calibration claim can currently be made quantitatively.

ANNOTATION IS NOT NEEDED, AND THAT WAS THE USER'S CONSTRAINT
------------------------------------------------------------
Labels are computed by construction, not by a human and not by a model. Each item names a
figure and a candidate value, and the truth is decided by the generator's own bookkeeping.
That removes both the annotation burden and the circularity of using a judge to make the
answer key.

THE DESIGN PROBLEM THAT MATTERS
-------------------------------
A calibration curve is only informative if the confidence scores are SPREAD OUT. Items
that are trivially true produce a spike at 1.0 and a curve of one point. So difficulty is
an explicit, crossed factor with four levels chosen to put mass at different confidences
while keeping the truth unambiguous at every level:

  explicit_support    the state states the candidate value AS the current value   -> true
  explicit_contra     the state states a DIFFERENT value as current               -> false
  partial_support     the candidate appears, with a marker implying currency but
                      not stating it outright                                    -> true
  partial_contra      a different value carries the marker, the candidate is listed
                      without it                                                 -> false
  no_support          the candidate value does not appear at all                  -> false

`no_support` is the one that directly tests the protocol rule "absence of a statement is
NOT evidence for it": a well-behaved judge should answer false, and a lenient one will
drift toward 0.5 or above. It is the calibration analogue of the benign-paraphrase
control, and it is where a judge with a surface-cue habit is expected to break.

Both judges run on every item, so the LLM and Laya reliability curves are paired and
their ECE difference is within-item rather than across-corpus.
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


sys.path.insert(0, str(ROOT / "src" / "instrument"))
from deepseek_client import (chat, parse_label, parse_prob,  # noqa: E402
                             prompt_forced_choice)
from laya_client import LayaClient, instrument_record  # noqa: E402

RESULTS = ROOT / "results"

QUANTITIES = [
    ("pallets shipped in Q3", "units"), ("authentication outage duration", "minutes"),
    ("invoice amount", "USD"), ("late deliveries in March", "parcels"),
    ("warranty battery replacements", "cells"), ("median ticket resolution time", "hours"),
    ("customer churn in Q2", "accounts"), ("warehouse overtime hours", "hours"),
    ("refund requests in April", "tickets"), ("distinct cards blocked", "cards"),
    ("chargebacks filed", "disputes"), ("average call handling time", "seconds"),
    ("new merchant signups", "merchants"), ("failed settlement attempts", "attempts"),
    ("manual review escalations", "cases"), ("duplicate charge reports", "reports"),
    ("delayed settlements in May", "settlements"), ("unresolved disputes", "disputes"),
    ("accounts flagged for review", "accounts"), ("terminal replacements issued", "terminals"),
    ("statements reissued", "statements"), ("fraud alerts raised", "alerts"),
    ("reversal requests approved", "reversals"), ("address changes processed", "changes"),
]

LEVELS = ["explicit_support", "explicit_contra", "partial_support",
          "partial_contra", "no_support"]


def distinct_values(base: int, rng: random.Random, k: int = 4) -> list[int]:
    """Values separated by magnitude so no two are confusable as numerals."""
    out = [base]
    for mult in (11, 47, 3, 19):
        v = base * mult
        if all(abs(v - o) / max(o, 1) > 0.15 for o in out):
            out.append(v)
    while len(out) < k:
        out.append(base * (len(out) + 7))
    return out[:k]


def build_item(idx: int, level: str, rng: random.Random) -> dict:
    label, unit = QUANTITIES[idx % len(QUANTITIES)]
    base = rng.choice([120, 340, 918, 1520, 4182, 9700])
    vals = distinct_values(base, rng)
    other = vals[1]
    cand = vals[0]
    rng.shuffle(vals)

    if level == "explicit_support":
        truth = True
        lines = [f"{label} = {cand} {unit} (current)",
                 f"{label} = {other} {unit}"]
        q = f"Does the state record {cand} {unit} as the current {label}?"
    elif level == "explicit_contra":
        truth = False
        lines = [f"{label} = {other} {unit} (current)",
                 f"{label} = {cand} {unit}"]
        q = f"Does the state record {cand} {unit} as the current {label}?"
    elif level == "partial_support":
        truth = True
        lines = [f"{label}: {cand} {unit}, recorded as the latest revision",
                 f"{label}: {other} {unit}, earlier revision"]
        q = f"Does the state record {cand} {unit} as the current {label}?"
    elif level == "partial_contra":
        truth = False
        lines = [f"{label}: {other} {unit}, recorded as the latest revision",
                 f"{label}: {cand} {unit}, earlier revision"]
        q = f"Does the state record {cand} {unit} as the current {label}?"
    else:  # no_support
        truth = False
        lines = [f"{label} = {other} {unit} (current)"]
        q = f"Does the state record {cand} {unit} as the current {label}?"

    rng.shuffle(lines)
    state = ("Ledger extract. Successive revisions may appear; the one marked (current) "
             "or latest is authoritative.\n" + "\n".join(lines))
    return {"item_id": f"CAL-{level}-{idx:04d}", "level": level, "truth": truth,
            "candidate": cand, "unit": unit, "quantity": label, "question": q,
            "state": state, "criteria": {
                "true": f"the state records {cand} {unit} as the current {label}",
                "false": f"the state does not record {cand} {unit} as the current {label}"}}


def ece_bins(pairs: list[tuple[float, bool]], n_bins: int = 10) -> dict:
    """Reliability table + ECE. `pairs` are (stated P(true), actual truth)."""
    bins = [[] for _ in range(n_bins)]
    for p, t in pairs:
        i = min(n_bins - 1, max(0, int(p * n_bins)))
        bins[i].append((p, t))
    rows, ece, n = [], 0.0, len(pairs)
    for i, b in enumerate(bins):
        if not b:
            rows.append({"bin": f"{i/n_bins:.1f}-{(i+1)/n_bins:.1f}", "n": 0})
            continue
        mp = sum(p for p, _ in b) / len(b)
        mt = sum(1 for _, t in b if t) / len(b)
        rows.append({"bin": f"{i/n_bins:.1f}-{(i+1)/n_bins:.1f}", "n": len(b),
                     "mean_stated_p": round(mp, 4), "empirical_rate": round(mt, 4),
                     "gap": round(mt - mp, 4)})
        ece += (len(b) / n) * abs(mt - mp)
    # Brier + a constant-0.5 baseline, because a pure-ECE leaderboard rewards a judge
    # that predicts the base rate and has zero resolution (V3's calibration defect b).
    brier = sum((p - (1.0 if t else 0.0)) ** 2 for p, t in pairs) / n if n else None
    base = (sum(1 for _, t in pairs if t) / n) if n else None
    brier_const = sum((base - (1.0 if t else 0.0)) ** 2 for _, t in pairs) / n if n else None
    return {"n": n, "ece": round(ece, 4), "bins": rows,
            "brier": round(brier, 4) if brier is not None else None,
            "base_rate": round(base, 4) if base is not None else None,
            "brier_constant_predictor": round(brier_const, 4) if brier_const is not None else None,
            "beats_constant_predictor": (brier is not None and brier_const is not None
                                         and brier < brier_const)}


def run(per_level: int = 220, seed: int = 20260922) -> dict:
    client = LayaClient()
    client.ensure_up()
    rng = random.Random(seed)
    items = [build_item(i, lv, rng) for lv in LEVELS for i in range(per_level)]

    rows: list[dict] = []
    for it in items:
        rec = {"item_id": it["item_id"], "level": it["level"], "truth": it["truth"]}
        # ---- Laya: noul, so P(true) is `noul` directly (never `probability`)
        try:
            r = client.ask(it["state"], {"q": {"type": "noul",
                                               "instructions": it["question"],
                                               "criteria": it["criteria"]}})
            a = r["answers"]["q"]
            rec["laya_p"] = float(a["noul"])
            rec["laya_pred"] = rec["laya_p"] >= 0.5
            rec["laya_correct"] = rec["laya_pred"] == it["truth"]
        except Exception as exc:
            rec["laya_error"] = str(exc)[:160]
        # ---- LLM: forced choice with a stated probability.
        # PROBABILITY SEMANTICS, and this project has now hit this trap three times
        # (Jev's `probability`, the prose parser, the label-space mismatch). The prompt
        # asks for "prob = your probability that the chosen label is correct", so the
        # model's number is confidence in its OWN ANSWER, not P(claim is true). The pilot
        # run coded it as P(true), which inverted every item the model answered `false`
        # and produced a nonsense 0.0 accuracy on the explicit_contra level. P(true) must
        # be derived FROM the label:
        #     chose "true"  -> P(true) = prob
        #     chose "false" -> P(true) = 1 - prob
        try:
            lr = chat(prompt_forced_choice(it["state"], it["question"], it["criteria"]),
                      effort="none", json_mode=True, max_tokens=96)
            lab = parse_label(lr, it["criteria"])
            conf = parse_prob(lr)
            rec["llm_label"] = lab
            rec["llm_conf"] = conf
            if lab is None or conf is None:
                rec["llm_p"] = None
                rec["llm_pred"] = None
                rec["llm_correct"] = None
            else:
                rec["llm_p"] = conf if lab == "true" else 1.0 - conf
                rec["llm_pred"] = lab == "true"
                rec["llm_correct"] = rec["llm_pred"] == it["truth"]
            rec["llm_cost_usd"] = lr.cost.get("off_peak_usd")
        except Exception as exc:
            rec["llm_error"] = str(exc)[:160]
        rows.append(rec)

    def curves(prefix: str) -> dict:
        pairs = [(r[f"{prefix}_p"], r["truth"]) for r in rows
                 if r.get(f"{prefix}_p") is not None]
        acc = [r[f"{prefix}_correct"] for r in rows if r.get(f"{prefix}_correct") is not None]
        by_level = {}
        for lv in LEVELS:
            sub = [r for r in rows if r["level"] == lv and r.get(f"{prefix}_p") is not None]
            if sub:
                by_level[lv] = {
                    "n": len(sub),
                    "accuracy": round(sum(1 for r in sub if r[f"{prefix}_correct"]) / len(sub), 4),
                    "mean_p_true": round(sum(r[f"{prefix}_p"] for r in sub) / len(sub), 4),
                }
        return {"n_scored": len(acc),
                "accuracy": round(sum(1 for a in acc if a) / len(acc), 4) if acc else None,
                "calibration": ece_bins(pairs), "by_level": by_level}

    summary = {
        "n_items": len(rows),
        "levels": LEVELS,
        "laya": curves("laya"),
        "llm": curves("llm"),
        "instrument": instrument_record(),
        "controls": {
            "labels": "computed by construction; no human and no model made the answer key",
            "difficulty": "crossed factor; `no_support` tests whether absence is treated "
                          "as evidence for the claim",
            "brier_vs_constant": "reported because pure ECE rewards a zero-resolution "
                                 "judge that predicts the base rate",
        },
        "caveat": (f"{len(rows)} items from templates, one sample per item per judge. "
                   f"Adequate for a reliability curve and an ECE comparison; the items are "
                   f"formulaic, so absolute accuracy is not a capability estimate."),
    }
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run(per_level=220)
    p = RESULTS / "P19-calibration.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    s = out["summary"]
    print(f"items: {s['n_items']}")
    for who in ("laya", "llm"):
        c = s[who]
        print(f"\n=== {who.upper()} ===  accuracy={c['accuracy']} n={c['n_scored']}")
        print(f"  ECE={c['calibration']['ece']}  Brier={c['calibration']['brier']} "
              f"(const {c['calibration']['brier_constant_predictor']})  "
              f"base_rate={c['calibration']['base_rate']}  "
              f"beats_const={c['calibration']['beats_constant_predictor']}")
        for lv, d in c["by_level"].items():
            print(f"    {lv:<18} n={d['n']:<4} acc={d['accuracy']:<7} mean_p={d['mean_p_true']}")
        print("  bins:")
        for b in c["calibration"]["bins"]:
            if b["n"]:
                print(f"    {b['bin']}  n={b['n']:<4} stated={b['mean_stated_p']:<7} "
                      f"empirical={b['empirical_rate']:<7} gap={b['gap']}")
    print(f"\nwritten: {p}")
