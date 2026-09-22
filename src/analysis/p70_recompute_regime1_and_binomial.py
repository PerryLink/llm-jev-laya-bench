"""Make the two numbers ERRATA 10.1 items 2 and 3 need RECOMPUTABLE, before they are printed.

WHY THIS EXISTS
---------------
Two paper-text defects in `results/ERRATA.md` section 10 cannot be fixed by editing prose,
because the replacement text needs numbers that no artifact currently carries:

  (1) ERRATA 10.1 item 3 -- section 7.2 never mentions P14's PROSE arm. That arm records
      LLM 46/48, one judge-only item, and `delta_catch = +0.0435`: the ONE measurable
      Delta_catch in regime 1, and it is POSITIVE. Printing a signed point estimate with a
      denominator of TWO (the prose arm's LLM errs on 2 of 48 items) without its interval
      would replace one unverifiable claim with another. The project's own rule is that an
      interval belongs next to any point estimate -- so the interval has to exist, in an
      artifact, before the sentence does.

  (2) ERRATA 10.1 item 2 -- the one-sided p-values 0.052 / 0.043 / 0.103 in section 8.6.1(b)
      are NORMAL APPROXIMATIONS and are not labelled as such. Labelling them is not enough
      on its own: the label is only checkable if the exact binomial lower tail is computed
      from the same cells, by a stored script, next to the approximation. Both conventions
      must appear side by side, with the same n and the same baseline, or the reader is
      again being asked to trust a number they cannot re-derive.

WHAT IT DOES
------------
Extends `src/analysis/p28_recompute_all_stats.py` -- the project's single recomputation
script, whose docstring promises "every interval and exact test the paper prints" -- with:

  * a REGIME 1 block covering BOTH arms of `P14-llm-arm-full.json` (the forced-choice arm,
    which has ZERO LLM errors and therefore no defined Delta_catch, and the prose arm, which
    has two), carrying Wald + Newcombe intervals for the prose arm;
  * per-draw exact one-sample binomial lower tails (and the normal approximation) for the
    comparison of `P(judge correct | LLM wrong)` against the judge's own marginal accuracy,
    which is what 0.052 / 0.043 / 0.103 were silently computing.

The edit is ANCHORED: each insertion point is matched literally and the script exits
non-zero if any anchor is missing, so a silent no-op is impossible. It then RUNS p28 and
asserts the values the paper is about to print, so a drift in any input artifact fails here
rather than in the manuscript.
"""

from __future__ import annotations

# Paths resolve through bench_env, which locates the repository root by walking
# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,
# ...). Run `python bench_env.py` to print what was resolved.
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
import subprocess
import sys
from pathlib import Path

SRC = ROOT / "src" / "analysis" / "p28_recompute_all_stats.py"
R = ROOT / "results"

# ---------------------------------------------------------------- anchored insertions

# 1. an exact one-sample binomial lower tail + its normal approximation.
ANCHOR_FUNCS = '''def phi_2x2(a: int, b: int, c: int, d: int) -> float:'''
INSERT_FUNCS = '''def binomial_lower_tail(x: int, n: int, p0: float) -> float:
    """EXACT one-sided lower tail P(X <= x) for X ~ Binomial(n, p0).

    This is the convention the paper must name. The value 0.052 printed in section 8.6.1(b)
    is NOT this number -- it is the normal approximation below -- and the two differ by more
    than 40% relative on the same cells, which is exactly why ERRATA 10.1 item 2 requires the
    convention to be stated or both values to be reported.
    """
    if n == 0:
        return float("nan")
    return sum(math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(x + 1))


def binomial_lower_tail_normal(x: int, n: int, p0: float) -> float:
    """The NORMAL APPROXIMATION to the same tail: Phi((p_hat - p0) / sqrt(p0(1-p0)/n)).

    Kept only so the paper can show what convention produced the 0.052 / 0.043 / 0.103 it
    printed before this script existed. No continuity correction -- adding one moves the
    three values to 0.061 / 0.050 / 0.117, i.e. it is a third convention again, and the
    drafts' values are reproduced by the uncorrected form.
    """
    if n == 0:
        return float("nan")
    p_hat = x / n
    se = math.sqrt(p0 * (1 - p0) / n)
    z = (p_hat - p0) / se
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def phi_2x2(a: int, b: int, c: int, d: int) -> float:'''

# 2. report_block must survive an arm with ZERO failures on one side, and must accept the
#    judge column name, because P14's paired rows use `typed_correct`.
ANCHOR_BLOCK = '''def report_block(label: str, rs: list[dict]) -> dict:
    a, b, c, d, x1, n1, x2, n2 = contrast(rs)
    p1, p2 = x1 / n1, x2 / n2
    w = wald_diff(x1, n1, x2, n2)
    nc = newcombe_diff(x1, n1, x2, n2)
    return {
        "label": label, "n": len(rs), "table": {"both": a, "llm_only": b,
                                                "judge_only": c, "neither": d},
        "p_judge_given_llm_wrong": round(p1, 4), "n_wrong_arm": n1,
        "p_judge_given_llm_right": round(p2, 4), "n_right_arm": n2,
        "delta_catch": round(p1 - p2, 4),
        "wald": [round(v, 4) for v in w],
        "newcombe": [round(v, 4) for v in nc],
        "wald_excludes_0": w[1] < 0 or w[0] > 0,
        "newcombe_excludes_0": nc[1] < 0 or nc[0] > 0,
        "fisher_p": round(fisher_two_sided(a, b, c, d), 4),
        "phi": round(phi_2x2(a, b, c, d), 4),
        "max_achievable_p1_upper_bound": (round(clopper_pearson_upper(x1, n1), 4)
                                          if x1 == 0 else None),
    }'''
INSERT_BLOCK = '''def report_block(label: str, rs: list[dict], judge: str = "laya_correct") -> dict:
    """One draw's paired contrast, with every interval the paper may want.

    DEGENERATE ARMS ARE A REAL CASE, NOT AN EDGE CASE: P14's forced-choice arm has the LLM
    correct on 48/48 items, so `n_wrong_arm` is 0 and Delta_catch is UNDEFINED rather than
    zero. Emitting 0.0 there would silently convert "unmeasurable" into "no effect" -- the
    exact substitution section 7.5 warns against -- so the conditional fields become null.
    """
    a, b, c, d, x1, n1, x2, n2 = contrast(rs, llm="llm_correct", judge=judge)
    out = {
        "label": label, "n": len(rs), "table": {"both": a, "llm_only": b,
                                                "judge_only": c, "neither": d},
        "n_wrong_arm": n1, "n_right_arm": n2,
        "fisher_p": round(fisher_two_sided(a, b, c, d), 4),
        "phi": round(phi_2x2(a, b, c, d), 4),
    }
    if n1 == 0 or n2 == 0:
        out.update({
            "p_judge_given_llm_wrong": None, "p_judge_given_llm_right": None,
            "delta_catch": None, "wald": None, "newcombe": None,
            "wald_excludes_0": None, "newcombe_excludes_0": None,
            "max_achievable_p1_upper_bound": None,
            "delta_catch_undefined_because": (
                "one arm of the 2x2 is empty (n_wrong_arm=%d, n_right_arm=%d), so the "
                "conditional probability it is conditioned on does not exist" % (n1, n2)),
        })
        return out
    p1, p2 = x1 / n1, x2 / n2
    w = wald_diff(x1, n1, x2, n2)
    nc = newcombe_diff(x1, n1, x2, n2)
    # the judge's own MARGINAL accuracy on this battery: the independence baseline that
    # section 8.6.1(b) compares the conditional rate against. Derived, never transcribed.
    marginal = (a + c) / len(rs)
    out.update({
        "p_judge_given_llm_wrong": round(p1, 4),
        "p_judge_given_llm_right": round(p2, 4),
        "delta_catch": round(p1 - p2, 4),
        "wald": [round(v, 4) for v in w],
        "newcombe": [round(v, 4) for v in nc],
        "wald_excludes_0": w[1] < 0 or w[0] > 0,
        "newcombe_excludes_0": nc[1] < 0 or nc[0] > 0,
        "max_achievable_p1_upper_bound": (round(clopper_pearson_upper(x1, n1), 4)
                                          if x1 == 0 else None),
        "judge_marginal_accuracy": round(marginal, 4),
        "vs_marginal_one_sided": {
            "x": x1, "n": n1, "baseline": round(marginal, 4),
            "exact_binomial_lower_tail": round(binomial_lower_tail(x1, n1, marginal), 4),
            "normal_approximation": round(binomial_lower_tail_normal(x1, n1, marginal), 4),
            "_note": ("both conventions are reported because the paper printed the normal "
                      "approximation without naming it (ERRATA 10.1 item 2); no continuity "
                      "correction is applied to the approximation"),
        },
    })
    return out'''

# 3. the regime-1 block itself, printed before regime 2 and stored as `regime1`.
ANCHOR_MAIN = '''    print("=" * 78)
    print("REGIME 2 -- P15 record + P15b r1..r3   (77-class intent battery)")'''
INSERT_MAIN = '''    print("=" * 78)
    print("REGIME 1 -- P14, BOTH arms of the SAME 48-item battery")
    print("=" * 78)
    print("The forced-choice arm has ZERO LLM errors, so its Delta_catch is UNDEFINED; the")
    print("prose arm has two, and its Delta_catch is POSITIVE. Section 7.2 reported only the")
    print("first arm and declared the regime unmeasurable (ERRATA 10.1 item 3).\\n")
    p14 = json.loads((R / "P14-llm-arm-full.json").read_text(encoding="utf-8"))
    reg1 = []
    print(f"{'arm':26s} {'delta':>8s} {'Wald':>20s} {'Newcombe':>20s} "
          f"{'Fisher':>8s} {'phi':>7s}")
    for key, label in (("complementarity", "P14 forced-choice arm"),
                       ("complementarity_prose_arm", "P14 prose arm")):
        arm = p14[key]
        blk = report_block(label, arm["detail"], judge="typed_correct")
        # the recomputation must agree with the artifact's own recorded arithmetic, or the
        # paper would be quoting two different numbers for one measurement
        assert blk["table"]["both"] == arm["confusion"]["both_correct"], label
        assert blk["table"]["llm_only"] == arm["confusion"]["llm_only_correct"], label
        assert blk["table"]["judge_only"] == arm["confusion"]["typed_only_correct"], label
        assert blk["table"]["neither"] == arm["confusion"]["neither_correct"], label
        if arm["delta_catch"] is None:
            assert blk["delta_catch"] is None, label
        else:
            assert abs(blk["delta_catch"] - arm["delta_catch"]) < 5e-5, \\
                f"{label}: {blk['delta_catch']} vs artifact {arm['delta_catch']}"
        reg1.append(blk)
        w, nc = blk["wald"], blk["newcombe"]
        if w is None:
            print(f"{label:26s} {'undefined':>8s} {'--':>20s} {'--':>20s} "
                  f"{blk['fisher_p']:>8.4f} {blk['phi']:>7.3f}")
        else:
            print(f"{label:26s} {blk['delta_catch']:>8.4f} "
                  f"[{w[0]:>7.3f},{w[1]:>7.3f}] [{nc[0]:>7.3f},{nc[1]:>7.3f}] "
                  f"{blk['fisher_p']:>8.4f} {blk['phi']:>7.3f}")
    out["regime1"] = reg1

    print("\\n" + "=" * 78)
    print("REGIME 2 -- P15 record + P15b r1..r3   (77-class intent battery)")'''


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    problems = []

    if "def binomial_lower_tail(" not in src:
        if ANCHOR_FUNCS not in src:
            problems.append("anchor for the binomial helpers is missing")
        else:
            src = src.replace(ANCHOR_FUNCS, INSERT_FUNCS, 1)

    # SENTINEL CHOICE MATTERS: `judge: str = "laya_correct"` also occurs in `contrast()`, so
    # using it here made the first run skip this patch while reporting success -- a guard that
    # tests the wrong string is a fix that silently does nothing. The sentinel must be unique
    # to the definition being replaced.
    if "def report_block(label: str, rs: list[dict], judge:" not in src:
        if ANCHOR_BLOCK not in src:
            problems.append("anchor for report_block is missing")
        else:
            src = src.replace(ANCHOR_BLOCK, INSERT_BLOCK, 1)

    if 'out["regime1"]' not in src:
        if ANCHOR_MAIN not in src:
            problems.append("anchor for the regime-2 banner is missing")
        else:
            src = src.replace(ANCHOR_MAIN, INSERT_MAIN, 1)

    if problems:
        for p in problems:
            print(f"  MISS  {p}")
        print("\\nno edit written: an anchor did not match, and guessing is how a fix "
              "silently does nothing")
        return 1

    SRC.write_text(src, encoding="utf-8")
    print(f"patched {SRC.relative_to(ROOT)}")

    r = subprocess.run([sys.executable, str(SRC)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(ROOT))
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        return 1
    for line in r.stdout.splitlines():
        if "REGIME 1" in line or "arm" in line or "undefined" in line:
            print("   ", line)

    doc = json.loads((R / "P28-recomputed-statistics.json").read_text(encoding="utf-8"))
    reg1 = doc["regime1"]
    fc, prose = reg1[0], reg1[1]

    checks = [
        ("forced-choice arm has no defined delta",
         fc["delta_catch"] is None and fc["n_wrong_arm"] == 0),
        ("prose arm confusion is 21/25/1/1",
         [prose["table"][k] for k in ("both", "llm_only", "judge_only", "neither")]
         == [21, 25, 1, 1]),
        ("prose arm Delta_catch is +0.0435 (POSITIVE, and the regime-1 only measurable one)",
         abs(prose["delta_catch"] - 0.0435) < 5e-5),
        ("prose arm denominator is 2 LLM errors -- the reason its interval is wide",
         prose["n_wrong_arm"] == 2),
    ]
    for label, good in checks:
        print(f"  {'ok  ' if good else 'FAIL'}  {label}")

    p_vals = doc["holm"]["regime3"]["p_values"]
    exact = [b["vs_marginal_one_sided"]["exact_binomial_lower_tail"]
             for b in doc["regime3"][1:]]
    normal = [b["vs_marginal_one_sided"]["normal_approximation"]
              for b in doc["regime3"][1:]]
    print(f"\\n  exact binomial lower tails (r1/r2/r3): {exact}")
    print(f"  normal approximations         (r1/r2/r3): {normal}")
    expected_exact = [0.076, 0.061, 0.149]
    expected_normal = [0.052, 0.043, 0.103]
    ok_exact = all(abs(a - b) <= 0.001 for a, b in zip(exact, expected_exact))
    ok_normal = all(abs(a - b) <= 0.001 for a, b in zip(normal, expected_normal))
    print(f"  {'ok  ' if ok_exact else 'FAIL'}  exact tails match the audited values "
          f"{expected_exact}")
    print(f"  {'ok  ' if ok_normal else 'FAIL'}  approximations reproduce the printed "
          f"{expected_normal} (so the unlabelled numbers are now traceable)")
    print(f"  (Fisher two-sided, a different test, is {p_vals} -- not to be conflated)")

    ok = all(g for _, g in checks) and ok_exact and ok_normal
    print("\\nOK" if ok else "\\nFAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
