#!/usr/bin/env python
"""
build.py — Convert wiki/*.md → site/*.html (mskbook style)

Usage:
    python build.py          # Build all pages
    python build.py --clean  # Clean site/ and rebuild

Single source of truth: wiki/
Output: site/ (deployed to GitHub Pages)
"""

import os
import re
import sys
import shutil
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────
WIKI_DIR = Path("wiki")
OUTPUT_DIR = Path("site")
SITE_TITLE = "MSK MRI Reference"
SITE_SUBTITLE = "Musculoskeletal MRI Knowledge Base"
SITE_AUTHORS = "Built with LLM Wiki Pattern"

# Region display config: key=folder name, icon, display name, sort order
REGIONS = {
    "shoulder": {"icon": "🦴", "name": "Shoulder", "order": 1},
    "elbow":    {"icon": "💪", "name": "Elbow",    "order": 2},
    "wrist":    {"icon": "✋", "name": "Wrist & Hand", "order": 3},
    "hip":      {"icon": "🦵", "name": "Hip",      "order": 4},
    "knee":     {"icon": "🦿", "name": "Knee",     "order": 5},
    "ankle":    {"icon": "🦶", "name": "Ankle & Foot", "order": 6},
    "spine":    {"icon": "🔩", "name": "Spine",    "order": 7},
    "tumor":    {"icon": "🔬", "name": "Tumor (General)", "order": 8},
}

# ── Markdown Parser ─────────────────────────────────────────────────

def parse_markdown(md_text):
    """Parse wiki markdown into structured data.

    Returns: {
        title: str,
        parts: [{ title, anchor, sections: [{ title, anchor, html }] }]
    }
    """
    lines = md_text.split('\n')
    title = ""
    parts = []
    current_part = None
    current_section = None
    content_lines = []

    def flush_content():
        nonlocal content_lines, current_section
        if not content_lines or not any(l.strip() for l in content_lines):
            content_lines = []
            return
        html = convert_content_to_html(content_lines)
        if current_section is not None:
            current_section["html"] += html
        elif current_part is not None and html.strip():
            # Content directly under H2 with no H3 — auto-create section
            current_section = {"title": current_part["title"], "anchor": current_part["anchor"], "html": html}
            current_part["sections"].append(current_section)
        content_lines = []

    for line in lines:
        # H1 — page title
        m = re.match(r'^# (.+)$', line)
        if m:
            title = m.group(1).strip()
            continue

        # H2 — Part
        m = re.match(r'^## (.+?)(?:\s*\{#([\w-]+)\})?\s*$', line)
        if m:
            flush_content()
            part_title = m.group(1).strip()
            anchor = m.group(2) or slugify(part_title)
            current_part = {"title": part_title, "anchor": anchor, "sections": []}
            parts.append(current_part)
            current_section = None
            continue

        # H3 — Section
        m = re.match(r'^### (.+?)(?:\s*\{#([\w-]+)\})?\s*$', line)
        if m:
            flush_content()
            sec_title = m.group(1).strip()
            anchor = m.group(2) or slugify(sec_title)
            current_section = {"title": sec_title, "anchor": anchor, "html": ""}
            if current_part is None:
                current_part = {"title": title or "Content", "anchor": "main", "sections": []}
                parts.append(current_part)
            current_part["sections"].append(current_section)
            continue

        # H4 — Subsection (rendered inline)
        m = re.match(r'^#### (.+?)(?:\s*\{#([\w-]+)\})?\s*$', line)
        if m:
            flush_content()
            sub_title = m.group(1).strip()
            if current_section is None:
                if current_part is None:
                    current_part = {"title": title or "Content", "anchor": "main", "sections": []}
                    parts.append(current_part)
                current_section = {"title": "Overview", "anchor": "overview", "html": ""}
                current_part["sections"].append(current_section)
            current_section["html"] += f'<div class="subsection"><h4 class="subsection-title">{inline_format(sub_title)}</h4></div>\n'
            continue

        # HR
        if re.match(r'^-{3,}\s*$', line):
            flush_content()
            continue

        # Everything else is content
        content_lines.append(line)

    flush_content()

    # If no parts were found but there's content, create a default part
    if not parts and title:
        pass  # Empty page

    return {"title": title, "parts": parts}


def convert_content_to_html(lines):
    """Convert a block of markdown content lines to HTML."""
    html = ""
    i = 0
    while i < len(lines):
        line = lines[i]

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Table
        if '|' in line and i + 1 < len(lines) and re.match(r'^\s*\|[-:|]+\|', lines[i + 1]):
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            html += render_table(table_lines)
            continue

        # Warning box (> **⚠️ or > **Warning or > ⚠️)
        if re.match(r'^>\s*\*?\*?[⚠️🔑📏💡❗]', line) or re.match(r'^>\s*\*?\*?(?:Warning|IMPORTANT|Key|Note|Pitfall)', line, re.I):
            box_lines = [line]
            i += 1
            while i < len(lines) and (lines[i].startswith('>') or (lines[i].strip() and not lines[i].startswith('#'))):
                if not lines[i].startswith('>'):
                    break
                box_lines.append(lines[i])
                i += 1
            html += render_callout_box(box_lines)
            continue

        # Regular blockquote
        if line.startswith('>'):
            box_lines = [line]
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                box_lines.append(lines[i])
                i += 1
            html += render_blockquote(box_lines)
            continue

        # Unordered list
        if re.match(r'^[-*]\s', line.strip()):
            list_lines = [line]
            i += 1
            while i < len(lines) and (re.match(r'^[-*]\s', lines[i].strip()) or re.match(r'^\s{2,}[-*]\s', lines[i])):
                list_lines.append(lines[i])
                i += 1
            html += render_unordered_list(list_lines)
            continue

        # Ordered list
        if re.match(r'^\d+\.\s', line.strip()):
            list_lines = [line]
            i += 1
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                list_lines.append(lines[i])
                i += 1
            html += render_ordered_list(list_lines)
            continue

        # Paragraph
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('-') and not lines[i].startswith('*') and not lines[i].startswith('>') and not lines[i].startswith('|') and not re.match(r'^\d+\.\s', lines[i]):
            para_lines.append(lines[i])
            i += 1
        text = ' '.join(l.strip() for l in para_lines)
        html += f'<p>{inline_format(text)}</p>\n'

    return html


def render_table(lines):
    """Render markdown table to HTML."""
    # Parse header
    headers = [c.strip() for c in lines[0].strip('|').split('|')]
    # Skip separator (line 1)
    rows = []
    for line in lines[2:]:
        if re.match(r'^\s*\|[-:|]+\|', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)

    html = '<div class="table-wrapper"><table>\n'
    html += '<tr>' + ''.join(f'<th>{inline_format(h)}</th>' for h in headers) + '</tr>\n'
    for row in rows:
        html += '<tr>' + ''.join(f'<td>{inline_format(c)}</td>' for c in row) + '</tr>\n'
    html += '</table></div>\n'
    return html


def render_unordered_list(lines):
    """Render unordered list to HTML."""
    html = '<ul>\n'
    for line in lines:
        text = re.sub(r'^\s*[-*]\s+', '', line)
        html += f'<li>{inline_format(text)}</li>\n'
    html += '</ul>\n'
    return html


def render_ordered_list(lines):
    """Render ordered list to HTML."""
    html = '<ol>\n'
    for line in lines:
        text = re.sub(r'^\s*\d+\.\s+', '', line)
        html += f'<li>{inline_format(text)}</li>\n'
    html += '</ol>\n'
    return html


def render_callout_box(lines):
    """Render blockquote as warning/info box."""
    text = '\n'.join(re.sub(r'^>\s?', '', l) for l in lines)
    # Detect type
    if any(w in text.lower() for w in ['warning', '⚠️', 'pitfall', 'important', '❗', 'avoid', 'caution']):
        box_class = "warning-box"
        icon = "⚠️"
    else:
        box_class = "info-box"
        icon = "💡"

    # Extract title (first bold text)
    title_match = re.match(r'\*\*(.+?)\*\*[:\s]*(.*)', text.split('\n')[0])
    if title_match:
        title = title_match.group(1)
        rest_first = title_match.group(2)
        rest = rest_first + '\n' + '\n'.join(text.split('\n')[1:])
    else:
        title = "Note"
        rest = text

    content_html = convert_content_to_html(rest.strip().split('\n'))
    return f'<div class="{box_class}"><div class="box-title">{icon} {inline_format(title)}</div>{content_html}</div>\n'


def render_blockquote(lines):
    """Render regular blockquote."""
    text = '\n'.join(re.sub(r'^>\s?', '', l) for l in lines)
    inner = convert_content_to_html(text.split('\n'))
    return f'<div class="info-box">{inner}</div>\n'


def inline_format(text):
    """Convert inline markdown to HTML."""
    # Wiki links: [[page-name]] or [[page-name#anchor]]
    text = re.sub(r'\[\[([^\]|]+?)(?:#([^\]]+?))?\]\]', wiki_link_replace, text)
    # Bold + Italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Em dash
    text = text.replace(' — ', ' &mdash; ')
    return text


def wiki_link_replace(match):
    """Convert [[wiki-link]] to <a href>."""
    page = match.group(1)
    anchor = match.group(2)
    # Find the page in wiki structure
    href = resolve_wiki_link(page)
    if anchor:
        href += f'#{anchor}'
    display = page.replace('-', ' ').title()
    return f'<a href="{href}" class="wiki-link">{display}</a>'


# Global page registry (filled during build)
PAGE_REGISTRY = {}

def resolve_wiki_link(page_name):
    """Resolve wiki page name to relative URL."""
    if page_name in PAGE_REGISTRY:
        return PAGE_REGISTRY[page_name]
    # Fallback: assume flat structure
    return f'{page_name}.html'


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ── HTML Templates ──────────────────────────────────────────────────

CHAPTER_CSS = """\
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #e9ecef;
    --text-primary: #212529;
    --text-secondary: #495057;
    --text-muted: #6c757d;
    --border-color: #dee2e6;
    --accent-color: #0d6efd;
    --accent-hover: #0b5ed7;
    --warning-bg: #fff3cd;
    --warning-border: #ffecb5;
    --warning-text: #664d03;
    --info-bg: #cff4fc;
    --info-border: #b6effb;
    --info-text: #055160;
    --shadow: 0 2px 8px rgba(0,0,0,0.1);
    --code-bg: #f1f3f5;
}

[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-tertiary: #0f3460;
    --text-primary: #e8e8e8;
    --text-secondary: #b8b8b8;
    --text-muted: #888888;
    --border-color: #3d3d5c;
    --accent-color: #4dabf7;
    --accent-hover: #74c0fc;
    --warning-bg: #332701;
    --warning-border: #4d3a02;
    --warning-text: #ffc107;
    --info-bg: #032830;
    --info-border: #055160;
    --info-text: #6edff6;
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
    --code-bg: #2d2d44;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    transition: background-color 0.3s, color 0.3s;
}

/* Header */
.header {
    position: sticky; top: 0;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    padding: 12px 20px; z-index: 1000;
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}
.header h1 { font-size: 1.2rem; font-weight: 600; flex: 1; min-width: 200px; }

/* Search */
.search-container { position: relative; flex: 0 1 300px; }
.search-input {
    width: 100%; padding: 8px 36px 8px 12px;
    border: 1px solid var(--border-color); border-radius: 6px;
    background: var(--bg-primary); color: var(--text-primary); font-size: 14px;
}
.search-input:focus { outline: none; border-color: var(--accent-color); }
.search-clear {
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: var(--text-muted);
    cursor: pointer; font-size: 18px; display: none;
}
.search-results-count { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* Theme Toggle */
.theme-toggle {
    background: var(--bg-tertiary); border: 1px solid var(--border-color);
    border-radius: 6px; padding: 8px 12px; cursor: pointer;
    color: var(--text-primary); font-size: 14px;
    display: flex; align-items: center; gap: 6px;
}
.theme-toggle:hover { background: var(--border-color); }

/* Back Link */
.back-link {
    color: var(--text-primary); background: var(--bg-tertiary);
    text-decoration: none; padding: 6px 12px; border-radius: 6px;
    font-size: 14px; transition: background 0.2s;
    border: 1px solid var(--border-color);
}
.back-link:hover { background: var(--border-color); }

/* TOC Toggle (Mobile) */
.toc-toggle {
    display: none; background: var(--accent-color); color: white;
    border: none; border-radius: 6px; padding: 8px 12px;
    cursor: pointer; font-size: 14px;
}

/* Layout */
.container { display: flex; max-width: 1400px; margin: 0 auto; }

/* Sidebar TOC */
.sidebar {
    width: 220px; height: calc(100vh - 60px);
    position: sticky; top: 60px; overflow-y: auto;
    padding: 12px; border-right: 1px solid var(--border-color);
    background: var(--bg-secondary); flex-shrink: 0;
}
.sidebar h2 { font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); }
.expand-all-btn {
    background: var(--bg-tertiary); border: 1px solid var(--border-color);
    border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 14px;
}
.expand-all-btn:hover { background: var(--border-color); }
.toc-list { list-style: none; }
.toc-part { margin-bottom: 16px; }
.toc-part-title {
    font-weight: 600; font-size: 14px; color: var(--text-secondary);
    padding: 6px 0; cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.toc-part-title::before { content: '▸'; font-size: 10px; transition: transform 0.2s; }
.toc-part.expanded .toc-part-title::before { transform: rotate(90deg); }
.toc-sections { display: none; padding-left: 14px; }
.toc-part.expanded .toc-sections { display: block; }
.toc-link {
    display: block; padding: 5px 0; font-size: 14px; color: var(--text-secondary);
    text-decoration: none; border-left: 2px solid transparent;
    padding-left: 8px; margin-left: -8px;
}
.toc-link:hover { color: var(--accent-color); }
.toc-link.active { color: var(--accent-color); border-left-color: var(--accent-color); font-weight: 500; }

/* Main Content */
.main-content { flex: 1; padding: 24px 32px; min-width: 0; }
.chapter-header { text-align: center; padding-bottom: 24px; border-bottom: 2px solid var(--border-color); margin-bottom: 32px; }
.chapter-header h1 { font-size: 1.8rem; margin-bottom: 8px; }
.chapter-header .subtitle { color: var(--text-secondary); font-size: 1.1rem; }

/* Parts */
.part { margin-bottom: 40px; border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; }
.part-header {
    background: linear-gradient(135deg, var(--accent-color), var(--accent-hover));
    padding: 14px 20px; cursor: pointer;
    display: flex; align-items: center; justify-content: space-between; user-select: none;
}
.part-header:hover { filter: brightness(1.1); }
.part-title { font-size: 1.2rem; color: white; margin: 0; border: none; padding: 0; }
.part-toggle { font-size: 1.4rem; color: white; transition: transform 0.3s; }
.part.collapsed .part-toggle { transform: rotate(-90deg); }
.part-content { padding: 20px; }
.part.collapsed .part-content { display: none; }

/* Sections */
.section { margin-bottom: 24px; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.section .section-header {
    background: var(--bg-secondary); padding: 12px 16px; cursor: pointer;
    display: flex; align-items: center; justify-content: space-between; user-select: none;
    border-bottom: none;
}
.section .section-header:hover { background: var(--bg-tertiary); }
.section-title { font-size: 1.1rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.section-number { background: var(--accent-color); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; }
.section-toggle { font-size: 1.2rem; color: var(--text-muted); transition: transform 0.2s; }
.section.expanded .section-toggle { transform: rotate(180deg); }
.section-content { display: none; padding: 16px; border-top: 1px solid var(--border-color); }
.section.expanded .section-content { display: block; }

/* Content Elements */
.subsection { margin-bottom: 20px; }
.subsection-title { font-weight: 600; color: var(--text-primary); margin-bottom: 8px; font-size: 1rem; }
ul, ol { padding-left: 24px; margin-bottom: 12px; }
li { margin-bottom: 4px; }
p { margin-bottom: 12px; }
.table-wrapper { overflow-x: auto; margin: 16px 0; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 10px 12px; text-align: left; border: 1px solid var(--border-color); }
th { background: var(--bg-tertiary); font-weight: 600; }
tr:nth-child(even) { background: var(--bg-secondary); }
code { background: var(--code-bg); padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }

/* Special Boxes */
.warning-box {
    background: var(--warning-bg); border: 1px solid var(--warning-border);
    border-left: 4px solid var(--warning-text); padding: 12px 16px;
    border-radius: 4px; margin: 16px 0;
}
.warning-box .box-title { font-weight: 600; color: var(--warning-text); margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.warning-box ul { color: var(--warning-text); margin-bottom: 0; }
.info-box {
    background: var(--info-bg); border: 1px solid var(--info-border);
    border-left: 4px solid var(--info-text); padding: 12px 16px;
    border-radius: 4px; margin: 16px 0;
}
.info-box .box-title { font-weight: 600; color: var(--info-text); margin-bottom: 8px; }
.info-box ul, .info-box p { color: var(--info-text); }

/* Wiki Links */
.wiki-link { color: var(--accent-color); text-decoration: none; border-bottom: 1px dashed var(--accent-color); }
.wiki-link:hover { border-bottom-style: solid; }

/* Highlight for search */
mark { background: #ffeb3b; color: #000; padding: 1px 2px; border-radius: 2px; }
[data-theme="dark"] mark { background: #ffc107; color: #000; }

/* Footer */
.footer { text-align: center; padding: 24px; border-top: 1px solid var(--border-color); margin-top: 40px; color: var(--text-muted); font-size: 14px; }

/* Scroll to top */
.scroll-top {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--accent-color); color: white; border: none;
    border-radius: 50%; width: 48px; height: 48px; font-size: 24px;
    cursor: pointer; box-shadow: var(--shadow);
    display: none; align-items: center; justify-content: center;
}
.scroll-top.visible { display: flex; }

/* Responsive */
@media (max-width: 900px) {
    .sidebar {
        position: fixed; left: -240px; top: 60px; width: 220px;
        height: calc(100vh - 60px); z-index: 999;
        transition: left 0.3s; box-shadow: var(--shadow);
    }
    .sidebar.open { left: 0; }
    .toc-toggle { display: block; }
    .main-content { padding: 16px; }
    .chapter-header h1 { font-size: 1.4rem; }
}

@media (max-width: 600px) {
    .header { padding: 10px 12px; }
    .header h1 { font-size: 1rem; }
    .search-container { flex: 1 1 100%; order: 3; }
}
"""

CHAPTER_JS = """\
// Theme Toggle
function toggleTheme() {
    const body = document.body;
    const icon = document.getElementById('themeIcon');
    const text = document.getElementById('themeText');
    if (body.getAttribute('data-theme') === 'dark') {
        body.removeAttribute('data-theme');
        icon.textContent = '🌙'; text.textContent = '深色';
        localStorage.setItem('theme', 'light');
    } else {
        body.setAttribute('data-theme', 'dark');
        icon.textContent = '☀️'; text.textContent = '淺色';
        localStorage.setItem('theme', 'dark');
    }
}
// Load saved theme
(function() {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        document.getElementById('themeIcon').textContent = '☀️';
        document.getElementById('themeText').textContent = '淺色';
    }
})();

// Sidebar Toggle (Mobile)
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.toc-toggle');
    if (sidebar && toggle && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// Part Toggle
function togglePart(el) { el.parentElement.classList.toggle('collapsed'); }

// Toggle All
let allExpanded = false;
function toggleAllParts() {
    const parts = document.querySelectorAll('.part');
    const sections = document.querySelectorAll('.section');
    const tocParts = document.querySelectorAll('.toc-part');
    const icon = document.getElementById('expandAllIcon');
    if (allExpanded) {
        parts.forEach(p => p.classList.add('collapsed'));
        sections.forEach(s => s.classList.remove('expanded'));
        tocParts.forEach(t => t.classList.remove('expanded'));
        icon.textContent = '📕'; allExpanded = false;
    } else {
        parts.forEach(p => p.classList.remove('collapsed'));
        sections.forEach(s => s.classList.add('expanded'));
        tocParts.forEach(t => t.classList.add('expanded'));
        icon.textContent = '📖'; allExpanded = true;
    }
}

// TOC Part Toggle
function toggleTocPart(el) {
    el.parentElement.classList.toggle('expanded');
    const targetId = el.getAttribute('data-target');
    if (targetId) {
        const targetPart = document.getElementById(targetId);
        if (targetPart && el.parentElement.classList.contains('expanded')) {
            targetPart.classList.remove('collapsed');
            targetPart.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

// Section Toggle
function toggleSection(el) { el.parentElement.classList.toggle('expanded'); }

// Search
function handleSearch() {
    const query = document.getElementById('searchInput').value.trim().toLowerCase();
    const clearBtn = document.getElementById('searchClear');
    const countDiv = document.getElementById('searchCount');
    clearBtn.style.display = query ? 'block' : 'none';
    // Reset highlights
    document.querySelectorAll('mark').forEach(mark => {
        const parent = mark.parentNode;
        parent.replaceChild(document.createTextNode(mark.textContent), mark);
        parent.normalize();
    });
    if (!query) { countDiv.textContent = ''; return; }
    // Expand all for search
    document.querySelectorAll('.part').forEach(p => p.classList.remove('collapsed'));
    document.querySelectorAll('.section').forEach(s => s.classList.add('expanded'));
    // Highlight
    let count = 0;
    const walker = document.createTreeWalker(
        document.querySelector('.main-content'), NodeFilter.SHOW_TEXT, null, false
    );
    const nodes = [];
    while (walker.nextNode()) {
        if (walker.currentNode.nodeValue.toLowerCase().includes(query)) nodes.push(walker.currentNode);
    }
    nodes.forEach(node => {
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')})`, 'gi');
        const parts = node.nodeValue.split(regex);
        if (parts.length > 1) {
            const frag = document.createDocumentFragment();
            parts.forEach(part => {
                if (part.toLowerCase() === query.toLowerCase()) {
                    const m = document.createElement('mark'); m.textContent = part; frag.appendChild(m); count++;
                } else { frag.appendChild(document.createTextNode(part)); }
            });
            node.parentNode.replaceChild(frag, node);
        }
    });
    countDiv.textContent = count > 0 ? `找到 ${count} 個結果` : '沒有找到結果';
    const firstMark = document.querySelector('mark');
    if (firstMark) firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
function clearSearch() { document.getElementById('searchInput').value = ''; handleSearch(); }

// TOC Active State
const tocLinks = document.querySelectorAll('.toc-link');
const allSections = document.querySelectorAll('.section');
window.addEventListener('scroll', () => {
    let current = '';
    allSections.forEach(s => { if (s.getBoundingClientRect().top <= 100) current = s.id; });
    tocLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) link.classList.add('active');
    });
    const btn = document.getElementById('scrollTop');
    if (btn) { if (window.scrollY > 500) btn.classList.add('visible'); else btn.classList.remove('visible'); }
});

// Smooth scroll for TOC links
tocLinks.forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const target = document.getElementById(link.getAttribute('href').substring(1));
        if (target) { target.classList.add('expanded'); target.scrollIntoView({ behavior: 'smooth' }); }
        document.getElementById('sidebar').classList.remove('open');
    });
});

// Scroll to top
function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }

// Keyboard shortcuts
document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') document.getElementById('searchInput').focus();
    if (e.key === 'Escape') clearSearch();
});
"""

INDEX_CSS = """\
:root {
    --bg-primary: #ffffff; --bg-secondary: #f8f9fa; --bg-card: #ffffff;
    --text-primary: #212529; --text-secondary: #495057; --text-muted: #6c757d;
    --border-color: #dee2e6; --accent-color: #0d6efd; --accent-hover: #0b5ed7;
    --success-color: #198754; --warning-color: #ffc107;
    --shadow: 0 4px 12px rgba(0,0,0,0.1); --shadow-hover: 0 8px 24px rgba(0,0,0,0.15);
}
[data-theme="dark"] {
    --bg-primary: #1a1a2e; --bg-secondary: #16213e; --bg-card: #1f2940;
    --text-primary: #e8e8e8; --text-secondary: #b8b8b8; --text-muted: #888888;
    --border-color: #3d3d5c; --accent-color: #4dabf7; --accent-hover: #74c0fc;
    --success-color: #51cf66; --warning-color: #fcc419;
    --shadow: 0 4px 12px rgba(0,0,0,0.3); --shadow-hover: 0 8px 24px rgba(0,0,0,0.4);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-secondary); color: var(--text-primary); line-height: 1.6;
    min-height: 100vh; transition: background-color 0.3s, color 0.3s;
}
.header {
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 50%, #2b6cb0 100%);
    color: white; padding: 40px 20px; text-align: center; position: relative;
}
[data-theme="dark"] .header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%); }
.header h1 { font-size: 2.2rem; margin-bottom: 8px; font-weight: 700; }
.header .subtitle { font-size: 1.1rem; opacity: 0.9; }
.header .authors { font-size: 0.9rem; opacity: 0.8; margin-top: 12px; }
.theme-toggle {
    position: absolute; top: 20px; right: 20px;
    background: rgba(255,255,255,0.2); border: none; border-radius: 8px;
    padding: 10px 14px; cursor: pointer; color: white; font-size: 14px;
    display: flex; align-items: center; gap: 6px; transition: background 0.2s;
}
.theme-toggle:hover { background: rgba(255,255,255,0.3); }
.stats-bar {
    background: var(--bg-primary); border-bottom: 1px solid var(--border-color);
    padding: 16px 20px; display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;
}
.stat-item { text-align: center; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: var(--accent-color); }
.stat-label { font-size: 0.85rem; color: var(--text-muted); }
.search-container { max-width: 600px; margin: 24px auto; padding: 0 20px; }
.search-input {
    width: 100%; padding: 14px 20px;
    border: 2px solid var(--border-color); border-radius: 12px;
    background: var(--bg-primary); color: var(--text-primary); font-size: 16px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.search-input:focus { outline: none; border-color: var(--accent-color); box-shadow: 0 0 0 4px rgba(13,110,253,0.15); }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.section-header {
    display: flex; align-items: center; gap: 12px;
    margin: 32px 0 20px; padding-bottom: 12px; border-bottom: 2px solid var(--border-color);
}
.section-icon { font-size: 1.5rem; }
.section-title { font-size: 1.3rem; font-weight: 600; color: var(--text-primary); }
.section-count { background: var(--bg-secondary); padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; color: var(--text-muted); }
.chapter-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
.chapter-card {
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: 12px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s;
    position: relative; cursor: pointer;
}
.chapter-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
.card-header { padding: 20px; background: linear-gradient(135deg, var(--accent-color), var(--accent-hover)); color: white; }
.region-name { font-size: 0.85rem; opacity: 0.9; margin-bottom: 4px; }
.chapter-title { font-size: 1.2rem; font-weight: 600; }
.card-body { padding: 16px 20px; }
.chapter-description { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 12px; }
.chapter-meta { display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.85rem; color: var(--text-muted); }
.meta-item { display: flex; align-items: center; gap: 4px; }
.quick-links { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.quick-link {
    background: var(--bg-secondary); padding: 4px 10px; border-radius: 6px;
    font-size: 0.8rem; color: var(--accent-color); text-decoration: none; transition: background 0.2s;
}
.quick-link:hover { background: var(--border-color); }
.card-footer {
    padding: 12px 20px; background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    display: flex; justify-content: space-between; align-items: center;
}
.status-badge { padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 500; }
.status-badge.ready { background: rgba(25,135,84,0.15); color: var(--success-color); }
.view-btn {
    background: var(--accent-color); color: white; border: none;
    padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; cursor: pointer; transition: background 0.2s;
}
.view-btn:hover { background: var(--accent-hover); }
.footer { text-align: center; padding: 32px 20px; margin-top: 40px; border-top: 1px solid var(--border-color); color: var(--text-muted); font-size: 0.9rem; }
.no-results { text-align: center; padding: 60px 20px; color: var(--text-muted); display: none; }
.no-results-icon { font-size: 3rem; margin-bottom: 16px; }
@media (max-width: 600px) {
    .header h1 { font-size: 1.6rem; }
    .stats-bar { gap: 24px; }
    .stat-value { font-size: 1.4rem; }
    .chapter-grid { grid-template-columns: 1fr; }
    .theme-toggle { top: 10px; right: 10px; padding: 8px 10px; }
}
"""


# ── Page Renderers ──────────────────────────────────────────────────

def render_chapter_page(page_data, region_name, back_href="../index.html"):
    """Render a full chapter HTML page."""
    title = page_data["title"]
    parts = page_data["parts"]

    # Build TOC
    toc_html = ""
    section_counter = 0
    for pi, part in enumerate(parts):
        part_id = f"part-{pi+1}"
        expanded = ""
        toc_html += f'<div class="toc-part {expanded}">\n'
        toc_html += f'  <div class="toc-part-title" onclick="toggleTocPart(this)" data-target="{part_id}">{part["title"]}</div>\n'
        toc_html += '  <div class="toc-sections">\n'
        for sec in part["sections"]:
            section_counter += 1
            sec_id = f"section-{section_counter}"
            sec["_id"] = sec_id
            toc_html += f'    <a href="#{sec_id}" class="toc-link">{section_counter}. {sec["title"]}</a>\n'
        toc_html += '  </div>\n</div>\n'

    # Build content
    content_html = ""
    section_counter = 0
    for pi, part in enumerate(parts):
        part_id = f"part-{pi+1}"
        content_html += f'<div class="part collapsed" id="{part_id}">\n'
        content_html += f'  <div class="part-header" onclick="togglePart(this)">\n'
        content_html += f'    <h2 class="part-title">{part["title"]}</h2>\n'
        content_html += f'    <span class="part-toggle">▼</span>\n'
        content_html += f'  </div>\n'
        content_html += f'  <div class="part-content">\n'

        for sec in part["sections"]:
            section_counter += 1
            sec_id = f"section-{section_counter}"
            expanded = ""
            content_html += f'    <div class="section {expanded}" id="{sec_id}">\n'
            content_html += f'      <div class="section-header" onclick="toggleSection(this)">\n'
            content_html += f'        <span class="section-title"><span class="section-number">{section_counter}</span> {sec["title"]}</span>\n'
            content_html += f'        <span class="section-toggle">▼</span>\n'
            content_html += f'      </div>\n'
            content_html += f'      <div class="section-content">\n'
            content_html += sec["html"]
            content_html += f'      </div>\n'
            content_html += f'    </div>\n'

        content_html += '  </div>\n</div>\n'

    subtitle = region_name if region_name else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {SITE_TITLE}</title>
    <style>{CHAPTER_CSS}</style>
</head>
<body>
    <header class="header">
        <a href="{back_href}" class="back-link">← 目錄</a>
        <button class="toc-toggle" onclick="toggleSidebar()">☰ 導航</button>
        <h1>{title}</h1>
        <div class="search-container">
            <input type="text" class="search-input" id="searchInput" placeholder="搜索關鍵字..." oninput="handleSearch()">
            <button class="search-clear" id="searchClear" onclick="clearSearch()">×</button>
            <div class="search-results-count" id="searchCount"></div>
        </div>
        <button class="theme-toggle" onclick="toggleTheme()">
            <span id="themeIcon">🌙</span>
            <span id="themeText">深色</span>
        </button>
    </header>

    <div class="container">
        <aside class="sidebar" id="sidebar">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h2>目錄導航</h2>
                <button class="expand-all-btn" onclick="toggleAllParts()" title="展開/收合全部">
                    <span id="expandAllIcon">📖</span>
                </button>
            </div>
            <nav class="toc-list">
{toc_html}
            </nav>
        </aside>

        <main class="main-content">
            <div class="chapter-header">
                <h1>{title}</h1>
                <p class="subtitle">{subtitle}</p>
            </div>
{content_html}
        </main>
    </div>

    <button class="scroll-top" id="scrollTop" onclick="scrollToTop()">↑</button>
    <footer class="footer">
        <p>Generated from <a href="https://github.com/mickeypeng530/mskbook">LLM Wiki</a></p>
    </footer>

    <script>{CHAPTER_JS}</script>
</body>
</html>"""


def render_index_page(regions_data, total_pages, total_sections):
    """Render the index page with card grid."""
    cards_html = ""

    for region in regions_data:
        region_key = region["key"]
        icon = region.get("icon", "📄")
        display_name = region.get("display_name", region_key.title())

        for page in region["pages"]:
            page_name = page["name"]
            description = page["description"]
            href = page["href"]
            # Count sections in the page
            sec_count = page.get("section_count", 0)

            # Quick links (first 4 parts)
            quick_links_html = ""
            for ql in page.get("quick_links", [])[:4]:
                quick_links_html += f'<a href="{href}#part-{ql["num"]}" class="quick-link">{ql["title"]}</a>\n'

            keywords = page.get("keywords", "")

            cards_html += f"""
            <div class="chapter-card" onclick="window.location.href='{href}'" data-keywords="{keywords}">
                <div class="card-header">
                    <div class="region-name">{icon} {display_name}</div>
                    <div class="chapter-title">{page_name}</div>
                </div>
                <div class="card-body">
                    <p class="chapter-description">{description}</p>
                    <div class="chapter-meta">
                        <span class="meta-item">📑 {sec_count} sections</span>
                    </div>
                    <div class="quick-links">
                        {quick_links_html}
                    </div>
                </div>
                <div class="card-footer">
                    <span class="status-badge ready">✓ Ready</span>
                    <button class="view-btn">查看 →</button>
                </div>
            </div>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SITE_TITLE}</title>
    <style>{INDEX_CSS}</style>
</head>
<body>
    <header class="header">
        <button class="theme-toggle" onclick="toggleTheme()">
            <span id="themeIcon">🌙</span>
            <span id="themeText">深色</span>
        </button>
        <h1>{SITE_TITLE}</h1>
        <p class="subtitle">{SITE_SUBTITLE}</p>
        <p class="authors">{SITE_AUTHORS}</p>
    </header>

    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-value">{total_pages}</div>
            <div class="stat-label">主題頁面</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{total_sections}</div>
            <div class="stat-label">知識區塊</div>
        </div>
    </div>

    <div class="search-container">
        <input type="text" class="search-input" id="searchInput" placeholder="搜尋主題或關鍵字..." oninput="filterChapters()">
    </div>

    <div class="container">
        <div class="chapter-grid" id="allCards">
{cards_html}
        </div>

        <div class="no-results" id="noResults">
            <div class="no-results-icon">🔍</div>
            <p>找不到符合的主題</p>
        </div>
    </div>

    <footer class="footer">
        <p>Generated from <a href="https://github.com/mickeypeng530/mskbook">LLM Wiki</a></p>
        <p style="margin-top:12px;">Last updated: <span id="lastUpdate"></span></p>
    </footer>

    <script>
        document.getElementById('lastUpdate').textContent = new Date().toLocaleDateString('zh-TW', {{
            year: 'numeric', month: 'long', day: 'numeric'
        }});

        function toggleTheme() {{
            const body = document.body;
            const icon = document.getElementById('themeIcon');
            const text = document.getElementById('themeText');
            if (body.getAttribute('data-theme') === 'dark') {{
                body.removeAttribute('data-theme');
                icon.textContent = '🌙'; text.textContent = '深色';
                localStorage.setItem('theme', 'light');
            }} else {{
                body.setAttribute('data-theme', 'dark');
                icon.textContent = '☀️'; text.textContent = '淺色';
                localStorage.setItem('theme', 'dark');
            }}
        }}
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.setAttribute('data-theme', 'dark');
            document.getElementById('themeIcon').textContent = '☀️';
            document.getElementById('themeText').textContent = '淺色';
        }}

        function filterChapters() {{
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.chapter-card');
            let visible = 0;
            cards.forEach(card => {{
                const title = card.querySelector('.chapter-title').textContent.toLowerCase();
                const desc = card.querySelector('.chapter-description').textContent.toLowerCase();
                const region = card.querySelector('.region-name').textContent.toLowerCase();
                const keywords = (card.getAttribute('data-keywords') || '').toLowerCase();
                const matches = !query || title.includes(query) || desc.includes(query) || region.includes(query) || keywords.includes(query);
                card.style.display = matches ? '' : 'none';
                if (matches) visible++;
            }});
            document.getElementById('noResults').style.display = visible === 0 ? '' : 'none';
        }}

        document.addEventListener('keydown', e => {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }}
        }});
    </script>
</body>
</html>"""


# ── Build Engine ────────────────────────────────────────────────────

def discover_pages():
    """Scan wiki/ and return list of pages to build."""
    pages = []
    for region_dir in sorted(WIKI_DIR.iterdir()):
        if not region_dir.is_dir():
            continue
        region_name = region_dir.name
        if region_name == "sources":
            continue  # Skip source summaries

        for md_file in sorted(region_dir.glob("*.md")):
            if md_file.name.startswith("_"):
                continue  # Skip _overview.md etc. for now — could include later
            pages.append({
                "region": region_name,
                "file": md_file,
                "stem": md_file.stem,
            })
    return pages


def build_page_registry(pages):
    """Build global registry for wiki-link resolution.
    In merged mode, all pages in a region link to region.html#anchor."""
    global PAGE_REGISTRY
    for page in pages:
        region = page["region"]
        stem = page["stem"]
        anchor = stem  # e.g. rotator-cuff
        # Wiki links: [[rotator-cuff]] → shoulder.html#rotator-cuff
        PAGE_REGISTRY[stem] = f"{region}.html#{anchor}"
        PAGE_REGISTRY[f"{region}/{stem}"] = f"{region}.html#{anchor}"


def parse_index_md():
    """Parse _index.md to get page descriptions."""
    index_file = WIKI_DIR / "_index.md"
    if not index_file.exists():
        return {}

    descriptions = {}
    with open(index_file, encoding="utf-8") as f:
        for line in f:
            # Match: - [[page-name]] — description
            m = re.match(r'^- \[\[([^\]]+)\]\]\s*[—–-]\s*(.+)$', line.strip())
            if m:
                page_name = m.group(1)
                desc = m.group(2).strip()
                descriptions[page_name] = desc
    return descriptions


def merge_region_pages(pages_in_region):
    """Merge multiple .md files into one page_data structure.
    Each .md file's H1 becomes a Part; its H2s become Sections within that Part.
    """
    merged_parts = []
    for page_info in pages_in_region:
        md_file = page_info["file"]
        stem = page_info["stem"]
        with open(md_file, encoding="utf-8") as f:
            md_text = f.read()
        page_data = parse_markdown(md_text)
        file_title = page_data["title"] or stem.replace('-', ' ').title()

        if page_data["parts"]:
            # Wrap all content under one Part named after the file's H1
            # Each original H2-Part becomes sections, and original H3-Sections become subsections
            merged_sections = []
            for part in page_data["parts"]:
                # Each original Part becomes a Section in the merged view
                # Collect all its sections' HTML into one block
                combined_html = ""
                for sec in part["sections"]:
                    combined_html += f'<div class="subsection"><h4 class="subsection-title">{sec["title"]}</h4>{sec["html"]}</div>\n'
                if combined_html:
                    merged_sections.append({
                        "title": part["title"],
                        "anchor": part["anchor"],
                        "html": combined_html,
                    })
                else:
                    # Part with no sections — shouldn't happen after parser fix
                    merged_sections.append({
                        "title": part["title"],
                        "anchor": part["anchor"],
                        "html": "",
                    })

            merged_parts.append({
                "title": file_title,
                "anchor": stem,  # e.g. "rotator-cuff" for anchor linking
                "sections": merged_sections,
            })
        else:
            # Empty page
            merged_parts.append({
                "title": file_title,
                "anchor": stem,
                "sections": [],
            })

    return merged_parts


def build():
    """Main build function. Merges all .md per region into one HTML page."""
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"Building site from {WIKI_DIR}/ -> {OUTPUT_DIR}/")

    # Clean output
    if "--clean" in sys.argv and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Discover pages
    pages = discover_pages()
    if not pages:
        print("No pages found in wiki/")
        return

    build_page_registry(pages)
    descriptions = parse_index_md()

    # Group pages by region
    from collections import OrderedDict
    region_groups = OrderedDict()
    for page_info in pages:
        region = page_info["region"]
        if region not in region_groups:
            region_groups[region] = []
        region_groups[region].append(page_info)

    print(f"Found {len(pages)} pages across {len(region_groups)} regions")

    # Build one HTML per region
    total_pages = 0
    total_sections = 0
    index_regions = []

    for region, region_pages in region_groups.items():
        region_info = REGIONS.get(region, {"icon": "📄", "name": region.title(), "order": 99})
        region_display = f"{region_info['icon']} {region_info['name']}"

        # Merge all .md into one page_data
        merged_parts = merge_region_pages(region_pages)
        sec_count = sum(len(p["sections"]) for p in merged_parts)
        total_sections += sec_count
        total_pages += 1

        merged_page = {
            "title": region_info["name"],
            "parts": merged_parts,
        }

        # Render HTML
        html = render_chapter_page(merged_page, region_display, back_href="index.html")
        out_file = OUTPUT_DIR / f"{region}.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {region}.html ({len(region_pages)} topics, {sec_count} sections)")

        # Collect for index — one card per region
        # Build description from page titles
        page_titles = [p["file"].stem.replace('-', ' ').title() for p in region_pages]
        desc = ", ".join(page_titles[:5])
        if len(page_titles) > 5:
            desc += f" +{len(page_titles)-5} more"

        # Quick links = each Part (each .md file)
        quick_links = []
        sec_counter = 0
        for part in merged_parts:
            sec_counter += 1
            quick_links.append({"num": sec_counter, "title": part["title"]})

        keywords = " ".join(
            w.lower() for w in re.findall(r'\w+', " ".join(page_titles))
        )

        index_regions.append({
            "key": region,
            "icon": region_info["icon"],
            "display_name": region_info["name"],
            "order": region_info["order"],
            "pages": [{
                "name": region_info["name"],
                "description": desc,
                "href": f"{region}.html",
                "section_count": sec_count,
                "quick_links": quick_links[:6],
                "keywords": keywords,
            }],
        })

    # Sort regions by order
    sorted_regions = sorted(index_regions, key=lambda r: r["order"])

    # Build index page
    index_html = render_index_page(sorted_regions, total_pages, total_sections)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  ✓ index.html ({total_pages} region cards)")

    print(f"\nDone! {total_pages} region pages + index -> {OUTPUT_DIR}/")
    print(f"Open {OUTPUT_DIR}/index.html to preview")


if __name__ == "__main__":
    build()
