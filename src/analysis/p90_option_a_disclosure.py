"""Option A: keep the published chain battery as the measurement of record, and disclose the
re-measurement prominently in the body. Plus: collapse the duplicated markers p76/p77 left.

WHY OPTION A (the author's argument, recorded here so the script can be read against it)
--------------------------------------------------------------------------------------
The published battery is what the paper's claims rest on and what its text describes. The
generator changed AFTER the artifact was made, so the published battery is the correct
measurement OF THE PROTOCOL THE PAPER DESCRIBES; substituting the re-measured one would rewrite
every regime-3 number to describe a protocol the paper never claimed to have run. The central
negative result is unaffected either way (Delta_catch stays negative in 3/3 draws).

BUT THE DISCLOSURE IS NOT A FOOTNOTE. Putting the ignore-SUPERSEDED value into the options moves
Delta_catch from -0.233/-0.247/-0.182 to -0.056/-0.099/-0.066, Fisher p from 0.086/0.049/0.163 to
0.787/0.425/0.595, and phi from +0.24/+0.26/+0.19 to +0.06/+0.11/+0.07. That says the regime-3
effect is substantially a function of HOW THE OPTIONS ARE BUILT -- the paper's own thesis applied
to the paper's own central measurement. A reader who learns the shared-failure reading was
already weak, and then learns that a defensible change to the option set halves the effect, has
learned something the paper should be telling them.

WHAT THIS SCRIPT DOES
  1. de-duplicates the untraceable-number markers: p76/p77 appended them once per run, so some
     sentences currently carry the same caveat two or three times in a row;
  2. inserts the disclosure table in section 7.6.1, immediately after the fixed-battery results
     (both languages);
  3. adds the one-sentence qualification to the section's ruling (7.5) and a limitation (7.9).

The pinned copies the disclosure cites are byte-identical duplicates of each other, asserted here
and again by K2/K11 in `verify_all.py`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER, ROOT  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                # noqa: BLE001
    pass


def load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "src" / "analysis" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ 0. the pinned copies
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


PIN = {}
for i in (1, 2, 3):
    a = ROOT / "results" / "_superseded" / f"P22b-fixed-r{i}.json.pre-repair"
    b = ROOT / "rerun" / "baseline" / f"P22b-fixed-r{i}.json"
    assert a.exists() and b.exists(), f"pinned copy missing for r{i}"
    assert sha(a) == sha(b), f"the two pinned copies of r{i} differ -- the citation is unsafe"
    PIN[i] = sha(a)[:12]
print(f"  ok    pinned copies agree byte-for-byte: {PIN}")

DISCLOSURE_ZH = """
**⚠️ 重测披露（第九轮新增；写在正文，不是脚注）：本电池在重跑中被重测，而重测出的电池【不是】本表这一个。**
生成器在本产物生成**之后**才改变：现版本会把「忽略作废」的值**优先插入选项**，故**只有 2 条**条目不含该值（本表所依据的版本是 **7 条**）——**选项集因此不同**；而判定器是 (state, options) 的确定性函数，**其标签在 68 条中有 24 条改变**，这证明差别来自**构造**而非抽样噪声。

| 读数（n=68，三次固定抽样） | **本表：已发表电池（论文所述协议）** | 重测电池（生成器已改） |
|---|---|---|
| 判定器总体 | 0.2941（3 次逐位相同） | 0.2794（3 次逐位相同） |
| 仅判定器对 | 3 / 3 / 4 | **8 / 7 / 7** |
| **Δ_catch** | **−0.233 / −0.247 / −0.182** | **−0.056 / −0.099 / −0.066** |
| Fisher 精确 p（2×2） | 0.086 / 0.049 / 0.163 | **0.787 / 0.425 / 0.595** |
| φ（失败相关） | +0.24 / +0.26 / +0.19 | **+0.06 / +0.11 / +0.07** |
| 单侧二项下尾（对判定器边际） | 0.076 / 0.061 / 0.149 | 0.443 / 0.330 / 0.413 |

→ **这不是复现性脚注，而是对本区制主张的直接限定**：**只要把「忽略作废」的值放进选项，Δ_catch 的幅度就减半以上**——即**区制三的效应在很大程度上是「选项如何构造」的函数**。这正是本文的中心论题用在本项目自己的中心测量上。
→ **两句必须并置**：(a) **方向不变**——Δ_catch 在 **3/3** 次抽样中仍为负，故**中心负结果「无互补」不受影响**；(b) **但「与共享失效一致」这一正面读法失去了它原本就微弱的支持**：Fisher p 由「3 次中 1 次仅未校正显著」变为「三次都远不显著」（0.425–0.787），φ 由 +0.19…+0.26 降到 +0.06…+0.11。
→ **本文以已发表电池为准**（理由：它是**论文所述协议**的测量，生成器是在产物生成之后才改变的）。其逐字节副本保存在 **`results\\_superseded\\P22b-fixed-r1..r3.json.pre-repair`** 与 **`rerun\\baseline\\P22b-fixed-r1..r3.json`**（两份互为逐字节相同；sha256 前缀 **`{pin1}` / `{pin2}` / `{pin3}`**）；重测电池存于 `results\\P22b-fixed-r1..r3.json`。**读者可用后者独立复核本披露。**
→ **⚠️ 由此，条款 17 的「判定臂 100%」也必须读作「在已发表电池上」的性质**：它在**选项集未变的条目上 61/61 = 100%**；重测电池的选项集变动条数是 **2**（原为 7），故该读数的口径**随电池而变，不得跨电池引用**。
→ **⚠️ 而 `results\\P28-recomputed-statistics.json` 的 `regime3` 块是从【当前】产物重算的**，故它现在记的是**重测电池**的数（Δ_catch −0.056 / −0.099 / −0.066，基率 0.2794）。**本表的数字以两份 pinned 副本为准**；`paper\\verify_all.py` 的 **K2 检查即对 pinned 副本重算**，不对当前产物重算——这一分工是刻意写进检查里的。
"""

DISCLOSURE_EN = """
**⚠️ Re-measurement disclosed (ninth round; in the body, not a footnote): this battery was
re-measured during the re-run, and the battery that came back is NOT the one in the table above.**
The generator changed **after** this artifact was produced: the current version **inserts the
ignore-SUPERSEDED value among the options**, so only **2** items lack it (the version this table
rests on had **7**) — **the option sets therefore differ**, and since the judge is a deterministic
function of (state, options), **24 of its 68 labels change**, which makes this a change of
CONSTRUCTION rather than sampling noise.

| reading (n=68, three pinned draws) | **this table: the published battery (the protocol the paper describes)** | the re-measured battery (generator changed) |
|---|---|---|
| judge overall | 0.2941 (bit-identical 3/3) | 0.2794 (bit-identical 3/3) |
| judge-only-correct | 3 / 3 / 4 | **8 / 7 / 7** |
| **Δ_catch** | **−0.233 / −0.247 / −0.182** | **−0.056 / −0.099 / −0.066** |
| Fisher exact p (2×2) | 0.086 / 0.049 / 0.163 | **0.787 / 0.425 / 0.595** |
| φ (failure correlation) | +0.24 / +0.26 / +0.19 | **+0.06 / +0.11 / +0.07** |
| one-sided binomial lower tail (vs the judge's marginal) | 0.076 / 0.061 / 0.149 | 0.443 / 0.330 / 0.413 |

→ **This is not a reproducibility footnote; it is a direct qualification of this regime's claim**:
**merely putting the ignore-SUPERSEDED value among the options more than halves Δ_catch** — i.e.
**the regime-3 effect is substantially a function of how the options are built**. That is this
paper's own thesis applied to the paper's own central measurement.
→ **Two statements must be read together**: (a) **the direction is unchanged** — Δ_catch is still
negative in **3/3** draws, so **the central negative result, "no complementarity", is unaffected**;
(b) **but the positive reading, "consistent with shared failure", loses the support it had, which
was already weak**: Fisher p goes from "1 of 3 significant uncorrected" to "nowhere near
significant in any draw" (0.425–0.787), and φ falls from +0.19…+0.26 to +0.06…+0.11.
→ **The paper reports the published battery as the measurement of record** (it is the measurement
of **the protocol the paper describes**; the generator changed only after the artifact was made).
Byte-identical copies are kept at **`results\\_superseded\\P22b-fixed-r1..r3.json.pre-repair`** and
**`rerun\\baseline\\P22b-fixed-r1..r3.json`** (the two are byte-identical to each other; sha256
prefixes **`{pin1}` / `{pin2}` / `{pin3}`**); the re-measured battery is
`results\\P22b-fixed-r1..r3.json`. **A reader can check this disclosure against the latter.**
→ **⚠️ Consequently clause 17's "judge arm = 100%" must also be read as a property of the PUBLISHED
battery**: it is **61/61 = 100% on items whose option set did not change**; in the re-measured
battery the number of changed option sets is **2** (it was 7), so that figure's denominator is
battery-specific and **must not be quoted across batteries**.
→ **⚠️ And `results\\P28-recomputed-statistics.json`'s `regime3` block is recomputed from the
CURRENT artifacts**, so it now holds the **re-measured** battery's numbers (Δ_catch −0.056 /
−0.099 / −0.066, baseline 0.2794). **The table above is pinned to the two pre-rerun copies**;
`paper\\verify_all.py`'s **K2 check recomputes from those pinned copies, not from the live
artifacts** — that division is deliberate and is written into the check.
"""

EDITS: list[tuple] = [
    # ---------------------------------------------------------------- 2. the disclosure block
    ("08-results-D-draft.md",
     "**四条关键读数**：",
     DISCLOSURE_ZH.format(pin1=PIN[1], pin2=PIN[2], pin3=PIN[3])
     + "\n**四条关键读数**：",
     "§7.6.1: the option-set disclosure (zh)"),

    ("en/08-results-D.md",
     "**Four key readings**:",
     DISCLOSURE_EN.format(pin1=PIN[1], pin2=PIN[2], pin3=PIN[3])
     + "\n**Four key readings**:",
     "§7.6.1: the option-set disclosure (en)"),

    # ---------------------------------------------------------------- 3. ruling and limitation
    ("08-results-D-draft.md",
     "且失败相关**在 3/3 次抽样中为正**——即证据**与「共享失效」一致**，而非互补。",
     "且失败相关**在 3/3 次抽样中为正**——即证据**与「共享失效」一致**，而非互补。"
     "**⚠️ 但这句话在第九轮被加了一条限定（见 §8.6.1 的重测披露）**：把「忽略作废」的值放进选项后，"
     "Δ_catch 由 **−0.233…−0.182** 变为 **−0.056…−0.066**、φ 由 +0.19…+0.26 降到 +0.06…+0.11——"
     "**方向不变，幅度是选项构造的函数**；「与共享失效一致」的读法在重测下失去原本就微弱的支持。",
     "§7.5: the ruling's option-set qualification (zh)"),

    ("en/08-results-D.md",
     "and the failure correlation is **positive in 3/3 draws** — i.e. the evidence is **consistent with \"shared failure\"**, rather than being complementarity.",
     "and the failure correlation is **positive in 3/3 draws** — i.e. the evidence is **consistent with \"shared failure\"**, rather than being complementarity. "
     "**⚠️ In the ninth round that sentence acquired a qualification (see the re-measurement disclosure in §8.6.1)**: "
     "putting the ignore-SUPERSEDED value among the options moves Δ_catch from **−0.233…−0.182** to **−0.056…−0.066** and φ from +0.19…+0.26 down to +0.06…+0.11 — "
     "**the direction is unchanged and the magnitude is a function of how the options are built**; the \"consistent with shared failure\" reading loses the weak support it had.",
     "§7.5: the ruling's option-set qualification (en)"),

    ("08-results-D-draft.md",
     "5. **LLM 只测了一个配置**（`deepseek-flash`、非思考、单次采样）。",
     "5. **LLM 只测了一个配置**（`deepseek-flash`、非思考、单次采样）；\n"
     "6. **区制三的效应幅度对「选项如何构造」敏感**（重测披露，§8.6.1）：Δ_catch 在两种选项策略下为 **−0.18…−0.25** 与 **−0.06…−0.10**。"
     "**能跨电池成立的只有符号（3/3 次为负）与「上限已破除」，效应量不得跨电池引用。**",
     "§7.9: the option-set limitation (zh)"),

    ("en/08-results-D.md",
     "5. **The LLM was measured in only one configuration** (`deepseek-flash`, non-thinking, single draw).",
     "5. **The LLM was measured in only one configuration** (`deepseek-flash`, non-thinking, single draw);\n"
     "6. **Regime three's effect magnitude is sensitive to how the options are built** (re-measurement disclosure, §8.6.1): Δ_catch is **−0.18…−0.25** under one option policy and **−0.06…−0.10** under the other. "
     "**Only the sign (negative in 3/3 draws) and \"the ceiling has been broken\" carry across batteries; the effect size must not be quoted across them.**",
     "en §7.9: the option-set limitation"),
]


def dedupe_markers() -> int:
    """Collapse every marker p76/p77 appended more than once down to one copy."""
    removed = 0
    for mod_name, sub in (("p76_mark_untraceable_numbers", None),
                          ("p77_sync_english_untraceable", "en")):
        mod = load(mod_name)
        root = PAPER / sub if sub else PAPER
        per_file: dict[str, str] = {}
        tails = []
        for entry in mod.EDITS:
            fname, old, new = entry[0], entry[1], entry[2]
            if new.startswith(old):
                tails.append((fname, new[len(old):]))
            elif new.endswith(old):
                tails.append((fname, new[:-len(old)]))
        # longest first, so a tail that contains another cannot be shortened by it
        for fname, tail in sorted(tails, key=lambda p: -len(p[1])):
            if not tail.strip():
                continue
            t = per_file.get(fname) or (root / fname).read_text(encoding="utf-8")
            n = t.count(tail)
            while t.count(tail) > 1:
                t = t.replace(tail, "", 1)
                removed += 1
            per_file[fname] = t
        for fname, t in per_file.items():
            (root / fname).write_text(t, encoding="utf-8")
    return removed


def main() -> int:
    n = dedupe_markers()
    print(f"  ok    collapsed {n} duplicated untraceable-number marker(s)")

    miss = 0
    for entry in EDITS:
        fname, old, new, label = entry
        p = PAPER / fname
        t = p.read_text(encoding="utf-8")
        if new in t:
            print(f"  ok    {label} (already applied)")
        elif old in t:
            p.write_text(t.replace(old, new, 1), encoding="utf-8")
            print(f"  ok    {label}")
        else:
            print(f"  MISS  {label}")
            miss += 1

    print(f"\n{miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
