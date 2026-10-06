from pathlib import Path
import hashlib
import importlib
import json
import sys

ROOT = Path('C:/ck3-war-episode04-research-20261004-a01')
BASE = Path(__file__).parent

def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def read_pinned(path, size, sha):
    data = Path(path).read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
        raise ValueError('Exact source drift: ' + str(path))
    return json.loads(data)

def write_new(name, obj):
    path = BASE / name
    with path.open('xb') as stream:
        stream.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

root_review_path = ROOT / 'e04-final-BC-Root-actual-source-review-a01/Root-NO-BLOCK.json'
root_review = read_pinned(root_review_path, 15648, '5874bd3c5cc0557a61a47a66fb3788841ed1dd78c00eb02ebe6323cc6902428f')
draft_path = BASE / 'English-semantic-draft-a03-NOT-FINAL.json'
draft = json.loads(draft_path.read_bytes())
if root_review['source_review_status'] != 'NO_BLOCK' or root_review['final_freeze'] is not True:
    raise ValueError('Actual Root Chinese/source freeze is absent')
for name in ['chinese_body_sha256', 'chinese_ledger_sha256']:
    if draft[name] != root_review[name]:
        raise ValueError('English source binding drift: ' + name)
ids = [row['id'] for row in draft['paragraphs']]
if ids != root_review['subtitle_changed_ids']:
    raise ValueError('Actual subtitle delta mismatch')
claims_path = ROOT / 'e04-final-BC-story-a01/actual-story-a02/claim-ledger-final-BC-a06.json'
claims_bytes = claims_path.read_bytes()
if hashlib.sha256(claims_bytes).hexdigest() != draft['chinese_ledger_sha256']:
    raise ValueError('Actual ledger bytes drift')
claims = {row['id']: row for row in json.loads(claims_bytes)['claims']}

helper_dir = ROOT / 'e04-subtitle-timeline-a01'
expected_helpers = {
    'subtitle_producer.py': (16685, 'b0f9a94bc29e16142a03089259a0a07ab77c4dc3176acb0cacb296928a7e4dc2'),
    'reflow_english_term_lines_a01.py': (4151, 'e519f20eecae0771ab43d389e367aed78e361e5d68e2b555816d0b82e2ce36a9'),
}
for name, (size, sha) in expected_helpers.items():
    data = (helper_dir / name).read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
        raise ValueError('Existing layout helper drift: ' + name)
sys.path.insert(0, str(helper_dir))
p = importlib.import_module('subtitle_producer')
english_lines = importlib.import_module('reflow_english_term_lines_a01').english_lines

paragraphs = []
alignment_rows = []
review_rows = []
for row in draft['paragraphs']:
    if row['source_keys'] != claims[row['id']]['source_keys']:
        raise ValueError('English source_keys differ from final ledger: ' + row['id'])
    if ''.join(unit['zh'] for unit in row['units']) != claims[row['id']]['claim_summary']:
        raise ValueError('Chinese units do not reconstruct actual final source: ' + row['id'])
    if ' '.join(unit['en'] for unit in row['units']) != row['subtitles_en']:
        raise ValueError('English units do not reconstruct actual paragraph: ' + row['id'])
    display_units = []
    for number, unit in enumerate(row['units'], 1):
        display_units.append({'unit': number, **unit,
                              'display': {'zh': p.display_lines(unit['zh'], 'zh'),
                                          'en': english_lines(unit['en'])}})
    paragraphs.append({key: row[key] for key in ['id', 'subtitles_en', 'source_keys']})
    alignment_rows.append({'paragraph_id': row['id'], 'units': row['units']})
    review_rows.append({'paragraph_id': row['id'], 'source_keys': row['source_keys'],
                       'subtitles_zh': ''.join(unit['zh'] for unit in row['units']),
                       'subtitles_en': row['subtitles_en'], 'units': display_units})

english = {'schema': 'xar.e04.final-English-diff.v1', 'source_review_status': 'NO_BLOCK',
           'chinese_body_sha256': draft['chinese_body_sha256'],
           'chinese_ledger_sha256': draft['chinese_ledger_sha256'],
           'Root_Chinese_source_review': pin(root_review_path), 'paragraphs': paragraphs,
           'ABC_winner': None, 'human_signoff': False}
english_pin = write_new('English-diff-final-BC-a01.json', english)
alignment = {'schema': 'xar.e04.actual-final-semantic-alignment.v1',
             'English_diff_sha256': english_pin['sha256'],
             'Chinese_body_sha256': draft['chinese_body_sha256'],
             'paragraphs': alignment_rows, 'source_review_status': 'NO_BLOCK',
             'actual_audio_timing': None, 'human_listening_signoff': False}
alignment_pin = write_new('semantic-alignment-final-BC-a01.json', alignment)
readability = {'schema': 'xar.e04.final-English-semantic-readable-review.v1',
               'status': 'TEXT_SEMANTICS_AND_NEW_UNIT_LAYOUT_NO_BLOCK',
               'English_diff': english_pin, 'alignment': alignment_pin,
               'Root_Chinese_source_review': pin(root_review_path),
               'paragraphs': review_rows, 'actual_new_unit_count': len([u for row in review_rows for u in row['units']]),
               'layout': {'width': 1920, 'height': 1080, 'Chinese_font_size': 35,
                          'English_font_size': 25, 'max_lines_each_language': 2,
                          'maximum_font_width_px': 1700},
               'source_semantic_bounds': ['B windows remain separate', 'C first observed at day77; actual arrival in (75,77]',
                                          'Main original cohort; never all-player total', 'current1percent is not applied casualty count',
                                          'gold differences remain net, not payment/march-cost ledger',
                                          'sampling deviations retained; no controlled winner', 'C05-14 explicitly returns to A before unchanged C05-15'],
               'reading_rate_pending_actual_PCM_WB': True,
               'provider_calls': 0, 'media_reads': 0, 'human_signoff': False}
readability_pin = write_new('ROOT-English-semantic-readable-review-a01.json', readability)
delivery = {'schema': 'xar.e04.actual-final-English-delivery.v1',
            'status': 'ACTUAL_FINAL_TEXT_READY_FOR_AUDIO_INDEX_AND_TIMED_SUBTITLES',
            'English_diff': english_pin, 'alignment': alignment_pin,
            'semantic_readable_review': readability_pin,
            'changed_paragraph_ids': root_review['changed_paragraph_ids'],
            'subtitle_changed_ids': ids, 'Root_source_review': pin(root_review_path),
            'actual_new_unit_count': sum(len(row['units']) for row in draft['paragraphs']),
            'unaffected_English_paragraphs': 62, 'actual_audio_timing': None,
            'human_signoff': False}
delivery_pin = write_new('EN-ROOT-DELIVERY-a01.json', delivery)
print(json.dumps({'delivery': delivery_pin, 'English_diff': english_pin,
                  'alignment': alignment_pin, 'readability': readability_pin}, ensure_ascii=False, indent=2))
