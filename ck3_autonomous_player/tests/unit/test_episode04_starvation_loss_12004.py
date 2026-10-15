from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).parents[2]/'src/xar_autoplayer/bridge/episode04_starvation_loss_12004.py'
spec = importlib.util.spec_from_file_location('episode04_starvation_loss_12004', MODULE)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def packet():
    values = lambda current: dict(current_soldiers=current, maximum_soldiers=100, state_raw=0)
    writer = dict(sequence=1, army_regiment_id=0, request_raw=500000, request_scale=100000,
        caller_return_rva=0x24E35FF, caller_kind='supply_preferred', observed_date_raw=124,
        before_current_soldiers=100, before_maximum_soldiers=100,
        after_current_soldiers=195, after_maximum_soldiers=200,
        same_instance_after=True, cached_current_delta=95, cached_maximum_delta=100,
        capture_failure_flags=0, native_data_record_count=2, captured_data_record_count=2,
        physical_capture_complete=True, physical_debit_observed=True,
        actual_physical_soldier_debit=5, physical_slot_count=1,
        data_aliases=[dict(data_record_index=i, persistent_regiment_id=16777216,
            data_chunk_ordinal=0, physical_slot_index=0) for i in range(2)],
        physical_slots=[dict(physical_slot_index=0, before=values(100), after=values(95), same_instance_after=True)])
    fields = lambda stock: dict(supply_raw=stock, last_supply_update_date_raw64=100, supply_updated_byte_raw=1)
    callback = dict(sequence=1, army_id=0, native_carmy_id=16777216,
        passed_date_raw64=124, caller_return_rva=0x2A9AB4B, before=fields(1000000),
        after=fields(999999), same_instance_after=True, capture_failure_flags=0)
    family = lambda event, source: dict(status='available', source=source,
        observer_installed=True, oldest_available_sequence=1, latest_sequence=1,
        overwritten_events=0, unattributed_capture_failures=0, event_count=1, events=[event])
    army = dict(monthly_loss_budget_inputs_v1=dict(loaded_supply_state_levels=[60,10,0],
        loaded_supply_state_fractions_raw=[0,0,5000]),
        actual_loss_writer_observations_v1={**family(writer, 'native_natural_writer_entry_return'), 'membership_basis':'membership_at_query'},
        actual_supply_callback_observations_v1={**family(callback, 'native_natural_supply_callback_entry_return'),
            'identity_basis':'public_unit_and_native_carmy_full_ids_at_invocation'})
    window = dict(game_version='1.20.0.4', executable_sha256=api.EXE_SHA256,
        machine_id='fixture-machine-not-live', endpoint_references=['fixture-before','fixture-after'],
        roster_before=[0], roster_after=[0], army_id=0, native_carmy_id=16777216,
        date_before_raw=100, date_after_raw=124, same_session=True, same_army_full_ids=True,
        exact_day=True, stationary_window=True, no_county_arrival=True, no_reorganization=True,
        no_combat=True, no_gathering=True)
    return army, window


def assess(army, window):
    return api.assess_episode04_starvation_loss_12004(army, window=window,
        loss_after_sequence=0, callback_after_sequence=0)


class StarvationEvidenceTests(unittest.TestCase):
    def test_strict_boundary_negative_truncation_wrap_and_loaded_override(self):
        state = lambda raw: api.stock_state_12004(raw, 100000, [60,10,0], [0,0,5000])
        for raw, whole, index, base in [(999999,9,2,5000),(1000000,10,1,0),
                (1000001,10,1,0),(0,0,2,5000),(-1,0,2,5000),(-100001,-1,2,5000),
                ((2**32+10)*100000,10,1,0)]:
            with self.subTest(raw=raw):
                actual = state(raw)
                self.assertEqual((actual['stock_integer'],actual['state_index'],actual['base_fraction_raw']), (whole,index,base))
                self.assertEqual(actual['nonnegative_strict_below_ten'], 0 <= raw < 1000000)
        custom = api.stock_state_12004(999999,100000,[60,7,0],[0,0,2500])
        self.assertEqual(custom['base_fraction_raw'],0)
        self.assertFalse(custom['loaded_arrays_are_stock_60_10_0'])
        for raw, scale in [(True,100000),(1.0,100000),(999999,1),(999999,100000.0)]:
            with self.subTest(raw=raw,scale=scale), self.assertRaises(ValueError):
                api.stock_state_12004(raw,scale,[60,10,0],[0,0,5000])

    def test_physical_aliases_and_cache_increase_do_not_invent_strict_causal_join(self):
        army, window = packet()
        original = deepcopy((army,window))
        result = assess(army,window)
        self.assertEqual(result['actual_supply_preferred_physical_debit_soldiers'],5)
        self.assertTrue(result['source_endpoint_candidate'])
        self.assertEqual(result['strict_starvation_causal_attribution'],'unknown')
        self.assertIn('no_shared_callback_writer_invocation_key_or_stock_at_writer_capture',result['unknown_reasons'])
        self.assertEqual((army,window),original)

    def test_observed_equal_ten_and_negative_poststock_are_not_r05_candidates(self):
        for stock in [1000000,1000001,-1]:
            army,window=packet()
            army['actual_supply_callback_observations_v1']['events'][0]['after']['supply_raw']=stock
            self.assertFalse(assess(army,window)['source_endpoint_candidate'])

    def test_county_same_day_and_siege_or_residual_never_become_supply_stage(self):
        army,window=packet()
        window['no_county_arrival']=False
        self.assertFalse(assess(army,window)['source_endpoint_candidate'])
        for kind,rva in [('siege_or_raid_preferred',0x24E377C),('residual_allocator',0x2A958E8),('other_writer_caller',0x24E25E9)]:
            army,window=packet()
            army['actual_loss_writer_observations_v1']['events'][0].update(caller_kind=kind,caller_return_rva=rva)
            result=assess(army,window)
            self.assertIsNone(result['actual_supply_preferred_physical_debit_soldiers'])
            self.assertEqual(result['rejected_writer_sequences'],[1])

    def test_request_and_net_cache_are_not_physical_debit_and_bad_slot_sum_rejected(self):
        for mutate in [lambda e:e.update(actual_physical_soldier_debit=100),
                lambda e:e.update(physical_capture_complete=False),
                lambda e:e['physical_slots'][0].update(same_instance_after=False),
                lambda e:e.update(native_data_record_count=65),
                lambda e:e['physical_slots'][0]['after'].update(current_soldiers=None)]:
            army,window=packet()
            mutate(army['actual_loss_writer_observations_v1']['events'][0])
            self.assertIsNone(assess(army,window)['actual_supply_preferred_physical_debit_soldiers'])

    def test_gap_repeat_callback_and_membership_change_block_endpoint_candidate(self):
        army,window=packet()
        family=army['actual_loss_writer_observations_v1']
        family.update(oldest_available_sequence=3,latest_sequence=3)
        family['events'][0]['sequence']=3
        self.assertIn('loss_journal_fence_gap_or_reset',assess(army,window)['unknown_reasons'])
        army,window=packet()
        family=army['actual_supply_callback_observations_v1']
        second=deepcopy(family['events'][0]);second['sequence']=2
        family['events'].append(second);family.update(event_count=2,latest_sequence=2)
        self.assertFalse(assess(army,window)['source_endpoint_candidate'])
        army,window=packet();window['roster_after']=[16777216]
        self.assertFalse(assess(army,window)['source_endpoint_candidate'])

    def test_empty_history_is_unknown_and_wrong_build_cannot_qualify(self):
        army,window=packet()
        army['actual_loss_writer_observations_v1'].update(event_count=0,events=[],oldest_available_sequence=0,latest_sequence=0)
        result=assess(army,window)
        self.assertIsNone(result['actual_supply_preferred_physical_debit_soldiers'])
        self.assertIn('empty_retained_writer_history_does_not_prove_zero_loss',result['unknown_reasons'])
        army,window=packet();window['game_version']='1.20.0.3'
        self.assertFalse(assess(army,window)['source_endpoint_candidate'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
