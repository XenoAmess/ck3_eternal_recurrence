"""Check actual encoded trailer bytes and create a pending XAR review package."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from xar_promo import probe_and_write_bound_media
from xar_promo.evidence import bind_external_artifact, write_evidence_bundle_v2, write_sampling_plan_v2
from check_audio_continuity import check_audio_continuity


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt-directory', type=Path, required=True)
    parser.add_argument('--movie', type=Path, required=True, help='Check the delivered OneDrive copy after client synchronization.')
    args = parser.parse_args()
    attempt = args.attempt_directory.resolve()
    native_root = attempt / 'native-run'
    run_manifest = native_root / 'run-manifest.json'
    movie = args.movie.resolve(strict=True)
    post = native_root / 'postflight'
    post.mkdir(parents=True, exist_ok=False)
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    assert ffmpeg and ffprobe
    counter = 0

    def command(argv: list[str], label: str) -> subprocess.CompletedProcess[bytes]:
        nonlocal counter
        counter += 1
        result = subprocess.run(argv, capture_output=True)
        prefix = post / f'{counter:02d}-{label}'
        prefix.with_suffix('.stdout.txt').write_bytes(result.stdout)
        prefix.with_suffix('.stderr.txt').write_bytes(result.stderr)
        prefix.with_suffix('.command.json').write_text(json.dumps({'argv': argv, 'exit_code': result.returncode}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return result

    envelope = probe_and_write_bound_media(ffprobe, movie, output_path=post / 'final.bound-probe.json', audit_directory=post / 'bound-probe-audit')
    raw_probe = dict(envelope.probe.raw)
    video = [row for row in raw_probe['streams'] if row['codec_type'] == 'video']
    audio = [row for row in raw_probe['streams'] if row['codec_type'] == 'audio']
    duration = float(raw_probe['format']['duration'])
    checks = {
        'duration_in_approved_range': 90 <= duration <= 300,
        'one_video_stream': len(video) == 1,
        'one_audio_stream': len(audio) == 1,
        'resolution_1920_1080': len(video) == 1 and (video[0]['width'], video[0]['height']) == (1920, 1080),
        'h264_yuv420p_30fps': len(video) == 1 and video[0]['codec_name'] == 'h264' and video[0]['pix_fmt'] == 'yuv420p' and Fraction(video[0]['avg_frame_rate']) == 30,
        'aac_48khz_stereo': len(audio) == 1 and audio[0]['codec_name'] == 'aac' and audio[0]['sample_rate'] == '48000' and audio[0]['channels'] == 2,
    }
    decode = command([ffmpeg, '-hide_banner', '-nostdin', '-v', 'error', '-i', str(movie), '-f', 'null', '-'], 'full-decode')
    checks['whole_movie_decodes_without_errors'] = decode.returncode == 0 and not decode.stderr.strip()
    loudness = command([ffmpeg, '-hide_banner', '-nostdin', '-i', str(movie), '-af', 'loudnorm=I=-16:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'], 'encoded-loudness')
    loudness.check_returncode()
    stderr = loudness.stderr.decode('utf-8', errors='replace')
    analysis, _ = json.JSONDecoder().raw_decode(stderr[stderr.rfind('{'):])
    checks['encoded_true_peak_at_most_minus_1_db'] = float(analysis['input_tp']) <= -1
    checks['encoded_loudness_readable_range'] = -19 <= float(analysis['input_i']) <= -13
    run = json.loads(run_manifest.read_bytes())
    artifact = next(row for row in run['artifacts'] if row['id'] == 'deliverable.player-trailer')
    retained_movie = native_root / artifact['path']
    movie_sha = sha(movie)
    checks['deliverable_matches_native_preserved_bytes'] = movie_sha == artifact['sha256'].lower() == sha(retained_movie)
    inputs_artifact = next(row for row in run['artifacts'] if row['id'] == 'render.inputs')
    inputs = json.loads((native_root / inputs_artifact['path']).read_bytes())
    narration = json.loads(Path(inputs['narration_summary']['path']).read_bytes())
    checks['requested_voice_and_ten_real_narrations'] = narration['voice'] == 'zh-CN-XiaoxiaoNeural' and narration['successful_scenes'] == 10
    checks['single_music_source'] = inputs['music']['sha256'] == sha(Path(inputs['music']['path']))
    layout_path = attempt / 'build/subtitle-layout-report.json'
    checks['actual_subtitle_layout_report_exists'] = layout_path.is_file()
    layout = json.loads(layout_path.read_bytes())
    paragraphs = [event for events in layout['scenes'].values() for event in events]
    expected_text = {scene['scene_id']: scene['narration'] for scene in narration['scenes']}
    checks['ten_scenes_ten_continuous_paragraphs'] = layout.get('subtitle_policy') == 'one-complete-paragraph-per-scene' and layout.get('cue_count') == 10 and len(paragraphs) == 10 and all(len(events) == 1 for events in layout['scenes'].values())
    checks['paragraph_text_complete_and_unchanged'] = all(event['narration_text'] == expected_text[event['scene_id']] == ''.join(event['lines']) for event in paragraphs)
    checks['paragraphs_fit_two_lines_and_safe_width'] = all(len(event['lines']) <= 2 and max(event['widths_px']) <= 1460 for event in paragraphs)
    narration_duration = {scene['scene_id']: scene['duration_seconds'] for scene in narration['scenes']}
    checks['paragraph_stays_through_full_narration'] = all(event['end_seconds'] - event['start_seconds'] >= narration_duration[event['scene_id']] for event in paragraphs)
    timeline = json.loads((attempt / 'build/timeline.json').read_bytes())
    early_source_paths = [Path(scene['visual']['background']['source_path']) for scene in timeline['scenes'][:5]]
    early_source_hashes = [sha(path) for path in early_source_paths]
    checks['first_five_scenes_have_at_least_four_independent_sources'] = len(set(early_source_hashes)) >= 4
    audio_continuity = check_audio_continuity(movie, attempt, post / 'audio-continuity')
    checks.update({'audio.' + key: value for key, value in audio_continuity['checks'].items()})
    report = {'format_version': 1, 'kind': 'superman_qiang_encoded_media_check', 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'result': 'PASS' if all(checks.values()) else 'FAIL', 'movie_path': str(movie), 'movie_sha256': movie_sha, 'movie_bytes': movie.stat().st_size, 'duration_seconds': duration, 'checks': checks, 'encoded_loudness': analysis, 'subtitle_layout_path': str(layout_path), 'subtitle_layout_sha256': sha(layout_path) if layout_path.is_file() else None, 'subtitle_cue_count': len(paragraphs), 'first_five_source_bindings': [{'path': str(path), 'sha256': value} for path, value in zip(early_source_paths, early_source_hashes)], 'human_full_playback': 'not-recorded', 'manual_signoff_granted': False}
    report_path = post / 'encoded-media-check.json'
    report['audio_continuity_report_path'] = audio_continuity['report_path']
    report['audio_continuity_report_sha256'] = audio_continuity['report_sha256']
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not all(checks.values()):
        print(json.dumps(report, ensure_ascii=False))
        return 2

    cli = [sys.executable, '-X', 'utf8', '-m', 'xar_promo']
    review_args = cli + ['review', str(movie), '--storyboard', str(attempt / 'build/storyboard.json'), '--probe', str(post / 'final.bound-probe.json'), '--output-directory', str(post / 'review'), '--audit-directory', str(post / 'review-audit'), '--ffmpeg', ffmpeg]
    command(review_args + ['--plan-only'], 'review-plan').check_returncode()
    command(review_args, 'review-materialize').check_returncode()
    frame_producer = {'adapter_id': 'superman-qiang-prepared-stills', 'tool': 'ffmpeg', 'tool_version': '9.0.1', 'operation': 'encode-player-trailer', 'execution': 'external'}
    media_producer = {'adapter_id': 'superman-qiang-prepared-stills', 'tool': 'ffmpeg', 'tool_version': '9.0.1', 'operation': 'decode-and-loudness-check', 'execution': 'external'}
    source = bind_external_artifact(retained_movie, project_root=native_root, artifact_id='deliverable.player-trailer', collection='derived', role='deliverable', label='Exact encoded player trailer', media_type='video/mp4', producer=frame_producer)
    plan_path = post / 'media-evidence-plan.json'
    plan = write_sampling_plan_v2(plan_path, [{'id': 'complete-trailer', 'kind': 'video', 'source': source, 'start_seconds': '0.000000', 'end_seconds': f'{duration:.6f}'}], project_root=native_root, interval_seconds='999.000000', required_roles=['media-check'], external_producers={'media-check': media_producer})
    bundle_path = post / 'media-evidence-bundle.json'
    write_evidence_bundle_v2(bundle_path, project_root=native_root, plan_path=plan_path, submissions=[{'sample_id': sample['id'], 'role': 'media-check', 'path': report_path, 'media_type': 'application/json', 'producer': media_producer} for sample in plan['samples']])
    audit = command(cli + ['audit', str(run_manifest), '--subject-artifact-id', 'deliverable.player-trailer', '--evidence-bundle', str(bundle_path), '--report', str(post / 'automated-audit.json'), '--report-artifact-id', 'audit.encoded-media'], 'native-audit')
    audit.check_returncode()
    print(json.dumps({'result': report['result'], 'movie_path': str(movie), 'duration_seconds': duration, 'movie_sha256': movie_sha, 'loudness_lufs': analysis['input_i'], 'true_peak_dbfs': analysis['input_tp'], 'review_package': str(post / 'review/review-package.json'), 'native_audit': str(post / 'automated-audit.json'), 'manual_signoff': 'not-recorded'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
