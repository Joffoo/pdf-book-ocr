# PDF Book OCR (出版级图书数字化与 EPUB 3 排版引擎)

> **基于多模态 AI 智能体的大师级长篇图书数字化、语义重构与流式排版引擎。**  
> **Publication-grade PDF-to-EPUB 3 & Obsidian digitizer powered by Multimodal AI Agents.**

<p align="center">
  <a href="#简体中文">简体中文</a> •
  <a href="#english">English</a> •
  <a href="#license">License</a>
</p>

---

<a name="简体中文"></a>
## 简体中文

`pdf-book-ocr` 是一款面向长篇图书（100~500+ 页，扫描件或数字版 PDF）的高精度数字化与排版工具，能够将复杂书籍一键转录为出版级 **EPUB 3** 电子书与典藏版 **Obsidian Markdown** 文档。

工具采用“多模态 AI 理解 + 本地确定性工程”的协同设计，在确保全书文字与结构高度精确的同时，完整还原图书的经典排版韵味、高清插图与双向学术注释。

### 🌟 核心特性

1. **多模态理解与工程执行协同**
   - **大模型负责语义理解与版式感知**：章节标题层级、篇首署名排版、插图区域检测与版权元数据归纳。
   - **本地脚本负责精密工程执行**：300 DPI 高清无损裁图、跨分片接缝连续性修复、脚注独立命名空间映射与 EPUB 3 容器封装。
2. **统一高清插图提取管线**
   - 全书插图统一标注协议：`<!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->`。
   - 自动按坐标从原始 PDF 中光栅化裁切 300 DPI 锁边图像，无论是印刷照片、手绘线描还是信息图表均可高清呈现。
   - 图文正交互斥，杜绝录入正文与插图文字重复。
3. **接缝连续性审计与缝合（`seam_auditor`）**
   - 自动化跨分片接缝平滑缝合：智能识别分片边缘的断句、跨切片引号闭合与重叠行消除，确保长篇连贯阅读体验。
4. **中英双态智能折行排版**
   - 智能识别断行特征：中文行尾自动无缝接排，西文字词换行自动保留空格，同时保护 Markdown 链接与脚注语法不受破坏。
5. **经典书卷排版与 MathML 公式支持**
   - 内置经典排版样式表（[`styles_book.css`](assets/styles_book.css)），支持楷体章节作者卡、优雅分割线与居中独立题记。
   - 完美支持 EPUB 3 双向弹出式气泡脚注（`epub:type="noteref"` / `<aside epub:type="footnote">`）。
   - LaTeX 数学公式编译为 W3C 标准 MathML，自适应各大主流阅读器、夜间模式与墨水屏设备。
6. **目录审查门禁（TOC Review Gate）**
   - 支持通过 `--preview-toc` 预检全书大纲层级与字数分布，生成清单供快速核验，确保章节划分清晰准确。

---

### 🏗 统一处理管线

```
[原始 PDF 图书 (扫描版或数字文字版)]
       │
       ▼ (Step 1: 预处理、切片规划与全局目录提取)
 digitize_book.py ──> 提取封面、切片为 10~15 页微型 PDF、建立任务单
       │              (生成 slice_plan.json 与 subagent_jobs.json)
       ▼
[Step 2: Subagent 批次滚动转写/清洗] ──> 注入大章白名单约束，逐片落盘 raw_md/*.md
       │
       ▼ (Step 3: 语义汇编与目录审查门禁)
 digitize_book.py --preview-toc / --assemble
       ├── seam_auditor.py: 校验首尾断缝与段落连续性，焊接未闭合对白 (seam_report.md)
       ├── toc_manifest.json: 主 Agent 对照白名单核验目录拟案 (TOC Review Gate)
       ├── chapter_assembler.py: 按真实 ## 大章动态聚合、隔离章节脚注命名空间
       └── epub_builder.py: Pandoc 离线编译 EPUB 3 + 注入双向弹框注释与 MathML
       │
       ▼ (Step 4: 出厂交付)
 《书名》.epub + 《书名》.md + images/ (产出至输出工作目录)
```

---

### 📦 运行依赖与安装

#### 环境要求
- **Python**: 3.10 及以上
- **Pandoc**: 3.0 及以上 ([Pandoc 官网安装指引](https://pandoc.org/installing.html))

```bash
# 1. 克隆代码仓库
git clone https://github.com/Joffoo/pdf-book-ocr.git
cd pdf-book-ocr

# 2. 安装 Python 核心依赖
pip install -r requirements.txt

# 3. 一键环境自检 (Doctor Mode)
python scripts/digitize_book.py --doctor
```

---

### 🚀 命令行指南 (`digitize_book.py`)

| 命令行参数 | 参数类型 | 功能描述 | 默认值 |
| :--- | :--- | :--- | :---: |
| `pdf` | 位置参数 | 待数字化的 PDF 图书文件路径 | 必需 |
| `--doctor` | 标记 | 自动诊断 Python、PyMuPDF、BS4 及 Pandoc 环境完整性 | `False` |
| `--preview-toc DIR` | 路径 | 预览指定工作目录下的章节划分与字数（TOC 审查门禁） | `None` |
| `--assemble DIR` | 路径 | 完整汇编指定工作目录下的分片并编译最终成果 | `None` |
| `--drama` | 标记 | 启用剧本对白（`p.dialogue`）与舞台动作专用排版规则 | `False` |
| `--force-recrop` | 标记 | 汇编时强制重新裁切并锁边正文全部插图 | `False` |
| `--status DIR` | 路径 | 查看工作目录中分片 Markdown 的转写与落盘进度 | `None` |
| `--title TITLE` | 文本 | 自定义图书标题（默认根据文件名与版本词保护清洗） | 自动识别 |
| `--author AUTHOR` | 文本 | 自定义作者署名（优先于文件名提取） | 自动识别 |
| `--out-dir DIR` | 路径 | 自定义成果物输出目录 | `<书名>_output` |
| `--chunk-size N` | 整数 | 单个物理分片的页数 | `15` |
| `--force-scan` | 标记 | 强制按图像扫描版切分，跳过文字层草稿提取 | `False` |

---

### 📂 目录结构与模块说明

```
pdf-book-ocr/
├── README.md                      # 双语项目说明文档 (Bilingual Documentation)
├── SKILL.md                       # Antigravity / Claude Agent 核心规约
├── requirements.txt               # Python 依赖清单
├── LICENSE                        # MIT 开源许可证
├── assets/
│   └── styles_book.css            # 出版级 EPUB 3 经典书卷排版样式表
├── references/
│   ├── prompt_templates.md        # 体裁分支路由与提示词索引
│   ├── troubleshooting.md         # 21 个经典排版陷阱与防御全景指南
│   └── prompts/                   # 原子提示词模具目录
│       ├── prose.txt              # 散文/小说/通用非虚构正向模具
│       ├── academic.txt           # 学术专著/论文集模具
│       ├── drama.txt              # 戏剧/剧本文学专用模具
│       └── digital.txt            # 原生数字文字版清洗模具
└── scripts/
    ├── digitize_book.py           # 一键流水线主控脚本
    ├── pdf_analyzer.py            # 预检与自适应切片规划器
    ├── pdf_slicer.py              # 物理切片引擎
    ├── seam_auditor.py            # 接缝连续性与断句审计引擎
    ├── chapter_assembler.py       # 逻辑章节聚合与插图锁边裁剪引擎
    ├── epub_builder.py            # EPUB 3 离线编译与双向气泡注释注入器
    └── vector_figure_extractor.py # 独立矢量图表批量提取辅助工具
```

---

<a name="english"></a>
## English

`pdf-book-ocr` is a high-precision digitizer and typesetting engine designed for long-form publications (100–500+ pages, scanned prints or digital PDFs). It converts complex books into publication-grade **EPUB 3** e-books and archival **Obsidian Markdown** vaults.

By combining multimodal AI vision with deterministic engineering, `pdf-book-ocr` ensures structural fidelity, classical typographic aesthetics, crisp figure reproduction, and native academic footnotes.

### 🌟 Key Features

1. **Multimodal AI & Deterministic Engineering**
   - **Semantic layout vision by AI**: Chapter hierarchy classification, author epigraph styling, figure bounding-box detection, and front-matter parsing.
   - **Precision engineering by Code**: 300 DPI lossless rasterization, cross-slice seam healing, footnote namespace isolation, and EPUB 3 container packaging.
2. **Unified High-Resolution Figure Pipeline**
   - Universal figure protocol across all genres: `<!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->`.
   - Deterministic 300 DPI high-resolution cropping directly from the source PDF, ensuring crisp rendering for photographs, line art, and complex vector charts.
   - Strict figure-text orthogonality prevents duplicated text between prose and images.
3. **Seam Continuity & Sentence Healing (`seam_auditor`)**
   - Automated junction inspection across batch slices: heals mid-sentence breaks, sutures unclosed quotes, and deduplicates overlapping lines.
4. **Language-Aware Typography**
   - Intelligent line-wrap normalization: CJK characters merge seamlessly without extraneous spaces, while Latin/ASCII words preserve word spacing. Protects Markdown links and footnotes from regex corruption.
5. **Classical Typography & Semantic MathML**
   - Built-in classical typographic theme ([`styles_book.css`](assets/styles_book.css)) with Kaiti chapter-author cards, elegant dividers, and centered epigraphs.
   - Native EPUB 3 popup footnote support (`epub:type="noteref"` / `<aside epub:type="footnote">`).
   - Compiles LaTeX formulas into W3C-standard MathML, natively responsive across e-readers, dark mode, and E-Ink screens.
6. **TOC Review Gate**
   - Pre-flight chapter inspection via `--preview-toc`, exporting `toc_manifest.json` with word counts to verify structural hierarchy before compilation.

---

### 🏗 Architecture & Pipeline

```
[Source PDF (Scanned Print or Digital PDF)]
       │
       ▼ (Step 1: Preflight & Slice Planning)
 digitize_book.py ──> Extracts cover, plans 10~15 page slices, extracts Global TOC whitelist
       │              (Generates slice_plan.json & subagent_jobs.json)
       ▼
[Step 2: Subagent Rolling Batches] ──> Positive prompt contracts, transcribes to raw_md/*.md
       │
       ▼ (Step 3: Semantic Assembly & TOC Review Gate)
 digitize_book.py --preview-toc / --assemble
       ├── seam_auditor.py: Junction continuity audit & quotation healing (seam_report.md)
       ├── toc_manifest.json: Structure verification against Global TOC whitelist
       ├── chapter_assembler.py: Dynamic H2 aggregation & footnote namespace isolation
       └── epub_builder.py: Pandoc compilation to EPUB 3 + popup footnotes + MathML
       │
       ▼ (Step 4: Delivery)
 《Title》.epub + 《Title》.md + images/ (Output Directory)
```

---

### 📦 Installation

#### Prerequisites
- **Python**: 3.10 or higher
- **Pandoc**: 3.0 or higher ([Installation Guide](https://pandoc.org/installing.html))

```bash
# 1. Clone repository
git clone https://github.com/Joffoo/pdf-book-ocr.git
cd pdf-book-ocr

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify environment
python scripts/digitize_book.py --doctor
```

---

### 🚀 Usage & CLI Reference

#### 1. Plan & Slice
```bash
python scripts/digitize_book.py "book.pdf"
```
Automatically extracts the cover, slices the book into manageable 10–15 page chunks in `parts/`, and generates `subagent_jobs.json`.

#### 2. Transcribe Slices
Dispatch chunks to AI agents (e.g. Gemini, Claude, GPT-4o) using prompt templates in `references/prompts/`:
- `prose.txt`: General prose, fiction, non-fiction
- `academic.txt`: Scholarly monographs with formulas & citations
- `drama.txt`: Scripts, dialogues, stage directions
- `digital.txt`: Fast semantic cleanup for digital PDFs

Each slice transcribes to `raw_md/part_XX.md`.

#### 3. Preview TOC (Optional Review Gate)
```bash
python scripts/digitize_book.py --preview-toc "book_output"
```
Generates `toc_manifest.json` and prints the chapter tree to ensure sub-sections have not been erroneously promoted.

#### 4. Assemble & Compile
```bash
# General prose / academic monograph
python scripts/digitize_book.py --assemble "book_output"

# Drama / play script
python scripts/digitize_book.py --assemble "book_output" --drama

# Force re-cropping of figures
python scripts/digitize_book.py --assemble "book_output" --force-recrop
```

---

<a name="license"></a>
## 📄 License

This project is licensed under the [MIT License](LICENSE).  
本项目遵循 [MIT License](LICENSE) 开源协议。
