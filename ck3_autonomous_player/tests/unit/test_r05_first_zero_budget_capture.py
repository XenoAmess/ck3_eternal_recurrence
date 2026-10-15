"""First-zero/zero-retaining budget decisions; fixture inputs only."""
from copy import deepcopy
import unittest
from test_r05_zero_preparation_decision import context
from xar_autoplayer.bridge.army_zero_stock_clock_12004 import (
    successful_supply_occurrences_to_zero_12004 as opportunities,
    project_zero_stock_next_callback_candidate_12004 as next_candidate,
)
from xar_autoplayer.strategy import plan_r05_zero_stock_preparation

def zero_fixture(*,stock=1,rate=-1,count=20):
    data=context();row=data['army_query']['army_strengths'][0]
    row.update(current_supply_raw=stock,current_supply_change_monthly_raw=rate)
    row['monthly_loss_budget_inputs_v1'].update(status='available',ready=True,
        unavailable_reason=None,scale=100000,native_fleet_supply_loss_suppressed=False,
        loaded_supply_state_levels=[60,10,0],loaded_supply_state_fractions_raw=[0,0,5000],
        commander_valid=True,commander_supply_modifier_id=77,commander_supply_modifier_raw=0)
    row['loss_application_inputs_v1']=dict(supply_eligible_soldiers=count)
    return data,row

class FirstZeroBudgetCaptureTests(unittest.TestCase):
    def test_raw_negative_one_finite_and_cap_add_before_clamp(self):
        self.assertEqual(opportunities(3,100,-1)['successful_bucket_occurrences'],3)
        maximum=(1<<63)-1
        self.assertEqual(opportunities(maximum,maximum,-1)['successful_bucket_occurrences'],maximum)
        self.assertEqual(opportunities(30000000,10000000,-1)['successful_bucket_occurrences'],10000001)
        for stock in (1,10000000):
            self.assertFalse(opportunities(stock,10000000,0)['ready'])

    def test_zero_retaining_cases_do_not_require_negative_monthly(self):
        value=opportunities(0,10000000,0)
        self.assertTrue(value['ready']);self.assertEqual(value['successful_bucket_occurrences'],0)
        self.assertEqual(value['first_new_zero_writer_opportunity'],1)
        self.assertEqual(opportunities(10000000,0,0)['successful_bucket_occurrences'],1)
        self.assertTrue(opportunities(0,0,2000000)['ready'])
        self.assertFalse(opportunities(0,10000000,1)['ready'])

    def test_first_zero_callback_has_positive_budget_before_zero_entry_exists(self):
        _,row=zero_fixture()
        value=next_candidate(row)
        self.assertFalse(value['conditional_zero_entry_capture_candidate'])
        budget=value['conditional_next_zero_supply_budget_v1']
        self.assertTrue(budget['conditional_positive_budget_capture_candidate'])
        self.assertTrue(budget['first_reaches_zero_in_this_conditional_callback'])
        self.assertEqual(budget['supply_budget_soldiers'],1)
        self.assertEqual(budget['candidate_first_original_pointer_position'],0)
        self.assertEqual(budget['current_supply_fraction_modifier_id'],77)
        self.assertFalse(budget['physical_loss_observed'])
        self.assertFalse(budget['physical_writer_execution_ready'])

    def test_zero_rate_zero_stock_now_uses_existing_decision(self):
        data,row=zero_fixture(stock=0,rate=0,count=100)
        value=plan_r05_zero_stock_preparation(**data)
        self.assertIsNotNone(value['r05_zero_stock_preparation_v1']['selected'])
        self.assertEqual(value['selected_step'],'life-advance-one-day')
        budget=next_candidate(row)['conditional_next_zero_supply_budget_v1']
        self.assertEqual(budget['supply_budget_soldiers'],5)
        self.assertTrue(budget['conditional_positive_budget_capture_candidate'])

    def test_first_zero_nonpositive_budget_at_floor_or_component_suppression(self):
        for count,expected in ((19,0),(20,1)):
            _,row=zero_fixture(count=count)
            budget=next_candidate(row)['conditional_next_zero_supply_budget_v1']
            self.assertEqual(budget['supply_budget_soldiers'],expected)
            self.assertEqual(budget['conditional_positive_budget_capture_candidate'],expected>0)
        _,row=zero_fixture(count=100)
        row['monthly_loss_budget_inputs_v1']['commander_supply_modifier_raw']=-100000
        self.assertEqual(next_candidate(row)['conditional_next_zero_supply_budget_v1']['supply_budget_soldiers'],0)
        row['monthly_loss_budget_inputs_v1']['native_fleet_supply_loss_suppressed']=True
        row['monthly_loss_budget_inputs_v1']['loaded_supply_state_levels']=None
        row['monthly_loss_budget_inputs_v1'].update(status='unavailable',ready=False,unavailable_reason='unneeded_later_inputs')
        self.assertFalse(next_candidate(row)['conditional_next_zero_supply_budget_v1']['conditional_positive_budget_capture_candidate'])

    def test_missing_fraction_or_wrong_gate_never_becomes_default_five_percent(self):
        data=context();row=data['army_query']['army_strengths'][0]
        row.update(current_supply_raw=0,current_supply_change_monthly_raw=0)
        budget=next_candidate(row)['conditional_next_zero_supply_budget_v1']
        self.assertIsNone(budget['conditional_positive_budget_capture_candidate'])
        self.assertIn('complete_current_monthly_loss_budget_inputs_v1',budget['missing_inputs'])
        _,row=zero_fixture()
        row['monthly_loss_budget_inputs_v1']['native_unit_in_combat']=True
        self.assertFalse(next_candidate(row)['conditional_next_zero_supply_budget_v1']['conditional_positive_budget_capture_candidate'])
        _,row=zero_fixture(stock=0,rate=1000000)
        budget=next_candidate(row)['conditional_next_zero_supply_budget_v1']
        self.assertEqual(budget['conditional_post_supply_raw'],1000000)
        self.assertFalse(budget['conditional_positive_budget_capture_candidate'])

    def test_absent_commander_unclamped_fraction_preserves_native_signed_budget(self):
        _,row=zero_fixture(count=1)
        row['monthly_loss_budget_inputs_v1'].update(commander_valid=False,
            commander_supply_modifier_id=None,commander_supply_modifier_raw=None,
            loaded_supply_state_fractions_raw=[0,0,100000*(1<<31)])
        budget=next_candidate(row)['conditional_next_zero_supply_budget_v1']
        self.assertEqual(budget['supply_budget_soldiers'],-(1<<31))
        self.assertFalse(budget['conditional_positive_budget_capture_candidate'])
