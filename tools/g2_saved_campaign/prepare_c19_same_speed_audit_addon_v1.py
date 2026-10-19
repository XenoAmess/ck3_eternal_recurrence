"""One-leaf source addendum over the frozen C19 canonical tree.

Reconstruct the full old manifest from its pinned source15 inventory and
fifteen frozen delta rows.  Check every mode/blob/size against the immutable
Git parent, then replace only the pinned same-speed observation helper.
compose() writes nothing and never reads a complete Driver or runtime ledger.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re

import prepare_c16_perf_warm_sdk_v1 as exact

REPO = Path(__file__).resolve().parents[2]
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
PARENT = '65f7749cd2114854a2631227f87ee83b7f93d5c9'
PARENT_REF = 'refs/heads/campaign/robert-v20261019-c19-combined-cold-01'
NEW_REF = 'refs/heads/campaign/robert-v20261019-c19-same-speed-audit-01'
BASE = '0e8a190bf3e5ec187e7bc30d76310585922a0b50'
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
BASE_ROOT = N/'sdk-v20261019-candidate/src15'
BASE_FREEZE = N/'robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C18.json'
BASE_PIN = (375083, '624c0a229abea3241474e31958bfe4b4102e970f7032f3fc9821273a15ee1d5b')
HELPER = 'xar_autoplayer/bridge/exact_day_speed_configuration_v1.py'
OLD_PIN = (3412, '7ae8f53a2bbe1a241c8b6f3f00779cd199f6209155c371a962767b9a7d3a4185')
NEW_PIN = (4934, '493573ea5525b6281f4530fb659c5ef95725b14e30b19a998a4b4e92d0b3a53c')
OLD_ROWS_PIN = (373692, 'a91c8952d863eafbf433b1aa4fedec5ad42f8edfe0da4f14a3b29de972649b10')
NEW_ROWS_PIN = (373692, '443af4f80195dc413d5e7add1af7fbadcba65069b91675120226d182020f0abf')
EPOCH = '3642dbf251640efc845ab0c633d8f5f832e49682e482cd1df9b676324fb6ddc3'
FAMILY = 'xar_autoplayer/family_marriage_formal_consumer.py'
FAMILY_PIN = (61273, 'd8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf')
OLD_PLAN = 'docs/ck3-native-ai/evidence/c19-combined-cold-sdk-source-plan-2026-10-20.json'
OLD_PROOF = 'docs/ck3-native-ai/evidence/c19-combined-cold-sdk-source-qualification-2026-10-20.json'
M0_PROOF = 'docs/ck3-native-ai/evidence/same-speed-persistent-audit-source-ready-2026-10-20.json'
M0_TEST = 'ck3_autonomous_player/tests/unit/test_exact_day_same_speed_configuration_v1.py'
INPUT_PINS = {
    'tools/g2_saved_campaign/prepare_c16_perf_warm_sdk_v1.py':
        (25869, 'ed79fdb82f422c4cd17dc9fc1c00a133603dbea2ca4374b980172c1eb33a916b'),
    'tools/g2_saved_campaign/prepare_c19_combined_cold_sdk_v1.py':
        (12899, '4831dc944a60aa0861ce8f769988b44463ef27312e4acabeca492cd4111523f5'),
    'tools/g2_saved_campaign/qualify_c19_combined_cold_sdk_v1.py':
        (7198, 'f29907d1d942f10483c7b2f4c35c962fa148d759eda10564d9042b923808295c'),
    OLD_PLAN: (10051, 'c2e58f17950012ec8717fef262a590b26a117e7523080c179128ba79995a7a84'),
    OLD_PROOF: (50330, '6bf8a60137edc13f626315cde1b9ecb0da61e63bf1e6594f0175d6048bd6931b'),
    M0_PROOF: (1822, '4e985b55d1b67300eb9c4e91d1c0b362334ac898106d71682a8c18eaae01130f'),
    M0_TEST: (20802, 'dfdcaf39eb3f39234713102129fb93676d6c622bc4ba8bd3105a2723009742fc'),
}
SOURCE_CARD = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01') / (
    'M0-AUDIT32KiB-C19-ADDON96KiB-CONTROLS96KiB-M7-TRANSITION160KiB-SOURCE-COMMITMENTS01.json')
CARD_PIN = (2672, 'd667018d1f6c01a622e2f677b68e59c3029fe0139eae5dff47f43c908ee9b8da')
SOURCE_CAP = 98304


def require(ok, why):
    if not ok:
        raise ValueError('C19 same-speed audit addendum denied: ' + why)


def canonical_rows(rows):
    return json.dumps([rows[n] for n in sorted(rows)], sort_keys=True,
                      separators=(',', ':')).encode()


def checked_row(row):
    require(type(row) is dict and set(row) == {
        'relative', 'bytes', 'sha256', 'git_blob_sha1', 'git_mode'}, 'row schema differs')
    exact.safe_relative(row['relative'])
    require(type(row['bytes']) is int and 0 <= row['bytes'] <= 8*1024**2
            and row['git_mode'] in ('100644', '100755')
            and re.fullmatch('[0-9a-f]{64}', row['sha256'])
            and re.fullmatch('[0-9a-f]{40}', row['git_blob_sha1']), 'invalid source row')
    return dict(row)


def source_commitment():
    doc = json.loads(exact.check_bytes(SOURCE_CARD.read_bytes(), CARD_PIN, 'addon source card'))
    scope = doc['scopes']['C19_independent_same_speed_audit_business_addon']
    require(doc['machine_id'] == MACHINE and doc['status'] == 'ADMITTED_SOURCE_ONLY'
            and scope['complete_hard_bytes'] == SOURCE_CAP
            and scope['owner'] == 'warm_sdk_composer', 'source scope differs')
    return doc


def read_parent_rows():
    inputs = {}
    for name, pin in INPUT_PINS.items():
        inputs[name] = exact.check_bytes((REPO/name).read_bytes(), pin, 'frozen input ' + name)
    base = json.loads(exact.check_bytes(BASE_FREEZE.read_bytes(), BASE_PIN, 'actual source15 inventory'))
    require(base['schema'] == 'root.ck3.final-sdk-freeze/v1'
            and base['status'] == 'FINAL_SOURCE_FROZEN' and base['machine_id'] == MACHINE
            and base['business_source_commit'] == BASE
            and Path(base['source_root']).resolve() == BASE_ROOT.resolve()
            and base['source_file_count'] == 1445 and base['source_bytes'] == 59052571,
            'actual family-fixed source15 binding differs')
    original = {}
    for row in base['files']:
        row = checked_row(row); name = row['relative']
        require(name not in original, 'duplicate original row')
        original[name] = row
    require(len(original) == 1445 and len({n.casefold() for n in original}) == 1445
            and sum(r['bytes'] for r in original.values()) == 59052571, 'original inventory differs')
    prior = json.loads(inputs[OLD_PROOF]); plan = json.loads(inputs[OLD_PLAN])
    require(prior['machine_id'] == plan['machine_id'] == MACHINE
            and prior['base_business_commit'] == plan['base']['business_commit'] == BASE
            and prior['base_freeze']['sha256'] == plan['base']['freeze']['sha256'] == BASE_PIN[1]
            and len(prior['delta']) == 15 and prior['new_leaves'] == 9
            and prior['changed_existing_leaves'] == 6, 'old composition origin differs')
    rows = {n: dict(r) for n, r in original.items()}; seen = set()
    for change in prior['delta']:
        name = exact.safe_relative(change['relative'])
        require(name not in seen and change['before'] == rows.get(name), 'old delta preimage differs')
        after = checked_row(change['after'])
        require(after['relative'] == name and change['net_bytes'] ==
                after['bytes'] - (change['before']['bytes'] if change['before'] else 0), 'old delta differs')
        rows[name] = after; seen.add(name)
    require(len(rows) == 1454 and sum(r['bytes'] for r in rows.values()) == 59176029
            and HELPER not in seen and FAMILY not in seen, 'old manifest arithmetic differs')
    exact.check_bytes(canonical_rows(rows), OLD_ROWS_PIN, 'old exact full1454 rows')
    require(prior['complete_manifest'] == plan['output']['complete_manifest']
            and prior['complete_manifest']['canonical_rows_JSON'] == exact.pin(canonical_rows(rows)),
            'old full-manifest claims differ')
    require(exact.git('rev-parse', PARENT_REF).decode().strip() == PARENT, 'old create-only ref changed')
    metadata = exact.git('ls-tree', '-r', '-l', '-z', PARENT, '--', exact.PREFIX)
    git_rows = {}
    for entry in metadata.split(b'\0'):
        if not entry:
            continue
        header, path = entry.split(b'\t', 1)
        mode, kind, blob, size = header.split(); path = path.decode()
        require(kind == b'blob' and path.startswith(exact.PREFIX), 'unexpected Git entry')
        name = exact.safe_relative(path[len(exact.PREFIX):])
        require(name not in git_rows, 'duplicate Git source row')
        git_rows[name] = (mode.decode(), blob.decode(), int(size))
    require(set(git_rows) == set(rows) and all(git_rows[n] ==
        (r['git_mode'], r['git_blob_sha1'], r['bytes']) for n, r in rows.items()),
        'immutable parent differs in mode/blob/size from full1454 SHA inventory')
    return original, rows, prior, inputs


def one_insertion(old, new):
    edits = [(tag, a, b, c, d) for tag, a, b, c, d in difflib.SequenceMatcher(
        None, old.splitlines(keepends=True), new.splitlines(keepends=True), autojunk=False).get_opcodes()
        if tag != 'equal']
    require(len(edits) == 1 and edits[0][0] == 'insert', 'only one insertion is permitted')
    _, a, b, c, d = edits[0]; require(a == b, 'old bytes replaced')
    old_lines = old.splitlines(keepends=True); new_lines = new.splitlines(keepends=True)
    offset = sum(map(len, old_lines[:a])); inserted = b''.join(new_lines[c:d])
    require(len(inserted) == 1522 and old[:offset] + inserted + old[offset:] == new
            and new[:offset] + new[offset + len(inserted):] == old,
            'insertion does not exactly invert all old helper bytes')
    before_asts = exact.function_asts(old); after_asts = exact.function_asts(new)
    names = sorted(n for n in set(before_asts) | set(after_asts)
                   if before_asts.get(n) != after_asts.get(n))
    require(names == ['prepare_exact_day_speed_v1'], 'unexpected function changed')
    def outside_functions(raw):
        return [ast.dump(n, include_attributes=False) for n in ast.parse(raw).body
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    require(outside_functions(old) == outside_functions(new), 'imports or module setup changed')
    compile(new, HELPER, 'exec', dont_inherit=True)
    return {'kind': 'one_exact_success_branch_insertion', 'offset_in_old_bytes': offset,
            'inserted': exact.pin(inserted), 'inverse_restores_entire_old_helper': True,
            'changed_function_ASTs': names, 'all_other_function_ASTs_and_imports_unchanged': True}


def compose():
    original, rows, prior, inputs = read_parent_rows()
    old = exact.check_bytes(exact.git_source(PARENT, HELPER), OLD_PIN, 'old canonical helper')
    require(exact.blob_sha(old) == rows[HELPER]['git_blob_sha1'], 'old helper Gitblob differs')
    new = exact.check_bytes((REPO/exact.PREFIX/HELPER).read_bytes(), NEW_PIN, 'M0 frozen audit helper')
    m0 = json.loads(inputs[M0_PROOF])
    require(m0['machine_id'] == MACHINE and m0['old_helper'] == exact.pin(old)
            and m0['helper']['sha256'] == NEW_PIN[1] and m0['helper']['bytes'] == NEW_PIN[0]
            and m0['test']['sha256'] == INPUT_PINS[M0_TEST][1], 'M0 provenance differs')
    operation = one_insertion(old, new)
    before = dict(rows[HELPER]); after = {**before, **exact.pin(new), 'git_blob_sha1': exact.blob_sha(new)}
    parent_rows = {n: dict(r) for n, r in rows.items()}; rows[HELPER] = after
    require([n for n in rows if rows[n] != parent_rows[n]] == [HELPER], 'extra parent delta')
    stable = [rows[n] for n in sorted(rows)]; raw = canonical_rows(rows)
    exact.check_bytes(raw, NEW_ROWS_PIN, 'new exact full1454 rows')
    require(len(rows) == 1454 and sum(r['bytes'] for r in rows.values()) == 59177551,
            'new manifest arithmetic differs')
    source15_delta = [n for n in rows if rows[n] != original.get(n)]
    require(len(source15_delta) == 16 and len(set(rows)-set(original)) == 9
            and (rows[FAMILY]['bytes'], rows[FAMILY]['sha256']) == FAMILY_PIN
            and rows[FAMILY] == original[FAMILY], 'family or original source15 delta changed')
    epoch_inputs = prior['epoch_inputs']
    require('bridge/exact_day_speed_configuration_v1.py' not in epoch_inputs
            and all(rows['xar_autoplayer/' + name]['sha256'] == pin for name, pin in epoch_inputs.items()),
            'audit helper unexpectedly changes an epoch input')
    epoch = hashlib.sha256(json.dumps(epoch_inputs, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    require(epoch == prior['epoch_source_model'] == EPOCH, 'unchanged epoch model differs')
    dependencies = ['xar_autoplayer/bridge/driver.py', 'xar_autoplayer/bridge/version_identity.py']
    require(all(rows[n] == original[n] for n in dependencies), 'helper dependency is not source15 original')
    report = {
        'schema': 'xar.c19.same-speed-audit-addon-source-composition/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOURCE_ONLY_NOT_ADOPTED',
        'actual_source15_base': {'path': str(BASE_FREEZE), **dict(zip(('bytes', 'sha256'), BASE_PIN)),
            'source_root': str(BASE_ROOT), 'business_commit': BASE, 'files': 1445},
        'parent': {'commit': PARENT, 'ref': PARENT_REF, 'files': 1454, 'source_bytes': 59176029,
            'canonical_rows_JSON': dict(zip(('bytes', 'sha256'), OLD_ROWS_PIN)),
            'all_rows_reconstructed_and_Git_mode_blob_size_verified': True},
        'complete_manifest': {'file_count': 1454, 'source_bytes': 59177551,
            'canonical_rows_JSON': exact.pin(raw), 'access': 'compose() returns all1454 rows in memory'},
        'delta_from_parent': [{'relative': HELPER, 'before': before, 'after': after, 'net_bytes': 1522}],
        'unchanged_parent_rows': 1453, 'original_source15_total_delta': 16,
        'original_source15_new_leaves': 9, 'original_source15_changed_existing_leaves': 7,
        'original_source15_unchanged_leaves': 1438, 'operation': operation,
        'family_fix_preserved': rows[FAMILY], 'prior_fifteen_delta_rows_unchanged': True,
        'M7_WAL_M2_Driver_Runtime_owner_rootparser_epoch_bytes_unchanged': True,
        'epoch_source_model': epoch, 'epoch_unchanged_reason': 'Helper is outside existing epoch names; no additional epoch leaf is changed.',
        'helper_direct_dependency_rows': [rows[n] for n in dependencies],
        'reused_M0_functional_qualification': {'path': M0_PROOF, **dict(zip(('bytes', 'sha256'), INPUT_PINS[M0_PROOF])),
            'result': m0['focused'], 'tests_rerun': 0},
        'prospective_original_source15_dual_changed4096cluster_upper':
            sum(2*((rows[n]['bytes']+4095)//4096)*4096 for n in source15_delta),
        'prospective_parent_only_dual_changed4096cluster_upper': 16384,
        'prospective_sizes_are_not_capacity_or_runtime_admission': True,
        'semantics': 'Observation already_observed/submittedFalse/acceptedNone. Native commands remain3; audit rows4. No setter ACK or world credit.',
        'new_create_only_ref': NEW_REF, 'Root_parent_commit': PARENT,
        'Native30_binary_or_loaded_qualification_added': 0, 'actual_H': 'unknown',
        'actual_performance_credit': None, 'Driver_SAVE_ledger_body_reads': 0,
        'D_Git_Task_Game_RPC_writes': 0, 'FULL_timing_business_leaves_added': 0,
        'historical_recovery_or_copy_optimization_included': False,
    }
    require(report['prospective_original_source15_dual_changed4096cluster_upper'] == 4177920,
            'prospective data quote differs')
    return {HELPER: new}, stable, report


def canonical_anchor_with_root_writer(git_writer, *, anchor_ref, root_release_sha256):
    """Optional Root-owned recipe; never invoked by compose or qualification.

    A separately admitted Root callback alone may write objects/create the new
    ref.  Every sibling tree entry and all1453 other source rows are retained.
    No checkout, index, master, old ref, D tree or runtime is changed.
    """
    require(callable(git_writer) and anchor_ref == NEW_REF
            and re.fullmatch('[0-9a-f]{64}', root_release_sha256), 'Root release/ref required')
    require(not exact.git('for-each-ref', '--format=%(refname)', anchor_ref).strip(), 'new ref already exists')
    changed, rows, report = compose(); new = changed[HELPER]
    blob = git_writer(['hash-object', '-w', '--stdin'], new).decode().strip()
    require(blob == exact.blob_sha(new), 'Root-written helper blob differs')
    parts = (exact.PREFIX + HELPER).split('/')

    def replace(tree, depth):
        entries = exact.git('ls-tree', '-z', tree).split(b'\0'); rebuilt = []; matches = 0
        for entry in entries:
            if not entry:
                continue
            header, name = entry.split(b'\t', 1); mode, kind, oid = header.split()
            if name.decode() == parts[depth]:
                matches += 1
                if depth == len(parts)-1:
                    require(kind == b'blob' and oid.decode() == report['delta_from_parent'][0]['before']['git_blob_sha1'],
                            'parent helper tree entry differs')
                    replacement = blob
                else:
                    require(kind == b'tree', 'parent directory is not a tree')
                    replacement = replace(oid.decode(), depth+1)
                entry = b' '.join((mode, kind, replacement.encode())) + b'\t' + name
            rebuilt.append(entry + b'\0')
        require(matches == 1, 'exact parent path missing or duplicated')
        return git_writer(['mktree', '-z'], b''.join(rebuilt)).decode().strip()

    tree = replace(exact.git('rev-parse', PARENT+'^{tree}').decode().strip(), 0)
    changes = exact.git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z', PARENT, tree)
    require(changes.split(b'\0') == [(exact.PREFIX+HELPER).encode(), b''], 'Root tree changed another leaf')
    commit = git_writer(['commit-tree', tree, '-p', PARENT], (
        'Add same-speed observation audit to C19 canonical SDK\n\nRoot release '+root_release_sha256+'\n').encode()).decode().strip()
    require(re.fullmatch('[0-9a-f]{40}', commit), 'Root commit response differs')
    git_writer(['update-ref', anchor_ref, commit, '0'*40], None)
    require(exact.git('rev-parse', anchor_ref).decode().strip() == commit
            and exact.git('rev-parse', PARENT_REF).decode().strip() == PARENT, 'create-only ref readback differs')
    return {'commit': commit, 'parent': PARENT, 'ref': anchor_ref, 'tree': tree,
            'complete_manifest': report['complete_manifest'], 'source15_delta': 16,
            'new_Git_objects_only': True, 'D_Task_Game_writes': 0}


if __name__ == '__main__':
    _, _, report = compose()
    print(json.dumps(report, ensure_ascii=False, indent=2))
