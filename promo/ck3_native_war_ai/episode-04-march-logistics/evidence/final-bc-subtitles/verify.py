"""Read-only portable subtitle proof. Default PLAN; --verify reads only catalogued text."""
from pathlib import Path
import argparse
import hashlib
import json
import re


def verify(root):
    root = root.resolve()
    index = json.loads((root / 'index.json').read_bytes())
    roles = {}
    for row in index['files']:
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Catalog path outside package')
        data = path.read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Exact catalog bytes differ: ' + row['path'])
        if row['role'] in roles:
            raise ValueError('Duplicate catalog role')
        roles[row['role']] = path
    def doc(role):
        return json.loads(roles[role].read_bytes())
    timeline = doc('final-global-timeline')
    baseline = doc('historical-A-global-timeline')
    english = doc('final-English-source')
    alignment = doc('final-semantic-display-alignment')
    review = doc('Root-Chinese-source-review')
    enreview = doc('Root-English-display-source-review')
    body = dict(re.findall(r'^\[(C\d{2}-\d{2})\] (.+)$', roles['final-Chinese-body'].read_text(encoding='utf-8-sig'), re.MULTILINE))
    if len(body) != 69 or len(timeline['paragraphs']) != 69:
        raise ValueError('Actual 69-paragraph roster differs')
    if (timeline['sample_rate'], timeline['sample_frames'], timeline['actual_seconds']) != (24000, 41658624, 1735.776):
        raise ValueError('Actual PCM clock differs')
    cursor = 0
    for para in timeline['paragraphs']:
        if para['global_start_sample'] != cursor:
            raise ValueError('Paragraph PCM gap/overlap')
        cursor = para['global_end_sample']
    if cursor != timeline['sample_frames']:
        raise ValueError('Final paragraph endpoint differs from actual PCM')
    changed = review['subtitle_changed_ids']
    if len(changed) != 7 or [row['id'] for row in english['paragraphs']] != changed:
        raise ValueError('Actual seven-paragraph delta differs')
    final_en = {row['id']: row['subtitles_en'] for row in english['paragraphs']}
    claims = {row['id']: row for row in doc('final-claim-ledger')['claims']}
    events = timeline['events']
    old_events = baseline['events']
    new_units = 0
    for para in timeline['paragraphs']:
        key = para['id']
        current = [event for event in events if event['paragraph_id'] == key]
        old = [event for event in old_events if event['paragraph_id'] == key]
        if ''.join(event['zh'] for event in current) != body[key]:
            raise ValueError('Actual Chinese subtitle reconstruction differs: ' + key)
        expected_en = final_en[key] if key in changed else ' '.join(event['en'] for event in old)
        if ' '.join(event['en'] for event in current) != expected_en:
            raise ValueError('Full English source reconstruction differs: ' + key)
        if key in changed:
            new_units += len(current)
            if any(event['review_flags'] for event in current):
                raise ValueError('Actual new reading-rate flag remains')
            if any(event['reading_rate']['english_words_per_second'] > 4.5 or event['reading_rate']['Chinese_characters_per_second'] > 7 for event in current):
                raise ValueError('Actual new declared reading rate exceeds bound')
        else:
            if len(current) != len(old):
                raise ValueError('Unchanged subtitle unit roster differs')
            for now, prior in zip(current, old):
                for field in ['zh', 'en', 'display']:
                    if now[field] != prior[field]:
                        raise ValueError('Unchanged text/display differs: ' + key)
                for nbind, obind in zip(now['timing_bindings'], prior['timing_bindings']):
                    if {k: v for k, v in nbind.items() if k not in ['start_seconds', 'end_seconds']} != {k: v for k, v in obind.items() if k not in ['start_seconds', 'end_seconds']}:
                        raise ValueError('Unchanged native timing source differs: ' + key)
    if len(events) != 326 or new_units != 86:
        raise ValueError('Actual subtitle unit count differs')
    for row in english['paragraphs']:
        if row['source_keys'] != claims[row['id']]['source_keys']:
            raise ValueError('English source keys differ from final ledger')
    if review['source_review_status'] != 'NO_BLOCK' or enreview['source_review_status'] != 'NO_BLOCK':
        raise ValueError('Actual Root text source review is absent')
    if alignment['English_diff_sha256'] != hashlib.sha256(roles['final-English-source'].read_bytes()).hexdigest():
        raise ValueError('Final display alignment/English source pin differs')
    if timeline['ABC_winner'] is not None or timeline['C_subject_scope']['all_player_total_soldiers'] is not None:
        raise ValueError('A winner or all-player count was fabricated')
    affected = {}
    for chapter, count in [('E4-05', 16), ('E4-06', 10)]:
        relative = doc(chapter + '-relative-delivery')
        expected = ['C' + chapter[-2:] + '-' + str(n).zfill(2) for n in range(1, count + 1)]
        if [row['paragraph_id'] for row in relative['paragraphs']] != expected:
            raise ValueError('Affected chapter relative roster differs')
        for key in expected:
            relative_timeline = doc(key + '-relative-timeline')
            if relative_timeline['paragraph_id'] != key:
                raise ValueError('Relative paragraph identity differs')
            if ''.join(event['zh'] for event in relative_timeline['events']) != body[key]:
                raise ValueError('Relative exact Chinese differs')
        affected[chapter] = count
    audio = doc('final-English-bound-audio-ROOT')
    wb_count = 0
    new_fragment_count = 0
    old_fragment_count = 0
    coarse_count = 0
    for row in audio['chapter_timeline']:
        index_doc = doc(row['chapter_id'] + '-final-audio-index')
        for para in index_doc['paragraphs']:
            for frag in para['fragments']:
                if para['id'] in changed:
                    metadata = roles['WordBoundary-' + frag['fragment_id']]
                    lines = [json.loads(line) for line in metadata.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
                    native = [line for line in lines if line['type'] == 'WordBoundary']
                    if len(native) != frag['WordBoundary_count']:
                        raise ValueError('Actual native WordBoundary count differs')
                    wb_count += len(native)
                    new_fragment_count += 1
                else:
                    old_fragment_count += 1
                    if frag['metadata'] is None:
                        coarse_count += 1
    if (new_fragment_count, old_fragment_count, coarse_count, wb_count) != (7, 67, 6, 774):
        raise ValueError('Actual audio/WB reuse scope differs')
    return {'status': 'PORTABLE_TEXT_BYTE_AND_ACTUAL_SUBTITLE_CLOCK_VERIFIED',
            'catalog_files': len(index['files']), 'paragraphs': 69, 'subtitle_units': 326,
            'actual_new_units': 86, 'affected_relative_paragraphs': affected,
            'actual_PCM_samples': 41658624, 'actual_seconds': 1735.776,
            'new_WordBoundary': 774, 'reused_fragments': 67, 'old_null_WB_fragments': 6,
            'movie_or_audio_bytes_read': 0, 'provider_calls': 0,
            'human_listening_signoff': False, 'film_signoff': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if not args.verify:
        result = {'status': 'PLAN_ONLY', 'root': str(args.root),
                  'execute': 'python -I -S verify.py --verify', 'file_reads': 0,
                  'writes': 0, 'provider_or_media_calls': 0,
                  'human_signoff': False}
    else:
        result = verify(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
