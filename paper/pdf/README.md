# The two deposited PDFs

`paper-en.pdf` and `paper-zh.pdf` are the **exact files deposited on Zenodo**. The binary
files are gitignored (they are 10 MB of regenerable output), so in their place this
directory records what they are, how they were made, and a hash that proves a regenerated
copy matches the deposited one.

## Identity of the deposited files

| | English | Chinese |
|---|---|---|
| File | `paper-en.pdf` | `paper-zh.pdf` |
| Bytes | 3,303,623 | 7,038,415 |
| Pages | 100 | 80 |
| Page size | A4 (595 × 842 pt) | A4 (595 × 842 pt) |
| SHA256 | `49bc1412945cad4b35294c517b1b2e33ea481301f771cbee01f28a176a0b2d1d` | `d6764a8aafb3b5117a7586f3997aa4d574bfb11b5da239440b260d997c643eff` |
| Zenodo DOI, v1 (97 / 79 pp) | `10.5281/zenodo.22901853` | `10.5281/zenodo.22902025` |
| Zenodo DOI, v2 (erratum) | see `PUBLISHED.md` | see `PUBLISHED.md` |

> **Page counts changed from 97/79 to 100/80** in the erratum revision. The added pages carry
> defect 6 (the `noul` label defect), the rewritten defect 3 with its measurements table, the
> correction block, and the two `✅ Fixed` notes. A reader comparing versions should expect the
> pagination to differ.

PDF `/Title`, `/Author` and the Zenodo deposit record must all carry the same strings:

- English title: `When a Judgment Layer's Self-Reported Fields Lie: Cost, Latency and the Failure Boundary of Three Judgment Layers on the Same Items`
- Chinese title: `当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测`
  — ⚠️ **the colon is FULL-WIDTH `：` (U+FF1A)**, not the ASCII `:`. The Zenodo record for
  the Chinese deposit was first saved with the half-width colon, so the recorded title and
  the PDF's `/Title` differed in exactly one character. Both were 31 characters long, which
  is why it is easy to miss; only a character-level comparison catches it.
- Author on both: `Perry Link`

Each PDF's title block also names the other language version and all three DOIs, so a
reader holding **only a PDF** can tell the translation from a duplicate submission. Zenodo
has **no `is translation of` relation** (verified: not among its 34 relation types), so no
machine-readable link can carry that fact — the prose in the title block is what does.

## How they were produced

```powershell
# 1. assemble the English manuscript (Chinese is hand-authored at paper/MANUSCRIPT.md)
python paper\en\_assemble.py

# 2. render print CSS to HTML in both languages
uv run --quiet --no-project --with markdown-it-py python src\analysis\p96_render_html.py

# 3. print to PDF with headers and footers OFF
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
foreach ($lang in @("en","zh")) {
  $uri = ([System.Uri](Resolve-Path "paper\dist\$lang.html").Path).AbsoluteUri
  & $chrome --headless=new --disable-gpu --no-sandbox `
      --user-data-dir="$env:TEMP\dsh-chrome-pdf" `
      --no-pdf-header-footer --print-to-pdf-no-header `
      --run-all-compositor-stages-before-draw --virtual-time-budget=30000 `
      --print-to-pdf="paper\pdf\paper-$lang.pdf" $uri
}

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
page. The measured answer is zero blocks in either band on all 176 pages, with the text
block running 20.4 mm from the top and 20.7 mm from the bottom, matching the `@page`
rule's 20 mm margins.
