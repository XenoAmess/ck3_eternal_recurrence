"""One new real serializer wire to strict Army contract and Service consumer."""
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
                    'snapshot_id': 'new-native71-late-event-wire', 'backend_id': 'synthetic-offline-wire',
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
    require(packet == before, 'Service changed owned actual wire')
    require(backend.calls == [('query-army-strengths-v1', 42)], 'Service issued additional native reads')
    raw = before['army_strengths'][0]['actual_army_late_event_observations_v1']
    require(result['army_strengths'][0]['actual_army_late_event_observations_v1'] == raw, 'strict parser lost actual context operands')
    require(result['native_readiness'] == before['native_readiness'], 'native readiness overwritten')
    projection = result['actual_army_late_event_consumption_12004'][0]['projection']
    require(projection['actual_native_dispatch_return_observed'] is True, 'actual natural return was not consumed')
    require(projection['natural_original_return_sequences'] == [1], 'owned event sequence lost')
    require(projection['events'][0]['source_kind'] == 'flag21'
            and projection['events'][0]['caller_return_rva'] == 0x2C448F5, 'source route lost')
    require(raw['events'][0]['before_context']['context_seed_10_raw_u32'] == 37
            and raw['events'][0]['after_context']['context_seed_10_raw_u32'] == 41, 'actual copied pre/post seeds lost')
    require(raw['events'][0]['before_context']['builder_called'] is None, 'context shape promoted to builder execution')
    require(not projection['context_builder_call_inferred'] and not projection['complete_effects_observed']
            and not projection['full_monthly_ready'], 'dispatcher return promoted to complete historical effects')
    outputs = {'owned_actual_query_wire': projection}
    for label, update in (
        ('different-generation', lambda p: p['army_strengths'][0].update(native_carmy_id=-2113929183)),
        ('unobserved-builder', lambda p: p['army_strengths'][0]['actual_army_late_event_observations_v1']['events'][0]['before_context'].update(builder_called=False)),
        ('unobserved-selected-effects', lambda p: p['army_strengths'][0]['actual_army_late_event_observations_v1']['events'][0].update(selected_effects_observed=True)),
        ('wrong-source-route', lambda p: p['army_strengths'][0]['actual_army_late_event_observations_v1']['events'][0].update(caller_return_rva=0x2639CF6)),
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
            del absent['army_strengths'][0]['actual_army_late_event_observations_v1']
        elif label == 'nullable-absence':
            absent['army_strengths'][0]['actual_army_late_event_observations_v1'] = None
        else:
            absent['source'] = {'game_version': CK3_12003.game_version, 'executable_sha256': CK3_12003.executable_sha256}
        value = GameplayBridgeService(Backend(absent)).query_army_strengths([11], expected_revision=42)
        projected = value['actual_army_late_event_consumption_12004'][0]['projection']
        require(projected['status'] == 'unavailable' and not projected['actual_native_dispatch_return_observed'], label + ' became historical evidence')
        require(value['army_strengths'][0]['current_soldiers'] == 160, 'independent native scalar changed')
        outputs[label] = projected
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'native71-59b-first-querywire-Service-compound/1', 'result': 'GREEN',
        'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv, 'pins': pins,
        'input_basis': 'synthetic offline native journal ingress and actual production whole Army serializer',
        'checks': ['whole-native-Army-serializer-to-strict-to-Service', 'actual-owned-pre-post-context-preservation',
            'original-once-return-consumption', 'full-generation-source-builder-effect-rejections',
            'legacy-null-and-exact-build-independent-readiness'],
        'old64_source_focus_or_old_FIRST_replayed': False, 'actual_gameplay_acceptance': False,
        'full_monthly_production_pipeline_ready': False}
    (args.output_dir / 'OBSERVED-OUTPUTS.json').write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'FOCUSED-VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'GREEN', 'checks': len(receipt['checks'])}))


if __name__ == '__main__':
    main()
