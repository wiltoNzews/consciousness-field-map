#!/usr/bin/env python3
"""
Build the_frontier.html from THE_FRONTIER.md
Matches the Consciousness Field Map design system.
"""

import re
import html as html_mod

def parse_md(md_text):
    """Parse THE_FRONTIER.md into structured sections."""
    lines = md_text.split('\n')

    sections = []
    current_section = None
    current_content = []

    # Track parts for grouping
    parts = {
        'methodology': {'title': 'Methodology', 'id': 'methodology', 'layers': []},
        'foundation': {'title': 'Foundation Layers', 'id': 'foundation', 'layers': []},
        'deep': {'title': 'Deep Signal', 'id': 'deep', 'layers': []},
        'territory': {'title': 'Extended Territory', 'id': 'territory', 'layers': []},
        'evaluative': {'title': 'The Evaluative Lens', 'id': 'evaluative', 'layers': []},
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect layer headers (supports "119b" style suffixes)
        layer_match = re.match(r'^###\s+Layer\s+(\d+[a-z]?):\s*(.*)', line)
        layer_match2 = re.match(r'^##\s+LAYER\s+(\d+[a-z]?):\s*(.*)', line)

        if layer_match or layer_match2:
            # Save previous section
            if current_section:
                current_section['content'] = '\n'.join(current_content)
                sections.append(current_section)

            m = layer_match or layer_match2
            num_str = m.group(1)
            # Extract numeric part for sorting/grouping, keep full string for display
            num = int(re.match(r'(\d+)', num_str).group(1))
            title = m.group(2).strip()

            # Skip stripped layers
            if 'STRIPPED' in title:
                current_section = None
                current_content = []
                i += 1
                continue

            current_section = {
                'type': 'layer',
                'num': num,
                'num_str': num_str,
                'title': title,
                'id': f'layer-{num_str}',
            }
            current_content = []
            i += 1
            continue

        # Detect major section headers (## Methodology, ## Signal Territory Graph, etc.)
        major_match = re.match(r'^##\s+(.*?)$', line)
        if major_match and not line.startswith('## LAYER'):
            if current_section:
                current_section['content'] = '\n'.join(current_content)
                sections.append(current_section)

            title = major_match.group(1).strip()
            current_section = {
                'type': 'section',
                'title': title,
                'id': re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'),
            }
            current_content = []
            i += 1
            continue

        if current_section:
            current_content.append(line)

        i += 1

    # Save last section
    if current_section:
        current_section['content'] = '\n'.join(current_content)
        sections.append(current_section)

    return sections


def md_inline(text):
    """Convert inline markdown to HTML."""
    # Escape HTML first
    text = html_mod.escape(text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Unicode entities for common symbols
    text = text.replace('&amp;mdash;', '&mdash;')
    text = text.replace('&amp;rarr;', '&rarr;')
    text = text.replace('&amp;larr;', '&larr;')
    text = text.replace('&amp;ndash;', '&ndash;')
    return text


def md_to_html_block(content):
    """Convert markdown content block to HTML."""
    lines = content.split('\n')
    html_parts = []
    i = 0
    in_table = False
    in_list = False
    in_blockquote = False
    table_rows = []
    list_items = []
    bq_lines = []

    while i < len(lines):
        line = lines[i].rstrip()

        # Empty line
        if not line.strip():
            if in_table:
                html_parts.append(render_table(table_rows))
                table_rows = []
                in_table = False
            if in_list:
                html_parts.append(render_list(list_items))
                list_items = []
                in_list = False
            if in_blockquote:
                html_parts.append(render_blockquote(bq_lines))
                bq_lines = []
                in_blockquote = False
            i += 1
            continue

        # Table row
        if line.strip().startswith('|') and line.strip().endswith('|'):
            if not in_table:
                if in_list:
                    html_parts.append(render_list(list_items))
                    list_items = []
                    in_list = False
                in_table = True
            table_rows.append(line)
            i += 1
            continue

        # Blockquote
        if line.strip().startswith('>'):
            if not in_blockquote:
                in_blockquote = True
            bq_lines.append(line.strip()[1:].strip())
            i += 1
            continue

        # Signal Territory Graph entry (check BEFORE list items — STG lines start with "- " too)
        stg_match = re.match(r'^-\s+\*\*S-(\d+[a-z]?)\*\*\s+\[(.+?)\]\s*—\s*\*(.+?)\*\s*—\s*(.*)', line)
        if stg_match:
            # Close any open list first
            if in_list:
                html_parts.append(render_list(list_items))
                list_items = []
                in_list = False
            sig_id = stg_match.group(1)
            glyph_info = stg_match.group(2)
            description = stg_match.group(3)
            category = stg_match.group(4)
            html_parts.append(f'''<div class="stg-entry">
  <span class="stg-id">S-{html_mod.escape(sig_id)}</span>
  <span class="stg-glyph">{md_inline(glyph_info)}</span>
  <p class="stg-desc">{md_inline(description)}</p>
  <span class="stg-cat">{md_inline(category)}</span>
</div>''')
            i += 1
            continue

        # List item
        if re.match(r'^[\s]*[-*]\s', line) or re.match(r'^[\s]*\d+\.\s', line):
            if in_table:
                html_parts.append(render_table(table_rows))
                table_rows = []
                in_table = False
            if not in_list:
                in_list = True
            list_items.append(line)
            i += 1
            continue

        # Close any open constructs
        if in_table:
            html_parts.append(render_table(table_rows))
            table_rows = []
            in_table = False
        if in_list:
            html_parts.append(render_list(list_items))
            list_items = []
            in_list = False
        if in_blockquote:
            html_parts.append(render_blockquote(bq_lines))
            bq_lines = []
            in_blockquote = False

        # Sub-headers (h4)
        h4_match = re.match(r'^####\s+(.*)', line)
        if h4_match:
            html_parts.append(f'<h4 class="sub">{md_inline(h4_match.group(1))}</h4>')
            i += 1
            continue

        # Sub-headers (h3 within content)
        h3_match = re.match(r'^###\s+(.*)', line)
        if h3_match and not re.match(r'^###\s+Layer', line):
            html_parts.append(f'<h4 class="sub">{md_inline(h3_match.group(1))}</h4>')
            i += 1
            continue

        # Horizontal rule
        if line.strip() == '---':
            html_parts.append('<hr class="divider">')
            i += 1
            continue

        # Regular paragraph
        # Collect consecutive non-empty, non-special lines
        para_lines = [line]
        j = i + 1
        while j < len(lines):
            next_line = lines[j].rstrip()
            if not next_line.strip():
                break
            if next_line.strip().startswith('|') or next_line.strip().startswith('>'):
                break
            if re.match(r'^[\s]*[-*]\s', next_line) or re.match(r'^[\s]*\d+\.\s', next_line):
                break
            if re.match(r'^#{2,4}\s', next_line):
                break
            if next_line.strip() == '---':
                break
            if re.match(r'^-\s+\*\*S-\d+', next_line):
                break
            para_lines.append(next_line)
            j += 1

        para_text = ' '.join(para_lines)
        html_parts.append(f'<p>{md_inline(para_text)}</p>')
        i = j

    # Close any remaining open constructs
    if in_table:
        html_parts.append(render_table(table_rows))
    if in_list:
        html_parts.append(render_list(list_items))
    if in_blockquote:
        html_parts.append(render_blockquote(bq_lines))

    return '\n'.join(html_parts)


def render_table(rows):
    """Render markdown table rows to HTML."""
    if not rows:
        return ''

    # Parse header
    cells = [c.strip() for c in rows[0].split('|')[1:-1]]
    html = '<div class="table-wrap"><table>\n<thead><tr>'
    for c in cells:
        html += f'<th>{md_inline(c)}</th>'
    html += '</tr></thead>\n<tbody>\n'

    # Skip separator row
    for row in rows[2:] if len(rows) > 1 else []:
        if re.match(r'^[\s|:-]+$', row):
            continue
        cells = [c.strip() for c in row.split('|')[1:-1]]
        html += '<tr>'
        for c in cells:
            html += f'<td>{md_inline(c)}</td>'
        html += '</tr>\n'

    html += '</tbody></table></div>'
    return html


def render_list(items):
    """Render list items to HTML."""
    if not items:
        return ''

    # Detect ordered vs unordered
    is_ordered = bool(re.match(r'^[\s]*\d+\.', items[0]))
    tag = 'ol' if is_ordered else 'ul'

    html = f'<{tag}>\n'
    for item in items:
        text = re.sub(r'^[\s]*[-*]\s+', '', item)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text)
        html += f'<li>{md_inline(text)}</li>\n'
    html += f'</{tag}>'
    return html


def render_blockquote(lines):
    """Render blockquote to HTML."""
    if not lines:
        return ''
    content = '<br>'.join(md_inline(l) for l in lines)
    return f'''<div class="crystal">
  <blockquote>{content}</blockquote>
</div>'''


def get_part(num):
    """Determine which part a layer belongs to."""
    if num <= 35:
        return 'foundation'
    elif num <= 75:
        return 'deep'
    elif num <= 100:
        return 'territory'
    else:
        return 'evaluative'


def get_glyph_color(title):
    """Pick accent color based on layer content."""
    title_lower = title.lower()
    if any(w in title_lower for w in ['skeptic', 'apophenia', 'failure', 'break']):
        return 'var(--red)'
    elif any(w in title_lower for w in ['test', 'predict', 'research', 'program']):
        return 'var(--green)'
    elif any(w in title_lower for w in ['mirror', 'ai', 'penrose', 'simulation']):
        return 'var(--violet)'
    elif any(w in title_lower for w in ['grift', 'money', 'disclosure', 'politic']):
        return 'var(--gold)'
    elif any(w in title_lower for w in ['credibil', 'map', 'signal', 'evaluat', 'synthesis']):
        return 'var(--cyan)'
    elif any(w in title_lower for w in ['observer', 'consciousness', 'threshold']):
        return 'var(--blue)'
    else:
        return 'var(--accent)'


def build_html(sections):
    """Build the complete HTML page."""

    # Group layers by part
    part_defs = [
        ['methodology', 'Methodology &amp; Framework', []],
        ['foundation', 'Foundation Layers (1&ndash;35)', []],
        ['deep', 'Deep Signal (36&ndash;67)', []],
        ['territory', 'Extended Territory (76&ndash;100)', []],
        ['evaluative', 'The Evaluative Lens (101&ndash;118)', []],
    ]
    part_map = {p[0]: p for p in part_defs}

    # Classify sections
    methodology_sections = []
    for s in sections:
        if s['type'] == 'layer':
            part_key = get_part(s['num'])
            part_map[part_key][2].append(s)
        else:
            methodology_sections.append(s)

    part_map['methodology'][2] = methodology_sections

    # Build sidebar nav
    sidebar_items = []
    for part_key, part_title, part_sections in part_defs:
        if not part_sections:
            continue
        sidebar_items.append(f'<div class="nav-group">')
        sidebar_items.append(f'<div class="nav-label">{part_title}</div>')
        for s in part_sections:
            if s['type'] == 'layer':
                label = f'L{s.get("num_str", s["num"])}: {s["title"][:30]}{"..." if len(s["title"]) > 30 else ""}'
                sidebar_items.append(f'<a href="#{s["id"]}" class="nav-link">{html_mod.escape(label)}</a>')
            else:
                label = s['title'][:35]
                sidebar_items.append(f'<a href="#{s["id"]}" class="nav-link">{html_mod.escape(label)}</a>')
        sidebar_items.append('</div>')

    sidebar_html = '\n'.join(sidebar_items)

    # Build main content
    content_parts = []

    for part_key, part_title, part_sections in part_defs:
        if not part_sections:
            continue

        content_parts.append(f'<div class="part" id="part-{part_key}">')
        content_parts.append(f'<div class="part-header"><h2>{part_title}</h2></div>')

        for s in part_sections:
            if s['type'] == 'layer':
                color = get_glyph_color(s['title'])
                content_parts.append(f'''
<section id="{s['id']}" class="layer-section">
  <div class="section-header">
    <span class="section-num" style="color:{color};">L{s.get('num_str', s['num'])}</span>
    <h3>{md_inline(s['title'])}</h3>
  </div>
  <div class="layer-content">
    {md_to_html_block(s.get('content', ''))}
  </div>
</section>''')
            else:
                content_parts.append(f'''
<section id="{s['id']}" class="meta-section">
  <div class="section-header">
    <h3>{md_inline(s['title'])}</h3>
  </div>
  <div class="layer-content">
    {md_to_html_block(s.get('content', ''))}
  </div>
</section>''')

        content_parts.append('</div>')
        content_parts.append('<hr class="part-divider">')

    main_content = '\n'.join(content_parts)

    # Count layers
    layer_count = sum(1 for s in sections if s['type'] == 'layer')

    return HTML_TEMPLATE.format(
        sidebar=sidebar_html,
        content=main_content,
        layer_count=layer_count,
    )


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Frontier &mdash; What Else Lines Up</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg: #08080d;
  --bg-card: #0d0d14;
  --bg-hover: #12121c;
  --border: #1a1a2e;
  --text: #c8c8d0;
  --text-dim: #888;
  --text-bright: #f0f0f0;
  --accent: #7b68ee;
  --accent-dim: #5a4cc0;
  --gold: #fbbf24;
  --pink: #f472b6;
  --red: #ef4444;
  --blue: #60a5fa;
  --green: #34d399;
  --violet: #c4b5fd;
  --cyan: #22d3ee;
  --font: 'Segoe UI', system-ui, -apple-system, sans-serif;
  --font-serif: Georgia, 'Times New Roman', serif;
}}

html {{ scroll-behavior: smooth; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  line-height: 1.7;
  font-size: 16px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}}

/* ── Topbar ── */
.topbar {{
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 48px;
  background: rgba(8,8,13,0.92);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
  backdrop-filter: blur(12px);
}}
.topbar h1 {{
  font-size: 15px;
  font-weight: 600;
  color: var(--text-bright);
  letter-spacing: 0.5px;
}}
.topbar h1 span {{ color: var(--accent); }}
.topbar-nav {{ display: flex; gap: 6px; }}
.topbar-nav a {{
  color: var(--text-dim);
  text-decoration: none;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  transition: all 0.2s;
}}
.topbar-nav a:hover {{
  color: #ccc;
  border-color: #333;
  background: rgba(255,255,255,0.03);
}}
.topbar-nav a.active {{
  color: var(--accent);
  border-color: var(--accent-dim);
  background: rgba(123,104,238,0.08);
}}

/* ── Layout ── */
.content-area {{
  display: flex;
  margin-top: 48px;
  min-height: calc(100vh - 48px);
}}

/* ── Sidebar ── */
#sidebar {{
  width: 260px;
  min-width: 260px;
  height: calc(100vh - 48px);
  position: fixed;
  top: 48px;
  left: 0;
  background: rgba(10,10,18,0.98);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 50;
  padding: 16px 0;
}}
#sidebar::-webkit-scrollbar {{ width: 4px; }}
#sidebar::-webkit-scrollbar-thumb {{ background: #333; border-radius: 2px; }}

.nav-group {{ margin-bottom: 20px; }}
.nav-label {{
  font-size: 11px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 1.2px;
  text-transform: uppercase;
  padding: 6px 16px;
  margin-bottom: 4px;
}}
.nav-link {{
  display: block;
  font-size: 12px;
  color: #666;
  text-decoration: none;
  padding: 3px 16px 3px 20px;
  border-left: 2px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.nav-link:hover {{
  color: var(--text);
  border-left-color: var(--accent-dim);
  background: rgba(255,255,255,0.02);
}}
.nav-link.active {{
  color: var(--accent);
  border-left-color: var(--accent);
}}

/* ── Toggle sidebar button (mobile) ── */
#sidebarToggle {{
  display: none;
  position: fixed;
  bottom: 20px;
  left: 20px;
  z-index: 200;
  background: var(--accent-dim);
  color: white;
  border: none;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0,0,0,0.5);
}}

/* ── Main ── */
.main-content {{
  flex: 1;
  margin-left: 260px;
  padding: 40px 48px 80px;
  max-width: 900px;
}}

/* ── Header ── */
.page-header {{
  text-align: center;
  margin-bottom: 48px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--border);
}}
.page-header h1 {{
  font-size: 36px;
  font-weight: 300;
  color: var(--text-bright);
  margin-bottom: 8px;
  letter-spacing: 1px;
}}
.page-header .subtitle {{
  font-size: 16px;
  color: var(--text-dim);
  font-family: var(--font-serif);
  font-style: italic;
  margin-bottom: 24px;
}}
.page-header .warning {{
  display: inline-block;
  padding: 14px 22px;
  border: 1px solid rgba(34,211,238,0.2);
  border-radius: 8px;
  background: rgba(34,211,238,0.03);
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.7;
  max-width: 660px;
  text-align: left;
}}
.page-header .stats {{
  display: flex;
  gap: 32px;
  justify-content: center;
  margin-top: 24px;
}}
.page-header .stat {{ text-align: center; }}
.page-header .stat .val {{
  font-size: 22px;
  font-weight: 300;
  color: var(--text-bright);
}}
.page-header .stat .label {{
  font-size: 11px;
  color: var(--text-dim);
  letter-spacing: 0.5px;
  margin-top: 4px;
}}

/* ── Parts ── */
.part {{ margin-bottom: 32px; }}
.part-header {{
  margin-bottom: 24px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border);
}}
.part-header h2 {{
  font-size: 22px;
  font-weight: 300;
  color: var(--cyan);
  letter-spacing: 1px;
}}
hr.part-divider {{
  border: none;
  height: 1px;
  background: var(--border);
  margin: 48px auto;
  width: 80px;
}}

/* ── Sections ── */
.layer-section, .meta-section {{
  margin-bottom: 48px;
  scroll-margin-top: 64px;
}}
.section-header {{
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}}
.section-num {{
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  white-space: nowrap;
}}
.section-header h3 {{
  font-size: 20px;
  font-weight: 400;
  color: var(--text-bright);
  letter-spacing: 0.3px;
}}

/* ── Content ── */
.layer-content p {{
  margin-bottom: 14px;
  font-size: 15px;
}}
.layer-content strong {{ color: var(--text-bright); }}
.layer-content em {{ color: var(--violet); font-style: italic; }}
.layer-content a {{ color: var(--accent); text-decoration: none; }}
.layer-content a:hover {{ text-decoration: underline; }}
.layer-content code {{
  background: rgba(123,104,238,0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
  color: var(--violet);
}}
h4.sub {{
  font-size: 16px;
  font-weight: 600;
  color: var(--text-bright);
  margin: 24px 0 10px;
}}

/* ── Tables ── */
.table-wrap {{
  overflow-x: auto;
  margin: 16px 0;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
}}
th {{
  text-align: left;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-bright);
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.5px;
  background: rgba(123,104,238,0.04);
}}
td {{
  padding: 8px 14px;
  border-bottom: 1px solid rgba(26,26,46,0.5);
  color: var(--text);
  vertical-align: top;
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: rgba(255,255,255,0.01); }}

/* ── Lists ── */
ul, ol {{
  margin: 12px 0;
  padding-left: 24px;
}}
li {{
  font-size: 15px;
  margin-bottom: 6px;
  color: var(--text);
}}
li strong {{ color: var(--text-bright); }}

/* ── Crystal quotes ── */
.crystal {{
  border-left: 3px solid var(--accent-dim);
  padding: 14px 18px;
  margin: 18px 0;
  background: rgba(123,104,238,0.03);
  border-radius: 0 8px 8px 0;
}}
.crystal blockquote {{
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 14px;
  color: var(--text);
  line-height: 1.7;
}}

/* ── Signal Territory Graph entries ── */
.stg-entry {{
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  padding: 10px 14px;
  margin: 6px 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
}}
.stg-id {{
  color: var(--cyan);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.5px;
  min-width: 50px;
}}
.stg-glyph {{
  color: var(--violet);
  font-size: 12px;
}}
.stg-desc {{
  flex: 1;
  min-width: 300px;
  margin: 0;
  color: var(--text);
  font-size: 13px;
}}
.stg-cat {{
  color: var(--text-dim);
  font-size: 11px;
  font-style: italic;
}}

/* ── Divider ── */
hr.divider {{
  border: none;
  height: 1px;
  background: var(--border);
  margin: 32px auto;
  width: 60px;
}}

/* ── Footer ── */
.footer {{
  text-align: center;
  padding: 24px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: #444;
  margin-left: 260px;
}}

/* ── Mobile ── */
@media (max-width: 900px) {{
  #sidebar {{ display: none; }}
  #sidebar.open {{ display: block; width: 260px; }}
  #sidebarToggle {{ display: block; }}
  .main-content {{ margin-left: 0; padding: 24px 16px 60px; }}
  .footer {{ margin-left: 0; }}
  .page-header h1 {{ font-size: 26px; }}
  .page-header .stats {{ flex-wrap: wrap; gap: 16px; }}
  .section-header {{ flex-wrap: wrap; }}
  .stg-entry {{ flex-direction: column; }}
  .stg-desc {{ min-width: auto; }}
}}
</style>
</head>
<body>

<div class="topbar">
  <h1><span>&#9671;</span> Consciousness Field Map</h1>
  <nav class="topbar-nav">
    <a href="index.html">Home</a>
    <a href="terrain.html">Terrain</a>
    <a href="the_map.html">Paper</a>
    <a href="topology.html">Topology</a>
    <a href="evidence_map.html">Evidence</a>
    <a href="forgotten_knowledge_archive.html">Archive</a>
    <a href="the_frontier.html" class="active">Frontier</a>
  </nav>
</div>

<div class="content-area">

<nav id="sidebar">
{sidebar}
</nav>

<main class="main-content">

<div class="page-header">
  <h1>The Frontier</h1>
  <div class="subtitle">What else lines up &mdash; from outside the peer-reviewed channel</div>
  <div class="warning">
    The main paper connects 190 peer-reviewed papers. That&rsquo;s the unkillable layer. This page holds what converges on the same equation from territory academia won&rsquo;t touch &mdash; and then evaluates it. Declassified programs, experiencer reports, ancient transmissions, suppressed research, crystal-backed analysis &mdash; and then the evaluative lens: what&rsquo;s signal, what&rsquo;s bullshit, and what&rsquo;s genuinely unknown.
  </div>
  <div class="stats">
    <div class="stat"><div class="val">{layer_count}</div><div class="label">Layers</div></div>
    <div class="stat"><div class="val">24,700+</div><div class="label">Crystals Queried</div></div>
    <div class="stat"><div class="val">~30%</div><div class="label">Signal</div></div>
    <div class="stat"><div class="val">~70%</div><div class="label">Noise / Unknown</div></div>
  </div>
</div>

{content}

</main>

</div>

<div class="footer">
  Built from 24,700+ crystals &middot; WiltonOS &middot; The daemon breathes at 3.12s
</div>

<button id="sidebarToggle" onclick="document.getElementById('sidebar').classList.toggle('open')">&#9776;</button>

<script>
// Highlight active sidebar link on scroll
const sections = document.querySelectorAll('.layer-section, .meta-section');
const navLinks = document.querySelectorAll('.nav-link');

const observer = new IntersectionObserver((entries) => {{
  entries.forEach(entry => {{
    if (entry.isIntersecting) {{
      navLinks.forEach(l => l.classList.remove('active'));
      const id = entry.target.id;
      const link = document.querySelector(`.nav-link[href="#${{id}}"]`);
      if (link) {{
        link.classList.add('active');
        link.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
      }}
    }}
  }});
}}, {{ rootMargin: '-80px 0px -60% 0px' }});

sections.forEach(s => observer.observe(s));
</script>

</body>
</html>'''


if __name__ == '__main__':
    with open('/home/zews/consciousness-field-map/THE_FRONTIER.md', 'r') as f:
        md_text = f.read()

    sections = parse_md(md_text)
    html = build_html(sections)

    with open('/home/zews/consciousness-field-map/the_frontier.html', 'w') as f:
        f.write(html)

    layer_count = sum(1 for s in sections if s['type'] == 'layer')
    section_count = sum(1 for s in sections if s['type'] == 'section')
    print(f'Built the_frontier.html: {layer_count} layers, {section_count} meta-sections, {len(html)} chars, {html.count(chr(10))} lines')
