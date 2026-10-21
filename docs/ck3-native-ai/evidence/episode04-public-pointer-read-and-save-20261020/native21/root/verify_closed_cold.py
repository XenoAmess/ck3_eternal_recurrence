"""Read closed native evidence and emit unaccepted candidates. Never runs native code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import TypedDict

T = Path('C:/w/e04parentread03')
S = Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-read-source-p03')
OUT = Path('C:/ck3-e04-resume-20261020-a01/r08-public-pointer-read-v2-source-2300-a01/Root/cold-adjudication-a01')
sys.path[:0] = [str(T / 'control-metadata-a01'), str(S)]

from readwatch_control import Pin, PinJSON, MACHINE, REPO, pin, exact, parse_pin, load, object_row, sequence, strings, integer, text, true, parse_plan, verify_source, measure, write, now
from run_parent_pointer_read_cold import REFUSALS, FAULTS, PARTIAL_REASONS, raw_rows, read_meta, observer_argv, expected_from_meta, assert_zero_arm_refusal, verify_audit, verify_build
from cold_runner_models import Options, audit_rows, target_result, binary_files
from parent_pointer_read_contract import MODE, normalize_rows
from pointer_read_wire import wire_json, decimal64

SUITE_SHA = '0cc1044aa13ab3f946d0c0fd1ca98a08477353a1aa313cdd6b22e7b7f15eb717'
SOURCE_SHA = '23758688b3ecf62b3168436e26489fbe6d6a7f9837c37aed7a1b48f9585c72cd'
PRODUCER_SHA = 'd7a012a13cfe4c7b4822420353217cd6413df5bd228cd5192c728b06c3a763f1'
GATE_SHA = 'be8cdcad90fc5c1dccba0bb4fc161a35615affd1fa53bfe85b02da7ebc8121da'
OBSERVER_SHA = 'd0beda84eb549f6b0b773e99f773f36224d64be366dbd9a66d8cd3188a8500c9'
REQUIRED = ('foreign257_then_target', 'created_thread', 'foreign4096_limit', 'timeout', 'restore-fault', 'readback-fault', 'continue-fault', 'default-off', 'missing-ack', 'bad-schema', 'occupied-dr', 'occupied-tf', 'context-drift', 'fullid-drift', 'magic-drift', 'session-drift', 'null-context', 'other-player-read', 'other-player-write', 'null-admission', 'cancel_late')

class CaseProof(TypedDict):
    case: str
    case_pin: PinJSON
    raw_pin: PinJSON | None
    audit_pin: PinJSON
    wait_pins: list[PinJSON]
    target_exit: int
    observer_exit: int

def known(path: Path, sha: str) -> Pin:
    ref = pin(path)
    if ref.sha256 != sha:
        raise ValueError('Exact closed evidence digest mismatch: ' + str(path))
    return ref

def original_wait(directory: Path, role: str, expected_code: int, expected_argv: tuple[str, ...]) -> Pin:
    spawn = object_row(load(directory / (role + '.POPEN.actual.json')), 'original spawn')
    wait_path = directory / (role + '.ORIGINAL-WAIT.actual.json')
    wait = object_row(load(wait_path), 'original wait')
    true(wait, 'original_Popen'); true(wait, 'original_wait')
    if spawn.get('machine_id') != MACHINE or wait.get('machine_id') != MACHINE:
        raise ValueError('Original process machine mismatch')
    if integer(wait.get('exit_code'), 'exit code') != expected_code:
        raise ValueError('Unexpected actual original native exit')
    pid = integer(spawn.get('pid'), 'spawn PID')
    if not 0 < pid <= 0xffffffff or integer(wait.get('pid'), 'wait PID') != pid or decimal64(spawn.get('created'), 'spawn birth') != decimal64(wait.get('created'), 'wait birth'):
        raise ValueError('Original PID/birth identity mismatch')
    if strings(spawn.get('argv'), 'spawn argv') != expected_argv:
        raise ValueError('Original native argv is not this exact synthetic case')
    return pin(wait_path)

def verify_case(case_ref: Pin, expected_name: str) -> CaseProof:
    exact(case_ref)
    case = object_row(load(case_ref.path), 'actual case')
    if case.get('schema') != 'xar.maintenance.parent_pointer_read.cold.case.v1' or case.get('status') != 'PASS' or case.get('machine_id') != MACHINE or case.get('case') != expected_name:
        raise ValueError('Actual case schema/status/machine/name mismatch')
    directory = T / 'cold-a01' / expected_name
    if case_ref.path.parent != directory or 'native_consumer' not in case or 'raw' not in case:
        raise ValueError('Case path or required nullable fields mismatch')
    meta_path = directory / 'target.meta.txt'
    meta = read_meta(meta_path)
    raw_path = directory / 'observer.raw.ndjson'
    rows = raw_rows(raw_path, True)
    raw_ref: Pin | None = None
    if case['raw'] is not None:
        raw_ref = parse_pin(case['raw']); exact(raw_ref)
        if raw_ref.path != raw_path:
            raise ValueError('Case raw pin names another file')
    elif raw_path.exists():
        raise ValueError('Actual raw file cannot be replaced by null')
    observer_args, timeout = observer_argv(T / 'build-a01/maintenance_parent_pointer_read_observer.exe', directory / 'BAD-SCHEMA.meta.txt' if expected_name == 'bad-schema' else meta_path, raw_path, directory / 'READY.actual.json', MACHINE, expected_name)
    observer_code = integer(case.get('observer_original_exit'), 'observer exit')
    target_code = integer(case.get('target_original_exit'), 'target exit')
    if target_code != 0:
        raise ValueError('Actual target did not finish successfully')
    if expected_name in REFUSALS:
        assert_zero_arm_refusal(rows, observer_code, (directory / 'READY.actual.json').exists())
        if case['native_consumer'] is not None:
            raise ValueError('Refusal consumer must remain null')
    else:
        if observer_code != (1 if expected_name in PARTIAL_REASONS else 0):
            raise ValueError('Actual observer exit does not match case semantics')
        normalized = normalize_rows(rows, expected_from_meta(meta, MACHINE, timeout))
        if wire_json(normalized) != case['native_consumer']:
            raise ValueError('Persisted native consumer differs from exact raw normalization')
        if expected_name in PARTIAL_REASONS and normalized['reason'] != PARTIAL_REASONS[expected_name]:
            raise ValueError('Partial outcome has another reason')
        if not normalized['cleanup_complete']:
            raise ValueError('Native raw does not prove full cleanup')
        if expected_name == 'cancel_late' and (not any(row.get('owned_late_event') is True for row in rows) or normalized['target_post_read_retained']):
            raise ValueError('Actual cancel/late owned event was not witnessed')
    mode = 'foreign257_then_target' if expected_name in FAULTS else 'timeout' if expected_name in {'default-off', 'missing-ack', 'bad-schema'} else expected_name
    target_args = (str(T / 'build-a01/maintenance_parent_pointer_read_cold_target.exe'), '--mode', mode, '--prefix', str(directory / 'target'))
    waits = [original_wait(directory, 'target', target_code, target_args), original_wait(directory, 'observer', observer_code, tuple(observer_args))]
    target_spawn = object_row(load(directory / 'target.POPEN.actual.json'), 'target spawn')
    if integer(target_spawn.get('pid'), 'target PID') != int(meta['pid']) or decimal64(target_spawn.get('created'), 'target birth') != int(meta['created']):
        raise ValueError('Actual target meta is not the retained original target')
    initial_raw = load(directory / 'target.initial-debug.json')
    after_raw = load(directory / 'target.after-debug.json')
    before, after = audit_rows(initial_raw), audit_rows(after_raw)
    derived = object_row(wire_json(verify_audit(rows, before, after, expected_name in REFUSALS)), 'derived full-six audit')
    audit_ref = parse_pin(case.get('independent_audit')); exact(audit_ref)
    audit = object_row(load(audit_ref.path), 'stored independent audit')
    if audit_ref.path != directory / 'INDEPENDENT-DR-AUDIT.actual.json' or audit.get('before') != initial_raw or audit.get('after') != after_raw:
        raise ValueError('Independent audit does not retain these original peer vectors')
    for key, value in derived.items():
        if audit.get(key) != value:
            raise ValueError('Full-six independent audit differs at ' + key)
    if expected_name == 'occupied-tf':
        true(audit, 'independent_preexisting_TF_preserved_before_target_release')
        first = next((row for row in before if row['tid'] == int(meta['tid'])), None)
        last = next((row for row in after if first is not None and row['tid'] == first['tid'] and row['created'] == first['created']), None)
        if first is None or last is None or not first['eflags'] & 0x100 or not last['eflags'] & 0x100:
            raise ValueError('Pre-existing TF is not actually preserved')
    result = target_result(load(directory / 'target.result.json'))
    if result.raw != case.get('actual_target_result') or result.return_failures or result.audit_failures:
        raise ValueError('Actual function/result or audit failed')
    counts = (257, 1) if expected_name == 'foreign257_then_target' or expected_name in FAULTS else (0, 0) if expected_name == 'timeout' or expected_name in REFUSALS else (0, 1)
    if (result.foreign_body_calls, result.target_body_calls) != counts or result.actual_body_calls != sum(counts):
        raise ValueError('Actual original calls were not executed exactly once')
    other = 4096 if expected_name in {'foreign4096_limit', 'cancel_late'} else 257 if expected_name in {'other-player-read', 'other-player-write'} else 0
    if result.other_access_calls != other:
        raise ValueError('Actual other accesses were not executed once per call')
    captures = [row for row in rows if row.get('kind') == 'post_parent_pointer_read']
    if captures and (integer(captures[0].get('eflags'), 'capture flags') & 0x8d5) != result.post_arithmetic_flags:
        raise ValueError('Original arithmetic flags changed across data trap')
    if expected_name in {'null-context', 'null-admission'} and (result.loaded_context != 0 or len(captures) != 1):
        raise ValueError('Legitimate loaded null was lost')
    return CaseProof(case=expected_name, case_pin=case_ref.json(), raw_pin=raw_ref.json() if raw_ref else None, audit_pin=audit_ref.json(), wait_pins=[ref.json() for ref in waits], target_exit=target_code, observer_exit=observer_code)

def adjudicate(expected_suite_sha: str) -> tuple[dict[str, object], dict[str, object]]:
    suite_ref = known(T / 'cold-a01/SELECTED-COLD.actual.json', expected_suite_sha)
    if expected_suite_sha != SUITE_SHA:
        raise ValueError('This adjudication only covers the exact closed 21-case suite')
    suite = object_row(load(suite_ref.path), 'suite')
    if suite.get('schema') != 'xar.maintenance.parent_pointer_read.cold.suite.v1' or suite.get('mode') != MODE or suite.get('machine_id') != MACHINE or suite.get('status') != 'SELECTED_CASES_COMPLETED_NOT_QUALIFICATION':
        raise ValueError('Wrong closed synthetic suite')
    if strings(suite.get('selected_cases'), 'selected cases') != REQUIRED:
        raise ValueError('Exact 21-case order with cancel last required')
    source_ref = known(S / 'SOURCE-MANIFEST.actual.json', SOURCE_SHA)
    producer_ref = known(T / 'control-metadata-a01/READWATCH-NATIVE-RECIPE.prepared-a01.json', PRODUCER_SHA)
    sources = verify_source(parse_plan(load(producer_ref.path)), producer_ref)
    gate_ref = known(T / 'EXECUTION-GATE.actual.json', GATE_SHA)
    options = Options(repo=REPO, build_dir=T / 'build-a01', machine_build_record=T / 'MACHINE-BUILD.actual.json', output_root=T / 'cold-a01')
    rebuilt_gate = verify_build(options, MACHINE)
    saved_gate = object_row(load(gate_ref.path), 'saved SYSTEM gate')
    projected_gate = object_row(rebuilt_gate, 'reverified typed SYSTEM gate')
    for key in ('machine_id', 'producer', 'original_build', 'SYSTEM_receipt', 'SYSTEM_manifest'):
        if saved_gate.get(key) != projected_gate.get(key):
            raise ValueError('Actual source/build/SYSTEM gate pin mismatch: ' + key)
    # The saved receipt retains CMake target provenance; the shared typed model
    # projects path/size/SHA. verify_build already requires the full unprojected
    # receipt.files == manifest.files, so this comparison keeps that guarantee.
    if binary_files(saved_gate.get('files')) != rebuilt_gate['files']:
        raise ValueError('Actual two EXE file projections differ')
    observer = known(T / 'build-a01/maintenance_parent_pointer_read_observer.exe', OBSERVER_SHA)
    case_pins = tuple(parse_pin(value) for value in sequence(suite.get('cases'), 'case pins'))
    if len(case_pins) != 21:
        raise ValueError('Exact 21 case pins required')
    proofs = [verify_case(ref, name) for ref, name in zip(case_pins, REQUIRED)]
    source_pins = [ref.json() for ref in sources]
    acceptance: dict[str, object] = {'schema': 'xar.maintenance.parent_pointer_read.Root-acceptance.candidate.v1', 'machine_id': MACHINE, 'observed_at_utc': now(), 'mode': MODE, 'accepted': False, 'status': 'ROOT_REVIEW_PENDING', 'observer_sha256': observer.sha256, 'source_pins': source_pins, 'cold_suite_sha256': suite_ref.sha256, 'accepted_cases': list(REQUIRED), 'actual_reverified_cases': proofs, 'actual_native_original_waits': 42, 'source_manifest_pin': source_ref.json(), 'actual_SYSTEM_gate_pin': gate_ref.json(), 'candidate_only_not_runtime_authorization': True, 'native_case_reexecutions': 0, 'full_R08': False, 'paid_maintenance_raw': None, 'payer': None, 'cadence': None}
    q: dict[str, object] = {'schema': 'xar.maintenance.parent_pointer_read.pointer-read-qualification.v1', 'status': 'ROOT_REVIEW_PENDING', 'intended_final_status_after_Root_acceptance': 'SELECTED_POINTER_READ_COLD_PASS', 'mode': MODE, 'machine_id': MACHINE, 'observer_pin': observer.json(), 'source_pins': source_pins, 'SYSTEM_receipt_pin': rebuilt_gate['SYSTEM_receipt'], 'cold_suite_pin': suite_ref.json(), 'candidate_only_not_runtime_authorization': True, 'review_by_utc': '2026-10-22T22:30:00Z', 'full_R08': False}
    return acceptance, q

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite-sha256', default=SUITE_SHA)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    acceptance, q = adjudicate(text(args.suite_sha256, 'suite SHA'))
    if args.verify_only is True:
        print(json.dumps({'machine_id': MACHINE, 'verified_cases': 21, 'original_waits': 42, 'outputs_written': False, 'accepted': False}))
        return 0
    estimate = len(json.dumps(acceptance).encode()) + len(json.dumps(q).encode()) + 8192
    if measure(OUT) + estimate > 98304:
        raise ValueError('Explicit Root adjudication 96KiB sub-budget exceeded')
    acceptance_path = OUT / 'ROOT-ACCEPTANCE.candidate-a01.json'
    write(acceptance_path, acceptance)
    q['Root_acceptance_pin'] = pin(acceptance_path).json()
    q_path = OUT / 'POINTER-READ-QUALIFICATION.candidate-a01.json'
    write(q_path, q)
    print(json.dumps({'machine_id': MACHINE, 'acceptance_candidate': pin(acceptance_path).json(), 'qualification_candidate': pin(q_path).json(), 'verified_cases': 21, 'original_waits': 42, 'accepted': False, 'root_bytes': measure(OUT)}))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
