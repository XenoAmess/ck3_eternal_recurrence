from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE / 'audit-attempt-a01'
ROOT = PACKAGE.parent
RAW = ROOT / 'r0177-raw-abc-a2-a01/raw.mkv'
TERMINAL = ROOT / 'r0177-raw-abc-a2-a01/result.json'
EXPECTED_TERMINAL_SHA = '9bf818e426a225cd3c3f245e3ef8d351221984e6f18aed10633b15777f33cc6e'
FINISH = None
TOOLS = ROOT / 'recording-preflight-a01/media-tools.json'


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_new(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def pin(path: Path) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
            size += len(block)
    return {'path': str(path), 'bytes': size, 'sha256': digest.hexdigest()}


def probe(name: str, argv: list[str]) -> dict:
    folder = BASE / name
    folder.mkdir()
    write_new(folder / 'argv.json', {'argv': argv, 'purpose': name, 'read_only_source': str(RAW)})
    start = now()
    start_ns = time.monotonic_ns()
    with (folder / 'stdout.json').open('xb') as out, (folder / 'stderr.txt').open('xb') as err:
        result = subprocess.run(argv, stdout=out, stderr=err, check=False)
    receipt = {'started_at_utc': start, 'completed_at_utc': now(),
        'elapsed_seconds': (time.monotonic_ns() - start_ns) / 1e9,
        'returncode': result.returncode,
        'argv_identity': pin(folder / 'argv.json'),
        'stdout_identity': pin(folder / 'stdout.json'),
        'stderr_identity': pin(folder / 'stderr.txt')}
    write_new(folder / 'receipt.json', receipt)
    print(json.dumps({'probe_finished': name, 'returncode': result.returncode,
        'elapsed_seconds': receipt['elapsed_seconds']}, ensure_ascii=False), flush=True)
    return receipt


def monotonic(rows: list[dict], field: str, time_base: Fraction) -> dict:
    missing = 0
    equality = 0
    regressions = []
    previous = None
    first = None
    last = None
    delta_min = None
    delta_max = None
    duration_sum = Decimal(0)
    for index, row in enumerate(rows):
        value = row.get(field)
        if value is None or value == 'N/A':
            missing += 1
            continue
        current = int(value)
        if first is None:
            first = current
        last = current
        if previous is not None:
            delta = current - previous
            delta_min = delta if delta_min is None else min(delta_min, delta)
            delta_max = delta if delta_max is None else max(delta_max, delta)
            if delta == 0:
                equality += 1
            elif delta < 0:
                if len(regressions) < 32:
                    regressions.append({'index': index, 'previous': previous, 'current': current})
        previous = current
        if row.get('duration_time') not in (None, 'N/A'):
            duration_sum += Decimal(row['duration_time'])
    to_seconds = lambda value: str(Decimal(value) * Decimal(time_base.numerator) / Decimal(time_base.denominator)) if value is not None else None
    result = {'field': field, 'count': len(rows), 'present': len(rows) - missing,
        'missing': missing, 'equal_adjacent': equality, 'regression_examples': regressions,
        'non_decreasing': not regressions and missing == 0,
        'strictly_increasing': not regressions and missing == 0 and equality == 0,
        'first_raw': first, 'last_raw': last, 'first_seconds': to_seconds(first),
        'last_seconds': to_seconds(last), 'minimum_adjacent_delta_raw': delta_min,
        'maximum_adjacent_delta_raw': delta_max,
        'span_seconds': to_seconds(last - first) if first is not None and last is not None else None,
        'sum_declared_duration_seconds': str(duration_sum), 'time_base': str(time_base)}
    return result


parser = argparse.ArgumentParser(description='Audit only after Root supplied a successful finished recording receipt; no active-raw probing.')
parser.add_argument('--execute-finished-audit', action='store_true', required=True)
parser.add_argument('--finish-receipt', type=Path, required=True)
parser.add_argument('--finish-response-sha256', required=True)
args = parser.parse_args()
FINISH = args.finish_receipt.resolve(strict=True)
expected_finish_sha = args.finish_response_sha256.lower()
if len(expected_finish_sha) != 64 or any(c not in '0123456789abcdef' for c in expected_finish_sha):
    raise SystemExit('Explicit finish response SHA-256 required')
actual_finish_identity = pin(FINISH)
if actual_finish_identity['sha256'] != expected_finish_sha:
    raise SystemExit('Finish receipt SHA mismatch; raw untouched')
finish = json.loads(FINISH.read_text(encoding='utf-8-sig'))
if (finish.get('is_error') is not False or finish['body']['state'] != 'NORMAL_TREE_EMPTY' or
    finish['body']['job']['returncode'] != 0 or finish['body']['job']['job_active_processes'] != 0 or
    Path(finish['body']['raw']['path']).resolve() != RAW.resolve()):
    raise SystemExit('Recording has no successful exit0/Jobempty finish binding; raw untouched')
BASE.mkdir()
write_new(BASE / 'audit-execution-argv.json', {'argv': sys.argv, 'interpreter': sys.executable,
    'finish_receipt_identity': actual_finish_identity, 'finished_receipt_gate_passed': True})
start_at = now()
tools = json.loads(TOOLS.read_text(encoding='utf-8-sig'))
assert finish['is_error'] is False
assert finish['body']['state'] == 'NORMAL_TREE_EMPTY'
assert finish['body']['job']['returncode'] == 0
assert finish['body']['job']['job_active_processes'] == 0
assert Path(finish['body']['raw']['path']).resolve() == RAW.resolve()
terminal_identity = pin(TERMINAL)
assert terminal_identity['sha256'] == EXPECTED_TERMINAL_SHA
terminal = json.loads(TERMINAL.read_text(encoding='utf-8-sig'))
assert terminal == finish['body']
raw_stat_before = RAW.stat()
assert raw_stat_before.st_size == finish['body']['raw']['bytes']
ffprobe = Path(tools['ffprobe']['path'])
ffmpeg = Path(tools['ffmpeg']['path'])
with ThreadPoolExecutor(max_workers=4) as executor:
    identities = dict(zip(('ffprobe', 'ffmpeg', 'finish'), executor.map(pin, (ffprobe, ffmpeg, FINISH))))
identities['raw'] = dict(finish['body']['raw'])  # Exact sealed OwnedRecorder terminal identity; raw not rehashed here.
assert identities['raw']['bytes'] == finish['body']['raw']['bytes']
assert identities['raw']['sha256'] == finish['body']['raw']['sha256']
assert identities['ffprobe']['bytes'] == tools['ffprobe']['bytes']
assert identities['ffprobe']['sha256'] == tools['ffprobe']['sha256']
assert identities['ffmpeg']['bytes'] == tools['ffmpeg']['bytes']
assert identities['ffmpeg']['sha256'] == tools['ffmpeg']['sha256']
write_new(BASE / 'source-bindings.json', {'at': now(), 'interpreter': sys.executable,
    'python_version': sys.version, 'identities': identities, 'media_tools_identity': pin(TOOLS),
    'finish_job': finish['body']['job'], 'terminal_result_identity': terminal_identity,
    'sealed_terminal_hash_reused': True, 'audit_raw_sha_reads': 0, 'recorder_clean_spans_certified': False,
    'recorder_human_approval': False})
print(json.dumps({'sealed_terminal_source_sha_reused': identities['raw']['sha256'], 'ffprobe_sha_verified': identities['ffprobe']['sha256']}, ensure_ascii=False), flush=True)

common = [str(ffprobe), '-v', 'error', '-threads', '4']
commands = {
    'streams-format': common + ['-show_streams', '-show_format', '-of', 'json', str(RAW)],
    'video-packets': common + ['-select_streams', 'v:0', '-show_packets', '-show_entries',
        'packet=stream_index,pts,pts_time,dts,dts_time,duration,duration_time,flags', '-of', 'json', str(RAW)],
    'video-frames': common + ['-select_streams', 'v:0', '-show_frames', '-show_entries',
        'frame=stream_index,pts,pts_time,best_effort_timestamp,best_effort_timestamp_time,pkt_dts,pkt_dts_time,duration,duration_time,key_frame,pict_type',
        '-of', 'json', str(RAW)],
    'strict-full-decode': [str(ffmpeg), '-hide_banner', '-nostdin', '-loglevel', 'error', '-xerror',
        '-threads', '4', '-err_detect', 'explode', '-i', str(RAW), '-map', '0:v:0', '-an',
        '-progress', 'pipe:1', '-stats_period', '20', '-f', 'null', '-'],
}
receipts = {}
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(probe, name, argv): name for name, argv in commands.items()}
    for future in as_completed(futures):
        receipts[futures[future]] = future.result()

errors = []
metadata = json.loads((BASE / 'streams-format/stdout.json').read_text(encoding='utf-8-sig'))
packets = json.loads((BASE / 'video-packets/stdout.json').read_text(encoding='utf-8-sig'))['packets']
frames = json.loads((BASE / 'video-frames/stdout.json').read_text(encoding='utf-8-sig'))['frames']
streams = metadata['streams']
video = [stream for stream in streams if stream['codec_type'] == 'video']
audio = [stream for stream in streams if stream['codec_type'] == 'audio']
if len(video) != 1:
    errors.append('expected_exactly_one_video_stream')
v = video[0]
time_base = Fraction(v['time_base'])
duration = Decimal(metadata['format']['duration'])
fps = Fraction(v['avg_frame_rate'])
packet_pts = monotonic(packets, 'pts', time_base)
packet_dts = monotonic(packets, 'dts', time_base)
frame_pts = monotonic(frames, 'pts', time_base)
frame_best_effort = monotonic(frames, 'best_effort_timestamp', time_base)
for name, receipt in receipts.items():
    if receipt['returncode'] != 0:
        errors.append(name + '_nonzero_exit')
    if receipt['stderr_identity']['bytes']:
        errors.append(name + '_ffprobe_error_output')
if (v['width'], v['height']) != (1920, 1080):
    errors.append('resolution_mismatch')
if fps != 30 or Fraction(v['r_frame_rate']) != 30:
    errors.append('frame_rate_mismatch')
if duration <= 0:
    errors.append('nonpositive_format_duration')
if audio:
    errors.append('unexpected_audio_stream_for_video_only_raw_contract')
frame_equivalent = Decimal(len(frames)) * Decimal(fps.denominator) / Decimal(fps.numerator)
if abs(frame_equivalent - duration) > Decimal('0.1'):
    errors.append('frame_count_duration_mismatch_over_100ms')
if not packets or len(frames) != len(packets):
    errors.append('decoded_frame_packet_count_mismatch')
for name, sequence in [('packet_pts', packet_pts), ('packet_dts', packet_dts),
    ('frame_pts', frame_pts), ('frame_best_effort_timestamp', frame_best_effort)]:
    if not sequence['strictly_increasing']:
        errors.append(name + '_not_complete_strictly_increasing')
decode_progress = (BASE / 'strict-full-decode/stdout.json').read_text(encoding='utf-8-sig')
decode_blocks = decode_progress.strip().split('progress=')
decode_done = decode_progress.rstrip().endswith('progress=end')
decode_frame_values = [int(line.split('=', 1)[1]) for line in decode_progress.splitlines() if line.startswith('frame=')]
decode_last_frames = decode_frame_values[-1] if decode_frame_values else None
if not decode_done or decode_last_frames != len(frames):
    errors.append('strict_full_decode_not_end_or_framecount_mismatch')
frame_dts = monotonic(frames, 'pkt_dts', time_base)
raw_stat_after = RAW.stat()
unchanged = (raw_stat_before.st_size, raw_stat_before.st_mtime_ns) == (raw_stat_after.st_size, raw_stat_after.st_mtime_ns)
raw_identity_after = {'stat_only': True, 'path': str(RAW), 'bytes': raw_stat_after.st_size, 'mtime_ns': raw_stat_after.st_mtime_ns, 'no_second_large_raw_rehash': True}
if not unchanged:
    errors.append('raw_bytes_or_mtime_changed_during_audit')
report = {
    'schema': 'episode04-raw-media-audit-v1', 'state': 'PASS' if not errors else 'RED',
    'started_at_utc': start_at, 'completed_at_utc': now(), 'errors': errors,
    'source_identity': identities['raw'], 'ffprobe_identity': identities['ffprobe'],
    'finish_receipt_identity': identities['finish'], 'probe_receipts': receipts,
    'raw_stat_unchanged_during_audit': unchanged, 'closed_source_sha_independently_verified_once': False,
    'sealed_terminal_hash_reused': True, 'audit_raw_sha_reads': 0, 'terminal_result_identity': terminal_identity,
    'terminal_finish_body_matches': True, 'source_identity_after_audit': raw_identity_after,
    'format': metadata['format'], 'video_stream': v,
    'stream_counts': {'video': len(video), 'audio': len(audio), 'all': len(streams)},
    'actual_duration_seconds': str(duration), 'actual_duration_minutes': str(duration / 60),
    'decoded_frames': len(frames), 'video_packets': len(packets),
    'decoded_frame_equivalent_seconds_at_declared_fps': str(Decimal(len(frames)) / Decimal(fps.numerator) * Decimal(fps.denominator)),
    'timestamps': {'packet_pts': packet_pts, 'packet_dts': packet_dts,
        'frame_pts': frame_pts, 'frame_best_effort_timestamp': frame_best_effort, 'frame_packet_dts': frame_dts},
    'observed_picture_types': {kind: sum(frame.get('pict_type') == kind for frame in frames)
        for kind in sorted({frame.get('pict_type', 'unknown') for frame in frames})},
    'strict_full_decode': {'reached_progress_end': decode_done, 'final_decoded_frames': decode_last_frames, 'errors_on_stderr': receipts['strict-full-decode']['stderr_identity']['bytes'], 'ffmpeg_identity': identities['ffmpeg']},
    'scope': 'Finished R0177 first A2 tape only: full-file demux metadata, complete packet timestamps and complete decoded-frame timestamps. No human audiovisual viewing, clean span, pixel-content or final film verdict.',
    'full_human_viewing_performed': False, 'clean_spans_certified': False,
    'human_signoff': False, 'final_film_certified': False,
    'sdk_requests_executed': 0, 'game_processes_started': 0, 'desktop_inputs': 0,
    'ffmpeg_recorders_started': 0, 'source_media_modified': False,
}
write_new(BASE / 'report.json', report)
write_new(BASE / 'delivery.json', {'report_identity': pin(BASE / 'report.json'),
    'script_identity': pin(Path(__file__)), 'source_identity': identities['raw'],
    'state': report['state'], 'human_signoff': False, 'clean_spans_certified': False})
print(json.dumps({'state': report['state'], 'errors': errors, 'duration_seconds': str(duration),
    'frames': len(frames), 'packets': len(packets), 'report': str(BASE / 'report.json'),
    'report_identity': pin(BASE / 'report.json')}, ensure_ascii=False), flush=True)
raise SystemExit(0 if not errors else 1)
