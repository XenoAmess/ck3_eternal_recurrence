"""Only the new fixed topbar scope: complete actual-root census or reject."""
from copy import deepcopy
import unittest
from xar_autoplayer.bridge.gui_window_tree_contract import normalize_gui_window_tree_v1

class IngameTopbarScopeTests(unittest.TestCase):
    def raw(self):
        return {"step": "inspect-gui-window-tree-v1", "accepted": True,
                "status": "available", "scope_root_name": "ingame_topbar",
                "root_available": True, "truncated": False, "widget_count": 1,
                "widgets": [{"runtime_name": "ingame_topbar", "child_path": "", "depth": 0,
                             "child_count": 0, "vtable_rva": 1,
                             "effective_visible": True, "enabled": True}]}

    def test_actual_fixed_topbar_scope_is_read_only(self):
        result = normalize_gui_window_tree_v1(self.raw(), "ingame_topbar")
        self.assertEqual(result["window_kind"], "ingame_topbar")
        self.assertEqual(result["scope_root_name"], "ingame_topbar")
        self.assertTrue(result["read_only"])
        self.assertFalse(result["business_model_available"])

    def test_wrong_actual_topbar_root_is_rejected(self):
        raw = self.raw()
        raw["widgets"][0]["runtime_name"] = "tab_decisions"
        with self.assertRaises(ValueError):
            normalize_gui_window_tree_v1(raw, "ingame_topbar")

    def test_incomplete_topbar_census_is_rejected(self):
        raw = self.raw()
        for missing in (True, None):
            with self.subTest(truncated=missing):
                candidate = deepcopy(raw)
                candidate["truncated"] = missing
                with self.assertRaises(ValueError):
                    normalize_gui_window_tree_v1(candidate, "ingame_topbar")
