# arXiv 背书请求 —— 可直接复制发送

**代码：`BZKLNO`** ｜ 分类：**cs.CL** ｜ 状态：等一位背书人回信

> **发送前必须先查**：在 arXiv 摘要页底部点 **"Which of the authors of this article can endorse?"**，
> 确认对方**能背书 `cs.CL`**。不能就换下一位。

---

## 为什么这版比你之前看到的更有力

**论文已经在 Zenodo 上发表了，有 DOI。** 请求信里现在能写的是：

> 「我的论文已发表，DOI 在此。」

**这比「我有一个 GitHub 仓库」强得多。** 背书人最担心的是给一个来路不明的人担保；**已发表、有 DOI、可全文查阅的成果，把这个担心去掉了大半。**

而**最有力的那一句**仍然是你论文独有的：

> **论文在正文中标明了自己四条被撤回的结论。**

**这一条几乎无法伪造**，而且它证明的不是「我做了很多工作」，而是**「我愿意被核验」**——**这恰恰是 arXiv 版主和背书人真正在意的东西。**

---

## 收件人与邮箱（已核实）

| 优先 | 收件人 | 邮箱 | 用哪篇论文搭话 |
|---|---|---|---|
| **1** | **Prof. Pilsung Kang**（首尔大学） | **`pilsung_kang@snu.ac.kr`** | *Same Answer, Different Confidence: Protocol Sensitivity in LLM Confidence Calibration* |
| 2 | **Prof. Yulia Tsvetkov**（华盛顿大学） | **`yuliats@cs.washington.edu`** | *Know Your Limits: A Survey of Abstention in Large Language Models* |
| 3 | **Dr. Nils Feldhus**（DFKI） | **`Nils.Feldhus@dfki.de`** | *Judge Circuits Explain Format-Induced Inconsistency in LLM...* |

---

# 信件 ①（发给 Kang 教授）

**主题：**
```
arXiv endorsement request (cs.CL) — measurement study of judgment layers
```

**正文：**

```
Dear Professor Kang,

I am an independent researcher and would like to submit a measurement study to
arXiv (cs.CL). I am approaching you because your paper "Same Answer, Different
Confidence: Protocol Sensitivity in LLM Confidence Calibration" addresses almost
exactly the question my paper measures, and I cite it.

My endorsement code is: BZKLNO

The paper is written and already published, so you can read it in full before
deciding:

  Paper (English)  10.5281/zenodo.22901853
  Artifact + every measurement + the audit trail
                   https://github.com/PerryLink/llm-jev-laya-bench
                   10.5281/zenodo.22901248

It measures the cost, latency and failure boundaries of three judgment layers on
a common item set — a local non-autoregressive typed-decision model, a remote
typed-decision service, and a frontier LLM. Its central contribution is negative:
the judges' own self-reported fields are unreliable, capability collapses exactly
where the task requires noticing an ABSENCE, and a heterogeneous judge provided no
incremental coverage in any of three task regimes.

Two things may be worth knowing before you decide. First, four of the paper's own
earlier conclusions are RETRACTED IN THE TEXT rather than quietly corrected, and
the audit trail records why each was withdrawn. Second, the artifact ships with 60
automated checks that anyone can re-run, including a standard-library-only
recomputation of every interval and exact test in the paper.

I publish under the name Perry Link rather than my legal name, for personal
reasons; I am happy to identify myself privately if that would help you decide.
What I am asking you to endorse is the category, and I am asking on the strength
of the work.

To endorse, please visit: https://arxiv.org/auth/endorse

Thank you for considering it.

Perry Link
Independent Researcher
```

---

# 信件 ②（发给 Tsvetkov 教授）

**只改第二段**，其余完全相同：

```
I am an independent researcher and would like to submit a measurement study to
arXiv (cs.CL). I am approaching you because your survey "Know Your Limits: A
Survey of Abstention in Large Language Models" maps the space my paper measures a
corner of, and I cite it.
```

---

# 信件 ③（发给 Feldhus 博士）

**只改第二段**：

```
I am an independent researcher and would like to submit a measurement study to
arXiv (cs.CL). I am approaching you because your paper "Judge Circuits Explain
Format-Induced Inconsistency in LLM..." is the closest prior work to my section on
why a judge's own reported fields cannot be trusted, and I cite it.
```

---

## 发送纪律

1. **一次只发一位。** 三人同时发，被识破的概率不低，而且不专业。
2. **只发 Kang 教授这一封，等 3–5 天。** 没回音再发 Tsvetkov。
3. **不要跟进催促。** 一周后可以发一封两行的礼貌提醒，仅此一次。
4. **信不要再加长。** 它已经到了合适的上限。

---

## 三个人的回复预期

| 情形 | 怎么办 |
|---|---|
| 回信同意，并已背书 | 回到 <https://arxiv.org/submit/8115595/start> 继续投稿 |
| 回信说「我不够格」 | 换下一位。他可能是好意但确实不满足 3 篇规则 |
| 回信拒绝 | 换下一位，**不要追问理由** |
| 三人都没回 | 回参考文献里再找资深作者；或换 cs.AI 试（**换分类需要新的代码**） |
| 一周无回音 | 发一封两行提醒，仍无回音就换人 |

---

## 与此同时

**arXiv 只是曝光渠道，不是发表的必要条件——你已经发表完了。**

**中文稿的发表问题已经解决**（Zenodo `10.5281/zenodo.22902025`）。
**制品也已经有 DOI 了**（`10.5281/zenodo.22901248`）。

**优先权已经确立，带时间戳，公开可引用。** arXiv 通过了是锦上添花，通不过也不影响你已经拿到的东西。
