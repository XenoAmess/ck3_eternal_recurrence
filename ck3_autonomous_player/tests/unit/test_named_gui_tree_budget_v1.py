"""One focused Python DTO boundary for the larger native tree census."""
import unittest
from xar_autoplayer.bridge.frontend_gui_route_contract import (
    INSPECT_FRONTEND_GUI_TREE_V1_MAXIMUM_WIDGETS,
    normalize_frontend_gui_tree_inspection_v1,
)

class NamedGuiTreeBudgetTests(unittest.TestCase):
    def test_bounded_rows_and_honest_truncation(self):
        def tree(count, truncated=False):
            return {"step": "inspect-frontend-gui-tree-v1", "accepted": True,
                "status": "available", "scope_root_name": "frontend_bookmarks",
                "root_available": True, "truncated": truncated, "widget_count": count,
                "widgets": [{"runtime_name": "frontend_bookmarks" if i == 0 else "node",
                    "child_path": "" if i == 0 else str(i - 1), "depth": 0 if i == 0 else 1,
                    "child_count": count - 1 if i == 0 else 0, "vtable_rva": 1,
                    "effective_visible": True, "enabled": True} for i in range(count)]}
        self.assertEqual(INSPECT_FRONTEND_GUI_TREE_V1_MAXIMUM_WIDGETS, 2048)
        self.assertEqual(normalize_frontend_gui_tree_inspection_v1(tree(2048))["widget_count"], 2048)
        with self.assertRaises(ValueError):
            normalize_frontend_gui_tree_inspection_v1(tree(2049))
        # A partial DTO is observable; it remains explicitly truncated.
        self.assertTrue(normalize_frontend_gui_tree_inspection_v1(tree(2048, True))["truncated"])
