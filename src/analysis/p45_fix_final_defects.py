"""Final pass on the trace-audit defects: the three patterns that did not match, plus the
section-8 staleness and overclaim items."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

# --- the three that missed: match on a distinctive fragment, not the whole sentence -----
FRAGMENTS = [
    ("06-results-B-draft.md", "0.9981", "0.9989",
     "§6 M2: the highest confidence",
     "**（⚠️ 第八轮更正：原印 0.9981，但紧接的下一行印着 0.9989，"
     "`recon\\R13-laya-probe.md:456` 亦记 0.9989——原句自相矛盾）**"),
    ("06-results-B-draft.md", "`insufficient`", "`undecided`",
     "§6 M6: the mock's verdict label",
     "**（⚠️ 第八轮更正：原印 `insufficient`，但被引来源记录的恰恰相反——"
     "`recon\\R12-jev-probe.md:307` 的逐字夹具返回 `undecided`；"
     "`insufficient` 只记在另一个夹具上。一个夹具各记一边，普遍化措辞不被所引来源支持）**"),
]

# --- section-8 staleness, overclaims and the undisambiguated MDE ------------------------
S8 = [
    ("| **LLM** | **误差复合**：K≥8 后准确率随链长下降（**K=4 仍为 1.000，故非单调**；见 §7.6.2） | ✅ 是 |",
     "| **LLM** | **一次跌落**：K=4→K=8 之间下降，此后平坦（**非误差复合**——K=8 与 K=16 的 p = 1.000，机制未定，见 §7.6.2） | ⚠️ **否** |",
     "§8 stale: the error-compounding mechanism"),
    ("这正是 Δ_catch ≈ 0 的结构性原因",
     "这正是 Δ_catch 为负的结构性背景（**⚠️ 第八轮更正：原印「Δ_catch ≈ 0」是修复前的 −0.007；修复版三次为 −0.182…−0.247**）",
     "§8 stale: Δ_catch ≈ 0"),
    ("| 链式核验（K=2…16） | 某行被标记作废 | **0.25–0.42（恒定）** | 0.83 → 1.00 → 0.42（K≥8 后下降，**非单调**）|",
     "| 链式核验（K=2…16） | 某行被标记作废 | **0.25–0.42（恒定）** | **0.917 → 1.000 → 0.508 → 0.507**（修复版三次合并；K≥8 后平坦，**非单调**）|",
     "§8 stale: the summary row used pilot per-K values"),
    ("**⚠️ 仍未解决的效力问题**：本电池 MDE（80% power）= **0.28–0.30**",
     "**⚠️ 仍未解决的效力问题**：本电池（**三个固定抽样**）MDE（80% power）= **0.28–0.30**"
     "（**⚠️ 与 §7.6 中修复前电池的 0.311 不是同一个量**——后者是 n=69 单次抽样）",
     "§8: the undisambiguated MDE"),
    ("（b）把 `P(Laya 对 | LLM 错)` 与**独立性基线 0.2941** 相比，三个 **Wilson 95% CI 全部包含基线**",
     "（b）把 `P(Laya 对 | LLM 错)` 与**独立性基线 0.2941** 相比，三个 **Wilson 95% CI 全部包含基线**"
     "（**⚠️ 同处的单侧 p = 0.052 / 0.043 / 0.103 是正态近似，不是精确值**；"
     "精确二项下尾为 **0.076 / 0.061 / 0.149**，一律不显著）",
     "§8: the unlabelled normal approximation"),
]

# --- §7.2: the prose arm has a POSITIVE Δ_catch and is never mentioned ------------------
S7 = [
    ("**LLM 一次都没错**",
     "**在该强制选择臂上 LLM 一次都没错**（**⚠️ 第八轮补充：同一产物的「散文臂」不是这样**——"
     "`complementarity_prose_arm` 记录 LLM 46/48、仅判定器对 1 条、**Δ_catch = +0.0435**。"
     "**这是区制一唯一可测的 Δ_catch，且符号为正**，第 7.2 节此前完全未提；"
     "该产物的 `_provenance.published_figures_at_risk` 本就列着「prose arm 0.958」）",
     "§7 O1: the omitted prose arm"),
]


def main() -> int:
    ok = miss = 0
    cache: dict[str, str] = {}

    def get(f: str) -> str:
        if f not in cache:
            cache[f] = (PAPER / f).read_text(encoding="utf-8")
        return cache[f]

    # fragment-based replacements with an appended note
    for fname, old, new, label, note in FRAGMENTS:
        t = get(fname)
        if old in t:
            # replace only the FIRST occurrence that looks like the claim, then append the note
            i = t.index(old)
            t = t[:i] + new + t[i + len(old):]
            # put the note at the end of that line
            line_end = t.index("\n", i)
            t = t[:line_end] + " " + note + t[line_end:]
            cache[fname] = t
            print(f"  ok    {label}")
            ok += 1
        else:
            print(f"  MISS  {label}")
            miss += 1

    for fname, edits in (("08-results-D-draft.md", S8), ("07-results-C-draft.md", S7)):
        for old, new, label in edits:
            t = get(fname)
            if old in t:
                cache[fname] = t.replace(old, new, 1)
                print(f"  ok    {label}")
                ok += 1
            else:
                print(f"  MISS  {label}")
                miss += 1

    for f, t in cache.items():
        (PAPER / f).write_text(t, encoding="utf-8")
    print(f"\n{ok} applied, {miss} not found")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
