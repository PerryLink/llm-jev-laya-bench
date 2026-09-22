"""Certificate verification: prove empirically that the carrier is REQUIRED.

THE GAP THIS CLOSES
-------------------
`pipeline.py` attaches a certificate to every item declaring that the decisive figure
lives only in a carrier line, so the item is unanswerable without it. That is a
DECLARATION. V4's audit found the same class of claim ("the judge could have recovered
the planted error") unsupported in the original design, and named it the threat it
could not solve. A declaration is not a certificate; this script makes it one.

TWO CHECKS PER LEVEL
--------------------
  carrier present  -> the judge must answer CORRECTLY. If it cannot answer when the
                      decisive line is in plain view, the item is broken, not the
                      judge: that is the DERIVABILITY check.
  carrier withheld -> the judge must NOT answer correctly (it can only pick a decoy,
                      or land on one by chance). This is the NECESSITY check, and it
                      is what certifies `carrier_required=True`.

An item where the withheld-carrier arm still answers correctly is NOT carrier-required:
it is inert, its answer does not depend on horizon, and under D2 it would contribute
nothing while consuming a slot. Such items are reported and excluded.

Because a 5-option choice can be right by chance, one item per level is far too few to
certify anything: the expected chance hit rate is 0.20. This runs every generated item
in both arms, so a level's certification rests on `n_per_level` observations rather
than one, and reports the chance-corrected picture alongside the raw counts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from laya_client import LayaClient, instrument_record  # noqa: E402
from pipeline import Item, generate  # noqa: E402

RESULTS = Path(r"D:\Projects\llm-jev-laya-bench\results")
RESULTS.mkdir(parents=True, exist_ok=True)


def ask_item(client: LayaClient, item: Item, include_carrier: bool) -> dict:
    state = item.render_state(include_carrier=include_carrier)
    q = {"q": {"type": item.primitive,
               "instructions": item.question["instructions"],
               "criteria": item.question["criteria"]}}
    resp = client.ask(state, q)
    ans = resp["answers"]["q"]
    probs = ans.get("probabilities") or {}
    return {
        "chosen": ans.get("choice"),
        "correct": ans.get("choice") == item.ground_truth,
        "p_truth": probs.get(item.ground_truth),
        "truncated": bool(resp.get("truncated")),
        "state_tokens": client.count_tokens(state),
    }


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    items = generate(n_per_level=4)
    rows: list[dict] = []
    for it in items:
        with_c = ask_item(client, it, include_carrier=True)
        without_c = ask_item(client, it, include_carrier=False)
        rows.append({
            "item_id": it.item_id, "level": it.level,
            "true_pos": it.meta["true_pos"],
            "with_carrier_correct": with_c["correct"],
            "with_carrier_p_truth": with_c["p_truth"],
            "without_carrier_correct": without_c["correct"],
            "without_carrier_p_truth": without_c["p_truth"],
            "state_tokens": without_c["state_tokens"],
            "any_truncated": with_c["truncated"] or without_c["truncated"],
        })
        print(f"{it.item_id:<14} L{it.level:<4} pos={it.meta['true_pos']}  "
              f"with={str(with_c['correct']):<5} p={with_c['p_truth']}  "
              f"without={str(without_c['correct']):<5} p={without_c['p_truth']}")

    by_level: dict = {}
    for lvl in sorted({r["level"] for r in rows}):
        sub = [r for r in rows if r["level"] == lvl]
        n = len(sub)
        w = sum(1 for r in sub if r["with_carrier_correct"])
        wo = sum(1 for r in sub if r["without_carrier_correct"])
        by_level[lvl] = {
            "n": n,
            "with_carrier_correct": w,
            "without_carrier_correct": wo,
            "derivable": w > 0,
            "carrier_required_verified": wo == 0,
            # chance of a correct pick by luck on a 5-option question
            "chance_hits_expected": round(0.2 * n, 2),
        }

    n_total = len(rows)
    w_total = sum(1 for r in rows if r["with_carrier_correct"])
    wo_total = sum(1 for r in rows if r["without_carrier_correct"])
    summary = {
        "n_items": n_total,
        "with_carrier_accuracy": w_total / n_total if n_total else None,
        "without_carrier_accuracy": wo_total / n_total if n_total else None,
        "chance_rate": 0.2,
        "certified_live_items": sum(1 for r in rows if not r["without_carrier_correct"]),
        "certified_live_fraction": (
            sum(1 for r in rows if not r["without_carrier_correct"]) / n_total
            if n_total else None),
        "by_level": by_level,
        "verdict": None,
        "instrument": instrument_record(),
        "caveat": ("PROBE SCALE: 4 items per level, 5 options, so one chance hit per "
                   "level is 0.2 expected. A level with 4/4 withheld-carrier failures "
                   "is consistent with true necessity; a level with any withheld-carrier "
                   "hit at this n weakens that item's certificate, not the design."),
    }
    if summary["with_carrier_accuracy"] is not None:
        if summary["with_carrier_accuracy"] >= 0.75 and wo_total == 0:
            summary["verdict"] = ("CERTIFICATES VERIFIED at probe scale: items are "
                                  "derivable with the carrier and unanswerable without it")
        elif summary["with_carrier_accuracy"] < 0.5:
            summary["verdict"] = ("ITEMS NOT DERIVABLE: the judge fails even with the "
                                  "decisive line in view, so the family needs redesign "
                                  "before it can carry a horizon claim")
        else:
            summary["verdict"] = ("MIXED: see per-level detail; some items may be inert "
                                  "or the task may be harder than authored")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P5-certificate-verification.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
