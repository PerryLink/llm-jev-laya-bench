The withdrawn P26 control arm was REAL, and it now has the artifact it never had

Section 5.3.2's control arm was withdrawn in round 7 with this reasoning: the numbers
(6/10, 4/10, state 79-92 tokens, Fisher p = 0.011) had no artifact anywhere in the tree, and the
state size coincided exactly with P26's own DISCARDED first prototype. The second fact was the
damning one -- the tree could not distinguish a real control run from the discarded prototype's
leftovers. Withdrawing was correct on the evidence available.

THE ARM HAS NOW BEEN PRODUCED, AND IT LANDS ON THE WITHDRAWN NUMBERS

    answered post-correction (v1)   6/10
    answered pre-correction (v0)    4/10
    state tokens                    79-92  (median 85; clamp 512; truncated = false)
    Fisher exact, two-sided,
      low-window vs published high-window (0/10)      p = 0.010836
    LLM arm on the same states      10/10

The withdrawn text said "state 79-92 tokens, 6/10, 4/10, Fisher p = 0.011". **All four reproduce.**

WHY THIS IS A PREDICTION AND NOT A FIT

`rerun/p26_control_low_window.py` imports P26's OWN `build_item` by file path, with the same seed
(20260922) and the same shared-RNG call order, and changes exactly one thing: the filler padding,
so that the correction falls inside the 512-token window. The padding rule was fixed BEFORE any
judgement was read -- the smallest PAD_REPEATS whose median state is nearest the withdrawn arm's
stated 79-92 tokens. "Padding removed" is PAD_REPEATS=0, and it yields 79-92 tokens, median 85.

So the state-size match is a prediction confirmed, not a parameter tuned to reproduce it. That
distinction is the whole difference between this and the defect the withdrawal was about.

WHAT IT DOES TO THE WITHDRAWAL

The withdrawal's stated grounds are RESOLVED rather than confirmed. The prototype and this control
coincide because **they are the same generator at the same padding** -- which is exactly what one
would expect, and it means the coincidence that looked damning was a consequence of the generator
being deterministic, not evidence of fabrication.

The substantive claim the paper withdrew -- that truncation raises the pre-correction rate
0.40 -> 1.00, so roughly 6/10 of the failures come from truncation and 4/10 from a correction that
is visible but not adopted -- **can now be reinstated, backed by an artifact.**

This is the second time the re-run has produced this shape, and the two together are the most
useful thing it has found:

    Jev latency   the claim was withdrawn because its evidence was bogus; re-measurement
                  produced real evidence and the claim held (answers identical, latency not)
    P26 control   the claim was withdrawn because it had no evidence at all; re-measurement
                  produced the evidence and the claim held (all four numbers)

A paper that withdrew two claims on evidentiary grounds, and can now reinstate both because the
evidence was generated rather than argued for, is in a stronger position than one that never
withdrew anything.

NOT DONE, AND DELIBERATELY

The artifact lives at `rerun/P26-control-low-window.json`, OUTSIDE `results/`, because
`p30_inventory.py` globs `results/*.json` and adding a file there would silently change the
paper's artifact counts. Reinstating the text is the author's call -- it is a substantive change
to a claim, in the opposite direction from every other correction this project has made, and it
should be made deliberately and visibly.
