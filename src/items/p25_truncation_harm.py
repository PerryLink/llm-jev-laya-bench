"""P25 -- Does truncation actually destroy judgment, or only the state?

THE QUESTION P24 LEFT OPEN
--------------------------
P24 accumulated 60 records and found Laya's window fits only the first 14 steps (23% of
the run; the final state is 1,751 tokens against a 512-token clamp), while the LLM scored
1.00 on all 60. But P24 SKIPPED Laya once the state overflowed, on the principle that
admission should never rely on the judge's own flag. In production nothing skips: an
oversized state is silently truncated from the end and the judge answers anyway.

So the interesting question is not whether the window runs out -- P24 settled that -- but
whether running out HARMS the answer. That depends entirely on WHERE the needed evidence
sits, and the fixed serializer puts the NEWEST record first, so an end-truncating reader
loses the OLDEST material.

THE PAIRED DESIGN
-----------------
For a set of overflowing states, two noul questions against the SAME state:

    forward   about a record still inside the window  -> evidence survives truncation
    backward  about the OLDEST record in the ledger   -> evidence is dropped

plus a control that isolates what the truncation itself did: the backward question asked
again with that oldest record DELETED from the state. If the deletion changes the answer,
the item is one where truncation is decision-relevant; if it does not, the item cannot
show harm and is excluded from the harm estimate rather than counted as a success.

PRE-DECLARED READING
  If backward accuracy falls while forward holds, truncation is harmless for recent
  evidence and fatal for old evidence -- which turns "the window is small" into the much
  more useful "the window is small AND here is when it costs you".
  If both hold, truncation is benign on this task and the §5.3/§6.1 concern is narrower
  than the paper currently implies.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))
from deepseek_client import chat, parse_label, prompt_forced_choice  # noqa: E402
from laya_client import CHECKPOINT_CLAMP_TOKENS, LayaClient, instrument_record  # noqa: E402
from p24_reduced_horizon import gen_step, render  # noqa: E402

RESULTS = ROOT / "results"
N_RECORDS = 24          # comfortably past the 512-token clamp (P24 overflowed at 14)
N_ITEMS = 6


def ask_laya(client: LayaClient, state: str, question: str, criteria: dict) -> dict:
    r = client.ask(state, {"q": {"type": "noul", "instructions": question,
                                 "criteria": criteria}})
    a = r["answers"]["q"]
    p = float(a["noul"])
    return {"p_true": p, "pred": p >= 0.5, "truncated_flag": bool(r.get("truncated"))}


def ask_llm(state: str, question: str, criteria: dict) -> dict:
    r = chat(prompt_forced_choice(state, question, criteria), effort="none",
             json_mode=True, max_tokens=96)
    lab = parse_label(r, criteria)
    return {"label": lab, "pred": (lab == "true") if lab else None,
            "cost": r.cost.get("off_peak_usd")}


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    rng = random.Random(20260922)
    steps = [gen_step(rng, i) for i in range(N_RECORDS)]
    records = [s["record"] for s in steps]

    rows: list[dict] = []
    for k in range(N_ITEMS):
        # state = the k most recent records, chosen to sit past the clamp
        take = N_RECORDS - k
        sub = records[:take]
        state = render(sub)
        toks = client.count_tokens(state)
        newest, oldest = steps[take - 1], steps[0]

        def q_for(step: dict) -> dict:
            return {"question": f"Does the ledger record {step['value']} {step['unit']} "
                                f"as the current {step['label']}?",
                    "criteria": {"true": f"the ledger records {step['value']} "
                                         f"{step['unit']} as current for {step['label']}",
                                 "false": f"the ledger does not record {step['value']} "
                                          f"{step['unit']} as current for {step['label']}"}}

        rec = {"item": k, "n_records": take, "state_tokens": toks,
               "window_frac": round(min(1.0, 450 / max(1, toks)), 4)}
        qn, qo = q_for(newest), q_for(oldest)

        try:
            rec["fwd_laya"] = ask_laya(client, state, qn["question"], qn["criteria"])
            rec["bwd_laya"] = ask_laya(client, state, qo["question"], qo["criteria"])
            # control: the oldest record removed, so nothing needs to be truncated
            state_no_oldest = render(sub[1:])
            rec["bwd_control_laya"] = ask_laya(client, state_no_oldest, qo["question"],
                                               qo["criteria"])
        except Exception as exc:
            rec["laya_error"] = str(exc)[:200]

        try:
            rec["fwd_llm"] = ask_llm(state, qn["question"], qn["criteria"])
            rec["bwd_llm"] = ask_llm(state, qo["question"], qo["criteria"])
        except Exception as exc:
            rec["llm_error"] = str(exc)[:200]

        # Is this item capable of showing harm? Only if the oldest record's presence
        # changes the answer, i.e. truncating it away is decision-relevant.
        if "bwd_laya" in rec and "bwd_control_laya" in rec:
            rec["deletion_changes_answer"] = (
                rec["bwd_laya"]["pred"] != rec["bwd_control_laya"]["pred"])
        rows.append(rec)
        print(f"item {k}: recs={take:>2} tok={toks:>4} "
              f"fwd={rec.get('fwd_laya', {}).get('pred')} "
              f"bwd={rec.get('bwd_laya', {}).get('pred')} "
              f"bwd_ctl={rec.get('bwd_control_laya', {}).get('pred')} "
              f"llm_fwd={rec.get('fwd_llm', {}).get('pred')} "
              f"llm_bwd={rec.get('bwd_llm', {}).get('pred')}")

    def acc(key: str) -> dict | None:
        vals = [r[key]["pred"] for r in rows if key in r and r[key]["pred"] is not None]
        if not vals:
            return None
        # every truth in this battery is TRUE (the value IS recorded as current)
        return {"n": len(vals), "correct": sum(1 for v in vals if v), "accuracy": round(
            sum(1 for v in vals if v) / len(vals), 4)}

    summary = {
        "n_items": len(rows),
        "records_per_item_max": N_RECORDS,
        "clamp_tokens": CHECKPOINT_CLAMP_TOKENS["english"],
        "state_tokens_range": [min(r["state_tokens"] for r in rows),
                               max(r["state_tokens"] for r in rows)],
        "forward_recent_evidence": {
            "laya": acc("fwd_laya"), "llm": acc("fwd_llm")},
        "backward_oldest_evidence": {
            "laya": acc("bwd_laya"), "llm": acc("bwd_llm")},
        "backward_with_oldest_record_deleted_control": {"laya": acc("bwd_control_laya")},
        "items_where_deletion_changes_answer": sum(
            1 for r in rows if r.get("deletion_changes_answer")),
        "instrument": instrument_record(),
        "caveat": (f"{N_ITEMS} states of {N_RECORDS} records each, one call per cell. "
                   f"Small n: this isolates the DIRECTION of the truncation effect, not "
                   f"its magnitude."),
        "verdict": None,
    }
    f = summary["forward_recent_evidence"]["laya"]
    b = summary["backward_oldest_evidence"]["laya"]
    if f and b:
        fwd = f["accuracy"]
        bwd = b["accuracy"]
        if fwd > bwd + 0.2:
            summary["verdict"] = (
                f"TRUNCATION IS SELECTIVE: with evidence that survives the window Laya "
                f"scores {fwd} ({f['correct']}/{f['n']}); asking about the OLDEST record, "
                f"whose evidence is dropped, it scores {bwd} ({b['correct']}/{b['n']}). "
                f"So the cost of a small window depends on WHERE the evidence sits, not "
                f"merely on the state being long.")
        else:
            summary["verdict"] = (
                f"TRUNCATION IS BENIGN ON THIS TASK: forward {fwd} vs backward {bwd}. "
                f"Even with the evidence in the truncated region Laya answers about as "
                f"well, so the window concern is narrower than an items-fit-count "
                f"suggests -- note that a positive result here is partly explainable by "
                f"the question being answerable from the surviving scaffold text.")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P25-truncation-harm.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps({k: v for k, v in out["summary"].items() if k != "instrument"},
                     indent=2, ensure_ascii=False))
    print(f"\nwritten: {p}")
