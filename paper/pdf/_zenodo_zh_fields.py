"""Print the Chinese deposit's field values, ready to copy-paste.

Same reasoning as the English one: the title must match the PDF's embedded
/Title and the printed H1 exactly, and the abstract is 4,268 characters of
markdown that nobody should retype.  So they are extracted, not retyped.

Also puts the Chinese title on the clipboard, since it is the field most likely
to be mistyped (full-width colon, nine characters of subtitle).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]


def section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.strip() == heading:
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    for l in lines[start:]:
        if l.strip().startswith("## ") or l.strip() == "---":
            break
        out.append(l)
    return "\n".join(out).strip("\n")


zh = (ROOT / "paper" / "00-abstract-draft.md").read_text(encoding="utf-8")

title = "当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测"
body = section(zh, "## 摘要正文")
kw = section(zh, "## 关键词").replace("\n", " ").replace(" · ", "; ")

print("=" * 70)
print("中文稿 —— 逐字复制")
print("=" * 70)
print(f"\nTITLE:\n{title}\n")
print("AUTHORS/CREATORS:  Family name = Link   Given names = Perry")
print("RESOURCE TYPE:     Publication / Preprint")
print("LICENSE:           CC BY 4.0")
print("LANGUAGE:          输 zho -> Chinese")
print(f"KEYWORDS:\n{kw}\n")
print("RELATED WORKS (两条):")
print("  1) is supplemented by   10.5281/zenodo.22901248   Software")
print("  2) is translation of    10.5281/zenodo.22901853   Preprint")
print(f"\nDESCRIPTION ({len(body):,} chars, {body.count(chr(10)) + 1} lines):")
print(body)

try:
    subprocess.run(["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                   input=title.encode("utf-8"), check=True)
    print("\n[已复制] 中文标题在剪贴板里，直接粘贴到 Title 框")
except Exception as e:                                       # pragma: no cover
    print(f"\n[剪贴板不可用: {e}]")
