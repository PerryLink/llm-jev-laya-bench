# P16–P18 — Laya 的窗口是**启动配置**的属性，而**不是代码修订**的属性

> 实测：2026-09-22 · **全部在钉定快照修订上**（`protocol/instrument-snapshot/`，逐文件 SHA256）
> 原始数据：`results\P16-pinned-clamp-replication.json`、`P17-clamp-attribution.json`、`P18-loadout-window-sweep.json`
> 复现：`src\instrument\p16_pinned_clamp_replication.py`、`p17_clamp_attribution.py`、`p18_loadout_window_sweep.py`

---

## 0. 这项工作的目的

目标项 (4)：**把 Laya 关键测量在快照修订上重跑**，以消除版本归属的不确定性。这个不确定性是真实的——`worker.py` 曾在一次会话内被改写三次，且**两个入口曾同时服务不同修订**（R11）。
而 Result B（「仪器自报字段不可信」）是论文最强的一节，其核心数字正是截断窗口。**若该数字不可归属到某个代码修订，整节都要打折。**

---

## 1. 过程：三次测量，两次翻转结论

### 1.1 P16：钉定修订上**没有 512 钳位**

在钉定快照上跑同一扫描：`input_tokens_padded` 一路涨到 **791 并继续增长**，**没有 512 钳位**。
→ 初步结论写成「修订有差异，pre-snapshot 测量需全部重跑」。

### 1.2 P17：**归因测试** —— 是**启动参数**，不是修订

但 P16 与 P3 的**启动方式不同**：P3 载入**三个** checkpoint（`--model english --also multilingual --also typed-decisions`），P16 只载入 **english**。
→ 这正是「把序列化器的错归咎于模型」那一类混淆。于是跑 2×2：

| | P3 参数（三 checkpoint） | P16 参数（单 checkpoint） |
|---|---|---|
| **同一钉定修订** | **钳位 512**（onset 3,082；`truncated` @3,193） | **无 512 钳位**（涨到 1024） |

**→ 同一份代码，仅因载入的 checkpoint 集合不同，窗口差 2 倍。修订不是变量。**

### 1.3 P18：**逐 loadout 扫描** + 确定性检验

| loadout | 已加载 | **长 state 钳位** |
|---|---|---|
| `--model english` | english | **1024** |
| `--model english --also multilingual` | english, multilingual | **512** |
| `--model english --also typed-decisions` | english, typed-decisions | **512** |
| `--model english --also multilingual --also typed-decisions` | 三个 | **512** |

**确定性检验**（各重启 3 次）：`english_only` → **[1024, 1024, 1024]**；`all_three` → **[512, 512, 512]**。
→ **完全确定，不是显存波动。**

---

## 2. 结论

### 2.1 对论文的直接后果

**1. Result B 成立，且现在有了版本归属。**
本项目**所有** Laya 测量都在**三 checkpoint loadout** 下取得 → **512 token 窗口与 111 字符未告警区间对它们一致适用**。P3 的数字**对该配置是正确的**，并且现在是在**钉定修订**上复现的（P17 第一行：onset 3,082、`truncated` @3,193、钳位 512 —— **与 P3 逐项吻合**）。

**2. 但窗口必须连同启动配置一起报告。**
「Laya 的窗口是 512 token」这个说法**对另一个操作者可能错 2 倍**。**任何只写「窗口 = 512」的表述都是不完整的**，必须写成「在载入 N 个 checkpoint 的 loadout 下」。
→ **这是本轮新增的协议强制项。**

**3. 一条对实践的可用结论**：**只载入 english 一个 checkpoint，可以把可用 state 窗口从 512 翻倍到 1024 token**，代价是失去多语与 typed-decisions 能力。**这是一个可操作的权衡，且有实测支撑。**

**4. 机制未隔离。** 我**不知道**为什么第二个 checkpoint 会把窗口砍半——可能是容量策略、也可能是 `--also` 处理路径的副作用。**论文只报告这一经验规律，不得声称机制。**

### 2.2 对本项目方法学的一次验证

这一轮同时**检验了钉定基础设施**：`run_pinned_sidecar` 的断言确实拦住了错误修订（P16/P17/P18 三次启动都打印了断言通过的导入路径），并允许在**不干扰你 harness 上 8787 端口**的前提下，用独立端口（8791/8792/8793/8794）跑并行 sidecar。
→ **「仪器哈希 + 钉定启动 + 漂移守卫」这套机制是可用的**，不只是写在协议里。

---

## 3. 对目标清单的更新

| # | 项 | 状态 |
|---|---|---|
| 4 | **Laya 关键测量在快照修订上重跑** | ✅ **完成**：钳位/静默窗口在钉定修订上复现；不确定性来源已从「代码修订」更正为「启动配置」 |
| 1 | 强项区制互补性 | ✅ 完成（P15）→ **两个区制均无互补，架构主张放弃** |
| 6 | 撰写论文 | ⬜ 未开始（大纲已定稿：`protocol\PAPER-OUTLINE-AND-EVIDENCE.md`） |
| — | 校准曲线（≥500 二值项） | ⬜ 未做 |
| — | 多语误路由区制 | ⬜ 未做 |
| — | LLM logprobs / 思考模式成本 | ⬜ 未做 |
| — | 提示词变体带 P1–P4 | ⬜ 未做 |
| — | horizon（D2 裁定降级为描述性） | ⬜ 未做 |

---

## 4. 限制

1. **机制未隔离**（见 §2.1-4）。只报告「第二个 checkpoint 使窗口减半」这一经验规律。
2. **单一 checkpoint 组合**：只测了 english / multilingual / typed-decisions 的 4 种组合，**未测**「不以 english 为主」的 loadout。
3. **单机单设备**（RTX 5060 Laptop，8,151 MiB）。**若显存更大，行为可能不同**——这条特别值得标注，因为「第二个 checkpoint 砍半窗口」看起来像容量策略。
4. 只测了**长 state 的钳位**；未重测选项压缩、`noul` 语义等其余 P3/R13 结论（但 §2.1-1 论证了它们在同一 loadout 下一致适用）。
