"""One portable production-ingress/physical-consumer compound; native premises synthetic."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import sys
import types
import subprocess

sys.dont_write_bytecode = True


def need(ok, why):
    if not ok:
        raise ValueError(why)


def rejected(call):
    try:
        call()
    except ValueError:
        return
    raise ValueError('Malformed native direct ownership was accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--package-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), 'Create-only compound output already exists')
    contract_relative = 'ck3_autonomous_player/src/xar_autoplayer/bridge/army_actual_loss_writer_observations_contract.py'
    module_relative = 'ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_primary_direct_owner_12004.py'
    original = candidate = (args.repo/contract_relative).read_bytes()
    if args.package_root:
        sys.path.insert(0, str(args.package_root))
        from delivery_plan import patched_contract
        original, candidate = patched_contract(args.repo)
    sys.path.insert(0, str(args.repo/'ck3_autonomous_player/src'))
    import xar_autoplayer.bridge as bridge
    if args.package_root:
        bridge.__path__.insert(0, str(args.package_root/'candidate/ck3_autonomous_player/src/xar_autoplayer/bridge'))
        for name in ('army_actual_loss_writer_observations_contract', 'army_physical_loss_evidence_12004',
                     'army_county_entry_loss_evidence_12004', 'army_county_primary_owner_12004'):
            sys.modules.pop('xar_autoplayer.bridge.' + name, None)
        name = 'xar_autoplayer.bridge.army_actual_loss_writer_observations_contract'
        contract = types.ModuleType(name)
        contract.__package__ = 'xar_autoplayer.bridge'
        contract.__file__ = '<exact-in-memory-postimage:' + contract_relative + '>'
        sys.modules[name] = contract
        exec(compile(candidate, contract.__file__, 'exec'), contract.__dict__)
    from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1 as normalize
    from xar_autoplayer.bridge.army_county_primary_direct_owner_12004 import KEY, EXE, UNBOUND_KEY, UNBOUND_OVERWRITTEN, evaluate_county_primary_direct_owner_evidence_12004 as consume
    from xar_autoplayer.bridge.army_county_primary_owner_12004 import evaluate_county_primary_owner_evidence_12004 as consume_v1
    from xar_autoplayer.bridge.army_county_entry_loss_evidence_12004 import classify_retained_loss_writer_window_v1 as old_classify
    fixture_path = args.repo/'ck3_autonomous_player/tests/unit/test_army_county_entry_loss_evidence_12004.py'
    spec = importlib.util.spec_from_file_location('_existing_county_direct_fixture', fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    e = fixture.event(sequence=1201, caller=0x24E25EE)
    e['observed_date_raw'] = 53147544
    owner = dict(schema_version=2, source='native_county_primary_R13_direct_writer_v2',
        caller_return_rva=0x24E25EE, writer_invocation_token=50001,
        writer_receiver_identity=0x3000000, source_carmy_identity=0x3001000,
        current_game_state_identity=0x4000000, public_unit_identity=0x3002000,
        writer_thread_id=30600, writer_event=dict(clock_identity=0x123456, sequence=301, thread_id=30600),
        observed_date_raw64=(0x42B << 32) | e['observed_date_raw'], natural_sampling_enabled=True,
        actual4_source_qualified=True, natural_sampling_epoch=6, army_id=0, native_carmy_id=0,
        writer_full_regiment_id=e['army_regiment_id'], native_army_registry_identity=0x3001000,
        public_unit_registry_identity=0x3002000, writer_registry_identity=0x3000000,
        army_roster_occurrence=0, army_roster_count=1, receiver_identity_matches=True,
        writer_identity_matches=True, native_army_registry_matches=True,
        public_unit_registry_matches=True, public_native_bidirectional_matches=True,
        writer_registry_matches=True, actual_array_contains_writer=True,
        physical_association_complete=True, physical_capture_complete=True,
        captured_physical_association_count=2, capture_failure_flags=0, capture_skip_reason='',
        active_phase_observed=False, active_phase_kind=0, active_phase_entry_rva=0,
        source_complete=True, physical_associations=[])
    for index in range(2):
        owner['physical_associations'].append(dict(data_record_index=index, persistent_regiment_id=12,
            data_chunk_ordinal=2, physical_slot_index=0, persistent_registry_identity=0x9000000,
            selected_physical_identity=0x9000060, expected_physical_identity=0x9000060,
            physical_persistent_regiment_id=12, physical_own_ordinal=2,
            physical_army_regiment_id=e['army_regiment_id'], registry_matches=True,
            physical_identity_matches=True))
    e[KEY] = owner
    family = fixture.family([e])
    family.update(oldest_available_sequence=1170, latest_sequence=1385, overwritten_events=1169)
    row = dict(status='available', army_id=0, native_carmy_id=0,
        regiment_strengths=[dict(army_regiment_id=e['army_regiment_id'])],
        actual_loss_writer_observations_v1=family)

    def run(value, after=1190):
        return consume(value, executable_sha256=EXE, after_sequence=after,
                       before_unattributed_capture_failures=0)

    def context(value):
        return value['actual_loss_writer_observations_v1']['events'][0][KEY]

    normalized = normalize(family, current_regiment_ids=[e['army_regiment_id']])
    need(normalized['events'][0][KEY] == owner and normalized['events'][0][KEY] is not owner,
         'Exact new child did not survive the production normalizer as an owned copy')
    observed = run(row)
    need(len(observed['positive_invocations']) == 1 and observed['positive_invocations'][0]['actual_physical_soldier_debit'] == 7
         and observed['individual_county_army_owner_observed'] and observed['global_window_continuous'],
         'Native direct no-phase premises did not join actual physical evidence')
    need(observed['county_total_debit'] is None and observed['complete_army_loss_history'] is False
         and observed['whole_window_county_total_ready'] is False and observed['returned_phase_parent_claimed'] is False,
         'One invocation acquired a whole-window or returned-phase claim')
    post = deepcopy(row)
    context(post).update(active_phase_observed=True, active_phase_kind=2, active_phase_entry_rva=0x2A9A570)
    need(len(run(post)['positive_invocations']) == 1 and run(post)['returned_phase_parent_claimed'] is False,
         'Post-date diagnostic was lost or reclassified as a returned pre-date parent')
    checks = ['production_exact_ingress_to_physical_consumer_no_phase_and_post_date']
    gap = run(row, after=0)
    need(len(gap['positive_invocations']) == 1 and not gap['global_window_continuous']
         and gap['global_window_continuity_reasons'] == ['requested_window_overwritten'],
         'Individual direct fact concealed a global ring gap')
    checks.append('global_195_call_window_and_target_fact_are_independent')
    wide = deepcopy(row); context(wide).update(army_roster_count=65536, army_roster_occurrence=65535)
    need(len(run(wide)['positive_invocations']) == 1, 'Native roster capture boundary differs from Python')

    for mutate in (
        lambda c: c.update(native_army_registry_identity=c['source_carmy_identity'] + 8),
        lambda c: c.update(writer_registry_matches=False),
        lambda c: c['writer_event'].update(thread_id=7896),
        lambda c: c.update(natural_sampling_enabled=False),
        lambda c: c.update(capture_failure_flags=1 << 16),
        lambda c: c.update(source_complete=False, capture_failure_flags=1, capture_skip_reason=''),
        lambda c: c.update(army_roster_count=65537),
    ):
        bad = deepcopy(row); mutate(context(bad)); rejected(lambda: run(bad))
    checks.append('registry_thread_sampling_and_unknown_failure_guards_are_strict')
    bad = deepcopy(row); context(bad)['army_id'] = 1
    need(not run(bad)['positive_invocations'], 'Cross-Army source was filled from selected query')
    bad = deepcopy(row); c = context(bad); c['writer_full_regiment_id'] = 0x2000001
    for association in c['physical_associations']:
        association['physical_army_regiment_id'] = c['writer_full_regiment_id']
    need(not run(bad)['positive_invocations'], 'Different full ArRg generation was filled from query')
    bad = deepcopy(row); context(bad)['observed_date_raw64'] += 24
    need(not run(bad)['positive_invocations'], 'Literal writer game-state date mismatch was ignored')
    checks.append('cross_Army_full_generation_and_date_are_not_backfilled')

    repeated = deepcopy(row)
    duplicate = deepcopy(e); duplicate['sequence'] += 1
    repeated['actual_loss_writer_observations_v1']['events'].append(duplicate)
    repeated['actual_loss_writer_observations_v1']['event_count'] += 1
    need(not run(repeated)['positive_invocations'], 'One actual entry token qualified two writer calls')
    checks.append('writer_invocation_token_reuse_rejects_both_calls')
    for mutate in (
        lambda c: c['physical_associations'][0].update(expected_physical_identity=0x9000064),
        lambda c: c['physical_associations'][0].update(physical_own_ordinal=3),
    ):
        bad = deepcopy(row); mutate(context(bad)); rejected(lambda: run(bad))
    bad = deepcopy(row)
    bad['actual_loss_writer_observations_v1']['events'][0]['data_aliases'][0]['persistent_regiment_id'] = 13
    need(not run(bad)['positive_invocations'], 'Child physical association was attached to a different DATA alias')
    bad = deepcopy(row)
    bad['actual_loss_writer_observations_v1']['events'][0]['actual_physical_soldier_debit'] = 999
    need(not run(bad)['positive_invocations'], 'Direct ownership replaced unique physical before/after proof')
    checks.append('physical_pointer_triple_DATA_binding_and_actual_debit_are_independent')

    incomplete = deepcopy(row)
    context(incomplete).update(source_complete=False, writer_invocation_token=0,
        capture_failure_flags=1, capture_skip_reason='writer_registers_missing')
    excluded = run(incomplete)['excluded_invocations'][0]
    need(not run(incomplete)['positive_invocations']
         and excluded['native_direct_capture']['capture_skip_reason'] == 'writer_registers_missing',
         'Missing register capture diagnostics were dropped or qualified')
    legacy = deepcopy(row); legacy['actual_loss_writer_observations_v1']['events'][0].pop(KEY)
    need(not run(legacy)['positive_invocations'] and run(legacy)['global_window_continuous'],
         'Old missing-child evidence was reclassified')
    need(not consume_v1(row, executable_sha256=EXE, after_sequence=1190,
                       before_unattributed_capture_failures=0)['positive_invocations'],
         'Direct v2 child was used to bypass the strict v1 returned-phase contract')
    old = old_classify(family, current_regiment_ids=[e['army_regiment_id']], executable_sha256=EXE,
                      after_sequence=1190, before_unattributed_capture_failures=0)
    need(old['army_at_invocation_observed'] is False and old['county_total_debit'] is None,
         'Legacy source classifier was silently upgraded')
    checks.append('explicit_register_skip_legacy_unknown_and_strict_v1_contract_preserved')
    foreign = deepcopy(family); foreign['events'][0]['caller_return_rva'] = 0x24E35FF
    rejected(lambda: normalize(foreign, current_regiment_ids=[e['army_regiment_id']]))
    checks.append('foreign_parent_caller_cannot_carry_direct_county_child')

    unbound = deepcopy(row)
    diagnostic = deepcopy(context(incomplete))
    unbound['actual_loss_writer_observations_v1'][UNBOUND_KEY] = [dict(diagnostic_only=True, ownership=diagnostic)]
    unbound['actual_loss_writer_observations_v1'][UNBOUND_OVERWRITTEN] = 3
    kept = run(unbound)
    need(len(kept['positive_invocations']) == 1 and kept['global_window_continuous']
         and kept['global_journal_coverage']['event_count'] == 1
         and kept['unbound_direct_capture_diagnostics']['scope'] == 'global_unbound_no_selected_Army_membership'
         and kept['unbound_direct_capture_diagnostics']['overwritten'] == 3,
         'Unbound diagnostics changed selected events or global journal coverage')
    diagnostic_only = deepcopy(unbound)
    diagnostic_only['actual_loss_writer_observations_v1']['events'][0].pop(KEY)
    need(not run(diagnostic_only)['positive_invocations'], 'Unbound diagnostics filled selected Army ownership')
    for mutate in (
        lambda f: f.pop(UNBOUND_OVERWRITTEN),
        lambda f: f[UNBOUND_KEY][0].update(diagnostic_only=False),
        lambda f: f[UNBOUND_KEY][0].update(ownership=deepcopy(owner)),
        lambda f: f[UNBOUND_KEY][0]['ownership'].update(capture_failure_flags=0, capture_skip_reason=''),
    ):
        bad = deepcopy(unbound); mutate(bad['actual_loss_writer_observations_v1']); rejected(lambda: run(bad))
    need(UNBOUND_KEY not in normalized and UNBOUND_OVERWRITTEN not in normalized,
         'Legacy absent diagnostic pair was invented')
    checks.append('independent_unbound_pair_is_strict_diagnostic_only_and_preserves_old_counts')

    if args.package_root:
        base = json.loads((args.package_root/'BASE.actual.json').read_text(encoding='utf-8'))
        machine = base['machine_id']
        module_path = args.package_root/'candidate'/module_relative
    else:
        machine = subprocess.check_output([sys.executable, '-B', str(args.repo/'tools/ck3_live_run_id.py'), 'machine'], text=True).strip()
        module_path = args.repo/module_relative
    report = dict(schema='xar.r218.county-direct-owner.compound.v1',
        status='PASS_ONE_PRODUCTION_DIRECT_OWNER_COMPOUND', machine_id=machine,
        observed_at_utc=datetime.now(timezone.utc).isoformat(), checks=checks,
        native_inputs='explicitly synthetic registers/registry/membership/date/physical premises',
        contract_pre_sha256=hashlib.sha256(original).hexdigest(),
        contract_post_sha256=hashlib.sha256(candidate).hexdigest(),
        new_module_sha256=hashlib.sha256(module_path.read_bytes()).hexdigest(),
        native_DLL_built=False, native_code_executed=False, SDK_DR_game_calls=0, D_writes=0,
        actual_R217_reclassified=False, R04_live_closed=False, old_matrix_runs=0,
        optimization=sys.flags.optimize)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2); output.write('\n')
    print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
