from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.raiktor_owner_exit_utility_model_provider import (
    MODEL_CONTRACT,
    OwnerExitUtilityModelError,
    PROVIDER_ID,
    PROVIDER_SCHEMA,
    SOURCE_CONTRACT,
    UTILITY_UNIT,
    provide_raiktor_owner_exit_utility_model,
    render_raiktor_owner_exit_utility_model,
)


AUTOPLAYER_ROOT = Path(__file__).resolve().parents[2]
DRAFT_FIXTURE = (
    AUTOPLAYER_ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_owner_exit_utility_model_draft_v1.json"
)


def _approved_source() -> dict[str, object]:
    """Synthetic test input; these values are not an owner profile."""

    return {
        "schema_version": 1,
        "contract": SOURCE_CONTRACT,
        "approval": {
            "status": "approved",
            "approved_by": "synthetic-test-owner",
            "approved_at_utc": "2026-09-07T04:00:00Z",
        },
        "model_id": "synthetic-test-only-model",
        "model_version": "test-v1",
        "utility_unit": UTILITY_UNIT,
        "budget_profile_binding": {
            "profile_id": "synthetic-test-budget",
            "profile_source_sha256": "B" * 64,
        },
        "domain_coefficients_q100000": {
            "primary_gold_transfer_raw": -11,
            "attacker_prestige_delta_raw": 12,
            "declared_claim_removed_count": -13,
            "favor_hook_applied": -14,
            "truce_day_count": -15,
            "pow_release_count": 16,
            "title_holder_change_count": 17,
            "hostage_transfer_count": 18,
            "war_bound_soldier_loss_count": -19,
        },
        "nonlinear_policy": {
            "rule_id": "synthetic-test-nonlinear",
            "parameters_raw": {"threshold": 20},
        },
        "uncertainty_policy": {
            "rule_id": "synthetic-test-uncertainty",
            "parameters_raw": {"interval_padding": 21},
        },
        "tail_risk_policy": {
            "rule_id": "synthetic-test-tail-risk",
            "parameters_raw": {"loss_multiplier": 22},
        },
    }


class RaiktorOwnerExitUtilityModelProviderTests(unittest.TestCase):
    def test_missing_source_is_typed_unavailable_without_defaults(self) -> None:
        result = provide_raiktor_owner_exit_utility_model(None)

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["provider"], PROVIDER_ID)
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["model_source_available"])
        self.assertFalse(result["owner_approved_source_ready"])
        self.assertIsNone(result["owner_exit_utility_model"])
        self.assertEqual(
            result["provider_blockers"],
            ["owner_exit_utility_model_source_unavailable"],
        )
        self.assertIn(
            "no_default_or_fixture_utility_coefficients",
            result["boundaries"],
        )
        self.assertTrue(
            all(
                value is False
                for value in result["downstream_readiness"].values()
            )
        )

    def test_repository_fixture_is_draft_and_keeps_readiness_false(self) -> None:
        payload = DRAFT_FIXTURE.read_bytes()
        expected_sha = hashlib.sha256(payload).hexdigest().upper()

        result = provide_raiktor_owner_exit_utility_model(DRAFT_FIXTURE)

        model = result["owner_exit_utility_model"]
        self.assertIsInstance(model, dict)
        assert isinstance(model, dict)
        self.assertEqual(result["status"], "incomplete")
        self.assertTrue(result["model_source_available"])
        self.assertFalse(result["owner_approved_source_ready"])
        self.assertEqual(result["source"]["sha256"], expected_sha)
        self.assertEqual(model["model_source_sha256"], expected_sha)
        self.assertEqual(model["contract"], MODEL_CONTRACT)
        self.assertEqual(model["status"], "incomplete")
        self.assertFalse(model["owner_approved_source_ready"])
        self.assertGreater(len(model["missing_owner_choices"]), 0)
        self.assertIn("model_id", model["missing_owner_choices"])
        self.assertTrue(
            all(
                value is False
                for value in result["downstream_readiness"].values()
            )
        )

    def test_synthetic_approved_source_validates_but_is_not_live(self) -> None:
        source = _approved_source()
        payload = json.dumps(
            source, ensure_ascii=False, sort_keys=True, indent=2
        ).encode("utf-8")
        expected_sha = hashlib.sha256(payload).hexdigest().upper()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-test-model.json"
            path.write_bytes(payload)

            result = provide_raiktor_owner_exit_utility_model(path)

        model = result["owner_exit_utility_model"]
        self.assertIsInstance(model, dict)
        assert isinstance(model, dict)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["owner_approved_source_ready"])
        self.assertEqual(result["provider_blockers"], [])
        self.assertEqual(result["source"]["sha256"], expected_sha)
        self.assertEqual(model["status"], "complete")
        self.assertEqual(model["missing_owner_choices"], [])
        self.assertTrue(model["owner_approved_source_ready"])
        self.assertTrue(
            all(
                value is False
                for value in result["downstream_readiness"].values()
            )
        )

    def test_draft_can_be_partially_filled_without_becoming_approved(self) -> None:
        source = json.loads(DRAFT_FIXTURE.read_text(encoding="utf-8"))
        source["model_id"] = "owner-draft-in-progress"
        source["domain_coefficients_q100000"][
            "primary_gold_transfer_raw"
        ] = -1

        model = render_raiktor_owner_exit_utility_model(
            source,
            source_sha256="A" * 64,
        )

        self.assertEqual(model["status"], "incomplete")
        self.assertFalse(model["owner_approved_source_ready"])
        self.assertNotIn("model_id", model["missing_owner_choices"])
        self.assertIn("model_version", model["missing_owner_choices"])

    def test_approved_source_rejects_every_unresolved_owner_choice(self) -> None:
        cases = {
            "model-id": ("model_id", None),
            "budget-sha": (
                "budget_profile_binding.profile_source_sha256",
                None,
            ),
            "coefficient": (
                "domain_coefficients_q100000.pow_release_count",
                None,
            ),
            "nonlinear-rule": ("nonlinear_policy.rule_id", None),
            "uncertainty-parameters": (
                "uncertainty_policy.parameters_raw",
                None,
            ),
            "tail-rule": ("tail_risk_policy.rule_id", None),
        }
        for name, (path, value) in cases.items():
            with self.subTest(name=name):
                source = _approved_source()
                _set_path(source, path, value)
                with self.assertRaises(OwnerExitUtilityModelError):
                    render_raiktor_owner_exit_utility_model(
                        source,
                        source_sha256="A" * 64,
                    )

    def test_malformed_fields_and_extra_keys_are_rejected(self) -> None:
        cases: list[tuple[str, dict[str, object]]] = []
        wrong_unit = _approved_source()
        wrong_unit["utility_unit"] = "points"
        cases.append(("wrong-unit", wrong_unit))
        boolean_coefficient = _approved_source()
        boolean_coefficient["domain_coefficients_q100000"][
            "pow_release_count"
        ] = True
        cases.append(("boolean-coefficient", boolean_coefficient))
        bad_budget_hash = _approved_source()
        bad_budget_hash["budget_profile_binding"][
            "profile_source_sha256"
        ] = "b" * 64
        cases.append(("lowercase-budget-hash", bad_budget_hash))
        split_policy = _approved_source()
        split_policy["nonlinear_policy"]["parameters_raw"] = None
        cases.append(("split-policy", split_policy))
        extra_key = _approved_source()
        extra_key["inferred_defaults"] = True
        cases.append(("extra-key", extra_key))

        for name, source in cases:
            with self.subTest(name=name):
                with self.assertRaises(OwnerExitUtilityModelError):
                    render_raiktor_owner_exit_utility_model(
                        source,
                        source_sha256="A" * 64,
                    )

    def test_malformed_approval_never_promotes(self) -> None:
        cases = {
            "unknown-status": ("status", "ready"),
            "approved-without-author": ("approved_by", None),
            "approved-without-time": ("approved_at_utc", None),
            "bad-time": ("approved_at_utc", "2026-09-07"),
        }
        for name, (key, value) in cases.items():
            with self.subTest(name=name):
                source = _approved_source()
                source["approval"][key] = value
                with self.assertRaises(OwnerExitUtilityModelError):
                    render_raiktor_owner_exit_utility_model(
                        source,
                        source_sha256="A" * 64,
                    )

        draft = json.loads(DRAFT_FIXTURE.read_text(encoding="utf-8"))
        draft["approval"]["approved_by"] = "stale-author"
        with self.assertRaises(OwnerExitUtilityModelError):
            render_raiktor_owner_exit_utility_model(
                draft,
                source_sha256="A" * 64,
            )

    def test_source_hash_binds_exact_bytes(self) -> None:
        source = _approved_source()
        compact = json.dumps(source, separators=(",", ":")).encode("utf-8")
        indented = json.dumps(source, indent=2).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            compact_path = Path(directory) / "compact.json"
            indented_path = Path(directory) / "indented.json"
            compact_path.write_bytes(compact)
            indented_path.write_bytes(indented)

            compact_result = provide_raiktor_owner_exit_utility_model(
                compact_path
            )
            indented_result = provide_raiktor_owner_exit_utility_model(
                indented_path
            )

        self.assertNotEqual(
            compact_result["source"]["sha256"],
            indented_result["source"]["sha256"],
        )
        self.assertNotEqual(
            compact_result["owner_exit_utility_model"][
                "model_source_sha256"
            ],
            indented_result["owner_exit_utility_model"][
                "model_source_sha256"
            ],
        )

    def test_invalid_file_and_explicit_missing_path_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaises(OwnerExitUtilityModelError):
                provide_raiktor_owner_exit_utility_model(missing)

            invalid = Path(directory) / "invalid.json"
            invalid.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(OwnerExitUtilityModelError):
                provide_raiktor_owner_exit_utility_model(invalid)

    def test_render_does_not_mutate_source(self) -> None:
        source = _approved_source()
        before = deepcopy(source)

        render_raiktor_owner_exit_utility_model(
            source,
            source_sha256="A" * 64,
        )

        self.assertEqual(source, before)


def _set_path(value: dict[str, object], dotted_path: str, replacement: object) -> None:
    cursor = value
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        child = cursor[part]
        assert isinstance(child, dict)
        cursor = child
    cursor[parts[-1]] = replacement


if __name__ == "__main__":
    unittest.main()
