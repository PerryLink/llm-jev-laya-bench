# §3 被测系统与仪器缺陷

> 本节的作用是让读者能判断**每个后续数字是在什么仪器上取得的**——因为本文的核心发现正是「自报字段不可信」，所以仪器必须被完整交代。

---

## 3.1 三个被测系统

| 维度 | **LLM**（DeepSeek-V4.1-Flash） | **Jev**（TypeSafe） | **Laya**（Convai） |
|---|---|---|---|
| 类型 | 自回归**生成器** | 状态条件**判别器** | 状态条件**判别器** |
| 能否采取行动 | **能** | **不能** | **不能** |
| 输入 | 任意上下文 | 一个 `state` + 一组声明式问题 | 同左，**窗口受限** |
| 输出 | 自由文本 / 工具调用 | 标签 + 概率 | 标签 + 概率 + `confidence` |
| 本项目调用方式 | 直连 `POST /chat/completions` | DSH 插件（openrouter 路线） | HTTP sidecar（Path A） |
| **接入层**（合成自报字段者） | provider 的 API 响应字段 | **DSH 插件**（本项目所用） | **`laya-mcp` 包装器**（第三方，见下） |

**关键约束**：**Jev 与 Laya 不能执行任务**，因此本文全部对比都是**判断层对比**——生成器恒定，只有判断层变化（§4.1）。

### 3.1.1 归属声明：被测的是「引擎 + 接入层」，自报字段大多属于**接入层**

**这一条决定本文结果 B 的适用范围，必须写在最前面。**

| 组件 | 版本 | 作者 / 出处 | 本文所测的自报字段归属 |
|---|---|---|---|
| **Laya 引擎** | `laya 0.3.4` | **Convai Innovations**（`convaiinnovations/laya`）| 模型权重与前向；`noul` / `choices` / `probabilities` 等**张量派生输出** |
| **`laya-mcp` 包装器** | `0.1.0` | **PerryLink**（`github.com/PerryLink/laya-mcp`，**第三方**，非 Convai）| **`fits`、`truncated`、`exact`、`laya_plan`、`planning.py::_CHARS_PER_TOKEN`、`--max-len`/`--head-max-len` 的预算算术** |
| **本项目 HTTP sidecar** | `0.2.1` | 第三方包装器的服务化入口（**本项目钉定的修订**）| 入口与端口行为、语言路由字段 |
| **Jev 引擎** | `typesafe/jev-1.13` | TypeSafe | 判定原语输出 |
| **DSH Jev 插件** | 本项目所用 | 本项目运行环境 | **`provider` / `model` / `warning` / `costUsd` 等接入字段** |

**因此本文的措辞必须精确**：
- **不得**写「Convai 的 Laya 谎报截断」。截断标志与预算算术**由第三方 `laya-mcp` 包装器合成**，本文从未测过 Convai 引擎自身的截断协议（若存在）。
- 同理，Jev 侧的 `provider` / `warning` 字段由 **DSH 插件**产生，测的是该接入层。
- **本文的发现应表述为**：**「判定层接入路径的自报字段不可信」**——这是一个关于**接入层**的结论，其可迁移性在于「这类字段普遍由包装器合成」，而**不是**对任一引擎质量的主张。
- 这一区分本身是本文方法论的一部分：把**引擎**与**接入层**混为一谈，正是 §4 所述「把测量装置的属性当成被测对象的属性」的一种形式。

---

## 3.2 版本与采集口径

| 组件 | 标识 |
|---|---|
| **LLM** | `deepseek-flash`（= DeepSeek-V4.1-Flash）；`thinking: disabled`（除非注明）；`reasoning_effort` 逐实验记录 |
| **Jev** | **`typesafe/jev-1.13`**（本机运行时解析为 `typesafe/jev-1.13-20260917`；厂商文档记作 `jev-1.13.0`）· 路线 **openrouter** |
| **Laya** | 引擎 `laya 0.3.4`（**Convai Innovations**）；接入层 **`laya-mcp 0.1.0`（PerryLink，第三方）**；本项目 sidecar **0.2.1**；checkpoint `convaiinnovations/laya`（english / multilingual / typed-decisions）|
| **Laya 启动配置** | `--model english --also multilingual --also typed-decisions --device cuda --max-len 1024 --head-max-len 512` |
| **设备** | RTX 5060 Laptop（8,151 MiB，sm_120）· Intel Ultra 7 255HX · torch 2.11.0+cu128 |

**⚠️ 窗口同时取决于启动配置与所查询的 checkpoint**（§4.8）：english 在该三-checkpoint loadout 下为 **512 token**，单独载入时为 **1024**；而 multilingual 与 typed-decisions 在同机同 loadout 下实测为 **1024**。
→ **任何 Laya 数字都必须连同「loadout × checkpoint」一起报告。**

---

## 3.3 五个已确认的仪器缺陷

本节只列**事实**，其后果与协议对策见 §6。**每条的「归属」一栏标明该字段由谁合成**（见 §3.1.1）。

### 缺陷 1：Jev 的默认 provider 是**离线 mock**，且它看起来完全正常

- 配置为 `provider: mock` 时**不发任何网络请求**，答案 = `FNV-1a(questionId + "\0" + JSON.stringify(state))`；
- **`instructions`、`criteria`、选项描述、`boundary` 全都不参与哈希** → **把问题改写成相反的意思，数字不动**；
- 实测：对**逐字支持主张**的证据返回 `undecided`；对**空 claim + 空 evidence** 返回 `conflicted`；
- **最危险的是它的结果表**：一次 **14 项**校准电池产出了合理的置信度分布，而其中**有二元真值的 10 项**上 **Brier = 0.359**——**劣于常数 0.5 预测器的 0.25**。
  **⚠️ 两个 n 必须分清（第七轮更正）**：**电池是 14 项，Brier 的 n 是 10**（另 4 项没有二元真值，不计入）。初稿写作「14 项校准电池……但 Brier 0.359」，读起来像是 14 项上的 Brier——**这是把「电池规模」与「统计量的 n」混为一谈**，正是本项目命名的错误类别（**写法的缺陷冒充关于对象的结论**）。两个数字各自都是对的，**错的只是它们的挂靠**；也正因如此，它躲过了五轮审计。出处 `recon\R12-jev-probe.md:177` 与 `:187`。

**且 mock 的自报字段会骗过检测**：`model` 字段报告 `"jev-latest"`（与 live 无法区分），而**一次短路调用返回的响应完全没有 `warning` 字段** → **不能靠 warning 缺失判断 live**，只能靠 `provider == "mock"`。

### 缺陷 2：`laya_plan`（**接入层**）已损坏

返回 `tool "laya_plan" returned invalid output: "value.fits" must be a boolean`。
→ **Laya 唯一可用的预检手段失效**；替代方案是自算 tokenizer（§4.9）。

**⚠️ 归属收窄（2026-09-23）**：该工具是 **`laya-mcp` 包装器**的工具、**不是 Convai 引擎的接口** —— 这一半成立。但对该包装器中 `fits` 的**每一处赋值**做审计后发现：它**不可能输出非布尔值** —— `planning.py` 把该字段声明为 `fits: bool = True`，**唯一的赋值是 `fits=not any_truncation`**，`to_dict()` 原样传出；合成 plan 亦确认 `type(to_dict()["fits"]) is bool`。而 `value.fits` 是 **JSON-Schema 风格路径，该包内不存在任何 `value` 键**。

→ **故此处观察到的是「调用失败」，而违规由校验结果的那一侧抛出**（客户端）。**这是又一处对象错配** —— 一个正确的观察挂在了并未产生它的组件上。无论归属如何，该包装器应当**以测试持有 `fits` 的布尔契约**，此前缺少该测试，**现已补上**（`tests/preflight_contract.py`，覆盖三种判定下的类型）。**✅ 已修（2026-09-23，`laya-mcp` 0.2.3）。**

### 缺陷 3：规划器不跑 tokenizer，且估算误差在两种方向上均超安全系数（**接入层**）

`planning.py` 用 `chars / 4.0 × 1.15` 估算 token，即**隐含 3.478 chars/token**，而每次响应的 `exact` 都是 `false` —— **引擎自带的 tokenizer 从未被该规划器调用**。

**该估算的误差随输入类型变化，而两种方向都超出 1.15 的安全系数**（用各 checkpoint 自带的 tokenizer 实测）：

| 状态文本类型 | 实测 chars/token | 规划器方向 |
|---|---|---|
| 英文散文（`english`） | **4.31** | 高估 **1.239 倍**（安全） |
| 英文散文（`multilingual`） | 4.03 | 高估 1.158 倍 |
| 英文 markdown | 3.83 | 高估 1.101 倍 |
| Python 源码 | 3.24 | **低估 1.075 倍** |
| **JSON 产物** | **2.40** | **低估 1.450 倍** |
| **中文**（`multilingual` tokenizer） | 1.65 | **低估 2.105 倍** |
| **CSV 表**（构造样本 †） | **1.62** | **低估 2.150 倍** |
| 服务器日志 + traceback（构造样本 †） | 2.20 | **低估 1.564 倍** |

> 前三行与 CSV 行、中文行出自 `results\P31-token-density.json`；**日志行**出自独立审计 `planner-token-audit/measurements.json`（S14），其构造样本本仓库未复刻，故沿用该报告的读数。† 标注的两类输入在树内无逐字文件可测，故按真实结果形状构造 —— **列表本身即结论的一部分：越接近该模块 docstring 自陈的服务对象（「合同、日志、邮件线索」与序列化 JSON），估算越偏低。**

→ **对结构化与多语言状态估算偏低** ⇒ 规划器报 `fits` 而状态实际已被截断，**即 `laya_plan` 存在所要防的那件事**；**1.15 的安全系数不足以覆盖 1.08–2.15 倍的缺口。**

**⚠️ 一处必须同时给出的更正**（**撤回 RETRACTED** 下列两个数字，并改挂其正确对象）：本节初稿曾写「该编码器在英文散文上实测 ≈6.33 chars/token → 高估约 1.8 倍」。**两个数字都是真的，但挂在错误的对象上**：那个 6.33（重测 **6.78**，**撤回 RETRACTED**）是**本项目的截断扫描状态**的密度，而该状态是 **`DECOY + FILLER×45 + CORRECTION`，即同一句 filler 重复 45 遍** —— 它**不是英文散文，而是本项目里对规划器最有利的输入**：同一句重复 1 次为 5.550 chars/token、重复 100 次为 6.920，而真实英文散文只有 **4.31**。**在该测试状态上高估为 1.949 倍**（初稿印 1.8 倍，**撤回 RETRACTED**；该项经重测修正，因初稿所据的 token 列偏高约 7–8%）；**对真实英文散文只有 1.239 倍。** **本文因此既写错了对象，也低估了真正危险的方向。** 见 `results\ERRATA.md` 与 `results\P31-token-density.json`。

**归属**：`planning.py` 属于 **`laya-mcp` 包装器**；引擎自带的 tokenizer **并未**被该规划器调用（本文的预算一律自算，见 §4.9）。

**✅ 已修（2026-09-23，`laya-mcp` 0.2.3）**：规划器现在从每个已加载的 `Agent` 取得其 tokenizer，并在每次预检与每次 `ask` 时传入 —— 状态预算**从估算变为真实计数**（`exact: true`）；sidecar 分支改为调用服务端 `/plan`（模型与 tokenizer 都在那一侧），从而删去了两条可能对同一问题给出不同答案的路径；`_looks_non_latin` 改为**跨全文采样并取最密窗口**（消除前缀依赖导致的非单调），且**识别 ASCII 转义的 CJK**（`json.dumps` 的 `ensure_ascii=True` 默认值曾让纯中文内容按拉丁比值计算）。**两处旧实现均使预算偏低 —— 正是 `laya_plan` 所要防的静默截断。**

**⚠️ 限定**：修复的正确性已由 **24 项纯逻辑测试**（`tests/preflight_contract.py`，无需模型）与既有 **94 项** smoke 测试验证，覆盖「tokenizer 被传入后 `exact` 为真」「两种 tokenizer 协议均被接受」「不可用对象回退且告警」「非单调消失」「转义 CJK 被识别」。**但「真实运行下 `exact` 变为 true」尚未验证** —— 那需要加载模型，故本文只主张**计数路径正确且可达**，不主张生产环境下 `exact` 现为 true。

### 缺陷 4：截断钳位逐 checkpoint 不同，而标志不随之缩放（**接入层 + checkpoint 配置**）

| checkpoint | 同机实测钳位 |
|---|---|
| english | **512 token** |
| multilingual | **1024 token** |
| typed-decisions | **1024 token** |

而 **`truncated` 在三个 checkpoint 上都于 3,193 字符才首次触发** → 标志由一个**未随预算缩放的字符估计**驱动（后果见 §6.2）。
**归属**：`truncated` 与预算算术由 **`laya-mcp` 包装器**合成；钳位本身由 `--max-len` / `--head-max-len` 与各 checkpoint 的配置共同决定。

### 缺陷 5：`probability` 是 P(所选选项)，不是 P(true)（**接入层**）

同一响应中 `band` 朝向 true、`probability` 朝向所选，**方向相反**（后果见 §6.4）。
**同一陷阱在 LLM 一侧独立出现**：其 `prob` 是**所答标签的置信度**。
**归属**：这两个字段分别由 **`laya-mcp` 包装器**与 **LLM provider 的响应**给出；两处**独立**出现同一歧义，正是 §6.4 把它当作协议级问题的理由。

### 缺陷 6：`noul` 的答案由**标签词**决定，而不由状态决定（**引擎侧**；本条为勘误补记）

`render_options` 把 `noul` 的两个选项**硬编码**为 `false:` / `true:`。上游 issue [#156](https://github.com/NandhaKishorM/laya/issues/156) 报告：在 english checkpoint 上，**`noul` 对正例与负例都返回负标签**，且 `confidence` 饱和至 1.0000；把标签换成 `A`/`B` 后同一判断恢复正常。**独立复现者三人**（报告者、MrJev、AlKor13）；**维护者于 2026-09-22 确认它为当时最重要的未修复缺陷**，并指出成因**未定**（疑为训练侧对布尔标签词的先验，而非 `render_options` 可修）。

**⚠️ 状态更新（2026-09-25）**：该 issue **已于 2026-09-23 关闭（completed）**——即本勘误版手稿汇编之后约 9 小时。关闭前后落地两项：可选的 `labels` 覆盖（[#163](https://github.com/NandhaKishorM/laya/pull/163)，2026-09-23 合并），使标签词效应可在**不改默认值**的前提下自行测量；以及**本项目提交并合并的 [#249](https://github.com/NandhaKishorM/laya/pull/249)**，把「`noul` 的 `criteria` 用了 `true`/`false` 以外的键被**静默替换**为默认描述」改为**报错**（第三方已在 0.3.11 上验证）。**但偏置本身未修复** —— 维护者关闭时的原话是「The English-checkpoint bias itself needs a retrained checkpoint」。**故本条的现状是：偏置仍在，其可测量性与静默替换已修。** 另需注意：第三方在 0.3.20 上实测该 `labels` 覆盖在 `laya` 上有效、在 `laya-typed-decisions` 上**劣于默认值**，故这一缓解手段**随 checkpoint 而异**，不可当作通用解法。

**⚠️ 本文的测量路径未复现该饱和。** 本文 P19 校准电池**正是用 `noul`**、且 `criteria` 的键**就是 `"true"`/`"false"`**（`src\items\p19_calibration.py:144-146`），而 1100 条的 `laya_p` 落在 **0.061–0.963**、**无一个饱和值**，且对真值有区分（truth=TRUE 均值 0.781、truth=FALSE 均值 0.607，`results\P19-calibration.json`）。**因此「本文路径上 `noul` 未饱和」是实测，而非推断；两条路径（本项目 sidecar → `laya-mcp`，与直接驱动 `agent.system_one`）的差异未经对照实验，成因未定。**

**对本文结论的影响**：§7 的 `explicit_support 0.9909` **是 `noul` 上的读数**，故其有效性依赖上述路径差异；在该差异被澄清之前，**该数字应按「在本项目的接入路径与配置上测得」来读**，不得读作 english checkpoint 上 `noul` 的一般性质。

**归属**：`render_options` 的硬编码与标头打分属**引擎侧**；本条来自外部报告，**不是本文仪器所产**，故本文只记录现象与自身路径上的反证，不主张成因。

---

## 3.4 入口点：一个必须钉死的事实

**Laya 存在两个宿主，工具名决定用哪一个**：

| 入口 | 到达 | 规划器 max_len / head_max_len |
|---|---|---|
| 插件工具（`laya_ask` 等） | HTTP sidecar（:8787）| **1024 / 512** |
| MCP 工具（`mcp__laya__*`） | stdio 服务 | **512 / 192** |

同一请求、同一秒：`state_room_estimated` **917 vs 405**。
→ **不说明入口的协议在比较两种不同仪器。** 本文全部 Laya 测量使用 **HTTP sidecar**。

**并且**：该 sidecar **从不做语言检测与路由**——对每种输入（含西里尔与天城文）都报告 `routing.reason = "explicit model selection"`，**不传 `--model` 启动时亦然**。
→ **本文不得对 DSH 插件所用的 Python `Router` 作任何陈述**——那是本项目从未触达的组件。

---

## 3.5 仪器冻结（因为被测仪器是活跃开发中的工作树）

本会话期间 `worker.py` 被**改写三次**（见 `src\instrument\laya_client.py` 的自述记录：`planning.py / worker.py / server.py` 在 18:16–18:17 被改写），且**两个入口曾同时服务不同修订**。

| 机制 | 位置 | 实际状态 |
|---|---|---|
| **六个仪器哈希**（逐文件 SHA256）| `protocol\INSTRUMENT-FREEZE.json` | ⚠️ 该文件冻结于 10:18:25Z，**早于快照**（10:20:01Z），其 `worker.py` 一格原记 `6FE665BF…`——那是 18 秒后被覆写的**未提交中间修订**，在两棵树、全部结果文件中均不存在（正确值 `829EB8C3…`）。**该值已更正，并在 `_hash_corrections` 中保留被取代的原值与原因**（不改则等于把 10:18:25Z 那一刻描述错）。**关键：此格不影响任何已发表数字**——全部 28 个记录 `worker.py` 哈希的产物一律记 `829EB8C3…`，且无代码读取本文件。**另有一处自报错误**：该文件的 `sidecar_capabilities_state_budget` 记为 `512/512/512`，而 P3 实测为 english **512** / multilingual **1024** / typed-decisions **1024**——**这本身就是 Result B 的一个实例：服务自报的字段不是对它的测量** |
| **不可变快照**（13 `.py` + 2 config）| `protocol\instrument-snapshot\`（含 `PIN.json`）| ✅ **有效**：13 个哈希与字节数经独立重算**全部匹配** |
| **钉定启动器**（断言导入路径落在快照内，失败即退出）| `src\instrument\run_pinned_sidecar.py` | ✅ 实际拦住了错误修订（P16–P18 三次启动均打印通过） |
| **每条结果自带仪器记录** | `laya_client.instrument_record()` | ✅ **42 个结果文件中 39 个带溯源记录，其余 3 个全是纯派生文件**（不产生测量，故无仪器可归属）——**未解释缺口为 0**。计数由 `src\analysis\p30_inventory.py` 从目录推导（产物 `P30-evidence-inventory.json`），不再是手写数字。该记录自第五轮起哈希**固定快照**（`protocol\instrument-snapshot\`）而非活工作树。**⚠️ 仍存的真实缺口**：`deepseek_client.py`（LLM 那一臂自己的客户端）**全树无文件哈希它** |
| **漂移中止** | `laya_client.assert_instrument()` | ❌ **死代码：全仓零调用点**。论文早期版本称它「实际拦住了错误修订」，该说法**不成立**，已删除 |

**⚠️ 关于「漂移」**：本项目曾记录「漂移 NONE」。该结论**不成立**——工作树与快照现有 **3 个文件不同**（`__init__.py`、`cli.py`、`mcp_server.py`）。
**但必须同时说明其影响范围**：决定行为的四个文件（`planning.py`、`worker.py`、`capability.py`、`server.py`）在工作树与快照之间**逐字节相同**，故该漂移**不可能改变**钳位、tokenizer 或判定语义，**已发表的数字不受影响**。
**且这暴露了一个结构性盲区**：`instrument_hashes()` 的清单**不包含**那 3 个实际漂移的文件 ⇒ **可复现性清单对唯一真实发生的漂移是盲的**。

---

## 3.6 本节小结

**读者应带走的一件事**：本文比较的三条**判定层接入路径**，其**自报字段都不可信**，且**不可信的方式各不相同**。因此 §4 的方法不是「我们怎么做实验」，而是「**我们如何发现自己做错了**」——本项目**四次**同类错误，**每次都伪装成关于模型的发现**。

**⚠️ 这一结论的适用范围**（§3.1.1）：这些字段**大多由接入层合成**（Laya 侧为第三方 `laya-mcp`，Jev 侧为 DSH 插件），**不是**对 Convai 引擎或 TypeSafe 引擎自身协议的主张。本文测的是**「引擎 + 接入层」的组合**，而发现的性质是**接入层**的。
