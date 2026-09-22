"""P26 CONTROL ARM -- the low-window arm that has no artifact.

WHAT IS MISSING
---------------
`paper/05-results-A-draft.md` (and `paper/en/05-results-A.md`) record a control arm for
the truncation-harm battery:

    "control (padding removed, correction visible): state 79-92 tokens, 6/10, 4/10,
     Fisher exact two-sided p = 0.011"

The arm was WITHDRAWN in the seventh round because it has **no artifact anywhere in the
tree** -- no rows, no script, no spend record -- and because its state size (79-92 tokens)
coincides with P26's own discarded first prototype, whose report says there was "nothing
to truncate". The tree could not distinguish a new control run from the discarded
prototype's numbers.

WHAT THIS DOES
--------------
Produces that arm for real, with the SAME item generator as P26 (`build_item`, same seed,
same shared RNG so v0/v1 are identical), changing ONE thing: the filler padding, so the
correction sits INSIDE the 512-token window instead of past it.

The comparison is then like-for-like by construction:
    high-window arm (P26 as published): states ~1969-1982 tok, correction past the clamp
    low-window arm  (this script)     : states ~ 79- 92 tok, correction inside the window

PRE-DECLARED READING
    low-window arm answers v1  -> the correction WAS read when it fit: truncation harm
    low-window arm still answers v0 -> the failure is not truncation

No artifact in `results/` is touched: the output is written to
`rerun/P26-control-low-window.json`, outside the glob that `p30_inventory.py` counts.
"""
from __future__ import annotations

import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "instrument"))
sys.path.insert(0, str(ROOT / "src" / "items"))

from deepseek_client import chat, parse_label, prompt_forced_choice  # noqa: E402
from laya_client import CHECKPOINT_CLAMP_TOKENS, LayaClient, instrument_record  # noqa: E402

# ---- load P26's OWN builder, so the items are identical by construction --------------
spec = importlib.util.spec_from_file_location(
    "p26_mod", str(ROOT / "src" / "items" / "p26_truncation_harm_valid.py"))
p26 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p26)          # its main() is guarded by __name__

SEED = 20260922
N = p26.N_ITEMS
OUT = ROOT / "rerun" / "P26-control-low-window.json"


def build_all(pad: int) -> list[dict]:
    """Same seed, same call order as p26.run(): one shared rng across items.

    Filler padding is not drawn from the rng, so v0/v1 are IDENTICAL for every pad.
    """
    old = p26.PAD_REPEATS
    p26.PAD_REPEATS = pad
    try:
        rng = random.Random(SEED)
        return [p26.build_item(i, rng) for i in range(N)]
    finally:
        p26.PAD_REPEATS = old


def main() -> int:
    client = LayaClient()
    client.ensure_up()

    # ---- choose the padding that puts the state inside the clamp, near the withdrawn
    # arm's stated 79-92 tokens. The rule is fixed BEFORE looking at any judgement.
    scan = {}
    for pad in (0, 1, 2, 3, 90):
        items = build_all(pad)
        toks = [client.count_tokens(it["state_full"]) for it in items]
        scan[pad] = {"min": min(toks), "max": max(toks),
                     "median": statistics.median(toks), "tokens": toks}
        print(f"  PAD_REPEATS={pad:>3}  state tokens {min(toks):>5}-{max(toks):<5} "
              f"median {statistics.median(toks):.0f}  "
              f"{'INSIDE' if max(toks) <= CHECKPOINT_CLAMP_TOKENS['english'] else 'PAST the clamp'}")

    inside = [p for p in (0, 1, 2, 3)
              if scan[p]["max"] <= CHECKPOINT_CLAMP_TOKENS["english"]]
    target = 85.5                       # midpoint of the withdrawn arm's 79-92
    chosen = min(inside, key=lambda p: abs(scan[p]["median"] - target))
    print(f"\n  clamp = {CHECKPOINT_CLAMP_TOKENS['english']} tokens; "
          f"padding inside the clamp: {inside}; chosen PAD_REPEATS={chosen} "
          f"(median {scan[chosen]['median']:.0f} vs withdrawn arm's 79-92)")

    items = build_all(chosen)
    rows = []
    for it in items:
        tok = client.count_tokens(it["state_full"])
        rec = {"item_id": it["item_id"], "v0": it["v0"], "v1": it["v1"],
               "state_tokens": tok,
               "cert_necessity": it["cert_necessity"],
               "cert_correction_value_appears_once":
                   it["cert_correction_value_appears_once"]}
        # FULL arm: correction present and INSIDE the window
        la = p26.ask_laya(client, it["state_full"], it["question"], it["criteria"])
        rec["full_laya"] = la
        rec["full_laya_correct"] = la["chosen"] == it["truth_key"]
        rec["full_laya_picked_pre_correction"] = la["chosen"] == it["decoy_key"]
        ll = p26.ask_llm(it["state_full"], it["question"], it["criteria"])
        rec["full_llm"] = ll
        rec["full_llm_correct"] = ll["chosen"] == it["truth_key"]
        rows.append(rec)
        print(f"  {it['item_id']} tok={tok:>4}  laya={la['chosen']} "
              f"(truth={it['truth_key']}, decoy={it['decoy_key']}) "
              f"correct={rec['full_laya_correct']} pre={rec['full_laya_picked_pre_correction']} "
              f"| llm correct={rec['full_llm_correct']}")

    toks = [r["state_tokens"] for r in rows]
    laya_correct = sum(1 for r in rows if r["full_laya_correct"])
    laya_pre = sum(1 for r in rows if r["full_laya_picked_pre_correction"])
    llm_correct = sum(1 for r in rows if r["full_llm_correct"])

    published_full = json.loads(
        (ROOT / "rerun" / "baseline" / "P26-truncation-harm-valid.json").read_text(
            encoding="utf-8"))["summary"]

    out = {
        "_generated_by": "rerun/p26_control_low_window.py (re-measurement)",
        "_instrument": instrument_record(
            "Laya HTTP 127.0.0.1:8787 (three-checkpoint loadout) + DeepSeek deepseek-flash"),
        "arm": "CONTROL: filler padding removed so the correction falls INSIDE the window",
        "why": ("the arm recorded in paper/05-results-A-draft.md ('state 79-92 tokens, "
                "6/10, 4/10, Fisher p=0.011') has no artifact anywhere in the tree and was "
                "withdrawn in round 7. This produces it for real from P26's own generator."),
        "item_generator": "src/items/p26_truncation_harm_valid.py::build_item",
        "seed": SEED,
        "padding_scan": scan,
        "chosen_pad_repeats": chosen,
        "clamp_tokens": CHECKPOINT_CLAMP_TOKENS["english"],
        "state_tokens": {"min": min(toks), "max": max(toks),
                         "median": statistics.median(toks)},
        "all_states_inside_window": max(toks) <= CHECKPOINT_CLAMP_TOKENS["english"],
        "full_arm_laya": {"n": len(rows), "answered_post_correction": laya_correct,
                          "answered_pre_correction": laya_pre,
                          "accuracy": round(laya_correct / len(rows), 4)},
        "full_arm_llm": {"n": len(rows), "correct": llm_correct,
                         "accuracy": round(llm_correct / len(rows), 4)},
        "high_window_reference_P26_published": {
            "state_tokens": published_full["state_tokens"],
            "full_arm_laya_answered_post_correction":
                published_full["FULL_arm_correction_present"]["laya"]["correct"],
            "full_arm_laya_answered_pre_correction":
                published_full["laya_picked_pre_correction_value_in_full_arm"],
            "n": published_full["n_items"],
        },
        "withdrawn_claim_in_paper": {"state_tokens": "79-92", "answered_post": 6,
                                     "answered_pre": 4, "fisher_p_two_sided": 0.011},
        "rows": rows,
        "verdict": None,
    }

    # Fisher exact, two-sided, on post-correction answers: low window vs published high window
    def fisher2x2(a, b, c, d) -> float:
        from math import comb
        n = a + b + c + d
        r1, r2, c1 = a + b, c + d, a + c

        def p_of(x):
            return (comb(r1, x) * comb(r2, c1 - x)) / comb(n, c1)
        p0 = p_of(a)
        lo = max(0, c1 - r2)
        hi = min(r1, c1)
        return round(sum(p_of(x) for x in range(lo, hi + 1) if p_of(x) <= p0 + 1e-12), 6)

    hi_n = published_full["n_items"]
    hi_post = published_full["FULL_arm_correction_present"]["laya"]["correct"]
    p = fisher2x2(laya_correct, len(rows) - laya_correct, hi_post, hi_n - hi_post)
    out["fisher_exact_two_sided_low_vs_high_window"] = p
    out["verdict"] = (
        f"CONTROL PRODUCED. With the correction INSIDE the window "
        f"({min(toks)}-{max(toks)} tokens vs a {CHECKPOINT_CLAMP_TOKENS['english']}-token "
        f"clamp) Laya answers the post-correction value on {laya_correct}/{len(rows)} items "
        f"and the pre-correction value on {laya_pre}/{len(rows)}. In the published "
        f"high-window arm ({published_full['state_tokens']['min']}-"
        f"{published_full['state_tokens']['max']} tokens) it answered post-correction "
        f"{hi_post}/{hi_n}. The withdrawn paper arm claimed 6/10 and 4/10 at 79-92 tokens; "
        f"this re-run gives {laya_correct}/{len(rows)} and {laya_pre}/{len(rows)} "
        f"(Fisher two-sided p = {p} against the high-window arm)."
    )
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== VERDICT ===")
    print(out["verdict"])
    print(f"\nLLM calls this script: {2 * len(rows)}")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
