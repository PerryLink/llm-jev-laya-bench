# Zenodo 逐步操作

目标：把**英文稿**和**中文稿**各做成一条独立的 Zenodo 记录，各得一个 DOI，并关联到已有的制品 DOI
`10.5281/zenodo.22901248`。

**不需要任何人批准，不需要机构邮箱，不需要等 arXiv。**

---

## 第 0 步：先把两份稿子转成 PDF

Zenodo 接受 PDF，不接受 Markdown 或 HTML（虽然能传，但读者打不开好看的版本）。

**打开** `paper/dist/en.html`（英文）或 `paper/dist/zh.html`（中文）：
在浏览器里直接双击文件即可。

**然后** `Ctrl + P`（打印）→ **目标 / Destination 选「另存为 PDF」**

**打印设置逐项确认：**

| 设置 | 选什么 |
|---|---|
| 目标 | **另存为 PDF** |
| 页面 | **A4** |
| 边距 | **默认** |
| **页眉和页脚** | ⚠️ **取消勾选** |
| 背景图形 | **勾选**（表格底色要印出来） |

> ⚠️ **「页眉和页脚」一定要取消**，否则每页会印上 `file:///D:/...` 和页码——**arXiv 和 Zenodo 都不该收到这种东西**。

**存成**：
- `paper-en.pdf`（英文稿）
- `paper-zh.pdf`（中文稿）

**存完打开翻两页**，确认：
- ✅ **正文不是方框**（中文字体渲染正常）
- ✅ 表格没有超出页面
- ✅ 首页没有 URL 和日期

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
| **Title** | `When a Judgment Layer's Self-Reported Fields Lie` |
| **Description** | 见下方「摘要填法」 |
| **Publication date** | 保持今天 |
| **Creators** | 点 **Add creator** → Family name: **Perry** / Given names: **Link**；或点右侧的 **+** 用 **Organization/Person** 方式填 **PerryLink** |
| **License** | 选 **Creative Commons Attribution 4.0 International (CC BY 4.0)** |
| **Language** | **English** |

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

**Files** 一栏 → **Choose files** → 选 `paper-en.pdf`

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
| **Language** | **Chinese** |
| **Creators** | 同上，**Perry Link** |
| **License** | **CC BY 4.0**（与英文稿一致） |
| **Related works** | 加**两条**：<br>① `10.5281/zenodo.22901248` → **is supplemented by** → Software<br>② 英文稿的 DOI → **is translation of** → Preprint |
| **Files** | `paper-zh.pdf` |

> **`is translation of`** 这个关系很重要——它向读者说明**两份是同一项工作的两个语言版本**，不是两篇论文。**否则可能被误认为重复发表。**

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
| 作者栏只让填 Family/Given | Family: **Perry**，Given: **Link**（与 arXiv 保持一致） |
| 传完发现 PDF 有 URL 页眉 | 删掉这条记录重传（未发布前可删；已发布只能新建版本） |
| 想同时传 Markdown 源 | **Files 里可以传多个文件**，把 `.md` 一并传上去更好——它让读者能复制内容 |
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
