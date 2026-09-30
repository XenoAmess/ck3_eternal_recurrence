"""Preserve a05 and rebuild only chunks with confirmed evidence-label fixes.

This project composer creates a new native run and retains all inputs and
outputs. Narration, bilingual subtitles, timing, raw shots and AAC remain exact.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import importlib.metadata
import json
import mimetypes
import shutil
import sys
from pathlib import Path

import compose_review_boards_a04 as boards
import review_story_a04 as producer
from war_ai_promo import series_palette

ROOT = Path(__file__).resolve().parent
PREVIOUS = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-20261001-a01')
A04 = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04')
OLD_NAME = 'CK3-War-AI-Episode02-BrownGold-20261001-a05.mp4'
OLD_SHA = 'DE3471E6B14246A9D606C35DB72750D5910074CA9B53C1943CF44AF29D7222E4'
OLD_BYTES = 239565059
A04_NAME = 'CK3-War-AI-Episode02-Review-20260930-a04.mp4'
A04_SHA = 'CB141C63966D86BDC8E267B4D958A79C1BB06A8EF69814DC0D6788F0345B8C7E'
NEW_NAME = 'CK3-War-AI-Episode02-BrownGold-Evidence-20261001-a06.mp4'
CARD_TARGETS = ['pursuit-p028', 'reinforcement-r038']
RAW_INSETS = {
    'knights-k035': {
        'source_path': 'D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv',
        'source_dimensions': [2560, 1440],
        'crop_xywh': [1070, 1008, 422, 111],
        'output_dimensions': [844, 222], 'output_xy': [1010, 140],
        'visible_duration_seconds': 2.5, 'source_pts_interval': [233.0, 235.5],
        'scope': 'Same displayed death notice enlarged; 12/30 UI retained; no d27-state claim',
    },
}
TARGETS = [*CARD_TARGETS, *RAW_INSETS]
LABEL = 'A01真实UI｜12月15日｜我方827／敌方4106'
SPEC_PATH = ROOT / 'project/review-story-a04-board-specs-v2.json'
EDIT_PATH = ROOT / 'project/review-story-a04-edit-v2.json'
CATALOG_PATH = ROOT / 'project/review-story-a04-v2.json'


def chunk_mapping(timeline: dict) -> list[dict]:
    mapping = []
    for chapter in timeline['chapters']:
        receipts = producer.read(PREVIOUS / 'chapters' / chapter['id'] / 'chunk-receipts.json')
        items = chapter['utterances']
        if len(receipts) != (len(items) + 7) // 8:
            raise ValueError(f"a05 chunk coverage differs: {chapter['id']}")
        for index, begin in enumerate(range(0, len(items), 8), 1):
            group = items[begin:begin+8]
            old = receipts[index-1]
            mapping.append({
                'chapter': chapter['id'], 'chunk_index': index,
                'keys': [utterance['key'] for utterance in group],
                'duration_expected': sum(utterance['duration'] for utterance in group),
                'global_start': group[0]['global_start'],
                'local_start': group[0]['local_start'],
                'previous_receipt': old,
                'affected_keys': [utterance['key'] for utterance in group if utterance['key'] in TARGETS],
            })
    return mapping


def inspect() -> None:
    specs = producer.read(SPEC_PATH)
    edit = producer.read(EDIT_PATH)
    timeline = producer.read(PREVIOUS / 'timeline.json')
    mapping = chunk_mapping(timeline)
    print(json.dumps({
        'spec_top': [key for key in specs if key != 'utterances'],
        'edit_top': [key for key in edit if key != 'utterances'],
        'targets': {key: {'spec': specs['utterances'][key], 'edit': edit['utterances'][key]} for key in TARGETS},
        'chunks': len(mapping), 'affected_chunks': [row for row in mapping if row['affected_keys']],
    }, ensure_ascii=False, indent=2))


def assert_previous() -> dict:
    identity = producer.ref(PREVIOUS / OLD_NAME)
    if identity['sha256'] != OLD_SHA or identity['bytes'] != OLD_BYTES:
        raise ValueError('a05 identity differs from the preserved review')
    return identity


def allowed_spec(old: dict, key: str) -> dict:
    result = copy.deepcopy(old)
    if key == 'reinforcement-r038':
        result['ui_label'] = LABEL
    elif key == 'pursuit-p028':
        if sum(line.count('↔') for line in result['diagram_lines']) != 4:
            raise ValueError('expected four affected pursuit glyphs')
        result['diagram_lines'] = [line.replace('↔', '对应') for line in result['diagram_lines']]
    return result


def locator_diff(old: object, current: object, path: tuple = ()) -> list[dict]:
    """Allow only the repaired source locators within fact records."""
    if old == current:
        return []
    if path and path[-1] in {'source_path', 'source_field_or_line'} and 'facts' in path:
        return [{'path': list(path), 'old': old, 'new': current}]
    if isinstance(old, dict) and isinstance(current, dict) and old.keys() == current.keys():
        return [change for key in old for change in locator_diff(old[key], current[key], (*path, key))]
    if isinstance(old, list) and isinstance(current, list) and len(old) == len(current):
        return [change for index, (previous, revised) in enumerate(zip(old, current))
                for change in locator_diff(previous, revised, (*path, index))]
    raise ValueError(f'claim catalog differs beyond repaired fact source locators: {path}')


def catalog_preflight() -> None:
    changes = locator_diff(producer.read(PREVIOUS / 'sources/story.json'), producer.read(CATALOG_PATH))
    print(json.dumps({'comparison_basis': 'a05 frozen story',
                     'changed_fields': len(changes),
                     'changed_fact_count': len({tuple(change['path'][:-1]) for change in changes}),
                     'source': producer.ref(CATALOG_PATH)}, ensure_ascii=False))


def prepare(run: Path) -> None:
    if run.exists():
        raise FileExistsError(run)
    previous_identity = assert_previous()
    run.mkdir(parents=True, exist_ok=False)
    for name in ['sources', 'logs', 'boards', 'audit']:
        (run / name).mkdir()
    latest_path = producer.command(run, 'latest-release-gh', [
        'gh', 'release', 'view', '--repo', 'XenoAmess/xar_promo_toolchain',
        '--json', 'tagName,name,publishedAt,url,assets,isDraft,isPrerelease'])
    latest = producer.read(latest_path)
    installed = importlib.metadata.version('xar-promo-toolchain')
    if latest['isDraft'] or latest['isPrerelease'] or latest['tagName'].lstrip('v') != installed:
        raise ValueError('main venv must use latest formal xar-promo wheel')
    wheel = next(asset for asset in latest['assets'] if asset['name'].endswith('.whl'))
    previous_environment = producer.read(PREVIOUS / 'sources/environment.json')
    wheel_ref = producer.ref(previous_environment['wheel']['path'])
    if wheel_ref['sha256'] != wheel['digest'].split(':')[-1].upper():
        raise ValueError('retained wheel differs from current formal release')
    producer.write(run / 'release-query.json', {'at_utc': producer.stamp(), 'release': latest})
    head_path = producer.command(run, 'local-source-head', ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'])
    producer.write(run / 'sources/environment.json', {
        'at_utc': producer.stamp(), 'python': sys.executable, 'python_version': sys.version,
        'promo_version': installed, 'wheel': wheel_ref,
        'pillow_version': importlib.metadata.version('Pillow'),
        'edge_tts_version': importlib.metadata.version('edge-tts'),
        'ffmpeg': str(producer.FFMPEG), 'ffprobe': str(producer.FFPROBE),
        'source_base': previous_environment['source_base'],
        'local_source_head': head_path.read_text(encoding='utf-8').strip(),
        'branch': previous_environment['branch'], 'main_venv_explicitly_selected': True,
        'no_game_or_desktop': True,
    })
    config = producer.read(PREVIOUS / 'project-config.json')
    config['project']['id'] = 'ck3-war-ai-episode02-brown-gold-evidence-a06'
    config['project']['title'] = '战斗后半笔账：棕金包装与已核实图卡更正'
    producer.write(run / 'project-config.json', config)
    for name, arguments in [('version', ['--version']), ('help', ['--help']),
                            ('start-help', ['start-run', '--help']),
                            ('preserve-help', ['preserve', '--help']),
                            ('validate-help', ['validate', '--help'])]:
        producer.command(run, 'toolchain-' + name, [sys.executable, '-X', 'utf8', '-m', 'xar_promo', *arguments])
    producer.command(run, 'ffmpeg-version', [str(producer.FFMPEG), '-version'])
    producer.command(run, 'ffprobe-version', [str(producer.FFPROBE), '-version'])
    producer.command(run, 'start-run', [sys.executable, '-X', 'utf8', '-m', 'xar_promo', 'start-run',
                     str(run / 'project-config.json'), '--run-id', run.name,
                     '--run-directory', str(run / 'native-run')])
    producer.command(run, 'validate-config', [sys.executable, '-X', 'utf8', '-m', 'xar_promo',
                     'validate', str(run / 'project-config.json')])
    sources = [Path(__file__), Path(boards.__file__), Path(producer.__file__),
               Path(series_palette.__file__), ROOT / 'recolor_series_a05.py',
               SPEC_PATH, EDIT_PATH, ROOT / 'project/review-story-a04-v2.json',
               ROOT / 'evidence-a04-audit-20261001/locator-corrections.json']
    frozen_sources = []
    for source in sources:
        shutil.copyfile(source, run / 'sources' / source.name)
        frozen_sources.append(producer.ref(source))
    for source, name in [(PREVIOUS / 'timeline.json', 'timeline.json'),
                         (PREVIOUS / 'sources/story.json', 'sources/story.json'),
                         (PREVIOUS / 'edit.json', 'sources/a05-edit.json'),
                         (PREVIOUS / 'input-freeze.json', 'sources/a05-input-freeze.json'),
                         (PREVIOUS / 'final-brown-gold-artifact.json', 'sources/a05-final-artifact.json')]:
        shutil.copyfile(source, run / name)
    shutil.copyfile(CATALOG_PATH, run / 'claim-catalog.json')
    catalog = producer.read(run / 'claim-catalog.json')
    prior_story = producer.read(PREVIOUS / 'sources/story.json')
    locator_changes = locator_diff(prior_story, catalog)
    for change in locator_changes:
        path = change['path']
        chapter, utterance = path[1], path[3]
        change['utterance_key'] = catalog['chapters'][chapter]['id'] + '-' + catalog['chapters'][chapter]['utterances'][utterance]['id']
    producer.write(run / 'locator-diff.json', {
        'comparison_basis': 'a05 frozen narration story versus repaired checked-in claim catalog',
        'previous_story': producer.ref(PREVIOUS / 'sources/story.json'),
        'current_catalog': producer.ref(run / 'claim-catalog.json'),
        'checked_in_source': producer.ref(CATALOG_PATH),
        'changes': locator_changes,
        'changed_fact_count': len({tuple(change['path'][:-1]) for change in locator_changes}),
        'zh_en_visual_chapters_and_other_fields_unchanged': True,
    })
    producer.write(run / 'input-freeze.json', {
        'at_utc': producer.stamp(), 'previous': previous_identity,
        'sources': frozen_sources, 'previous_edit': producer.ref(PREVIOUS / 'edit.json'),
        'timeline': producer.ref(PREVIOUS / 'timeline.json'),
        'story': producer.ref(PREVIOUS / 'sources/story.json'), 'wheel': wheel_ref,
        'current_claim_catalog': producer.ref(run / 'claim-catalog.json'),
    })
    old_edit = producer.read(PREVIOUS / 'edit.json')
    specs = producer.read(SPEC_PATH)['utterances']
    source_edit = producer.read(EDIT_PATH)['utterances']
    if set(specs) != set(old_edit['utterances']) or set(source_edit) != set(specs):
        raise ValueError('source utterance coverage differs from a05')
    new_edit = copy.deepcopy(old_edit)
    changed_specs = []
    pixel_checks = []
    from PIL import Image, ImageChops, ImageDraw
    for key, shot in old_edit['utterances'].items():
        if shot['kind'] == 'raw-excerpt':
            if source_edit[key] != shot:
                raise ValueError(f'raw source edit differs from a05: {key}')
            if key in RAW_INSETS:
                inset = RAW_INSETS[key]
                if Path(shot['image']).resolve() != Path(inset['source_path']).resolve():
                    raise ValueError('notice inset must use the exact original raw excerpt')
                if Path(shot['image']).stat().st_size != shot['source_binding']['bytes']:
                    raise ValueError('notice source size differs from its frozen raw receipt')
                raw_probe = producer.probe(run, 'raw-notice-source-probe', Path(shot['image']))
                video = next(stream for stream in raw_probe['streams'] if stream['codec_type'] == 'video')
                if [video['width'], video['height']] != inset['source_dimensions']:
                    raise ValueError('confirmed notice crop dimensions differ from raw media')
                x, y, width, height = inset['crop_xywh']
                if x < 0 or y < 0 or x + width > video['width'] or y + height > video['height']:
                    raise ValueError('notice crop is outside raw source dimensions')
                new_edit['utterances'][key]['raw_notice_inset'] = copy.deepcopy(inset)
            continue
        expected = allowed_spec(shot['spec'], key)
        if expected != specs[key] or expected != source_edit[key]['spec']:
            raise ValueError(f'changes exceed the confirmed card fields: {key}')
        if key not in CARD_TARGETS:
            continue
        if producer.ref(shot['source_binding']['path']) != shot['source_binding']:
            raise ValueError(f'exact original UI source changed: {key}')
        fresh = boards.board(run / 'boards', key, expected)
        new_edit['utterances'][key] = fresh
        with Image.open(shot['image']) as old_opened, Image.open(fresh['image']) as new_opened:
            delta = ImageChops.difference(old_opened.convert('RGB'), new_opened.convert('RGB'))
            bbox = delta.getbbox()
            allowed = (40, 164, 970, 207) if key == 'reinforcement-r038' else (1035, 275, 1855, 565)
            ImageDraw.Draw(delta).rectangle(allowed, fill=(0, 0, 0))
            if delta.getbbox():
                raise ValueError(f'pixels changed outside the corrected diagram/label: {key}')
        if not bbox:
            raise ValueError(f'expected authored label pixels did not change: {key}')
        pixel_checks.append({'key': key, 'difference_bbox': bbox,
                             'allowed_text_rectangle': allowed,
                             'all_other_pixels_identical': True,
                             'original_board': producer.ref(shot['image']),
                             'corrected_board': fresh['rendered_image']})
        changed_specs.append({'key': key, 'old_spec': shot['spec'], 'new_spec': expected,
                              'extra_ui_unchanged': shot['spec'].get('extra_ui') == expected.get('extra_ui')})
    if {row['key'] for row in changed_specs} != set(CARD_TARGETS):
        raise ValueError('both confirmed card corrections must be regenerated')
    timeline = producer.read(run / 'timeline.json')
    mapping = chunk_mapping(timeline)
    producer.write(run / 'edit.json', new_edit)
    producer.write(run / 'chunk-plan.json', mapping)
    producer.write(run / 'card-pixel-checks.json', pixel_checks)
    producer.write(run / 'card-spec-diff.json', changed_specs)
    producer.write(run / 'raw-inset-plan.json', RAW_INSETS)
    producer.write(run / 'edit-input-freeze.json', {
        'edit': producer.ref(run / 'edit.json'),
        'images': [producer.ref(path) for path in sorted({Path(shot['image']) for shot in new_edit['utterances'].values() if shot['kind'] != 'raw-excerpt'})],
        'raw_frozen_receipts': [shot['source_binding'] for shot in new_edit['utterances'].values() if shot['kind'] == 'raw-excerpt'],
        'timeline_audio': [{key: utterance[key] for key in ['key', 'audio', 'tts_raw', 'tts_trimmed']} for chapter in timeline['chapters'] for utterance in chapter['utterances']],
    })
    producer.write(run / 'revision-intent.json', {
        'previous': previous_identity, 'output_name': NEW_NAME, 'target_keys': TARGETS,
        'chunk_count': len(mapping),
        'affected_chunks': [row for row in mapping if row['affected_keys']],
        'unchanged_chunks': sum(not row['affected_keys'] for row in mapping),
        'unchanged_utterances': len(old_edit['utterances'])-len(TARGETS),
        'narration_subtitles_timing_and_original_ui_sources_unchanged': True,
        'raw_notice_inset': RAW_INSETS,
        'timeline_role': 'Exact a05 narration, subtitle and audio timing input; old fact locators retained as historical bytes',
        'claim_source_of_truth': {'catalog': producer.ref(run / 'claim-catalog.json'),
                                 'locator_audit': producer.ref(run / 'locator-diff.json')},
        'human_signoff': 'not-provided', 'production_clean_admission': False,
    })
    print(json.dumps({'phase': 'prepared', 'run': str(run), 'chunks': len(mapping),
                     'affected_chunks': [(row['chapter'], row['chunk_index']) for row in mapping if row['affected_keys']]}))


def render_chunk_with_notice(run: Path, chapter: dict, edit: dict, items: list[dict], index: int) -> dict:
    """Use the producer's composition policy with only the confirmed raw inset.

    The shared renderer source is unchanged. Its still, subtitle, audio and
    encoding policy stays exact; a local raw-filter override splits k035's same
    source frame into the full overview and an enlarged notification crop.
    """
    from xar_promo.render import ass_burn_in_filter
    cid = chapter['id']
    root = run / 'chapters' / cid / f'chunk-{index:02d}'
    root.mkdir(parents=True, exist_ok=False)
    offset = items[0]['local_start']
    duration = sum(utterance['duration'] for utterance in items)
    local = [{**utterance, 'local_start': utterance['local_start']-offset} for utterance in items]
    subtitles = root / 'subtitles.ass'
    producer.text_once(subtitles, producer.subtitles({**chapter, 'utterances': local}, edit))
    argv = [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n']
    filters = []
    overrides = []
    for number, utterance in enumerate(local):
        shot = edit['utterances'][utterance['key']]
        visual = Path(shot['image'])
        length = utterance['duration']
        if shot.get('kind') == 'raw-excerpt':
            argv += ['-threads', '1', '-ss', str(shot['start']), '-t', str(min(length, shot['source_duration'])), '-i', str(visual)]
            packaging = f'scale=1920:900:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:0:color=0x{series_palette.BG[1:]},drawbox=x=0:y=900:w=iw:h=2:color=0x{series_palette.GOLD[1:]}:t=fill,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration={length},trim=duration={length},format=yuv420p'
            inset = shot.get('raw_notice_inset')
            if inset:
                if utterance['key'] not in RAW_INSETS or inset != RAW_INSETS[utterance['key']]:
                    raise ValueError('raw inset differs from the frozen confirmed mapping')
                x, y, width, height = inset['crop_xywh']
                output_width, output_height = inset['output_dimensions']
                output_x, output_y = inset['output_xy']
                enable = f"lt(t,{inset['visible_duration_seconds']})"
                filters.append(f'[{number}:v]setpts=PTS-STARTPTS,split=2[rawmain{number}][rawnotice{number}]')
                filters.append(f'[rawmain{number}]{packaging}[base{number}]')
                filters.append(f'[rawnotice{number}]crop={width}:{height}:{x}:{y}:exact=1,scale={output_width}:{output_height}:flags=lanczos,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration={length},trim=duration={length},format=yuv420p[notice{number}]')
                filters.append(f"[base{number}][notice{number}]overlay=x={output_x}:y={output_y}:eof_action=repeat:shortest=0:enable='{enable}',drawbox=x={output_x}:y={output_y}:w={output_width}:h={output_height}:color=0x{series_palette.GOLD[1:]}:t=2:enable='{enable}',trim=duration={length},format=yuv420p[v{number}]")
                overrides.append({'key': utterance['key'], 'source_binding': shot['source_binding'], 'start': shot['start'], 'source_duration': shot['source_duration'], 'duration': length, 'inset': inset})
            else:
                filters.append(f'[{number}:v]setpts=PTS-STARTPTS,{packaging}[v{number}]')
        else:
            argv += ['-threads', '1', '-loop', '1', '-framerate', '30', '-t', str(length), '-i', str(visual)]
            filters.append(f'[{number}:v]trim=duration={length},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v{number}]')
    for utterance in local:
        argv += ['-i', utterance['audio']]
    count = len(local)
    filters.append(''.join(f'[v{number}]' for number in range(count)) + f'concat=n={count}:v=1:a=0,' + ass_burn_in_filter(subtitles) + '[video]')
    for number, utterance in enumerate(local):
        filters.append(f'[{count+number}:a]apad,atrim=duration={utterance["duration"]},asetpts=PTS-STARTPTS[a{number}]')
    filters.append(''.join(f'[a{number}]' for number in range(count)) + f'concat=n={count}:v=0:a=1[audio]')
    graph = root / 'filter.txt'
    producer.text_once(graph, ';\n'.join(filters))
    producer.write(root / 'raw-filter-overrides.json', overrides)
    output = root / 'chunk.mp4'
    argv += ['-filter_complex_threads', '2', '-/filter_complex', str(graph), '-map', '[video]', '-map', '[audio]', '-t', str(duration), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '22', '-threads', '3', '-r', '30', '-fps_mode', 'cfr', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', str(output)]
    producer.command(run, f'{cid}-chunk-{index:02d}-render', argv)
    return {**producer.ref(output), 'duration_expected': duration}


def render(run: Path) -> None:
    assert_previous()
    timeline = producer.read(run / 'timeline.json')
    edit = producer.read(run / 'edit.json')
    mapping = producer.read(run / 'chunk-plan.json')
    chapter_by_id = {chapter['id']: chapter for chapter in timeline['chapters']}
    receipts = {}
    (run / 'sources/a05-process').mkdir()
    for row in mapping:
        cid, index = row['chapter'], row['chunk_index']
        previous_root = PREVIOUS / 'chapters' / cid / f'chunk-{index:02d}'
        expected = row['previous_receipt']
        if producer.ref(previous_root / 'chunk.mp4') != {key: expected[key] for key in ['path', 'bytes', 'sha256']}:
            raise ValueError(f'a05 chunk identity differs: {cid}/{index}')
        for path in sorted((PREVIOUS / 'logs').glob(f'{cid}-chunk-{index:02d}-render.*')):
            shutil.copyfile(path, run / 'sources/a05-process' / path.name)
        if not row['affected_keys']:
            target = run / 'chapters' / cid / f'chunk-{index:02d}'
            shutil.copytree(previous_root, target)
            identity = producer.ref(target / 'chunk.mp4')
            if identity['sha256'] != expected['sha256'] or identity['bytes'] != expected['bytes']:
                raise ValueError('exact chunk copy failed')
            receipts[cid, index] = {**identity, 'duration_expected': row['duration_expected']}
    affected = [row for row in mapping if row['affected_keys']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        for row in affected:
            chapter = chapter_by_id[row['chapter']]
            items = [utterance for utterance in chapter['utterances'] if utterance['key'] in row['keys']]
            renderer = render_chunk_with_notice if any(key in RAW_INSETS for key in row['keys']) else producer.render_chunk
            pending[row['chapter'], row['chunk_index']] = pool.submit(renderer, run, chapter, edit, items, row['chunk_index'])
        for key, future in pending.items():
            receipts[key] = future.result()
    chunk_diff = []
    for row in mapping:
        cid, index = row['chapter'], row['chunk_index']
        previous_ass = PREVIOUS / 'chapters' / cid / f'chunk-{index:02d}/subtitles.ass'
        new_ass = run / 'chapters' / cid / f'chunk-{index:02d}/subtitles.ass'
        if previous_ass.read_bytes() != new_ass.read_bytes():
            raise ValueError(f'bilingual subtitle bytes changed: {cid}/{index}')
        chunk_diff.append({**row, 'new_receipt': receipts[cid, index],
                           'action': 'recompiled-confirmed-card-fix' if row['affected_keys'] else 'exact-byte-copy',
                           'chunk_bytes_identical': receipts[cid, index]['sha256'] == row['previous_receipt']['sha256'],
                           'subtitle_bytes_identical': True})
    producer.write(run / 'a05-to-a06-chunk-diff.json', chunk_diff)
    chapter_receipts = []
    for chapter in timeline['chapters']:
        cid = chapter['id']
        root = run / 'chapters' / cid
        chunks = [receipts[row['chapter'], row['chunk_index']] for row in mapping if row['chapter'] == cid]
        producer.write(root / 'chunk-receipts.json', chunks)
        concat = root / 'concat.txt'
        producer.text_once(concat, ''.join("file '" + item['path'].replace(chr(92), '/') + "'\n" + f"duration {item['duration_expected']:.9f}\n" for item in chunks))
        output = root / 'chapter.mp4'
        producer.command(run, cid + '-chapter-join', [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n',
                         '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', '-movflags', '+faststart', str(output)])
        chapter_receipts.append({**producer.ref(output), 'duration_expected': chapter['duration']})
    producer.write(run / 'chapter-render-receipts.json', chapter_receipts)
    concat = run / 'concat.txt'
    producer.text_once(concat, ''.join("file '" + item['path'].replace(chr(92), '/') + "'\n" + f"duration {item['duration_expected']:.9f}\n" for item in chapter_receipts))
    metadata = run / 'chapters.ffmetadata'
    shutil.copyfile(PREVIOUS / 'chapters.ffmetadata', metadata)
    intermediate = run / 'rendered-evidence-with-chunk-audio.mp4'
    producer.command(run, 'final-join', [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n',
                     '-f', 'concat', '-safe', '0', '-i', str(concat), '-f', 'ffmetadata', '-i', str(metadata),
                     '-map', '0', '-map_metadata', '1', '-map_chapters', '1', '-c', 'copy', '-movflags', '+faststart', str(intermediate)])
    original_audio = producer.ref(A04 / A04_NAME)
    if original_audio['sha256'] != A04_SHA:
        raise ValueError('a04 original AAC source changed')
    output = run / NEW_NAME
    producer.command(run, 'final-original-audio-mux', [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n',
                     '-i', str(intermediate), '-i', original_audio['path'], '-map', '0:v:0', '-map', '1:a:0',
                     '-map_metadata', '0', '-map_chapters', '0', '-c', 'copy', '-movflags', '+faststart', str(output)])
    info = producer.probe(run, 'final-probe', output)
    producer.write(run / 'final-probe.json', info)
    identity = producer.ref(output)
    final_report = {**identity, 'duration_expected': timeline['total_duration'],
                   'previous': assert_previous(), 'original_aac_source': original_audio,
                   'recompiled_chunks': len(affected), 'copied_chunks': len(mapping)-len(affected),
                   'timeline_unchanged': producer.sha(run / 'timeline.json') == producer.sha(PREVIOUS / 'timeline.json'),
                   'final_aac_stream_copied': True,
                   'human_signoff': 'not-provided', 'production_clean_admission': False,
                   'status': 'pending-independent-machine-and-frame-review'}
    producer.write(run / 'final-artifact.json', final_report)
    producer.write(run / 'final-brown-gold-artifact.json', final_report)
    producer.write(run / 'a05-to-a06-diff.json', {
        'at_utc': producer.stamp(), 'a05': assert_previous(), 'a06': identity,
        'confirmed_card_changes': producer.read(run / 'card-spec-diff.json'),
        'raw_notice_inset': RAW_INSETS,
        'claim_catalog': producer.ref(run / 'claim-catalog.json'),
        'locator_diff': producer.ref(run / 'locator-diff.json'),
        'card_pixel_checks': producer.read(run / 'card-pixel-checks.json'),
        'chunk_diff': chunk_diff, 'subtitle_bytes_identical_in_all_chunks': True,
        'chapter_metadata_identical': producer.sha(metadata) == producer.sha(PREVIOUS / 'chapters.ffmetadata'),
        'timeline_bytes_identical': producer.sha(run / 'timeline.json') == producer.sha(PREVIOUS / 'timeline.json'),
        'final_aac_stream_copied_from_a04': True, 'narration_or_mix_changed': False,
        'human_signoff': 'not-provided', 'production_clean_admission': False,
    })
    print(json.dumps(identity))


def preserve(run: Path) -> None:
    from xar_promo.operations import preserve_artifact
    from xar_promo.project import load_document
    from xar_promo.runlog import append_phase_record
    manifest = run / 'native-run/run-manifest.json'
    final = producer.read(run / 'final-artifact.json')
    if producer.ref(final['path']) != {key: final[key] for key in ['path', 'bytes', 'sha256']}:
        raise ValueError('final output bytes changed before preservation')
    records = []
    paths = [run / name for name in ['project-config.json', 'revision-intent.json', 'timeline.json',
             'claim-catalog.json', 'locator-diff.json',
             'input-freeze.json', 'edit.json', 'edit-input-freeze.json', 'release-query.json', 'chunk-plan.json',
             'card-pixel-checks.json', 'card-spec-diff.json', 'raw-inset-plan.json', 'a05-to-a06-chunk-diff.json',
             'a05-to-a06-diff.json', 'chapter-render-receipts.json', 'final-artifact.json', 'final-brown-gold-artifact.json', 'final-probe.json']]
    paths.extend(sorted((run / 'sources').rglob('*')))
    paths.extend(sorted((run / 'logs').glob('*.receipt.json')))
    paths.extend(sorted((run / 'chapters').glob('*/chunk-*/subtitles.ass')))
    paths.extend(sorted((run / 'chapters').glob('*/chunk-*/filter.txt')))
    paths.extend(sorted((run / 'chapters').glob('*/chunk-*/raw-filter-overrides.json')))
    paths.extend(sorted((run / 'boards').rglob('*.png')))
    for index, path in enumerate([Path(final['path']), *[path for path in paths if path.is_file()]]):
        record = preserve_artifact(manifest, path, artifact_id='a06-deliverable' if index == 0 else f'a06-retained-{index:03d}',
                                   collection='derived', role='deliverable' if index == 0 else 'process-evidence',
                                   label=path.name, media_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        records.append({'source': producer.ref(path), 'preserved': record.to_dict()})
    process_index = {'at_utc': producer.stamp(), 'subject': final, 'human_signoff': 'not-provided',
                     'production_clean_admission': False,
                     'process_files': [producer.ref(path) for path in sorted(run.rglob('*')) if path.is_file() and 'native-run' not in path.parts]}
    producer.write(run / 'retained-process-index.json', process_index)
    index_record = preserve_artifact(manifest, run / 'retained-process-index.json', artifact_id='a06-process-index',
                                      collection='derived', role='process-index', label='retained-process-index.json', media_type='application/json')
    records.append({'source': producer.ref(run / 'retained-process-index.json'), 'preserved': index_record.to_dict()})
    plan = producer.read(run / 'chunk-plan.json')
    changed = sum(bool(row['affected_keys']) for row in plan)
    append_phase_record(manifest, phase_id='project-confirmed-card-corrections', status='succeeded',
                        artifact_ids=['a06-deliverable'], detail=f'Two confirmed authored-card fixes plus same-frame k035 death-notice inset. {changed} mapped chunks recompiled; {len(plan)-changed} other chunks copied exactly. Original a04 AAC copied. No human signoff or external upload.')
    loaded = load_document(manifest, check_files=True)
    producer.write(run / 'native-preservation-complete.json', {
        'at_utc': producer.stamp(), 'manifest': producer.ref(manifest), 'artifacts': records,
        'human_signoffs': len(loaded.run.signoffs), 'scope': 'Source freezing, declared chunk reuse and process preservation only'})
    producer.command(run, 'validate-preserved-run', [sys.executable, '-X', 'utf8', '-m', 'xar_promo', 'validate', str(manifest)])
    print(json.dumps(producer.ref(run / 'native-preservation-complete.json')))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['inspect', 'catalog-preflight', 'prepare', 'render', 'preserve'])
    parser.add_argument('--run', type=Path)
    args = parser.parse_args()
    if args.phase == 'inspect':
        inspect()
    elif args.phase == 'catalog-preflight':
        catalog_preflight()
    else:
        if args.run is None:
            parser.error('--run is required for prepare/render/preserve')
        existed_before = args.run.exists()
        try:
            {'prepare': prepare, 'render': render, 'preserve': preserve}[args.phase](args.run)
        except Exception as error:
            if args.run.exists() and not (args.phase == 'prepare' and existed_before):
                failure_path = args.run / f'{args.phase}-failure.json'
                if not failure_path.exists():
                    producer.write(failure_path, {
                        'at_utc': producer.stamp(), 'phase': args.phase,
                        'error_type': type(error).__name__, 'error': str(error),
                        'human_signoff': 'not-provided',
                        'retained_process_files': [producer.ref(path) for path in sorted(args.run.rglob('*'))
                                                   if path.is_file() and 'native-run' not in path.parts],
                    })
                    manifest = args.run / 'native-run/run-manifest.json'
                    if manifest.is_file():
                        from xar_promo.runlog import append_phase_record
                        append_phase_record(manifest, phase_id='project-' + args.phase, status='failed',
                                            artifact_ids=[], detail=f'{type(error).__name__}: {error}; all partial outputs and process evidence retained.')
            raise


if __name__ == '__main__':
    main()
