"""Does an explicit authority marker do the work, or can the judge integrate?

THE DIAGNOSIS THIS TESTS
------------------------
P5b found that the only promising classifier template still scored 0.75 when the
decisive line was DELETED, and concluded the likely cause was that a literal
`(current)` token let the judge pattern-match instead of integrate. That conclusion
rested on n=4 per cell, where one hit is 0.25 -- far too little to act on.

This probe settles it at usable scale by crossing two factors on identical items:

    MARKER    explicit   the decisive line is tagged " (current)"
              implicit   nothing is tagged; the decisive line is identifiable only
                         because it is the LATEST revision, and the question asks for
                         the latest one. The judge must use the ordering/recency
                         relation rather than a lexical tag.

    PRESENCE  full       all ledger lines present
              withheld   the decisive line is DELETED

The four cells separate the two hypotheses cleanly:
  * If the marker did the work, accuracy in (implicit, full) collapses toward chance
    while (explicit, full) stays high.
  * A template is only usable for the study if (full) is high AND (withheld) is low in
    the SAME marker condition. High (withheld) means the item is INERT: it is not
    carrier-required, so under D2 it would contribute nothing to a horizon claim.

PRE-DECLARED ACCEPTANCE RULE (fixed before running, so the result cannot be spun):
  A template is ADOPTED iff, in at least one marker condition,
      accuracy(full) >= 0.80  AND  accuracy(withheld) <= 0.40.
  Otherwise the family is rejected for the main battery and the horizon component
  falls back to D2's descriptive branch.

PROBE SIZE: 5 topics x 2 markers x 2 presence = 20 calls, versus 4 items/cell before.
Still a probe, and reported as one, but large enough that a 0.25-vs-0.75 difference is
no longer one observation.
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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402


RESULTS.mkdir(parents=True, exist_ok=True)

# Distinct figures per unit so options are semantically separable (P5's first failure
# was near-identical numerics 4182/4219/4220/4221).
CASES = [
    ("pallets shipped in Q3", "units", [4182, 3900, 5240, 2870, 6105]),
    ("authentication outage duration", "minutes", [47, 74, 12, 240, 95]),
    ("invoice INV-4471 amount", "USD", [18400, 14800, 1840, 184000, 41000]),
    ("late deliveries in March", "parcels", [312, 132, 521, 231, 465]),
    ("warranty battery replacements", "cells", [918, 198, 890, 1200, 405]),
]

# Fixed carrier width across all items: the drawn line stays in the same position so
# that only the marker/implicit cue varies.
_W = 5


def build(label: str, unit: str, figs: list[int], marker: str) -> dict:
    true_val = figs[0]
    vals = figs[:_W]
    # deterministic reordering so the decisive line is not always first
    order = [2, 0, 4, 1, 3]
    vals = [vals[i] for i in order]
    true_pos = vals.index(true_val)
    spans = [
        {"span_id": "s1", "kind": "preamble",
         "text": "Audit memo. The ledger lists successive revisions; later lines "
                 "supersede earlier ones."},
    ]
    for i, v in enumerate(vals):
        tag = " (current)" if (marker == "explicit" and i == true_pos) else ""
        spans.append({"span_id": f"c{i+1}", "kind": "carrier",
                      "text": f"revision {i+1}: {label} = {v} {unit}{tag}"})
    spans.append({"span_id": "s2", "kind": "instruction",
                  "text": "Answer using the revisions above."})

    key = f"c{true_pos+1}"
    cands = list(vals)
    crit = {f"i{i+1:02d}": f"{v} {unit}" for i, v in enumerate(cands)}
    truth = f"i{cands.index(true_val)+1:02d}"
    instr = (f"What is the current {label}?" if marker == "explicit"
             else f"What is the latest recorded {label}?")
    return {"spans": spans, "decisive": key, "criteria": crit, "truth": truth,
            "instruction": instr, "true_val": true_val, "true_pos": true_pos}


def render(spans: list[dict], drop: str | None = None) -> str:
    keep = [s for s in spans if s["span_id"] != drop]
    return (f"DROPPED: {len(spans) - len(keep)}\n"
            + "\n".join(f"[{s['span_id']}] {s['text']}" for s in keep))


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    q_cache: dict[str, dict] = {}
    rows: list[dict] = []

    for marker in ("explicit", "implicit"):
        for label, unit, figs in CASES:
            it = build(label, unit, figs, marker)
            q = {"q": {"type": "choice", "instructions": it["instruction"],
                       "criteria": it["criteria"]}}
            for presence, drop in (("full", None), ("withheld", it["decisive"])):
                state = render(it["spans"], drop=drop)
                try:
                    a = client.ask(state, q)["answers"]["q"]
                    probs = a.get("probabilities") or {}
                    rec = {"marker": marker, "presence": presence, "label": label,
                           "chosen": a.get("choice"),
                           "correct": a.get("choice") == it["truth"],
                           "p_truth": probs.get(it["truth"]),
                           "returned_type": a.get("type"),
                           "state_tokens": client.count_tokens(state)}
                except Exception as exc:
                    rec = {"marker": marker, "presence": presence, "label": label,
                           "error": str(exc)[:200]}
                rows.append(rec)
                print(f"{marker:<9} {presence:<9} {label[:30]:<32} "
                      f"correct={rec.get('correct')} p={rec.get('p_truth')}")

    cells: dict = {}
    for marker in ("explicit", "implicit"):
        for presence in ("full", "withheld"):
            sub = [r for r in rows if r["marker"] == marker
                   and r["presence"] == presence and "error" not in r]
            if sub:
                cells[f"{marker}/{presence}"] = {
                    "n": len(sub),
                    "accuracy": sum(1 for r in sub if r["correct"]) / len(sub),
                    "mean_p_truth": sum(r["p_truth"] or 0 for r in sub) / len(sub),
                }

    adopted = []
    for marker in ("explicit", "implicit"):
        f = cells.get(f"{marker}/full", {}).get("accuracy")
        w = cells.get(f"{marker}/withheld", {}).get("accuracy")
        if f is not None and w is not None and f >= 0.80 and w <= 0.40:
            adopted.append(marker)

    summary = {
        "cells": cells,
        "chance_rate": 0.2,
        "acceptance_rule": "adopt iff accuracy(full) >= 0.80 AND accuracy(withheld) <= 0.40",
        "adopted_marker_conditions": adopted,
        "verdict": None,
        "instrument": instrument_record(),
        "caveat": ("PROBE: 5 topics per cell. n=5 means a single call is 0.20, so cell "
                   "accuracies move in steps of 0.2 and no cell estimate is precise. "
                   "Purpose is to separate a lexical-tag explanation from an "
                   "integration explanation, not to estimate study accuracy."),
    }
    ef = cells.get("explicit/full", {}).get("accuracy")
    if_ = cells.get("implicit/full", {}).get("accuracy")
    ew = cells.get("explicit/withheld", {}).get("accuracy")
    iw = cells.get("implicit/withheld", {}).get("accuracy")
    if None not in (ef, if_):
        if ef is not None and if_ is not None and ef - if_ >= 0.40:
            summary["verdict"] = ("MARKER-DEPENDENT: removing the lexical tag collapses "
                                  "accuracy, so the earlier high scores were tag-matching, "
                                  "not evidence integration")
        elif adopted:
            summary["verdict"] = (f"USABLE: {adopted[0]} marker condition satisfies both "
                                  f"the derivability and necessity bars")
        else:
            summary["verdict"] = ("NEITHER CONDITION USABLE: full-arm accuracy is not "
                                  "high enough and/or the withheld arm is not low enough")
        summary["marker_effect_on_full"] = (ef - if_) if (ef is not None and if_ is not None) else None
        summary["necessity_gap_explicit"] = (ef - ew) if (ef is not None and ew is not None) else None
        summary["necessity_gap_implicit"] = (if_ - iw) if (if_ is not None and iw is not None) else None
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P5c-marker-vs-integration.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
