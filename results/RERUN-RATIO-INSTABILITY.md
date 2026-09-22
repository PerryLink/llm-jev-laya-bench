The size-matched ratio was never a stable number, and the re-run shows it

THE DISCREPANCY

  paper, five places      1.94  (the "size-matched, therefore correct" ratio)
  live artifact now       1.49
  pre-rerun artifact      1.94  (1851 / 956.2 = 1.936)

The ratio is `plugin self-reported latencyMs p50 (1,851 ms, n=7)` divided by `size-matched wall
clock p50`. Only the DENOMINATOR moved: 956.2 ms -> 1,244.8 ms, because that reference is drawn
from a rung of the P27c size ladder, and the ladder was re-measured.

WHY THIS IS NOT JUST ARITHMETIC

Section 5.2 was itself a correction. The paper originally printed the UNMATCHED ratio, then
corrected it to the size-matched one and explained why: the two states have to be the same size
or the comparison is meaningless. That correction was right, and it is the more careful of the two
figures.

But the correction fixed the STATE SIZE, not the LATENCY. `1.94` is a ratio between two latency
measurements, and this project has just established, from P27's own re-run, that Jev latency is
precisely the quantity that does NOT reproduce:

    same state, same n=20, same cost, same token count
    p50  1,191.8 ms  ->  952.9 ms     (-20%)
    max  4,018.6 ms  ->  6,360.4 ms   (+58%)

A ratio whose denominator moves by 20% between runs is not a fixed property of the plugin. It is
a property of one run, and printing it to three significant figures as a correction to an earlier
figure implies a stability it does not have.

WHAT THE PAPER SHOULD SAY, AND WHY IT IS BETTER

The honest form is a range with the reason stated:

    the plugin's self-reported latencyMs is about 1.5-1.9x the size-matched wall clock,
    depending on the run; the ratio is unstable because its denominator is a latency
    measurement, and Jev's latency varies about 20% between runs at a fixed state.

That is a stronger sentence than `1.94x`, because it tells the reader what kind of quantity they
are being given. It also fits the paper's own thesis: a figure presented as more precise than its
evidence is the defect the whole paper is about, and this one is the paper's own.

Note the sign of this finding: the earlier correction moved the number from 1.55 to 1.94, i.e.
made the plugin look WORSE. The re-run moves it to 1.49, i.e. better. So this is not a correction
that conveniently improves the paper's position, and it should not be presented as one -- it is a
range because the measurement is unstable, full stop.

NOT YET DONE

Five places carry `1.94` -- sections 4, 5 and 6 in Chinese, and sections 3, 5 and 6 in English --
plus the two generated manuscripts. No text has been changed; the fix belongs to whoever is
editing the drafts, and the decision of range-versus-point belongs to the author's judgement of
what the claim is for.
