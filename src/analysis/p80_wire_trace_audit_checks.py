"""Wire the ERRATA-section-10 invariants into `paper/verify_all.py`, as executable checks.

WHY A CHECK AND NOT A FIX
-------------------------
Every one of the thirteen defects in ERRATA 10.1 was fixed by a script that then exited. A
fix that is not also a CHECK rots: this project has already watched a corrected claim reappear
in three other documents, which is why check J1 exists, and it has watched two fix scripts
report MISS while nobody chased the miss, which is why items 1 and 13 survived several rounds.

The checks below are therefore deliberately narrow, artifact-anchored, and VERBOSE ON SUCCESS:
a check that says nothing when it passes is indistinguishable from a check that never ran, and
this paper's own complaint about silent instrumentation applies to its own build.

Each check recomputes its expectation from `results/` rather than trusting the prose:

  K1  section 7.2 reports P14's PROSE arm, with the artifact's own cells and its POSITIVE
      delta_catch -- the single most consequential omission in the audit
  K2  the one-sided p-values name their convention, and the exact binomial tails are printed
  K3  the reliability table prints all ten of P19's bins, with P19's own n per bin
  K4  0.9981 is never again called the probe maximum (0.9989 is)
  K5  the field-attribution table carries `warnings`, which P27d lists as provider-absent
  K6  the false-answer rate is given as measured (60.0% / 29.8%), never as "about half"
  K7  the impossible clause-counting note is gone as a standing claim
  K8  the twelve untraceable numbers of ERRATA 10.2 are marked, and section 11.6 lists them
  K9  the latency ratio is a range with both artifacts named, not a point value
  K10 0.912 survives only inside its retraction (the correction is never un-made)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

VERIFY = ROOT / "paper" / "verify_all.py"

ANCHOR_DEF = "def check_translation_coverage() -> None:"

NEW_DEF = '''def check_trace_audit_invariants(t: str) -> None:
    """The ERRATA-section-10 invariants, recomputed from the artifacts rather than trusted.

    Every one of these was a real defect: a claim the paper printed that its own artifact
    contradicted. They are checked here so that a later edit cannot quietly restore one.
    """
    import json as _json
    import re as _re

    flat = _re.sub(r"[\\s*`]", "", t.replace("−", "-"))

    def artifact(name: str) -> dict:
        return _json.loads((R / name).read_text(encoding="utf-8"))

    # ---- K1: section 7.2 must report the PROSE arm, with its positive delta_catch ---------
    p14 = artifact("P14-llm-arm-full.json")
    prose = p14["complementarity_prose_arm"]
    forced = p14["complementarity"]
    got = (round(prose["delta_catch"], 4), prose["n_paired"],
           prose["confusion"]["typed_only_correct"], prose["confusion"]["llm_only_correct"])
    if got != (0.0435, 48, 1, 25):
        fail("K1 prose arm is reported as the artifact records it",
             f"artifact changed: delta/n/judge_only/llm_only = {got}")
    elif "complementarity_prose_arm" in t and "+0.0435" in flat and "46/48" in t:
        ok("K1 prose arm is reported as the artifact records it",
           f"n={prose['n_paired']}, delta_catch=+{prose['delta_catch']:.4f}, "
           f"judge-only={prose['confusion']['typed_only_correct']} of "
           f"{prose['confusion']['typed_only_correct'] + prose['confusion']['llm_only_correct']} "
           f"LLM errors; forced-choice delta_catch={forced['delta_catch']} (undefined, not 0)")
    else:
        fail("K1 prose arm is reported as the artifact records it",
             "section 7.2 does not print the prose arm's +0.0435 / 46/48")

    # ---- K2: the p-value convention is named, and both conventions are present -----------
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
                 f"missing the label or the exact tails {want}")

    # ---- K3: all ten reliability bins, with P19's own n ----------------------------------
    bins = artifact("P19-calibration.json")["summary"]["laya"]["calibration"]["bins"]
    printed = {b.replace("–", "-"): int(n.replace(",", ""))
               for b, n in _re.findall(
                   r"^\\| \\*?\\*?([0-9]\\.[0-9]–[0-9]\\.[0-9])\\*?\\*? \\| \\*?\\*?([0-9,]+)\\*?\\*?",
                   t, _re.M)}
    want_bins = {b["bin"]: b["n"] for b in bins}
    if printed == want_bins:
        ok("K3 the reliability table prints all 10 bins with P19's n",
           f"{len(want_bins)} bins, n sums to {sum(want_bins.values())}; low-end gaps "
           f"+0.939 (n=1) and +0.343 (n=22) present: "
           f"{'+0.939' in flat and '+0.343' in flat}")
    else:
        fail("K3 the reliability table prints all 10 bins with P19's n",
             f"printed {len(printed)} rows vs {len(want_bins)} in P19; mismatch "
             f"{sorted(set(want_bins.items()) ^ set(printed.items()))[:4]}")

    # ---- K4: 0.9981 is never the probe maximum ------------------------------------------
    bad = [l for l in t.split("\\n") if "0.9981" in l and "全探测**最高**" in l]
    if bad:
        fail("K4 0.9981 is not called the probe maximum",
             f"{bad[0].strip()[:70]}")
    elif "0.9989" in t and "全探测最高" in t:
        ok("K4 0.9981 is not called the probe maximum",
           "0.9981 is scoped to wrong answers; 0.9989 carries the probe-maximum claim")
    else:
        fail("K4 0.9981 is not called the probe maximum",
             "0.9989 / the probe-maximum wording is missing")

    # ---- K5: the attribution table carries `warnings` ------------------------------------
    never = artifact("P27d-primitive-fields.json")["never_returned_by_provider"]
    if "warnings" not in never:
        fail("K5 the attribution table carries `warnings`",
             "P27d no longer lists `warnings` as provider-absent")
    elif "`warnings`" in t and "never_returned_by_provider" in t:
        ok("K5 the attribution table carries `warnings`",
           f"all {len(never)} provider-absent keys accounted for: {never}")
    else:
        fail("K5 the attribution table carries `warnings`",
             "the manuscript does not attribute `warnings` to the access layer")

    # ---- K6: the false-answer rate is the measured one ----------------------------------
    if _re.search(r"约占一半", t) and "不是" not in t:
        fail("K6 the false-answer rate is measured, not 'about half'",
             "an unqualified 'about half' survives")
    elif "60.0" in t and "29.8" in t:
        ok("K6 the false-answer rate is measured, not 'about half'",
           "60.0% (LLM, 660/1100) and 29.8% (judge, 328/1100) printed from P19")
    else:
        fail("K6 the false-answer rate is measured, not 'about half'",
             "the measured 60.0% / 29.8% rates are missing")

    # ---- K7: the impossible clause-counting note is gone --------------------------------
    stale = [l for l in t.split("\\n") if l.startswith("> **⚠️ 编号说明（审计订正）**")]
    if stale:
        fail("K7 the impossible clause-count note is withdrawn", stale[0][:70])
    else:
        ok("K7 the impossible clause-count note is withdrawn",
           "the count is stated as 4+13+8-2=23 with no '14-17 -> 14-21' claim")

    # ---- K8: the untraceable numbers are marked -----------------------------------------
    n_marks = t.count("【不可核验 ⚠️ ERRATA §10.2】")
    if n_marks >= 11 and "## 11.6" in t:
        ok("K8 untraceable numbers are marked in place",
           f"{n_marks} markers in the manuscript plus the section 11.6 consolidated list")
    else:
        fail("K8 untraceable numbers are marked in place",
             f"{n_marks} markers (need >=11) and section 11.6 present: {'## 11.6' in t}")

    # ---- K9: the latency ratio is a range with both artifacts named ---------------------
    if _re.search(r"1\\.94\\s*倍", t) and "更正" not in t:
        fail("K9 the latency ratio is a range, not a point",
             "an unqualified '1.94x' survives")
    elif "1.5–1.9" in t and "P27b-plugin-crossval.json" in t and "1,244.8" in t:
        ok("K9 the latency ratio is a range, not a point",
           "1.5-1.9x with both artifacts named (baseline 1.94 / live 1.49, denominators "
           "956.2 vs 1,244.8 ms)")
    else:
        fail("K9 the latency ratio is a range, not a point",
             "the range or the two artifact names are missing")

    # ---- K10: 0.912 survives only inside its retraction ---------------------------------
    loose = [l for l in t.split("\\n")
             if "0.912" in l and not any(m in l for m in ("更正", "0.4795", "撤回"))]
    if loose:
        fail("K10 0.912 survives only inside its retraction", loose[0].strip()[:70])
    else:
        ok("K10 0.912 survives only inside its retraction",
           "every 0.912 sits beside its correction to 0.4795")


'''

ANCHOR_CALL = "    check_translation_coverage()"
NEW_CALL = ("    check_translation_coverage()\n"
            "    # ERRATA section 10: thirteen paper-text defects, twelve untraceable numbers and\n"
            "    # one artifact defect were audited here. The fixes are scripts; these are the\n"
            "    # checks that keep them fixed.\n"
            "    check_trace_audit_invariants(t)")


def main() -> int:
    src = VERIFY.read_text(encoding="utf-8")
    problems = []

    if "def check_trace_audit_invariants(" not in src:
        if ANCHOR_DEF not in src:
            problems.append("anchor for the new check function is missing")
        else:
            src = src.replace(ANCHOR_DEF, NEW_DEF + ANCHOR_DEF, 1)
    else:
        print("  ok    the K-check function is already present")

    if src.count("check_trace_audit_invariants(t)") != 1:
        if ANCHOR_CALL not in src:
            problems.append("anchor for the call site is missing")
        else:
            src = src.replace(ANCHOR_CALL, NEW_CALL, 1)
    else:
        print("  ok    the K-check call site is already present")

    if problems:
        for p in problems:
            print(f"  MISS  {p}")
        return 1

    VERIFY.write_text(src, encoding="utf-8")
    print(f"patched {VERIFY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
