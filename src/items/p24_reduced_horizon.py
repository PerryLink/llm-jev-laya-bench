"""P24 -- REDUCED HORIZON: does accuracy or the judge's usable window degrade over a
multi-session run?

WHY THIS EXISTS
---------------
§10.1 of the paper lists "the long-horizon / multi-session experiment was not executed"
as its FIRST limitation, and it is the one that cannot be papered over: the paper's whole
framing is about long-line execution, yet every measurement so far is a single call.
CHAIN-AUDIT (P22) supplied DEPTH -- many hops inside one call -- but not TIME SPAN.

A full battery (24 families x 4 runs x 120 steps) is larger than everything else in this
project combined. This is the REDUCED version the lead offered as option 2: a small
number of sessions, each appending steps to a carried state, measuring the two things
that plausibly change with horizon:

  (a) JUDGMENT ACCURACY over steps -- does it drift as the carried state grows?
  (b) THE JUDGE'S USABLE WINDOW over steps -- Laya's window is fixed while the state
      grows, so the fraction of state that survives truncation must fall. This is the
      prediction the paper's §5.3 and §6.1 make, and until now it was measured only at
      synthetic sizes rather than along an actual accumulating run.

WHY THE GENERATOR IS PROGRAMMATIC
---------------------------------
The carried state is built from generated claim records, and the ground truth for each
step's question is COMPUTED from those records. So this is a genuine multi-step
accumulation with an exact oracle and zero annotation cost, and the only spend is model
calls. The LLM is used in the role §4.1 assigns it -- as a JUDGE, not as a text
generator -- so the run measures judgment under accumulation rather than generation
quality.

HONEST SCOPING. This is NOT the full agentic battery: no tool use, no code execution, no
resumption across process boundaries. It measures whether an accumulating state degrades
judgment and erodes the window, which is the specific mechanism the paper claims matters.
The paper must describe it as such and must NOT upgrade it into an autonomous long-run
result.
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
import statistics
import sys
from pathlib import Path


sys.path.insert(0, str(ROOT / "src" / "instrument"))
from deepseek_client import chat, parse_label, prompt_forced_choice  # noqa: E402
from laya_client import (CHECKPOINT_CLAMP_TOKENS, LayaClient,  # noqa: E402
                         instrument_record)

RESULTS = ROOT / "results"

LABELS = [
    ("pallets shipped in Q3", "units"), ("authentication outage duration", "minutes"),
    ("invoice amount", "USD"), ("late deliveries in March", "parcels"),
    ("warranty battery replacements", "cells"), ("median ticket resolution time", "hours"),
    ("customer churn in Q2", "accounts"), ("warehouse overtime hours", "hours"),
    ("refund requests in April", "tickets"), ("distinct cards blocked", "cards"),
    ("chargebacks filed", "disputes"), ("average call handling time", "seconds"),
    ("new merchant signups", "merchants"), ("failed settlement attempts", "attempts"),
    ("manual review escalations", "cases"), ("duplicate charge reports", "reports"),
]

STEPS_PER_SESSION = 20
N_SESSIONS = 3


def gen_step(rng: random.Random, step_index: int) -> dict:
    label, unit = LABELS[step_index % len(LABELS)]
    value = rng.choice([128, 340, 918, 1520, 4182, 9700]) * (1 + step_index % 3)
    decoy = value + rng.choice([47, 260, 1300])
    # The authoritative line is tagged (current); this is the template P5c validated as
    # BOTH derivable and carrier-required (accuracy 1.00 with the carrier, 0.00 without).
    text = (f"revision {step_index + 1}: {label} = {value} {unit} (current)\n"
            f"revision {step_index + 1}b: {label} = {decoy} {unit}")
    crit = {"true": f"the ledger records {value} {unit} as current for {label}",
            "false": f"the ledger does not record {value} {unit} as current for {label}"}
    q = f"Does the ledger record {value} {unit} as the current {label}?"
    return {"step": step_index, "label": label, "unit": unit, "value": value,
            "decoy": decoy, "record": text, "truth": True, "criteria": crit,
            "question": q}


def render(state_records: list[str]) -> str:
    """Fixed serializer. Newest records first, so an end-truncating reader loses the
    OLDEST material, and `DROPPED` is emitted first so a front-keeping reader sees it."""
    return ("Ledger of audited revisions (most recent first).\n"
            + "\n".join(reversed(state_records)))


def run() -> dict:
    client = LayaClient()
    client.ensure_up()
    rng = random.Random(20260922)
    all_steps = [gen_step(rng, i) for i in range(STEPS_PER_SESSION * N_SESSIONS)]

    rows: list[dict] = []
    records: list[str] = []
    for step in all_steps:
        records.append(step["record"])
        state = render(records)
        st_tokens = client.count_tokens(state)
        clamp = CHECKPOINT_CLAMP_TOKENS["english"]

        rec = {"step": step["step"],
               "session": step["step"] // STEPS_PER_SESSION,
               "n_records": len(records),
               "state_chars": len(state),
               "state_tokens": st_tokens,
               # the window-erosion prediction: how much of the state fits
               "fits_window": st_tokens <= (clamp - 61 - 1),
               "state_frac_within_window": round(min(1.0, (clamp - 61 - 1) / max(1, st_tokens)), 4)}

        # ---- Laya, admitted only if OUR tokenizer says it fits (never Laya's flag)
        if rec["fits_window"]:
            try:
                lr = client.ask(state, {"q": {"type": "noul",
                                              "instructions": step["question"],
                                              "criteria": step["criteria"]}})
                a = lr["answers"]["q"]
                p = float(a["noul"])
                rec["laya_p_true"] = p
                rec["laya_correct"] = (p >= 0.5) == step["truth"]
                rec["laya_truncated_flag"] = bool(lr.get("truncated"))
            except Exception as exc:
                rec["laya_error"] = str(exc)[:160]
        else:
            rec["laya_skipped"] = "over window by our own count"

        # ---- LLM on the same state and question
        try:
            r = chat(prompt_forced_choice(state, step["question"], step["criteria"]),
                     effort="none", json_mode=True, max_tokens=96)
            lab = parse_label(r, step["criteria"])
            rec["llm_correct"] = (lab == "true") == step["truth"] if lab else None
            rec["llm_cost"] = r.cost.get("off_peak_usd")
        except Exception as exc:
            rec["llm_error"] = str(exc)[:160]

        rows.append(rec)
        print(f"step {rec['step']:>2} sess={rec['session']} recs={rec['n_records']:>2} "
              f"tok={rec['state_tokens']:>4} fits={rec['fits_window']!s:<5} "
              f"laya={rec.get('laya_correct')} llm={rec.get('llm_correct')}")

    def sess_stats(pred) -> dict:
        out: dict = {}
        for s in range(N_SESSIONS):
            sub = [r for r in rows if r["session"] == s and pred(r) is not None]
            out[s] = {"n": len(sub),
                      "accuracy": round(sum(1 for r in sub if pred(r)) / len(sub), 4)
                      if sub else None}
        return out

    laya_acc = sess_stats(lambda r: r.get("laya_correct"))
    llm_acc = sess_stats(lambda r: r.get("llm_correct"))
    fits = [r["fits_window"] for r in rows]
    first_overflow = next((r["step"] for r in rows if not r["fits_window"]), None)

    summary = {
        "n_steps": len(rows),
        "n_sessions": N_SESSIONS,
        "steps_per_session": STEPS_PER_SESSION,
        "laya_accuracy_by_session": laya_acc,
        "llm_accuracy_by_session": llm_acc,
        "window": {
            "fits_count": sum(1 for f in fits if f),
            "over_count": sum(1 for f in fits if not f),
            "first_overflow_step": first_overflow,
            "clamp_tokens": CHECKPOINT_CLAMP_TOKENS["english"],
            "final_state_tokens": rows[-1]["state_tokens"],
            "final_state_chars": rows[-1]["state_chars"],
        },
        "instrument": instrument_record(),
        "caveat": ("REDUCED horizon: 3 sessions x 20 accumulated records, single judge "
                   "call per step, no tool use and no cross-process resumption. It "
                   "measures accumulation effects on judgment and window erosion, NOT "
                   "autonomous long-run behaviour. Do not report it as a full agentic "
                   "long-horizon result."),
        "verdict": None,
    }
    # What the two hypotheses predict:
    #   drift      -> accuracy falls from session 0 to session 2
    #   erosion    -> the window stops fitting the state at some step, and Laya is
    #                 therefore skipped or truncating from then on
    l0 = laya_acc.get(0, {}).get("accuracy")
    l2 = laya_acc.get(2, {}).get("accuracy")
    drift = (l0 - l2) if (l0 is not None and l2 is not None) else None
    summary["laya_drift_session0_minus_session2"] = drift
    summary["verdict"] = (
        f"WINDOW EROSION OBSERVED: the accumulated state stops fitting at step "
        f"{first_overflow}/{len(rows)} (final {rows[-1]['state_tokens']} tokens vs a "
        f"{CHECKPOINT_CLAMP_TOKENS['english']}-token clamp). Laya drift s0->s2: {drift}."
        if first_overflow is not None else
        f"NO EROSION within {len(rows)} steps (final state {rows[-1]['state_tokens']} "
        f"tokens, still inside the {CHECKPOINT_CLAMP_TOKENS['english']}-token clamp). "
        f"Laya drift s0->s2: {drift}.")
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    out = run()
    p = RESULTS / "P24-reduced-horizon.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    s = out["summary"]
    print("\n=== SUMMARY ===")
    print(json.dumps({k: v for k, v in s.items() if k != "instrument"},
                     indent=2, ensure_ascii=False))
    print(f"\nwritten: {p}")
