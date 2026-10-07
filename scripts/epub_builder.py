#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
epub_builder.py
---------------
Automated EPUB 3 and Obsidian Master Markdown builder:
1. Compiles Markdown chapters into EPUB 3 using Pandoc.
2. Injects classical paper-like CSS styles (styles_book.css).
3. Enhances XHTML:
   - Injects EPUB 3 popup footnote attributes and classes.
   - Tags dialogue and stage-direction classes.
4. Generates an Obsidian Master Note with complete YAML Frontmatter.
"""

import os
import sys
import re
import shutil
import zipfile
import subprocess
import argparse
import datetime

sys.stdout.reconfigure(encoding='utf-8')

def find_pandoc():
    p = shutil.which('pandoc')
    if p: return p
    std_candidates = []
    if os.name == 'nt':
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        std_candidates.extend([
            os.path.join(program_files, 'Pandoc', 'pandoc.exe'),
            os.path.join(program_files_x86, 'Pandoc', 'pandoc.exe'),
            os.path.join(local_appdata, 'Pandoc', 'pandoc.exe'),
        ])
    elif sys.platform == 'darwin':
        std_candidates.extend(['/usr/local/bin/pandoc', '/opt/homebrew/bin/pandoc'])
    elif sys.platform.startswith('linux'):
        std_candidates.extend(['/usr/bin/pandoc', '/usr/local/bin/pandoc'])
    for c in std_candidates:
        if os.path.exists(c): return c
    raise FileNotFoundError("Pandoc executable not found! Please install Pandoc or add to PATH.")

def build_epub_and_master(
    title,
    author,
    chapter_paths,
    cover_image,
    out_epub,
    out_master_md=None,
    translator=None,
    publisher=None,
    css_path=None,
    front_matter_md=None,
    resource_path=None,
    tags=None,
    is_drama=False
):
    pandoc_exe = find_pandoc()
    print(f"[*] Found Pandoc: {pandoc_exe}")
    
    if css_path is None:
        skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        css_path = os.path.join(skill_root, 'assets', 'styles_book.css')
        
    if not os.path.exists(css_path):
        raise FileNotFoundError(f"CSS file not found: {css_path}")

    # 1. Build Master Obsidian Markdown note
    if out_master_md:
        print(f"[*] Building Master Obsidian Markdown: {out_master_md}")
        if tags is None:
            tag_list = ['书籍', '电子书']
        elif isinstance(tags, str):
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        else:
            tag_list = list(tags)
        tag_yaml = "\n".join(f"  - {t}" for t in tag_list)
        header = f"""---
title: {title}
author: "{author}"
{f'translator: "{translator}"' if translator else ''}
date: {datetime.date.today().isoformat()}
tags:
{tag_yaml}
{f'cover: "[[{os.path.basename(cover_image)}]]"' if cover_image else ''}
---

{f'![[{os.path.basename(cover_image)}|400]]' if cover_image else ''}

"""
        with open(out_master_md, 'w', encoding='utf-8') as f_out:
            f_out.write(header)
            if front_matter_md and os.path.exists(front_matter_md):
                with open(front_matter_md, 'r', encoding='utf-8') as f_fm:
                    f_out.write(f_fm.read() + "\n\n---\n\n")
            for cp in chapter_paths:
                with open(cp, 'r', encoding='utf-8') as f_c:
                    f_out.write(f_c.read() + "\n\n---\n\n")
        print(f"[OK] Master note saved: {out_master_md} ({os.path.getsize(out_master_md)} bytes)")

    # 2. Compile EPUB with Pandoc
    raw_epub = out_epub + '.tmp.epub'
    cmd = [
        pandoc_exe,
        '-s',
        '-o', raw_epub,
        '--from=markdown+smart+footnotes',
        '--to=epub3',
        '--mathml',
        '--metadata', f'title={title}',
        '--metadata', f'author={author}',
        '--metadata', 'language=zh-CN',
        '--toc',
        '--toc-depth=1',
        '--split-level=1',
        '--epub-title-page=false'
    ]
    if translator:
        cmd.extend(['--metadata', f'translator={translator}'])
    if publisher:
        cmd.extend(['--metadata', f'publisher={publisher}'])
    if cover_image and os.path.exists(cover_image):
        cmd.extend([f'--epub-cover-image={cover_image}'])
    if css_path and os.path.exists(css_path):
        cmd.extend([f'--css={css_path}'])

    # Resource search paths for images
    res_dirs = []
    if resource_path:
        if isinstance(resource_path, (list, tuple)):
            res_dirs.extend(resource_path)
        else:
            res_dirs.append(resource_path)

    out_dir = os.path.dirname(os.path.abspath(out_epub))
    res_dirs.append(out_dir)
    res_dirs.append(os.path.join(out_dir, "images"))
    if chapter_paths and os.path.exists(chapter_paths[0]):
        ch_dir = os.path.dirname(os.path.abspath(chapter_paths[0]))
        res_dirs.append(ch_dir)
        res_dirs.append(os.path.join(ch_dir, "images"))

    valid_res = []
    for rd in res_dirs:
        if os.path.exists(rd) and rd not in valid_res:
            valid_res.append(rd)
    if valid_res:
        sep = ';' if os.name == 'nt' else ':'
        cmd.extend([f'--resource-path={sep.join(valid_res)}'])

    cmd.extend(chapter_paths)
    
    print(f"[*] Invoking Pandoc to compile EPUB 3 ({len(chapter_paths)} chapters)...")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print("Pandoc Error:", res.stderr)
        raise RuntimeError("Pandoc EPUB compilation failed!")

    print(f"[OK] Pandoc compiled initial EPUB ({os.path.getsize(raw_epub)} bytes)")

    # 3. Post-process EPUB archive
    print("[*] Post-processing EPUB files for popup footnotes & dialogue styling...")
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()

    files_data = {}
    with zipfile.ZipFile(raw_epub, 'r') as zin:
        for name in zin.namelist():
            files_data[name] = zin.read(name)

    # Inject updated CSS
    for name in list(files_data.keys()):
        if name.endswith('.css'):
            files_data[name] = css_content.encode('utf-8')

    # Process XHTML chapters
    def tag_p(m):
        content = m.group(1)
        if any(k in content for k in ['时代', '地点', '登场人物']):
            return f'<p class="play-meta">{content}'
        return f'<p class="dialogue">{content}'

    for name in list(files_data.keys()):
        if name.endswith(('.xhtml', '.html')) and not name.endswith('nav.xhtml'):
            text = files_data[name].decode('utf-8', errors='ignore')
            
            # Transform inline em captions: <p><img ... /> <em>caption</em></p> -> <figure><figcaption>
            text = re.sub(
                r'<p><img\s+src="([^"]+)"\s+alt=""\s*/>\s*<em>(.*?)</em></p>',
                r'<figure>\n<img src="\1" alt="\2" />\n<figcaption>\2</figcaption>\n</figure>',
                text
            )

            if is_drama:
                # Tag dialogue paragraphs
                text = re.sub(r'<p>(<strong>[^*<]+</strong>[：:])', tag_p, text)
                # Split metadata lines (时代/地点) joined by <br /> so each line receives full paragraph indent
                text = re.sub(r'<br\s*/?>\s*(<strong>(?:地点|时代|登场人物)</strong>[：:])', r'</p>\n<p class="play-meta">\1', text)
                # Tag stage direction paragraphs (single-line emphasis paragraphs)
                text = re.sub(r'<p>\s*(<em>.*?</em>)\s*</p>', r'<p class="stage-direction">\1</p>', text)
            
            # Ensure popover class on <aside epub:type="footnote">
            text = re.sub(r'<aside\s+([^>]*epub:type="footnote"[^>]*)>', r'<aside \1 class="footnote-popup">', text)
            # Ensure footnote-ref has noteref class
            text = re.sub(r'<a\s+([^>]*epub:type="noteref"[^>]*)>', r'<a \1 class="noteref">', text)

            # Publishing-grade styling for Epigraph & Poetry sections
            if re.search(r'id="[^"]*题记[^"]*"', text) or re.search(r'<h1[^>]*>.*?题记.*?</h1>', text):
                text = re.sub(r'(<section\s+[^>]*class="[^"]*)(")', r'\1 epigraph-section\2', text)
                text = re.sub(r'<section(?!\s+[^>]*class=)([^>]*)>', r'<section class="epigraph-section"\1>', text)
                text = re.sub(r'(<h1\s+class="[^"]*)(")', r'\1 epigraph-title" style="display:none;\2', text, count=1)
                text = re.sub(r'<h1(?!\s+class=)([^>]*)>', r'<h1 class="epigraph-title" style="display:none;"\1>', text, count=1)
                text = re.sub(r'<p(?!\s+class=)>', r'<p class="poem-stanza">', text)
            
            files_data[name] = text.encode('utf-8')
        elif name.endswith('nav.xhtml'):
            nav_text = files_data[name].decode('utf-8', errors='ignore')
            # Ensure clean TOC text without residual footnote numbers
            nav_text = re.sub(r'<a\s+([^>]*)>([^<]*)<a[^>]*class="footnote-ref"[^>]*>.*?</a>(.*?)</a>', r'<a \1>\2\3</a>', nav_text)
            files_data[name] = nav_text.encode('utf-8')

    # Validate MathML formulas
    total_mathml = sum(files_data[name].decode('utf-8', errors='ignore').count('<math') for name in files_data if name.endswith(('.xhtml', '.html')))
    residual_raw_math = sum(files_data[name].decode('utf-8', errors='ignore').count('$$') for name in files_data if name.endswith(('.xhtml', '.html')))
    if total_mathml > 0:
        print(f"[√] MathML 编译验证成功: 已无损嵌入 {total_mathml} 处 MathML 语义数学公式")
    if residual_raw_math > 0:
        print(f"[!] 警告: 发现 {residual_raw_math} 处残留未闭合的 '$$' 原始公式代码，请排查接缝")

    # Gate 3.5: Validate poetry / epigraph line breaks and image dimensions
    for name, data in files_data.items():
        if name.endswith(('.xhtml', '.html')) and not name.endswith('nav.xhtml'):
            txt = data.decode('utf-8', errors='ignore')
            if any(kw in txt for kw in ('题记', '序诗', '献词')):
                p_tags = re.findall(r'<p[^>]*>(.*?)</p>', txt, flags=re.DOTALL)
                for p_content in p_tags:
                    clean_p = re.sub(r'<[^>]+>', '', p_content).strip()
                    # If epigraph paragraph is multiline text without <br />, warn
                    if len(clean_p) > 50 and '<br' not in p_content and ('\n' in p_content or len(re.findall(r'[\u4e00-\u9fa5]{4,}\s+[\u4e00-\u9fa5]{4,}', clean_p)) > 1):
                        print(f"[!] 警告: 题记/诗歌页面 ({name}) 疑似存在未断行长段落: '{clean_p[:25]}...'")

    # Save final EPUB
    os.makedirs(os.path.dirname(os.path.abspath(out_epub)), exist_ok=True)
    with zipfile.ZipFile(out_epub, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        if 'mimetype' in files_data:
            zout.writestr('mimetype', files_data['mimetype'], compress_type=zipfile.ZIP_STORED)
            del files_data['mimetype']
        else:
            zout.writestr('mimetype', b'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
        for fname, data in files_data.items():
            zout.writestr(fname, data)

    if os.path.exists(raw_epub):
        os.remove(raw_epub)

    print(f"[OK] FINAL EPUB GENERATED: {out_epub} ({os.path.getsize(out_epub)} bytes)")
    return out_epub

def main():
    parser = argparse.ArgumentParser(description="Build EPUB 3 and Master Markdown from assembled chapters")
    parser.add_argument("--title", required=True, help="Book Title")
    parser.add_argument("--author", required=True, help="Book Author")
    parser.add_argument("--chapters", nargs="+", required=True, help="Ordered list of chapter Markdown files")
    parser.add_argument("--cover", default=None, help="Cover image path")
    parser.add_argument("--out-epub", required=True, help="Output EPUB path")
    parser.add_argument("--out-master-md", default=None, help="Output Master Obsidian Markdown path")
    parser.add_argument("--translator", default=None, help="Translator name")
    parser.add_argument("--publisher", default=None, help="Publisher name")
    parser.add_argument("--css", default=None, help="Custom CSS file path")
    parser.add_argument("--front-matter", default=None, help="Front matter markdown file")
    parser.add_argument("--tags", default=None, help="Comma-separated Obsidian tags (default: 书籍,电子书)")
    parser.add_argument("--drama", action="store_true", help="Apply drama dialogue and stage direction formatting")
    args = parser.parse_args()

    build_epub_and_master(
        title=args.title,
        author=args.author,
        chapter_paths=args.chapters,
        cover_image=args.cover,
        out_epub=args.out_epub,
        out_master_md=args.out_master_md,
        translator=args.translator,
        publisher=args.publisher,
        css_path=args.css,
        front_matter_md=args.front_matter,
        tags=args.tags,
        is_drama=args.drama
    )

if __name__ == "__main__":
    main()
