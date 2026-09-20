from __future__ import annotations

import unittest

import run_auto_upgrade_buildings_mcp_cost_probe as probe


class SemanticFrontendInspectionTest(unittest.TestCase):
    def test_reports_native_route_and_visible_overlay_without_ocr(self) -> None:
        summary = probe.summarize_frontend_inspection(
            {
                "scope_root_name": "frontend_bookmarks",
                "widget_count": 3,
                "uses_ocr": False,
                "uses_mouse": False,
                "uses_keyboard": False,
                "widgets": [
                    {
                        "runtime_name": "frontend_bookmarks",
                        "effective_visible": True,
                    },
                    {
                        "runtime_name": "dlc_list_overlay",
                        "effective_visible": True,
                    },
                    {
                        "runtime_name": "tutorial_prompt_overlay",
                        "effective_visible": False,
                    },
                ],
            }
        )

        self.assertEqual(summary["tree_route"], "bookmarks")
        self.assertEqual(summary["visible_blockers"], ["dlc_list_overlay"])
        self.assertIs(summary["uses_ocr"], False)
        self.assertIs(summary["uses_mouse"], False)
        self.assertIs(summary["uses_keyboard"], False)

    def test_malformed_inspection_fails_closed(self) -> None:
        self.assertEqual(
            probe.summarize_frontend_inspection("bridge unavailable"),
            {"tree_route": None, "visible_blockers": []},
        )


if __name__ == "__main__":
    unittest.main()
