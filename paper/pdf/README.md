# The two deposited PDFs

`paper-en.pdf` and `paper-zh.pdf` are the **exact files deposited on Zenodo**. The binary
files are gitignored (they are 10 MB of regenerable output), so in their place this
directory records what they are, how they were made, and a hash that proves a regenerated
copy matches the deposited one.

## Identity of the deposited files

| | English | Chinese |
|---|---|---|
| File | `paper-en.pdf` | `paper-zh.pdf` |
| Bytes | 3,303,619 | 7,038,405 |
| Pages | 100 | 80 |
| Page size | A4 (595 × 842 pt) | A4 (595 × 842 pt) |
| SHA256 | `9d71283c1690ea803128a4c2f4a230582cda4994ce2dc8ef93a3cd1f5d3fc0aa` | `cb2171629ac93656cd4dc8a2eea95546255873fe548342c244b3a8b256ade92d` |
| MD5 | `d320bdf508d017bd31378cc183e859a4` | `69ff34bcf02fbc6ebb4351dd6db7d1ea` |
| Zenodo DOI (unchanged across every revision) | `10.5281/zenodo.22901853` | `10.5281/zenodo.22902025` |

> **These are the revision-3 bytes, and revision 3 is NOT on Zenodo yet.** The rebuild corrected
> the counts the papers state about themselves (`results/ERRATA.md` §13). **What the records hold
> today is revision 2** — the erratum build, same 100 / 80 pages — whose sizes and hashes are
> recorded in `PUBLISHED.md`. `recon/R19-verify-zenodo-edit.py` checks the record against a
> recorded manifest per revision rather than against these local files, precisely so that a
> working tree which has moved ahead is reported as *moved ahead* and not as *upload failed*.

> **Page counts changed from 97/79 to 100/80** in the erratum revision (revision 2). The added
> pages carry defect 6 (the `noul` label defect), the rewritten defect 3 with its measurements
> table, the correction block, and the two `✅ Fixed` notes. A reader comparing versions should
> expect the pagination to differ. **Revision 3 did not change the pagination**: every corrected
> figure kept its digit count (`24`→`62`, `49`→`62`, `11`→`13`), so the layout is identical and
> only the bytes and the hashes moved.

PDF `/Title`, `/Author` and the Zenodo deposit record must all carry the same strings:

- English title: `When a Judgment Layer's Self-Reported Fields Lie: Cost, Latency and the Failure Boundary of Three Judgment Layers on the Same Items`
- Chinese title: `当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测`
  — ⚠️ **the colon is FULL-WIDTH `：` (U+FF1A)**, not the ASCII `:`. The Zenodo record for
  the Chinese deposit was first saved with the half-width colon, so the recorded title and
  the PDF's `/Title` differed in exactly one character. Both were 31 characters long, which
  is why it is easy to miss; only a character-level comparison catches it.
- Author on both: `Perry Link`

**Only the English PDF's title block names the other language version and all three DOIs.** The
Chinese PDF carries the artifact DOI in its §11.5 and **no DOI block in its front matter**, so a
reader holding only `paper-zh.pdf` cannot tell from the file that an English original exists —
which matters, because `PUBLISHED.md` says the English text governs where the two differ. The
asymmetry is real and is recorded as an open item in `PUBLISHED.md`; it is stated here rather than
smoothed over, because the previous version of this file claimed **both** PDFs carried the block
and that was untrue of the Chinese one.

For the English PDF the reason the block exists at all: Zenodo has **no `is translation of`
relation** (verified: not among its 34 relation types), so no machine-readable link can carry the
fact, and the prose in the title block is what does.

## How they were produced

```powershell
# 1. assemble both manuscripts from their section sources
python paper\_assemble.py        # Chinese
python paper\en\_assemble.py     # English

# 2. render print CSS to HTML in both languages
uv run --quiet --no-project --with markdown-it-py python src\analysis\p96_render_html.py

# 3. print to PDF with headers and footers OFF
#    ⚠️ --print-to-pdf MUST be an ABSOLUTE path. Chrome does not resolve a relative one against
#    your shell's working directory: it reports `Failed to write file paper\pdf\paper-en.pdf:
#    The system cannot find the path specified` and exits 0, leaving the PREVIOUS PDF in place.
#    The first revision-3 build was silently a no-op for exactly this reason, and was caught only
#    because the byte count was compared before and after.
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
foreach ($lang in @("en","zh")) {
  $uri  = ([System.Uri](Resolve-Path "paper\dist\$lang.html").Path).AbsoluteUri
  $dest = (Resolve-Path "paper\pdf").Path + "\paper-$lang.pdf"
  & $chrome --headless=new --disable-gpu --no-sandbox `
      --user-data-dir="$env:TEMP\dsh-chrome-pdf" `
      --no-pdf-header-footer --print-to-pdf-no-header `
      --run-all-compositor-stages-before-draw --virtual-time-budget=30000 `
      --print-to-pdf="$dest" $uri
}
Get-ChildItem paper\pdf\*.pdf | Select-Object Name, Length   # verify it actually moved

# 4. stamp metadata, then check what was actually written
python paper\pdf\_set_metadata.py
```

## How to check a regenerated copy

```powershell
python paper\pdf\_verify_pdf.py     # A4, no header/footer, full text, CJK sanity
python paper\pdf\_check_chrome.py   # positional proof there is no running header/footer
python paper\pdf\_titles.py         # prints the exact title string to type into Zenodo
```

`_set_metadata.py` is a **no-op when the metadata is already correct**, on purpose: PyMuPDF
stamps `/ModDate` on every save, so re-saving an unchanged file still moved the bytes
(measured — two consecutive runs produced four different hashes). Running the tools must
not change the hash of the deposited artifact, or the hash proves nothing.

## Things worth remembering

**The English PDF had no title for 97 pages.** Until this was fixed, `paper/dist/en.html`
opened at `# Abstract`: the renderer writes the title into the HTML `<title>` tag but not
into the body, and `paper/MANUSCRIPT.md` (Chinese) happens to carry its title block in the
markdown while `paper/en/MANUSCRIPT.md` did not. The Chinese PDF looked correct the whole
time, which is why nobody noticed the English one was missing a front page. The English
title block now lives in `paper/en/_assemble.py`.

**Three separate detectors reported false failures before one worked.** Each was a bug in
the check, not a defect in the document:

1. looking for `(...)Tj` found nothing, because Chrome emits hex-encoded glyph runs;
2. decoding those runs with all fonts' `ToUnicode` CMaps merged produced
   "rusually sold on the grounds that it saves money", because glyph ids collide across
   subset fonts;
3. flagging any page ending in `N/M` flagged nine pages of legitimate content — `(21/46)`,
   `6/30`, `40/68, 43/68` are fractions, not page numbers.

A fourth flagged `Delta_catch` as missing when the manuscript writes `Δ_catch`. Hence
`_verify_pdf.py` (PyMuPDF — which was installed all along) plus `_check_chrome.py`, which
settles the header/footer question **positionally**: text in the top or bottom 16 mm of a
page. The measured answer is **zero blocks in either band on all 180 pages** (100 + 80), with the
text block running 20.4 mm from the top and 20.7 mm from the bottom, matching the `@page`
rule's 20 mm margins.
