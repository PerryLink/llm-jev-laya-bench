"""Resolve the two translation defects the translator flagged, and extend the glossary.

The translator surfaced eight judgment calls. Six are genuine author decisions and are
recorded in paper/TRANSLATION-GLOSSARY.md section 5 as open questions. Two are defects with
a clearly correct answer, and are fixed here:

  1. FALSE FRIEND. "不可行动轴" was rendered "Non-actionable axis". In English
     "non-actionable" means "not practicable", not "cannot act" -- the opposite of the
     intended sense, which is that the judge cannot take actions at all. Fixed to
     "Cannot-act axis".
  2. INTERNAL INCONSISTENCY. The approved abstract says "judge-only-correct" while the new
     translation says "typed-only correct" for the same statistic, and "judge" vs "typed
     judge" for the same arm. Two files in the same deliverable must not disagree.
     Unified on the abstract's wording, since the abstract was approved first.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

EN = PAPER / "en"
ok = miss = 0


def sub(path: Path, old: str, new: str, label: str) -> None:
    global ok, miss
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new), encoding="utf-8")
        print(f"  ok    {label}")
        ok += 1
    else:
        print(f"  MISS  {label}")
        miss += 1


# ---- defect 1: the false friend ------------------------------------------------------
for f in sorted(EN.glob("*.md")):
    t = f.read_text(encoding="utf-8")
    if "Non-actionable axis" in t or "non-actionable axis" in t:
        sub(f, "Non-actionable axis", "Cannot-act axis", f"{f.name}: the false friend")

# ---- defect 2: unify the statistics vocabulary on the approved abstract --------------
for f in sorted(EN.glob("*.md")):
    if f.name == "00-abstract.md":
        continue
    t = f.read_text(encoding="utf-8")
    if "typed-only correct" in t or "Typed judge" in t or "typed judge" in t:
        t2 = (t.replace("typed-only correct", "judge-only-correct")
                .replace("Typed judge", "Judge")
                .replace("typed judge", "judge"))
        f.write_text(t2, encoding="utf-8")
        print(f"  ok    {f.name}: unified on judge / judge-only-correct")
        ok += 1

# ---- extend the glossary with what the translation proved was missing -----------------
G = PAPER / "TRANSLATION-GLOSSARY.md"
g = G.read_text(encoding="utf-8")
if "## 5. Open questions" not in g:
    g += """

---

## 5. Open questions raised by the first translation round

The translator of §1–§2 surfaced eight judgment calls rather than improvising. Two were
defects and are fixed (see `src/analysis/p46_fix_translation_terms.py`); six are decisions
for the author:

1. **§1.1 is syntactically ambiguous in the Chinese.** 「三者都在 10⁻⁵ 美元量级，最贵的组合跑完一次
   运行的判断层约 1.2 美分」 — is 判断层 the subject of the cost, or is 「跑完一次运行的判断层」
   one noun phrase? The English currently reads "the most expensive combination's judgment
   layer, over one complete run, is about 1.2 cents", which differs from the approved
   abstract's "the most expensive LLM configuration costs about 1.2 cents to complete one
   120-checkpoint run". **The Chinese should be checked, and the two brought into line.**
2. **「一个在小概率上自信地错」** — "confidently wrong at low probability" vs "on
   low-probability items". Genuinely ambiguous; the two readings say different things.
3. **「状态条件判别器」 vs 「判别式（条件）概率分类器」** — rendered "state-conditioned" and
   "conditional" respectively. Deliberate (the second is the standard term) but worth
   confirming.
4. **「改写」 vs the abstract's "restate"** — the same claim is introduced two ways in two
   files.
5. **【】as an emphasis device** — rendered as italics inside bold rather than kept as
   full-width brackets. Revert if glyph-for-glyph traceability matters more than English
   typography.
6. **「能力塌缩」** — the glossary asks for it to be flagged as a coinage; the translator
   added quotation marks but no prose saying so, correctly refusing to add text. **If the
   coinage should be flagged inline, that is an author decision and must be made in BOTH
   languages.**

## 6. Terms the glossary was missing, now fixed by usage

These were used consistently across §1–§2 and should be carried forward:

| Chinese | English |
|---|---|
| 判断层 | judgment layer (same English as 判定层; 判定层 does not occur in §1–§2) |
| 异种 / 异种判定器 | heterogeneous / heterogeneous judge |
| 触顶 / 上限已破除 | hits the ceiling / the ceiling has been broken |
| 墙钟 / 客户端墙钟 | wall clock / client-side wall clock |
| 静默丢弃 / 告警 | silently discards / warns |
| 冻结条目 | frozen items |
| 校准电池 | calibration battery |
| 常数预测器 | constant predictor |
| 增量 | increment — deliberately NOT "contribution" or "novelty", so it stays distinct from the paper's separate novelty claim |
| 同族 / 并非同族 | same family / not the same family |
| 对标对象 | point of comparison (not "benchmark") |
| 来源等级 / 一手 / 官方一手 / 第三方转述 | source tier / first-hand / official first-hand / third-party relay |
| 基座 | the base model |
| 不可行动轴 | **Cannot-act axis** (NOT "Non-actionable axis" — that English phrase means "not practicable") |
"""
    G.write_text(g, encoding="utf-8")
    print("  ok    TRANSLATION-GLOSSARY.md: sections 5 and 6 added")

print(f"\n{ok} applied, {miss} not found")
sys.exit(1 if miss else 0)
