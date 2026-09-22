"""Recompute every interval and exact test the paper prints, from the artifacts.

WHY THIS EXISTS
---------------
An audit established that none of the paper's inferential statistics is reproducible from a
stored script: `src/` contains no Wald / Newcombe / Wilson / Clopper-Pearson / CMH /
permutation / bootstrap / AUC code at all. Every interval in the drafts was computed ad hoc
during an audit, in a throwaway interpreter session. Two consequences followed, and both
were real:

  1. Two cells of the P15/P15b Newcombe row did not match any Newcombe interval for the data
     they claimed to describe -- one of them was byte-identical to that column's WALD value,
     i.e. a relabelled number.
  2. A Fisher p of 0.0487 was called significant while the paper's own pre-specified rule
     (`04-method-draft.md`: primary family corrected by Holm) requires 0.05/3 = 0.0167.

This script makes every such number recomputable. It reads the artifacts, computes the
statistics with the standard library only (the venv has no scipy), and prints a table the
paper's numbers can be checked against line by line.

Convention: `p1` is P(judge correct | generator WRONG), `p2` is P(judge correct |
generator RIGHT); delta_catch = p1 - p2. That conditional, unpaired contrast is the paper's
estimand -- McNemar tests a different hypothesis and is deliberately NOT used here.
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
import math
import statistics
from pathlib import Path


R = ROOT / "results"
Z = 1.959963985


# --------------------------------------------------------------------------- intervals
def wilson(x: int, n: int, z: float = Z) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def wald_diff(x1: int, n1: int, x2: int, n2: int,
              z: float = Z) -> tuple[float, float]:
    """Unpaired Wald interval for p1 - p2."""
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return (p1 - p2 - z * se, p1 - p2 + z * se)


def newcombe_diff(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    """Newcombe method 10 (MOVER over Wilson score intervals).

    Chosen because it stays valid when a cell is ZERO -- which is exactly this project's
    case (several draws have 0 judges correct among the generator's failures), where Wald
    collapses to a spuriously narrow interval.
    """
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    lo = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return (lo, hi)


def clopper_pearson_upper(x: int, n: int, alpha: float = 0.05) -> float:
    """Exact one-sided upper bound -- the honest bound when the count is ZERO."""
    if x == 0:
        return 1 - alpha ** (1 / n)
    if x == n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):                      # bisect on the Beta tail
        mid = (lo + hi) / 2
        tail = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i)
                   for i in range(x + 1))
        if tail > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact two-sided Fisher on [[a,b],[c,d]] -- standard library only."""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def prob(x: int) -> float:
        return (math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1))

    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    obs = prob(a)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= obs * (1 + 1e-9)))


def binomial_lower_tail(x: int, n: int, p0: float) -> float:
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


def phi_2x2(a: int, b: int, c: int, d: int) -> float:
    num = a * d - b * c
    den = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    return num / den if den else float("nan")


def auc(scores: list[float], labels: list[int]) -> float:
    """Rank-based AUC with midranks for ties."""
    pairs = sorted(zip(scores, labels))
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    pos = sum(1 for _, y in pairs if y == 1)
    neg = len(pairs) - pos
    rsum = sum(r for r, (_, y) in zip(ranks, pairs) if y == 1)
    return (rsum - pos * (pos + 1) / 2) / (pos * neg)


# --------------------------------------------------------------------------- loading
def rows(name: str) -> list[dict]:
    return json.loads((R / name).read_text(encoding="utf-8"))["rows"]


def contrast(rs: list[dict], llm: str = "llm_correct", judge: str = "laya_correct"):
    a = sum(1 for r in rs if r[llm] and r[judge])          # both
    b = sum(1 for r in rs if r[llm] and not r[judge])      # llm only
    c = sum(1 for r in rs if not r[llm] and r[judge])      # judge only
    d = sum(1 for r in rs if not r[llm] and not r[judge])  # neither
    n1 = c + d                                             # llm WRONG
    n2 = a + b                                             # llm RIGHT
    return a, b, c, d, c, n1, a, n2


def report_block(label: str, rs: list[dict], judge: str = "laya_correct") -> dict:
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
    return out


def main() -> None:
    out: dict = {"_note": __doc__.strip().split("\n")[0]}

    print("=" * 78)
    print("REGIME 1 -- P14, BOTH arms of the SAME 48-item battery")
    print("=" * 78)
    print("The forced-choice arm has ZERO LLM errors, so its Delta_catch is UNDEFINED; the")
    print("prose arm has two, and its Delta_catch is POSITIVE. Section 7.2 reported only the")
    print("first arm and declared the regime unmeasurable (ERRATA 10.1 item 3).\n")
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
            assert abs(blk["delta_catch"] - arm["delta_catch"]) < 5e-5, \
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

    print("\n" + "=" * 78)
    print("REGIME 2 -- P15 record + P15b r1..r3   (77-class intent battery)")
    print("=" * 78)
    blocks = []
    reg2 = [("P15-complementarity-strong-regime.json", "P15 record (unpinned)")] + \
           [(f"P15b-rep-r{i}.json", f"P15b r{i} (temperature=0)") for i in (1, 2, 3)]
    print(f"{'draw':26s} {'delta':>8s} {'Wald':>20s} {'Newcombe':>20s} "
          f"{'Fisher':>8s} {'phi':>7s}")
    for name, label in reg2:
        blk = report_block(label, rows(name))
        blocks.append(blk)
        w, nc = blk["wald"], blk["newcombe"]
        print(f"{label:26s} {blk['delta_catch']:>8.4f} "
              f"[{w[0]:>7.3f},{w[1]:>7.3f}] [{nc[0]:>7.3f},{nc[1]:>7.3f}] "
              f"{blk['fisher_p']:>8.4f} {blk['phi']:>7.3f}")
    out["regime2"] = blocks

    print("\n  cells with a ZERO count (where Wald is not trustworthy):")
    for blk in blocks:
        if blk["p_judge_given_llm_wrong"] == 0.0 or blk["p_judge_given_llm_right"] == 0.0:
            print(f"    {blk['label']:26s} judge-only={blk['table']['judge_only']} "
                  f"of {blk['n_wrong_arm']} -> exact upper bound "
                  f"{blk['max_achievable_p1_upper_bound']}")

    print("\n" + "=" * 78)
    print("REGIME 3 -- chain battery (P22b r1..r3) + the pre-fix pilot")
    print("=" * 78)
    blocks3 = []
    reg3 = [("P22-chain-audit.json", "pilot (unpinned, n=69)")] + \
           [(f"P22b-fixed-r{i}.json", f"P22b r{i} (temperature=0)") for i in (1, 2, 3)]
    print(f"{'draw':26s} {'delta':>8s} {'Wald':>20s} {'Newcombe':>20s} "
          f"{'Fisher':>8s} {'phi':>7s}")
    for name, label in reg3:
        blk = report_block(label, rows(name))
        blocks3.append(blk)
        w, nc = blk["wald"], blk["newcombe"]
        print(f"{label:26s} {blk['delta_catch']:>8.4f} "
              f"[{w[0]:>7.3f},{w[1]:>7.3f}] [{nc[0]:>7.3f},{nc[1]:>7.3f}] "
              f"{blk['fisher_p']:>8.4f} {blk['phi']:>7.3f}")
    out["regime3"] = blocks3

    # ------------------------------------------------------------------ Holm correction
    print("\n" + "=" * 78)
    print("HOLM CORRECTION over the three temperature-pinned draws")
    print("=" * 78)
    print("The paper's pre-specified rule (`04-method-draft.md`) puts the primary endpoint")
    print("family under Holm. With 3 draws the first threshold is 0.05/3 = 0.01667.\n")
    holm = {}
    for tag, blks in (("regime2", blocks[1:]), ("regime3", blocks3[1:])):
        ps = sorted((b["fisher_p"], b["label"]) for b in blks)
        survivors = []
        for i, (p, lab) in enumerate(ps):
            thr = 0.05 / (len(ps) - i)
            ok = p <= thr and (not survivors or True)
            print(f"  {tag:8s} {lab:26s} p={p:.4f}  threshold={thr:.5f}  "
                  f"{'SURVIVES' if ok else 'does not survive'}")
            if ok:
                survivors.append(lab)
            else:
                break
        holm[tag] = {"p_values": [round(p, 4) for p, _ in ps],
                     "holm_survivors": survivors,
                     "none_survive": not survivors}
        if not survivors:
            print(f"  {tag:8s} -> NO Fisher p survives the paper's own Holm correction")
    out["holm"] = holm

    # ------------------------------------------------------------------ calibration
    print("\n" + "=" * 78)
    print("CALIBRATION (P19, n=1100) -- equal-FREQUENCY bins, as the paper states")
    print("=" * 78)
    cal = json.loads((R / "P19-calibration.json").read_text(encoding="utf-8"))
    crs = cal["rows"]
    # The forecast is the JUDGE's P(true) (`laya_p`) and the OUTCOME it forecasts is whether
    # the claim is actually TRUE -- not whether the judge was right. Using `laya_correct` as
    # the outcome silently substitutes accuracy for base rate and inflates UNC from 0.2400
    # to 0.2455.
    ps = [r["laya_p"] for r in crs]
    ys = [1 if r["truth"] else 0 for r in crs]
    acc = sum(1 for r in crs if r["laya_correct"]) / len(crs)
    n = len(ys)
    base = sum(ys) / n
    a = auc(ps, ys)
    order = sorted(range(n), key=lambda i: ps[i])
    bins = 10
    rel = res = 0.0
    for b in range(bins):
        idx = order[b * n // bins:(b + 1) * n // bins]
        if not idx:
            continue
        mp = statistics.fmean(ps[i] for i in idx)
        my = statistics.fmean(ys[i] for i in idx)
        rel += len(idx) / n * (mp - my) ** 2
        res += len(idx) / n * (my - base) ** 2
    print(f"  n={n}  base rate P(true)={base:.4f}  accuracy={acc:.4f}  AUC={a:.4f}")
    print(f"  Murphy (equal-frequency 10 bins): REL={rel:.4f}  RES={res:.4f}  "
          f"UNC={base * (1 - base):.4f}")
    print(f"  Brier (direct, no binning) = {statistics.fmean((p - y) ** 2 for p, y in zip(ps, ys)):.4f}"
          f"   [REL-RES+UNC = {rel - res + base * (1 - base):.4f}; the two differ only because "
          f"the decomposition bins]")
    brier_direct = statistics.fmean((p - y) ** 2 for p, y in zip(ps, ys))
    out["calibration"] = {"n": n, "base_rate": round(base, 4), "accuracy": round(acc, 4),
                          "auc": round(a, 4),
                          "rel": round(rel, 4), "res": round(res, 4),
                          "unc": round(base * (1 - base), 4),
                          "brier_direct": round(brier_direct, 4),
                          "brier_from_decomposition": round(rel - res + base * (1 - base), 4)}

    # ------------------------------------------------------------------ truncation
    print("\n" + "=" * 78)
    print("TRUNCATION CONTROL (P26 valid arm)")
    print("=" * 78)
    p26 = json.loads((R / "P26-truncation-harm-valid.json").read_text(encoding="utf-8"))
    print(f"  keys: {sorted(p26.keys())}")
    out["_provenance"] = {
        "artifact": "src/analysis/p28_recompute_all_stats.py",
        "generated_from": [n for n, _ in reg2 + reg3] + ["P19-calibration.json",
                                                         "P26-truncation-harm-valid.json"],
        "note": ("Standard library only: the project venv has no scipy. Fisher is the exact "
                 "two-sided test; Newcombe is method 10 (MOVER over Wilson); Clopper-Pearson "
                 "is the exact one-sided upper bound used where a count is zero."),
    }

    dest = R / "P28-recomputed-statistics.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwritten: {dest}")


if __name__ == "__main__":
    main()
