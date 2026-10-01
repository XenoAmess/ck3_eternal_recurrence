"""Create-only static review receipts. No game, desktop, Git, or process access."""
import sys
sys.dont_write_bytecode = True
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import capstone
import pefile

ROOT = Path(__file__).resolve().parent
BASE = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
READY = BASE / 'R0141-ui-hidden-modal-repair-other-a01/source-freeze-ui-hidden-modal-a02/source-ready-and-test-receipt.json'
STATIC = BASE / 'R0141-modal-admission-diagnosis-other-a01/static-modal-anchors-a01.json'

def meta(path):
    p = Path(path)
    data = p.read_bytes()
    return {'path': str(p), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest().upper()}

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def verify_descriptor(d):
    got = meta(d['path'])
    if got['bytes'] != d['bytes'] or got['sha256'] != d['sha256'].upper():
        raise AssertionError({'expected': d, 'actual': got})
    return got

def nested_files(x):
    if isinstance(x, dict):
        if {'path', 'bytes', 'sha256'} <= x.keys():
            yield x
        else:
            for value in x.values():
                yield from nested_files(value)
    elif isinstance(x, list):
        for value in x:
            yield from nested_files(value)

def save_new(name, data):
    path = ROOT / name
    with path.open('xb') as f:
        f.write(data)
    return meta(path)

ready = load(READY)
assert meta(READY)['sha256'] == 'BED9386BAD72A03160BBDFC2BCA0C6B4268BC8C3274580EACEBA6A6018FC334F'
sources = []
diff_lines = []
for row in ready['sources']:
    verified = {name: verify_descriptor(row[name]) for name in ('current', 'frozen_copy', 'previous_fda')}
    current = Path(verified['current']['path']).read_bytes()
    copy = Path(verified['frozen_copy']['path']).read_bytes()
    prior = Path(verified['previous_fda']['path']).read_bytes()
    assert current == copy
    assert (current != prior) == row['changed']
    sources.append({'relative_path': row['relative_path'], 'changed': row['changed'], **verified,
                    'same_current_and_frozen_bytes': True,
                    'unchanged_baseline_bytes': current == prior})
    if row['changed']:
        diff_lines.extend(difflib.unified_diff(prior.decode('utf-8-sig').splitlines(True),
                         current.decode('utf-8-sig').splitlines(True),
                         fromfile=str(verified['previous_fda']['path']),
                         tofile=str(verified['current']['path'])))
assert sum(s['changed'] for s in sources) == 4
diff_receipt = save_new('four-source-diff-a01.txt', ''.join(diff_lines).encode('utf-8'))

evidence = {}
for d in nested_files(ready):
    got = verify_descriptor(d)
    evidence[got['path']] = got
anchors = load(STATIC)
evidence[str(STATIC)] = meta(STATIC)
for d in nested_files(anchors):
    got = verify_descriptor(d)
    evidence[got['path']] = got

original = next(f for f in anchors['functions'] if f['name'] == 'NativeShortcutManagerActivate')
exe = Path(anchors['executable']['path'])
pe = pefile.PE(str(exe), fast_load=True)
begin, end = int(original['rva_begin'], 16), int(original['rva_end'], 16)
file_offset = pe.get_offset_from_rva(begin)
with exe.open('rb') as f:
    f.seek(file_offset)
    actual_bytes = f.read(end - begin)
assert actual_bytes == Path(original['raw']['path']).read_bytes()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
instructions = [{'rva': hex(i.address), 'bytes': bytes(i.bytes).hex(),
                 'mnemonic': i.mnemonic, 'operands': i.op_str}
                for i in md.disasm(actual_bytes, begin)]
assert instructions == original['instructions']
by_rva = {i['rva']: i for i in instructions}
assert by_rva['0x36e1c70']['bytes'] == '4d63909c020000'
assert by_rva['0x36e1c80']['bytes'] == '4d8b8090020000'
assert by_rva['0x36e1c93']['bytes'] == '498b0cc0'
assert by_rva['0x36e1c97']['bytes'] == 'f681d000000008'
assert by_rva['0x36e1c9e']['bytes'] == '7408'
pe.close()

build_path = Path(ready['verification']['actual_build_receipt']['path'])
build = load(build_path)
for d in nested_files(build):
    got = verify_descriptor(d)
    evidence[got['path']] = got
assert all(s['returncode'] == 0 for s in build['steps'])
assert not build['full_DLL_linked'] and not build['new_live_pass_claim']
junit = ET.parse(ready['verification']['CTest_JUnit']['path']).getroot()
assert junit.attrib['tests'] == '1' and junit.attrib['failures'] == '0'
fixture_stdout = Path(ready['verification']['native_fixture_original_stdout']['path']).read_text(encoding='utf-8')
python_stderr = Path(ready['verification']['python_UI_stderr']['path']).read_text(encoding='utf-8')
assert '15 bounded/hidden/visible/mixed/null/unreadable cases and 2 actual serializer checks PASS' in fixture_stdout
assert 'Ran 24 tests' in python_stderr and python_stderr.rstrip().endswith('OK')
assert Path(ready['verification']['sources_before']['path']).read_bytes() == Path(ready['verification']['sources_after']['path']).read_bytes()

checks = [
    {'id': 'EXACT_ORIGINAL_ABI', 'status': 'PASS_STATIC',
     'evidence': 'Original EXE SHA, complete 245-byte function range, and every Capstone instruction independently matched frozen original bytes.',
     'interpretation': 'Original sign-extends count+29C, reads vector+290 with stride8, and skips each receiver whose D0 bit08 is set. A visible receiver reaches original descendant check against the absolute top; new global navigation policy refuses every visible receiver conservatively.'},
    {'id': 'BOUNDED_FAIL_CLOSED_MODAL_READ', 'status': 'PASS_SOURCE_REVIEW',
     'location': 'ingame_ui_navigation_v1.cpp:62',
     'evidence': 'Signed count0..256, required readable non-null vector when count>0, required non-null entry, D0 byte read, mandatory equal header re-read. Zero-count may have null vector. Negative/oversize/bad reads/header change reject. No names or descendant bypass.'},
    {'id': 'HIDDEN_VISIBLE_SEMANTICS', 'status': 'PASS_SOURCE_AND_EXISTING_OFFLINE_TEST',
     'evidence': 'B8 has bit08 and allows; D0=0 and local-hidden10 alone reject; mixed vectors reject regardless of order; all256 hidden allow. Mask08 is unchanged in supporting header.'},
    {'id': 'OWNER_PAUSE_FULL_ID_PRESERVED', 'status': 'PASS_DIFF_REVIEW',
     'location': 'ingame_ui_navigation_v1.cpp:494',
     'evidence': 'Only old modal_count==0 block replaced. Existing exact-build/no-offline-override/snapshot paused/map/actor/stamp date/thread/pump/GUI double-binding guards remain identical. Char fullID18, unit fullID10/actor/native army/backref, combat fullID8/player-army scope, MilitaryView owner and hover/fit context guards remain identical. Frontend/bridge/TLS/action ticket and after-binding dependencies unchanged byte-for-byte.'},
    {'id': 'ACTION_SCOPE_AND_OUTCOME', 'status': 'PASS_DIFF_REVIEW',
     'evidence': 'All actions use one modal helper after current GUI binding; query early return remains read-only. Dispatch still verification_pending; no new public pointer parameter, pixel signoff, date advance, or game-state write added by this modal helper.'},
    {'id': 'RAW_FAILURE_DIAGNOSTICS', 'status': 'PASS_SOURCE_AND_EXISTING_OFFLINE_TEST',
     'evidence': 'Unread header serializes receiver_count:null. Actual addresses/raw flags are recorded when read. Failure does not create an observed zero count. Serializer fixture checks null count and raw flags184.'},
    {'id': 'EXISTING_ACTUAL_TEST_RESULTS', 'status': 'PASS_REHASHED_EXISTING_PROCESS_EVIDENCE',
     'evidence': 'Five recorded steps exit0; three actual Release TUs compiled; native CTest1/failures0; production helper fixture15 cases+serializer2; Python24/OK. Rehashed stdio/objects/argv/JUnit and source-before/after. Configure stderr44733B exists; other build/CTest/fixture stderr empty. No test rerun in this independent review.',
     'coverage_limit': 'Header-change rejection is reviewed in production source; supplied offline helper fixture does not dynamically change a header during reading. Full DLL link and fresh actual UI success are not supplied by this receipt.'}
]
receipt = {
    'schema': 'ck3.R0141.hidden-modal-independent-readonly-review/v1',
    'kind': 'READONLY_STATIC_SOURCE_AND_EXISTING_OFFLINE_EVIDENCE_NOT_LIVE_TRUTH',
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer': '/root/a04_knights_evidence',
    'status': 'PASS_NARROW_REVIEW_NO_MATERIAL_FINDINGS',
    'source_freeze': meta(READY),
    'baseline_private_source': ready['private_source_base'],
    'four_source_diff': diff_receipt,
    'sources': sources,
    'original_function': {'executable': meta(exe), 'rva_begin': hex(begin), 'rva_end': hex(end),
                          'original_raw': meta(original['raw']['path']), 'exact_exe_bytes_match': True,
                          'independent_disassembly_matches': True, 'instructions': instructions},
    'checks': checks,
    'material_findings': [],
    'existing_process_evidence': {'build_receipt': meta(build_path), 'steps': build['steps'],
                                  'CTest_tests': 1, 'CTest_failures': 0, 'Python_UI_tests': 24,
                                  'native_fixture_original_stdout': fixture_stdout,
                                  'source_before_after_identical': True},
    'evidence_index': sorted(evidence.values(), key=lambda x: x['path']),
    'boundaries': {'source_written_by_review': False, 'original_assets_modified': False,
                   'new_build_or_tests_run': False, 'game_or_process_read_called': False,
                   'desktop_Steam_Git_master_action': False, 'full_DLL_linked_here': False,
                   'live_success_proven_by_review': False, 'R0141_date_advancement': 0,
                   'R0141_no_day_fact_source': 'Parent reported actual run RED/no advancement and SDK cleanup; this review does not re-run or infer after-state.',
                   'six_gaps_closed': False, 'global_bundle_complete': False,
                   'human_approval_created': False, 'video_modified': False},
    'script': meta(__file__), 'interpreter': str(Path(sys.executable)), 'python_version': sys.version
}
result = save_new('readonly-source-review-a01.json', (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'status': receipt['status'], 'receipt': result, 'diff': diff_receipt, 'checks': len(checks),
                  'files_rehashed': len(evidence)}, ensure_ascii=False))
