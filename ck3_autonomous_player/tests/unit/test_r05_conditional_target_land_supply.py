"""R05 conditional arrival behavior; all native inputs are fixtures."""
import copy
import unittest
from xar_autoplayer import strategy
from xar_autoplayer.bridge.army_target_land_supply_projection_12004 import project_conditional_target_land_rate_12004 as project
from xar_autoplayer.bridge.army_full_land_supply_rate_projection import _project_land_rate_operands_v1
from xar_autoplayer.bridge.war_contract import preview_move_army_step,move_army_step

def context():
    date = 43800024
    snapshot = dict(snapshot_id="native:44", revision=9, native_revision=44,
        diagnostics=dict(connection_generation=1), episode_run_id="normal-R05", date_raw=date,
        paused=True, player_armies=[dict(army_id=18, current_province_id=2628,
            controllable=True, in_combat=False, retreating=False)])
    lease = dict(queried_snapshot_id="native:44", queried_revision=9,
        queried_native_revision=44, queried_connection_generation=1,
        queried_episode_run_id="normal-R05")
    regiment = dict(stored_index=0, army_regiment_id=12, status="available", unavailable_reason=None,
        current_soldiers=100, maximum_soldiers=100, native_supply_loss_eligible=True,
        replenishment_records_v1=None)
    contributor = dict(source="native_current_province_mode0", status="available", unavailable_reason=None,
        current_usage_ready=True, contributors_ready=True, province_id=2628,
        subject_army_id=18, subject_carmy_id=18, owner_character_id=22,
        native_province_unit_count=1, native_supply_limit_soldiers=50,
        native_supply_usage_soldiers=100, soldiers_scale=1,
        occurrences=[dict(stored_index=0, army_id=18, status="available", unavailable_reason=None,
            owner_character_id=22, included=True, inclusion_basis="same_owner", native_carmy_id=18,
            native_eligible_current_soldiers=100, regiments=[regiment])])
    phases = [dict(phase_index_i32=i, status="available", ready=True, unavailable_reason=None,
        capacity_raw_i32=1, count_raw_i32=1, data_pointer_present=True,
        matching_positions=[0] if i == 2 else [], subject_occurrence_count_i32=1 if i == 2 else 0)
        for i in range(30)]
    future = dict(schema_version=1, source="native_source_derived_next_daily_supply_frame_inputs_12004",
        stage="source_derived_conditional_next_date_pair", status="available", ready=True,
        unavailable_reason=None, subject_army_id_u32=18, subject_carmy_id_u32=18,
        current_date_storage_raw64=date, current_date_raw_i32=date, current_native_day_index_raw_i32=1,
        source_derived_next_date_raw_i32=date+24, source_derived_next_native_day_index_raw_i32=2,
        actual_future_date_stage_observed=False, actual_future_callback_observed=False,
        future_bucket_mutations_reconstructed=False, future_stock_or_strength_ready=False,
        full_daily_supply_transition_ready=False, full_monthly_ready=False)
    row = dict(status="available", army_id=18, native_carmy_id=18,
        current_supply_raw=10000000, current_supply_capacity_raw=10000000,
        current_supply_change_monthly_raw=-1000000,
        current_province_supply_contributors_v1=contributor,
        monthly_loss_budget_inputs_v1=dict(unit_native_170_raw=0, native_unit_in_combat=False,
            native_unit_gathering=False, army_gathering_count_raw=0),
        army_update_clock_v1=dict(status="available", ready=True, unavailable_reason=None,
            current_date_raw=date, native_day_index=1, selected_bucket_phase=1,
            observed_army_bucket_phase=2, last_supply_update_date_raw=date-720,
            grace_anchor_date_raw=date-48, loaded_grace_days=0,
            last_supply_update_date_storage_raw64=date-720, grace_anchor_date_storage_raw64=date-48),
        source_derived_next_daily_supply_frame_inputs_v1=future,
        future_daily_supply_schedule_inputs_v1=dict(schema_version=1,
            source="native_future_daily_supply_schedule_inputs_12004", stage="observed_current_all_phase_schedule",
            status="available", ready=True, unavailable_reason=None, subject_army_id_u32=18,
            subject_carmy_id_u32=18, current_date_storage_raw64=date, current_date_raw_i32=date,
            native_day_index_raw_i32=1, selected_phase_index_i32=1,
            secondary_identity="game_data_plus_2a548", phases=phases,
            actual_future_callback_observed=False, future_bucket_mutations_reconstructed=False,
            full_daily_supply_transition_ready=False, full_monthly_ready=False))
    return dict(army_query={**lease, "army_strengths":[row], "source":dict(game_version="1.20.0.4",
        executable_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518")}, snapshot=snapshot,
        sites=dict(candidates=[dict(province_id=2628), dict(province_id=2630)]),
        commands=[], active_wars=[], commander_queries=[],
        available_steps=["query-army-strengths-v1", "life-advance-one-day",
            "query-army-commander-candidates-v1-for-army-18", preview_move_army_step(18,2630)],
        army_ids=(18,))


def fixture(*,p=-200000,resupply=False,target=2630,usage=0,limit=1000,child=True):
    data=context();row=data['army_query']['army_strengths'][0]
    operands=dict(source='native_captured_target_loss_operands',scale=100000,status='available',
        observation_ready=True,unavailable_reason=None,commander_raw_full_id=9,
        commander_resolved_full_id=9,commander_used_native_fallback=False,
        commander_modifier_1a9_raw=0,loaded_excess_slope_raw=100,loaded_min_loss_raw=500000,
        loaded_max_loss_raw=1000000,loaded_divisor_floor_raw=10000)
    family=dict(source='native_captured_target_land_supply_inputs',input_basis='captured_owner_and_target_province',
        scale=100000,status='available',current_inputs_ready=True,unavailable_reason=None,
        subject_army_id=18,subject_carmy_id=18,owner_character_id=22,province_id=target,
        province_component_observation_ready=True,province_component_unavailable_reason=None,
        native_province_component_applicable=p!=0,province_component_raw=p,
        resupply_observation_ready=True,resupply_unavailable_reason=None,
        native_resupply_eligible=resupply,loaded_gain_raw=2000000)
    if child:family['loss_adjustment_operands_v1']=operands
    preview=dict(status='available',army_id=18,origin_province_id=2628,target_province_id=target,
        previewed_date_raw=data['snapshot']['date_raw'],route_province_ids=[target],
        province_supply=dict(status='available',army_id=18,native_carmy_id=18,owner_character_id=22,
            commander_character_id=9,target=dict(status='available',role='target',province_id=target,
                scale=1,native_supply_usage_soldiers=usage,native_supply_limit_soldiers=limit,
                captured_target_land_supply_inputs_v1=family)))
    return data,row,preview

class NewTargetCases(unittest.TestCase):
    def test_remote_add_once_same_province_no_double_add(self):
        _,r,p=fixture(usage=0,limit=100)
        value=project(r,p,same_frame_inputs=True)
        self.assertEqual(value['conditional_arrival_usage_soldiers'],100)
        self.assertEqual(value['excess_loss_raw'],0)
        self.assertEqual(value['conditional_full_land_rate_raw'],-200000)
        self.assertFalse(value['actual_target_monthly_observed'])
        _,r,p=fixture(target=2628,usage=100,limit=100)
        value=project(r,p,same_frame_inputs=True)
        self.assertEqual(value['conditional_arrival_usage_soldiers'],100)
        self.assertFalse(value['selected_supply_eligible_union'][0]['added_to_target_current_usage'])

    def test_boundary_overflow_and_new_negative_adjustment_paths(self):
        _,r,p=fixture(usage=1,limit=100)
        value=project(r,p,same_frame_inputs=True)
        self.assertEqual(value['excess_loss_raw'],500000)
        self.assertEqual(value['conditional_full_land_rate_raw'],-700000)
        x=p['province_supply']['target']['captured_target_land_supply_inputs_v1']['loss_adjustment_operands_v1']
        x['commander_modifier_1a9_raw']=54000
        self.assertEqual(project(r,p,same_frame_inputs=True)['conditional_full_land_rate_raw'],-454545)
        p['province_supply']['target']['native_supply_usage_soldiers']=(1<<31)-1
        self.assertIn('ordinary_arrival_usage_within_signed32',project(r,p,same_frame_inputs=True)['missing_inputs'])

    def test_missing_unused_M_is_not_missing_rate_and_missing_reached_M_stays_unknown(self):
        _,r,p=fixture(p=0,resupply=True,child=False)
        value=project(r,p,same_frame_inputs=True)
        self.assertEqual(value['conditional_full_land_rate_raw'],2000000)
        _,r,p=fixture(p=0,resupply=False,child=False)
        self.assertEqual(project(r,p,same_frame_inputs=True)['conditional_full_land_rate_raw'],0)
        _,r,p=fixture(child=False)
        value=project(r,p,same_frame_inputs=True)
        self.assertFalse(value['full_land_rate_ready'])
        self.assertIn('commander_modifier_1a9_raw',value['missing_inputs'])
        self.assertIsNone(value['conditional_full_land_rate_raw'])

    def test_complete_selected_union_and_shared_fullid_rejection(self):
        _,r,p=fixture(limit=150)
        second=copy.deepcopy(r);second.update(army_id=93,native_carmy_id=85)
        f=second['current_province_supply_contributors_v1'];f.update(subject_army_id=93,subject_carmy_id=85)
        f['occurrences'][0].update(army_id=93,native_carmy_id=85)
        with self.assertRaisesRegex(ValueError,'shares eligible'):
            project(r,p,same_frame_inputs=True,selected_rows=(r,second))
        f['occurrences'][0]['regiments'][0]['army_regiment_id']=13
        value=project(r,p,same_frame_inputs=True,selected_rows=(r,second))
        self.assertEqual(value['conditional_arrival_usage_soldiers'],200)
        self.assertEqual(value['excess_loss_raw'],500000)
        f['occurrences'][0]['native_eligible_current_soldiers']=101
        with self.assertRaisesRegex(ValueError,'flags2 count'):
            project(r,p,same_frame_inputs=True,selected_rows=(r,second))

    def test_lease_commander_and_child_type_reject(self):
        _,r,p=fixture()
        self.assertIn('same_paused_frame_query_and_preview_lease',project(r,p)['missing_inputs'])
        child=p['province_supply']['target']['captured_target_land_supply_inputs_v1']['loss_adjustment_operands_v1']
        child['commander_modifier_1a9_raw']=False
        with self.assertRaisesRegex(ValueError,'integer width'):project(r,p,same_frame_inputs=True)
        child['commander_modifier_1a9_raw']=0;child['commander_resolved_full_id']=10
        with self.assertRaisesRegex(ValueError,'raw/resolved FullID'):project(r,p,same_frame_inputs=True)

    def test_unreached_resupply_reader_is_not_required_over_limit(self):
        _,r,p=fixture(usage=1,limit=100)
        family=p['province_supply']['target']['captured_target_land_supply_inputs_v1']
        family.update(status='partial',current_inputs_ready=False,
            resupply_observation_ready=False,native_resupply_eligible=None,
            resupply_unavailable_reason='native_target_resupply_predicate_unavailable',
            unavailable_reason='native_target_resupply_predicate_unavailable')
        self.assertEqual(project(r,p,same_frame_inputs=True)['conditional_full_land_rate_raw'],-700000)
        p['province_supply']['target']['native_supply_limit_soldiers']=1000
        self.assertIn('native_resupply_eligible',project(r,p,same_frame_inputs=True)['missing_inputs'])

    def test_unwitnessed_modifier_and_conflicting_same_frame_loaded_values_reject(self):
        _,r,p=fixture()
        child=p['province_supply']['target']['captured_target_land_supply_inputs_v1']['loss_adjustment_operands_v1']
        child.update(status='unavailable',observation_ready=False,unavailable_reason='missing',
            commander_resolved_full_id=None)
        with self.assertRaisesRegex(ValueError,'resolved commander witness'):project(r,p,same_frame_inputs=True)
        child.update(status='available',observation_ready=True,unavailable_reason=None,commander_resolved_full_id=9)
        current=dict(source='native_current_province_land_supply_rate_inputs',status='not_land',
            unavailable_reason=None,current_observation_ready=False,scale=100000,
            subject_army_id=18,subject_carmy_id=18,owner_character_id=22,province_id=2628,
            commander_raw_full_id=None,commander_resolved_full_id=None,
            commander_used_native_fallback=None,native_land_branch_applicable=False,
            native_province_component_applicable=None,province_component_raw=None,
            commander_modifier_1a9_raw=None,loaded_excess_slope_raw=100,
            loaded_min_loss_raw=500000,loaded_max_loss_raw=999999,loaded_divisor_floor_raw=10000)
        r['current_land_supply_rate_inputs_v1']=current
        with self.assertRaisesRegex(ValueError,'loss operands disagree'):project(r,p,same_frame_inputs=True)

    def test_existing_decision_emits_normal_move_then_requires_readback(self):
        data,r,p=fixture()
        # Existing current site's actual rate is nonnegative; remote is a real
        # conditional negative trial, never copied from that current rate.
        r['current_supply_change_monthly_raw']=0
        data['sites']={'candidates':[{'province_id':2630}]}
        lease={k:v for k,v in data['army_query'].items() if k.startswith('queried_')}
        data['commands']=[dict(command=preview_move_army_step(18,2630),ok=True,result={**lease,'route_preview':p})]
        data['available_steps'].append(move_army_step(18,2630))
        value=strategy.plan_r05_zero_stock_preparation(**data)
        selected=value['r05_zero_stock_preparation_v1']['selected']
        self.assertIsNotNone(selected)
        self.assertEqual(value['selected_step'],move_army_step(18,2630))
        self.assertEqual(selected['successful_opportunities']['successful_bucket_occurrences'],50)
        self.assertIsNone(selected['observed_current_monthly_raw'])
        self.assertTrue(selected['actual_arrival_readback_required'])
        data['army_query']['queried_connection_generation']=99
        self.assertIsNone(strategy.plan_r05_zero_stock_preparation(**data)['r05_zero_stock_preparation_v1']['selected'])

    def test_native_divisor_zero_is_not_assumed_negative_loss(self):
        value=_project_land_rate_operands_v1(usage=0,limit=0,p=-200000,resupply=False,gain=None,
            operands=dict(loaded_divisor_floor_raw=0,commander_modifier_1a9_raw=-100000,loaded_max_loss_raw=1000000))
        self.assertEqual(value['conditional_full_land_rate_raw'],4294967295)
        self.assertEqual(value['division_path'],'zero_divisor_positive_u32_max')

