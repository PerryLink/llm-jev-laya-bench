# 两步操作手册

这两步需要你的账号和浏览器，我做不了。以下是逐步操作。

---

# 第一步：arXiv endorsement（**先做这个，因为它依赖别人回复**）

## 背景：为什么需要它

arXiv 对**首次投稿者**要求 endorsement（背书）。规则是：**在某个分类下还没有被背书过的人，第一次投稿需要一位该分类下的已投稿者替你背书。**

**没有学术机构不是问题。** arXiv 不要求单位，只要求背书。

**你不需要先写好论文再申请**——背书代码是独立于稿件的。

## 操作步骤

### 1. 注册 arXiv 账号

打开 <https://arxiv.org/user/register>

- 用**能长期收信的邮箱**（后面所有通知都走它）
- 填姓名时用 **PerryLink**（和 `CITATION.cff` 一致）
- 单位可以留空或写 **Independent Researcher**
- 会发一封确认邮件，**点里面的链接激活**

### 2. 查你是否需要背书

登录后打开 <https://arxiv.org/auth/need-endorsement>

或者直接开始一次投稿：<https://arxiv.org/submit>

**如果系统提示你需要 endorsement**，它会给你一个**背书代码**（一串字母数字）和一个请求链接。**把这个代码抄下来**——下一步要用。

> ⚠️ 如果系统**没有**要求背书，说明你已符合条件，跳到第二步。

### 3. 选一位背书人

**这是整件事唯一需要动脑的地方。** 选人原则：

**推荐顺序：**
1. **你引用过的、主题最接近的论文的作者** —— 他最能判断你的工作
2. 该论文的**通讯作者或资深作者**（通常是最后一位）
3. 优先选**近年仍活跃**的（看他 arXiv 上有没有近期投稿）

**从你的参考文献里挑。** 打开 `paper/references.bib`，找这类条目：
- PhantomFill、CONSTRUCT、Judge Circuits、Protocol Sensitivity —— 这几篇和你的工作最直接相关
- 或者 Feldhus、Kim & Kang 这类判定器可靠性方向的

**具体怎么找背书人：**

1. 在 arXiv 上搜到那篇论文的摘要页
2. 页面**右下角**有一行 **"Which authors of this paper are endorsers?"**
3. 点它 —— **如果该作者是背书人，你能看到他们愿意背书的分类**
4. 从里面找到**愿意背书 cs.CL 的**那一位

**如果点进去显示"不是背书人"**，就换下一篇论文的作者。

### 4. 发请求信

**信要短，要具体，要让对方一眼看懂你在做什么。** 邮件正文：

```
Subject: arXiv endorsement request for cs.CL

Dear Dr. [姓氏],

I am an independent researcher preparing to submit a measurement study to
arXiv (cs.CL), and I am writing to ask whether you would be willing to
endorse me. I am approaching you because your work on [论文标题] is directly
related to what I am submitting.

My endorsement code is: [从第 2 步抄下来的代码]

What the paper does, in three sentences: it measures the cost, latency and
failure boundaries of three judgment layers on a common item set -- a local
non-autoregressive typed-decision model, a remote typed-decision service,
and a frontier LLM. Its central contribution is negative: the judges' own
self-reported fields are unreliable, capability collapses exactly where the
task requires noticing an ABSENCE, and a heterogeneous judge provided no
incremental coverage in any of three task regimes. Four of the paper's own
earlier conclusions are retracted in the text rather than quietly corrected,
and the artifact ships with 59 automated checks a reader can re-run.

The artifact is public and archived:
  https://github.com/PerryLink/llm-jev-laya-bench
  DOI 10.5281/zenodo.22901248

To endorse, please visit:
  https://arxiv.org/auth/endorse

Thank you for considering it.

PerryLink
Independent Researcher
```

**怎么发：**
- 从论文页面找作者的邮箱（通常在 PDF 首页，或搜索其个人主页）
- **不要群发** —— 一次找一位，等三五天没回音再找下一位
- 一次只问一个人，语气保持克制

### 5. 对方背书之后

你会收到 arXiv 的邮件通知。**然后就可以投稿了**（第二步）。

---

# 第二步：投稿

## A. arXiv（英文稿）

**前提**：背书已到位。

1. 打开 <https://arxiv.org/submit>
2. **选分类**：
   - Primary: **cs.CL**（Computation and Language）
   - Cross-list: **cs.AI**（如系统允许）
3. **上传**：用 `paper/en/MANUSCRIPT.md`
   - arXiv 要 **LaTeX 或 PDF**。你有两个选择：
     - **把 Markdown 转成 PDF**（最简单）：用 Pandoc，或直接在编辑器里导出
     - **让 arXiv 用它的编译器** —— 但 Markdown 不支持，需要先转 LaTeX
   - **如果只想省事**：先转 PDF 上传，arXiv 接受 PDF 投稿
4. **填元数据**：
   - **Title**: `When a Judgment Layer's Self-Reported Fields Lie`
   - **Authors**: `PerryLink`
   - **Abstract**: 从 `paper/en/00-abstract.md` 复制
   - **Comments**: 可写 `59 automated checks; artifact DOI 10.5281/zenodo.22901248`
   - **License**: 选 **CC-BY-4.0**（与你的决定一致）
5. **AI 使用声明** —— arXiv 要求在**正文中**报告。你已经有 `paper/en/13-ai-disclosure.md`，**它已经在 MANUSCRIPT.md 里**，无需额外操作。
6. 提交后会进入 **moderation**（人工审核），通常一到几个工作日。

## B. ChinaXiv（中文稿）

1. 打开 <https://chinaxiv.org>
2. 注册账号（可能需要邮箱验证；**部分功能要求机构邮箱**——若被卡住，看它是否接受个人申请）
3. 投稿时用 `paper/MANUSCRIPT.md`
4. **同样填 DOI** `10.5281/zenodo.22901248` 作为关联制品
5. 选分类：**计算机科学 → 人工智能**

> ⚠️ ChinaXiv 对**首次投稿的个人**可能有额外审核。**如果它要求机构邮箱而你没有**，可以先只发 arXiv——中文稿放在 GitHub 上同样是公开可引用的，等 ChinaXiv 走通再补。

---

# 需要提前准备的三个文件

| 用途 | 文件 | 位置 |
|---|---|---|
| arXiv 英文稿 | `MANUSCRIPT.md` | `paper/en/` |
| ChinaXiv 中文稿 | `MANUSCRIPT.md` | `paper/` |
| 摘要（两个都要填） | `00-abstract.md` | `paper/en/` 和 `paper/` |

**Markdown 转 PDF**（如果你需要）：

```bash
# 需要先装 pandoc 和一个 LaTeX 引擎
pandoc paper/en/MANUSCRIPT.md -o paper-en.pdf \
  --pdf-engine=xelatex -V mainfont="Noto Serif CJK SC" \
  --toc --number-sections
```

中文稿转 PDF 时 `mainfont` 要选**支持中文的字体**，否则会全是方框。

---

# 顺序与预期时间

```
今天     注册 arXiv，拿到背书代码，发出第一封请求
3–7 天   等回复（没回就换下一位）
背书到位 投稿 arXiv → moderation 1–5 个工作日
之后     投 ChinaXiv
```

**唯一可能拖很久的是等背书人回信。所以今天就发第一封。**

---

# 如果卡住了

| 症状 | 怎么办 |
|---|---|
| 论文作者都不是背书人 | 换一篇你引用的论文找他作者；或搜 cs.CL 近期论文的活跃作者 |
| 发了三封都没回 | 继续换人。这是常态，不是你的问题 |
| arXiv 说分类不对 | cs.CL 是主选；若被拒可试 cs.AI |
| Markdown 转 PDF 失败 | 直接上传 Markdown 转出的 HTML→打印成 PDF，或告诉我，我帮你生成 LaTeX |
| ChinaXiv 要机构邮箱 | 先只发 arXiv，中文稿留在 GitHub |

---

**卡在任何一步，把报错或页面内容发给我，我接着帮你处理。**
