"""Source21 candidate: exact five-leaf composition over canonical Source20.

Only immutable Git source blobs and pinned records are read. All five full
outputs participate in the gross source budget, but remain in RAM/in their
existing owner packages. This module writes only its named small proof/plan
when --freeze is explicitly selected. It cannot write Git or export an SDK.
"""
from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
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
BASE_ROWS = (371996, '7b62abe6c91e382af449b1c7057bf304d729db310ad88deea4861218c8379935')
OLD_FREEZE = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C18.json')
OLD_FREEZE_PIN = (375083, '624c0a229abea3241474e31958bfe4b4102e970f7032f3fc9821273a15ee1d5b')
SOURCE20_PROOF = 'docs/ck3-native-ai/evidence/source20-minimal-warm-sdk-source-qualification-2026-10-20.json'
SOURCE20_ACTUAL = 'docs/ck3-native-ai/evidence/source20-root-git-actual-2026-10-20.json'
FILTER_PROOF = 'docs/ck3-native-ai/evidence/m5-private-copy-boundary-source-2026-10-19.json'
PARTITION_PROOF = 'docs/ck3-native-ai/evidence/turn-bundle-owned-partition-source-ready-2026-10-20.json'
M6_PROOF = 'docs/ck3-native-ai/evidence/g2-m6-durable-receipt-recovery-source-2026-10-20.json'
M6_REVIEW = 'docs/ck3-native-ai/evidence/m6-receipt-durable-source-root-review-2026-10-20.json'
RESERVE_PROOF = 'docs/ck3-native-ai/evidence/primary-defender-preventive-reserve-source-2026-10-20.json'
RESERVE_REVIEW = 'docs/ck3-native-ai/evidence/primary-defender-reserve-root-review-2026-10-20.json'
INPUTS = {
    SOURCE20_PROOF: (17222, '51d42bd50000f21eadad3158308a4061ddab26e1641c7ebc8bb3ad05c5e69d57'),
    SOURCE20_ACTUAL: (4622, '8836237f119acb3e7d59d8a179bd954711f46397d8f9097b14ad2ec92264649d'),
    FILTER_PROOF: (3377, '7bef78c61a15d0ba7198c29d36dc3a9449d78d3ed8b9e8b7d0bb7f2ae181eeda'),
    PARTITION_PROOF: (10325, '398857e02ccc9672ae40daef0bc64235831323724647189250657d9b27b25d3e'),
    M6_PROOF: (5408, '65999738032c972df747676a07cc2cbb54a19f87afd55e06310d26dfe9ad1ad7'),
    M6_REVIEW: (1712, '0ed6995dcfb06dfc86e9a1e66f188f3d7878f93cfed3d416b7b2e740228ec9f7'),
    RESERVE_PROOF: (5363, '8fc0c78b8310624237d53768653ab6ef19490e95905e5a643e477f5d65e15086'),
    RESERVE_REVIEW: (1907, '671725df8fc527038e1cbf81609d75014d2695980cfc98cd1c7b20becd1a040e'),
}
# The exact donor parent must equal the complete Source20 leaf, not just a
# matching function excerpt. No other path from any donor commit is adopted.
CANDIDATES = (
    ('xar_autoplayer/m5_formal_proposal_collector.py', '368f702355a5eae9a70e67127d9d4fa78f800e5a',
     36095, '27e24743ebe5a5b33e049a88406a683ec3b8201208970d35c8664f7d9693c5cf',
     36154, '6488c6f3ab6d930e37d8f9730285214ebbc700a8a6ec968124826b81b1c8172e', FILTER_PROOF),
    ('xar_autoplayer/bridge/turn_bundle_contract.py', '0b5ebd7e40cba44ac940bc84b3479a73eb25d3fe',
     27516, '0119ea8a1d41a0ab84ac6dd33f865b022f54595c8097bb6e55a70ba7bcff356a',
     27974, 'd02a8e56a83494a9643d9ded350e125ad96d6d6922eef75132e37d711ed91acc', PARTITION_PROOF),
    ('xar_autoplayer/sway_formal_consumer.py', '23cdb469ce57b247de6263913a6c7cdd02f89809',
     27237, 'fa27a839036564f762d18969265c2baae33d5b8e517ee9d01d0ceb7393394dc8',
     34660, '02ff455d7ae350ba10b4c2cbcd042350499a04d5bd69b3ec3525af408c959ec7', M6_PROOF),
    ('xar_autoplayer/bridge/active_scheme_sway_formal_private_transport.py', '23cdb469ce57b247de6263913a6c7cdd02f89809',
     7028, '5b1c3fc2d2a9235496799b72e1c0018a92faadf3a24aa5c55a7da5b6bedfb63c',
     8276, '6e3e389fce8ecb6f92c579384d5a02afaa2f2cf9efc2fb62c924d057b46b3e5c', M6_PROOF),
    ('xar_autoplayer/war_reinforcement_tradeoff_v1.py', 'ee15c1eefba13448d38a9854507a699a00e41ee7',
     19588, 'c27266b60a80e7b18a38c22bdc8a076a79f351eb0b3b976c367ddc3dc90299ac',
     20067, '4e22f96567f30b1b6101ea29e33ec485b417cea8f23ba0c2851070bbc91a767a', RESERVE_PROOF),
)
CARD = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/COMPOSER-FUTURE-SOURCE20-FIVE-LEAF-PERFORMANCE192KiB-SOURCE-COMMITMENT01.json')
CARD_PIN = (1480, 'c7653cbac85546869399a111f6000331f8a2f07ba7b1567129c5c92c5367c8c8')
PROOF = 'docs/ck3-native-ai/evidence/source21-longterm-sdk-source-qualification-2026-10-20.json'
PLAN = 'docs/ck3-native-ai/evidence/source21-longterm-sdk-source-plan-2026-10-20.json'
OWN = 'tools/g2_saved_campaign/prepare_source21_longterm_sdk_v1.py'
PROTECTED = (
    'xar_autoplayer/bridge/service.py', 'xar_autoplayer/bridge/readonly_planning_retry_v1.py',
    'xar_autoplayer/bridge/campaign_root_terminal_retry_v1.py',
    'xar_autoplayer/bridge/campaign_root_retry_diagnostic_v1.py', 'xar_autoplayer/bridge/mcp_server.py',
    'xar_autoplayer/bridge/exact_day_speed_configuration_v1.py',
    'xar_autoplayer/family_marriage_formal_consumer.py',
    'xar_autoplayer/bridge/native_driver.py', 'xar_autoplayer/bridge/driver_state_wal_v1.py',
)


def require(ok, why):
    if not ok:
        raise ValueError('Source21 candidate denied: '+why)


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def checked(raw, expected, label):
    require((len(raw), pin(raw)['sha256']) == expected, label+' bytes/SHA differ')
    return raw


def blob_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def safe_name(name):
    require(type(name) is str and ':' not in name and '\\' not in name and '\0' not in name,
            'unsafe source path')
    path = PurePosixPath(name)
    require(not path.is_absolute() and path.as_posix() == name and name not in ('', '.')
            and not any(p in ('..', '.') for p in path.parts), 'unsafe source path')
    return name


def rows_bytes(rows):
    return json.dumps([rows[n] for n in sorted(rows)], sort_keys=True, separators=(',', ':')).encode()


def row_index(rows):
    result = {}
    for row in rows:
        require(set(row) == {'relative', 'bytes', 'sha256', 'git_blob_sha1', 'git_mode'}, 'row shape differs')
        name = safe_name(row['relative'])
        require(name not in result and type(row['bytes']) is int and 0 <= row['bytes'] <= 8*1024**2
            and row['git_mode'] in ('100644', '100755') and re.fullmatch('[0-9a-f]{64}', row['sha256'])
            and re.fullmatch('[0-9a-f]{40}', row['git_blob_sha1']), 'invalid inventory row')
        result[name] = dict(row)
    require(len({n.casefold() for n in result}) == len(result), 'case-colliding source paths')
    return result


def base_rows():
    records = {name: json.loads(checked((REPO/name).read_bytes(), value, name)) for name, value in INPUTS.items()}
    require(all(doc['machine_id'] == MACHINE for doc in records.values()), 'record machine identity differs')
    old = json.loads(checked(OLD_FREEZE.read_bytes(), OLD_FREEZE_PIN, 'historical Source15 full inventory'))
    require(old['machine_id'] == MACHINE and old['source_file_count'] == 1445
        and old['source_bytes'] == 59052571 and old['business_source_commit'] == '0e8a190bf3e5ec187e7bc30d76310585922a0b50',
        'historical inventory identity differs')
    rows = row_index(old['files'])
    for change in records[SOURCE20_PROOF]['delta']:
        name = safe_name(change['relative'])
        require(rows.get(name) == change['before'], 'Source20 six-delta preimage differs')
        rows[name] = row_index([change['after']])[name]
    require(len(rows) == 1447 and sum(r['bytes'] for r in rows.values()) == 59065188,
            'Source20 inventory arithmetic differs')
    checked(rows_bytes(rows), BASE_ROWS, 'complete Source20 rows')
    actual = records[SOURCE20_ACTUAL]['actual']
    require(actual['commit'] == BASE and actual['complete_manifest']['canonical_rows_JSON'] == pin(rows_bytes(rows)),
            'actual Root Source20 anchor does not bind the complete inventory')
    indexed_git = {}
    for entry in git('ls-tree', '-r', '-l', '-z', BASE, '--', PREFIX).split(b'\0'):
        if entry:
            header, path = entry.split(b'\t', 1); mode, kind, oid, count = header.split()
            name = path.decode(); require(name.startswith(PREFIX) and kind == b'blob', 'unexpected Git source entry')
            name = safe_name(name[len(PREFIX):]); require(name not in indexed_git, 'duplicate Git entry')
            indexed_git[name] = (mode.decode(), oid.decode(), int(count))
    require(set(indexed_git) == set(rows) and all(indexed_git[n] ==
        (r['git_mode'], r['git_blob_sha1'], r['bytes']) for n, r in rows.items()), 'full Source20 Git metadata differs')
    return rows, records


def parse_hunks(diff):
    require(diff.count(b'diff --git ') == 1, 'one ordinary source diff required')
    hunks = []; old = new = None
    for line in diff.splitlines(keepends=True):
        if line.startswith(b'@@ '):
            if old is not None:
                hunks.append((b''.join(old), b''.join(new)))
            require(re.fullmatch(rb'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@[^\r\n]*\r?\n', line), 'invalid hunk header')
            old, new = [], []
        elif old is not None:
            require(line[:1] in (b' ', b'+', b'-'), 'unsupported source diff marker')
            if line[:1] in (b' ', b'-'):
                old.append(line[1:])
            if line[:1] in (b' ', b'+'):
                new.append(line[1:])
    if old is not None:
        hunks.append((b''.join(old), b''.join(new)))
    require(hunks and all(a and b and a != b for a, b in hunks), 'empty hunk')
    return hunks


def transfer(raw, hunks):
    result = raw
    for before, after in hunks:
        require(result.count(before) == 1, 'hunk context not unique')
        result = result.replace(before, after, 1)
    inverse = result
    for before, after in reversed(hunks):
        require(inverse.count(after) == 1, 'inverse context not unique')
        inverse = inverse.replace(after, before, 1)
    require(inverse == raw, 'inverse did not restore complete Source20 bytes')
    return result


def function_map(raw):
    result = {}
    for node in ast.parse(raw).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[node.name+'.'+method.name] = ast.dump(method, include_attributes=False)
    return result


def dependencies(changed, rows):
    found = {}
    for name, raw in changed.items():
        package = name[:-3].split('/')[:-1]; targets = set()
        for node in ast.walk(ast.parse(raw)):
            if not isinstance(node, ast.ImportFrom) or not node.level:
                continue
            prefix = package[:len(package)-node.level+1]
            modules = [node.module] if node.module else [alias.name for alias in node.names]
            for module in modules:
                path = '/'.join(prefix+module.split('.'))
                candidates = (path+'.py', path+'/__init__.py')
                actual = next((p for p in candidates if p in rows), None)
                require(actual is not None, 'relative import absent from complete candidate '+name+': '+path)
                targets.add(actual)
        found[name] = sorted(targets)
    return found


def prospective_quote(changed):
    def loose(kind, count):
        return ((count+len(kind)+len(str(count))+2+4096+4095)//4096)*4096
    objects = [{'kind': 'blob', 'path': name, 'payload_bytes': len(raw), 'upper': loose('blob', len(raw))}
               for name, raw in sorted(changed.items())]
    dirs = ('', 'ck3_autonomous_player', 'ck3_autonomous_player/src',
            'ck3_autonomous_player/src/xar_autoplayer', 'ck3_autonomous_player/src/xar_autoplayer/bridge')
    for directory in dirs:
        size = 0
        for entry in git('ls-tree', '-z', BASE+(':'+directory if directory else '')).split(b'\0'):
            if entry:
                header, name = entry.split(b'\t', 1); mode, kind, oid = header.split()
                size += len(mode.lstrip(b'0'))+1+len(name)+1+20
        # No paths/modes are added; replacement object IDs keep the byte size.
        objects.append({'kind': 'tree', 'path': directory or '<root>', 'payload_bytes': size, 'upper': loose('tree', size)})
    objects.append({'kind': 'commit', 'path': '<future Root commit>', 'payload_cap': 8192, 'upper': loose('commit', 8192)})
    retained = sum(o['upper'] for o in objects); temp = max(o['upper'] for o in objects)
    data = sum(2*((len(raw)+4095)//4096)*4096 for raw in changed.values())
    return {'status': 'FUTURE_PHASE_QUOTES_ONLY_NO_GIT_VIEW_EXPORT_COLD_PERMISSION',
        'Git_uncompressed_object_inventory': objects, 'Git_retained_upper': retained,
        'Git_extra_largest_temp_upper': temp, 'Git_refs_dirs_locks_reserve': 65536,
        'Git_peak_upper': retained+temp+65536, 'Git_proposed_envelope': 524288, 'compression_credit': 0,
        'Git_conditions': 'RAM stdin/no extra disk payload alias; per-object serialized bytes+4096 aligned4K; future commit payload<=8192. Existing Git-object dedup is not credited.',
        'immutable_business_view_changed_dual4096_data': data,
        'rich_inventory_ATTEMPT_COMPLETE_MFT_FS_envelope': 4194304,
        'compact_final_inventory_envelope': 524288,
        'immutable_views_and_export_metadata_quote': data+4194304+524288,
        'unmodified_source_rows_for_future_verified_hardlinks': 1442,
        'future_control_Task_feeder_atomic_Native_Game_profile_SAVE_recording_Driver_budgets':
            'Not included or treated as zero; Root defines the later cold configuration and each separate card.',
        'physical_allocated_bytes': None, 'actual_seconds_saved': None}


def compose():
    original, records = base_rows(); rows = {n: dict(r) for n, r in original.items()}
    changed = {}; operations = []; master = git('rev-parse', 'refs/heads/master').decode().strip()
    for name, donor, old_bytes, old_sha, new_bytes, new_sha, authority in CANDIDATES:
        before = checked(git('show', BASE+':'+PREFIX+name), (old_bytes, old_sha), 'Source20 preimage '+name)
        require(pin(before) == {'bytes': original[name]['bytes'], 'sha256': original[name]['sha256']}
                and blob_sha(before) == original[name]['git_blob_sha1'], 'preimage inventory differs')
        parent = git('show', donor+'^:'+PREFIX+name)
        require(parent == before, 'donor parent is not the entire actual Source20 leaf')
        after = checked(git('show', donor+':'+PREFIX+name), (new_bytes, new_sha), 'source-qualified donor '+name)
        require(subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', donor, master],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0, 'donor is not in observed master')
        diff = git('diff', '--no-ext-diff', '--no-color', '--unified=3', donor+'^', donor, '--', PREFIX+name)
        hunks = parse_hunks(diff); result = transfer(before, hunks)
        require(result == after, 'exact hunks do not reconstruct the qualified full blob')
        old_functions, new_functions = function_map(before), function_map(after)
        names = sorted(n for n in set(old_functions)|set(new_functions) if old_functions.get(n) != new_functions.get(n))
        if authority == FILTER_PROOF:
            require(names == ['plan_m5_formal_query_only'], 'collector scope expanded')
        if authority == PARTITION_PROOF:
            require(names == ['_owned_partition_component', 'build_turn_bundle_v1']
                    and old_functions['_component'] == new_functions['_component'], 'partition ownership scope expanded')
        if authority == RESERVE_PROOF:
            require(names == ['observe_war_spending_priority_v1'] and len(after)-len(before) == 479,
                    'preventive reserve scope expanded')
        row = {'relative': name, **pin(after), 'git_blob_sha1': blob_sha(after), 'git_mode': original[name]['git_mode']}
        rows[name] = row; changed[name] = after
        operations.append({'relative': name, 'donor': donor, 'donor_parent': git('rev-parse', donor+'^').decode().strip(),
            'entire_Source20_preimage_equals_donor_parent': True, 'before': original[name], 'after': row,
            'net_bytes': new_bytes-old_bytes, 'patch': pin(diff), 'hunk_count': len(hunks),
            'inverse_restores_complete_Source20_blob': True, 'changed_or_added_function_ASTs': names,
            'source_qualification': {'path': authority, **dict(zip(('bytes', 'sha256'), INPUTS[authority]))}})
    require(len(changed) == 5 and sum(map(len, changed.values())) == 127131 and len(rows) == 1447
        and sum(r['bytes'] for r in rows.values()) == 59074855 and set(rows) == set(original), 'five-leaf arithmetic differs')
    require(all(rows[n] == original[n] for n in original if n not in changed), 'unrelated source row changed')
    require(all(rows[n] == original[n] for n in PROTECTED), 'Source20 recovery/audit/family/Driver bindings changed')
    require(rows['xar_autoplayer/family_marriage_formal_consumer.py']['sha256'] ==
            'd8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf', 'family fix missing')
    closure = dependencies(changed, rows)
    require('xar_autoplayer/bridge/active_scheme_sway_formal_private_transport.py' in
            closure['xar_autoplayer/sway_formal_consumer.py'], 'M6 source-sidecar dependency not joined')
    report = {'schema': 'xar.source21.longterm-five-leaf-source-composition/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOURCE21_CANDIDATE_SOURCE_ONLY',
        'actual_SDK': 'C20 / Source20, unchanged; Source21 is not installed',
        'base': {'business_commit': BASE, 'files': 1447, 'source_bytes': 59065188,
            'canonical_rows_JSON': dict(zip(('bytes', 'sha256'), BASE_ROWS)),
            'full1447_mode_blob_size_checked_against_actual_commit': True,
            'full_inventory_recipe': {'old_inventory': {'path': str(OLD_FREEZE), **dict(zip(('bytes', 'sha256'), OLD_FREEZE_PIN))},
                'six_Source20_delta_inventory': {'path': SOURCE20_PROOF, **dict(zip(('bytes', 'sha256'), INPUTS[SOURCE20_PROOF]))},
                'only_reconstructs_current_Source20_not_an_old_baseline_overlay': True}},
        'observed_master_commit': master, 'complete_manifest': {'file_count': 1447, 'source_bytes': 59074855,
            'canonical_rows_JSON': pin(rows_bytes(rows)), 'access': 'compose() returns full1447 rows and exact five outputs only in RAM'},
        'delta': operations, 'changed_existing_leaves': 5, 'new_leaves': 0, 'unchanged_base_leaves': 1442,
        'net_source_bytes': 9667, 'full_participating_output_bytes': 127131,
        'all_original_Source20_unmodified_rows_preserved': True,
        'protected_Source20_bindings': [rows[n] for n in PROTECTED], 'static_internal_dependency_closure': closure,
        'qualification_inheritance': {
            'filter': 'Frozen3PASS; private fields filtered before deepcopy; public detached aliases preserved. Private deepcopy side effects are outside its contract.',
            'owned_partition': 'Frozen3PASS; three input branch clones/default component/final public succession deepcopy preserved. Commit0b5eb records M1 readonly noBlock; pending status in original proof remains historical.',
            'M6': 'Final34PASS incl real atomic writer/fresh-process reopen, not power-loss/fsync or CK3 SAVE. Two extra small ledger saves with sidecar, one without; no query/endpoint/snapshot added.',
            'preventive_reserve': 'Final15PASS narrowed roster guard; earlier53 at another source pin remain separate. Only complete observed primary-defender force deficit adds reason at nonnegative score; no arrival/odds/hire/loan/refund claim.'},
        'new_qualification_this_run': {'kind': 'Whole raw blob equality, unique exact hunk inverse, AST scope, full manifest and source-proof mapping only',
            'functional_tests_or_old_matrices_repeated': 0, 'SDK_module_imports': 0, 'source_tree_outputs': 0},
        'frozen_input_records': [{'path': n, **dict(zip(('bytes', 'sha256'), v))} for n, v in INPUTS.items()],
        'prospective_separate_phase_quotes': prospective_quote(changed),
        'Native_ABI_feature_boundary': 'Five Python leaves only. Existing exact1.20.0.4/EXE and private capability/receipt guards remain. No new request fields, exported endpoint or Native DLL. No unqualified Native30 binding. Root separately decides future cold Native/config/loaded feature qualification.',
        'performance_boundary': 'Avoid discarded private-view copies and one owned partition pass only on their existing paths. No timing benchmark or game-day rate measured. M6 adds durable IO and reliability; no speed benefit fabricated.',
        'world_evidence_boundary': 'Current Sway Start/fullID/benefit/terminal and current war roster deficit are not read or inferred. Historical receipt dates remain separate from fresh recovery evidence.',
        'future_branch_ref_export_cold_Task': 'Not created/not executed/not admitted; Root later defines separate configuration and capacity',
        'runtime_Driver_SAVE_body_reads': 0, 'Game_RPC_Native_Task_Git_mutations_D_outputs': 0,
        'actual_runtime_adoption_or_seconds_saved': None, 'scratch_bytes': 0}
    require(report['prospective_separate_phase_quotes']['immutable_business_view_changed_dual4096_data'] == 270336,
            'changed-data quote differs')
    return changed, [rows[n] for n in sorted(rows)], report


def freeze():
    require(sys.dont_write_bytecode, 'use -B; no bytecode scratch')
    card = json.loads(checked(CARD.read_bytes(), CARD_PIN, 'source192KiB card')); now = datetime.now(timezone.utc)
    require(card['status'] == 'ADMITTED_SOURCE_ONLY' and card['machine_id'] == MACHINE
        and card['base_business_commit'] == BASE and card['hard_bytes'] == 196608
        and now < datetime.fromisoformat(card['review_at_utc']), 'source card differs/expired')
    paths = [REPO/PROOF, REPO/PLAN]
    require(all(not p.exists() for p in paths), 'Source21 frozen proof/plan exists')
    changed, rows, report = compose(); encode = lambda d: (json.dumps(d, ensure_ascii=False, indent=2)+'\n').encode()
    proof = encode(report); own_raw = (REPO/OWN).read_bytes(); own_pin = {'path': str(REPO/OWN), **pin(own_raw)}
    proof_pin = {'path': str(paths[0]), **pin(proof)}
    participating = [{'relative': n, **pin(raw), 'git_blob_sha1': blob_sha(raw), 'storage': 'existing owner/master Git blob; RAM only, no new production copy'}
                     for n, raw in sorted(changed.items())]
    plan = {'schema': 'xar.source21.longterm-five-leaf-frozen-source-plan/v1', 'machine_id': MACHINE,
        'observed_at_utc': now.isoformat(), 'machine_source': 'tools/ck3_live_run_id.py machine; actual f31f1c',
        'status': 'SOURCE21_CANDIDATE_FROZEN_NOT_ADOPTED', 'actual_SDK': report['actual_SDK'],
        'producer_and_inline_qualification_helpers': own_pin, 'qualification': proof_pin,
        'entry': 'prepare_source21_longterm_sdk_v1.compose() -> five RAM byte leaves, full1447 rows, proof. No SDK imports/tests or source tree output.',
        'base': report['base'], 'output': report['complete_manifest'],
        'delta': {'existing': 5, 'new': 0, 'unchanged': 1442, 'net_bytes': 9667,
                  'exact_operations_and_inverse_guards_in': proof_pin},
        'participating_complete_output_leaves': participating,
        'source_qualification_inheritance': report['qualification_inheritance'],
        'all_Source20_typedROOT_sharedbudget_boundeddiag_audit_family_bindings': 'byte rows unchanged',
        'performance_boundary': report['performance_boundary'], 'Native_ABI_feature_boundary': report['Native_ABI_feature_boundary'],
        'world_evidence_boundary': report['world_evidence_boundary'],
        'prospective_separate_phase_quotes': {k: v for k, v in report['prospective_separate_phase_quotes'].items()
                                             if k != 'Git_uncompressed_object_inventory'},
        'full_Git_quote_object_metadata_in': proof_pin,
        'future': {'branch': 'not created', 'ref': 'not created', 'export': 'not executed', 'cold_Task': 'not configured or admitted',
            'Native30': 'not bound; qualification not inferred', 'current_C20_Source20': 'unchanged',
            'permission': 'This192K card is source-only; future Git/view/export/control/cold cards are independent'},
        'storage': {'source_card': {'path': str(CARD), **dict(zip(('bytes', 'sha256'), CARD_PIN))}, 'hard_complete_bytes': 196608,
            'five_in_place_participating_source_bytes': 127131, 'five_existing_owner_packages': 'referenced in place and not duplicated or silently recharged as new copies',
            'new_named_files_excluding_this_plan': [own_pin, proof_pin], 'new_named_files_bytes_including_this_plan': 0,
            'complete_gross_including_five_participating_leaves': 0, 'new_tests': 0, 'scratch_bytes': 0,
            'all_helpers': 'self-contained standard-library producer; no uncounted project code helper imported',
            'allocated_bytes': None, 'physical_credit_bytes': 0, 'future_writes_after_freeze': 0,
            'review_at_utc': card['review_at_utc'], 'record_review_at_utc': (now+timedelta(days=180)).isoformat()}}
    while True:
        raw = encode(plan); new_bytes = len(own_raw)+len(proof)+len(raw); gross = 127131+new_bytes
        if new_bytes == plan['storage']['new_named_files_bytes_including_this_plan']:
            break
        plan['storage']['new_named_files_bytes_including_this_plan'] = new_bytes
        plan['storage']['complete_gross_including_five_participating_leaves'] = gross
    # The admitted card caps these three files jointly, rather than giving
    # independent per-file quotas; all helpers and all five source leaves count.
    require(new_bytes <= 61440 and gross <= 196608,
            'complete source gross exceeds approved bounds '+str(gross))
    with paths[0].open('xb') as stream:
        stream.write(proof)
    with paths[1].open('xb') as stream:
        stream.write(raw)
    return {'producer': own_pin, 'qualification': proof_pin, 'plan': {'path': str(paths[1]), **pin(raw)},
        'five_participating_source_bytes': 127131, 'new_named_files_bytes': new_bytes, 'complete_gross': gross,
        'full_manifest': report['complete_manifest'], 'future_phase_quotes': plan['prospective_separate_phase_quotes'],
        'branch_ref_export_Task_created': False}


if __name__ == '__main__':
    if sys.argv[1:] == ['--freeze']:
        print(json.dumps(freeze(), ensure_ascii=False, indent=2))
    else:
        require(not sys.argv[1:], 'only --freeze or no arguments')
        _, _, summary = compose()
        print(json.dumps({k: summary[k] for k in ('status', 'actual_SDK', 'base', 'complete_manifest', 'net_source_bytes')}, indent=2))
