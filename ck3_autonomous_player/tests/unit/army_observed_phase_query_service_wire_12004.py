"""One new owned phase readout and whole query to strict contracts and Service."""
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


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--dependency-manifest', type=Path, required=True)
    parser.add_argument('--query-wire', type=Path, required=True)
    parser.add_argument('--owned-phase-packet', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.dependency_manifest.read_text(encoding='utf-8'))
    pins = []

    def pin(path, expected=None):
        path = Path(path)
        data = path.read_bytes()
        actual = {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        if expected is not None:
            require(actual['sha256'] == expected, 'frozen input changed: ' + str(path))
        pins.append(actual)
        return path

    for item in manifest['production_python'] + manifest['case_exports']:
        pin(item['path'], item['sha256'])
    for path in (Path(__file__), args.dependency_manifest, args.query_wire, args.owned_phase_packet):
        pin(path)
    sys.path.insert(0, str(args.source_root / 'ck3_autonomous_player/src'))
    import xar_autoplayer.bridge
    import xar_autoplayer.simulation
    for package, key in ((xar_autoplayer.bridge, 'bridge_directories'),
                         (xar_autoplayer.simulation, 'simulation_directories')):
        package.__path__[:] = manifest[key] + list(package.__path__)
    for name in ('war_contract', 'service'):
        item = next(item for item in manifest['production_python']
                    if item['module'] == 'xar_autoplayer.bridge.' + name)
        load_file(item['module'], Path(item['path']))
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.army_observed_phase_contract_12004 import FAMILIES, normalize_army_observed_phase_family_12004
    from xar_autoplayer.bridge.army_observed_phase_consumption_12004 import project_army_observed_phases_12004, _phase_for
    from xar_autoplayer.bridge.version_identity import CK3_12004
    query = json.loads(args.query_wire.read_text(encoding='utf-8'))
    readout = json.loads(args.owned_phase_packet.read_text(encoding='utf-8'))
    query_before, readout_before = deepcopy(query), deepcopy(readout)

    class Backend:
        def __init__(self, value):
            self.value, self.calls = value, []
        def take_snapshot(self):
            return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                    'snapshot_id': 'new-owned-army-observed-stage-query', 'backend_id': 'synthetic-offline-wire',
                    'player_armies': [{'army_id': 11}], 'active_wars': [],
                    'diagnostics': {'hello': {'expected_ck3_version': CK3_12004.game_version,
                        'expected_ck3_sha256': CK3_12004.executable_sha256}}}
        def capabilities(self):
            return {'action_steps': ['query-army-strengths-v1']}
        def execute_step(self, step, *, expected_revision=None):
            self.calls.append((step, expected_revision))
            return deepcopy(self.value)

    backend = Backend(query)
    result = GameplayBridgeService(backend).query_army_strengths([11], expected_revision=42)
    require(backend.calls == [('query-army-strengths-v1', 42)], 'Service made additional native reads')
    row = result['army_strengths'][0]
    raw_row = query['army_strengths'][0]
    require(row['current_soldiers'] == 160 and row['maximum_soldiers'] == 200,
            'independent native strength scalars changed')
    require(row['native_carmy_id'] == -2130706399, 'signed full-generation native Army ID changed')
    require(result['native_readiness'] == query['native_readiness'], 'native readiness changed')
    for field in FAMILIES:
        require(row.get(field) == raw_row.get(field), 'owned family changed in strict route: ' + field)
    projected = result['actual_army_observed_phase_consumption_12004'][0]
    require(len(projected['preparation']) == 1 and len(projected['placement']) == 1,
            'actual owned35/36 events did not reach the production consumer')
    require(projected['preparation'][0]['owned_original_return_observed']
            and projected['preparation'][0]['source_inputs_ready'], 'actual preparation inputs were not consumed')
    placement = projected['placement'][0]
    conditional = placement['conditional_preparation_append']
    require(placement['owned_original_return_observed'] and conditional['mapping_ready']
            and conditional['projection'] is not None and conditional['matched_preparation_event'] is not None,
            'actual C++ placement adapter or its owned35 join was not consumed')
    require(not placement['after_table_promoted_to_later_append']
            and not projected['game_load_epoch_inferred']
            and not projected['full_monthly_ready'] and not projected['full_daily_assault_ready'],
            'independent raw facts were promoted to full pipeline readiness')
    require(projected['phase_lineage'] and all(record['session_identity'] is None
            for record in projected['phase_lineage']), 'unknown native load epoch was inferred')
    outputs = {'actual_Service_owned_query_projection': projected, 'owned_readout_projections': [], 'new_cases': {}}

    def normalize(field, value, full):
        return normalize_army_observed_phase_family_12004(field, value, expected_carmy_id=full)

    # These keys were copied from historical owned CArmy rosters. They do not
    # attest current ArmyStrength availability, process lifetime or a load epoch.
    require(readout['schema'] == 'army_owned_natural_journal_readout_12004/1'
            and readout['synthetic_offline_fixture'] is True
            and readout['current_ArmyStrength_availability'] is None
            and readout['current_game_load_epoch'] is None, 'readout provenance changed')
    choices = {field: [] for field in FAMILIES}
    for field in FAMILIES:
        if raw_row.get(field) is not None:
            choices[field].append((raw_row['native_carmy_id'] & 0xFFFFFFFF, raw_row[field]))
    normalized_subjects = []
    for subject in readout['subjects']:
        full = subject['captured_subject_full_carmy_id_u32']
        historical = {'army_id': 11, 'native_carmy_id': full if full < 0x80000000 else full - 0x100000000}
        for field in FAMILIES:
            if field in subject:
                historical[field] = normalize(field, subject[field], full)
                if subject[field] is not None:
                    choices[field].append((full, subject[field]))
        normalized_subjects.append(historical)
        outputs['owned_readout_projections'].append(project_army_observed_phases_12004(historical, exact_source=True))

    def event_count(value):
        if 'events' in value:
            return len(value['events'])
        if 'records' in value:
            return len(value['records'])
        if 'journal' in value:
            return len(value['journal']['events'])
        return sum(len(journal['events']) for journal in value['journals'])

    def coverage_rank(field, value):
        if field == 'actual_army_assault_placement_observations_v1':
            return (any(projection['mapping_ready'] for projection in value['conditional_preparation_append_projections']), event_count(value))
        if field == 'actual_army_regular_core_observations_v1':
            return (any(event['entry_provenance_complete'] and event['entry']['capture_complete']
                        and event['entry']['army_refresh_occurrences'] for event in value['events']), event_count(value))
        if field == 'actual_army_daily_assault_preparation_observations_v1':
            return (any(event['before']['source_inputs_ready'] for event in value['events']), event_count(value))
        return (True, event_count(value))

    for item in manifest['case_exports']:
        if item['kind'] == 'mapper':
            continue
        field = item['field']
        candidates = choices[field]
        if not candidates:
            outputs['new_cases'][item['name']] = ['coverage_unobserved: native family absent']
            continue
        full, family = max(candidates, key=lambda pair: coverage_rank(field, pair[1]))
        if item['name'] == 'core' and not coverage_rank(field, family)[0]:
            outputs['new_cases'][item['name']] = ['coverage_unobserved: no complete actual core entry occurrence']
            continue
        module = load_file('new_owned_case_' + item['name'], Path(item['path']))
        call = getattr(module, item['function'])
        if item['mode'] == 'phase':
            observed = call(family, expected_carmy_id=full,
                            normalize_family=normalize_army_observed_phase_family_12004)
        elif item['mode'] == 'preparation':
            observed = []
            for case in call(family, expected_carmy_id=full):
                raised = False
                try:
                    normalize(field, case['value'], full)
                except ValueError:
                    raised = True
                require(raised is case['expected_raise'], 'preparation new case: ' + case['name'])
                observed.append(case['name'])
        elif item['mode'] == 'keyword':
            observed = call(family, expected_carmy_id=full)
        else:
            observed = call(family, full)
        outputs['new_cases'][item['name']] = observed

    for item in manifest['case_exports']:
        if item['kind'] != 'mapper':
            continue
        module = load_file('new_owned_case_' + item['name'], Path(item['path']))
        call = getattr(module, item['function'])
        candidates = [subject for subject in normalized_subjects if subject.get(item['field'])]
        if item['mode'] == 'core_mapper':
            events = [event for subject in candidates for event in subject[item['field']]['events']]
            if events:
                event = max(events, key=lambda event: (event['entry']['capture_complete'], len(event['entry']['persistent_objects'])))
                outputs['new_cases'][item['name']] = call(event)
            else:
                outputs['new_cases'][item['name']] = ['coverage_unobserved: actual core entry absent']
        elif item['mode'] == 'consumer_mapper':
            pairs = [(event, _phase_for(subject.get('army_natural_phase_observations_v1', {}).get('records', []), event['parent']['phase_entry_event']))
                     for subject in candidates for event in subject[item['field']]['events']]
            pairs = [pair for pair in pairs if pair[1] is not None]
            outputs['new_cases'][item['name']] = call(*pairs[0]) if pairs else ['coverage_unobserved: actual consumer/phase join absent']
        else:
            # The release case export receives the same owned predecessor
            # envelope as the production consumer, including its actual IDs.
            from xar_autoplayer.simulation.army_actual_assault_consumer_stage_12004 import map_actual_assault_consumer_stage_12004
            pair = None
            for subject in candidates:
                daily = subject.get('army_actual_assault_consumer_observations_v1')
                for release in subject[item['field']]['events']:
                    if not daily:
                        continue
                    matches = [event for event in daily['events'] if event['parent']['entry_event'] == release['consumer_entry_event']]
                    if len(matches) != 1:
                        continue
                    event = matches[0]
                    phase = _phase_for(subject.get('army_natural_phase_observations_v1', {}).get('records', []), event['parent']['phase_entry_event'])
                    mapped = map_actual_assault_consumer_stage_12004(event, phase)
                    # Reuse the output already produced by this same production
                    # projection. Do not execute the old numeric kernel again.
                    projection = next((result for result in outputs['owned_readout_projections']
                        if result['native_carmy_id'] == subject['native_carmy_id']), None)
                    numerical = next((value['conditional_numerical_projection'] for value in projection['daily_assault']
                        if value['entry_event'] == event['parent']['entry_event']), None) if projection else None
                    pair = (release, {'native_event': event, 'phase_record': phase, 'mapped': mapped, 'projection': numerical})
                    break
                if pair:
                    break
            outputs['new_cases'][item['name']] = call(*pair) if pair else ['coverage_unobserved: actual release/predecessor join absent']

    require(query == query_before and readout == readout_before, 'a consumer or case export changed actual native input')
    for label, nullable in (('legacy-family-absence', False), ('explicit-family-null', True)):
        value = deepcopy(query)
        for field in FAMILIES:
            if nullable:
                value['army_strengths'][0][field] = None
            else:
                value['army_strengths'][0].pop(field, None)
        absent_backend = Backend(value)
        absent = GameplayBridgeService(absent_backend).query_army_strengths([11], expected_revision=42)
        require(absent['army_strengths'][0]['current_soldiers'] == 160
                and absent['actual_army_observed_phase_consumption_12004'][0]['status'] == 'unavailable'
                and len(absent_backend.calls) == 1, label + ' changed independent scalar or created stage evidence')
        outputs['new_cases'][label] = 'accepted; historical families unavailable'
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'army-observed-phase-whole-query-Service-compound/1', 'result': 'GREEN',
               'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv, 'pins': pins,
               'checks': ['actual-whole-query-to-strict-to-Service', 'installed-owned35-and36-production-adapter',
                          'native-scalars-and-full-generation-ID-preserved', 'unknown-epoch-independent-of-stage-facts',
                          'owned-retained-natural-journals-to-actual-consumers', 'new-family-semantic-and-mapper-cases',
                          'immutable-native-inputs', 'legacy-and-explicit-null-new-family-availability'],
               'synthetic_offline_fixture': True, 'actual_gameplay_acceptance': False,
               'prior_GREEN_focus_or_native_fixture_replayed': False, 'full_daily_monthly_ready': False}
    (args.output_dir / 'OBSERVED-OUTPUTS.json').write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'FOCUSED-VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'GREEN', 'checks': len(receipt['checks']), 'case_exports': len(manifest['case_exports'])}))


if __name__ == '__main__':
    main()
