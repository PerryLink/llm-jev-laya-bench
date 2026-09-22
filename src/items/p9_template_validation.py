"""PRE-WORK ITEM 14: does the explicit-authority template hold up at n>=30?

WHY THIS RE-RUN EXISTS
----------------------
P5c reported accuracy 1.00 for the explicit "(current)" template. P2 then showed that
leaving options in rendered order lets a positional preference masquerade as skill, and
that P5c's configuration was exactly the one that scored 0.125 once position was
decorrelated. So P5c's 1.00 was withdrawn as a probable positional artefact.

P2's corrected single measurement was 0.625 at n=8 -- better than chance but below the
pre-declared bar of 0.80, and at n=8 one item moves the rate by 0.125. That is not a
basis for adopting or rejecting a template that the whole horizon battery would rest on.

This runs the decision properly, with every control this project has had to learn:

  * n = 32 items (16 topics x 2 arms), so one item moves a rate by 0.031
  * option order DECORRELATED from correctness, truth position recorded (P2)
  * opaque option keys, descriptive text only in the value (P6)
  * BOTH arms: carrier present, and the decisive revision withheld (the necessity test)
  * a marker contrast on identical items: explicit "(current)" tag vs no tag (P5c)
  * admission by our own tokenizer count, never Laya's wrong-in-both-directions flag (P3)

PRE-DECLARED ACCEPTANCE RULE (fixed before running)
----------------------------------------------------
  ADOPT iff, in some marker condition,
      accuracy(full) >= 0.80   AND   accuracy(withheld) <= 0.40
  With n=32 in each arm, a 0.80 full-arm rate has a 95% Wilson interval of roughly
  [0.63, 0.90], so this is a screening decision, not a precision estimate, and the
  report says so.

The four cells also settle the marker question: if removing the lexical tag collapses
accuracy, the earlier high scores came from tag-matching rather than evidence
integration, which is a finding about the judge, not merely about the template.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

# 16 topics with 5 semantically distinct figures each (P5's first failure was a numeric
# option set differing by 1-40 units, which carries almost no distinguishing signal).
TOPICS: list[tuple[str, str, int]] = [
    ("pallets shipped in Q3", "units", 4182),
    ("authentication outage duration", "minutes", 47),
    ("invoice INV-4471 amount", "USD", 18400),
    ("late deliveries in March", "parcels", 312),
    ("warranty battery replacements", "cells", 918),
    ("median ticket resolution time", "hours", 26),
    ("customer churn in Q2", "accounts", 384),
    ("warehouse overtime hours", "hours", 1140),
    ("refund requests in April", "tickets", 207),
    ("distinct cards blocked", "cards", 63),
    ("chargebacks filed", "disputes", 129),
    ("average call handling time", "seconds", 214),
    ("new merchant signups", "merchants", 1520),
    ("failed settlement attempts", "attempts", 76),
    ("manual review escalations", "cases", 455),
    ("duplicate charge reports", "reports", 1188),
]

_SPREAD = [0, 900, -1100, 2500, 770]      # distinct magnitudes, applied to a base


def build(idx: int, marker: str, rng: random.Random) -> dict:
    label, unit, value = TOPICS[idx]
    figs = [value + d for d in _SPREAD]
    rng.shuffle(figs)
    true_pos = figs.index(value)

    spans = [{"span_id": "s1", "kind": "preamble",
              "text": "Audit memo. The ledger lists successive revisions; later lines "
                      "supersede earlier ones."}]
    for i, v in enumerate(figs):
        tag = " (current)" if (marker == "explicit" and i == true_pos) else ""
        spans.append({"span_id": f"c{i+1}", "kind": "carrier",
                      "text": f"revision {i+1}: {label} = {v} {unit}{tag}"})
    spans.append({"span_id": "s2", "kind": "instruction",
                  "text": "Answer using the revisions above."})
    decisive = f"c{true_pos+1}"

    # opaque keys; option order decorrelated per item (P2 control)
    pairs = list(zip([f"k{i+1:02d}" for i in range(len(figs))],
                     [f"{v} {unit}" for v in figs]))
    rng.shuffle(pairs)
    truth_key = next(k for k, v in pairs if v == f"{value} {unit}")
    instr = (f"What is the current {label}? Choose the figure marked (current)."
             if marker == "explicit" else f"What is the latest recorded {label}?")
    return {"spans": spans, "decisive": decisive, "criteria": dict(pairs),
            "truth": truth_key, "instruction": instr, "label": label,
            "truth_pos_in_criteria": [k for k, _ in pairs].index(truth_key)}


def render(spans: list[dict], drop: str | None = None) -> str:
    keep = [s for s in spans if s["span_id"] != drop]
    return (f"DROPPED: {len(spans) - len(keep)}\n"
            + "\n".join(f"[{s['span_id']}] {s['text']}" for s in keep))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - h) / d, (c + h) / d)


def run(seed: int = 20260922) -> dict:
    client = LayaClient()
    client.ensure_up()
    rows: list[dict] = []
    for marker in ("explicit", "implicit"):
        for idx in range(len(TOPICS)):
            rng = random.Random(f"{seed}:{marker}:{idx}")
            it = build(idx, marker, rng)
            q = {"q": {"type": "choice", "instructions": it["instruction"],
                       "criteria": it["criteria"]}}
            for presence, drop in (("full", None), ("withheld", it["decisive"])):
                state = render(it["spans"], drop=drop)
                toks = client.count_tokens(state)
                try:
                    resp = client.ask(state, q)
                    a = resp["answers"]["q"]
                    probs = a.get("probabilities") or {}
                    rec = {"marker": marker, "presence": presence, "topic": it["label"],
                           "correct": a.get("choice") == it["truth"],
                           "p_truth": probs.get(it["truth"]),
                           "confidence": a.get("confidence"),
                           "type_ok": a.get("type") == "choice",
                           "state_tokens": toks,
                           "truncated_flag": bool(resp.get("truncated"))}
                except Exception as exc:
                    rec = {"marker": marker, "presence": presence, "topic": it["label"],
                           "error": str(exc)[:200]}
                rows.append(rec)

    cells: dict = {}
    for marker in ("explicit", "implicit"):
        for presence in ("full", "withheld"):
            sub = [r for r in rows if r["marker"] == marker
                   and r["presence"] == presence and "error" not in r]
            if not sub:
                continue
            k = sum(1 for r in sub if r["correct"])
            lo, hi = wilson(k, len(sub))
            cells[f"{marker}/{presence}"] = {
                "n": len(sub), "correct": k,
                "accuracy": k / len(sub),
                "wilson95": [round(lo, 4), round(hi, 4)],
                "mean_p_truth": sum((r["p_truth"] or 0) for r in sub) / len(sub),
                "mean_confidence": sum((r["confidence"] or 0) for r in sub) / len(sub),
            }

    adopted = [m for m in ("explicit", "implicit")
               if cells.get(f"{m}/full", {}).get("accuracy", -1) >= 0.80
               and cells.get(f"{m}/withheld", {}).get("accuracy", 1) <= 0.40]

    ef = cells.get("explicit/full", {}).get("accuracy")
    inf = cells.get("implicit/full", {}).get("accuracy")
    summary = {
        "n_items_per_cell": len(TOPICS),
        "cells": cells,
        "chance_rate": 0.2,
        "acceptance_rule": "adopt iff accuracy(full) >= 0.80 AND accuracy(withheld) <= 0.40",
        "adopted_conditions": adopted,
        "marker_effect_on_full": (ef - inf) if (ef is not None and inf is not None) else None,
        "controls": {
            "option_order": "decorrelated per item; truth position recorded",
            "option_keys": "opaque k01-style; descriptive text only in the value",
            "admission": "own tokenizer count; Laya's truncated flag recorded only",
            "arms": "carrier present vs decisive revision withheld",
        },
        "instrument": instrument_record(),
        "caveat": ("SCREENING DECISION at n=32 per cell (95% Wilson half-width roughly "
                   "0.13 at p=0.80). Adopts or rejects a template; does not estimate the "
                   "study's accuracy."),
    }
    if adopted:
        summary["verdict"] = f"ADOPT {adopted[0]}: clears both bars at n=32"
    elif cell_max := max((c["accuracy"] for c in cells.values()), default=0):
        summary["verdict"] = ("NOT ADOPTED at n=32: no marker condition clears both the "
                              "derivability and necessity bars")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P9-template-validation-n32.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
