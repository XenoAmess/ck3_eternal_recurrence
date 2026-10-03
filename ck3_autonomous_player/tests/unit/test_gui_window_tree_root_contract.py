"""Fixed native root identity must survive generic validation projection."""
from copy import deepcopy
import unittest
from xar_autoplayer.bridge.gui_window_tree_contract import normalize_gui_window_tree_v1

class GuiWindowTreeRootTests(unittest.TestCase):
    def test_wrong_actual_root_row_is_rejected(self):
        raw = {"step": "inspect-gui-window-tree-v1", "accepted": True,
               "status": "available", "scope_root_name": "decisions_view",
               "root_available": True, "truncated": False, "widget_count": 1,
               "widgets": [{"runtime_name": "decisions_view", "child_path": "", "depth": 0,
                            "child_count": 0, "vtable_rva": 1,
                            "effective_visible": True, "enabled": True}]}
        self.assertEqual(normalize_gui_window_tree_v1(raw, "decisions")["scope_root_name"], "decisions_view")
        wrong = deepcopy(raw)
        wrong["widgets"][0]["runtime_name"] = "different_native_window"
        with self.assertRaises(ValueError):
            normalize_gui_window_tree_v1(wrong, "decisions")
