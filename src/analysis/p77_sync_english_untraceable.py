"""Mirror the ERRATA 10.2 untraceable-number markers into the English section files.

WHY
---
p76 marked 15 places in the Chinese drafts where a printed number has no `results/` artifact
behind it. If those markers exist only in Chinese, the English version -- the version arXiv
requires -- prints the same numbers with no qualification at all, and the two published
documents disagree about what is evidence. That is a worse defect than either version being
wrong alone, and it is the specific failure `paper/verify_all.py` check I5 was written for
(a translation that was silently one third short while every other check stayed green).

The marker wording is fixed here exactly as in Chinese, so a reader of either language learns
the convention once.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bench_env import PAPER  # noqa: E402

BC = "06-07-results-BC.md"
D = "08-results-D.md"
A = "05-results-A.md"
AB = "00-abstract.md"
DL = "09-10-11-discussion-limits-repro.md"


def mark(source: str, what: str = "") -> str:
    tail = f" ({what})" if what else ""
    return (f" **【NOT TRACEABLE ⚠️ ERRATA §10.2】**: this number has **no `results\\` artifact**; "
            f"it exists only in the lab record `{source}`{tail}. By this paper's own standard "
            f"(§11.5) **it cannot serve as evidence**; it is kept here as a record only.")


EDITS: list[tuple] = [
    # ------------------------------------------------------------------ Brier and t
    (BC,
     "- **The original wrote \"anti-information\" — that wording is too strong and has been downgraded**: at n=10 the standard error of a Brier difference of 0.109 is about 0.10 (t ≈ 1.1, **not significant**). The correct statement is \"**shows no information on this sample**\";",
     "- **The original wrote \"anti-information\" — that wording is too strong and has been downgraded**: at n=10 the standard error of a Brier difference of 0.109 is about 0.10 (t ≈ 1.1, **not significant**). The correct statement is \"**shows no information on this sample**\""
     + mark("probes\\P13-jev-remaining-measurements.md",
            "the t value is a hand computation from 0.109/0.10; no script and no artifact anywhere in the tree")
     + ";",
     "en §3.1: t ≈ 1.1 (10.2)"),

    # ------------------------------------------------------------------ the 7 verdicts
    (BC,
     "| a single unattributed note | 0.06 | 0.04 | 0.03 | `insufficient` |",
     "| a single unattributed note | 0.06 | 0.04 | 0.03 | `insufficient` |\n"
     "\n"
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **all 7 rows of this table** (and the `sufficient` readings quoted from it) have **no `results\\` artifact** — **no JSON under `results\\` contains a `sufficient` field at all**; these readings exist only in the lab record `probes\\P13-jev-remaining-measurements.md:47-56` (see also `protocol\\AUDIT-FINDINGS.md`). **So this table can only be read as a record, not as a re-checkable measurement**; the qualitative conclusion drawn from it (the five-value vocabulary degenerating to three) is internally consistent **within that record**, but **external verification needs a rerun** — and a rerun produces new numbers (`temperature` was not pinned), which is a cost this project has already documented.",
     "en §3.5: the 7 verdict rows (10.2)"),

    # ------------------------------------------------------------------ kappa CI
    (BC,
     "18. **The number of digits in a point estimate must not exceed the precision its interval width allows.** **Basis**: \"κ = 0.0062 is indistinguishable from chance\" is a four-decimal-place statement about an estimate whose bootstrap 95% CI is **[−0.185, +0.206]**.",
     "18. **The number of digits in a point estimate must not exceed the precision its interval width allows.** **Basis**: \"κ = 0.0062 is indistinguishable from chance\" is a four-decimal-place statement about an estimate whose bootstrap 95% CI is **[−0.185, +0.206]**. "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that bootstrap interval has **no `results\\` artifact and no script** — `P28-recomputed-statistics.json` recomputes Wald / Newcombe / Fisher / Clopper-Pearson and **contains no bootstrap**; the interval comes from a one-off interpreter session during the audit. The clause's lesson does not depend on this particular interval (the artifacts support enough κ-adjacent statistics to make the point), but **the number itself cannot be re-checked**.",
     "en §6.6 clause 18: the kappa bootstrap CI (10.2)"),

    (BC,
     "and every published P1 number is still reproducible (an independent replay of the 18 requests is **field-by-field, bit-for-bit identical** except for `latency_ms`).",
     "and every published P1 number is still reproducible (an independent replay of the 18 requests is **field-by-field, bit-for-bit identical** except for `latency_ms`). "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **that independent replay has no artifact and no script** — `P1-rank-vs-choice.json` has only `summary` and `rows`, **with no replay record of any kind**; the replay result comes from a one-off session during the audit. So the honest statement here is \"the record says the replay was bit-identical\", **not \"this has been reproduced\"**; asserting that would require the replay itself to be a script with a stored artifact (not done).",
     "en §6.6 clause 19: the 18-request replay (10.2)"),

    (BC,
     "so **the scored ground truth is not derivable for 11/69 items (15.9%)**, and for 10 of them the faithful answer is not even among the options (§8.6.1).",
     "so **the scored ground truth is not derivable for 11/69 items (15.9%)**, and for 10 of them the faithful answer is not even among the options (§8.6.1). "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the 69 rows of `P22-chain-audit.json` **carry no derivability field** (the row keys are `truth` / `llm_*` / `laya_*` / `alt_in_options` only), so **the count of 11 cannot be obtained from the artifact**; it comes from an independent recomputation during the audit. **After the fix** the battery enforces the property by build-time assertion (**96 → 0 → 68**), and **that part is checkable**; the historical \"11/69 before the fix\" can only be read as a record.",
     "en §6.6 clause 21: 11/69 (10.2)"),

    # ------------------------------------------------------------------ band
    (BC,
     "| `no_support` | the evidence does not exist | asserts true (P=0.564) | `band` gives low confidence, but `noul` is above 0.5 |",
     "| `no_support` | the evidence does not exist | asserts true (P=0.564) | `band` gives low confidence, but `noul` is above 0.5 (**⚠️ not traceable: `P19-calibration.json` has no `band` column, see below**) |",
     "en §6.5: the band cell (10.2)"),

    (BC,
     "**This hypothesis can be falsified**: if, on items where \"the candidate value does not appear\", it is given an **explicit absence marker**",
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the `band` assertion in the `no_support` row above **has no artifact behind it** — the 1,100 rows of `P19-calibration.json` **have no `band` field** ( `band` is an access-layer derivation; P19 records `noul` and `laya_p`). "
     "That row is therefore **kept as a shape description only**: what the artifacts support is the distribution of `noul` (mean 0.5643) and the accuracy (0.3091), **not** any distribution of `band` values. **Claiming a `band` distribution would require a rerun that records that field** (not done).\n"
     "\n**This hypothesis can be falsified**: if, on items where \"the candidate value does not appear\", it is given an **explicit absence marker**",
     "en §6.5: the band distribution (10.2)"),

    # ------------------------------------------------------------------ the R13 points
    (BC,
     "→ **Value as a contrast**: **on the same batch of items, one judge's maximum confidence is right and the other's is wrong.** A user cannot tell them apart from the returned values.",
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: the four rows of the table above marked **R13** (0.9981, 0.9989, 0.5399 vs 0.0046, and `noul 0.0011`) **have no `results\\` artifact** — they come from the lab record `recon\\R13-laya-probe.md` (`:430`, `:456`, `:448-449`), which records those responses as verbatim JSON, but **no result JSON corresponds to them**; the table's other two rows (P9b's 0.218 / 0.115) do have artifacts. "
     "**So those four rows can only be read as case records**: their value is the **shape** (the same field can be far from correctness in either direction), not re-checkability. Turning them into re-checkable evidence would require the requests and responses of that round to be written to an artifact (not done).\n"
     "→ **Value as a contrast**: **on the same batch of items, one judge's maximum confidence is right and the other's is wrong.** A user cannot tell them apart from the returned values.",
     "en §6.2: the four R13 points (10.2)"),

    # ------------------------------------------------------------------ section 8
    (D,
     "Consequence: **11/69 items (15.9%) have a scored ground truth that cannot be derived from the rendered question** (of which 10 have a \"faithful reading\" answer that is not even among the options).",
     "Consequence: **11/69 items (15.9%) have a scored ground truth that cannot be derived from the rendered question** (of which 10 have a \"faithful reading\" answer that is not even among the options). "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: `P22-chain-audit.json` has no derivability field, so this count cannot be obtained from the artifact (see the note at §7.6 clause 21); **after the fix** the 96 → 0 → 68 property is enforced by assertion and that part is checkable.",
     "en §7.6.1: 11/69 (10.2)"),

    (D,
     "⇒ **The paper must not claim \"the ground-truth defect depressed the effect\".** The counter-evidence is in this project's own records: rerunning the same 69-item battery **without any fix at all** twice already gives Δ_catch of **−0.0328 / −0.2071** — **the same magnitude is reachable without doing the ground-truth fix**.",
     "⇒ **The paper must not claim \"the ground-truth defect depressed the effect\".** The counter-evidence is in this project's own records: rerunning the same 69-item battery **without any fix at all** twice already gives Δ_catch of **−0.0328 / −0.2071** — **the same magnitude is reachable without doing the ground-truth fix**. "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: **those two n=69 reruns have no artifact** — the chain artifacts in `results\\` are the recorded round (n=69, `P22-chain-audit.json`) and **three n=68 draws after the fix** (`P22b-fixed-r1..r3.json`); **there is no second n=69 JSON**; −0.0328 / −0.2071 come from a session during the audit (`results\\ERRATA.md` §5 records them in prose, which is not an artifact either). "
     "**The direction of this argument does not depend on those two numbers** (`P22b`'s three negative draws and the recorded round's −0.007 already show that the negative sign is reachable without the fix), but **the numbers themselves cannot be re-checked**.",
     "en §7.6.1: the two n=69 reruns (10.2)"),

    (D,
     "; doing a 68-item permutation test at the correct clustering level gives a correlation of **+0.243**, **p = 0.057**;",
     "; doing a 68-item permutation test at the correct clustering level gives a correlation of **+0.243**, **p = 0.057** "
     "(**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that permutation test has **no artifact and no script** — `P28-recomputed-statistics.json` recomputes Wald / Newcombe / Fisher / Clopper-Pearson / AUC and **contains no permutation test**; **neither its definition nor its seed is recorded**, so it is **not reproducible**. Its role here is to **weaken** the significance claim above, so removing it would leave fewer objections, not more — and it is still marked, because what is being marked is checkability, not direction);",
     "en §7.6.1(c): the permutation test (10.2)"),

    (D,
     "the **pooled** failure correlation is positive in 3/3 draws, but **after stratifying by K none of the three is significant** (CMH permutation p = 0.059 / 0.055 / 0.201)\", rather than giving a precise effect size, and rather than \"significantly shared failure\".",
     "the **pooled** failure correlation is positive in 3/3 draws, but **after stratifying by K none of the three is significant** (CMH permutation p = 0.059 / 0.055 / 0.201; **⚠️ this group of p-values is not traceable — no artifact, no script and no recorded seed, see §8.6.1(d)**)\", rather than giving a precise effect size, and rather than \"significantly shared failure\".",
     "en §7.6.1(d): the CMH p-values (10.2)"),

    (D,
     "and it states plainly that the recorded round's κ = 0.0062 has a bootstrap 95% CI of **[−0.185, +0.206]** — reading a point estimate ±0.2 wide to four decimal places.",
     "and it states plainly that the recorded round's κ = 0.0062 has a bootstrap 95% CI of **[−0.185, +0.206]** — reading a point estimate ±0.2 wide to four decimal places. "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that bootstrap interval has no artifact and no script (`P28` contains no bootstrap); see the note at §7.6 clause 18.",
     "en §7.6: the kappa CI (10.2)"),

    (D,
     "(a) **The two arms' visible prefixes are bit-identical** — the dropped arm still has a ~4× clamp, and the correction sits at tokens 1,943–1,952, **beyond the 512 window the two share**, so \"the two arms give the same answer\" is a **construction necessity**;",
     "(a) **The two arms' visible prefixes are bit-identical** — the dropped arm still has a ~4× clamp, and the correction sits at tokens 1,943–1,952, **beyond the 512 window the two share**, so \"the two arms give the same answer\" is a **construction necessity**; "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that token position **has no artifact** — the `P25`/`P26` artifacts record `in_pad`, `truncated`, the options and the verdicts, **not the absolute position of the correction**; 1,943–1,952 comes from a one-off check during the audit. **The direction of the argument is supported by artifacts** (the shared window is 512 and the truth is always last), but **this specific position cannot be re-checked**;",
     "en §7.7(a): the token position (10.2)"),

    (A,
     "A token-by-token check: **the first 512 token ids of the two arms are completely identical on 10/10 items**, while the position of the correction is token **1,943–1,952**.",
     "A token-by-token check: **the first 512 token ids of the two arms are completely identical on 10/10 items**, while the position of the correction is token **1,943–1,952**. "
     "**【NOT TRACEABLE ⚠️ ERRATA §10.2】**: that token position has no `results\\` artifact (see the note at §8.7(a)); the \"first 512 token ids are identical\" part **is indirectly supported by P26's `in_pad` and option records**, but the absolute position is not.",
     "en §5: the token position (10.2)"),

    (AB,
     "  difficulty** (CMH permutation p = 0.059 / 0.055 / 0.201).",
     "  difficulty** (CMH permutation p = 0.059 / 0.055 / 0.201; **⚠️ this group of p-values is not\n"
     "  traceable — no artifact, no script, no recorded seed, see §8.6.1(d)**).",
     "en abstract: the CMH p-values (10.2)"),
]

ANCHOR_115 = ("**⚠️ A gap that is still not closed**: `deepseek_client.py` — the LLM arm's own client — "
              "**no file in the\nwhole tree hashes it**.")
ANNEX_115 = """## 11.6 Numbers traceable only to a lab record, with **no `results\\` artifact**
(`results\\ERRATA.md` §10.2, complete)

**This paper's standard is that a number which cannot be re-checked cannot serve as evidence.
The numbers below are printed in the body, but there is NO `results\\` artifact behind them** —
most exist only in a `recon\\` / `probes\\` lab record, or in a one-off interpreter session
during the audit. **They are not necessarily wrong** (several were independently recomputed to
within Monte Carlo error), but **by this paper's own standard they cannot serve as evidence**.
Each is marked where it appears; they are collected here so that a reader who samples the paper
still sees the disclosure.

| # | number | where printed | what it actually rests on | artifact-backed alternative |
|---|---|---|---|---|
| 1 | mock battery **Brier 0.359**, **t ≈ 1.1** | §6.1, abstract, §1, §3 | `recon\\R12-jev-probe.md:187` (the t is hand-computed from 0.109/0.10) | none (the live calibration battery's Brier **0.2571** does have one: `P19-calibration.json`) |
| 2 | the κ bootstrap 95% CI **[−0.185, +0.206]** | §7.6 clause 18, §8.6 | a one-off session; `P28` contains no bootstrap | Wald / Newcombe / Fisher / Clopper-Pearson (`P28-recomputed-statistics.json`) |
| 3 | CMH permutation p **0.059 / 0.055 / 0.201** | §8.6.1(d), abstract | a one-off session; **no definition, no seed** | per-stratum and pooled φ (`P28` has φ; **the per-stratum values are still prose-only**) |
| 4 | the 68-item permutation test (**+0.243**, p = 0.057), **its definition and seed** | §8.6.1(c) | a one-off session, definition and seed unrecorded | none |
| 5 | two **n=69** chain reruns (Δ_catch **−0.0328 / −0.2071**) | §8.6.1 | a one-off session; `ERRATA.md` §5 records them in prose | the three post-fix **n=68** draws (`P22b-fixed-r1..r3.json`) |
| 6 | **11/69 (15.9%)** non-derivable ground truths | §7.6 clause 21, §8.6.1 | an independent recomputation during the audit; **`P22` has no such field** | the post-fix **96 → 0 → 68** (build-time assertion, `P22b`) |
| 7 | "an independent replay of the 18 requests, bit-identical except `latency_ms`" | §7.6 clause 19 | a one-off session; `P1` has no replay key | the 18 rows of `P1-rank-vs-choice.json` themselves |
| 8 | **every `jev_check` verdict reading** (the 7-row table) | §6.5 | `probes\\P13-jev-remaining-measurements.md:47-56` | none (**no JSON under `results\\` contains a `sufficient` field**) |
| 9 | the **`band` distribution** on `no_support` items | §7.5 table | same; `P19` **has no `band` column** | the `noul` distribution and accuracy (`P19-calibration.json`) |
| 10 | **four R13 case points** (0.9981 / 0.9989 / 0.5399 vs 0.0046 / 0.0011) | §7.2 | `recon\\R13-laya-probe.md:430`, `:456`, `:448-449` | P9b's two rows (0.218 / 0.115, `P9b-...json`) |
| 11 | the correction's **token position 1,943–1,952** | §5, §8.7(a) | a one-off session; `P25`/`P26` have no such field | the two arms' shared 512 window (`P26`'s `in_pad`) |
| 12 | — | — | — | — |

**⚠️ This table is itself an application of the paper's argument**: it is **hand-written**, and
will therefore also go stale — row 12 is blank because the categories listed in ERRATA §10.2
are already covered by rows 1–11, not because an item is missing. **The list of categories is
determined by `results\\ERRATA.md` §10.2, not by this table**; if that section changes, this
table must change with it.

"""
EDITS.append((DL, ANCHOR_115, ANNEX_115 + ANCHOR_115,
              "en §11.6: the consolidated untraceable list (10.2)"))


def main() -> int:
    cache: dict[str, str] = {}

    def get(name: str) -> str:
        if name not in cache:
            cache[name] = (PAPER / "en" / name).read_text(encoding="utf-8")
        return cache[name]

    ok = miss = 0
    for fname, old, new, label in EDITS:
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

    r = subprocess.run([sys.executable, str(PAPER / "en" / "_assemble.py")],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(PAPER.parent))
    for line in (r.stdout or "").strip().splitlines()[-3:]:
        print("   ", line)
    if r.returncode != 0:
        print(r.stderr)
        miss += 1

    n = sum(v.count("【NOT TRACEABLE ⚠️ ERRATA §10.2】") for v in cache.values())
    if n >= 11:
        print(f"  ok    {n} English untraceable markers (expected >= 11)")
    else:
        print(f"  MISS  only {n} English untraceable markers")
        miss += 1

    print(f"\n{ok} applied, {miss} problems")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
