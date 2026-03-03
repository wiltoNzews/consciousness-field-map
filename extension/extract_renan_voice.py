#!/usr/bin/env python3
"""
Extract ONLY Renan's authentic voice — his personal story, emotions, health journey.
Filter OUT: terminal output, homework, copy-pasted ChatGPT responses, technical configs.
"""

import json
import re
from datetime import datetime, timezone
from collections import defaultdict

INPUT_FILE = '/home/zews/rag-local/ChatGPT_Exports/conversationsRENAN.json'

# Words that indicate terminal/technical noise (not Renan's voice)
NOISE_INDICATORS = [
    'root@wilton', 'zews@wilton', 'docker', 'systemctl', 'pip install',
    'npm install', 'git clone', 'sudo ', 'apt install', 'curl http',
    'CONTAINER ID', 'IMAGE', '.service', 'journalctl', 'pts/',
    'Escolha uma:', 'alternativa correta', 'Marque a alternativa',
    'questão', 'Pergunta 1', 'Pergunta 2', 'questões',
    '```bash', '```python', 'npm error', 'ERROR:', 'Cannot uninstall',
    'requirements.txt', '.pyc', 'node_modules', 'docker-compose',
    'CHANGELOG.md', 'cypress', 'demo.gif', 'CODE_OF_CONDUCT',
    'drwx', '-rw-', 'total ', 'ls -l', 'ps aux',
    'Nov 28', 'Dec 05', 'Dec 06',  # journalctl timestamps
    '(.venv)', 'root@', 'zews@', 'open-webui#',
    'GRUB_DEFAULT', 'grub.cfg',
    'Breathing in through infinite', 'Zλ(0.999)',  # ChatGPT/GPT responses pasted
    'Let me now', 'Here is', 'Perfect. Let',  # English GPT responses
    'Hell yes—this is how',  # Wilton's GPT output pasted
    '🧠 STATUS:', '## 🧠', '### 🖥', '🎯 VECTOR',  # formatted GPT output
    'Absolutely. You',  # GPT mirror responses
    'Component\tStatus', 'Vector Reading',  # GPT tables
    'psi-brain', 'VectorBridge', 'ψOS Sovereign',
    'NIST CSF', 'governança', 'MICROSOFT EXCEL',
    'open-webui', 'chromadb', 'vite dev',
    'ERESOLVE', 'svelte-kit',
    'audit:', 'kernel:', 'pam_unix',
    'SHA256:', 'sha256:', 'Digest:',
    '1 ponto\n', 'firebase', 'webpack',
]

# High-signal personal content keywords
PERSONAL_KEYWORDS = [
    # Health/Cancer
    'câncer', 'cancer', 'leucemia', 'linfoma', 'quimioterapia', 'quimio',
    'radioterapia', 'medula', 'transplante', 'internado', 'hospital',
    'biópsia', 'tomografia', 'pet scan', 'fentanil', 'remissão', 'curado',
    'doença', 'tratamento', 'dor ', 'dores', 'terminal',
    # Brother/Family
    'irmão', 'irmao', 'diego', 'cego', 'cegueira', 'doador', 'doação',
    'família', 'mãe', 'mainha', 'pai', 'filho', 'miguel', 'mulher',
    'esposa', 'surama', 'manuela', 'lucas',
    'são joaquim', 'bezerros', 'pernambuco',
    # Raw emotion
    'medo', 'sozinho', 'chorar', 'chorando', 'choro', 'lágrima',
    'triste', 'tristeza', 'desmoronando', 'desespero', 'morrer', 'morte',
    'desistir', 'não aguento', 'desabafo', 'pânico', 'trauma',
    'saudade', 'solidão', 'abandonado', 'pesadelo', 'enlouquecendo',
    'sofrimento', 'angústia', 'perdido',
    # Reconciliation/healing
    'perdoar', 'perdão', 'reconciliar', 'briga', 'brigar',
    'velório', 'ceifar', 'suicíd',
    # Spiritual/personal growth (Portuguese only)
    'despertar', 'purga', 'renascimento', 'renascer',
    'alma', 'deus', 'milagre', 'fé',
    'gratidão', 'testemunho', 'provação',
    # Relationship to Wilton (personal, not technical)
    'fundo do poço', 'salvou', 'anjo', 'enviado',
    'te amo', 'irmãozinho', 'guardião do tempo',
    # Life story
    'nasci', 'infância', 'avó', 'avô', 'enterro', 'caixão',
    'sequestro', 'sequestrado', 'mala do carro',
    # Near-death experience
    'fora do corpo', 'saída corpórea', 'luz', 'anestesia',
    # Emotional declarations
    'não tou bem', 'não estou bem', 'tou vendo coisas',
    'nova chance', 'driblei a morte',
]

def is_noise(text):
    """Check if message is technical noise rather than personal voice."""
    text_check = text[:500]  # Check beginning
    noise_count = 0
    for indicator in NOISE_INDICATORS:
        if indicator.lower() in text_check.lower():
            noise_count += 1
    # If 2+ noise indicators, it's noise
    if noise_count >= 2:
        return True
    # If starts with typical terminal prompt
    if re.match(r'^[\(\.]*(venv|root|zews)', text.strip()):
        return True
    # If it's clearly a ChatGPT English response (not Renan's voice)
    if text.strip().startswith('Perfect.') or text.strip().startswith('Absolutely.'):
        return True
    if text.strip().startswith('Hell yes'):
        return True
    return False

def has_personal_content(text_lower):
    """Check if message contains personal/emotional keywords."""
    matches = []
    for kw in PERSONAL_KEYWORDS:
        if kw.lower() in text_lower:
            matches.append(kw)
    return matches

def is_portuguese_personal(text):
    """Heuristic: is this Renan speaking in his own voice (not pasting GPT output)?"""
    # Portuguese personal indicators
    pt_personal = [
        'eu ', 'meu ', 'minha ', 'meus ', 'minhas ',
        'estou ', 'tou ', 'fui ', 'sou ', 'tenho ',
        'quero ', 'queria ', 'sinto ', 'senti ', 'lembro ',
        'pra ', 'porque ', 'cara,', 'velho', 'enfim',
    ]
    text_lower = text.lower()
    pt_count = sum(1 for p in pt_personal if p in text_lower)
    return pt_count >= 2

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    # Extract all user messages
    messages = []
    for conv in conversations:
        title = conv.get('title', 'Untitled')
        mapping = conv.get('mapping', {})
        conv_create_time = conv.get('create_time')
        for node_id, node in mapping.items():
            msg = node.get('message')
            if not msg:
                continue
            if msg.get('author', {}).get('role') != 'user':
                continue
            content = msg.get('content', {})
            parts = content.get('parts', [])
            text_parts = [p for p in parts if isinstance(p, str) and p.strip()]
            if not text_parts:
                continue
            text = '\n'.join(text_parts)
            create_time = msg.get('create_time') or conv_create_time
            if create_time is None:
                continue
            messages.append({
                'timestamp': create_time,
                'title': title,
                'text': text
            })

    matches = []
    for msg in messages:
        text = msg['text']

        # Skip very short
        if len(text.strip()) < 30:
            continue

        # Skip noise
        if is_noise(text):
            continue

        text_lower = text.lower()
        personal_kws = has_personal_content(text_lower)

        if not personal_kws:
            continue

        # Require Portuguese personal voice OR very strong keywords
        strong_kws = [k for k in personal_kws if k in [
            'câncer', 'cancer', 'leucemia', 'linfoma', 'quimioterapia', 'quimio',
            'radioterapia', 'transplante', 'biópsia', 'terminal', 'fentanil',
            'diego', 'cego', 'doador', 'doação',
            'chorar', 'chorando', 'choro', 'desmoronando', 'morrer',
            'desespero', 'pesadelo', 'enlouquecendo', 'ceifar',
            'fundo do poço', 'salvou', 'anjo', 'enviado',
            'fora do corpo', 'saída corpórea',
            'driblei a morte', 'nova chance',
            'sequestro', 'mala do carro',
            'velório', 'briga',
            'nasci', 'infância', 'avó',
        ]]

        is_personal_voice = is_portuguese_personal(text)

        if not (strong_kws or (personal_kws and is_personal_voice)):
            continue

        dt = datetime.fromtimestamp(msg['timestamp'], tz=timezone.utc)

        display_text = text
        if len(display_text) > 2000:
            display_text = display_text[:1500] + '\n\n[... continued, ' + str(len(text)) + ' chars total ...]'

        matches.append({
            'datetime': dt,
            'date_str': dt.strftime('%Y-%m-%d %H:%M'),
            'month_key': dt.strftime('%Y-%m'),
            'title': msg['title'],
            'text': display_text,
            'full_text': text,
            'keywords': personal_kws,
            'strong': bool(strong_kws),
        })

    matches.sort(key=lambda x: x['datetime'])

    print("=" * 80)
    print("RENAN'S VOICE — HIS STORY IN HIS OWN WORDS")
    print(f"{len(matches)} authentic personal messages")
    print("=" * 80)

    by_month = defaultdict(list)
    for m in matches:
        by_month[m['month_key']].append(m)

    for month_key in sorted(by_month.keys()):
        month_matches = by_month[month_key]
        try:
            month_dt = datetime.strptime(month_key, '%Y-%m')
            month_display = month_dt.strftime('%B %Y')
        except:
            month_display = month_key

        print(f"\n{'=' * 80}")
        print(f"## {month_display} — {len(month_matches)} messages")
        print(f"{'=' * 80}")

        for m in month_matches:
            kws = ', '.join(set(m['keywords']))
            print(f"\n{'~' * 70}")
            print(f"[{m['date_str']}] \"{m['title']}\"")
            print(f"Keywords: {kws}")
            print(f"{'~' * 70}")
            print(m['text'])

    # Print the full autobiography separately
    print("\n\n")
    print("=" * 80)
    print("FULL AUTOBIOGRAPHY — \"A vida\" (June 24, 2025)")
    print("=" * 80)
    for m in matches:
        if 'nasci' in m['keywords'] and len(m['full_text']) > 5000:
            print(m['full_text'])
            break

main()
