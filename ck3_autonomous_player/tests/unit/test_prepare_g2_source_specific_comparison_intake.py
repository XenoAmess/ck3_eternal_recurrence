from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_source_specific_comparison_intake.py"
)
LIFECYCLE_TEST = (
    ROOT
    / "tests"
    / "unit"
    / "test_g2_source_specific_war_loss_lifecycle.py"
)


def _load(path: Path, name: str) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INTAKE = _load(SCRIPT, "g2_source_specific_comparison_intake")
FIXTURE = _load(LIFECYCLE_TEST, "g2_source_specific_lifecycle_fixture")


def _report() -> dict[str, object]:
    normalized = FIXTURE.RUNNER.normalize_raiktor_source_specific_capture(
        FIXTURE._source_capture(), capture_sha256="A" * 64
    )
    ticket, handoff = FIXTURE.RUNNER.build_source_bound_ticket(
        normalized, FIXTURE._pre_sequence()
    )
    with tempfile.TemporaryDirectory() as temporary:
        FIXTURE.RUNNER.create_pre_mutation_checkpoint(
            FIXTURE._CheckpointDriver(Path(temporary) / "save games"), ticket
        )
    receipt = FIXTURE._receipt(ticket)
    receipt["termination"]["receipt_id"] = "B" * 64
    receipt["boundaries"].update(
        {
            "private_default_off": True,
            "action_readiness_promoted": False,
        }
    )
    receipt["ticket_validation"] = INTAKE.retention.validate_postwar_receipt(
        receipt, ticket
    )
    action = f"surrender-war-{FIXTURE.WAR_ID}"
    sequence = {
        "ok": True,
        "mutation_commands": [action],
        "postwar_receipt": receipt,
    }
    joined = FIXTURE.RUNNER.build_source_specific_loss_join(
        normalized, ticket, sequence
    )
    lifecycle = {
        "schema": INTAKE.LIFECYCLE_SCHEMA,
        "status": "green",
        "source_normalization": normalized,
        "handoff": handoff,
        "retention_ticket": ticket,
        "sequence": sequence,
        "source_specific_loss_join": joined,
        "mutation_commands": [action],
        "ok": True,
    }
    outer = {
        "schema": INTAKE.OUTER_SCHEMA,
        "status": "green-orchestration",
        "process_identity": {
            "normal_event_pid": FIXTURE.PID,
            "observer_pid": FIXTURE.PID,
            "bridge_pid": FIXTURE.PID,
            "lifecycle_pid": FIXTURE.PID,
        },
        "observer_handoff": {
            "breakpoint_restored": True,
            "debugger_detached": True,
            "process_terminated": False,
            "process_alive_after_detach": True,
        },
        "ownership": {
            "exclusive_launch_owner": "outer-owner",
            "same_driver_handoff": True,
            "final_cleanup_owner": "outer-owner",
            "final_cleanup_calls": 1,
        },
        "stage_trace": list(INTAKE.EXPECTED_TRACE),
        "lifecycle_result": lifecycle,
        "ok": True,
    }
    return {
        "schema": INTAKE.REPORT_SCHEMA,
        "status": "GREEN",
        "preflight": {
            "status": INTAKE.PREFLIGHT_STATUS,
            "boundaries": {
                "live_executed": False,
                "source_specific_loss_ready": False,
                "comparison_input_ready": False,
            },
        },
        "outer_owner": outer,
        "cleanup": {
            "driver_closed": True,
            "target_pid": FIXTURE.PID,
            "remaining_ck3": [],
            "errors": [],
            "ok": True,
        },
        "boundaries": {
            "terms_ready": True,
            "source_specific_loss_ready": True,
            "comparison_input_ready": True,
            "three_way_comparison_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }


class G2SourceSpecificComparisonIntakeTests(unittest.TestCase):
    def test_qualified_lifecycle_becomes_policy_consumable(self) -> None:
        projection, validation = INTAKE.build_observed_surrender_outcome(
            _report(), report_sha256="C" * 64
        )
        self.assertEqual(projection["status"], "complete")
        self.assertTrue(
            projection["war_bound_cleanup"][
                "source_specific_attribution_ready"
            ]
        )
        self.assertTrue(validation["receipt"]["ok"])
        policy = INTAKE.assess_raiktor_three_way_exit(
            None,
            None,
            None,
            None,
            None,
            observed_surrender_outcome_value=projection,
        )
        observed = policy["observed_surrender_outcome"]
        self.assertEqual(observed["status"], "source_specific_outcome_observed")
        self.assertTrue(observed["comparison_input_ready"])
        self.assertEqual(observed["blockers"], [])
        self.assertIsNone(policy["recommended_outcome"])
        self.assertFalse(policy["action_ready"])

    def test_generic_receipt_flag_cannot_erase_source_join_proof(self) -> None:
        report = _report()
        receipt = report["outer_owner"]["lifecycle_result"]["sequence"][
            "postwar_receipt"
        ]
        self.assertFalse(
            receipt["boundaries"]["source_specific_attribution_ready"]
        )
        projection, _ = INTAKE.build_observed_surrender_outcome(
            report, report_sha256="C" * 64
        )
        self.assertTrue(
            projection["war_bound_cleanup"][
                "source_specific_attribution_ready"
            ]
        )

    def test_join_or_identity_drift_is_rejected(self) -> None:
        report = _report()
        join = report["outer_owner"]["lifecycle_result"][
            "source_specific_loss_join"
        ]
        join["readiness"]["source_specific_loss_ready"] = False
        with self.assertRaisesRegex(INTAKE.IntakeError, "source_join_readiness"):
            INTAKE.build_observed_surrender_outcome(
                report, report_sha256="C" * 64
            )

        report = _report()
        report["outer_owner"]["process_identity"]["observer_pid"] += 1
        with self.assertRaisesRegex(INTAKE.IntakeError, "one_process"):
            INTAKE.build_observed_surrender_outcome(
                report, report_sha256="C" * 64
            )

    def test_readiness_overclaim_is_rejected(self) -> None:
        report = _report()
        report["boundaries"]["decision_ready"] = True
        with self.assertRaisesRegex(INTAKE.IntakeError, "report_boundaries"):
            INTAKE.build_observed_surrender_outcome(
                report, report_sha256="C" * 64
            )

        report = _report()
        report["boundaries"]["terms_ready"] = False
        with self.assertRaisesRegex(INTAKE.IntakeError, "report_boundaries"):
            INTAKE.build_observed_surrender_outcome(
                report, report_sha256="C" * 64
            )

    def test_offline_file_intake_requires_exact_report_hash(self) -> None:
        report = _report()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "report.json"
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(report_path.read_bytes()).hexdigest().upper()
            output = root / "intake.json"
            result = INTAKE.run_intake(
                report_path,
                output,
                expected_report_sha256=digest,
            )
            self.assertTrue(result["ok"])
            self.assertTrue(output.is_file())
            self.assertTrue(
                result["boundaries"][
                    "source_specific_loss_comparison_ready"
                ]
            )
            self.assertFalse(
                result["boundaries"]["three_way_comparison_ready"]
            )
            self.assertEqual(
                result["remaining_providers"], INTAKE.REMAINING_PROVIDERS
            )
            composed = result["three_way_intake_result"]
            self.assertEqual(
                composed["schema"],
                "xar.ck3.raiktor_three_way_exit_intake.v1",
            )
            self.assertEqual(composed["status"], "evidence_required")
            self.assertFalse(composed["action_ready"])
            self.assertIsNone(composed["action_literal"])
            self.assertEqual(
                composed["assessment"], result["three_way_policy_result"]
            )
            self.assertEqual(
                composed["assessment"]["observed_surrender_outcome"][
                    "status"
                ],
                "source_specific_outcome_observed",
            )

            with self.assertRaisesRegex(INTAKE.IntakeError, "hash differs"):
                INTAKE.run_intake(
                    report_path,
                    root / "wrong.json",
                    expected_report_sha256="D" * 64,
                )


if __name__ == "__main__":
    unittest.main()
