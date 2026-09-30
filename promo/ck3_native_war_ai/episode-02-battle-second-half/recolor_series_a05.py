"""Rebuild a04 packaging with the established series palette in a new run.

Reuse its exact narration, timing, raw shot choices and final AAC packets.
Preserve all source snapshots, outputs, subprocess logs and failed attempts.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import sys
import urllib.request
from pathlib import Path

import compose_review_boards_a04 as boards
import review_story_a04 as producer
from war_ai_promo import series_palette

ROOT = Path(__file__).resolve().parent
PREVIOUS = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04')
OLD_NAME = 'CK3-War-AI-Episode02-Review-20260930-a04.mp4'
NEW_NAME = 'CK3-War-AI-Episode02-BrownGold-20261001-a05.mp4'
OLD_SHA = 'CB141C63966D86BDC8E267B4D958A79C1BB06A8EF69814DC0D6788F0345B8C7E'


def prepare(run: Path) -> None:
    if run.exists():
        raise FileExistsError(run)
    previous_identity = producer.ref(PREVIOUS / OLD_NAME)
    if previous_identity['sha256'] != OLD_SHA or previous_identity['bytes'] != 240710781:
        raise ValueError('a04 final identity differs from the delivered review')
    run.mkdir(parents=True, exist_ok=False)
    for directory in ['sources', 'logs', 'boards', 'audit']:
        (run / directory).mkdir()
    release = json.load(urllib.request.urlopen(urllib.request.Request(
        'https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest',
        headers={'User-Agent': 'ck3-war-series-palette'}), timeout=30))
    wheel = next(asset for asset in release['assets'] if asset['name'].endswith('.whl'))
    installed = importlib.metadata.version('xar-promo-toolchain')
    if release['draft'] or release['prerelease'] or release['tag_name'].lstrip('v') != installed:
        raise ValueError('verified interpreter must use the latest formal wheel')
    old_environment = producer.read(PREVIOUS / 'sources/environment.json')
    wheel_path = Path(old_environment['wheel_local'])
    wheel_ref = producer.ref(wheel_path)
    if wheel_ref['sha256'] != wheel['digest'].split(':')[-1].upper():
        raise ValueError('retained wheel bytes do not match latest formal release')
    producer.write(run / 'release-query.json', {'at_utc': producer.stamp(), 'release': release})
    environment = {
        'at_utc': producer.stamp(), 'python': sys.executable, 'python_version': sys.version,
        'promo_version': installed, 'pillow_version': importlib.metadata.version('Pillow'),
        'edge_tts_version': importlib.metadata.version('edge-tts'),
        'wheel': wheel_ref, 'ffmpeg': str(producer.FFMPEG), 'ffprobe': str(producer.FFPROBE),
        'source_base': 'd81b91be1ae6bf818f38c3c5af0d595dd4ea4752',
        'branch': 'codex/war-series-brown-gold-20261001',
        'main_venv_explicitly_selected': True, 'no_game_or_desktop': True,
    }
    producer.write(run / 'sources/environment.json', environment)
    config = producer.read(ROOT / 'project/review-story-a04-project.json')
    config['project']['id'] = 'ck3-war-ai-episode02-brown-gold-a05'
    config['project']['title'] = '战斗后半笔账：系列棕金配色修订'
    producer.write(run / 'project-config.json', config)
    intent = {'kind': 'series-brown-gold-packaging-revision',
              'previous': previous_identity, 'output_name': NEW_NAME,
              'palette': {key: getattr(series_palette, key) for key in
                          ['BG', 'PANEL', 'INK', 'MUTED', 'GOLD', 'FAINT_RULE', 'HIGHLIGHT']},
              'reference_episodes': ['Episode 0 V5', 'Episode 1 R7F Corrected'],
              'game_pixels_recolored': False, 'narration_or_timing_changed': False,
              'human_signoff': 'not-provided'}
    producer.write(run / 'palette-intent.json', intent)
    sources = [Path(__file__), Path(boards.__file__), Path(producer.__file__),
               Path(series_palette.__file__), ROOT / 'project/review-story-a04-board-specs-v2.json',
               ROOT / 'project/review-story-a04-v2.json',
               ROOT.parent / 'episode-01-battle-win-probability/r7d-brown-gold/visual-style.md']
    frozen = []
    for source in sources:
        shutil.copyfile(source, run / 'sources' / source.name)
        frozen.append(producer.ref(source))
    producer.write(run / 'input-freeze.json', frozen)
    for name, args in [('version', ['--version']), ('help', ['--help']),
                       ('start-help', ['start-run', '--help']),
                       ('preserve-help', ['preserve', '--help']),
                       ('validate-help', ['validate', '--help'])]:
        producer.command(run, 'toolchain-' + name, [sys.executable, '-m', 'xar_promo', *args])
    producer.command(run, 'start-run', [sys.executable, '-m', 'xar_promo', 'start-run',
                     str(run / 'project-config.json'), '--run-id', run.name,
                     '--run-directory', str(run / 'native-run')])
    producer.command(run, 'validate-config', [sys.executable, '-m', 'xar_promo', 'validate',
                     str(run / 'project-config.json')])
    shutil.copyfile(PREVIOUS / 'timeline.json', run / 'timeline.json')
    shutil.copyfile(PREVIOUS / 'sources/story.json', run / 'sources/story.json')
    old_edit = producer.read(PREVIOUS / 'edit.json')
    specification = producer.read(ROOT / 'project/review-story-a04-board-specs-v2.json')['utterances']
    new_edit = {key: value for key, value in old_edit.items() if key != 'utterances'}
    new_edit['utterances'] = {}
    ui_checks = []
    for key, shot in old_edit['utterances'].items():
        if shot['kind'] == 'raw-excerpt':
            new_edit['utterances'][key] = shot
            continue
        if shot['spec'] != specification[key]:
            raise ValueError(f'final corrected source/crop must remain exact: {key}')
        actual_source = producer.ref(shot['source_binding']['path'])
        if actual_source != shot['source_binding']:
            raise ValueError(f'original UI source changed: {key}')
        fresh = boards.board(run / 'boards', key, shot['spec'])
        new_edit['utterances'][key] = fresh
        # Verify the enlarged game pixels directly, apart from packaging.
        from PIL import Image, ImageChops
        old_image = Image.open(shot['image']).convert('RGB')
        new_image = Image.open(fresh['image']).convert('RGB')
        if not shot['spec'].get('extra_ui'):
            # Only the empty margins change to brown. Select the exact pasted crop.
            _, crop = boards.source_crop(shot['spec']['source_image'], shot['spec']['crop_xyxy'])
            scale = min(930 / crop.width, 230 / crop.height)
            width, height = round(crop.width * scale), round(crop.height * scale)
            x, y = 40 + (930 - width) // 2, 580 + (230 - height) // 2
            pasted = (x, y, x + width, y + height)
            if ImageChops.difference(old_image.crop(pasted), new_image.crop(pasted)).getbbox():
                raise ValueError(f'original enlarged UI pixels changed: {key}')
            ui_checks.append({'key': key, 'rect': pasted, 'game_pixels_identical': True})
        old_image.close()
        new_image.close()
    producer.write(run / 'edit-brown-gold.json', new_edit)
    producer.write(run / 'original-ui-pixel-checks.json', ui_checks)
    producer.write(run / 'prepared-edit-input-freeze.json', {
        'previous_edit': producer.ref(PREVIOUS / 'edit.json'),
        'new_edit': producer.ref(run / 'edit-brown-gold.json'),
        'images': [shot['rendered_image'] for shot in new_edit['utterances'].values()
                   if shot['kind'] != 'raw-excerpt'],
        'raw_frozen_receipts': [shot['source_binding'] for shot in new_edit['utterances'].values()
                                if shot['kind'] == 'raw-excerpt'],
        'timeline_origin': producer.ref(PREVIOUS / 'timeline.json'),
    })
    print(json.dumps({'phase': 'prepared', 'run': str(run),
                     'stills': sum(s['kind'] != 'raw-excerpt' for s in new_edit['utterances'].values()),
                     'raw_shots': sum(s['kind'] == 'raw-excerpt' for s in new_edit['utterances'].values())}))


def render(run: Path) -> None:
    producer.render(run, run / 'edit-brown-gold.json', 'rendered-brown-gold-with-chunk-audio.mp4')
    # Deliver the original AAC stream, without another audio encode or mix.
    candidate = run / 'rendered-brown-gold-with-chunk-audio.mp4'
    old_identity = producer.ref(PREVIOUS / OLD_NAME)
    if old_identity['sha256'] != OLD_SHA:
        raise ValueError('retained audio source changed')
    output = run / NEW_NAME
    producer.command(run, 'final-original-audio-mux', [str(producer.FFMPEG),
                     '-hide_banner', '-nostdin', '-n', '-i', str(candidate),
                     '-i', str(PREVIOUS / OLD_NAME), '-map', '0:v:0', '-map', '1:a:0',
                     '-map_metadata', '0', '-map_chapters', '0', '-c', 'copy',
                     '-movflags', '+faststart', str(output)])
    report = {**producer.ref(output), 'previous': old_identity,
              'timeline_unchanged': True, 'final_aac_stream_copied': True,
              'human_signoff': 'not-provided', 'status': 'pending-machine-and-frame-review'}
    producer.write(run / 'final-brown-gold-artifact.json', report)
    print(json.dumps(report))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'render'])
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    (prepare if args.phase == 'prepare' else render)(args.run)


if __name__ == '__main__':
    main()
