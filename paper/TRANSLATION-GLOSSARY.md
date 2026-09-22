# Translation glossary and style rules

**Status: DRAFT — awaiting the author's approval before any translation begins.**

A faithful full translation needs ONE English rendering per term, fixed before prose is
written. Without that, the same Chinese word becomes three English words in three sections
and a reader cannot tell whether two things are the same thing. This file is that contract.

The manuscript is **84,149 characters / 1,738 lines**, so the translation is a substantial
piece of work, not a pass over the abstract. Getting the vocabulary wrong first is expensive.

---

## 1. Core terms

Frequency is the count in the current manuscript, so the table is ordered by how much a bad
choice would cost.

| Chinese | n | English | Note on the choice |
|---|---|---|---|
| 判定器 | 110 | **judge** | Not "adjudicator" (legalistic), not "classifier" (too narrow — these return probabilities and verdicts). "judge" is the term the LLM-as-a-judge literature uses, and the paper positions against that literature. |
| 条目 | 71 | **item** | The benchmark/psychometrics convention. Not "entry" or "sample". |
| 区制 | 63 | **regime** | An experimental condition, not a "region" or "zone". Three regimes: authority location, 77-class intent, chained verification. |
| 真值 | 47 | **ground truth** | Hyphenate as a modifier: "ground-truth derivation". |
| 窗口 | 46 | **window** | Always the context/state window. First use: "context window". |
| 接入层 | 34 | **access layer** | The layer between the provider and the caller that synthesises `band`, `probability`, `truncated`. This is a central term — it must never become "interface layer" or "API layer". |
| 互补性 | 28 | **complementarity** | The paper's fourth claim. |
| 钳位 | 26 | **clamp** | The point past which padding stops growing. Verb and noun both "clamp". Not "truncation" — the paper distinguishes them sharply (silent clamp vs flagged truncation). |
| 生成器 | 23 | **generator** | The autoregressive model, as opposed to the judge. |
| 自报字段 | 22 | **self-reported field** | Never "self-declared" or "metadata field". This is claim two. |
| 断言 | 21 | **assertion** | A build-time check that raises. Distinguish from 证书 below. |
| 证书 | 6 | **certificate** | The per-item build-time property (derivability + load-bearing). "Warrant" reads too philosophical. |
| 判定层 | 5 | **judgment layer** | The category the paper compares across. First use should gloss it. |
| 载入配置 | 20 | **launch loadout** | The paper already writes `loadout` in English; keep the identifier and use "launch loadout" in prose. |
| 可推导性 | 1 | **derivability** | Expand on first use: "the scored answer is derivable from the rendered state". |
| 失效模式 | — | **failure mode** | |
| 能力塌缩 | — | **capability collapse** | The paper's own coinage for the §7 finding. Keep it as a quoted phrase, flag it as coined. |
| 过自信 | — | **overconfidence** | |
| 长线 | — | **long-horizon** | "long-horizon reliability", not "long-term". |
| 逐项标签一致率 | — | **item-level label agreement** | The reproducibility statistic. Not "per-item consistency". |
| 未配对 Wald | — | **unpaired Wald** | The paper's intervals are unpaired and conditional; say so every time. |
| 条件正确率 | — | **conditional accuracy** | P(judge correct \| generator wrong/right). |
| 边际 | — | **marginal** | As in "marginal accuracy". |
| 自测 | — | **our own measurement** | The paper's source-tier marker; never "self-tested". |
| 外推 | — | **extrapolation** | |
| 受限 | — | **bounded** / **qualified** | Choose per sentence; there is no single rendering. |

---

## 2. Never translate these

These are identifiers, not prose. Translating or "tidying" them breaks traceability.

- **Field names**: `noul`, `probability`, `probabilities`, `band`, `truncated`, `fits`,
  `confidence`, `legend`, `score`, `choice`, `answer`, `type`, `costUsd`, `latencyMs`
- **Verdict vocabulary**: `no_support`, `partial_support`, `explicit_support`,
  `partial_contra`, `explicit_contra`, `conflicted`, `undecided`, `insufficient`
- **Paths and filenames**: `results/P22b-fixed-r1.json`, `src/instrument/jev_client.py`
- **Artifact IDs**: `P3`, `P22b`, `P27`, `CH-K8-021`, `RC-01-N21`, `CAL-explicit_support-0000`
- **Statistics**: `Δ_catch`, `φ`, `κ`, `AUC`, `ECE`, `Brier`, `REL`/`RES`/`UNC`, `MDE`
- **Model IDs**: `deepseek-flash`, `typesafe/jev-1.13`, `laya-mcp` 0.2.1
- **Crossrefs**: `§7.6.1` — renumber identically; the assembler remaps them, so the English
  build must use the same numbering or every cross-reference breaks

---

## 3. Style rules

1. **The paper's register is evidentiary, not promotional.** Chinese academic prose tolerates
   more explicit self-assessment ("论文不得声称…") than English does. Keep the substance;
   render "the paper must not claim X" as "we do not claim X" or "the evidence does not
   support X", not as a meta-instruction to the reader.
2. **Preserve the hedging exactly.** Every 限定 / 必须 / 不得 / 不能 is load-bearing. Where the
   Chinese says a figure "should not be read as precise", the English must not soften it to
   "should be interpreted with care".
3. **Preserve the em-dash asides.** The manuscript uses 「——」 to carry qualifications inline.
   English can use an em dash or a parenthetical; do not delete them to smooth the prose.
4. **Numbers, units and n's are copied verbatim**, including the exact decimal places. The
   paper makes a point about not printing more digits than an interval supports.
5. **Every ⚠️ marker stays a warning.** There are many, and they mark the places where a
   reader would otherwise over-read a result.
6. **Two registers of uncertainty must stay distinct**: "not measurable" (ceiling effect) vs
   "not found" (measured, negative). The Chinese distinguishes 不可测 from 未发现; English must too.
7. **Do not add citations in translation.** The reference list is built and verified
   separately, and a citation invented during translation is exactly the failure mode the
   policies punish.

---

## 4. Structural decisions still open

- **Length.** A faithful translation of 84k characters is roughly 40–60 pages. The author has
  chosen faithful-full over abridged, so this is expected — but TMLR reviewers will ask for
  compression, and the compression should happen to the CHINESE and ENGLISH in parallel, not
  to the English alone, or the two versions will diverge.
- **What moves out of the paper.** The five rounds of audit (`protocol/AUDIT-FINDINGS.md`,
  20 `recon/` reports, `results/ERRATA.md`) are process records. They are excellent evidence
  and belong in the artifact; a 40-page paper does not need to narrate them. Moving them out
  is a content decision for the author, not a translation decision.
- **Which language is primary on arXiv.** arXiv's policy (in effect since 2026-02-11) hosts
  both the original and the English version. The original is the Chinese manuscript; the
  English is the translation. Confirm before submitting.
