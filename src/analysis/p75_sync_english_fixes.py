"""Mirror the ERRATA 10.1 fixes into the English section files.

WHY THE ENGLISH IS NOT OPTIONAL
-------------------------------
arXiv (in effect from 2026-02-11) requires a full English version for a non-English
submission, so `paper/en/` is a deliverable, not a convenience. `verify_all.py` I1-I5 check it,
and I5 exists because a translation once shipped one third short with every other check green.

More importantly, this paper's whole thesis is that a claim which cannot be re-checked is
worthless. If the Chinese says the regime-1 prose arm has a POSITIVE Delta_catch and the
English still says regime 1 is unmeasurable, then the two published versions of the same
measurement disagree -- which is strictly worse than either being wrong on its own.

Every edit here is the counterpart of one made by p70-p74 in the Chinese drafts. The English
section files are the SOURCE (paper/en/MANUSCRIPT.md is generated), so this script edits them
and then runs `paper/en/_assemble.py`.

WHAT IS DELIBERATELY NOT DONE
-----------------------------
No new claims, no added citations, no smoothing of the hedges. The English carries the same
warnings, the same denominators and the same retraction text as the Chinese, per
`paper/TRANSLATION-GLOSSARY.md` sections 3 and 5-7.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

BC = "06-07-results-BC.md"
D = "08-results-D.md"
AB = "00-abstract.md"
IN = "01-intro-02.md"
DL = "09-10-11-discussion-limits-repro.md"

PROSE_BLOCK_EN = """
**⚠️ But the reading above is the forced-choice arm. The same artifact also records a second arm, and its Δ_catch is POSITIVE (ninth-round addition, ERRATA §10.1 item 3).**
`results\\P14-llm-arm-full.json`'s `complementarity_prose_arm` records the paired result on **the same 48 items** with the LLM answering **in prose** (the label recovered by an extractor):

| metric | value (P14 prose arm, n=48) |
|---|---|
| **LLM accuracy** | **0.9583 (46/48)** |
| judge accuracy (the same judge readings) | **0.4583** |
| both correct / only LLM / **only judge** / neither | 21 / 25 / **1** / 1 |
| **`P(judge correct \\| LLM wrong)`** | **0.5 (1/2)** |
| `P(judge correct \\| LLM right)` | 0.4565 (21/46) |
| **Δ_catch** | **+0.0435** |
| Δ_catch 95% CI (unpaired Wald / Newcombe) | **[−0.664, +0.751] / [−0.386, +0.471]** |
| Fisher exact p (2×2) | 1.0000 |

→ **This is the only measurable Δ_catch in regime one, and its sign is positive.** This section previously reported only the forced-choice arm and therefore wrote the whole regime off as "unmeasurable" — **that judgement holds for the forced-choice arm and does not hold for the prose arm.**
→ **The denominator must be given with the point estimate, or +0.0435 will be read as stronger than it is**: the LLM errs on only **2** of the 48 prose items, so `P(judge correct | LLM wrong)` is **1/2**; both 95% intervals are wide and both contain 0, and the Fisher p is 1.0000. **It is not established complementarity; but it is also not zero** — reading +0.0435 as "no complementarity" and reading it as "complementarity" are equally unsupported.
→ **The two arms are two answer formats of ONE 48-item battery** (this artifact's `_provenance.consumes` is `P9b`; the judge reads 0.4583 on both arms), **not two independent pieces of evidence**; in the capability profile each occupies one row and the pairing must be stated (§6.1).
→ Every number above is recomputed by `src\\analysis\\p28_recompute_all_stats.py` and written into the `regime1` block of `results\\P28-recomputed-statistics.json`; that block also records that **the forced-choice arm's Δ_catch is undefined because `n_wrong_arm = 0`** (it must not be printed as 0).
→ **⚠️ This artifact's `_provenance.published_figures_at_risk` already listed "prose arm 0.958"** — this arm has been on the "if this moves, the paper's numbers are at risk" list since it was recorded, yet it never appeared in the body text.
"""

EDITS: list[tuple] = [
    # ================================================================ en/08 -- items 3 and 2
    (D,
     "→ All that can be said is: **on this regime Laya caught no item the LLM missed (only Laya correct 0 / only LLM correct 26)**, but instead failed alone on 26 items.",
     "→ All that can be said is: **on this regime Laya caught no item the LLM missed (only Laya correct 0 / only LLM correct 26)**, but instead failed alone on 26 items.\n"
     + PROSE_BLOCK_EN,
     "en §7.2: the prose arm (item 3)"),

    (D,
     "**The strength of this regime's evidence**: a **ceiling effect** — it **cannot** prove \"no complementarity\", it can only prove that **this battery cannot measure complementarity**.",
     "**The strength of this regime's evidence**: the **ceiling effect applies only to the forced-choice arm** (LLM 48/48). **The prose arm is measurable**, with a Δ_catch point estimate of **+0.0435**, an interval containing 0, resting on only **2** items where the LLM errs. "
     "**⚠️ The accurate statement for this regime is therefore: not measurable in one answer format, measurable in the other with a positive point estimate and insufficient precision to decide** — not \"this battery cannot measure complementarity\" (ninth-round correction: the original sentence rested on the forced-choice arm alone; see the table above).",
     "en §7.2: the ruling (item 3)"),

    (D,
     "> On the **three** task regimes measured, **a heterogeneous judge provides no incremental coverage**. On one of them the LLM is strictly dominant (only LLM correct 26 / only judge correct 0);",
     "> On the **three** task regimes measured, **a heterogeneous judge provides no incremental coverage**. On one of them the LLM is strictly dominant (forced-choice arm: only LLM correct 26 / only judge correct 0; "
     "**⚠️ the same 48-item battery's prose arm is 25 / 1, Δ_catch = +0.0435 — the regime's only measurable Δ_catch, and it is positive, see §7.2**);",
     "en §7.5: the conclusion (item 3)"),

    (D,
     "1. **Regime one has a ceiling effect** (LLM 48/48), so its evidence **cannot prove the absence of complementarity**;",
     "1. **Regime one's ceiling effect occurs only in the forced-choice arm** (LLM 48/48); **on the prose arm the LLM is 46/48 with 1 judge-only item, Δ_catch = +0.0435 (Newcombe 95% CI [−0.386, +0.471]) — a positive point estimate resting on only 2 items where the LLM errs** "
     "⇒ that arm likewise **cannot prove the absence of complementarity**, and it **can** produce an (imprecise) **positive** point estimate; the rest of this section's conclusions rest on the **forced-choice** arm's \"only judge correct 0\", which this correction does not touch;",
     "en §7.9: regime one (item 3)"),

    (D,
     "with one-sided p = 0.052 / 0.043 / 0.103 ⇒ **\"below the marginal\" is a point estimate, not an established inequality**;",
     "with one-sided p = **0.052 / 0.043 / 0.103 (normal approximation, no continuity correction)** ⇒ **\"below the marginal\" is a point estimate, not an established inequality**; "
     "**⚠️ The convention must be named (ninth-round correction, ERRATA §10.1 item 2)**: these three numbers were printed without a stated test, so the reader could not tell which one produced them. "
     "**The exact binomial lower tails for the same `(x, n, baseline 0.2941)` are 0.076 / 0.061 / 0.149** — **nothing is significant under either convention**. "
     "Both conventions are recomputed from the artifacts by `src\\analysis\\p28_recompute_all_stats.py` and written into `results\\P28-recomputed-statistics.json` under `regime3[*].vs_marginal_one_sided`, which carries both `exact_binomial_lower_tail` and `normal_approximation`; "
     "**⚠️ do not conflate them with the Fisher exact p printed in the same place (0.086 / 0.049 / 0.163) — that is a different test on the 2×2 table**;",
     "en §7.6.1(b): the unlabelled approximation (item 2)"),

    # ================================================================ en/06-07 -- items 13, 4, 6, 5
    (BC,
     "| P(true) bin | items (all) | **of which binary-ground-truth items** | observed accuracy |\n"
     "|---|---|---|---|\n"
     "| 0.0–0.2 | 3 | — | 0.67 |\n"
     "| 0.2–0.4 | 2 | — | 0.00 |\n"
     "| 0.4–0.6 | 5 | **2** | 0.50 |\n"
     "| 0.6–0.8 | 2 | — | 0.50 |\n"
     "| 0.8–1.0 | 2 | — | 0.00 |\n"
     "| **Total** | **14** | **9** | — |",
     "| P(true) bin | items (all) | **of which binary-ground-truth items** | observed accuracy |\n"
     "|---|---|---|---|\n"
     "| 0.0–0.2 | 3 | **2** | 0.67 |\n"
     "| 0.2–0.4 | 2 | **2** | 0.00 |\n"
     "| 0.4–0.6 | 5 | **2** | 0.50 |\n"
     "| 0.6–0.8 | 2 | **2** | 0.50 |\n"
     "| 0.8–1.0 | 2 | **1** | 0.00 |\n"
     "| **Total** | **14** | **9** | — |",
     "en §3.1: the binary column (item 6)"),

    (BC,
     "**⚠️ The denominators must be spelled out (the original omitted that middle column)**: the **items** column has all 14 items as its denominator, while the **accuracy** column has the **binary-ground-truth subset** as its denominator — so \"5 items × 0.50\" is arithmetically impossible. The original set the two columns side by side without marking that the denominators differ, and the reader cannot reproduce it.\n"
     "**⚠️ And the original's summary figure cannot be reproduced from this table**: the original writes \"binary items at threshold 0.5 → **5/10 = chance**\", but this table's binary items sum to **9**; enumerating the (hits, total) combinations compatible with the rate column, the unique solution is **4/10 = 0.40**. Here it is corrected, per the reproducible value, to **4/10 = 0.40** (or the whole summary should be withdrawn).",
     "**⚠️ The denominators must be spelled out (seventh-round correction, completed in the ninth)**: the **items** column has all 14 items as its denominator, while the **accuracy** column has the **binary-ground-truth subset** as its denominator — so \"5 items × 0.50\" is arithmetically impossible. The original set the two columns side by side without marking that the denominators differ, and the reader cannot reproduce it. **The middle column is now filled in per bin from the source** (`recon\\R12-jev-probe.md:181-185` records 2 / 2 / 2 / 2 / 1), so the total **9** **can be obtained by adding up this table** (**⚠️ ninth-round correction, ERRATA §10.1 item 6**: four rows previously printed an em-dash, leaving the reader unable to reproduce the total they were reading).\n"
     "**⚠️ And the source contradicts itself in two places; this table can only set the two side by side, not adjudicate them**:\n"
     "- **the binary-item total**: R12's **table** gives **9** (2+2+2+2+1, addable bin by bin); R12's **prose** says **10** in two places (`:187`, `:388`), and the Brier 0.359 is recorded on \"10 items\". **9 ≠ 10, and there is no per-item record in the tree that could decide it.** This table therefore prints the **per-bin counts** and the **prose total** separately: at the Brier we keep the prose's **n=10** (next bullet) and mark the one-item discrepancy there.\n"
     "- **\"binary items at threshold 0.5 → 5/10 = chance\" cannot be derived from this table**: the (hits, total) combinations compatible with the rate column are **not unique** — **5/10 = 0.50** (what R12's prose records verbatim) and **4/10 = 0.40** are both compatible (0.67 requires that bin's n to be a multiple of 3, 0.50 requires it to be even, and both solutions satisfy this). The original printed \"the unique solution is 4/10 = 0.40\"; **\"unique\" is wrong** (**⚠️ ninth-round correction, ERRATA §10.1 item 5**). **This table no longer \"corrects\" that summary**; it **keeps the source's 5/10 verbatim** and marks it as **not reproducible from this table** — by this paper's own rule, **an unverifiable summary must not be replaced by another unverifiable summary**.",
     "en §3.1: the denominators and the 4/10 claim (items 5, 6)"),

    (BC,
     "- **Brier 0.359**, while **a constant predictor at 0.5 has Brier 0.25** → on **these 10 items that carry binary ground truth** (14 items in the whole battery), the mock's probabilities are **worse than the constant predictor**;",
     "- **Brier 0.359**, while **a constant predictor at 0.5 has Brier 0.25** → on **these 10 items that carry binary ground truth** (14 items in the whole battery), the mock's probabilities are **worse than the constant predictor** "
     "(**⚠️ that n=10 comes from the source's prose; the per-bin counts in the table above sum to 9 — a discrepancy of one that the tree cannot adjudicate, see above**);",
     "en §3.1: the Brier's n (item 6)"),

    (BC,
     "**Design**: eight live `jev_check` calls, covering support / negation / **explicit conflict** / **symmetric conflict** / irrelevant / weakly relevant / hearsay / a single unattributed note.",
     "**Design**: the **7 rows** of live `jev_check` readings (all 7 rows of the table below), covering support / negation / **explicit conflict** / **symmetric conflict** / irrelevant / weakly relevant and hearsay (one row) / a single unattributed note. "
     "**⚠️ Ninth-round correction (ERRATA §10.1 item 13)**: this sentence printed \"eight\" and listed eight categories, while **this section's own table has 7 rows** — in the source, \"weakly relevant\" and \"hearsay\" are **two rows**, merged into one here. "
     "**⚠️ And the source contradicts itself, with no artifact to adjudicate**: `probes\\P13-jev-remaining-measurements.md:45` says \"**seven**\" in its design line, while its table (`:47-56`) lists **8 rows** (one extra: \"prescriptive support 0.98 / 0.02 / 0.89 `supported`\", not carried into this table); that probe has **no `results\\` JSON artifact at all**, so 7-vs-8 **cannot be decided from the tree**. This table reports the **7 rows that are actually visible** and records the discrepancy here.",
     "en §3.5: the 'eight calls' line (item 13)"),

    (BC,
     "while the parser needs sufficiency ≥ a threshold (≈0.5) before it will give `undecided` / `conflicted`.",
     "while the parser needs sufficiency ≥ a threshold (≈0.5) before it will give `undecided` / `conflicted`. "
     "**⚠️ And this has been re-checked everywhere (ninth round, ERRATA §10.1 item 4)**: no second \"all 7 calls\" quantifier exists in the paper; and **the count is robust to the 7-vs-8 row question above** — in the source's 8 rows only 5 are `insufficient` as well (rows 1, 2 and 3 are `supported` / `contradicted` / `supported`), so \"5 calls\" holds under either row count.",
     "en §3.5: the quantifier (item 4)"),

    (BC,
     "- **`probability` is \"the probability of the selected option\", not P(true)** — recording `probability` as P(true) **will flip the sign of its half of the items**;",
     "- **`probability` is \"the probability of the selected option\", not P(true)** — recording `probability` as P(true) **flips the sign of every item answered `false`** "
     "(**⚠️ ninth-round correction, ERRATA §10.1 item 7**: the original printed \"its half of the items\", and this section's summary and the abstract printed \"about half\". **Measured, it is not half**: on the 1,100 items of `P19-calibration.json`, the **LLM answers `false` on 60.0% (660/1100)** and the **judge's `noul < 0.5` on 29.8% (328/1100)** — both obtained by adding up that artifact's per-bin `bins`, **neither anywhere near 0.5**);",
     "en §3.4: 'half of the items' (item 7)"),

    (BC,
     "| `truncated`, `stateChars`, `questionsChars`, `redactions` | **the access layer's egress accounting** |",
     "| `truncated`, `stateChars`, `questionsChars`, `redactions`, **`warnings`** | **the access layer's egress accounting** |",
     "en §3.4.1: the `warnings` row (item 11)"),

    (BC,
     "⇒ **These three kinds of field (the singular `probability`, `band`, `answer`) and all the egress/latency fields are, under the three primitives measured (1 call each), not supplied by the provider**;",
     "⇒ **⚠️ This table must match the artifact's key list key by key (ninth-round correction, ERRATA §10.1 item 11)**: `P27d-primitive-fields.json`'s `never_returned_by_provider` lists **9** keys — "
     "`band`, `probability`, `answer`, `truncated`, `stateChars`, `questionsChars`, `redactions`, `latencyMs`, **`warnings`** — while this table previously listed only **8** of them, **omitting `warnings`**. "
     "`warnings` in particular cannot be omitted: the whole basis of this section's first protocol clause is that **the absence of a warning must not be used to judge live vs mock**. With it added, the table covers the 7 keys the provider does return and the 9 it does not, 16 in all, matching the artifact.\n"
     "⇒ **These three kinds of field (the singular `probability`, `band`, `answer`) and all the egress/latency fields are, under the three primitives measured (1 call each), not supplied by the provider**;",
     "en §3.4.1: key-table completeness (item 11)"),

    (BC,
     "| 4 | field layer | `probability` is P(the selected option); it flips the sign of **every item answered `false`** (about half of that corpus), and points opposite to `band` |",
     "| 4 | field layer | `probability` is P(the selected option); it flips the sign of **every item answered `false`** (measured shares **60.0%** (LLM) / **29.8%** (judge), **not \"about half\"**), and points opposite to `band` |",
     "en §3.8 row 4 (item 7)"),

    (DL,
     "  **reverses the sign of every item answered `false`** (about half of that corpus); and **in the same",
     "  **reverses the sign of every item answered `false`** (measured: **29.8%**, 328/1100; the LLM on the\n"
     "  same corpus is **60.0%**, 660/1100 — **neither is \"about half\"**; source `P19-calibration.json`, see §6.4); and **in the same",
     "en §9.3: the repeated 'about half' (item 7)"),

    # ================================================================ en/06-07 -- items 9, 10, 1, 8, 12
    (BC,
     "| authority location (find the authoritative source among several statements, all options plausible) | LLM | **1.0000** | 48 | P14 |\n"
     "| authority location (as above) | **Laya** | **0.4583** | 48 | P9b |\n"
     "| 77-class intent classification (flat) | LLM | **0.750–0.900** (**4 draws**, centre ≈0.875) | 40 | P15 |",
     "| authority location (find the authoritative source among several statements, all options plausible) | LLM | **1.0000** | 48 | P14 |\n"
     "| authority location (**the other arm of the same 48 items**) | **Laya** | **0.4583** | 48 | P9b |\n"
     "| 77-class intent classification (flat) | LLM | **0.750–0.900** (**4 draws**; **median 0.875, mean 0.850**) | 40 | P15 + P15b r1–r3 |",
     "en §6.1: the paired battery and the two centres (items 9, 10)"),

    (BC,
     "**Three readings**:",
     "**⚠️ The pairing must be stated (ninth-round correction, ERRATA §10.1 item 9)**: the two \"authority location\" rows above are **the two arms of one 48-item battery** — "
     "`P14-llm-arm-full.json`'s `_provenance.consumes` is `P9b-template-validation-separated-n48.json`, and its `complementarity.detail` is **paired item by item** with P9b's 48 rows. "
     "So these two rows are **not two further independent measurements but the two sides of one paired comparison**; this profile counts the same 48 items **twice** (one LLM row, one Laya row) and **should be counted as 1 battery of 48 items** in any evidence count. "
     "**The numbers themselves do not move** (1.0000 and 0.4583 are the measured values on their own arms), but **the reading must change**: they are not two independent pieces of capability evidence.\n"
     "**⚠️ The word \"centre\" must be split here (ninth-round correction, ERRATA §10.1 item 10)**: the four draws are **0.750 / 0.900 / 0.875 / 0.875**, so the **median is 0.875 and the mean is 0.850** — the original \"centre ≈0.875\" holds only for the median. "
     "**And the source column previously read `P15` only**: **3 of the 4 draws are `P15b-rep-r1..r3.json`** (`temperature=0`), and only the recorded round is `P15-complementarity-strong-regime.json`; it now names the artifacts. (§7.3 and the abstract already gave \"empirical centre ≈0.875, mean 0.850\" in full and are unaffected.)\n"
     "\n**Three readings**:",
     "en §6.1: the double count and the centres (items 9, 10)"),

    (BC,
     "**Reliability curve shape** (Laya, **10 equal-width bins, [0,1], last bin right-closed**, all with mass): **the overconfidence is concentrated in the middle**.",
     "**Reliability curve shape** (Laya, **10 equal-width bins, [0,1], last bin right-closed**, **all 10 bins carry mass** — smallest n=1): **the overconfidence is concentrated in the middle, and the low end runs the other way**.",
     "en §6.2: the curve lead-in (item 8)"),

    (BC,
     "| bin | n | claimed P(true) | measured frequency | **gap** |\n"
     "|---|---|---|---|---|\n"
     "| 0.4–0.5 | 169 | 0.453 | 0.148 | **−0.305** |\n"
     "| 0.5–0.6 | 199 | 0.547 | 0.261 | **−0.286** |\n"
     "| 0.6–0.7 | 184 | 0.651 | 0.370 | **−0.281** |\n"
     "| 0.7–0.8 | 176 | 0.749 | 0.540 | **−0.210** |\n"
     "| 0.9–1.0 | 47 | 0.922 | 0.830 | −0.093 |\n"
     "\n"
     "→ **The middle of the range systematically exceeds the measured rate by 21–31 percentage points; the two ends are, if anything, acceptable.**",
     "**gap = measured frequency − claimed P(true)** (the same direction as the `gap` field of `results/P19-calibration.json`).\n"
     "\n"
     "| bin | n | claimed P(true) | measured frequency | **gap** |\n"
     "|---|---|---|---|---|\n"
     "| **0.0–0.1** | **1** | 0.061 | 1.000 | **+0.939** |\n"
     "| **0.1–0.2** | **22** | 0.157 | 0.500 | **+0.343** |\n"
     "| 0.2–0.3 | 51 | 0.252 | 0.294 | +0.042 |\n"
     "| 0.3–0.4 | 85 | 0.351 | 0.235 | −0.116 |\n"
     "| 0.4–0.5 | 169 | 0.453 | 0.148 | **−0.305** |\n"
     "| 0.5–0.6 | 199 | 0.547 | 0.261 | **−0.286** |\n"
     "| 0.6–0.7 | 184 | 0.651 | 0.370 | **−0.281** |\n"
     "| 0.7–0.8 | 176 | 0.749 | 0.540 | **−0.210** |\n"
     "| 0.8–0.9 | 166 | 0.847 | 0.687 | −0.160 |\n"
     "| 0.9–1.0 | 47 | 0.922 | 0.830 | −0.093 |\n"
     "| **Total** | **1,100** | — | — | — |\n"
     "\n"
     "→ **The middle (0.4–0.8, n=169/199/184/176) systematically exceeds the measured rate by 21–31 percentage points.**\n"
     "→ **But \"the two ends are acceptable\" holds only at the high end** (0.8–0.9 gap −0.160, 0.9–1.0 gap −0.093): **the low end runs the other way, with large gaps** — the 0.0–0.1 bin by **+0.939** (n=**1**) and the 0.1–0.2 bin by **+0.343** (n=**22**), i.e. **very low claimed probabilities that the data contradicts**.\n"
     "→ **⚠️ Ninth-round correction (ERRATA §10.1 item 8)**: this table previously printed only **5** of the 10 bins and on that basis wrote \"the two ends are, if anything, acceptable\". **The five omitted bins include the two largest miscalibrations in the whole table (+0.939 and +0.343, both at the low end)**, so \"the two ends are acceptable\" is **false at the low end**; the omitted ones also included 0.2–0.3, 0.3–0.4 and 0.8–0.9. **All 10 bins are now printed** (all carry mass; the n's sum to **1,100**, matching P19's n). **⚠️ The two low-end bins have n = 1 and n = 22 — a bin with n=1 cannot carry any conclusion**; they are printed **not in order to claim anything from them**, but because **omitting them makes this table read as support for a sentence it does not support**.",
     "en §6.2: the reliability table (item 8)"),

    (BC,
     "| the **highest** confidence in the whole probe | **0.9981 — on the single wrong answer** | R13 |\n"
     "| pure-noise state | `noul 0.0011 / confidence 0.9989` | R13 |",
     "| **the highest** confidence **on a wrong answer** (**not** the probe maximum) | **0.9981 — on the single wrong answer** | R13 |\n"
     "| **the probe maximum** confidence (**on a pure-noise state**) | `noul 0.0011 / confidence` **0.9989** | R13 |",
     "en §6.2: the two confidence rows (item 1)"),

    (BC,
     "→ **Value as a contrast**: **on the same batch of items, one judge's maximum confidence is right and the other's is wrong.** A user cannot tell them apart from the returned values.",
     "**⚠️ Ninth-round correction (ERRATA §10.1 item 1)**: this table originally printed **0.9981** as \"the **highest** confidence in the whole probe\", and **that wording is wrong**: **the very next row** (pure-noise state) records **0.9989**, which is higher. "
     "The source `recon\\R13-laya-probe.md:456` records **0.9989**; and **the same file at `:430` says 0.9981 is \"the highest value anywhere in this entire probe\" — the source contradicts itself**. "
     "The table therefore separates the two facts: **0.9981 is the highest value on a wrong answer; the probe maximum is 0.9989, on a pure-noise state.** Together the two rows say what this section needs to say: `confidence` indicates neither correctness nor whether the input carries information. "
     "(**Process note**: `p44` and `p45` each tried to repair this sentence and each reported MISS, because both were pointed at `06-results-B-draft.md` — it has never been in that file. ERRATA §10.1 item 1's file label was wrong in the same way and has been corrected.)\n"
     "→ **Value as a contrast**: **on the same batch of items, one judge's maximum confidence is right and the other's is wrong.** A user cannot tell them apart from the returned values.",
     "en §6.2: the correction note (item 1)"),

    (BC,
     "> **⚠️ Numbering note (audit correction)**: this section's clauses were originally numbered 14–17, and **one of them duplicated clause 13 of the \"Results B\" section (i.e. section 6 of this manuscript) verbatim** (\"the evaluation corpus must contain items in which the candidate value does not appear\"). The duplicate has been deleted, this section is now **14–21**, and the paper's total clause count is corrected, factually, to **23 non-duplicate clauses** (two of §4.4's four clauses duplicate Results B, hence 4+13+8−2 = 23).",
     "> **⚠️ Numbering note (rewritten in the ninth round, ERRATA §10.1 item 12)**: this section has **8 clauses, numbered 14–21**, listed below.\n"
     "> **The previous note was self-contradictory and has been withdrawn**: it said \"this section's clauses were originally numbered 14–17, one of them duplicated clause 13 of Results B verbatim, the duplicate has been deleted, this section is now 14–21\" — **14–17 is four clauses, and deleting one cannot yield eight**. And **none of 14–21 restates clause 13 of Results B** (the closest, clause 16, requires difficulty strata to cross \"explicit support / explicit contradiction\", which is not the same clause as 13's \"the corpus must contain items in which the candidate value does not appear\" — different wording, different referent).\n"
     "> **What is checkable is this**: of §4.4's four clauses (`04-method-draft.md`: probability semantics, per-response type/key assertions, the prose extractor, impossible-value review), **the 1st and 2nd duplicate Results B's 8th and 10th**; Results B has **13 clauses**; this section has **8**. So the paper's non-duplicate total is **4 + 13 + 8 − 2 = 23** — **the 23 stands; only the half-sentence about \"this section was originally 14–17\" is withdrawn**.",
     "en §6.6: the clause-counting note (item 12)"),

    # ================================================================ abstract and intro
    (AB,
     "- **Authority location**: the LLM was correct 48/48, the judge 0.4583, and it **caught none of\n"
     "  the items the LLM missed**;",
     "- **Authority location**: on the **forced-choice arm** the LLM was correct 48/48, the judge 0.4583,\n"
     "  and it **caught none of the items the LLM missed**; **⚠️ the same 48-item battery's prose arm is\n"
     "  the opposite**: LLM **46/48**, **1 judge-only item**, **Δ_catch = +0.0435** (95% CI [−0.386,\n"
     "  +0.471], resting on **2** items where the LLM errs). **Among the regime-level readings of the\n"
     "  three regimes, this is the only Δ_catch point estimate that is positive**, and we report it as\n"
     "  it stands, with its width and its denominator (§8.2);",
     "en abstract: the regime-1 bullet (item 3)"),

    (AB,
     "- **77-class intent classification** (n=40, **4 draws**): LLM **0.750–0.900** (centre ≈0.875),",
     "- **77-class intent classification** (n=40, **4 draws**): LLM **0.750–0.900** (the four are\n"
     "  0.750 / 0.900 / 0.875 / 0.875; **median 0.875, mean 0.850**),",
     "en abstract: the two centres (item 10)"),

    (IN,
     "**Across three task regimes, the answer is negative** (§8): in the first two regimes the LLM hits the ceiling, which makes its error structure **not measurable**; in the third regime the ceiling has been broken and the items were **re-judged after the ground-truth fix**, where Δ_catch is uniformly negative and the **failure correlation is significantly positive**:",
     "**Across three task regimes, the answer is negative** (§8): regime one **gives different answers in its two answer formats** — the forced-choice arm has the LLM at 48/48 (error structure not measurable), while **the prose arm is measurable and its Δ_catch point estimate is +0.0435 (positive, interval containing 0)**; in regime two the LLM is at the ceiling (0.750–0.900), which thins its error structure, but **Δ_catch is negative in 4/4 draws**; in the third regime the ceiling has been broken and the items were **re-judged after the ground-truth fix**, where Δ_catch is uniformly negative and the **failure correlation is positive in 3/3 draws pooled** "
     "(**⚠️ ninth-round correction**: this sentence previously printed \"the failure correlation is **significantly** positive\" — that wording was withdrawn in §8.6.1, where stratifying by difficulty leaves none of the three draws significant; this was a missed propagation, see §8.6.1):",
     "en intro: the three-regime sentence"),

    (IN,
     "| Authority location | **1.0000** | 0.4583 | **0** | 26 | not definable (LLM zero errors) |",
     "| Authority location (**forced-choice arm**) | **1.0000** | 0.4583 | **0** | 26 | not definable (LLM zero errors) |\n"
     "| Authority location (**prose arm**, same 48 items) | **0.9583** | 0.4583 | **1** | **25** | **+0.0435** (interval containing 0) |",
     "en intro: the regime table"),

    (IN,
     "and reporting that **no** incremental coverage was **found**.",
     "and reporting that **no established** incremental coverage was **found** (**⚠️ ninth-round qualification**: regime one's prose arm gives a **positive** point estimate whose interval contains 0, so \"not found\" must not be read as \"does not exist\", see §8.2).",
     "en intro: the increment sentence"),

    (DL,
     "**Basis** (§7): on **three** regimes, the heterogeneous judge provided no incremental coverage at all —\n"
     "- regime one (authority location, n=48): it **caught none** of the items the LLM missed (judge-only correct\n"
     "  **0**, against LLM-only correct **26**);",
     "**Basis** (§7): on **three** regimes, the heterogeneous judge provided no **established** incremental coverage —\n"
     "- regime one (authority location, n=48): on the **forced-choice arm** it **caught none** of the items the LLM\n"
     "  missed (judge-only correct **0**, against LLM-only correct **26**); **⚠️ but on the same 48-item battery's\n"
     "  prose arm the LLM errs on 2 items and the judge catches 1 of them, Δ_catch = +0.0435 (interval containing\n"
     "  0)** — so the wording here can only be \"no established incremental coverage\", not \"no incremental\n"
     "  coverage\" (§8.2);",
     "en §9.6: the regime-1 bullet"),
]


def main() -> int:
    cache: dict[str, str] = {}

    def get(name: str) -> str:
        if name not in cache:
            cache[name] = (PAPER / "en" / name).read_text(encoding="utf-8")
        return cache[name]

    ok = miss = 0
    for entry in EDITS:
        fname, old, new, label = entry
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
        (PAPER / "en" / fname).write_text(t, encoding="utf-8")

    # the English build must be regenerated from its sources, exactly like the Chinese one
    r = subprocess.run([sys.executable, str(PAPER / "en" / "_assemble.py")],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(PAPER.parent))
    tail = (r.stdout or "").strip().splitlines()[-3:]
    for line in tail:
        print("   ", line)
    if r.returncode != 0:
        print(r.stderr)
        miss += 1

    # post-conditions: the mirrors must actually be in the English sources
    for name, needle in ((AB, "+0.0435"), (IN, "+0.0435"), (D, "+0.0435"),
                         (D, "0.076 / 0.061 / 0.149"), (BC, "**0.9989**"),
                         (BC, "`warnings`"), (BC, "0.8–0.9 | 166"), (DL, "0.0435")):
        if needle in get(name):
            print(f"  ok    en/{name} carries {needle!r}")
        else:
            print(f"  MISS  en/{name} lacks {needle!r}")
            miss += 1

    print(f"\n{ok} applied, {miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
