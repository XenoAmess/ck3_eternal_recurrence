"""One new software transport qualification using the exact emitted 57e wire."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import sys
import threading

sys.dont_write_bytecode = True


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser()
    for key in ['source-root', 'candidate-root', 'wire', 'recipe', 'output-dir']:
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    recipe = json.loads(args.recipe.read_text(encoding='utf-8'))
    pins = []
    def pin(path, expected=None):
        data = Path(path).read_bytes()
        result = {'path': Path(path).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        require(expected is None or result['sha256'] == expected, 'frozen input changed: ' + str(path))
        pins.append(result)
        return result
    for item in recipe['sources']:
        pin(item['path'], item['sha256'])
    wire_pin = pin(args.wire, recipe['wire']['sha256'])
    sys.path.insert(0, str(args.source_root / 'ck3_autonomous_player/src'))
    import xar_autoplayer.bridge
    xar_autoplayer.bridge.__path__.insert(0, str(args.candidate_root / 'ck3_autonomous_player/src/xar_autoplayer/bridge'))
    # bridge.__init__ eagerly imports the existing driver. Reload only these
    # exact frozen source modules so the real driver's imported decoder is the
    # external candidate, without changing any repository file.
    def load_exact_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    load_exact_module('xar_autoplayer.bridge.battle_control_contract',
                      args.candidate_root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py')
    load_exact_module('xar_autoplayer.bridge.native_driver',
                      args.source_root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py')
    from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1, QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
    from xar_autoplayer.bridge.entry_preceding_capture_contract_12004 import normalize_entry_preceding_capture_12004
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    packet = json.loads(args.wire.read_text(encoding='utf-8'))
    require(packet['type'] == 'command_result' and packet['ok'] is True, 'actual native response is not successful')
    raw = packet['result']['battle_control_snapshot']
    before = deepcopy(packet)
    field = 'entry_preceding_capture_12004'
    sidecar = raw[field]
    checks = []
    kwargs = {'expected_subject_public_cunit_id': raw['subject_public_cunit_id'],
              'expected_observed_date_raw': raw['observed_date_raw'], 'expected_snapshot_revision': raw['snapshot_revision']}
    base_raw = deepcopy(raw)
    base_raw.pop(field)
    base = normalize_battle_control_snapshot_v1(base_raw, **kwargs)
    normalized = normalize_battle_control_snapshot_v1(raw, **kwargs)
    require(normalized[field] == sidecar and {key: value for key, value in normalized.items() if key != field} == base,
            'optional sidecar changed base Battle facts or was not retained exactly')
    require(normalized['status'] == 'available' and normalized['battle_control_ready'] is True and
            normalized[field]['full_entry'] is False and all(row['outer_invocation'] is None for row in normalized[field]['records']),
            'raw preceding capture changed Battle readiness or promoted full Entry')
    checks.append('actual57_parent_strict_preserves_exact_owned_sidecar_and_base_facts')
    class FakeResponseDriver(NativeHeadlessGameplayDriver):
        def __init__(self):
            self._driver_state_lock = threading.RLock()
            self._battle_control_snapshot_v1_query = None
            self.response_calls = []
            self.frame = {'paused': True, 'revision': 9, 'native_revision': raw['snapshot_revision'],
                          'snapshot_id': 'new57e-actual-packet-software', 'date_raw': raw['observed_date_raw'],
                          'episode_run_id': 'new59e-offline', 'diagnostics': {'connection_generation': 1},
                          'player_armies': [{'army_id': raw['subject_public_cunit_id'], 'controllable': True, 'in_combat': True,
                                             'current_province_id': raw['province_id']}]}
        def take_snapshot(self):
            return deepcopy(self.frame)
        def capabilities(self):
            return {'bridge_capabilities': [QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY]}
        def _execute_primitive_step(self, step, *, expected_revision=None, required_capability=None):
            require(expected_revision == 9 and required_capability == QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
                    'unexpected software submission')
            self.response_calls.append(step)
            require(len(self.response_calls) == 1, 'actual transport response consumed more than once')
            # Metadata ordinarily supplied by the existing protocol adapter;
            # the emitted battle payload is copied without any field changes.
            return {'step': step, **deepcopy(packet['result']), 'backend_id': 'synthetic-offline-native-response'}
    driver = FakeResponseDriver()
    step = 'query-battle-control-snapshot-v1-' + str(raw['subject_public_cunit_id'])
    answer = driver._execute_battle_control_snapshot_v1_query(step, expected_revision=9)
    require(answer['battle_control_snapshot'][field] == sidecar and len(driver.response_calls) == 1,
            'actual query consumer lost the same-response capture')
    require(answer['status'] == 'available' and 'active_combat_resume_inputs_v1' not in answer,
            'optional capture changed ordinary availability or synthesized resume inputs')
    cached = driver._battle_control_snapshot_v1_cache_for_snapshot(driver.take_snapshot(), episode_run_id='new59e-offline')
    require(cached is not None and cached['battle_control_snapshot'][field] == sidecar and len(driver.response_calls) == 1,
            'existing cache re-normalization lost the owned raw field or made another query')
    checks.append('one_fake_response_actual_driver_query_cache_and_answer_preserve_sidecar')
    require(normalize_battle_control_snapshot_v1(base_raw, **kwargs) == base, 'legacy absence changed')
    null = deepcopy(base_raw)
    null[field] = None
    require(normalize_battle_control_snapshot_v1(null, **kwargs) == {**base, field: None}, 'explicit null changed base availability')
    checks.append('legacy_absence_and_explicit_null_keep_base_contract')
    variants = {}
    wrong = deepcopy(sidecar)
    wrong['records'][0]['combat_full_id_before'] ^= 1 << 24
    wrong['records'][0]['combat_full_id_after'] ^= 1 << 24
    variants['same_index_different_full_generation'] = wrong
    wrong = deepcopy(sidecar)
    wrong['request_filtered'] = False
    variants['unfiltered_history'] = wrong
    wrong = deepcopy(sidecar)
    wrong['full_entry'] = True
    variants['invented_full_entry'] = wrong
    wrong = deepcopy(sidecar)
    wrong['records'][0]['outer_invocation'] = wrong['records'][0]['record_sequence']
    variants['ordinal_as_outer_invocation'] = wrong
    wrong = deepcopy(sidecar)
    wrong['records'][0]['raw_return_bits'] = True
    variants['boolean_raw_RAX'] = wrong
    wrong = deepcopy(sidecar)
    wrong['records'][0]['original_begin']['thread_id'] = 1 << 32
    variants['thread_width'] = wrong
    for label, value in variants.items():
        try:
            normalize_entry_preceding_capture_12004(value, expected_combat_id=raw['combat_id'])
        except ValueError:
            pass
        else:
            raise AssertionError('strict raw leaf accepted ' + label)
        changed = deepcopy(base_raw)
        changed[field] = value
        require(normalize_battle_control_snapshot_v1(changed, **kwargs) == {**base, field: None},
                'optional malformed sidecar invalidated the base frame: ' + label)
    checks.append('strict_malformed_and_full_generation_misbinding_only_disable_optional_facts')
    partial = deepcopy(sidecar)
    partial['configured'] = False
    partial['installed'] = False
    partial['records'][0]['combat_full_id_after'] = None
    partial['records'][0]['identity_stable'] = False
    partial['records'][0]['original_begin']['thread_id'] = None
    partial['records'][0]['original_completion']['thread_id'] = None
    changed = deepcopy(base_raw)
    changed[field] = partial
    require(normalize_battle_control_snapshot_v1(changed, **kwargs)[field] == partial,
            'nullable independent return identity/thread or retained uninstalled facts were filled or rejected')
    checks.append('partial_return_identity_nullable_threads_and_uninstalled_retained_facts_preserved')
    copied = normalize_entry_preceding_capture_12004(sidecar, expected_combat_id=raw['combat_id'])
    copied['records'][0]['raw_return_bits'] = 0
    require(packet == before and pin(args.wire) == wire_pin, 'raw actual native input was mutated')
    require(sidecar['records'][0]['raw_return_bits'] > (1 << 63), 'actual large unsigned RAX witness is absent')
    checks.append('owned_copy_and_large_uint64_RAX_preserved_native_wire_immutable')
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=False)
    outputs = {'actual_driver_answer': answer, 'actual_cache_readout': cached, 'actual_normalized_battle': normalized,
               'negative_optional_case_labels': list(variants), 'resume_coverage': 'actual57 wire has no resume sibling; absent remains absent'}
    (output / 'OBSERVED-OUTPUTS.json').write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
    proof = {'schema': 'same-query-Battle-preceding-capture-actual-wire-Python-proof/1', 'status': 'GREEN',
             'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'pins': pins,
             'actual_wire': wire_pin, 'fake_response_invocations': 1, 'native_queries': 0,
             'native_compiles': 0, 'native_fixture_runs': 0, 'old_Army_Battle_Entry_tests_replayed': False,
             'full_entry': False, 'outer_invocation': None, 'actual_gameplay_acceptance': False, 'synthetic_offline': True}
    (output / 'FOCUSED-VALIDATION.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'GREEN', 'checks': len(checks), 'fake_response_invocations': 1, 'native_queries': 0}))


if __name__ == '__main__':
    main()
