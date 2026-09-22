"""K2 now verifies the paper's p-values against the PINNED chain copies, and K11 guards them.

WHY K2 HAD TO CHANGE, AND WHY IT MUST NOT SIMPLY BE RELAXED
----------------------------------------------------------
K2 was red because the manuscript prints exact binomial tails of 0.076 / 0.061 / 0.149 while the
LIVE `P22b-fixed-r*.json` (regenerated at 23:33-23:35 with a changed generator) produce
0.443 / 0.330 / 0.413. The author's ruling -- Option A -- is that the PUBLISHED battery is the
measurement of record, because it is the measurement of the protocol the paper describes, and
that the re-measurement is disclosed in the body as a follow-up (p90).

That ruling makes the check's object precise: the paper's numbers must match the record they cite.
So K2 now recomputes from `results/_superseded/P22b-fixed-r*.json.pre-repair` and
`rerun/baseline/P22b-fixed-r*.json`, asserts the two copies are byte-identical (otherwise the
citation names two different things), and requires the manuscript to print those values WITH the
convention labelled. It also requires the disclosure itself to be present, so the check cannot go
green by deleting the follow-up.

K11 is new and guards the citation's integrity: the six pinned files must exist and pair up
byte-for-byte. If a future re-run overwrites one side, K11 fails and says so -- which is the
defect that started this whole thread.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

VERIFY = ROOT / "paper" / "verify_all.py"

OLD_K2 = '''    # ---- K2: the p-value convention is named, and both conventions are present -----------
    p28 = artifact("P28-recomputed-statistics.json")
    exact = [b["vs_marginal_one_sided"]["exact_binomial_lower_tail"]
             for b in p28.get("regime3", [])[1:]]
    normal = [b["vs_marginal_one_sided"]["normal_approximation"]
              for b in p28.get("regime3", [])[1:]]
    if not exact or not normal:
        fail("K2 the one-sided p-values name their convention",
             "P28 has no vs_marginal_one_sided block -- re-run p28_recompute_all_stats.py")
    else:
        want = [f"{v:.3f}" for v in exact]
        if "正态近似" in t and all(w in t for w in want) and "精确二项" in t:
            ok("K2 the one-sided p-values name their convention",
               f"normal approximation {['%.3f' % v for v in normal]} labelled; exact binomial "
               f"lower tails {want} printed")
        else:
            fail("K2 the one-sided p-values name their convention",
                 f"missing the label or the exact tails {want}")'''

NEW_K2 = '''    # ---- K2: the one-sided p-values are labelled AND match the record the paper cites -----
    #
    # THE OBJECT MATTERS (this check was red for a day, on purpose). The paper reports the
    # PUBLISHED chain battery -- the measurement of the protocol the text describes. That
    # battery's live artifacts were later regenerated with a changed option-set policy, so the
    # LIVE files no longer reproduce the printed numbers, while the pinned pre-rerun copies do.
    # K2 therefore recomputes from the pinned copies, which the disclosure in section 8.6.1
    # names, and requires the disclosure to be present: a check that could be made green by
    # deleting the follow-up would be worse than no check.
    import hashlib as _hash

    def _pinned(i: int):
        a = R / "_superseded" / f"P22b-fixed-r{i}.json.pre-repair"
        b = ROOT / "rerun" / "baseline" / f"P22b-fixed-r{i}.json"
        return a, b

    def _binomial_lower(x: int, n: int, p0: float) -> float:
        import math as _math
        return sum(_math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(x + 1))

    def _binomial_normal(x: int, n: int, p0: float) -> float:
        import math as _math
        se = _math.sqrt(p0 * (1 - p0) / n)
        return 0.5 * (1 + _math.erf(((x / n - p0) / se) / _math.sqrt(2)))

    pinned_exact, pinned_normal, mismatched = [], [], []
    for i in (1, 2, 3):
        a, b = _pinned(i)
        if not (a.exists() and b.exists()):
            mismatched.append(f"r{i} pinned copy missing")
            continue
        if _hash.sha256(a.read_bytes()).hexdigest() != _hash.sha256(b.read_bytes()).hexdigest():
            mismatched.append(f"r{i} the two pinned copies differ")
            continue
        rows = _json.loads(a.read_text(encoding="utf-8"))["rows"]
        both = sum(1 for r in rows if r["llm_correct"] and r["laya_correct"])
        jonly = sum(1 for r in rows if not r["llm_correct"] and r["laya_correct"])
        llm_wrong = sum(1 for r in rows if not r["llm_correct"])
        marginal = (both + jonly) / len(rows)
        pinned_exact.append(_binomial_lower(jonly, llm_wrong, marginal))
        pinned_normal.append(_binomial_normal(jonly, llm_wrong, marginal))

    if mismatched or len(pinned_exact) != 3:
        fail("K2 the one-sided p-values match the pinned record they cite",
             f"pinned copies unusable: {mismatched}")
    else:
        want_exact = [f"{v:.3f}" for v in pinned_exact]
        want_normal = [f"{v:.3f}" for v in pinned_normal]
        labelled = "正态近似" in t and "精确二项" in t
        printed = all(w in t for w in want_exact)
        disclosed = "重测" in t and "P22b-fixed-r1..r3.json.pre-repair" in t
        if labelled and printed and disclosed:
            ok("K2 the one-sided p-values match the pinned record they cite",
               f"exact binomial tails {want_exact} and normal approximations {want_normal} "
               f"printed with the convention labelled; re-measurement disclosed against the "
               f"pinned copies")
        else:
            fail("K2 the one-sided p-values match the pinned record they cite",
                 f"labelled={labelled} printed={printed} disclosed={disclosed}; "
                 f"expected exact {want_exact}, normal {want_normal}")'''

NEW_K11 = '''
    # ---- K11: the pinned chain copies still exist and still pair up ------------------------
    import hashlib as _hash11
    pairs, bad = [], []
    for i in (1, 2, 3):
        a = R / "_superseded" / f"P22b-fixed-r{i}.json.pre-repair"
        b = ROOT / "rerun" / "baseline" / f"P22b-fixed-r{i}.json"
        if not (a.exists() and b.exists()):
            bad.append(f"r{i} missing")
            continue
        ha = _hash11.sha256(a.read_bytes()).hexdigest()[:12]
        hb = _hash11.sha256(b.read_bytes()).hexdigest()[:12]
        if ha != hb:
            bad.append(f"r{i} {ha} != {hb}")
        else:
            pairs.append(ha)
    if bad:
        fail("K11 the pinned chain copies are intact and identical",
             f"{bad} -- the published battery's record has been disturbed; the paper cites it")
    else:
        ok("K11 the pinned chain copies are intact and identical",
           f"3 pairs byte-identical: {pairs}")
'''


def main() -> int:
    src = VERIFY.read_text(encoding="utf-8")
    problems = []
    changed = 0

    if "the pinned record they cite" in src:
        print("  ok    K2 already verifies against the pinned copies")
    elif OLD_K2 in src:
        src = src.replace(OLD_K2, NEW_K2, 1)
        changed += 1
        print("  ok    K2 rewritten to recompute from the pinned pre-rerun copies")
    else:
        problems.append("K2's block is not in the expected form")

    if "K11 the pinned chain copies are intact" in src:
        print("  ok    K11 is already present")
    elif "    # ---- K10: 0.912 survives only inside its retraction" in src:
        src = src.replace("    # ---- K10: 0.912 survives only inside its retraction",
                          NEW_K11 + "\n    # ---- K10: 0.912 survives only inside its retraction", 1)
        changed += 1
        print("  ok    K11 added (pinned-copy integrity)")
    else:
        problems.append("anchor for K11 is missing")

    if problems:
        for p in problems:
            print(f"  MISS  {p}")
        return 1
    if changed:
        VERIFY.write_text(src, encoding="utf-8")
        print(f"  patched {VERIFY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
