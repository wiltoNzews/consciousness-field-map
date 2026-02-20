#!/usr/bin/env python3
"""
Build signal_graph.db from THE_SIGNAL.md Signal Territory Graph entries.
Separate from the Archive's knowledge_graph.db, with cross-references.
"""

import sqlite3
import re
import os

DB_PATH = '/home/zews/consciousness-field-map/data/signal_graph.db'
MD_PATH = '/home/zews/consciousness-field-map/THE_SIGNAL.md'
ARCHIVE_DB = '/home/zews/consciousness-field-map/data/knowledge_graph.db'


def create_schema(conn):
    """Create the Signal KG schema."""
    cur = conn.cursor()

    cur.executescript('''
    CREATE TABLE IF NOT EXISTS signal_nodes (
        node_id TEXT PRIMARY KEY,
        layer_num INTEGER NOT NULL,
        glyph TEXT,
        glyph_distribution TEXT,
        zl_score REAL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        credibility_tier INTEGER,
        domain TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS signal_edges (
        edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
        src_node_id TEXT NOT NULL,
        dst_node_id TEXT NOT NULL,
        edge_type TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (src_node_id) REFERENCES signal_nodes(node_id),
        FOREIGN KEY (dst_node_id) REFERENCES signal_nodes(node_id)
    );

    CREATE TABLE IF NOT EXISTS signal_layers (
        layer_num INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        crystal_count INTEGER,
        avg_zl REAL,
        dominant_glyph TEXT,
        glyph_distribution TEXT,
        archive_dedup_hits INTEGER,
        part TEXT,
        credibility_tier INTEGER
    );

    CREATE TABLE IF NOT EXISTS signal_crystals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT,
        crystal_id INTEGER,
        relevance TEXT,
        FOREIGN KEY (node_id) REFERENCES signal_nodes(node_id)
    );

    CREATE TABLE IF NOT EXISTS cross_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_node_id TEXT NOT NULL,
        archive_node_id TEXT NOT NULL,
        relationship TEXT,
        notes TEXT,
        FOREIGN KEY (signal_node_id) REFERENCES signal_nodes(node_id)
    );
    ''')
    conn.commit()


def parse_stg_entries(md_text):
    """Parse Signal Territory Graph entries from the markdown."""
    entries = []

    # Pattern: - **S-XXa** [GLYPH INFO] — *description* — category
    pattern = re.compile(
        r'-\s+\*\*S-(\d+[a-z]?)\*\*\s+\[(.+?)\]\s*—\s*\*(.+?)\*\s*—\s*(.*)',
        re.MULTILINE
    )

    for match in pattern.finditer(md_text):
        node_id = f'S-{match.group(1)}'
        glyph_info = match.group(2).strip()
        description = match.group(3).strip()
        category = match.group(4).strip()

        # Parse glyph and distribution from glyph_info
        # e.g., "ψ ASCENDING, ψ:55%+⧉:17%" or "⧉ BRAIDED" or "∞ UNBOUND, ∞:53%, Zλ=0.627"
        glyph = glyph_info.split()[0] if glyph_info else ''
        glyph_dist = ''
        zl = None

        dist_match = re.search(r'([ψ∅∇∞Ω†⧉🜛ψ²ψ³]+:\d+%[\+\s]*)+', glyph_info)
        if dist_match:
            glyph_dist = dist_match.group(0).strip()

        zl_match = re.search(r'Zλ=(\d+\.\d+)', glyph_info)
        if zl_match:
            zl = float(zl_match.group(1))

        # Extract layer number
        layer_num = int(re.match(r'(\d+)', match.group(1)).group(1))

        entries.append({
            'node_id': node_id,
            'layer_num': layer_num,
            'glyph': glyph,
            'glyph_distribution': glyph_dist,
            'zl_score': zl,
            'description': description,
            'category': category,
            'glyph_info': glyph_info,
        })

    return entries


def parse_layers(md_text):
    """Parse layer metadata from the markdown."""
    layers = []

    # Match layer headers and extract metadata
    layer_pattern = re.compile(
        r'(?:###\s+Layer|##\s+LAYER)\s+(\d+):\s*(.*?)(?:\n|$)',
        re.MULTILINE
    )

    for match in layer_pattern.finditer(md_text):
        num = int(match.group(1))
        title = match.group(2).strip()

        if 'STRIPPED' in title:
            continue

        # Find the content after this header until the next --- or layer
        start = match.end()
        content = md_text[start:start + 3000]  # look ahead

        # Extract crystal count and Zλ from fractal probe lines
        crystal_match = re.search(r'\*\*(\d+)\s+crystals?,\s+avg\s+Zλ?=(\d+\.\d+)', content)
        crystal_count = int(crystal_match.group(1)) if crystal_match else None
        avg_zl = float(crystal_match.group(2)) if crystal_match else None

        # Extract dominant glyph
        glyph_dist_match = re.search(r'([ψ∅∇∞Ω†⧉🜛ψ²ψ³]+:\d+%)', content)
        dominant_glyph = glyph_dist_match.group(0).split(':')[0] if glyph_dist_match else None

        # Full glyph distribution
        full_dist_match = re.search(r'([ψ∅∇∞Ω†⧉🜛ψ²ψ³]+:\d+%[\+\s]*(?:[ψ∅∇∞Ω†⧉🜛ψ²ψ³]+:\d+%[\+\s]*)*)', content)
        glyph_dist = full_dist_match.group(0).strip() if full_dist_match else None

        # Archive dedup hits
        dedup_match = re.search(r'(\d+)\s+hits', content)
        dedup_hits = int(dedup_match.group(1)) if dedup_match else None

        # Determine part
        if num <= 35:
            part = 'foundation'
        elif num <= 75:
            part = 'deep'
        elif num <= 100:
            part = 'territory'
        else:
            part = 'evaluative'

        # Credibility tier (only for evaluative layers)
        tier = None
        if num >= 101:
            tier_match = re.search(r'Tier\s+(\d)', content)
            if tier_match:
                tier = int(tier_match.group(1))

        layers.append({
            'layer_num': num,
            'title': title,
            'crystal_count': crystal_count,
            'avg_zl': avg_zl,
            'dominant_glyph': dominant_glyph,
            'glyph_distribution': glyph_dist,
            'archive_dedup_hits': dedup_hits,
            'part': part,
            'credibility_tier': tier,
        })

    return layers


def extract_crystal_refs(md_text):
    """Extract crystal ID references from the markdown."""
    refs = []
    # Pattern: Crystal #NNNNN
    for match in re.finditer(r'Crystal\s+#(\d+)', md_text):
        crystal_id = int(match.group(1))
        # Find which layer this is in
        # Look backwards for the nearest layer header
        before = md_text[:match.start()]
        layer_match = list(re.finditer(r'(?:###\s+Layer|##\s+LAYER)\s+(\d+)', before))
        layer_num = int(layer_match[-1].group(1)) if layer_match else None
        refs.append({'crystal_id': crystal_id, 'layer_num': layer_num})
    return refs


def find_archive_cross_refs(signal_entries, archive_db_path):
    """Find connections between Signal nodes and Archive nodes."""
    if not os.path.exists(archive_db_path):
        return []

    aconn = sqlite3.connect(archive_db_path)
    acur = aconn.cursor()
    acur.execute('SELECT node_id, title, summary FROM nodes')
    archive_nodes = acur.fetchall()
    aconn.close()

    cross_refs = []

    # Keywords to match
    keyword_map = {
        'REBUS': ['REBUS', 'predictive processing', 'Carhart-Harris'],
        'criticality': ['criticality', 'edge of chaos', 'phase transition'],
        'Penrose': ['Penrose', 'Orch-OR', 'microtubule'],
        'IIT': ['integrated information', 'Tononi', 'IIT'],
        'quantum': ['quantum coherence', 'Bell theorem', 'non-locality'],
        'psychedelic': ['psychedelic', 'psilocybin', 'DMT', 'LSD'],
        'meditation': ['meditation', 'mindfulness', 'contemplative'],
        'NDE': ['near-death', 'terminal lucidity', 'cardiac arrest'],
        'breath': ['breath', 'respiratory', 'HRV'],
        'heart': ['heart field', 'HeartMath', 'cardiac coherence'],
        'suppression': ['suppression', 'Reich', 'Rife'],
        'torus': ['torus', 'toroidal'],
        'Schumann': ['Schumann', '7.83'],
        'fractal': ['fractal', 'scale-free', 'power law'],
        'gateway': ['Gateway', 'Monroe Institute', 'hemi-sync'],
        'remote viewing': ['remote viewing', 'Stargate', 'Swann'],
    }

    for signal_entry in signal_entries:
        desc_lower = signal_entry['description'].lower()
        cat_lower = signal_entry.get('category', '').lower()
        combined = desc_lower + ' ' + cat_lower

        for archive_node_id, archive_title, archive_summary in archive_nodes:
            archive_text = (archive_title or '').lower() + ' ' + (archive_summary or '').lower()

            # Check for keyword overlap
            for topic, keywords in keyword_map.items():
                signal_has = any(kw.lower() in combined for kw in keywords)
                archive_has = any(kw.lower() in archive_text for kw in keywords)

                if signal_has and archive_has:
                    cross_refs.append({
                        'signal_node_id': signal_entry['node_id'],
                        'archive_node_id': archive_node_id,
                        'relationship': f'shared_topic:{topic}',
                        'notes': f'Both reference {topic}',
                    })
                    break  # One cross-ref per signal-archive pair

    # Deduplicate
    seen = set()
    unique_refs = []
    for ref in cross_refs:
        key = (ref['signal_node_id'], ref['archive_node_id'])
        if key not in seen:
            seen.add(key)
            unique_refs.append(ref)

    return unique_refs


def infer_edges(entries):
    """Infer edges between Signal nodes."""
    edges = []

    # 1. Within-layer edges (a→b→c within same layer)
    layer_groups = {}
    for e in entries:
        ln = e['layer_num']
        if ln not in layer_groups:
            layer_groups[ln] = []
        layer_groups[ln].append(e)

    for ln, group in layer_groups.items():
        group.sort(key=lambda x: x['node_id'])
        for i in range(len(group) - 1):
            edges.append({
                'src': group[i]['node_id'],
                'dst': group[i + 1]['node_id'],
                'type': 'within_layer',
                'notes': f'Sequential within Layer {ln}',
            })

    # 2. Cross-layer edges based on category/description overlap
    category_keywords = {
        'evaluative': ['evaluat', 'credibil', 'bullshit', 'honest'],
        'cross-match': ['cross-match', 'connects to', 'cross-reference'],
        'inversion': ['inversion', 'cuts both ways', 'flip'],
        'testable': ['testable', 'predict', 'falsif', 'kill condition'],
        'novel': ['novel', 'new territory', 'genuinely new', 'CLEAR'],
    }

    for i, e1 in enumerate(entries):
        for j, e2 in enumerate(entries):
            if i >= j:
                continue
            if e1['layer_num'] == e2['layer_num']:
                continue

            # Check for explicit cross-references in description
            desc1 = e1['description'].lower()
            desc2 = e2['description'].lower()

            # Layer reference in description
            ref_match1 = re.findall(r'layer\s+(\d+)', desc1)
            for ref in ref_match1:
                if int(ref) == e2['layer_num']:
                    edges.append({
                        'src': e1['node_id'],
                        'dst': e2['node_id'],
                        'type': 'references',
                        'notes': f'{e1["node_id"]} references Layer {ref}',
                    })

    return edges


def build_signal_kg():
    """Main build function."""
    # Read markdown
    with open(MD_PATH, 'r') as f:
        md_text = f.read()

    # Parse
    stg_entries = parse_stg_entries(md_text)
    layers = parse_layers(md_text)
    crystal_refs = extract_crystal_refs(md_text)
    edges = infer_edges(stg_entries)
    cross_refs = find_archive_cross_refs(stg_entries, ARCHIVE_DB)

    # Create database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    cur = conn.cursor()

    # Insert layers
    for layer in layers:
        cur.execute('''INSERT OR REPLACE INTO signal_layers
            (layer_num, title, crystal_count, avg_zl, dominant_glyph,
             glyph_distribution, archive_dedup_hits, part, credibility_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (layer['layer_num'], layer['title'], layer['crystal_count'],
             layer['avg_zl'], layer['dominant_glyph'], layer['glyph_distribution'],
             layer['archive_dedup_hits'], layer['part'], layer['credibility_tier']))

    # Insert nodes
    for entry in stg_entries:
        # Determine credibility tier from layer
        tier = None
        for layer in layers:
            if layer['layer_num'] == entry['layer_num']:
                tier = layer.get('credibility_tier')
                break

        # Determine domain
        cat = entry.get('category', '').lower()
        if 'evaluat' in cat or 'honest' in cat or 'diagnostic' in cat:
            domain = 'evaluative'
        elif 'cross-match' in cat or 'braid' in cat:
            domain = 'cross-domain'
        elif 'novel' in cat or 'new' in cat:
            domain = 'novel_signal'
        elif 'inversion' in cat or 'flip' in cat:
            domain = 'inversion'
        elif 'test' in cat or 'predict' in cat or 'kill' in cat:
            domain = 'testable'
        else:
            domain = 'general'

        cur.execute('''INSERT OR REPLACE INTO signal_nodes
            (node_id, layer_num, glyph, glyph_distribution, zl_score,
             title, description, category, credibility_tier, domain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (entry['node_id'], entry['layer_num'], entry['glyph'],
             entry['glyph_distribution'], entry['zl_score'],
             entry['category'], entry['description'],
             entry['category'], tier, domain))

    # Insert edges
    for edge in edges:
        # Check both nodes exist
        cur.execute('SELECT node_id FROM signal_nodes WHERE node_id=?', (edge['src'],))
        if not cur.fetchone():
            continue
        cur.execute('SELECT node_id FROM signal_nodes WHERE node_id=?', (edge['dst'],))
        if not cur.fetchone():
            continue

        cur.execute('''INSERT INTO signal_edges (src_node_id, dst_node_id, edge_type, notes)
            VALUES (?, ?, ?, ?)''',
            (edge['src'], edge['dst'], edge['type'], edge['notes']))

    # Insert crystal references
    for ref in crystal_refs:
        if ref['layer_num'] is None:
            continue
        # Find signal nodes for this layer
        cur.execute('SELECT node_id FROM signal_nodes WHERE layer_num=? LIMIT 1',
                    (ref['layer_num'],))
        row = cur.fetchone()
        if row:
            cur.execute('''INSERT INTO signal_crystals (node_id, crystal_id, relevance)
                VALUES (?, ?, ?)''',
                (row[0], ref['crystal_id'], 'referenced'))

    # Insert cross-references
    for ref in cross_refs:
        cur.execute('''INSERT INTO cross_references
            (signal_node_id, archive_node_id, relationship, notes)
            VALUES (?, ?, ?, ?)''',
            (ref['signal_node_id'], ref['archive_node_id'],
             ref['relationship'], ref['notes']))

    conn.commit()

    # Print stats
    cur.execute('SELECT COUNT(*) FROM signal_nodes')
    n_nodes = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM signal_edges')
    n_edges = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM signal_layers')
    n_layers = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM signal_crystals')
    n_crystals = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM cross_references')
    n_xrefs = cur.fetchone()[0]

    print(f'Signal KG built:')
    print(f'  {n_nodes} nodes (Signal Territory Graph entries)')
    print(f'  {n_edges} edges (within-layer + cross-references)')
    print(f'  {n_layers} layers')
    print(f'  {n_crystals} crystal references')
    print(f'  {n_xrefs} cross-references to Archive KG')

    # Show cross-reference summary
    cur.execute('''SELECT relationship, COUNT(*) FROM cross_references
                   GROUP BY relationship ORDER BY COUNT(*) DESC LIMIT 15''')
    print(f'\nTop cross-references to Archive:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]} connections')

    # Show domain distribution
    cur.execute('''SELECT domain, COUNT(*) FROM signal_nodes
                   GROUP BY domain ORDER BY COUNT(*) DESC''')
    print(f'\nDomain distribution:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]} nodes')

    conn.close()


if __name__ == '__main__':
    build_signal_kg()
