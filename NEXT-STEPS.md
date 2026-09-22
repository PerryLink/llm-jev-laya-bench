# What remains before this can be submitted

State as of commit `279c02b`. `paper/verify_all.py`: **45 passed, 2 warnings, 0 failures
(47 checks)**. Nothing is pushed, posted or submitted anywhere. The submission gate is
closed and stays closed until the author says otherwise.

---

## 1. Two things only the author can supply

These are the two `verify_all.py` warnings, printed on every run.

### 1.1 The AI-assistance disclosure

`paper/AI-DISCLOSURE-DRAFT.md` holds two options in both languages:

- **Option A (short)** — one sentence stating that generative AI assisted with drafting and
  code, and that the author verified all output.
- **Option B (long)** — names the tools, the model, the roles (drafting, code, analysis), and
  the verification steps taken.

**The relevant policies were verified from primary sources** (see `protocol/` and the
citation comments in `paper/references.bib`; the venue survey is in
`paper/VENUE-AND-POLICY-SURVEY.md` if present, otherwise the README):

- **No venue in the survey bans AI involvement.** arXiv requires (a) that generative-AI use
  be reported, (b) that authors take full responsibility for all content, and (c) that AI
  systems not be listed as authors. It penalises only *unchecked* output — hallucinated
  references, leftover model chatter — with a one-year ban.
- **TMLR**: "LLMs may be used as general-purpose assistive tools… LLMs are not eligible for
  authorship."
- **ACL**: disclosure plus author responsibility.
- arXiv also **requires a full English version** for non-English submissions (in effect from
  2026-02-11) — which is why the translation in `paper/en/` is not optional.

**Decision needed: A or B.** The paper's own thesis argues for B — a paper about
unverifiable self-reports should not under-report its own provenance — but A is defensible
and shorter.

### 1.2 The author block

`CITATION.cff` contains `REPLACE` placeholders and `verify_all.py` check G3 fails while they
remain. Needed: name, and optionally ORCID. **Affiliation may be "Independent Researcher"** —
no venue in the survey requires an academic affiliation, and arXiv requires only
*endorsement*, which is obtained by requesting a personal endorsement from an author of a
paper you cite, via the "Which authors of this paper are endorsers?" link on that paper's
arXiv page.

The manuscript front matter needs the same block.

---

## 2. Work that is mine to finish

### 2.1 Finish the English translation (6 of 9 sections done)

| File | Sections | Status |
|---|---|---|
| `paper/en/00-abstract.md` | Abstract | done |
| `paper/en/01-intro-02.md` | §1–§2 | done |
| `paper/en/03-04-systems-method.md` | §3–§4 | done |
| `paper/en/09-10-11-discussion-limits-repro.md` | §9–§11 | done |
| `paper/en/05-results-A.md` | §5 | **in flight** |
| `paper/en/06-07-results-BC.md` | §6–§7 | **in flight** |
| `paper/en/08-results-D.md` | §8 | **not started** — deliberately held back until §6–§7 land, so terminology does not drift |

`verify_all.py` check **I5** enforces that each English file covers every numbered section of
its Chinese source, and fails on a leftover `TRANSLATION-CONTINUES-HERE` marker. Read
`paper/TRANSLATION-GLOSSARY.md` sections 5, 6 and 7 before translating anything: they record
every terminology decision made so far and six open questions for the author.

### 2.2 Finish the trace-audit fixes

`results/ERRATA.md` **section 10** lists what is known and NOT yet fixed: 13 paper-text
defects, 12 untraceable numbers, 1 artifact-idempotency defect. The three trace audits
checked roughly 350 printed numbers against the artifacts; most reproduce exactly.

**The most consequential unfixed item** is ERRATA §10.1 item 3: §7.2 never mentions P14's
**prose arm**, which records LLM 46/48, one judge-only item, and **Δ_catch = +0.0435**. That
is the *one* measurable delta in regime 1 and it is **positive**, while the section declares
the regime unmeasurable on the strength of the forced-choice arm alone. Fixing it may weaken
or complicate the paper's central negative claim, which is exactly why it must be faced
rather than left.

### 2.3 Re-run the experiments — NOT YET DONE, and it is the point of the exercise

**IN PROGRESS.** Two artifacts have been re-measured so far and both reproduce exactly:

| artifact | fields compared | differing | what it backs |
|---|---|---|---|
| **P3** | 12 | **0** | the 512/1024 clamps, the 3082/7966/6967-char onsets, the flag firing at 3193 on all three, the +111 / −4773 / −3774 errors, the frozen post-clamp scores |
| **P16** | 49 | **0** | including its NEGATIVE verdict: the clamp effect replicates but the unwarned gap does NOT, because english clamps at 1024 when loaded alone rather than 512, and this run's gap is −3774 against P3's +111 — opposite sign |

P16 matters most of the two, because its published conclusion is a negative result *about the
instrument's own inconsistency*. Re-running it tested whether that negative result is itself
stable. It is. Together the two runs independently confirm the paper's claim that the window is
a function of **(launch loadout × queried checkpoint)**, and that "window = 512" is not a
general property of the engine.

**This is the distinction the re-run exists to draw.** Every artifact-level defect found earlier
in this session — the non-idempotent repair script, the derived field read as a second run, the
control arm with no artifact — sits in the layer of **recording and repair**, not in the layer
of **measurement**. The re-run is separating the two, and so far the measurement layer holds.

Still to re-measure: P17, P18, the P27 family (including whether the idempotency fix restores
the clobbered historical values), and whether the missing P26 control arm can now be produced.

The pre-rerun copies of everything regenerated are preserved under
`results/_superseded/*.pre-rerun`.

The author asked for the experiments to be re-run before submission to confirm they are
sound. All three audit rounds so far **read artifacts**; none **re-measured**. That
distinction matters, because this session found artifact-level problems that only a re-run
can confirm or clear:

- a repair script that ran twice and **overwrote its own historical record** with the
  repaired values (`results/P27b-plugin-crossval.json`), so it is not idempotency-safe;
- a **derived field read as if it were a second run** (the withdrawn Jev latency claim);
- a mock-provider **control arm with no artifact at all**, whose state size coincides with a
  discarded prototype's;
- `p27e`/`p27d` imports with side effects that once forced a `git checkout` restore.

Budget: **≈ $0.08–0.10**, on the author's explicit authorisation. Recorded spend to date is
**$0.0808 across 1,773 API calls**, dominated by P19 (n=1100, $0.0443). The re-run should
follow `README.md`'s three-tier table, respecting its two Tier-2 traps:

1. **the launch loadout must match**, or the state window changes (english clamps at 512
   tokens under a three-checkpoint loadout, 1024 when loaded alone);
2. **the GPU is part of the instrument** — an RTX 5060 Laptop, 8,151 MiB, sm_120.

Do not disturb the running sidecar on port 8787 (≈3,427 calls, 0 failures).

---

## 3. The gate

Nothing is to be pushed, posted, or submitted until the author gives explicit approval.
When that comes, the venue survey and the policy findings above determine where things may
go: GitHub (code + data + paper source), Zenodo (DOI-pinned release), and arXiv /
ChinaXiv for the paper — with the licence split already decided by the author:
**artifacts Apache-2.0, paper CC-BY-4.0**, and the conflict of interest disclosed in both the
README and the paper (**the author maintains `laya-mcp`**).

---

## 4. A note on what this session actually found

Three audit rounds and one translation round did not overturn the direction of the paper's
four claims, but they repeatedly **weakened their strength**, and withdrew three claims
outright:

- §5's "the same script run twice differs greatly" — **the second run does not exist**;
  `915.1` was the pre-repair value of a derived field.
- §5's "truncation explains about 6/10 of the effect" — the control arm **has no artifact**,
  and its state size equals a discarded prototype's.
- §8's propagation chain, plus a **sign error** (−0.243 should be +0.243).

Every one of those corrections **lowered** the paper's claims. That is the correct direction
for a correction to move, and it is the reason the pre-submission audit was worth doing.

---

## 5. Known gap found at the very end: the English reference list is Chinese

paper/en/_assemble.py appends paper/12-references-draft.md to the English manuscript,
because that file is generated from 
eferences.bib and is the single source of truth. But it
is generated in CHINESE -- its entries carry Chinese explanatory notes about provenance and
about known defects of the cited works.

erify_all.py I2 now warns: the English MANUSCRIPT.md contains 3 lines of untranslated
Chinese, all from that appended list.

**Fix options, in order of preference:**

1. Generate a second, English rendering of the reference list from the same 
eferences.bib
   (the generator is src/analysis/p34_bib_to_markdown.py). This keeps one source of truth and
   gives arXiv an all-English document.
2. Have the English assembler append the .bib entries directly, without the Chinese notes.
3. Accept the Chinese list and declare it, if the venue allows.

Option 1 is right if the paper goes to arXiv; the Chinese provenance notes are genuinely
useful and should not simply be dropped, so they want an English rendering rather than removal.
