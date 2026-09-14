from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_index7_targeted_readiness300.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_index7_targeted_readiness300_v1.json"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("g2_index7_readiness300", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load preflight module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class G2Index7Readiness300PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_freezes_distinct_300_second_budget(self) -> None:
        self.module.validate_manifest_contract(self.manifest)
        self.assertEqual(self.manifest["timeouts"]["readiness_seconds"], 300.0)
        self.assertEqual(
            self.manifest["evidence"]["failed_attempt_session_seconds"],
            122.731,
        )
        self.assertEqual(
            self.manifest["evidence"]["same_checkpoint_green_control_seconds"],
            205.7,
        )

    def test_python_launch_plan_is_fresh_index7_only_and_explicit(self) -> None:
        plan = self.module.build_python_launch_plan(self.manifest)
        argv = plan["argv"]
        self.assertEqual(plan["schema"], "xar.ck3.python_launch_plan.v1")
        self.assertEqual(
            sum("run_war_termination_terms_live_acceptance.py" in item for item in argv),
            1,
        )
        self.assertEqual(argv.count("--readiness-timeout"), 1)
        self.assertEqual(argv[argv.index("--readiness-timeout") + 1], "300")
        self.assertEqual(argv[argv.index("--timeout") + 1], "420")
        self.assertIn(
            "g2-index7-private-v2.jsonl",
            next(iter(plan["environment"].values())),
        )
        command = " ".join(argv)
        self.assertNotIn(
            "surrender",
            command.lower().replace("run_war_termination_terms_live_acceptance.py", ""),
        )
        self.assertNotIn("white-peace", command.lower())
        self.assertNotIn("enforce", command.lower())

    def test_manifest_keeps_private_and_production_boundaries_closed(self) -> None:
        private = self.manifest["private_capture"]
        boundaries = self.manifest["boundaries"]
        self.assertEqual(private["root_index"], 7)
        self.assertEqual(private["schema"], "xar.ck3.g2_truce_private_capture.v2")
        self.assertTrue(boundaries["index7_only"])
        self.assertTrue(boundaries["duration_input_address_only"])
        self.assertFalse(boundaries["evaluator_called"])
        self.assertFalse(boundaries["mutation_enabled"])
        self.assertFalse(boundaries["public_abi_changed"])
        self.assertFalse(boundaries["readiness_changed"])
        self.assertFalse(boundaries["production_shape_contract_changed"])

    def test_preflight_source_has_no_launch_surface(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "subprocess",
            "NativeHeadlessGameplayDriver",
            "native_session(",
            "Start" + "-Process",
            "Popen(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
