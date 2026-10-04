"""Clarify full actor delta from already parsed immutable resource evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys
import copy

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent
PRIOR = EXT / 'r6-resource-and-elector-origin-resume-20261005-003'
HELPER = EXT / 'r6-baseline-readback-001/helper-v2/r6_i2_readback.py'
spec = importlib.util.spec_from_file_location('r6_actor_fields_helper', HELPER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from xar_autoplayer.simulation.knight_causal_save_projection import delta

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out:
        out.write(raw)

def js(path, value):
    write(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

def normalized(entries):
    out = copy.deepcopy(entries)
    alive = m.one(out, 'alive_data', required=True)
    variables = m.one(alive, 'variables', required=True)
    records = {}
    for row in m.one(variables, 'data', required=True):
        flag = m.unquote(m.one(row['value'], 'flag', required=True))
        records.setdefault(flag, []).append(row['value'])
    for row in variables:
        if row['key'] == 'data':
            row['value'] = []
    return out, records

def main():
    assert not (ROOT / 'REPORT.json').exists()
    projections, rows, inputs = {}, {}, []
    for label in ['0036-actual-dplus2', '0040-resources']:
        path = PRIOR / 'evidence' / label / 'character-31254.excerpt.txt'
        raw = path.read_bytes()
        write(ROOT / 'inputs' / (label + '-character-31254.excerpt.txt'), raw)
        inputs.append({'path': str(path), 'bytes': len(raw), 'sha256': sha(path)})
        projections[label], rows[label] = normalized(m.parsed(raw.decode()))
    old, new = (rows[label] for label in projections)
    variable_delta = {'added_flags': sorted(set(new) - set(old)), 'removed_flags': sorted(set(old) - set(new)),
                      'altered_existing_flags': sorted(flag for flag in set(old) & set(new) if old[flag] != new[flag]),
                      'unchanged_existing_flag_count': sum(old[flag] == new[flag] for flag in set(old) & set(new))}
    other_delta = delta(*projections.values())
    report = {'schema': 'lyd.r6-resource-actor-fields-supplement.v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'game_called': False, 'native_called': False, 'git_called': False, 'tracked_written': False,
              'prior_report': {'path': str(PRIOR / 'REPORT.json'), 'sha256': sha(PRIOR / 'REPORT.json')},
              'scope': 'Existing exact31254 excerpts only. Variable arrays are keyed by actual saved flag while retaining all duplicate occurrences per flag; insertion positions do not masquerade as flag changes. Other complete character fields retain lossless parsed structure.',
              'inputs': inputs, 'actual_all_saved_flag_delta': variable_delta, 'other_actor_lossless_field_delta': other_delta,
              'conclusions': {'all_prior_saved_flag_occurrences_exactly_unchanged': not variable_delta['removed_flags'] and not variable_delta['altered_existing_flags'],
                              'additional_observed_fields': 'Saved income7.2965→6.22214 and accumulatedpiety1035→10035 also changed. Accumulatedpiety delta+9000 matches the explicit resource effect; income cause is not established by this readback.',
                              'pass_boundary': 'Prior PASS_RESOURCE_FIXTURE_ONLY proves specified resource amounts, no additional existing LYD mutations, unchanged other complete character records and Faith/Rite/title graphs. It does not mean all actor fields except currency are identical.'}}
    assert report['conclusions']['all_prior_saved_flag_occurrences_exactly_unchanged']
    assert len(variable_delta['added_flags']) == 7
    assert set(row['path'] for row in other_delta) == {'/alive_data[0]/gold[0]/value[0]', '/alive_data[0]/income[0]', '/alive_data[0]/piety[0]/accumulated[0]', '/alive_data[0]/piety[0]/currency[0]'}
    js(ROOT / 'REPORT.json', report)
    write(ROOT / 'REPORT.md', ('# R6 actor resource-field clarification\n\n' + report['conclusions']['additional_observed_fields'] + '\n\nAll original saved flags, including non-LYD flags, retain exact occurrences. Only seven resource fixture flags were added; apparent shifted array positions in the prior lossless delta are insertions, not changed existing flags.\n\n' + report['conclusions']['pass_boundary'] + '\n').encode())
    js(ROOT / 'INDEX.json', {'files': [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(ROOT.rglob('*')) if path.is_file()]})
    print(json.dumps({'report_sha256': sha(ROOT / 'REPORT.json'), 'index_sha256': sha(ROOT / 'INDEX.json'), 'flag_delta': variable_delta, 'other_delta': other_delta}, ensure_ascii=False))

if __name__ == '__main__':
    main()
