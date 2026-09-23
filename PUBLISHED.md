# What is published, and where

**This is the single place that lists every published record for this project.** It exists
because the project's output had spread across eight records in two services, and no single
document listed them — while three separate hand-off documents (`SUBMISSION-PLAN.md`,
`ZENODO-STEPS.md`, `ZENODO-FORM.md`) described the submission process at three different
times with partly superseded instructions. The next reader would have had to reconcile them.

Last verified: 2026-09-23, against the live APIs, not against memory.

---

## ✅ The erratum revision is deposited (in place, 2026-09-23)

Both papers were corrected and extended on **2026-09-23** (`results/ERRATA.md` §12), and the
corrected files were put into the **existing records by in-place file edit** — the route the
author chose, which leaves every DOI untouched.

| what changed | effect |
|---|---|
| defect 3 rewritten — the 6.33 chars/token claim was attached to the wrong text, and its magnitude was wrong | pagination **97 → 100** (English), **79 → 80** (Chinese) |
| **defect 6 added** — the `noul` label defect (upstream laya#156) | pagination changed |
| a `✅ Fixed` note on defects 2 and 3 (`laya-mcp` 0.2.3) | pagination changed |
| the artifact count 42 → 43 | text only |

**Verified against the live records** (`recon/R19-verify-zenodo-edit.py`, exit 0): both records
carry files whose md5 **and** byte count match the local corrected files, both **DOIs and concept
DOIs are unchanged**, and both PDFs contain the erratum content (defect 6, the retraction markers,
the corrected 4.31 / 1.949 / 1.239 figures).

| record | DOI (unchanged) | concept DOI | files now |
|---|---|---|---|
| English paper | `10.5281/zenodo.22901853` | `10.5281/zenodo.22901852` | `paper-en.pdf` 3,303,623 · `MANUSCRIPT.md` 280,617 |
| Chinese paper | `10.5281/zenodo.22902025` | `10.5281/zenodo.22902024` | `paper-zh.pdf` 7,038,415 · `MANUSCRIPT.md` 234,119 |

**Consequence: nothing downstream needed changing.** `CITATION.cff`, `README.md`, §11 of both
manuscripts and the profile all cite the DOIs that still resolve to this content, so no third
iteration was required.

### Known and accepted: the Chinese title's colon

The PDF's embedded `/Title` and its printed title block use the **full-width** `：` (U+FF1A); the
Zenodo record's title field shows the **half-width** `:` (U+003A). Attempts to set the full-width
form reverted after saving, so Zenodo appears to normalise it.

**Recorded rather than retried, by the author's decision.** It is a one-character difference in a
metadata display field; the DOI, the authors, the language, the licence, the files and both titles'
*words* are all correct. Anyone who needs the exact published title string should take it from the
PDF.

*The alternative — a new version — was declined because it would have forced a further iteration to
cite the new DOI. The tradeoff is set out in `ZENODO-EDIT-VS-VERSION.md`.*

---

## The eight records

| # | What | Where | Identifier |
|---|---|---|---|
| 1 | **Paper** (English, original) | Zenodo | [10.5281/zenodo.22901853](https://doi.org/10.5281/zenodo.22901853) |
| 2 | **Paper** (Chinese translation) | Zenodo | [10.5281/zenodo.22902025](https://doi.org/10.5281/zenodo.22902025) |
| 3 | **Artifact** (code + every `results/` JSON) | Zenodo | concept [10.5281/zenodo.22901248](https://doi.org/10.5281/zenodo.22901248) → v1.0.2 |
| 4 | Artifact, v1.0.2 version DOI | Zenodo | `10.5281/zenodo.22901355` |
| 5 | Artifact, v1.0.1 version DOI | Zenodo | `10.5281/zenodo.22901249` |
| 6 | Source + audit trail | GitHub | [PerryLink/llm-jev-laya-bench](https://github.com/PerryLink/llm-jev-laya-bench) (tag `v1.0.2`) |
| 7 | Concept DOI for the papers | Zenodo | `10.5281/zenodo.22901852` (English) · `10.5281/zenodo.22902024` (Chinese) |
| 8 | The instrument the measurements are attributed to | Zenodo-adjacent | `protocol/instrument-snapshot/` — a byte-identical copy of `laya-mcp` 0.2.1, **never edit** |

**Records 7 exist but are not what you cite.** A concept DOI is the version-family root; it
resolves to the latest version and is what you use when you mean "whatever the current
version is". For citation, use the version DOIs in rows 1, 2 and 3.

---

## Which DOI to cite for what

| You want to cite… | Use | Not |
|---|---|---|
| the measurements, claims, numbers | **row 1** (English paper) | the artifact |
| the same, in Chinese | **row 2** | row 1 |
| the code, the `results/` JSONs, the audit trail | **row 3** (artifact concept DOI) | the paper |
| a frozen snapshot of the code | row 4 (`22901355`, v1.0.2) | row 3 |

> ⚠️ **Rows 1 and 2 are language versions of ONE piece of work, not two papers.**
> **Cite one, not both**, and do not present them as two independent works. Where they
> differ, **the English text governs**.
>
> Zenodo has **no `is translation of` relation** — verified against its own vocabulary
> (34 relation types, `istranslationof` absent). So the machine-readable link that would
> normally prevent a duplicate-submission reading **cannot exist**, and the fact is carried
> instead by prose in each PDF's front matter and in each record's Description. That prose
> is load-bearing, not decoration.

---

## Licences

| Work | Licence |
|---|---|
| Artifact (code) | **Apache-2.0** |
| Papers (both languages) | **CC-BY-4.0** |
| Third-party components | see [`THIRD-PARTY.md`](THIRD-PARTY.md); `protocol/instrument-snapshot/` is a verbatim copy of a separate Apache-2.0 project and is **not** a fork to develop against |

---

## Disclosures carried in the papers

- **AI assistance** — long-form disclosure, in both languages, inside the manuscripts.
- **Conflict of interest** — the author maintains `laya-mcp`, which is the access layer for
  one of the three systems measured, and it is reported as scoring 0.225. Disclosed in both
  languages and in the README.

---

## Still open

| Item | State |
|---|---|
| **arXiv (cs.CL)** | **Blocked on endorsement.** Everything else is ready. Independent of the Zenodo line — do not wait on one for the other. |
| English record: Description lacks the translation sentence | The Chinese record carries it; the English one does not, so the relationship is discoverable in one direction only. |
| English record: PDF is the pre-DOI-block build | Same page count (97), so it is invisible from outside. Cosmetic. |
| Artifact record: Description does not name the papers | Related-works already links artifact → paper, so this is optional. |
| Credential rotation | `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`. Preventive only — the artifact tree holds **0** credentials, verified. Incident on record: `protocol/INCIDENT-credential-echo.md`. |

---

## How to verify any of this

```powershell
python paper/verify_all.py                 # 59 checks: paper vs artifacts, 59/0/0
python paper/pdf/_verify_pdf.py            # the two deposited PDFs: A4, no header/footer, full text
python paper/pdf/_check_chrome.py          # positional proof there is no running header/footer
python paper/pdf/_baseline_now.py          # current hashes of the four deliverable files
python paper/pdf/_prepush_scan.py          # credential scan before any push
python src/analysis/p28_recompute_all_stats.py   # every interval and exact test, stdlib only
python src/analysis/p30_inventory.py             # evidence counts, derived not typed
```

The four deliverable files and their SHA256 are recorded in
[`paper/pdf/README.md`](paper/pdf/README.md); regenerating them is a copy-paste of the
commands in that file.

---

## The submission documents, and which is current

| File | Status |
|---|---|
| **`PUBLISHED.md`** (this file) | **current** — the record of what exists |
| `ZENODO-FORM.md` | current as a field-by-field guide; carries the two corrected traps (`chi`, and `Languages` searching by name not code) |
| `ZENODO-STEPS.md` | **partly superseded** — written against the older wizard-style form. Kept for the abstract-extraction step, but where it disagrees with `ZENODO-FORM.md`, the latter is right. Notably it once instructed `is translation of`, which does not exist. |
| `SUBMISSION-PLAN.md` | **partly superseded** — the venue plan. The Zenodo half is done; the arXiv half is the open item. |
| `RELEASE.md` | current for tagging and releasing the artifact |
| `NEXT-STEPS.md` | historical round plan; no open items of its own |
