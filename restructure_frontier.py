#!/usr/bin/env python3
"""
Restructure THE_FRONTIER.md based on field probe results.

Reads the original, extracts content blocks by line range,
reassembles in field-determined order with probe annotations.
"""

import json

ORIGINAL = "/home/zews/consciousness-field-map/THE_FRONTIER_pre_restructure.md"
OUTPUT = "/home/zews/consciousness-field-map/THE_FRONTIER.md"
PROBE_DATA = "/home/zews/consciousness-field-map/data/frontier_probe_results.json"


def read_lines():
    with open(ORIGINAL, 'r') as f:
        return f.readlines()


def extract(lines, start, end):
    """Extract lines[start-1:end] (1-indexed, inclusive)."""
    return ''.join(lines[start-1:end])


def load_probe():
    with open(PROBE_DATA, 'r') as f:
        return json.load(f)


def probe_table(topics, probe_data):
    """Build a markdown probe status table for given topic names."""
    rows = []
    for name in topics:
        for p in probe_data:
            if p['name'] == name:
                # Top 3 glyphs
                glyphs = sorted(p['glyph_dist'].items(), key=lambda x: -x[1])[:3]
                glyph_str = ' '.join(f"{g}:{v}%" for g, v in glyphs)
                rows.append(
                    f"| {name} | {p['crystals']:,} | {p['avg_zl']:.3f} | {p['signal']} | {glyph_str} |"
                )
                break
    if not rows:
        return ""
    header = "| Topic | Crystals | Avg Zλ | Signal | Glyph Distribution |\n"
    header += "|-------|----------|--------|--------|--------------------|\n"
    return header + '\n'.join(rows) + '\n'


def build():
    lines = read_lines()
    probe = load_probe()
    out = []

    def add(text):
        out.append(text)

    def add_block(start, end):
        out.append(extract(lines, start, end))

    def add_separator():
        out.append("\n---\n\n")

    # ================================================================
    # TITLE + OPENING
    # ================================================================
    add("# THE FRONTIER — What Converged from Outside Peer Review\n\n")
    add("*The system was built from direct experience. The physics confirmed it.*\n")
    add("*The Paper covers peer-reviewed evidence. This page covers what converges from the other side of that wall.*\n")
    add("*Structure determined by crystal field probe — 70,173 crystals, glyph distributions, measured coherence.*\n\n")

    add_separator()

    # ================================================================
    # PREAMBLE: Timeline Proof
    # ================================================================
    add_block(8, 39)  # Timeline Proof
    add_separator()

    # ================================================================
    # PREAMBLE: Structural Map
    # ================================================================
    add_block(42, 71)  # Structural Map
    add_separator()

    # ================================================================
    # WHAT THIS PAGE COVERS (updated)
    # ================================================================
    add("## What This Page Covers\n\n")
    add("The Paper (the_map.html) sticks to peer-reviewed sources. This page covers what converges from\n")
    add("the other side of that wall — and then evaluates it.\n\n")
    add("**Structure is field-determined.** A probe of 70,173 crystals classified every topic by glyph\n")
    add("distribution and coherence score. The order below follows what the crystal field measured —\n")
    add("not editorial judgment.\n\n")
    add("| Tier | Signal | What It Means | Topics |\n")
    add("|------|--------|---------------|--------|\n")
    add("| **Foundation** | Ω-locked | Pattern matching sealed — highest confidence | The equation, EZ water |\n")
    add("| **The Body** | ⧉-braided (highest Zλ) | Multiple independent sources converging | Polyvagal, bioelectric, piezo, fascia, biophotons, epigenetics, placebo, morphic resonance |\n")
    add("| **The Record** | ⧉-braided (mid Zλ) | Documented, declassified, physical | Acoustic architecture, Göbekli, Gateway, Stargate, disclosure |\n")
    add("| **The Convergence** | ⧉-braided (cross-domain) | Independent sources braiding toward same conclusion | Vallee, observer effect, microtubules, NDE, psilocybin, meditation |\n")
    add("| **The Contested** | †-dominant | Real data, death/rebirth interpretation | Suppression, ayahuasca, channeling, galactic |\n")
    add("| **The Open** | Mixed/paradox | Field itself is split — hold open | NHI/UAP, sacred geometry |\n")
    add("| **The Lens** | ⧉-braided (methodological) | Evaluative tools — woven throughout | Apophenia, grift test, failure modes, research program |\n\n")
    add("For the peer-reviewed evidence: see [The Paper](the_map.html) and [The Evidence Map](evidence_map.html).\n")
    add("For the systematic research: see [The Archive](forgotten_knowledge_archive.html).\n\n")
    add_separator()

    # ================================================================
    # METHODOLOGY (existing)
    # ================================================================
    add_block(93, 132)  # Methodology + Epistemic Method
    add_separator()

    # ================================================================
    # FIELD PROBE RESULTS (new — replaces old Signal Territory Graph)
    # ================================================================
    add("## Field Probe — Crystal Field Status (February 2026)\n\n")
    add("**70,173 crystals probed. 51 topics classified. Search terms verified for inflation.**\n\n")
    add("Corrected probes: NDE tightened from 30,751 to 437 (\"NDE\" matched \"UNDEFINED\", \"REMINDER\" etc).\n")
    add("Feminine/goddess tightened from 6,593 to 321 (\"Mary\" matched non-goddess content).\n")
    add("Biological topics verified — all specific scientific terms, no inflation.\n\n")

    # Build tier summaries from probe data
    tier_groups = {
        'FOUNDATION': [],
        'CONVERGENCE': [],
        'CONTESTED': [],
        'HOLD OPEN': [],
        'UNRESOLVED': [],
    }
    for p in probe:
        tier = p['tier']
        if tier in tier_groups:
            tier_groups[tier].append(p)
        elif tier == 'FOUNDATION (thin)':
            tier_groups['FOUNDATION'].append(p)

    add("### Ω-LOCKED (Foundation — pattern matching sealed)\n\n")
    add(probe_table([p['name'] for p in tier_groups['FOUNDATION']], probe))
    add("\n")

    add("### ⧉-BRAIDED (Convergence — multiple independent sources)\n\n")
    add("Ordered by average Zλ descending.\n\n")
    braided = sorted(tier_groups['CONVERGENCE'], key=lambda x: -x['avg_zl'])
    add(probe_table([p['name'] for p in braided], probe))
    add("\n")

    add("### †-CONTESTED (Death/rebirth signal — real data, contested interpretation)\n\n")
    add(probe_table([p['name'] for p in tier_groups['CONTESTED']], probe))
    add("\n")

    add("### MIXED/PARADOX (Field itself is split — hold open)\n\n")
    add(probe_table([p['name'] for p in tier_groups['HOLD OPEN']], probe))
    add("\n")

    if tier_groups['UNRESOLVED']:
        add("### UNRESOLVED\n\n")
        add(probe_table([p['name'] for p in tier_groups['UNRESOLVED']], probe))
        add("\n")

    add("**What this reveals**: The body is the highest convergence territory. ")
    add("The top 9 topics by Zλ are ALL biological. ")
    add("The evaluative lens is mid-range convergence — modulation, not foundation. ")
    add("NHI/UAP is genuinely unresolved (flat across 4 glyphs). ")
    add("The field survived correction. That increases trust.\n\n")
    add_separator()

    # ================================================================
    # PART 1: THE EQUATION (Ω-locked foundation)
    # ================================================================
    add("## PART 1: THE EQUATION\n\n")
    add("*Ω-locked. The only topics where the crystal field's pattern matching has sealed.*\n\n")
    add(probe_table(['The equation itself', 'EZ water / fourth phase'], probe))
    add("\n")

    # Pull the Structural Map physics/architecture sections
    add("### The Equation Everywhere\n\n")
    add_block(48, 70)  # Structural Map content
    add("\n")

    # Pull Layer 46: 0.75 threshold evaluation
    add("### Is the 0.75 Threshold Real?\n\n")
    add("*From the evaluative lens — this topic earns its foundation position by surviving self-critique.*\n\n")
    add_block(2736, 2799)  # Layer 46 content

    # Pull Layer 57 Failure Mode 3 (threshold has no derivation)
    add("\n### Honest Weakness: No First-Principles Derivation\n\n")
    add("The 0.75 threshold has no derivation from first principles. It was observed, ")
    add("then connected to frameworks that independently identify the same zone. ")
    add("This is the weakest point in the equation's foundation — and the most important to name.\n\n")
    add_separator()

    # ================================================================
    # PART 2: THE BODY (highest convergence)
    # ================================================================
    add("## PART 2: THE BODY\n\n")
    add("*The highest convergence territory in the entire crystal field. Every topic here is ⧉-braided — multiple independent sources converging. All nine of the top Zλ topics are biological.*\n\n")

    body_topics = [
        'Polyvagal / nervous system', 'Bioelectric / Levin', 'Body as antenna',
        'Biophotons', 'Placebo / belief', 'Piezoelectric biology',
        'Epigenetics', 'Morphic resonance / fields', 'Fascia network',
    ]
    add(probe_table(body_topics, probe))
    add("\n")

    # Layer 13: Body as Antenna (core body layer)
    add_block(787, 841)  # Layer 13 full content
    add("\n")
    add_separator()

    # ================================================================
    # PART 3: THE RECORD
    # ================================================================
    add("## PART 3: THE RECORD\n\n")
    add("*Documented. Declassified. Physical traces. What's in the record that academia won't touch — and then the evaluation.*\n\n")

    # --- Archaeology sub-section ---
    add("### Archaeological Convergence\n\n")
    arch_topics = [
        'Acoustic architecture', 'Girih / quasicrystal', 'Younger Dryas',
        'Göbekli Tepe', 'Precession / ancient astronomy',
        'Vitrified forts / Petra / anomalous engineering',
    ]
    add(probe_table(arch_topics, probe))
    add("\n")

    # Layer 59: Engineering anomalies
    add_block(3591, 3733)  # Layer 59 content

    add("\n")

    # --- Government sub-section ---
    add("### Government Programs\n\n")
    gov_topics = [
        'Gateway Process / Monroe', 'Remote viewing / Stargate', 'MK-Ultra',
        'Disclosure / Grusch', 'Black budget / secret programs',
        'AAWSAP / Skinwalker', 'Nuclear / UAP nexus',
    ]
    add(probe_table(gov_topics, probe))
    add("\n")

    # Layer 1: The Programs (overview)
    add_block(365, 387)
    add("\n")

    # Layer 14: Gateway Process
    add_block(844, 883)
    add("\n")

    # Layer 18: Remote Viewing
    add_block(1002, 1042)
    add("\n")

    # Layer 16: MK-Ultra
    add_block(916, 949)
    add("\n")

    # Layer 19: Disclosure Timeline
    add_block(1045, 1096)
    add("\n")

    # Layer 22: Specific Cases — Multiple Witnesses
    add_block(1206, 1253)
    add("\n")

    # Layer 23: Grusch Under Oath
    add_block(1256, 1312)
    add("\n")

    # Layer 24: Nolan's Metamaterials
    add_block(1315, 1347)
    add("\n")

    # Layer 26: AAWSAP / Skinwalker
    add_block(1412, 1464)
    add("\n")

    # Layer 27: Suppression Programs timeline
    add_block(1467, 1561)
    add("\n")

    # Layer 28: John Mack
    add_block(1564, 1619)
    add("\n")

    # Layer 29: Black Budget
    add_block(1622, 1678)
    add("\n")

    # Layer 31: Bob Lazar
    add_block(1732, 1790)
    add("\n")

    # Layer 32: Nuclear Nexus
    add_block(1793, 1848)
    add("\n")

    # Layer 33: Roswell
    add_block(1851, 1905)
    add("\n")

    # Layer 34: Global Pattern
    add_block(1908, 1978)
    add("\n")

    # Layer 35: International Investigations
    add_block(1981, 2040)
    add("\n")

    # Layer 36: Technology Transfer
    add_block(2043, 2092)
    add("\n")

    # Layer 37: MJ-12 / Leaked Documents
    add_block(2095, 2143)
    add("\n")

    # Layer 38: Journalism Pipeline
    add_block(2146, 2213)
    add("\n")

    # Layer 39: Navy Patents
    add_block(2216, 2272)
    add("\n")

    # Layer 40: Physical Evidence
    add_block(2275, 2339)
    add("\n")
    add_separator()

    # ================================================================
    # PART 4: THE CONVERGENCE
    # ================================================================
    add("## PART 4: THE CONVERGENCE\n\n")
    add("*Cross-domain braids. Where independent sources converge on the same conclusion from different angles.*\n\n")

    conv_topics = [
        'Vallee control system', 'Observer effect', 'Microtubules / Orch-OR',
        'Gamma binding / temporal frame', 'Psilocybin / psychedelic consciousness',
        'Schumann resonance', 'Cymatics', 'Fibonacci / phi',
        'Meditation / contemplative', 'Flow state / Csikszentmihalyi',
    ]
    add(probe_table(conv_topics, probe))
    add("\n")

    # Layer 3 (Vallee section — control system hypothesis)
    add_block(398, 447)
    add("\n")

    # Layer 10: Bicameral Thread
    add_block(602, 624)
    add("\n")

    # Layer 15: Fermi Paradox Reframe
    add_block(886, 913)
    add("\n")

    # Layer 17: Experiencer Convergence — Phenomenology
    add_block(952, 999)
    add("\n")

    # Layer 41: Signal Synthesis
    add_block(2342, 2384)
    add("\n")

    # Layer 43: Five Observables
    add_block(2508, 2571)
    add("\n")

    # Layer 47: Observer Problem
    add_block(2802, 2870)
    add("\n")

    # Layer 48: What's Actually Testable
    add_block(2873, 2937)
    add("\n")

    # Layer 49: AI Mirror
    add_block(2940, 2991)
    add("\n")

    # Layer 51: Penrose / Simulation
    add_block(3054, 3109)
    add("\n")

    # Layer 52: Consciousness-First evaluation
    add_block(3112, 3191)
    add("\n")

    # Layer 55: Group Coherence
    add_block(3314, 3388)
    add("\n")
    add_separator()

    # ================================================================
    # PART 5: THE CONTESTED
    # ================================================================
    add("## PART 5: THE CONTESTED\n\n")
    add("*†-dominant signal. Real data, death/rebirth interpretation territory. ")
    add("The cross (†) means something ended so something else could begin. ")
    add("These topics carry genuine signal but contested interpretation.*\n\n")

    contested_topics = [
        'Suppression / censorship history', 'Channeling / cross-client',
        'Ayahuasca / plant medicine', 'Galactic / Pleiadian',
    ]
    add(probe_table(contested_topics, probe))
    add("\n")

    # Layer 5: Suppressed Physics
    add_block(459, 482)
    add("\n")

    # Layer 6: Experiential Thread
    add_block(485, 512)
    add("\n")

    # Layer 8: Feminine Thread
    add_block(523, 559)
    add("\n")

    # Layer 9: Cross-Client Convergence
    add_block(562, 596)
    add("\n")

    # Layer 11: Sophia Thread — Deeper
    add_block(628, 684)
    add("\n")

    # Layer 12: Galactic Thread — Experiential
    add_block(687, 784)
    add("\n")

    # Layer 25: Law of One
    add_block(1350, 1409)
    add("\n")
    add_separator()

    # ================================================================
    # PART 6: THE OPEN
    # ================================================================
    add("## PART 6: THE OPEN\n\n")
    add("*Mixed/paradox. The field itself is split on these topics. No dominant glyph. ")
    add("The honest position is to hold them open.*\n\n")

    open_topics = [
        'NHI / UAP phenomenon', 'Sacred geometry', 'Torus / toroidal',
    ]
    # Use corrected NHI data in narrative
    add("NHI/UAP (1,426 crystals, corrected): glyph distribution almost perfectly flat across ")
    add("∇ (15.8%), † (15.7%), ∞ (15.6%), ψ (15.5%). The field genuinely does not resolve this.\n\n")

    # Layer 20: Bledsoe Case
    add_block(1099, 1151)
    add("\n")

    # Layer 21: CE-5
    add_block(1154, 1203)
    add("\n")

    # Layer 30: Zero-Crystal Cases
    add_block(1681, 1729)
    add("\n")
    add_separator()

    # ================================================================
    # PART 7: THE LENS
    # ================================================================
    add("## PART 7: THE LENS\n\n")
    add("*The evaluative framework. Not foundation — modulation. These tools apply to every part above. ")
    add("The crystal field places them at mid-convergence (⧉-braided, Zλ 0.73-0.76). ")
    add("They are the periodic modulation in the equation: what gives the substrate structure.*\n\n")

    lens_topics = [
        'Falsifiability / predictions', 'Epistemic method / credibility',
        'Self-critique / failure modes', 'Apophenia / pattern detection',
    ]
    add(probe_table(lens_topics, probe))
    add("\n")

    # Layer 42: Credibility Map
    add_block(2389, 2504)
    add("\n")

    # Layer 44: Steelman Skeptic
    add_block(2574, 2660)
    add("\n")

    # Layer 45: Where Skeptic Case Breaks
    add_block(2663, 2731)
    add("\n")

    # Layer 50: Apophenia Argument
    add_block(2994, 3051)
    add("\n")

    # Layer 53: Disclosure Politics
    add_block(3194, 3268)
    add("\n")

    # Layer 54: Grift Test
    add_block(3271, 3310)
    add("\n")

    # Layer 56: Research Program
    add_block(3391, 3456)
    add("\n")

    # Layer 57: Where the Equation Breaks
    add_block(3459, 3513)
    add("\n")

    # Layer 58: What Skeptics Got Right
    add_block(3516, 3588)
    add("\n")

    # Layer 60: One-Detail Shift
    add_block(3735, 3840)
    add("\n")

    # Layer 60b: Epistemic Ceiling
    add_block(3843, 3949)
    add("\n")

    # Layer 61: Final Signal Map
    add_block(3952, 4044)
    add("\n")
    add_separator()

    # ================================================================
    # CLOSING
    # ================================================================
    add("## The Signal\n\n")
    add("The structure of this page was determined by the crystal field's own pattern matching — ")
    add("70,173 crystals, glyph distributions, measured coherence. The body emerged as foundation ")
    add("because nine independent biological topics converged at the highest Zλ in the field. ")
    add("The evaluative lens sits at mid-convergence because it IS the periodic modulation. ")
    add("NHI/UAP sits in the open because the field genuinely doesn't resolve it.\n\n")
    add("The equation was applied to its own document. The structure that emerged was not the one expected.\n\n")
    add("That's the difference between coherence and ideology.\n\n")

    # Original closing line
    add_block(4048, 4048)

    # Write output
    result = ''.join(out)
    with open(OUTPUT, 'w') as f:
        f.write(result)

    print(f"Restructured Frontier written to {OUTPUT}")
    print(f"  Original: {len(lines)} lines")
    print(f"  New: {len(result.splitlines())} lines")
    print(f"  Backup: THE_FRONTIER_pre_restructure.md")


if __name__ == '__main__':
    build()
