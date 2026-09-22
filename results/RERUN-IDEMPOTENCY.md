P27f idempotency: the defect demonstrated live, and the data is recoverable

Run on a byte-identical scratch copy (`D:\Projects\llm-jev-laya-bench-rerun-scratch`), no API
calls, published tree untouched. The repair was run three times and the forensic record
inspected after each pass.

WHAT IT SHOWS

    before pass 1   _stale_superseded.superseded_p50 = 1191.8   superseded_ratio = 1.55
    after  pass 1   _stale_superseded.superseded_p50 = 1191.8   superseded_ratio = 1.55
    after  pass 2   unchanged
    after  pass 3   unchanged

    identical to the post-repair top-level values?  True
    passes 2 and 3 leave it unchanged?              True

So the defect is exactly this: **the field whose entire purpose is to preserve what the values
USED TO BE now holds what they ARE.** `superseded_p50 = 1191.8` and the live `p50` is also
1191.8; `superseded_ratio = 1.55` and the live ratio is also 1.55. The record is self-nullifying.
A future reader inspecting `_stale_superseded` learns nothing except that the values did not
change -- which is false.

Further passes are stable, so the script is idempotent **in the narrow sense that it stops making
things worse**. That is not the property it needed. The property it needed was to preserve the
pre-repair values, and it destroyed them on the pass that was supposed to record them.

THE DATA IS NOT LOST

The re-run agent established this independently and it is the reason the defect is survivable:
the true superseded values (**915.1 ms / 2.02**) survive verbatim in
`results/_superseded/P27b-plugin-crossval.json.pre-repair`. Comparing that file against the live
artifact shows they differ in exactly two leaves, both under `_stale_superseded` -- so the round-5
repair pass repaired nothing and overwrote only its own forensic record.

That is worth stating plainly because it changes what has to be done: the artifact needs its
`_stale_superseded` block RESTORED FROM THE BACKUP, not re-derived (re-deriving is what destroyed
it), and `p27f` needs a guard that refuses to overwrite a `_stale_superseded` block that already
exists.

A SEPARATE, SMALLER DEFECT CONFIRMED IN THE SAME RUN

    P27 `_spend_usd`             = $0.001242822
    sum of persisted rows        = $0.001228542
    difference                   = $0.000014280

One call's cost is recorded in the ledger but has no row. This is the same $0.000014280 found
earlier by a different route, and it reproduces across passes, so it is a real property of the
artifact rather than a transcription slip.
