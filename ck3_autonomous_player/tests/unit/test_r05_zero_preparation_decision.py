"""New R05 candidate/decision behavior checks; no old fixture execution."""
from copy import deepcopy
import unittest

from xar_autoplayer.strategy import plan_r05_zero_stock_preparation
from xar_autoplayer.bridge.army_zero_stock_clock_12004 import successful_supply_occurrences_to_zero_12004
from xar_autoplayer.bridge.war_contract import preview_move_army_step


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


class R05ZeroPreparationTests(unittest.TestCase):
    def test_cap_clamps_after_add_and_first_zero_is_same_invocation(self):
        estimate=successful_supply_occurrences_to_zero_12004(30000000,10000000,-1000000)
        self.assertEqual(estimate["first_successful_post_stock_raw"],10000000)
        self.assertEqual(estimate["successful_bucket_occurrences"],11)
        self.assertIsNone(estimate["actual_days"])
        one=successful_supply_occurrences_to_zero_12004(10,100,-10)
        self.assertEqual(one["successful_bucket_occurrences"],1)
        self.assertTrue(one["first_zero_same_invocation_can_apply_supply_loss"])

    def test_missing_nonnegative_boolean_rates_never_get_default_loss(self):
        for rate in (None,0,20,False,0.0):
            value=successful_supply_occurrences_to_zero_12004(100,100,rate)
            self.assertFalse(value["ready"])
            self.assertIsNone(value["successful_bucket_occurrences"])
        zero=successful_supply_occurrences_to_zero_12004(0,100,-1)
        self.assertEqual(zero["successful_bucket_occurrences"],0)
        self.assertEqual(zero["first_new_zero_writer_opportunity"],1)

    def test_existing_strategy_entry_selects_verified_current_context_only(self):
        value=plan_r05_zero_stock_preparation(**context())
        selected=value["r05_zero_stock_preparation_v1"]["selected"]
        self.assertEqual(selected["province_id"],2628)
        self.assertEqual(selected["successful_opportunities"]["successful_bucket_occurrences"],10)
        self.assertEqual(value["selected_step"],"life-advance-one-day")
        self.assertFalse(value["r05_zero_stock_preparation_v1"]["shortest_actual_calendar_preparation_ready"])

    def test_negative_current_rate_is_not_pasted_to_remote_site(self):
        inputs=context()
        lease={key:value for key,value in inputs["army_query"].items() if key.startswith("queried_")}
        inputs["commands"]=[dict(command=preview_move_army_step(18,2630),ok=True,result={**lease,
            "route_preview":dict(status="available",army_id=18,origin_province_id=2628,
                target_province_id=2630,previewed_date_raw=43800024,route_province_ids=[2628,2630])})]
        value=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
        remote=next(row for row in value["candidates"] if row["province_id"]==2630)
        self.assertIsNone(remote["observed_current_monthly_raw"])
        self.assertFalse(remote["ready"])
        self.assertIn("actual_target_arrival_ArmyStrength.current_supply_change_monthly_raw",remote["required_fields"])
        self.assertEqual(remote["native_route_hops"],1)

    def test_actual_route_conflict_and_stale_generation_are_rejected(self):
        inputs=context()
        inputs["active_wars"]=[dict(enemy_armies=[dict(army_id=99,current_province_id=2628,
            move_target_province_id=None,route_province_ids=[],army_state="idle")])]
        value=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
        self.assertIsNone(value["selected"])
        self.assertIn("ordinary_war_route_audit_unsafe",value["candidates"][0]["rejected_reasons"])
        inputs=context()
        inputs["army_query"]["queried_connection_generation"]=2
        self.assertIsNone(plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]["selected"])

    def test_event_nonreinforcement_does_not_replace_supply_qualification(self):
        inputs=context()
        row=inputs["army_query"]["army_strengths"][0]
        row.pop("current_province_supply_contributors_v1")
        row["can_replenish"]=False
        row["guard138"]=1
        value=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
        self.assertIsNone(value["selected"])
        self.assertIn("current_province_supply_contributors_v1.subject_native_eligible_current_soldiers",value["required_fields"])

    def test_candidate_zero_is_never_unassignment_and_capacity_is_not_invented(self):
        inputs=context()
        lease={key:value for key,value in inputs["army_query"].items() if key.startswith("queried_")}
        family=dict(army_id=18,native_carmy_id=18,current_commander=dict(character_id=9),
            candidates=[dict(character_id=character,available=True,final_eligibility_observable=True,
                can_assign=True) for character in (0,9,10)])
        inputs["commander_queries"]=[{**lease,"army_commander_candidates":family}]
        selected=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]["selected"]
        self.assertEqual([value["character_id"] for value in selected["lower_capacity_probe_candidates"]],[10])
        self.assertFalse(selected["lower_capacity_probe_candidates"][0]["actual_lower_capacity_ready"])

    def test_next_gate_reject_and_all_static_sites_cannot_become_prepared(self):
        inputs=context()
        inputs["army_query"]["army_strengths"][0]["monthly_loss_budget_inputs_v1"]["native_unit_in_combat"]=True
        self.assertIsNone(plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]["selected"])
        result=plan_r05_zero_stock_preparation(army_query=dict(rows=[dict(army_id=18,
            native_carmy_id=18,status="available",current_supply_raw=30000000,
            current_supply_capacity_raw=30000000,current_supply_change_monthly_raw=0)]),
            sites=dict(candidates=[dict(province_id=2602,terrain="mountains",safe=True,
                monthly_supply_change=-10)]), available_steps=["query-army-strengths-v1"],army_ids=(18,))
        self.assertIsNone(result["r05_zero_stock_preparation_v1"]["selected"])
        self.assertEqual(result["selected_step"],"query-army-strengths-v1")

    def test_exact_source_binding_delta_rejects_old_or_missing_build(self):
        inputs=context()
        good=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
        self.assertIsNotNone(good["selected"])
        for source in (None,dict(game_version="1.20.0.3",executable_sha256="legacy")):
            with self.subTest(source=source):
                inputs["army_query"]["source"]=source
                result=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
                self.assertIsNone(result["selected"])
                self.assertIn("army_query.source.exact_1_20_0_4_executable_binding",result["required_fields"])

    def test_complete_subject_witness_survives_unrelated_partial_province(self):
        inputs=context()
        contributor=inputs["army_query"]["army_strengths"][0]["current_province_supply_contributors_v1"]
        contributor.update(status="partial",contributors_ready=False,
            unavailable_reason="unrelated_stale_Province_occurrence",native_province_unit_count=2)
        contributor["occurrences"].append(dict(stored_index=1,army_id=99,status="unavailable",
            unavailable_reason="unrelated_stale_generation",owner_character_id=None,included=None,
            inclusion_basis=None,native_carmy_id=None,native_eligible_current_soldiers=None,regiments=[]))
        value=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
        self.assertIsNotNone(value["selected"])
        self.assertEqual(value["selected"]["supply_eligible_current_soldiers"],100)
        inputs["snapshot"]=None
        value=plan_r05_zero_stock_preparation(**inputs)["r05_zero_stock_preparation_v1"]
        current=next(row for row in value["candidates"] if row["province_id"]==2628)
        self.assertEqual(current["observed_current_monthly_raw"],-1000000)
        self.assertEqual(current["supply_eligible_current_soldiers"],100)
        self.assertIsNone(value["selected"])


if __name__=="__main__":
    unittest.main()
