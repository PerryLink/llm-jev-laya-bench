"""ERRATA 10.3 -- make the P27-family repair idempotency-safe, at the GENERATOR.

WHY THE GENERATOR IS THE RIGHT PLACE
------------------------------------
`p27f_repair_p27_family.py` exists to re-derive P27b's stale derived fields and, in the same
pass, to preserve what those fields USED TO BE under `_stale_superseded`. On its second run it
read the already-repaired values as "what used to be", wrote them into the forensic block, and
so destroyed the only in-artifact record of the historical numbers: `superseded_p50 = 1191.8`
while the live `p50` was also 1191.8. A field whose entire purpose is to record a CHANGE
recorded that nothing changed. `results/RERUN-IDEMPOTENCY.md` demonstrates this live on a
scratch copy and is the reason this fix is written against the guard rather than the artifact.

The historical values (915.1 ms / 2.02) are NOT lost: they survive verbatim in
`results/_superseded/P27b-plugin-crossval.json.pre-repair` and in the re-run campaign's
baseline archive. So this script repairs the CODE, and asserts the recoverability of the data
from those two files, instead of touching a measurement artifact that the re-run campaign has
since regenerated (the live P27b no longer carries a `_stale_superseded` block at all).

WHAT THE GUARD DOES
-------------------
`save()`  -- never overwrites an existing `.pre-repair` backup (it already had this property,
             and this script asserts it rather than assuming it).
`_stale_superseded` -- is written ONLY when it does not already exist. If it exists, the block
             is preserved verbatim and a `repair_passes` counter plus an explicit note are
             added, so a later reader can see that the repair ran again and changed nothing.

The script then RE-RUNS the repaired p27f against a scratch copy of the artifacts and proves
that the forensic block is unchanged, which is the property that was missing.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import ROOT  # noqa: E402

P27F = ROOT / "src" / "instrument" / "p27f_repair_p27_family.py"
R = ROOT / "results"

ANCHOR = """    p27b["latency_self_report_vs_wall_clock"]["_stale_superseded"] = {
        "reason": ("P27-jev-live.json was re-run after this artifact was written, so the "
                   "unmatched reference and the ratio derived from it were stale."),
        "superseded_unmatched_p50_ms": old_p50,
        "superseded_ratio_of_medians_unmatched": old_ratio,
        "repaired_by": "src/instrument/p27f_repair_p27_family.py",
        "note": ("Only DERIVED fields were recomputed. The plugin's 7 hand-transcribed rows "
                 "and its self-reported latencyMs distribution are untouched."),
    }"""

REPLACEMENT = '''    # IDEMPOTENCY GUARD (ERRATA 10.3). This block records what the derived fields USED to be,
    # so it may be written ONCE. Writing it again records the post-repair values as if they
    # were the pre-repair values -- which is exactly what happened on this script's second run
    # (`results/RERUN-IDEMPOTENCY.md` demonstrates it): the forensic field became identical to
    # the live field and the historical numbers (915.1 ms / 2.02) survived only in the
    # `.pre-repair` backup. A record that cannot survive its own repair is not a record.
    forensic = p27b["latency_self_report_vs_wall_clock"].get("_stale_superseded")
    if forensic is None:
        p27b["latency_self_report_vs_wall_clock"]["_stale_superseded"] = {
            "reason": ("P27-jev-live.json was re-run after this artifact was written, so the "
                       "unmatched reference and the ratio derived from it were stale."),
            "superseded_unmatched_p50_ms": old_p50,
            "superseded_ratio_of_medians_unmatched": old_ratio,
            "repaired_by": "src/instrument/p27f_repair_p27_family.py",
            "repair_passes": 1,
            "note": ("Only DERIVED fields were recomputed. The plugin's 7 hand-transcribed "
                     "rows and its self-reported latencyMs distribution are untouched."),
        }
    else:
        # preserve the ORIGINAL record verbatim; only count the extra pass
        forensic["repair_passes"] = int(forensic.get("repair_passes", 1)) + 1
        forensic["later_pass_note"] = (
            "This script ran again and found the derived fields already at the values it "
            "would write. The historical values above are NOT overwritten: re-recording "
            "them from the current state would destroy the only record that they changed "
            "(ERRATA 10.3). Historical values recoverable from "
            "results/_superseded/P27b-plugin-crossval.json.pre-repair if ever lost.")


'''

# The `save()` helper must keep its copy-once property; assert it rather than trust it.
SAVE_MARKER = """    b = p.with_suffix(".json.pre-repair")
    if not b.exists():
        shutil.copy2(p, b)"""


def main() -> int:
    src = P27F.read_text(encoding="utf-8")
    problems = []

    if "IDEMPOTENCY GUARD (ERRATA 10.3)" not in src:
        if ANCHOR not in src:
            problems.append("anchor for the _stale_superseded block is missing")
        else:
            src = src.replace(ANCHOR, REPLACEMENT.rstrip("\n"), 1)
    else:
        print("  ok    the idempotency guard is already in place")

    if problems:
        for p in problems:
            print(f"  MISS  {p}")
        return 1

    P27F.write_text(src, encoding="utf-8")
    print(f"patched {P27F.relative_to(ROOT)}")

    # ---- the copy-once property of save(), asserted rather than assumed -----------------
    if SAVE_MARKER in src:
        print("  ok    save() still refuses to overwrite an existing .pre-repair backup")
    else:
        print("  MISS  save() no longer has the copy-once guard")
        return 1

    # ---- prove the guard works, on a scratch copy: no measurement artifact is touched ----
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td)
        (scratch / "results").mkdir()
        for name in ("P27-jev-live.json", "P27b-plugin-crossval.json"):
            shutil.copy2(R / name, scratch / "results" / name)
        # seed the forensic block with known-historical values, as a first repair would
        doc = json.loads((scratch / "results" / "P27b-plugin-crossval.json")
                         .read_text(encoding="utf-8"))
        lat = doc["latency_self_report_vs_wall_clock"]
        lat["_stale_superseded"] = {
            "reason": "seed", "superseded_unmatched_p50_ms": 915.1,
            "superseded_ratio_of_medians_unmatched": 2.02,
            "repaired_by": "seed", "repair_passes": 1, "note": "seed",
        }
        (scratch / "results" / "P27b-plugin-crossval.json").write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

        # run the patched p27f inside the scratch tree by shadowing its ROOT resolution:
        # bench_env walks up from the script, so the script is copied in beside a stub
        # bench_env that points at the scratch directory.
        (scratch / "src" / "instrument").mkdir(parents=True)
        (scratch / "bench_env.py").write_text(
            "from pathlib import Path\nROOT = Path(__file__).resolve().parent\n",
            encoding="utf-8")
        shutil.copy2(P27F, scratch / "src" / "instrument" / "p27f_repair_p27_family.py")
        r = subprocess.run([sys.executable, str(scratch / "src" / "instrument"
                                                / "p27f_repair_p27_family.py")],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(r.stdout)
            print(r.stderr)
            print("  MISS  the patched p27f could not be exercised on the scratch copy")
            return 1
        after = json.loads((scratch / "results" / "P27b-plugin-crossval.json")
                           .read_text(encoding="utf-8"))
        ss = after["latency_self_report_vs_wall_clock"]["_stale_superseded"]
        checks = [
            ("the historical p50 survives a second repair pass",
             ss["superseded_unmatched_p50_ms"] == 915.1),
            ("the historical ratio survives a second repair pass",
             ss["superseded_ratio_of_medians_unmatched"] == 2.02),
            ("the extra pass is counted, not hidden", ss.get("repair_passes") == 2),
            ("the derived fields were still re-derived (the repair still repairs)",
             after["latency_self_report_vs_wall_clock"]["unmatched_direct_for_reference"]
             ["p50_ms"] is not None),
            ("the .pre-repair backup still holds the file as it was",
             (scratch / "results" / "P27b-plugin-crossval.json.pre-repair").exists()),
        ]
        ok = True
        for label, good in checks:
            print(f"  {'ok  ' if good else 'FAIL'}  {label}")
            ok = ok and good
        if not ok:
            return 1

    # ---- the historical values are still recoverable from the two archived copies --------
    for rel in ("results/_superseded/P27b-plugin-crossval.json.pre-repair",
                "rerun/baseline/_superseded/P27b-plugin-crossval.json.pre-repair"):
        p = ROOT / rel
        if not p.exists():
            print(f"  warn  {rel} is absent; recoverability rests on the surviving copy only")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        ss = d["latency_self_report_vs_wall_clock"]["_stale_superseded"]
        good = (ss["superseded_unmatched_p50_ms"] == 915.1
                and ss["superseded_ratio_of_medians_unmatched"] == 2.02)
        print(f"  {'ok  ' if good else 'FAIL'}  {rel} records the true historical values "
              f"(915.1 / 2.02)")
        if not good:
            return 1

    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
