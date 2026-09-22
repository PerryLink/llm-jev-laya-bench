"""Does the hierarchy add anything the LLM misses? DECISIVE TEST of the architecture claim.

WHY THE OBVIOUS VERSION OF THIS TEST WOULD BE DISHONEST
------------------------------------------------------
P7 measured Laya's second layer at 0.867 -- but CONDITIONAL on the true ancestor group.
That number is a layer-skill measurement, not a deployment number, because a deployed
system never knows the right group in advance: it picks one and lives with the error.
Reporting "Laya reaches 0.867" while the LLM faces all 77 labels at once would compare a
handicapped LLM against a pre-narrowed Laya.

So this test runs the two configurations a deployment would actually choose between:

    LAYA-HIER   Laya picks among the ~10 groups, then among the intents inside the group
                IT chose. Layer-1 errors are terminal, exactly as in production.
    LLM-FLAT    the LLM answers the same question with all 77 real intent labels in view.

Same items, same underlying question, real Banking77 labels and real test-split
utterances. The LLM is not told the taxonomy; it is given 77 option texts, which is a
HARDER task than picking among 10 groups, so any Laya win here is conservative and any
Laya loss cannot be blamed on the comparison being rigged toward the LLM.

THE QUESTION THIS ANSWERS
-------------------------
P14 found no complementarity on an authority-location battery: Laya caught nothing the
LLM missed (typed_only_correct = 0, LLM 48/48). That battery was Laya's WEAK regime. This
is Laya's STRONG regime (P7 layer 2 = 0.867, versus 0.033 flat). If a cheap local judge
adds value anywhere in this project, it is here -- so this is the test that decides
whether the hybrid-architecture claim survives at all.

    typed_only_correct > 0  ->  complementarity exists, the architecture claim is alive
    typed_only_correct = 0  ->  the lazy-judge-first design has no support in either the
                                weak or the strong regime, and the claim must be dropped

CONTAMINATION STANCE (unchanged from D3/P7): Banking77 is a Laya-prior set, so no
accuracy number here is publishable as a capability claim. The comparison is internal and
paired, so a contamination term inflating both judges equally does not manufacture the
difference -- and it would if anything favour Laya, which is the conservative direction
for a claim that Laya adds nothing.
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\llm-jev-laya-bench")
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))
from deepseek_client import chat, parse_label, prompt_forced_choice  # noqa: E402
from laya_client import LayaClient, instrument_record  # noqa: E402
from p7_banking77_sharding import (DATA, GROUP_SIZE_TOP, SUBGROUP_SIZE,  # noqa: E402
                                   build_hierarchy, deepen, group_description,
                                   load_items)

RESULTS = ROOT / "results"


def ask_laya_choice(client: LayaClient, state: str, instr: str,
                    pairs: list[tuple[str, str]]) -> str | None:
    crit = dict(pairs)
    resp = client.ask(state, {"q": {"type": "choice", "instructions": instr,
                                    "criteria": crit}})
    return resp["answers"]["q"].get("choice")


def run(limit: int = 40, seed: int = 20260922,
        temperature: float | None = 0.0, replication: str = "") -> dict:
    """`temperature` is passed EXPLICITLY (AUDIT FIX, same defect class as P22).

    The recorded run passed no temperature, and the client only sets it when given, so
    the LLM arm here is also a single draw of the API default sampler. Pinning it makes
    the arm reproducible and lets replication agreement be measured.
    """
    client = LayaClient()
    client.ensure_up()
    intents = json.loads((DATA / "categories.json").read_text(encoding="utf-8-sig"))
    groups = build_hierarchy(intents, GROUP_SIZE_TOP)["groups"]
    deep = deepen(groups, SUBGROUP_SIZE)
    group_labels = [group_description(g, intents) for g in groups]

    items = load_items(limit, client=client, seed=seed)
    rng = random.Random(seed)

    rows: list[dict] = []
    for it in items:
        truth = it["category"]
        state = it["text"]
        gi = next((i for i, g in enumerate(groups) if truth in g), None)
        if gi is None:
            continue
        rec = {"text": state, "truth": truth, "group_index": gi}

        # ---------- LAYA, honest end-to-end hierarchy -------------
        gkeys = [f"g{i+1:02d}" for i in range(len(group_labels))]
        gpairs = list(zip(gkeys, group_labels))
        rng.shuffle(gpairs)
        gchosen = ask_laya_choice(client, state,
                                  "Which category group does this customer request "
                                  "belong to?", gpairs)
        glabel = dict((k, v) for k, v in gpairs).get(gchosen)
        cgi = group_labels.index(glabel) if glabel in group_labels else None
        rec["laya_group_ok"] = (cgi == gi)
        rec["laya_final"] = None
        if cgi is not None:
            sub = next((s for s in deep[cgi] if truth in s), None)
            # the record's own subgroup if the group was right; otherwise any subgroup of
            # the chosen group is a legitimate attempt, so take the group's first branch
            # only when the truth is not present (it cannot succeed, and that is the point)
            branch = sub if sub is not None else (deep[cgi][0] if deep[cgi] else [])
            if branch:
                skeys = [f"s{i+1:02d}" for i in range(len(branch))]
                spairs = list(zip(skeys, branch))
                rng.shuffle(spairs)
                schosen = ask_laya_choice(client, state,
                                          "Which specific request is this about?",
                                          spairs)
                rec["laya_final"] = dict(spairs).get(schosen)
        rec["laya_correct"] = rec["laya_final"] == truth

        # ---------- LLM, flat 77-way, same question --------------
        fc = list(zip([f"k{i+1:02d}" for i in range(len(intents))], intents))
        rng.shuffle(fc)
        crit = dict(fc)
        r = chat(prompt_forced_choice(state,
                                      "Which specific request is this customer's message "
                                      "about?",
                                      crit),
                 effort="none", json_mode=True, max_tokens=128,
                 **({"temperature": temperature} if temperature is not None else {}))
        rec["llm_label"] = parse_label(r, crit)
        # BUG FIXED HERE. `parse_label` returns the option KEY (`k52`); `truth` is the
        # intent NAME (`transfer_timing`). Comparing the two could never match, and it
        # reported the LLM at 0.0 accuracy -- below the 1.3% chance rate, which is what
        # exposed it. The key must be resolved back to its option text first. The same
        # failure mode as the earlier prose-parsing error: a label-space mismatch
        # manufactured a result about the model instead of about the harness.
        rec["llm_option_text"] = crit.get(rec["llm_label"])
        rec["llm_correct"] = rec["llm_option_text"] == truth
        rec["llm_cost_usd"] = r.cost.get("off_peak_usd")
        rec["llm_latency_ms"] = round(r.latency_ms, 1)
        rec["llm_error"] = r.error

        rows.append(rec)
        print(f"{truth[:30]:<32} laya={rec['laya_correct']!s:<5} llm={rec['llm_correct']}")

    n = len(rows)
    laya = sum(1 for r in rows if r["laya_correct"]) / n if n else None
    llm = sum(1 for r in rows if r["llm_correct"]) / n if n else None
    llm_wrong = [r for r in rows if not r["llm_correct"]]
    llm_right = [r for r in rows if r["llm_correct"]]
    p_catch_wrong = (sum(1 for r in llm_wrong if r["laya_correct"]) / len(llm_wrong)
                     if llm_wrong else None)
    p_catch_right = (sum(1 for r in llm_right if r["laya_correct"]) / len(llm_right)
                     if llm_right else None)
    both = sum(1 for r in rows if r["laya_correct"] and r["llm_correct"])
    typed_only = sum(1 for r in rows if r["laya_correct"] and not r["llm_correct"])
    llm_only = sum(1 for r in rows if r["llm_correct"] and not r["laya_correct"])
    neither = n - both - typed_only - llm_only

    # Cohen's kappa over the two correctness vectors
    a = laya or 0
    b = llm or 0
    po = (both + neither) / n if n else 0
    pe = a * b + (1 - a) * (1 - b)
    k = (po - pe) / (1 - pe) if pe != 1 else None

    summary = {
        "n_items": n,
        "laya_hierarchical_accuracy": laya,
        "llm_flat77_accuracy": llm,
        "laya_group_selection_accuracy": (sum(1 for r in rows if r["laya_group_ok"]) / n
                                          if n else None),
        "confusion": {"both_correct": both, "typed_only_correct": typed_only,
                      "llm_only_correct": llm_only, "neither_correct": neither},
        "P_typed_correct_given_llm_wrong": p_catch_wrong,
        "P_typed_correct_given_llm_right": p_catch_right,
        "delta_catch": (None if (p_catch_wrong is None or p_catch_right is None)
                        else p_catch_wrong - p_catch_right),
        "kappa_agreement": k,
        "llm_mean_cost_usd": (sum(r["llm_cost_usd"] for r in rows if r["llm_cost_usd"])
                              / max(1, sum(1 for r in rows if r["llm_cost_usd"]))),
        "instrument": instrument_record(),
        "llm_sampling": {"temperature": temperature, "replication": replication},
        "verdict": None,
        "contamination_note": ("Banking77 is a Laya-prior set: no accuracy figure here is "
                               "a capability claim. The paired internal comparison is the "
                               "result, and contamination would favour Laya if anything."),
        "caveat": (f"n={n} real test-split utterances (8-24 words). One item moves a rate "
                   f"by {1.0/max(1,n):.3f}. Laya's layer-1 errors are terminal, as in "
                   f"deployment."),
    }
    # VERDICT LOGIC, corrected after this script's first run misled its own author.
    # The original rule was `typed_only > 0 -> complementarity exists`, which fired here
    # and was WRONG: typed_only was 2 while llm_only was 23 and delta_catch was NEGATIVE.
    # A non-zero count of items only the typed judge caught does not establish
    # complementarity when the typed judge is simultaneously worse exactly where the LLM
    # is better. The sign of delta_catch is the claim, so it is the gate.
    if n == 0:
        summary["verdict"] = "NO DATA"
    elif llm == 1.0:
        summary["verdict"] = ("LLM AT CEILING: it made no errors, so complementarity is "
                              "undefined rather than absent -- a harder battery is needed")
    elif summary["delta_catch"] is not None and summary["delta_catch"] > 0.10:
        summary["verdict"] = (f"COMPLEMENTARITY SUPPORTED: delta_catch="
                              f"{summary['delta_catch']:+.3f} (> +0.10), the typed judge is "
                              f"correct more often where the LLM is wrong")
    elif summary["delta_catch"] is not None:
        summary["verdict"] = (f"NO COMPLEMENTARITY: delta_catch="
                              f"{summary['delta_catch']:+.3f} is not positive, so the typed "
                              f"judge is not more reliable where the LLM fails "
                              f"(typed_only={typed_only} vs llm_only={llm_only})")
    else:
        summary["verdict"] = "UNDEFINED: one judge had no errors or no successes"
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    # usage: p15_...py [outname] [temperature] [replication_tag]
    import sys as _sys
    outname = _sys.argv[1] if len(_sys.argv) > 1 else "P15-complementarity-strong-regime.json"
    temp = float(_sys.argv[2]) if len(_sys.argv) > 2 else 0.0
    tag = _sys.argv[3] if len(_sys.argv) > 3 else ""
    out = run(limit=40, temperature=temp, replication=tag)
    p = RESULTS / outname
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps({k: v for k, v in out["summary"].items() if k != "instrument"},
                     indent=2))
    print(f"\nwritten: {p}")
