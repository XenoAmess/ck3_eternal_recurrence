"""RAM-only Source22 composition over the frozen Source21 logical inventory.

Source21 has no separate canonical anchor. Its five exact output refs extend
the actual Source20 f198 anchor. This adds two qualified helpers and exact
Driver/MCP patches; it never writes full production leaves, Git, or SDK views.
The clock addition is an error diagnostic, not a clock root-cause repair.
"""
from __future__ import annotations

import ast
import copy
from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
BASE = 'f19864de1cc073eed62617faad2307c57ad45a97'
PREFIX = 'ck3_autonomous_player/src/'
OLD_FREEZE = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C18.json')
OLD_FREEZE_PIN = (375083, '624c0a229abea3241474e31958bfe4b4102e970f7032f3fc9821273a15ee1d5b')
S20 = 'docs/ck3-native-ai/evidence/source20-minimal-warm-sdk-source-qualification-2026-10-20.json'
S21 = 'docs/ck3-native-ai/evidence/source21-longterm-sdk-source-qualification-2026-10-20.json'
S21_PLAN = 'docs/ck3-native-ai/evidence/source21-longterm-sdk-source-plan-2026-10-20.json'
S20_ROWS = (371996, '7b62abe6c91e382af449b1c7057bf304d729db310ad88deea4861218c8379935')
S21_ROWS = (371996, 'c4b506600cca3f78b90b41e9daf8475bf337c350d9dff6eebc661ea273f602ba')
DRIVER = 'xar_autoplayer/bridge/native_driver.py'
MCP = 'xar_autoplayer/bridge/mcp_server.py'
WAL = 'xar_autoplayer/bridge/succession_binding_refresh_wal_v1.py'
DIAG = 'xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py'
DRIVER_BASE = (1637048, 'cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab')
MCP_BASE = (264359, '8b1c260f779dbd3e25770af75ed87de0cfd39200454c7662f611accfce92688f')
WAL_DRIVER = (1639164, '15defa9d4a7c2ea778b78720afb65db556a59c0fe071f703c53cce3eceb5705d')
A0_DRIVER = (1638219, 'b26db9389bb5e015e5607122c3d0eb8cf66fe828df0e2036419683e3cd6f8eb1')
A0_MCP = (264620, '75e01e9b117fd6a64de10b7971a65a0571ffe3923e93aa7065f166987ab05de5')
WAL_PIN = (10331, '2323491006b60bee56f96a8b18e4458b1e702fb8982cdf7213ef7234e30ba690')
DIAG_PIN = (6624, '8bf4dc3413fae7634999e3bd1b3509c2b9f2b9a58e0a13ee1abb7a477c52276f')
WAL_PATCH = 'docs/ck3-native-ai/evidence/succession-binding-refresh-wal-v1.patch'
WAL_PROOF = 'docs/ck3-native-ai/evidence/succession-binding-refresh-wal-source-ready-2026-10-20.json'
WAL_PRODUCER = 'tools/g2_saved_campaign/prepare_succession_binding_refresh_wal_v1.py'
A0_ROOT = 'tools/g2_saved_campaign/candidates/a0_clock_diagnostic_20261020'
A0_READY = A0_ROOT+'/SOURCE-READY.json'
A0_REVISION = A0_ROOT+'/ERROR-DISPATCH-REVISION2.json'
A0_PLAN = A0_ROOT+'/PLAN.json'
A0_PREPARE = A0_ROOT+'/prepare_candidate.py'
INPUTS = {
    S20: (17222, '51d42bd50000f21eadad3158308a4061ddab26e1641c7ebc8bb3ad05c5e69d57'),
    S21: (20520, '2b95564293a2c4af7a168f1f3cb239b136cffda415d7b6ecbfc42110c1d1073f'),
    S21_PLAN: (9446, '9fdb39ffa6d1eb92ef47733f943477ad40110238d1b378209d71c5aa6f286ed2'),
    WAL_PATCH: (5800, '23a15c97291a18706fc453347151eda9259204dd3a6ad97d502a3e27410d319c'),
    WAL_PROOF: (7504, '581459ae4e03fd76d4de01c4f0ecb4bad1d854df42315dddd79b754b23f09601'),
    WAL_PRODUCER: (7340, 'a4a40ee6c7426aae5579320f9426af29017e4cd2bdde56b2a090798b5377ac43'),
    A0_READY: (3479, 'affe69fa98e1fed78e793f61f7c556d5930f0c6d5381a8111f27f54070b7fe29'),
    A0_REVISION: (3047, '16ccd9b77324ec1cc54b47cd589416d289460e138448490e0038208a85b885d3'),
    A0_PLAN: (4490, 'dd266aaad8a89225f60e3666ee0e7db4079cf1d75d7fb9a602eee4e585b0f5f7'),
    A0_PREPARE: (7579, 'c243f2184f04fe484d3a7cc72fd12e0d1b4d057bed5afdac99474d1864853287'),
}
WAL_METHODS = {'__init__', 'retain_succession_expectation_v1',
               '_try_persist_driver_state_wal_append_v1', '_persist_driver_state'}
CLOCK_METHOD = '_advance_exact_day_with_sentinel'
CARD = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/SOURCE22-NEW96KiB-FULL-GROSS2p25MiB-COMMITMENT01.json')
CARD_PIN = (2965, '0c3e6a0c94837bf41f9ee62688d662924758e6931ab48abbca428c759debf446')
OWN = 'tools/g2_saved_campaign/prepare_source22_wal_clock_diagnostic_v1.py'
PROOF = 'docs/ck3-native-ai/evidence/source22-wal-clock-diagnostic-source-qualification-2026-10-20.json'
PLAN = 'docs/ck3-native-ai/evidence/source22-wal-clock-diagnostic-source-plan-2026-10-20.json'


def require(ok, why):
    if not ok:
        raise ValueError('Source22 composition denied: '+why)


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def checked(raw, expected, label):
    require((len(raw), pin(raw)['sha256']) == expected, label+' bytes/SHA differ')
    return raw


def blob_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def name_guard(name):
    require(type(name) is str and ':' not in name and '\\' not in name and '\0' not in name, 'unsafe path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and p.as_posix() == name and name not in ('', '.')
            and not any(x in ('.', '..') for x in p.parts), 'unsafe relative path')
    return name


def index_rows(rows):
    result = {}
    for row in rows:
        require(set(row) == {'relative', 'bytes', 'sha256', 'git_blob_sha1', 'git_mode'}, 'row schema differs')
        name = name_guard(row['relative'])
        require(name not in result and type(row['bytes']) is int and 0 <= row['bytes'] <= 8*1024**2
            and row['git_mode'] in ('100644', '100755') and re.fullmatch('[0-9a-f]{64}', row['sha256'])
            and re.fullmatch('[0-9a-f]{40}', row['git_blob_sha1']), 'invalid source row')
        result[name] = dict(row)
    require(len({n.casefold() for n in result}) == len(result), 'case-colliding source names')
    return result


def rows_bytes(rows):
    return json.dumps([rows[n] for n in sorted(rows)], sort_keys=True, separators=(',', ':')).encode()


def read_inputs():
    raw = {name: checked((REPO/name).read_bytes(), value, 'frozen input '+name) for name, value in INPUTS.items()}
    docs = {name: json.loads(value) for name, value in raw.items() if name.endswith('.json')}
    require(all(doc['machine_id'] == MACHINE for doc in docs.values()), 'qualification machine differs')
    old = json.loads(checked(OLD_FREEZE.read_bytes(), OLD_FREEZE_PIN, 'historical complete inventory'))
    require(old['machine_id'] == MACHINE and old['source_file_count'] == 1445
            and old['source_bytes'] == 59052571, 'historical inventory identity differs')
    source20 = index_rows(old['files'])
    for change in docs[S20]['delta']:
        name = name_guard(change['relative'])
        require(source20.get(name) == change['before'], 'Source20 delta preimage differs')
        source20[name] = index_rows([change['after']])[name]
    checked(rows_bytes(source20), S20_ROWS, 'full canonical Source20 inventory')
    require(len(source20) == 1447 and sum(r['bytes'] for r in source20.values()) == 59065188, 'Source20 arithmetic differs')
    metadata = {}
    for entry in git('ls-tree', '-r', '-l', '-z', BASE, '--', PREFIX).split(b'\0'):
        if entry:
            header, path = entry.split(b'\t', 1); mode, kind, oid, count = header.split()
            name = path.decode(); require(name.startswith(PREFIX) and kind == b'blob', 'unexpected Git row')
            name = name_guard(name[len(PREFIX):]); require(name not in metadata, 'duplicate Git row')
            metadata[name] = (mode.decode(), oid.decode(), int(count))
    require(set(metadata) == set(source20) and all(metadata[n] ==
            (r['git_mode'], r['git_blob_sha1'], r['bytes']) for n, r in source20.items()), 'actual f198 full metadata differs')
    rows = {n: dict(r) for n, r in source20.items()}; prior_outputs = {}
    require(docs[S21]['base']['business_commit'] == BASE and docs[S21_PLAN]['output']['file_count'] == 1447,
            'Source21 does not derive from actual Source20')
    for change in docs[S21]['delta']:
        name = name_guard(change['relative'])
        require(rows.get(name) == change['before'], 'Source21 preimage differs')
        row = index_rows([change['after']])[name]
        value = checked(git('cat-file', 'blob', row['git_blob_sha1']), (row['bytes'], row['sha256']), 'retained Source21 blob')
        require(blob_sha(value) == row['git_blob_sha1'], 'retained Source21 Gitblob differs')
        rows[name] = row; prior_outputs[name] = value
    checked(rows_bytes(rows), S21_ROWS, 'full frozen Source21 logical inventory')
    require(len(prior_outputs) == 5 and sum(map(len, prior_outputs.values())) == 127131
        and len(rows) == 1447 and sum(r['bytes'] for r in rows.values()) == 59074855, 'Source21 arithmetic differs')
    require(rows[DRIVER] == source20[DRIVER] and rows[MCP] == source20[MCP]
        and WAL not in rows and DIAG not in rows, 'two original rows or new helper paths differ')
    require(docs[WAL_PROOF]['base_commit'] == BASE and docs[A0_PLAN]['base_business_commit'] == BASE,
            'candidate baseline differs')
    require(docs[A0_REVISION]['original_10_pass_only_applies_to_prior_helper'] is True
        and docs[A0_REVISION]['tests']['passed'] == 2, 'a0 revision qualification scope differs')
    return raw, docs, source20, rows, prior_outputs


def parse_hunks(diff):
    hunks = []; old = new = None
    for line in diff.splitlines(keepends=True):
        if line.startswith(b'@@ '):
            if old is not None:
                hunks.append((b''.join(old), b''.join(new)))
            require(re.fullmatch(rb'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@[^\r\n]*\r?\n', line), 'invalid patch header')
            old, new = [], []
        elif old is not None:
            require(line[:1] in (b' ', b'+', b'-'), 'unsupported patch marker')
            if line[:1] in (b' ', b'-'):
                old.append(line[1:])
            if line[:1] in (b' ', b'+'):
                new.append(line[1:])
    if old is not None:
        hunks.append((b''.join(old), b''.join(new)))
    require(hunks and all(a and b and a != b for a, b in hunks), 'empty source patch')
    return hunks


def apply_hunks(raw, hunks, reverse=False):
    result = raw
    for a, b in (reversed(hunks) if reverse else hunks):
        old, new = (b, a) if reverse else (a, b)
        require(result.count(old) == 1, 'source hunk absent or nonunique')
        result = result.replace(old, new, 1)
    return result


def make_diff(before, after, path):
    return ''.join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
        fromfile='a/'+PREFIX+path, tofile='b/'+PREFIX+path)).encode()


def driver_methods(raw):
    tree = ast.parse(raw)
    owners = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'NativeHeadlessGameplayDriver']
    require(len(owners) == 1, 'Driver owner class ambiguous')
    return {n.name: ast.dump(n, include_attributes=False) for n in owners[0].body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def changed_names(before, after):
    return {n for n in set(before)|set(after) if before.get(n) != after.get(n)}


def mask_function_body(raw, name):
    tree = ast.parse(raw); nodes = [n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    require(len(nodes) == 1, 'unique function span required '+name)
    nodes[0].body = [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def closure(changed, rows):
    result = {}
    for name, raw in changed.items():
        package = name[:-3].split('/')[:-1]; targets = set()
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.ImportFrom) and node.level:
                prefix = package[:len(package)-node.level+1]
                modules = [node.module] if node.module else [x.name for x in node.names]
                for module in modules:
                    target = '/'.join(prefix+module.split('.'))
                    path = next((p for p in (target+'.py', target+'/__init__.py') if p in rows), None)
                    require(path is not None, 'internal source dependency missing '+target)
                    targets.add(path)
        result[name] = sorted(targets)
    return result


def quote(changed_actual):
    def upper(kind, n):
        return ((n+len(kind)+len(str(n))+2+4096+4095)//4096)*4096
    items = [{'kind': 'blob', 'path': n, 'payload_bytes': len(raw), 'upper': upper('blob', len(raw))}
             for n, raw in sorted(changed_actual.items())]
    directories = ('', 'ck3_autonomous_player', 'ck3_autonomous_player/src',
        'ck3_autonomous_player/src/xar_autoplayer', 'ck3_autonomous_player/src/xar_autoplayer/bridge')
    for directory in directories:
        size = 0
        for entry in git('ls-tree', '-z', BASE+(':'+directory if directory else '')).split(b'\0'):
            if entry:
                header, name = entry.split(b'\t', 1); mode, kind, oid = header.split()
                size += len(mode.lstrip(b'0'))+1+len(name)+1+20
        if directory.endswith('/bridge'):
            size += sum(len('100644')+1+len(p.rsplit('/', 1)[1].encode())+1+20 for p in (WAL, DIAG))
        items.append({'kind': 'tree', 'path': directory or '<root>', 'payload_bytes': size, 'upper': upper('tree', size)})
    items.append({'kind': 'commit', 'path': '<future Root commit>', 'payload_cap': 8192, 'upper': upper('commit', 8192)})
    retained = sum(i['upper'] for i in items); largest = max(i['upper'] for i in items)
    peak = retained+largest+65536; git_envelope = ((peak+262143)//262144)*262144
    data = sum(2*((len(raw)+4095)//4096)*4096 for raw in changed_actual.values())
    return {'status': 'QUOTATION_ONLY_SEPARATE_PHASE_ADMISSION_REQUIRED', 'Git_object_metadata': items,
        'Git_uncompressed_retained_upper': retained, 'Git_extra_largest_temp_upper': largest,
        'Git_refs_dirs_locks_reserve': 65536, 'Git_peak_upper': peak, 'Git_proposed_envelope': git_envelope,
        'compression_or_existing_object_dedup_credit': 0,
        'Git_writer_conditions': 'RAM stdin, no extra full disk payload alias, commit<=8192; add any other writer peak before admission',
        'dual_changed_view4096_data_from_actual_Source20': data,
        'rich_ATTEMPT_COMPLETE_MFT_FS_envelope': 4194304, 'compact_inventory_envelope': 524288,
        'immutable_business_views_export_metadata_quote': data+4194304+524288,
        'control_Task_feeder_atomic_Native_Game_profile_SAVE_recording_Driver_budgets':
            'Not included and not zero; later actual cold configuration is Root-owned.',
        'physical_allocated_bytes': None, 'source_or_runtime_admission': False}


def compose():
    inputs, docs, source20, base21, retained21 = read_inputs()
    original = checked(git('show', BASE+':'+PREFIX+DRIVER), DRIVER_BASE, 'actual cc60 Driver')
    mcp_before = checked(git('show', BASE+':'+PREFIX+MCP), MCP_BASE, 'actual Source20 MCP')
    wal_hunks = parse_hunks(inputs[WAL_PATCH])
    wal_driver = checked(apply_hunks(original, wal_hunks), WAL_DRIVER, 'qualified WAL-only Driver')
    require(apply_hunks(wal_driver, wal_hunks, True) == original, 'WAL whole inverse differs')
    # Read existing candidate refs once; do not copy either complete candidate.
    a0_driver = checked((REPO/A0_ROOT/'xar_autoplayer/bridge/native_driver.py').read_bytes(), A0_DRIVER, 'a0 qualified Driver')
    mcp_after = checked((REPO/A0_ROOT/'xar_autoplayer/bridge/mcp_server.py').read_bytes(), A0_MCP, 'a0 qualified MCP')
    driver_diff = make_diff(original, a0_driver, DRIVER); diag_hunks = parse_hunks(driver_diff)
    mcp_diff = make_diff(mcp_before, mcp_after, MCP); mcp_hunks = parse_hunks(mcp_diff)
    require(apply_hunks(original, diag_hunks) == a0_driver
        and apply_hunks(a0_driver, diag_hunks, True) == original, 'a0 whole Driver inverse differs')
    require(apply_hunks(mcp_before, mcp_hunks) == mcp_after
        and apply_hunks(mcp_after, mcp_hunks, True) == mcp_before, 'a0 entire MCP inverse differs')
    combined = apply_hunks(wal_driver, diag_hunks)
    alternate = apply_hunks(a0_driver, wal_hunks)
    require(combined == alternate and len(combined) == 1640335, 'two Driver composition orders differ')
    require(apply_hunks(combined, diag_hunks, True) == wal_driver
        and apply_hunks(combined, wal_hunks, True) == a0_driver
        and apply_hunks(apply_hunks(combined, diag_hunks, True), wal_hunks, True) == original
        and apply_hunks(apply_hunks(combined, wal_hunks, True), diag_hunks, True) == original,
        'cross-order Driver inverse lost the other patch')
    before_map = driver_methods(original); wal_map = driver_methods(wal_driver)
    diag_map = driver_methods(a0_driver); final_map = driver_methods(combined)
    require(changed_names(before_map, wal_map) == WAL_METHODS
        and changed_names(before_map, diag_map) == {CLOCK_METHOD}
        and not WAL_METHODS.intersection({CLOCK_METHOD})
        and changed_names(before_map, final_map) == WAL_METHODS|{CLOCK_METHOD}, 'Driver method domains differ')
    require(all(final_map[n] == wal_map[n] for n in WAL_METHODS)
        and final_map[CLOCK_METHOD] == diag_map[CLOCK_METHOD], 'one patch changed the other method body')
    require(mask_function_body(mcp_before, 'ck3_auto_turn') == mask_function_body(mcp_after, 'ck3_auto_turn'),
            'MCP changed outside AUTO exception DTO owner')
    wal_helper = checked((REPO/PREFIX/WAL).read_bytes(), WAL_PIN, 'WAL thin helper')
    diag_helper = checked((REPO/A0_ROOT/DIAG).read_bytes(), DIAG_PIN, 'final actual-type/step diagnostic helper')
    require(docs[WAL_PROOF]['candidate_RAM_only'] == pin(wal_driver)
        and any(p['bytes'] == DIAG_PIN[0] and p['sha256'] == DIAG_PIN[1] for p in docs[A0_REVISION]['updated_pins']),
        'qualified source pins not bound by final evidence')
    added = {DRIVER: combined, MCP: mcp_after, WAL: wal_helper, DIAG: diag_helper}
    rows = {n: dict(r) for n, r in base21.items()}; delta = []
    for name, raw in sorted(added.items()):
        before = rows.get(name)
        after = {'relative': name, **pin(raw), 'git_blob_sha1': blob_sha(raw),
                 'git_mode': before['git_mode'] if before else '100644'}
        rows[name] = after; delta.append({'relative': name, 'before': before, 'after': after,
            'net_bytes': len(raw)-(before['bytes'] if before else 0)})
    require(len(rows) == 1449 and sum(r['bytes'] for r in rows.values()) == 59095358
        and len(set(rows)-set(base21)) == 2 and set(rows)-set(base21) == {WAL, DIAG}, 'Source22 manifest arithmetic differs')
    require(all(rows[n] == base21[n] for n in base21 if n not in (DRIVER, MCP)), 'a Source21 base row was overwritten')
    actual_outputs = {**retained21, **added}
    require(len(actual_outputs) == 9 and sum(map(len, actual_outputs.values())) == 2049041,
            'complete participating output gross differs')
    for name, value in retained21.items():
        require(rows[name] == base21[name] and pin(value) == {'bytes': rows[name]['bytes'], 'sha256': rows[name]['sha256']},
                'retained Source21 exact output differs')
    family = 'xar_autoplayer/family_marriage_formal_consumer.py'
    protected = [family, 'xar_autoplayer/bridge/service.py', 'xar_autoplayer/bridge/readonly_planning_retry_v1.py',
        'xar_autoplayer/bridge/campaign_root_terminal_retry_v1.py', 'xar_autoplayer/bridge/campaign_root_retry_diagnostic_v1.py',
        'xar_autoplayer/bridge/exact_day_speed_configuration_v1.py', 'xar_autoplayer/bridge/driver_state_wal_v1.py']
    require(all(rows[n] == base21[n] for n in protected)
        and rows[family]['sha256'] == 'd8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf',
        'Source20 shared budget/audit/family/WAL format changed')
    # A0 adds an earlier typed error projection, while this pre-existing ROOT
    # bounded-diagnostic tail and its native diagnostic remain byte-identical.
    tail_start = mcp_before.index(b'            diagnostics = {diagnostic_key: diagnostic}')
    tail_end = mcp_before.index(b'            )', tail_start)+len(b'            )')
    require(mcp_before[tail_start:tail_end] in mcp_after, 'typed ROOT bounded diagnostic tail changed')
    deps = closure(added, rows)
    require(WAL in deps[DRIVER] and DIAG in deps[DRIVER] and DIAG in deps[MCP], 'new dependency closure incomplete')
    protected_rows = [rows[n] for n in protected]
    report = {'schema': 'xar.source22.wal-clock-diagnostic-source-composition/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOURCE22_CANDIDATE_NOT_ADOPTED',
        'actual_SDK': 'C20 / Source20 per Root; no Source21/22 deployment is claimed',
        'actual_canonical_base': {'commit': BASE, 'files': 1447, 'bytes': 59065188,
            'canonical_rows_JSON': dict(zip(('bytes', 'sha256'), S20_ROWS)), 'all1447_Git_metadata_checked': True},
        'logical_Source21_base': {'plan': {'path': S21_PLAN, **dict(zip(('bytes', 'sha256'), INPUTS[S21_PLAN]))},
            'files': 1447, 'bytes': 59074855, 'canonical_rows_JSON': dict(zip(('bytes', 'sha256'), S21_ROWS)),
            'not_a_separate_canonical_commit_or_tree': True},
        'complete_manifest': {'file_count': 1449, 'source_bytes': 59095358,
            'canonical_rows_JSON': pin(rows_bytes(rows)), 'access': 'compose() returns full1449 rows and nine participating outputs in RAM only'},
        'delta_from_logical_Source21': delta, 'new_helpers': 2, 'changed_existing': 2,
        'unchanged_Source21_rows': 1445, 'retained_Source21_five_output_refs': [rows[n] for n in sorted(retained21)],
        'actual_Source20_total_delta': {'changed_existing': 7, 'new_helpers': 2, 'output_rows': 9},
        'Driver_composition': {'base': pin(original), 'WAL_only': pin(wal_driver), 'diagnostic_only': pin(a0_driver),
            'combined': pin(combined), 'WAL_patch': pin(inputs[WAL_PATCH]), 'a0_Driver_generated_patch': pin(driver_diff),
            'WAL_hunks': len(wal_hunks), 'a0_hunks': len(diag_hunks),
            'WAL_methods': sorted(WAL_METHODS), 'diagnostic_methods': [CLOCK_METHOD],
            'method_domains_disjoint': True, 'WAL_then_A0_equals_A0_then_WAL_whole_bytes': True,
            'removing_either_patch_preserves_the_other_entire_blob': True,
            'both_inverse_orders_restore_entire_cc60': True, 'every_other_Driver_method_AST_unchanged': True},
        'MCP_composition': {'before': pin(mcp_before), 'after': pin(mcp_after), 'generated_patch': pin(mcp_diff),
            'hunks': len(mcp_hunks), 'whole_inverse_restores_Source20_MCP': True,
            'only_owner': 'ck3_auto_turn', 'outside_owner_AST_unchanged': True,
            'Source20_ROOT_bounded_diagnostic_tail_preserved': True},
        'protected_source_rows': protected_rows, 'static_internal_dependency_closure': deps,
        'qualification_inheritance': {
            'Source21': 'Five frozen leaves/source provenance retained exactly; no original matrices repeated.',
            'WAL': '581459 proof: portable3 and actual f198 RAM integration7 passed separately, synthetic filesystem only. No old16/144 matrix repeated.',
            'a0': 'affe69 SOURCE-READY original10 passed only with earlier helper9c8e. Final helper8bf4 has revision16ccd9 two targeted actual-type/selected-step cases; the ten were NOT rerun at new helper.',
            'independent_source_review': 'performance_python final a0 NoBlock and M3 WAL source NoBlock reported to Root; those are source review, not this composition or runtime credit.'},
        'new_checks_this_run': {'kind': 'RAM full-source pins, exact two-order hunks/inverses, AST domains, manifest and provenance closure only',
            'full_SDK_imports': 0, 'functional_tests_or_owner_matrices_repeated': 0, 'source_tree_outputs': 0},
        'frozen_source_inputs': [{'path': p, **dict(zip(('bytes', 'sha256'), v))} for p, v in INPUTS.items()],
        'full_participating_output_bytes': 2049041, 'full_participating_output_count': 9,
        'participating_storage': 'Source21 refs127131 and retained A0/WAL inputs stay in original held packages; no duplicate Driver/MCP candidate or source tree. One combined Driver is RAM only.',
        'future_separate_phase_quotes': quote(actual_outputs),
        'WAL_enablement_boundary': 'Existing constructor/default/env guard retained; source qualification cannot prove actual App writer enabled or claim WAL speedup. Format reader, once/barrier/dirty/cold/save/close guards remain.',
        'clock_boundary': 'Diagnostic only. No clock root cause repair; M5 investigation remains UNKNOWN. No new query or timeout/sampling change. Arm is not a stop receipt; error DTO grants zero credit and never replay.',
        'Native_boundary': 'No DLL/ABI/CPP/EXE or capability change and no unqualified Native30 binding. Later cold config and actual loaded feature qualification are Root-owned.',
        'future_branch_ref_export_cold_Task': 'Not created/exported/configured/admitted',
        'runtime_Driver_SAVE_body_reads': 0, 'Git_D_Task_Game_RPC_Native_mutations': 0,
        'actual_seconds_saved_or_runtime_recovery': None, 'scratch_bytes': 0}
    return actual_outputs, [rows[n] for n in sorted(rows)], report


def freeze():
    require(sys.dont_write_bytecode, 'run -B; no bytecode scratch allowed')
    card = json.loads(checked(CARD.read_bytes(), CARD_PIN, 'source22 admission')); now = datetime.now(timezone.utc)
    require(card['machine_id'] == MACHINE and card['status'] == 'SOURCE_ONLY_ADMITTED'
        and card['complete_new_helpers_proof_plan_hard_bytes'] == 98304
        and card['full_participating_gross_hard_bytes'] == 2359296
        and now < datetime.fromisoformat(card['review_at_utc']), 'source22 card differs/expired')
    paths = [REPO/PROOF, REPO/PLAN]; require(all(not p.exists() for p in paths), 'frozen Source22 report exists')
    outputs, rows, report = compose(); encode = lambda d: (json.dumps(d, ensure_ascii=False, indent=2)+'\n').encode()
    proof = encode(report); own = (REPO/OWN).read_bytes(); own_pin = {'path': str(REPO/OWN), **pin(own)}
    proof_pin = {'path': str(paths[0]), **pin(proof)}
    plan = {'schema': 'xar.source22.wal-clock-diagnostic-frozen-source-plan/v1', 'machine_id': MACHINE,
        'observed_at_utc': now.isoformat(), 'machine_source': 'tools/ck3_live_run_id.py machine; recorded actual108b44',
        'status': 'SOURCE22_CANDIDATE_FROZEN_NOT_ADOPTED', 'actual_SDK': report['actual_SDK'],
        'producer_all_inline_helpers': own_pin, 'qualification': proof_pin,
        'entry': 'prepare_source22_wal_clock_diagnostic_v1.compose() -> nine exact RAM output refs, complete1449 rows, proof. No project code imports/tests or production output writer.',
        'actual_canonical_base': report['actual_canonical_base'], 'logical_Source21_base': report['logical_Source21_base'],
        'output': report['complete_manifest'],
        'delta': {'from_Source21': '2 changed existing+2 new helpers; all1445 other rows preserved',
                  'from_actual_Source20_f198': report['actual_Source20_total_delta'], 'exact_rows_and_two_order_inverse_in': proof_pin},
        'participating_complete_output_pins': [{'relative': n, **pin(raw), 'git_blob_sha1': blob_sha(raw),
            'storage': 'existing held refs/RAM output only; no new production copy'} for n, raw in sorted(outputs.items())],
        'Driver_function_domains': {'WAL': sorted(WAL_METHODS), 'a0': [CLOCK_METHOD], 'disjoint': True,
            'two_orders_entire_bytes_equal': True, 'either_inverse_preserves_other': True, 'cc60_full_inverse': True},
        'MCP_scope': 'Only ck3_auto_turn exact typed exception DTO; original ROOT retry diagnostic and other branches retained.',
        'qualification_inheritance': report['qualification_inheritance'], 'new_qualification_scope': report['new_checks_this_run'],
        'WAL_enablement_boundary': report['WAL_enablement_boundary'], 'clock_boundary': report['clock_boundary'],
        'Native_boundary': report['Native_boundary'],
        'future_separate_phase_quotes': {k: v for k, v in report['future_separate_phase_quotes'].items()
                                         if k != 'Git_object_metadata'}, 'Git_object_quote_metadata_in': proof_pin,
        'future': {'branch': 'not created', 'ref': 'not created', 'export': 'not executed', 'cold_Task': 'Root later config',
            'Native30': 'not bound/qualified', 'clock_root_cause': 'UNKNOWN, diagnosis does not solve it',
            'permission': 'This source-only card grants no Git/view/export/SDK/Task/Game/Native operation'},
        'storage': {'source_card': {'path': str(CARD), **dict(zip(('bytes', 'sha256'), CARD_PIN))},
            'new_three_files_hard': 98304, 'full_participating_gross_hard': 2359296,
            'participating_output_bytes': 2049041, 'participating_Output_refs': 9,
            'new_named_files_excluding_this_plan': [own_pin, proof_pin], 'new_named_files_bytes_including_this_plan': 0,
            'complete_gross_including_participating_outputs': 0,
            'existing_holds': 'Source21 192KiB, A0 2MiB, WALthin192KiB remain retained; source refs are in-place deduplicated, no second full candidate tree',
            'all_helper_code': 'self-contained producer; external producer files are read as pinned evidence only, never imported/executed',
            'new_tests': 0, 'scratch_bytes': 0, 'new_full_Driver_MCP_or_source_tree_copies': 0,
            'allocated_bytes': None, 'physical_credit_bytes': 0, 'future_writes_after_freeze': 0,
            'review_at_utc': card['review_at_utc'], 'record_review_at_utc': (now+timedelta(days=180)).isoformat()}}
    while True:
        raw = encode(plan); new_bytes = len(own)+len(proof)+len(raw); gross = 2049041+new_bytes
        if new_bytes == plan['storage']['new_named_files_bytes_including_this_plan']:
            break
        plan['storage']['new_named_files_bytes_including_this_plan'] = new_bytes
        plan['storage']['complete_gross_including_participating_outputs'] = gross
    require(new_bytes <= 98304 and gross <= 2359296, 'new96K/full2.25M source bounds exceeded '+str((new_bytes, gross)))
    with paths[0].open('xb') as stream:
        stream.write(proof)
    with paths[1].open('xb') as stream:
        stream.write(raw)
    return {'producer': own_pin, 'qualification': proof_pin, 'plan': {'path': str(paths[1]), **pin(raw)},
        'new_three_file_bytes': new_bytes, 'participating_output_bytes': 2049041, 'complete_gross': gross,
        'full_manifest': report['complete_manifest'], 'combined_Driver': report['Driver_composition']['combined'],
        'future_phase_quotes': plan['future_separate_phase_quotes'], 'branch_ref_export_created': False}


if __name__ == '__main__':
    if sys.argv[1:] == ['--freeze']:
        print(json.dumps(freeze(), ensure_ascii=False, indent=2))
    else:
        require(not sys.argv[1:], 'only --freeze or no args')
        _, _, report = compose()
        print(json.dumps({k: report[k] for k in ('status', 'actual_SDK', 'logical_Source21_base', 'complete_manifest', 'clock_boundary')}, indent=2))
