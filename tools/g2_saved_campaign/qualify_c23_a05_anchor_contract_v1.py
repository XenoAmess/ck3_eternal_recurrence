"""Independent actual-input/RAM-negative checks; never amend an installed file."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
import prepare_c23_a05_anchor_contract_v1 as candidate


def ref(path, limit=524288):
    path = Path(path).resolve(strict=True)
    if path.stat().st_size > limit:
        raise ValueError('bounded actual metadata required')
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def checked(item, limit=524288):
    if ref(item['path'], limit) != item:
        raise ValueError('actual metadata source pin differs')
    return json.loads(Path(item['path']).read_bytes())


def main():
    machine = subprocess.check_output([sys.executable, '-B', str(candidate.REPO / 'tools/ck3_live_run_id.py'),
                                       'machine'], text=True).strip()
    if machine != 'xenoamess-full-tower-eb9d2c1186':
        raise ValueError('actual machine differs')
    archive = candidate.T5.parent.parent / 'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/post-close/a05-prepare-contract01'
    helper_raw, review = candidate.build_source(helper_ref=ref(archive / candidate.HELPER))
    scope = {'__name__': '_strict_actual_Source26_candidate_RAM'}
    exec(compile(helper_raw, 'strict-actual-Source26-helper-RAM', 'exec'), scope)
    helper = SimpleNamespace(**scope)
    anchor_ref = ref(candidate.ANCHOR)
    anchor = checked(anchor_ref)
    freeze_ref = ref(candidate.T5 / 'ROOT-FINAL-SDK-FREEZE-P37C23-A05.json')
    freeze = checked(freeze_ref)
    admission = {'business_anchor': anchor_ref, 'business_source_commit': anchor['commit']}
    if 'Native30_bound' in anchor:
        raise ValueError('actual Source26 writer unexpectedly acquired a legacy field')
    helper.validate_business_anchor(anchor)
    helper.validate_frozen_business(admission, freeze, checked)
    cases = [{'case': 'actual-Source26-anchor-without-invented-Native30_bound', 'result': 'PASS'},
             {'case': 'actual-U5-freeze-1462-rows-all-twelve-output-members', 'result': 'PASS'}]

    def reject(name, call):
        try:
            call()
        except (ValueError, KeyError, TypeError) as error:
            cases.append({'case': name, 'result': 'REJECTED', 'diagnostic': str(error)})
        else:
            raise AssertionError('accepted negative ' + name)

    for name, key, value in (
        ('wrong-Source26-commit', 'commit', '0' * 40),
        ('eleven-changed-rows', 'output_pins', anchor['output_pins'][:-1]),
        ('wrong-complete-row-count', 'source_file_count', 1461),
        ('new-Native-operation-credit', 'Git_export_runtime_Task_Game_Native_RPC_calls_before_writer', 1),
        ('invented-Native30-bound-field', 'Native30_bound', False),
        ('loaded-provider-credit', 'actual_loaded_provider', True),
        ('invented-H-credit', 'actual_H', 'passed'),
        ('filesystem-authority-credit', 'source_epoch_actual_filesystem_authority', True),
    ):
        bad = copy.deepcopy(anchor)
        bad[key] = value
        reject(name, lambda bad=bad: helper.validate_business_anchor(bad))
    bad = copy.deepcopy(anchor)
    bad['writer']['sha256'] = '0' * 64
    reject('wrong-writer-provenance', lambda: helper.validate_business_anchor(bad))
    for name, key, value in (('freeze-count-drift', 'source_file_count', 1461),
                             ('freeze-byte-sum-drift', 'source_bytes', 59253401),
                             ('freeze-business-commit-drift', 'business_source_commit', anchor['parent'])):
        bad_freeze = copy.deepcopy(freeze)
        bad_freeze[key] = value
        reject(name, lambda bad_freeze=bad_freeze: helper.validate_frozen_business(admission, bad_freeze, checked))
    bad_admission = copy.deepcopy(admission)
    bad_admission['business_anchor']['sha256'] = '0' * 64
    reject('wrong-anchor-reference-pin', lambda: helper.validate_frozen_business(bad_admission, freeze, checked))

    # Execute the original full saved_basis pipeline against the installed
    # strict helper. Its closure sources and metadata retain actual pin checks;
    # nothing is written or reloaded.
    producer = candidate.OWN / 'prepare_c23_a03_cold_owner_metadata_v1.py'
    source = producer.read_text(encoding='utf-8').replace('C23-A03', 'C23-A05').replace(
        'source25_canonical_anchor', 'source26_canonical_anchor')
    source = source.replace("semantic=ref(runtime/'p37-responses/10479-1-result.json',262144)",
                            "semantic=ref(DEFAULT_OLD_RUNTIME/'p37-responses/10479-1-result.json',262144)")
    source = source.replace("runtime/'ROOT-P37C20-CLASSIFIER-PIN.json'",
                            "runtime/'ROOT-P37C23-CLASSIFIER-PIN.json'")
    basis_scope = {'__file__': str(producer), '__name__': '_actual_saved_basis_candidate_RAM'}
    exec(compile(source, 'original-saved-basis-with-explicit-RAM-helper', 'exec'), basis_scope)
    policy_ref = freeze['canonical_preload_policy']
    basis_scope.update(DEFAULT_OLD_RUNTIME=candidate.T5.with_name('runtime'),
        FINAL_PIN=(freeze_ref['bytes'], freeze_ref['sha256']),
        POLICY_PIN=(policy_ref['bytes'], policy_ref['sha256']))
    candidate.exact(candidate.T5 / candidate.HELPER,
                    (len(helper_raw), hashlib.sha256(helper_raw).hexdigest()))
    _, basis = basis_scope['saved_basis'](runtime_root=candidate.T5)
    cases.append({'case': 'original-full-saved_basis-actual-installed-strict-helper', 'result': 'PASS'})
    print(json.dumps({'schema': 'xar.C23-A05-actual-anchor-contract-RAM-qualification/v1',
        'machine_id': machine, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'candidate': ref(candidate.__file__), 'qualification_script': ref(__file__),
        'review': review, 'actual_freeze': freeze_ref, 'cases': cases,
        'saved_basis': basis, 'actual_installed_new_helper': True,
        'saved_basis_scope': 'actual installed complete closure and strict Source26 helper through original checker',
        'runtime_Task_Game_Git_mutations': 0, 'Driver_SAVE_media_hash_bytes': 0},
        ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()
