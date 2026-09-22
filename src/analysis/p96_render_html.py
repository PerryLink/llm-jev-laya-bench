"""Render the manuscripts to print-ready HTML for PDF export via the browser.

No PDF toolchain is installed (no pandoc, no LaTeX, no weasyprint), and installing one is
heavier than the problem deserves. Browsers already have a PDF engine and already have CJK
fonts, so the cleanest path is: render to HTML with print CSS, open it, print to PDF.

The CSS is written for paper, not for screen:
  * A4 with 20mm margins, 11pt body, 1.55 line height
  * CJK and Latin font stacks that fall back sensibly
  * tables that do not overflow the page, with header repeat
  * blockquotes and the paper's warning markers kept visually distinct
  * page-break rules so headings do not strand at the foot of a page
  * `@page` so the browser's default header/footer can be turned off

Usage:
    python src/analysis/p96_render_html.py          # both languages
Then open paper/dist/en.html (or zh.html) and print to PDF.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

from markdown_it import MarkdownIt  # noqa: E402

OUT = PAPER / "dist"

CSS = """
@page { size: A4; margin: 20mm 18mm; }
* { box-sizing: border-box; }
body {
  font-family: "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC",
               "Times New Roman", Georgia, serif;
  font-size: 11pt; line-height: 1.55; color: #111; margin: 0;
  -webkit-text-size-adjust: 100%;
}
main { max-width: 46em; margin: 0 auto; padding: 0 4mm; }
h1, h2, h3, h4 {
  font-family: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC",
               "Helvetica Neue", Arial, sans-serif;
  line-height: 1.3; margin: 1.6em 0 .6em; break-after: avoid; page-break-after: avoid;
}
h1 { font-size: 1.6em; border-bottom: 2px solid #222; padding-bottom: .25em; }
h2 { font-size: 1.28em; border-bottom: 1px solid #ccc; padding-bottom: .2em; }
h3 { font-size: 1.1em; }
h4 { font-size: 1em; font-style: italic; }
p, li { orphans: 2; widows: 2; }
p { margin: .6em 0; }
a { color: #0b4f9e; text-decoration: none; word-break: break-all; }
code, pre, kbd {
  font-family: "Cascadia Mono", "SF Mono", Consolas, "Liberation Mono", monospace;
  font-size: .88em;
}
code { background: #f4f4f5; padding: .1em .3em; border-radius: 3px; }
pre {
  background: #f7f7f8; border: 1px solid #e3e3e6; border-radius: 5px;
  padding: .7em .9em; overflow-wrap: anywhere; white-space: pre-wrap;
  break-inside: avoid; page-break-inside: avoid;
}
pre code { background: none; padding: 0; }
table {
  border-collapse: collapse; width: 100%; margin: .9em 0; font-size: .93em;
  break-inside: auto;
}
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td { border: 1px solid #cfcfd4; padding: .35em .55em; text-align: left;
         vertical-align: top; }
th { background: #f0f0f3; font-weight: 600; }
blockquote {
  margin: .8em 0; padding: .55em .9em; border-left: 3px solid #b9b9c0;
  background: #fafafb; break-inside: avoid;
}
blockquote p { margin: .3em 0; }
hr { border: none; border-top: 1px solid #d8d8dd; margin: 2em 0; }
ul, ol { padding-left: 1.5em; }
img { max-width: 100%; }
strong { font-weight: 700; }
del { color: #888; }
""".strip()

TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""

JOBS = [
    ("en", PAPER / "en" / "MANUSCRIPT.md", OUT / "en.html",
     "When a Judgment Layer's Self-Reported Fields Lie"),
    ("zh", PAPER / "MANUSCRIPT.md", OUT / "zh.html",
     "当判定层的自报字段说谎时"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    md = MarkdownIt("commonmark", {"html": True, "linkify": False}).enable("table")
    rc = 0
    for lang, src, dst, title in JOBS:
        if not src.exists():
            print(f"  MISS  {src}")
            rc = 1
            continue
        text = src.read_text(encoding="utf-8")
        body = md.render(text)
        dst.write_text(TEMPLATE.format(lang=lang, title=html.escape(title),
                                       css=CSS, body=body), encoding="utf-8")
        print(f"  ok    {dst.relative_to(PAPER.parent)}  "
              f"({len(text):,} md chars -> {len(body):,} html)")
    print()
    print("Open the .html in a browser, then Print -> Save as PDF.")
    print("In the print dialog: margins = Default/None, and UNTICK headers & footers")
    print("so arXiv/Zenodo do not receive the URL and page-number furniture.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
