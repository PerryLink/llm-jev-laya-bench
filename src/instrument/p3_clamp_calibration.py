"""PRE-WORK ITEM 3 (DECISIONS.md): per-checkpoint clamp calibration.

WHY THE CLAMP IS NOT A CONSTANT
-------------------------------
R13 measured the english checkpoint and reported a 512-token clamp, then treated 512
as a global property of Laya. A main-session probe (R8 s1) showed that is an
overgeneralisation: the clamp is PER CHECKPOINT. english clamps at 512 while
multilingual and typed-decisions clamp at 1024. Any design that hard-codes one W is
therefore wrong for two of the three checkpoints, and R15's integrity(t)=1[tokens<=W]
curve needs one W per checkpoint.

WHAT THIS MEASURES, per checkpoint, without needing a tokenizer estimate:
  * the character count at which `input_tokens_padded` STOPS growing  (= real clamp)
  * the character count at which `truncated` FIRST fires               (= reported clamp)
  * the gap between them = the UNWARNED DAMAGED INTERVAL

The gap is the clean instrument-honesty statistic: inside it the tail has already
been discarded while every self-reported field still says the request is fine. It is
measurable by scanning characters and reading two observable fields, so it depends on
no estimate of B, N, or the tokenizer.

The freeze check is included because it is the sidecar-independent proof that the
tail is being ignored: once the clamp binds, further text cannot change the answer,
so the score becomes bit-identical across increasing state size.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument"))
from laya_client import LayaClient, CHECKPOINT_CLAMP_TOKENS, instrument_record  # noqa: E402

RESULTS = Path(r"D:\Projects\llm-jev-laya-bench\results")
RESULTS.mkdir(parents=True, exist_ok=True)

DECOY = "The vault access code is AAA-1111."
CORRECTION = " Correction: the vault access code is now ZQX-4471."
FILLER = ("Quarterly logistics review. The warehouse processed routine shipments "
          "and filed standard compliance paperwork. ")

# Coarse-then-fine: the coarse pass locates the neighbourhood, the fine pass brackets
# it to a single filler repetition. Character counts are exact by construction.
COARSE = [100, 1000, 2000, 2400, 2600, 2800, 3000, 3100, 3200, 3400, 4000,
          5000, 6000, 7000, 8000, 10000, 12000, 16000]
FINE = [3050, 3080, 3110, 3140, 3170, 3200, 3230, 3260, 3290]


def make_state(n_chars: int) -> str:
    """DECOY + filler + CORRECTION, padded to about n_chars. Correction stays LAST
    so that tail truncation removes the deciding evidence."""
    budget = max(0, n_chars - len(DECOY) - len(CORRECTION))
    reps = budget // len(FILLER)
    return DECOY + FILLER * reps + CORRECTION


def probe(client: LayaClient, state: str, checkpoint: str) -> dict:
    q = {
        "code": {
            "type": "noul",
            "instructions": ("According to the state, is the vault access code "
                             "ZQX-4471?"),
            "criteria": {
                "true": "the state gives ZQX-4471 as the vault access code",
                "false": "the state does not give ZQX-4471 as the vault access code",
            },
        }
    }
    resp = client.ask(state, q, checkpoint=checkpoint)
    ans = resp["answers"]["code"]
    usage = resp.get("usage") or {}
    return {
        "chars": len(state),
        "in_pad": usage.get("input_tokens_padded"),
        "noul": LayaClient.noul_p_true(ans),
        "truncated": bool(resp.get("truncated")),
        "warnings": resp.get("warnings") or [],
    }


def calibrate(checkpoint: str) -> dict:
    client = LayaClient()
    client.ensure_up()
    rows: list[dict] = []
    seen: set[int] = set()
    for n in COARSE + FINE:
        s = make_state(n)
        if len(s) in seen:
            continue
        seen.add(len(s))
        try:
            rows.append(probe(client, s, checkpoint))
        except Exception as exc:  # record, never silently drop
            rows.append({"chars": len(s), "error": str(exc)[:200]})
    rows.sort(key=lambda r: r["chars"])

    ok = [r for r in rows if "error" not in r]
    clamp_tokens = max((r["in_pad"] or 0) for r in ok) if ok else None

    # Clamp onset := the FIRST character count at which the pad has REACHED the cap.
    # (An earlier version searched for a consecutive equal-pad pair, which returns the
    # LAST equal pair — it reported 3193/9964/7966 and mis-stated multilingual's onset
    # as 9964 when the pad had already reached 1024 by 7966. Fixed here.)
    clamp_chars = next((r["chars"] for r in ok if r["in_pad"] == clamp_tokens), None)

    # Freeze onset := the first char count whose score equals every later score.
    # This is the sidecar-independent proof that the tail stopped being read.
    freeze_chars = None
    for i, r in enumerate(ok):
        if i + 1 < len(ok) and all(abs(x["noul"] - r["noul"]) < 1e-9 for x in ok[i + 1:]):
            freeze_chars = r["chars"]
            break

    # Reported clamp onset := first char count at which `truncated` fires.
    trunc_chars = next((r["chars"] for r in ok if r["truncated"]), None)

    # Freeze check, and it must be measured from the freeze onset itself rather than
    # from the clamp onset. The two differ by one grid step: `clamp_chars` is the last
    # character count whose pad was still GROWING (it equals the cap only because the
    # final write reached it), so including that row adds a still-live score and makes
    # the freeze test report False even when the output is frozen from the next step on.
    post = [r for r in ok if freeze_chars is not None and r["chars"] >= freeze_chars]
    frozen = (len({round(r["noul"], 6) for r in post}) == 1) if len(post) >= 2 else None

    return {
        "checkpoint": checkpoint,
        "expected_clamp_tokens": CHECKPOINT_CLAMP_TOKENS[checkpoint],
        "measured_clamp_tokens": clamp_tokens,
        "real_clamp_onset_chars": clamp_chars,
        "truncated_first_fires_chars": trunc_chars,
        # POSITIVE = the flag lags the real damage (silent window).
        # NEGATIVE = the flag fires thousands of chars before any damage (false positive).
        "flag_error_chars": (
            (trunc_chars - clamp_chars)
            if (trunc_chars is not None and clamp_chars is not None) else None),
        "freeze_onset_chars": freeze_chars,
        "freeze_aligns_with_clamp": (
            abs((freeze_chars or 0) - (clamp_chars or 0)) <= 200
            if (freeze_chars is not None and clamp_chars is not None) else None),
        "output_frozen_after_clamp": frozen,
        "post_clamp_distinct_scores": sorted({round(r["noul"], 6) for r in post}),
        "restart_count": client.restart_count,
        "cold_start_ms": client.cold_start_ms,
        "calls": client.call_count,
        "rows": rows,
    }


if __name__ == "__main__":
    out = {}
    for cp in ("english", "multilingual", "typed-decisions"):
        print(f"\n=== {cp} ===")
        res = calibrate(cp)
        out[cp] = res
        print(f"  measured clamp tokens : {res['measured_clamp_tokens']} "
              f"(expected {res['expected_clamp_tokens']})")
        print(f"  real clamp onset      : {res['real_clamp_onset_chars']} chars")
        print(f"  'truncated' first     : {res['truncated_first_fires_chars']} chars")
        print(f"  FLAG ERROR            : {res['flag_error_chars']} chars "
              f"(positive = flag lags the damage; negative = false positive)")
        print(f"  freeze onset          : {res['freeze_onset_chars']} chars "
              f"(aligns with clamp: {res['freeze_aligns_with_clamp']})")
        print(f"  output frozen?        : {res['output_frozen_after_clamp']} "
              f"(distinct post-clamp scores: {res['post_clamp_distinct_scores'][:6]})")

    # AUDIT FIX (finding M-5/F-7): this file is the source of the paper's headline
    # clamp number but previously carried NO instrument record at all, and no freeze
    # file recorded the launch loadout -- even though the clamp is a function of
    # (loadout x queried checkpoint). It now records both.
    out["_instrument"] = instrument_record(
        entry_point="HTTP 127.0.0.1:8787 (Path A)")
    out["_note"] = ("measured_clamp_tokens is PER (loadout x checkpoint). All three "
                    "checkpoints were queried against the SAME three-checkpoint "
                    "loadout, so english=512 while multilingual/typed-decisions=1024 "
                    "is not explained by the checkpoint alone: P16 and P18 show english "
                    "ALONE clamps at 1024, i.e. english's clamp is LOADOUT-dependent "
                    "while the other two were only ever measured at 1024. Reporting "
                    "either factor without the other is incomplete.")
    path = RESULTS / "P3-clamp-calibration.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwritten: {path}")
