"""ERRATA 10.1 items 1, 8, 9, 10 and 12 -- the five defects in `07-results-C-draft.md`.

WHY EACH ONE MATTERS
--------------------
  * item 8  the reliability table printed 5 of the artifact's 10 bins and asserted "the two
            ends are, if anything, acceptable". The five omitted bins include the two LARGEST
            miscalibrations in the whole table (+0.939 at n=1, +0.343 at n=22, both at the low
            end). A table that drops half its rows while generalising over all of them is not a
            rounding choice; it is the failure this paper is about -- and the dropped rows are
            the ones that contradict the sentence under them.
  * item 1  "the highest confidence in the whole probe (0.9981)" is exceeded by the NEXT row's
            0.9989 -- in the paper, and in the source itself (`recon/R13-laya-probe.md:430`
            vs `:456`). Two earlier fix scripts tried to repair this and both MISSed, because
            they were pointed at `06-results-B-draft.md`; the sentence has never been there.
  * item 9  the capability profile prints the SAME 48-item battery twice (LLM row, judge row).
            P14's `_provenance.consumes` records that it pairs item-by-item against P9b, so the
            two rows are the two arms of one paired comparison, not two measurements.
  * item 10 "centre about 0.875" is the MEDIAN; the mean of the four draws is 0.850 -- and
            three of those four draws are `P15b` files, cited as `P15`.
  * item 12 the clause-counting note is arithmetically impossible: it says one clause was
            deleted from an original "14-17" and the section is now "14-21". Four clauses minus
            one is not eight. What the note SHOULD say is checkable and is stated instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

C = "07-results-C-draft.md"

# The ten bins, verbatim from `results/P19-calibration.json` -> summary.laya.calibration.bins.
# `gap` there is empirical_rate - mean_stated_p, the same direction as this table's column, so
# these are transcriptions, not computations. n sums to 1,100, which is P19's own n.
RELIABILITY_OLD = """| 箱 | n | 声称 P(true) | 实测频率 | **差距** |
|---|---|---|---|---|
| 0.4–0.5 | 169 | 0.453 | 0.148 | **−0.305** |
| 0.5–0.6 | 199 | 0.547 | 0.261 | **−0.286** |
| 0.6–0.7 | 184 | 0.651 | 0.370 | **−0.281** |
| 0.7–0.8 | 176 | 0.749 | 0.540 | **−0.210** |
| 0.9–1.0 | 47 | 0.922 | 0.830 | −0.093 |

→ **中段系统性高出实测 21–31 个百分点，两端反而尚可。**"""

RELIABILITY_NEW = """**差距 = 实测频率 − 声称 P(true)**（与产物 `P19-calibration.json` 的 `gap` 字段同向）。

| 箱 | n | 声称 P(true) | 实测频率 | **差距** |
|---|---|---|---|---|
| **0.0–0.1** | **1** | 0.061 | 1.000 | **+0.939** |
| **0.1–0.2** | **22** | 0.157 | 0.500 | **+0.343** |
| 0.2–0.3 | 51 | 0.252 | 0.294 | +0.042 |
| 0.3–0.4 | 85 | 0.351 | 0.235 | −0.116 |
| 0.4–0.5 | 169 | 0.453 | 0.148 | **−0.305** |
| 0.5–0.6 | 199 | 0.547 | 0.261 | **−0.286** |
| 0.6–0.7 | 184 | 0.651 | 0.370 | **−0.281** |
| 0.7–0.8 | 176 | 0.749 | 0.540 | **−0.210** |
| 0.8–0.9 | 166 | 0.847 | 0.687 | −0.160 |
| 0.9–1.0 | 47 | 0.922 | 0.830 | −0.093 |
| **合计** | **1,100** | — | — | — |

→ **中段（0.4–0.8，n=169/199/184/176）系统性高出实测 21–31 个百分点。**
→ **但「两端尚可」只在高端成立**（0.8–0.9 差 −0.160、0.9–1.0 差 −0.093）：**低端是反向的大偏差**——0.0–0.1 箱差 **+0.939**（n=**1**）、0.1–0.2 箱差 **+0.343**（n=**22**），即**声称极低概率而实测偏真**。
→ **⚠️ 第九轮更正（ERRATA §10.1 第 8 项）**：本表此前只印 10 箱中的 **5** 箱，并据此写下「两端反而尚可」。**被略去的 5 箱里包含全表最大的两个偏差（+0.939、+0.343，都在低端）**，故「两端尚可」**在低端是假的**；被略去的还有 0.2–0.3、0.3–0.4、0.8–0.9 三箱。现**全部 10 箱印出**（全部有质量；n 之和 = **1,100**，与 P19 的 n 一致）。**⚠️ 低端两箱的 n 分别是 1 与 22——n=1 的箱不能承载任何结论**，本表把它们印出来**不是为了据以主张**，而是因为**略去它们会让这张表读起来支持它并不支持的句子**。"""

EDITS: list[tuple[str, str, str, str]] = [
    # ------------------------------------------------------------------ item 1
    ("| 全探测**最高** confidence | **0.9981——出现在唯一的错答上** | R13 |\n"
     "| 纯噪声 state | `noul 0.0011 / confidence 0.9989` | R13 |",
     "| **错答上**的**最高** confidence（**并非全探测最高**）| **0.9981——出现在唯一的错答上** | R13 |\n"
     "| **全探测最高** confidence（**出现在纯噪声 state 上**）| `noul 0.0011 / confidence` **0.9989** | R13 |",
     "§6.2: the 'highest confidence in the whole probe' (item 1)"),

    ("→ **对照价值**：**同一批条目上，一个判定器的满置信度是对的，另一个的满置信度是错的。** 用户无法从返回值区分。",
     "**⚠️ 第九轮更正（ERRATA §10.1 第 1 项）**：本表原把 **0.9981** 印成「全探测**最高** confidence」——**该措辞是错的**：**紧接的下一行**（纯噪声 state）记录 **0.9989**，比它更高。"
     "来源 `recon\\R13-laya-probe.md:456` 记 **0.9989**；而**同一文件 `:430` 又写 0.9981 是「the highest value anywhere in this entire probe」——来源自身即自相矛盾**。"
     "本表因此把两件事分开陈述：**0.9981 是「错答上」的最高值；全探测最高值是 0.9989，出现在纯噪声 state 上**。两行合起来才是本节要说的话：`confidence` 既不指示正确性，也不指示输入是否含有信息。"
     "（**过程记录**：`p44` 与 `p45` 两次试图修此句，均因把文件记成 `06-results-B-draft.md` 而报 MISS——该句从来不在那个文件里；ERRATA §10.1 第 1 项的行号标签同错，已一并更正。）\n"
     "→ **对照价值**：**同一批条目上，一个判定器的满置信度是对的，另一个的满置信度是错的。** 用户无法从返回值区分。",
     "§6.2: the correction note for item 1"),

    # ------------------------------------------------------------------ item 8
    ("**可靠性曲线形状**（Laya，**10 个等宽箱、[0,1]、末箱右闭**，全部有质量）：**过度自信集中在中间**。",
     "**可靠性曲线形状**（Laya，**10 个等宽箱、[0,1]、末箱右闭**，**全部 10 箱都有质量**——最小 n=1）：**过度自信集中在中间，低端则相反**。",
     "§6.2: the curve-shape lead-in (item 8)"),

    (RELIABILITY_OLD, RELIABILITY_NEW, "§6.2: the reliability table, 5 bins -> 10 (item 8)"),

    # ------------------------------------------------------------------ items 9 and 10
    ("| 权威定位（多处陈述中找权威来源，全部选项合理） | LLM | **1.0000** | 48 | P14 |\n"
     "| 权威定位（同上） | **Laya** | **0.4583** | 48 | P9b |\n"
     "| 77 类意图分类（扁平） | LLM | **0.750–0.900**（**4 次抽样**，中心 ≈0.875） | 40 | P15 |",
     "| 权威定位（多处陈述中找权威来源，全部选项合理） | LLM | **1.0000** | 48 | P14 |\n"
     "| 权威定位（**同一批 48 条的另一臂**） | **Laya** | **0.4583** | 48 | P9b |\n"
     "| 77 类意图分类（扁平） | LLM | **0.750–0.900**（**4 次抽样**；**中位数 0.875，均值 0.850**） | 40 | P15 + P15b r1–r3 |",
     "§6.1: the paired battery and the two centres (items 9, 10)"),

    ("**三条读法**：",
     "**⚠️ 配对关系必须标注（第九轮更正，ERRATA §10.1 第 9 项）**：上表「权威定位」两行是**同一批 48 条电池的两个臂**——"
     "`P14-llm-arm-full.json` 的 `_provenance.consumes` 即 `P9b-template-validation-separated-n48.json`，其 `complementarity.detail` 与 P9b 的 48 行**逐条配对**。"
     "故这两行**不是两份额外的独立测量，而是一次配对比较的两侧**；本画像把同一批 48 条**计了两次**（LLM 一行、Laya 一行），**在证据计数上应记作 1 项 48 条电池**。"
     "**数字本身不动**（1.0000 与 0.4583 分别是各自臂上的实测），但**读法必须改**：它不是两条独立的能力证据。\n"
     "**⚠️ 「中心」一词在此必须拆开（第九轮更正，ERRATA §10.1 第 10 项）**：四次抽样为 **0.750 / 0.900 / 0.875 / 0.875**，"
     "**中位数 = 0.875，均值 = 0.850**——原印「中心 ≈0.875」只对中位数成立。**且出处列原只写 `P15`**：四次中有 **3 次是 `P15b-rep-r1..r3.json`**（`temperature=0`），仅记录轮是 `P15-complementarity-strong-regime.json`；现按产物写全。（§7.3 与本摘要同处的「经验中心 ≈0.875，均值 0.850」本已写全，未受影响。）\n"
     "\n**三条读法**：",
     "§6.1: the double count and the two centres (items 9, 10)"),

    # ------------------------------------------------------------------ item 12
    ("> **⚠️ 编号说明（审计订正）**：本节条款原编号为 14–17，**其中一条与「结果 B」一节（即本稿的第 6 节）的第 13 条逐字重复**（「评测语料必须包含候选值不出现的条目」）。重复项已删除，本节现为 **14–21**，全文条款总数据实订正为 **23 条不重复**（§4.4 四条中的两条与结果 B 重复，故 4+13+8−2 = 23）。",
     "> **⚠️ 编号说明（第九轮重写，ERRATA §10.1 第 12 项）**：本节条款共 **8 条，编号 14–21**，逐条见下。\n"
     "> **此前的说明自相矛盾，已撤下**：它写「本节条款原编号为 14–17，其中一条与结果 B 的第 13 条逐字重复，重复项已删除，本节现为 14–21」——"
     "**14–17 只有 4 条，删掉 1 条不可能得到 8 条**；而且**本节 14–21 中没有任何一条复述结果 B 的第 13 条**（最接近的第 16 条讲的是「难度档必须交叉明确支持/明确矛盾」，与第 13 条「语料必须包含候选值不出现的条目」不是同一条，措辞与所指都不同）。\n"
     "> **可核对的计数如下**：§4.4 四条（`04-method-draft.md`：概率语义、类型/键断言、散文抽取器、不可能值复核）中，**第 1、2 条分别与结果 B 的第 8、10 条重复**；结果 B 共 **13 条**；本节 **8 条**。"
     "故全文不重复条款数 = **4 + 13 + 8 − 2 = 23**——**这个 23 成立，被撤下的只是关于「本节原编号 14–17」的那半句**。",
     "§6.6: the impossible clause-counting note (item 12)"),

    # ------------------------------------------------------------------ item 10, abstract copy
    ("00-abstract-draft.md",
     "- **77 类意图分类**（n=40，**4 次抽样**）：LLM **0.750–0.900**（中心 ≈0.875），判定器 **0.225**（4 次逐位相同）；",
     "- **77 类意图分类**（n=40，**4 次抽样**）：LLM **0.750–0.900**（四次为 0.750 / 0.900 / 0.875 / 0.875；**中位数 0.875，均值 0.850**），判定器 **0.225**（4 次逐位相同）；",
     "abstract: the two centres (item 10)"),
]


def main() -> int:
    cache: dict[str, str] = {}

    def get(name: str) -> str:
        if name not in cache:
            cache[name] = (PAPER / name).read_text(encoding="utf-8")
        return cache[name]

    ok = miss = 0
    for entry in EDITS:
        # (old, new, label) defaults to the Results C draft; the abstract copy of item 10
        # carries its own file name. Normalised rather than repeated, because typing the file
        # name on five entries and forgetting it on the sixth fails at run time, not at
        # review time -- as it did twice in this session.
        fname, old, new, label = (entry if len(entry) == 4 else (C,) + tuple(entry))
        t = get(fname)
        if old in t:
            cache[fname] = t.replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1
        elif new in t:
            print(f"  ok    {label} (already applied)")
            ok += 1
        else:
            print(f"  MISS  {label}")
            miss += 1

    for fname, t in cache.items():
        (PAPER / fname).write_text(t, encoding="utf-8")

    # ---- post-conditions, checked against the artifact rather than against the prose
    import json
    import re
    bins = json.loads((PAPER.parent / "results" / "P19-calibration.json")
                      .read_text(encoding="utf-8"))["summary"]["laya"]["calibration"]["bins"]
    c = get(C)
    rows = re.findall(r"^\| \*?\*?([0-9]\.[0-9]–[0-9]\.[0-9])\*?\*? \| \*?\*?([0-9,]+)\*?\*?", c, re.M)
    # the paper writes en-dashes in bin labels and the artifact writes ASCII hyphens; a
    # comparison that does not fold them reports a failure on identical data
    got = {b.replace("–", "-"): int(n.replace(",", "")) for b, n in rows}
    want = {b["bin"]: b["n"] for b in bins}
    if got == want:
        print(f"  ok    all {len(want)} bins printed with the artifact's own n "
              f"(sum {sum(want.values())})")
    else:
        print(f"  MISS  bin table does not match P19: got {got}, want {want}")
        miss += 1

    if "0.9989" in c and "全探测最高" in c:
        print("  ok    the highest-confidence claim names 0.9989 as the probe maximum")
    else:
        print("  MISS  the 0.9989 correction is not in place")
        miss += 1

    # The corrected note QUOTES the old wording to retract it, so the check must key on the
    # note's own opening (a blockquote line), not on the quoted phrase inside the retraction.
    stale_note = any(line.startswith("> **⚠️ 编号说明（审计订正）**") for line in c.split("\n"))
    if stale_note:
        print("  MISS  the impossible clause-counting note survives as a standing claim")
        miss += 1
    else:
        print("  ok    the impossible '14-17 -> 14-21' note is gone "
              "(it survives only inside its own retraction)")

    print(f"\n{ok} applied, {miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
