#!/usr/bin/env python3
"""
Knowledge Graph Explorer
========================

Interactive command-line tool for exploring the consciousness research
knowledge graph. Designed for researchers who want to verify claims,
trace evidence chains, and understand cross-domain connections.

Database schema:
  - nodes: Research concepts, mechanisms, models, claims, measurements
  - edges: Typed relationships between nodes (with confidence and layer)
  - evidence: Peer-reviewed citations, books, and synthesis records
  - edge_evidence: Links edges to their supporting evidence
  - node_aliases: Alternative names for nodes (for flexible search)
  - measurements: Acoustic/physical measurement data at sites

Usage:
  python explore.py summary
  python explore.py search "vagal"
  python explore.py node mechanism:vagal_regulation
  python explore.py path mechanism:vagal_regulation claim:coherence_is_aperiodic_plus_modulation
  python explore.py domain BIOLOGY
  python explore.py evidence ev:bak1987
  python explore.py convergence
  python explore.py export-csv
  python explore.py mdi

No external dependencies required (Python 3.7+ stdlib only).
"""

import argparse
import csv
import os
import sqlite3
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DB = SCRIPT_DIR / "data" / "knowledge_graph.db"


def connect(db_path: str) -> sqlite3.Connection:
    """Open a read-only connection to the knowledge graph database."""
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def wrap(text: str, width: int = 78, indent: str = "  ") -> str:
    """Word-wrap a block of text with a hanging indent."""
    if not text:
        return f"{indent}(none)"
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent)


def table_print(headers: list, rows: list, col_widths: list = None):
    """Print a simple aligned table to stdout."""
    if not rows:
        print("  (no results)")
        return

    # Auto-calculate widths if not provided
    if col_widths is None:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Cap widths at 60 to avoid runaway columns
    col_widths = [min(w, 60) for w in col_widths]

    # Header
    header_line = "  ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(f"  {header_line}")
    print(f"  {'  '.join('-' * w for w in col_widths)}")

    # Rows
    for row in rows:
        cells = []
        for cell, w in zip(row, col_widths):
            s = str(cell) if cell is not None else ""
            if len(s) > w:
                s = s[:w - 3] + "..."
            cells.append(s.ljust(w))
        print(f"  {'  '.join(cells)}")


def section(title: str):
    """Print a section header."""
    print()
    print(f"{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")
    print()


def subsection(title: str):
    """Print a subsection header."""
    print()
    print(f"  --- {title} ---")
    print()


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_summary(conn: sqlite3.Connection):
    """Print a high-level overview of the knowledge graph."""
    c = conn.cursor()

    node_count = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edge_count = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    evidence_count = c.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    alias_count = c.execute("SELECT COUNT(*) FROM node_aliases").fetchone()[0]
    measurement_count = c.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
    edge_evidence_count = c.execute("SELECT COUNT(*) FROM edge_evidence").fetchone()[0]

    section("KNOWLEDGE GRAPH SUMMARY")

    print(f"  Nodes:              {node_count:>6}")
    print(f"  Edges:              {edge_count:>6}")
    print(f"  Evidence records:   {evidence_count:>6}")
    print(f"  Edge-evidence links:{edge_evidence_count:>6}")
    print(f"  Node aliases:       {alias_count:>6}")
    print(f"  Measurements:       {measurement_count:>6}")

    # Domain breakdown
    subsection("Nodes by Domain")
    rows = c.execute(
        "SELECT domain, COUNT(*) as cnt FROM nodes "
        "GROUP BY domain ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Domain", "Count"], [(r["domain"], r["cnt"]) for r in rows])

    # Node type breakdown
    subsection("Nodes by Type")
    rows = c.execute(
        "SELECT node_type, COUNT(*) as cnt FROM nodes "
        "GROUP BY node_type ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Node Type", "Count"],
                [(r["node_type"], r["cnt"]) for r in rows])

    # Confidence breakdown
    subsection("Nodes by Confidence Level")
    rows = c.execute(
        "SELECT confidence, COUNT(*) as cnt FROM nodes "
        "GROUP BY confidence ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Confidence", "Count"],
                [(r["confidence"], r["cnt"]) for r in rows])

    # Edge layer breakdown
    subsection("Edges by Layer")
    rows = c.execute(
        "SELECT edge_layer, COUNT(*) as cnt FROM edges "
        "WHERE edge_layer IS NOT NULL "
        "GROUP BY edge_layer ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Edge Layer", "Count"],
                [(r["edge_layer"], r["cnt"]) for r in rows])

    # Edge type breakdown
    subsection("Edges by Type")
    rows = c.execute(
        "SELECT edge_type, COUNT(*) as cnt FROM edges "
        "GROUP BY edge_type ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Edge Type", "Count"],
                [(r["edge_type"], r["cnt"]) for r in rows])

    # Evidence type breakdown
    subsection("Evidence by Type")
    rows = c.execute(
        "SELECT evidence_type, COUNT(*) as cnt FROM evidence "
        "GROUP BY evidence_type ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Evidence Type", "Count"],
                [(r["evidence_type"], r["cnt"]) for r in rows])

    # Verification status breakdown
    subsection("Evidence by Verification Status")
    rows = c.execute(
        "SELECT verification_status, COUNT(*) as cnt FROM evidence "
        "GROUP BY verification_status ORDER BY cnt DESC"
    ).fetchall()
    table_print(["Verification Status", "Count"],
                [(r["verification_status"], r["cnt"]) for r in rows])

    print()


def cmd_search(conn: sqlite3.Connection, term: str):
    """Search nodes by keyword in title, summary, aliases, and node_id."""
    c = conn.cursor()
    like = f"%{term}%"

    section(f"SEARCH RESULTS FOR: \"{term}\"")

    # Search across node fields and aliases
    rows = c.execute("""
        SELECT DISTINCT n.node_id, n.title, n.domain, n.node_type,
               n.confidence, n.summary
        FROM nodes n
        LEFT JOIN node_aliases a ON n.node_id = a.node_id
        WHERE n.title LIKE ?
           OR n.summary LIKE ?
           OR n.node_id LIKE ?
           OR a.alias LIKE ?
        ORDER BY n.domain, n.title
    """, (like, like, like, like)).fetchall()

    if not rows:
        print("  No matching nodes found.")
        print()
        return

    print(f"  Found {len(rows)} matching node(s):")
    print()

    for row in rows:
        print(f"  [{row['node_type']}] {row['node_id']}")
        print(f"    Title:      {row['title']}")
        print(f"    Domain:     {row['domain']}")
        print(f"    Confidence: {row['confidence']}")
        if row["summary"]:
            print(wrap(row["summary"], indent="    Summary:    "))

        # Show connections for this node
        out_edges = c.execute(
            "SELECT edge_type, dst_node_id, edge_layer FROM edges "
            "WHERE src_node_id = ?", (row["node_id"],)
        ).fetchall()
        in_edges = c.execute(
            "SELECT edge_type, src_node_id, edge_layer FROM edges "
            "WHERE dst_node_id = ?", (row["node_id"],)
        ).fetchall()

        if out_edges or in_edges:
            total_conn = len(out_edges) + len(in_edges)
            print(f"    Connections: {total_conn} "
                  f"({len(out_edges)} outgoing, {len(in_edges)} incoming)")
        print()

    print()


def cmd_node(conn: sqlite3.Connection, node_id: str):
    """Show full detail for a specific node."""
    c = conn.cursor()

    # Try exact match first, then try alias lookup
    row = c.execute("SELECT * FROM nodes WHERE node_id = ?",
                     (node_id,)).fetchone()

    if not row:
        # Check aliases
        alias_row = c.execute(
            "SELECT node_id FROM node_aliases WHERE alias = ?",
            (node_id,)
        ).fetchone()
        if alias_row:
            row = c.execute("SELECT * FROM nodes WHERE node_id = ?",
                             (alias_row["node_id"],)).fetchone()

    if not row:
        print(f"Error: Node '{node_id}' not found.", file=sys.stderr)
        print("  Hint: Use 'search' to find nodes by keyword.",
              file=sys.stderr)
        return

    section(f"NODE: {row['title']}")

    print(f"  ID:             {row['node_id']}")
    print(f"  Type:           {row['node_type']}")
    print(f"  Domain:         {row['domain']}")
    print(f"  Confidence:     {row['confidence']}")
    print(f"  Coherence class:{row['coherence_class']}")
    print(f"  Created:        {row['created_at']}")
    if row["source_crystal_id"]:
        print(f"  Source crystal:  #{row['source_crystal_id']}")
    if row["tags"]:
        print(f"  Tags:           {row['tags']}")
    print()
    print("  Summary:")
    print(wrap(row["summary"], indent="    "))

    # Aliases
    aliases = c.execute(
        "SELECT alias FROM node_aliases WHERE node_id = ?",
        (row["node_id"],)
    ).fetchall()
    if aliases:
        subsection("Aliases")
        for a in aliases:
            print(f"    - {a['alias']}")

    # Outgoing edges
    out_edges = c.execute("""
        SELECT e.edge_id, e.edge_type, e.dst_node_id, e.edge_layer,
               e.confidence, e.weight, e.notes, e.reviewer_attack,
               e.rewrite_suggestion, n.title as dst_title
        FROM edges e
        JOIN nodes n ON e.dst_node_id = n.node_id
        WHERE e.src_node_id = ?
        ORDER BY e.edge_layer, e.edge_type
    """, (row["node_id"],)).fetchall()

    if out_edges:
        subsection(f"Outgoing Edges ({len(out_edges)})")
        for e in out_edges:
            print(f"    -> [{e['edge_type']}] {e['dst_node_id']}")
            print(f"       \"{e['dst_title']}\"")
            print(f"       Layer: {e['edge_layer']}  "
                  f"Confidence: {e['confidence']}  "
                  f"Weight: {e['weight']}")
            if e["notes"]:
                print(f"       Notes: {e['notes']}")
            if e["reviewer_attack"]:
                print(f"       Reviewer attack: {e['reviewer_attack']}")
            if e["rewrite_suggestion"]:
                print(f"       Rewrite suggestion: {e['rewrite_suggestion']}")

            # Evidence for this edge
            ev_rows = c.execute("""
                SELECT ev.evidence_id, ev.citation, ev.verification_status,
                       ee.relevance
                FROM edge_evidence ee
                JOIN evidence ev ON ee.evidence_id = ev.evidence_id
                WHERE ee.edge_id = ?
                ORDER BY ee.relevance
            """, (e["edge_id"],)).fetchall()
            if ev_rows:
                for ev in ev_rows:
                    status = ev["verification_status"] or ""
                    rel = ev["relevance"] or ""
                    print(f"       [{rel}] {ev['citation']}")
                    print(f"              Status: {status}")
            print()

    # Incoming edges
    in_edges = c.execute("""
        SELECT e.edge_id, e.edge_type, e.src_node_id, e.edge_layer,
               e.confidence, e.weight, e.notes, n.title as src_title
        FROM edges e
        JOIN nodes n ON e.src_node_id = n.node_id
        WHERE e.dst_node_id = ?
        ORDER BY e.edge_layer, e.edge_type
    """, (row["node_id"],)).fetchall()

    if in_edges:
        subsection(f"Incoming Edges ({len(in_edges)})")
        for e in in_edges:
            print(f"    <- [{e['edge_type']}] {e['src_node_id']}")
            print(f"       \"{e['src_title']}\"")
            print(f"       Layer: {e['edge_layer']}  "
                  f"Confidence: {e['confidence']}  "
                  f"Weight: {e['weight']}")
            if e["notes"]:
                print(f"       Notes: {e['notes']}")

            # Evidence for this edge
            ev_rows = c.execute("""
                SELECT ev.evidence_id, ev.citation, ev.verification_status,
                       ee.relevance
                FROM edge_evidence ee
                JOIN evidence ev ON ee.evidence_id = ev.evidence_id
                WHERE ee.edge_id = ?
                ORDER BY ee.relevance
            """, (e["edge_id"],)).fetchall()
            if ev_rows:
                for ev in ev_rows:
                    status = ev["verification_status"] or ""
                    rel = ev["relevance"] or ""
                    print(f"       [{rel}] {ev['citation']}")
                    print(f"              Status: {status}")
            print()

    # Measurements (if this node is a site)
    measurements = c.execute(
        "SELECT * FROM measurements WHERE site_node_id = ?",
        (row["node_id"],)
    ).fetchall()
    if measurements:
        subsection("Measurements")
        for m in measurements:
            print(f"    ID:         {m['measurement_id']}")
            print(f"    Method:     {m['method']}")
            print(f"    Instrument: {m['instrument']}")
            print(f"    Peak Hz:    {m['peak_hz']}")
            print(f"    Reference:  {m['raw_ref']}")
            print(f"    Replications: {m['replication_count']}")
            if m["notes"]:
                print(f"    Notes:      {m['notes']}")
            print()

    print()


def cmd_path(conn: sqlite3.Connection, node_a: str, node_b: str):
    """Find shortest path between two nodes using BFS."""
    c = conn.cursor()

    # Validate both nodes exist
    for nid in (node_a, node_b):
        exists = c.execute(
            "SELECT node_id FROM nodes WHERE node_id = ?", (nid,)
        ).fetchone()
        if not exists:
            # Try alias
            alias = c.execute(
                "SELECT node_id FROM node_aliases WHERE alias = ?", (nid,)
            ).fetchone()
            if alias:
                if nid == node_a:
                    node_a = alias["node_id"]
                else:
                    node_b = alias["node_id"]
            else:
                print(f"Error: Node '{nid}' not found.", file=sys.stderr)
                return

    if node_a == node_b:
        print("  Start and end nodes are the same.")
        return

    # Build adjacency list (undirected for path-finding)
    edges = c.execute(
        "SELECT src_node_id, dst_node_id, edge_type, edge_layer FROM edges"
    ).fetchall()

    adj = defaultdict(list)
    for e in edges:
        adj[e["src_node_id"]].append(
            (e["dst_node_id"], e["edge_type"], e["edge_layer"], "->"))
        adj[e["dst_node_id"]].append(
            (e["src_node_id"], e["edge_type"], e["edge_layer"], "<-"))

    # BFS
    from collections import deque
    queue = deque([(node_a, [node_a], [])])
    visited = {node_a}

    found_path = None
    found_edges = None

    while queue:
        current, path, edge_info = queue.popleft()
        if current == node_b:
            found_path = path
            found_edges = edge_info
            break

        for neighbor, etype, elayer, direction in adj[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((
                    neighbor,
                    path + [neighbor],
                    edge_info + [(current, neighbor, etype, elayer, direction)]
                ))

    section(f"PATH: {node_a} -> {node_b}")

    if found_path is None:
        print("  No path found between these nodes.")
        print()
        return

    print(f"  Shortest path length: {len(found_path) - 1} edge(s)")
    print()

    # Display the path step by step
    for i, node in enumerate(found_path):
        title_row = c.execute(
            "SELECT title, domain FROM nodes WHERE node_id = ?", (node,)
        ).fetchone()
        title = title_row["title"] if title_row else "(unknown)"
        domain = title_row["domain"] if title_row else ""

        if i == 0:
            print(f"  START: {node}")
            print(f"         \"{title}\" [{domain}]")
        elif i == len(found_path) - 1:
            src, dst, etype, elayer, direction = found_edges[i - 1]
            arrow = f"{direction} [{etype}]"
            print(f"    {arrow}  (layer: {elayer})")
            print(f"  END:   {node}")
            print(f"         \"{title}\" [{domain}]")
        else:
            src, dst, etype, elayer, direction = found_edges[i - 1]
            arrow = f"{direction} [{etype}]"
            print(f"    {arrow}  (layer: {elayer})")
            print(f"  [{i}]    {node}")
            print(f"         \"{title}\" [{domain}]")

    print()


def cmd_domain(conn: sqlite3.Connection, domain_name: str):
    """List all nodes in a given domain."""
    c = conn.cursor()

    # Case-insensitive match
    rows = c.execute("""
        SELECT node_id, title, node_type, confidence, coherence_class, summary
        FROM nodes
        WHERE UPPER(domain) = UPPER(?)
        ORDER BY node_type, title
    """, (domain_name,)).fetchall()

    section(f"DOMAIN: {domain_name.upper()}")

    if not rows:
        print(f"  No nodes found in domain '{domain_name}'.")
        print(f"  Available domains:")
        for r in c.execute(
                "SELECT DISTINCT domain FROM nodes ORDER BY domain"):
            print(f"    - {r['domain']}")
        print()
        return

    print(f"  {len(rows)} node(s) in this domain:")
    print()

    # Group by node type
    by_type = defaultdict(list)
    for row in rows:
        by_type[row["node_type"]].append(row)

    for ntype in sorted(by_type.keys()):
        nodes = by_type[ntype]
        print(f"  {ntype} ({len(nodes)})")
        print(f"  {'-' * 50}")
        for n in nodes:
            conf = n["confidence"] or ""
            cc = n["coherence_class"] or ""
            print(f"    {n['node_id']}")
            print(f"      {n['title']}  [{conf}] [{cc}]")
        print()

    print()


def cmd_evidence(conn: sqlite3.Connection, identifier: str):
    """Show evidence detail. Accepts either an evidence_id or a node_id."""
    c = conn.cursor()

    # Check if this is an evidence_id
    ev_row = c.execute(
        "SELECT * FROM evidence WHERE evidence_id = ?", (identifier,)
    ).fetchone()

    if ev_row:
        # Show single evidence record and all edges it supports
        section(f"EVIDENCE: {ev_row['evidence_id']}")
        print(f"  Type:         {ev_row['evidence_type']}")
        print(f"  Citation:     {ev_row['citation']}")
        print(f"  Authors:      {ev_row['authors']}")
        print(f"  Year:         {ev_row['year']}")
        print(f"  Venue:        {ev_row['venue']}")
        print(f"  Verification: {ev_row['verification_status']}")
        if ev_row["url"]:
            print(f"  URL:          {ev_row['url']}")
        if ev_row["notes"]:
            print(f"  Notes:        {ev_row['notes']}")

        # Find edges that cite this evidence
        edge_links = c.execute("""
            SELECT ee.edge_id, ee.relevance, e.src_node_id, e.dst_node_id,
                   e.edge_type, e.edge_layer
            FROM edge_evidence ee
            JOIN edges e ON ee.edge_id = e.edge_id
            WHERE ee.evidence_id = ?
        """, (identifier,)).fetchall()

        if edge_links:
            subsection(f"Cited by {len(edge_links)} Edge(s)")
            for el in edge_links:
                print(f"    {el['src_node_id']} -> {el['dst_node_id']}")
                print(f"      Type: {el['edge_type']}  "
                      f"Layer: {el['edge_layer']}  "
                      f"Relevance: {el['relevance']}")
                print()

        print()
        return

    # Otherwise treat as a node_id and show all evidence linked via edges
    node_row = c.execute(
        "SELECT node_id, title FROM nodes WHERE node_id = ?", (identifier,)
    ).fetchone()

    if not node_row:
        # Try alias
        alias_row = c.execute(
            "SELECT node_id FROM node_aliases WHERE alias = ?", (identifier,)
        ).fetchone()
        if alias_row:
            node_row = c.execute(
                "SELECT node_id, title FROM nodes WHERE node_id = ?",
                (alias_row["node_id"],)
            ).fetchone()

    if not node_row:
        print(f"Error: '{identifier}' not found as evidence_id or node_id.",
              file=sys.stderr)
        return

    # Gather all evidence connected to this node's edges
    section(f"EVIDENCE FOR NODE: {node_row['title']}")
    print(f"  Node ID: {node_row['node_id']}")

    evidence_records = c.execute("""
        SELECT DISTINCT ev.*, ee.relevance, e.edge_type, e.edge_layer,
               e.src_node_id, e.dst_node_id
        FROM edges e
        JOIN edge_evidence ee ON e.edge_id = ee.edge_id
        JOIN evidence ev ON ee.evidence_id = ev.evidence_id
        WHERE e.src_node_id = ? OR e.dst_node_id = ?
        ORDER BY ev.year, ev.authors
    """, (node_row["node_id"], node_row["node_id"])).fetchall()

    if not evidence_records:
        print("  No evidence linked to this node's edges.")
        print()
        return

    # Deduplicate by evidence_id (an evidence record may appear for
    # multiple edges)
    seen = set()
    unique_evidence = []
    for ev in evidence_records:
        if ev["evidence_id"] not in seen:
            seen.add(ev["evidence_id"])
            unique_evidence.append(ev)

    print(f"  {len(unique_evidence)} unique evidence record(s):")
    print()

    for ev in unique_evidence:
        year_str = str(ev["year"]) if ev["year"] else "n/a"
        status = ev["verification_status"] or ""
        print(f"  [{year_str}] {ev['evidence_id']}")
        print(f"    {ev['citation']}")
        print(f"    Type: {ev['evidence_type']}  "
              f"Status: {status}  "
              f"Relevance: {ev['relevance']}")
        if ev["authors"]:
            print(f"    Authors: {ev['authors']}")
        if ev["venue"]:
            print(f"    Venue: {ev['venue']}")
        print()

    print()


def cmd_convergence(conn: sqlite3.Connection):
    """Show nodes connected to 3+ different domains (convergence points)."""
    c = conn.cursor()

    section("CONVERGENCE POINTS")
    print("  Nodes whose edges connect to 3 or more distinct domains.")
    print("  These represent cross-disciplinary convergence in the graph.")
    print()

    # For each node, find all domains of its neighbors (via edges in
    # both directions)
    nodes = c.execute("SELECT node_id, title, domain FROM nodes").fetchall()

    convergence_nodes = []

    for node in nodes:
        nid = node["node_id"]
        own_domain = node["domain"]

        neighbor_domains = c.execute("""
            SELECT DISTINCT n.domain
            FROM edges e
            JOIN nodes n ON (
                (e.dst_node_id = n.node_id AND e.src_node_id = ?)
                OR
                (e.src_node_id = n.node_id AND e.dst_node_id = ?)
            )
            WHERE n.domain IS NOT NULL
        """, (nid, nid)).fetchall()

        domains = set(r["domain"] for r in neighbor_domains)
        # Include the node's own domain
        if own_domain:
            domains.add(own_domain)

        if len(domains) >= 3:
            # Count edges
            edge_count = c.execute(
                "SELECT COUNT(*) FROM edges "
                "WHERE src_node_id = ? OR dst_node_id = ?",
                (nid, nid)
            ).fetchone()[0]

            convergence_nodes.append({
                "node_id": nid,
                "title": node["title"],
                "own_domain": own_domain,
                "connected_domains": sorted(domains),
                "domain_count": len(domains),
                "edge_count": edge_count,
            })

    # Sort by number of domains (desc), then edge count (desc)
    convergence_nodes.sort(key=lambda x: (x["domain_count"], x["edge_count"]),
                           reverse=True)

    if not convergence_nodes:
        print("  No convergence points found (no nodes connect 3+ domains).")
        print()
        return

    print(f"  {len(convergence_nodes)} convergence point(s) found:")
    print()

    for cn in convergence_nodes:
        domains_str = ", ".join(cn["connected_domains"])
        print(f"  {cn['node_id']}")
        print(f"    \"{cn['title']}\"")
        print(f"    Own domain: {cn['own_domain']}  |  "
              f"Edges: {cn['edge_count']}  |  "
              f"Domains touched: {cn['domain_count']}")
        print(f"    Domains: {domains_str}")
        print()

    print()


def cmd_mdi(conn: sqlite3.Connection, db_path: str):
    """Run the Modulation Dominance Index analysis."""
    section("MODULATION DOMINANCE INDEX (MDI) ANALYSIS")

    # Try to import from scripts/mdi_analysis.py
    scripts_dir = SCRIPT_DIR / "scripts"
    mdi_module_path = scripts_dir / "mdi_analysis.py"

    if not mdi_module_path.exists():
        print("  The MDI analysis module was not found at:")
        print(f"    {mdi_module_path}")
        print()
        print("  The MDI analysis quantifies whether the knowledge graph")
        print("  uses modulation/tuning language vs. generation/creation")
        print("  language when describing consciousness mechanisms.")
        print()
        print("  Formula: MDI = log((M + alpha) / (G + alpha))")
        print("    M = modulation term count")
        print("    G = generation term count")
        print("    alpha = Laplace smoothing (default 1)")
        print()
        print("  MDI > 0 -> modulation-dominant")
        print("  MDI < 0 -> generation-dominant")
        print()
        print("  To enable this analysis, place mdi_analysis.py in:")
        print(f"    {scripts_dir}/")
        print()
        return

    # Import and run
    import importlib.util
    spec = importlib.util.spec_from_file_location("mdi_analysis",
                                                   str(mdi_module_path))
    mdi_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mdi_mod)

    results = mdi_mod.run_analysis(db_path)
    mdi_mod.print_report(results)
    print()


def cmd_export_csv(conn: sqlite3.Connection):
    """Export nodes, edges, and evidence as CSV files to data/."""
    c = conn.cursor()
    data_dir = SCRIPT_DIR / "data"
    data_dir.mkdir(exist_ok=True)

    section("CSV EXPORT")

    # --- Nodes ---
    nodes_path = data_dir / "nodes.csv"
    rows = c.execute("SELECT * FROM nodes").fetchall()
    if rows:
        cols = rows[0].keys()
        with open(nodes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))
        print(f"  Exported {len(rows)} nodes to {nodes_path}")
    else:
        print("  No nodes to export.")

    # --- Edges ---
    edges_path = data_dir / "edges.csv"
    rows = c.execute("SELECT * FROM edges").fetchall()
    if rows:
        cols = rows[0].keys()
        with open(edges_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))
        print(f"  Exported {len(rows)} edges to {edges_path}")
    else:
        print("  No edges to export.")

    # --- Evidence ---
    evidence_path = data_dir / "evidence.csv"
    rows = c.execute("SELECT * FROM evidence").fetchall()
    if rows:
        cols = rows[0].keys()
        with open(evidence_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))
        print(f"  Exported {len(rows)} evidence records to {evidence_path}")
    else:
        print("  No evidence to export.")

    # --- Edge-evidence links ---
    edge_ev_path = data_dir / "edge_evidence.csv"
    rows = c.execute("SELECT * FROM edge_evidence").fetchall()
    if rows:
        cols = rows[0].keys()
        with open(edge_ev_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))
        print(f"  Exported {len(rows)} edge-evidence links to {edge_ev_path}")
    else:
        print("  No edge-evidence links to export.")

    # --- Node aliases ---
    aliases_path = data_dir / "node_aliases.csv"
    rows = c.execute("SELECT * FROM node_aliases").fetchall()
    if rows:
        cols = rows[0].keys()
        with open(aliases_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))
        print(f"  Exported {len(rows)} node aliases to {aliases_path}")
    else:
        print("  No aliases to export.")

    # --- Measurements ---
    meas_path = data_dir / "measurements.csv"
    rows = c.execute("SELECT * FROM measurements").fetchall()
    if rows:
        cols = rows[0].keys()
        with open(meas_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))
        print(f"  Exported {len(rows)} measurements to {meas_path}")
    else:
        print("  No measurements to export.")

    print()
    print("  All exports complete. Files written to:")
    print(f"    {data_dir}/")
    print()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="explore.py",
        description=(
            "Knowledge Graph Explorer -- interactive tool for researchers "
            "to verify and explore the consciousness research knowledge graph."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python explore.py summary
              python explore.py search "vagal regulation"
              python explore.py node mechanism:vagal_regulation
              python explore.py path mechanism:vagal_regulation claim:coherence_is_aperiodic_plus_modulation
              python explore.py domain BIOLOGY
              python explore.py evidence ev:bak1987
              python explore.py evidence mechanism:vagal_regulation
              python explore.py convergence
              python explore.py export-csv
              python explore.py mdi
              python explore.py --db /path/to/other.db summary
        """),
    )

    parser.add_argument(
        "--db", type=str, default=str(DEFAULT_DB),
        help=(
            "Path to the knowledge graph SQLite database. "
            f"Default: {DEFAULT_DB}"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # summary
    subparsers.add_parser(
        "summary",
        help="Print overview: counts, domain breakdown, edge layers",
    )

    # search
    sp_search = subparsers.add_parser(
        "search",
        help="Search nodes by keyword in title, summary, and aliases",
    )
    sp_search.add_argument(
        "term", type=str,
        help="Search term (matched against title, summary, node_id, aliases)",
    )

    # node
    sp_node = subparsers.add_parser(
        "node",
        help="Show full detail for a node (edges, evidence, measurements)",
    )
    sp_node.add_argument(
        "node_id", type=str,
        help="Node ID (e.g., mechanism:vagal_regulation) or alias",
    )

    # path
    sp_path = subparsers.add_parser(
        "path",
        help="Find shortest path between two nodes (BFS, undirected)",
    )
    sp_path.add_argument("node_a", type=str, help="Start node ID or alias")
    sp_path.add_argument("node_b", type=str, help="End node ID or alias")

    # domain
    sp_domain = subparsers.add_parser(
        "domain",
        help="List all nodes in a domain (case-insensitive)",
    )
    sp_domain.add_argument(
        "domain_name", type=str,
        help="Domain name (e.g., BIOLOGY, PHYSICS, MIND, CONVERGENCE)",
    )

    # mdi
    subparsers.add_parser(
        "mdi",
        help="Run Modulation Dominance Index analysis",
    )

    # evidence
    sp_evidence = subparsers.add_parser(
        "evidence",
        help="Show evidence for a node or detail for an evidence_id",
    )
    sp_evidence.add_argument(
        "identifier", type=str,
        help="Evidence ID (e.g., ev:bak1987) or node ID",
    )

    # convergence
    subparsers.add_parser(
        "convergence",
        help="Show nodes connected to 3+ different domains",
    )

    # export-csv
    subparsers.add_parser(
        "export-csv",
        help="Export all tables as CSV files to data/",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    conn = connect(args.db)

    try:
        if args.command == "summary":
            cmd_summary(conn)
        elif args.command == "search":
            cmd_search(conn, args.term)
        elif args.command == "node":
            cmd_node(conn, args.node_id)
        elif args.command == "path":
            cmd_path(conn, args.node_a, args.node_b)
        elif args.command == "domain":
            cmd_domain(conn, args.domain_name)
        elif args.command == "mdi":
            cmd_mdi(conn, args.db)
        elif args.command == "evidence":
            cmd_evidence(conn, args.identifier)
        elif args.command == "convergence":
            cmd_convergence(conn)
        elif args.command == "export-csv":
            cmd_export_csv(conn)
        else:
            parser.print_help()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
