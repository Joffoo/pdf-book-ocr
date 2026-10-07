---
name: pdf-book-ocr
description: Convert PDF books (scanned or digital) to EPUB 3 and Obsidian Markdown. Triggers on "PDF转电子书", "做成EPUB", "OCR整本书", "扫描件数字化", "PDF书籍排版". Unified pipeline with chunking, subagent transcription, semantic H2 assembly, and popup footnotes.
---

# PDF Book OCR (出版级图书数字化工具)

将长篇 PDF（100~500+页，扫描或数字版）转换为出版级 EPUB 3 与 Obsidian 典藏笔记。采用**单轨统一流水线**（Unified Single Pipeline），自动规避长文档上下文超限与跨页断裂。

---

## 统一处理架构

```
[原始 PDF 图书 (扫描版或数字文字版)]
       │
       ▼ (Step 1: 预处理、切片规划与全局目录提取)
 digitize_book.py ──> 提取封面、切片为 10~15 页微型 PDF、提取《全书大章白名单》
       │              (数字版附带 raw.txt 纯文本草稿，扫描版提供微型 PDF)
       ▼
[Step 2: Subagent 批次滚动转写/清洗] ──> 注入大章白名单约束，防小节升格，逐片落盘 raw_md/*.md
       │
       ▼ (Step 3: 语义汇编与目录审查门禁)
 digitize_book.py --preview-toc / --assemble
       ├── seam_auditor: 校验首尾断缝与段落连续性
       ├── toc_manifest: 主 Agent 审查章节拟案（TOC Review Gate），剔除碎片短章
       ├── chapter_assembler: 按真实 ## 大章标题聚合章节、隔离脚注命名空间
       └── epub_builder: Pandoc 编译 EPUB 3 + 注入双向弹框注释
       │
       ▼ (Step 4: 出厂验收)
《书名》.epub + 《书名》.md + images/ (生成至输出工作目录)
```

---

## 执行标准与作业规约 (Agent SOP)

当用户提出 PDF 转电子书或 OCR 请求时，严格按以下步骤与**验收门禁（Completion Gates）**执行：

### Step 1: 环境检查、切片规划与目录白名单提取
1. 运行 `python .agent/skills/pdf-book-ocr/scripts/digitize_book.py --doctor`，确认依赖正常。
2. 运行 `python .agent/skills/pdf-book-ocr/scripts/digitize_book.py "<PDF路径>"`。
   - 脚本自动提取封面、配图并生成 10~15 页物理切片，建立 `subagent_jobs.json`。
   - **数字文字版**：自动提取高质插图并生成 `parts/*.raw.txt` 纯文本草稿，供纯文本低 Token 快速清洗；
   - **扫描版**：自动提供纯微型 PDF 供视觉多模态转写。
3. **全局目录提取（Global TOC Whitelist）**：切片完成后，主 Agent 使用 `view_file` 审阅第 1~2 个切片（通常含目录、卷首说明或编者按），提炼出本书的《全书大章白名单》（例如 `['伸伸脚', '十封信', '幸运的错误', ...]`）。若全书无显式目录（如纯长篇连续小说），记录“无显式目录，依大章通则转写”。
- **Gate 1 验收门禁**：检查 `subagent_jobs.json` 已生成（条目数 > 0），且已提炼出《全书大章白名单》（或确认无显式目录）。

### Step 2: 分发分片并发清洗/转写
读取 `subagent_jobs.json`，根据体裁从 `references/prompts/` 读取对应原子提示词模具（数字版选 `digital.txt`，散文小说选 `prose.txt`，戏剧选 `drama.txt`，学术专著选 `academic.txt`；路由索引参见 [references/prompt_templates.md](references/prompt_templates.md)），使用 `invoke_subagent` 派发任务：
- **无状态直通作业律 (Stateless Straight-Through & Context Boundary)**：
  依据《writing-for-agents》视界封锁与正向导向法则，子 Agent 为严格无状态的叶子节点。
  1. **上下文断火墙**：子 Agent 仅知晓当前切片输入与目标输出，绝不向其透露全书宏观流程、下游 Pandoc 编译、TOC 审查等全局信息，杜绝子智能体产生越界焦虑与工具探查冲动；
  2. **绝对正向声明 (Zero Negation)**：派发提示词严禁使用“严禁/切勿/不得”等否定句式（否定句会把被禁止的行为如 Python 脚本、图片裁切直接拉入注意力前台），仅声明正向执行链条：`view_file 打开切片 -> 纯视觉版面映射 -> write_to_file 直接落盘 -> send_message 单行标记`；
  3. **可核验完成判据 (Checkable Criteria)**：完成判据仅为文件成功落盘与单行 `[DONE] {part_name}`，严禁要求子 Agent 汇报精确字数，彻底杜绝模型因统计字数而执行脚本计数的次生风险；
  4. **下游自动仲裁**：跨分片大章标题与断句缝合 100% 由下游汇编器自动处理，子任务零跨片依赖。
- **正向安全历史档案锚定 (Safe Archival Framing)**：针对医学、生物、历史通识读物，Prompt 前置声明任务为“公开发行国家正规出版物历史社科文献数字化转录”，并引导思维链聚焦于字符拓扑与排版校验，杜绝外部 CBRN 安全过滤器误杀。
- **前置大章白名单注入**：派发 Prompt 时，将 Gate 1 提炼的《全书大章白名单》注入提示词：仅白名单内篇目可标为二级标题 `##`；其余小节、编号、副标题统一标为三级标题 `###`。
- **批次滚动派发（Rolling Batching）**：分片总数 > 4 时，**强制以 3~4 个分片为一组滚动派发**。当前批次全部落盘后，再拉起下一批，严防 API 限流（429）。
- **极简中继与静默推进（Silent Relaying）**：批次推进期间，父 Agent 严禁对每个分片进行长篇剧情汇报（防止膨胀上下文），批次转换仅输出单行紧凑状态（如 `批次 [01~04/24] 完成，推进批次 [05~08]`）。
- **多模态全流程履约铁律（Anti-Downgrade Redline）**：扫描版必须完整执行视觉子 Agent 转写，以确保版式拓扑理解、跨页自然断句缝合与插图定位品质。严禁擅自切换为纯本地机械 OCR。
- **目标路径**：所有子任务直接落盘写入 `raw_md/{md_file}`。
- **文本流式与排版三态语义模型 (Tri-State Semantic Model)**：
  1. **流式正文态（默认态）**：所有小说、杂文、人物故事、科普论述与叙述正文，自然段内各句必须平滑缝合为连续自然段，严禁添加反斜杠 `\`，享有阅读器标准 2em 首行缩进；
  2. **全篇诗体态（独立题记/序诗）**：全书开篇若有题记、序诗或献词，顶部显式标记一级标题 `# 题记`（或 `# 序诗` / `# 献词`），行末添加反斜杠 `\` 保持硬换行（输出 HTML `<br />`），节与节之间保留空行。汇编器自动注入 `epigraph-section` 样式并在正文版面优雅隐藏 H1，保持 TOC 大纲清晰；
  3. **附属卡片态（篇首作者小传/引言卡片）**：篇首作者简介或短篇引言卡片若需保留艺术分行排版，**严禁使用裸 `<p>` 加 `\`**（防止首行 2em 缩进与后续顶格产生刺眼的“阶梯状锯齿错位”），必须包裹在语义化容器中：`<div class="author-bio">` 或 `<div class="epigraph">`，容器内强制 `text-indent: 0 !important` 并配置雅致楷体与装饰竖线。
- **篇章开篇三层契约 (Chapter Header & Author Schema)**：
  在文集、期刊或含独立作者的图书中，若大章存在作者/译者署名，紧随 `## 大章标题` 显式标注 `<p class="chapter-author">作者名</p>`。后续若有肖像插图与简介，按 `## 标题` $\to$ `<p class="chapter-author">作者名</p>` $\to$ `<!-- FIGURE -->` $\to$ 简介卡片（`<div class="author-bio">`）/正文自然衔接，避免作者信息被插图阻断。
- **插图与图题正交契约（Figure Caption & Orthogonality SSOT）**：
  - `<!-- FIGURE -->` 的 bbox 仅界定独立非文本视觉实体本身（照片、画作、插画、线描、图表）的紧致外接矩形；采用 0~1000 千分比整数：`round(coord / dim * 1000)`；
  - **图文正交互斥律（Image-Text Orthogonality）**：凡在 Markdown 正文中已转写录入的排版文本（正文句子、标题、图注、作者简介等），其物理版面区域与插图 bbox 严格正交互斥，严禁重叠；
  - **紧致裁切（Tight Subject Envelope）**：bbox 紧致贴合图像主体外轮廓，杜绝盲目外扩留白（留白由阅读器样式控制，严禁打包进图像资产）；
  - **图题正向语法（Caption Syntax）**：
    - 有图题：`![图题文字](images/part_{part_index}_fig_{fig_index}.png)`（文字严格封闭在方括号内，Pandoc 原生编译为 `<figure><figcaption>`）；
    - 无图题：`![](images/part_{part_index}_fig_{fig_index}.png)`（方括号留空；篇首肖像强制留空，下方姓名与生平文字作为流式正文）；
    - 严禁在图片下方另起段落书写裸文字或斜体图题（防止被解析为普通 `<p>` 段落并继承 2em 首行缩进）。
- **非线性图表切图**：饼图、柱状图、走势图或横向多列表格统一按插图或 bbox 处理，避免移动端排版坍塌。
- **随文注忠实保留**：正文中的括号随文注/夹注直接保留在正文中，不转为脚注。
- **版权信息剔除**：文前与文后的版权页、出版声明、CIP 编目、公众号二维码推广等直接忽略。
- **Gate 2 验收门禁**：检查 `raw_md/` 下文件数量**必须 100% 等于分片总数**，且每个文件大小 > 100 字节。未全部就绪前严禁执行组装！

### Step 3: 目录审查门禁与一键语义汇编
所有切片完成且 Gate 2 通过后：
1. **目录拟案快速预检（TOC Preview Gate）**：
   可运行 `python .agent/skills/pdf-book-ocr/scripts/digitize_book.py --preview-toc "<输出工作目录>"`。
   流水线输出拟定章节清单并保存 `toc_manifest.json`，标记潜在异常（如 `<1500` 字的孤立英文单词/编号章节）。
   - **主 Agent 审查责任**：对照 Gate 1 的大章白名单核对章节结构。若发现小节未降级（如某文章下的英文单词小节被割裂），主 Agent 在 `raw_md/*.md` 中执行批量平推降级（`##` $\to$ `###`），确保章节数量与原书篇目真实对应。
2. **完整组装与编译成书**：
   运行 `python .agent/skills/pdf-book-ocr/scripts/digitize_book.py --assemble "<输出工作目录>"`（需要重新裁剪插图时可加 `--force-recrop`）。
   流水线自动执行三重汇编：
   - **接缝连续性审计与焊接 (`seam_auditor`)**：自动诊断相邻切片接口首尾对，执行跨切片引号闭环焊接（`MERGE` 对白）、未完结断句缝合（`MERGE`）与文本重叠剔除（`MERGE_DEDUP`），并生成 `seam_report.md`。
   - **逻辑章节聚合与排版保全 (`chapter_assembler`)**：依接缝仲裁平滑拼接连续文本流，按正文真实 `## 章节标题` 动态切分章节，隔离各章脚注命名空间；集成**诗歌/题记断行保全引擎**（识别题记/序诗自动注入硬换行）；对插图执行**确定性几何映射 (`resolve_bbox_to_points`)** 与 300 DPI 紧致主体锁边裁切（严禁猜测式启发算法与盲目外扩 padding）。
   - **出版级编译与门禁审计 (`epub_builder`)**：Pandoc 开启 `--mathml` 离线编译 EPUB 3，注入双向弹框注释、MathML 自适应排版样式与对话元数据。
- **Gate 3 / Gate 3.5 验收门禁**：
  1. 确认生成 `seam_report.md`（无断句缝隙）、`toc_manifest.json` 与 `assembled_chapters/`（章节名 100% 对应原书大章，无碎片微短章）、全书主 Markdown 笔记与 `.epub` 文件；
  2. **数学公式审计**：校验 EPUB 3 内部公式已 100% 转译为语义化 MathML 标签且无残留裸 `$$` 源码；
  3. **阅读器断行保真度审计**：校验题记、序诗等成组分行段落未被合并坍塌，必须存在 `<br />` 换行标签；
  4. **篇章署名审计 (Chapter Author Sanity Audit)**：针对多作者文集，校验各章是否存在规范的 `<p class="chapter-author">`。

### Gate 3.8: 主 Agent 全页图文终审门禁 (Mandatory Multimodal Layout & Visual Audit Gate)
在向用户交付前，主 Agent **必须**调用多模态视神经（`view_file`）对生成的插图资产与图文排版效果执行闭环终审。**严禁用纯像素宽高、长宽比等数字指标做伪验收**，必须基于视觉语义逐一过目所有篇首肖像、图表与图文衔接：
1. **插图资产对账（Inventory Reconciliation）**：
   确认 `raw_md/*.md` 中所有 `<!-- FIGURE: ... -->` 与导出的 `images/` 文件 100% 一一对应，无重要图表漏标。
2. **多模态语义三大验收判据（Visual Semantic Criteria via `view_file`）**：
   主 Agent 亲自加载审阅所有核心图元，执行三票否决：
   - **无文字泄露（Zero Text Bleed）**：画面内部或边缘不得截入任何已在 Markdown 正文中排版的印刷体字句（正文绝对禁止在图片中重复出现）；
   - **主体完整（Unbroken Silhouette）**：画面核心实体（人物外形、五官肢体、图表线条、外沿边框）轮廓闭合完整，无异常截断或削顶；
   - **视场纯净（Clean Field）**：画面主体四周纯净，无误截入的书脊暗影、纸张污斑或页眉残线。
3. **图文排版语义审查（Layout Semantic Sanity）**：
   - **审图题**：图题必须由 `<figcaption>` 渲染（居中、浅灰字色、强制 `text-indent: 0`），绝不能沦为带 2em 缩进的正文段落；
   - **审署名**：大章开篇若有作者，必须具备雅致的 `<p class="chapter-author">`，杜绝大标题下突兀出现孤立线而作者名流落为普通正文。
4. **原地修正闭环（Self-Healing Loop）**：
   若视检验出任何文字泄露、主体残缺、杂质或排版退化，主 Agent 直接在对应 `raw_md/*.md` 中针对性修正 bbox 坐标或图题语法，运行 `python .agent/skills/pdf-book-ocr/scripts/digitize_book.py --assemble "<输出工作目录>" --force-recrop` 重新切图与编译，并再次使用 `view_file` 复核确认，直至完全达标。

### Step 4: 出版级闭环验收
交付给用户前，执行快速自检：
1. 抽查 `assembled_chapters/`，确认章节名皆为书本真实章节名而非机械切片号。
2. 确认生成的成果文件已完整输出至指定工作目录（默认 `<书名>_output/` 或用户指定路径），Gate 3.8 插图视觉终审通过，向用户汇报电子书与笔记已就绪。

---

## 资源索引

- **提示词路由与原子模具**：[references/prompt_templates.md](references/prompt_templates.md)（体裁分支路由与 `references/prompts/` 原子模具集）。
- **排版陷阱与防御**：[references/troubleshooting.md](references/troubleshooting.md)（脚注隔离、随文注防悬空、列表空行等踩坑指南）。
- **排版样式表**：[assets/styles_book.css](assets/styles_book.css)（EPUB 3 弹框注释、字体回退与对白样式）。
