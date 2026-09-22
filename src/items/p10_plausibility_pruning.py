"""PRE-WORK ITEM 15: is "plausibility pruning" the real mechanism? A PAIRED test.

THE CLAIM UNDER TEST
--------------------
Comparing P9 (clustered figures, accuracy 1.00, n=16) with P9b (magnitude-separated
figures, accuracy 0.458, n=48) suggested that NEAR-IDENTICAL option values give the
judge a shortcut: implausible candidates can be eliminated by plausibility reasoning
without ever locating the authoritative line. Making the options mutually plausible
removed that shortcut and the measured accuracy fell.

That comparison is NOT controlled: the two runs differ in topic count, wording and item
set as well as in figure spread, so the mechanism is inferred rather than demonstrated.
This script turns it into a paired within-item experiment.

DESIGN (each item is its own control)
  Same topic, same state, same question, same true value, same option COUNT.
  Only the DISTRACTOR VALUES change:

    PRUNABLE   distractors sit at magnitudes that are obviously wrong for the quantity
               (e.g. "invoice amount = 5082 USD" when the ledger's other lines and the
               quantity type make that absurd)
    PLAUSIBLE  distractors are all close to the true value, so every option is equally
               believable and only the authoritative line can decide

  Paired comparison across the SAME items removes between-item variance entirely, which
  is exactly what the earlier uncontrolled comparison could not do. Reported as a paired
  difference with a discordance breakdown (b = prunable-only correct, c = plausible-only
  correct) and an exact McNemar test.

PRE-DECLARED READING
  If PRUNABLE >> PLAUSIBLE on paired items, the pruning mechanism is demonstrated and
  the paper must report option-plausibility structure alongside every accuracy figure.
  If they are equal, the earlier difference was an artefact of the uncontrolled sets and
  the mechanism claim is withdrawn.
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

TOPICS = [
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
]


def make_set(value: int, kind: str, rng: random.Random, k: int = 5) -> list[int]:
    """k values including the truth, in one of two plausibility regimes."""
    if kind == "prunable":
        # magnitudes obviously inconsistent with the neighbouring revisions
        cands = [value * 40, max(1, value // 30), value * 220, max(2, value // 12)]
    else:  # plausible
        # all within a narrow band, so no candidate can be dismissed on its face
        deltas = [3, 7, 11, 19]
        cands = [value + d for d in deltas]
    rng.shuffle(cands)
    return [value] + cands[: k - 1]


def build(idx: int, kind: str, rng: random.Random) -> dict:
    label, unit, value = TOPICS[idx]
    figs = make_set(value, kind, rng)
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
    rng.shuffle(pairs)
    truth_key = next(k for k, v in pairs if v == f"{value} {unit}")
    spread = (max(figs) - min(figs)) / max(1, value)
    return {"spans": spans, "criteria": dict(pairs), "truth": truth_key,
            "values": sorted(figs), "relative_spread": round(spread, 3),
            "instruction": f"What is the current {label}? Choose the figure marked "
                           f"(current)."}


def render(spans: list[dict]) -> str:
    return (f"DROPPED: 0\n"
            + "\n".join(f"[{s['span_id']}] {s['text']}" for s in spans))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value."""
    from math import comb
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    rows: list[dict] = []
    for idx in range(len(TOPICS)):
        rec: dict = {"topic": TOPICS[idx][0]}
        for kind in ("prunable", "plausible"):
            rng = random.Random(f"20260922:{idx}:{kind}")
            it = build(idx, kind, rng)
            try:
                a = client.ask(render(it["spans"]), {"q": {
                    "type": "choice", "instructions": it["instruction"],
                    "criteria": it["criteria"]}})["answers"]["q"]
                probs = a.get("probabilities") or {}
                rec[f"{kind}_correct"] = a.get("choice") == it["truth"]
                rec[f"{kind}_p_truth"] = probs.get(it["truth"])
                rec[f"{kind}_spread"] = it["relative_spread"]
            except Exception as exc:
                rec[f"{kind}_error"] = str(exc)[:160]
        rows.append(rec)
        print(f"{rec['topic'][:34]:<36} prunable={rec.get('prunable_correct')!s:<5} "
              f"plausible={rec.get('plausible_correct')}")

    ok = [r for r in rows if "prunable_correct" in r and "plausible_correct" in r]
    n = len(ok)
    p_acc = sum(1 for r in ok if r["prunable_correct"]) / n if n else None
    q_acc = sum(1 for r in ok if r["plausible_correct"]) / n if n else None
    b = sum(1 for r in ok if r["prunable_correct"] and not r["plausible_correct"])
    c = sum(1 for r in ok if r["plausible_correct"] and not r["prunable_correct"])
    both = sum(1 for r in ok if r["prunable_correct"] and r["plausible_correct"])
    neither = n - b - c - both
    summary = {
        "n_paired_items": n,
        "prunable_accuracy": p_acc,
        "plausible_accuracy": q_acc,
        "paired_difference": (p_acc - q_acc) if (p_acc is not None and q_acc is not None) else None,
        "discordance": {"prunable_only_correct_b": b, "plausible_only_correct_c": c,
                        "both_correct": both, "neither_correct": neither},
        "mcnemar_exact_p": mcnemar_exact(b, c) if n else None,
        "mean_relative_spread": {
            "prunable": sum(r["prunable_spread"] for r in ok) / n if n else None,
            "plausible": sum(r["plausible_spread"] for r in ok) / n if n else None,
        },
        "instrument": instrument_record(),
        "caveat": (f"PROBE: {n} paired items, single seed. Paired design removes "
                   f"between-item variance, but n={n} means the exact McNemar test has "
                   f"low power; a large difference is interpretable, a small one is not."),
        "verdict": None,
    }
    if p_acc is not None and q_acc is not None:
        if p_acc - q_acc >= 0.25:
            summary["verdict"] = ("PRUNING MECHANISM DEMONSTRATED: paired items score far "
                                  "higher when distractors are implausible, so option-set "
                                  "plausibility must be reported with every accuracy figure")
        elif abs(p_acc - q_acc) <= 0.10:
            summary["verdict"] = ("MECHANISM NOT SUPPORTED: prunable and plausible option "
                                  "sets score comparably on paired items, so the earlier "
                                  "P9-vs-P9b gap was an artefact of the uncontrolled sets")
        else:
            summary["verdict"] = "INCONCLUSIVE at this n: difference present but modest"
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P10-plausibility-pruning-paired.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
