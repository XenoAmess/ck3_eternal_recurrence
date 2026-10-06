"""Unique actual Review01 audit: reused producer identities; no old raw or approval.

Adapted from the preserved actual A-only auditor. AAC audit observes original
timestamps before any repair and uses real nb_samples and packet trim metadata.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from array import array
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import difflib, hashlib, json, math, re, subprocess, sys, time, traceback, wave
ROOT = Path('C:/ck3-war-episode04-research-20261004-a01')
PACKAGE = Path(__file__).resolve().parent
BASE = PACKAGE / 'attempt-a02'
PRODUCER = ROOT / 'e4-final-review01-a01'
DELIVERY = PRODUCER / 'CLOSED-MOVIE-DELIVERY-a01.json'
EXPECTED_DELIVERY = '3ddb222eaabcb8c1db767fdb335b8b98259147abb145a3f4d156f9e7470ab2f3'
EXPECTED_MEDIA_SHA = 'a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346'
EXPECTED_PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
FFTOOLS = Path('C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin')
FFMPEG = FFTOOLS / 'ffmpeg.exe'
FFPROBE = FFTOOLS / 'ffprobe.exe'
EXPECTED_FF = {'ffmpeg.exe': (222229504, '57c56e369d5b4873b4d93fc1a1d833cb7cd8bc9325c14b05c34ce60b22842d8a'), 'ffprobe.exe': (222026240, 'afe05347caaabe479b3c4eae71992b6ec1e11c57266a1d665deb0f9fe9847208')}
if not Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve():
    raise RuntimeError('audit prerequisite failed: Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve()')

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p, value):
    with Path(p).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')

def pin(p, bounded_media=False):
    p = Path(p)
    if p.suffix.lower() in {'.mp4', '.mkv', '.mov', '.wav', '.pcm'}:
        if not (bounded_media and p.is_relative_to(BASE)):
            raise RuntimeError('Large source identity must be reused')
    digest = hashlib.sha256()
    count = 0
    with p.open('rb') as handle:
        while (block := handle.read(8 * 1024 * 1024)):
            digest.update(block)
            count += len(block)
    return {'path': str(p), 'bytes': count, 'sha256': digest.hexdigest()}

def stat(p):
    value = Path(p).stat()
    return {'path': str(p), 'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns}

def check_small_identity(identity):
    actual = pin(identity['path'])
    if not (actual['bytes'] == identity['bytes'] and actual['sha256'].lower() == identity['sha256'].lower()):
        raise RuntimeError(identity)
    return actual

def owned_command(label, argv):
    directory = BASE / label
    directory.mkdir()
    write(directory / 'argv.json', {'argv': argv, 'shell': False, 'codec_threads': 1, 'filter_threads': 1, 'medium_source': 'new closed Review01 only'})
    start = now()
    mono = time.monotonic_ns()
    with (directory / 'stdout.bin').open('xb') as out, (directory / 'stderr.bin').open('xb') as err:
        process = subprocess.Popen(argv, stdout=out, stderr=err)
        write(directory / 'owned-process.json', {'pid': process.pid, 'started_utc': start, 'foreign_process_operations': 0})
        print(json.dumps({'started': label, 'pid': process.pid, 'utc': start}), flush=True)
        rc = process.wait()
    result = {'returncode': rc, 'started_utc': start, 'ended_utc': now(), 'elapsed_seconds': (time.monotonic_ns() - mono) / 1000000000.0, 'argv': pin(directory / 'argv.json'), 'stdout': pin(directory / 'stdout.bin'), 'stderr': pin(directory / 'stderr.bin'), 'partials_retained': True}
    write(directory / 'result.json', result)
    print(json.dumps({'completed': label, 'rc': rc, 'seconds': result['elapsed_seconds']}), flush=True)
    return result

def stats_s16(data, channels):
    values = array('h')
    values.frombytes(data)
    if sys.byteorder != 'little':
        values.byteswap()
    if not len(values) % channels == 0:
        raise RuntimeError('audit prerequisite failed: len(values) % channels == 0')
    rows = []
    for channel in range(channels):
        samples = values[channel::channels]
        count = len(samples)
        if not count > 0:
            raise RuntimeError('audit prerequisite failed: count > 0')
        lo, hi = (min(samples), max(samples))
        square = sum((v * v for v in samples))
        rms = math.sqrt(square / count)
        peak = max(abs(lo), abs(hi)) / 32768
        rows.append({'channel': channel, 'samples': count, 'min_s16': lo, 'max_s16': hi, 'mean_s16': sum(samples) / count, 'rms_s16': rms, 'rms_dBFS': 20 * math.log10(rms / 32768) if rms else None, 'peak_normalized': peak, 'peak_dBFS': 20 * math.log10(peak) if peak else None, 'samples_at_integer_limit': sum((v in (-32768, 32767) for v in samples)), 'NaN_Inf_possible_in_s16': False})
    return {'sample_frames': len(values) // channels, 'channels': rows}

def source_pcm_scan(identity, expected_header):
    path = Path(identity['path'])
    before = stat(path)
    if not before['bytes'] == identity['bytes']:
        raise RuntimeError("audit prerequisite failed: before['bytes'] == identity['bytes']")
    with wave.open(str(path), 'rb') as source:
        nc, width, rate, nframes, compression, _ = source.getparams()
        header = {'sample_rate': rate, 'channels': nc, 'sample_width_bytes': width, 'sample_frames': nframes, 'seconds': str(Decimal(nframes) / rate), 'compression': compression}
        if not (nc, width, rate, nframes, compression) == (1, 2, 24000, 41658624, 'NONE'):
            raise RuntimeError("audit prerequisite failed: (nc, width, rate, nframes, compression) == (1, 2, 24000, 41658624, 'NONE')")
        if not nframes == expected_header['sample_frames']:
            raise RuntimeError("audit prerequisite failed: nframes == expected_header['sample_frames']")
        count = 0
        square = 0
        total = 0
        lo = 32767
        hi = -32768
        limits = 0
        front = bytearray()
        tail = bytearray()
        boundary_size = rate * nc * width
        while (data := source.readframes(1024 * 1024)):
            values = array('h')
            values.frombytes(data)
            if sys.byteorder != 'little':
                values.byteswap()
            count += len(values)
            total += sum(values)
            square += sum((v * v for v in values))
            lo = min(lo, min(values))
            hi = max(hi, max(values))
            limits += sum((v in (-32768, 32767) for v in values))
            if len(front) < boundary_size:
                front.extend(data[:boundary_size - len(front)])
            tail.extend(data)
            tail = tail[-boundary_size:]
    after = stat(path)
    if not (after == before and count == nframes):
        raise RuntimeError('audit prerequisite failed: after == before and count == nframes')
    boundaries = {}
    for label, data in [('front', bytes(front)), ('back', bytes(tail))]:
        artifact = BASE / ('source-narration-' + label + '-1s.pcm')
        with artifact.open('xb') as handle:
            handle.write(data)
        boundaries[label] = {'artifact': pin(artifact, True), 'statistics': stats_s16(data, nc)}
    rms = math.sqrt(square / count)
    peak = max(abs(lo), abs(hi)) / 32768
    result = {'state': 'PASS_NEW_SOURCE_PCM_SAMPLE_STRUCTURE', 'source_identity_reused': identity, 'header': header, 'full_scan_sample_frames': count, 'full_sample_scan_count': 1, 'full_source_hash_read_count': 0, 'NaN_Inf_count': 0, 'finite_proof': 'Each sample decoded from validated signed 16-bit integer PCM; NaN/Inf are not representable', 'min_s16': lo, 'max_s16': hi, 'mean_s16': total / count, 'peak_normalized': peak, 'peak_dBFS': 20 * math.log10(peak) if peak else None, 'rms_s16': rms, 'rms_dBFS': 20 * math.log10(rms / 32768) if rms else None, 'samples_at_integer_limit': limits, 'front_back_from_same_full_scan': boundaries, 'source_stat_before': before, 'source_stat_after': after, 'source_PCM_equals_lossy_mixed_AAC_claimed': False, 'listening': False}
    write(BASE / 'source-PCM-full-scan.json', result)
    print(json.dumps({'completed': 'source_pcm_full_scan', 'samples': count}), flush=True)
    return result

def boundary_wave(path):
    with wave.open(str(path), 'rb') as source:
        nc, width, rate, nf, compression, _ = source.getparams()
        data = source.readframes(nf)
    if not (nc, width, rate, nf, compression) == (2, 2, 48000, 48000, 'NONE'):
        raise RuntimeError("audit prerequisite failed: (nc, width, rate, nf, compression) == (2, 2, 48000, 48000, 'NONE')")
    return {'artifact': pin(path, True), 'header': {'channels': nc, 'sample_width_bytes': width, 'sample_rate': rate, 'sample_frames': nf}, 'statistics': stats_s16(data, nc), 'listening': False}

def distributions(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}

def analyze_probe(path, video, audio, expected_frames, expected_samples):
    body = load(path)
    rows = body.get('packets_and_frames')
    if not isinstance(rows, list):
        raise RuntimeError('Actual combined packets+frames schema unavailable')
    frames = [row for row in rows if row.get('type') == 'frame']
    packets = [row for row in rows if row.get('type') == 'packet']
    vf = [row for row in frames if row.get('stream_index') == video['index']]
    af = [row for row in frames if row.get('stream_index') == audio['index']]
    vp = [row for row in packets if row.get('stream_index') == video['index']]
    ap = [row for row in packets if row.get('stream_index') == audio['index']]
    errors = []
    if len(vf) != expected_frames or len(vp) != expected_frames:
        errors.append('video_frame_or_packet_count')
    if any((int(row.get('pts', -1)) != index * 1600 or row.get('width') != 1920 or row.get('height') != 1080 for index, row in enumerate(vf))):
        errors.append('video_frame_grid_or_picture_metadata')
    if any((int(row.get('pts', -1)) != index * 1600 or int(row.get('dts', -1)) != index * 1600 or int(row.get('duration', -1)) != 1600 for index, row in enumerate(vp))):
        errors.append('video_packet_PTS_DTS_duration_grid')
    for label, items in [('video', vp), ('audio', ap)]:
        dts = [int(row['dts']) for row in items if 'dts' in row]
        if len(dts) != len(items) or any((right <= left for left, right in zip(dts, dts[1:]))):
            errors.append(label + '_packet_DTS_monotonic')
    af_samples = sum((int(row.get('nb_samples', 0)) for row in af))
    af_pts = [int(row.get('pts', -99999999)) for row in af]
    af_gaps = [int(right.get('pts', -99999999)) - int(left.get('pts', -99999999)) - int(left.get('nb_samples', 0)) for left, right in zip(af, af[1:])]
    if not af or af_pts[0] != 0 or af_samples != expected_samples or (af_pts[-1] + int(af[-1].get('nb_samples', 0)) != expected_samples) or any(af_gaps):
        errors.append('probe_decoded_audio_actual_sample_clock')
    if any((row.get('channels') != 2 or int(row.get('nb_samples', 0)) <= 0 for row in af)):
        errors.append('probe_audio_frame_metadata')
    if not ap:
        errors.append('audio_packets_missing')
    priming = None
    tail = None
    packet_gaps = []
    effective_segments = []
    for index, row in enumerate(ap):
        pts, duration = (int(row.get('pts', -99999999)), int(row.get('duration', 0)))
        sides = row.get('side_data_list', [])
        skip = sum((int(x.get('skip_samples', 0)) for x in sides if x.get('side_data_type') == 'Skip Samples'))
        discard = sum((int(x.get('discard_padding', 0)) for x in sides if x.get('side_data_type') == 'Skip Samples'))
        if index == 0 and pts < 0:
            priming = {'packet': row, 'actual_skip_samples': skip, 'effective_start': pts + skip, 'effective_end': pts + duration}
            if pts + skip != 0 or pts + duration != 0 or skip <= 0:
                errors.append('AAC_priming_metadata_not_explaining_zero_start')
            continue
        start = pts + skip
        end = pts + duration
        tail_policy = 'duration_used_once'
        if end > expected_samples:
            if discard <= 0 or end - discard != expected_samples:
                errors.append('AAC_unexplained_tail_overflow')
            else:
                end -= discard
                tail_policy = 'actual_discard_applied_once_to_untrimmed_duration'
        elif discard:
            if end != expected_samples:
                errors.append('AAC_discard_on_nonterminal_trimmed_packet')
            tail_policy = 'duration_already_trimmed_discard_not_subtracted_twice'
        if end <= start:
            errors.append('AAC_nonpositive_effective_packet_duration')
        effective_segments.append((start, end))
        if index == len(ap) - 1:
            tail = {'packet': row, 'actual_discard_padding': discard, 'effective_start': start, 'effective_end': end, 'policy': tail_policy, 'decoded_last_actual_nb_samples': int(af[-1].get('nb_samples', 0)) if af else None, 'assumed_fixed_last1024': False}
    if not priming:
        errors.append('AAC_actual_priming_receipt_missing')
    if effective_segments:
        packet_gaps = [right[0] - left[1] for left, right in zip(effective_segments, effective_segments[1:])]
        if effective_segments[0][0] != 0 or effective_segments[-1][1] != expected_samples or any(packet_gaps):
            errors.append('AAC_effective_packet_sample_grid')
    raw_ap_pts = [int(row.get('pts', -99999999)) for row in ap]
    raw_steps = [b - a for a, b in zip(raw_ap_pts, raw_ap_pts[1:])]
    if any((step != 1024 for step in raw_steps)):
        errors.append('AAC_raw_packet_pts_step')
    effective_total = sum((b - a for a, b in effective_segments))
    if effective_total != expected_samples:
        errors.append('AAC_effective_packet_sample_total')
    result = {'state': 'PASS_ACTUAL_FRAME_PACKET_CLOCK' if not errors else 'RED_ACTUAL_FRAME_PACKET_CLOCK', 'errors': errors, 'actual_schema': 'packets_and_frames[] with type discriminator', 'video_frames': len(vf), 'video_packets': len(vp), 'video_first_frame': vf[0] if vf else None, 'video_last_frame': vf[-1] if vf else None, 'video_tick_per_frame': 1600, 'audio_frames': len(af), 'audio_packets': len(ap), 'audio_actual_decoded_sample_frames': af_samples, 'audio_first_frame': af[0] if af else None, 'audio_last_frame': af[-1] if af else None, 'audio_frame_boundary_delta_samples_distribution': distributions(af_gaps), 'audio_packet_raw_pts_step_distribution': distributions(raw_steps), 'audio_effective_packet_boundary_delta_samples_distribution': distributions(packet_gaps), 'audio_effective_packet_sample_total': effective_total, 'AAC_priming': priming, 'AAC_tail': tail, 'expected_actual_presentation_sample_frames': expected_samples, 'native_event_exact_frame': None, 'human_or_clean_approval': False}
    write(BASE / 'frame-packet-clock-summary.json', result)
    return result

def analyze_decode(result, expected_frames, expected_samples):
    directory = BASE / 'strict-whole-video-AAC-decode'
    text = (directory / 'stderr.bin').read_text(encoding='utf-8', errors='replace')
    progress = (directory / 'stdout.bin').read_text(encoding='utf-8', errors='replace')
    counts = [int(v) for v in re.findall('^frame=(\\d+)$', progress, re.M)]
    pattern = re.compile('\\bn:(\\d+)\\s+pts:(-?\\d+)\\s+pts_time:(\\S+)\\s+fmt:(\\S+)\\s+channels:(\\d+)\\s+chlayout:(\\S+)\\s+rate:(\\d+)\\s+nb_samples:(\\d+)\\s+checksum:')
    rows = []
    mismatch = []
    gaps = []
    offsets = []
    expected_next = 0
    cumulative = 0
    with (BASE / 'decoded-AAC-frame-clock.csv').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write('ordinal,pts_samples,nb_samples,rate,channels,pts_time_text\n')
        for match in pattern.finditer(text):
            n, pts, seconds, fmt, channels, layout, rate, ns = match.groups()
            n, pts, channels, rate, ns = map(int, (n, pts, channels, rate, ns))
            row = {'n': n, 'pts': pts, 'pts_time_text': seconds, 'format': fmt, 'channels': channels, 'layout': layout, 'rate': rate, 'nb_samples': ns}
            if n != len(rows) or channels != 2 or rate != 48000 or (ns <= 0):
                if len(mismatch) < 32:
                    mismatch.append(row)
            if rows:
                gaps.append(pts - expected_next)
            offsets.append(pts - cumulative)
            rows.append(row)
            expected_next = pts + ns
            cumulative += ns
            handle.write(f'{n},{pts},{ns},{rate},{channels},{seconds}\n')
    astats = [line for line in text.splitlines() if '[Parsed_astats_' in line]
    astat_text = '\n'.join(astats)
    nonfinite = [float(v) for v in re.findall('Number of (?:NaNs|Infs):\\s*([\\d.]+)', astat_text)]
    peaks = [float(v) for v in re.findall('Peak level dB:\\s*([-+\\d.eE]+)', astat_text)]
    rms = [float(v) for v in re.findall('RMS level dB:\\s*([-+\\d.eE]+)', astat_text)]
    errors = []
    if result['returncode'] != 0:
        errors.append('strict_decode_nonzero')
    if not progress.rstrip().endswith('progress=end'):
        errors.append('strict_decode_incomplete_progress')
    if not counts or counts[-1] != expected_frames:
        errors.append('strict_decode_video_count')
    if not rows or mismatch:
        errors.append('AAC_frame_signature_or_metadata')
    if cumulative != expected_samples:
        errors.append('AAC_actual_sample_count')
    if not rows or rows[0]['pts'] != 0 or expected_next != expected_samples or any(gaps) or any(offsets):
        errors.append('AAC_original_integer_PTS_not_exact')
    if not nonfinite or any(nonfinite):
        errors.append('decoded_mixed_audio_NaN_Inf')
    if not peaks or not rms:
        errors.append('decoded_mixed_audio_peak_RMS_missing')
    error_lines = [line for line in text.splitlines() if re.search('Error while|Invalid data found|corrupt decoded|non monotonically|Non-monotonous|Conversion failed', line, re.I)]
    if error_lines:
        errors.append('strict_decode_error_lines')
    boundaries = {}
    for label in ['front', 'back']:
        path = BASE / ('decoded-mix-' + label + '-1s.wav')
        try:
            boundaries[label] = boundary_wave(path)
        except Exception as exc:
            errors.append('decoded_' + label + '_boundary_missing_or_invalid')
            boundaries[label] = {'error': repr(exc)}
    report = {'state': 'PASS_STRICT_DECODE_COUNTS_AND_EXACT_AAC_SAMPLE_CLOCK' if not errors else 'RED_STRICT_DECODE_COUNTS_OR_AAC_SAMPLE_CLOCK', 'errors': errors, 'video_decoded_frames': counts[-1] if counts else None, 'AAC_decoded_frame_count': len(rows), 'AAC_sample_frames_per_channel': cumulative, 'expected_samples': expected_samples, 'sample_count_delta': cumulative - expected_samples, 'first_actual_frame': rows[0] if rows else None, 'last_actual_frame': rows[-1] if rows else None, 'tail_actual_nb_samples': rows[-1]['nb_samples'] if rows else None, 'audio_frame_ordinals_complete': not mismatch and bool(rows), 'audio_original_integer_PTS_exact': bool(rows) and (not any(gaps)) and (not any(offsets)), 'adjacent_boundary_delta_samples_distribution': distributions(gaps), 'absolute_offset_samples_distribution': distributions(offsets), 'metadata_failure_examples': mismatch, 'NaN_Inf_counter_values': nonfinite, 'peak_dBFS_channel_and_overall': peaks, 'RMS_dBFS_channel_and_overall': rms, 'decoded_float_peak_above_0dBFS': any((v > 0 for v in peaks)), 'astats_lines': astats, 'full_decoded_clock_table': pin(BASE / 'decoded-AAC-frame-clock.csv'), 'same_single_decode_PCM_boundaries': boundaries, 'strict_error_lines': error_lines[:32], 'original_timestamp_repair_applied_to_audit_branch': False, 'fixed1024_tail_or_ceil_sample_target_used': False, 'mixed_PCM_equals_source_narration_PCM_claimed': False, 'audible_quality_verdict': None, 'listening_or_human_approval': False}
    write(BASE / 'strict-decode-audio-summary.json', report)
    return report

def main():
    started = now()
    BASE.mkdir(exist_ok=False)
    write(BASE / 'metadata-read-failure-preserved.json', {'operation': 'initial offline text read only', 'requested_wrong_path': str(PRODUCER / 'actual-render-a01/CLOSED-MOVIE-DELIVERY-a01.json'), 'actual_delivery_is_at_producer_root': str(DELIVERY), 'error': 'FileNotFoundError before any media read/process', 'media_audit_retries': 0})
    if not pin(DELIVERY)['sha256'] == EXPECTED_DELIVERY:
        raise RuntimeError("audit prerequisite failed: pin(DELIVERY)['sha256'] == EXPECTED_DELIVERY")
    delivery = load(DELIVERY)
    media = Path(delivery['movie']['path'])
    if not delivery['state'] == 'ACTUAL_RENDER_RC0_CLOSED_PENDING_UNIQUE_WHOLE_AUDIT':
        raise RuntimeError("audit prerequisite failed: delivery['state'] == 'ACTUAL_RENDER_RC0_CLOSED_PENDING_UNIQUE_WHOLE_AUDIT'")
    if not (delivery['movie']['sha256'].lower() == EXPECTED_MEDIA_SHA and delivery['movie']['bytes'] == 1199061934):
        raise RuntimeError("audit prerequisite failed: delivery['movie']['sha256'].lower() == EXPECTED_MEDIA_SHA and delivery['movie']['bytes'] == 1199061934")
    identities = {key: check_small_identity(delivery[key]) for key in ['unique_streams_format_bound_probe', 'producer_receipt', 'actual_encode_command', 'actual_execute_result', 'input_source_snapshot', 'Root_actual_story_freeze']}
    if not load(delivery['actual_execute_result']['path'])['returncode'] == 0:
        raise RuntimeError("audit prerequisite failed: load(delivery['actual_execute_result']['path'])['returncode'] == 0")
    bound = load(delivery['unique_streams_format_bound_probe']['path'])
    if not (bound['subject']['bytes'] == delivery['movie']['bytes'] and bound['subject']['sha256'].lower() == EXPECTED_MEDIA_SHA):
        raise RuntimeError("audit prerequisite failed: bound['subject']['bytes'] == delivery['movie']['bytes'] and bound['subject']['sha256'].lower() == EXPECTED_MEDIA_SHA")
    video = next((s for s in bound['ffprobe']['streams'] if s['codec_type'] == 'video'))
    audio = next((s for s in bound['ffprobe']['streams'] if s['codec_type'] == 'audio'))
    if not len(bound['ffprobe']['streams']) == 2:
        raise RuntimeError("audit prerequisite failed: len(bound['ffprobe']['streams']) == 2")
    nf, ns = (delivery['actual_video_frames'], delivery['expected_48k_samples_from_actual_video_grid'])
    if not (nf == 52074 and ns == 83318400 and (int(video['nb_frames']) == nf)):
        raise RuntimeError("audit prerequisite failed: nf == 52074 and ns == 83318400 and (int(video['nb_frames']) == nf)")
    if not (video['time_base'] == audio['time_base'] == '1/48000' and video['duration_ts'] == audio['duration_ts'] == ns):
        raise RuntimeError("audit prerequisite failed: video['time_base'] == audio['time_base'] == '1/48000' and video['duration_ts'] == audio['duration_ts'] == ns")
    if not (video['width'], video['height'], video['avg_frame_rate']) == (1920, 1080, '30/1'):
        raise RuntimeError("audit prerequisite failed: (video['width'], video['height'], video['avg_frame_rate']) == (1920, 1080, '30/1')")
    if not (audio['sample_rate'], audio['channels'], audio['codec_name']) == ('48000', 2, 'aac'):
        raise RuntimeError("audit prerequisite failed: (audio['sample_rate'], audio['channels'], audio['codec_name']) == ('48000', 2, 'aac')")
    if not Decimal(bound['ffprobe']['format']['duration']) == Decimal('1735.8'):
        raise RuntimeError("audit prerequisite failed: Decimal(bound['ffprobe']['format']['duration']) == Decimal('1735.8')")
    media_before = stat(media)
    if not media_before['bytes'] == delivery['movie']['bytes']:
        raise RuntimeError("audit prerequisite failed: media_before['bytes'] == delivery['movie']['bytes']")
    tool_pins = {}
    for path in [FFMPEG, FFPROBE]:
        identity = load(PACKAGE / 'attempt-a01/PLAN-AND-ACTUAL-INPUTS-a01.json')['tool_pins'][path.name]
        if not stat(path)['bytes'] == identity['bytes']:
            raise RuntimeError('previously hashed media tool size changed')
        if not (identity['bytes'], identity['sha256']) == EXPECTED_FF[path.name]:
            raise RuntimeError("audit prerequisite failed: (identity['bytes'], identity['sha256']) == EXPECTED_FF[path.name]")
        tool_pins[path.name] = identity
    original = ROOT / 'e4-A-only-final-machine-audit-a01/audit_final_A_only01.py'
    preserved = BASE / 'source-original-A-only-auditor.py.txt'
    with preserved.open('xb') as handle:
        handle.write(original.read_bytes())
    with (BASE / 'SOURCE-ADAPTATION-a02.patch').open('x', encoding='utf-8', newline='\n') as handle:
        handle.writelines(difflib.unified_diff(original.read_text(encoding='utf-8-sig').splitlines(True), Path(__file__).read_text(encoding='utf-8').splitlines(True), fromfile='actual-A-only-auditor-preserved', tofile='actual-Review01-auditor'))
    plan = {'schema': 'xar.e04.closed-Review01-unique-whole-audit-plan.v1', 'started_utc': started, 'input_movie_identity_reused': delivery['movie'], 'producer_delivery': pin(DELIVERY), 'source_freeze_and_prior_probe_pins': identities, 'movie_stat_before': media_before, 'source_narration_identity_reused': delivery['source_narration_PCM'], 'interpreter': sys.executable, 'python_version': sys.version, 'tool_pins': tool_pins, 'expected_video_frames': nf, 'expected_audio_presentation_samples_per_channel': ns, 'operations': {'new_combined_full_frames_packets_probe': 1, 'new_strict_whole_video_AAC_decode': 1, 'new_source_PCM_sample_scan': 1, 'movie_SHA_rehash': 0, 'repeated_streams_format_probe': 0, 'old_RAW_movie_audit': 0, 'max_parallel_medium_processes': 2, 'codec_filter_threads_each': 1}, 'mixed_standalone_source_PCM_exists': False, 'mixed_decode_astats_and_boundary_only': True, 'human_1x_watch_listen_or_signoff': False, 'film_approved': False}
    write(BASE / 'PLAN-AND-ACTUAL-INPUTS-a02.json', plan)
    probe_argv = [str(FFPROBE), '-v', 'error', '-threads', '1', '-show_frames', '-show_packets', '-show_entries', 'frame=media_type,stream_index,pts,nb_samples,width,height,channels,duration,pix_fmt,best_effort_timestamp:packet=codec_type,stream_index,pts,dts,duration,flags:packet_side_data=side_data_type,skip_samples,discard_padding', '-of', 'json', str(media)]
    duration = Decimal(ns) / 48000
    filters = '[0:a:0]asplit=3[audit_in][front_in][back_in];[audit_in]ashowinfo,astats=metadata=0:reset=0[audit];[front_in]atrim=duration=1,asetpts=PTS-STARTPTS[front];[back_in]atrim=start=' + str(duration - 1) + ':end=' + str(duration) + ',asetpts=PTS-STARTPTS[back]'
    decode_argv = [str(FFMPEG), '-hide_banner', '-nostdin', '-loglevel', 'info', '-xerror', '-err_detect', 'explode', '-threads', '1', '-filter_threads', '1', '-filter_complex_threads', '1', '-i', str(media), '-filter_complex', filters, '-progress', 'pipe:1', '-stats_period', '20', '-map', '0:v:0', '-map', '[audit]', '-c:v', 'wrapped_avframe', '-c:a', 'pcm_s16le', '-threads:v', '1', '-threads:a', '1', '-fps_mode', 'passthrough', '-f', 'null', '-', '-map', '[front]', '-c:a', 'pcm_s16le', '-threads:a', '1', '-n', str(BASE / 'decoded-mix-front-1s.wav'), '-map', '[back]', '-c:a', 'pcm_s16le', '-threads:a', '1', '-n', str(BASE / 'decoded-mix-back-1s.wav')]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {'probe': pool.submit(owned_command, 'whole-frame-packet-probe', probe_argv), 'decode': pool.submit(owned_command, 'strict-whole-video-AAC-decode', decode_argv), 'source_PCM': pool.submit(source_pcm_scan, delivery['source_narration_PCM'], delivery['source_PCM_actual_header'])}
        results = {name: future.result() for name, future in futures.items()}
    probe_summary = analyze_probe(BASE / 'whole-frame-packet-probe/stdout.bin', video, audio, nf, ns)
    decode_summary = analyze_decode(results['decode'], nf, ns)
    after = stat(media)
    errors = probe_summary['errors'] + decode_summary['errors']
    if results['probe']['returncode'] != 0 or results['probe']['stderr']['bytes'] != 0:
        errors.append('full_probe_exit_or_stderr')
    if media_before != after:
        errors.append('movie_stat_changed_during_check')
    if probe_summary['audio_actual_decoded_sample_frames'] != decode_summary['AAC_sample_frames_per_channel']:
        errors.append('independent_probe_decode_sample_count_disagreement')
    report = {'schema': 'xar.e04.Review01-new-full-film-machine-audit.v1', 'state': 'PASS_MACHINE_STRUCTURE_COUNTS_AND_EXACT_AAC_CLOCK_ONLY' if not errors else 'RED_NEW_FILM_MACHINE_STRUCTURE_OR_CLOCK', 'started_utc': started, 'completed_utc': now(), 'errors': errors, 'actual_movie_identity_reused': delivery['movie'], 'producer_delivery': pin(DELIVERY), 'producer_prior_streams_format_bound_probe_reused': identities['unique_streams_format_bound_probe'], 'actual_video_duration_seconds': str(duration), 'actual_video_decoded_frames': decode_summary['video_decoded_frames'], 'actual_video_frame_and_packet_counts': [probe_summary['video_frames'], probe_summary['video_packets']], 'actual_audio_decoded_frames': decode_summary['AAC_decoded_frame_count'], 'actual_audio_sample_frames_per_channel': decode_summary['AAC_sample_frames_per_channel'], 'actual_audio_seconds': str(Decimal(decode_summary['AAC_sample_frames_per_channel']) / 48000), 'source_narration_sample_frames': results['source_PCM']['full_scan_sample_frames'], 'source_narration_rate': 24000, 'source_narration_seconds': '1735.776', 'audio_video_grid_tail_seconds': '0.024', 'exact_decoded_AAC_integer_clock': decode_summary['audio_original_integer_PTS_exact'], 'exact_packet_grid_and_priming_tail': not probe_summary['errors'], 'AAC_tail_actual_decoded_samples': decode_summary['tail_actual_nb_samples'], 'mixed_decoded_NaN_Inf_counters_zero': bool(decode_summary['NaN_Inf_counter_values']) and (not any(decode_summary['NaN_Inf_counter_values'])), 'decoded_float_peak_above_0dBFS': decode_summary['decoded_float_peak_above_0dBFS'], 'source_PCM_scan': pin(BASE / 'source-PCM-full-scan.json'), 'full_frame_packet_summary': pin(BASE / 'frame-packet-clock-summary.json'), 'strict_decode_audio_summary': pin(BASE / 'strict-decode-audio-summary.json'), 'full_frame_packet_result': pin(BASE / 'whole-frame-packet-probe/result.json'), 'strict_decode_result': pin(BASE / 'strict-whole-video-AAC-decode/result.json'), 'source_stat_before': media_before, 'source_stat_after': after, 'tool_pins': tool_pins, 'plan_and_inputs': pin(BASE / 'PLAN-AND-ACTUAL-INPUTS-a02.json'), 'medium_SHA_reads': 0, 'full_new_probe_count': 1, 'full_new_strict_decode_count': 1, 'full_source_PCM_scans': 1, 'old_RAW_movie_media_operations': 0, 'original_old_A_exactPTS_RED_preserved': True, 'new_formal_xar_promo_adapter_validation_claimed': False, 'all_argv_stdio_partials_source_preserved': True, 'native_event_exact_encoded_tick': None, 'fresh_human_watch_listen_1x': False, 'human_signoff': False, 'continuous_clean_source_review': False, 'film_approved': False, 'audio_subjective_quality_verdict': None, 'SDK_UI_Game_bus_Git_OneDrive_operations': 0}
    write(BASE / 'report.json', report)
    write(PACKAGE / 'ROOT-DELIVERY-a02.json', {'state': report['state'], 'report': pin(BASE / 'report.json'), 'frame_packet_summary': report['full_frame_packet_summary'], 'decode_audio_summary': report['strict_decode_audio_summary'], 'source_PCM_scan': report['source_PCM_scan'], 'audit_source': pin(Path(__file__)), 'actual_movie_identity_reused': delivery['movie'], 'producer_delivery': pin(DELIVERY), 'film_pending_human_review': True, 'human_signoff': False, 'continuous_clean_review': False, 'large_media_rehashes': 0, 'old_media_audits': 0, 'operations': plan['operations']})
    print(json.dumps({'state': report['state'], 'errors': errors, 'video_frames': report['actual_video_decoded_frames'], 'AAC_samples': report['actual_audio_sample_frames_per_channel'], 'AAC_last_actual_nb_samples': report['AAC_tail_actual_decoded_samples'], 'delivery': pin(PACKAGE / 'ROOT-DELIVERY-a02.json')}, indent=2), flush=True)
    return 0 if not errors else 1
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        if BASE.is_dir():
            with (BASE / 'UNEXPECTED-FAILURE-PRESERVED.txt').open('x', encoding='utf-8') as handle:
                handle.write(traceback.format_exc())
        raise
