# R6 — Jev 接口裁决与代价（R12 实测后的修订）

> 作者：主控
> 依据：R12 完整报告（68 次调用：62 次 mock 成功、6 次拒绝前拦截、**0 次真实**）。
> 本文件**修订 R3/R5 中涉及 Jev 的部分**，并新增三条会导致「静默错误数字」的强制规则。

---

## 1. 头条：**零条真实 Jev 数据存在**

| 结果 | 计数 | 签名 |
|---|---|---|
| mock 成功响应 | **62** | `provider:"mock"`、`latencyMs:0`、`inputTokens:0`、`outputTokens:0`、`costUsd:0`、含 SYNTHETIC 警告 |
| provider 前置拒绝 | 6 | 仅错误串 |
| **`provider != "mock"`** | **0** | — |
| 非零延迟/token/成本 | **0** | — |
| 合计调用 | 68 | |

**凭证不存在**：环境变量无 `typesafe|jev|openrouter|openai|anthropic|api_key|token`；`.credentials.yaml` 只登记了 `DEEPSEEK_API_KEY`（仅检视键名，未读取值）。

### 1.1 mock 的确切契约（R12 实证，非引用文档）

- 答案 = `FNV-1a(questionId + "\u0000" + JSON.stringify(state))`，保留 4 位小数。
- **instructions、criteria、选项描述完全不参与哈希** → **把问题改写成相反的意思，数字不会动。**
- **boundary 也不参与哈希** → 声明 vs 不声明的差值是**构造性的 0.0000**。
- `confidence` 在 mock 下是**硬编码常量 0.5**，与选项数、与正确性均无关。

**⚠️ 由此产生的最大陷阱**：在 mock 上做边界敏感性实验会得到**恰好零差值**，从而「证明」边界措辞无关紧要。这是**夹具产生的假阴性**，不是关于 Jev 的发现。
→ **R12 因此推翻了我的 R2 建议**：R2 曾建议强制声明 boundary；R12 实测表明**该建议缺乏测量依据**。修订为：**boundary 仍写入协议以保证可复现，但在 live 差值被证明非零之前，不得声称其有或没有效果。**

---

## 2. **三条会导致静默错误的语义陷阱**（最高危，必须写入协议）

### T-1 `probability` 是「所选选项的概率」，**不是 P(true)**

R12 在 62 条响应中一致验证：
- `answer == "true"` 时 `probability == noul`
- `answer == "false"` 时 `probability == 1 − noul`

→ **任何把 `probability` 当作 P(true) 记录的 harness，会静默地把它那一半条目反号。**
**强制规则**：**记录 `noul` 作为 P(true)**，永不记录 `probability`；并对每条响应断言 `answer == (noul >= 0.5)`。

### T-2 未知 `type` 被**静默强制转换为 `score`**

提交 `"type": "ranking"` → 返回 `"type": "score"` 与 2 级 legend，**不报错**。
→ 一个本想做分类的 `choice` 若拼错，会返回一个被朴素 harness 记成分类的 **score 信封**。
**强制规则**：**对每条响应断言「返回的 `type` == 请求的 `type`」**，不等则丢弃该条并计入错误率。

### T-3 `score` 的**方向由 criteria 书写顺序决定**

`score = Σ(index × probability)`（R12 精确验证两次）。legend 以 **0 起**回显**书写顺序**。
→ **一个按降序书写的 criteria 映射会静默地把每一个 score 反号。**
**强制规则**：**随每条响应存储返回的 `legend`**，并断言它与预期顺序一致；顺序不符即整批作废。

**附带**：`score` 与 `answer` **可以不一致**——`answer` 是 argmax，`score` 是均值。R12 实测返回 `score 2.0258`（≈level 2）同时 `answer` = level 4。→ 两者都要存储，且**不得**互相替代。

---

## 3. 已确认的接口事实（这些在 mock 下依然成立，因此现在就可写入协议）

### 3.1 预算与包线

| 事实 | 实测值 | 行为 |
|---|---|---|
| `state` 上限 | **16,000 字符** | **截断而非拒绝**（`truncated:true` + `egress.stateChars:16000`）——**且在包线内静默发生** |
| `questions` 上限 | **4,000 字符** | **拒绝而非截断**，且**重试无法挽救** |
| `jev_rank` 批量上限 | `N_max ≈ floor(3999 / (126 + len(criterion)))` | 4 点精确验证；文档边界 `L=69→20`、`L=400→7`、`L=1,000→3` |
| 单次调用总预算 | **40,000 ms** | 且**一次逻辑调用最多三次线上尝试**（同一 state 可能被重复发送）→ 影响墙钟与速率上限估算 |
| 选项数 | **25 选项被接受**，返回完整 25 路分布（和为 1.0000） | **未发现选项上限**；协议出于设计选择封顶 20，而非被迫 |
| `egress` 块 | `{truncated, stateChars, questionsChars, redactedFields, redactedValues, redactionRules, redactions}` | 三个工具都有 |

**⚠️ 截断的隐藏危险（文档明载）**：候选列表过长时**在 `state` 内部被截断**，而**每个候选仍返回一个描述该片段的分数** → **排名看起来是完整的，实际只评判了部分输入。**

### 3.2 provider 前置校验（与 provider 无关，因此现在就有效）

| 输入 | 结果 |
|---|---|
| `choice` 声明 0 或 1 个 criteria | **拒绝** |
| `noul` instructions 为空 | **拒绝** |
| `questions` 为空映射 | **拒绝** |
| **`jev_check` 空 claim + 空 evidence** | **接受**，返回 `"verdict":"conflicted"` → **check 完全不校验输入** |
| 空 state `""` | **接受**，返回答案 |
| `jev_rank` 0 个候选 | **接受**，返回退化信封（无 warning/usage/egress，`model` 为空串） |
| 未知 `type` | **接受并静默转成 `score`** |

### 3.3 `check` 的判定词表：**工具描述是错的**

- **插件源码实际词表**：`['supported','contradicted','conflicted','insufficient','undecided']` —— **没有 `unknown`**，尽管工具描述里列了它。
- **插件自身的两次改写**：`supported` 但无 sufficiency 答案 → `insufficient`；`insufficient` 但其 sufficiency 答案 ≥ 阈值 → `undecided`。
- **优先级**：`conflicted > insufficient > supported/contradicted > undecided`。
- 阈值被 R12 括出区间：support ∈ (0.5714, 0.7021]、contradiction ∈ (0.6245, 0.8103]、sufficiency ∈ (0.4108, 0.5044]。
→ **这是插件逻辑而非模型输出，所以它是真实的，将同样作用于 live 运行**；但喂给它的概率是合成的，故**观测到的判定结果本身毫无意义**。

### 3.4 其他两条

- **选项键名看似凭据会触发脱敏**：`api_key`、`auth_token`、`client_secret`、`password` 四个键全部触发 `redactionRules:["key-name"]`。**测量仪器内部发生脱敏事件**。→ 协议须避免使用这类键名。
- **mock 的 `model` 字段不可作为标记**：文档说 mock 报告 `mock/jev-synthetic`，但实际 62 条全部报告 `"model":"jev-latest"`，**与 live 无法区分**。

---

## 4. 对成本模型的修订（**推翻 R3 的 Jev 成本列**）

R12 查明两条决定性事实：

1. **TypeSafe 路由根本不报告成本**：官方文档明确 **`costUsd: 0` 意为「未报告」，不是「免费」**。→ **从零值构建的成本表是虚构。**
2. **只有 OpenRouter 路由填充 `costUsd`**，代价是**另一个第三方**接收 state（不同的留存与日志策略），且模型 id 受限（不接受 `typesafe/jev-latest`，须 `tev-*` 或 `typesafe/jev-1.13`）。

**修订后的 Jev 成本口径**（按优先级）：
- **首选**：走 OpenRouter 路由，**直接读 `usage.costUsd`**（真实计量）。
- **次选**：按公开定价 $0.042/1M 输入 **自行计价**，但**前提是能拿到 token 数**——而 TypeSafe 路由连 token 数是否报告都未确认。
- **禁止**：把 `costUsd: 0` 解释为免费。

→ **R3 中「Jev 单次 $0.000063」这一数字，其前提（token 数可得）已被 R12 动摇。** R3 的**结论方向**（钱不是约束、成本优势随 horizon 消失）仍然成立，因为它主要依赖于 LLM 侧的可验证定价；但 **Jev 那一列必须标记为「待 live 实测」。**

---

## 5. 延迟：**本次会话无法得出任何延迟预算**

R12 的方法学自评非常诚实：以 `pwsh` 时间戳包夹工具调用块，得到

| 区间 | 载荷 | 墙钟 |
|---|---|---|
| S1→S2 | **1** 次 `jev_ask` | **4.441 s** |
| S2→S3 | **0** 次（空对照） | **4.683 s** |
| S4→S5 | **5** 次并行 `jev_ask` | **5.833 s** |

→ **区间长度在 0、1、5 次调用之间基本恒定，空对照甚至更长** → 该方法测的是 **agent/harness 回合开销，不是 provider 时间**。
**强制规则**：**延迟只从 provider 字段读取**（`latencyMs`、`usage`），**永不**从工具调用外层墙钟读取；并把 40,000 ms 上限与最多三次线上尝试**作为文档事实声明，而非实测**。

→ 结合 R11 的发现（并行工具调用共享同一结果时间戳），**LLM 臂的单次延迟与会话记录中的 Jev 延迟均不可得**。这是 R5 §4.4 第 14 条的加强版。

---

## 6. **激活配方（含一个会静默留在 mock 的陷阱）**

### 6.1 陷阱（R12 从插件 README 查得，最高价值）

> **DSH 会剥除它派生的任何服务中名字含 `KEY`、`PASSWORD`、`SECRET`、`TOKEN` 的环境变量**，随后合并自己的凭据映射。

→ **在 shell 里 `export TYPESAFE_API_KEY=...` 永远不会到达插件，且插件会静默留在 mock、不报任何错。**
→ **凭据必须通过 DSH 的凭据服务登记**（ref `TYPESAFE_API_KEY`），不能靠 shell。

### 6.2 建议的改动（**未执行**——出境决定属人类）

改**profile 补丁**而非 `node_modules` 内的副本（后者会被包更新覆盖）：

`C:\Users\zzhdz\.dsh\profiles\web\cordis.patch.yml` 已有 `- id: jev` / `disabled: false`，追加：

```yaml
- id: jev
  disabled: false
  config:
    provider: live              # 原为 mock
    apiKeyRef: TYPESAFE_API_KEY
```

撤回 = 删除 `provider: live`（或改回 `mock`）。`provider` 每次调用时读取，故运行中加键即生效。配置值拼错会在加载时报错并指名，**不会静默改变隐私姿态**。

**唯一可靠的激活证据**：启动日志出现
```
[jevcore] provider=live  endpoint=https://api.typesafe.ai  egress=ON
```

### 6.3 出境后果（按功能）

| 功能 | 默认 | 出境内容 | 上限 |
|---|---|---|---|
| `jev_ask` | 被调用时运行 | 模型传入的参数（脱敏后） | state ≤16,000c / questions ≤4,000c |
| `jev_rank` | 被调用时运行 | query + **每一个候选** | 同上 |
| `jev_check` | 被调用时运行 | claim 与其 evidence | 同上 |
| `gate:safety` | **关闭（须显式开启）** | 工具名、参数、**工作区根路径** | state ≤8,000c / questions ≤2,000c |
| `gate:context` | **关闭（须显式开启）** | agent 刚收到的大段工具结果 | state ≤6,000c / questions ≤2,000c |

**关键区别**：两个 gate **开启后会对每一次匹配的工具调用触发**，而非只在模型主动调用 Jev 时触发 → **开启 gate 是比开启 provider 严格更大的决定**，这正是它们默认关闭的原因。
**暴露面**：本协议下出境的是**任务语料本身**——每次调用都上传完整任务 state。

---

## 7. 两个**决定性判别器**（每次运行首尾都要跑）

| # | 探针 | mock 实测 | live 必须 |
|---|---|---|---|
| **A** | 用三种说法陈述同一主张的 state + 声明 boundary | `noul = 0.0317` | **`noul` ≥ 0.9** |
| **B** | 边界敏感性：同 state、同 question id、同 instructions，声明 vs 不声明边界 | 差值**恰好 0.0000** | **非零差值** |

任一不通过 → **凭据未生效，运行仍在 mock 上**，无论其他字段显示什么。
**另需对每条响应断言**：`provider == "live"`、`warning` **缺失**、`latencyMs > 0`、`inputTokens > 0`、choice/score 的 `confidence != 0.5`。

**⚠️ 反向陷阱**：**不能靠「没有 warning」来判断是否 live**——R12 实测 `jev_rank` 传空候选时返回的完整响应体**没有 warning、没有 usage、没有 egress**，比正常响应「更干净」。**判别一律用 `provider == "mock"`。**

---

## 8. mock 的「看起来像真的」风险（务必写进论文的动机）

R12 用完整 14 项校准电池在 mock 上跑出了这样一张表：

| P(true) 分箱 | 项数 | 观测正确率 |
|---|---|---|
| 0.0–0.2 | 3 | 0.67 |
| 0.2–0.4 | 2 | 0.00 |
| 0.4–0.6 | 5 | 0.50 |
| 0.6–0.8 | 2 | 0.50 |
| 0.8–1.0 | 2 | 0.00 |

二值项阈值 0.5 → **5/10 = 随机**；**Brier 0.359，比常数 0.5 的 0.25 还差**。
→ **它不是一个「看起来没用」的评估器，而是一个「看起来平庸但真实」的评估器**，有合理的置信度分布，**在结果表里不会读作「坏了」**。
→ **这正是本文最有说服力的方法论论点**：**一个没有判断能力的判定器，可以产生完全可信的结果表。** 建议作为论文动机段的一部分，并作为「为什么必须内建判别器断言」的论据。

---

## 9. 修订后的样本量要求（三方独立结论一致）

R12（≥500 二值项，ECE ±0.05 需 ≥1,000）、R13（准确率 ±0.05 需 385；可靠性 ≥500；比较两判定器 ECE ≥1,000）、R14（horizon 斜率 300）**三方独立收敛**。

**最终口径**：
- **校准/ECE：≥1,000 二值项**，且**只有真值明确的二值项可进箱**；共享 state 的重复测量**不独立**，会降低有效 n。
- **准确率单判定器 ±0.05：≈385**。
- **两判定器准确率差 0.10、80% 功效：≈390/臂**。
- **horizon 斜率：300**（R14 的配对设计）。
→ R5 §3 冲突 2 的裁决不变，但门槛提高为 **1000 主电池**。

---

## 10. 新增强制规则汇总（并入 R5 §4）

1. 记录 **`noul`** 作为 P(true)，**永不记录 `probability`**；断言 `answer == (noul >= 0.5)`。
2. **断言返回 `type` == 请求 `type`**，不等即丢弃并计入错误率。
3. **存储返回的 `legend` 并断言顺序**；不匹配即整批作废。
4. 断言 `score == Σ(index × probability)`（廉价，可连续校验）。
5. 每条响应检查 `truncated: true` **方可入库**；`egress` 块与 `provider` 一并存储。
6. **判别 live/mock 一律用 `provider == "mock"`**，不靠 warning 的有无。
7. **每次运行首尾各跑一次判别器 A/B**，以证明 provider 中途未变。
8. 凭据**必须经 DSH 凭据服务**登记；只认启动行 `provider=live egress=ON`。
9. 延迟**只从 provider 字段读取**；声明 40,000 ms 上限与最多三次尝试为文档事实。
10. `choice` ≥2 criteria、instructions 非空；`check` 输入**须上游校验**（它自己不校验）。
11. `rank` 批量按 `N_max ≈ floor(3999/(126+len(criterion)))` **在协议构建期**定尺寸；超限**重试无用**。
12. 选项键名**不得形似凭据**（触发脱敏）。
13. **`costUsd: 0` = 未报告 ≠ 免费**；优先走 OpenRouter 路线以取得真实成本。
14. 固定**一个** criteria 书写顺序（方向即语义）；`answer` 与 `score` 都存，互不替代。

---

## 11. 交核对单元的新增项

- [ ] R3 的 Jev 成本列在「token 数是否可得」未定之前应如何表述（现在是「待 live 实测」是否足够诚实）。
- [ ] 若走 OpenRouter 路线，**另一个第三方**接收 state 的合规口径如何写入论文的伦理/出境声明。
- [ ] 判别器 A/B 的阈值（≥0.9 / 非零）**是否会被审稿人视为事后挑选**；是否需要预注册其确切形式与理由。
- [ ] 「mock 产生可信结果表」这一发现，是否应升级为论文的一个**独立贡献**（对 agent 评测方法论的警示），而不仅是内部风险控制。
