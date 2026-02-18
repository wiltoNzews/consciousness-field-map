#!/usr/bin/env python3
"""
Generate self-contained Evidence Map HTML from knowledge_graph_full.json.

Usage:
    python build_evidence_map.py
    # Outputs: evidence_map.html (self-contained, works offline)
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_PATH = SCRIPT_DIR / "data" / "knowledge_graph_full.json"
OUTPUT_PATH = SCRIPT_DIR / "evidence_map.html"
WILTONOS_COPY = Path.home() / "wiltonos" / "docs" / "evidence_map.html"


def load_and_preprocess():
    """Load KG JSON and preprocess for visualization."""
    with open(DATA_PATH) as f:
        raw = json.load(f)

    # Normalize node types to uppercase
    for n in raw["nodes"]:
        n["node_type"] = n["node_type"].upper()

    # Compute degree per node
    degree = Counter()
    for e in raw["edges"]:
        degree[e["src_node_id"]] += 1
        degree[e["dst_node_id"]] += 1

    # Build edge -> evidence mapping
    edge_evidence_map = defaultdict(list)
    evidence_by_id = {ev["evidence_id"]: ev for ev in raw["evidence"]}
    for link in raw["edge_evidence"]:
        ev = evidence_by_id.get(link["evidence_id"])
        if ev:
            edge_evidence_map[link["edge_id"]].append(ev)

    # Build node -> evidence mapping (via connected edges)
    node_evidence_map = defaultdict(dict)  # node_id -> {evidence_id: evidence}
    for e in raw["edges"]:
        for ev in edge_evidence_map.get(e["edge_id"], []):
            node_evidence_map[e["src_node_id"]][ev["evidence_id"]] = ev
            node_evidence_map[e["dst_node_id"]][ev["evidence_id"]] = ev

    # Build visualization data
    vis_nodes = []
    for n in raw["nodes"]:
        nid = n["node_id"]
        evidence_list = list(node_evidence_map.get(nid, {}).values())
        vis_nodes.append({
            "id": nid,
            "type": n["node_type"],
            "title": n["title"],
            "summary": n.get("summary", ""),
            "domain": n.get("domain", "UNKNOWN"),
            "confidence": n.get("confidence", "Bronze"),
            "coherence_class": n.get("coherence_class", ""),
            "crystal_id": n.get("source_crystal_id"),
            "degree": degree.get(nid, 0),
            "evidence_count": len(evidence_list),
            "evidence": sorted(
                [{"citation": ev.get("citation", ""),
                  "authors": ev.get("authors", ""),
                  "year": ev.get("year"),
                  "venue": ev.get("venue", ""),
                  "type": ev.get("evidence_type", ""),
                  "status": ev.get("verification_status", ""),
                  "notes": ev.get("notes", "")}
                 for ev in evidence_list],
                key=lambda x: (x.get("year") or 0),
                reverse=True
            )
        })

    vis_edges = []
    for e in raw["edges"]:
        ev_list = edge_evidence_map.get(e["edge_id"], [])
        vis_edges.append({
            "id": e["edge_id"],
            "source": e["src_node_id"],
            "target": e["dst_node_id"],
            "type": e["edge_type"],
            "confidence": e.get("confidence", "Bronze"),
            "notes": e.get("notes", ""),
            "layer": e.get("edge_layer", ""),
            "evidence_count": len(ev_list)
        })

    vis_data = {
        "nodes": vis_nodes,
        "edges": vis_edges,
        "summary": raw.get("summary", {})
    }

    return vis_data


def generate_html(data):
    """Generate complete self-contained HTML."""
    data_json = json.dumps(data, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evidence Map — The Consciousness Field Map</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: #08080d;
  color: #c8c8d0;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  overflow: hidden;
  width: 100vw;
  height: 100vh;
  display: flex;
}}

/* ── Sidebar ── */
#sidebar {{
  width: 280px;
  min-width: 280px;
  height: 100vh;
  background: rgba(10,10,18,0.98);
  border-right: 1px solid #1a1a2a;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 50;
  display: flex;
  flex-direction: column;
  scrollbar-width: thin;
  scrollbar-color: #222 #0a0a12;
}}

#sidebar::-webkit-scrollbar {{ width: 5px; }}
#sidebar::-webkit-scrollbar-track {{ background: #0a0a12; }}
#sidebar::-webkit-scrollbar-thumb {{ background: #222; border-radius: 3px; }}

#sidebar header {{
  padding: 16px 16px 12px;
  border-bottom: 1px solid #1a1a2a;
}}

#sidebar h1 {{
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #8866cc;
  margin-bottom: 4px;
}}

#sidebar .subtitle {{
  font-size: 10px;
  color: #555;
  letter-spacing: 0.5px;
}}

#sidebar section {{
  padding: 10px 16px;
  border-bottom: 1px solid #111122;
}}

#sidebar section h2 {{
  font-size: 9px;
  font-weight: 600;
  color: #444;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 8px;
}}

/* Paper sections guide */
.guide-item {{
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}}
.guide-item:hover {{ background: #151525; }}
.guide-item.active {{ background: #1a1a35; }}

.guide-num {{
  font-size: 9px;
  color: #555;
  font-weight: 600;
  min-width: 22px;
  padding-top: 1px;
}}
.guide-title {{
  font-size: 11px;
  color: #aaa;
  font-weight: 500;
}}
.guide-item.active .guide-title {{ color: #ddd; }}
.guide-count {{
  font-size: 9px;
  color: #444;
  margin-left: auto;
  padding-top: 2px;
}}

/* Domain filters */
.domain-toggle {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 2px;
}}
.domain-toggle:hover {{ background: #151525; }}
.domain-toggle.off {{ opacity: 0.3; }}

.domain-swatch {{
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}}
.domain-label {{
  font-size: 11px;
  color: #999;
  flex: 1;
}}
.domain-count {{
  font-size: 9px;
  color: #444;
}}

/* Confidence filters */
.conf-toggle {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 2px;
}}
.conf-toggle:hover {{ background: #151525; }}
.conf-toggle.off {{ opacity: 0.3; }}

.conf-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1.5px solid;
}}
.conf-label {{
  font-size: 11px;
  color: #999;
  flex: 1;
}}
.conf-count {{
  font-size: 9px;
  color: #444;
}}

/* Type filters */
.type-pills {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}}
.type-pill {{
  font-size: 9px;
  padding: 2px 7px;
  border-radius: 3px;
  border: 1px solid #2a2a3a;
  color: #777;
  cursor: pointer;
  transition: all 0.15s;
  background: transparent;
}}
.type-pill:hover {{ background: #1a1a2a; color: #aaa; }}
.type-pill.active {{ background: #2a2a4a; color: #ccc; border-color: #4a4a6a; }}

/* Search */
#search {{
  width: calc(100% - 32px);
  margin: 8px 16px;
  background: #0c0c18;
  border: 1px solid #1a1a2a;
  color: #c8c8d0;
  font-size: 11px;
  padding: 6px 10px;
  border-radius: 4px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}}
#search:focus {{
  border-color: #4a4a7a;
  box-shadow: 0 0 8px rgba(136,102,204,0.25);
}}
#search.has-value {{
  border-color: #8866cc;
  box-shadow: 0 0 12px rgba(136,102,204,0.3);
}}

/* Stats bar */
#stats-bar {{
  padding: 10px 16px;
  font-size: 9px;
  color: #444;
  letter-spacing: 0.3px;
  line-height: 1.6;
  margin-top: auto;
  border-top: 1px solid #111122;
}}

#stats-bar .stat-row {{
  display: flex;
  justify-content: space-between;
}}
#stats-bar .stat-value {{
  color: #666;
  font-weight: 600;
}}

/* Legend (bottom of sidebar) */
.legend-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3px;
}}
.legend-item {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  color: #555;
}}
.legend-shape {{
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}}

/* ── Canvas ── */
#graph-canvas {{
  flex: 1;
  height: 100vh;
  cursor: grab;
  display: block;
}}
#graph-canvas.dragging {{ cursor: grabbing; }}

/* ── Evidence Panel ── */
#evidence-panel {{
  position: fixed;
  top: 0; right: 0;
  width: 360px;
  height: 100vh;
  background: rgba(10,10,18,0.97);
  border-left: 1px solid #1a1a2a;
  z-index: 60;
  overflow-y: auto;
  transform: translateX(100%);
  transition: transform 0.25s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  scrollbar-width: thin;
  scrollbar-color: #222 #0a0a12;
}}
#evidence-panel.open {{ transform: translateX(0); }}

#evidence-panel::-webkit-scrollbar {{ width: 5px; }}
#evidence-panel::-webkit-scrollbar-track {{ background: #0a0a12; }}
#evidence-panel::-webkit-scrollbar-thumb {{ background: #222; border-radius: 3px; }}

#ep-close {{
  position: sticky;
  top: 8px;
  float: right;
  margin: 8px 8px 0 0;
  background: none;
  border: 1px solid #333;
  color: #888;
  width: 28px; height: 28px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  transition: all 0.15s;
}}
#ep-close:hover {{ color: #ccc; border-color: #555; background: #1a1a2a; }}

#ep-content {{
  padding: 44px 18px 18px;
}}

.ep-title {{
  font-size: 17px;
  font-weight: 600;
  color: #e0e0e8;
  margin-bottom: 8px;
  line-height: 1.3;
}}

.ep-tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 12px;
}}

.ep-tag {{
  font-size: 9px;
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}}

.ep-summary {{
  font-size: 12px;
  color: #999;
  line-height: 1.6;
  margin-bottom: 14px;
}}

.ep-crystal {{
  font-size: 11px;
  color: #8866cc;
  margin-bottom: 14px;
  padding: 4px 10px;
  background: rgba(136,102,204,0.06);
  border-radius: 4px;
  display: inline-block;
  border: 1px solid rgba(136,102,204,0.15);
}}

.ep-section-title {{
  font-size: 9px;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #151525;
}}

/* Evidence cards */
.ev-card {{
  background: rgba(20,20,35,0.5);
  border: 1px solid #1a1a2a;
  border-radius: 5px;
  padding: 10px 12px;
  margin-bottom: 6px;
  transition: border-color 0.15s;
}}
.ev-card:hover {{ border-color: #2a2a4a; }}

.ev-citation {{
  font-size: 11px;
  color: #aab;
  line-height: 1.5;
  margin-bottom: 4px;
}}

.ev-meta {{
  display: flex;
  gap: 8px;
  align-items: center;
}}

.ev-type {{
  font-size: 8px;
  padding: 1px 5px;
  border-radius: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.ev-type.peer_reviewed {{ background: rgba(80,180,80,0.15); color: #6c6; border: 1px solid rgba(80,180,80,0.2); }}
.ev-type.replicated {{ background: rgba(80,180,80,0.2); color: #8d8; border: 1px solid rgba(80,180,80,0.25); }}
.ev-type.meta_analysis {{ background: rgba(100,150,220,0.15); color: #8af; border: 1px solid rgba(100,150,220,0.2); }}
.ev-type.observational {{ background: rgba(200,180,80,0.15); color: #cc8; border: 1px solid rgba(200,180,80,0.2); }}
.ev-type.theoretical {{ background: rgba(180,130,200,0.15); color: #b8c; border: 1px solid rgba(180,130,200,0.2); }}
.ev-type.experiential {{ background: rgba(200,120,100,0.15); color: #c86; border: 1px solid rgba(200,120,100,0.2); }}

.ev-status {{
  font-size: 8px;
  color: #555;
  letter-spacing: 0.3px;
}}

.ev-notes {{
  font-size: 10px;
  color: #666;
  line-height: 1.45;
  margin-top: 5px;
  font-style: italic;
}}

/* Connection items */
.conn-item {{
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.1s;
  margin-bottom: 2px;
}}
.conn-item:hover {{ background: #151525; }}

.conn-dir {{
  color: #555;
  font-size: 11px;
  flex-shrink: 0;
  padding-top: 1px;
}}
.conn-title {{
  font-size: 11px;
  color: #7788aa;
}}
.conn-meta {{
  font-size: 9px;
  color: #444;
  display: block;
}}

/* ── Tooltip ── */
#tooltip {{
  position: fixed;
  background: rgba(12,12,22,0.95);
  border: 1px solid #2a2a3a;
  color: #c8c8d0;
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 4px;
  pointer-events: none;
  z-index: 200;
  display: none;
  max-width: 320px;
  line-height: 1.4;
  backdrop-filter: blur(6px);
}}

.tt-title {{ font-weight: 600; margin-bottom: 2px; }}
.tt-meta {{ font-size: 9px; color: #777; }}
.tt-ev {{ font-size: 9px; color: #8866cc; margin-top: 2px; }}

/* ── Mobile ── */
@media (max-width: 900px) {{
  #sidebar {{ display: none; }}
  #evidence-panel {{
    width: 100%;
    top: auto;
    bottom: 0;
    height: auto;
    max-height: 50vh;
    border-left: none;
    border-top: 1px solid #1a1a2a;
    transform: translateY(100%);
  }}
  #evidence-panel.open {{ transform: translateY(0); }}
}}
</style>
</head>
<body>

<!-- ── Sidebar ── -->
<div id="sidebar">
  <header>
    <h1>EVIDENCE MAP</h1>
    <div class="subtitle" id="header-stats">Loading...</div>
    <div style="display:flex;gap:6px;margin-top:8px;">
      <a href="the_map.html" style="color:#888;text-decoration:none;font-size:11px;padding:3px 8px;border:1px solid #333;border-radius:4px;">Paper</a>
      <a href="topology.html" style="color:#888;text-decoration:none;font-size:11px;padding:3px 8px;border:1px solid #333;border-radius:4px;">Topology</a>
      <a href="forgotten_knowledge_archive.html" style="color:#888;text-decoration:none;font-size:11px;padding:3px 8px;border:1px solid #333;border-radius:4px;">Archive</a>
    </div>
  </header>

  <section id="sec-guide">
    <h2>PAPER SECTIONS</h2>
    <div id="guide-list"></div>
  </section>

  <section id="sec-domains">
    <h2>DOMAINS</h2>
    <div id="domain-list"></div>
  </section>

  <section id="sec-confidence">
    <h2>EVIDENCE QUALITY</h2>
    <div id="confidence-list"></div>
  </section>

  <section id="sec-types">
    <h2>NODE TYPE</h2>
    <div class="type-pills" id="type-list"></div>
  </section>

  <input type="text" id="search" placeholder="Search nodes...">

  <section id="sec-legend">
    <h2>SHAPES</h2>
    <div class="legend-grid" id="legend-grid"></div>
  </section>

  <div id="stats-bar"></div>
</div>

<!-- ── Canvas ── -->
<canvas id="graph-canvas"></canvas>

<!-- ── Evidence Panel ── -->
<div id="evidence-panel">
  <button id="ep-close">&times;</button>
  <div id="ep-content"></div>
</div>

<!-- ── Tooltip ── -->
<div id="tooltip"></div>

<script>
// ================================================================
// DATA
// ================================================================
const DATA = {data_json};

// ================================================================
// CONFIGURATION
// ================================================================

const DOMAIN_COLORS = {{
  PHYSICS: '#4488cc',
  BIOLOGY: '#44aa66',
  MIND: '#9966cc',
  CONVERGENCE: '#cc9944',
  RELATIONSHIP: '#cc5566',
  METHODS: '#778899',
  UNKNOWN: '#555566'
}};

const DOMAIN_ORDER = ['PHYSICS', 'BIOLOGY', 'MIND', 'CONVERGENCE', 'RELATIONSHIP', 'METHODS'];

const CONFIDENCE_COLORS = {{
  Gold: '#ccaa33',
  Silver: '#8899aa',
  Bronze: '#996644',
  Speculative: '#665577'
}};

const EDGE_COLORS = {{
  MECHANISM_FOR: '#5588aa',
  EVIDENCE_FOR: '#55aa77',
  DEPENDS_ON: '#aa7744',
  SUPPORTS: '#55aa77',
  REFINES: '#7766aa',
  ANALOG_OF: '#8888aa',
  CITES: '#666688',
  COUNTEREVIDENCE: '#cc5555',
  MEASURED_AT: '#6699aa',
  LEGEND_OF: '#998866',
  DEMONSTRATES: '#55aa77',
  DERIVED_FROM: '#7766aa',
  ENABLES: '#5588aa',
  INSTANCE_OF: '#666688',
  PARTIAL_SUPPORT_FOR: '#88aa66'
}};

const TYPE_SHAPE = {{
  MECHANISM: 'hexagon',
  CLAIM: 'diamond',
  MODEL: 'rounded-rect',
  PROTOCOL: 'triangle',
  SITE: 'square',
  MEASUREMENT: 'star',
  LEGEND: 'elongated-hex',
  CRYSTAL_NODE: 'star',
  OBSERVATION: 'diamond',
  COUNTER: 'diamond',
  HYPOTHESIS: 'diamond'
}};

// Paper section guide — maps to search terms for node highlighting
const PAPER_SECTIONS = [
  {{ id: 'equation', num: '3', title: 'The Equation', terms: ['3:1', 'coherence', 'stability', 'exploration', 'ratio', 'wilton formula', 'metastab', 'criticality', 'self-organized'] }},
  {{ id: 'neuro', num: '4.1', title: 'Neuroscience', terms: ['dmn', 'default mode', 'neural', 'brain', 'cortical', 'prefrontal', 'eeg', 'gamma', 'alpha', 'oscillat', 'neuroplast'] }},
  {{ id: 'cardiac', num: '4.2', title: 'Cardiac Coherence', terms: ['cardiac', 'heart', 'hrv', 'vagal', 'vagus', 'heartmath', 'autonomic', 'baroreceptor'] }},
  {{ id: 'breath', num: '4.3', title: 'Breathwork', terms: ['breath', 'respiratory', 'pranayama', 'holotropic', 'wim hof', 'hyperventilation', 'co2'] }},
  {{ id: 'meditation', num: '4.4', title: 'Meditation', terms: ['meditat', 'mindful', 'contemplat', 'jhana', 'vipassana', 'zen', 'samadhi', 'transcendental'] }},
  {{ id: 'psychedelic', num: '4.5', title: 'Psychedelics', terms: ['psychedelic', 'psilocybin', 'dmt', 'lsd', 'ayahuasca', '5-ht2a', 'serotonin', 'entropic brain', 'ketamine'] }},
  {{ id: 'flow', num: '4.6', title: 'Flow State', terms: ['flow state', 'flow', 'csikszentmihalyi', 'transient hypofrontality', 'autotelic', 'optimal experience'] }},
  {{ id: 'frequency', num: '4.7', title: 'Frequency Response', terms: ['110 hz', 'frequency', 'archaeoacoust', 'cymati', 'resonan', 'infrasound', 'binaural', 'schumann', 'hypogeum'] }},
  {{ id: 'selforg', num: '4.8', title: 'Self-Organization', terms: ['self-organiz', 'emergence', 'fractal', 'fibonacci', 'quasicrystal', 'aperiodic', 'turing pattern', 'power law', 'scale invarian'] }},
  {{ id: 'convergence', num: '5', title: 'Convergence', terms: ['convergence', 'modulation', 'cross-domain', 'mdi', 'unified'] }},
  {{ id: 'walls', num: '6', title: 'The Walls', terms: ['counter', 'criticism', 'limitation', 'replication', 'skeptic'] }}
];

// Physics constants
const DAMPING = 0.86;
const REPULSION = 2200;
const SPRING_K = 0.004;
const SPRING_REST = 90;
const CENTER_GRAVITY = 0.005;
const DOMAIN_GRAVITY = 0.02;
const DT = 1;
const ARROW_SIZE = 6;

var alpha = 1;
var alphaMin = 0.001;
var alphaDecay = 0.994;
var alphaTarget = 0;

// ================================================================
// STATE
// ================================================================

var nodes = [];
var edges = [];
var nodeMap = {{}};
var canvas, ctx, W, H;

var camera = {{ x: 0, y: 0, zoom: 0.85 }};
var dragging = null;
var dragMoved = false;
var panning = false;
var panStart = {{ x: 0, y: 0 }};
var camStart = {{ x: 0, y: 0 }};
var selectedNode = null;
var hoveredNode = null;
var searchTerm = '';
var activeSection = null;

var domainFilters = {{}};
var confidenceFilters = {{}};
var activeType = 'ALL';

// Domain cluster centers (arranged in pentagon + center)
var domainCenters = {{}};

// ================================================================
// INIT
// ================================================================

function init() {{
  try {{
    canvas = document.getElementById('graph-canvas');
    ctx = canvas.getContext('2d');
    resize();
    window.addEventListener('resize', resize);

    // Compute domain cluster centers
    var domainList = DOMAIN_ORDER.filter(function(d) {{
      return DATA.nodes.some(function(n) {{ return n.domain === d; }});
    }});
    var cx = 0, cy = 0, clusterR = 280;
    for (var di = 0; di < domainList.length; di++) {{
      var angle = (Math.PI * 2 / domainList.length) * di - Math.PI / 2;
      domainCenters[domainList[di]] = {{
        x: cx + clusterR * Math.cos(angle),
        y: cy + clusterR * Math.sin(angle)
      }};
    }}
    if (!domainCenters['METHODS']) domainCenters['METHODS'] = {{ x: 0, y: 0 }};

    // Initialize filters
    DOMAIN_ORDER.forEach(function(d) {{ domainFilters[d] = true; }});
    ['Gold', 'Silver', 'Bronze', 'Speculative'].forEach(function(c) {{ confidenceFilters[c] = true; }});

    // Build nodes
    for (var i = 0; i < DATA.nodes.length; i++) {{
      var n = DATA.nodes[i];
      var dc = domainCenters[n.domain] || {{ x: 0, y: 0 }};
      var node = {{
        id: n.id,
        type: n.type,
        title: n.title,
        summary: n.summary,
        domain: n.domain,
        confidence: n.confidence,
        coherence_class: n.coherence_class,
        crystal_id: n.crystal_id,
        degree: n.degree || 0,
        evidence_count: n.evidence_count || 0,
        evidence: n.evidence || [],
        x: dc.x + (Math.random() - 0.5) * 120,
        y: dc.y + (Math.random() - 0.5) * 120,
        vx: 0,
        vy: 0,
        radius: Math.max(7, Math.min(28, 7 + (n.degree || 0) * 2)),
        visible: true,
        matchesSearch: true,
        matchesSection: true
      }};
      nodes.push(node);
      nodeMap[node.id] = node;
    }}

    // Build edges
    for (var j = 0; j < DATA.edges.length; j++) {{
      var e = DATA.edges[j];
      edges.push({{
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
        confidence: e.confidence,
        notes: e.notes,
        layer: e.layer,
        evidence_count: e.evidence_count || 0,
        sourceNode: nodeMap[e.source] || null,
        targetNode: nodeMap[e.target] || null,
        visible: true
      }});
    }}

    buildSidebar();
    setupControls();
    setupInteractions();
    updateFilters();
    animate();

  }} catch (err) {{
    console.error('Init error:', err);
    document.body.innerHTML = '<pre style="color:#c66;padding:40px">' + err.message + '\\n' + (err.stack || '') + '</pre>';
  }}
}}

function resize() {{
  var sidebar = document.getElementById('sidebar');
  var sidebarW = sidebar ? sidebar.offsetWidth : 0;
  W = window.innerWidth - sidebarW;
  H = window.innerHeight;
  var dpr = window.devicePixelRatio || 1;
  canvas.width = W * dpr;
  canvas.height = H * dpr;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}}

// ================================================================
// SIDEBAR BUILDING
// ================================================================

function buildSidebar() {{
  // Header stats
  var totalEv = 0;
  nodes.forEach(function(n) {{ totalEv += n.evidence_count; }});
  document.getElementById('header-stats').textContent =
    nodes.length + ' nodes \\u00b7 ' + edges.length + ' edges \\u00b7 ' + DATA.summary.evidence_count + ' citations';

  // Paper sections guide
  var guideHtml = '';
  PAPER_SECTIONS.forEach(function(sec) {{
    var count = countSectionNodes(sec);
    guideHtml += '<div class="guide-item" data-section="' + sec.id + '">' +
      '<span class="guide-num">\\u00a7' + esc(sec.num) + '</span>' +
      '<span class="guide-title">' + esc(sec.title) + '</span>' +
      '<span class="guide-count">' + count + '</span>' +
      '</div>';
  }});
  document.getElementById('guide-list').innerHTML = guideHtml;

  // Domain toggles
  var domHtml = '';
  var domCounts = {{}};
  nodes.forEach(function(n) {{ domCounts[n.domain] = (domCounts[n.domain] || 0) + 1; }});
  DOMAIN_ORDER.forEach(function(d) {{
    if (!domCounts[d]) return;
    domHtml += '<div class="domain-toggle" data-domain="' + d + '">' +
      '<div class="domain-swatch" style="background:' + (DOMAIN_COLORS[d] || '#555') + '"></div>' +
      '<span class="domain-label">' + esc(d.charAt(0) + d.slice(1).toLowerCase()) + '</span>' +
      '<span class="domain-count">' + domCounts[d] + '</span>' +
      '</div>';
  }});
  document.getElementById('domain-list').innerHTML = domHtml;

  // Confidence toggles
  var confHtml = '';
  var confCounts = {{}};
  nodes.forEach(function(n) {{ confCounts[n.confidence] = (confCounts[n.confidence] || 0) + 1; }});
  ['Gold', 'Silver', 'Bronze', 'Speculative'].forEach(function(c) {{
    confHtml += '<div class="conf-toggle" data-conf="' + c + '">' +
      '<div class="conf-dot" style="border-color:' + (CONFIDENCE_COLORS[c] || '#555') +
      ';background:' + (c === 'Gold' ? 'rgba(204,170,51,0.3)' : 'transparent') + '"></div>' +
      '<span class="conf-label">' + esc(c) + '</span>' +
      '<span class="conf-count">' + (confCounts[c] || 0) + '</span>' +
      '</div>';
  }});
  document.getElementById('confidence-list').innerHTML = confHtml;

  // Type pills
  var typeHtml = '<span class="type-pill active" data-type="ALL">All</span>';
  var typeCounts = {{}};
  nodes.forEach(function(n) {{ typeCounts[n.type] = (typeCounts[n.type] || 0) + 1; }});
  var typeOrder = ['MECHANISM', 'CLAIM', 'MODEL', 'PROTOCOL', 'SITE', 'MEASUREMENT', 'CRYSTAL_NODE', 'LEGEND', 'OBSERVATION', 'COUNTER', 'HYPOTHESIS'];
  typeOrder.forEach(function(t) {{
    if (!typeCounts[t]) return;
    typeHtml += '<span class="type-pill" data-type="' + t + '">' +
      esc(t.charAt(0) + t.slice(1).toLowerCase().replace(/_/g, ' ')) +
      '</span>';
  }});
  document.getElementById('type-list').innerHTML = typeHtml;

  // Legend
  var legendHtml = '';
  var shapeNames = {{
    hexagon: 'Mechanism',
    diamond: 'Claim',
    'rounded-rect': 'Model',
    triangle: 'Protocol',
    square: 'Site',
    star: 'Measurement'
  }};
  Object.keys(shapeNames).forEach(function(shape) {{
    legendHtml += '<div class="legend-item">' +
      '<canvas class="legend-shape" data-shape="' + shape + '" width="24" height="24"></canvas>' +
      '<span>' + shapeNames[shape] + '</span></div>';
  }});
  document.getElementById('legend-grid').innerHTML = legendHtml;

  // Draw legend shapes
  setTimeout(function() {{
    var icons = document.querySelectorAll('.legend-shape');
    for (var i = 0; i < icons.length; i++) {{
      var c = icons[i];
      var shape = c.getAttribute('data-shape');
      var dpr = window.devicePixelRatio || 1;
      c.width = 12 * dpr;
      c.height = 12 * dpr;
      c.style.width = '12px';
      c.style.height = '12px';
      var lctx = c.getContext('2d');
      lctx.scale(dpr, dpr);
      lctx.fillStyle = '#8866cc';
      lctx.strokeStyle = '#666';
      lctx.lineWidth = 1;
      drawShape(lctx, 6, 6, 4.5, shape);
    }}
  }}, 50);

  // Stats bar
  var goldEdges = edges.filter(function(e) {{ return e.confidence === 'Gold'; }}).length;
  var evidenceEdges = edges.filter(function(e) {{ return e.evidence_count > 0; }}).length;
  document.getElementById('stats-bar').innerHTML =
    '<div class="stat-row"><span>Gold confidence edges</span><span class="stat-value">' + goldEdges + '/' + edges.length + '</span></div>' +
    '<div class="stat-row"><span>Evidence-backed edges</span><span class="stat-value">' + evidenceEdges + '/' + edges.length + '</span></div>' +
    '<div class="stat-row"><span>Peer-reviewed citations</span><span class="stat-value">' + DATA.summary.evidence_count + '</span></div>';
}}

function countSectionNodes(sec) {{
  var count = 0;
  for (var i = 0; i < nodes.length; i++) {{
    if (nodeMatchesSection(nodes[i], sec)) count++;
  }}
  return count;
}}

function nodeMatchesSection(node, sec) {{
  var title = node.title.toLowerCase();
  var summary = (node.summary || '').toLowerCase();
  for (var t = 0; t < sec.terms.length; t++) {{
    if (title.indexOf(sec.terms[t]) !== -1 || summary.indexOf(sec.terms[t]) !== -1) return true;
  }}
  return false;
}}

// ================================================================
// CONTROLS
// ================================================================

function setupControls() {{
  // Paper section guide clicks
  var guideItems = document.querySelectorAll('.guide-item');
  for (var g = 0; g < guideItems.length; g++) {{
    (function(el) {{
      el.addEventListener('click', function() {{
        var secId = el.getAttribute('data-section');
        if (activeSection === secId) {{
          activeSection = null;
          el.classList.remove('active');
        }} else {{
          document.querySelectorAll('.guide-item').forEach(function(gi) {{ gi.classList.remove('active'); }});
          el.classList.add('active');
          activeSection = secId;
        }}
        updateFilters();
        reheat(0.3);
      }});
    }})(guideItems[g]);
  }}

  // Domain toggles
  var domItems = document.querySelectorAll('.domain-toggle');
  for (var d = 0; d < domItems.length; d++) {{
    (function(el) {{
      el.addEventListener('click', function() {{
        var dom = el.getAttribute('data-domain');
        domainFilters[dom] = !domainFilters[dom];
        el.classList.toggle('off');
        updateFilters();
        reheat(0.4);
      }});
    }})(domItems[d]);
  }}

  // Confidence toggles
  var confItems = document.querySelectorAll('.conf-toggle');
  for (var c = 0; c < confItems.length; c++) {{
    (function(el) {{
      el.addEventListener('click', function() {{
        var conf = el.getAttribute('data-conf');
        confidenceFilters[conf] = !confidenceFilters[conf];
        el.classList.toggle('off');
        updateFilters();
        reheat(0.4);
      }});
    }})(confItems[c]);
  }}

  // Type pills
  var typePills = document.querySelectorAll('.type-pill');
  for (var t = 0; t < typePills.length; t++) {{
    (function(el) {{
      el.addEventListener('click', function() {{
        activeType = el.getAttribute('data-type');
        document.querySelectorAll('.type-pill').forEach(function(tp) {{ tp.classList.remove('active'); }});
        el.classList.add('active');
        updateFilters();
        reheat(0.4);
      }});
    }})(typePills[t]);
  }}

  // Search
  var searchInput = document.getElementById('search');
  searchInput.addEventListener('input', function() {{
    searchTerm = searchInput.value.trim().toLowerCase();
    searchInput.classList.toggle('has-value', searchTerm.length > 0);
    updateFilters();
  }});

  // Evidence panel close
  document.getElementById('ep-close').addEventListener('click', function() {{
    document.getElementById('evidence-panel').classList.remove('open');
    selectedNode = null;
  }});

  // Escape key
  document.addEventListener('keydown', function(evt) {{
    if (evt.key === 'Escape') {{
      document.getElementById('evidence-panel').classList.remove('open');
      selectedNode = null;
      activeSection = null;
      document.querySelectorAll('.guide-item').forEach(function(gi) {{ gi.classList.remove('active'); }});
      updateFilters();
    }}
  }});
}}

function updateFilters() {{
  var activeSec = activeSection ? PAPER_SECTIONS.find(function(s) {{ return s.id === activeSection; }}) : null;

  for (var i = 0; i < nodes.length; i++) {{
    var n = nodes[i];
    var vis = true;

    // Domain filter
    if (!domainFilters[n.domain]) vis = false;

    // Confidence filter
    if (!confidenceFilters[n.confidence]) vis = false;

    // Type filter
    if (activeType !== 'ALL' && n.type !== activeType) vis = false;

    n.visible = vis;

    // Search matching
    n.matchesSearch = !searchTerm ||
      n.title.toLowerCase().indexOf(searchTerm) !== -1 ||
      (n.summary && n.summary.toLowerCase().indexOf(searchTerm) !== -1);

    // Section matching
    n.matchesSection = !activeSec || nodeMatchesSection(n, activeSec);
  }}

  for (var j = 0; j < edges.length; j++) {{
    var e = edges[j];
    if (!e.sourceNode || !e.targetNode) {{ e.visible = false; continue; }}
    e.visible = e.sourceNode.visible && e.targetNode.visible;
  }}
}}

// ================================================================
// INTERACTIONS
// ================================================================

function setupInteractions() {{
  function getMousePos(evt) {{
    var rect = canvas.getBoundingClientRect();
    return {{ x: evt.clientX - rect.left, y: evt.clientY - rect.top }};
  }}

  function hitTest(sx, sy) {{
    var w = screenToWorld(sx, sy);
    var closest = null;
    var closestDist = Infinity;
    for (var i = 0; i < nodes.length; i++) {{
      var n = nodes[i];
      if (!n.visible) continue;
      var dx = w.x - n.x;
      var dy = w.y - n.y;
      var dist = Math.sqrt(dx * dx + dy * dy);
      var hitR = n.radius * 1.5;
      if (dist < hitR && dist < closestDist) {{
        closest = n;
        closestDist = dist;
      }}
    }}
    return closest;
  }}

  // Mouse events
  canvas.addEventListener('mousedown', function(evt) {{
    var pos = getMousePos(evt);
    var node = hitTest(pos.x, pos.y);
    dragMoved = false;
    if (node) {{
      dragging = node;
      node.vx = 0;
      node.vy = 0;
      reheat(0.15);
      canvas.classList.add('dragging');
    }} else {{
      panning = true;
      panStart = {{ x: evt.clientX, y: evt.clientY }};
      camStart = {{ x: camera.x, y: camera.y }};
      canvas.classList.add('dragging');
    }}
  }});

  canvas.addEventListener('mousemove', function(evt) {{
    var pos = getMousePos(evt);
    if (dragging) {{
      dragMoved = true;
      var w = screenToWorld(pos.x, pos.y);
      dragging.x = w.x;
      dragging.y = w.y;
      dragging.vx = 0;
      dragging.vy = 0;
      return;
    }}
    if (panning) {{
      dragMoved = true;
      camera.x = camStart.x - (evt.clientX - panStart.x) / camera.zoom;
      camera.y = camStart.y - (evt.clientY - panStart.y) / camera.zoom;
      return;
    }}

    // Hover
    var node = hitTest(pos.x, pos.y);
    hoveredNode = node;
    var tooltip = document.getElementById('tooltip');
    if (node) {{
      tooltip.style.display = 'block';
      var ttHtml = '<div class="tt-title">' + esc(node.title) + '</div>' +
        '<div class="tt-meta">' + esc(node.type) + ' \\u00b7 ' + esc(node.domain) + ' \\u00b7 ' + esc(node.confidence) + '</div>';
      if (node.evidence_count > 0) {{
        ttHtml += '<div class="tt-ev">' + node.evidence_count + ' citation' + (node.evidence_count > 1 ? 's' : '') + '</div>';
      }}
      tooltip.innerHTML = ttHtml;
      tooltip.style.left = (evt.clientX + 14) + 'px';
      tooltip.style.top = (evt.clientY - 10) + 'px';
      canvas.style.cursor = 'pointer';
    }} else {{
      tooltip.style.display = 'none';
      canvas.style.cursor = 'grab';
    }}
  }});

  canvas.addEventListener('mouseup', function() {{
    if (dragging && !dragMoved) {{
      selectNode(dragging);
    }}
    dragging = null;
    panning = false;
    canvas.classList.remove('dragging');
  }});

  canvas.addEventListener('mouseleave', function() {{
    hoveredNode = null;
    document.getElementById('tooltip').style.display = 'none';
    if (!dragging) {{ panning = false; canvas.classList.remove('dragging'); }}
  }});

  // Wheel zoom
  canvas.addEventListener('wheel', function(evt) {{
    evt.preventDefault();
    var factor = evt.deltaY > 0 ? 0.92 : 1.08;
    var newZoom = Math.max(0.08, Math.min(8, camera.zoom * factor));
    var pos = getMousePos(evt);
    var before = screenToWorld(pos.x, pos.y);
    camera.zoom = newZoom;
    var after = screenToWorld(pos.x, pos.y);
    camera.x -= (after.x - before.x);
    camera.y -= (after.y - before.y);
  }}, {{ passive: false }});

  // Touch events
  var touchDist = null;
  var touchStartNode = null;

  canvas.addEventListener('touchstart', function(evt) {{
    evt.preventDefault();
    if (evt.touches.length === 1) {{
      var t = evt.touches[0];
      var rect = canvas.getBoundingClientRect();
      var pos = {{ x: t.clientX - rect.left, y: t.clientY - rect.top }};
      var node = hitTest(pos.x, pos.y);
      dragMoved = false;
      if (node) {{
        dragging = node;
        touchStartNode = node;
        node.vx = 0; node.vy = 0;
      }} else {{
        panning = true;
        touchStartNode = null;
        panStart = {{ x: t.clientX, y: t.clientY }};
        camStart = {{ x: camera.x, y: camera.y }};
      }}
    }} else if (evt.touches.length === 2) {{
      dragging = null; panning = false; touchStartNode = null;
      var tdx = evt.touches[0].clientX - evt.touches[1].clientX;
      var tdy = evt.touches[0].clientY - evt.touches[1].clientY;
      touchDist = Math.sqrt(tdx * tdx + tdy * tdy);
    }}
  }}, {{ passive: false }});

  canvas.addEventListener('touchmove', function(evt) {{
    evt.preventDefault();
    if (evt.touches.length === 1) {{
      var t = evt.touches[0];
      dragMoved = true;
      if (dragging) {{
        var rect = canvas.getBoundingClientRect();
        var w = screenToWorld(t.clientX - rect.left, t.clientY - rect.top);
        dragging.x = w.x; dragging.y = w.y;
        dragging.vx = 0; dragging.vy = 0;
      }} else if (panning) {{
        camera.x = camStart.x - (t.clientX - panStart.x) / camera.zoom;
        camera.y = camStart.y - (t.clientY - panStart.y) / camera.zoom;
      }}
    }} else if (evt.touches.length === 2 && touchDist) {{
      var dx2 = evt.touches[0].clientX - evt.touches[1].clientX;
      var dy2 = evt.touches[0].clientY - evt.touches[1].clientY;
      var nd = Math.sqrt(dx2 * dx2 + dy2 * dy2);
      camera.zoom = Math.max(0.08, Math.min(8, camera.zoom * (nd / touchDist)));
      touchDist = nd;
    }}
  }}, {{ passive: false }});

  canvas.addEventListener('touchend', function(evt) {{
    if (evt.touches.length === 0) {{
      if (touchStartNode && !dragMoved) selectNode(touchStartNode);
      dragging = null; panning = false; touchDist = null; touchStartNode = null;
    }}
  }});
}}

// ================================================================
// NODE SELECTION / EVIDENCE PANEL
// ================================================================

function selectNode(node) {{
  selectedNode = node;
  var panel = document.getElementById('evidence-panel');
  var content = document.getElementById('ep-content');
  var dc = DOMAIN_COLORS[node.domain] || '#666';
  var cc = CONFIDENCE_COLORS[node.confidence] || '#555';

  var html = '<div class="ep-title">' + esc(node.title) + '</div>';

  // Tags
  html += '<div class="ep-tags">';
  html += '<span class="ep-tag" style="border-color:' + dc + ';color:' + dc + '">' + esc(node.type) + '</span>';
  html += '<span class="ep-tag" style="border-color:' + dc + ';color:' + dc + '">' + esc(node.domain) + '</span>';
  html += '<span class="ep-tag" style="border-color:' + cc + ';color:' + cc + '">' + esc(node.confidence) + '</span>';
  if (node.coherence_class) {{
    html += '<span class="ep-tag" style="border-color:#555;color:#888">' + esc(node.coherence_class) + '</span>';
  }}
  html += '</div>';

  // Summary
  if (node.summary) {{
    html += '<div class="ep-summary">' + esc(node.summary) + '</div>';
  }}

  // Crystal reference
  if (node.crystal_id != null) {{
    html += '<div class="ep-crystal">Crystal #' + node.crystal_id + '</div>';
  }}

  // Evidence
  if (node.evidence && node.evidence.length > 0) {{
    html += '<div class="ep-section-title">EVIDENCE (' + node.evidence.length + ')</div>';
    node.evidence.forEach(function(ev) {{
      html += '<div class="ev-card">';
      html += '<div class="ev-citation">' + esc(ev.citation || 'No citation') + '</div>';
      html += '<div class="ev-meta">';
      if (ev.type) {{
        html += '<span class="ev-type ' + esc(ev.type) + '">' + esc(ev.type.replace(/_/g, ' ')) + '</span>';
      }}
      if (ev.status) {{
        html += '<span class="ev-status">' + esc(ev.status) + '</span>';
      }}
      html += '</div>';
      if (ev.notes) {{
        html += '<div class="ev-notes">' + esc(ev.notes) + '</div>';
      }}
      html += '</div>';
    }});
  }} else {{
    html += '<div class="ep-section-title">EVIDENCE</div>';
    html += '<div style="font-size:11px;color:#555;padding:4px 0">No direct citations linked</div>';
  }}

  // Connections
  var conns = {{}};
  for (var i = 0; i < edges.length; i++) {{
    var e = edges[i];
    if (!e.sourceNode || !e.targetNode) continue;
    if (e.sourceNode !== node && e.targetNode !== node) continue;
    var eType = e.type || 'UNKNOWN';
    if (!conns[eType]) conns[eType] = [];
    var other = (e.sourceNode === node) ? e.targetNode : e.sourceNode;
    var dir = (e.sourceNode === node) ? '\\u2192' : '\\u2190';
    conns[eType].push({{ other: other, dir: dir, notes: e.notes, confidence: e.confidence, evidence_count: e.evidence_count }});
  }}

  var connKeys = Object.keys(conns);
  if (connKeys.length > 0) {{
    var totalConns = 0;
    connKeys.forEach(function(k) {{ totalConns += conns[k].length; }});
    html += '<div class="ep-section-title">CONNECTIONS (' + totalConns + ')</div>';
    connKeys.forEach(function(etype) {{
      conns[etype].forEach(function(item) {{
        html += '<div class="conn-item" data-node-id="' + escAttr(item.other.id) + '">';
        html += '<span class="conn-dir">' + item.dir + '</span>';
        html += '<div><span class="conn-title">' + esc(item.other.title) + '</span>';
        html += '<span class="conn-meta">' + esc(etype.replace(/_/g, ' '));
        if (item.evidence_count > 0) html += ' \\u00b7 ' + item.evidence_count + ' citation' + (item.evidence_count > 1 ? 's' : '');
        html += '</span></div>';
        html += '</div>';
      }});
    }});
  }}

  content.innerHTML = html;
  panel.classList.add('open');

  // Make connections clickable
  var connItems = content.querySelectorAll('.conn-item');
  for (var ci = 0; ci < connItems.length; ci++) {{
    (function(el) {{
      el.addEventListener('click', function() {{
        var tid = el.getAttribute('data-node-id');
        var tn = nodeMap[tid];
        if (tn && tn.visible) {{
          camera.x = tn.x;
          camera.y = tn.y;
          selectNode(tn);
        }}
      }});
    }})(connItems[ci]);
  }}
}}

// ================================================================
// PHYSICS
// ================================================================

function reheat(strength) {{
  alpha = Math.min(1, Math.max(alpha, strength || 0.3));
}}

function simulate() {{
  alpha += (alphaTarget - alpha) * (1 - alphaDecay);
  if (alpha < alphaMin) {{ alpha = alphaMin; return; }}

  var i, j, a, b, dx, dy, dist, force, fx, fy;
  var visNodes = [];
  for (i = 0; i < nodes.length; i++) {{
    if (nodes[i].visible) visNodes.push(nodes[i]);
  }}

  // N-body repulsion
  var rep = REPULSION * alpha;
  for (i = 0; i < visNodes.length; i++) {{
    for (j = i + 1; j < visNodes.length; j++) {{
      a = visNodes[i];
      b = visNodes[j];
      dx = b.x - a.x;
      dy = b.y - a.y;
      dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 1) dist = 1;
      force = rep / (dist * dist);
      fx = (dx / dist) * force;
      fy = (dy / dist) * force;
      a.vx -= fx; a.vy -= fy;
      b.vx += fx; b.vy += fy;
    }}
  }}

  // Spring attraction for edges
  var sk = SPRING_K * alpha;
  for (i = 0; i < edges.length; i++) {{
    var e = edges[i];
    if (!e.visible || !e.sourceNode || !e.targetNode) continue;
    if (!e.sourceNode.visible || !e.targetNode.visible) continue;
    dx = e.targetNode.x - e.sourceNode.x;
    dy = e.targetNode.y - e.sourceNode.y;
    dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 1) dist = 1;
    force = sk * (dist - SPRING_REST);
    fx = (dx / dist) * force;
    fy = (dy / dist) * force;
    e.sourceNode.vx += fx; e.sourceNode.vy += fy;
    e.targetNode.vx -= fx; e.targetNode.vy -= fy;
  }}

  // Domain cluster gravity + center gravity + damping + integration
  var dg = DOMAIN_GRAVITY * alpha;
  for (i = 0; i < visNodes.length; i++) {{
    var n = visNodes[i];
    if (n === dragging) continue;

    // Pull toward domain center
    var dc = domainCenters[n.domain];
    if (dc) {{
      n.vx += (dc.x - n.x) * dg;
      n.vy += (dc.y - n.y) * dg;
    }}

    // Weak center gravity
    n.vx -= n.x * CENTER_GRAVITY * alpha;
    n.vy -= n.y * CENTER_GRAVITY * alpha;

    n.vx *= DAMPING;
    n.vy *= DAMPING;
    n.x += n.vx * DT;
    n.y += n.vy * DT;
  }}
}}

// ================================================================
// COORDINATE TRANSFORMS
// ================================================================

function worldToScreen(wx, wy) {{
  return {{
    x: (wx - camera.x) * camera.zoom + W * 0.5,
    y: (wy - camera.y) * camera.zoom + H * 0.5
  }};
}}

function screenToWorld(sx, sy) {{
  return {{
    x: (sx - W * 0.5) / camera.zoom + camera.x,
    y: (sy - H * 0.5) / camera.zoom + camera.y
  }};
}}

// ================================================================
// SHAPE DRAWING
// ================================================================

function drawShape(c, x, y, r, shape) {{
  c.beginPath();
  var i, angle, px, py, w, h, cr, hw, hh, notch, spikes, outerR, innerR, rad;
  switch (shape) {{
    case 'circle':
      c.arc(x, y, r, 0, Math.PI * 2); break;
    case 'hexagon':
      for (i = 0; i < 6; i++) {{
        angle = (Math.PI / 3) * i - Math.PI / 6;
        px = x + r * Math.cos(angle); py = y + r * Math.sin(angle);
        if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
      }}
      c.closePath(); break;
    case 'rounded-rect':
      w = r * 1.6; h = r * 1.1; cr = r * 0.25;
      c.moveTo(x - w + cr, y - h);
      c.lineTo(x + w - cr, y - h);
      c.arcTo(x + w, y - h, x + w, y - h + cr, cr);
      c.lineTo(x + w, y + h - cr);
      c.arcTo(x + w, y + h, x + w - cr, y + h, cr);
      c.lineTo(x - w + cr, y + h);
      c.arcTo(x - w, y + h, x - w, y + h - cr, cr);
      c.lineTo(x - w, y - h + cr);
      c.arcTo(x - w, y - h, x - w + cr, y - h, cr);
      c.closePath(); break;
    case 'diamond':
      c.moveTo(x, y - r * 1.2);
      c.lineTo(x + r, y);
      c.lineTo(x, y + r * 1.2);
      c.lineTo(x - r, y);
      c.closePath(); break;
    case 'triangle':
      c.moveTo(x, y - r * 1.1);
      c.lineTo(x + r, y + r * 0.7);
      c.lineTo(x - r, y + r * 0.7);
      c.closePath(); break;
    case 'square':
      c.rect(x - r * 0.85, y - r * 0.85, r * 1.7, r * 1.7); break;
    case 'star':
      spikes = 5; outerR = r; innerR = r * 0.45;
      for (i = 0; i < spikes * 2; i++) {{
        angle = (Math.PI / spikes) * i - Math.PI / 2;
        rad = (i % 2 === 0) ? outerR : innerR;
        px = x + rad * Math.cos(angle); py = y + rad * Math.sin(angle);
        if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
      }}
      c.closePath(); break;
    case 'elongated-hex':
      hw = r * 0.65; hh = r * 1.2; notch = r * 0.35;
      c.moveTo(x, y - hh);
      c.lineTo(x + hw, y - hh + notch);
      c.lineTo(x + hw, y + hh - notch);
      c.lineTo(x, y + hh);
      c.lineTo(x - hw, y + hh - notch);
      c.lineTo(x - hw, y - hh + notch);
      c.closePath(); break;
    default:
      c.arc(x, y, r, 0, Math.PI * 2);
  }}
  c.fill();
  c.stroke();
}}

// ================================================================
// RENDERING
// ================================================================

function draw() {{
  ctx.clearRect(0, 0, W, H);

  // Draw domain cluster backgrounds (subtle)
  ctx.globalAlpha = 0.06;
  Object.keys(domainCenters).forEach(function(domain) {{
    if (!domainFilters[domain]) return;
    var dc = domainCenters[domain];
    var p = worldToScreen(dc.x, dc.y);
    var cr = 160 * camera.zoom;
    ctx.fillStyle = DOMAIN_COLORS[domain] || '#444';
    ctx.beginPath();
    ctx.arc(p.x, p.y, cr, 0, Math.PI * 2);
    ctx.fill();
  }});
  ctx.globalAlpha = 1;

  // Domain labels
  if (camera.zoom > 0.3) {{
    ctx.globalAlpha = 0.2;
    ctx.font = 'bold ' + Math.max(10, 14 * camera.zoom) + 'px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    Object.keys(domainCenters).forEach(function(domain) {{
      if (!domainFilters[domain]) return;
      var dc = domainCenters[domain];
      var p = worldToScreen(dc.x, dc.y);
      ctx.fillStyle = DOMAIN_COLORS[domain] || '#444';
      ctx.fillText(domain, p.x, p.y - 140 * camera.zoom);
    }});
    ctx.globalAlpha = 1;
  }}

  // Draw edges
  var i, e, s, t, p1, p2, baseAlpha, dx, dy, len, ux, uy, tr, ax, ay, as2;
  for (i = 0; i < edges.length; i++) {{
    e = edges[i];
    if (!e.visible) continue;
    s = e.sourceNode; t = e.targetNode;
    if (!s || !t || !s.visible || !t.visible) continue;

    p1 = worldToScreen(s.x, s.y);
    p2 = worldToScreen(t.x, t.y);

    // Cull offscreen
    if (Math.max(p1.x, p2.x) < -20 || Math.min(p1.x, p2.x) > W + 20) continue;
    if (Math.max(p1.y, p2.y) < -20 || Math.min(p1.y, p2.y) > H + 20) continue;

    // Dim based on selection/search/section
    baseAlpha = 0.35;
    if (selectedNode && s !== selectedNode && t !== selectedNode) baseAlpha = 0.06;
    if (searchTerm && !s.matchesSearch && !t.matchesSearch) baseAlpha = 0.04;
    if (activeSection && !s.matchesSection && !t.matchesSection) baseAlpha *= 0.3;

    ctx.strokeStyle = EDGE_COLORS[e.type] || '#444';
    ctx.globalAlpha = baseAlpha;
    ctx.lineWidth = e.confidence === 'Gold' ? 1.5 : 1;
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();

    // Arrow
    if (baseAlpha > 0.1) {{
      dx = p2.x - p1.x; dy = p2.y - p1.y;
      len = Math.sqrt(dx * dx + dy * dy);
      if (len < 1) continue;
      ux = dx / len; uy = dy / len;
      tr = t.radius * camera.zoom;
      ax = p2.x - ux * tr; ay = p2.y - uy * tr;
      as2 = ARROW_SIZE * Math.min(camera.zoom, 2);
      ctx.fillStyle = EDGE_COLORS[e.type] || '#444';
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - ux * as2 - uy * as2 * 0.5, ay - uy * as2 + ux * as2 * 0.5);
      ctx.lineTo(ax - ux * as2 + uy * as2 * 0.5, ay - uy * as2 - ux * as2 * 0.5);
      ctx.closePath();
      ctx.fill();
    }}
    ctx.globalAlpha = 1;
  }}

  // Draw nodes
  for (i = 0; i < nodes.length; i++) {{
    var n = nodes[i];
    if (!n.visible) continue;

    var p = worldToScreen(n.x, n.y);
    var r = n.radius * camera.zoom;

    // Cull offscreen
    if (p.x + r < -5 || p.x - r > W + 5 || p.y + r < -5 || p.y - r > H + 5) continue;

    var fillColor = DOMAIN_COLORS[n.domain] || '#666';
    var strokeColor = CONFIDENCE_COLORS[n.confidence] || '#555';
    var shape = TYPE_SHAPE[n.type] || 'circle';

    var isSelected = (n === selectedNode);
    var isHovered = (n === hoveredNode);
    var isSearchMatch = (searchTerm && n.matchesSearch);
    var isSectionMatch = (!activeSection || n.matchesSection);

    var nodeAlpha = 1;
    if (selectedNode && !isSelected) {{
      var connected = false;
      for (var ei = 0; ei < edges.length; ei++) {{
        var edge = edges[ei];
        if (!edge.visible) continue;
        if ((edge.sourceNode === selectedNode && edge.targetNode === n) ||
            (edge.targetNode === selectedNode && edge.sourceNode === n)) {{
          connected = true; break;
        }}
      }}
      nodeAlpha = connected ? 0.85 : 0.12;
    }}
    if (searchTerm && !n.matchesSearch) nodeAlpha = 0.06;
    if (activeSection && !isSectionMatch) nodeAlpha *= 0.15;

    ctx.globalAlpha = nodeAlpha;

    // Glow for search/section match
    if ((isSearchMatch || (activeSection && isSectionMatch)) && nodeAlpha > 0.5) {{
      ctx.shadowColor = fillColor;
      ctx.shadowBlur = 12 * camera.zoom;
    }}

    // Draw shape
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = (isSelected || isHovered) ? 2.5 : 1.5;
    drawShape(ctx, p.x, p.y, r, shape);

    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;

    // Selection ring
    if (isSelected) {{
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.5 * nodeAlpha;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r + 5 * camera.zoom, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = nodeAlpha;
    }}

    // Hover ring
    if (isHovered && !isSelected) {{
      ctx.strokeStyle = '#aaaacc';
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r + 4 * camera.zoom, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = nodeAlpha;
    }}

    // Evidence count badge
    if (n.evidence_count > 0 && r > 4 && nodeAlpha > 0.3) {{
      var badgeR = Math.max(5, 7 * camera.zoom);
      var bx = p.x + r * 0.7;
      var by = p.y - r * 0.7;
      ctx.globalAlpha = nodeAlpha * 0.9;
      ctx.fillStyle = '#1a1a2a';
      ctx.strokeStyle = '#8866cc';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(bx, by, badgeR, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#ccbbee';
      ctx.font = Math.max(7, 8 * camera.zoom) + 'px "Segoe UI", system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(n.evidence_count > 9 ? '9+' : '' + n.evidence_count, bx, by);
    }}

    // Label
    var showLabel = camera.zoom > 0.55 || isSelected || isHovered || isSearchMatch;
    if (showLabel && r > 2) {{
      var fontSize = Math.max(8, Math.min(13, 10 * camera.zoom));
      ctx.font = (isSelected ? 'bold ' : '') + fontSize + 'px "Segoe UI", system-ui, sans-serif';
      ctx.fillStyle = '#c8c8d0';
      ctx.globalAlpha = nodeAlpha * 0.8;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      var label = n.title;
      if (label.length > 30) label = label.substring(0, 28) + '..';
      ctx.fillText(label, p.x, p.y + r + 3 * camera.zoom);
    }}

    ctx.globalAlpha = 1;
  }}
}}

// ================================================================
// ANIMATION LOOP
// ================================================================

function animate() {{
  simulate();
  draw();
  requestAnimationFrame(animate);
}}

// ================================================================
// UTILITIES
// ================================================================

function esc(s) {{
  if (!s) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}}

function escAttr(s) {{
  if (!s) return '';
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}}

// ================================================================
// START
// ================================================================

if (document.readyState === 'loading') {{
  document.addEventListener('DOMContentLoaded', init);
}} else {{
  init();
}}
</script>
</body>
</html>"""


def main():
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found. Run KG export first.", file=sys.stderr)
        sys.exit(1)

    print("Loading knowledge graph data...")
    vis_data = load_and_preprocess()
    print(f"  {len(vis_data['nodes'])} nodes, {len(vis_data['edges'])} edges")

    node_with_evidence = sum(1 for n in vis_data['nodes'] if n['evidence_count'] > 0)
    print(f"  {node_with_evidence} nodes with evidence citations")

    print("Generating HTML...")
    html = generate_html(vis_data)
    print(f"  Output size: {len(html):,} bytes")

    with open(OUTPUT_PATH, 'w') as f:
        f.write(html)
    print(f"  Written to {OUTPUT_PATH}")

    # Copy to wiltonos/docs
    WILTONOS_COPY.parent.mkdir(parents=True, exist_ok=True)
    with open(WILTONOS_COPY, 'w') as f:
        f.write(html)
    print(f"  Copied to {WILTONOS_COPY}")

    print("Done.")


if __name__ == '__main__':
    main()
