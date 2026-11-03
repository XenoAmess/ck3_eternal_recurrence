"""Finite DATA-only first-N/FIFO retention arithmetic. No native custody authority."""
import argparse
from collections import OrderedDict
import json
from pathlib import Path
import sys

ORDER = (
    'publication_attempts', 'held_path_attempts', 'acquisition_attempts',
    'acquired_retained', 'acquired_unretained', 'fallback_attempts',
    'entry_bound', 'handle_bound', 'byte_bound', 'peak_entries',
    'peak_retained_bytes', 'current_entries_before_finish',
    'current_bytes_before_finish', 'retired_pairs',
)

def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(name + ' is outside its finite integer range')
    return value

def validate(caps, publications):
    if type(caps) is not list or len(caps) != 3:
        raise ValueError('caps must be [entries, bytes, handles]')
    entries = integer(caps[0], 1, 4096, 'entries')
    budget = integer(caps[1], 1, 268435456, 'bytes')
    handles = integer(caps[2], 4, 8192, 'handles')
    if type(publications) is not list or len(publications) > 100000:
        raise ValueError('trace must be a list with at most 100000 rows')
    identities = {}
    for row in publications:
        if type(row) is not list or len(row) != 3:
            raise ValueError('row must be [id, payload_bytes, pair_bytes]')
        key, payload, pair = row
        if type(key) is not str or not 1 <= len(key) <= 256:
            raise ValueError('id must be nonempty bounded text')
        integer(payload, 0, 67108864, 'payload_bytes')
        integer(pair, payload, 2**63-1, 'pair_bytes')
        sizes = (payload, pair)
        if key in identities and identities[key] != sizes:
            raise ValueError('same id cannot change its payload or pair charge')
        identities[key] = sizes
    return entries, budget, handles

def simulate(caps, publications, policy):
    maximum_entries, maximum_bytes, maximum_handles = validate(caps, publications)
    if policy not in ('firstN', 'FIFO'):
        raise ValueError('policy must be firstN or FIFO')
    held = OrderedDict()
    used = 0
    counts = dict.fromkeys(ORDER, 0)
    def admission(payload):
        return (len(held) < maximum_entries
                and len(held)*2 <= maximum_handles-4
                and payload <= (maximum_bytes-used)//2)
    for key, payload, pair in publications:
        counts['publication_attempts'] += 1
        if key in held:
            counts['held_path_attempts'] += 1
            continue
        admitted = admission(payload)
        if (not admitted and policy == 'FIFO' and held
                and (len(held) >= maximum_entries
                     or len(held)*2 > maximum_handles-4)):
            oldest = next(iter(held))
            freed = held[oldest]
            if payload <= (maximum_bytes-(used-freed))//2:
                # DATA model assumes successful double-close; no native failures simulated.
                del held[oldest]
                used -= freed
                counts['retired_pairs'] += 1
                admitted = admission(payload)
        if admitted:
            counts['acquisition_attempts'] += 1
            if pair <= maximum_bytes-used:
                held[key] = pair
                used += pair
                counts['acquired_retained'] += 1
                counts['peak_entries'] = max(counts['peak_entries'], len(held))
                counts['peak_retained_bytes'] = max(counts['peak_retained_bytes'], used)
            else:
                counts['acquired_unretained'] += 1
        else:
            counts['fallback_attempts'] += 1
            if len(held) >= maximum_entries:
                counts['entry_bound'] += 1
            elif len(held)*2 > maximum_handles-4:
                counts['handle_bound'] += 1
            elif payload > (maximum_bytes-used)//2:
                counts['byte_bound'] += 1
            else:
                raise AssertionError('admission and first-failed predicate disagree')
    counts['current_entries_before_finish'] = len(held)
    counts['current_bytes_before_finish'] = used
    return counts

def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    arguments = parser.parse_args()
    with arguments.input.open('rb') as source:
        raw = source.read(1048577)
    if len(raw) > 1048576:
        raise ValueError('finite 1MiB input required')
    def bad_constant(value):
        raise ValueError('nonfinite JSON constant')
    request = json.loads(raw.decode('utf-8'), object_pairs_hook=strict_object,
                         parse_constant=bad_constant)
    if type(request) is not dict or set(request) != {'caps', 'trace'}:
        raise ValueError('input must contain exactly caps and trace')
    result = {p: simulate(request['caps'], request['trace'], p) for p in ('firstN', 'FIFO')}
    result['qualification'] = 'synthetic DATA arithmetic only; no IO, identity, close-failure, timing, or actual workload inference'
    print(json.dumps(result, separators=(',', ':')))

if __name__ == '__main__':
    try:
        main()
    except (OSError, UnicodeError, ValueError) as problem:
        print(type(problem).__name__ + ': ' + str(problem), file=sys.stderr)
        raise SystemExit(2)
