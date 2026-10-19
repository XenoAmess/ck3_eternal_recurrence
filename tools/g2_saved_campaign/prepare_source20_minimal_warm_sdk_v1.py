"""Source20: compose only the necessary audit, retry and diagnostic leaves.

The complete actual Source15 inventory is the sole base. Independent frozen
transforms operate on its actual Service/MCP bytes in RAM. No canonical master
Service, C19 business bytes, full SDK output, runtime state or Git writes are
used by compose().
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import prepare_c16_perf_warm_sdk_v1 as exact
import transform_campaign_root_terminal_retry_v1 as retry
import prepare_campaign_root_retry_mcp_observability_v1 as observe

REPO = Path(__file__).resolve().parents[2]
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
BASE = '0e8a190bf3e5ec187e7bc30d76310585922a0b50'
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
P = N/'p51-fresh1066-v20261019-prepare01'
BASE_ROOT = N/'sdk-v20261019-candidate/src15'
BASE_FREEZE = N/'robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C18.json'
BASE_PIN = (375083, '624c0a229abea3241474e31958bfe4b4102e970f7032f3fc9821273a15ee1d5b')
BASE_ROWS_PIN = (371514, '20b02b77ebbe43b9f822717295ac377b9ca445d43b11429d1117f330cc8252f7')
SERVICE = 'xar_autoplayer/bridge/service.py'
MCP = 'xar_autoplayer/bridge/mcp_server.py'
SPEED = 'xar_autoplayer/bridge/exact_day_speed_configuration_v1.py'
PREDICATE = 'xar_autoplayer/bridge/campaign_root_terminal_retry_v1.py'
DIAGNOSTIC = 'xar_autoplayer/bridge/campaign_root_retry_diagnostic_v1.py'
READONLY = 'xar_autoplayer/bridge/readonly_planning_retry_v1.py'
FAMILY = 'xar_autoplayer/family_marriage_formal_consumer.py'
FAMILY_PIN = (61273, 'd8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf')
OLD_PINS = {
    SERVICE: (877777, '5b49eaf311269230aeb046e9f61ccb829aa4392c627b23f0878e14f42c3883f8'),
    MCP: (263923, 'b4d2fab30a5c8cd8a0291c3759d9a0518b31df55698002d8ea6e7e64ad3bfb4a'),
    SPEED: (3412, '7ae8f53a2bbe1a241c8b6f3f00779cd199f6209155c371a962767b9a7d3a4185'),
    READONLY: (13443, '69ff7e9dc23dc6d06c2703e8c0f4a7475589cb91475b12f4e11e569234194414'),
}
NEW_PINS = {
    SERVICE: (878063, '642e62f20b49ceed796b7dcb106b19cb94043db0593cceabeca0f0746d7aabb9'),
    MCP: (264359, '8b1c260f779dbd3e25770af75ed87de0cfd39200454c7662f611accfce92688f'),
    SPEED: (4934, '493573ea5525b6281f4530fb659c5ef95725b14e30b19a998a4b4e92d0b3a53c'),
    PREDICATE: (3566, 'c7187d98c791148686369636848a5209b4323c25618c050f81b840da8ce9641c'),
    DIAGNOSTIC: (6111, '9c2a85ba1b00efd0a68ca3c92bb195dd15938223a91ad3abfdc794ebec41f4e9'),
    READONLY: (14139, 'a761179ca74f576950cdeda76649af9f39d8f1c831af21941753b622696cb24f'),
}
M0_PROOF = 'docs/ck3-native-ai/evidence/same-speed-persistent-audit-source-ready-2026-10-20.json'
MCP_PROOF = 'docs/ck3-native-ai/evidence/source20-campaign-root-retry-mcp-observability-2026-10-20.json'
MCP_ADDENDUM = 'docs/ck3-native-ai/evidence/source20-campaign-root-retry-mcp-bounded-input-addendum-2026-10-20.json'
MCP_BUDGET_PROOF = 'docs/ck3-native-ai/evidence/source20-campaign-root-retry-budget-diagnostic-addendum-2026-10-20.json'
M5_PROOF = 'docs/ck3-native-ai/evidence/source20-campaign-root-shared-budget-addendum-2026-10-20.json'
INPUT_PINS = {
    'tools/g2_saved_campaign/prepare_c16_perf_warm_sdk_v1.py':
        (25869, 'ed79fdb82f422c4cd17dc9fc1c00a133603dbea2ca4374b980172c1eb33a916b'),
    'tools/g2_saved_campaign/transform_campaign_root_terminal_retry_v1.py':
        (5257, 'fb787f922b21c869bc94acdef0aff9ad5fc729f3469a41b6f8c86b1429efa729'),
    'tools/g2_saved_campaign/prepare_campaign_root_retry_mcp_observability_v1.py':
        (3340, '32770be8ebe15169c9418295f2cd11c068302bd2c1bc1f40c310c2d69c95a7e6'),
    M0_PROOF: (1822, '4e985b55d1b67300eb9c4e91d1c0b362334ac898106d71682a8c18eaae01130f'),
    MCP_PROOF: (2744, 'd821fdd4705266b2d1c855286bb0c98e7b6cf13a11442e08ca0226783c3fe9f0'),
    MCP_ADDENDUM: (3254, '3e3ec2ae12d2d8db78165b7d074561fefd02cf308babccf13cca7e82b864f78d'),
    MCP_BUDGET_PROOF: (3704, 'e660a710006bcf217a029b68b1e335c522ce55be2d9ce74f27b275fcee04b029'),
    M5_PROOF: (7701, '448daca214cc539d240a7d984796ca4c1ae1a2f52a29588d79d5354f06ecc4b0'),
}
CARD = Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01') / (
    'COMPOSER-SOURCE20-64KiB-M6-RECEIPT128KiB-TEST128KiB-SOURCE-COMMITMENTS01.json')
CARD_PIN = (2428, '6b1d3056eaa215037e61a9c37360a1372e4bb3fa18c17ddba6cfb37c394f7f9e')
SOURCE_CAP = 65536
# The withdrawn five-delta candidate is superseded by the pinned shared-budget
# addendum and the fourth existing leaf. The actual source pins remain mandatory.
M5_SHARED_BUDGET_QUALIFIED = True
NEW_REF = 'refs/heads/campaign/robert-v20261019-c20-campaign-root-retry-warm-01'
PROPOSED_ROOTS = {
    'source_destination': str(N/'sdk-v20261019-candidate/src17'),
    'reference_destination': str(N/'sdk-v20261019-candidate/reference-c20/src'),
    'output_root': str(P/'c20-campaign-root-retry97/immutable-source-export'),
    'authority': 'runtime message; names only, absence/closed-state/capacity not inspected or admitted',
}


def require(ok, why):
    if not ok:
        raise ValueError('Source20 minimal warm denied: '+why)


def canonical_rows(rows):
    return json.dumps([rows[n] for n in sorted(rows)], sort_keys=True, separators=(',', ':')).encode()


def read_base():
    for name, pin in INPUT_PINS.items():
        exact.check_bytes((REPO/name).read_bytes(), pin, 'frozen input '+name)
    raw = exact.check_bytes(BASE_FREEZE.read_bytes(), BASE_PIN, 'fresh actual Source15 inventory')
    doc = json.loads(raw)
    require(doc['schema'] == 'root.ck3.final-sdk-freeze/v1' and doc['machine_id'] == MACHINE
        and doc['status'] == 'FINAL_SOURCE_FROZEN' and doc['business_source_commit'] == BASE
        and Path(doc['source_root']).resolve() == BASE_ROOT.resolve()
        and doc['source_file_count'] == 1445 and doc['source_bytes'] == 59052571, 'base identity differs')
    rows = {}
    for row in doc['files']:
        require(set(row) == {'relative', 'bytes', 'sha256', 'git_blob_sha1', 'git_mode'}, 'row shape differs')
        name = exact.safe_relative(row['relative'])
        require(name not in rows and type(row['bytes']) is int and 0 <= row['bytes'] <= 8*1024**2
            and row['git_mode'] in ('100644', '100755')
            and re.fullmatch('[0-9a-f]{64}', row['sha256'])
            and re.fullmatch('[0-9a-f]{40}', row['git_blob_sha1']), 'invalid inventory row')
        rows[name] = dict(row)
    require(len(rows) == len({n.casefold() for n in rows}) == 1445
            and sum(r['bytes'] for r in rows.values()) == 59052571, 'inventory arithmetic differs')
    exact.check_bytes(canonical_rows(rows), BASE_ROWS_PIN, 'complete actual Source15 rows')
    verify_git_rows(BASE, rows)
    return doc, rows


def verify_git_rows(tree, rows):
    actual = {}
    for entry in exact.git('ls-tree', '-r', '-l', '-z', tree, '--', exact.PREFIX).split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1); mode, kind, oid, size = header.split()
        name = name.decode(); require(kind == b'blob' and name.startswith(exact.PREFIX), 'unexpected Git entry')
        name = exact.safe_relative(name[len(exact.PREFIX):]); require(name not in actual, 'duplicate Git entry')
        actual[name] = (mode.decode(), oid.decode(), int(size))
    require(set(actual) == set(rows) and all(actual[n] == (r['git_mode'], r['git_blob_sha1'], r['bytes'])
            for n, r in rows.items()), 'full Git mode/blob/size inventory differs')


def actual_source(name, rows):
    path = BASE_ROOT/name
    require(path.is_file() and not path.is_symlink(), 'actual changed source missing/link')
    raw = path.read_bytes(); row = rows[name]
    exact.check_bytes(raw, (row['bytes'], row['sha256']), 'actual Source15 '+name)
    require(exact.blob_sha(raw) == row['git_blob_sha1'], 'actual Gitblob differs '+name)
    return raw


def memory_git_objects(changed):
    """Return six blobs and five canonical ancestor trees without writing Git."""
    objects = []
    replacements = {name.rsplit('/', 1)[1]: ('100644', 'blob', exact.blob_sha(raw))
                    for name, raw in changed.items()}
    for name, raw in sorted(changed.items()):
        objects.append({'kind': 'blob', 'oid': exact.blob_sha(raw), 'path': exact.PREFIX+name, 'raw': raw})
    directories = ['', 'ck3_autonomous_player', 'ck3_autonomous_player/src',
                   'ck3_autonomous_player/src/xar_autoplayer',
                   'ck3_autonomous_player/src/xar_autoplayer/bridge']
    child = None
    for directory in reversed(directories):
        entries = {}
        for entry in exact.git('ls-tree', '-z', BASE+(':'+directory if directory else '')).split(b'\0'):
            if entry:
                header, name = entry.split(b'\t', 1); mode, kind, oid = header.decode().split()
                entries[name.decode()] = (mode, kind, oid)
        if child is None:
            require(all(n in entries for n in (SERVICE.rsplit('/', 1)[1], MCP.rsplit('/', 1)[1], SPEED.rsplit('/', 1)[1], READONLY.rsplit('/', 1)[1]))
                and PREDICATE.rsplit('/', 1)[1] not in entries and DIAGNOSTIC.rsplit('/', 1)[1] not in entries,
                'source bridge path preimage differs')
            entries.update(replacements)
        else:
            name, oid = child
            require(name in entries and entries[name][1] == 'tree', 'ancestor path differs')
            entries[name] = (entries[name][0], 'tree', oid)
        ordered = sorted(entries.items(), key=lambda e: e[0].encode()+
                         (b'/' if e[1][1] == 'tree' else b''))
        raw = b''.join(mode.lstrip('0').encode()+b' '+name.encode()+b'\0'+bytes.fromhex(oid)
                       for name, (mode, kind, oid) in ordered)
        oid = hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        objects.append({'kind': 'tree', 'oid': oid, 'path': directory or '<root>', 'raw': raw})
        child = (directory.rsplit('/', 1)[-1], oid)
    require(len(objects) == 11, 'expected six blobs and five ancestor trees')
    return objects, child[1]


def quote(changed, objects):
    # No compression savings: add4096 bytes to every complete serialized object,
    # align to4096, then reserve ALL retained objects plus the largest temp too.
    def loose(kind, count):
        serialized = count+len(kind)+len(str(count))+2
        return ((serialized+4096+4095)//4096)*4096
    inventory = [{'kind': o['kind'], 'path': o['path'], 'oid': o['oid'], 'payload_bytes': len(o['raw']),
                  'loose_uncompressed4096overhead_cluster_upper': loose(o['kind'], len(o['raw']))} for o in objects]
    inventory.append({'kind': 'commit', 'path': '<future Root commit>', 'payload_cap_bytes': 8192,
                      'loose_uncompressed4096overhead_cluster_upper': loose('commit', 8192)})
    retained = sum(o['loose_uncompressed4096overhead_cluster_upper'] for o in inventory)
    largest = max(o['loose_uncompressed4096overhead_cluster_upper'] for o in inventory)
    git_peak = retained+largest+65536
    git_envelope = ((git_peak+262143)//262144)*262144
    data = sum(2*((len(raw)+4095)//4096)*4096 for raw in changed.values())
    components = {'Z_Git_uncompressed_alias_temp_refs_envelope': git_envelope,
        'D_dual_changed4096cluster_upper': data, 'D_rich_JSON_MFT_and_FS_reserve': 4194304,
        'D_compact_ROOTFINAL_envelope': 524288, 'D_controls_and_feeder_envelope': 409600,
        'D_Task_specs_initial_metadata_logs_envelope': 262144, 'D_atomic_control_temp_envelope': 65536}
    return {'status': 'QUOTE_ONLY_NOT_CAPACITY_ADMISSION', 'logical_changed_source_each': sum(map(len, changed.values())),
        'Git_object_inventory': inventory, 'Git_retained_upper': retained, 'Git_largest_extra_temporary_upper': largest,
        'Git_refs_locks_dirs_extra_reserve': 65536, 'Git_conservative_peak_upper': git_peak,
        'compression_credit': 0, 'Git_callback_requires': 'stdin RAM payload; no extra disk source/full SDK alias; commit payload<=8192. Any different writer adds its actual peak before admission.',
        'components': components, 'complete_stage_quote_upper': sum(components.values()),
        'Root_budget_ceiling_bytes': 12582912, 'budget_is_not_write_authorization': True,
        'physical_allocated_bytes': None, 'closed_Driver_bytes': None,
        'closed_Driver_copy': 'Separate actual normal-close stat and existing Driver-budget card; not zero, not read or silently included in this source-stage quote.',
        'feeder_controls_atomic': '400KiB includes then actual controls+feeder;64KiB is additional atomic temp. Final owner exact pins/peak must fit or quote rises; current controls not assumed installed.'}


def compose():
    require(M5_SHARED_BUDGET_QUALIFIED,
            'withdrawn M5 candidate: await frozen shared whole-plan budget inputs and integration proof')
    _, original = read_base()
    old = {name: actual_source(name, original) for name in OLD_PINS}
    for name, pin in OLD_PINS.items():
        exact.check_bytes(old[name], pin, 'mandatory actual preimage '+name)
    changed = {SERVICE: retry.transform_service_source(old[SERVICE])}
    require(retry.transform_service_source(changed[SERVICE], reverse=True) == old[SERVICE], 'Service inverse differs')
    changed[READONLY] = retry.transform_retry_source(old[READONLY])
    require(retry.transform_retry_source(changed[READONLY], reverse=True) == old[READONLY], 'shared budget inverse differs')
    changed[MCP], mcp_report = observe.transform_mcp_source_v1(old[MCP])
    require(changed[MCP].count(observe.NEW.encode()) == 1 and changed[MCP].replace(
        observe.NEW.encode(), observe.OLD.encode(), 1) == old[MCP], 'MCP inverse differs')
    for name in (SPEED, PREDICATE, DIAGNOSTIC):
        changed[name] = exact.check_bytes((REPO/exact.PREFIX/name).read_bytes(), NEW_PINS[name], 'frozen helper '+name)
    for name, raw in changed.items():
        exact.check_bytes(raw, NEW_PINS[name], 'minimal candidate '+name)
        compile(raw, name, 'exec', dont_inherit=True)
    require(PREDICATE not in original and DIAGNOSTIC not in original, 'new helper already in old base')
    # The audit change remains exactly one insertion, not a replacement helper.
    import difflib
    hunks = list(difflib.SequenceMatcher(None, old[SPEED].splitlines(keepends=True),
        changed[SPEED].splitlines(keepends=True), autojunk=False).get_opcodes())
    edits = [h for h in hunks if h[0] != 'equal']
    require(len(edits) == 1 and edits[0][0] == 'insert', 'unexpected same-speed delta')
    _, a, b, c, d = edits[0]; offset = sum(map(len, old[SPEED].splitlines(keepends=True)[:a]))
    insertion = b''.join(changed[SPEED].splitlines(keepends=True)[c:d])
    require(a == b and len(insertion) == 1522 and changed[SPEED][:offset]+changed[SPEED][offset+1522:] == old[SPEED],
            'same-speed inverse differs')
    rows = {n: dict(r) for n, r in original.items()}; delta = []
    for name, raw in sorted(changed.items()):
        before = rows.get(name)
        after = {'relative': name, **exact.pin(raw), 'git_blob_sha1': exact.blob_sha(raw),
                 'git_mode': before['git_mode'] if before else '100644'}
        rows[name] = after; delta.append({'relative': name, 'before': before, 'after': after,
            'net_bytes': len(raw)-(before['bytes'] if before else 0)})
    require(len(rows) == 1447 and len(delta) == 6 and sum(r['bytes'] for r in rows.values()) == 59065188
        and len(set(rows)-set(original)) == 2 and all(rows[n] == original[n] for n in original if n not in changed),
        'complete minimal composition arithmetic differs')
    require((rows[FAMILY]['bytes'], rows[FAMILY]['sha256']) == FAMILY_PIN and FAMILY not in changed,
            'family fix differs')
    objects, tree = memory_git_objects(changed)
    report = {'schema': 'xar.source20.minimal-warm-sdk-source-composition/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOURCE_ONLY_NOT_ADOPTED',
        'base': {'freeze': {'path': str(BASE_FREEZE), **dict(zip(('bytes', 'sha256'), BASE_PIN))},
            'source_root': str(BASE_ROOT), 'business_commit': BASE, 'files': 1445, 'source_bytes': 59052571,
            'canonical_rows_JSON': dict(zip(('bytes', 'sha256'), BASE_ROWS_PIN)),
            'all1445_Git_mode_blob_size_checked': True,
            'unchanged1441_body_SHA_authority': 'Pinned actual624c inventory; not falsely rehashed this run. Original exporter rechecks frozen inputs before materialization.'},
        'complete_manifest': {'file_count': len(rows), 'source_bytes': sum(r['bytes'] for r in rows.values()),
            'canonical_rows_JSON': exact.pin(canonical_rows(rows)), 'access': 'compose() returns all1447 rows in RAM'},
        'delta': delta, 'changed_existing_leaves': 4, 'new_leaves': 2, 'unchanged_original_leaves': 1441,
        'Service_inverse_entire_actual_bytes': True, 'Service_existing_retry_method_segment_unchanged': True,
        'existing_ContextVar_shared_claim_API': 'typed inner claim and existing outer retry share one remaining budget; outer loop is not replaced',
        'readonly_budget_inverse_entire_actual_bytes': True,
        'MCP_actual_transform': mcp_report, 'audit_single_insertion_bytes': 1522,
        'family_fix_preserved': rows[FAMILY], 'candidate_Git_tree_model': tree,
        'candidate_tree_model_not_actual_Git_object_or_deployment': True,
        'prospective_capacity': quote(changed, objects), 'proposed_roots': PROPOSED_ROOTS,
        'Root_create_only_ref': NEW_REF, 'Root_parent_commit': BASE,
        'existing_frozen_input_pins': [{'path': n, **dict(zip(('bytes', 'sha256'), pin))} for n, pin in INPUT_PINS.items()],
        'boundaries': {'C19_M7_multiday_finite_source_bytes_included': False,
            'canonical_master_Service_or_MCP_overlay': False, 'Source15_temporary_classifier_wrapper_included': False,
            'Native_binary_ABI_or_qualification_changed': False, 'current_C18_modified': False,
        'new_retry_beyond_shared_once_or_Native_reads': 0, 'runtime_Driver_SAVE_ledger_body_reads': 0,
            'D_Git_Task_Game_RPC_writes': 0, 'actual_seconds_saved': None, 'actual_runtime_recovery_credit': False},
        'future_materialization': 'Original immutable full-view exporter8b697; same Native29pin8ace and Hostd90 remain. Needs Root actual new business anchor, exact capacity card and then normal warm controls/inputs. No C19 Native30/M7 cold authority is imported.'}
    require(report['prospective_capacity']['components']['D_dual_changed4096cluster_upper'] == 2367488,
            'data quote differs')
    return changed, [rows[n] for n in sorted(rows)], report


def canonical_anchor_with_root_writer(git_writer, *, anchor_ref, root_release_sha256):
    """Only a separately admitted Root writer can execute this create-only recipe."""
    require(callable(git_writer) and anchor_ref == NEW_REF and re.fullmatch('[0-9a-f]{64}', root_release_sha256),
            'Root callback/release/ref required')
    require(not exact.git('for-each-ref', '--format=%(refname)', anchor_ref).strip(), 'new ref exists')
    changed, stable, report = compose(); objects, tree = memory_git_objects(changed)
    for obj in objects:
        oid = git_writer(['hash-object', '-t', obj['kind'], '-w', '--stdin'], obj['raw']).decode().strip()
        require(oid == obj['oid'], 'Root-written object differs')
    verify_git_rows(tree, {row['relative']: row for row in stable})
    paths = exact.git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z', BASE, tree).split(b'\0')
    require(set(paths) == {*( (exact.PREFIX+n).encode() for n in changed), b''}, 'new tree has unrelated changes')
    commit = git_writer(['commit-tree', tree, '-p', BASE], (
        'Compose necessary Source20 audit and campaign-root retry diagnostics\n\nRoot release '+root_release_sha256+'\n').encode()).decode().strip()
    require(re.fullmatch('[0-9a-f]{40}', commit), 'invalid Root commit response')
    git_writer(['update-ref', anchor_ref, commit, '0'*40], None)
    require(exact.git('rev-parse', anchor_ref).decode().strip() == commit, 'new ref readback differs')
    return {'commit': commit, 'parent': BASE, 'ref': anchor_ref, 'tree': tree,
            'complete_manifest': report['complete_manifest'], 'D_Task_Game_writes': 0}


if __name__ == '__main__':
    _, _, result = compose()
    print(json.dumps(result, ensure_ascii=False, indent=2))
