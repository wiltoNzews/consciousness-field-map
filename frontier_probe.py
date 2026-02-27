#!/usr/bin/env python3
"""
Frontier Field Probe — Let the crystal field determine the restructure order.

For each Frontier topic, queries the crystal DB, computes:
- Crystal count
- Average Zλ
- Glyph distribution (canonical 10 only)
- Field signal classification
- Confidence tier

The output determines the foundation order of the restructured Frontier.
"""

import sqlite3
import json
from collections import Counter

DB_PATH = "/home/zews/wiltonos/data/crystals_unified.db"

# Canonical glyphs
CANONICAL = ['∅', 'ψ', 'ψ²', '∇', '∞', 'Ω', '†', '⧉', 'ψ³', '🜛']

def normalize_glyph(g):
    """Map non-canonical glyph strings to canonical."""
    if not g or g == '?' or g.strip() == '':
        return None
    if g in CANONICAL:
        return g
    # Map common variants
    mapping = {
        '∅∞': '∞', '∇Ω': 'Ω', '∇ψ': '∇', 'ψΩ⟲': 'Ω',
        '∞ψΩ': '∞', '∇Ω∞': '∞', 'Ω∞': '∞', 'ψ∇Ω': '∇',
    }
    return mapping.get(g, None)


def probe_topic(conn, name, search_terms, exclude_terms=None):
    """
    Probe the crystal field for a topic.
    search_terms: list of strings to search for (OR logic)
    exclude_terms: list of strings to exclude (AND NOT logic)
    """
    c = conn.cursor()

    # Build query
    where_parts = []
    params = []
    for term in search_terms:
        where_parts.append("content LIKE ?")
        params.append(f"%{term}%")

    where_clause = "(" + " OR ".join(where_parts) + ")"

    if exclude_terms:
        for term in exclude_terms:
            where_clause += " AND content NOT LIKE ?"
            params.append(f"%{term}%")

    query = f"""
        SELECT id, content, zl_score, glyph_primary, created_at
        FROM crystals
        WHERE {where_clause}
        AND is_valid = 1
    """

    c.execute(query, params)
    rows = c.fetchall()

    if not rows:
        return {
            'name': name,
            'crystals': 0,
            'avg_zl': 0,
            'glyph_dist': {},
            'signal': 'NO DATA',
            'tier': 'none'
        }

    # Compute stats
    zl_scores = [r[2] for r in rows if r[2] is not None and r[2] > 0]
    avg_zl = sum(zl_scores) / len(zl_scores) if zl_scores else 0

    # Glyph distribution (canonical only)
    glyph_counts = Counter()
    for r in rows:
        g = normalize_glyph(r[3])
        if g:
            glyph_counts[g] += 1

    total_glyphed = sum(glyph_counts.values())
    glyph_pct = {}
    if total_glyphed > 0:
        for g in CANONICAL:
            if glyph_counts[g] > 0:
                glyph_pct[g] = round(glyph_counts[g] / total_glyphed * 100, 1)

    # Determine dominant glyph
    dominant = glyph_counts.most_common(1)[0] if glyph_counts else (None, 0)
    dom_glyph = dominant[0]
    dom_pct = (dominant[1] / total_glyphed * 100) if total_glyphed > 0 else 0

    # Classify field signal
    omega_pct = glyph_pct.get('Ω', 0)
    psi3_pct = glyph_pct.get('ψ³', 0)
    braid_pct = glyph_pct.get('⧉', 0)
    cross_pct = glyph_pct.get('†', 0)
    psi_pct = glyph_pct.get('ψ', 0)
    inf_pct = glyph_pct.get('∞', 0)
    nabla_pct = glyph_pct.get('∇', 0)

    signal = 'UNCLASSIFIED'
    if omega_pct >= 30 and avg_zl >= 0.85:
        signal = 'Ω-LOCKED'
    elif omega_pct >= 20 and psi3_pct >= 15 and avg_zl >= 0.85:
        signal = 'Ω+ψ³ DEEP LOCK'
    elif psi3_pct >= 20 and avg_zl >= 0.85:
        signal = 'ψ³-DEEP'
    elif braid_pct >= 15:
        signal = '⧉-BRAIDED'
    elif cross_pct >= 20:
        signal = '†-CONTESTED'
    elif psi_pct + inf_pct > 50:
        signal = 'ASCENT'
    elif dom_pct < 30:
        signal = 'MIXED/PARADOX'
    else:
        signal = f'DOMINANT-{dom_glyph}' if dom_glyph else 'SPARSE'

    # Confidence tier based on signal + crystal count + avg_zl
    if signal.startswith('Ω') and len(rows) >= 10:
        tier = 'FOUNDATION'
    elif signal.startswith('Ω') and len(rows) < 10:
        tier = 'FOUNDATION (thin)'
    elif signal == 'ψ³-DEEP' or signal == 'Ω+ψ³ DEEP LOCK':
        tier = 'PARADIGM'
    elif signal == '⧉-BRAIDED':
        tier = 'CONVERGENCE'
    elif signal == '†-CONTESTED':
        tier = 'CONTESTED'
    elif signal == 'ASCENT':
        tier = 'BUILDING'
    elif signal == 'MIXED/PARADOX':
        tier = 'HOLD OPEN'
    else:
        tier = 'UNRESOLVED'

    # Date range
    dates = [r[4] for r in rows if r[4]]
    earliest = min(dates) if dates else 'N/A'
    latest = max(dates) if dates else 'N/A'

    return {
        'name': name,
        'crystals': len(rows),
        'with_zl': len(zl_scores),
        'avg_zl': round(avg_zl, 3),
        'glyph_dist': glyph_pct,
        'dominant': f"{dom_glyph} ({dom_pct:.0f}%)" if dom_glyph else 'none',
        'signal': signal,
        'tier': tier,
        'earliest': earliest[:10] if earliest != 'N/A' else 'N/A',
        'latest': latest[:10] if latest != 'N/A' else 'N/A',
    }


# ============================================================
# TOPIC DEFINITIONS
# Each topic maps to the Frontier's actual content domains
# ============================================================

TOPICS = {
    # === EVALUATIVE / METHODOLOGICAL ===
    'Apophenia / pattern detection': {
        'terms': ['apophenia', 'pattern matching', 'confirmation bias', 'pareidolia'],
    },
    'Falsifiability / predictions': {
        'terms': ['falsif', 'prediction', 'testable', 'would kill', 'would prove'],
        'exclude': ['predicted winner', 'predict the map'],
    },
    'Epistemic method / credibility': {
        'terms': ['epistemic', 'credibility', 'evidence tier', 'signal vs noise', 'bullshit test', 'grift test'],
    },
    'Self-critique / failure modes': {
        'terms': ['failure mode', 'self-critique', 'honest about', 'where it breaks', 'what breaks'],
    },

    # === GOVERNMENT PROGRAMS (DECLASSIFIED) ===
    'Gateway Process / Monroe': {
        'terms': ['Gateway Process', 'Monroe Institute', 'Hemi-Sync', 'Robert Monroe'],
    },
    'MK-Ultra': {
        'terms': ['MK-Ultra', 'MKULTRA', 'MK Ultra'],
    },
    'Remote viewing / Stargate': {
        'terms': ['remote viewing', 'Stargate program', 'Ingo Swann', 'Hal Puthoff', 'SRI International'],
    },
    'AAWSAP / Skinwalker': {
        'terms': ['AAWSAP', 'Skinwalker', 'AATIP', 'Lacatski'],
    },
    'Disclosure / Grusch': {
        'terms': ['Grusch', 'disclosure', 'NDAA', 'congressional', 'whistleblower'],
        'exclude': ['Biden', 'Trump', 'election'],
    },

    # === PHYSICAL/ENGINEERING ANOMALIES ===
    'Piezoelectric biology': {
        'terms': ['piezoelectric', 'piezo', 'quartz crystal', 'collagen piezo'],
    },
    'Bioelectric / Levin': {
        'terms': ['bioelectric', 'Levin', 'bioelectr', 'voltage gradient', 'morphogenetic field'],
    },
    'EZ water / fourth phase': {
        'terms': ['EZ water', 'exclusion zone water', 'fourth phase', 'Pollack water', 'Gerald Pollack'],
    },
    'Biophotons': {
        'terms': ['biophoton', 'bio-photon', 'Fritz-Albert Popp'],
    },
    'Fascia network': {
        'terms': ['fascia', 'connective tissue', 'myofascial'],
    },
    'Acoustic architecture': {
        'terms': ['Hypogeum', 'acoustic architecture', 'resonant chamber', 'Gothic acoustic', 'Chavín', 'neuroacoustic'],
    },
    'Vitrified forts / Petra / anomalous engineering': {
        'terms': ['vitrified fort', 'Petra hydraulic', 'anomalous engineering', 'ancient engineering', 'megalithic precision'],
    },

    # === CONSCIOUSNESS CONVERGENCE ===
    'NDE / AWARE': {
        'terms': ['near-death', 'NDE', 'AWARE study', 'Parnia', 'van Lommel', 'clinical death'],
    },
    'Psilocybin / psychedelic consciousness': {
        'terms': ['psilocybin', 'psychedelic', 'Griffiths', 'mystical experience', 'Carhart-Harris'],
        'exclude': ['microdose schedule'],
    },
    'Meditation / contemplative': {
        'terms': ['meditation', 'contemplative', 'mindfulness', 'vipassana', 'jhana'],
    },
    'Body as antenna': {
        'terms': ['body as antenna', 'body antenna', 'human antenna', 'piezoelectric body', 'transducer'],
    },
    'Polyvagal / nervous system': {
        'terms': ['polyvagal', 'vagus nerve', 'Porges', 'ventral vagal', 'dorsal vagal'],
    },
    'Gamma binding / temporal frame': {
        'terms': ['gamma binding', 'gamma oscillation', '40 Hz', 'temporal binding', 'Singer', 'Ricard meditation'],
    },
    'Epigenetics': {
        'terms': ['epigenetic', 'transgenerational', 'methylation', 'Yehuda', 'inherited trauma'],
    },
    'Placebo / belief': {
        'terms': ['placebo', 'nocebo', 'Kaptchuk', 'belief effect', 'open-label placebo'],
    },
    'Morphic resonance / fields': {
        'terms': ['morphic resonance', 'Sheldrake', 'morphogenetic', 'Gurwitsch'],
    },

    # === ARCHAEOLOGICAL ===
    'Göbekli Tepe': {
        'terms': ['Göbekli', 'Gobekli', 'Schmidt excavat'],
    },
    'Younger Dryas': {
        'terms': ['Younger Dryas', 'Wolbach', 'impact hypothesis', '10800 BCE', '12800'],
    },
    'Precession / ancient astronomy': {
        'terms': ['precession', 'Santillana', 'yuga cycle', 'ancient astronomy', 'Hamlet\'s Mill'],
    },
    'Girih / quasicrystal': {
        'terms': ['girih', 'quasicrystal', 'Penrose tiling', 'aperiodic tiling'],
    },

    # === EXPERIENTIAL / HIGH-VOLTAGE ===
    'Ayahuasca / plant medicine': {
        'terms': ['ayahuasca', 'DMT', 'plant medicine', 'Santo Daime', 'UDV'],
    },
    'NHI / UAP phenomenon': {
        'terms': ['NHI', 'UAP', 'UFO', 'unidentified aerial', 'non-human intelligence'],
    },
    'Vallee control system': {
        'terms': ['Vallee', 'Jacques Vallée', 'control system', 'Passport to Magonia'],
    },
    'Channeling / cross-client': {
        'terms': ['channeling', 'channelled', 'Dolores Cannon', 'Bashar', 'Law of One', 'Ra Material'],
    },
    'Sumerian / Anunnaki': {
        'terms': ['Sumerian', 'Anunnaki', 'Enki', 'Enlil', 'Sitchin'],
    },
    'Galactic / Pleiadian': {
        'terms': ['Pleiadian', 'galactic', 'star seed', 'Arcturian', 'galactic federation'],
        'exclude': ['Grand Slam', 'Galaxy'],
    },
    'Sophia / Gnostic': {
        'terms': ['Sophia', 'Gnostic', 'Nag Hammadi', 'archon', 'demiurge', 'pleroma'],
    },
    'Feminine / goddess thread': {
        'terms': ['Lady in White', 'Bledsoe', 'Hathor', 'divine feminine', 'goddess', 'Isis', 'Mary'],
        'exclude': ['Mary Poppins', 'Mary Jane'],
    },

    # === CROSS-DOMAIN BRAIDS ===
    'Microtubules / Orch-OR': {
        'terms': ['microtubule', 'Orch-OR', 'Penrose-Hameroff', 'Hameroff', 'quantum brain'],
    },
    'Cymatics': {
        'terms': ['cymatics', 'Chladni', 'sound geometry', 'Jenny cymatics'],
    },
    'Sacred geometry': {
        'terms': ['sacred geometry', 'flower of life', 'seed of life', 'Metatron cube', 'vesica piscis'],
    },
    'Schumann resonance': {
        'terms': ['Schumann', '7.83', 'Earth resonance', 'cavity resonance'],
    },
    'Fibonacci / phi': {
        'terms': ['Fibonacci', 'golden ratio', 'phi ratio', '1.618', 'phyllotaxis'],
    },
    'Torus / toroidal': {
        'terms': ['torus', 'toroidal', 'doughnut', 'vector equilibrium'],
    },
    'Observer effect': {
        'terms': ['observer effect', 'double slit', 'Wheeler delayed', 'measurement problem'],
    },
    'Flow state / Csikszentmihalyi': {
        'terms': ['flow state', 'Csikszentmihalyi', 'optimal experience', 'in the zone'],
    },

    # === SUPPRESSION PATTERN ===
    'Suppression / censorship history': {
        'terms': ['suppressed', 'censored', 'burned', 'library destruction', 'forbidden knowledge', 'book burning'],
    },
    'Tesla / suppressed physics': {
        'terms': ['Tesla', 'Nikola Tesla', 'free energy', 'zero point'],
        'exclude': ['Tesla car', 'Tesla stock', 'Model S'],
    },
    'Black budget / secret programs': {
        'terms': ['black budget', 'SAP ', 'special access program', 'compartment', 'unacknowledged'],
    },

    # === NUCLEAR NEXUS ===
    'Nuclear / UAP nexus': {
        'terms': ['nuclear', 'Malmstrom', 'nuclear site', 'nuclear weapon', 'missile shutdown'],
        'exclude': ['nuclear family'],
    },

    # === SELF-REFERENTIAL ===
    'Crystal field convergence': {
        'terms': ['crystal field', 'glyph distribution', 'field probe', 'the field says'],
    },
    'The equation itself': {
        'terms': ['aperiodic substrate', 'periodic modulation', 'coherence equation', 'ψ = aperiodic'],
    },
}


def main():
    conn = sqlite3.connect(DB_PATH)

    results = []
    for name, config in TOPICS.items():
        r = probe_topic(conn, name, config['terms'], config.get('exclude'))
        results.append(r)

    conn.close()

    # Sort by tier priority, then by avg_zl descending
    tier_order = {
        'FOUNDATION': 0,
        'FOUNDATION (thin)': 1,
        'PARADIGM': 2,
        'CONVERGENCE': 3,
        'CONTESTED': 4,
        'HOLD OPEN': 5,
        'BUILDING': 6,
        'UNRESOLVED': 7,
        'none': 8,
    }

    results.sort(key=lambda r: (tier_order.get(r['tier'], 9), -r['avg_zl']))

    # Print results
    print("=" * 120)
    print("FRONTIER FIELD PROBE — Crystal Field Determines Foundation Order")
    print(f"Database: {DB_PATH} — 70,173 crystals")
    print("=" * 120)

    current_tier = None
    for r in results:
        if r['tier'] != current_tier:
            current_tier = r['tier']
            print(f"\n{'─' * 120}")
            print(f"  TIER: {current_tier}")
            print(f"{'─' * 120}")

        glyph_str = '  '.join(f"{g}:{p}%" for g, p in sorted(r['glyph_dist'].items(), key=lambda x: -x[1])[:5])
        print(f"\n  {r['name']}")
        print(f"    Crystals: {r['crystals']:,}  |  Avg Zλ: {r['avg_zl']:.3f}  |  Signal: {r['signal']}  |  Dominant: {r['dominant']}")
        print(f"    Glyphs: {glyph_str}")
        print(f"    Date range: {r['earliest']} → {r['latest']}")

    # Print foundation order summary
    print(f"\n\n{'=' * 120}")
    print("PROPOSED FOUNDATION ORDER (field-determined)")
    print(f"{'=' * 120}")

    for i, tier_name in enumerate(['FOUNDATION', 'FOUNDATION (thin)', 'PARADIGM', 'CONVERGENCE', 'CONTESTED', 'HOLD OPEN', 'BUILDING']):
        tier_topics = [r for r in results if r['tier'] == tier_name]
        if tier_topics:
            print(f"\n  {i+1}. {tier_name} ({len(tier_topics)} topics)")
            for r in tier_topics:
                print(f"     {'●' if r['crystals'] >= 20 else '○'} {r['name']} ({r['crystals']:,} crystals, Zλ={r['avg_zl']:.3f}, {r['signal']})")

    # Save full results as JSON for further analysis
    with open('/home/zews/consciousness-field-map/data/frontier_probe_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n\nFull results saved to data/frontier_probe_results.json")


if __name__ == '__main__':
    main()
