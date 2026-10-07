#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chapter_assembler.py
--------------------
Assembles slice Markdown files into clean, publishing-grade chapter files:
1. Merges sequential sub-part slices into full chapters.
2. Isolates footnotes with chapter namespace prefixes ([^c01_1]...) to avoid EPUB collisions.
3. Automatically fixes common Markdown formatting issues:
   - Injects missing blank lines before list blocks (prevents list collapse).
   - Normalizes dialogue blocks (prevents dialogue cramming & indent defects).
   - Normalizes stage directions and metadata.
   - Strips code fencing and trailing soft-break spaces.
"""

import os
import sys
import re
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8')

def resolve_bbox_to_points(bbox, rect):
    """
    Resolves bbox [ymin, xmin, ymax, xmax] (0~1000 normalized permille) to PDF points (x0, y0, x1, y1).
    Unified Single Source of Truth (SSOT): All bbox coordinates are in 0~1000 permille.
    """
    ymin, xmin, ymax, xmax = [float(v) for v in bbox]
    x0 = (xmin / 1000.0) * rect.width
    y0 = (ymin / 1000.0) * rect.height
    x1 = (xmax / 1000.0) * rect.width
    y1 = (ymax / 1000.0) * rect.height
    return x0, y0, x1, y1

def crop_and_snap_figure(doc, page_no, bbox_norm, out_path):
    """
    Crop figure from slice PDF page using normalized bbox [ymin, xmin, ymax, xmax] (0~1000).
    Renders in 300 DPI high resolution.
    Safely trims pure paper margins without destructive frame snapping or gutter slicing.
    """
    import fitz
    import numpy as np
    from PIL import Image

    if page_no < 0 or page_no >= len(doc):
        print(f"[-] Warning: page_no {page_no} out of bounds (0..{len(doc)-1})")
        return False

    page = doc[page_no]
    rect = page.rect
    x0, y0, x1, y1 = resolve_bbox_to_points(bbox_norm, rect)

    crop_rect = fitz.Rect(x0, y0, x1, y1)
    mat = fitz.Matrix(300 / 72, 300 / 72)
    pix = page.get_pixmap(matrix=mat, clip=crop_rect, alpha=False)

    try:
        samples = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        gray = np.mean(samples[:, :, :3], axis=2)

        # Trims pure white paper margin (>240 across whole row/col) to tight subject envelope
        row_min = np.min(gray, axis=1)
        col_min = np.min(gray, axis=0)

        ink_rows = np.where(row_min < 240)[0]
        ink_cols = np.where(col_min < 240)[0]

        if len(ink_rows) > 0 and len(ink_cols) > 0:
            margin = 1  # 1px anti-aliasing guard at 300 DPI (< 0.25 pt)
            top = max(0, int(ink_rows[0]) - margin)
            bottom = min(pix.h - 1, int(ink_rows[-1]) + margin)
            left = max(0, int(ink_cols[0]) - margin)
            right = min(pix.w - 1, int(ink_cols[-1]) + margin)

            img = Image.frombytes('RGB', [pix.w, pix.h], pix.samples)
            cropped_img = img.crop((left, top, right + 1, bottom + 1))
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            cropped_img.save(out_path)
            return True
    except Exception as e:
        print(f"[-] Notice: safe trim fallback to raw crop: {e}")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    pix.save(out_path)
    return True

def crop_figures_for_work_dir(work_dir, force_recrop=False):
    """
    Scans raw_md/*.md for figure annotations:
    <!-- FIGURE: page=N bbox=[ymin, xmin, ymax, xmax] -->
    ![...](images/...)
    Extracts high-res cropped images from parts/*.pdf into images/.
    """
    import fitz

    raw_md_dir = os.path.join(work_dir, "raw_md")
    parts_dir = os.path.join(work_dir, "parts")
    images_dir = os.path.join(work_dir, "images")

    if not os.path.exists(raw_md_dir):
        return 0

    os.makedirs(images_dir, exist_ok=True)
    fig_pattern = re.compile(
        r'<!--\s*FIGURE:\s*(?:page=(\d+)\s+)?bbox=\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\](?:\s+caption="([^"]*)")?\s*-->\s*\n\s*!\[([^\]]*)\]\((images/[^)]+)\)',
        re.IGNORECASE
    )

    total_cropped = 0
    for fname in os.listdir(raw_md_dir):
        if not fname.endswith('.md'):
            continue
        md_path = os.path.join(raw_md_dir, fname)
        base_stem = os.path.splitext(fname)[0]
        slice_pdf = os.path.join(parts_dir, f"{base_stem}.pdf")

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        matches = list(fig_pattern.finditer(content))
        if not matches:
            continue

        if not os.path.exists(slice_pdf):
            print(f"[-] Warning: slice PDF not found for figure extraction: {slice_pdf}")
            continue

        doc = fitz.open(slice_pdf)
        for m in matches:
            page_str = m.group(1)
            ymin = int(m.group(2))
            xmin = int(m.group(3))
            ymax = int(m.group(4))
            xmax = int(m.group(5))
            img_rel_path = m.group(8)

            page_no = max(0, int(page_str) - 1) if page_str else 0
            if page_no >= len(doc):
                page_no = 0

            target_img_path = os.path.join(work_dir, img_rel_path)
            if force_recrop or not os.path.exists(target_img_path):
                ok = crop_and_snap_figure(doc, page_no, (ymin, xmin, ymax, xmax), target_img_path)
                if ok:
                    total_cropped += 1
        doc.close()

    if total_cropped > 0:
        print(f"[OK] Extracted and cropped {total_cropped} figures into {images_dir}")
    return total_cropped

def normalize_text_layout(text, is_drama=False):
    """Clean and normalize markdown layout for publishing."""
    # Strip accidental markdown code blocks
    text = re.sub(r'^```markdown\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text.strip(), flags=re.MULTILINE)
    
    # 1. Fix unspaced lists: ensure blank line before list if preceded by text
    # Supports both unordered (-, *) and ordered (1., 2.) list markers
    text = re.sub(r'([^\n])\n((?:[-*+]|\d+[\.\)])\s+[^\n]+)', r'\1\n\n\2', text)
    # Ensure blank line after list block ends
    text = re.sub(r'(\n(?:[-*+]|\d+[\.\)])\s+[^\n]+)\n+([^-\d*+\n\s])', r'\1\n\n\2', text)
    
    if is_drama:
        # Drama specific normalization
        text = text.replace(r'\*其余剧中只提及名字的人物', '*其余剧中只提及名字的人物')
        text = re.sub(r'(\*\*时代\*\*：[^\n]+)\n+(\*\*地点\*\*：[^\n]+)', r'\1  \n\2', text)
        text = re.sub(r'(\*\*地点\*\*：[^\n]+)\n+(\*\*登场人物\*\*：)', r'\1\n\n\2', text)
        text = re.sub(r'(\*\*登场人物\*\*：)\n+([-*]\s+)', r'\1\n\n\2', text)
        
        lines = text.splitlines()
        new_lines = []
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith('>') or re.match(r'^\s*\[\^[^\]]+\]:', line) or re.match(r'^\s*[-*]\s+', line):
                new_lines.append(line)
                continue
            if re.match(r'^\s*\*\*(时代|地点|登场人物)\*\*：', line):
                new_lines.append(line)
                if '登场人物' in line:
                    new_lines.append('')
                continue
            if re.match(r'^\s*\*\*[^*]+\*\*：', line):
                clean_line = re.sub(r'\s+$', '', line)
                new_lines.append(clean_line)
                new_lines.append('')
                continue
            if re.match(r'^\s*\*[^*]+\*\s*$', trimmed):
                clean_line = re.sub(r'\s+$', '', trimmed)
                new_lines.append(clean_line)
                new_lines.append('')
                continue
            new_lines.append(line)
        text = '\n'.join(new_lines)
    else:
        # Prose: eliminate trailing double spaces that cause accidental <br /> inside paragraphs
        lines = text.splitlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith('>'):
                new_lines.append(line)  # keep poetry / song lines inside blockquotes
            else:
                new_lines.append(re.sub(r'  +$', '', line))
        text = '\n'.join(new_lines)

    # Punctuation normalization: convert ASCII punctuation between Chinese characters to full-width
    text = re.sub(r'([\u4e00-\u9fa5]),([\u4e00-\u9fa5\s])', r'\1，\2', text)
    text = re.sub(r'([\u4e00-\u9fa5]);([\u4e00-\u9fa5\s])', r'\1；\2', text)
    text = re.sub(r'([\u4e00-\u9fa5]):([\u4e00-\u9fa5])', r'\1：\2', text)
    text = re.sub(r'([\u4e00-\u9fa5])\(([\d\u4e00-\u9fa5]+)\)(?!\])', r'\1（\2）', text)

    # Normalize spacing around images: ensure blank lines before and after image blocks
    text = re.sub(r'([^\n])\n(!\[[^\]]*\]\([^)]+\))', r'\1\n\n\2', text)
    text = re.sub(r'(!\[[^\]]*\]\([^)]+\))\n+([^\n*])', r'\1\n\n\2', text)

    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def smart_join_lines(lines):
    """
    Language-aware line merger:
    If boundary between lines consists of non-CJK (e.g. Latin/ASCII text), insert a space
    (unless trailing hyphen).
    If either side is CJK, merge seamlessly without space.
    """
    if not lines:
        return ""
    result = lines[0]
    for nxt in lines[1:]:
        if not result:
            result = nxt
            continue
        if not nxt:
            continue
        is_cjk_prev = bool(re.search(r'[\u4e00-\u9fa5\u3000-\u303f\uff01-\uff5e]$', result))
        is_cjk_next = bool(re.search(r'^[\u4e00-\u9fa5\u3000-\u303f\uff01-\uff5e]', nxt))
        if not is_cjk_prev and not is_cjk_next:
            sep = "" if result.endswith('-') else " "
        else:
            sep = ""
        result = result + sep + nxt
    return result

def preserve_poetic_line_breaks(text, chapter_title=""):
    """
    Auto-detect and preserve poetic/epigraph line breaks with trailing backslashes `\\`.
    Prevents CommonMark/Pandoc from collapsing intentional stanzas into a single run-on <p>.
    For normal prose chapters, strips trailing `\\` from narrative prose to ensure proper flowing paragraphs.
    """
    is_poetic_chapter = any(kw in chapter_title for kw in ("题记", "序诗", "献词", "诗篇", "诗歌"))
    blocks = re.split(r'\n\n+', text)
    processed_blocks = []

    for block in blocks:
        lines = block.splitlines()
        if len(lines) <= 1:
            processed_blocks.append(block)
            continue

        first = lines[0].strip()
        if first.startswith(('#', '>', '-', '*', '`', '|', '<!--', '![', '<')):
            processed_blocks.append(block)
            continue

        # Check if this block is a list (ordered or unordered or Chinese numbered list)
        is_list_block = any(
            re.match(r'^\s*(?:\d+[\.\)]|[-*+]|[一二三四五六七八九十]+[、.]|（[一二三四五六七八九十\d]+）)\s+', l)
            for l in lines
        )
        if is_list_block:
            processed_blocks.append(block)
            continue

        non_empty = [l.strip() for l in lines if l.strip()]
        if not non_empty:
            processed_blocks.append(block)
            continue

        if is_poetic_chapter:
            new_lines = []
            for i, line in enumerate(lines):
                s = line.rstrip()
                if i < len(lines) - 1 and s and not s.endswith(('\\', '<br />', '<br/>', '  ')):
                    s += '\\'
                new_lines.append(s)
            processed_blocks.append('\n'.join(new_lines))
        else:
            # Normal prose: strip accidental trailing backslashes inside paragraphs and merge into natural flowing prose
            clean_lines = [re.sub(r'\\+$', '', l).strip() for l in lines]
            merged = smart_join_lines(clean_lines)
            processed_blocks.append(merged)

    return '\n\n'.join(processed_blocks)

def assemble_chapter(chapter_id, title, source_md_paths, out_path, is_drama=False):
    """Merge source markdown files and remap footnotes with chapter namespace."""
    combined_body = []
    definitions = {}

    for src in source_md_paths:
        if not os.path.exists(src):
            print(f"[-] Warning: missing source slice: {src}")
            continue
        with open(src, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        part_lines = []
        for line in lines:
            m_def = re.match(r'^\s*\[\^([^\]]+)\]:\s*(.+)$', line)
            if m_def:
                k = m_def.group(1).strip()
                v = m_def.group(2).strip()
                definitions[k] = v
            elif line.strip() == '---':
                continue
            else:
                part_lines.append(line)
        combined_body.append("".join(part_lines).strip())

    full_text = "\n\n".join(combined_body)
    
    # If content starts with a ## heading, convert it to H1 (EPUB TOC needs H1 for chapter splits)
    # Otherwise prepend a H1 title
    if full_text.startswith('## '):
        full_text = '# ' + full_text[3:]
    elif not full_text.startswith('# '):
        full_text = f"# {title}\n\n" + full_text

    # Remap footnotes in order of appearance
    ref_keys = []
    for m in re.finditer(r'\[\^([^\]]+)\]', full_text):
        k = m.group(1).strip()
        if k not in ref_keys:
            ref_keys.append(k)

    def_keys = list(definitions.keys())
    id_map = {}
    for idx, old_k in enumerate(ref_keys, start=1):
        new_k = f"{chapter_id}_{idx}"
        id_map[old_k] = new_k
        if old_k not in definitions and idx <= len(def_keys):
            definitions[old_k] = definitions[def_keys[idx-1]]

    def ref_replacer(match):
        old_k = match.group(1).strip()
        new_k = id_map.get(old_k, old_k)
        return f"[^{new_k}]"

    full_text = re.sub(r'\[\^([^\]]+)\]', ref_replacer, full_text)
    
    # Layout normalization
    full_text = normalize_text_layout(full_text, is_drama=is_drama)
    full_text = preserve_poetic_line_breaks(full_text, chapter_title=title)

    # Append mapped footnote definitions
    if id_map:
        full_text += "\n\n---\n\n"
        for old_k, new_k in sorted(id_map.items(), key=lambda x: int(x[1].split('_')[1])):
            content = definitions.get(old_k, "（注释文本缺失）")
            full_text += f"[^{new_k}]: {content}\n"

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full_text + '\n')

    print(f"[OK] Chapter '{title}' -> {out_path} ({len(full_text)} chars, {len(id_map)} footnotes)")
    return out_path

def main():
    parser = argparse.ArgumentParser(description="Assemble markdown slices into full normalized chapters")
    parser.add_argument("--id", required=True, help="Chapter ID prefix (e.g. c01)")
    parser.add_argument("--title", required=True, help="Chapter title (e.g. 'Chapter 1')")
    parser.add_argument("--sources", nargs="+", required=True, help="List of slice markdown files in order")
    parser.add_argument("--out", required=True, help="Output markdown path")
    parser.add_argument("--drama", action="store_true", help="Apply drama script normalization")
    args = parser.parse_args()

    assemble_chapter(args.id, args.title, args.sources, args.out, is_drama=args.drama)

if __name__ == "__main__":
    main()
