"""ERRATA 10.1 items 4, 5, 6, 7, 11 and 13 -- the six defects in `06-results-B-draft.md`.

WHY EACH ONE MATTERS
--------------------
All six are the same species of error, and it is the species this paper is about: a number
that is correct in itself, attached to the wrong object, or a quantifier that the sentence's
own table falsifies.

  * item 13  "eight live `jev_check` calls" over a 7-row table, against a source whose design
             line says SEVEN and whose table lists EIGHT rows. Nothing in the tree can
             adjudicate, because the probe has no `results/` artifact -- so the fix is to
             report the 7 rows that exist and to record the source's own contradiction.
  * item 4   "sufficient never exceeds 0.14 in all 7 calls" -- falsified by the two rows that
             print 0.88 and 0.92. One instance was corrected (p44); this script checks for
             others and makes the corrected count robust to the 7-vs-8 question.
  * item 6   the table's binary-item column printed an em-dash in four of five rows, so its own
             "total 9" could not be derived from it. The per-bin counts DO exist in the source
             (`recon/R12-jev-probe.md:181-185`) and are restored here.
  * item 5   "the unique solution is 4/10 = 0.40" -- NOT unique: 5/10 is equally consistent,
             and 5/10 is what the source actually says. The paper had silently "corrected" a
             source number on the strength of a uniqueness claim that does not hold.
  * item 7   "about half of this corpus" answered false -- measured, it is 60.0% for the LLM
             and 29.8% for the judge; "about half" fits neither, and the phrase was repeated in
             the section summary, the discussion and the abstract.
  * item 11  the field-attribution table omits `warnings`, which the artifact
             `P27d-primitive-fields.json` lists among the nine keys the provider never returns
             -- and `warnings` is the one key the section's own first protocol clause is about.

The two denominator mistakes (items 5/6) are worth stating plainly: the paper's own
correction INTRODUCED an error, by treating a table as if it determined an answer it does not.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

B = "06-results-B-draft.md"

# The per-bin binary counts, exactly as `recon/R12-jev-probe.md:181-185` records them:
# 0.0-0.2 -> 2, 0.2-0.4 -> 2, 0.4-0.6 -> 2, 0.6-0.8 -> 2, 0.8-1.0 -> 1. Sum 9 -- which is NOT
# the 10 the same file's prose uses for the Brier. Both are printed; neither is invented.
TABLE_OLD = """| P(true) 分箱 | 项数（全部） | **其中二值真值项** | 观测正确率 |
|---|---|---|---|
| 0.0–0.2 | 3 | — | 0.67 |
| 0.2–0.4 | 2 | — | 0.00 |
| 0.4–0.6 | 5 | **2** | 0.50 |
| 0.6–0.8 | 2 | — | 0.50 |
| 0.8–1.0 | 2 | — | 0.00 |
| **合计** | **14** | **9** | — |"""

TABLE_NEW = """| P(true) 分箱 | 项数（全部） | **其中二值真值项** | 观测正确率 |
|---|---|---|---|
| 0.0–0.2 | 3 | **2** | 0.67 |
| 0.2–0.4 | 2 | **2** | 0.00 |
| 0.4–0.6 | 5 | **2** | 0.50 |
| 0.6–0.8 | 2 | **2** | 0.50 |
| 0.8–1.0 | 2 | **1** | 0.00 |
| **合计** | **14** | **9** | — |"""

CAVEAT_OLD = """**⚠️ 分母必须说清楚（原稿省略了中间那一列）**：**项数**一列的分母是全部 14 项，而**正确率**一列的分母是**二值真值子集**——故「5 项 × 0.50」在算术上不可能。原稿把两列并列而未标注分母不同，读者无法复现。
**⚠️ 且原稿的汇总数字无法由该表复现**：原稿写「二值项阈值 0.5 → **5/10 = 随机**」，但本表二值项之和为 **9**；穷举与速率列相容的 (命中, 总数) 组合，唯一解是 **4/10 = 0.40**。此处按可复现值更正为 **4/10 = 0.40**（或应整体撤回该汇总）。"""

CAVEAT_NEW = """**⚠️ 分母必须说清楚（第七轮更正，第九轮补全）**：**项数**一列的分母是全部 14 项，而**正确率**一列的分母是**二值真值子集**——故「5 项 × 0.50」在算术上不可能。原稿把两列并列而未标注分母不同，读者无法复现。**中间一列现已按来源逐箱填全**（`recon\\R12-jev-probe.md:181-185` 记 2 / 2 / 2 / 2 / 1），使合计 **9** **可由本表直接相加得到**（**⚠️ 第九轮更正，ERRATA §10.1 第 6 项**：此前四行印破折号，读者无法复现自己正在读的合计）。
**⚠️ 而来源在两处互相矛盾，本表只能并置、不能替它裁决**：
- **二值项总数**：R12 的**表**给出 **9**（2+2+2+2+1，逐箱可加）；R12 的**正文**两处（`:187`、`:388`）写 **10**，Brier 0.359 也记在「10 项」上。**9 ≠ 10，而树内没有逐项记录可以裁决**。故本表把**逐箱计数**与**正文所记总数**分开印：Brier 处沿用正文的 **n=10**（下条），并在该处标注这一差 1 的不一致。
- **「二值项阈值 0.5 → 5/10 = 随机」不能由本表推出**：与速率列相容的 (命中, 总数) **不是唯一解**——**5/10 = 0.50**（R12 正文逐字所记）与 **4/10 = 0.40** 都相容（0.67 要求该箱 n 为 3 的倍数，0.50 要求为偶数，两解都满足）。原稿在此印「唯一解是 4/10 = 0.40」，**「唯一」是错的**（**⚠️ 第九轮更正，ERRATA §10.1 第 5 项**）。**本表不再自行更正该汇总**，改为**逐字保留来源的 5/10**，并标注它**不可由本表复现**——按本文自己的规则，**不可核验的汇总不得被换成另一个同样不可核验的汇总**。"""

EDITS: list[tuple] = [
    # ---------------------------------------------------------------- item 13 (+item 4)
    ("**设计**：八次 live `jev_check`，覆盖 支持 / 否定 / **明确冲突** / **对称冲突** / 无关 / 弱相关 / 传闻 / 单条未署名笔记。",
     "**设计**：live `jev_check` 的 **7 行**读数（即下表全部 7 行），覆盖 支持 / 否定 / **明确冲突** / **对称冲突** / 无关 / 弱相关与传闻（同一行）/ 单条未署名笔记。"
     "**⚠️ 第九轮更正（ERRATA §10.1 第 13 项）**：本句原印「八次」并列出八个类别，而**本节自己的表只有 7 行**——「弱相关」与「传闻」在来源中是**两行**，在此并作一行。"
     "**⚠️ 且来源自身矛盾、且无产物可裁决**：`probes\\P13-jev-remaining-measurements.md:45` 的设计行写「**七次**」，其表（`:47-56`）却列 **8 行**（多出一行「处方式支持 0.98 / 0.02 / 0.89 `supported`」，本表未收）；该探针**没有任何 `results\\` JSON 产物**，故 7 还是 8 **不能从树内判定**。本表只报**逐行可见的 7 行**，并把这一不一致如实记在此处。",
     "§3.5: the 'eight calls' design line (item 13)"),

    # ---------------------------------------------------------------- item 4 (check for others)
    ("且已被 `protocol\\AUDIT-FINDINGS.md:225` 记为审计发现 m-8，初稿未同步）**，而解析器需要 sufficiency ≥ 阈值（≈0.5）才给出 `undecided` / `conflicted`。",
     "且已被 `protocol\\AUDIT-FINDINGS.md:225` 记为审计发现 m-8，初稿未同步）**，而解析器需要 sufficiency ≥ 阈值（≈0.5）才给出 `undecided` / `conflicted`。"
     "**⚠️ 并已逐处复查（第九轮，ERRATA §10.1 第 4 项）**：全文再无第二处「全部 7 次」式量词；且**该计数对上文 7 行 / 8 行之争是稳健的**——来源的 8 行中同样只有 5 行是 `insufficient`（第 1、2、3 行为 `supported` / `contradicted` / `supported`），故「5 次」在两种行数下都成立。",
     "§3.5: the 'all 7 calls' quantifier (item 4)"),

    # ---------------------------------------------------------------- items 5 and 6
    (TABLE_OLD, TABLE_NEW, "§3.1: the binary-item column (item 6)"),
    (CAVEAT_OLD, CAVEAT_NEW, "§3.1: the 'unique 4/10' claim (item 5)"),

    ("- **Brier 0.359**，而**常数预测器 0.5 的 Brier 是 0.25** → 在**有二元真值的这 10 项**（全电池 14 项）上，mock 的概率**劣于常数预测器**；",
     "- **Brier 0.359**，而**常数预测器 0.5 的 Brier 是 0.25** → 在**有二元真值的这 10 项**（全电池 14 项）上，mock 的概率**劣于常数预测器**"
     "（**⚠️ 该 n=10 出自来源正文；上表逐箱计数合计为 9——差 1 且树内无法裁决，见上**）；",
     "§3.1: the Brier's n against the table's total (item 6)"),

    # ---------------------------------------------------------------- item 7
    ("- **`probability` 是「所选选项的概率」，不是 P(true)** —— 把 `probability` 记为 P(true) **会把它那一半条目反号**；",
     "- **`probability` 是「所选选项的概率」，不是 P(true)** —— 把 `probability` 记为 P(true) **会把所有答 `false` 的条目反号**"
     "（**⚠️ 第九轮更正，ERRATA §10.1 第 7 项**：原印「它那一半条目」，本节小结与摘要处并印「约占一半」——**实测不是一半**：在 `P19-calibration.json` 的 1100 条上，"
     "**LLM 答 `false` 的占 60.0%（660/1100）**，**判定器 `noul < 0.5` 的占 29.8%（328/1100）**，两个比例都由该产物 `bins` 各箱 n 直接相加得到，**均不接近 0.5**）；",
     "§3.4: 'about half of that corpus' (item 7)"),

    ("| 4 | 字段层 | `probability` 是 P(所选选项)，反号**所有答 `false` 的条目**（在该语料上约占一半），且与 `band` 方向相反 |",
     "| 4 | 字段层 | `probability` 是 P(所选选项)，反号**所有答 `false` 的条目**（实测占比 **60.0%**（LLM）/ **29.8%**（判定器），**不是「约一半」**），且与 `band` 方向相反 |",
     "§3.8 summary row 4 (item 7)"),

    # ---------------------------------------------------------------- item 11
    ("| `truncated`、`stateChars`、`questionsChars`、`redactions` | **接入层的出口记账** |",
     "| `truncated`、`stateChars`、`questionsChars`、`redactions`、**`warnings`** | **接入层的出口记账** |",
     "§3.4.1: the missing `warnings` row (item 11)"),

    ("⇒ **这三类字段（单数 `probability`、`band`、`answer`）与全部出口/延迟字段，在已实测的三个原语（各 1 次调用）下都未由 provider 提供**；",
     "⇒ **⚠️ 本表必须与产物的键表逐字对齐（第九轮更正，ERRATA §10.1 第 11 项）**：`P27d-primitive-fields.json` 的 `never_returned_by_provider` 列出 **9 个**键——"
     "`band`、`probability`、`answer`、`truncated`、`stateChars`、`questionsChars`、`redactions`、`latencyMs`、**`warnings`**——而本表此前只列了其中 **8** 个，**漏掉 `warnings`**。"
     "`warnings` 尤其不能漏：本节第 1 条协议条款的全部依据就是「**不能靠 warning 缺失判断 live/mock**」。补入后，本表覆盖 provider 已返回的 7 键与未返回的 9 键，共 16 键，与产物一致。\n"
     "⇒ **这三类字段（单数 `probability`、`band`、`answer`）与全部出口/延迟字段，在已实测的三个原语（各 1 次调用）下都未由 provider 提供**；",
     "§3.4.1: key-table completeness (item 11)"),

    # ---------------------------------------------------------------- item 7, discussion copy
    ("09-10-11-discussion-limits-repro-draft.md",
     "- Jev 的 `probability` 是 **P(所选选项)**，不是 P(true)——把 `probability` 记作 P(true) 会**反号所有答 `false` 的条目**（在该语料上约占一半）；",
     "- Jev 的 `probability` 是 **P(所选选项)**，不是 P(true)——把 `probability` 记作 P(true) 会**反号所有答 `false` 的条目**"
     "（实测占 **29.8%**（328/1100）；同一语料上 LLM 为 **60.0%**（660/1100）——**均非「约一半」**，来源 `P19-calibration.json`，见 §6.4）；",
     "§9: the repeated 'about half' (item 7)"),
]

EDITS_D = []          # the discussion copy is carried in EDITS above, with its file name


def main() -> int:
    cache: dict[str, str] = {}

    def get(name: str) -> str:
        if name not in cache:
            cache[name] = (PAPER / name).read_text(encoding="utf-8")
        return cache[name]

    ok = miss = 0
    for entry in EDITS:
        # Entries are (old, new, label) and default to the Results B draft; the one that
        # belongs to the discussion draft carries its file name as a 4th element. Written
        # this way because writing the file name on all nine and forgetting it on one is
        # exactly how the previous pass produced a 3-tuple that blew up at run time.
        fname, old, new, label = (entry if len(entry) == 4 else (B,) + tuple(entry))
        t = get(fname)
        # ORDER MATTERS, AND GETTING IT WRONG COST A DUPLICATE: two of the edits below APPEND
        # to a sentence rather than replacing it, so `old` remains a substring of the patched
        # file. Testing `old` first therefore re-applied them on the second run and printed
        # two copies of the correction. Testing `new` first is the correct guard.
        if new in t:
            print(f"  ok    {label} (already applied)")
            ok += 1
        elif old in t:
            cache[fname] = t.replace(old, new, 1)
            print(f"  ok    {label}")
            ok += 1
        else:
            print(f"  MISS  {label}")
            miss += 1

    # ---- repair the duplication the wrong guard produced, and say so explicitly: a repair
    # that hides its own cause cannot be audited.
    #
    # The duplicate is the APPENDED TAIL, not the whole replacement: when `new` = `old` +
    # tail, a second application replaces the `old` PREFIX of the already-patched text and
    # leaves the first tail in place, so `new` itself still occurs exactly once and a dedupe
    # keyed on `new` finds nothing. That is the third guard in this script to test the wrong
    # object, which is why each one now prints what it actually compared.
    for fname in sorted({e[0] if len(e) == 4 else B for e in EDITS}):
        t = get(fname)
        for entry in EDITS:
            fn, old, new, label = (entry if len(entry) == 4 else (B,) + tuple(entry))
            if fn != fname:
                continue
            dup = new[len(old):] if new.startswith(old) else new
            while dup and t.count(dup) > 1:
                t = t.replace(dup, "", 1)
                print(f"  ok    de-duplicated a re-applied correction in {fname}: {label}")
        cache[fname] = t

    for fname, t in cache.items():
        (PAPER / fname).write_text(t, encoding="utf-8")

    # ---- "check for others": the falsified quantifier and the 'half' wording must not
    # survive in any other draft, in either direction. The scans are deliberately narrow:
    # a scan that fires on the correction text itself (「全部 7 次」式量词) or on an unrelated
    # "halved" (`08-results-D`: K>=8 accuracy falls to about half) is a false positive, and a
    # scan that cries wolf is a scan nobody reads.
    b = get(B)
    stale_quantifier = [i for i, line in enumerate(b.split("\n"), 1)
                        if re.search(r"全部\s*7\s*次", line)
                        and "式量词" not in line and "原印" not in line]
    if stale_quantifier:
        print(f"  MISS  a second 'all 7 calls' quantifier survives in {B} at "
              f"{stale_quantifier}")
        miss += 1
    else:
        print("  ok    no surviving 'all 7 calls' quantifier in the Results B draft")

    # the withdrawn wording is the parenthetical about the FALSE-ANSWER rate, so the scan
    # requires the false-answer context on the same line
    half = []
    for f in sorted(PAPER.glob("*-draft.md")):
        for i, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            if re.search(r"[约大]约?一半|约一半", line) and ("反号" in line or "答 `false`" in line):
                if not any(m in line for m in ("不是", "非「约一半」", "均非", "原印", "更正")):
                    half.append(f"{f.name}:{i}")
    if half:
        print(f"  MISS  'about half' survives for the false-answer rate at {half}")
        miss += 1
    else:
        print("  ok    no unqualified 'about half' for the false-answer rate in any draft")

    print(f"\n{ok} applied, {miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
