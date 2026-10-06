"""File-only final B/C subtitle increment with an explicit data request.

Commands: plan, validate, build. Plan does not create subtitle/media assets.
Build requires a final reviewed text/alignment and published actual PCM/WB.
It invokes no provider, FFmpeg, CK3, SDK, UI, Git, or upload operation.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
EXPECTED_LAYOUT = {'width': 1920, 'height': 1080, 'Chinese_font_size': 35,
                   'English_font_size': 25, 'max_lines_each_language': 2,
                   'Chinese_chars_per_line': 40, 'English_chars_per_line': 100,
                   'maximum_font_width_px': 1700}
REQUIRED = ['final_chinese_body', 'final_claim_ledger', 'final_English_diff',
            'final_alignment', 'source_review', 'final_audio_delivery',
            'final_C_terminal_source']


def read(path):
    return json.loads(Path(path).read_bytes())


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def exact(row):
    if not isinstance(row, dict) or set(row) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Each small JSON/text/source input requires exact path/bytes/sha256')
    if type(row['bytes']) is not int or row['bytes'] < 0 or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
        raise ValueError('Invalid source pin')
    actual = pin(row['path'])
    if actual != row:
        raise ValueError('Pinned input differs: ' + row['path'])
    return actual


def write_new(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def paragraph_map(body):
    rows = re.findall(r'^\[(C\d{2}-\d{2})\] (.+)$', body, re.MULTILINE)
    if len(rows) != 69 or len(dict(rows)) != 69:
        raise ValueError('Final Chinese body must have the exact 69 unique paragraph IDs')
    return dict(rows)


def baseline(request):
    if request['schema'] != 'xar.e04.final-subtitle-increment-request.v1' or request['layout'] != EXPECTED_LAYOUT:
        raise ValueError('Unsupported request schema or silent change of frozen ZH35/EN25 layout')
    exact(request['baseline_subtitle_package'])
    package = read(request['baseline_subtitle_package']['path'])
    exact(package['full_global_timeline'])
    timeline = read(package['full_global_timeline']['path'])
    if len(timeline['paragraphs']) != 69 or timeline['sample_frames'] != 37900224:
        raise ValueError('Baseline is not the completed A-only subtitle package')
    if timeline['ABC_results']['B'] is not None or timeline['ABC_results']['C'] is not None:
        raise ValueError('Unexpected reinterpretation of the historical A-only package')
    return package, timeline


def plan(request):
    package, base = baseline(request)
    missing = [key for key in REQUIRED if request.get(key) is None]
    return {'schema': 'xar.e04.final-subtitle-file-plan.v1',
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'AWAITING_FINAL_ACTUAL_INPUTS' if missing else 'READY_FOR_EXPLICIT_VALIDATION',
            'baseline': request['baseline_subtitle_package'], 'baseline_font_layout': EXPECTED_LAYOUT,
            'B_candidate_only': request['B_candidate_only'], 'provisional_changed_ids': request['provisional_changed_ids'],
            'missing_pinned_inputs': missing,
            'final_changed_ids': None, 'final_audio_samples': None, 'final_audio_seconds': None,
            'final_picture_frames': None, 'final_ABC_results': None, 'final_winner': None,
            'unchanged_reuse_contract': 'Keep source text, English, display lines/fonts, actual audio and relative native time of every unchanged paragraph. Only shift chapter/global sample offsets.',
            'new_timing_contract': 'Each changed paragraph must have exact-source semantic units and actual WordBoundary metadata for all its changed audio fragments. Never estimate its duration or refit native offsets.',
            'picture_reuse_contract': 'Keep previous prepared MOV bytes as source artifacts. Allocate final clips from cumulative actual PCM boundaries; necessary final-frame trimming belongs to a new picture attempt. Do not automatically hold or pad.',
            'history_contract': 'NEW output directory; keep A-only 1579.176 seconds/47376 frames as historical values, not final predictions.',
            'produced_subtitles': False, 'provider_calls': 0, 'audio_raw_or_movie_hashes': 0,
            'film_or_listening_signoff': False}


def bind_Main_subject_scope(actual_scope, scope_sha256, review, ledger):
    if actual_scope.get('schema') != 'ck3.e04.abc.required-cohort-scope/v1' or actual_scope.get('required_Main_rows_available') is not True or actual_scope.get('no_unknown_value_coerced_to_zero_or_transport') is not True:
        raise ValueError('Root Main/partial health scope is unavailable or unsupported')
    subject_scope = {
        'kind': 'required_Main_original_cohort',
        'required_public_ids': actual_scope['required_public_ids'],
        'required_native_carmy_ids': actual_scope['required_native_carmy_ids'],
        'required_full_regiments': actual_scope['required_full_regiments'],
        'required_full_DATA': actual_scope['required_full_DATA'],
        'global_health_status': actual_scope['actual_global_scope_status_preserved'],
        'unassessed_CUnit_ids': actual_scope['unassessed_current_CUnit_ids'],
        'unassessed_health': actual_scope['excluded_health'],
        'all_player_total_soldiers': None,
    }
    if review.get('C_Main_scope_source_sha256') != scope_sha256 or ledger.get('C_Main_scope_source_sha256') != scope_sha256:
        raise ValueError('Source review/ledger do not bind Root Main scope bytes')
    if review.get('C_subject_scope') != subject_scope or ledger.get('C_subject_scope') != subject_scope:
        raise ValueError('Main scope/global partial/unknown health must remain exact, never all-player total')
    return subject_scope


def validate(request):
    package, base = baseline(request)
    missing = [key for key in REQUIRED if request.get(key) is None]
    if missing:
        raise ValueError('Actual final inputs missing: ' + ', '.join(missing))
    for key in REQUIRED:
        exact(request[key])
    review = read(request['source_review']['path'])
    if review.get('source_review_status') != 'NO_BLOCK' or review.get('final_freeze') is not True:
        raise ValueError('Final reviewed source/alignment freeze is absent; B drafts are not final authority')
    body = paragraph_map(Path(request['final_chinese_body']['path']).read_text(encoding='utf-8-sig'))
    baseline_text = {row['id']: ''.join(e['zh'] for e in base['events'] if e['paragraph_id'] == row['id']) for row in base['paragraphs']}
    if list(body) != list(baseline_text):
        raise ValueError('Paragraph IDs or order changed')
    voice_changed = [key for key in body if body[key] != baseline_text[key]]
    if not voice_changed or voice_changed != review.get('changed_paragraph_ids'):
        raise ValueError('Final changed IDs do not match the exact Chinese delta/review')
    if review.get('chinese_body_sha256') != request['final_chinese_body']['sha256'] or review.get('chinese_ledger_sha256') != request['final_claim_ledger']['sha256']:
        raise ValueError('Source review does not bind the final Chinese body/ledger')
    if review.get('C_terminal_source_sha256') != request['final_C_terminal_source']['sha256']:
        raise ValueError('Source review does not bind the actual final C terminal source')
    context = request.get('current_C_Root_basis_source')
    if context is None:
        raise ValueError('Actual Root sampling-policy source pin is missing')
    exact(context)
    if review.get('C_sampling_Root_receipt_sha256') != context['sha256']:
        raise ValueError('Final source review does not bind the actual Root sampling receipt')
    sampling = read(context['path'])
    if sampling.get('controlled_comparison_eligibility_granted') is not False or not isinstance(sampling.get('sampling_protocol_deviations'), list):
        raise ValueError('Unsupported/missing actual Root sampling eligibility facts')
    if review.get('C_controlled_comparison_eligibility') != 'NOT_GRANTED' or review.get('ABC_winner') is not None:
        raise ValueError('Actual C sampling limits cannot be relabelled a controlled winner')
    scope_pin = request.get('current_C_Main_scope_source')
    if scope_pin is None:
        raise ValueError('Actual Root-linked Main scope pin is missing')
    exact(scope_pin)
    actual_scope = read(scope_pin['path'])
    ledger = read(request['final_claim_ledger']['path'])
    subject_scope = bind_Main_subject_scope(actual_scope, scope_pin['sha256'], review, ledger)
    english = read(request['final_English_diff']['path'])
    if english.get('source_review_status') != 'NO_BLOCK' or english.get('chinese_body_sha256') != request['final_chinese_body']['sha256'] or english.get('chinese_ledger_sha256') != request['final_claim_ledger']['sha256']:
        raise ValueError('English diff is not bound to the final reviewed Chinese source')
    english_rows = {row['id']: row for row in english['paragraphs']}
    changed = review.get('subtitle_changed_ids', voice_changed)
    if not isinstance(changed, list) or [key for key in body if key in changed] != changed or not set(voice_changed) <= set(changed):
        raise ValueError('Subtitle IDs must be ordered and include all real Chinese voice changes')
    if len(english_rows) != len(english['paragraphs']) or list(english_rows) != changed:
        raise ValueError('English diff must contain only the final changed IDs in body order')
    alignment = read(request['final_alignment']['path'])
    if alignment.get('English_diff_sha256') != request['final_English_diff']['sha256'] or alignment.get('Chinese_body_sha256') != request['final_chinese_body']['sha256']:
        raise ValueError('Semantic alignment does not bind final source bytes')
    aligned = {row['paragraph_id']: row['units'] for row in alignment['paragraphs']}
    if len(aligned) != len(alignment['paragraphs']) or list(aligned) != changed:
        raise ValueError('Semantic alignment must contain only the final changed IDs')
    for key in changed:
        if ''.join(unit['zh'] for unit in aligned[key]) != body[key] or ' '.join(unit['en'] for unit in aligned[key]) != english_rows[key]['subtitles_en']:
            raise ValueError('Semantic units do not reconstruct exact final Chinese/English: ' + key)
    old_English = {row['id']: ' '.join(e['en'] for e in base['events'] if e['paragraph_id'] == row['id']) for row in base['paragraphs']}
    English_only = [key for key in changed if key not in voice_changed]
    if any(english_rows[key]['subtitles_en'] == old_English[key] for key in English_only):
        raise ValueError('English-only IDs must be an actual English change, not a picture-card refresh')
    for key in English_only:
        old_units = [event['zh'] for event in base['events'] if event['paragraph_id'] == key]
        if [unit['zh'] for unit in aligned[key]] != old_units:
            raise ValueError('English-only alignment must keep actual old Chinese units/display/timing')
    audio = read(request['final_audio_delivery']['path'])
    rows = audio['chapter_timeline']
    if [row['chapter_id'] for row in rows] != [f'E4-{n:02d}' for n in range(1, 7)]:
        raise ValueError('Final audio must retain six chapter order')
    indexes = {}
    cursor = 0
    new_fragment_count = 0
    old_indexes = {}
    for chapter in base['chapters']:
        original = read(exact(chapter['source_timeline'])['path'])
        old_indexes[chapter['chapter_id']] = read(exact(original['source_audio_index'])['path'])
    for row in rows:
        index = read(exact(row['index'])['path'])
        pcm = index['actual_PCM']
        if pcm['sample_rate'] != 24000 or pcm['sample_frames'] / 24000 != pcm['seconds'] or index['inserted_silence_frames'] != 0:
            raise ValueError('Final actual PCM sample contract differs')
        if row['start_sample'] != cursor or row['end_sample'] != cursor + pcm['sample_frames']:
            raise ValueError('Final chapter/global sample offsets are not actual cumulative PCM')
        old_paras = {para['id']: para for para in old_indexes[row['chapter_id']]['paragraphs']}
        index_cursor = 0
        for para in index['paragraphs']:
            key = para['id']
            old = old_paras[key]
            expected_en = english_rows[key]['subtitles_en'] if key in changed else old['subtitles_en']
            if para['subtitles_zh'] != body[key] or para['subtitles_en'] != expected_en:
                raise ValueError('Final audio index differs from final exact text: ' + key)
            if para['chapter_start_sample'] != index_cursor:
                raise ValueError('Paragraph gap/overlap in actual PCM')
            fcursor = index_cursor
            text = ''
            if key not in voice_changed and len(para['fragments']) != len(old['fragments']):
                raise ValueError('Unchanged paragraph fragment roster changed: ' + key)
            for number, fragment in enumerate(para['fragments']):
                if fragment['chapter_start_sample'] != fcursor or fragment['decoded_PCM']['sample_frames'] != fragment['chapter_end_sample'] - fcursor:
                    raise ValueError('Fragment actual PCM offsets disagree')
                if fragment['text_sha256'] != hashlib.sha256(fragment['text_zh'].encode('utf-8')).hexdigest():
                    raise ValueError('Fragment text SHA disagrees')
                text += fragment['text_zh']
                if key in voice_changed:
                    if fragment['metadata'] is None or fragment['kind'] != 'new-generated-audio' or type(fragment['WordBoundary_count']) is not int or fragment['WordBoundary_count'] < 1:
                        raise ValueError('Changed paragraph lacks actual new WordBoundary: ' + key)
                    exact(fragment['metadata'])
                    new_fragment_count += 1
                else:
                    prior = old['fragments'][number]
                    for field in ['fragment_id', 'text_sha256', 'text_zh', 'audio', 'decoded_audio', 'decoded_PCM', 'metadata', 'WordBoundary_count']:
                        if fragment[field] != prior[field]:
                            raise ValueError('Unchanged actual audio/metadata source differs: ' + key + '/' + field)
                fcursor = fragment['chapter_end_sample']
            if text != para['subtitles_zh'] or fcursor != para['chapter_end_sample']:
                raise ValueError('Fragment text/sample roster does not reconstruct paragraph')
            index_cursor = para['chapter_end_sample']
        if index_cursor != pcm['sample_frames']:
            raise ValueError('Chapter PCM endpoint differs')
        cursor += pcm['sample_frames']
        indexes[row['chapter_id']] = index
    if audio['actual_PCM']['sample_frames'] != cursor or audio['actual_PCM']['seconds'] != cursor / 24000:
        raise ValueError('Final total actual audio length is not the chapter sum')
    if not isinstance(review.get('ABC_results'), dict) or set(review['ABC_results']) != {'A', 'B', 'C'} or 'ABC_winner' not in review:
        raise ValueError('Final semantics must explicitly retain A/B/C and winner values or nulls')
    return {'package': package, 'base': base, 'body': body, 'changed': changed,
            'voice_changed': voice_changed, 'English_only': English_only, 'subject_scope': subject_scope,
            'english': english_rows,
            'aligned': aligned, 'audio': audio, 'indexes': indexes, 'review': review,
            'new_fragment_count': new_fragment_count, 'samples': cursor}


def load_producer(request):
    dependency = request['producer_helpers']
    for row in dependency.values():
        exact(row)
    sys.path.insert(0, str(Path(dependency['subtitle_producer']['path']).parent))
    import subtitle_producer as p
    from reflow_english_term_lines_a01 import english_lines
    if p.ref(p.__file__) != dependency['subtitle_producer']:
        raise ValueError('Loaded producer module is not the pinned helper')
    return p, english_lines


def frame_times(event):
    event['start_frame'] = round(event['start_seconds'] * 30)
    event['end_frame'] = max(event['start_frame'] + 1, math.floor(event['end_seconds'] * 30))


def replace_English_only(events, units, p, english_lines):
    """Keep Chinese display and actual time exact; never touch audio/metadata."""
    if len(events) != len(units) or any(event['zh'] != unit['zh'] for event, unit in zip(events, units)):
        raise ValueError('English-only units must retain existing Chinese source cuts')
    result = copy.deepcopy(events)
    flags = []
    for event, unit in zip(result, units):
        event['en'] = unit['en']
        for field in ['english_display_text', 'english_display_edit', 'english_display_line_change']:
            event.pop(field, None)
        display_en = unit.get('english_display_text', unit['en'])
        if display_en != unit['en']:
            if unit.get('display_equivalence_reviewed') is not True:
                raise ValueError('English-only display wording lacks frozen equivalence review')
            event['english_display_text'] = display_en
        event['display']['en'] = english_lines(display_en)
        duration = (event['end_frame'] - event['start_frame']) / 30
        event['reading_rate'] = {'english_words_per_second': len(display_en.split()) / duration,
            'Chinese_characters_per_second': len(p.normal(event['zh'])) / duration}
        event['review_flags'] = (['english_rate_above4.5wps'] if event['reading_rate']['english_words_per_second'] > 4.5 else []) + (['Chinese_rate_above7cps'] if event['reading_rate']['Chinese_characters_per_second'] > 7 else [])
        if event['review_flags']:
            flags.append({'id': event['id'], 'flags': event['review_flags']})
    return result, flags


def pair(folder, timeline, p):
    folder.mkdir()
    write_new(folder / 'timeline.json', timeline)
    with (folder / 'subtitles.ass').open('xb') as stream:
        stream.write(p.ass_bytes(timeline['events']))
    return {'timeline': pin(folder / 'timeline.json'), 'subtitles': pin(folder / 'subtitles.ass')}


def build(request, output):
    data = validate(request)
    p, english_lines = load_producer(request)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'request-snapshot.json', request)
    base = data['base']
    chapters = []
    global_events = []
    global_paragraphs = []
    cursor = 0
    relative = []
    rate_flags = []
    try:
        for row in data['audio']['chapter_timeline']:
            key = row['chapter_id']
            index = data['indexes'][key]
            old_ref = next(c['source_timeline'] for c in base['chapters'] if c['chapter_id'] == key)
            old = read(old_ref['path'])
            old_para = {para['id']: para for para in old['paragraphs']}
            events, paragraphs, timing_sources = [], [], []
            for para in index['paragraphs']:
                ident = para['id']
                if ident not in data['voice_changed']:
                    delta = (para['chapter_start_sample'] - old_para[ident]['chapter_start_sample']) / 24000
                    new_events = [copy.deepcopy(e) for e in old['events'] if e['paragraph_id'] == ident]
                    for event in new_events:
                        event['start_seconds'] += delta
                        event['end_seconds'] += delta
                        for binding in event['timing_bindings']:
                            binding['start_seconds'] += delta
                            binding['end_seconds'] += delta
                        frame_times(event)
                    if ident in data['English_only']:
                        new_events, English_flags = replace_English_only(new_events, data['aligned'][ident], p, english_lines)
                        rate_flags += English_flags
                else:
                    fragments, char_cursor = [], 0
                    for original in para['fragments']:
                        fragment = copy.deepcopy(original)
                        fragment['char_start'], fragment['char_end'] = char_cursor, char_cursor + len(fragment['text_zh'])
                        char_cursor = fragment['char_end']
                        fragment['chapter_start_seconds'] = fragment['chapter_start_sample'] / 24000
                        fragment['chapter_end_seconds'] = fragment['chapter_end_sample'] / 24000
                        fragment['seconds'] = fragment['decoded_PCM']['sample_frames'] / 24000
                        lines = [json.loads(line) for line in Path(fragment['metadata']['path']).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
                        fragment['word_positions'] = p.word_positions(fragment['text_zh'], lines, fragment['seconds'])
                        if len(fragment['word_positions']) != fragment['WordBoundary_count']:
                            raise ValueError('Published actual word count differs')
                        timing_sources.append({'fragment_id': fragment['fragment_id'], 'metadata': fragment['metadata'],
                            'native_divisor': 1e7, 'mapped_words': len(fragment['word_positions'])})
                        fragments.append(fragment)
                    new_events, chars = [], 0
                    for number, original_unit in enumerate(data['aligned'][ident], 1):
                        unit = copy.deepcopy(original_unit)
                        unit.update({'id': f'{ident}-S{number:02d}', 'char_start': chars,
                                     'char_end': chars + len(unit['zh']), 'english_cue_id': f'{ident}-EN-{number:02d}'})
                        chars = unit['char_end']
                        begin, end, bindings = p.unit_time(unit, fragments)
                        display_en = unit.get('english_display_text', unit['en'])
                        if display_en != unit['en'] and not unit.get('display_equivalence_reviewed'):
                            raise ValueError('Display wording changed without the final frozen equivalence review')
                        event = {**unit, 'paragraph_id': ident, 'chapter_id': key,
                                 'start_seconds': begin, 'end_seconds': end, 'timing_bindings': bindings,
                                 'display': {'zh': p.display_lines(unit['zh'], 'zh'), 'en': english_lines(display_en)}}
                        frame_times(event)
                        duration = (event['end_frame'] - event['start_frame']) / 30
                        event['reading_rate'] = {'english_words_per_second': len(display_en.split()) / duration,
                                                'Chinese_characters_per_second': len(p.normal(unit['zh'])) / duration}
                        event['review_flags'] = (['english_rate_above4.5wps'] if event['reading_rate']['english_words_per_second'] > 4.5 else []) + (['Chinese_rate_above7cps'] if event['reading_rate']['Chinese_characters_per_second'] > 7 else []) + (['duration_below1sec'] if duration < 1 else [])
                        if event['review_flags']:
                            rate_flags.append({'id': event['id'], 'flags': event['review_flags']})
                        new_events.append(event)
                events += new_events
                paragraphs.append({'id': ident, 'chapter_start_sample': para['chapter_start_sample'],
                    'chapter_end_sample': para['chapter_end_sample'], 'event_ids': [e['id'] for e in new_events]})
            last = 0
            for event in events:
                if last > event['start_frame'] or event['end_seconds'] > index['actual_PCM']['seconds'] + 1e-8:
                    raise ValueError('Native unit boundary overlaps or exceeds chapter actual PCM')
                last = event['end_frame']
            changed_here = any(para['id'] in data['changed'] for para in index['paragraphs'])
            if changed_here:
                source = {**copy.deepcopy(old), 'source_audio_index': row['index'], 'audio': index['audio'],
                    'actual_PCM': index['actual_PCM'], 'paragraphs': paragraphs, 'events': events,
                    'timing_sources': [s for s in old['timing_sources'] if s['fragment_id'].split('-F')[0] not in data['voice_changed']] + timing_sources,
                    'ABC_results': data['review']['ABC_results'], 'ABC_winner': data['review']['ABC_winner'],
                    'chapter_story_freeze': 'final_reviewed_actual_source', 'prior_timeline': old_ref,
                    'word_alignment_signoff': False, 'film_signoff': False}
                chapter_assets = pair(output / key, source, p)
                source_ref = chapter_assets['timeline']
            else:
                if events != old['events'] or index['actual_PCM'] != old['actual_PCM']:
                    raise ValueError('Unchanged chapter changed relative timing or PCM')
                source, source_ref = old, old_ref
            chapters.append({'chapter_id': key, 'start_sample': cursor, 'end_sample': cursor + index['actual_PCM']['sample_frames'],
                'start_seconds': cursor / 24000, 'end_seconds': (cursor + index['actual_PCM']['sample_frames']) / 24000,
                'source_timeline': source_ref, 'source_audio': index['audio']})
            for para in paragraphs:
                global_paragraphs.append({**copy.deepcopy(para), 'chapter_id': key,
                    'global_start_sample': cursor + para['chapter_start_sample'],
                    'global_end_sample': cursor + para['chapter_end_sample']})
            for original in events:
                event = copy.deepcopy(original)
                event['chapter_start_seconds'], event['chapter_end_seconds'] = event['start_seconds'], event['end_seconds']
                event['start_seconds'] += cursor / 24000
                event['end_seconds'] += cursor / 24000
                frame_times(event)
                global_events.append(event)
            # Export every paragraph in each affected chapter, not only changed IDs.
            if changed_here:
                for para in paragraphs:
                    begin = para['chapter_start_sample'] / 24000
                    duration = (para['chapter_end_sample'] - para['chapter_start_sample']) / 24000
                    relative_events = [copy.deepcopy(e) for e in events if e['paragraph_id'] == para['id']]
                    for event in relative_events:
                        event['chapter_start_seconds'], event['chapter_end_seconds'] = event['start_seconds'], event['end_seconds']
                        event['start_seconds'] -= begin
                        event['end_seconds'] -= begin
                        frame_times(event)
                    rel = {'schema': 'xar.e04.actual-paragraph-subtitles.v1', 'paragraph_id': para['id'],
                        'source_timeline': source_ref, 'source_chapter_audio': index['audio'],
                        'audio_slice': {'start_sample': para['chapter_start_sample'], 'end_sample': para['chapter_end_sample'],
                            'sample_rate': 24000, 'exact_seconds': duration, 'picture_duration_frames': math.ceil(duration * 30),
                            'coordinate_basis': 'Actual PCM sample slice; allocate the final movie by cumulative global boundaries.'},
                        'events': relative_events,
                        'actual_WordBoundary_available': all(all(b['basis'] == 'actual-provider-WordBoundary' for b in e['timing_bindings']) for e in relative_events),
                        'estimated_or_mixed_internal_times': any(any(b['basis'].startswith('estimated-') for b in e['timing_bindings']) for e in relative_events),
                        'actual_full_PCM_fragment_times_without_WB': any(any(b['basis'] == 'actual-whole-fragment-PCM-no-WordBoundary' for b in e['timing_bindings']) for e in relative_events),
                        'relative_frame_quantization': 'Exact sample-origin shift then30fps start-round/end-floor; chapter native bindings retained.',
                        'ABC_results': data['review']['ABC_results'],
                        'ABC_winner': data['review']['ABC_winner'], 'film_signoff': False}
                    relative.append({'paragraph_id': para['id'], **pair(output / para['id'], rel, p)})
            cursor += index['actual_PCM']['sample_frames']
        last = 0
        for event in global_events:
            if last > event['start_frame']:
                raise ValueError('Global PCM/frame boundary overlap')
            last = event['end_frame']
        if rate_flags:
            raise ValueError('New subtitle reading-rate flags require explicit alignment/display revision: ' + json.dumps(rate_flags))
        timeline = {'schema': 'xar.e04.actual-stable-full-subtitle-timeline.v1', 'source_request': pin(output / 'request-snapshot.json'),
            'source_audio_delivery': request['final_audio_delivery'], 'sample_rate': 24000,
            'sample_frames': cursor, 'actual_seconds': cursor / 24000,
            'picture_frames_30fps': math.ceil(cursor / 24000 * 30), 'chapters': chapters,
            'paragraphs': global_paragraphs, 'events': global_events,
            'coordinate_basis': 'Actual PCM sample offsets, then global30fps start-round/end-floor; native source timing retained.',
            'ABC_results': data['review']['ABC_results'], 'ABC_winner': data['review']['ABC_winner'],
            'C_subject_scope': data['subject_scope'], 'source_review': request['source_review'],
            'listening_signoff': False, 'film_signoff': False, 'final_film': False}
        full = pair(output / 'full-global', timeline, p)
        relative_deliveries = {}
        for chapter_id in ['E4-05', 'E4-06']:
            prefix = 'C' + chapter_id.split('-')[1] + '-'
            rows = [row for row in relative if row['paragraph_id'].startswith(prefix)]
            if rows:
                target = output / (chapter_id + '-relative-ROOT-DELIVERY.json')
                write_new(target, {'schema': 'xar.e04.actual-affected-chapter-relative-delivery.v1',
                    'chapter_id': chapter_id, 'paragraphs': rows,
                    'paragraph_count': len(rows), 'actual_only': True, 'film_signoff': False})
                relative_deliveries[chapter_id] = pin(target)
        write_new(output / 'ROOT-DELIVERY.json', {'schema': 'xar.e04.actual-final-subtitle-increment-delivery.v1',
            'status': 'ACTUAL_FINAL_INPUT_BOUND_SUBTITLES_PENDING_VISUAL_AND_LISTENING_REVIEW',
            'source_request': pin(output / 'request-snapshot.json'), 'producer': pin(Path(__file__)),
            'full_global': full, 'chapters': chapters, 'relative_paragraphs': relative,
            'affected_chapter_relative_deliveries': relative_deliveries,
            'changed_ids': data['changed'], 'voice_changed_ids': data['voice_changed'],
            'English_only_ids': data['English_only'], 'C_subject_scope': data['subject_scope'],
            'paragraphs': 69, 'subtitle_pairs': len(global_events),
            'actual_PCM_samples': cursor, 'actual_seconds': cursor / 24000,
            'picture_frames_30fps': math.ceil(cursor / 24000 * 30), 'new_rate_flags': rate_flags,
            'unchanged_source_display_audio_relative_timing_reused': True,
            'provider_calls': 0, 'audio_raw_or_movie_hashes': 0, 'film_signoff': False})
        return pin(output / 'ROOT-DELIVERY.json')
    except Exception as error:
        write_new(output / 'FAILURE.json', {'error': type(error).__name__ + ': ' + str(error),
            'partial_assets_retained': True, 'provider_calls': 0, 'no_old_assets_overwritten': True})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['plan', 'validate', 'build']:
        command = sub.add_parser(name)
        command.add_argument('--request', required=True, type=Path)
        command.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    request = read(args.request)
    if args.command == 'plan':
        result = plan(request)
        result['source_request'] = pin(args.request)
        write_new(args.output, result)
        print(json.dumps({'status': result['status'], 'plan': pin(args.output)}, ensure_ascii=False, indent=2))
    elif args.command == 'validate':
        try:
            data = validate(request)
            result = {'status': 'ACTUAL_INPUTS_VALIDATED_NOT_SUBTITLES_BUILT', 'changed_ids': data['changed'],
                      'actual_PCM_samples': data['samples'], 'actual_seconds': data['samples'] / 24000,
                      'actual_new_fragments': data['new_fragment_count'], 'source_request': pin(args.request)}
        except Exception as error:
            write_new(args.output, {'status': 'NOT_READY', 'error': type(error).__name__ + ': ' + str(error),
                                   'no_subtitle_or_media_assets_created': True, 'source_request': pin(args.request)})
            raise
        write_new(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(build(request, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
