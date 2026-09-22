"""PRE-WORK ITEM 6 (DECISIONS.md, created by the P1 result): can a MULTI-LEVEL
hierarchical choice recover high-cardinality classification that a single flat
choice cannot?

WHY THIS EXISTS
---------------
P1 measured that a flat `choice` collapses above ~15 options: accuracy 0.33 at N=15,
0.00 at N>=20, with AUC decaying to ~0.47 (chance), i.e. the ORDERING information is
lost, not merely the argmax. That directly threatens the two largest adopted dataset
families (D3): MASSIVE (60 intents) and CLINC150 (150 intents), whose single-level use
would land squarely inside the measured failure region.

A sharding design was therefore proposed: choose among <=10 coarse groups, then among
<=10 fine labels inside the chosen group. But two things about that design are
unverified, and this probe tests both:

  Q1. Does per-layer accuracy actually hold at <=10 options on this task?
      P1 suggests yes (0.67-1.00 at N<=10) but that was a single-choice relevance task,
      not a taxonomy, and one datapoint per cell.
  Q2. HOW DOES ERROR COMPOUND ACROSS LAYERS? A two-level design with 0.90 per layer
      yields 0.81 end-to-end; three levels yields 0.73. If per-layer accuracy is only
      ~0.7 the hierarchy is WORSE than a flat choice would be at the same cardinality.
      This is the quantity a design decision actually turns on, and it is measurable.

MEASURED, per item:
  * coarse accuracy            -- top level, G groups
  * fine-given-correct-coarse  -- second level, conditional, i.e. the layer's own skill
  * END-TO-END accuracy        -- the composition a deployment would experience
  * flat accuracy              -- single-level choice over ALL fine labels, for contrast

GROUND TRUTH BY CONSTRUCTION
----------------------------
Each ticket names exactly one artefact and one requested action, so the correct coarse
group and the correct fine intent follow from the text deterministically. Labels are
authored, not produced by any model. This is a PROBE (small N), not the study battery.
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402


RESULTS.mkdir(parents=True, exist_ok=True)

# A 6-group taxonomy with 3-4 fine intents each = 20 fine labels.
# This mirrors MASSIVE's shape (60 intents) at reduced scale while keeping every
# layer inside the <=10-option regime that P1 found usable.
TAXONOMY: dict[str, dict[str, str]] = {
    "money": {
        "refund_request": "the customer asks for money back for a charge",
        "billing_dispute": "the customer disputes the amount of a charge",
        "price_question": "the customer asks what something costs",
        "payment_failed": "the customer reports a payment that did not go through",
    },
    "access": {
        "password_reset": "the customer cannot log in and needs credentials reset",
        "account_locked": "the customer's account has been locked out",
        "permissions_request": "the customer asks for access to a resource they cannot reach",
        "two_factor_problem": "the customer cannot complete two-factor authentication",
    },
    "hardware": {
        "device_not_powering_on": "the customer's device will not turn on",
        "battery_drain": "the customer reports the battery draining unusually fast",
        "screen_damage": "the customer reports a cracked or broken screen",
    },
    "software": {
        "app_crash": "the application closes unexpectedly",
        "sync_failure": "data the customer saved did not synchronise",
        "update_problem": "an update failed or broke something",
        "feature_request": "the customer asks for a capability that does not exist yet",
    },
    "shipping": {
        "delivery_late": "a shipment has not arrived when promised",
        "delivery_damaged": "a shipment arrived damaged",
        "wrong_item_received": "the customer received something they did not order",
    },
    "account": {
        "cancel_subscription": "the customer wants to end their subscription",
        "change_contact_details": "the customer wants to update their email or phone",
        "data_deletion_request": "the customer wants their personal data erased",
    },
}

# (ticket text, expected coarse group, expected fine intent)
ITEMS: list[tuple[str, str, str]] = [
    ("I was charged twice for the same order last month and I want the extra one refunded.",
     "money", "refund_request"),
    ("Your invoice says 49 dollars but my plan is listed as 29 dollars on your own pricing page.",
     "money", "billing_dispute"),
    ("How much does the business tier cost per seat if we buy twenty of them?",
     "money", "price_question"),
    ("My card keeps getting declined at checkout even though there is money in the account.",
     "money", "payment_failed"),
    ("I have forgotten my login details and the reset email never arrives.",
     "access", "password_reset"),
    ("I tried my password too many times and now it says my account is locked out.",
     "access", "account_locked"),
    ("I can see the shared drive but every file in it says I do not have permission.",
     "access", "permissions_request"),
    ("The authenticator code is always rejected when I try to finish signing in.",
     "access", "two_factor_problem"),
    ("My laptop will not switch on at all, no lights, nothing happens when I hold the button.",
     "hardware", "device_not_powering_on"),
    ("The battery used to last all day and now it is flat by lunchtime with the same usage.",
     "hardware", "battery_drain"),
    ("I dropped the tablet and the glass over the display is cracked.",
     "hardware", "screen_damage"),
    ("The desktop application shuts itself down about a minute after I open it.",
     "software", "app_crash"),
    ("Notes I typed on my phone yesterday are still missing on my laptop today.",
     "software", "sync_failure"),
    ("After installing the newest version the export button stopped working entirely.",
     "software", "update_problem"),
    ("Could you add a way to export my reports as a spreadsheet? There is no option for it.",
     "software", "feature_request"),
    ("The parcel was supposed to be here on Tuesday and it is still not here on Friday.",
     "shipping", "delivery_late"),
    ("The box arrived crushed and the screen inside is shattered.",
     "shipping", "delivery_damaged"),
    ("I ordered a blue medium and the package contains a red large.",
     "shipping", "wrong_item_received"),
    ("Please stop my monthly plan, I do not want to be billed again.",
     "account", "cancel_subscription"),
    ("I have a new phone number and I need to change the one on my profile.",
     "account", "change_contact_details"),
    ("Under the privacy rules I want everything you hold about me deleted.",
     "account", "data_deletion_request"),
]

ALL_FINE = [f for g in TAXONOMY.values() for f in g]
COARSE_NAMES = {g: g for g in TAXONOMY}


def coarse_criteria() -> dict[str, str]:
    # Each group description lists its member intents, which is how a real
    # hierarchical router would present the taxonomy.
    return {
        g: ("tickets about " + "; ".join(f.replace("_", " ") for f in fine.values()))
        for g, fine in TAXONOMY.items()
    }


def run() -> dict:
    client = LayaClient()
    client.ensure_up()

    coarse_q = {
        "coarse": {
            "type": "choice",
            "instructions": "Which category best matches what this customer wants?",
            "criteria": coarse_criteria(),
        }
    }

    rows: list[dict] = []
    for text, expect_c, expect_f in ITEMS:
        state = {"subject": "customer support ticket", "body": text}
        state_tokens = client.count_tokens(json.dumps(state))
        rec: dict = {"text": text, "expect_coarse": expect_c, "expect_fine": expect_f,
                     "state_tokens": state_tokens}

        # ---- level 1: coarse group, G = 6 options
        try:
            r1 = client.ask(state, coarse_q)
            a1 = r1["answers"]["coarse"]
            rec["coarse_chosen"] = a1.get("choice")
            rec["coarse_correct"] = a1.get("choice") == expect_c
            rec["coarse_type_returned"] = a1.get("type")
        except Exception as exc:
            rec["error"] = f"coarse: {exc}"[:200]
            rows.append(rec)
            continue

        # ---- level 2a: fine, CONDITIONAL on the true coarse group (isolates the
        #      layer's own skill from level-1 errors, so compounding is separable)
        fine_true = TAXONOMY[expect_c]
        q_fine_true = {
            "fine": {
                "type": "choice",
                "instructions": "Which specific request is this ticket about?",
                "criteria": {k: v for k, v in fine_true.items()},
            }
        }
        try:
            r2 = client.ask(state, q_fine_true)
            a2 = r2["answers"]["fine"]
            rec["fine_given_correct_coarse"] = a2.get("choice") == expect_f
        except Exception as exc:
            rec["error"] = f"fine-conditional: {exc}"[:200]

        # ---- level 2b: fine, CONDITIONAL on what level 1 ACTUALLY chose (end-to-end)
        chosen_c = rec.get("coarse_chosen")
        if chosen_c in TAXONOMY:
            q_fine_chosen = {
                "fine": {
                    "type": "choice",
                    "instructions": "Which specific request is this ticket about?",
                    "criteria": {k: v for k, v in TAXONOMY[chosen_c].items()},
                }
            }
            try:
                r3 = client.ask(state, q_fine_chosen)
                a3 = r3["answers"]["fine"]
                rec["end_to_end_correct"] = (chosen_c == expect_c
                                             and a3.get("choice") == expect_f)
            except Exception as exc:
                rec["error"] = f"fine-endtoend: {exc}"[:200]

        # ---- baseline: FLAT choice over all 20 fine labels (the regime P1 says fails)
        q_flat = {
            "flat": {
                "type": "choice",
                "instructions": "Which specific request is this ticket about?",
                "criteria": {k: v for g in TAXONOMY.values() for k, v in g.items()},
            }
        }
        try:
            r4 = client.ask(state, q_flat)
            a4 = r4["answers"]["flat"]
            rec["flat_chosen"] = a4.get("choice")
            rec["flat_correct"] = a4.get("choice") == expect_f
            probs = a4.get("probabilities") or {}
            rec["flat_p_correct"] = probs.get(expect_f)
            rec["flat_top_prob"] = max(probs.values()) if probs else None
        except Exception as exc:
            rec["error"] = f"flat: {exc}"[:200]

        rows.append(rec)

    ok = [r for r in rows if "coarse_correct" in r]
    n = len(ok)
    def rate(key: str) -> float | None:
        vals = [r[key] for r in ok if key in r]
        return (sum(1 for v in vals if v) / len(vals)) if vals else None

    flat_probs = [r["flat_p_correct"] for r in ok if r.get("flat_p_correct") is not None]
    summary = {
        "n_items": n,
        "coarse_options": len(TAXONOMY),
        "fine_options_max": max(len(v) for v in TAXONOMY.values()),
        "flat_options": len(ALL_FINE),
        "coarse_accuracy": rate("coarse_correct"),
        "fine_given_correct_coarse": rate("fine_given_correct_coarse"),
        "end_to_end_accuracy": rate("end_to_end_correct"),
        "flat_accuracy": rate("flat_correct"),
        "flat_mean_p_on_correct_label": (
            sum(flat_probs) / len(flat_probs) if flat_probs else None),
        "coarse_confusion": {
            r["expect_coarse"]: r.get("coarse_chosen") for r in ok
            if not r.get("coarse_correct")
        },
    }
    # The decision this probe exists to inform:
    e2e = summary["end_to_end_accuracy"]
    flat = summary["flat_accuracy"]
    if e2e is not None and flat is not None:
        summary["hierarchy_beats_flat"] = e2e > flat
        summary["hierarchy_verdict"] = (
            "HIERARCHY VIABLE: end-to-end exceeds flat at the same label set"
            if e2e > flat else
            "HIERARCHY NOT VIABLE on this probe: compounding costs more than the "
            "high-cardinality penalty it avoids")
    summary["caveat"] = (
        "PROBE, NOT THE STUDY BATTERY. 21 authored tickets, one call per cell, single "
        "seed. Measures per-layer accuracy and how it compounds; far too small to "
        "estimate the study's accuracy, and the taxonomy is authored rather than drawn "
        "from MASSIVE/CLINC150."
    )
    summary["instrument"] = instrument_record()
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    path = RESULTS / "P6-hierarchical-sharding.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {path}")
