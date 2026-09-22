# Third-party components

This repository contains code and data that are not original to it. Each is listed with its
licence and the obligations that follow.

---

## 1. `protocol/instrument-snapshot/` — Apache-2.0

**What it is.** A verbatim frozen copy of 13 modules + 2 configs from **`laya-mcp` 0.2.1**,
a *separate* project by the same author:

- upstream: <https://github.com/PerryLink/laya-mcp>
- package: `laya-mcp` on PyPI
- licence: Apache-2.0 (see `protocol/instrument-snapshot/` and the repository `LICENSE`)

**Why a copy exists here at all.** The sidecar was under active development during the
measurement campaign — `worker.py` was rewritten three times in one session. Publishing a
number attributed to a moving target would be meaningless, so the revision the measurements
belong to is frozen here and pinned by SHA256 in `PIN.json`.
`src/instrument/run_pinned_sidecar.py` re-hashes all 13 modules and **refuses to launch** on
a mismatch.

**Obligations, and how they are met.**

| Apache-2.0 requirement | How |
|---|---|
| Include a copy of the licence | repository `LICENSE`; the package's own `LICENSE` is preserved in the snapshot |
| State changes made | the snapshot is **byte-identical to upstream 0.2.1** — no changes. `PIN.json` records every hash, so this is checkable rather than asserted |
| Retain notices | upstream copyright and licence headers are unmodified |

**This is not a fork.** Do not develop against it. Install `laya-mcp` from PyPI, or clone the
upstream repository.

**Also note**: the `laya` *model* package (`laya>=0.3.4,<0.4`, a dependency of `laya-mcp`) is
a further upstream component and is **not** included here. Neither are the model weights.

---

## 2. `data/banking77/` — CC-BY-4.0

**What it is.** The Banking77 intent-classification dataset.

- upstream: <https://github.com/PolyAI-LDN/task-specific-datasets>
- licence: **Creative Commons Attribution 4.0 International** (the upstream `LICENSE` file)
- citation: Casanueva et al., *Efficient Intent Detection with Dual Sentence Encoders*,
  Proceedings of the 2nd Workshop on NLP for ConvAI (ACL 2020).
  <https://arxiv.org/abs/2003.04807>

**Attribution.** The dataset is used unmodified, solely as an evaluation item pool. Creator
identification, the copyright notice, the licence notice and the upstream URI are given
here and in `data/banking77/README.md`.

**Redistribution.** CC-BY-4.0 permits redistribution with attribution, so shipping the CSVs
is lawful. It is nevertheless **discouraged**, and `.gitignore` excludes them by default:
a vendored copy becomes a second source of truth that silently goes stale, and only the
hash actually matters for reproducibility. Prefer `src/analysis/fetch_data.py`, which
downloads and verifies a SHA256.

**A finding about this dataset belongs to the paper, not to this notice.** Banking77 is
in Laya's prior training set, and the paper states that the LLM's exposure is *stronger*
still — so contamination runs **with** the negative result rather than against it. See the
paper's limitations section. No accuracy claim in this repository should be read without it.

---

## 3. Quoted material

`protocol/`, `recon/` and `probes/` quote vendor documentation and third-party claims for
provenance. Those quotes remain the property of their authors and are included as evidence
of what was claimed at a recorded time, not as endorsement. Where a vendor figure is quoted
it is labelled as **self-reported and not independently reproduced**, in keeping with
`recon/R2-verified-externals.md`, which forbids third-party paraphrase as paper evidence.

---

## 4. Not included

- Model weights for any checkpoint.
- Credentials of any kind. `protocol/INCIDENT-credential-echo.md` records a credential
  value that once reached a session log; no credential value is present in this tree, and
  no script prints one.
- The sibling `laya-family` development checkout, its virtualenv, or its logs.
