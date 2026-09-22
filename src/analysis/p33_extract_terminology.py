"""Extract the terminology the English translation must keep consistent.

The manuscript is Chinese and uses a dense technical vocabulary with several coined or
domain-specific terms. A faithful translation has to fix ONE English rendering per term
before any prose is written, or the translation will drift: the same Chinese word becomes
three English words in three sections, and a reader cannot tell whether two things are the
same thing.

This script lists every identifier used in code spans, plus the frequency of the core
Chinese terms, so the glossary can be built from what the paper actually says rather than
from what a translator remembers it saying.
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

T = (PAPER / "MANUSCRIPT.md").read_text(encoding="utf-8")

print("=== code-span identifiers, by frequency (the paper's own vocabulary) ===")
spans = collections.Counter(re.findall(r"`([A-Za-z_][A-Za-z0-9_.\-]{2,45})`", T))
for k, v in spans.most_common(60):
    print(f"  {v:5d}  {k}")

print()
print("=== core Chinese terms, by frequency ===")
CN = ["判定器", "生成器", "判定层", "钳位", "窗口", "载入配置", "loadout", "证书",
      "断言", "条目", "区制", "互补性", "自报字段", "接入层", "真值", "可推导性",
      "截断", "失效模式", "能力塌缩", "校准", "过自信", "长线", "条件正确率",
      "边际", "独立性", "配对", "未配对", "固定", "重复抽样", "逐项标签一致率",
      "仪器", "漂移", "快照", "钉定", "自测", "受限", "外推", "负结果"]
for term in CN:
    n = T.count(term)
    if n:
        print(f"  {n:5d}  {term}")

print()
print("=== section headings (structure the translation must preserve) ===")
for line in T.split("\n"):
    if re.match(r"^#{1,3}\s", line.strip()):
        print("  " + line.strip()[:100])
