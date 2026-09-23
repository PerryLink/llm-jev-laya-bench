# What is published, and where

**This is the single place that lists every published record for this project.** It exists
because the project's output had spread across eight records in two services, and no single
document listed them — while three separate hand-off documents (`SUBMISSION-PLAN.md`,
`ZENODO-STEPS.md`, `ZENODO-FORM.md`) described the submission process at three different
times with partly superseded instructions. The next reader would have had to reconcile them.

Last verified: 2026-09-23, against the live APIs, not against memory.

---

## ⏳ Revision 3 (the stated counts) — rebuilt and verified, **NOT yet uploaded**

Both PDFs were rebuilt on **2026-09-23** to correct two figures the papers state about
themselves (`results/ERRATA.md` §13):

| what was wrong | what revision 2 says | what revision 3 says |
|---|---|---|
| one script described twice, with two different totals | §11 said `24`, §13 said `49`, while the gate printed 59 at the first build and 60 at the erratum build | **62**, in both places |
| ERRATA's own section count | stated as `11`, stale by one the moment §12 was appended | **13** |

Two new gate checks — `L1` and `L2` — now hold those figures, and
`src/analysis/p97_sync_declared_counts.py` rewrites all 22 sites that state them, taking **both
numbers from their sources** (it runs the gate and reads its total; it counts `ERRATA.md`) rather
than typing them in. The previous correction of this same defect failed for exactly that reason:
see §13.3 of the errata.

| | English | Chinese |
|---|---|---|
| PDF | 3,303,619 B · md5 `d320bdf508d017bd31378cc183e859a4` | 7,038,405 B · md5 `69ff34bcf02fbc6ebb4351dd6db7d1ea` |
| `MANUSCRIPT.md` | 280,617 B · md5 `9feb155e8cb2143edcca7e05c82d2b92` | 234,119 B · md5 `d88f58ee72bac78e29cd20248b6667bd` |
| pagination | 100 pp, unchanged | 80 pp, unchanged |
| verification | `paper/verify_all.py` → **62 passed, 0 warnings, 0 failures**; A4 and no header/footer on all 180 pages; both PDFs carry the corrected figures and no stale one | same |

**The upload has not been made, by the author's instruction.** Until it is, the records hold
revision 2 and the local files are one revision ahead —
`recon/R19-verify-zenodo-edit.py` reports exactly that (revision 2 by default, `--rev 3` for the
post-upload check), because it compares each record against a **recorded manifest per revision**
rather than against whatever the working tree currently holds.

**The upload is the same in-place file edit used for revision 2**, so the DOIs are unaffected and
again nothing downstream needs changing.

---

## ✅ Revision 2, the erratum — deposited (in place, 2026-09-23)

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

| record | DOI (unchanged) | concept DOI | files as deposited (revision 2) |
|---|---|---|---|
| English paper | `10.5281/zenodo.22901853` | `10.5281/zenodo.22901852` | `paper-en.pdf` 3,303,623 B · md5 `e2df8e260850731b6564cc593f6ed758` · sha256 `49bc1412945cad4b35294c517b1b2e33ea481301f771cbee01f28a176a0b2d1d` · `MANUSCRIPT.md` 280,617 B · md5 `761801c8f4de27d4330b4e151e5311eb` |
| Chinese paper | `10.5281/zenodo.22902025` | `10.5281/zenodo.22902024` | `paper-zh.pdf` 7,038,415 B · md5 `b87f99acaad538449afde2b1b996a091` · sha256 `d6764a8aafb3b5117a7586f3997aa4d574bfb11b5da239440b260d997c643eff` · `MANUSCRIPT.md` 234,119 B · md5 `c9abe32ac003a128a5fff66d8768b833` |

*These are the hashes of the bytes the records hold **today**. They are recorded here, and in
`recon/R19-verify-zenodo-edit.py`'s revision-2 manifest, so that the deposited revision stays
verifiable after the working tree moves on to revision 3.*

**Consequence: nothing downstream needed changing.** `CITATION.cff`, `README.md`, §11 of both
manuscripts and the profile all cite the DOIs that still resolve to this content, so no third
iteration was required.

This also **closed** the previously open item "English record: PDF is the pre-DOI-block build".
The deposited English PDF is a fresh build whose front matter carries all three DOIs, and its
page count is 100, not 97.

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
| **Revision 3 upload** | **Rebuilt and verified, not uploaded** — the author's instruction. It is the same in-place file edit, so DOIs are unaffected. `recon/R19-verify-zenodo-edit.py --rev 3` is the post-upload check. |
| **arXiv (cs.CL)** | **Blocked on endorsement.** Everything else is ready. Independent of the Zenodo line — do not wait on one for the other. |
| **Chinese PDF has no DOI block in its front matter** | The English PDF names the other language version and all three DOIs; the Chinese PDF names only the artifact DOI, in §11.5. A reader holding only `paper-zh.pdf` therefore cannot see from the file that an English original exists — and the English text governs where they differ. **Deliberately not changed in revision 3**: the author approved a count correction, and this would be new content. Recorded here as a decision, not overlooked. |
| English record: neither its Description nor its related-works names the Chinese version | Verified against the live API: the English Description (11,291 chars) contains neither the Chinese DOI nor any word for the translation, and its only related work is `isSupplementedBy` → the artifact. The Chinese record links back (`isDerivedFrom` → the English DOI) and opens by naming the English original. So the relationship is discoverable in one direction only. **The English PDF does carry it in its front matter**, so a reader who opens the file sees it; one who reads only the record page does not. |
| Artifact record: Description does not name the papers | Related-works already links artifact → paper, so this is optional. |
| Credential rotation | `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`. Preventive only — the artifact tree holds **0** credentials, verified. Incident on record: `protocol/INCIDENT-credential-echo.md`. |

---

## How to verify any of this

```powershell
python paper/verify_all.py                 # 62 checks: paper vs artifacts, 62/0/0
python paper/pdf/_verify_pdf.py            # the two deposited PDFs: A4, no header/footer, full text
python paper/pdf/_check_chrome.py          # positional proof there is no running header/footer
python paper/pdf/_baseline_now.py          # current hashes of the four deliverable files
python paper/pdf/_prepush_scan.py          # credential scan before any push
python src/analysis/p97_sync_declared_counts.py --check   # stated counts still match their sources
python src/analysis/p98_line_ending_audit.py             # no edit rewrote a file's line endings
python src/analysis/p28_recompute_all_stats.py   # every interval and exact test, stdlib only
python src/analysis/p30_inventory.py             # evidence counts, derived not typed
```

`p97` takes both figures it enforces **from their sources** — it runs the gate and reads the total
the gate prints, and it counts `ERRATA.md` — so there is no number inside it that can go stale.
`L1` and `L2` in the gate enforce the same two properties on every commit. `p98` exists because
`.gitattributes` sets `* -text` deliberately, so in this repository a line-ending change is a real
change rather than a normalisation: the first run of `p97` silently converted nine files from LF
to CRLF and `p98` is what reports that class of mistake.

The four deliverable files and their SHA256 are recorded in
[`paper/pdf/README.md`](paper/pdf/README.md); regenerating them is a copy-paste of the
commands in that file.

---

## The submission documents, and which is current

| File | Status |
|---|---|
| **`PUBLISHED.md`** (this file) | **current** — the record of what exists |
| **`ZENODO-EDIT-STEPS.md`** | **current** — the in-place Edit procedure, updated to **revision 3**'s byte counts and md5s. Both revisions used this same route. |
| `ZENODO-ERRATUM-STEPS.md` | ⛔ **withdrawn.** It describes the *new version* route, which was not taken, and its stated reason — that the files could not be edited because the 30-day window had closed — **was false when written** (one day had passed). Kept for the route itself, with the error withdrawn in place. |
| `ZENODO-FORM.md` | current as a field-by-field guide; carries the two corrected traps (`chi`, and `Languages` searching by name not code) |
| `ZENODO-STEPS.md` | **partly superseded** — written against the older wizard-style form. Kept for the abstract-extraction step, but where it disagrees with `ZENODO-FORM.md`, the latter is right. Notably it once instructed `is translation of`, which does not exist. |
| `SUBMISSION-PLAN.md` | **partly superseded** — the venue plan. The Zenodo half is done; the arXiv half is the open item. |
| `RELEASE.md` | current for tagging and releasing the artifact |
| `NEXT-STEPS.md` | historical round plan; no open items of its own |
