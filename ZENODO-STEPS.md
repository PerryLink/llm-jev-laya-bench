# Zenodo 逐步操作

目标：把**英文稿**和**中文稿**各做成一条独立的 Zenodo 记录，各得一个 DOI，并关联到已有的制品 DOI
`10.5281/zenodo.22901248`。

**不需要任何人批准，不需要机构邮箱，不需要等 arXiv。**

---

## 第 0 步：PDF —— ✅ **已经做好了**

**你不需要自己转 PDF。** 两份已经生成并逐项验证通过：

| 文件 | 页数 | 大小 |
|---|---|---|
| `paper/pdf/paper-en.pdf` | 97 | 3.2 MB |
| `paper/pdf/paper-zh.pdf` | 79 | 6.9 MB |

**直接拿去上传即可**（第 5 步用）。

已经验证过的项目（`paper/pdf/_verify_pdf.py` 与 `_check_chrome.py`，两项都通过）：

- ✅ **A4**，全部 176 页
- ✅ **无页眉页脚** —— 不是「看起来没有」，而是**位置证明**：全页**上下各 16 mm 内一个文字块都没有**；正文距顶 20.4 mm、距底 20.7 mm，正好等于 `@page` 设定的 20 mm 边距
- ✅ **正文完整** —— 英文抽出 245,933 字符、中文 109,752 字符
- ✅ **中文不是方框** —— 1,017 个不同汉字，**零个替换字符**

**如果你还是想自己重印**（改了稿子之后），完整命令在 `paper/pdf/README.md`。要点三条：
`--no-pdf-header-footer`、**页眉和页脚必须关**、**背景图形必须开**。

> ⚠️ **顺手把 `paper/pdf/README.md` 里记的两个 SHA256 抄下来。** 它是「你上传的文件 = 我验证过的文件」的唯一凭据。

---

## 第 1 步：登录

打开 **<https://zenodo.org>** → 右上角 **Sign in** → 选 **Sign in with GitHub**

（你已经在用 GitHub 登录了，所以直接进）

---

## 第 2 步：新建上传

打开 **<https://zenodo.org/uploads/new>**

---

## 第 3 步：填表 —— 英文稿

### 顶部

| 字段 | 填什么 |
|---|---|
| **Upload type** | **Publication** → 再选 **Preprint** |

### Basic information

| 字段 | 填什么 |
|---|---|
| **Title** | `When a Judgment Layer's Self-Reported Fields Lie: Cost, Latency and the Failure Boundary of Three Judgment Layers on the Same Items` |
| **Description** | 见下方「摘要填法」 |
| **Publication date** | 保持今天 |
| **Creators** | Family name: **Link** / Given names: **Perry** |
| **License** | 选 **Creative Commons Attribution 4.0 International (CC BY 4.0)** |
| **Language** | **English** |

> ⚠️ **Title 请逐字照抄上面那一行。** 它和 PDF 内嵌的 `/Title`、和 PDF 第一页印的标题**必须完全一致**——三者不一致，读者检索到的标题和文件里的标题就不是同一个东西。这正是本论文在讲的那类错配，不该由论文自己犯。

**摘要填法**：从 `paper/en/00-abstract.md` 复制**摘要正文**（不是整份文件，是 `## Abstract` 下面那几段）。
粘进去后 Zenodo 会自动渲染 Markdown，没问题。

### Recommended information（可选，但建议填）

| 字段 | 填什么 |
|---|---|
| **Keywords** | `judgment layer`, `calibration`, `silent truncation`, `cascade architectures`, `evaluation methodology`, `negative results`, `reproducibility` |

---

## 第 4 步：关联到已有制品（**重要**）

找到 **Related works** 一栏 → 点 **Add**

| 字段 | 填什么 |
|---|---|
| **Relation** | **is supplemented by** 或 **is part of** |
| **Identifier** | `10.5281/zenodo.22901248` |
| **Resource type** | **Software** |

> **为什么重要**：这样读者从论文能找到制品，从制品也能找到论文。**双向可追溯**——这正是这篇论文在讲的事，它自己应当做到。

---

## 第 5 步：上传文件

**Files** 一栏 → **Choose files** → 选 `paper/pdf/paper-en.pdf`

上传完等进度条走完。

---

## 第 6 步：检查并发布

1. 点右上或底部的 **Review**（如有）
2. **通读一遍** preview——**这是你最后一次改的机会**
3. 点 **Publish**

⚠️ **一旦 Publish，DOI 立刻生效且不可撤销。** 发布前确认：
- 标题对
- 作者是 **Perry Link**
- 许可 **CC BY 4.0**
- PDF 打开正常

4. **抄下新的 DOI**（形如 `10.5281/zenodo.XXXXXXXX`）

---

## 第 7 步：中文稿（重复第 2–6 步）

同样 **Publication → Preprint**，但：

| 字段 | 填什么 |
|---|---|
| **Title** | `当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测` |
| **Language** | **Chinese** —— ⚠️ 搜索框输 **`Chinese`**，选**名字就是 `Chinese`、不带方言前缀**的那条（代码 `zho`）。**别输 `chi`，也别输 `zho`**（`zho` 会跳出「闽中语」）。详见 `ZENODO-FORM.md` §⑦ |
| **Creators** | 同上：Family name **Link** / Given names **Perry** |
| **License** | **CC BY 4.0**（与英文稿一致） |
| **Related works** | 加**两条**：<br>① `10.5281/zenodo.22901248` → **Is supplemented by** → Software<br>② 英文稿的 DOI → **Is derived from** → Preprint（**Zenodo 没有 `is translation of`，实测其 34 条关系词表里不存在**） |
| **Files** | `paper/pdf/paper-zh.pdf` |

> ⚠️ **`is translation of` 不存在**，别再找了。用 **`Is derived from`** 指向英文稿 DOI。
> 但**关系表不说明「派生方式是翻译」**，所以**必须在 Description 开头加一句文字说明**
> （模板见 `ZENODO-FORM.md` §⑨），否则读者可能以为是两篇不同的论文。**中文 PDF 里也要加同样的说明。**

---

## 完成后告诉我

把**两个新 DOI** 发给我，我会：

1. 把英文稿 DOI 写进 `CITATION.cff` 和 README
2. **两个 DOI 都写进论文的 §11 数据可用性段**（中英双语）
3. 重建两份稿子
4. 跑 `verify_all.py`（必须仍是 59/0/0）
5. 提交并推送

**论文里引用自己 DOI 的顺序不能颠倒**——**DOI 先存在，论文才能声称它有 DOI。**

---

## 常见问题

| 情况 | 怎么办 |
|---|---|
| 找不到 `Publication → Preprint` | 选 **Publication → Other**，效果一样 |
| 作者栏只让填 Family/Given | Family: **Link**，Given: **Perry**（与 arXiv、`CITATION.cff`、PDF 内嵌 `/Author` 一致） |
| 传完发现 PDF 有 URL 页眉 | 不会发生——已用位置证明排除。若真出现，删掉重传（未发布前可删；已发布只能新建版本） |
| 想同时传 Markdown 源 | **Files 里可以传多个文件**，把 `paper/en/MANUSCRIPT.md`、`paper/MANUSCRIPT.md` 一并传上去更好——它让读者能复制内容 |
| 摘要粘贴后格式乱 | 粘完用它的预览看，必要时手动调空行 |

---

## 为什么值得今天做完

| | arXiv | **Zenodo** |
|---|---|---|
| 需要别人批准 | ❌ 需要背书 | ✅ **不需要** |
| 需要机构邮箱 | 不需要 | **不需要** |
| 出 DOI | 有 | **有** |
| 今天能完成 | 取决于别人 | ✅ **能** |

**arXiv 在等别人回信，Zenodo 不用。两件事不要绑在一起等。**
