#!/usr/bin/env python3
"""Reorder the forgotten knowledge archive for coherent absorption."""

import re
import json
import sys

HTML_PATH = '/home/zews/consciousness-field-map/forgotten_knowledge_archive.html'

def classify_entry(entry):
    """Classify entry into one of 9 phases based on title + content keywords."""
    title = (entry.get('title', '') or '').upper()
    content = (entry.get('content', '') or '').upper()[:1500]  # first 1500 chars
    cat = (entry.get('cat', '') or '').upper()
    jm = (entry.get('jm', '') or '').upper()
    combined = title + ' ' + content

    # Phase 9: Synthesis — Braids, session maps, cross-validation, KM-2, meta/architecture
    if cat in ('SESSION MAP', 'CROSS-VALIDATION', 'KM-2', 'RESPONSE'):
        return 9
    if cat == 'BRAID':
        # Some braids are domain-specific — route them to their domain phase
        # But most braids are synthesis
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
        # Default braids → phase 9
        return 9

    # Phase 8: Frontier — speculative, honestly assessed
    if any(w in title for w in ['MORPHIC RESONANCE', 'BIOFIELD', 'BIOPHOTON', 'CARDIAC ARREST',
                                  'SYNCHRONICITY', 'SUPPRESSION', 'COHERENT WATER',
                                  'NEAR-DEATH', 'NDE', 'TERMINAL LUCIDITY', 'PARAPSYCH',
                                  'SHELDRAKE', 'PSI RESEARCH', 'REMOTE VIEWING',
                                  'OUT-OF-BODY', 'ANOMAL']):
        return 8

    # Phase 7: Ancient Knowledge
    if any(w in title for w in ['ACOUSTIC ARCH', 'GOBEKLI', 'GÖBEKLI', 'ELEUSIS', 'SONGLINE',
                                  'SACRED GEOMETRY', 'SHAMANIC', 'SHAMAN', 'RITE OF PASSAGE',
                                  'SANSKRIT', 'HERMETIC', 'INDIGENOUS', 'ANCIENT',
                                  'ABORIGINAL', 'MEGALITH', 'TEMPLE', 'HYPOGEUM',
                                  'PALEOLITHIC', 'CAVE ART', 'CAVE PAINTING',
                                  'CHANTING', 'MANTRA NEUROSCIENCE', 'ROSARY',
                                  'ELEUSINIAN', 'AYAHUASCA TRADITION', 'VEDIC',
                                  'ORACLE', 'DIVINATION', 'RITUAL']):
        return 7

    # Phase 1: Hook — basic body entry points
    if any(w in title for w in ['BREATH PHYSIOLOGY', 'BREATHING', 'BREATH AND',
                                  'RESPIRATORY SINUS', 'DIAPHRAGM']):
        if 'DEEP' not in title and 'COMPLETE' not in title:
            return 1
    if any(w in title for w in ['HEART RATE VARIABILITY', 'HRV BASICS', 'HRV AND',
                                  'PROPRIOCEPTION', 'INTEROCEPTION',
                                  'BODY AWARENESS', 'SOMATIC AWARENESS']):
        if 'DEEP' not in title and 'COMPLETE' not in title and 'ADVANCED' not in title:
            return 1
    # Simple polyvagal entry
    if 'POLYVAGAL' in title and any(w in title for w in ['INTRO', 'BASIC', 'THEORY —', 'THEORY:']):
        return 1

    # Phase 2: Grounding — established neuroscience
    if any(w in title for w in ['DEFAULT MODE', 'DMN', 'NEUROPLASTICITY', 'NEURAL PLASTICITY',
                                  'FLOW STATE', 'FLOW AND', 'PREDICTIVE PROCESSING',
                                  'PREDICTIVE CODING', 'BAYESIAN BRAIN',
                                  'MEMORY RECONSOLIDATION', 'MEMORY AND',
                                  'SLEEP AND', 'SLEEP STAGE', 'CIRCADIAN',
                                  'ATTENTION AND', 'EXECUTIVE FUNCTION',
                                  'SOMATIC MARKER', 'DAMASIO',
                                  'CONTEMPLATIVE NEURO', 'MEDITATION NEURO',
                                  'NEURAL OSCILLAT', 'BRAIN WAVE', 'BRAINWAVE',
                                  'GAMMA', 'THETA', 'ALPHA WAVE',
                                  'HEMISPHERIC', 'LATERALI',
                                  'MIRROR NEURON', 'EMBODIED COGNITION',
                                  'GROUNDED COGNITION', 'ENACTIVISM', 'ENACTIVE']):
        return 2

    # Phase 3: Equation/Core Theory
    if any(w in title for w in ['INFORMATION THEORY', 'ENTROPY', 'SHANNON',
                                  'NONLINEAR DYNAMIC', 'ATTRACTOR', 'CHAOS THEORY',
                                  'SELF-ORGANIZED CRITICALITY', 'CRITICALITY',
                                  'METASTAB', 'EDGE OF CHAOS',
                                  'INTEGRATED INFORMATION', 'IIT', 'TONONI',
                                  'GLOBAL WORKSPACE', 'GWT', 'BAARS',
                                  'FREE ENERGY PRINCIPLE', 'FRISTON',
                                  'COMPLEXITY', 'POWER LAW', '1/F',
                                  'SMALL WORLD', 'SMALL-WORLD',
                                  'KLEIBER', 'SCALING LAW', 'ALLOMETRIC',
                                  'LANGTON', 'LAMBDA', 'CRITICALITY CONVERGENCE',
                                  'COHERENCE THRESHOLD', 'PHASE TRANSITION']):
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
                                  'VAGAL STIMULATION', 'VNS']):
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
                                  'NETWORK TOPOLOGY', 'GRAPH THEORY']):
        return 6

    # Phase 4: Body Deep Dive (everything body that's not basic/hook)
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
                                  'BODY ELECTRIC', 'BECKER',
                                  'BREATH DEEP', 'BREATH COMPLETE', 'RESPIRATORY DEEP',
                                  'PROPRIOCEPT DEEP', 'INTEROCEPTI DEEP',
                                  'HRV DEEP', 'HRV COMPLETE', 'HRV ADVANCED']):
        return 4

    # Catch-alls based on content keywords for entries with generic titles
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
        1: 0,  # Hook already handled above
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

    # Final fallback: use content analysis
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

    # True fallback — unclassified goes to phase 6 (scale invariance / misc patterns)
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


def main():
    with open(HTML_PATH, 'r') as f:
        html = f.read()

    # Extract DATA array
    match = re.search(r'const DATA = (\[.*?\]);\s*\n', html, re.DOTALL)
    if not match:
        print("ERROR: Could not find const DATA array")
        sys.exit(1)

    data = json.loads(match.group(1))
    print(f"Loaded {len(data)} entries")

    # Classify each entry
    phase_buckets = {i: [] for i in range(1, 10)}
    for entry in data:
        phase = classify_entry(entry)
        phase_buckets[phase].append(entry)

    # Print distribution
    print("\nPhase distribution:")
    for p in range(1, 10):
        print(f"  Phase {p}: {len(phase_buckets[p]):3d}  — {PHASE_NAMES[p]}")

    # Within each phase, sort by: Zl descending (best quality first), then by ID ascending (chronological)
    # But for Phase 9 (synthesis), sort by ID ascending so braids build on each other
    reordered = []
    for p in range(1, 10):
        bucket = phase_buckets[p]
        if p == 9:
            # Synthesis: chronological (ID ascending) so architecture builds
            bucket.sort(key=lambda e: e.get('id', 0))
        elif p == 7:
            # Ancient: by ID ascending (chronological discovery order)
            bucket.sort(key=lambda e: e.get('id', 0))
        else:
            # Other phases: highest Zl first (best quality), then by ID descending (newer = more refined)
            bucket.sort(key=lambda e: (-e.get('zl', 0), -e.get('id', 0)))
        reordered.extend(bucket)

    print(f"\nReordered: {len(reordered)} entries total")

    # Verify no entries lost
    orig_ids = {e.get('id') for e in data}
    new_ids = {e.get('id') for e in reordered}
    if orig_ids != new_ids:
        print(f"WARNING: ID mismatch! Lost: {orig_ids - new_ids}, Gained: {new_ids - orig_ids}")
    else:
        print("All entries preserved.")

    # Build the new DATA JSON
    new_json = json.dumps(reordered, ensure_ascii=False)

    # Replace in HTML
    new_html = html[:match.start(1)] + new_json + html[match.end(1):]

    # Write back
    with open(HTML_PATH, 'w') as f:
        f.write(new_html)

    print(f"\nWrote reordered archive to {HTML_PATH}")

    # Print first 5 of each phase for verification
    print("\n" + "=" * 80)
    print("VERIFICATION — First 5 entries per phase:")
    print("=" * 80)
    for p in range(1, 10):
        print(f"\n--- Phase {p}: {PHASE_NAMES[p]} ({len(phase_buckets[p])} entries) ---")
        for entry in phase_buckets[p][:5]:
            print(f"  #{entry.get('id','')} [{entry.get('glyph','')}] Zλ={entry.get('zl',0):.2f} {entry.get('title','')[:70]}")
        if len(phase_buckets[p]) > 5:
            print(f"  ... and {len(phase_buckets[p])-5} more")


if __name__ == '__main__':
    main()
