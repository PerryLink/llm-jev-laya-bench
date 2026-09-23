# Zenodo 原地 Edit：完整详细步骤

**目标**：把两份论文的**勘误版**替换进**已有记录**，**DOI 不变**（`22901853` / `22902025`）。
**做完后 `CITATION.cff`、`README.md`、论文 §11 一个字都不用改。**

**官方依据**（[Manage files](https://help.zenodo.org/docs/deposit/manage-files/)，原文）：
> *"if you would like to make minor corrections, and you are **within 30 days** after publication,
> you can edit the uploaded files of the record."*
> 步骤：*"Open the **Edit files** accordion → Click **Edit published files** → Read and complete
> the **Edit files** modal"*
> 约束：*"The draft must be published within 45 days of the original publishing of the record.
> **Publishing the draft will not change the DOI.**"*

**窗口状态**：发布于 2026-09-22，今天 2026-09-23 → 已过 **1 天**，45 天窗口剩 **44 天**。

---

## 开工前：先把这两处打开

**文件所在目录**（我要你在资源管理器里对照字节数）：

```
D:\Projects\llm-jev-laya-bench\paper\pdf\          ← 两个 PDF
D:\Projects\llm-jev-laya-bench\paper\en\           ← 英文 MD
D:\Projects\llm-jev-laya-bench\paper\              ← 中文 MD
```

**剪贴板**：**正确的中文标题已经在里面**（31 字符，第 13 位是全角 `：`，我核对过与 PDF `/Title` 逐字一致）。
⚠️ **在用到它之前不要复制任何别的东西**，否则会被覆盖。若被覆盖，告诉我，我重放。

---

# 第 1 步：英文记录

## 1-1 打开记录并进入编辑

1. 打开 **<https://zenodo.org/records/22901853>**
2. 点页面上的 **`Edit`** 按钮（绿色，通常在右上）

## 1-2 解锁文件

1. 在编辑页往**下滚**，找到 **`Edit files`** 折叠区（accordion）
2. 点它展开 → 点 **`Edit published files`**
3. **弹窗**：读完内容，按要求确认（可能要你选一个理由或勾选确认）
4. 点确认 → 文件列表**变为可编辑**

> 这一步就是「解锁」。文档说 *"You can now change the files of the record."*

## 1-3 删掉两个旧文件

点 `paper-en.pdf` 和 `MANUSCRIPT.md` 各自的**垃圾桶图标**。

**对照表**（旧文件大小，确认你删对了）：

| 要删的 | 当前记录里的大小 |
|---|---|
| `paper-en.pdf` | 3,202,893 字节 |
| `MANUSCRIPT.md` | 272,899 字节 |

## 1-4 传两个新文件

**拖入**（或用 `Upload files` 按钮选）：

| 文件 | 完整路径 | 字节数 | md5（Zenodo 会显示，请对上） |
|---|---|---|---|
| **PDF** | `paper\pdf\paper-en.pdf` | **3,303,623** | `e2df8e260850731b6564cc593f6ed758` |
| **MD** | `paper\en\MANUSCRIPT.md` | **280,617** | `761801c8f4de27d4330b4e151e5311eb` |

> ⚠️ **`MANUSCRIPT.md` 在 `paper\en\` 里**（多一层 `en\`）。传错就会把中文稿放进英文记录。

**等两个文件都出现 md5 和实际字节数。**
进度列显示 **红色 100%** 或 **"Checksum not yet calculated"** 就是**还没算完**，此时 Publish 是灰的。

## 1-5 勾 Preview

在文件表格的 **`Preview`** 列，**勾选 `paper-en.pdf`** 那一行的复选框。

> 这一列是单选。不勾的话读者打开记录页看不到论文正文（系统按字母序挑中 `MANUSCRIPT.md`，而 md 不可预览）。

## 1-6 元数据：一个字都不用动

标题、作者、许可、语言、related works 全部保持原样。

**可选**：把 **Version** 填 `v2`（原记录里是空的）。

## 1-7 Publish

滚到底 → **`Publish`**（绿色）→ 确认。

> **官方原话**：*"Publishing the draft will not change the DOI."*

**DOI 仍是 `10.5281/zenodo.22901853`。**

---

# 第 2 步：中文记录

## 2-1 打开并进入编辑

1. 打开 **<https://zenodo.org/records/22902025>**
2. 点 **`Edit`**

## 2-2 ⚠️ 顺手修标题的全角冒号

**当前记录里是半角，要改成全角：**

```
现在 : 当判定层的自报字段说谎时:三类判断层的成本、延迟与失效边界实测   ← 半角 U+003A
应为 : 当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测   ← 全角 U+FF1A
```

**操作**：
1. 找到 **Title** 输入框
2. **Ctrl+A 全选 → Delete 清空**
3. **Ctrl+V** —— **正确标题在剪贴板里**
4. ⚠️ **不要手打**，也不要从别处复制片段 —— 上次就是手打出的事

**粘完自查**：「说谎时」后面、「三」前面那个冒号，**两点要占满一个汉字宽度**。

## 2-3 解锁文件

同 1-2：**`Edit files`** 折叠区 → **`Edit published files`** → 弹窗确认。

## 2-4 删旧文件

| 要删的 | 当前大小 |
|---|---|
| `paper-zh.pdf` | 6,924,090 字节 |
| `MANUSCRIPT.md` | 227,497 字节 |

## 2-5 传新文件

| 文件 | 完整路径 | 字节数 | md5 |
|---|---|---|---|
| **PDF** | `paper\pdf\paper-zh.pdf` | **7,038,415** | `b87f99acaad538449afde2b1b996a091` |
| **MD** | `paper\MANUSCRIPT.md` | **234,119** | `c9abe32ac003a128a5fff66d8768b833` |

> ⚠️ **中文的 `MANUSCRIPT.md` 在 `paper\` 里，没有 `en\`。**

**等 md5 出现。**

## 2-6 其余元数据不用动

作者、许可、语言（`zho`）、related works 两条都保持原样。

| related work | 值 | 要不要改 |
|---|---|---|
| `is supplemented by` | `10.5281/zenodo.22901248` | 不改 |
| `is derived from` | `10.5281/zenodo.22901853` | **不改** —— v1 是那一版的记录，链接依然成立 |

**Version** 可填 `v2`。

## 2-7 勾 `Preview` → 勾 **`paper-zh.pdf`**

## 2-8 Publish

**DOI 仍是 `10.5281/zenodo.22902025`。**

---

# 第 3 步：做完后让我核验

**两个记录都 Publish 之后，跟我说一声。** 我会拉 API 逐项比对：

| 我会检查 | 期望 |
|---|---|
| 英文记录 `paper-en.pdf` | 3,303,623 字节，md5 `e2df8e26…` |
| 英文记录 `MANUSCRIPT.md` | 280,617 字节，md5 `761801c8…` |
| 中文记录 `paper-zh.pdf` | 7,038,415 字节，md5 `b87f99ac…` |
| 中文记录 `MANUSCRIPT.md` | 234,119 字节，md5 `c9abe32a…` |
| 中文标题第 13 位 | **U+FF1A 全角** |
| 两个 DOI | **未变**（`22901853` / `22902025`） |

**通过之后我更新 `PUBLISHED.md`**，把「待发布」改成已完成 —— 那一步只动文档，不用再碰 Zenodo。

---

# 常见问题

| 情况 | 怎么办 |
|---|---|
| **找不到 `Edit files` 折叠区** | 往下滚（它在文件列表附近）；仍找不到就把那一屏发我 |
| **点 `Edit published files` 没反应 / 报错** | Zenodo 当前不稳定（顶部常有横幅）。**等一会儿重试，别连点** |
| **弹窗问理由** | 按最贴近的选，比如「minor correction / metadata or file correction」 |
| **`Progress` 红色 100%** | 校验和没算完。**等**；若一直不变，删掉那个文件重传。**不要反复刷新** |
| **Publish 灰着** | 有文件没算完，或有必填字段报错。看 `Basic information` 左边红色计数 |
| **怕传错语言** | 对照 md5 —— 四个都不同，传错立刻能看出来 |
| **想中途放弃** | 未发布的草稿可直接删（记录页 `Manage` → `Delete record` 只删草稿；**已发布内容不受影响**） |

---

# 为什么这次选 Edit 而不是发新版本

| | Edit（本次） | New version |
|---|---|---|
| DOI | **不变** | 新增 |
| 下游要改的文档 | **零** | `CITATION.cff`、`README`、`PUBLISHED.md`、可能还有论文 §11 |
| 迭代轮数 | **1 次做完** | 若引 version DOI 则要第 3 轮 |
| 代价 | `22901853` 不再指向「最初那一版」 | 记录里同时留着有错的一版 |

**你选了零迭代，这是合理的，而且 concept DOI 在学术引用里本来就是标准做法。**
唯一放弃的是「记录里保留曾发布过一版有错误的稿子」这个事实 —— 而论文自己已经公开了那次勘误
（`results/ERRATA.md` §12），所以这件事并没有从世界上消失，只是不再由 Zenodo 的那条记录承担。
