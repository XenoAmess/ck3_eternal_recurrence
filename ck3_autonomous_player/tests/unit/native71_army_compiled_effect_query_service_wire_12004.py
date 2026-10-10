"""One new compiled-effect whole native query wire to strict route and Service."""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--query-wire', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / 'ck3_autonomous_player/src'))
    import xar_autoplayer.bridge
    pins = []

    def pin(path):
        data = path.read_bytes()
        return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    for name, relative in (
        ('xar_autoplayer.bridge.war_contract', 'ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py'),
        ('xar_autoplayer.bridge.service', 'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py'),
    ):
        path = args.candidate_root / relative
        pins.append(pin(path))
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.version_identity import CK3_12004, CK3_12003
    pins.extend([pin(Path(__file__)), pin(args.query_wire)])
    packet = json.loads(args.query_wire.read_text(encoding='utf-8'))
    before = deepcopy(packet)

    class Backend:
        def __init__(self, value):
            self.value, self.calls = value, []

        def take_snapshot(self):
            return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                    'snapshot_id': 'new-native71-compiled-effect-wire', 'backend_id': 'synthetic-offline-wire',
                    'player_armies': [{'army_id': 11}], 'active_wars': [],
                    'diagnostics': {'hello': {'expected_ck3_version': CK3_12004.game_version,
                        'expected_ck3_sha256': CK3_12004.executable_sha256}}}

        def capabilities(self):
            return {'action_steps': ['query-army-strengths-v1']}

        def execute_step(self, step, *, expected_revision=None):
            self.calls.append((step, expected_revision))
            return deepcopy(self.value)

    backend = Backend(packet)
    result = GameplayBridgeService(backend).query_army_strengths([11], expected_revision=42)
    require(packet == before, 'Service changed owned compiled-effect wire')
    require(backend.calls == [('query-army-strengths-v1', 42)], 'Service issued additional native reads')
    raw = before['army_strengths'][0]['actual_compiled_effect_observations_v1']
    require(result['army_strengths'][0]['actual_compiled_effect_observations_v1'] == raw, 'strict parser lost copied native operands')
    require(result['native_readiness'] == before['native_readiness'], 'native readiness overwritten')
    projection = result['actual_army_compiled_effect_consumption_12004'][0]['projection']
    require(projection['owned_original_return_sequences'] == [1, 2]
            and projection['owned_original_return_observed'], 'owned actual returns were not consumed')
    require([event['source_kind'] for event in projection['events']] == ['positive_1e0', 'flag30'], 'source routes lost')
    require([event['original_rax_raw_u64'] for event in projection['events']] == [0xF123456789ABCDEF] * 2, 'raw original RAX bits lost')
    require(projection['events'][0]['before_seed_raw_u32'] == 17
            and projection['events'][1]['before_seed_raw_u32'] == 0x80000009
            and projection['events'][1]['negative_seed_receiver_key_2c_raw_u32'] == 0x76543210, 'conditional copied receiver operands lost')
    require(raw['current_session_guard'] is False and projection['current_session_guard'] is False
            and projection['status'] == 'partial' and not projection['actual_native_compiled_effect_return_observed'], 'synthetic fixture promoted to installed current session')
    require(projection['derived_seed'] is None and projection['date_or_frame_at_invocation'] is None
            and not projection['complete_effects_observed'] and not projection['full_monthly_ready'], 'unknown seed/date/effects/monthly inferred')
    outputs = {'owned_actual_compiled_effect_query_wire': projection}
    for label, update in (
        ('different-generation', lambda p: p['army_strengths'][0].update(native_carmy_id=-2113929183)),
        ('invalid-native-sentinel', lambda p: p['army_strengths'][0].update(native_carmy_id=-1)),
        ('negative-logical-army-id', lambda p: p['army_strengths'][0].update(army_id=-1)),
        ('wrong-receiver-route', lambda p: p['army_strengths'][0]['actual_compiled_effect_observations_v1']['events'][0].update(receiver_owner_offset=0x230)),
        ('noninteger-thread', lambda p: p['army_strengths'][0]['actual_compiled_effect_observations_v1']['events'][0].update(thread_id=True)),
        ('unobserved-fallback', lambda p: p['army_strengths'][0]['actual_compiled_effect_observations_v1']['events'][0].update(rng_fallback_observed=True)),
        ('unobserved-derived-seed', lambda p: p['army_strengths'][0]['actual_compiled_effect_observations_v1']['events'][0].update(derived_seed_raw_u32=29)),
    ):
        malformed = deepcopy(packet)
        update(malformed)
        try:
            GameplayBridgeService(Backend(malformed)).query_army_strengths([11], expected_revision=42)
        except BridgeUnavailableError:
            outputs[label] = 'rejected by strict production Army route'
        else:
            raise AssertionError(label + ' was accepted')
    for label in ('legacy-absence', 'nullable-absence', 'other-exact-build'):
        absent = deepcopy(packet)
        if label == 'legacy-absence':
            del absent['army_strengths'][0]['actual_compiled_effect_observations_v1']
        elif label == 'nullable-absence':
            absent['army_strengths'][0]['actual_compiled_effect_observations_v1'] = None
        else:
            absent['source'] = {'game_version': CK3_12003.game_version, 'executable_sha256': CK3_12003.executable_sha256}
        value = GameplayBridgeService(Backend(absent)).query_army_strengths([11], expected_revision=42)
        projected = value['actual_army_compiled_effect_consumption_12004'][0]['projection']
        require(projected['status'] == 'unavailable' and not projected['owned_original_return_observed'], label + ' became historical evidence')
        require(value['army_strengths'][0]['current_soldiers'] == 160, 'independent native scalar changed')
        outputs[label] = projected
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'native71-59c-first-compiled-querywire-Service-compound/1', 'result': 'GREEN',
        'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv, 'pins': pins,
        'input_basis': 'synthetic offline compiled-effect native ingress and actual whole production Army serializer',
        'checks': ['whole-native-query-serializer-to-strict-to-Service', 'owned-caller-thread-entry-return-and-RAX-preservation',
            'conditional-negative-receiver-key-preservation', 'synthetic-session-does-not-get-installed-production-credit',
            'full-generation-source-thread-fallback-derived-seed-rejections', 'nullable-legacy-and-other-build-readiness'],
        'old59b_or_63b_source_focus_or_FIRST_replayed': False, 'actual_gameplay_acceptance': False,
        'full_monthly_production_pipeline_ready': False}
    (args.output_dir / 'OBSERVED-OUTPUTS.json').write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'FOCUSED-VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'GREEN', 'checks': len(receipt['checks'])}))


if __name__ == '__main__':
    main()
