from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_postwar_comparison_intake.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_postwar_comparison_intake_r3_manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "prepare_g2_postwar_comparison_intake", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot import {SCRIPT}")
INTAKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INTAKE)

from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (  # noqa: E402
    SOURCE_SPECIFIC_LOSS_PROVIDER,
    assess_raiktor_three_way_exit,
)


REPORT_SHA256 = "A" * 64
GENERATION_SHA256 = "B" * 64
RECEIPT_ID = "C" * 64
TICKET_ID = "D" * 64
WAR_ID = 50_331_699
CHARACTER_ID = 29_829
OPPONENT_ID = 36_769
DATE_RAW = 53_223_936


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _generations() -> list[dict[str, object]]:
    return [
        {
            "persistent_regiment_id": 101,
            "current_rows": [
                {
                    "composition_ordinal": 0,
                    "current_army_regiment_id": 201,
                    "raised_carmy_id": 301,
                    "current_soldiers": 400,
                }
            ],
        },
        {
            "persistent_regiment_id": 102,
            "current_rows": [
                {
                    "composition_ordinal": 0,
                    "current_army_regiment_id": 202,
                    "raised_carmy_id": 302,
                    "current_soldiers": 198,
                }
            ],
        },
    ]


def _ticket(generations: list[dict[str, object]]) -> dict[str, object]:
    return {
        "retention_ticket_id": TICKET_ID,
        "exact_build_sha256": INTAKE.retention.EXPECTED_EXE_SHA256,
        "source_report_sha256": "E" * 64,
        "war_id": WAR_ID,
        "character_id": CHARACTER_ID,
        "opponent_character_id": OPPONENT_ID,
        "date_raw": DATE_RAW,
        "pre_termination_soldiers": 598,
        "evaluated_days": 1825,
        "frozen_generation_sha256": INTAKE.retention._sha256_json(generations),
        "frozen_generations": copy.deepcopy(generations),
    }


def _receipt(
    ticket: dict[str, object], generations: list[dict[str, object]]
) -> dict[str, object]:
    action = f"surrender-war-{WAR_ID}"
    receipt = {
        "schema": INTAKE.retention.EXPECTED_RECEIPT_SCHEMA,
        "status": INTAKE.retention.EXPECTED_RECEIPT_STATUS,
        "retention_ticket_id": TICKET_ID,
        "exact_build": {
            "game_executable_sha256": INTAKE.retention.EXPECTED_EXE_SHA256
        },
        "session_binding": {
            "ck3_pid": 9001,
            "connection_generation": 2,
            "episode_run_id": "fixture-r3-episode",
            "character_id": CHARACTER_ID,
            "war_id": WAR_ID,
        },
        "pre": {
            "source_report_sha256": ticket["source_report_sha256"],
            "snapshot_id": "native:3",
            "revision": 4,
            "native_revision": 3,
            "date_raw": DATE_RAW,
            "terms_query_sequence": 2,
            "receipt_sequence": 2,
            "ck3_pid": 9001,
            "connection_generation": 2,
            "episode_run_id": "fixture-r3-episode",
            "pre_termination_soldiers": 598,
            "frozen_generation_sha256": ticket["frozen_generation_sha256"],
            "frozen_generations": copy.deepcopy(generations),
        },
        "termination": {
            "submitted": True,
            "accepted": True,
            "step": action,
            "war_id": WAR_ID,
            "receipt_sequence": 3,
            "receipt_id": RECEIPT_ID,
            "ck3_pid": 9001,
            "connection_generation": 2,
            "episode_run_id": "fixture-r3-episode",
        },
        "post": {
            "revision": 5,
            "native_revision": 4,
            "date_raw": DATE_RAW,
            "receipt_sequence": 4,
            "ck3_pid": 9001,
            "connection_generation": 2,
            "episode_run_id": "fixture-r3-episode",
            "paused": True,
            "war_id": WAR_ID,
            "old_full_generation_war_id_absent": True,
            "war_bound_cleanup": {
                "observable": True,
                "status": "destroyed",
                "frozen_generations": copy.deepcopy(generations),
                "post_termination_soldiers": 0,
                "proven_boundary_soldiers_lost": 598,
            },
            "truce_expiry": {
                "observable": True,
                "source": INTAKE.retention.EXPECTED_EXPIRY_SOURCE,
                "formula_derived": False,
                "from_character_id": CHARACTER_ID,
                "to_character_id": OPPONENT_ID,
                "evaluated_days": 1825,
                "queried_at_date_raw": DATE_RAW,
                "expiry_date_raw": DATE_RAW + 43_800,
            },
        },
        "mutation_commands": [action],
        "boundaries": {
            "private_default_off": True,
            "source_specific_attribution_ready": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }
    receipt["ticket_validation"] = INTAKE.retention.validate_postwar_receipt(
        receipt, ticket
    )
    return receipt


def _report() -> tuple[dict[str, object], dict[str, object]]:
    generations = _generations()
    ticket = _ticket(generations)
    receipt = _receipt(ticket, generations)
    action = f"surrender-war-{WAR_ID}"
    checks = {"receipt": True, "cleanup": True}
    return (
        {
            "kind": INTAKE.EXPECTED_REPORT_KIND,
            "status": INTAKE.EXPECTED_REPORT_STATUS,
            "ok": True,
            "elapsed_seconds": 176.682,
            "policy": {"mutation_commands": [action]},
            "identity": {
                "bridge_dll_sha256": "F" * 64,
                "bridge_injector_sha256": "1" * 64,
            },
            "mcp_sequence": {
                "mutation_commands": [action],
                "postwar_receipt": receipt,
                "checks": checks,
                "ok": True,
            },
            "session": {
                "pid": 9001,
                "mode": "native-headless",
                "restart_count": 0,
                "ok": True,
            },
            "cleanup": {
                "shutdown_ok": True,
                "tree_gone": True,
                "cleanup_proven": True,
                "driver_closed": True,
                "ok": True,
            },
            "source_invariant": {
                "before": {"checkpoint": "2" * 64},
                "after": {"checkpoint": "2" * 64},
                "unchanged": True,
            },
            "formal_private_capture": {
                "retention_ticket_id": TICKET_ID,
                "only_mutation": action,
                "cleanup_destroyed_must_come_from_exact_store_reader": True,
                "war_id_absence_is_admission_only": True,
            },
        },
        ticket,
    )


def _expected() -> dict[str, object]:
    return {
        "source_report_sha256": REPORT_SHA256,
        "ck3_exe_sha256": INTAKE.retention.EXPECTED_EXE_SHA256,
        "bridge_dll_sha256": "F" * 64,
        "bridge_injector_sha256": "1" * 64,
        "retention_ticket_id": TICKET_ID,
        "character_id": CHARACTER_ID,
        "opponent_character_id": OPPONENT_ID,
        "war_id": WAR_ID,
        "counts": {
            "frozen_persistent_regiments": 2,
            "frozen_current_regiments": 2,
            "frozen_armies": 2,
            "pre_termination_soldiers": 598,
            "post_termination_soldiers": 0,
            "proven_boundary_soldiers_lost": 598,
            "evaluated_days": 1825,
        },
    }


class G2PostwarComparisonIntakeTests(unittest.TestCase):
    def test_r3_receipt_reaches_existing_policy_but_stays_source_red(self) -> None:
        report, ticket = _report()
        projection, validation = INTAKE.build_observed_surrender_outcome(
            report,
            report_sha256=REPORT_SHA256,
            ticket=ticket,
            expected=_expected(),
        )
        result = assess_raiktor_three_way_exit(
            None, None, None, None, None, projection
        )
        observed = result["observed_surrender_outcome"]
        self.assertTrue(validation["receipt"]["ok"])
        self.assertEqual(
            observed["status"],
            "observed_generic_boundary_source_attribution_required",
        )
        self.assertTrue(observed["observed_checkpoint_boundary_ready"])
        self.assertFalse(observed["source_specific_loss_comparison_ready"])
        self.assertFalse(observed["comparison_input_ready"])
        self.assertEqual(
            observed["blockers"],
            ["source_specific_war_loss_attribution_unavailable"],
        )
        self.assertEqual(observed["next_provider"], SOURCE_SPECIFIC_LOSS_PROVIDER)
        self.assertIsNone(result["recommended_outcome"])
        self.assertFalse(result["action_ready"])

    def test_readiness_promotion_is_rejected_before_policy_consumption(self) -> None:
        report, ticket = _report()
        report["mcp_sequence"]["postwar_receipt"]["boundaries"][
            "decision_ready"
        ] = True
        with self.assertRaises(INTAKE.IntakeError):
            INTAKE.build_observed_surrender_outcome(
                report,
                report_sha256=REPORT_SHA256,
                ticket=ticket,
                expected=_expected(),
            )

    def test_committed_manifest_pins_r3_without_claiming_comparison(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], INTAKE.EXPECTED_MANIFEST_SCHEMA)
        self.assertFalse(manifest["live_authorized"])
        self.assertEqual(
            manifest["expected"]["source_report_sha256"],
            "44E1F7C0B470B2CF7B6549192865402F21F88C7CF073E896DE1B93632311D5D0",
        )
        self.assertEqual(manifest["expected"]["source_report_size_bytes"], 214389654)
        self.assertEqual(
            manifest["comparison_contract"]["consumer"],
            "raiktor-three-way-exit-policy-v1",
        )
        self.assertFalse(
            manifest["comparison_contract"]["comparison_input_ready"]
        )
        for name in ("retention_manifest", "current_pin_manifest"):
            path = ROOT.parent / manifest["paths"][name]
            self.assertEqual(_sha256(path), manifest["sha256"][name])


if __name__ == "__main__":
    unittest.main()
