"""Read existing Rakaly text endpoints; no native calls or RNG evaluation.

Inventories saved keys with RNG-like names, rather than claiming these contain
all engine or execution-context RNG. Repeated event ordinals are locations only.
"""
import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import re


def identity(path):
    p = pathlib.Path(path)
    with p.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest().upper()
    return {'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': digest}


def inventory(path):
    frames = []
    occurrences = collections.Counter()
    rows = []
    top = {}
    line_count = 0
    pattern = re.compile(r'^(\t*)([^\s={}]+)=(.*)$')
    with pathlib.Path(path).open('r', encoding='utf-8-sig') as f:
        for line_count, line in enumerate(f, 1):
            stripped = line.rstrip('\r\n')
            match = pattern.match(stripped)
            if not match:
                continue
            tabs, key, value = match.groups()
            depth = len(tabs)
            frames = [fr for fr in frames if fr['depth'] < depth]
            parent = '/'.join(fr['label'] for fr in frames)
            if value == '{':
                tag = (parent, key)
                occurrences[tag] += 1
                frames.append({'depth': depth, 'label': key + '#' + str(occurrences[tag])})
                continue
            if depth == 0 and key in ('random_seed', 'random_count', 'date', 'speed'):
                if key in top:
                    raise ValueError('duplicate serialized top-level ' + key)
                top[key] = {'line': line_count, 'raw_value': value}
            if not any(piece in key.lower() for piece in ('random', 'rng', 'seed')):
                continue
            path_name = (parent + '/' if parent else '') + key
            if depth == 0 and key in ('random_seed', 'random_count'):
                category = 'serialized-top-level-seed-or-count'
            elif parent.startswith('meta_data#') and 'portrait' in parent:
                category = 'portrait-seed-not-combat-rng'
            elif parent.startswith('triggered_event#') and '/scope#' in parent:
                category = 'queued-triggered-event-scope-seed'
            else:
                category = 'other-saved-rng-like-key-not-interpreted'
            rows.append({'path': path_name, 'line': line_count, 'key': key,
                         'raw_value': value, 'category': category})
    for key in ('random_seed', 'random_count'):
        if key not in top or not top[key]['raw_value'].isdigit():
            raise ValueError('serialized top-level numeric RNG field missing: ' + key)
        number = int(top[key]['raw_value'])
        if not 0 <= number < 2**32:
            raise ValueError('serialized top-level RNG field out of uint32 range')
        top[key]['uint32'] = number
    return {'source': identity(path), 'line_count': line_count,
            'top_level': top, 'named_field_occurrences': rows,
            'category_counts': dict(collections.Counter(r['category'] for r in rows)),
            'key_counts': dict(collections.Counter(r['key'] for r in rows))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-melted', required=True)
    parser.add_argument('--after-melted', required=True)
    parser.add_argument('--before-raw', required=True)
    parser.add_argument('--after-raw', required=True)
    parser.add_argument('--decoder-before-receipt', required=True)
    parser.add_argument('--decoder-after-receipt', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = pathlib.Path(args.output)
    if out.exists():
        raise FileExistsError('create-only output already exists')
    before, after = inventory(args.before_melted), inventory(args.after_melted)
    raw = {'before': identity(args.before_raw), 'after': identity(args.after_raw)}
    decoders = {}
    for side, path in (('before', args.decoder_before_receipt), ('after', args.decoder_after_receipt)):
        command = json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))
        if command['raw']['sha256'] != raw[side]['sha256'] or command['raw']['bytes'] != raw[side]['bytes']:
            raise ValueError('decoder original save binding differs')
        decoders[side] = {'receipt': identity(path), 'original_command': command}
    comparison = {}
    for key in ('random_seed', 'random_count'):
        left, right = before['top_level'][key]['uint32'], after['top_level'][key]['uint32']
        comparison[key] = {'before': left, 'after': right, 'equal': left == right,
                           'uint32_delta_modulo': (right-left) % 2**32}
    report = {'schema_version': 1, 'kind': 'EXISTING_SERIALIZED_RNG_FIELD_ENDPOINT_INVENTORY',
              'created_at_utc': datetime.datetime.now(datetime.UTC).isoformat(),
              'reader': identity(__file__), 'raw_saves': raw, 'decoder_commands': decoders,
              'before': before, 'after': after, 'top_level_comparison': comparison,
              'all_rng_unchanged': 'UNKNOWN', 'local_selector_rng_unchanged': 'UNKNOWN',
              'notification_context_rng_unchanged': 'UNKNOWN',
              'scope_seed_rows_paired_as_same_event_instances': False,
              'snapshot_time_resolution': 'saved endpoint only',
              'limits': [
                  'Seed/count equality can prove only equality of these serialized endpoint fields.',
                  'RNG-like key inventory is not an exhaustive map of every engine/context RNG.',
                  'Portrait seeds are separate from battle RNG.',
                  'Queued event location ordinals do not identify the same event instance across saves.',
                  'Equal saved endpoints do not rule out transient advancement or restoration between endpoints.',
                  'No new UI-window files, whole-engine RNG state, or unsaved execution-context state are inferred.'
              ], 'game_calls': 0, 'desktop_inputs': 0, 'master_intake': False}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'report': identity(out), 'top_level_comparison': comparison,
                      'before_counts': before['category_counts'], 'after_counts': after['category_counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
