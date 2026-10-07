# PDF Book OCR (出版级图书数字化与 EPUB 3 排版引擎)

> **Publication-grade PDF-to-EPUB 3 & Obsidian digitizer powered by Multimodal AI Agents.**  
> **基于多模态 AI 智能体的大师级长篇图书数字化、语义重构与流式排版引擎。**

<p align="center">
  <a href="#english">English</a> •
  <a href="#简体中文">简体中文</a> •
  <a href="#license">License</a>
</p>

---

<a name="english"></a>
## English

`pdf-book-ocr` converts long-form PDF books (100–500+ pages, scanned prints or digital PDFs) into publication-grade **EPUB 3** e-books and archival **Obsidian Markdown** vaults.

Designed around a **Single Source of Truth (SSOT)** and an **Agent-Native** division of responsibility, it avoids heuristic guessing, brittle keyword enumeration, and hardcoded development paths.

### 🌟 Key Features

1. **Agent-Native Architecture (Cognition vs. Execution)**
   - **Semantic decisions by Agents**: Subagents visually classify headings, portrait layouts, captions, and ignore barcode/CIP pages based on positive prompts.
   - **Deterministic execution by Code**: PyMuPDF and Pandoc handle 300 DPI rasterization, footnote namespace remapping, MathML formulas, and zip packaging without guessing semantics.
2. **Unified Single-Source Figure Pipeline**
   - Universal figure protocol `<!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->` across all genres.
   - Deterministic 300 DPI high-resolution cropping with paper-margin snapping. Whether the source is a scanned photograph, an archival painting, or an Excel/Matplotlib vector chart, PyMuPDF renders it losslessly.
   - Strict figure-text orthogonality prevents duplicate text in images.
3. **Seam Continuity & Sentence Healing (`seam_auditor`)**
   - Automatically inspects the junction pairs between consecutive chunks.
   - State-machine healing: closes cross-slice quotation marks (`MERGE`), sutures mid-sentence breaks (`MERGE`), and deduplicates overlapping OCR text (`MERGE_DEDUP`).
   - Recursively peels nested closing bracket stacks (`。”）`) to prevent false joins.
4. **Language-Aware Typography (`smart_join_lines`)**
   - Distinguishes Latin/ASCII line wraps (preserving spaces) from CJK characters (merging seamlessly without spurious spaces).
   - Protects Markdown links and footnotes from regex corruption.
5. **EPUB 3 Classical Styling & MathML Support**
   - Built-in classical typographic theme ([`styles_book.css`](assets/styles_book.css)) with Kaiti chapter-author styles, elegant dividers, and centered epigraph stanzas.
   - Full EPUB 3 popup footnote support (`epub:type="noteref"` / `<aside epub:type="footnote">`).
   - Compiles inline and block LaTeX formulas to W3C-compliant semantic MathML with offline compatibility across Apple Books, WeChat Read, KOReader, and Kindle.
6. **Transparent Review Gates (Zero Silent Deletion)**
   - Pre-flight TOC manifest (`--preview-toc`) exports `toc_manifest.json` with character counts and anomaly tags.
   - Copyright or front-matter pages trigger review warnings instead of silent data drops.

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

### 🚀 Usage

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

<a name="简体中文"></a>
## 简体中文

`pdf-book-ocr` 是一款面向公开发行图书（100~500+ 页，扫描件或数字版）的高精度数字化工具，能够将长篇文献一键转录为出版级 **EPUB 3** 电子书与典藏版 **Obsidian 笔记**。

本项目贯彻**单一真理源（SSOT）**与 **Agent-Native** 架构，彻底剥离针对单本书打补丁的脆弱正则、年份白名单与平台私有路径，具备高通用性、零误杀与零机器特异性。

### 🌟 核心特性

1. **智能体原生架构（认知与执行明确分工）**
   - **认知归智能体**：篇章标题分级、篇首肖像与生平、插图边界、文前文后版权过滤等认知任务，由正向 Prompt 契约约束 Agent 决策。
   - **执行归代码**：300 DPI 物理光栅化裁剪、脚注命名空间隔离映射、MathML 公式转译、EPUB 容器封装由确定性 Python 脚本执行，拒绝用代码盲猜人类语义。
2. **单轨统一插图引擎（Unified Figure Pipeline）**
   - 全体裁通用标注契约：`<!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->`。
   - 300 DPI 紧致锁边：无论是印刷照片、手绘线描，还是 Excel/Matplotlib 渲染的非图像矢量信息图，PyMuPDF 直接按坐标无损光栅化切图，杜绝移动端宽表坍塌。
   - 图文正交互斥律：正文已录入文本与插图 `bbox` 物理区域严格互斥，杜绝文字在图片中二次泄露。
3. **出版级接缝审计与语义闭环（`seam_auditor`）**
   - 自动提取相邻切片交界接口并进行语义拓扑诊断。
   - 状态机平滑缝合：跨切片对白引号闭环焊接（`MERGE`）、未完结断句自动缝合（`MERGE`）、文本重叠自动剔除（`MERGE_DEDUP`）。
   - 递归剥离末尾多层连续闭合符号堆栈（如 `。”）`），精准探测内层真实标点，杜绝误判假断缝。
4. **语言拓扑自适应缝合（`smart_join_lines`）**
   - 自动识别断行分界特征：分界处两侧为拉丁/ASCII 字符（如英文单词、逗号）时保留空格，任意一侧为 CJK 汉字或标点时无缝拼接，彻底消除“英文粘连吃空格”缺陷。
   - 标点全角规约具备负向先行断言，严格保护 Markdown 超链接语法。
5. **经典书卷排版与 MathML 原生支持**
   - 内置经典纸书排版样式表（[`styles_book.css`](assets/styles_book.css)），支持楷体章节作者署名卡、优雅分割线与居中独立题记/序诗。
   - 完美适配 EPUB 3 双向弹出式气泡脚注（`epub:type="noteref"` / `<aside epub:type="footnote">`）。
   - Pandoc 原生转译 TeX 为语义化 MathML，离线自适应夜间模式与墨水屏设备。
6. **透明化审查门禁（零静默删除）**
   - 支持 `--preview-toc` 预检大纲与篇幅体量，输出 `toc_manifest.json`。
   - 版权页与疑似短章仅作 Warning 预警呈现，代码坚守数据中立，绝不静默删除用户章节。

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

<a name="license"></a>
## 📄 License

This project is licensed under the [MIT License](LICENSE).
本项目遵循 [MIT License](LICENSE) 开源协议。
