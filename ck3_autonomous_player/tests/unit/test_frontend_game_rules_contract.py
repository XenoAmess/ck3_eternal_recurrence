from __future__ import annotations

import ast
import copy
from pathlib import Path
import runpy
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = runpy.run_path(str(PROJECT_ROOT / "src/xar_autoplayer/bridge/frontend_game_rules_contract.py"))
normalize = CONTRACT["normalize_frontend_game_rule_selections_v1"]


def observed_off() -> dict[str, object]:
    return {
        "schema": "frontend_game_rule_selections_v1", "schema_version": 1,
        "game_version": "1.20.0.3",
        "executable_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
        "source": "CJominiGameRulesGui.current_selections", "read_only": True,
        "uses_ocr": False, "uses_mouse": False, "uses_keyboard": False,
        "applied_settings_proven": False, "ready": True, "unavailable_reason": "",
        "selection_count": 1,
        "selections": [{"rule_key": "zg361_enabled", "selected_setting_key": "zg361_off"}],
        "backend_id": "native-headless",
    }


class FrontendGameRulesContractTests(unittest.TestCase):
    def test_actual_off_and_unavailable_are_preserved(self) -> None:
        row = observed_off()
        self.assertEqual(normalize(row)["selections"][0]["selected_setting_key"], "zg361_off")
        unavailable = {**row, "ready": False, "unavailable_reason": "visible_game_rules_root_unverified",
                       "selection_count": 0, "selections": []}
        self.assertIs(normalize(unavailable)["ready"], False)

    def test_eight_malformed_native_observations_are_rejected(self) -> None:
        for patch in [{"game_version": "1.20.0.2"}, {"uses_ocr": True},
                      {"applied_settings_proven": True}, {"selection_count": 2},
                      {"ready": False}, {"selection_count": True},
                      {"selections": [{"rule_key": "zg361_enabled", "selected_setting_key": "guessed value"}]},
                      {"schema_version": True}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                normalize({**observed_off(), **patch})

    def test_candidate_driver_returns_actual_off_under_one_frontend_request(self) -> None:
        driver = ast.parse((PROJECT_ROOT / "src/xar_autoplayer/bridge/native_driver.py").read_text(encoding="utf-8-sig"))
        method = next(n for n in ast.walk(driver) if isinstance(n, ast.FunctionDef)
                      and n.name == "query_frontend_game_rule_selections_v1")
        classnode = ast.ClassDef(name="Harness", bases=[], keywords=[], body=[copy.deepcopy(method)], decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[classnode], type_ignores=[]))
        binding = {"bridge_pid": 123, "connection_generation": 1}
        namespace = {**CONTRACT, "BridgeUnavailableError": RuntimeError,
                     "frontend_gui_route_binding_from_capabilities": lambda value: value["binding"]}
        exec(compile(module, "native_driver_game_rules_query", "exec"), namespace)
        harness = namespace["Harness"]()
        harness._request_sequence = 7
        harness.capabilities = lambda: {"binding": binding}
        calls = []
        def primitive(step, **kwargs):
            calls.append((step, kwargs))
            return copy.deepcopy(observed_off())
        harness._execute_primitive_step = primitive
        result = harness.query_frontend_game_rule_selections_v1()
        self.assertEqual(result["selections"][0]["selected_setting_key"], "zg361_off")
        self.assertEqual(result["binding"], binding)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["expected_revision"], 0)
        self.assertIs(calls[0][1]["allow_frontend_revision_zero"], True)


if __name__ == "__main__":
    unittest.main()
