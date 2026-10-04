"""Freeze the approved player trailer's actual inputs in a new native XAR run."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt-directory', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--narration-summary', type=Path, required=True)
    parser.add_argument('--music-receipt', type=Path, required=True)
    parser.add_argument('--reuse-visual-attempt', type=Path, help='Bind an unchanged previous visual stream for an audio-only revision.')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    repo = project.parents[1]
    config = project / 'render-project.json'
    visual_plan_path = project / 'visual-plan.json'
    config_payload = json.loads(config.read_bytes())
    assert len(config_payload['chapters']) == 10
    assert all(chapter['state'] == 'ready' for chapter in config_payload['chapters'])
    visual_plan = json.loads(visual_plan_path.read_bytes())
    narration_path = args.narration_summary.resolve()
    narration = json.loads(narration_path.read_bytes())
    assert narration['successful_scenes'] == 10
    assert narration['voice'] == 'zh-CN-XiaoxiaoNeural'
    receipt_path = args.music_receipt.resolve()
    receipt = json.loads(receipt_path.read_bytes())
    music_path = Path(receipt['music_path'])
    assert digest(music_path) == receipt['music_sha256']
    attempt = args.attempt_directory.resolve()
    attempt.mkdir(parents=True, exist_ok=False)
    commands = attempt / 'orchestration-commands'
    commands.mkdir()
    cli = [sys.executable, '-X', 'utf8', '-m', 'xar_promo']
    counter = 0

    def command(argv: list[str], label: str) -> bytes:
        nonlocal counter
        counter += 1
        result = subprocess.run(argv, cwd=repo, capture_output=True)
        prefix = commands / f'{counter:03d}-{label}'
        prefix.with_suffix('.stdout.txt').write_bytes(result.stdout)
        prefix.with_suffix('.stderr.txt').write_bytes(result.stderr)
        prefix.with_suffix('.command.json').write_text(json.dumps({'argv': argv, 'cwd': str(repo), 'exit_code': result.returncode}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result.check_returncode()
        return result.stdout

    latest = json.loads(command(['gh', 'api', 'repos/XenoAmess/xar_promo_toolchain/releases/latest'], 'latest-release'))
    wheels = [asset for asset in latest['assets'] if asset['name'].endswith('.whl')]
    assert not latest['draft'] and not latest['prerelease'] and len(wheels) == 1
    distribution = metadata.distribution('xar-promo-toolchain')
    direct_url = json.loads(distribution.read_text('direct_url.json'))
    wheel_sha = wheels[0]['digest'].removeprefix('sha256:')
    assert latest['tag_name'] == 'v' + distribution.version
    assert direct_url['url'] == wheels[0]['browser_download_url']
    assert direct_url['archive_info']['hashes']['sha256'] == wheel_sha
    framework = {'queried_at_utc': datetime.now(timezone.utc).isoformat(), 'release_tag': latest['tag_name'], 'release_id': latest['id'], 'wheel_sha256': wheel_sha, 'wheel_url': wheels[0]['browser_download_url'], 'python': sys.executable, 'python_version': sys.version, 'package_version': distribution.version, 'source_head': command(['git', 'rev-parse', 'HEAD'], 'source-head').decode().strip()}
    framework_path = attempt / 'framework-version.json'
    framework_path.write_text(json.dumps(framework, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, flags in [('version', ['--version']), ('help', ['--help']), ('start-run-help', ['start-run', '--help']), ('plan-help', ['plan', '--help']), ('build-help', ['build', '--help']), ('preserve-help', ['preserve', '--help'])]:
        command(cli + flags, label)
    command(cli + ['validate', str(config), '--json'], 'validate-config')
    run_directory = attempt / 'native-run'
    command(cli + ['start-run', str(config), '--run-id', args.run_id, '--run-directory', str(run_directory)], 'start-run')
    run_manifest = run_directory / 'run-manifest.json'

    def preserve(path: Path, artifact_id: str, role: str, collection: str = 'raw') -> None:
        command(cli + ['preserve', str(path), '--run-manifest', str(run_manifest), '--artifact-id', artifact_id, '--collection', collection, '--role', role], 'preserve-' + artifact_id)

    visual_root = Path(visual_plan['work_directory'])
    sources: set[Path] = set(visual_root.rglob('*.png'))
    for scene in visual_plan['scenes']:
        if scene.get('background', {}).get('source_path'):
            sources.add(Path(scene['background']['source_path']))
    for relative in ['mod_superman_qiang/thumbnail.png', 'workshop/superman_qiang_media/v3/01_absorption.jpg', 'workshop/superman_qiang_media/v2/04_natural_event.jpg', 'workshop/superman_qiang_media/v3/05_notification.jpg', 'workshop/superman_qiang_media/v3/05_notification.raw.png']:
        sources.add(repo / relative)
    font = Path('C:/Windows/Fonts/msyh.ttc')
    sources.add(font)
    for row in narration['scenes']:
        for field in ['audio_path', 'boundaries_path', 'request_path']:
            sources.add(Path(row[field]))
    inputs = {'format_version': 1, 'kind': 'superman_qiang_render_inputs', 'narration_summary': {'path': str(narration_path), 'sha256': digest(narration_path)}, 'visual_plan': {'path': str(visual_plan_path), 'sha256': digest(visual_plan_path)}, 'visual_root': str(visual_root), 'music': {'path': str(music_path), 'sha256': digest(music_path), 'start_seconds': 0, 'duration_seconds': receipt['duration_seconds']}, 'subtitle_font': {'path': str(font), 'family': 'Microsoft YaHei', 'size': 46}, 'frame': {'width': 1920, 'height': 1080, 'fps': 30}, 'duration_policy': {'minimum_seconds': 90, 'maximum_seconds': 300}, 'source_bindings': [{'path': str(path), 'sha256': digest(path)} for path in sorted(sources)]}
    reused_sources = []
    if args.reuse_visual_attempt:
        previous = args.reuse_visual_attempt.resolve(strict=True)
        previous_root = previous / 'native-run'
        previous_run = json.loads((previous_root / 'run-manifest.json').read_bytes())
        old_input = next(row for row in previous_run['artifacts'] if row['id'] == 'render.inputs')
        old_inputs = json.loads((previous_root / old_input['path']).read_bytes())
        assert old_inputs['visual_plan']['sha256'] == digest(visual_plan_path), 'Changed visual plan cannot reuse old video.'
        layout = json.loads((previous / 'build/subtitle-layout-report.json').read_bytes())
        assert layout['subtitle_policy'] == 'one-complete-paragraph-per-scene' and layout['cue_count'] == 10
        for row in narration['scenes']:
            assert layout['scenes'][row['scene_id']][0]['narration_text'] == row['narration']
        movie = previous / 'build/deliverables/superman-qiang-player-trailer.mp4'
        old_movie = next(row for row in previous_run['artifacts'] if row['id'] == 'deliverable.player-trailer')
        assert digest(movie) == old_movie['sha256'].lower()
        timeline = previous / 'build/timeline.json'
        segments = {row['scene_id']: previous / f"build/segments/{index:04d}-{row['scene_id']}.mp4" for index, row in enumerate(narration['scenes'], 1)}
        inputs['reuse_visuals'] = {'movie': {'path': str(movie), 'sha256': digest(movie)}, 'timeline': {'path': str(timeline), 'sha256': digest(timeline)}, 'segments': {key: {'path': str(path), 'sha256': digest(path)} for key, path in segments.items()}}
        reused_sources = [('movie', movie), ('timeline', timeline), *segments.items()]
    inputs_path = attempt / 'render-inputs.json'
    inputs_path.write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    preserve(inputs_path, 'render.inputs', 'render-inputs')
    preserve(music_path, 'music.source', 'music')
    preserve(receipt_path, 'music.receipt', 'music-receipt')
    preserve(narration_path, 'narration.summary', 'narration-summary')
    preserve(visual_plan_path, 'visual.plan', 'visual-plan')
    preserve(framework_path, 'framework.version', 'framework-version')
    for name, path in reused_sources:
        preserve(path, 'visual.reuse.' + name, 'previous-visual-source')
    for row in narration['scenes']:
        scene = row['scene_id']
        preserve(Path(row['audio_path']), 'narration.input.' + scene, 'audio')
        preserve(Path(row['boundaries_path']), 'narration.boundaries.' + scene, 'tts-boundaries')
        preserve(Path(row['request_path']), 'narration.request.' + scene, 'tts-request')
    for row in visual_plan['scenes']:
        preserve(Path(row['overlay_path']), 'visual.overlay.' + row['scene_id'], 'visual-overlay')
    for index, path in enumerate(sorted(sources)):
        if path.suffix == '.mp3' or path.name == 'request.json' or path.name.endswith('.boundaries.jsonl') or path.parent.name == 'overlays' and path.stem in {chapter['id'] for chapter in config_payload['chapters']}:
            continue
        preserve(path, f'source.binding.{index:03d}', 'source-image' if path.suffix.lower() in {'.png', '.jpg'} else 'source-font')
    for name in ['tools/player_trailer_composer.py', 'tools/compose_player_visuals.py', 'tools/prepare_render_run.py', 'tools/check_player_trailer.py', 'tools/check_audio_continuity.py', 'tools/deliver_player_video.py', 'tools/prepare_final_frame_inspection.py', 'tools/retain_render_attempt.py', '02m/director.md', '02m/director.json', 'asset-and-claim-ledger.json', 'production-selection.json', 'visual-revision-20261004.md', 'audio-revision-20261004.md']:
        preserve(project / name, 'project.' + name.replace('/', '.').replace('.py', ''), 'project-source')
    for index, path in enumerate(sorted((project / 'images/revision-20261004').glob('*.json'))):
        preserve(path, f'project.imagegen-request-and-receipt.{index:03d}', 'source-imagegen-metadata')
    for index, path in enumerate(sorted((project / 'plugin').rglob('*'))):
        if path.is_file() and path.suffix in {'.py', '.toml', '.md'}:
            preserve(path, f'project.registration.{index:03d}', 'project-registration-source')
    registration = Path('C:/ck3-superman-qiang-promo-20261004/composer-prep-A0001/registration-A0003')
    preserve(registration / 'wheel/superman_qiang_promo_project-0.1.0-py3-none-any.whl', 'project.registration-wheel', 'project-registration-wheel')
    for name in ['final-source-probe.json']:
        preserve(registration / name, 'project.registration-' + name.replace('.json', ''), 'project-registration-evidence')
    command(cli + ['validate', str(run_manifest), '--json'], 'validate-run')
    result = {'state': 'inputs-preserved', 'run_manifest': str(run_manifest), 'render_inputs': str(inputs_path), 'planned_build_workdir': str(attempt / 'build'), 'framework': framework}
    (attempt / 'preparation-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
