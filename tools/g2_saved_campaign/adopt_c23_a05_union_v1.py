"""Quote or create one separately admitted A05 runtime; never register/run a Task."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_c23_a05_union_v1 as union


def require(ok, reason):
    if not ok:
        raise ValueError('A05 adoption denied: ' + reason)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def ref(path, limit=131072):
    path = Path(path).resolve(strict=True)
    require(path.stat().st_size <= limit, 'bounded exact file required')
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def checked(item, limit=131072):
    require(ref(item['path'], limit) == item, 'actual reference differs')
    return json.loads(Path(item['path']).read_bytes())


def load_pinned(item, expected_name):
    require(Path(item['path']).resolve() == (OWN / expected_name).resolve(), 'explicit local producer required')
    require(ref(item['path']) == item, 'producer source differs')
    spec = importlib.util.spec_from_file_location('_a05_adopt_' + expected_name[:-3], item['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def compose(plan_ref):
    plan = checked(plan_ref)
    require(ref(union.__file__) == plan['union_producer'], 'reviewed union source differs')
    display = load_pinned(plan['display_producer'], 'prepare_c23_a05_display_v1.py')
    values, review, companion = display.compose(plan['display'])
    outputs, quote = union.compose(plan, display_values=values, display_review=review,
                                   companion_values=companion)
    require(all(len(data) <= 524288 for data in outputs.values()), 'single-file write cap')
    quote['adopter'] = ref(__file__)
    quote['input_plan'] = plan_ref
    return plan, outputs, quote


def once(path, data):
    path = Path(path)
    require(len(data) <= 524288, 'single-file cap')
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    require(path.read_bytes() == data, 'actual create-only readback differs')
    return ref(path, 524288)


def compose_amend(plan_ref):
    plan = checked(plan_ref)
    module = load_pinned(plan['amendment_producer'], 'prepare_c23_a05_cold_amendment_v1.py')
    candidate = load_pinned(plan['candidate_producer'], 'prepare_c23_a05_anchor_contract_v1.py')
    original = ref(plan['original_adopter_source']['path'])
    require(original == plan['original_adopter_source'] and original['sha256'] ==
            checked(plan['quote_ref'], 262144)['adopter']['sha256'], 'original failed adopter source must survive')
    helper, review = candidate.build_source(helper_ref=ref(module.U / module.HELPER))
    outputs, quote = module.compose(plan, helper_bytes=helper, helper_review=review,
                                    newfull_ref=plan['newfull_ref'])
    quote['adopter'] = ref(__file__)
    quote['input_plan_ref'] = plan_ref
    # The persisted quote is JSON: arrays have one representation even when
    # an in-memory producer uses tuples. Preserve every serialized byte.
    quote = json.loads(encoded(quote))
    return module, plan, outputs, quote


def amend(plan_ref, quote_ref, card_ref):
    module, plan, outputs, quote = compose_amend(plan_ref)
    require(quote == checked(quote_ref, 262144), 'complete amendment quote changed')
    card = checked(card_ref)
    require(card.get('schema') == 'xar.C23-A05-cold-contract-amendment-admission/v1'
            and card.get('machine_id') == union.MACHINE and card.get('owner') == 'Root'
            and card.get('status') == 'ADMITTED' and card.get('root_direct_execution_release') is True
            and card.get('plan') == plan_ref and card.get('quote') == quote_ref
            and card.get('newfull_ref') == plan['newfull_ref']
            and card.get('canonical_capacity_review_passed') is True
            and type(card.get('hard_bytes')) is int and quote['peak_upper'] <= card['hard_bytes'],
            'exact separately admitted cold amendment required')
    floor = card['capacity']['D_conservative_floor_bytes']
    deadline = datetime.fromisoformat(quote['review_at_utc'].replace('Z', '+00:00'))
    require(shutil.disk_usage(module.O).free >= floor and datetime.now(timezone.utc) < deadline,
            'fresh admitted capacity or review unavailable')
    intent = module.O / 'A05-COLD-AMENDMENT-INTENT01.json'
    receipt = module.O / 'A05-COLD-AMENDMENT-COMPLETE01.json'
    require(not intent.exists() and not receipt.exists(), 'cold amendment already consumed')
    require(module.ARCHIVE.resolve().is_relative_to(module.O.resolve())
            and not module.ARCHIVE.exists(), 'exact project archive root must be absent')
    ntfs = module._ntfs()
    once(intent, encoded({'machine_id': union.MACHINE, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'ONE_SHOT_COLD_AMENDMENT_INTENT', 'plan': plan_ref, 'quote': quote_ref, 'card': card_ref}))
    archived = []
    try:
        module.ARCHIVE.mkdir(parents=True, exist_ok=False)
        for row in quote['changed_leaves']:
            path, archive = Path(row['old']['path']), Path(row['archive_path'])
            require(path.parent == module.U.resolve() and archive.parent == module.ARCHIVE.resolve()
                    and not archive.exists(), 'exact source and archive paths required')
            require(ref(path, 524288) == row['old'] and ntfs.ntfs_identity(path) == row['old_identity'],
                    'old leaf or identity changed')
            require(shutil.disk_usage(module.O).free >= floor and datetime.now(timezone.utc) < deadline,
                    'admission lost before next cold leaf')
            before = path.stat()
            path.rename(archive)
            after = archive.stat()
            require((before.st_ino, before.st_dev) == (after.st_ino, after.st_dev)
                    and ref(archive, 524288) == {'path': str(archive), 'bytes': row['old']['bytes'],
                                              'sha256': row['old']['sha256']}, 'archived original identity differs')
            require(once(path, outputs[path]) == row['new'], 'new cold leaf readback differs')
            archived.append({'old': row['old'], 'archive': ref(archive, 524288), 'new': row['new'],
                             'original_FileID_retained': str(after.st_ino)})
        original_quote = checked(plan['quote_ref'], 262144)
        for row in original_quote['files']:
            path = Path(row['path'])
            expected = ({'path': str(path), 'bytes': len(outputs[path]),
                         'sha256': hashlib.sha256(outputs[path]).hexdigest()} if path in outputs
                        else {key: row[key] for key in ('path', 'bytes', 'sha256')})
            require(ref(path, 524288) == expected, 'projected complete119 pin readback differs')
        final = checked(ref(module.U / module.FREEZE, 524288), 524288)
        policy = checked(final['canonical_preload_policy'])
        for path, digest in policy['entry_source_pins']:
            require(ref(path, 524288)['sha256'] == digest, 'actual closure44 differs')
        sys.path[:0] = [final['source_root'], str(module.U), str(module.U / 'creator-tools'), str(OWN.parent)]
        chain = union._module(module.U / 'creator-tools/g2_saved_campaign/canonical_native_provider_chain_v1.py',
                              '_a05_amended_actual_private_chain')
        require(len(chain._verified_entry_sources(policy['canonical_entry_source_pins'])) == 6,
                'actual canonical6 original max8 verifier refused')
        scope = {'__file__': str(OWN / 'prepare_c23_a03_cold_owner_metadata_v1.py'),
                 '__name__': '_a05_amended_actual_saved_basis'}
        source = union.raw(OWN / 'prepare_c23_a03_cold_owner_metadata_v1.py').decode()
        source = source.replace('C23-A03', 'C23-A05').replace('source25_canonical_anchor', 'source26_canonical_anchor')
        source = source.replace("semantic=ref(runtime/'p37-responses/10479-1-result.json',262144)",
                                "semantic=ref(DEFAULT_OLD_RUNTIME/'p37-responses/10479-1-result.json',262144)")
        source = source.replace("runtime/'ROOT-P37C20-CLASSIFIER-PIN.json'", "runtime/'ROOT-P37C23-CLASSIFIER-PIN.json'")
        exec(compile(source, 'A05-amended-original-saved-basis', 'exec'), scope)
        finalref = ref(module.U / module.FREEZE, 524288)
        scope.update(DEFAULT_RUNTIME=module.U, DEFAULT_OLD_RUNTIME=module.T,
                     FINAL_PIN=(finalref['bytes'], finalref['sha256']),
                     POLICY_PIN=(final['canonical_preload_policy']['bytes'], final['canonical_preload_policy']['sha256']))
        _, basis = scope['saved_basis'](runtime_root=module.U)
        live = ref(module.U / 'STORAGE-ADMISSION.json')
        require({key: live[key] for key in ('bytes', 'sha256')} ==
                {key: plan['newfull_ref'][key] for key in ('bytes', 'sha256')}, 'actual new full differs')
        return once(receipt, encoded({'schema': 'xar.C23-A05-cold-contract-amendment-complete/v1',
            'machine_id': union.MACHINE, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'ACTUAL_COLD_AMENDMENT_VERIFIED_NOT_RUN', 'intent': ref(intent),
            'plan': plan_ref, 'quote': quote_ref, 'card': card_ref, 'archived_originals': archived,
            'actual_projected_pins_verified': 119, 'complete44_verified': True,
            'canonical6_original_max8_verified': True, 'actual_saved_basis': basis,
            'newfull_ref': plan['newfull_ref'], 'actual_live_full': live, 'review_at_utc': quote['review_at_utc'],
            'Task_Game_SDK_RPC_calls': 0, 'original_adopter_retry': False}))
    except BaseException as error:
        once(module.O / 'A05-COLD-AMENDMENT-FAILED01.json', encoded({'machine_id': union.MACHINE,
            'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'FAILED_OR_UNKNOWN_DO_NOT_REPLAY',
            'plan': plan_ref, 'quote': quote_ref, 'intent': ref(intent), 'completed_leaf_pairs': archived,
            'error': {'type': type(error).__name__, 'text': str(error)[:2048]}}))
        raise


def adopt(plan_ref, quote_ref, card_ref):
    plan, outputs, quote = compose(plan_ref)
    wanted = checked(quote_ref, 262144)
    card = checked(card_ref)
    require(quote == wanted, 'complete RAM quote changed')
    require(card.get('schema') == 'xar.C23-A05-runtime-prepare-admission/v1'
            and card.get('machine_id') == union.MACHINE and card.get('owner') == 'Root'
            and card.get('status') == 'ADMITTED' and card.get('root_direct_execution_release') is True
            and card.get('plan') == plan_ref and card.get('quote') == quote_ref
            and card.get('full_storage_ref') == plan['full_storage_ref']
            and card.get('canonical_capacity_review_passed') is True, 'separate exact runtime admission required')
    require(type(card.get('hard_bytes')) is int and quote['prepare_peak_upper'] <= card['hard_bytes'],
            'runtime peak exceeds exact admission')
    deadline = datetime.fromisoformat(quote['review_at_utc'].replace('Z', '+00:00'))
    require(datetime.now(timezone.utc) < deadline, 'storage review expired')
    machine = subprocess.check_output([sys.executable, '-B', '-X', 'utf8',
        str(OWN.parent / 'ck3_live_run_id.py'), 'machine'], text=True).strip()
    require(machine == union.MACHINE, 'actual machine differs')
    floor = card['capacity']['D_conservative_floor_bytes']
    require(type(floor) is int and floor > 0 and shutil.disk_usage(union.O).free >= floor,
            'fresh coordinated volume free floor unavailable')
    full = union.checked(plan['full_storage_ref'], 32768)
    roots = [Path(p).resolve() for p in full['approved_output_roots']]
    require(all(any(path == root or path.is_relative_to(root) for root in roots)
                for path in outputs), 'output not covered by full approved roots')
    runtime = union.T5.resolve()
    taskroot = union.O / 'tasks/spec-supervisor-a05'
    require(not runtime.exists() and not taskroot.exists(), 'one-shot root already consumed')
    intent = union.O / 'A05-PREPARE-INTENT01.json'
    receipt = union.O / 'A05-PREPARED01.json'
    require(not intent.exists() and not receipt.exists(), 'one-shot intent already consumed')
    # Reuse the exact source, metadata and profile union. Nothing is silently skipped.
    for row in quote['files']:
        path = Path(row['path'])
        require(not path.exists() and not path.is_symlink(), 'create-only destination exists')
        if row['mode'] == 'hardlink':
            require(ref(row['source']['path'], 1048576) == row['source'], 'old immutable source differs')
            require(Path(row['source']['path']).stat().st_dev == union.O.stat().st_dev,
                    'immutable source on different volume')
        else:
            require(row['mode'] == 'create-only', 'unknown output mode')
    once(intent, encoded({'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'ONE_SHOT_A05_PREPARE_INTENT', 'plan': plan_ref, 'quote': quote_ref, 'card': card_ref}))
    runtime.mkdir(exist_ok=False)
    (runtime / 'recordings').mkdir(exist_ok=False)
    state = runtime / 'state'
    result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(state), str(union.T0 / 'state')],
                            capture_output=True)
    require(result.returncode == 0, 'exact state junction creation failed: ' + result.stderr[:512].decode(errors='replace'))
    require(state.resolve(strict=True) == (union.T0 / 'state').resolve(strict=True)
            and state.stat().st_ino == (union.T0 / 'state').stat().st_ino
            and state.stat().st_dev == (union.T0 / 'state').stat().st_dev, 'actual same-identity state alias differs')
    actual = []
    for row in quote['files']:
        require(datetime.now(timezone.utc) < deadline and shutil.disk_usage(union.O).free >= floor,
                'admission lost before next exact write')
        path = Path(row['path'])
        path.parent.mkdir(parents=True, exist_ok=True)
        require(not path.exists() and not path.is_symlink(), 'destination changed after intent')
        if row['mode'] == 'hardlink':
            source = Path(row['source']['path'])
            require(ref(source, 1048576) == row['source'], 'source changed before immutable link')
            os.link(source, path)
            require(path.stat().st_ino == source.stat().st_ino and path.stat().st_dev == source.stat().st_dev,
                    'actual hardlink identity differs')
        else:
            once(path, outputs[path])
        require(ref(path, 524288) == {key: row[key] for key in ('path', 'bytes', 'sha256')},
                'complete output pin readback differs')
        actual.append({key: row[key] for key in ('path', 'bytes', 'sha256')})
    freeze = union.checked(union.ref(runtime / 'ROOT-FINAL-SDK-FREEZE-P37C23-A05.json'), 524288)
    policy = union.checked(freeze['canonical_preload_policy'], 32768)
    for path, digest in policy['entry_source_pins']:
        require(ref(path, 1048576)['sha256'] == digest, 'actual complete44 closure differs')
    require(len(policy['entry_source_pins']) == 44 and len(policy['canonical_entry_source_pins']) == 6,
            'complete44/canonical6 shape differs')
    sys.path[:0] = [str(Path(freeze['source_root']).resolve(strict=True)),
                    str(runtime), str(runtime / 'creator-tools'), str(OWN.parent)]
    private_chain = runtime / 'creator-tools/g2_saved_campaign/canonical_native_provider_chain_v1.py'
    chain = union._module(private_chain, '_a05_actual_private_chain')
    require(len(chain._verified_entry_sources(policy['canonical_entry_source_pins'])) == 6,
            'original max8 canonical6 verifier refused')
    owner = load_pinned(ref(OWN / 'interactive_task_owner_v1.py'), 'interactive_task_owner_v1.py')
    specpath = taskroot / 'SPEC.json'
    owner.checked_spec(specpath, ref(specpath)['sha256'])
    # Validate saved basis with the actual deployed helper, while no Game or SDK exists.
    source = union.raw(OWN / 'prepare_c23_a03_cold_owner_metadata_v1.py').decode()
    source = source.replace('C23-A03', 'C23-A05').replace('source25_canonical_anchor', 'source26_canonical_anchor')
    source = source.replace("semantic=ref(runtime/'p37-responses/10479-1-result.json',262144)",
                            "semantic=ref(DEFAULT_OLD_RUNTIME/'p37-responses/10479-1-result.json',262144)")
    source = source.replace("runtime/'ROOT-P37C20-CLASSIFIER-PIN.json'", "runtime/'ROOT-P37C23-CLASSIFIER-PIN.json'")
    scope = {'__file__': str(OWN / 'prepare_c23_a03_cold_owner_metadata_v1.py'), '__name__': '_a05_actual_saved_basis'}
    exec(compile(source, 'A05-actual-saved-basis', 'exec'), scope)
    finalref = union.ref(runtime / 'ROOT-FINAL-SDK-FREEZE-P37C23-A05.json')
    scope.update(DEFAULT_RUNTIME=runtime, DEFAULT_OLD_RUNTIME=union.T0,
                 FINAL_PIN=(finalref['bytes'], finalref['sha256']),
                 POLICY_PIN=(freeze['canonical_preload_policy']['bytes'], freeze['canonical_preload_policy']['sha256']))
    _, basis_report = scope['saved_basis'](runtime_root=runtime)
    return once(receipt, encoded({'schema': 'xar.C23-A05-finite-prepare-complete/v1',
        'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'A05_PREPARED_NOT_REGISTERED_NOT_RUN', 'plan': plan_ref, 'quote': quote_ref,
        'card': card_ref, 'intent': ref(intent), 'outputs': actual, 'saved_basis': basis_report,
        'complete44_actual_readback': True, 'canonical6_original_max8_verifier_passed': True,
        'supervisor_SPEC_original_validator_passed': True, 'Task_Game_SDK_RPC_calls': 0,
        'state_same_FileID': True, 'large_input_bytes_copied_or_hashed': 0,
        'full_storage_ref': plan['full_storage_ref'], 'live_storage_ref': plan['live_storage_ref']}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('command', choices=('quote', 'adopt', 'amend-quote', 'amend'))
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--plan-sha', required=True)
    parser.add_argument('--quote', type=Path)
    parser.add_argument('--quote-sha')
    parser.add_argument('--card', type=Path)
    parser.add_argument('--card-sha')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute-root-adoption', action='store_true')
    args = parser.parse_args()
    def pinned(path, digest, limit=131072):
        value = ref(path, limit)
        require(value['sha256'] == digest, 'CLI exact SHA differs')
        return value
    planref = pinned(args.plan, args.plan_sha)
    if args.command in ('quote', 'amend-quote'):
        value = compose(planref)[2] if args.command == 'quote' else compose_amend(planref)[3]
        if args.output:
            result = once(args.output, encoded(value))
        else:
            result = value
    else:
        require(args.execute_root_adoption and all((args.quote, args.quote_sha, args.card, args.card_sha)),
                'adoption is default OFF; exact quote and separate card required')
        action = amend if args.command == 'amend' else adopt
        result = action(planref, pinned(args.quote, args.quote_sha, 262144), pinned(args.card, args.card_sha))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
