"""PRE-WORK ITEM 6, v2 — hierarchical sharding WITHOUT the label-name shortcut.

WHY A v2 EXISTS (a confound found in v1)
---------------------------------------
v1 measured: coarse 0.762, fine-given-correct-coarse 1.000, end-to-end 0.762,
flat 0.905 -> "hierarchy not viable". But v1's flat arm was given criteria whose KEYS
were the intent names (`refund_request`, `battery_drain`, ...) AND whose coarse group
description listed those same intent names. So the flat arm carried a free grouping
cue that the real datasets do not have:

  * MASSIVE ships intent names like `alarm_set` / `alarm_remove`, not
    `refund_request`;
  * CLINC150 ships 150 short intent names, likewise not self-describing a taxonomy.

Reporting v1's flat=0.905 as a fair baseline would have been wrong. This v2 removes the
cue by using OPAQUE keys (i1..i22) for BOTH arms while keeping the semantic
descriptions byte-identical. Both arms then see the same information; only the
DECOMPOSITION differs.

WHAT CHANGED BETWEEN v1 AND v2, EXACTLY
  * criteria keys: descriptive intent names  ->  opaque `i<n>` codes
  * criteria values: unchanged (byte-identical descriptions)
  * coarse group descriptions: previously listed member intent names; now describe the
    group semantically without naming members, because naming members would reintroduce
    the cue through the coarse arm instead.

Everything else (items, order, call structure, taxonomy shape) is identical, so a v1/v2
difference is attributable to the label-naming cue alone.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, instrument_record  # noqa: E402

RESULTS = Path(r"D:\Projects\llm-jev-laya-bench\results")
RESULTS.mkdir(parents=True, exist_ok=True)

# Same 6-group taxonomy as v1, same descriptions, but keys become opaque codes.
_TAXONOMY_NAMED: dict[str, dict[str, str]] = {
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

# Group descriptions that do NOT enumerate member intent names.
GROUP_DESC = {
    "money": "tickets about charges, prices, payments and money owed",
    "access": "tickets about signing in, credentials and permission to reach something",
    "hardware": "tickets about a physical device being broken or failing",
    "software": "tickets about the application, its data or its updates misbehaving",
    "shipping": "tickets about parcels being late, damaged or wrong",
    "account": "tickets about the customer's own profile, plan or personal data",
}

# Opaque codes: stable, order-independent mapping name -> i<n>.
_CODE: dict[str, str] = {}
for _g, _fine in _TAXONOMY_NAMED.items():
    for _name in _fine:
        _CODE[_name] = f"i{len(_CODE) + 1:02d}"

GROUP_CODE = {g: f"g{i + 1}" for i, g in enumerate(_TAXONOMY_NAMED)}


def fine_criteria(group: str) -> dict[str, str]:
    return {_CODE[n]: d for n, d in _TAXONOMY_NAMED[group].items()}


def coarse_criteria() -> dict[str, str]:
    return {GROUP_CODE[g]: GROUP_DESC[g] for g in _TAXONOMY_NAMED}


FLAT_CRITERIA = {_CODE[n]: d for g in _TAXONOMY_NAMED.values() for n, d in g.items()}

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
    group_of_code = {GROUP_CODE[g]: g for g in _TAXONOMY_NAMED}

    rows: list[dict] = []
    for text, expect_c, expect_f in ITEMS:
        state = {"subject": "customer support ticket", "body": text}
        rec: dict = {"expect_coarse": expect_c, "expect_fine": expect_f,
                     "state_tokens": client.count_tokens(json.dumps(state))}
        try:
            a1 = client.ask(state, coarse_q)["answers"]["coarse"]
            rec["coarse_chosen_code"] = a1.get("choice")
            rec["coarse_chosen"] = group_of_code.get(a1.get("choice"))
            rec["coarse_correct"] = rec["coarse_chosen"] == expect_c
        except Exception as exc:
            rec["error"] = f"coarse: {exc}"[:200]
            rows.append(rec)
            continue

        # level 2 conditional on the TRUE group: isolates the layer's own skill
        try:
            a2 = client.ask(state, {"fine": {
                "type": "choice",
                "instructions": "Which specific request is this ticket about?",
                "criteria": fine_criteria(expect_c)}})["answers"]["fine"]
            rec["fine_given_correct_coarse"] = a2.get("choice") == _CODE[expect_f]
        except Exception as exc:
            rec["error"] = f"fine-cond: {exc}"[:200]

        # level 2 conditional on the CHOSEN group: the end-to-end experience
        if rec.get("coarse_chosen") in _TAXONOMY_NAMED:
            try:
                a3 = client.ask(state, {"fine": {
                    "type": "choice",
                    "instructions": "Which specific request is this ticket about?",
                    "criteria": fine_criteria(rec["coarse_chosen"])}})["answers"]["fine"]
                rec["end_to_end_correct"] = (
                    rec["coarse_correct"] and a3.get("choice") == _CODE[expect_f])
            except Exception as exc:
                rec["error"] = f"fine-e2e: {exc}"[:200]

        # flat arm: identical option descriptions, opaque keys
        try:
            a4 = client.ask(state, {"flat": {
                "type": "choice",
                "instructions": "Which specific request is this ticket about?",
                "criteria": FLAT_CRITERIA}})["answers"]["flat"]
            probs = a4.get("probabilities") or {}
            rec["flat_correct"] = a4.get("choice") == _CODE[expect_f]
            rec["flat_p_correct"] = probs.get(_CODE[expect_f])
        except Exception as exc:
            rec["error"] = f"flat: {exc}"[:200]

        rows.append(rec)

    ok = [r for r in rows if "coarse_correct" in r]

    def rate(k: str):
        v = [r[k] for r in ok if k in r]
        return (sum(1 for x in v if x) / len(v)) if v else None

    summary = {
        "n_items": len(ok),
        "coarse_options": len(_TAXONOMY_NAMED),
        "flat_options": len(_CODE),
        "label_keys": "OPAQUE (i01..i22, g1..g6) — the v1 shortcut is removed",
        "coarse_accuracy": rate("coarse_correct"),
        "fine_given_correct_coarse": rate("fine_given_correct_coarse"),
        "end_to_end_accuracy": rate("end_to_end_correct"),
        "flat_accuracy": rate("flat_correct"),
        "coarse_confusion": {r["expect_coarse"]: r.get("coarse_chosen")
                             for r in ok if not r.get("coarse_correct")},
        "caveat": ("PROBE. 21 authored tickets, one call per cell. Small N; the taxonomy "
                   "is authored, not drawn from MASSIVE/CLINC150."),
        "instrument": instrument_record(),
    }
    e2e, flat = summary["end_to_end_accuracy"], summary["flat_accuracy"]
    if e2e is not None and flat is not None:
        summary["hierarchy_beats_flat"] = e2e > flat
        summary["delta_e2e_minus_flat"] = e2e - flat
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P6b-hierarchical-sharding-opaque-keys.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"\nwritten: {p}")
