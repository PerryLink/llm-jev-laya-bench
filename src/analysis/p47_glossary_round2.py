"""Record the terminology decisions from the section 3-4 translation.

The translator surfaced thirteen judgment calls rather than improvising. Four of them recur
paper-wide, so they must be fixed globally or §5-§8 will use different English for the same
Chinese. Recorded here and in the glossary.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

G = PAPER / "TRANSLATION-GLOSSARY.md"
g = G.read_text(encoding="utf-8")

ADD = """
## 7. Terms fixed by the section 3-4 translation

These recur paper-wide. Fixing them now keeps §5-§8 consistent with §3-§4; without that,
the same Chinese would appear as different English in different sections and a reader could
not tell whether two things are the same thing.

| Chinese | English | Note |
|---|---|---|
| 载体 / 带载体 / 去载体 | **carrier** / with carrier / carrier removed | Needed for §7 and §8 to match; chosen partly because P5b's own artifact label, quoted in the source, reads "ANSWERABLE BUT NOT CARRIER-REQUIRED" |
| 口径 | **conventions** | As in "Versions and collection conventions", "Conventions for cost and latency". Recurs paper-wide. Distinct from 测量点 = "measurement point", which must NOT be collapsed into it |
| 启动配置 | **launch loadout** | The source uses 启动配置 while the glossary maps 载入配置 to "launch loadout"; the paper writes `loadout` in English beside both. Unified deliberately. **If the author intends a distinction, §3.2's row label must become "launch configuration"** |
| 判定 (as the third row label in the §4.5 table) | **verdict** | NOT "judgment", which is reserved for 判定器 = judge and 判定层 = judgment layer |
| 归属 | **Attribution** | Heading, table column, and the per-defect lines. NOT "ownership" and NOT "provenance" (already used for 溯源记录) |
| 挂靠 | what they are **attached to** | Colloquial Chinese; kept plain. A gloss like "which number they are attached to" is clearer if the author prefers |
| 写法 | **the writing** | As in "a defect in the writing masquerading as a conclusion about the object". NOT the abstract's "specification-level semantic defect", which is broader than §3's claim |
| 定位 / 小结 | this section's **transferable conclusions** | NOT "scope", which collides with 适用范围 |

### Rendering conventions

- **Ratios**: normalised to the form the approved abstract uses -- 1.8 倍 becomes 1.8×, and
  翻倍 becomes "double". Numbers unchanged; the 倍-vs-× typographic distinction is not
  preserved. Consequence: "347 token" becomes "347-token" where adjectival.
- **Blockquotes** are re-wrapped to ~110 columns rather than kept as single long lines. The
  rendered output is identical; a raw line-by-line diff against the Chinese will show this
  as noise.
- **不得 + 本文** becomes "We must not ..." rather than "This paper must not ...", per
  glossary rule 3.1, which forbids addressing meta-instructions to the reader. Where the
  Chinese states a practice rather than a prohibition (不声称), "we do not claim" is used.

### A note on the brief for §3-§4

Two instructions in the translation brief did not apply to those files, and the translator
correctly reported that rather than forcing a fit: 依据 occurs zero times in §3 and §4 (the
23 protocol clauses with "依据：" are §7), and the round markers are 第七轮 (once) and 第五轮
(twice), not the 第六轮/第七轮 pair the brief named. **The brief was written from the abstract's
vocabulary, not from the files.** Worth remembering when briefing the remaining sections.
"""

if "## 7. Terms fixed by the section 3-4 translation" not in g:
    G.write_text(g.rstrip() + "\n" + ADD, encoding="utf-8")
    print("  ok    glossary section 7 added")
else:
    print("  already present")
