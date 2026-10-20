"""Finite RAM/source qualification and real two-base frozen-validator readback.

This runs no display owner, Task, Game, OBS, desktop or media-body operation.
The two real Python layers load the retained A04 capture from its actual path;
they validate the projected profile structure and the exact amended hotfix.
A05 actual-file import/Task/lifecycle remain later Root responsibilities.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_c23_a05_display_v1 as producer
import qualify_recording_validator_closure_v1 as existing


def expect_denial(call, label):
    try:
        call()
    except (ValueError, AssertionError):
        return {'case': label, 'status': 'DENIED'}
    raise AssertionError('negative case admitted: ' + label)


def qualify(plan):
    values, review, companions = producer.compose(plan)
    repeated = producer.compose(copy.deepcopy(plan))
    assert (values, review, companions) == repeated
    assert len(values) == 18 and len(companions) == 3
    assert not producer.T5.exists() and not producer.TASK5.exists()
    manifest = json.loads(values[producer.MANIFEST])
    assert len(manifest['files']) == 18
    for row in manifest['files']:
        name = row['relative_path']
        if name.startswith('@'):
            assert name == '@frozen-host/tools/ck3_capture_closed_receipt.py'
            assert producer.checked({k: row[k] for k in ('path', 'bytes', 'sha256')})
        else:
            assert producer.pin(producer.T5 / name, values[name]) == {
                k: row[k] for k in ('path', 'bytes', 'sha256')}
    assert {p: producer.pin(p, raw) for p, raw in companions.items()} == {
        Path(row['path']): row for row in review['companion_files']}
    _, owner_spec = producer.assignment(values[producer.OWNER], 'SPEC')
    assert owner_spec == review['new_owner_SPEC']
    assert owner_spec['display_nonce'] == plan['display_nonce']
    assert owner_spec['generation'] == 'C23-A05'
    assert owner_spec['previous_Game_tuple'] == list(producer.OLD_GAME)
    profile = json.loads(companions[producer.T5 / producer.PROFILE])
    assert profile['profile_name'] == profile['collection_name'] == 'ManagedWindowCapture-' + plan['display_nonce']
    assert profile['A05_display_nonce'] == plan['display_nonce']
    assert profile['storage']['admission_sha256'] == plan['full_storage_ref']['sha256']
    assert profile['storage']['admission_path'] == str(producer.T5 / 'STORAGE-ADMISSION.json')
    config = Path(profile['config_root'])
    assert set(companions) == {producer.T5 / producer.PROFILE,
        config / 'basic/profiles' / profile['profile_name'] / 'basic.ini',
        config / 'basic/scenes' / (profile['profile_name'] + '.json')}
    # The original static provider is a pinned input and a complete projected
    # source leaf. It never enters the future publisher-output namespace.
    assert producer.PROVIDER in values
    assert str(producer.T5 / producer.PROVIDER) not in review['fresh_output_namespace']
    negative = []
    bad = copy.deepcopy(plan); bad['display_nonce'] = json.loads(producer.finite(producer.TASK4))['nonce']
    negative.append(expect_denial(lambda: producer.compose(bad), 'reused A04 Task nonce'))
    bad = copy.deepcopy(plan); bad['machine_id'] = 'other-machine'
    negative.append(expect_denial(lambda: producer.compose(bad), 'foreign machine'))
    bad = copy.deepcopy(plan); bad['full_storage_ref']['sha256'] = '0' * 64
    negative.append(expect_denial(lambda: producer.compose(bad), 'changed full admission pin'))
    bad = copy.deepcopy(plan); bad['display_nonce'] = 'not-a-nonce'
    negative.append(expect_denial(lambda: producer.compose(bad), 'invalid nonce'))
    bad = copy.deepcopy(plan); bad['observed_at_utc'] = '2099-01-01T00:00:00+00:00'
    negative.append(expect_denial(lambda: producer.compose(bad), 'expired full admission'))
    negative.append(expect_denial(lambda: producer.build_task_spec(values, review,
        task_nonce=plan['display_nonce'], game_launch_ref={}, placement_ref={}),
        'display and Task nonce equality'))
    old = json.loads(producer.finite(producer.TASK4))
    env = dict(os.environ); env.update(review['Task_environment'])
    capture = producer.T4 / 'presentation-c23/ck3_obs_capture_png_retry_c23.py'
    # Reuse the exact real validator qualification child with only one extra
    # structural-profile check; this source never launches or controls OBS.
    seam = 'spec.loader.exec_module(capture)\n'
    assert existing.CHILD.count(seam) == 1
    child = existing.CHILD.replace(seam, seam + 'capture.validate_profile(p["new_profile"])\n', 1)
    payload = {'python': old['python'], 'runtime': str(producer.T4), 'host': str(producer.HOST),
        'layer': 0, 'hotfix': values['presentation-c23/hotfix_provider.py'].decode(),
        'hotfix_path': str(producer.T4 / 'presentation-c23/hotfix_provider.py'),
        'capture': str(capture), 'capture_sha': producer.closure.CAPTURE_SHA,
        'validator_sha': producer.closure.VALIDATOR_SHA,
        'stdlib_imports': producer.closure.STD_IMPORTS,
        'request': str(producer.T4 / 'ROOT-OBS-RECORDING-REQUESTED-C23.json'),
        'launch': str(producer.T4 / 'ROOT-ACTUAL-GAME-LAUNCH-C23.json'),
        'session_id': 'b72da700-8919-48ee-a855-c3c26730b923',
        'child_code': child, 'new_profile': profile}
    run = subprocess.run([old['python'], '-B', '-X', 'utf8', '-c', child],
        input=json.dumps(payload), text=True, encoding='utf-8', capture_output=True,
        cwd=producer.T4, env=env, timeout=60, check=False,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert run.returncode == 0, (run.returncode, run.stderr[-8000:])
    detail = json.loads(run.stdout)
    assert detail['validation']['status'] == 'CAPTURE_CLOSED_VERIFIED'
    assert detail['inherited_environment_layer']['validation'] == detail['validation']
    assert detail['media_body_bytes_read'] == 0
    return {'schema': 'xar.C23-A05-complete-display-qualification/v1',
        'machine_id': producer.MACHINE, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS_RAM_SOURCE_AND_EXISTING_CAPTURE_CLOSURE',
        'producer': producer.pin(producer.__file__, producer.finite(producer.__file__)),
        'qualifier': producer.pin(__file__, producer.finite(__file__)),
        'plan': plan, 'deterministic_repeat_identical': True,
        'complete_graph_leaves': 18, 'manifest_source_rows': 18, 'companion_count': 3,
        'display_review': review, 'negative_cases': negative,
        'real_base_layers': 2, 'closure_detail': detail,
        'actual_A05_file_import_or_Task_run': False,
        'actual_A04_capture_and_validator_mocked': False,
        'old_tree_writes': 0, 'runtime_writes': 0, 'media_body_bytes_read': 0,
        'Game_OBS_Task_desktop_calls': 0,
        'limits': 'RAM complete graph and profile structure; real frozen A04 capture closure in two base layers. No A05 deployment, import, Task, pixels or lifecycle credit.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-storage', type=Path, required=True)
    parser.add_argument('--display-nonce', required=True)
    parser.add_argument('--observed-at-utc', required=True)
    parser.add_argument('--proof', type=Path)
    a = parser.parse_args()
    raw = producer.finite(a.full_storage, 32768)
    plan = {'schema': 'xar.C23-A05-display-prepare-input/v1',
        'machine_id': producer.MACHINE, 'full_storage_ref': producer.pin(a.full_storage, raw),
        'display_nonce': a.display_nonce, 'observed_at_utc': a.observed_at_utc}
    result = qualify(plan)
    review = result.pop('display_review')
    detail = result.pop('closure_detail')
    review_raw = producer.encode(review)
    result.update(
        complete_display_review_RAM_JSON={'bytes': len(review_raw), 'sha256': producer.sha(review_raw),
                                          'reproduce': 'producer.compose(exact plan)[1]'},
        projected_source_outputs=review['files'], companion_outputs=review['companion_files'],
        source_graph_bytes=review['source_graph_bytes'], companion_bytes=review['companion_bytes'],
        actual_source_manifest=next(ref for ref in review['inputs']
            if ref['path'] == str(producer.T4 / producer.MANIFEST)),
        closure_validator=review['external_validator'],
        recording_parent_prerequisite=review['prerequisite_directories'],
        profile_name=review['profile_name'], private_password_printed=False,
        static_provider_is_input_not_attempt_output=True,
        Task_SPEC_status=review['Task_SPEC_status'],
        real_two_layer_closure={
            'python': detail['python'], 'module_origins': detail['module_origins'],
            'validation': detail['validation'],
            'inherited_layer_validation': detail['inherited_environment_layer']['validation'],
            'inherited_origins_identical': detail['inherited_environment_layer']['module_origins'] == detail['module_origins'],
            'H_tools_present_in_both_post_hotfix_environments': all(str(producer.HOST / 'tools')
                in row['post_prefix_pythonpath'].split(os.pathsep)
                for row in (detail, detail['inherited_environment_layer'])),
            'media_body_bytes_read': 0})
    if a.proof:
        proof_raw = producer.encode(result)
        assert len(proof_raw) <= 20480, 'finite 32KiB artifact allocation includes parent directories'
        a.proof.parent.mkdir(parents=True, exist_ok=False)
        with a.proof.open('xb') as stream:
            stream.write(proof_raw)
        print(json.dumps({'status': result['status'], 'proof': producer.pin(a.proof, producer.finite(a.proof))}))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
