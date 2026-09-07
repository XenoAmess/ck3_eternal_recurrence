from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from test_raiktor_three_way_exit_intake import (
    _complete_inputs,
    _write_owner,
)
from test_prepare_g2_source_specific_comparison_intake import (
    INTAKE as SOURCE_INTAKE,
    _report as _source_specific_report,
)
from test_prepare_g2_postwar_comparison_intake import (
    INTAKE as POSTWAR_INTAKE,
    REPORT_SHA256 as POSTWAR_REPORT_SHA256,
    _expected as _postwar_expected,
    _report as _postwar_report,
)
from test_raiktor_surrender_session_binding_contract import _bound


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_three_way_exit_file_intake.py"
)


def _load() -> object:
    spec = importlib.util.spec_from_file_location("g2_file_intake", SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INTAKE = _load()


def _write_json(path: Path, value: object) -> str:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _binding(path: Path) -> dict[str, object]:
    return {
        "path": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }


def _manifest(
    root: Path, *, complete: bool, bind_session: bool = False
) -> tuple[Path, str]:
    owner_path = _write_owner(str(root))
    candidate, terms, campaign, observation, utility = _complete_inputs(
        owner_path
    )
    values = {
        "candidate": candidate,
        "surrender_terms": terms,
        "campaign_certificate": campaign,
        "white_peace_terms_observation": observation,
        "white_peace_utility_evaluation": utility,
    }
    entries: dict[str, object] = {}
    for name, value in values.items():
        path = root / f"{name}.json"
        _write_json(path, value)
        entries[name] = _binding(path)
    entries["owner_budget_source"] = _binding(owner_path)
    entries["observed_surrender_outcome"] = None
    if bind_session:
        binding_path = root / "surrender_aggregate_session_binding.json"
        _write_json(binding_path, _bound())
        entries["surrender_aggregate_session_binding"] = _binding(
            binding_path
        )
    if not complete:
        for name in (
            "campaign_certificate",
            "owner_budget_source",
            "white_peace_terms_observation",
            "white_peace_utility_evaluation",
        ):
            entries[name] = None
    manifest = {
        "schema_version": 2 if bind_session else 1,
        "contract": (
            INTAKE.MANIFEST_CONTRACT_V2
            if bind_session
            else INTAKE.MANIFEST_CONTRACT
        ),
        "inputs": entries,
    }
    path = root / "manifest.json"
    return path, _write_json(path, manifest)


def _generic_postwar_envelope() -> dict[str, object]:
    report, ticket = _postwar_report()
    projection, validation = POSTWAR_INTAKE.build_observed_surrender_outcome(
        report,
        report_sha256=POSTWAR_REPORT_SHA256,
        ticket=ticket,
        expected=_postwar_expected(),
    )
    composed = POSTWAR_INTAKE.compose_three_way_intake(projection)
    return {
        "schema": POSTWAR_INTAKE.EXPECTED_OUTPUT_SCHEMA,
        "status": POSTWAR_INTAKE.EXPECTED_OUTPUT_STATUS,
        "ok": True,
        "manifest": "fixture-manifest.json",
        "manifest_sha256": "E" * 64,
        "source_report": "fixture-report.json",
        "source_report_sha256": POSTWAR_REPORT_SHA256,
        "source_report_elapsed_seconds": report["elapsed_seconds"],
        "source_commit": "F" * 40,
        "ck3_started_or_attached": False,
        "process_inventory_not_required_for_offline_artifact_read": True,
        "receipt_validation": validation,
        "observed_surrender_outcome": projection,
        "three_way_intake_result": composed,
        "three_way_policy_result": composed["assessment"],
        "closed_gap": (
            "R3 action-bound postwar facts are now consumed by the unified "
            "three-way intake"
        ),
        "remaining_gap": {
            "reason": "source_specific_war_loss_attribution_unavailable",
            "provider": INTAKE.SOURCE_SPECIFIC_LOSS_PROVIDER,
            "native_entry": "spawn_army_post_finalize_rva_0x2e7f951",
            "required_observation": "fixture source observation",
        },
        "boundaries": {
            "r3_generic_boundary_used_as_source_specific_loss": False,
            "three_way_outcome_compared": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }


class G2ThreeWayExitFileIntakeTests(unittest.TestCase):
    def test_v2_manifest_binds_session_to_execution_projection_only(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, digest = _manifest(
                root, complete=True, bind_session=True
            )

            result = INTAKE.run_file_intake(
                manifest,
                root / "result.json",
                expected_manifest_sha256=digest,
            )

            execution = result["intake_result"][
                "surrender_execution_readiness"
            ]
            self.assertTrue(
                result["input_bindings"][
                    "surrender_aggregate_session_binding"
                ]["supplied"]
            )
            self.assertTrue(execution["terms"]["session_provenance_ready"])
            self.assertNotIn(
                "six_domain_session_provenance_not_bound",
                execution["terms"]["blockers"],
            )
            self.assertFalse(result["boundaries"]["action_ready"])
            self.assertFalse(execution["action"]["ready"])
            self.assertFalse(execution["postcondition"]["ready"])
            self.assertIsNone(execution["action"]["literal"])

    def test_v2_manifest_requires_exact_session_input_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = _manifest(root, complete=True)
            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["schema_version"] = 2
            value["contract"] = INTAKE.MANIFEST_CONTRACT_V2
            digest = _write_json(manifest, value)

            with self.assertRaisesRegex(
                INTAKE.FileIntakeError, "manifest input names drifted"
            ):
                INTAKE.run_file_intake(
                    manifest,
                    root / "result.json",
                    expected_manifest_sha256=digest,
                )

    def test_complete_hash_bound_manifest_writes_static_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, digest = _manifest(root, complete=True)
            output = root / "result.json"

            result = INTAKE.run_file_intake(
                manifest,
                output,
                expected_manifest_sha256=digest,
            )

            self.assertTrue(output.is_file())
            self.assertTrue(result["ok"])
            self.assertEqual(
                result["status"], "static_recommendation_available"
            )
            self.assertEqual(
                result["intake_result"]["recommended_outcome"],
                "white_peace",
            )
            self.assertEqual(result["intake_result"]["blockers"], [])
            self.assertFalse(
                result["intake_result"]["inputs"][
                    "surrender_aggregate_session_binding_supplied"
                ]
            )
            execution = result["intake_result"][
                "surrender_execution_readiness"
            ]
            self.assertFalse(
                execution["terms"]["session_provenance_ready"]
            )
            self.assertFalse(result["boundaries"]["action_ready"])
            self.assertEqual(result["boundaries"]["mutation_commands"], [])

    def test_missing_provider_files_emit_typed_evidence_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, digest = _manifest(root, complete=False)

            result = INTAKE.run_file_intake(
                manifest,
                root / "result.json",
                expected_manifest_sha256=digest,
            )

            self.assertEqual(result["status"], "evidence_required")
            self.assertIn(
                "campaign_dominance_certificate_unavailable",
                result["intake_result"]["blockers"],
            )
            self.assertFalse(
                result["input_bindings"]["campaign_certificate"][
                    "supplied"
                ]
            )
            self.assertFalse(result["intake_result"]["action_ready"])

    def test_manifest_and_input_hash_drift_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, digest = _manifest(root, complete=True)
            with self.assertRaisesRegex(
                INTAKE.FileIntakeError, "manifest hash differs"
            ):
                INTAKE.run_file_intake(
                    manifest,
                    root / "wrong-manifest.json",
                    expected_manifest_sha256="A" * 64,
                )

            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["inputs"]["candidate"]["sha256"] = "B" * 64
            digest = _write_json(manifest, value)
            with self.assertRaisesRegex(
                INTAKE.FileIntakeError, "candidate hash differs"
            ):
                INTAKE.run_file_intake(
                    manifest,
                    root / "wrong-input.json",
                    expected_manifest_sha256=digest,
                )

    def test_existing_output_and_manifest_shape_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, digest = _manifest(root, complete=False)
            existing = root / "existing.json"
            existing.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                INTAKE.FileIntakeError, "output already exists"
            ):
                INTAKE.run_file_intake(
                    manifest,
                    existing,
                    expected_manifest_sha256=digest,
                )

            malformed = json.loads(manifest.read_text(encoding="utf-8"))
            malformed["unexpected"] = True
            digest = _write_json(manifest, malformed)
            with self.assertRaisesRegex(
                INTAKE.FileIntakeError, "manifest keys drifted"
            ):
                INTAKE.run_file_intake(
                    manifest,
                    root / "malformed.json",
                    expected_manifest_sha256=digest,
                )

    def test_complete_source_specific_envelope_is_consumed_directly(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = _manifest(root, complete=True)
            report_path = root / "source-report.json"
            report_sha = _write_json(report_path, _source_specific_report())
            source_output = root / "source-intake.json"
            source_result = SOURCE_INTAKE.run_intake(
                report_path,
                source_output,
                expected_report_sha256=report_sha,
            )
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_value["inputs"]["observed_surrender_outcome"] = (
                _binding(source_output)
            )
            digest = _write_json(manifest, manifest_value)

            result = INTAKE.run_file_intake(
                manifest,
                root / "result.json",
                expected_manifest_sha256=digest,
            )

            observed = result["intake_result"]["assessment"][
                "observed_surrender_outcome"
            ]
            self.assertEqual(
                observed["status"], "source_specific_outcome_observed"
            )
            self.assertTrue(observed["comparison_input_ready"])
            self.assertEqual(observed["blockers"], [])
            self.assertEqual(
                observed["normalized"],
                source_result["observed_surrender_outcome"],
            )
            self.assertFalse(result["boundaries"]["action_ready"])

    def test_source_specific_envelope_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = _manifest(root, complete=False)
            report_path = root / "source-report.json"
            report_sha = _write_json(report_path, _source_specific_report())
            source_output = root / "source-intake.json"
            source_result = SOURCE_INTAKE.run_intake(
                report_path,
                source_output,
                expected_report_sha256=report_sha,
            )
            source_result["boundaries"]["decision_ready"] = True
            _write_json(source_output, source_result)
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_value["inputs"]["observed_surrender_outcome"] = (
                _binding(source_output)
            )
            digest = _write_json(manifest, manifest_value)

            with self.assertRaisesRegex(
                INTAKE.FileIntakeError,
                "source-specific intake boundary drifted",
            ):
                INTAKE.run_file_intake(
                    manifest,
                    root / "result.json",
                    expected_manifest_sha256=digest,
                )

    def test_generic_postwar_envelope_is_consumed_without_source_promotion(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = _manifest(root, complete=False)
            postwar_output = root / "postwar-intake.json"
            postwar_result = _generic_postwar_envelope()
            _write_json(postwar_output, postwar_result)
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_value["inputs"]["observed_surrender_outcome"] = (
                _binding(postwar_output)
            )
            digest = _write_json(manifest, manifest_value)

            result = INTAKE.run_file_intake(
                manifest,
                root / "result.json",
                expected_manifest_sha256=digest,
            )

            observed = result["intake_result"]["assessment"][
                "observed_surrender_outcome"
            ]
            self.assertEqual(
                observed["status"],
                "observed_generic_boundary_source_attribution_required",
            )
            self.assertTrue(observed["observed_checkpoint_boundary_ready"])
            self.assertFalse(observed["source_specific_loss_comparison_ready"])
            self.assertEqual(
                observed["blockers"],
                ["source_specific_war_loss_attribution_unavailable"],
            )
            self.assertEqual(
                observed["normalized"],
                postwar_result["observed_surrender_outcome"],
            )
            self.assertFalse(result["boundaries"]["action_ready"])

    def test_generic_postwar_envelope_overclaim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = _manifest(root, complete=False)
            postwar_output = root / "postwar-intake.json"
            postwar_result = _generic_postwar_envelope()
            postwar_result["boundaries"]["decision_ready"] = True
            _write_json(postwar_output, postwar_result)
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_value["inputs"]["observed_surrender_outcome"] = (
                _binding(postwar_output)
            )
            digest = _write_json(manifest, manifest_value)

            with self.assertRaisesRegex(
                INTAKE.FileIntakeError,
                "generic postwar intake boundary drifted",
            ):
                INTAKE.run_file_intake(
                    manifest,
                    root / "result.json",
                    expected_manifest_sha256=digest,
                )


if __name__ == "__main__":
    unittest.main()
