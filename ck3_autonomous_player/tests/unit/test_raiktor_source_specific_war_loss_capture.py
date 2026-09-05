from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    CONTRACT,
    EXPECTED_ARM_SHA256,
    EXPECTED_EXE_SHA256,
    normalize_raiktor_source_specific_capture,
)


CONTRACT_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_source_specific_war_loss_attribution_v1_contract.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _capture() -> dict[str, object]:
    war_id = 50_331_699
    executions: list[dict[str, object]] = []
    for index in range(6):
        first_current = 20_000 + index * 10
        second_current = first_current + 1
        first_soldiers = 73 + index
        second_soldiers = 19 + index * 2
        executions.append(
            {
                "sequence": index + 1,
                "thread_id": 700 + index,
                "loaded_node": f"0x{0x1000 + index * 0x100:X}",
                "created_army": f"0x{0x9000 + index * 0x100:X}",
                "army_generation_id": 10_000 + index,
                "war_id": war_id,
                "initial_soldiers": first_soldiers + second_soldiers,
                "evaluated_name": "norman_highwaymen",
                "current_regiments": [
                    {
                        "generation_id": first_current,
                        "current_soldiers": first_soldiers,
                    },
                    {
                        "generation_id": second_current,
                        "current_soldiers": second_soldiers,
                    },
                ],
                "persistent_regiments": [
                    {
                        "generation_id": 30_000 + index * 10,
                        "war_id": war_id,
                        "current_regiment_ids": [first_current],
                    },
                    {
                        "generation_id": 30_001 + index * 10,
                        "war_id": war_id,
                        "current_regiment_ids": [second_current],
                    },
                ],
            }
        )
    return {
        "schema": "raiktor-war-bound-private-capture-v1",
        "status": "private_test_only",
        "result": "GREEN",
        "reason": "six-action-bound-source-executions-captured",
        "read_only": True,
        "public_bridge_abi_changed": False,
        "production_detour_installed": False,
        "readiness_promotion": False,
        "pid": 17292,
        "image_base": "0x140000000",
        "observation_stop_rva": "0x2E7F951",
        "observation_window_end_rva_exclusive": "0x2E7F9A6",
        "exe_sha256": EXPECTED_EXE_SHA256,
        "arm_proof_sha256": EXPECTED_ARM_SHA256,
        "event_definition_key": "bookmark.1071",
        "option_key": "bookmark.1071.a",
        "option_index": 0,
        "exact_raiktor_war_id": war_id,
        "source_execution_count": 6,
        "breakpoint_installed": True,
        "original_breakpoint_byte_restored": True,
        "process_terminated": False,
        "attach_mode": True,
        "debugger_detached": True,
        "executions": executions,
    }


class RaiktorSourceSpecificWarLossCaptureTests(unittest.TestCase):
    def test_six_execution_capture_normalizes_measured_source_set(self) -> None:
        capture = _capture()
        result = normalize_raiktor_source_specific_capture(
            capture, capture_sha256="A" * 64
        )
        source_set = result["source_set"]
        self.assertEqual(result["contract"], CONTRACT)
        self.assertEqual(source_set["war_id"], 50_331_699)
        self.assertEqual(len(source_set["executions"]), 6)
        self.assertEqual(len(source_set["persistent_generation_ids"]), 12)
        self.assertEqual(len(source_set["current_generation_ids"]), 12)
        expected_total = sum(
            row["initial_soldiers"] for row in capture["executions"]
        )
        self.assertEqual(source_set["measured_initial_soldiers"], expected_total)
        self.assertNotEqual(expected_total, 3000)
        self.assertTrue(result["readiness"]["source_origin_shape_ready"])
        self.assertFalse(result["readiness"]["private_live_evidence_classified"])
        self.assertFalse(result["readiness"]["source_specific_loss_ready"])
        self.assertFalse(result["readiness"]["comparison_input_ready"])

    def test_identity_or_generation_drift_is_rejected(self) -> None:
        for mutate in (
            lambda value: value["executions"][5].__setitem__(
                "loaded_node", value["executions"][0]["loaded_node"]
            ),
            lambda value: value["executions"][5].__setitem__("war_id", 7),
            lambda value: value["executions"][0]["persistent_regiments"][0].__setitem__(
                "current_regiment_ids", [999_999]
            ),
            lambda value: value["executions"][0].__setitem__(
                "initial_soldiers", 3000
            ),
        ):
            capture = deepcopy(_capture())
            mutate(capture)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                normalize_raiktor_source_specific_capture(
                    capture, capture_sha256="A" * 64
                )

    def test_generic_r3_rows_cannot_be_substituted_for_source_capture(self) -> None:
        capture = _capture()
        capture["event_definition_key"] = None
        capture["option_key"] = None
        capture["arm_proof_sha256"] = "B" * 64
        with self.assertRaises(ValueError):
            normalize_raiktor_source_specific_capture(
                capture, capture_sha256="A" * 64
            )

    def test_frozen_contract_pins_existing_default_off_capture(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["contract"], CONTRACT)
        self.assertTrue(contract["default_off"])
        self.assertFalse(contract["live_authorized"])
        self.assertFalse(contract["typed_output"]["comparison_input_ready"])
        self.assertFalse(contract["hard_boundaries"]["capture_live_executed"])
        self.assertEqual(
            contract["exact_observation"]["stop_rva"], "0x2E7F951"
        )
        self.assertEqual(
            contract["exact_observation"]["window_end_rva_exclusive"],
            "0x2E7F9A6",
        )
        for name in (
            "spawn_army_abi",
            "spawn_army_verifier",
            "capture_source",
            "capture_manifest",
            "cmake",
            "provider",
            "preflight",
        ):
            path = ROOT.parent / contract["paths"][name]
            self.assertEqual(_sha256(path), contract["sha256"][name])


if __name__ == "__main__":
    unittest.main()
