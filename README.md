# When a Judgment Layer's Self-Reported Fields Lie

**Cost, latency and failure boundaries of three judgment layers on a common item set**

> **This is a measurement and characterisation study, not an algorithm paper.**
> Of four claims, three hold independently — *cost is not the binding constraint*;
> *access-layer self-reported fields are not trustworthy*; *capability collapses where the
> task requires noticing an absence* — and **the fourth, that a heterogeneous judge provides
> incremental coverage over the generator, is NOT supported in any of three task regimes**.
> The paper's own wording and numbers are deliberately bounded to what the evidence carries.

---

## Verify the paper's numbers in about two minutes, with no installs

The paper's inferential statistics were previously computed ad hoc, in throwaway interpreter
sessions. An audit found that **two cells of a published confidence-interval row could not be
reproduced by any implementation** — one of them was a Wald value carrying a Newcombe label.
That is fixed, and the fix is executable:

```bash
python src/analysis/p28_recompute_all_stats.py   # every interval and exact test
python src/analysis/p30_inventory.py             # the evidence inventory, derived not typed
python paper/verify_all.py                       # 24 checks over paper and artifacts
```

**All three run on a bare Python 3.12 — standard library only.** No scipy, no pandas, no
statsmodels, no GPU, no network, no API keys. If a number in the manuscript disagrees with
`results/P28-recomputed-statistics.json`, that is a bug and we want to know.

---

## Three tiers of reproducibility — read this before running anything

The artifact does **not** have one reproducibility story. It has three, and conflating them
is how a reader concludes "it doesn't reproduce" when they were missing a GPU.

| Tier | What | Requirements | Cost |
|---|---|---|---|
| **1. Re-derive every statistic** | `src/analysis/*`, `paper/verify_all.py` | **Python 3.12, nothing else** | **$0** |
| **2. Re-run the instrument sweeps** | P3, P16, P17, P18, P1, P5–P9 (clamp, window, loadout) | The local Laya sidecar: `torch` + `laya` + **~8 GB VRAM**, and **the same launch loadout** | **$0** (local) |
| **3. Re-run the judgment batteries** | P14, P15b, P19, P21, P22b, P23, P24, Jev P27 | Paid **DeepSeek** access, and paid **TypeSafe Jev** access | **≈ $0.08** for all of it |

**Two traps in Tier 2, both of which have bitten this project:**

- **The loadout must match.** The context window is a function of *(launch loadout × queried
  checkpoint)*, not of the checkpoint alone: the `english` checkpoint clamps at **512** tokens
  under a three-checkpoint loadout and at **1024** when loaded alone. Run the sweep with the
  wrong loadout and the headline number moves by a factor of two.
- **The GPU is part of the instrument.** The published clamp values were taken on the card
  named in `protocol/INSTRUMENT-FREEZE.json`. A different card is not guaranteed to reproduce
  them.

**Tier 3 costs less than you think.** Summed from the recorded artifacts: **$0.0808 across
1,773 API calls.** The dominant term is the n=1100 calibration battery at $0.0443.

---

## Point it at your own machine

Nothing is hardcoded. `bench_env.py` walks up to the repository root and resolves the rest,
with every path overridable by environment variable:

```bash
python bench_env.py        # prints exactly what was resolved, and what is missing
```

```
LAYA_ROOT          the sibling `laya-family` checkout   (venv, models, sidecar source)
LAYA_VENV_PYTHON   interpreter that can import `laya_mcp`
LAYA_MODEL_ROOT    the three checkpoint snapshots
DSH_CREDENTIALS    credential store, default ~/.dsh/.credentials.yaml
LAYA_PORT          default 8787
```

Credentials are read at runtime and **never** stored, logged or committed.

---

## What is in here

```
paper/        manuscript + section drafts + the assembler + verify_all.py
               MANUSCRIPT.md is GENERATED from the *-draft.md files; edit the drafts.
src/analysis/ the tier-1 scripts: statistics, inventory, data fetch
src/instrument/ sidecar client, pinned launcher, Jev client, LLM client, probe scripts
src/items/    the batteries themselves
results/      42 machine-readable artifacts, each with provenance
               ERRATA.md  -- 10 sections recording superseded or retracted fields
               _superseded/ -- byte-copies of artifacts as they stood before repair
protocol/     pinned instrument snapshot, freeze record, audit findings, incident record
probes/       22 measurement reports      recon/  20 reconnaissance and audit reports
decisions/    the four decision records that fixed scope
```

**`results/` is a measurement record, not a build output.** Its own policy
(`results/ERRATA.md`) is that stale fields are *documented rather than silently rewritten*;
where a repair was arithmetic rather than a re-measurement, the original is preserved under
`results/_superseded/` so the change can be checked.

---

## Two disclosures

**1. Conflict of interest — the author maintains one of the systems being evaluated.**
**Laya**, the local typed-decision judge, is the author's own published project
(`laya-mcp`, <https://github.com/PerryLink/laya-mcp>). This repository reports it scoring
**0.225 end-to-end** on the 77-class battery and failing to detect absences, while the LLM it
was meant to back up scores 0.75–0.90. The negative result is partly *about the author's own
tool*. This is stated here, and belongs in the paper, because a reader should not have to
discover it.

**2. AI assistance — stated plainly, because the policies require it and because it is true.**
The experiments, the analysis code, the audits and the drafting were carried out by an AI
agent under the human author's direction and review. The author takes full responsibility for
every claim in the paper and every number in `results/`, irrespective of how the content was
generated — which is exactly what [arXiv's policy](https://info.arxiv.org/help/moderation/index.html)
requires of a signing author.

What makes that defensible rather than merely disclosed is the verification trail, and it is
the same trail a reader can run:

- `paper/verify_all.py` — **24 executable checks**, all passing
- `src/analysis/p28_recompute_all_stats.py` — every statistic recomputable from scratch
- `src/analysis/p30_inventory.py` — evidence counts **derived**, not typed by hand
- `results/ERRATA.md` — 10 sections of self-reported defects, including two that overturned
  the authors' own prior conclusions
- five rounds of adversarial audit, of which `protocol/AUDIT-FINDINGS.md` is the record

arXiv's stated penalty applies to submissions showing *"incontrovertible evidence that the
authors did not check the results of LLM generation"* — hallucinated references, or leftover
model chatter like *"here is a 200 word summary"*. This tree contains neither: the scanner
for both is `paper/verify_all.py`, and the paper cites only sources that were opened and
checked by hand.

> **⚠️ PENDING — do not publish this file as written.** The AI-disclosure wording above and
> the author block in `CITATION.cff` are drafts awaiting the author's decision; `verify_all.py`
> reports both as warnings on every run. The reference list now exists
> (`paper/references.bib` → `paper/12-references-draft.md`, **41 entries, every one verified
> against a fetched primary source**), and building it changed three claims in the paper:
> a novelty claim that prior work had already covered, a miscited attribution of
> overconfidence, and an unsupported use of "cheap" to describe a process reward model.
> Those are fixed in the text. See `paper/AI-DISCLOSURE-DRAFT.md` for the open decision.

---

## Citing

See `CITATION.cff`. Cite both the paper and the archived artifact (Zenodo DOI, added at the
first tagged release). The artifact is licensed **Apache-2.0**; the paper is licensed
**CC-BY-4.0**. Third-party components and their obligations are in
[`THIRD-PARTY.md`](THIRD-PARTY.md) — note in particular that
`protocol/instrument-snapshot/` is a verbatim copy of a separate Apache-2.0 project and is
**not** a fork to develop against.
