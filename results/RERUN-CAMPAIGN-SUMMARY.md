# Re-run campaign: consolidated result

Budget: **under $0.005 of the authorised $0.10**. Every entry is a re-measurement, not a
re-reading. Companion findings: `RERUN-FINDING.md`, `RERUN-JEV-LATENCY.md`,
`RERUN-IDEMPOTENCY.md`, `RERUN-RATIO-INSTABILITY.md`, `RERUN-P20-DOES-NOT-SURVIVE.md`,
`RERUN-P26-REINSTATED.md`.

---

## Four kinds of result, and telling them apart was the whole job

**1. REPRODUCED EXACTLY**

| artifact | fields | note |
|---|---|---|
| P18 loadout window sweep | **0 differing of 65** | all four loadouts, clamps 1024/512/512/512; did not need the GPU free |
| P16 pinned clamp replication | **0 differing of 49** | including its NEGATIVE verdict |
| P17 clamp attribution | 0 differing of 23 | |
| P3 clamp calibration | 0 differing | provenance fields only |
| P30 evidence inventory | 0 differing | |
| P14 LLM arm | **1.0000 -> 1.0000** (48/48) | the ceiling effect behind "regime 1 is unmeasurable" |
| P23 logprobs | verdict identical, constant **0.0033 -> 0.0023** | exactly what the paper's "single unpinned draw" disclosure predicts |

P23 is the most useful of these: it is the paper's own documented limitation showing up as a
measurement instead of an assertion.

**2. A WITHDRAWN CLAIM, WITH THE EVIDENCE NOW EXISTING -- twice**

- **Jev latency.** Withdrawn because its "second run" was the pre-repair value of a derived field.
  Re-measured: p50 **1,191.8 -> 952.9 ms**, max **4,018.6 -> 6,360.4 ms**, with answers, costs and
  token counts identical. The finding is sharper than the withdrawn one: **Jev's ANSWERS are
  exactly reproducible and its LATENCY is not.**
- **P26 control arm.** Withdrawn for having no artifact. Re-produced from the tree's own generator
  and it lands on all four numbers -- **79-92 tokens, 6/10, 4/10, p = 0.010836** -- with the
  padding rule fixed before any judgement was read. See `RERUN-P26-REINSTATED.md`.

In both cases the withdrawal was correct when made, and the claim turned out to be true.

**3. THE ARTIFACT DISAGREES BECAUSE ITS CODE CHANGED**

This is not a reproducibility failure and must not be recorded as one. Re-running current code
measures the CURRENT protocol, not the published one.

- **P20** -- `criteria_used` null in the artifact, populated in the re-run. Settled by a half-split
  inside one artifact: the **true-item arm, rubric correct in both versions, reproduces 48/48
  fields across all eight languages**; the **false-item arm, rubric wrong in the published version,
  differs on 22**. The two runs asked the judge different questions.
- **P5** -- frozen evidence: `items/evidence-brief-pilot.json`, written four minutes AFTER the P5
  artifact, records `true_pos=4` where the artifact has 5. Today's generator matches the frozen
  snapshot, so P5's re-run measured a different item set.
- **P27c** -- all three ladder rungs re-measured higher. The size-matched rung is INTACT (126 chars
  / 347 tokens / n=5 in both runs); what moved is that rung's own p50, 956.2 -> 1,244.8 ms.

**4. A DEFECT THE RE-RUN CREATED**

**Re-running a generator destroys every metadata layer added to the artifact AFTER it was
measured, because the generator cannot reproduce it by construction.** Observed in three places:
`p29`'s `_provenance` (P21, P14), `p27f`'s `_stale_superseded` (P27b), and `p27f`'s
`cost._ledger_reconciliation` (P27-jev-live). Any pipeline that enriches artifacts after the fact
is one re-run away from silently deleting the enrichment, and nothing in the checks would notice,
because every number still looks right.

---

## The diff itself was wrong first, and that is part of the result

The first verdict compared each artifact against `_superseded/X.json.pre-rerun`. But the archiver
copies the artifact to that path BEFORE attempting the run, so for a run that failed or was never
attempted the backup **is** the artifact -- and the diff compared a file against itself and
reported "reproduced exactly". **Ten artifacts came back that way. Every one was a false positive.**

A backup diff cannot distinguish "reproduced" from "never ran". Only a change in the artifact's own
bytes can establish that a run happened. `src/analysis/p71_rerun_verdict_fixed.py` hashes against
the immutable baseline and reports three cases rather than two: UNCHANGED (never re-run, not a
result), CHANGED (compare values), no baseline (report, do not assume).

**A re-run that "reproduces everything" is not automatically good news, and one that "fails to
reproduce" is not automatically bad news. Both have to be established with the same care.** This
is the same class of error the paper itself keeps finding: a check that reports success because it
cannot see the failure.

---

## Paper text changed as a result

| what | from | to | why |
|---|---|---|---|
| P20 cross-language false-item P(true) | 0.912 | **0.4795** | 18 places; measured with the rubric wrong |
| plugin-vs-wall-clock ratio | 1.94 | **1.5-1.9, citing both artifacts** | the denominator is a latency measurement |
| regime-1 prose arm | absent | **added: delta_catch +0.0435, both intervals include 0** | the one measurable delta in regime 1, and it is POSITIVE |
| P26 withdrawal | closed | **amended with the new evidence; decision left to the author** | the only correction that moves a claim UP |

Every one carries a marker naming the round and the reason. The remaining occurrences of `0.912`
and `1.94` in either language are inside those markers, quoting the withdrawn values deliberately.

---

## Outstanding

1. **The author's P26 decision** -- reinstate or leave withdrawn.
2. **The consolidated subagent reports** have not landed; their findings are committed.
3. **P15 and P19** were still running. P19 (n=1100) is the largest item and is affordable.
4. **The provenance backfiller** needs re-running with figures DERIVED from the artifacts rather
   than hardcoded, plus a guard refusing to overwrite an annotation that already exists. P21 and
   P14 currently carry no provenance at all -- the re-run re-created exactly the defect ERRATA
   section 9 existed to fix.
