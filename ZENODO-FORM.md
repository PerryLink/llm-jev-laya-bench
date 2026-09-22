# Zenodo 上传 —— 对照你当前页面的逐步填写

页面顶端那条横幅（"Zenodo is currently experiencing slowness..."）**不影响上传**，忽略即可。

> **这一版表单是 Zeonodo 新版的单页表单**（和我早先写的分步向导不同）：所有栏目一次性全列出来，
> **只有少数几个是必填的**，其余留空完全没问题。下面按你贴出的栏目顺序逐条给值。

**两份记录分开做，各得一个 DOI。** 先做英文，再做中文。

---

## 一、必填的 6 个字段

### ① Resource type

点开下拉，选 **Publication** → 然后选 **Preprint**。

> 找不到 Preprint 就选 **Publication → Other**，效果一样。

### ② Title —— **逐字照抄**

**英文稿**：

```
When a Judgment Layer's Self-Reported Fields Lie: Cost, Latency and the Failure Boundary of Three Judgment Layers on the Same Items
```

**中文稿**：

```
当判定层的自报字段说谎时：三类判断层的成本、延迟与失效边界实测
```

> ⚠️ **这两个字符串和 PDF 内嵌的 `/Title`、和 PDF 第一页印的标题已经核对为完全一致。**
> 改一个字，检索到的标题就和文件里的标题不是同一个东西了 —— **这正是本论文在讲的那类错配。**

### ③ Publication date

**保持 `2026-09-22` 不动。** 它和 `CITATION.cff` 的 `date-released` 一致。

> 这个字段要的是**首次发表日期**。制品（v1.0.1）就是这天发的，所以填它对。

### ④ Authors/Creators

点 **Add creator**，填**两个框**：

| 框 | 填 |
|---|---|
| **Family name** | `Link` |
| **Given names** | `Perry` |

> ⚠️ **不要用 `PerryLink`，也不要只填一个框。** 你的 `CITATION.cff` 里原先写的是 `PerryLink`，
> 我已改成 `Link` / `Perry`，四处（PDF 首页、PDF 内嵌 `/Author`、`CITATION.cff`、这里）现在一致。
> 单框填 handle 会让 Zenodo 渲染成 "PerryLink, PerryLink"，那正是当初改用单框的原因 —— 但解法是
> **分开填 given/family**，不是换个拼法。

### ⑤ Description

**英文稿的摘要已经在你的剪贴板里了**（我刚放进去的，10,562 字符）。

直接 **Ctrl + V** 粘进 Description 框即可。它是 Markdown，Zenodo 会自动渲染：
粗体、破折号、`⚠️`、`n=` 都会正常显示。

**中文稿**：摘要不在剪贴板里（剪贴板只放得下一份）。从
`paper/pdf/_zenodo-fields.txt` 里复制 —— 那个文件里**两份记录的每个字段都齐了**，用记事本打开即可。

> **只粘摘要正文**，不要粘 `paper/en/00-abstract.md` 整个文件 ——
> 文件里还有「翻译说明」和「Disclosure compliance check（编者记录）」，
> **那是给编辑看的内部合规记录，不该出现在 Zenodo 的摘要里。**

### ⑥ Files

把文件拖进 **Drag and drop files** 区域：

- 英文稿：`paper/pdf/paper-en.pdf`（97 页，3.2 MB）
- 中文稿：`paper/pdf/paper-zh.pdf`（79 页，6.9 MB）

**顺手把 Markdown 源也拖进去**（同一批，可以多选）：英文拖 `paper/en/MANUSCRIPT.md`，
中文拖 `paper/MANUSCRIPT.md`。**它让读者能直接复制内容**，也方便将来重排。

> **⚠️ 传完两个文件后，必须去勾 `Preview` 列。**
>
> Zenodo 官方文档 [Manage files](https://help.zenodo.org/docs/deposit/manage-files/) 的规则是：
> **"the first previewable file in alphanumeric order"** —— **按字母序第一个可预览的文件**。
>
> | 文件 | 首字母 | 字母序 |
> |---|---|---|
> | `MANUSCRIPT.md` | **M** | 在前 |
> | `paper-en.pdf` | **p** | 在后 |
>
> **ASCII 里所有大写字母排在小写字母之前**，所以 `MANUSCRIPT.md` 总是排在 `paper-*.pdf` 前面。
> 而 **Markdown 不是 Zenodo 的可预览格式**，系统挑了它却渲染不出来，
> **读者打开记录页就看不到论文正文**。
>
> **→ 在 `Preview` 那一列勾选 `paper-en.pdf`（中文记录勾 `paper-zh.pdf`）。**
> 该复选框是**单选**的 —— 一份记录只能有一个默认预览文件。
>
> 勾错语言是最容易犯的错：**两份记录独立，各勾各的**。

---

## 二、已经填好的（不用动）

| 字段 | 现状 | 说明 |
|---|---|---|
| **Licenses** | ✅ Creative Commons Attribution 4.0 International | 正确，别改。英文中文都用 CC BY 4.0 |
| **Copyright** | ✅ `Copyright (C) 2026 The Authors.` | 正确，别改 |
| **Publisher** | ✅ `Zenodo` | 正确，别改 |
| **Visibility** | ✅ **Public** | 必须 Public，否则没有 DOI |

---

## 三、建议填的（4 个，各 30 秒）

### ⑦ Languages

**英文稿**：搜索框输入 **`eng`** → 选 **English**。

**中文稿**：搜索框输入 **`Chinese`** → 在下拉列表里选**名字就是 `Chinese`、不带任何方言前缀**的那一条（代码 `zho`）。

> **⚠️⚠️ 两个坑，都实际踩过**
>
> **坑 1：输 `chi` 没用。** `chi` 不是一个词条。词表 API 实测 `q=chi` 只返回一条
> **"Ho Chi Minh City Sign Language"**，与中文无关。
>
> **坑 2：输 `zho` 会跳出「闽中语」。** ⚠️ **这是实际踩到的坑。**
> 词表 API 里 `q=zho` 返回的确实是 `Chinese`（正确），
> **但界面的搜索框是在下拉列表里做子串过滤，不是按代码查** ——
> 输 `zho` 会先匹配到 **"Min Zho**ng Chinese"** 里的 `Zho`，于是跳出 **Min Zhong Chinese（闽中语）**。
> 实测 `q=Zhong` 只返回一条，正是 `Min Zhong Chinese`。
>
> **→ 所以按「名字」搜，不要按「代码」搜。**
>
> **正确做法**：输 **`Chinese`**（出来 19 条），选**名字就是 `Chinese`、后面不跟任何方言名**的那一条。
>
> | 名字 | 代码 | 备注 |
> |---|---|---|
> | **`Chinese`** | **`zho`** | ✅ **选这个** —— 宏语言，泛指中文 |
> | Jinyu Chinese | cjy | 晋语 |
> | Mandarin Chinese | cmn | 官话 |
> | Huizhou Chinese | czh | 徽语 |
> | Gan Chinese | gan | 赣语 |
> | Hakka Chinese | hak | 客家话 |
> | Xiang Chinese | hsn | 湘语 |
> | Literary Chinese | lzh | 文言 |
> | Old Chinese | och | 上古汉语 |
> | Wu Chinese | wuu | 吴语 |
> | Yue Chinese | yue | 粤语 |
> | Min Dong Chinese | cdo | 闽东语 |
> | Chinese Pidgin English | cpi | 中国洋泾浜英语 |
> | Chinese Sign Language | csl | 中国手语 |
> | Pu-Xian Chinese | cpx | 莆仙语 |
> | Min Zhong Chinese | czo | 闽中语（**误选过这个**） |
> | Late Middle Chinese | ltc | 中古汉语晚期 |
> | Min Bei Chinese | mnp | 闽北语 |
> | Min Nan Chinese | nan | 闽南语 |
>
> *（19 条取自 `api/vocabularies/languages?q=Chinese`。）*
>
> **为什么选 `zho` 而不是 `cmn`**：`zho` 是**宏语言**，只声明「这份文档是中文」；
> `cmn`（官话）是**具体语言**，用它等于宣称这是**官话口语**语料 —— 而本稿是**书面学术中文**。
>
> ⚠️ **带地名前缀的一律不对**（Min Zhong / Min Nan / Min Bei / Yue / Wu / Hakka…）——
> 那些是**具体方言**，本论文不属于任何一种。
>
> **只选一条。** 选错了不要紧：**元数据发布后随时可改**（只有文件受 45 天限制），
> 改元数据**不会改变 DOI**。

### ⑧ Keywords and subjects

**英文稿**（复制这一行）：

```
LLM evaluation; judgment layer; calibration; silent truncation; cascade architectures; evaluation methodology; long-horizon agents; negative results; reproducibility
```

**中文稿**：

```
判定模型; 校准; 静默截断; 级联架构; 评测方法学; 长线智能体; 阴性结果; 可复现性
```

### ⑨ Related works —— **这条最重要**

点 **Add**，填**三格**：

**英文稿填一条：**

| 格 | 填 |
|---|---|
| **Relation** | **is supplemented by** |
| **Identifier** | `10.5281/zenodo.22901248` |
| **Resource type** | **Software** |

**中文稿填两条：**

| Relation | Identifier | Resource type |
|---|---|---|
| **is supplemented by** | `10.5281/zenodo.22901248` | **Software** |
| **is translation of** | *英文稿的新 DOI* | **Preprint** |

> ⚠️ **`is translation of` 不能省。** 它向读者和索引说明**两份是同一项工作的两个语言版本，不是两篇论文** ——
> **否则可能被当成重复发表。**
>
> ⚠️ **`is translation of` 的指向必须用英文稿的 DOI**，而英文稿要**先发布**才有 DOI。
> **所以顺序是：先发英文，拿到 DOI，再发中文。** 反过来做不出来。

> **为什么要关联 `10.5281/zenodo.22901248`**：那是你制品的 DOI。这样读者从论文能找到制品、
> 从制品也能找到论文 —— **双向可追溯**。这正是这篇论文在讲的事，它自己应当做到。

### ⑩ Version（可选，建议填）

英文稿填 `v1.0.2`，中文稿填 `v1.0.2`（跟着制品走）。不填也没关系。

---

## 四、**全部留空**的栏目

这些你可以直接跳过，一个字都不用填：

| 栏目 | 为什么留空 |
|---|---|
| **Select the community...** | 可选项。除非你想投某个 Zenodo 社区，否则不选 |
| **Digital Object Identifier** | ⚠️ **这是给「别处已有 DOI」用的。你没有，所以留空。** 填了反而出错 |
| **Contributors** | 只有你一个作者，已在 Authors/Creators 里；这里是给**非作者**贡献者用的 |
| **Dates** | 除 Publication date 外的其他日期（收集期、有效期），没有 |
| **Funding / Awards/Grants** | 无资助 |
| **Alternate identifiers** | 无 |
| **References** | 参考文献已在 PDF 里，这里不重复 |
| **Software 全套**（Repository URL / Programming language / Development Status） | ⚠️ **这是因为你选了 Preprint 才会出现的栏目。制品（software）那条记录里已经填过了，这里留空** |
| **Publishing information 全套**（Journal / ISSN / Volume / Issue / Page range / Imprint / ISBN / Place / Pagination / Edition） | 未在期刊发表 |
| **Thesis 全套**（Awarding university / department / Thesis type / Submission date / Defense date） | 不是学位论文 |
| **Conference 全套**（Title / Acronym / Place / Dates / Session / Part / Website） | 未投会议 |
| **Options → Apply an embargo** | 不 embargo，要立刻公开 |

> **表单很长不代表要填满。** 必填的就那 6 项，其余空白是完全正常、完全合规的 Zenodo 记录。

---

## 五、发布

1. 滚到底部，点 **Publish**
2. **发布前最后核对四条**（这是你唯一的机会）：
   - Title 逐字对
   - Authors 是 **Link / Perry**
   - License 是 **CC BY 4.0**
   - PDF 点开能正常看
3. ⚠️ **一旦 Publish，DOI 立刻生效，文件不能再改。** 要改只能新建版本（会得到新 DOI）
4. **把新 DOI 抄下来**，形如 `10.5281/zenodo.XXXXXXXX`

---

## 六、两个 DOI 到手之后

**发给我**，我会：

1. 写进 `CITATION.cff` 和 `README.md`
2. **两个 DOI 都写进论文 §11 数据可用性段**（中英双语）
3. 重建两份稿子、重出 HTML
4. 重转两份 PDF（用 `paper/pdf/README.md` 里记的命令，已脚本化）
5. 跑 `verify_all.py`（必须仍是 59/0/0）
6. 提交

> **顺序不能颠倒**：**DOI 先存在，论文才能声称它有 DOI。**
> 现在论文里没有 DOI，是**陈述准确**，不是漏写。

---

## 七、关于横幅和当前的不稳定

页面顶部说 Zenodo 因爬虫流量而变慢、间歇性不可用。这意味着：

- **上传可能变慢或中途失败** —— 失败就重试，别反复刷新丢状态
- **Publish 卡住不要连点** —— 等它转完，重复提交可能产生两条记录
- **如果出现两条重复记录**：趁未发布删掉多余的那条；已发布就只能新建版本修正

**这不影响可行性。** Zenodo 不需要任何人批准、不需要机构邮箱、不需要等 arXiv 背书 ——
**arXiv 在等别人回信，Zenodo 不用，两件事不要绑在一起等。**
