Record the re-run's real finding: construction drift, not measurement noise

The corrected verdict (p71, which hashes against an immutable baseline instead of
diffing an artifact against a possibly-identical backup) gives the honest picture:

  15 artifacts were genuinely re-run. 27 were never rewritten and are NOT results.
  63 measurement values differ.

The differences are NOT random. They fall into two kinds, and only one of them is a
threat to the paper.

PROVENANCE DRIFT -- harmless, and expected. 34 keys are ADDED to most artifacts
because instrument_hashes() now returns snapshot.*/worktree.* keys plus a drift block,
where the published artifacts carry four flat keys. P1's two differences are also
provenance (restart_count 1->0, cold_start_ms -> null). Every measurement reproduces;
only the record of the instrument changed. That is a reproducibility finding worth
stating: re-running an early artifact under current code cannot reproduce its
provenance block even when every measurement reproduces, because the provenance
function itself changed mid-campaign.

CONSTRUCTION DRIFT -- this is the real finding, and it is not about noise.

  P20  criteria_used: published = null, re-run = explicit criteria for both the true
       and false item. The two runs measured DIFFERENT CONDITIONS. The script carries
       an "AUDIT FIX (finding: mismatched criteria on the false item)" comment at
       src/items/p20_language_misrouting.py:104-115, so the code changed AFTER the
       artifact was produced. With criteria supplied the judge does much better on
       false items (non-Latin mean P(true) 0.9121 -> 0.4795; bands move 'yes' ->
       'uncertain'; several predictions flip to correct).

  P5   carrier_required_verified flips True -> False on EVERY level, and derivable
       flips in both directions. Those are properties of the ITEMS, not of the judge's
       answer. If the item-construction code changed, the re-run is measuring a
       different battery, and the accuracy shifts follow from that rather than from
       any instability in the model.

So the re-run has answered its question, and the answer is more useful than "it
reproduces": **the measurement layer is stable, and the artifacts that disagree do so
because the CODE THAT BUILT THEM changed after they were written.** Re-running current
code on a published artifact measures the current protocol, not the published one, and
the two are not the same thing.

That has a direct consequence for the paper, and it is not a small one: for P20 in
particular, the 0.912 figure the paper prints as a headline may rest on the PRE-FIX
protocol. If so, the disagreement is between the paper and its own code, not between
two runs -- and it has to be resolved by deciding which protocol the claim belongs to,
not by re-running again.

No paper claim has been changed. Pinning the condition down comes first.
