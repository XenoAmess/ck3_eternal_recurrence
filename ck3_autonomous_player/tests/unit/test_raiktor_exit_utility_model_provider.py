from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.raiktor_exit_utility_model_provider import (
    DEFAULT_BUDGET_PATH,
    DEFAULT_MODEL_PATH,
    ExitUtilityModelError,
    MODEL_CONTRACT,
    PROVIDER_SCHEMA,
    SOURCE_CONTRACT,
    provide_raiktor_exit_utility_model,
    render_raiktor_exit_utility_model,
)


class RaiktorExitUtilityModelProviderTests(unittest.TestCase):
    def test_repository_default_is_complete_and_byte_bound(self) -> None:
        result = provide_raiktor_exit_utility_model()
        payload = DEFAULT_MODEL_PATH.read_bytes()

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["default_source_used"])
        self.assertEqual(result["source_kind"], "repository_default")
        self.assertTrue(result["model_production_eligible"])
        self.assertEqual(result["provider_blockers"], [])
        self.assertEqual(
            result["source"]["sha256"],
            hashlib.sha256(payload).hexdigest().upper(),
        )
        model = result["exit_utility_model"]
        self.assertEqual(model["contract"], MODEL_CONTRACT)
        self.assertEqual(model["model_version"], "1.1.0")
        self.assertEqual(
            model["tail_risk_policy"]["rule_id"],
            "measured-power-relation-long-war-penalty-v2",
        )
        self.assertEqual(
            model["tail_risk_policy"]["parameters_raw"][
                "long_war_scale_start_days"
            ],
            730,
        )
        self.assertTrue(model["model_production_eligible"])
        self.assertTrue(
            all(
                ready is False
                for ready in result["downstream_readiness"].values()
            )
        )

    def test_default_binds_current_repository_budget_bytes(self) -> None:
        result = provide_raiktor_exit_utility_model()
        binding = result["exit_utility_model"]["budget_profile_binding"]
        self.assertEqual(binding["profile_id"], "raiktor-exit-balanced-v1")
        self.assertEqual(binding["profile_version"], "1.0.0")
        self.assertEqual(
            binding["profile_source_sha256"],
            hashlib.sha256(DEFAULT_BUDGET_PATH.read_bytes()).hexdigest().upper(),
        )

    def test_operator_override_must_bind_default_identity(self) -> None:
        source = json.loads(DEFAULT_MODEL_PATH.read_text(encoding="utf-8"))
        source["activation"] = {
            "kind": "operator_override",
            "source": "focused scenario override",
            "base_model_id": source["model_id"],
            "base_model_version": source["model_version"],
        }
        source["model_id"] = "raiktor-exit-focused-utility-v1"
        source["model_version"] = "1.0.1"
        source["domain_coefficients_q100000"][
            "primary_gold_transfer_raw"
        ] = -200000
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "override.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            result = provide_raiktor_exit_utility_model(path)

            drifted = deepcopy(source)
            drifted["activation"]["base_model_version"] = "2.0.0"
            drifted_path = Path(directory) / "drifted.json"
            drifted_path.write_text(json.dumps(drifted), encoding="utf-8")
            with self.assertRaisesRegex(
                ExitUtilityModelError, "base model identity drifted"
            ):
                provide_raiktor_exit_utility_model(drifted_path)

        self.assertFalse(result["default_source_used"])
        self.assertEqual(result["source_kind"], "operator_override")
        self.assertEqual(result["source_model_version"], "1.0.1")

    def test_explicit_repository_default_is_not_an_override(self) -> None:
        with self.assertRaisesRegex(
            ExitUtilityModelError, "must declare operator_override"
        ):
            provide_raiktor_exit_utility_model(DEFAULT_MODEL_PATH)

    def test_budget_binding_drift_is_rejected(self) -> None:
        source = json.loads(DEFAULT_MODEL_PATH.read_text(encoding="utf-8"))
        source["budget_profile_binding"]["profile_source_sha256"] = "A" * 64
        model = render_raiktor_exit_utility_model(
            source, source_sha256="B" * 64
        )
        self.assertEqual(
            model["budget_profile_binding"]["profile_source_sha256"],
            "A" * 64,
        )
        with tempfile.TemporaryDirectory() as directory:
            source["activation"] = {
                "kind": "operator_override",
                "source": "drift test",
                "base_model_id": "raiktor-exit-balanced-utility-v1",
                "base_model_version": "1.1.0",
            }
            path = Path(directory) / "drift.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(
                ExitUtilityModelError, "budget profile binding drifted"
            ):
                provide_raiktor_exit_utility_model(path)

    def test_schema_and_integer_types_are_strict(self) -> None:
        source = json.loads(DEFAULT_MODEL_PATH.read_text(encoding="utf-8"))
        source["extra"] = True
        with self.assertRaisesRegex(ExitUtilityModelError, "malformed schema"):
            render_raiktor_exit_utility_model(source, source_sha256="A" * 64)

        source = json.loads(DEFAULT_MODEL_PATH.read_text(encoding="utf-8"))
        source["domain_coefficients_q100000"]["favor_hook_applied"] = True
        with self.assertRaisesRegex(ExitUtilityModelError, "signed int64"):
            render_raiktor_exit_utility_model(source, source_sha256="A" * 64)

    def test_render_does_not_mutate_source(self) -> None:
        source = json.loads(DEFAULT_MODEL_PATH.read_text(encoding="utf-8"))
        before = deepcopy(source)
        model = render_raiktor_exit_utility_model(
            source, source_sha256="A" * 64
        )
        self.assertEqual(model["contract"], MODEL_CONTRACT)
        self.assertEqual(source, before)
        self.assertEqual(source["contract"], SOURCE_CONTRACT)


if __name__ == "__main__":
    unittest.main()
