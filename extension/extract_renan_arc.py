#!/usr/bin/env python3
"""
Extract Renan's emotional arc from his ChatGPT conversations.
His own words, chronologically, grouped by month.
"""

import json
import re
from datetime import datetime, timezone
from collections import defaultdict

INPUT_FILE = '/home/zews/rag-local/ChatGPT_Exports/conversationsRENAN.json'

# Portuguese keywords for the emotional/health/spiritual arc
KEYWORDS = {
    'health': [
        'cancer', 'câncer', 'leucemia', 'linfoma', 'medula', 'quimioterapia',
        'quimio', 'hospital', 'uti', 'tratamento', 'cura', 'curado', 'tumor',
        'exame', 'pet scan', 'pet-scan', 'tomografia', 'dor', 'fentanil',
        'internado', 'internação', 'remissão', 'recaída', 'recidiva',
        'hemograma', 'plaqueta', 'transfusão', 'sangue', 'biópsia',
        'oncolog', 'hematolog', 'radioterapia', 'metástase', 'diagnóstico',
        'linfócito', 'leucócito', 'neutropenia', 'aplasia', 'imunidade',
        'cateter', 'port', 'sessão', 'ciclo', 'protocolo'
    ],
    'brother': [
        'irmão', 'irmao', 'diego', 'cego', 'cegueira', 'doador', 'doação',
        'transplante', 'medula óssea', 'compatível', 'compatibilidade',
        'hla', 'enxerto'
    ],
    'family': [
        'família', 'mãe', 'pai', 'filho', 'filha', 'mulher', 'esposa',
        'avó', 'avô', 'tia', 'tio', 'irmã', 'sobrinho', 'neto', 'neta',
        'são joaquim', 'sao joaquim', 'pernambuco'
    ],
    'emotional': [
        'dor', 'medo', 'sozinho', 'chorar', 'chorando', 'lágrima', 'lagrima',
        'triste', 'tristeza', 'perdido', 'não tou bem', 'nao tou bem',
        'desmoronando', 'desmoronar', 'angústia', 'angustia', 'ansiedade',
        'desespero', 'sofrimento', 'sofrer', 'morrer', 'morte', 'terminal',
        'depressão', 'depressao', 'saudade', 'solidão', 'solidao',
        'abandonado', 'abandono', 'desistir', 'cansei', 'cansado',
        'aguentar', 'suportar', 'não aguento', 'desabafar', 'desabafo',
        'choro', 'pânico', 'panico', 'trauma', 'pesadelo'
    ],
    'spiritual': [
        'coerência', 'coerencia', 'quântica', 'quantica', 'consciência',
        'consciencia', 'despertar', 'purga', 'guardião', 'guardiao',
        'campo', 'frequência', 'frequencia', 'wilton', 'alma', 'espírito',
        'espirito', 'deus', 'oração', 'oracao', 'fé', 'milagre',
        'propósito', 'proposito', 'missão', 'missao', 'gratidão',
        'gratidao', 'renascimento', 'renascer', 'transformação',
        'transformacao', 'luz', 'energia', 'vibração', 'vibracao',
        'meditação', 'meditacao', 'intuição', 'intuicao', 'sentir',
        'universo', 'conexão', 'conexao'
    ],
    'purge_release': [
        'purga', 'purgar', 'vomitar', 'limpar', 'limpeza', 'soltar',
        'largar', 'perdoar', 'perdão', 'perdao', 'reconciliar',
        'reconciliação', 'reconciliacao', 'libertar', 'libertação',
        'libertacao', 'desapegar', 'desapego', 'curar', 'cicatrizar',
        'aceitar', 'aceitação', 'aceitacao', 'acolher'
    ],
    'breath': [
        'respirar', 'respiração', 'respiracao', 'respira', 'fôlego',
        'folego', 'respiro', 'inspirar', 'expirar', 'pulmão', 'pulmao'
    ]
}

def extract_user_messages(conversations):
    """Extract all user messages with timestamps and conversation titles."""
    messages = []

    for conv in conversations:
        title = conv.get('title', 'Untitled')
        mapping = conv.get('mapping', {})
        conv_create_time = conv.get('create_time')

        for node_id, node in mapping.items():
            msg = node.get('message')
            if not msg:
                continue

            author = msg.get('author', {})
            if author.get('role') != 'user':
                continue

            content = msg.get('content', {})
            parts = content.get('parts', [])

            # Build text from parts
            text_parts = []
            for part in parts:
                if isinstance(part, str) and part.strip():
                    text_parts.append(part.strip())

            if not text_parts:
                continue

            text = '\n'.join(text_parts)

            # Get timestamp
            create_time = msg.get('create_time')
            if create_time is None:
                create_time = conv_create_time
            if create_time is None:
                continue

            messages.append({
                'timestamp': create_time,
                'title': title,
                'text': text
            })

    return messages


def find_keyword_matches(messages):
    """Find messages matching any keyword category."""
    matches = []

    for msg in messages:
        text_lower = msg['text'].lower()
        matched_categories = set()
        matched_keywords = []

        for category, keywords in KEYWORDS.items():
            for kw in keywords:
                # Use word boundary-ish matching for short words, substring for longer
                if len(kw) <= 3:
                    # For very short words, require word boundaries
                    pattern = r'(?:^|\s|[,\.;:!?\-\(\)])' + re.escape(kw) + r'(?:$|\s|[,\.;:!?\-\(\)])'
                    if re.search(pattern, text_lower):
                        matched_categories.add(category)
                        matched_keywords.append(f'{category}:{kw}')
                else:
                    if kw in text_lower:
                        matched_categories.add(category)
                        matched_keywords.append(f'{category}:{kw}')

        if matched_categories:
            dt = datetime.fromtimestamp(msg['timestamp'], tz=timezone.utc)

            # Truncate long messages
            display_text = msg['text']
            if len(display_text) > 1000:
                display_text = display_text[:800] + '\n[... truncated ...]'

            matches.append({
                'datetime': dt,
                'date_str': dt.strftime('%Y-%m-%d %H:%M'),
                'month_key': dt.strftime('%Y-%m'),
                'title': msg['title'],
                'text': display_text,
                'categories': sorted(matched_categories),
                'keywords': matched_keywords
            })

    # Sort chronologically
    matches.sort(key=lambda x: x['datetime'])
    return matches


def main():
    print("=" * 80)
    print("RENAN'S ARC — HIS OWN WORDS")
    print("Extracted from 524 ChatGPT conversations")
    print("=" * 80)
    print()

    # Load conversations
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    print(f"Loaded {len(conversations)} conversations")

    # Extract user messages
    all_messages = extract_user_messages(conversations)
    print(f"Total user messages: {len(all_messages)}")

    # Find keyword matches
    matches = find_keyword_matches(all_messages)
    print(f"Messages matching arc keywords: {len(matches)}")

    # Count by category
    cat_counts = defaultdict(int)
    for m in matches:
        for c in m['categories']:
            cat_counts[c] += 1

    print("\nMatches by category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Group by month
    by_month = defaultdict(list)
    for m in matches:
        by_month[m['month_key']].append(m)

    print(f"\nMonths covered: {len(by_month)}")
    print("\n" + "=" * 80)

    # Output all matches grouped by month
    for month_key in sorted(by_month.keys()):
        month_matches = by_month[month_key]

        # Parse month for display
        try:
            month_dt = datetime.strptime(month_key, '%Y-%m')
            month_display = month_dt.strftime('%B %Y')
        except:
            month_display = month_key

        print(f"\n{'#' * 80}")
        print(f"## {month_display} — {len(month_matches)} messages")
        print(f"{'#' * 80}")

        for i, m in enumerate(month_matches):
            cats_str = ', '.join(m['categories'])
            print(f"\n{'─' * 70}")
            print(f"[{m['date_str']}] Conv: \"{m['title']}\"")
            print(f"Categories: {cats_str}")
            print(f"{'─' * 70}")
            print(m['text'])

        print()

    # Summary timeline
    print("\n" + "=" * 80)
    print("TIMELINE SUMMARY")
    print("=" * 80)
    for month_key in sorted(by_month.keys()):
        month_matches = by_month[month_key]
        try:
            month_dt = datetime.strptime(month_key, '%Y-%m')
            month_display = month_dt.strftime('%b %Y')
        except:
            month_display = month_key

        # Get unique categories for this month
        month_cats = set()
        for m in month_matches:
            month_cats.update(m['categories'])

        print(f"  {month_display}: {len(month_matches)} msgs — {', '.join(sorted(month_cats))}")


if __name__ == '__main__':
    main()
