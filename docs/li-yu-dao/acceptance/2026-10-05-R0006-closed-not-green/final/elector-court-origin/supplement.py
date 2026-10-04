"""Read only immutable saved council correspondence; no game or native calls."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
EXT = ROOT.parent
PRIOR = EXT / 'r6-resource-and-elector-origin-resume-20261005-003'
SUPPORT = EXT / 'r6-resource-and-elector-origin-resume-20261005-002/readback_world_and_origin.py'
spec = importlib.util.spec_from_file_location('r6_origin_supplement_support', SUPPORT)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as out:
        out.write(data)

def js(p, obj):
    write(p, (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode())

def scalar_projection(row):
    return {k: row[k] for k in ['id', 'section', 'first_name', 'birth', 'culture', 'rite_id', 'organization', 'saved_base_learning', 'actual_court_employer', 'actual_council_task', 'join_court_date', 'is_in_the_council_saved_flag_present', 'lyd_variables', 'lyd_lists']}

def main():
    assert not (ROOT / 'REPORT.json').exists()
    report = {'schema': 'lyd.r6-elector-court-origin-supplement.v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'game_called': False, 'native_called': False, 'git_called': False, 'tracked_written': False,
              'scope': 'Two immutable snapshots and existing full-world result. Only inspect actual council replacement and own rite; no event action or fabricated appointment trace.',
              'prior_report': {'path': str(PRIOR / 'REPORT.json'), 'sha256': sha(PRIOR / 'REPORT.json')},
              'snapshots': {}, 'source_references': []}
    for label in ['0030-setup', '0036-actual-dplus2']:
        dirname, expected = c.SAVES[label]
        save = c.LIVE / 'checkpoints' / dirname / 'save.ck3'
        stat = save.stat()
        assert sha(save) == expected
        text = save.read_bytes().decode('utf-8-sig').replace('\r\n', '\n')
        selected = json.loads((PRIOR / 'evidence' / label / 'selected-character-state.json').read_bytes())
        rows = {cid: scalar_projection(selected[cid]) for cid in ['34232', '34973', '59621', '65856', '65857'] if cid in selected}
        for section, following in c.SECTIONS:
            body = c.m.r3.section(text, section, following)
            matches = list(re.finditer(r'(?ms)^59758=\{\n.*?^\}', body))
            for ordinal, match in enumerate(matches):
                raw = match.group(0)
                p = ROOT / 'evidence' / label / ('character-59758-' + section + '-' + str(ordinal) + '.excerpt.txt')
                write(p, (raw + '\n').encode())
                row = c.parse_character(raw, section)
                rows.setdefault('59758', []).append(scalar_projection(row))
        taskrows = {}
        for tid in ['506', '1359']:
            path = PRIOR / 'evidence' / label / ('council-task-' + tid + '.excerpt.txt')
            raw = path.read_bytes()
            write(ROOT / 'evidence' / label / path.name, raw)
            taskrows[tid] = c.m.parsed(raw.decode())
        report['snapshots'][label] = {'save': str(save), 'sha256': expected, 'characters': rows, 'council_tasks': taskrows}
        assert sha(save) == expected and save.stat().st_mtime_ns == stat.st_mtime_ns
    report['conclusions'] = {
        'foreign_ruler_34973_own_rite': [report['snapshots'][x]['characters']['34973']['rite_id'] for x in ['0030-setup', '0036-actual-dplus2']],
        'foreign_ruler_34232_own_rite': [report['snapshots'][x]['characters']['34232']['rite_id'] for x in ['0030-setup', '0036-actual-dplus2']],
        'task1359_original_to_new_owner': ['59621', '65860'],
        'task506_original_to_new_owner': ['59758', '65861'],
        'mechanism_boundary': 'Observed saved court-task owner replacement and same-rite new adult clergy are consistent with loaded auto_fill/fill_from_pool/pool_court_chaplain rules. Original native creation and appointment calls are not present; unique causation is not proven.',
        'proposal_creation_excluded': '65860 and65861 already exist in0036 and0040. Full world0040-to0042 comparison had no character additions or deletions.'}
    source = PRIOR / 'source/06-00_council_positions.txt'
    pool = PRIOR / 'source/08-00_clergy.txt'
    fixture = PRIOR / 'source/02-lyd_r4_fixture_effects.txt'
    for path in [source, pool, fixture, SUPPORT]:
        report['source_references'].append({'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size})
    js(ROOT / 'REPORT.json', report)
    lines = ['# R6 foreign-court clergy supplement', '',
             'The two foreign rulers changed their own saved rite from ' + str(report['conclusions']['foreign_ruler_34973_own_rite'][0]) + ' to ' + str(report['conclusions']['foreign_ruler_34973_own_rite'][1]) + ' (34973) and from ' + str(report['conclusions']['foreign_ruler_34232_own_rite'][0]) + ' to ' + str(report['conclusions']['foreign_ruler_34232_own_rite'][1]) + ' (34232) between0030 and0036.', '',
             'The same saved religious-relations council task1359 changed owner59621 to65860; task506 changed owner59758 to65861. New councillors already exist before resources and the C2 proposal.', '',
             report['conclusions']['mechanism_boundary'], '',
             'Old councillor and foreign-ruler scalar records, original exact59758 character excerpts, and both original council-task excerpts are retained in REPORT.json and evidence/. No total Learning or hidden event decision is reconstructed.']
    write(ROOT / 'REPORT.md', ('\n'.join(lines) + '\n').encode())
    index = {'schema': 'lyd.external-evidence-index.v1', 'files': []}
    for path in sorted(ROOT.rglob('*')):
        if path.is_file():
            index['files'].append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': sha(path)})
    js(ROOT / 'INDEX.json', index)
    print(json.dumps({'report': str(ROOT / 'REPORT.json'), 'report_sha256': sha(ROOT / 'REPORT.json'), 'index_sha256': sha(ROOT / 'INDEX.json'), 'conclusions': report['conclusions']}))

if __name__ == '__main__':
    main()
