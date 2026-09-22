"""Record, in ERRATA, the one finding that leaves the gate RED -- and why red is correct here.

WHAT HAPPENED (found while re-running the fix scripts for idempotency, not by reading)
-------------------------------------------------------------------------------------
`results/P22b-fixed-r1..r3.json` were regenerated at 23:33-23:35, AFTER the re-run campaign's
own consolidated summary was written (23:32:44), so nothing in the tree yet records it. The
regenerated battery is not the published one: the generator now inserts the ignore-SUPERSEDED
value into the options (only **2** items lack it, against **7** before), so the OPTION SETS
changed and the judge's answers changed with them. Laya is deterministic given (state, options),
so the judge arm moving on **24 of 68** items is proof of a construction change rather than
sampling noise -- and it is exactly the class the re-run agent named for P20 and P5.

Consequence: the whole chain block of section 7.6.1 (both languages) is now stale -- LLM/Laya
accuracies, the confusion cells, Delta_catch and its intervals, the Fisher p-values, phi, the
item-level agreement rates that clause 17 rests on, and the "61/61 = 100%" claim about the judge
arm being a deterministic function. The recomputation is mechanical (`p28`), but the decision of
WHICH battery is canonical is not mine: `RERUN-P22-PILOT-OVERWRITTEN.md` asks the same question
about the pilot.

So `verify_all.py`'s K2 check fails, and it is right to fail: the manuscript prints exact
binomial tails of 0.076 / 0.061 / 0.149 while the live artifacts now produce 0.443 / 0.330 /
0.413. A gate that stayed green here would be precisely the "check that reports success because
it cannot see the failure" that this project keeps finding. The red is recorded rather than
papered over.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

ERRATA = ROOT / "results" / "ERRATA.md"

ANCHOR = """4. **`results/P27b-plugin-crossval.json` no longer reconstructs its own history.** After the
   re-run regenerated it, the artifact carries no `_stale_superseded` block, so the earlier
   values survive only in the two `.pre-repair` copies. Provenance that lives only in a backup
   is provenance with one deletion between it and nothing -- the same shape as 10.1 item 3,
   where the artifact's own `published_figures_at_risk` list named a figure the text never used."""

ADDITION = ANCHOR + """

5. **The chain battery was re-measured after the re-run campaign's own summary, and section
   8.6.1 is now stale in both languages.** `results/P22b-fixed-r1..r3.json` were rewritten at
   23:33-23:35, after `RERUN-CAMPAIGN-SUMMARY.md` (23:32:44), so no document yet records it.
   The regenerated battery is **not the same measurement**: the generator now inserts the
   ignore-SUPERSEDED value among the options, so **2** items lack it instead of **7**, the
   option sets therefore differ, and the judge's answers move with them -- for a deterministic
   judge, **24 of 68 labels changing** is proof of a construction change, not sampling noise.
   This is the class the re-run agent named for P20 and P5 (`RERUN-CAMPAIGN-SUMMARY.md` §3), and
   it lands on the one regime whose published numbers rest on item-level agreement.

   | quantity (n=68, three pinned draws) | published | recomputed from the live artifacts |
   |---|---|---|
   | LLM overall | 0.6765 / 0.6618 / 0.6618 | **0.5294** (r1 only; the artifacts differ per draw) |
   | judge overall | 0.2941 (3x identical) | **0.2794** (3x identical) |
   | judge-only-correct | 3 / 3 / 4 | **8 / 7 / 7** |
   | Delta_catch | -0.2332 / -0.2473 / -0.1816 | **-0.0556 / -0.0985 / -0.0663** |
   | Fisher p (2x2) | 0.086 / 0.049 / 0.163 | **0.7873 / 0.4246 / 0.5954** |
   | phi | +0.239 / +0.257 / +0.189 | **+0.0618 / +0.1094 / +0.0731** |
   | one-sided binomial lower tail vs the judge's marginal | 0.076 / 0.061 / 0.149 | **0.4425 / 0.3299 / 0.4132** |

   **The direction survives and the strength does not.** Delta_catch is still negative in 3/3
   draws, so "no complementarity" still holds; but the *shared-failure* reading -- the paper's
   positive claim about phi -- loses even the weak statistical support it had: Fisher p goes from
   "significant in 1 of 3 uncorrected" to "nowhere near significant in any draw", and phi falls
   from +0.19...+0.26 to +0.06...+0.11. The claim that the judge arm is a **deterministic
   function of (state, options)** -- 61/61 = 100% on items whose option set did not change -- must
   also be re-derived, because the count of changed option sets is itself different (7 -> 2).

   **Which battery is canonical is a decision, not a computation.** `RERUN-P22-PILOT-OVERWRITTEN.md`
   asks the same question about the n=69 pilot; the live pilot artifact currently matches the
   published recorded round, so only the fixed battery is affected. Until that decision is made,
   the paper's section 8.6.1 block cannot be re-derived -- and `verify_all.py`'s **K2 check fails
   on purpose**, because the manuscript prints tails (0.076 / 0.061 / 0.149) that the live
   artifacts no longer produce (0.443 / 0.330 / 0.413). **The gate is red because the paper and
   its artifacts disagree; making it green without fixing that would be the failure mode this
   whole section documents.**"""


def main() -> int:
    t = ERRATA.read_text(encoding="utf-8")
    if "The chain battery was re-measured after the re-run campaign" in t:
        print("  ok    the chain-battery finding is already recorded")
        return 0
    if ANCHOR not in t:
        print("  MISS  anchor (section 11.4 item 4) is not in ERRATA.md -- refusing to guess")
        return 1
    ERRATA.write_text(t.replace(ANCHOR, ADDITION, 1), encoding="utf-8")
    print("  ok    recorded item 5 in ERRATA section 11.4 (the chain battery re-measurement)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
