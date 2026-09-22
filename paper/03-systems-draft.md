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
- **最危险的是它的结果表**：14 项校准电池产出合理的置信度分布，但 **Brier 0.359**，劣于常数预测器的 0.25。

**且 mock 的自报字段会骗过检测**：`model` 字段报告 `"jev-latest"`（与 live 无法区分），而**一次短路调用返回的响应完全没有 `warning` 字段** → **不能靠 warning 缺失判断 live**，只能靠 `provider == "mock"`。

### 缺陷 2：`laya_plan`（**接入层**）已损坏

返回 `tool "laya_plan" returned invalid output: "value.fits" must be a boolean`。
→ **Laya 唯一可用的预检手段失效**；替代方案是自算 tokenizer（§4.9）。
**归属**：`laya_plan` 是 **`laya-mcp` 包装器**的工具，**不是 Convai 引擎的接口**。

### 缺陷 3：规划器不跑 tokenizer（**接入层**）

`planning.py` 用 `chars / 4.0 × 1.15` 估算 token，即**隐含 3.478 chars/token**；而该编码器在英文散文上实测 **≈6.33 chars/token** → **规划器高估 token 数约 1.8 倍**，且每次响应的 `exact` 都是 `false`。
**归属**：`planning.py` 属于 **`laya-mcp` 包装器**；引擎自带的 tokenizer **并未**被该规划器调用（本文的预算一律自算，见 §4.9）。

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
