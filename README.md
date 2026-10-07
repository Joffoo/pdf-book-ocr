# PDF Book OCR (PDF 图书数字化与 EPUB 3 排版引擎)

> 基于多模态 AI 与本地脚本的长篇 PDF 图书数字化与 EPUB 3 排版工具。  
> Convert PDF books into EPUB 3 e-books and Obsidian Markdown notes.

<p align="center">
  <a href="#简体中文">简体中文</a> •
  <a href="#english">English</a> •
  <a href="#license">License</a>
</p>

---

<a name="简体中文"></a>
## 简体中文

`pdf-book-ocr` 是一款面向长篇图书（100~500+ 页，扫描件或数字版 PDF）的数字化与排版工具，能够将书籍转录为 **EPUB 3** 电子书与 **Obsidian Markdown** 笔记。

工具结合多模态大模型与本地处理脚本，支持提取 300 DPI 高清插图、转换双向气泡注释，并保留书籍的版式结构。

### 🌟 核心特性

1. **多模态理解与本地脚本协同**
   - **大模型负责版式感知**：识别章节层级、篇首署名、插图区域与版权元数据。
   - **本地脚本负责文件处理**：执行 300 DPI 插图裁剪、跨分片接缝修复、隔离脚注命名空间并打包 EPUB 3。
2. **统一插图提取管线**
   - 全书插图统一标注协议：`<!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->`。
   - 按坐标从原始 PDF 中直接裁切 300 DPI 图像，支持照片、线描插画与矢量图表。
   - 裁图区域与正文文本互斥，避免正文与插图文字重复。
3. **分片接缝连续性修复（`seam_auditor`）**
   - 自动检测并缝合切片边缘的断句、未闭合引号与重叠行，保障长篇文本连贯。
4. **中西文混排折行优化**
   - 智能识别断行特征：中文行尾自动无缝接排，西文字词换行保留空格，同时保护 Markdown 链接与脚注标记。
5. **排版样式与 MathML 公式支持**
   - 内置排版样式表（[`styles_book.css`](assets/styles_book.css)），支持楷体章节作者卡、分割线与居中题记。
   - 支持 EPUB 3 双向弹出式气泡脚注（`epub:type="noteref"` / `<aside epub:type="footnote">`）。
   - 将 LaTeX 数学公式编译为 W3C 标准 MathML，适配多端阅读器。
6. **目录大纲预检（TOC Review Gate）**
   - 提供 `--preview-toc` 预检全书大纲层级与字数分布，方便在编译前核验章节划分。

---

### 🏗 处理管线

```
[原始 PDF 图书 (扫描版或数字文字版)]
       │
       ▼ (Step 1: 预处理与切片规划)
 digitize_book.py ──> 提取封面、切片为 10~15 页微型 PDF、建立任务单
       │              (生成 slice_plan.json 与 subagent_jobs.json)
       ▼
[Step 2: Subagent 批次转写/清洗] ──> 注入大章约束，逐片保存 raw_md/*.md
       │
       ▼ (Step 3: 汇编与目录预检)
 digitize_book.py --preview-toc / --assemble
       ├── seam_auditor.py: 校验首尾断缝与段落连续性 (seam_report.md)
       ├── toc_manifest.json: 核验目录结构 (TOC Review Gate)
       ├── chapter_assembler.py: 按 ## 章节聚合内容、隔离章节脚注命名空间
       └── epub_builder.py: Pandoc 编译 EPUB 3 + 注入双向气泡注释与 MathML
       │
       ▼ (Step 4: 生成输出)
 《书名》.epub + 《书名》.md + images/ (产出至输出工作目录)
```

---

### 📦 运行环境与安装

#### 环境要求
- **Python**: 3.10 及以上
- **Pandoc**: 3.0 及以上 ([Pandoc 官网安装指引](https://pandoc.org/installing.html))

```bash
# 1. 克隆代码仓库
git clone https://github.com/Joffoo/pdf-book-ocr.git
cd pdf-book-ocr

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 环境自检 (Doctor Mode)
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
| `--drama` | 标记 | 启用剧本对白（`p.dialogue`）与舞台动作排版规则 | `False` |
| `--force-recrop` | 标记 | 汇编时强制重新裁切正文插图 | `False` |
| `--status DIR` | 路径 | 查看工作目录中分片 Markdown 的转写进度 | `None` |
| `--title TITLE` | 文本 | 自定义图书标题（默认根据文件名清洗） | 自动识别 |
| `--author AUTHOR` | 文本 | 自定义作者署名（优先于文件名提取） | 自动识别 |
| `--out-dir DIR` | 路径 | 自定义输出目录 | `<书名>_output` |
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
│   └── styles_book.css            # EPUB 3 排版样式表
├── references/
│   ├── prompt_templates.md        # 体裁分支路由与提示词索引
│   ├── troubleshooting.md         # 常见排版问题与处理建议
│   └── prompts/                   # 提示词模具目录
│       ├── prose.txt              # 散文/小说/通用非虚构模具
│       ├── academic.txt           # 学术专著/论文集模具
│       ├── drama.txt              # 戏剧/剧本文学专用模具
│       └── digital.txt            # 原生数字文字版清洗模具
└── scripts/
    ├── digitize_book.py           # 一键流水线主控脚本
    ├── pdf_analyzer.py            # 预检与切片规划器
    ├── pdf_slicer.py              # 物理切片引擎
    ├── seam_auditor.py            # 接缝连续性与断句审计引擎
    ├── chapter_assembler.py       # 逻辑章节聚合与插图裁剪引擎
    ├── epub_builder.py            # EPUB 3 编译与双向气泡注释注入器
    └── vector_figure_extractor.py # 矢量图表批量提取辅助工具
```

---

<a name="english"></a>
## English

`pdf-book-ocr` is a digitizer and typesetting tool designed for long-form publications (100–500+ pages, scanned prints or digital PDFs). It converts books into **EPUB 3** e-books and **Obsidian Markdown** notes.

By combining multimodal AI with deterministic Python scripts, it extracts 300 DPI figures, maps two-way popup footnotes, and preserves structural layouts.

### 🌟 Key Features

1. **Multimodal AI & Script Coordination**
   - **AI for layout perception**: Recognizes chapter hierarchy, author bylines, figure bounding boxes, and front-matter metadata.
   - **Scripts for file processing**: Handles 300 DPI image cropping, seam healing across slices, footnote namespace isolation, and EPUB 3 compilation.
2. **Unified Figure Pipeline**
   - Universal figure protocol across genres: `<!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->`.
   - Crops 300 DPI images directly from the source PDF for photos, line drawings, and vector charts.
   - Orthogonal figure-text regions prevent duplicated text between images and prose.
3. **Cross-Chunk Seam Auditing (`seam_auditor`)**
   - Automatically repairs junction edges: sutures mid-sentence breaks, closes unclosed quotation marks, and deduplicates overlapping lines.
4. **Language-Aware Typography**
   - Distinguishes CJK characters (seamless joining) from Latin/ASCII text (preserving space). Protects Markdown links and footnotes from syntax damage.
5. **EPUB 3 Typography & MathML Support**
   - Built-in stylesheet ([`styles_book.css`](assets/styles_book.css)) supporting author bylines, dividers, and centered epigraphs.
   - Full EPUB 3 popup footnote support (`epub:type="noteref"` / `<aside epub:type="footnote">`).
   - Compiles LaTeX formulas into W3C-standard MathML for cross-device readability.
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
       ▼ (Step 4: Final Output)
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
