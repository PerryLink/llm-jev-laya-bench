The recorded draw for regime 3 was overwritten by a re-run, and survives only in a backup

WHAT HAPPENED

`results/P22-chain-audit.json` is the PILOT battery, n=69. `results/P22b-fixed-r*.json` are the
FIXED battery, n=68. Re-running the pilot's generator has produced **n=68 under the pilot's
filename**, which means the generator now builds the fixed battery and the pilot's own item set no
longer exists in that code path.

    live      rows = 68,  alt_option_availability.n_items = 68,  _repair ABSENT
    backup    rows = 69,  _repair PRESENT

The 69-row record survives in `results/_superseded/P22-chain-audit.json.pre-rerun`, complete with
its `_repair` note.

WHY THIS IS WORSE THAN THE OTHER DRIFT FINDINGS

For P20 and P5, construction drift changed **which measurement was taken**, and the paper can be
corrected -- inconvenient, but recoverable by editing text.

Here the drift **destroyed the artifact that is itself the evidence for a published reproducibility
claim.** The paper cites P22-chain-audit as the RECORDED DRAW: the unpinned run whose item-level
label agreement with the pinned draws (58.8 / 63.2 / 60.3%) is the reproducibility evidence for
regime 3, and whose confusion table {12, 29, 8, 20} is the basis of the kappa = 0.0062 figure.
Overwriting it with a different battery does not lose a comparison -- **it deletes the thing the
comparison was against.**

Also lost: `summary._repair`, the p22f backfill note recording that **7** items (not 2) had the
ignore-SUPERSEDED value unavailable. That note is the origin of the 61-item denominator the paper
now uses. This is the third instance of the class the re-run agent named -- re-running a generator
destroys metadata added afterwards -- but it is the first that destroys a **pipeline note other
published numbers depend on**, rather than provenance.

WHAT HAS TO BE DECIDED

1. **Can the 69-item pilot be rebuilt?** The `_repair` note says the item set is seeded and the
   option sets were recovered exactly. If it can, rebuild it and restore the artifact. If it
   CANNOT, that is a finding in its own right and belongs in the report: it would mean one of the
   paper's three complementarity regimes has a recorded draw that current code cannot reproduce.
2. **Should the re-run of a historical artifact be allowed at all?** Every other artifact in this
   campaign is a measurement whose reproducibility is a fair question. P22-chain-audit is a
   HISTORICAL RECORD -- the "before" side of a before-and-after comparison. Re-running it does not
   test reproducibility; it destroys the comparison. The same question applies to
   `P22b-fixed-r*.json`, which are pinned draws rather than generator outputs.

THE GENERAL LESSON

Three separate failure modes have now appeared in this campaign, and only one of them is about
reproducibility:

    the measurement does not reproduce        a scientific finding, and the paper changes
    the code changed after the artifact       a protocol question, and someone must assign it
    the re-run destroyed the record           an ARCHIVING failure, and no re-run can fix it

The third is the one nothing in the tree guards against, and it is the one that produced a false
"reproduced exactly" verdict on the first attempt, because a backup that has not been overwritten
is indistinguishable from an artifact that reproduced.
