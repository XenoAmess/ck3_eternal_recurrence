"""R0180 only: audit one actual finished 45-second recording, after Root handoff.

Minimal adaptation of the completed R0174 media audit. One metadata probe,
one strict whole decode and at most six original-size JPEG samples from that
same decode. No SDK, desktop, recorder, raw re-encode, raw SHA read or signoff.
Preparing this source does not open or attest any future recording.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import argparse, hashlib, json, re, subprocess, sys, time, traceback
from PIL import Image

PREP = Path(__file__).resolve().parent
ASSETS = Path('C:/ck3-e04-resume-20261015-a01/live12004-logistics-next-a09-a01')
EXPECTED_SOURCE = 'c4992c304d196135d9590799d69ffb3c9f5510e6'
EXPECTED_PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
FFTOOLS = Path('C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin')
LIMIT = 8 * 1024 * 1024
RAW_LIMIT = 256 * 1024 * 1024
DEADLINE = datetime.fromisoformat('2026-10-16T07:45:01.597+00:00')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    path = Path(path)
    require(path.suffix.lower() == '.json' and path.is_file() and not path.is_symlink() and path.stat().st_size <= 2_000_000, 'bounded actual JSON required: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(body, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')

def stat(path):
    s = path.stat()
    return {'path': str(path), 'bytes': s.st_size, 'mtime_ns': s.st_mtime_ns}

def pin(path):
    path = Path(path)
    require(path.suffix.lower() in ('.json', '.bin', '.jpg', '.jpeg', '.py', '.md', '.txt', '.patch'), 'raw/media/tool hashes forbidden')
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= LIMIT, 'bounded derived evidence only')
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())

def command(output, label, argv):
    require(datetime.now(timezone.utc) < DEADLINE, 'fixed task deadline reached')
    directory = output / label
    directory.mkdir(exist_ok=False)
    write(directory / 'argv.json', {'argv': argv, 'shell': False, 'codec_filter_threads': 1})
    started = now()
    mono = time.monotonic()
    with (directory / 'stdout.bin').open('xb') as out, (directory / 'stderr.bin').open('xb') as err:
        process = subprocess.Popen(argv, stdout=out, stderr=err)
        write(directory / 'owned-process.json', {'pid': process.pid, 'started_at_utc': started})
        print(json.dumps({'started': label, 'pid': process.pid}), flush=True)
        timed_out = False
        try:
            remaining = (DEADLINE - datetime.now(timezone.utc)).total_seconds()
            rc = process.wait(timeout=max(0.01, min(60.0, remaining)))
        except subprocess.TimeoutExpired:
            timed_out = True
            # This Popen instance belongs only to this audit attempt; never
            # signal a recorder, CK3, SDK, or a reused numeric PID.
            process.terminate()
            try:
                rc = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                rc = process.wait(timeout=5)
    result = {'returncode': rc, 'started_at_utc': started, 'completed_at_utc': now(), 'elapsed_seconds': time.monotonic() - mono,
              'argv': pin(directory / 'argv.json'), 'stdout': pin(directory / 'stdout.bin'), 'stderr': pin(directory / 'stderr.bin'),
              'all_partials_retained': True, 'owned_process_timed_out': timed_out,
              'command_runtime_limit_seconds': 60, 'fixed_deadline_utc': DEADLINE.isoformat()}
    write(directory / 'result.json', result)
    return result

def execute(binding_path):
    require(Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve(), 'explicit verified project interpreter required')
    require(datetime.now(timezone.utc) < DEADLINE, 'original deadline reached; no renewal inferred')
    binding = load(binding_path)
    require(binding.get('schema') == 'xar.e04.R0180-actual-finished-raw-audit-input.v1', 'actual R0180 binding schema required')
    require(binding.get('source_head') == EXPECTED_SOURCE and binding.get('run_id', '').endswith('--R0180'), 'wrong scene/source binding')
    for key in ('raw_path', 'finished_recorder_receipt', 'output_directory'):
        require(isinstance(binding.get(key), str) and binding[key] and Path(binding[key]).is_absolute(), 'actual absolute path required: ' + key)
    raw = Path(binding['raw_path']).resolve(strict=True)
    finish_path = Path(binding['finished_recorder_receipt']).resolve(strict=True)
    output = Path(binding['output_directory']).resolve()
    require(raw.is_relative_to(ASSETS.resolve()) and raw.suffix.lower() == '.mkv' and raw.is_file() and not raw.is_symlink(), 'raw must be the actual owned R0180 MKV')
    require(finish_path.is_relative_to(ASSETS.resolve()), 'actual finish receipt must belong to R0180 assets')
    require(output.is_relative_to(ASSETS.resolve()) and output != ASSETS.resolve() and not output.exists(), 'fresh external R0180 audit output required')
    require(not any(p.is_symlink() for p in output.parents), 'linked output ancestor rejected')
    finish = load(finish_path)
    if 'body' in finish:
        require(finish.get('is_error') is False and finish.get('request', {}).get('tool') == 'gameplay_recorder', 'actual finish response differs')
        closed = finish['body']
    else:
        closed = finish
    require(closed.get('state') == 'NORMAL_TREE_EMPTY' and closed.get('job', {}).get('returncode') == 0 and closed['job'].get('job_active_processes') == 0,
            'actual normally closed recorder Job is required before any media process')
    identity = closed.get('raw')
    require(isinstance(identity, dict) and Path(identity['path']).resolve() == raw, 'finish receipt does not bind the supplied raw')
    expected_bytes = binding['expected_raw_bytes']
    expected_sha = binding['expected_raw_sha256']
    require(type(expected_bytes) is int and 0 < expected_bytes <= RAW_LIMIT and type(expected_sha) is str and re.fullmatch('[0-9a-fA-F]{64}', expected_sha) is not None,
            'actual Root-provided byte count and SHA required; null/template input is forbidden')
    require(identity['bytes'] == expected_bytes and identity['sha256'].lower() == expected_sha.lower() and raw.stat().st_size == expected_bytes, 'raw differs from actual closed identity/stat')
    frames = binding['sample_frame_ordinals']
    require(isinstance(frames, list) and 1 <= len(frames) <= 6 and all(type(n) is int and 0 <= n < 1350 for n in frames) and frames == sorted(set(frames)),
            'one to six ordered distinct actual source frame ordinals in [0,1350) required')
    event_records = []
    for item in binding.get('native_event_receipts', []):
        require(isinstance(item, dict) and isinstance(item.get('label'), str) and item['label'], 'event receipt label required')
        path = Path(item['path']).resolve(strict=True)
        require(path.is_relative_to(ASSETS.resolve()), 'event receipt outside actual R0180 assets')
        body = load(path)
        event_records.append({'label': item['label'], 'file': pin(path), 'actual_top_level_times': {k: body[k] for k in ('at', 'at_utc', 'started_at_utc', 'completed_at_utc') if k in body},
                              'business_qualification_performed_by_media_audit': False})
    require(len(event_records) <= 12, 'bounded event metadata only')
    before = stat(raw)
    output.mkdir(parents=True, exist_ok=False)
    try:
        plan = {'schema': 'xar.e04.R0180-land-arrival-raw-audit-plan.v1', 'at_utc': now(), 'binding': pin(binding_path), 'source_head': EXPECTED_SOURCE,
                'actual_run_id': binding['run_id'], 'raw_identity_reused': identity, 'source_stat_before': before, 'actual_finish_receipt': pin(finish_path),
                'recorder_started_at_utc': closed.get('started_at_utc'), 'actual_native_event_receipts': event_records,
                'event_wall_to_encoded_PTS_relation': 'uncalibrated; selected source frame ordinals are samples, not inferred native event frames',
                'sample_frame_ordinals': frames, 'sample_frame_seconds': [str(Decimal(n) / 30) for n in frames],
                'raw_SHA_reads': 0, 'raw_reencodes': 0, 'full_metadata_probes': 1, 'full_strict_decodes': 1, 'additional_seek_commands': 0,
                'max_encoded_sample_images': 6, 'sample_encoding': 'mjpeg q5, yuvj444p, 1600x900 samples; showinfo original PTS before scale, same full-decode branch',
                'max_parallel_media_commands': 1, 'codec_filter_threads': 1, 'preparation_directory_bytes': size(PREP), 'total_derived_limit_bytes': LIMIT,
                'deadline_utc': DEADLINE.isoformat(), 'SDK_game_desktop_recorder_main_tree_operations': 0,
                'clean_spans_certified': False, 'human_signoff': False, 'native_land_arrival_business_acceptance': None}
        write(output / 'PLAN-AND-INPUTS.json', plan)
        probe = command(output, 'metadata-probe', [str(FFTOOLS / 'ffprobe.exe'), '-v', 'error', '-threads', '1', '-show_streams', '-show_format', '-of', 'json', str(raw)])
        require(probe['returncode'] == 0 and not probe['owned_process_timed_out'] and probe['stderr']['bytes'] == 0, 'metadata probe failed')
        metadata = json.loads((output / 'metadata-probe/stdout.bin').read_text(encoding='utf-8'))
        require(len(metadata['streams']) == 1 and metadata['streams'][0]['codec_type'] == 'video', 'expected video-only raw')
        video = metadata['streams'][0]
        require((video['codec_name'], video['pix_fmt'], video['avg_frame_rate']) == ('h264', 'yuv420p', '30/1'), 'recorded codec/pixel/fps differs')
        require(video['width'] >= 1920 and video['height'] >= 1080 and video['width'] % 2 == video['height'] % 2 == 0, 'unexpected actual recording dimensions')
        require(Decimal(metadata['format']['duration']) == Decimal(45) and int(metadata['format']['size']) == expected_bytes, 'actual 45-second source duration/size differs')
        write(output / 'ACTUAL-METADATA.json', {'raw_identity_reused': identity, 'probe_result': probe, 'streams_and_format': metadata})
        samples = output / 'samples'
        samples.mkdir(exist_ok=False)
        selection = '+'.join('eq(n\\,' + str(n) + ')' for n in frames)
        graph = '[0:v:0]split=2[whole][selected];[selected]select=' + selection + ',showinfo,scale=1600:900[samples]'
        argv = [str(FFTOOLS / 'ffmpeg.exe'), '-hide_banner', '-nostdin', '-loglevel', 'info', '-xerror', '-err_detect', 'explode',
                '-threads', '1', '-filter_threads', '1', '-filter_complex_threads', '1', '-i', str(raw), '-filter_complex', graph,
                '-progress', 'pipe:1', '-stats_period', '5', '-map', '[whole]', '-an', '-c:v', 'wrapped_avframe', '-threads:v', '1', '-fps_mode', 'passthrough', '-f', 'null', '-',
                '-map', '[samples]', '-an', '-c:v', 'mjpeg', '-pix_fmt', 'yuvj444p', '-q:v', '5', '-threads:v', '1', '-fps_mode', 'vfr', '-start_number', '0', '-n', str(samples / 'frame-%02d.jpg')]
        decoded = command(output, 'strict-whole-decode-and-samples', argv)
        progress = (output / 'strict-whole-decode-and-samples/stdout.bin').read_text(encoding='utf-8', errors='replace')
        stderr = (output / 'strict-whole-decode-and-samples/stderr.bin').read_text(encoding='utf-8', errors='replace')
        counts = [int(n) for n in re.findall(r'^frame=(\d+)$', progress, re.M)]
        pattern = re.compile(r'\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:(\S+).*?\bfmt:(\S+).*?\bs:(\d+)x(\d+)')
        rows = [{'selected_ordinal': int(n), 'original_pts_ticks': int(pts), 'original_pts_time': seconds, 'pixel_format_before_JPEG': fmt,
                 'width': int(w), 'height': int(h)} for n, pts, seconds, fmt, w, h in pattern.findall(stderr)]
        files = sorted(samples.glob('frame-*.jpg'))
        errors = []
        if decoded['returncode'] != 0: errors.append('strict_decode_nonzero')
        if decoded['owned_process_timed_out']: errors.append('owned_strict_decode_timeout')
        if not progress.rstrip().endswith('progress=end'): errors.append('strict_decode_progress_incomplete')
        if not counts or counts[-1] != 1350: errors.append('decoded_frame_count_not1350')
        if len(rows) != len(frames) or len(files) != len(frames): errors.append('selected_sample_count')
        if before != stat(raw): errors.append('raw_stat_changed')
        error_lines = [s for s in stderr.splitlines() if re.search('Error while|Invalid data found|corrupt decoded|non monotonically|Non-monotonous|Conversion failed', s, re.I)]
        if error_lines: errors.append('strict_decode_error_lines')
        numerator, denominator = (int(x) for x in video['time_base'].split('/'))
        require(numerator > 0 and denominator > 0, 'invalid actual video time base')
        for row, ordinal, image_path in zip(rows, frames, files):
            # Matroska milliseconds quantize 30-fps frame times. Compare the
            # observed integer tick against the exact rational grid, allowing
            # at most half of one source-container tick, not a guessed wall time.
            exact_tick = Decimal(ordinal) * denominator / (30 * numerator)
            if abs(Decimal(row['original_pts_ticks']) - exact_tick) > Decimal('0.5'): errors.append('selected_original_PTS_grid')
            if (row['width'], row['height']) != (video['width'], video['height']): errors.append('sample_dimensions_changed')
            with Image.open(image_path) as encoded_image:
                if encoded_image.size != (1600, 900): errors.append('encoded_sample_dimensions_not1600x900')
            row.update({'encoded_sample_width': 1600, 'encoded_sample_height': 900, 'source_frame_ordinal': ordinal, 'time_base': video['time_base'], 'image': pin(image_path), 'AI_visual_observation': None,
                        'Root_visual_review': None, 'native_event_exact_frame_claimed': False, 'human_approval': False})
        if size(PREP) + size(output) > LIMIT - 32768: errors.append('shared_derived_budget_margin')
        report = {'schema': 'xar.e04.R0180-land-arrival-raw-offline-audit.v1', 'state': 'PASS_RAW_METADATA_AND_STRICT_DECODE_ONLY' if not errors else 'RED_RAW_METADATA_OR_DECODE',
                  'at_utc': now(), 'errors': errors, 'raw_identity_reused': identity, 'raw_stat_before': before, 'raw_stat_after': stat(raw),
                  'actual_source_head': EXPECTED_SOURCE, 'actual_run_id': binding['run_id'], 'recorder_rc0_job_empty': True,
                  'actual_duration_seconds': metadata['format']['duration'], 'decoded_frames': counts[-1] if counts else None,
                  'width': video['width'], 'height': video['height'], 'fps': video['avg_frame_rate'], 'time_base': video['time_base'],
                  'codec': video['codec_name'], 'pixel_format': video['pix_fmt'], 'audio_streams': 0,
                  'actual_metadata': pin(output / 'ACTUAL-METADATA.json'), 'strict_decode_result': pin(output / 'strict-whole-decode-and-samples/result.json'),
                  'plan_and_inputs': pin(output / 'PLAN-AND-INPUTS.json'), 'audit_source': pin(Path(__file__)), 'samples': rows,
                  'strict_error_lines': error_lines, 'decode_progress_end': progress.rstrip().endswith('progress=end'),
                  'raw_SHA_reads': 0, 'raw_reencodes': 0, 'metadata_probe_count': 1, 'strict_whole_decode_count': 1, 'extra_seek_count': 0,
                  'selected_JPEG_count': len(files), 'source_wall_to_PTS_calibrated': False, 'native_event_exact_encoded_frame': None,
                  'land_arrival_business_acceptance': None, 'land_arrival_in_source_confirmed': None, 'nextday_in_source_claimed': False,
                  'clean_spans_certified': False, 'continuous_clean_review': False, 'Root_visual_approval': None, 'human_1x_review': False, 'human_signoff': False,
                  'SDK_game_desktop_recorder_main_tree_Git_OneDrive_operations': 0, 'budget_pool': 'R0180_scene_other256MiB_Root_allocated8MiB',
                  'derived_bytes_before_report': size(PREP) + size(output), 'derived_bytes_limit': LIMIT, 'deadline_utc': DEADLINE.isoformat()}
        write(output / 'report.json', report)
        write(output / 'ROOT-DELIVERY.json', {'state': report['state'], 'report': pin(output / 'report.json'), 'raw_identity_reused': identity,
              'samples': [row['image'] for row in rows], 'derived_bytes_before_delivery': size(PREP) + size(output), 'derived_bytes_limit': LIMIT,
              'raw_SHA_reads': 0, 'Root_visual_approval': None, 'clean_spans_certified': False, 'human_signoff': False})
        require(size(PREP) + size(output) <= LIMIT, 'combined preparation and derived output exceeds 8 MiB')
        print(json.dumps({'state': report['state'], 'errors': errors, 'report': pin(output / 'report.json'), 'delivery': pin(output / 'ROOT-DELIVERY.json'),
                          'combined_derived_bytes': size(PREP) + size(output)}, ensure_ascii=False, indent=2), flush=True)
        return 0 if not errors else 1
    except Exception:
        with (output / 'UNEXPECTED-FAILURE.txt').open('x', encoding='utf-8') as handle:
            handle.write(traceback.format_exc())
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True, help='Root-supplied actual finished-raw JSON, never the null template')
    parser.add_argument('--run', action='store_true', help='Explicit execution after Root has supplied actual closed recorder paths and identity')
    args = parser.parse_args()
    require(args.run, 'Preparation alone grants no media execution; --run and actual finished binding are required')
    return execute(args.binding.resolve(strict=True))

if __name__ == '__main__':
    raise SystemExit(main())
