"""Classifier-template probe: find a template Laya can actually ANSWER.

WHY THIS EXISTS (the P5 certificate check failed)
-------------------------------------------------
The first EVIDENCE-BRIEF design asked "What is the <label>?" with criteria options that
were NUMERIC values (4182 / 4219 / 4220 / 4221), and the certificate verification
measured 0.25 accuracy WITH the decisive line in plain view -- essentially chance
(0.20). Per this project's own rule, that condemns the ACTION, not the actor: an item a
judge cannot answer even when the answer is visible is not a judge failure, it is an
item-construction failure, and building a horizon claim on it would manufacture "drift"
that is really item noise.

Two diagnosed causes:

  1. NUMERIC OPTIONS ARE NEAR-INDISTINGUISHABLE. Laya scores options by matching option
     text against the state; candidate figures differing by 1-40 units carry almost no
     distinguishing signal. Real datasets do not look like this (MASSIVE ships
     `alarm_set`, CLINC150 ships short intent names -- semantically distinct labels).
  2. NO ANSWERABILITY MARKER. Multiple ledger lines all asserted a value for the same
     label with nothing indicating which was authoritative, so the item was
     under-determined and NOT derivable. That is exactly V4's T3 failure mode,
     reproduced live.

THIS PROBE COMPARES TEMPLATES
----------------------------
Five candidate templates, all with a decisive line marked `(current)` so answerability
is explicit and the carrier is genuinely necessary:

  T1 figure-select    options are distinct VALUES, question asks for the current value
  T2 version-select   options are distinct VERSIONS, question asks which is current
  T3 claim-select     options are distinct SENTENCES, one states the current value
  T4 attribute-select options are distinct ATTRIBUTES, one matches the current line
  T5 boolean          noul: does the state record <value> as current?

Selection rule is pre-declared: adopt the template with the highest carrier-present
accuracy, provided the withheld-carrier arm does not also score well. If no template
clears 0.80, the family is not viable as an ML classifier target and the paper must not
build a horizon claim on it.
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

TOPICS = [
    ("pallets shipped in Q3", 4182, "units"),
    ("authentication outage duration", 47, "minutes"),
    ("invoice INV-4471 amount", 18400, "USD"),
    ("late deliveries in March", 312, "parcels"),
    ("warranty battery replacements", 918, "cells"),
    ("median ticket resolution time", 26, "hours"),
    ("customer churn in Q2", 384, "accounts"),
    ("warehouse overtime hours", 1140, "hours"),
]

# Semantically distinct alternative values: each is a *different quantity type* or
# magnitude from a different plausible reading, not a ±1 perturbation.
DISTINCT_FIGURES = {
    "units": [4182, 3900, 5240, 2870, 6105],
    "minutes": [47, 74, 12, 240, 95],
    "USD": [18400, 14800, 1840, 184000, 41000],
    "parcels": [312, 132, 521, 231, 465],
    "cells": [918, 198, 890, 1200, 405],
    "hours": [26, 62, 4, 210, 48],
    "accounts": [384, 843, 38, 438, 284],
}

VERSION_WORDS = ["revision A", "revision B", "revision C", "revision D", "revision E"]

ATTRIBUTES = [
    ("recorded at the northern depot", "the northern depot"),
    ("recorded at the coastal hub", "the coastal hub"),
    ("recorded at the inland centre", "the inland centre"),
    ("recorded at the river terminal", "the river terminal"),
    ("recorded at the airport annex", "the airport annex"),
]


def build_state(label: str, unit: str, true_val: int, alts: list[int],
                kind: str) -> tuple[list[dict], str, dict]:
    """Fixed-width carrier; the decisive line is marked `(current)` so answerability
    is explicit. Returns (spans, decisive_span_id, meta)."""
    spans = [
        {"span_id": "s1", "kind": "preamble",
         "text": "Audit memo covering the period under review."},
        {"span_id": "s2", "kind": "context",
         "text": f"The {label} is recorded in the ledger below. "
                 f"The line marked (current) is authoritative."},
    ]
    vals = [true_val] + alts[:4]
    rng = random.Random(hash((label, true_val, kind)) & 0xFFFF)
    rng.shuffle(vals)
    true_pos = vals.index(true_val)
    for i, v in enumerate(vals):
        mark = " (current)" if i == true_pos else ""
        spans.append({"span_id": f"c{i+1}", "kind": "carrier",
                      "text": f"ledger line {i+1}: {label} = {v} {unit}{mark}"})
    spans.append({"span_id": "s3", "kind": "instruction",
                  "text": "Answer using the ledger lines above."})
    return spans, f"c{true_pos+1}", {"true_pos": true_pos, "carrier_len": len(vals)}


def make_template(kind: str, label: str, unit: str, true_val: int,
                  rng: random.Random) -> dict:
    alts_all = [v for v in DISTINCT_FIGURES[unit] if v != true_val]
    rng.shuffle(alts_all)
    alts = alts_all[:4]
    spans, decisive, meta = build_state(label, unit, true_val, alts, kind)
    hint = " (current)"
    # find the rendered decisive line text to build claim options
    decisive_text = next(s["text"] for s in spans if s["span_id"] == decisive)

    if kind == "T1_figure_select":
        cands = [true_val] + alts
        rng.shuffle(cands)
        crit = {f"i{i+1:02d}": f"{v} {unit}" for i, v in enumerate(cands)}
        truth = next(k for k, v in crit.items() if v == f"{true_val} {unit}")
        q = {"instructions": f"What is the current {label}? "
                             f"Choose the figure marked (current).", "criteria": crit}

    elif kind == "T2_version_select":
        marks = [s["text"] for s in spans if s["kind"] == "carrier"]
        crit = {f"i{i+1:02d}": VERSION_WORDS[i] for i in range(len(marks))}
        truth = f"i{meta['true_pos']+1:02d}"
        q = {"instructions": "Which revision is marked (current) in the ledger?",
             "criteria": crit}

    elif kind == "T3_claim_select":
        claims = [f"the {label} is {true_val} {unit}"] + \
                 [f"the {label} is {a} {unit}" for a in alts]
        # render in the same style as the decisive line
        crit = {}
        for i, c in enumerate(claims):
            crit[f"i{i+1:02d}"] = c
        truth = next(k for k, v in crit.items() if v == f"the {label} is {true_val} {unit}")
        q = {"instructions": "Which statement matches the ledger line marked (current)?",
             "criteria": crit}

    elif kind == "T4_attribute_select":
        crit = {f"i{i+1:02d}": a for i, (a, _) in enumerate(ATTRIBUTES)}
        truth = "i01"  # attribute options are decorative here; see note in summary
        q = {"instructions": "Which location is recorded on the ledger line marked "
                             "(current)?", "criteria": crit}

    else:  # T5_boolean
        # A noul's criteria are a BOUNDARY naming what true and false mean, not a map
        # of alternatives; the sidecar rejects opaque keys here with
        # "a noul's `criteria` keys ('i01','i02') name no outcome". So this is the one
        # template whose keys are legitimately not opaque.
        crit = {"true": "the state records this value as current",
                "false": "the state does not record this value as current"}
        truth = "true"
        q = {"instructions": f"Does the state record {true_val} {unit} as the current "
                             f"{label}?", "criteria": crit}

    return {"kind": kind, "spans": spans, "decisive": decisive, "meta": meta,
            "question": q, "truth": truth, "label": label, "unit": unit,
            "true_val": true_val, "decisive_text": decisive_text}


def render(spans: list[dict], drop: str | None = None) -> str:
    keep = [s for s in spans if s["span_id"] != drop]
    head = f"DROPPED: {len(spans) - len(keep)}"
    return head + "\n" + "\n".join(f"[{s['span_id']}] {s['text']}" for s in keep)


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    rng = random.Random(20260922)
    kinds = ["T1_figure_select", "T2_version_select", "T3_claim_select",
             "T4_attribute_select", "T5_boolean"]
    rows: list[dict] = []

    for kind in kinds:
        for label, val, unit in TOPICS[:4]:
            it = make_template(kind, label, unit, val, rng)
            q = {"q": {"type": "choice" if kind != "T5_boolean" else "noul",
                       "instructions": it["question"]["instructions"],
                       "criteria": it["question"]["criteria"]}}
            full = render(it["spans"])
            # withheld arm: drop the decisive carrier line
            withheld = render(it["spans"], drop=it["decisive"])

            def call(state: str) -> dict:
                a = client.ask(state, q)["answers"]["q"]
                if kind == "T5_boolean":
                    # noul -> P(true); correct means P(true) >= 0.5 (R12 T-1:
                    # record `noul`, never `probability`)
                    p = float(a["noul"])
                    return {"correct": p >= 0.5, "p": p, "chosen": a.get("answer")}
                probs = a.get("probabilities") or {}
                return {"correct": a.get("choice") == it["truth"],
                        "p": probs.get(it["truth"]), "chosen": a.get("choice")}

            w = call(full)
            wo = call(withheld)
            rows.append({"kind": kind, "label": label, "n_options": len(q["q"]["criteria"]),
                         "with_correct": w["correct"], "with_p": w["p"],
                         "without_correct": wo["correct"], "without_p": wo["p"],
                         "state_tokens": client.count_tokens(full)})
        # end topics
    # end kinds

    by_kind: dict = {}
    for kind in kinds:
        sub = [r for r in rows if r["kind"] == kind]
        n = len(sub)
        by_kind[kind] = {
            "n": n,
            "with_carrier_accuracy": sum(1 for r in sub if r["with_correct"]) / n,
            "without_carrier_accuracy": sum(1 for r in sub if r["without_correct"]) / n,
            "n_options": sub[0]["n_options"],
            "mean_state_tokens": sum(r["state_tokens"] for r in sub) / n,
        }
    best = max(by_kind.items(), key=lambda kv: kv[1]["with_carrier_accuracy"])
    summary = {
        "by_template": by_kind,
        "best_template": best[0],
        "best_with_carrier_accuracy": best[1]["with_carrier_accuracy"],
        "selection_rule": "adopt the highest carrier-present accuracy template, "
                          "provided its withheld-carrier arm does not also score well",
        "verdict": None,
        "chance_rate_5_options": 0.2,
        "instrument": instrument_record(),
        "caveat": ("PROBE: 4 topics per template, single seed. n=4 per cell means one "
                   "hit is 0.25, so these are ordering signals, not accuracy estimates. "
                   "T4's option set is decorative (its truth is fixed at i01) and is "
                   "reported for completeness only."),
    }
    if best[1]["with_carrier_accuracy"] >= 0.80 and best[1]["without_carrier_accuracy"] <= 0.25:
        summary["verdict"] = f"VIABLE: {best[0]} is answerable and carrier-required"
    elif best[1]["with_carrier_accuracy"] >= 0.80:
        summary["verdict"] = (f"ANSWERABLE BUT NOT CARRIER-REQUIRED: {best[0]} scores "
                              f"well without the decisive line, so it would be INERT")
    else:
        summary["verdict"] = ("NO VIABLE TEMPLATE at probe scale: every template stays "
                              "near chance even with the answer in view, so an ML "
                              "classifier target in this family needs a different "
                              "construction before a horizon claim can rest on it")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P5b-classifier-templates.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print("\n=== per-row ===")
    for r in out["rows"]:
        print(f"{r['kind']:<20}{r['label'][:28]:<30}n={r['n_options']} "
              f"with={str(r['with_correct']):<5} p={r['with_p']}  without={r['without_correct']}")
    print(f"\nwritten: {p}")
