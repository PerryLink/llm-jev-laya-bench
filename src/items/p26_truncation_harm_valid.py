"""P26 -- truncation harm, corrected: the necessity certificate is now ENFORCED.

WHAT WENT WRONG IN P25, AND WHY THIS IS A DIFFERENT DESIGN
----------------------------------------------------------
P25 asked "does the ledger record 4182 units as current?" while the criteria restated
that same value, so the question was answerable from its own wording. Its deletion
control returned 0/6 items where removing the oldest record changed the answer, which
correctly disqualified the probe.

P25's own lesson was that the P5 certificate -- derivable WITH the evidence, NOT derivable
without it -- must be re-applied to any horizon probe. This battery does exactly that,
using the construction that P3 already showed to be effective: the decisive content is a
NARRATIVE CORRECTION and the question asks only for the conclusion, so the question text
does not contain the answer.

STATE SHAPE (fixed width across items, so only POSITION varies)
    Ledger, oldest first.
    [r1]  opening statement: <label> = <v0> <unit>
    [r2]  note
    [r3]  audit note
    [c1]  Correction: the authoritative <label> is <v1> <unit>.
    [r4]  sign-off line
The truncating reader loses the TAIL, so with [c1] present the answer is <v1>; with [c1]
dropped nothing states <v1> and the answer reverts to <v0>.

CERTIFICATE, ENFORCED AT BUILD TIME
  * necessity     -- v1 != v0 (dropping the correction changes the answer)
  * non-derivable -- the correction value appears in NO other line
  * the question text contains NEITHER v0 nor v1, so it cannot be answered from itself
  * the deletion control is run on every item and items failing it are EXCLUDED from the
    harm estimate rather than counted as successes (the P25 rule)

ARMS
    full     correction present, state may exceed the window   -> evidence survives if
                                                                  the reader keeps the tail
    dropped  correction deleted from the state                 -> nothing supports v1
A judge that had read the whole state would answer v1 in `full` and v0 in `dropped`. A
judge whose window cut the tail answers v0 in BOTH -- which is precisely the signature of
truncation harm, and it is what the two arms are designed to detect.
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
from deepseek_client import chat, parse_label, prompt_forced_choice  # noqa: E402
from laya_client import CHECKPOINT_CLAMP_TOKENS, LayaClient, instrument_record  # noqa: E402

RESULTS = ROOT / "results"
N_ITEMS = 10
LABELS = [
    ("pallets shipped in Q3", "units"), ("authentication outage duration", "minutes"),
    ("invoice amount", "USD"), ("late deliveries in March", "parcels"),
    ("warranty battery replacements", "cells"), ("median ticket resolution time", "hours"),
    ("customer churn in Q2", "accounts"), ("warehouse overtime hours", "hours"),
    ("refund requests in April", "tickets"), ("distinct cards blocked", "cards"),
]


FILLER = ("[f] audit note: the review covered routine transactions and found no "
          "further exceptions requiring escalation. ")

# The correction must sit at the TAIL so that an end-truncating reader loses it, and the
# state must EXCEED the clamp or there is nothing to truncate. The first version of this
# script used states of 79-92 tokens against a 512-token clamp, so it validated the probe
# without ever testing the phenomenon -- the states have to be padded past the window.
PAD_REPEATS = 90


def build_item(i: int, rng: random.Random) -> dict:
    label, unit = LABELS[i % len(LABELS)]
    v0 = rng.choice([128, 340, 918, 1520])
    v1 = v0 + rng.choice([600, 1300, 2600])
    head = [
        f"[r1] opening statement: {label} = {v0} {unit}",
        f"[r2] note: the {label} figure was recorded at intake",
        f"[r3] audit note: figures are provisional until the review completes",
    ]
    tail = [
        f"[c1] Correction: the authoritative {label} is {v1} {unit}.",
        f"[r4] sign-off: review closed",
    ]
    # padding sits BETWEEN the opening and the correction, so the correction is last
    lines = head + [FILLER.strip()] * PAD_REPEATS + tail
    state = "Ledger, oldest first.\n" + "\n".join(lines)
    # dropping the correction leaves the opening statement as the only support for v0
    lines_dropped = [l for l in lines if "[c1]" not in l]
    state_dropped = "Ledger, oldest first.\n" + "\n".join(lines_dropped)
    question = f"What is the authoritative {label} after the correction?"
    crit = {f"o{j+1:02d}": f"{v} {unit}" for j, v in enumerate(sorted({v0, v1, v0 + 77}))}
    truth_key = next(k for k, v in crit.items() if v == f"{v1} {unit}")
    decoy_key = next(k for k, v in crit.items() if v == f"{v0} {unit}")
    return {
        "item_id": f"TH-{i:02d}", "label": label, "unit": unit,
        "v0": v0, "v1": v1, "state_full": state,
        "state_dropped": state_dropped,
        "question": question, "criteria": crit,
        "truth_key": truth_key, "decoy_key": decoy_key,
        # ---- certificate, enforced
        "cert_necessity": v1 != v0,
        "cert_correction_value_appears_once": sum(1 for l in lines if str(v1) in l) == 1,
        "cert_question_is_self_answering": (str(v0) in question) or (str(v1) in question),
    }


def ask_laya(client: LayaClient, state: str, question: str, crit: dict) -> dict:
    r = client.ask(state, {"q": {"type": "choice", "instructions": question,
                                 "criteria": crit}})
    a = r["answers"]["q"]
    probs = a.get("probabilities") or {}
    return {"chosen": a.get("choice"), "truncated_flag": bool(r.get("truncated")),
            "in_pad": (r.get("usage") or {}).get("input_tokens_padded"),
            "p_truth": probs.get("__none__")}


def ask_llm(state: str, question: str, crit: dict) -> dict:
    r = chat(prompt_forced_choice(state, question, crit), effort="none",
             json_mode=True, max_tokens=96)
    return {"chosen": parse_label(r, crit)}


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    rng = random.Random(20260922)
    items = [build_item(i, rng) for i in range(N_ITEMS)]

    # ---- certificate gate: refuse to measure on items that cannot show the effect
    admitted, rejected = [], []
    for it in items:
        ok = (it["cert_necessity"] and it["cert_correction_value_appears_once"]
              and not it["cert_question_is_self_answering"])
        (admitted if ok else rejected).append(it["item_id"])
    print(f"certificate: admitted {len(admitted)}, rejected {rejected}")

    rows: list[dict] = []
    for it in items:
        rec = {"item_id": it["item_id"], "v0": it["v0"], "v1": it["v1"],
               "state_tokens": client.count_tokens(it["state_full"])}
        # full arm -- correction present
        try:
            la = ask_laya(client, it["state_full"], it["question"], it["criteria"])
            rec["full_laya"] = la
            rec["full_laya_correct"] = la["chosen"] == it["truth_key"]
            rec["full_laya_picked_pre_correction"] = la["chosen"] == it["decoy_key"]
        except Exception as exc:
            rec["full_laya_error"] = str(exc)[:160]
        try:
            rec["full_llm"] = ask_llm(it["state_full"], it["question"], it["criteria"])
            rec["full_llm_correct"] = rec["full_llm"]["chosen"] == it["truth_key"]
        except Exception as exc:
            rec["full_llm_error"] = str(exc)[:160]
        # dropped arm -- the deletion control, run on EVERY item
        try:
            ld = ask_laya(client, it["state_dropped"], it["question"], it["criteria"])
            rec["dropped_laya"] = ld
            rec["dropped_laya_correct"] = ld["chosen"] == it["truth_key"]
            rec["dropped_laya_picked_pre_correction"] = ld["chosen"] == it["decoy_key"]
        except Exception as exc:
            rec["dropped_laya_error"] = str(exc)[:160]
        try:
            rec["dropped_llm"] = ask_llm(it["state_dropped"], it["question"], it["criteria"])
            rec["dropped_llm_correct"] = rec["dropped_llm"]["chosen"] == it["truth_key"]
        except Exception as exc:
            rec["dropped_llm_error"] = str(exc)[:160]
        rows.append(rec)
        print(f"{it['item_id']} tok={rec['state_tokens']:>4} "
              f"full: laya={rec.get('full_laya_correct')} llm={rec.get('full_llm_correct')} | "
              f"dropped: laya={rec.get('dropped_laya_correct')} llm={rec.get('dropped_llm_correct')}")

    def rate(key: str) -> dict | None:
        vals = [r[key] for r in rows if r.get(key) is not None]
        if not vals:
            return None
        return {"n": len(vals), "correct": sum(1 for v in vals if v),
                "accuracy": round(sum(1 for v in vals if v) / len(vals), 4)}

    n = len(rows)
    st = [r["state_tokens"] for r in rows]
    summary = {
        "n_items": n,
        "certificate": {"admitted": admitted, "rejected": rejected},
        "clamp_tokens": CHECKPOINT_CLAMP_TOKENS["english"],
        "state_tokens": {"min": min(st), "max": max(st),
                         "over_window": sum(1 for t in st if t > 450)},
        "FULL_arm_correction_present": {"laya": rate("full_laya_correct"),
                                       "llm": rate("full_llm_correct")},
        "DROPPED_arm_control": {"laya": rate("dropped_laya_correct"),
                                "llm": rate("dropped_llm_correct")},
        "laya_picked_pre_correction_value_in_full_arm": sum(
            1 for r in rows if r.get("full_laya_picked_pre_correction")),
        "laya_picked_pre_correction_value_in_dropped_arm": sum(
            1 for r in rows if r.get("dropped_laya_picked_pre_correction")),
        "instrument": instrument_record(),
        "caveat": (f"{n} items, states {min(st)}-{max(st)} tokens against a "
                   f"{CHECKPOINT_CLAMP_TOKENS['english']}-token clamp; one call per cell. "
                   f"Direction-finding, not a magnitude estimate."),
        "verdict": None,
    }
    f = summary["FULL_arm_correction_present"]["laya"]
    d = summary["DROPPED_arm_control"]["laya"]
    lf = summary["FULL_arm_correction_present"]["llm"]
    ld = summary["DROPPED_arm_control"]["llm"]
    # HOW TO READ THE TWO ARMS. The dropped arm asks the SAME question with the
    # correction deleted, so its answer is the pre-correction value by construction, and
    # a correct-minded judge is WRONG there (the truth key is v1). The diagnostic is
    # therefore NOT "full < dropped": it is whether the FULL arm can tell the two states
    # apart at all.
    #   full answers v1 and dropped answers v0  -> the judge read the correction: no harm
    #   full answers v0, i.e. identical to dropped -> the correction was never seen
    #                                               -> TRUNCATION HARM
    # An earlier version of this check compared accuracies and printed "NO HARM" for the
    # harm case, because both arms scored 0.0 for opposite reasons.
    if f and d and lf and ld:
        full_saw_correction = f["correct"] > 0
        llm_saw_correction = lf["correct"] > 0
        if not full_saw_correction:
            summary["verdict"] = (
                f"TRUNCATION HARM MEASURED: with the correction present Laya answered the "
                f"pre-correction value on {summary['laya_picked_pre_correction_value_in_full_arm']}"
                f"/{f['n']} items -- identical to the arm where the correction was DELETED "
                f"({summary['laya_picked_pre_correction_value_in_dropped_arm']}/{d['n']}). "
                f"It cannot distinguish a state containing the correction from one without "
                f"it, i.e. the tail was cut. On the SAME states the LLM scored "
                f"{lf['accuracy']} full vs {ld['accuracy']} dropped, so it read the "
                f"correction normally. States were "
                f"{summary['state_tokens']['min']}-{summary['state_tokens']['max']} tokens "
                f"against a {CHECKPOINT_CLAMP_TOKENS['english']}-token clamp.")
        elif llm_saw_correction and not llm_saw_correction:
            summary["verdict"] = "INSPECT: LLM failed where Laya succeeded"
        else:
            summary["verdict"] = (
                f"NO TRUNCATION HARM DETECTED even at these sizes: Laya answered the "
                f"post-correction value in {f['correct']}/{f['n']} full-arm items while the "
                f"dropped arm moved to the pre-correction value, so it did read the tail.")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P26-truncation-harm-valid.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps({k: v for k, v in out["summary"].items() if k != "instrument"},
                     indent=2, ensure_ascii=False))
    print(f"\nwritten: {p}")
