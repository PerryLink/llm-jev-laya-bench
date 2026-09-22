# 三件事的处理报告

> 时间：2026-09-22 · 作者：主控
> 结论：**事件 2 已完全解决；事件 3 已记录并给出纠正措施；事件 1 无法由我完成，但已把「只差一个密钥」这件事变成可机械验证的状态。**

---

## 事件 1 — Jev 凭据：**我无法创建，但已把门做好并证明它会正确判别**

### 1.1 为什么我做不到

凭据必须来自 TypeSafe 账户（或 OpenRouter 账户）的**登录后操作**：

> 「**TypeSafe 直连** —— 如果你有来自 [console.typesafe.ai/settings/keys](https://console.typesafe.ai/settings/keys) 的密钥，用这条路」
> —— `jevcore-dsh` README 原文

我没有任何账户凭据，也无法替你注册账户。**这一步只能由你做。**

### 1.2 我查到并核实的确切激活路径（这比「改配置」精确得多）

我读了**实现**（不只是文档），得到三条会影响你操作方式的事实：

**事实一：解析顺序 = 凭据服务优先，环境变量兜底，且都是「每次调用时读取」**

```js
// jevcore/lib/credentials.js:21-40
if (options.credentials !== undefined) { ... return { value, source: 'credential' } }
const fromEnv = env(options.ref)?.trim();
if (fromEnv) return { value: fromEnv, source: 'environment' };
```

而 `index.ts:304` 的注释明确：「**每次调用重建，因此轮换的密钥无需重启即可生效**」。

→ **含义：密钥一旦落到 DSH 能解析的位置，不需要重启 DSH。**

**事实二：凭据引用的三个来源**（DSH 凭据子系统文档原文）

> 「一个 CredentialRef 回答『这个环境变量名背后是什么』，**层叠于进程环境、provider 管理的存储、以及 `.env` 文件**之上。」

→ **三条路都行**，且因为按调用解析，**不一定需要重启**。

**事实三：为什么 `export` 一定失败**（插件 README 原文）

> 「这个 env 映射不是可选的：**DSH 会剥离任何形如凭据的名字**——任何含 `KEY`、`PASSWORD`、`SECRET` 或 `TOKEN` 的，不分大小写——**从它派生给服务器的环境里**，然后再把这个映射合并回去。**你在 shell 里导出的密钥永远不会到达**，而服务器会留在离线 mock 上，**不报任何错**。」

→ 注意「派生给服务器」：这解释了你现在看到的 **stdio MCP 服务**为何收不到。而**HTTP sidecar 与插件在 DSH 主进程内**，所以主进程环境是有效的。

### 1.3 我为你准备好的东西

**门已经做好，且已用 mock 自测过双向判别**（`src\instrument\jev_gate_check.py --verify-fixture`）：

```
GATE CORRECTLY REJECTS THE MOCK: True
GATE ACCEPTS A LIVE-SHAPED RESPONSE: True
```

**并且我在本轮用真实调用测到了 mock 的两个判别基线**（此前只有 R12 的旧夹具）：

| 判别器 | mock 实测 | live 必须 |
|---|---|---|
| **A** 决定性状态（三种说法陈述同一主张） | **noul = 0.7142** | **≥ 0.9** |
| **B** 边界敏感性（同 state/同 id/同措辞，只换边界） | **差值恰好 0.0000** | **非零** |

**判别器 B 的证据链特别干净**：两次调用返回**完全相同的 0.7142**，而 `egress.questionsChars` 从 **216 → 198** —— **证明边界确实被序列化并计数了，只是从未进入哈希**。任何在 mock 上做的边界敏感性研究都会「证明」边界措辞无关紧要。

**检测规则**：一律用 `provider == "mock"`，**不可**靠「没有 warning」——R12 实测 `jev_rank` 传空候选时返回的响应**没有 warning、没有 usage、没有 egress**，比正常响应更「干净」。

### 1.4 你需要做的一件事（二选一）

**路线 A —— TypeSafe 直连（推荐：单一目的地，延迟最低）**

1. 到 [console.typesafe.ai/settings/keys](https://console.typesafe.ai/settings/keys) 创建密钥（有免费额度与限时免费 token 活动，但**额度细节我不核实，请你自己确认**）。
2. 用 DSH 的凭据服务登记，引用名 **`TYPESAFE_API_KEY`**。本机有已安装的 **`dsh.ps1`**，凭据子系统的写入口是 `CredentialProvider.set(ref, value)`，对应 CLI 子命令（**具体子命令名我未核实**，请 `dsh --help` 确认）。
   - 或：写进 DSH 会读取的 `.env`
   - ⚠️ **不要用 shell `export`**——见事实三。
3. 告诉我一声，我立刻跑判别器。**按调用解析，可能不需要重启 DSH**；若判别器不通过，再重启。

**路线 B —— 经 OpenRouter（若你有 OpenRouter 密钥更省事）**

- 配置项为 `provider: openrouter` + `openRouterApiKeyRef: OPENROUTER_API_KEY`
- **两个实质差别**：(1) **另一个第三方**（OpenRouter）接收你的 state，留存策略不同；(2) **这条路会返回 `usage.costUsd`**，而 TypeSafe 路线**根本不报成本**（`costUsd: 0` 意为「未报告」**而非免费**）。
- 模型 id 受限：裸 `jev-*` 或 `typesafe/jev-1.13`；**`typesafe/jev-latest` 不被接受**。

**成本**：判别器只需 3 次调用。按 $0.042/1M 输入、约 200 token/次计，**远低于 $0.001**。**零新增出境风险**——夹具是 R12 已公开的合成状态，不含任何真实语料。

### 1.5 门通过之后我才能做的事

Jev 的 A2 臂、A4-Jev 分支、以及成本表的 Jev 列**都卡在这个门上**。门一过，我可以在一次运行内补齐：延迟分布、`rank` 批量上限、`check` 判定语义、校准状态。**这些是论文成本章节与「Jev `rank` 是否可替代」结论的最后一块。**

---

## 事件 2 — 仪器被同时修改：**已完全解决**

### 2.1 诊断

`laya_mcp` 是 **editable 安装**，直接指向活跃开发树 `laya-mcp-pkg\src\laya_mcp`：

```
laya_mcp loaded from: D:\Projects\laya-family\laya-mcp-pkg\src\laya_mcp
```

本会话期间该树被反复改写（`worker.py` 一次会话内改了三次），且**两个入口曾同时服务不同修订**。所以此前所有测量都带有归属风险。

### 2.2 解决方案（已完成并验证）

**不再测量工作树。** 新增 `src\instrument\run_pinned_sidecar.py`：

1. **启动前重验快照**：逐个重算 `protocol\instrument-snapshot\` 里 13 个 `.py` 的 SHA256，与 `PIN.json` 比对，**不符则拒绝启动**；
2. **钉死导入路径**：以 `PYTHONPATH=<snapshot>/src` 优先，并清除已解析的 `laya_mcp`，然后**断言** `laya_mcp.__file__` 落在快照内；
3. **断言失败即退出**，绝不静默测量错误的代码。

**已验证**（`--help` 走通完整路径）：

```
[pin] laya_mcp from d:\projects\llm-jev-laya-bench\protocol\instrument-snapshot\src\laya_mcp
usage: laya-mcp [-h] [--version] {serve,mcp,doctor,install} ...
```

**好消息**：`git status --porcelain` 现在是**空的**——你的开发已提交，且快照哈希与工作树**仍然一致**。所以「漂移」目前不存在；但**守卫现在是常设的**，无论你之后怎么改，测量都只会在快照上跑。

**用法**：正式采集时用 `python run_pinned_sidecar.py`（默认参数已含 `--device cuda --max-len 1024 --head-max-len 512`），而不是直接 `laya-mcp serve`。

---

## 事件 3 — 凭据值进入会话记录：**已记录并纠正**

### 3.1 事实

我执行 `Select-String -Pattern 'TYPESAFE|OPENROUTER|DEEPSEEK'` 检查凭据引用，**`Select-String` 返回整行**，而该文件是 `KEY: value` 单行格式，因此 **`DEEPSEEK_API_KEY` 的完整值被打印进会话输出**。

### 3.2 影响

| 项 | 评估 |
|---|---|
| 离开本机 | **否**（仅进入本地会话记录） |
| 进入模型上下文 | **是** |
| 写入项目文件 | **否** |
| 可见者 | 能访问本机 DSH 会话记录的人 |

### 3.3 纠正

1. **已写入事件记录** `protocol\INCIDENT-credential-echo.md`（含错误命令与正确写法）。
2. **本项目所有后续核查脚本只枚举键名**，绝不回显值。
3. **建议你轮换 `DEEPSEEK_API_KEY`** —— 这是唯一能彻底消除该值暴露后果的动作。若该账户重要，顺便检查用量异常。
4. **建议把 `.credentials.yaml` 视为敏感文件**：它存的是明文值而非引用。若它曾被同步、备份或进入过任何版本控制，一并处理。

---

## 汇总：三件事的状态

| # | 事项 | 状态 |
|---|---|---|
| **1** | Jev 凭据 | ⏸ **阻塞于你的账户操作。** 我已核实确切路径、发现「shell export 必定失败」的机制、并**用真实调用建立了 mock 判别基线**（A: 0.7142 < 0.9；B: delta 恰好 0.0000），门已自测双向判别通过。**你登记密钥后我可在一次运行内补齐 Jev 全部测量。** |
| **2** | 仪器漂移 | ✅ **已解决。** 钉定启动器已验证可用，快照守卫常设；当前工作树与快照一致。 |
| **3** | 凭据回显 | ✅ **已记录并纠正。** 建议轮换 key。 |

**唯一需要你动手的是事件 1 的第 2 步**（创建并登记密钥）。其余我会在你给出密钥后立即执行。
