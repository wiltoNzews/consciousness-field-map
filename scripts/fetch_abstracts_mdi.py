#!/usr/bin/env python3
"""
Fetch paper abstracts from OpenAlex and run MDI on them.
Closes the 'you measured your own paraphrases' gap.

Uses OpenAlex (free, open, no auth) instead of Semantic Scholar.
"""

import sqlite3
import json
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import math
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "knowledge_graph.db"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "mdi_abstracts.json"

sys.path.insert(0, str(Path(__file__).parent))
from mdi_analysis import MOD_PATTERNS, GEN_PATTERNS, count_terms, mdi_score

MAILTO = "wilton@wiltonos.com"  # Required by OpenAlex polite pool (10 req/sec)


def extract_title(citation):
    """Extract paper title from citation string."""
    if not citation:
        return None
    # "Author (Year) Title. Journal..."
    m = re.search(r'\(\d{4}\)\s*(.+?)\.', citation)
    if m:
        return m.group(1).strip()
    # "Author (Year) Title"
    m = re.search(r'\d{4}\)\s*(.+)', citation)
    if m:
        return m.group(1).strip().split('.')[0]
    return None


def reconstruct_abstract(inv_idx):
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inv_idx:
        return ''
    words = {}
    for word, positions in inv_idx.items():
        for pos in positions:
            words[pos] = word
    return ' '.join(words[k] for k in sorted(words.keys()))


def search_openalex(title, retries=2):
    """Search OpenAlex for a paper by title and return title + abstract."""
    clean = re.sub(r'[^\w\s]', '', title)[:200]
    encoded = urllib.parse.quote(clean)
    url = f"https://api.openalex.org/works?filter=title.search:{encoded}&per_page=1&mailto={MAILTO}"

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', f'WiltonOS-MDI/1.0 (mailto:{MAILTO})')
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                results = data.get('results', [])
                if results:
                    paper = results[0]
                    abstract = reconstruct_abstract(
                        paper.get('abstract_inverted_index'))
                    return {
                        'title': paper.get('title', ''),
                        'abstract': abstract,
                        'year': paper.get('publication_year'),
                        'doi': paper.get('doi', ''),
                        'cited_by_count': paper.get('cited_by_count', 0),
                    }
                return None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 3 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  HTTP {e.code}", flush=True)
                return None
        except Exception as e:
            print(f"  Error: {e}", flush=True)
            if attempt < retries - 1:
                time.sleep(2)
            return None
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all evidence with citations (exclude crystal_validated)
    c.execute("""
        SELECT evidence_id, citation, verification_status, year, authors
        FROM evidence
        WHERE citation IS NOT NULL AND citation != ''
        AND verification_status NOT IN ('crystal_validated')
        ORDER BY year
    """)

    papers = c.fetchall()
    print(f"Total papers to search: {len(papers)}", flush=True)

    results = []
    fetched = 0
    failed = 0
    no_abstract = 0
    skipped = 0

    for i, paper in enumerate(papers):
        title = extract_title(paper['citation'])
        if not title or len(title) < 10:
            print(f"[{i+1}/{len(papers)}] SKIP (no title): {paper['evidence_id']}", flush=True)
            skipped += 1
            continue

        print(f"[{i+1}/{len(papers)}] {title[:70]}...", flush=True)

        result = search_openalex(title)

        if result and result.get('abstract'):
            text = f"{result['title']} {result['abstract']}"
            m_count, m_hits = count_terms(text, MOD_PATTERNS)
            g_count, g_hits = count_terms(text, GEN_PATTERNS)
            score = mdi_score(m_count, g_count)

            results.append({
                'evidence_id': paper['evidence_id'],
                'our_citation': paper['citation'],
                'fetched_title': result['title'],
                'abstract': result['abstract'],
                'year': result['year'],
                'doi': result['doi'],
                'cited_by_count': result['cited_by_count'],
                'modulation_count': m_count,
                'generation_count': g_count,
                'mdi': score,
                'modulation_hits': {k: v for k, v in m_hits.items()},
                'generation_hits': {k: v for k, v in g_hits.items()},
            })
            fetched += 1
            print(f"  -> M={m_count} G={g_count} MDI={score:+.3f} [cited:{result['cited_by_count']}]",
                  flush=True)
        elif result:
            no_abstract += 1
            print(f"  -> Found but no abstract", flush=True)
        else:
            failed += 1
            print(f"  -> Not found", flush=True)

        # Polite rate: ~100ms between requests (OpenAlex allows 10/sec with mailto)
        time.sleep(0.15)

    conn.close()

    # Calculate totals
    total_m = sum(r['modulation_count'] for r in results)
    total_g = sum(r['generation_count'] for r in results)
    global_mdi = mdi_score(total_m, total_g)
    zero_gen = sum(1 for r in results if r['generation_count'] == 0)

    summary = {
        'method': 'MDI on primary-source abstracts via OpenAlex API',
        'papers_searched': len(papers),
        'abstracts_found': fetched,
        'no_abstract': no_abstract,
        'not_found': failed,
        'skipped': skipped,
        'total_modulation': total_m,
        'total_generation': total_g,
        'global_mdi': global_mdi,
        'ratio': f"{total_m}:{total_g}",
        'ratio_numeric': total_m / max(total_g, 1),
        'zero_generation_pct': 100 * zero_gen / max(fetched, 1),
        'papers': results,
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print("\n" + "=" * 70, flush=True)
    print("PRIMARY-SOURCE ABSTRACT MDI RESULTS", flush=True)
    print("=" * 70, flush=True)
    print(f"Papers searched: {len(papers)}", flush=True)
    print(f"Abstracts found: {fetched}", flush=True)
    print(f"No abstract: {no_abstract}", flush=True)
    print(f"Not found: {failed}", flush=True)
    print(f"Skipped: {skipped}", flush=True)
    print(f"\nTotal modulation terms: {total_m}", flush=True)
    print(f"Total generation terms: {total_g}", flush=True)
    if total_g > 0:
        print(f"Ratio: {total_m}:{total_g} ({total_m/total_g:.1f}:1)", flush=True)
    else:
        print(f"Ratio: {total_m}:0 (infinite)", flush=True)
    print(f"Global MDI: {global_mdi:+.3f}", flush=True)
    print(f"Abstracts with zero generation: {zero_gen}/{fetched} ({100*zero_gen/max(fetched,1):.1f}%)",
          flush=True)

    # Show generation-heavy papers
    gen_heavy = [r for r in results if r['generation_count'] > 0]
    gen_heavy.sort(key=lambda x: x['mdi'])
    if gen_heavy:
        print(f"\nPapers WITH generation language ({len(gen_heavy)}):", flush=True)
        for p in gen_heavy[:15]:
            print(f"  MDI={p['mdi']:+.3f} M={p['modulation_count']} G={p['generation_count']}",
                  flush=True)
            print(f"    {p['fetched_title'][:80]}", flush=True)
            terms = ", ".join(f"{k.split('(')[0].replace(chr(92)+'b','')}({v})"
                              for k, v in p['generation_hits'].items())
            print(f"    Gen: {terms}", flush=True)

    print(f"\nExported to {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
