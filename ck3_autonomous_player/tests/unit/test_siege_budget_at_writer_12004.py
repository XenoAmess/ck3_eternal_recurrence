"""New stack-budget leaf cases; fixtures below are synthetic, not live loss."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from xar_autoplayer.bridge.army_actual_siege_budget_at_writer_contract import normalize_siege_budget_at_writer_v1
from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1
from xar_autoplayer.bridge.army_siege_parent_loss_evidence_12004 import evaluate_siege_parent_loss_evidence_12004

factory_path=Path(__file__).with_name('test_army_siege_parent_loss_evidence_12004.py')
spec=importlib.util.spec_from_file_location('r03_old_factory_only',factory_path)
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)

def leaf(siege=10,combined=10,supply=0,flags=0):
    complete=siege is not None and combined is not None
    raid=None if not complete else ((combined-siege+(1<<31))%(1<<32))-(1<<31)
    return dict(source_callback_entry_rva=0x24E3410,source_writer_return_rva=0x24E377C,
        return_slot_basis='natural_writer_hook_incoming_return_address',
        original_supply_budget_soldiers=supply,original_siege_budget_soldiers=siege,
        combined_siege_raid_budget_soldiers=combined,derived_original_raid_budget_soldiers=raid,
        siege_raid_capture_complete=complete,capture_failure_flags=flags)

def packet(value):
    army=factory.fixture()
    writer=army['actual_loss_writer_observations_v1']['events'][1]
    writer['siege_budget_at_writer_v1']=value
    # The callback's original supply budget is zero: no supply writer is
    # fabricated. Global sequence1 may belong to another queried-out ArRg.
    army['actual_loss_writer_observations_v1'].update(events=[writer],event_count=1)
    return army

def evaluate(army):
    army=deepcopy(army)
    army['actual_loss_writer_observations_v1']=normalize_actual_loss_writer_observations_v1(
        army['actual_loss_writer_observations_v1'],current_regiment_ids=[0])
    return evaluate_siege_parent_loss_evidence_12004(army,game_version='1.20.0.4',executable_sha256=factory.PIN,
        callback_after_sequence=0,loss_after_sequence=0,date_raw_min_exclusive=100,date_raw_max_inclusive=124)

class SiegeBudgetAtWriterTests(unittest.TestCase):
    def test_actual_budget_leaf_unlocks_only_this_complete_positive_siege_invocation(self):
        value=packet(leaf());before=deepcopy(value);result=evaluate(value)
        self.assertEqual(value,before)
        self.assertTrue(result['siege_only_causal_attribution_ready'])
        self.assertEqual(len(result['siege_only_positive_writer_events']),1)
        self.assertEqual(result['siege_only_positive_writer_events'][0]['original_supply_budget_soldiers'],0)
        self.assertFalse(result['complete_interval_loss_total_ready'])

    def test_nonzero_raid_or_zero_siege_does_not_claim_siege_only(self):
        for value in (leaf(10,12),leaf(0,10),leaf(-1,-1)):
            result=evaluate(packet(value))
            self.assertTrue(result['same_callback_combined_stage_positive_observed'])
            self.assertFalse(result['siege_only_causal_attribution_ready'])

    def test_failed_siege_combined_and_missing_return_slot_remain_unknown(self):
        for value in (leaf(None,10,flags=4),leaf(10,None,flags=8),leaf(None,None,None,1)):
            self.assertFalse(evaluate(packet(value))['siege_only_causal_attribution_ready'])

    def test_independent_supply_read_failure_does_not_erase_complete_siege_raid_operands(self):
        result=evaluate(packet(leaf(supply=None,flags=2)))
        self.assertTrue(result['siege_only_causal_attribution_ready'])
        self.assertIsNone(result['siege_only_positive_writer_events'][0]['original_supply_budget_soldiers'])

    def test_signed32_inverse_preserves_native_add_wrap(self):
        self.assertEqual(normalize_siege_budget_at_writer_v1(leaf((1<<31)-1,-(1<<31)))['derived_original_raid_budget_soldiers'],1)

    def test_source_basis_and_wrong_caller_do_not_accept_stack_from_a_helper(self):
        value=leaf();value['return_slot_basis']='typed_producer_helper_return_address'
        with self.assertRaises(ValueError):normalize_siege_budget_at_writer_v1(value)
        army=packet(leaf());army['actual_loss_writer_observations_v1']['events'][0].update(caller_kind='supply_preferred',caller_return_rva=0x24E35FF)
        with self.assertRaises(ValueError):evaluate(army)

    def test_legacy_wire_preserves_combined_fact_without_new_cause_credit(self):
        army=packet(leaf());army['actual_loss_writer_observations_v1']['events'][0].pop('siege_budget_at_writer_v1')
        result=evaluate(army)
        self.assertTrue(result['same_callback_combined_stage_positive_observed'])
        self.assertFalse(result['siege_only_causal_attribution_ready'])

    def test_malformed_derivation_boolean_operand_and_extent_are_rejected(self):
        for mutate in (lambda v:v.update(derived_original_raid_budget_soldiers=1),
                       lambda v:v.update(original_supply_budget_soldiers=True),
                       lambda v:v.update(original_siege_budget_soldiers=1<<31),
                       lambda v:v.update(siege_raid_capture_complete=False)):
            value=leaf();mutate(value)
            with self.assertRaises(ValueError):normalize_siege_budget_at_writer_v1(value)

if __name__=='__main__':unittest.main()
