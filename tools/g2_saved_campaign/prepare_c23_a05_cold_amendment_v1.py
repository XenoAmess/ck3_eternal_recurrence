"""Pure RAM amendment of the actual partial A05 saved-basis helper contract.

Never retries adoption or modifies deployed files. Root must separately admit
the exact returned quote, rename each old leaf to its absent same-volume archive
path, and create each new leaf with xb. Old hardlinks are never truncated.
"""
from __future__ import annotations

from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

OWN = Path(__file__).resolve().parent
REPO = OWN.parents[1]
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T = N / 'robert30-v20261019-campaign01/runtime'
U = T.with_name('runtime-a05')
O = N / 'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'
ARCHIVE = O / 'post-close/a05-prepare-contract01'
QUOTE = O / 'A05-ROOT-QUOTE02.json'
FAILURE = O / 'A05-ACTUAL-PREPARE-CONTRACT-FAILURE01.json'
INTENT = O / 'A05-PREPARE-INTENT01.json'
HELPER = 'root_c23_a03_source_abort_checkpoint_inputs.py'
POLICY = 'ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json'
FREEZE = 'ROOT-FINAL-SDK-FREEZE-P37C23-A05.json'
CLEAN = 'ROOT-CLEAN-SOURCE-FROZEN-C23-A05.json'
LAUNCH = 'ROOT-LAUNCH-CONFIG-C23-A05.json'
BINDING = 'ROOT-NATIVE30-SDK-BINDING-C23-A05.json'
EXPECTED_LEAVES = {HELPER, POLICY, FREEZE, CLEAN, LAUNCH, BINDING}
QUOTE_PIN = (114511, 'fd03557ffc5e7e36551f4216a8ef360d93df58b349d96e162be1e41e63fc591f')
FAILURE_PIN = (2277, '44989b30155e402a956b152b67db6210a4d220a01b3567e5b8f0232724ffd825')
INTENT_PIN = (896, '2c8de2ce90c91bfc1b5d23973b0c0c8ee643838bbe5b97120693441c04a7c509')
OLD_HELPER_PIN = (15280, '4778f4b406d5c33bc3cb6c52dfb5cea2fa744590d8404c607c9cb86c98d37d3e')
NEW_HELPER_PIN = (17637, 'bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e')
CANDIDATE = OWN / 'prepare_c23_a05_anchor_contract_v1.py'
CANDIDATE_PIN = (7733, '8ddb20e6af475bfdf255cc36cebd20464fb991e36c9f5c22368673cb7c329fda')
NTFS = OWN / 'export_immutable_sdk_views_v1.py'
NTFS_PIN = (22964, '8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432')
REQUESTED_HARD = 524288
FS_RESERVE = 65536
SMALL_RECEIPTS_RESERVE = 16384


def require(ok, why):
    if not ok:
        raise ValueError('A05 cold amendment denied: ' + why)


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def enc(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def raw(path, limit=524288):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= limit, 'bounded ordinary actual input required')
    with path.open('rb') as stream:
        value = stream.read(limit + 1)
    require(0 < len(value) <= limit, 'bounded complete actual input required')
    return value


def ref(path, limit=524288):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), **pin(raw(path, limit))}


def checked(item, limit=524288):
    require(type(item) is dict and set(item) == {'path', 'bytes', 'sha256'}
            and Path(item['path']).is_absolute(), 'exact absolute reference required')
    require(ref(item['path'], limit) == item, 'actual input reference differs')
    value = json.loads(raw(item['path'], limit))
    require(type(value) is dict and value.get('source_fixture') is not True,
            'actual JSON object required')
    return value


def exact_ref(item, path, expected, limit=524288):
    require(Path(item['path']).resolve() == path.resolve()
            and (item['bytes'], item['sha256']) == expected, 'exact event reference differs')
    return checked(item, limit)


def current(value, max_age=600):
    at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(at.tzinfo is not None and at.utcoffset().total_seconds() == 0
            and -10 <= (datetime.now(timezone.utc) - at).total_seconds() <= max_age,
            'fresh explicit UTC observation required')


def _ntfs():
    require((len(raw(NTFS)), pin(raw(NTFS))['sha256']) == NTFS_PIN, 'frozen NTFS helper differs')
    spec = importlib.util.spec_from_file_location('_a05_amendment_ntfs', NTFS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _quiescence(item, failure_ref):
    value = checked(item, 8192)
    require(value.get('schema') == 'xar.C23-A05-quiescent-preparation/v1'
            and value.get('machine_id') == MACHINE and value.get('game_processes') == []
            and value.get('sdk_processes') == [] and value.get('supervisor_task_registered') is False
            and value.get('sdk_process_scope') == 'exact current U5 or exact supervisor A05 SPEC argv; no unknown Python argv',
            'fresh exact A05 Game/SDK/Task quiescence required')
    current(value['observed_at_utc'])
    evidence = value.get('evidence_refs')
    require(type(evidence) is list and len(evidence) == 2 and failure_ref in evidence,
            'raw process/Task evidence and actual failure binding required')
    raw_ref = next(row for row in evidence if row != failure_ref)
    actual = checked(raw_ref, 32768)
    require(actual.get('machine_id') == MACHINE
            and actual.get('observed_at_utc') == value['observed_at_utc']
            and actual.get('kernel', {}).get('actual_active_ck3') == []
            and actual.get('owned_python_matches') == []
            and actual.get('unknown_python_cmdline_pids') == []
            and actual.get('task_actual_absent') is True
            and actual.get('match_scope') == [str(U).lower().replace('/', '\\'),
                str(O / 'tasks/spec-supervisor-a05').lower().replace('/', '\\')],
            'actual zero active CK3, zero current-owned Python, zero unknown argv and absent Task required')
    return value, raw_ref


def _replacement(value, old_refs, new_refs, trace, location=''):
    """Replace exact structured refs and exact full SHA tokens; no byte substring edits."""
    sha_map = {old_refs[path]['sha256']: new_refs[path]['sha256'] for path in new_refs}
    if type(value) is dict:
        result = {key: _replacement(item, old_refs, new_refs, trace, location + '/' + key)
                  for key, item in value.items()}
        if type(value.get('path')) is str and Path(value['path']).is_absolute():
            path = Path(value['path']).resolve()
            if path in new_refs and 'sha256' in value:
                old = old_refs[path]
                require(value['sha256'] == old['sha256']
                        and ('bytes' not in value or value['bytes'] == old['bytes']),
                        'stale structured reference encountered at ' + location)
                result['sha256'] = new_refs[path]['sha256']
                result['path'] = new_refs[path]['path']
                if 'bytes' in value:
                    result['bytes'] = new_refs[path]['bytes']
                trace.append({'json_pointer': location, 'target': str(path), 'kind': 'exact_reference'})
        return result
    if type(value) is list:
        return [_replacement(item, old_refs, new_refs, trace, location + '/' + str(index))
                for index, item in enumerate(value)]
    if type(value) is str and value in sha_map:
        trace.append({'json_pointer': location, 'kind': 'exact_SHA256_token'})
        return sha_map[value]
    return value


def _full_migration(actual_bytes, old_refs, newfull_ref):
    """Only named active consumer fields and one feeder admission literal move."""
    storage = U / 'STORAGE-ADMISSION.json'
    old = json.loads(actual_bytes[storage])
    new = checked(newfull_ref, 32768)
    oldfull_ref = json.loads(actual_bytes[U / LAUNCH])['full_storage_view']
    require(checked(oldfull_ref, 32768) == old
            and new.get('machine_id') == MACHINE and new.get('status') == 'ADMITTED'
            and new.get('schema') == old.get('schema') and new.get('policy_version') == '1.0.0'
            and old.get('review_at_utc') == '2026-10-20T06:30:00+00:00'
            and new.get('review_at_utc') == '2026-10-20T10:30:00+00:00'
            and type(new.get('disk_reserve_bytes')) is int and new['disk_reserve_bytes'] > 0,
            'separately admitted actual A05 10:30 compatible full required')
    deadline = new['review_at_utc']
    require(datetime.now(timezone.utc) < datetime.fromisoformat(deadline), 'newfull review expired')
    seeds = {storage: raw(newfull_ref['path'], 32768)}
    fields = {LAUNCH: ('review_at_utc',),
        'ROOT-PROMO-KEEPER-SOURCE-READY-C23-A05.json': ('source_review_at_utc',),
        'ROOT-OBS-PROFILE-C23.json': ('storage_review_at_utc',)}
    for name, keys in fields.items():
        value = json.loads(actual_bytes[U / name])
        for key in keys:
            require(value.get(key) == old['review_at_utc'], 'actual named old review differs')
            value[key] = deadline
        if name == 'ROOT-OBS-PROFILE-C23.json':
            require(value['storage']['admission_path'] == str(storage)
                    and value['storage']['admission_sha256'] == oldfull_ref['sha256'],
                    'actual profile local full binding differs')
            value['storage'].update(approved_output_roots=new['approved_output_roots'],
                disk_reserve_bytes=new['disk_reserve_bytes'], admission_sha256=newfull_ref['sha256'])
        seeds[U / name] = enc(value)
    feeder = U / 'root_p37c23_same_game_loop_feeder100.py'
    before = actual_bytes[feeder]
    literal = b'and a.get("review_deadline_utc") == "2026-10-20T06:30:00+00:00",'
    require(before.count(literal) == 1, 'one exact feeder review-admission seam required')
    after = before.replace(literal, literal.replace(old['review_at_utc'].encode(), deadline.encode()), 1)
    compile(after, str(feeder), 'exec')
    reverse = after.replace(deadline.encode(), old['review_at_utc'].encode())
    require(ast.dump(ast.parse(reverse), include_attributes=False)
            == ast.dump(ast.parse(before), include_attributes=False),
            'feeder changed beyond the exact review literal')
    seeds[feeder] = after
    return seeds, {Path(oldfull_ref['path']).resolve(): oldfull_ref}, {
        Path(oldfull_ref['path']).resolve(): newfull_ref}, dict(
        old_full=oldfull_ref, new_full=newfull_ref, old_review=old['review_at_utc'],
        new_review=deadline, named_review_fields=fields,
        feeder_literal_occurrences_changed=1, feeder_other_AST_unchanged=True,
        local_full_file=str(storage), native_pin_ref_and_all_full_refs_follow_exact_propagation=True)


def compose(plan, *, helper_bytes, helper_review, newfull_ref=None):
    """Return (six exact new bytes, quote) after verifying all 119 deployed pins.

    quote.admitted_within_requested_hard may be false. A false value is a real
    budget result, not permission to amend. This function never mutates files.
    """
    require(sys.dont_write_bytecode, 'run Python with -B')
    require(type(plan) is dict and plan.get('schema') == 'xar.C23-A05-cold-contract-amendment-input/v1'
            and plan.get('machine_id') == MACHINE and plan.get('owner') == 'Root'
            and plan.get('root_direct_execution_release') is True,
            'explicit Root amendment input required')
    current(plan['observed_at_utc'])
    review = checked(newfull_ref, 32768)['review_at_utc'] if newfull_ref else '2026-10-20T06:30:00+00:00'
    require(datetime.now(timezone.utc) < datetime.fromisoformat(review),
            'shared storage review expired')
    quote = exact_ref(plan['quote_ref'], QUOTE, QUOTE_PIN, 131072)
    failure = exact_ref(plan['failure_ref'], FAILURE, FAILURE_PIN, 8192)
    intent = exact_ref(plan['intent_ref'], INTENT, INTENT_PIN, 8192)
    require(failure.get('schema') == 'xar.C23-A05-actual-prepare-contract-failure/v1'
            and failure.get('machine_id') == MACHINE
            and failure.get('status') == '119_FILES_PREPARED_SAVED_BASIS_CONTRACT_REJECTED_NO_GAME'
            and failure.get('quote') == plan['quote_ref'] and failure.get('consumed_intent') == plan['intent_ref']
            and failure.get('actual_all_119_pins_match_quote') is True
            and failure.get('retry_same_adopter_forbidden') is True
            and failure.get('scheduler_actual_absent') is True
            and failure.get('Task_Game_SDK_RPC_calls') == 0
            and intent.get('status') == 'ONE_SHOT_A05_PREPARE_INTENT'
            and intent.get('machine_id') == MACHINE and intent.get('quote') == plan['quote_ref']
            and intent.get('plan') == failure.get('plan'),
            'actual consumed intent and partial-failure event must remain bound')
    quiescence, raw_quiescence_ref = _quiescence(plan['quiescence_ref'], plan['failure_ref'])
    for name in ('ROOT-ACTUAL-GAME-LAUNCH-C23.json', 'ROOT-ACTUAL-GAME-LAUNCH-C23-A05.json'):
        require(not (U / name).exists(), 'Game launch evidence already exists')
    require(not (U / 'p37-queue').exists() and not (O / 'A05-PREPARED01.json').exists(),
            'SDK queue or original prepare completion already exists')
    task_name = 'XARG2ManagedOwner-' + checked(failure['plan'], 8192)['task_nonce']
    raw_quiescence = checked(raw_quiescence_ref, 32768)
    require(raw_quiescence.get('task_name') == failure['scheduler_task_name'] == task_name,
            'exact original supervisor Task identity differs')
    require(quote.get('machine_id') == MACHINE and quote.get('unique_files') == 119
            and len(quote.get('files', [])) == 119 and quote.get('all_entry_rows') == 44,
            'exact original complete119 quote required')
    ntfs = _ntfs()
    actual_bytes, old_refs, identities = {}, {}, {}
    exact_rows = []
    for row in quote['files']:
        path = ntfs.no_reparse(row['path'])
        wanted = {key: row[key] for key in ('path', 'bytes', 'sha256')}
        require(path not in actual_bytes and ref(path) == wanted,
                'one of all 119 actual deployed pins differs: ' + str(path))
        actual_bytes[path] = raw(path)
        old_refs[path] = wanted
        identities[path] = ntfs.ntfs_identity(path)
        require(not identities[path]['directory'] and identities[path]['bytes'] == row['bytes'],
                'actual ordinary119 metadata differs')
        exact_rows.append(wanted)
    require(pin(enc(exact_rows)) == failure['actual_rows_JSON'],
            'all119 current exact rows differ from actual partial failure')
    state, original_state = (U / 'state').stat(), (T / 'state').stat()
    require((U / 'state').resolve(strict=True) == (T / 'state').resolve(strict=True)
            and state.st_ino == original_state.st_ino and state.st_dev == original_state.st_dev,
            'protected state junction identity differs')
    helper = (U / HELPER).resolve()
    require((old_refs[helper]['bytes'], old_refs[helper]['sha256']) == OLD_HELPER_PIN
            and failure.get('helper') == old_refs[helper]
            and type(helper_bytes) is bytes
            and (len(helper_bytes), pin(helper_bytes)['sha256']) == NEW_HELPER_PIN,
            'exact old helper and qualified new helper required')
    producer = ref(CANDIDATE)
    require((producer['bytes'], producer['sha256']) == CANDIDATE_PIN
            and helper_review.get('schema') == 'xar.C23-A05-actual-Source26-anchor-helper-RAM/v1'
            and helper_review.get('machine_id') == MACHINE
            and helper_review.get('old_helper') == old_refs[helper]
            and helper_review.get('actual_anchor') == failure.get('anchor')
            and helper_review.get('output') == dict(name=HELPER, **pin(helper_bytes))
            and helper_review.get('all_other_AST_unchanged') is True
            and helper_review.get('runtime_Git_Task_Game_writes_or_calls') == 0,
            'qualified two-validator helper review must bind actual partial graph')
    compile(helper_bytes, HELPER, 'exec')
    seeds = {helper: helper_bytes}
    external_old_refs, external_new_refs, migration = {}, {}, None
    if newfull_ref is not None:
        manual = checked(plan['newfull_review_ref'], 8192)
        require(manual.get('schema') == 'xar.storage.A05-manual1030-complete-immutable-review/v1'
                and manual.get('machine_id') == MACHINE and manual.get('owner') == 'Root'
                and manual.get('status') == 'FULL_COMPATIBILITY_AND_CAPACITY_REVIEWED_NOT_LIVE'
                and manual.get('full_storage_ref') == newfull_ref
                and manual.get('no_auto_renewal') is True,
                'actual manual current-A05 full review must be explicitly bound')
        extra, external_old_refs, external_new_refs, migration = _full_migration(
            actual_bytes, old_refs, newfull_ref)
        seeds.update(extra)
    outputs = dict(seeds)
    json_inputs = {path: json.loads(data) for path, data in actual_bytes.items() if path.suffix == '.json'}
    json_bases = {path: json.loads(seeds.get(path, data)) for path, data in actual_bytes.items()
                  if path.suffix == '.json' and path != U / 'STORAGE-ADMISSION.json'}
    propagation = {}
    for depth in range(1, 9):
        new_refs = {path: {'path': str(path), **pin(data)} for path, data in outputs.items()}
        replacements = {**new_refs, **external_new_refs}
        changes = {}
        for path, value in json_bases.items():
            trace = []
            changed = _replacement(value, {**old_refs, **external_old_refs}, replacements, trace)
            if trace:
                data = enc(changed)
                if data != actual_bytes[path]:
                    require(path.is_relative_to(U.resolve()), 'transitive change escaped current runtime')
                    changes[path] = data
                    propagation[str(path)] = trace
        expanded = {**seeds, **changes}
        if expanded == outputs:
            break
        outputs = expanded
    else:
        raise ValueError('A05 amendment reference graph did not settle in eight depths')
    expected = EXPECTED_LEAVES | ({'STORAGE-ADMISSION.json', 'ROOT-NATIVE30-NATIVE-PIN-C23-A05.json',
        'ROOT-PROMO-KEEPER-SOURCE-READY-C23-A05.json', 'ROOT-OBS-PROFILE-C23.json',
        'root_p37c23_same_game_loop_feeder100.py'} if migration else set())
    require({path.name for path in outputs} == expected and len(outputs) == len(expected),
            'actual transitive graph differs from the exact helper/full-review leaf contract')
    old_shas = {old_refs[path]['sha256'].encode() for path in outputs}
    for path, data in actual_bytes.items():
        candidate = outputs.get(path, data)
        if migration and path == U / 'STORAGE-ADMISSION.json':
            continue  # New full intentionally preserves predecessor provenance.
        require(not any(digest in candidate for digest in old_shas),
                'unhandled old SHA remains in current deployed graph: ' + str(path))
    new_policy = json.loads(outputs[U / POLICY])
    old_policy = json_inputs[U / POLICY]
    require(len(new_policy['entry_source_pins']) == 44
            and new_policy['canonical_entry_source_pins'] == old_policy['canonical_entry_source_pins']
            == quote['canonical_entry_source_pins']
            and len(new_policy['canonical_entry_source_pins']) == 6
            and all((Path(path) in outputs and pin(outputs[Path(path)])['sha256'] == digest)
                    or old_refs.get(Path(path), {}).get('sha256') == digest
                    for path, digest in new_policy['entry_source_pins']),
            'complete44 closure or unchanged canonical6 original max8 subset differs')
    old_freeze, new_freeze = json_inputs[U / FREEZE], json.loads(outputs[U / FREEZE])
    require({key: value for key, value in old_freeze.items() if key != 'canonical_preload_policy'}
            == {key: value for key, value in new_freeze.items() if key != 'canonical_preload_policy'},
            'SDK rows or other final-freeze fields changed outside policy reference')
    require(not ARCHIVE.exists() and not ARCHIVE.is_symlink(), 'one-shot archive root already exists')
    parent = ARCHIVE.parent
    while not parent.exists():
        parent = parent.parent
    archive_volume = ntfs.ntfs_identity(parent)['volume_serial']
    changed_rows, new_allocation = [], 0
    for path, data in sorted(outputs.items()):
        require(path.parent == U.resolve() and identities[path]['volume_serial'] == archive_volume,
                'all renamed old leaves must stay on their actual NTFS volume')
        archive = ARCHIVE / path.name
        require(not archive.exists() and not archive.is_symlink() and len(data) <= 524288,
                'bounded absent exact archive/new leaf required')
        cluster = identities[path]['cluster_bytes']
        allocation = ((len(data) + cluster - 1) // cluster) * cluster
        new_allocation += allocation
        changed_rows.append(dict(old=old_refs[path], old_identity=identities[path],
            archive_path=str(archive), archive_operation='rename_old_leaf_create_only_same_volume',
            old_body_copy_or_truncate_bytes=0,
            new={'path': str(path), **pin(data)}, new_operation='xb_after_verified_old_rename',
            new_allocation_upper=allocation))
    review_materials = 131072 if migration else 0
    peak = new_allocation + FS_RESERVE + SMALL_RECEIPTS_RESERVE + review_materials
    result = dict(schema='xar.C23-A05-cold-contract-amendment-quote/v1', machine_id=MACHINE,
        observed_at_utc=plan['observed_at_utc'], status='RAM_ONLY_NOT_AMENDED',
        producer=ref(__file__), candidate_producer=producer, candidate_review=helper_review,
        input_plan=plan, actual_partial_quote=plan['quote_ref'], actual_failure=plan['failure_ref'],
        consumed_intent=plan['intent_ref'], actual_quiescence=plan['quiescence_ref'],
        actual_raw_quiescence=raw_quiescence_ref,
        verified_all_original_pins=119, verified_current_rows_JSON=pin(enc(exact_rows)),
        changed_leaves=changed_rows, unchanged_original_leaves=119-len(changed_rows),
        full_review_migration=migration,
        exact_reference_propagation=propagation, source26_sdk_leaf_changes=0,
        old_state_SAVE_Driver_A04_H_changes=0, state_junction_same_FileID=True,
        canonical_six_unchanged=True, complete_closure_rows=44, original_max8_unchanged=True,
        Task_SPEC_bytes_unchanged=True, archive_root=str(ARCHIVE),
        new_data_allocation_upper=new_allocation, old_rename_body_copy_bytes=0,
        filesystem_metadata_reserve=FS_RESERVE, intent_receipt_metadata_reserve=SMALL_RECEIPTS_RESERVE,
        manual_newfull_review_materials_hard=review_materials,
        atomic_temporary_body_copy_bytes=0, create_strategy='rename old exact leaf then write new xb; no temp duplicate',
        peak_upper=peak, requested_hard_bytes=REQUESTED_HARD,
        admitted_within_requested_hard=peak <= REQUESTED_HARD,
        additional_bytes_needed=max(0, peak - REQUESTED_HARD),
        review_at_utc=migration['new_review'] if migration else '2026-10-20T06:30:00+00:00',
        execution_order='fresh no Game/SDK/Task; verify all119+FileIDs; create one intent; rename each old leaf once; xb each new leaf once; verify all119 projected pins, closure44, canonical6, saved_basis; new amendment receipt only',
        original_adopter_retry_forbidden=True, original_intent_reused=False,
        outputs_created=0, Task_Game_SDK_RPC_Git_calls=0)
    return outputs, result


if __name__ == '__main__':
    print(json.dumps(dict(status='RAM_API_ONLY_NO_EXECUTION_ENTRY', machine_id=MACHINE,
        original_adopter_retry_forbidden=True, outputs_created=0, Task_Game_SDK_RPC_Git_calls=0)))
