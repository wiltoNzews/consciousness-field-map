#!/usr/bin/env python3
"""
Export knowledge_graph.db into researcher-friendly CSV and JSON formats.

Outputs (all written to data/):
  - nodes.csv          All nodes with key fields
  - edges.csv          All edges with key fields
  - evidence.csv       All evidence records
  - knowledge_graph_full.json   Complete export with summary statistics
"""

import csv
import json
import os
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DB_PATH = DATA_DIR / "knowledge_graph.db"


def export_nodes(cur, data_dir):
    """Export nodes table to CSV."""
    cur.execute("""
        SELECT node_id, title, summary, domain, node_type, confidence
        FROM nodes
        ORDER BY node_id
    """)
    rows = cur.fetchall()

    out_path = data_dir / "nodes.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["node_id", "label", "description", "domain", "node_type", "verification_status"])
        for row in rows:
            node_id, title, summary, domain, node_type, confidence = row
            writer.writerow([node_id, title, summary, domain, node_type, confidence])

    print(f"  nodes.csv: {len(rows)} rows")
    return rows


def export_edges(cur, data_dir):
    """Export edges table to CSV."""
    cur.execute("""
        SELECT edge_id, src_node_id, dst_node_id, edge_type, notes, weight, edge_layer
        FROM edges
        ORDER BY edge_id
    """)
    rows = cur.fetchall()

    out_path = data_dir / "edges.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["edge_id", "source", "target", "edge_type", "label", "description", "weight", "edge_layer"])
        for row in rows:
            edge_id, src, dst, edge_type, notes, weight, edge_layer = row
            # Use edge_type as label, notes as description
            writer.writerow([edge_id, src, dst, edge_type, edge_type, notes, weight, edge_layer])

    print(f"  edges.csv: {len(rows)} rows")
    return rows


def export_evidence(cur, data_dir):
    """Export evidence table to CSV."""
    cur.execute("""
        SELECT evidence_id, evidence_type, citation, year, authors, verification_status
        FROM evidence
        ORDER BY evidence_id
    """)
    rows = cur.fetchall()

    # We also want to associate evidence with nodes via edge_evidence -> edges -> nodes.
    # Build a mapping: evidence_id -> set of node_ids it supports.
    cur.execute("""
        SELECT ee.evidence_id, e.src_node_id, e.dst_node_id
        FROM edge_evidence ee
        JOIN edges e ON ee.edge_id = e.edge_id
    """)
    ev_to_nodes = {}
    for ev_id, src, dst in cur.fetchall():
        ev_to_nodes.setdefault(ev_id, set()).add(src)
        ev_to_nodes.setdefault(ev_id, set()).add(dst)

    out_path = data_dir / "evidence.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["evidence_id", "node_id", "citation", "year", "authors",
                         "verification_status", "evidence_type"])
        written = 0
        for row in rows:
            evidence_id, evidence_type, citation, year, authors, verification_status = row
            node_ids = ev_to_nodes.get(evidence_id, {None})
            for node_id in sorted(node_ids, key=lambda x: x or ""):
                writer.writerow([evidence_id, node_id, citation, year, authors,
                                 verification_status, evidence_type])
                written += 1

    print(f"  evidence.csv: {written} rows ({len(rows)} unique evidence records)")
    return rows


def export_full_json(cur, data_dir):
    """Export complete knowledge graph as JSON with summary statistics."""
    # Nodes
    cur.execute("SELECT * FROM nodes ORDER BY node_id")
    node_cols = [desc[0] for desc in cur.description]
    node_rows = [dict(zip(node_cols, row)) for row in cur.fetchall()]

    # Edges
    cur.execute("SELECT * FROM edges ORDER BY edge_id")
    edge_cols = [desc[0] for desc in cur.description]
    edge_rows = [dict(zip(edge_cols, row)) for row in cur.fetchall()]

    # Evidence
    cur.execute("SELECT * FROM evidence ORDER BY evidence_id")
    ev_cols = [desc[0] for desc in cur.description]
    ev_rows = [dict(zip(ev_cols, row)) for row in cur.fetchall()]

    # Edge-evidence links
    cur.execute("SELECT * FROM edge_evidence ORDER BY edge_id, evidence_id")
    ee_cols = [desc[0] for desc in cur.description]
    ee_rows = [dict(zip(ee_cols, row)) for row in cur.fetchall()]

    # Node aliases
    cur.execute("SELECT * FROM node_aliases ORDER BY node_id, alias")
    alias_cols = [desc[0] for desc in cur.description]
    alias_rows = [dict(zip(alias_cols, row)) for row in cur.fetchall()]

    # Measurements
    cur.execute("SELECT * FROM measurements ORDER BY measurement_id")
    meas_cols = [desc[0] for desc in cur.description]
    meas_rows = [dict(zip(meas_cols, row)) for row in cur.fetchall()]

    # Compute summary
    domains = sorted(set(n.get("domain") or "UNKNOWN" for n in node_rows))
    edge_layers = sorted(set(e.get("edge_layer") or "UNKNOWN" for e in edge_rows))
    node_types = sorted(set(n.get("node_type") or "UNKNOWN" for n in node_rows))
    edge_types = sorted(set(e.get("edge_type") or "UNKNOWN" for e in edge_rows))

    export = {
        "nodes": node_rows,
        "edges": edge_rows,
        "evidence": ev_rows,
        "edge_evidence": ee_rows,
        "node_aliases": alias_rows,
        "measurements": meas_rows,
        "summary": {
            "node_count": len(node_rows),
            "edge_count": len(edge_rows),
            "evidence_count": len(ev_rows),
            "edge_evidence_links": len(ee_rows),
            "alias_count": len(alias_rows),
            "measurement_count": len(meas_rows),
            "domains": domains,
            "node_types": node_types,
            "edge_types": edge_types,
            "edge_layers": edge_layers,
        },
    }

    out_path = data_dir / "knowledge_graph_full.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False, default=str)

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  knowledge_graph_full.json: {size_mb:.2f} MB")
    print(f"    {len(node_rows)} nodes, {len(edge_rows)} edges, "
          f"{len(ev_rows)} evidence, {len(ee_rows)} edge-evidence links")
    print(f"    Domains: {domains}")
    print(f"    Node types: {node_types}")
    print(f"    Edge types: {edge_types}")
    print(f"    Edge layers: {edge_layers}")

    return export


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Exporting knowledge graph from {DB_PATH}")
    print(f"Output directory: {DATA_DIR}\n")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    try:
        print("Exporting CSVs:")
        export_nodes(cur, DATA_DIR)
        export_edges(cur, DATA_DIR)
        export_evidence(cur, DATA_DIR)

        print("\nExporting full JSON:")
        export_full_json(cur, DATA_DIR)

        print("\nDone.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
