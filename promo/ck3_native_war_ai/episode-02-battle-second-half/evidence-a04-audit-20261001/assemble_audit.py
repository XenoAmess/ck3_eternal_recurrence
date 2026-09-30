"""Assemble the three evidence reviews against the actual immutable a04 timeline.

This records coverage and declared boundaries. It does not approve media,
promote historical evidence into a new run, or close unobserved live gaps.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
A04 = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04')
CAPTURE_STOP = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/root-attempt-01/capture-stop.json')

def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def ref(path: Path):
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper()}

def main():
    timeline = read(A04 / 'timeline.json')
    actual = [utterance for chapter in timeline['chapters'] for utterance in chapter['utterances']]
    expected_counts = {'opening': 10, 'pursuit': 30, 'knights': 38,
                       'reinforcement': 42, 'terminal': 37, 'closing': 10}
    if Counter(row['chapter'] for row in actual) != Counter(expected_counts):
        raise ValueError('Actual a04 timeline chapter coverage changed')
    reviews = {}
    inputs = []
    for group in ('knights', 'reinforcement', 'other'):
        path = ROOT / group / 'utterance-audit.json'
        if group == 'knights':
            path = ROOT / group / 'sentence-audit.json'
        document = read(path)
        array_key = next((name for name in ('utterances', 'sentences', 'rows')
                          if isinstance(document.get(name), list)), None)
        rows = document.get(array_key)
        if not isinstance(rows, list):
            raise ValueError('Review has no utterance rows: ' + group)
        inputs.append(ref(path))
        for index, row in enumerate(rows):
            key = row['key']
            if key in reviews:
                raise ValueError('Duplicate reviewed key: ' + key)
            reviews[key] = {'path': str(path.resolve()), 'pointer': f'/{array_key}/{index}', 'row': row}
    if set(reviews) != {row['key'] for row in actual}:
        raise ValueError('The reviews do not cover exactly the actual 167 a04 utterances')
    assembled = []
    for utterance in actual:
        binding = reviews[utterance['key']]
        row = binding['row']
        sentence = row.get('chinese_sentence', row.get('zh', row.get('sentence')))
        if sentence != utterance['zh']:
            raise ValueError('Review sentence differs from actual a04 narration: ' + utterance['key'])
        assembled.append({'key': utterance['key'], 'chapter': utterance['chapter'],
                          'zh': utterance['zh'], 'global_start': utterance['global_start'],
                          'duration': utterance['duration'],
                          'review_locator': {key: binding[key] for key in ('path', 'pointer')},
                          'review': row})
    stop = read(CAPTURE_STOP)
    if stop['ck3_started'] or stop['new_native_observation_obtained'] or stop['new_ui_observation_obtained']:
        raise ValueError('This closeout must not claim a live observation')
    report = {
        'schema': 'ck3.a04-mechanism-evidence.audit-index.v1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'coverage': {'actual_a04_utterances': len(actual), 'audited_utterances': len(assembled),
                     'chapters': expected_counts, 'missing_keys': [], 'duplicate_keys': [],
                     'actual_narration_matched': True},
        'source_branch': 'codex/war-series-brown-gold-20261001',
        'source_base': 'd81b91be1ae6bf818f38c3c5af0d595dd4ea4752',
        'master_contents_received': False, 'merge_performed': False,
        'original_a04': {'path': str(A04 / 'CK3-War-AI-Episode02-Review-20260930-a04.mp4'),
                         'bytes': 240710781,
                         'sha256': 'CB141C63966D86BDC8E267B4D958A79C1BB06A8EF69814DC0D6788F0345B8C7E'},
        'review_inputs': inputs, 'actual_timeline': ref(A04 / 'timeline.json'),
        'conclusions': dict(Counter(str(row['review'].get('conclusion', 'UNCLASSIFIED')) for row in assembled)),
        'claims_catalogued': sum(len(row['review'].get('claims', [])) for row in assembled),
        'priority_remaining_gaps': [
            {'priority': 1, 'topic': 'knight-nextday', 'character_id': 33437,
             'new_observation_obtained': False,
             'gap': 'Current a02 failed final trace and has no d27 checkpoint/life row. Roster removal and old020 death do not prove the missing current nextday state.',
             'date_boundary': 'Case d26=1066-12-30/raw53146848 to d27=1066-12-31/raw53146872',
             'acceptance': 'New same-run paused native binding and one checkpoint at d27; hash-frozen save with exact CharacterID life/death data. Saved state is explicitly distinct from a targeted live query.'},
            {'priority': 2, 'topic': 'reinforcement-sameframe', 'new_observation_obtained': False,
             'gap': 'Historical A01 same-run/date UI is not pixel-bound to the join hook. Width tooltip and exact paired paused snapshot/control are missing.',
             'acceptance': 'Two current-run paused original UI frames, date/counts/width tooltip and exact native frame/revision/CombatID binding before and after at most one day. Do not equate post-pause current sums with join-return values.'},
        ],
        'capture_stop': ref(CAPTURE_STOP), 'capture_environment_status': stop['status'],
        'screen_lease_released': stop['screen_lease']['released'],
        'new_live_evidence': False, 'human_full_1x_review': False, 'human_signoff': 'not-provided',
        'utterances': assembled,
    }
    path = ROOT / 'audit-index.json'
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'report': ref(path), 'coverage': report['coverage'],
                      'conclusions': report['conclusions'], 'claims_catalogued': report['claims_catalogued']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
