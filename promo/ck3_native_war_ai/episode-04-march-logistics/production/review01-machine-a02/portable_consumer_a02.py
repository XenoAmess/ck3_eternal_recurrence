"""Stdlib-only verification of copied audit metadata, not a new media audit.

This verifies portable catalog bytes and the completed report's exact identities
and acceptance scope. It does not re-read the movie, render, listen, infer human
approval, or validate media facts independently of the preserved report.
"""
from pathlib import Path, PurePosixPath
import csv, hashlib, json, sys

EXPECTED_MOVIE_SHA = 'a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346'
EXPECTED_STATE = 'PASS_MACHINE_STRUCTURE_COUNTS_AND_EXACT_AAC_CLOCK_ONLY'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def load(path):
    require(path.is_file() and not path.is_symlink(), 'missing or linked metadata: ' + str(path))
    require(path.stat().st_size <= 5_000_000, 'metadata size bound exceeded')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def verify(root):
    root = root.resolve(strict=True)
    manifest = load(root / 'manifest.json')
    require(manifest['schema'] == 'xar.e04.Review01-portable-machine-audit-metadata.v1', 'wrong catalog schema')
    files = manifest['files']
    require(isinstance(files, list) and 1 <= len(files) <= 100, 'wrong catalog file count')
    seen = set()
    for record in files:
        rel = record['relative_path']
        pure = PurePosixPath(rel)
        require(isinstance(rel, str) and '\\' not in rel and ':' not in rel, 'portable path syntax')
        require(not pure.is_absolute() and rel == pure.as_posix() and all(x not in ('', '.', '..') for x in pure.parts), 'path escape')
        require(rel not in seen and rel != 'manifest.json', 'duplicate or self catalog path')
        seen.add(rel)
        path = root.joinpath(*pure.parts)
        require(path.resolve(strict=True).is_relative_to(root), 'resolved path escape')
        require(path.is_file() and not path.is_symlink(), 'not a regular file')
        require(path.suffix in ('.json', '.py', '.txt', '.md', '.csv'), 'text-only catalog violated')
        size = path.stat().st_size
        require(size <= 5_000_000 and size == record['bytes'], 'copied file byte count changed: ' + rel)
        data = path.read_bytes()
        data.decode('utf-8-sig')
        require(hashlib.sha256(data).hexdigest() == record['sha256'], 'copied file SHA changed: ' + rel)
    actual = {x.relative_to(root).as_posix() for x in root.rglob('*') if x.is_file()}
    require(actual == seen | {'manifest.json'}, 'uncataloged file or missing catalog entry')
    report = load(root / 'actual/report.json')
    require(report['state'] == EXPECTED_STATE and report['errors'] == [], 'actual movie audit was not PASS')
    movie = report['actual_movie_identity_reused']
    require(movie['bytes'] == 1199061934 and movie['sha256'].lower() == EXPECTED_MOVIE_SHA, 'movie identity differs')
    require(report['actual_video_decoded_frames'] == 52074, 'video decoded count differs')
    require(report['actual_video_frame_and_packet_counts'] == [52074, 52074], 'video frame packet count differs')
    require(report['actual_audio_sample_frames_per_channel'] == 83318400, 'AAC sample count differs')
    require(report['exact_decoded_AAC_integer_clock'] is True and report['exact_packet_grid_and_priming_tail'] is True, 'AAC timing audit incomplete')
    require(report['source_narration_sample_frames'] == 41658624 and report['source_narration_rate'] == 24000, 'source narration count differs')
    for name in ('human_signoff', 'film_approved', 'fresh_human_watch_listen_1x', 'continuous_clean_source_review'):
        require(report[name] is False, 'machine report escalated to human or continuous clean approval')
    require(report['medium_SHA_reads'] == 0 and report['old_RAW_movie_media_operations'] == 0, 'media operation scope differs')
    count = 0
    endpoint = 0
    last_samples = None
    with (root / 'actual/decoded-AAC-frame-clock.csv').open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == ['ordinal', 'pts_samples', 'nb_samples', 'rate', 'channels', 'pts_time_text'], 'decoded clock table schema differs')
        for row in reader:
            ordinal, pts, samples, rate, channels = (int(row[k]) for k in ('ordinal', 'pts_samples', 'nb_samples', 'rate', 'channels'))
            require(ordinal == count and pts == endpoint, 'decoded clock table ordinal or original PTS gap')
            require(samples > 0 and rate == 48000 and channels == 2, 'decoded clock table frame metadata')
            endpoint = pts + samples
            last_samples = samples
            count += 1
    require(count == 81366 and endpoint == 83318400 and last_samples == 640, 'decoded clock table total or observed short tail differs')
    return {'state': 'PASS_PORTABLE_METADATA_ONLY', 'catalog_files': len(files),
            'catalog_total_bytes': sum(x['bytes'] for x in files), 'bound_movie_sha256': EXPECTED_MOVIE_SHA,
            'new_media_read_or_probe': False, 'human_signoff': False,
            'actual_media_facts_independently_revalidated': False,
            'preserved_decoded_clock_table_rows_checked': count,
            'preserved_decoded_clock_table_endpoint_samples': endpoint}

if __name__ == '__main__':
    require(len(sys.argv) == 2, 'Usage: python -B portable_consumer_a02.py PACKAGE_DIRECTORY')
    print(json.dumps(verify(Path(sys.argv[1])), ensure_ascii=False))
