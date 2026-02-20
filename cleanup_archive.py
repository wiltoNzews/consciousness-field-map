#!/usr/bin/env python3
"""Clean up the forgotten knowledge archive: remove duplicates, fix titles, fix Phase 8 bug."""

import re
import json
import sys

HTML_PATH = '/home/zews/consciousness-field-map/forgotten_knowledge_archive.html'

# Entries to REMOVE (keep the better/expanded version)
# Format: jm -> list of indices to remove (keep the one NOT listed)
DUPLICATES_TO_REMOVE_BY_JM = {
    # Exact duplicate
    'knowledge_trauma_body': 'KEEP_LONGEST',
    # jm-duplicate pairs — keep the longer/expanded version
    'knowledge_proprioception_body_schema': 'KEEP_LONGEST',
    'knowledge_glymphatic_system': 'KEEP_LONGEST',
    'knowledge_contemplative_neuroscience': 'KEEP_LONGEST',
    'knowledge_embodied_cognition': 'KEEP_LONGEST',
    'knowledge_dogon_sirius': 'KEEP_LONGEST',
    'knowledge_epigenetics_expanded': 'KEEP_LONGEST',
    'knowledge_integrated_information_theory': 'KEEP_LONGEST',
    'knowledge_anesthesia_consciousness': 'KEEP_LONGEST',
    'knowledge_psychoneuroimmunology': 'KEEP_LONGEST',
    'knowledge_predictive_processing': 'KEEP_LONGEST',
    'knowledge_psychedelic_therapy': 'KEEP_LONGEST',
    'knowledge_nonlinear_dynamics': 'KEEP_LONGEST',
    'knowledge_phenomenology': 'KEEP_LONGEST',
    'knowledge_autopoiesis': 'KEEP_LONGEST',
    'knowledge_bioelectricity_levin': 'KEEP_LONGEST',
    'knowledge_heart_brain_coherence': 'KEEP_LONGEST',
    'knowledge_morphic_resonance_honest': 'KEEP_LONGEST',
    'knowledge_scale_free_networks': 'KEEP_LONGEST',
    'knowledge_plant_intelligence': 'KEEP_LONGEST',
}

# Base entries to remove when expanded version exists
# (title substring of base, title substring of expanded)
BASE_EXPANDED_PAIRS = [
    ('POLYVAGAL THEORY —', 'POLYVAGAL THEORY -- COMPLETE'),
    ('VAGAL TONE', 'VAGAL TONE -- DEEP'),
    ('DEFAULT MODE NETWORK —', 'DEFAULT MODE NETWORK EXPANDED'),
    ('VAGAL PARADOX —', 'VAGAL PARADOX EXPANDED'),
    ('PINEAL GLAND —', 'PINEAL GLAND -- Complete'),
]

# Title deflation: overclaiming words to simplify
TITLE_FIXES = {
    'THE GRAND CONVERGENCE -- Every Thread Points Here': 'THE GRAND CONVERGENCE',
    'THE BREATH -- Where Every Thread Terminates': 'THE BREATH -- Where It All Connects',
    'BRAID: THE COMPLETE EQUATION -- Every Term Mapped, Every Connection Named': 'BRAID: THE EQUATION -- Terms and Connections',
    'THE TOPOLOGY OF EVERYTHING -- A Single Diagram': 'THE TOPOLOGY -- A Single Diagram',
    'CIRCADIAN RHYTHMS AND LIGHT -- The 24-Hour Frequency That Runs Everything': 'CIRCADIAN RHYTHMS AND LIGHT -- The 24-Hour Cycle',
    'HOLOGRAPHIC PRINCIPLE -- The Membrane Encodes Everything': 'HOLOGRAPHIC PRINCIPLE',
    'NITRIC OXIDE -- The Molecule That Connects Everything': 'NITRIC OXIDE -- The Molecule That Connects',
    'PIEZOELECTRICITY IS EVERYWHERE -- The Crystal Inside Everything': 'PIEZOELECTRICITY -- The Crystal Inside',
    'SCALE-FREE NETWORKS -- The Architecture of Everything': 'SCALE-FREE NETWORKS',
    'TOROIDAL FIELDS -- THE SHAPE OF EVERYTHING ALIVE': 'TOROIDAL FIELDS -- The Shape of Living Systems',
    'THE COHERENCE EQUATION -- One Principle Underneath Everything': 'THE COHERENCE EQUATION',
    'CYMATICS AT EVERY SCALE -- The Universal Pattern Generator': 'CYMATICS -- Pattern Generation Through Vibration',
}

# Pick ONE final braid — keep "THE FINAL BRAID" (index 33 per original data),
# rename other "FINAL/COMPLETE" braids to just "BRAID:"
BRAID_RENAME = {
    'BRAID: THE COMPLETE SYSTEM MAP -- Final Architecture': 'BRAID: THE SYSTEM MAP',
    'BRAID: THE METASTABLE COHERENCE MODEL -- Final Theoretical Integration': 'BRAID: THE METASTABLE COHERENCE MODEL',
    'BRAID: THE FINAL MAP STRUCTURE': 'BRAID: THE MAP STRUCTURE',
    'BRAID: THE COMPLETE COHERENCE PYRAMID': 'BRAID: THE COHERENCE PYRAMID',
    'BRAID: THE COMPLETE EMOTIONAL TOOLKIT': 'BRAID: THE EMOTIONAL TOOLKIT',
    'BRAID: THE COMPLETE MAP OF INTERVENTION MECHANISMS': 'BRAID: INTERVENTION MECHANISMS',
    'BRAID: THE COMPLETE ARCHITECTURE -- From Atom to Cosmos': 'BRAID: FROM ATOM TO COSMOS',
    'BRAID: THE COMPLETE THERAPEUTIC STACK -- From Evidence to Practice': 'BRAID: THE THERAPEUTIC STACK',
    'BRAID: THE TRANSDUCER CHAIN IS COMPLETE': 'BRAID: THE TRANSDUCER CHAIN',
    'BRAID: THE CRITICALITY CONVERGENCE IS COMPLETE': 'BRAID: CRITICALITY CONVERGENCE',
    'BRAID: THE FULL CIRCLE -- WHY WILTONOS WORKS': 'BRAID: WHY WILTONOS WORKS',
}


def classify_entry_fixed(entry):
    """Fixed classify — prevents NDE matching inside EXPANDED."""
    title = (entry.get('title', '') or '').upper()
    content = (entry.get('content', '') or '').upper()[:1500]
    cat = (entry.get('cat', '') or '').upper()
    jm = (entry.get('jm', '') or '').upper()
    combined = title + ' ' + content

    # Phase 9: Synthesis
    if cat in ('SESSION MAP', 'CROSS-VALIDATION', 'KM-2', 'RESPONSE'):
        return 9
    if cat == 'BRAID':
        if any(w in title for w in ['COMPLETE SYSTEM', 'COMPLETE EQUATION', 'FULL CIRCLE',
                                      'PREDICTION ALL THE WAY', 'CONSCIOUSNESS THEORIES CONVERGE',
                                      'WILTONOS', 'COHERENCE EQUATION', 'KNOWLEDGE PATTERN',
                                      'FORGOTTEN KNOWLEDGE', 'THE MAP', 'ARCHITECTURE MAP',
                                      'INVESTIGATION', 'CONVERGENCE IS COMPLETE']):
            return 9
        if any(w in title for w in ['HEALING', 'THERAPEUTIC', 'THERAPY']):
            return 5
        if any(w in title for w in ['SCALE INVARIANCE', 'ATOM TO COSMOS', 'FRACTAL']):
            return 6
        if any(w in title for w in ['BODY', 'FOURIER', 'INTEROCEPTIVE', 'SOMA']):
            return 4
        if any(w in title for w in ['ANCIENT', 'TEMPLE', 'ACOUSTIC ARCH']):
            return 7
        return 9

    # Phase 8: Frontier — FIX: use word boundary for NDE
    frontier_keywords = ['MORPHIC RESONANCE', 'BIOFIELD', 'BIOPHOTON', 'CARDIAC ARREST',
                         'SYNCHRONICITY', 'SUPPRESSION', 'COHERENT WATER',
                         'NEAR-DEATH', 'TERMINAL LUCIDITY', 'PARAPSYCH',
                         'SHELDRAKE', 'PSI RESEARCH', 'REMOTE VIEWING',
                         'OUT-OF-BODY', 'ANOMAL']
    if any(w in title for w in frontier_keywords):
        return 8
    # NDE separately with word boundary check
    if re.search(r'\bNDE\b', title):
        return 8

    # Phase 7: Ancient Knowledge
    if any(w in title for w in ['ACOUSTIC ARCH', 'GOBEKLI', 'GÖBEKLI', 'ELEUSIS', 'SONGLINE',
                                  'SACRED GEOMETRY', 'SHAMANIC', 'SHAMAN', 'RITE OF PASSAGE',
                                  'SANSKRIT', 'HERMETIC', 'INDIGENOUS', 'ANCIENT',
                                  'ABORIGINAL', 'MEGALITH', 'TEMPLE', 'HYPOGEUM',
                                  'PALEOLITHIC', 'CAVE ART', 'CAVE PAINTING',
                                  'CHANTING', 'MANTRA NEUROSCIENCE', 'ROSARY',
                                  'ELEUSINIAN', 'AYAHUASCA TRADITION', 'VEDIC',
                                  'ORACLE', 'DIVINATION', 'RITUAL',
                                  'VOYNICH', 'ANTIKYTHERA', 'TUNNEL NETWORK']):
        return 7

    # Phase 1: Hook
    if any(w in title for w in ['BREATH PHYSIOLOGY', 'BREATHING', 'BREATH AND',
                                  'RESPIRATORY SINUS', 'DIAPHRAGM']):
        if 'DEEP' not in title and 'COMPLETE' not in title:
            return 1
    if any(w in title for w in ['HEART RATE VARIABILITY', 'HRV BASICS', 'HRV AND',
                                  'PROPRIOCEPTION', 'INTEROCEPTION',
                                  'BODY AWARENESS', 'SOMATIC AWARENESS']):
        if 'DEEP' not in title and 'COMPLETE' not in title and 'ADVANCED' not in title:
            return 1
    if 'POLYVAGAL' in title and any(w in title for w in ['INTRO', 'BASIC', 'THEORY —', 'THEORY:']):
        return 1

    # Phase 2: Established Neuroscience
    if any(w in title for w in ['DEFAULT MODE', 'DMN', 'NEUROPLASTICITY', 'NEURAL PLASTICITY',
                                  'FLOW STATE', 'FLOW AND', 'PREDICTIVE PROCESSING',
                                  'PREDICTIVE CODING', 'BAYESIAN BRAIN',
                                  'MEMORY RECONSOLIDATION', 'MEMORY AND',
                                  'SLEEP AND', 'SLEEP STAGE', 'SLEEP SCIENCE', 'CIRCADIAN',
                                  'ATTENTION AND', 'EXECUTIVE FUNCTION',
                                  'SOMATIC MARKER', 'DAMASIO',
                                  'CONTEMPLATIVE NEURO', 'MEDITATION NEURO',
                                  'NEURAL OSCILLAT', 'BRAIN WAVE', 'BRAINWAVE',
                                  'GAMMA', 'THETA', 'ALPHA WAVE',
                                  'HEMISPHERIC', 'LATERALI',
                                  'MIRROR NEURON', 'MIRROR SYSTEM', 'EMBODIED COGNITION',
                                  'GROUNDED COGNITION', 'ENACTIVISM', 'ENACTIVE',
                                  'ANESTHESIA', 'CONSCIOUSNESS UNDER',
                                  'METASTAB', 'GRAVITY']):
        return 2

    # Phase 3: Equation/Core Theory
    if any(w in title for w in ['INFORMATION THEORY', 'ENTROPY', 'SHANNON',
                                  'NONLINEAR DYNAMIC', 'ATTRACTOR', 'CHAOS THEORY',
                                  'SELF-ORGANIZED CRITICALITY', 'CRITICALITY',
                                  'EDGE OF CHAOS',
                                  'INTEGRATED INFORMATION', 'IIT', 'TONONI',
                                  'GLOBAL WORKSPACE', 'GWT', 'BAARS',
                                  'FREE ENERGY PRINCIPLE', 'FRISTON',
                                  'COMPLEXITY', 'POWER LAW', '1/F',
                                  'SMALL WORLD', 'SMALL-WORLD',
                                  'KLEIBER', 'SCALING LAW', 'ALLOMETRIC',
                                  'LANGTON', 'LAMBDA', 'CRITICALITY CONVERGENCE',
                                  'COHERENCE THRESHOLD', 'PHASE TRANSITION',
                                  'BOSE-EINSTEIN', 'COHERENCE EQUATION']):
        return 3

    # Phase 5: Healing/Therapy
    if any(w in title for w in ['TRAUMA', 'PTSD', 'THERAPY', 'THERAPEUTIC',
                                  'IFS', 'INTERNAL FAMILY', 'EMDR',
                                  'MEDITATION', 'MINDFULNESS',
                                  'PSYCHEDELIC', 'PSILOCYBIN', 'MDMA', 'DMT',
                                  'AYAHUASCA', 'KETAMINE',
                                  'PLACEBO', 'NOCEBO',
                                  'COLD EXPOSURE', 'HORMESIS', 'WIM HOF',
                                  'GRIEF', 'BEREAVEMENT',
                                  'COMPASSION', 'LOVING-KINDNESS', 'METTA',
                                  'EXPRESSIVE WRITING', 'JOURNALING',
                                  'YOGA NEURO', 'YOGA AND',
                                  'BIOFEEDBACK', 'NEUROFEEDBACK',
                                  'VAGAL STIMULATION', 'VNS',
                                  'ALEXANDER TECHNIQUE', 'BODY USE']):
        return 5

    # Phase 6: Scale Invariance
    if any(w in title for w in ['FRACTAL', 'SCALE-FREE', 'SCALE FREE', 'SCALE INVARIAN',
                                  'EMERGENCE', 'EMERGENT',
                                  'CYMATICS', 'CYMATIC',
                                  'QUANTUM BIOLOGY', 'QUANTUM COHERENCE IN BIO',
                                  'AUTOPOIESIS', 'AUTOPOIETIC',
                                  'COLLECTIVE INTELLIGENCE', 'SWARM',
                                  'PLANT INTELLIGENCE', 'PLANT COGNIT', 'PLANT NEURO',
                                  'FUNGAL', 'MYCELIUM', 'MYCORRHIZ',
                                  'MORPHOGENESIS', 'TURING PATTERN',
                                  'SLIME MOLD', 'STIGMERGY',
                                  'BIRD FLOCK', 'MURMURATION',
                                  'SELF-ORGANIZ', 'SELF ORGANIZ',
                                  'NETWORK TOPOLOGY', 'GRAPH THEORY',
                                  'FIBONACCI', 'ENTRAINMENT',
                                  'SONOLUMINESCENCE']):
        return 6

    # Phase 4: Body Deep
    if any(w in title for w in ['VAGUS', 'VAGAL', 'POLYVAGAL',
                                  'PSYCHONEUROIMMUN', 'PNI', 'NEUROIMMUN',
                                  'GUT-BRAIN', 'GUT BRAIN', 'MICROBIOME', 'ENTERIC',
                                  'ENDOCANNABINOID', 'ECS',
                                  'FASCIA', 'TENSEGRITY', 'CONNECTIVE TISSUE',
                                  'BIOELECTRIC', 'LEVIN',
                                  'EPIGENETIC', 'GENE EXPRESS',
                                  'HEART-BRAIN', 'HEART BRAIN', 'CARDIAC COHERENCE',
                                  'PAIN SCIENCE', 'PAIN NEURO', 'NOCICEPTI',
                                  'INFLAMMATION', 'CYTOKINE',
                                  'CORTISOL', 'HPA AXIS', 'STRESS RESPONSE',
                                  'AUTONOMIC', 'SYMPATHETIC', 'PARASYMPATHETIC',
                                  'OXYTOCIN', 'SEROTONIN', 'DOPAMINE',
                                  'NITRIC OXIDE', 'PIEZOELECTRIC',
                                  'BODY ELECTRIC', 'BECKER', 'BODY AS ANTENNA',
                                  'BREATH DEEP', 'BREATH COMPLETE', 'RESPIRATORY DEEP',
                                  'PROPRIOCEPT DEEP', 'INTEROCEPTI DEEP',
                                  'HRV DEEP', 'HRV COMPLETE', 'HRV ADVANCED',
                                  'PHENOMENOLOGY', 'QUALIA',
                                  'ATTACHMENT THEORY', 'ATTACHMENT AND']):
        return 4

    # Scoring fallback
    body_score = sum(1 for w in ['VAGUS', 'BREATH', 'HEART', 'BODY', 'NERVE', 'POLYVAGAL',
                                   'FASCIA', 'GUT', 'MUSCLE', 'SPINE', 'ORGAN']
                     if w in title)
    neuro_score = sum(1 for w in ['NEURAL', 'BRAIN', 'CORTEX', 'NETWORK', 'OSCILLAT',
                                    'COGNITIVE', 'PERCEPT', 'CONSCIOUS']
                      if w in title)
    physics_score = sum(1 for w in ['QUANTUM', 'WAVE', 'FIELD', 'RESONAN', 'FREQUENCY',
                                      'HARMONIC', 'ACOUSTIC', 'VIBRAT', 'SOUND']
                        if w in title)
    ancient_score = sum(1 for w in ['ANCIENT', 'TEMPLE', 'SACRED', 'RITUAL', 'TRADITION',
                                      'INDIGENOUS', 'SHAMAN']
                        if w in title)
    heal_score = sum(1 for w in ['HEAL', 'THERAP', 'TRAUMA', 'RECOVERY', 'TRANSFORM']
                     if w in title)

    scores = {
        1: 0,
        2: neuro_score * 2,
        3: physics_score if 'THEORY' in title or 'PRINCIPLE' in title or 'LAW' in title else 0,
        4: body_score * 2,
        5: heal_score * 2,
        6: physics_score if 'PATTERN' in title or 'EVERY' in title or 'INVARIANT' in title else 0,
        7: ancient_score * 3,
        8: 0,
    }

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    if any(w in combined[:500] for w in ['BREATH', 'HEART RATE', 'POLYVAGAL', 'VAGUS']):
        return 4
    if any(w in combined[:500] for w in ['NEURON', 'BRAIN', 'CORTEX', 'NEURAL']):
        return 2
    if any(w in combined[:500] for w in ['QUANTUM', 'ENTROPY', 'INFORMATION', 'DYNAMICS']):
        return 3
    if any(w in combined[:500] for w in ['THERAPY', 'TRAUMA', 'HEALING', 'MEDITATION']):
        return 5
    if any(w in combined[:500] for w in ['ANCIENT', 'TEMPLE', 'SACRED', 'RITUAL']):
        return 7
    if any(w in combined[:500] for w in ['FRACTAL', 'SCALE', 'EMERGENCE', 'PLANT']):
        return 6

    return 6


PHASE_NAMES = {
    1: "THE HOOK — Body as Entry Point",
    2: "THE GROUNDING — Established Neuroscience",
    3: "THE EQUATION — Core Theory & Mathematics",
    4: "BODY DEEP DIVE — Physiology Mapped",
    5: "HEALING — Practical Applications",
    6: "SCALE INVARIANCE — The Pattern Everywhere",
    7: "ANCIENT KNOWLEDGE — The Long Memory",
    8: "THE FRONTIER — Honest Speculations",
    9: "SYNTHESIS — Braids & Architecture",
}


def content_length(entry):
    """Get content length for comparison."""
    return len(entry.get('content', '') or '')


def main():
    with open(HTML_PATH, 'r') as f:
        html = f.read()

    match = re.search(r'const DATA = (\[.*?\]);\s*\n', html, re.DOTALL)
    if not match:
        print("ERROR: Could not find const DATA array")
        sys.exit(1)

    data = json.loads(match.group(1))
    print(f"Loaded {len(data)} entries")

    # Step 1: Remove jm-duplicates (keep longest)
    removed_jm = 0
    jm_groups = {}
    for i, entry in enumerate(data):
        jm = entry.get('jm', '')
        if jm and jm in DUPLICATES_TO_REMOVE_BY_JM:
            jm_groups.setdefault(jm, []).append(i)

    indices_to_remove = set()
    for jm, indices in jm_groups.items():
        if len(indices) > 1:
            # Keep the longest, remove the rest
            longest_idx = max(indices, key=lambda i: content_length(data[i]))
            for idx in indices:
                if idx != longest_idx:
                    indices_to_remove.add(idx)
                    removed_jm += 1
                    print(f"  REMOVE duplicate [{idx}] jm={jm}: {data[idx].get('title', '')[:60]}")
            print(f"  KEEP [{longest_idx}] jm={jm}: {data[longest_idx].get('title', '')[:60]}")

    # Step 2: Fix overclaiming titles
    title_fixes = 0
    for entry in data:
        title = entry.get('title', '')
        if title in TITLE_FIXES:
            entry['title'] = TITLE_FIXES[title]
            title_fixes += 1
        if title in BRAID_RENAME:
            entry['title'] = BRAID_RENAME[title]
            title_fixes += 1

    # Step 3: Remove marked entries
    cleaned_data = [entry for i, entry in enumerate(data) if i not in indices_to_remove]

    print(f"\nRemoved {removed_jm} jm-duplicates")
    print(f"Fixed {title_fixes} overclaiming titles")
    print(f"Remaining: {len(cleaned_data)} entries")

    # Step 4: Re-classify with fixed Phase 8 logic
    phase_buckets = {i: [] for i in range(1, 10)}
    for entry in cleaned_data:
        phase = classify_entry_fixed(entry)
        phase_buckets[phase].append(entry)

    print("\nPhase distribution (fixed):")
    for p in range(1, 10):
        print(f"  Phase {p}: {len(phase_buckets[p]):3d}  — {PHASE_NAMES[p]}")

    # Step 5: Sort within phases
    reordered = []
    for p in range(1, 10):
        bucket = phase_buckets[p]
        if p == 9:
            bucket.sort(key=lambda e: e.get('id', 0))
        elif p == 7:
            bucket.sort(key=lambda e: e.get('id', 0))
        else:
            bucket.sort(key=lambda e: (-e.get('zl', 0), -e.get('id', 0)))
        reordered.extend(bucket)

    print(f"\nFinal count: {len(reordered)} entries")

    # Build and replace
    new_json = json.dumps(reordered, ensure_ascii=False)
    new_html = html[:match.start(1)] + new_json + html[match.end(1):]

    with open(HTML_PATH, 'w') as f:
        f.write(new_html)

    print(f"Wrote cleaned archive to {HTML_PATH}")

    # Verification
    print("\n" + "=" * 80)
    print("Phase 8 entries (should be ONLY frontier/speculative):")
    print("=" * 80)
    for entry in phase_buckets[8]:
        print(f"  #{entry.get('id','')} {entry.get('title','')[:70]}")

    print(f"\nTotal Phase 8: {len(phase_buckets[8])}")


if __name__ == '__main__':
    main()
