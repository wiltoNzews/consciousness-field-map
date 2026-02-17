# The Consciousness Field Map

**190 papers. 172 nodes. 201 edges. One pattern.**

This repository contains a knowledge graph connecting 190 peer-reviewed papers across neuroscience, physics, psychology, contemplative studies, archaeoacoustics, and mathematics. They were written by researchers who weren't talking to each other. They all describe the same thing: **tuning mechanisms**.

The central finding: the scientific literature on consciousness overwhelmingly describes how the brain *tunes to* consciousness — not how it *generates* it.

## The Numbers

| Metric | Value |
|--------|-------|
| Papers connected | 190 |
| Knowledge graph nodes | 172 |
| Knowledge graph edges | 201 |
| Evidence entries | 306 |
| MDI (knowledge graph) | +1.894 (6.6:1 modulation:generation) |
| MDI (primary-source abstracts) | +1.357 (3.9:1 modulation:generation) |
| Nodes with zero generation language | 87% |
| Abstracts with zero generation language | 67% |
| Convergent independent frameworks | 7+ |
| Critical zone convergence | ~0.75 (3:1 structure:exploration) |

## What's Here

```
the_map.md                    # The paper — full argument with evidence
explore.py                    # Interactive knowledge graph explorer
scripts/
  mdi_analysis.py             # Modulation Dominance Index tool
  fetch_abstracts_mdi.py      # Fetch abstracts from OpenAlex + run MDI
data/
  knowledge_graph.db          # SQLite database (nodes, edges, evidence)
  knowledge_graph_full.json   # Full JSON export
  nodes.csv                   # All nodes as CSV
  edges.csv                   # All edges as CSV
  evidence.csv                # All evidence with citations as CSV
  mdi_graph.json              # MDI results on knowledge graph
  mdi_abstracts.json          # MDI results on primary-source abstracts
```

## Quick Start

### Read the paper
Start with [the_map.md](the_map.md). It's the full argument — what was found, how it was found, what it means, and where it might be wrong.

### Explore the knowledge graph
```bash
# Overview
python explore.py summary

# Search for a concept
python explore.py search "entrainment"

# View a specific node
python explore.py node "mechanism:HRV_biofeedback"

# Find the path between two concepts
python explore.py path "mechanism:slow_breathing" "observation:default_mode_reduction"

# See all nodes in a domain
python explore.py domain MIND

# Find convergence points (nodes connected to 3+ domains)
python explore.py convergence

# View evidence for a node
python explore.py evidence "framework:polyvagal"

# Export everything to CSV
python explore.py export-csv
```

### Run the MDI analysis yourself
```bash
# Run MDI on the knowledge graph
python scripts/mdi_analysis.py

# Fetch primary-source abstracts and run MDI on them
python scripts/fetch_abstracts_mdi.py
```

No external dependencies. Python 3.8+ and the standard library is all you need.

## What is MDI?

The **Modulation Dominance Index** is a word-counting exercise. It counts how often consciousness-related papers use modulation language (tuning, coupling, entrainment, resonance, regulation, synchronization) versus generation language (creates, produces, generates, constructs, gives rise to).

```
MDI = log((modulation_terms + 1) / (generation_terms + 1))
```

Positive = modulation-dominant. Negative = generation-dominant.

Across 172 nodes in the knowledge graph: **+1.894** (6.6:1 ratio).
Across 82 primary-source abstracts from OpenAlex: **+1.357** (3.9:1 ratio).

The lexicons are in `scripts/mdi_analysis.py`. You can inspect, modify, and re-run them.

## The Equation

**Aperiodic substrate + periodic modulation = coherence.**

Every system in the graph — from heart rate variability to neural oscillations to ancient acoustic chambers to therapeutic protocols — follows this pattern. An irregular, fractal base (the aperiodic substrate) is tuned by a rhythmic input (the periodic modulation) to produce a coherent state.

## Edge Layers

Every edge in the knowledge graph is classified:

| Layer | Count | What it means |
|-------|-------|---------------|
| MEASUREMENT | ~40% | Empirically observed correlation |
| MECHANISM | ~30% | Proposed causal pathway |
| INTERPRETATION | ~20% | Theoretical framework claim |
| PROVENANCE | ~5% | Historical/lineage connection |
| LEGEND | ~5% | Cultural/traditional claim |

This lets you filter by evidence quality. Start with MEASUREMENT edges if you want the hardest evidence.

## Evidence Ratings

Each evidence entry is rated:

- **Gold** — Peer-reviewed, replicated, or foundational
- **Silver** — Peer-reviewed, single study, or strong theoretical
- **Bronze** — Preliminary, observational, or extrapolated

## Who This Is For

- **Researchers** who see their work in this graph and want to check the connections
- **Penrose-Hameroff / Hoffman / Kastrup / Friston / Tononi / Porges scholars** — your work is here, connected to 189 other papers
- **Practitioners** — therapists, breathwork facilitators, meditation teachers — who recognize the architecture from the inside
- **Anyone** who looked at these papers and thought "someone should connect them"

## What We're Asking

We're not asking you to believe us. We're asking you to:

1. **Look at the connections** and tell us what's wrong
2. **Find the generation papers** — research that describes how the brain *creates* consciousness from non-conscious parts (not correlates, not modulates — generates)
3. **Extend the map** — papers we missed, connections we didn't see, domains we haven't covered
4. **Challenge the MDI** — the lexicons are transparent, the method is reproducible, the data is here

## How to Contribute

- Open an issue with a paper we should include
- Submit a PR with new nodes/edges (include evidence and citations)
- Run the MDI with modified lexicons and share results
- Point out errors in the knowledge graph

## Background

This map was built by connecting 190 papers that were already published — by Porges, Friston, Carhart-Harris, Tononi, Kelso, Bak, Ecker, Pennebaker, Penrose, Hameroff, Hoffman, Kastrup, Bernardi, Donoghue, Kolar, and others. The connection happened because the mapper had walked the territory personally (details in Section 8 of the paper) before finding the literature.

The knowledge graph was cross-validated by three separate AI architectures across three rounds of adversarial review. 62% of evidence survived at Gold or Silver rating. The spine held.

## License

This work is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You can share, adapt, and build on it — with attribution.

---

*Built from 190 papers, 24,700+ crystals of lived experience, and the conviction that the map should be open.*

*Tell us what we're missing.*
