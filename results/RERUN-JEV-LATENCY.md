The withdrawn claim was RIGHT, and its evidence was WRONG -- now there is real evidence

Section 5 withdrew the claim that "the same script run twice differs greatly" on Jev latency,
because the second run it cited did not exist: 915.1 ms was the pre-repair value of a derived
field, not a measurement.

The re-run has now produced an actual second measurement, and it says the withdrawn claim was
**directionally correct all along**:

| statistic | published artifact | re-run | change |
|---|---|---|---|
| n | 20 | 20 | -- |
| **p50** | **1,191.8 ms** | **952.9 ms** | **-20%** |
| mean | 1,550.6 ms | 1,525.6 ms | -1.6% |
| min | 846.7 ms | 804.8 ms | -5.0% |
| **max** | **4,018.6 ms** | **6,360.4 ms** | **+58%** |

Everything else in the probe reproduces exactly: the truth battery is 8/8 again with the same
noul values (0.98/0.02/0.99), the criteria sensitivity behaves identically (`criteria moved:
True`, distinct noul 0.91/0.96/0.97), the maximum accepted state is 39,927 characters again, and
the per-call cost is $1.428e-05 again.

**So the precise finding is sharper than the one that was withdrawn.** Jev's ANSWERS are exactly
reproducible and its LATENCY is not. The model is deterministic; the transport is not. That is a
much better claim than "two runs differ greatly", because it says which part varies and which
part does not -- and it is supported by two artifacts instead of one artifact and one derived
field.

WHAT THIS MEANS FOR THE PAPER

The withdrawal stands and should stay: the evidence originally cited really was not a second
run, and citing it was the defect. But the conclusion does not have to stay withdrawn. It can now
be reinstated in the corrected form, citing two real runs:

    n=20, p50 1,191.8 ms (first run) vs 952.9 ms (second run); max 4,018.6 vs 6,360.4 ms;
    identical answers, identical costs, identical token counts.

This is worth stating carefully in the text: the paper withdrew a claim, and re-measurement
supported the claim while refuting the evidence. That is a better story than either keeping the
claim or dropping it, and it is what the audit trail is for.

The 25-32x latency ratio band in section 5 now has a third data point: 952.9/37.4 = 25.5x. The
band's lower edge was previously the unbacked 24.5x; it is now backed by a real measurement.
