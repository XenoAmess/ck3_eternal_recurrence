"""Source-bound military census rejects aliases and unsafe callback targets."""
from copy import deepcopy
import unittest
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import SOURCE_12004
from xar_autoplayer.bridge.gui_window_tree_contract import normalize_gui_window_tree_v1


class MilitaryCallbackBinding12004Tests(unittest.TestCase):
    def raw(self, primary=True):
        return {"step": "inspect-gui-window-tree-v1", "accepted": True,
                "status": "available", "scope_root_name": "military_view",
                "root_available": True, "truncated": False, "widget_count": 2,
                "callback_binding_source_12004": dict(SOURCE_12004),
                "widgets": [
                    {"runtime_name": "military_view", "child_path": "", "depth": 0,
                     "child_count": 1, "vtable_rva": 0x1000, "effective_visible": True,
                     "enabled": True, "standard_click_binding_12004": {
                         "button_base_slot13": False, "group": "not_button_base", "callbacks": []}},
                    {"runtime_name": "", "child_path": "0", "depth": 1,
                     "child_count": 0, "vtable_rva": 0x2000, "effective_visible": True,
                     "enabled": True, "standard_click_binding_12004": {
                         "button_base_slot13": True, "group": "primary" if primary else "fallback",
                         "callbacks": [{"index": 0, "callback_vtable_rva": 0x3000,
                                        "callback_slot2_rva": 0x4000}]}}]}

    def test_both_source_group_routes_preserve_order_without_naming_callback(self):
        for primary in (True, False):
            result = normalize_gui_window_tree_v1(self.raw(primary), "military")
            self.assertEqual(result["widgets"][1]["standard_click_binding_12004"]["callbacks"][0]["callback_slot2_rva"], 0x4000)
            self.assertFalse(result["callback_method_name_available"])
            self.assertFalse(result["click_action_available"])

    def test_missing_window_is_observed_with_source_identity(self):
        raw = self.raw(); raw.update(root_available=False, status="unavailable", widget_count=0, widgets=[])
        self.assertFalse(normalize_gui_window_tree_v1(raw, "military")["root_available"])

    def test_old_build_or_modified_dispatch_mode_is_rejected(self):
        for key, value in (("executable_sha256", "2d00ff"), ("button_base_slot13_rva", 0x36D14C0),
                           ("input_modifier", 1), ("input_modifier", False)):
            with self.subTest(key=key, value=value):
                raw = self.raw(); raw["callback_binding_source_12004"][key] = value
                with self.assertRaises(ValueError): normalize_gui_window_tree_v1(raw, "military")

    def test_incomplete_census_or_missing_leaf_is_rejected(self):
        for mutate in (lambda r: r.update(truncated=True),
                       lambda r: r.update(root_available=False, status="unavailable"),
                       lambda r: r["widgets"][1].update(vtable_rva=0x61C5000),
                       lambda r: r["widgets"][1].pop("standard_click_binding_12004")):
            raw = self.raw(); mutate(raw)
            with self.assertRaises(ValueError): normalize_gui_window_tree_v1(raw, "military")

    def test_foreign_pointer_bool_and_noncontiguous_row_are_rejected(self):
        for key, value in (("callback_slot2_rva", 0), ("callback_slot2_rva", 0x61C5000),
                           ("callback_vtable_rva", 0x61C5000-23),
                           ("callback_slot2_rva", True), ("index", 1)):
            with self.subTest(key=key, value=value):
                raw = self.raw(); raw["widgets"][1]["standard_click_binding_12004"]["callbacks"][0][key] = value
                with self.assertRaises(ValueError): normalize_gui_window_tree_v1(raw, "military")

    def test_nonbutton_or_empty_primary_cannot_claim_callbacks(self):
        for mutate in (lambda b: b.update(button_base_slot13=False), lambda b: b.update(callbacks=[])):
            raw=self.raw(); mutate(raw["widgets"][1]["standard_click_binding_12004"])
            with self.assertRaises(ValueError): normalize_gui_window_tree_v1(raw, "military")

    def test_unnamed_callback_cannot_assert_named_semantics(self):
        raw=self.raw(); raw["widgets"][1]["standard_click_binding_12004"]["method_name"]="MilitaryView.OnMilitaryReinforcementClick"
        with self.assertRaises(ValueError): normalize_gui_window_tree_v1(raw, "military")

    def test_other_scope_cannot_carry_military_target_leaf(self):
        raw=self.raw(); raw["scope_root_name"]="decisions_view"; raw["widgets"][0]["runtime_name"]="decisions_view"
        with self.assertRaises(ValueError): normalize_gui_window_tree_v1(raw, "decisions")
