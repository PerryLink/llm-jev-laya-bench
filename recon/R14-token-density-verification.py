"""Consolidate every independent measurement of the token-density claim.

WHY: three independent parties measured this ratio and did not all describe what
they measured the same way, which is itself the finding. Before the paper is
corrected, the numbers have to sit in one place with their provenance, so the
correction cites measurements rather than recollections.

Sources:
  * P31-token-density.json  -- my own script, run in this repository
  * the recon record        -- recon/R13-laya-probe.md, where the paper's 6.33 came from
  * a subagent's report     -- independent measurement, reported 4.05 on prose
  * the paper itself        -- the sentence being checked

The script deliberately does NOT decide the verdict. It prints the comparison and
leaves the reading to a human, because the two candidate explanations for the
number (a chars-per-word mix-up, or a synthetic test state) are distinguishable
only by looking at which quantity actually equals ~6.33, and that is a judgement.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
# This file lives in recon/, so parents[1] is the repository root. parents[2]
# would be its parent directory -- a mistake worth naming because the failure it
# produces is a FileNotFoundError on a path that looks plausible.


def main() -> int:
    p31 = json.loads((ROOT / "results" / "P31-token-density.json").read_text(encoding="utf-8"))

    print("=" * 78)
    print("THE CLAIM UNDER CHECK")
    print("=" * 78)
    ms = (ROOT / "paper" / "MANUSCRIPT.md").read_text(encoding="utf-8")
    for line in ms.splitlines():
        if "6.33" in line:
            print("  " + line.strip()[:200])

    print()
    print("=" * 78)
    print("WHAT P31 MEASURED (reproducible: src/analysis/p31_token_density.py)")
    print("=" * 78)
    print(f"  planner assumes {p31['planner_assumed_chars_per_token']} chars/token")
    print()
    print(f"  {'tokenizer':16} {'sample':34} {'chars/tok':>9}  direction")
    print("  " + "-" * 74)
    for m in p31["measurements"]:
        print(f"  {m['tokenizer']:16} {m['sample']:34} {m['chars_per_token']:>9.2f}"
              f"  {m['direction']}")

    print()
    print("=" * 78)
    print("THE THREE CANDIDATE EXPLANATIONS FOR 6.33, AND WHICH QUANTITY MATCHES")
    print("=" * 78)
    # Pull the per-sample numbers we need out of the artifact rather than
    # recomputing them, so this summary cannot drift from the measurement.
    def ratio(sample: str, tokenizer: str = "english") -> float | None:
        for m in p31["measurements"]:
            if m["sample"] == sample and m["tokenizer"] == tokenizer:
                return m["chars_per_token"]
        return None

    prose = ratio("english_prose")
    # The exact R13 row the paper quotes -- NOT the 5000-char variant, which
    # measures the same density but is not the row the published figure came from.
    test_state = ratio("paper_test_state_5086")
    js = ratio("json_artifact")
    print(f"  A. 'the encoder delivers 6.33 on English prose'")
    print(f"     measured on English prose                 : {prose}")
    print(f"     => {'MATCHES' if prose and abs(prose - 6.33) < 0.5 else 'DOES NOT MATCH'}"
          f" (6.33 claimed)")
    print()
    print(f"  B. '6.33 is a chars-per-WORD value'")
    print(f"     a subagent computed chars/word for prose  : ~6.1-6.5 (their figure)")
    print(f"     note: chars/word is NOT in this artifact, because it is not a")
    print(f"     tokenizer measurement. Reported separately, not reproducible here.")
    print()
    print(f"  C. '6.33 is the real chars/token of the paper's synthetic test state'")
    print(f"     measured on the repeated-filler state     : {test_state}")
    print(f"     => {'CONSISTENT' if test_state and test_state > 5.5 else 'NOT CONSISTENT'}"
          f" with 6.33 (same direction, same magnitude)")

    print()
    print("=" * 78)
    print("WHAT THE PLANNER ACTUALLY DOES, PER TEXT TYPE")
    print("=" * 78)
    print(f"  {'sample':34} {'chars/tok':>9} {'estimate':>10} {'real':>8} {'verdict':>20}")
    print("  " + "-" * 74)
    for m in p31["measurements"]:
        if m["tokenizer"] != "english":
            continue
        verdict = ("UNDER-estimates -> reports fits for a state that is cut"
                   if m["direction"].startswith("UNDER") else "over-estimates -> safe")
        print(f"  {m['sample']:34} {m['chars_per_token']:>9.2f}"
              f" {m['planner_estimate']:>10,} {m['real_tokens']:>8,}  {verdict}")

    print()
    print("=" * 78)
    print("BOTTOM LINE (for the correction to state, not this script to decide)")
    print("=" * 78)
    print("  1. The 6.33 figure is reproducible on the paper's own test state,")
    print("     which is one filler sentence repeated dozens of times.")
    print("  2. It is NOT the density of English prose, which measures ~4.2-4.3.")
    print("  3. So the magnitude in the paper (1.8x) holds for that synthetic")
    print("     state and not for prose (~1.2x).")
    print("  4. The dangerous direction is the opposite of what the paper says:")
    print("     JSON and multilingual states are UNDER-estimated, and the 1.15")
    print("     safety factor does not cover the gap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
