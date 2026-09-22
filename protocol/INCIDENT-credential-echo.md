# 事件记录：凭据值意外进入会话记录

> 记录人：主控 · 时间：2026-09-22 · 严重度：中（非密钥泄漏到外部，但进入了会话日志）

## 发生了什么

在「开工前实测 #4（Jev 凭据）」的核查中，我需要确认 `.credentials.yaml` 里**登记了哪些凭据引用**。
我本意只读取**键名**（R12 在早前报告中正确地只做了这一件事，并明确注明「仅检视键名，未读取值」）。

但我执行的命令是：

```powershell
(Get-Content 'C:\Users\zzhdz\.dsh\.credentials.yaml') | Select-String -Pattern 'TYPESAFE|OPENROUTER|DEEPSEEK'
```

`Select-String` **返回整行**，而不是只返回匹配的键名。由于该文件的格式是 `KEY: value` 单行存放，
**`DEEPSEEK_API_KEY` 的完整值被打印到了会话输出中**，因此进入了本次会话的记录。

## 影响评估

| 项 | 评估 |
|---|---|
| 是否离开本机 | **否**。输出仅进入本地会话记录，未发送到任何第三方 |
| 是否被模型处理 | **是**。该值在本会话上下文中 |
| 是否已提交到代码库 | **否**。未写入任何 proyecto 文件 |
| 谁可见 | 能访问本机 DSH 会话记录的人 |

## 纠正措施

1. **本次会话及以后，一律不打印凭据文件的任何行。** 只允许读取**键名**，且必须显式剥离值：
   正确的写法是 `(Get-Content $f) -replace '(:|=).*$',''` 或直接解析 YAML 取键名。
2. **建议轮换 `DEEPSEEK_API_KEY`**（见下）。这是唯一能彻底消除该值暴露后果的动作。
3. 我把这条写进记录，而不是悄悄略过——本项目的方法论前提就是「错误必须留痕」。

## 给人类的两项建议

1. **轮换 `DEEPSEEK_API_KEY`**：在 DeepSeek 平台重新生成，并更新 `.credentials.yaml` 中的引用。
   若该 key 属于重要账户，建议一并检查用量是否有异常。
2. **把 `.credentials.yaml` 视为敏感文件**：它存的是明文值而非引用。若该文件曾被同步、备份、
   或进入过任何版本控制，应一并处理。

## 后续预防（已生效）

本项目的核查脚本已改为**只枚举键名**。例如检查 Jev 凭据是否就位时，只输出：

```
credential ref NAMES present: DEEPSEEK_API_KEY
env vars matching TYPESAFE|OPENROUTER|JEV: (none)
```

不再回显任何值。
