# R4 — 阻塞项登记册（P0/P1）与激活配方

> 作者：主控
> 状态：**P0-1 需人类决策**（涉及数据出境授权）。
> 规则：任一 P0 未解除前，相关章节**不得撰写**；不得用模拟数据顶替。

---

## P0-1（最高优先级）：Jev 当前为 **mock provider**，全部 Jev 测量无效

### 事实（主控亲自验证，非推断）

**配置源**：`C:\Users\zzhdz\.dsh\profiles\web\node_modules\jevcore-dsh\cordis.patch.yml` 第 8 行附近

```yaml
config:
  # Offline by default. With `provider: mock` this plugin makes no network
  # call at all; every answer is synthetic.
  provider: mock
  gates:
    safety:
      enabled: false
      onUndecided: ask
    context:
      enabled: false
```

**实测调用返回（主控发起，原文摘录）**：

```json
{ "provider": "mock", "model": "jev-latest", "latencyMs": 0,
  "answers": [ { "question": "supports", "type": "noul", "answer": "true",
                 "band": "uncertain", "noul": 0.6301 } ],
  "usage": { "inputTokens": 0, "outputTokens": 0, "costUsd": 0 },
  "warning": "These answers are SYNTHETIC. The mock provider derived them from a hash of the input;
              they carry no judgment. Set provider to \"live\" or \"openrouter\" with a credential for real answers." }
```

### 后果

| 受影响项 | 状态 |
|---|---|
| R12 的全部 Jev 实测（概率、边界敏感性、选项数退化、校准、check 判定、延迟） | **全部无效**：是输入哈希的确定性函数 |
| 成本章节的 Jev 列 | **阻塞**（虽然有第三方定价 $0.042/1M，但延迟与行为无法获得） |
| A2 臂（LLM+Jev） | **阻塞** |
| A4 自适应升级臂的 Jev 分支 | **阻塞** |
| 「Jev 在长 state 下单价反超 LLM」这一 R3 结论 | 定价部分仍成立（第三方一手），**但延迟与行为部分阻塞** |

**注意**：`jev_check` 在证据几乎逐字支持主张的情况下返回 `insufficient` —— 这不是 Jev 的行为缺陷，而是**哈希取值的产物**。任何基于它的论断都必须撤回。

### 激活所需的**唯一**改动（供人类决策，主控不擅自执行）

```yaml
provider: live          # 或 openrouter
```

**出境后果（来自同文件注释，须逐条确认）**：
- `provider: live` → **每次调用都把 state 文本发送给 TypeSafe（第三方）**。
- `gates.safety.enabled: true` → 判定型工具调用内容出境。
- `gates.context.enabled: true` → **读取工具结果**的内容出境。
- 两个 gate 目前均为 `false`；若只切 `provider: live` 而保持 gate 关闭，则只有显式发起的 `jev_ask/check/rank` 的 state 出境，工具调用与工具结果不出境。

**人类的三个选项**：
1. **提供凭据并启用 live** → 解除 P0-1，A2/A4 可执行，成本表可完成。
2. **保持 mock** → 论文结构需改为**两判定器**（LLM + Laya），Jev 降为「接口契约描述 + 第三方定价引用」，并在局限性中说明；**A2 臂删除**。
3. **先用 mock 验证管线，再启用 live 跑正式数据** → 推荐路径（见下）。

### 推荐执行顺序

1. **现在**：用 mock 跑通整条管线（harness、快照、回放、评分、统计），因为 mock 的延迟为 0、成本为 0，是**免费的端到端演练**。
2. 在 mock 下完成：序列化器冻结、问题库、哈希、`laya_plan` 替代方案、评分器实现、离线回放管线。
3. **凭据就绪后**：切 live，先跑**冒烟验证**（第 5 节），确认返回里 `provider != "mock"` 且 `latencyMs > 0`，再跑正式批次。
4. 论文中**必须**声明：所有 Jev 数据在 `<日期>` 之后于 `provider: live` 下采集，并附配置哈希。

---

## P0-2：`laya_plan` 已损坏，Laya 唯一的**预检**手段失效

**事实**（R11 实测）：调用 `laya_plan` 返回
```
tool "laya_plan" returned invalid output: "value.fits" must be a boolean
```

**后果**：Laya 对超长 state 的**静默尾部截断**无法在调用前预知，只能事后从 `budget_summary`/`truncated`/`warnings` 反推——而 R2 已记录这些字段**未必可靠地出现**。R15 的 `integrity(t)`/`blind_frac(t)`/`t_trunc` 三条曲线因此失去最直接的输入。

**替代方案（必须选一个，并写进协议）**：
1. **自行计数**：用 Laya 自己的 tokenizer（`<SNAP>\tokenizer\tokenizer.json`，本地已有）在调用前计数，与 `W ∈ {512, 1024}` 比较。**推荐**——不依赖损坏的工具，且可复现。
2. **事后反推**：从响应字段反推是否截断；因字段未必出现，**不可作为唯一手段**。
3. **主动探针**：在固定间隔上做「完整 state vs 尾部删除 20%」的成对调用，直接测出截断是否发生（R15 §1.4 已设计）。**作为交叉验证保留**。

→ 建议 1+3 组合：1 作主口径，3 作验证。

---

## P0-3：Jev 的**延迟与成本当前无法从会话记录取数**

**事实（R11）**：
- 会话记录（`.dsh/sessions/<encoded-cwd>/<sessionId>/*.jsonl.zstd`，拼接的 zstd 帧）**完整包含**：每步 `usage{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalTokens}`、毫秒时间戳、模型 id、工具参数**与工具结果原文**。
- **没有任何货币成本字段**（token-meter 只按启发式计价 token，不产生金额）。
- **并行工具调用共享同一个结果时间戳**：R11 一次批量发 5 个调用，全部落在 **3 ms** 内 → 记录只能给出**批量墙钟**，不能给出**单次调用延迟**。

**后果**：LLM 臂的单次判定延迟**无法**从会话记录获得，必须由外部 harness 自行计时（单发、不并行，或自行打点）。Laya 因为**自报 `latency_ms`** 而幸免。

**协议要求**：
- 所有需要单次延迟的测量一律**串行发起**并自行计时；
- 报告延迟时注明「自报」还是「外部计时」；
- `maxParallelToolCalls=20` 的能力**不得**用于延迟测量批次。

---

## P0-4：无法用 `laya_ask`（主控路径）完成任何实测——sidecar 未随会话启动

**事实**：主控首次调用 `laya_ask` 返回
```
cannot reach the sidecar at http://127.0.0.1:8787 (fetch failed). Start it with `laya-mcp serve`, then retry.
```
R13 自行启动后调用成功（`/health` 显示 `device: cuda`、`max_len 1024`、`head_max_len 512`）。

**后果与要求**：
- sidecar **不会随会话自动启动**，且上游 HANDOFF 记录它会**静默退出**。
- 正式运行时必须有**健康检查 + 自动重启**，并把**重启次数与冷启动次数**记入日志（冷启动 25–35 s，本机首次调用实测 **389.9 ms**，R11 另测 **4935.863 ms** 冷启动 → **必须区分冷/热**，否则延迟统计被污染）。

---

## 第 5 节：切换 live 之后的一次性冒烟验证（一页清单）

在跑任何正式批次前，逐项确认：

- [ ] 返回中 `provider` 字段 **≠ `"mock"`**
- [ ] `latencyMs` **> 0**，且重复调用 10 次给出**非恒定**值
- [ ] 响应中**不含** `SYNTHETIC` 警告
- [ ] 同一 state + 同一问题的返回**不**随输入哈希的微小改动而随机翻转（用一对语义等价的改写验证）
- [ ] `usage.inputTokens` **> 0**，且与 state 字符数量正相关
- [ ] 记录当次配置文件的**哈希**与采集**日期/时段**（峰谷价差 2×）
- [ ] `gates` 的实际取值被记录（决定出境范围）
- [ ] 若 `costUsd` 仍为 0，则以**第三方定价 × 实测 token 数**自行计价，并在论文中标注为「按公开价目表估算」

---

## 相关（非阻塞）修正：需回填 R2

- **deepseek-flash 支持 `logprobs`/`top_logprobs`**（R16 从官方 Chat Completions 参考核实）→ LLM 臂可获得**内部对数概率**，而不只是口头概率。这**显著加强**「公平的 LLM 判定器」这一梯级，应纳入协议。
- **思考模式下 `temperature` 无效，且 `top_p` 下限为 0.95**（同上）→ k 次自洽采样臂**不能在思考模式下**按「温度 0 vs 0.7」实现，必须走非思考模式。
- **`tool_choice: required` 在思考模式下返回 400**；关闭思考模式的取值是 **`none`**（不是 `"off"`）。
- **`usage` 直接返回缓存命中/未命中与推理 token 数** → 成本可直接记账，R3 的缓存命中率假设**可实测**而非假设。
