"""Close ERRATA section 10: record the resolution of every item, in the file that named them.

WHY THE ERRATA ITSELF MUST BE UPDATED
-------------------------------------
Section 10 is titled "Known but NOT yet fixed". After round 9 that title is false for all 26
items, and an audit file that keeps claiming open defects after they are closed is the same
defect it documents: a record that no longer describes the object. Two entries would also
mislead a reader who acts on them:

  * 10.3's closing sentence ("the published 1.55 is nonetheless the correct current value") is
    no longer true -- the re-run campaign regenerated P27 and P27b, and the ratio the paper
    prints is a range precisely because that value moved;
  * 10.2's list is a list of numbers, with no statement of what each one DOES rest on. Marking
    them in the paper (p76/p77) makes the list actionable, and this section says where.

The original text of 10.1-10.5 is NOT rewritten: the record of what was wrong is evidence.
Everything here is appended, and each claim names the script and the check that hold it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

ERRATA = ROOT / "results" / "ERRATA.md"

ANCHOR = ("**Rule adopted**: a fix script that reports `MISS` is not finished. Either the pattern "
          "or the\nlocation is wrong, and the difference must be established before moving on.")

APPENDIX = """

---

## 11. RESOLVED in round 9 -- the section-10 worklist, closed

**Status: all 13 paper-text defects (10.1), all 12 untraceable-number categories (10.2) and the
1 artifact defect (10.3) are fixed.** The fixes are scripts rather than hand edits, because a
hand edit cannot be re-run and this project's standard is that every claim is re-checkable.
Each script exits non-zero when its anchor is missing, and each was written to be idempotent
(`src/analysis/p70`-`p81`). `paper/verify_all.py` now carries the invariants as **K1-K10**,
which print their evidence on success as well as on failure -- a check that says nothing when
it passes is indistinguishable from a check that never ran.

### 11.1 The thirteen paper-text defects

| # | Fixed by | Backed by | Held by |
|---|---|---|---|
| 1 | `p74` (zh) + `p75` (en) | `recon/R13-laya-probe.md:430` vs `:456` | K4 |
| 2 | `p70` computes both conventions, `p71` labels them | `P28-recomputed-statistics.json` -> `regime3[*].vs_marginal_one_sided` | K2 |
| 3 | `p70` (interval), `p71`/`p72` (text) | `P14-llm-arm-full.json` -> `complementarity_prose_arm`; `P28` -> `regime1` | K1 |
| 4 | `p73` | `probes/P13-jev-remaining-measurements.md:47-56` (5 of the 8 recorded rows are `insufficient`) | `p73`'s own rescan |
| 5 | `p73` | `recon/R12-jev-probe.md:181-185` (per-bin counts) + `:187` (the prose summary) | -- |
| 6 | `p73` | same source's per-bin counts 2/2/2/2/1 | -- |
| 7 | `p73` (Results B, discussion) + `p72` (abstract) | `P19-calibration.json` -> `bins`: 660/1100 and 328/1100 | K6 |
| 8 | `p74` | `P19-calibration.json` -> all 10 bins, n summing to 1,100 | K3 |
| 9 | `p74` | `P14-llm-arm-full.json` -> `_provenance.consumes` = `P9b` | -- |
| 10 | `p74` | `P15-complementarity-strong-regime.json` + `P15b-rep-r1..r3.json` | -- |
| 11 | `p73` | `P27d-primitive-fields.json` -> `never_returned_by_provider`, 9 keys | K5 |
| 12 | `p74` | `04-method-draft.md` §4.4 vs `06-results-B-draft.md` clauses 8 and 10 | K7 |
| 13 | `p73` | `probes/P13-jev-remaining-measurements.md:45` vs `:47-56` | -- |

Every one of the thirteen is also present in the English section files (`p75`), because a
correction that exists in one language only leaves the two published versions disagreeing.

### 11.2 The twelve untraceable-number categories

Each is now **marked in place in both languages** -- 15 Chinese and 15 English markers
(`src/analysis/p76_mark_untraceable_numbers.py`, `p77_sync_english_untraceable.py`) -- and listed
once in a new **§11.6** of the manuscript that states, per category, what the number does rest on
and which artifact-backed alternative exists. Nothing was deleted and nothing was invented: the
numbers that cannot be re-checked are labelled as such at the point where a reader meets them.
Held by **K8**.

### 11.3 The artifact defect (10.3)

Resolved in three parts, and the third has moved again:

1. **The generator is fixed.** `p27f` now writes `_stale_superseded` **once** and preserves an
   existing block verbatim, counting further passes instead of overwriting them
   (`src/analysis/p78_fix_p27f_idempotency.py`, which also proves the guard on a scratch copy and
   asserts that `save()` still refuses to overwrite an existing `.pre-repair` backup).
2. **The historical values were never lost**, and are asserted recoverable: 915.1 ms / 2.02
   survive verbatim in `results/_superseded/P27b-plugin-crossval.json.pre-repair` and in
   `rerun/baseline/_superseded/P27b-plugin-crossval.json.pre-repair`.
3. **This section's closing sentence is superseded.** "The published 1.55 is nonetheless the
   correct current value" no longer holds: the re-run campaign regenerated `P27-jev-live.json`
   and `P27b-plugin-crossval.json`, the live artifact carries no `_stale_superseded` block at
   all, and the size-matched ratio now reads **1.49** against a denominator of 1,244.8 ms (it
   was 1.94 against 956.2 ms). That instability is exactly why the paper no longer prints either
   point value: the text now reports **about 1.5-1.9x** with both artifacts named and the reason
   stated, see `results/RERUN-RATIO-INSTABILITY.md` and
   `src/analysis/p79_fix_unstable_latency_ratio.py`. Held by **K9**.

### 11.4 New defects found while closing this worklist

Recorded because the pattern is by now familiar: none of these was found by reading, and each
was found by *running* something.

1. **A concurrent edit overwrote a per-artifact value with its own summary.** The ratio fix
   replaced the point value with the range `1.5-1.9` across the drafts and hit a sentence that
   reports what the ratio reads **against each artifact** -- yielding "reads 1.5-1.9 (baseline
   artifact) and 1.49 (live artifact)", which is not a sentence. Restored by `p79` to the value
   the baseline artifact records. **Class: a value and its summary share digits and differ in
   referent** -- this file's 10.4, one level down.
2. **`paper/verify_all.py` crashed while reporting its own results**: a detail string held a
   character the host console's GBK codec cannot encode, so the gate died in a
   `UnicodeEncodeError` traceback instead of printing a verdict. `stdout` is now reconfigured to
   UTF-8 with `errors="replace"`.
3. **Two of the new checks fired on correct data, because each tested the wrong object.** K3's
   row scan also collected the mock battery's bin table in section 3.1 (15 rows, not 10), and K4
   read the correction's own quotation of the withdrawn wording as the withdrawn claim. Both are
   repaired in `src/analysis/p81_repair_k_checks.py`. **The paper's own lesson applies to its
   tooling: a check that fails on correct data is a check that will be switched off.**
4. **`results/P27b-plugin-crossval.json` no longer reconstructs its own history.** After the
   re-run regenerated it, the artifact carries no `_stale_superseded` block, so the earlier
   values survive only in the two `.pre-repair` copies. Provenance that lives only in a backup
   is provenance with one deletion between it and nothing -- the same shape as 10.1 item 3,
   where the artifact's own `published_figures_at_risk` list named a figure the text never used.
"""


def main() -> int:
    t = ERRATA.read_text(encoding="utf-8")
    if "## 11. RESOLVED in round 9" in t:
        print("  ok    the resolution section is already present")
        return 0
    if ANCHOR not in t:
        print("  MISS  anchor (the 10.5 'Rule adopted' paragraph) is not in ERRATA.md -- "
              "refusing to guess where to append")
        return 1
    ERRATA.write_text(t + APPENDIX, encoding="utf-8")
    print(f"appended the resolution section to {ERRATA.relative_to(ROOT)} "
          f"({len(APPENDIX)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
