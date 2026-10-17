"""Four behavior cases for the fixed checkbox; no SDK or native game calls."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import military_reinforcement_12004 as action
from xar_autoplayer.bridge import military_reinforcement_12004_contract as contract
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import SOURCE_RECEIVER_12004


def snapshot():
    return dict(snapshot_id="native:109", revision=110, native_revision=109,
                episode_run_id="native-31254-test", paused=True, map_ready=True, date_raw=53148960,
                played_character=dict(character_id=31254, alive=True),
                diagnostics=dict(bridge_pid=29000, connection_generation=1,
                    hello=dict(pid=29000, expected_ck3_version="1.20.0.4",
                               expected_ck3_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
                               ck3_build_match=True, game_adapter_id="ck3-1.20.0.4-msvc-x64")))


def switch(raw):
    return dict(source="native_gui_type635_static_direct_owner_switch_12004",
                scope="static_direct_source_candidate", status="available", unavailable_reason=None,
                current_variable_table_observed=False, native_receiver_selected=False, provider_invoked=False,
                ancestor_depth=8, owner_full_id=31254, military_component_present=raw is not None,
                raw_byte_4a9=raw, enabled=raw is not None and raw != 0,
                value_basis="native_null_military_zero" if raw is None else "raw_military_byte",
                stable_double_read=True)


def entry(depth=0):
    return dict(ancestor_depth=depth, entry_type_48=635, entry_mode_40=0, entry_flag_4c=0,
                direct_value_present=False, provider_present=False, provider_vtable_rva=None,
                provider_slot2_rva=None, direct_owner_full_id=None, direct_owner_identity_verified=False)


def census(raw):
    local = dict(source="native_gui_type635_local_definition_entry_only_12004", scope="local_definition_entry_only",
        status="available", unavailable_reason=None, receiver_type_id=635, ancestor_depth=0,
        current_variable_table_observed=False, native_receiver_selected=False, receiver_variable_index=0,
        declared_type_id=635, raw_definition_entry_count=1, local_definition_active_raw=1, definition_present=True,
        local_entry_present=True, stable_double_read=True, entries=[entry()])
    prefix = dict(source="native_gui_type635_definition_chain_prefix_depth8_12004", scope="visited_definition_prefix_depth8",
        status="available", unavailable_reason=None, receiver_type_id=635, depth_limit=8, walk_complete=False,
        current_variable_table_observed=False, native_receiver_selected=False, receiver_variable_index=0,
        declared_type_id=635, frontier_depth=8, frontier_context_present=True, stable_double_read=True,
        rows=[dict(ancestor_depth=i, definition_present=True, raw_definition_entry_count=1 if i == 0 else 0,
            entries=[entry()] if i == 0 else [], parent_edge="context_e8", parent_present=True) for i in range(8)])
    direct = entry(8)
    direct.update(entry_mode_40=1, entry_flag_4c=1, direct_value_present=True,
                  direct_owner_full_id=31254, direct_owner_identity_verified=True)
    tail = dict(source="native_gui_type635_frontier_continuation_depth8_12_12004", scope="definition_frontier_depth8_through11",
        status="available", unavailable_reason=None, receiver_type_id=635, start_depth=8, depth_limit=12,
        current_variable_table_observed=False, native_receiver_selected=False, provider_invoked=False,
        receiver_variable_index=0, declared_type_id=635, stop_depth=8, stop_reason="static_direct_terminal",
        next_context_present=None, stable_double_read=True,
        rows=[dict(ancestor_depth=8, definition_present=True, raw_definition_entry_count=3, first_match_entry_index=0,
                   entries=[direct], parent_edge="not_read_native_static_stop", parent_present=None)],
        static_direct_owner_switch_12004=switch(raw))
    diagnostic = dict(stage="parent_walk", kind="parent_depth_exhausted", capture_pass=1, read_ordinal=51,
        ancestor_depth=8, raw_declaration_count=1, raw_index_count=1, raw_definition_entry_count=None,
        context_present=True, definition_present=None, local_definition_active_raw=1)
    candidate = dict(source="native_gui_type635_definition_candidates_12004", status="unavailable",
        unavailable_reason="candidate_parent_depth_exhausted", receiver_type_id=635,
        current_variable_table_observed=False, native_receiver_selected=False, receiver_variable_index=None,
        declared_type_id=None, stable_double_read=False, entries=[], failure_diagnostic=diagnostic,
        local_definition_entry_only=local, definition_chain_prefix_depth8=prefix,
        definition_frontier_continuation_depth8_12=tail)
    expression = dict(chain_count_24_raw=0, final_type_id_30=1, final_kind_34_raw=3,
        final_target_38_rva=0x1303D40, final_user_data_40_present=True, receiver_type_id_48=635,
        receiver_flag_4c_raw=0, chain_calls=[], receiver_entry_candidates_12004=candidate)
    callback = dict(index=0, callback_vtable_rva=0x40000, callback_slot2_rva=0x3AA30E0,
        indirect_target_3aa30e0=dict(native_target_8_rva=0x3A9F960, receiver_f0_present=True,
                                   expression_3a9f960=expression))
    target = "0/0/0/2/3/0/0/0"
    paths = [""] + ["/".join(target.split("/")[:n]) for n in range(1, 9)]
    names = {"": "military_view", "0/0/0/2": "tab_your_armies", "0/0/0/2/3": "footer"}
    rows = [dict(runtime_name=names.get(p, ""), child_path=p, depth=0 if p == "" else p.count("/") + 1,
        child_count=0 if p == target else 1, vtable_rva=0x50000, effective_visible=True, enabled=True,
        standard_click_binding_12004=dict(button_base_slot13=p == target,
            group="fallback" if p == target else "not_button_base", callbacks=[callback] if p == target else [])) for p in paths]
    frame = dict(native_revision=109, connection_generation=1, pump_epoch=96426, ticket_sequence=65,
        game_pid=29000, thread_id=29904, played_character_full_id=31254, date_raw=53148960,
        owner_thread_verified=True, frame_stable=True, gui_owner_stable=True)
    return dict(step="inspect-gui-window-tree-v1", accepted=True, status="available", scope_root_name="military_view",
                root_available=True, truncated=False, widget_count=len(rows), widgets=rows,
                callback_binding_source_12004=SOURCE_RECEIVER_12004, refill_receiver_frame_12004=frame)


def ack(raw, desired):
    binding = contract.reinforcement_binding(snapshot())
    observed = contract.observe_fixed_reinforcement(census(raw), snapshot(), snapshot())
    result = {key: True for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified",
        "gui_owner_binding_verified", "source_profile_verified", "current_tree_complete", "no_blocking_modal_verified")}
    attempted = observed["switch"]["enabled"] is not desired
    result.update(binding)
    result.pop("episode_run_id")
    result.update(schema=contract.SCHEMA, step=contract.step_for_desired(desired), accepted=True,
        unavailable_reason=None,
        status="acknowledged_verification_pending" if attempted else "noaction_already_desired",
        desired_enabled=desired, game_version="1.20.0.4",
        executable_sha256=snapshot()["diagnostics"]["hello"]["expected_ck3_sha256"],
        source_child_path=observed["source_child_path"], source_gui_sha256=contract.GUI_SHA256,
        before_switch=switch(raw), dispatch_attempted=attempted, dispatch_invoked=attempted,
        native_handled=False, postcondition_verified=False, verification_pending=True,
        current_variable_table_observed=False, native_receiver_selected=False, provider_invoked=False)
    return result


class Driver:
    def __init__(self, directory, before, later, desired):
        self.directory, self.before, self.later, self.desired = directory, before, later, desired
        self.sent, self.census_reads = [], 0

    def take_snapshot(self):
        return snapshot()

    def capabilities(self):
        return {"bridge_capabilities": ["game.command." + step for step in contract.STEPS]}

    def _native_driver_state_path(self):
        return Path(self.directory) / "driver.json"

    def inspect_gui_window_tree_v1(self, window_kind):
        assert window_kind == "military"
        self.census_reads += 1
        tree = census(self.before if self.census_reads == 1 else self.later)
        tree["refill_receiver_frame_12004"]["ticket_sequence"] += self.census_reads
        return tree

    def _execute_primitive_step(self, step, **kwargs):
        self.sent.append((step, kwargs))
        return ack(self.before, self.desired)


class MilitaryReinforcementTests(unittest.TestCase):
    def test_native_ack_false_handled_needs_later_same_owner_nonzero_byte(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = Driver(temporary, 0, 2, True)
            result = action.set_fixed_military_reinforcement_12004(driver, desired_enabled=True, expected_revision=110)
            self.assertEqual(result["status"], "verified_desired")
            self.assertTrue(result["postcondition_verified"])
            self.assertEqual(result["later_observation"]["switch"]["raw_byte_4a9"], 2)
            self.assertFalse(result["native_ack"]["native_handled"])
            self.assertEqual((len(driver.sent), driver.census_reads), (1, 2))

    def test_unchanged_later_byte_stays_pending_and_blocks_opposite_direction(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(action, "VERIFICATION_TIMEOUT_SECONDS", 0):
            driver = Driver(temporary, 1, 1, False)
            result = action.set_fixed_military_reinforcement_12004(driver, desired_enabled=False)
            self.assertFalse(result["postcondition_verified"])
            self.assertTrue(result["verification_pending"])
            self.assertEqual(result["status"], "acknowledged_verification_pending")
            with self.assertRaisesRegex(BridgeUnavailableError, "unresolved result"):
                action.set_fixed_military_reinforcement_12004(driver, desired_enabled=True)
            self.assertEqual((len(driver.sent), driver.census_reads), (1, 2))

    def test_null_military_false_is_already_desired_only_after_independent_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = Driver(temporary, None, None, False)
            result = action.set_fixed_military_reinforcement_12004(driver, desired_enabled=False)
            self.assertEqual(result["status"], "verified_already_desired")
            self.assertFalse(result["dispatch_attempted"])
            self.assertIsNone(result["later_observation"]["switch"]["raw_byte_4a9"])
            self.assertEqual(driver.census_reads, 2)

    def test_fresh_source_owner_frame_and_ack_contradictions_are_rejected(self):
        initial = snapshot()
        for mutation in ("owner", "frame", "hidden", "ancestor", "duplicate"):
            tree = census(1)
            if mutation == "owner":
                expression = tree["widgets"][-1]["standard_click_binding_12004"]["callbacks"][0]["indirect_target_3aa30e0"]["expression_3a9f960"]
                expression["receiver_entry_candidates_12004"]["definition_frontier_continuation_depth8_12"]["static_direct_owner_switch_12004"]["owner_full_id"] = 31255
            elif mutation == "frame": tree["refill_receiver_frame_12004"]["game_pid"] += 1
            elif mutation == "hidden": tree["widgets"][-1]["effective_visible"] = False
            elif mutation == "ancestor": tree["widgets"][4]["runtime_name"] = "other_tab"
            else:
                tree["widgets"].append(copy.deepcopy(tree["widgets"][-1])); tree["widget_count"] += 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                contract.observe_fixed_reinforcement(tree, initial, initial)
        before = contract.observe_fixed_reinforcement(census(0), initial, initial)
        binding = contract.reinforcement_binding(initial)
        for mutation in ({"postcondition_verified": True}, {"native_receiver_selected": True},
                         {"dispatch_attempted": False}, {"desired_enabled": 1}):
            raw = ack(0, True); raw.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                contract.normalize_reinforcement_ack(raw, binding, True, before)


if __name__ == "__main__":
    unittest.main()
