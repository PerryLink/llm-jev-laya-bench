"""Fix the size-matched ratio: 1.94 is a number the live artifact contradicts at 1.49.

The paper prints the plugin-vs-wall-clock latency ratio as 1.94 in three Chinese places (and three
English ones). The live P27b now reads `ratio_of_medians_matched = 1.49`, because only the
DENOMINATOR moved: the size-matched wall-clock p50 went 956.2 -> 1244.8 ms when the P27c ladder
was re-measured.

Section 5.2 was itself a correction -- the paper replaced the unmatched ratio with the size-matched
one and explained why. That was right. But it fixed the STATE SIZE, not the LATENCY, and this
project has just established that Jev's latency is the quantity that does not reproduce. A ratio
whose denominator moves 20% between runs is a property of one run, not of the plugin.

The honest form is a range that names BOTH artifacts, so the reader sees the cause rather than a
bare interval. A range with no cause reads as sloppiness; a range with a cause reads as a
measurement -- and this one is a demonstration of the paper's own thesis.

The section's real finding survives and is stated separately: p50 stays roughly FLAT across a 127x
state increase in both runs (published +12%, re-run -10%). The SHAPE reproduces; only the LEVEL
moves, by 4-33%.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(PAPER_PLACEHOLDER := str(Path(__file__).resolve().parents[2])))
from bench_env import PAPER  # noqa: E402

ZH_NOTE = ("**⚠️ 第八轮更正：该比值不是一个稳定数字。** 它是两个**延迟测量**之比，而 §5.2 本身已确立"
           "**Jev 的延迟正是那个不复现的量**（同状态、同 n、同成本、同 token 数：p50 1,191.8 → 952.9 ms，−20%；"
           "max 4,018.6 → 6,360.4 ms，+58%）。**尺寸匹配的档位是完好的**（两次同为 126 字符 / 347 token / n=5），"
           "移动的是**该档自己的 p50：956.2 → 1,244.8 ms**。故正确的表述是 "
           "**约 1.5–1.9 倍**：对修复前产物为 **1.94**，对当前产物为 **1.49**。"
           "**该节的实质发现不受影响**：p50 跨 127× 状态增长基本持平——两次运行方向一致（修复前 +12%，重跑 −10%），"
           "**形状复现，只有量级随环境移动 4–33%**。")

EN_NOTE = (" (**⚠️ Eighth-round correction: this ratio is not a stable number.** It is a ratio "
           "between two LATENCY measurements, and section 5.2 itself establishes that Jev's "
           "latency is the quantity that does not reproduce -- same state, same n, same cost, "
           "same token count: p50 1,191.8 -> 952.9 ms (-20%), max 4,018.6 -> 6,360.4 ms (+58%). "
           "**The size-matched rung is intact** (126 characters / 347 tokens / n=5 in both runs); "
           "what moved is that rung's own p50, 956.2 -> 1,244.8 ms. The correct statement is "
           "therefore **about 1.5-1.9x**: **1.94** against the pre-repair artifact and **1.49** "
           "against the current one. **The section's substantive finding is unaffected**: p50 "
           "stays roughly flat across a 127x state increase, in the same direction in both runs "
           "(+12% published, -10% re-run) -- **the SHAPE reproduces; only the level moves with "
           "the environment, by 4-33%**.)")

ZH = [
    (PAPER / "05-results-A-draft.md",
     "⇒ **插件的自报延迟约为独立墙钟的 1.94 倍**（**同尺寸状态**对比）。",
     "⇒ **插件的自报延迟约为独立墙钟的 1.5–1.9 倍**（**同尺寸状态**对比）。" + ZH_NOTE),
    (PAPER / "06-results-B-draft.md",
     "约为独立墙钟的 **1.94 倍**",
     "约为独立墙钟的 **1.5–1.9 倍**"),
    (PAPER / "04-method-draft.md",
     "**尺寸匹配时 1.94×",
     "**尺寸匹配时 1.5–1.9×"),
]

for path, old, new in ZH:
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    {path.name}: {old[:44]}")
    else:
        print(f"  MISS  {path.name}: {old[:44]}")

EN = [
    (PAPER / "en" / "05-results-A.md",
     "**The plugin's self-reported latency is about 1.94× the independent wall clock**",
     "**The plugin's self-reported latency is about 1.5-1.9× the independent wall clock**" + EN_NOTE),
    (PAPER / "en" / "06-07-results-BC.md", "about **1.94×**", "about **1.5-1.9×**"),
    (PAPER / "en" / "03-04-systems-method.md", "**1.94× when size-matched**",
     "**1.5-1.9× when size-matched**"),
]

for path, old, new in EN:
    if not path.exists():
        continue
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"  ok    en/{path.name}: {old[:44]}")
    else:
        print(f"  MISS  en/{path.name}: {old[:44]}")
