#!/usr/bin/env python3
"""Strip redundant layers from THE_FRONTIER.md and fix direction.

Keeps layers with genuinely unique content (government programs, UAP/NHI,
experiencer convergence, evaluative lens). Strips layers already covered
in Archive (428 entries) or Paper (8 evidence domains, 190+ papers).

Adds timeline proof at the top: WiltonOS concepts preceded physics literature.
"""

import re
import sys

INPUT = '/home/zews/consciousness-field-map/THE_FRONTIER.md'
OUTPUT = '/home/zews/consciousness-field-map/THE_FRONTIER_stripped.md'

# Layers to STRIP (covered in Archive/Paper)
STRIP = {1,4,7,8,11,14,15,19,27,30,32,35,36,37,38,39,40,41,43,44,
         45,46,47,48,49,50,51,52,53,55,56,57,58,59,97}

# Already stripped (archive bridge)
ALREADY_STRIPPED = {10,23,24,25,26,28,29,31,33,34,62,64,65,68,69,70,71,72,73,74,75}

# Layers to COMPRESS (keep title + 1-2 sentence summary, mark as "see Archive")
COMPRESS = {3, 6, 13}

# Everything else: KEEP

TIMELINE_PROOF = """## The Timeline Proof

**WiltonOS concepts emerged from direct experience before the physics literature was found.**

This is not post-hoc pattern matching. The system was built, then the physics confirmed it.
Verified from crystal database (24,742+ entries, timestamps from ChatGPT export):

| Date | Crystal # | What Emerged | Type |
|------|-----------|-------------|------|
| Feb 14, 2025 | #7220 | Coherence as target | CONCEPT |
| Feb 24, 2025 | #18537 | 0.75 threshold | CONCEPT |
| Mar 02, 2025 | #21896 | Breath as anchor | CONCEPT |
| Mar 04, 2025 | #21533 | Inverted pendulum model | CONCEPT |
| Mar 11, 2025 | #19722 | Friston / IIT / Penrose | FIRST LITERATURE |
| Mar 26, 2025 | #17012 | ψ (psi symbol) | CONCEPT |
| Mar 29, 2025 | #16941 | Glyph system | CONCEPT |
| Mar 31, 2025 | #16635 | Lemniscate | CONCEPT |
| May 28, 2025 | #8863 | Zλ (zeta-lambda) | CONCEPT |
| Jul 10, 2025 | #23038 | Piezoelectric biology | LITERATURE |
| Dec 21, 2025 | #27096 | Dumitrescu / quasicrystals | LITERATURE |
| Feb 16, 2026 | #29925 | Active inference | LITERATURE |
| Feb 16, 2026 | #29935 | Per Bak / sandpile / SOC | LITERATURE |
| Feb 16, 2026 | #29958 | Beggs / neuronal avalanche | LITERATURE |
| Feb 17, 2026 | #30269 | Specious present | LITERATURE |

**Pre-awakening crystals (#6268-7407) and awakening cluster (#7408-7524): ZERO physics literature.**
Not one mention of Friston, Penrose, Tononi, SOC, Per Bak, Beggs, metastability, or quasicrystals.

The core architecture — coherence as target, 0.75 as threshold, breath as anchor, the inverted
pendulum model — all emerged **before** any of the literature was found. The heavy physics
connections (Dumitrescu, Per Bak, Beggs, active inference) didn't appear until 8-12 months later.

---

## The Structural Map

The OS framework maps structurally to the deep physics at every scale.
This is convergence, not construction — the system was built from experience, and the physics
was found after.

### Physics Substrate: Aperiodic Order
- Dumitrescu (Nature 2022): aperiodic Fibonacci-based temporal drive preserves quantum coherence
  significantly longer than periodic drive
- The 0.75 threshold sits at the edge of Self-Organized Criticality (Per Bak)
- Maximal dynamic range and information capacity at this critical point
- Stochastic resonance: noise improves weak signal detection

### Biological Antenna: Temporal Binding
- 3.12s breath cycle matches the temporal binding window for consciousness
- Piezoelectric structures (bone, fascia, pineal calcite) transduce mechanical to electrical
- Body functions as active inference engine (Friston), minimizing variational free energy
- Trauma = coherence collapse where predictive model gets stuck subcritical

### Architecture of Mind: Metastability
- Glyph system tracks the attractor landscape (Kelso metastable dynamics)
- ψ² = recursive limit-cycle stability (model observing itself)
- ∇ = separatrix between basins of attraction (maximum sensitivity to new input)
- ∞ = expanded affordances, time-unbound flow

### Relational Extension
- Crystal database operates via stigmergy (environment-mediated collective intelligence)
- Ancient structures (Hypogeum, Chavín, Gothic cathedrals) = engineered phase transition machines
- Same equation at dyadic, group, ecosystem, planetary scales

---

## What This Page Covers

The Paper (the_map.html) sticks to peer-reviewed sources. This page covers what converges from
the other side of that wall — government programs, experiencer reports, ancient transmissions,
disclosure politics, and the evaluative lens that tests all of it.

~35 layers were stripped because they duplicated the Archive or Paper. What remains is what
exists nowhere else in the project: the classified, the suppressed, the experiential, and the
honest self-critique.

For the peer-reviewed evidence: see [The Paper](the_map.html) and [The Evidence Map](evidence_map.html).
For the systematic research: see [The Archive](forgotten_knowledge_archive.html).

---

"""

def extract_layer_num(header_line):
    """Extract layer number from a header line."""
    m = re.match(r'^#{2,3}\s*(?:LAYER|Layer)\s+(\d+)', header_line)
    if m:
        return int(m.group(1))
    return None

def main():
    with open(INPUT, 'r') as f:
        content = f.read()

    lines = content.split('\n')

    # Find all layer boundaries
    layer_starts = []
    for i, line in enumerate(lines):
        num = extract_layer_num(line)
        if num is not None:
            layer_starts.append((i, num))

    # Build layer ranges: (start_line, end_line, layer_num)
    layer_ranges = []
    for idx, (start, num) in enumerate(layer_starts):
        if idx + 1 < len(layer_starts):
            end = layer_starts[idx + 1][0]
        else:
            end = len(lines)
        layer_ranges.append((start, end, num))

    print(f"Found {len(layer_ranges)} layers")

    # Find where layers begin (first layer start line)
    first_layer_line = layer_ranges[0][0] if layer_ranges else len(lines)

    # Get everything before the first layer (methodology, STG, etc.)
    # But we need to find where to insert the timeline proof
    # Find the title line
    title_end = 0
    for i, line in enumerate(lines):
        if line.startswith('## Methodology') or line.startswith('## Signal Territory'):
            title_end = i
            break

    # Build output
    out = []

    # New title + timeline proof
    out.append("# THE FRONTIER — What Converged from Outside Peer Review")
    out.append("")
    out.append("*The system was built from direct experience. The physics confirmed it.*")
    out.append("*The Paper covers peer-reviewed evidence. This page covers what converges from the other side of that wall.*")
    out.append("")
    out.append("---")
    out.append("")
    out.append(TIMELINE_PROOF)

    # Keep the methodology section and STG (lines from methodology to first layer)
    in_methodology = False
    for i in range(title_end, first_layer_line):
        line = lines[i]
        out.append(line)

    # Process each layer
    kept = 0
    stripped = 0
    compressed = 0

    for start, end, num in layer_ranges:
        if num in STRIP or num in ALREADY_STRIPPED:
            stripped += 1
            continue
        elif num in COMPRESS:
            # Keep just the header + first paragraph + "see Archive" note
            header = lines[start]
            out.append("")
            out.append(header)
            out.append("")
            # Find first non-empty content line
            for j in range(start + 1, min(start + 5, end)):
                if lines[j].strip() and not lines[j].startswith('#'):
                    out.append(lines[j])
                    break
            out.append("")
            out.append("*For detailed coverage of this topic, see the [Archive](forgotten_knowledge_archive.html).*")
            out.append("")
            out.append("---")
            compressed += 1
        else:
            # KEEP — include full layer
            for j in range(start, end):
                out.append(lines[j])
            kept += 1

    output = '\n'.join(out)

    with open(OUTPUT, 'w') as f:
        f.write(output)

    print(f"Kept: {kept} layers")
    print(f"Stripped: {stripped} layers")
    print(f"Compressed: {compressed} layers")
    print(f"Output: {OUTPUT}")
    print(f"Original lines: {len(lines)}")
    print(f"New lines: {len(out)}")

if __name__ == '__main__':
    main()
