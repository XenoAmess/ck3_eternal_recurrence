from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).parent
old_path = BASE / 'semantic-alignment-final-BC-a01.json'
raw = old_path.read_bytes()
if len(raw) != 15493 or hashlib.sha256(raw).hexdigest() != '0b2faa9fc27c1646c1fbd34040dfd78919fd5a2b2a93f84fc9c5ff84e2a172c0':
    raise ValueError('Original actual alignment drift')
alignment = json.loads(raw)
events = json.loads((BASE / 'actual-subtitles-a01/E4-05/timeline.json').read_bytes())['events']
by_id = {event['id']: event for event in events}
changes = {
    'C05-04-S07': "B's London endpoint remains unobserved.",
    'C05-10-S08': 'Keep these windows separate.',
    'C05-14-S05': 'New regiment record: 1/1 soldier.',
    'C05-14-S18': 'Back to A: whole army, direct route.',
}
revision = []
for para in alignment['paragraphs']:
    for number, unit in enumerate(para['units'], 1):
        key = para['paragraph_id'] + '-S' + str(number).zfill(2)
        if key not in changes:
            continue
        event = by_id[key]
        if event['zh'] != unit['zh'] or event['en'] != unit['en']:
            raise ValueError('Actual failed event/source differs')
        seconds = (event['end_frame'] - event['start_frame']) / 30
        new = changes[key]
        new_rate = len(new.split()) / seconds
        if new_rate > 4.5:
            raise ValueError('Display revision still exceeds actual rate: ' + key)
        unit['english_display_text'] = new
        unit['display_equivalence_reviewed'] = True
        unit['display_equivalence_review_basis'] = 'Same actual Chinese/full English claim; observer/date/numeric/source scope preserved. Only displayed English shortened.'
        revision.append({'id': key, 'zh': unit['zh'], 'full_English_source': unit['en'],
                         'new_display_English': new, 'actual_duration_seconds': seconds,
                         'old_words_per_second': event['reading_rate']['english_words_per_second'],
                         'new_words_per_second': new_rate, 'timing_unchanged': True,
                         'Chinese_audio_and_source_unchanged': True})
if [row['id'] for row in revision] != list(changes):
    raise ValueError('Unexpected four-unit delta')
alignment['display_revision_only'] = True
alignment['prior_alignment'] = {'path': str(old_path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
alignment['Root_English_source_review'] = {
    'path': 'C:/ck3-war-episode04-research-20261004-a01/e04-final-BC-Root-actual-English-review-a01/Root-English-NO-BLOCK.json',
    'bytes': 2608, 'sha256': 'cb5adf685a6895c1461cc9295b14ac247ab2f4ad648e05f9d8bee33da5b11158'}
new_path = BASE / 'semantic-alignment-final-BC-display-a02.json'
with new_path.open('xb') as stream:
    stream.write((json.dumps(alignment, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
new_raw = new_path.read_bytes()
new_pin = {'path': str(new_path), 'bytes': len(new_raw), 'sha256': hashlib.sha256(new_raw).hexdigest()}
report = {'schema': 'xar.e04.actual-four-English-display-revision/v1',
          'full_English_diff_sha256_unchanged': 'b2243b8d3cd8d843f416b080f4ed96de15ade494a06e9fcd78aafefc643be944',
          'alignment': new_pin, 'actual_reading_rate_cases': revision,
          'Root_actual_display_review_status': None, 'Root_actual_reviewed_utc': None,
          'provider_calls': 0, 'audio_or_timing_change': False, 'human_film_signoff': False}
report_path = BASE / 'Root-four-display-equivalence-review-a01.json'
with report_path.open('xb') as stream:
    stream.write((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
report_raw = report_path.read_bytes()
print(json.dumps({'alignment': new_pin, 'review': {'path': str(report_path), 'bytes': len(report_raw),
                                                  'sha256': hashlib.sha256(report_raw).hexdigest()},
                  'cases': revision}, ensure_ascii=False, indent=2))
