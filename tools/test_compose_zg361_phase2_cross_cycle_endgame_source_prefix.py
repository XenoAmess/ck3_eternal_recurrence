#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from compose_zg361_phase2_cross_cycle_endgame_source_prefix import (  # noqa: E402
    EndgameSourcePrefixComposeError,
    compose_endgame_source_capture_prefix,
)
from test_zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    CaptureAndActionService,
    player_switch_locator,
)
from zg361_phase2_cross_cycle_endgame_source_capture import (  # noqa: E402
    CAPTURE_PREFIX_KIND,
    MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
    MULTI_BRANCH_CAPTURE_SCHEMA_VERSION,
    PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
    EndgameSourceCaptureError,
    phase2_source_lineage_set_id,
    preflight_endgame_source_capture_prefix,
)
from zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    capture_current_received_self_incident_checkpoint_v1,
)
from zg361_phase2_incident_source_capture_entry import (  # noqa: E402
    GENERIC_REBIND_AUTHORITY,
    build_schema2_incident_registry_capture_entry,
)
from zhongguo_phase2_event_choreography import (  # noqa: E402
    phase2_event_sequence_plan,
)


SEED_LINEAGE_ID = "zg361-phase2-seed-" + "a" * 64
INCIDENT_SEED_LINEAGE_ID = (
    "zg361-phase2-seed-"
    "8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9"
)
RUNTIME_SEED_LINEAGE_ID = "zg361-phase2-seed-" + "f" * 64
EXE_SHA256 = "B" * 64
PROMOTION_TREE = "C" * 64
PROJECTS_TREE = "D" * 64
INCIDENT_TREE = "E" * 64


def _record(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
    }


def _receipt(
    *, handler: str, owner: int, player: int, date_raw: int, sha256: str
) -> dict[str, object]:
    plan = phase2_event_sequence_plan(handler)
    return {
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "console_used": False,
        "span_id": plan.span_id,
        "event_definition_key": plan.source_event,
        "owner_character_id": owner,
        "player_character_id": player,
        "date_raw": date_raw,
        "checkpoint_sha256": sha256,
        "save_lineage_id": SEED_LINEAGE_ID,
    }


def _row(root: Path, *, handler: str, ordinal: int) -> dict[str, object]:
    plan = phase2_event_sequence_plan(handler)
    checkpoint = root / f"source-{ordinal}.ck3"
    checkpoint.write_bytes(f"real-source-{ordinal}".encode("ascii"))
    sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest().upper()
    owner = 9200 + ordinal
    player = 9001
    date_raw = 820 + ordinal
    return {
        "span_id": plan.span_id,
        "handler": handler,
        "source_event_definition_key": plan.source_event,
        "owner_character_id": owner,
        "player_character_id": player,
        "date_raw": date_raw,
        "checkpoint": {
            "path": str(checkpoint.resolve()),
            "bytes": checkpoint.stat().st_size,
            "sha256": sha256,
            "save_lineage_id": SEED_LINEAGE_ID,
        },
        "source_receipt": _receipt(
            handler=handler,
            owner=owner,
            player=player,
            date_raw=date_raw,
            sha256=sha256,
        ),
    }


def _canonical_lineage(
    tree_sha256: str, *, seed_lineage_id: str = INCIDENT_SEED_LINEAGE_ID
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "phase": "zhongguo_phase2",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": True,
        "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
        "seed_lineage_id": seed_lineage_id,
        "game": {"version": "1.19.0.6", "exe_sha256": EXE_SHA256},
        "mod_mount": {
            "kind": "product-only",
            "tree_sha256": tree_sha256,
            "enabled_mods": ["mod/zg361_acceptance.mod"],
        },
    }


def _inputs(
    root: Path,
) -> tuple[Path, Path, Path, str, list[dict[str, object]]]:
    promotion = _row(
        root, handler="capture_promotion_compensation", ordinal=1
    )
    projects = _row(root, handler="capture_projects_metrics", ordinal=2)
    promotion_lineage = {
        "seed_lineage_id": SEED_LINEAGE_ID,
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "product_only_runtime": True,
        "game_version": "1.19.0.6",
        "executable_sha256": EXE_SHA256,
        "session_kind": "managed_product_session",
    }
    projects_lineage = {
        "schema_version": 2,
        "kind": "zg361_projects_metrics_capture_lineage",
        "seed_lineage_id": SEED_LINEAGE_ID,
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "product_only_mount": True,
        "product_tree_sha256": PROJECTS_TREE,
        "runtime_product_tree_sha256": PROJECTS_TREE,
        "enabled_mods": ["mod/zg361_acceptance.mod"],
    }
    promotion_artifact = root / "promotion.json"
    promotion_artifact.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": "zg361_phase2_source_checkpoint_capture_artifact",
                "result": "GREEN",
                "readiness": "captured-real-promotion-source",
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                "seed_lineage_id": SEED_LINEAGE_ID,
                "capture_lineage": promotion_lineage,
                "entries": [promotion],
            }
        ),
        encoding="utf-8",
    )
    projects_artifact = root / "projects.json"
    projects_artifact.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "registry_kind": (
                    "zg361_projects_metrics_source_checkpoint_registry"
                ),
                "result": "GREEN",
                "readiness": "captured-real-checkpoint",
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                "seed_lineage_id": SEED_LINEAGE_ID,
                "capture_lineage": projects_lineage,
                "entries": [projects],
            }
        ),
        encoding="utf-8",
    )
    two = root / "two-of-four.json"
    two.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": "zg361_phase2_source_checkpoint_capture_artifact",
                "result": "GREEN",
                "readiness": "captured-real-two-of-four-sources",
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                "canonical_registry_ready": False,
                "captured_handlers": [
                    "capture_promotion_compensation",
                    "capture_projects_metrics",
                ],
                "missing_handlers": [
                    "capture_incidents_operations",
                    "capture_cross_cycle_endgame",
                ],
                "seed_lineage_id": SEED_LINEAGE_ID,
                "source_artifacts": {
                    "capture_promotion_compensation": _record(
                        promotion_artifact
                    ),
                    "capture_projects_metrics": _record(projects_artifact),
                },
                "entries": [promotion, projects],
            }
        ),
        encoding="utf-8",
    )

    incident_root = root / "incident"
    incident_root.mkdir()
    service = CaptureAndActionService(incident_root)
    switch_locator = player_switch_locator(
        incident_root,
        service,
        seed_lineage_id=INCIDENT_SEED_LINEAGE_ID,
    )
    receipt = capture_current_received_self_incident_checkpoint_v1(
        service,
        checkpoint_root=incident_root / "checkpoints",
        receipt_path=incident_root / "strict-receipt.json",
        seed_lineage_id=INCIDENT_SEED_LINEAGE_ID,
        capture_lineage=_canonical_lineage(INCIDENT_TREE),
        player_switch_receipt=switch_locator,
    )
    incident = build_schema2_incident_registry_capture_entry(
        receipt, expected_seed_lineage_id=INCIDENT_SEED_LINEAGE_ID
    )
    incident_path = root / "incident-entry.json"
    incident_path.write_text(json.dumps(incident), encoding="utf-8")
    source_checkpoint = root / "r106-source.ck3"
    source_checkpoint.write_bytes(b"immutable-r106-source")
    source_checkpoint_record = _record(source_checkpoint)
    report = {
        "schema_version": 1,
        "result": "GREEN",
        "fixture_used": False,
        "console_used": False,
        "mcp_only": True,
        "state_preparation": {
            "source_checkpoint": source_checkpoint_record,
        },
        "original_source_checkpoint_after": copy.deepcopy(
            source_checkpoint_record
        ),
        "original_source_checkpoint_unchanged": True,
        "source_entry": _record(incident_path),
        "player_switch": {
            "schema_version": 1,
            "result": "GREEN",
            "capture_lineage": _canonical_lineage(INCIDENT_TREE),
            "player_switch_receipt": switch_locator,
        },
    }
    report_path = root / "incident-run-report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return (
        two,
        incident_path,
        report_path,
        str(source_checkpoint_record["sha256"]),
        [promotion, projects, incident],
    )


class EndgameSourcePrefixComposerTests(unittest.TestCase):
    def test_composes_mixed_branch_prefix_without_rewriting_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two, incident, report, source_sha, original_rows = _inputs(root)
            prefix = compose_endgame_source_capture_prefix(
                two,
                incident,
                report,
                expected_incident_source_checkpoint_sha256=source_sha,
            )

            self.assertEqual(
                prefix["schema_version"], MULTI_BRANCH_CAPTURE_SCHEMA_VERSION
            )
            self.assertEqual(prefix["kind"], CAPTURE_PREFIX_KIND)
            self.assertEqual(prefix["result"], "LIVE_PENDING")
            self.assertEqual(prefix["readiness"], "live-pending-endgame-source")
            self.assertEqual(prefix["entries"], original_rows)
            self.assertNotIn("seed_lineage_id", prefix)
            lineage = prefix["capture_lineage"]
            self.assertEqual(
                lineage["kind"], PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND
            )
            self.assertEqual(
                lineage["capture_lineage_mode"],
                MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
            )
            per_entry = lineage["entry_capture_lineages"]
            self.assertEqual(
                [row["handler"] for row in per_entry],
                [
                    "capture_promotion_compensation",
                    "capture_projects_metrics",
                    "capture_incidents_operations",
                ],
            )
            self.assertEqual(
                [row["seed_lineage_id"] for row in per_entry],
                [
                    SEED_LINEAGE_ID,
                    SEED_LINEAGE_ID,
                    INCIDENT_SEED_LINEAGE_ID,
                ],
            )
            self.assertEqual(
                prefix["lineage_set_id"],
                phase2_source_lineage_set_id(per_entry),
            )
            self.assertTrue(
                per_entry[0]["capture_lineage"]["product_only_runtime"]
            )
            self.assertEqual(
                per_entry[1]["capture_lineage"]["product_tree_sha256"],
                PROJECTS_TREE,
            )
            self.assertEqual(
                per_entry[2]["capture_lineage"]["mod_mount"]["tree_sha256"],
                INCIDENT_TREE,
            )
            self.assertEqual(
                per_entry[2]["capture_run_input_checkpoint"]["sha256"],
                source_sha,
            )
            result = preflight_endgame_source_capture_prefix(prefix)
            self.assertEqual(result["entry_count"], 3)
            self.assertEqual(
                result["entry_seed_lineage_ids"],
                {
                    "capture_promotion_compensation": SEED_LINEAGE_ID,
                    "capture_projects_metrics": SEED_LINEAGE_ID,
                    "capture_incidents_operations": INCIDENT_SEED_LINEAGE_ID,
                },
            )

    def test_schema3_rejects_a_fictional_common_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two, incident, report, source_sha, _ = _inputs(root)
            prefix = compose_endgame_source_capture_prefix(
                two,
                incident,
                report,
                expected_incident_source_checkpoint_sha256=source_sha,
            )
            prefix["seed_lineage_id"] = SEED_LINEAGE_ID

            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(prefix)
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_prefix_header_invalid",
            )

    def test_schema3_rejects_checkpoint_seed_not_bound_to_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two, incident, report, source_sha, _ = _inputs(root)
            prefix = compose_endgame_source_capture_prefix(
                two,
                incident,
                report,
                expected_incident_source_checkpoint_sha256=source_sha,
            )
            prefix["entries"][2]["checkpoint"]["save_lineage_id"] = (
                SEED_LINEAGE_ID
            )

            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(prefix)
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_prefix_entry_invalid",
            )

    def test_schema3_rejects_missing_handler_lineage_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two, incident, report, source_sha, _ = _inputs(root)
            prefix = compose_endgame_source_capture_prefix(
                two,
                incident,
                report,
                expected_incident_source_checkpoint_sha256=source_sha,
            )
            prefix["capture_lineage"]["entry_capture_lineages"].pop()

            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(prefix)
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_lineage_invalid",
            )

    def test_rejects_stale_a400_incident_switch_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two, incident, report, source_sha, _ = _inputs(root)
            report_value = json.loads(report.read_text(encoding="utf-8"))
            report_value["player_switch"]["capture_lineage"][
                "seed_lineage_id"
            ] = SEED_LINEAGE_ID
            report.write_text(json.dumps(report_value), encoding="utf-8")

            with self.assertRaises(EndgameSourcePrefixComposeError) as raised:
                compose_endgame_source_capture_prefix(
                    two,
                    incident,
                    report,
                    expected_incident_source_checkpoint_sha256=source_sha,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_prefix_incident_run_report_invalid",
            )

    def test_rejects_source_artifact_that_does_not_own_exact_row(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two_path, incident_path, report, source_sha, _ = _inputs(root)
            two = json.loads(two_path.read_text(encoding="utf-8"))
            source = Path(
                two["source_artifacts"]["capture_projects_metrics"]["path"]
            )
            artifact = json.loads(source.read_text(encoding="utf-8"))
            artifact["entries"][0]["date_raw"] += 1
            source.write_text(json.dumps(artifact), encoding="utf-8")
            two["source_artifacts"]["capture_projects_metrics"] = _record(source)
            two_path.write_text(json.dumps(two), encoding="utf-8")

            with self.assertRaises(EndgameSourcePrefixComposeError) as raised:
                compose_endgame_source_capture_prefix(
                    two_path,
                    incident_path,
                    report,
                    expected_incident_source_checkpoint_sha256=source_sha,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_prefix_source_artifact_invalid",
            )

    def test_rejects_non_product_incident_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two_path, incident_path, report, source_sha, _ = _inputs(root)
            incident = json.loads(incident_path.read_text(encoding="utf-8"))
            incident["capture_lineage"].pop("mod_mount")
            incident_path.write_text(json.dumps(incident), encoding="utf-8")
            report_value = json.loads(report.read_text(encoding="utf-8"))
            report_value["source_entry"] = _record(incident_path)
            report.write_text(json.dumps(report_value), encoding="utf-8")

            with self.assertRaises(EndgameSourcePrefixComposeError) as raised:
                compose_endgame_source_capture_prefix(
                    two_path,
                    incident_path,
                    report,
                    expected_incident_source_checkpoint_sha256=source_sha,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_prefix_composed_manifest_invalid",
            )

    def test_preflight_rejects_lineage_not_bound_to_its_source_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two_path, incident_path, report, source_sha, _ = _inputs(root)
            prefix = compose_endgame_source_capture_prefix(
                two_path,
                incident_path,
                report,
                expected_incident_source_checkpoint_sha256=source_sha,
            )
            prefix["capture_lineage"]["entry_capture_lineages"][1][
                "capture_lineage"
            ]["product_tree_sha256"] = "9" * 64
            prefix["capture_lineage"]["entry_capture_lineages"][1][
                "capture_lineage"
            ]["runtime_product_tree_sha256"] = "9" * 64

            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(prefix)
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_lineage_entry_binding_invalid",
            )

    def test_runtime_may_use_another_product_tree_but_not_another_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            two, incident, report, source_sha, _ = _inputs(root)
            prefix = compose_endgame_source_capture_prefix(
                two,
                incident,
                report,
                expected_incident_source_checkpoint_sha256=source_sha,
            )
            runtime = _canonical_lineage(
                "F" * 64,
                seed_lineage_id=RUNTIME_SEED_LINEAGE_ID,
            )
            result = preflight_endgame_source_capture_prefix(
                prefix, runtime_capture_lineage=runtime
            )
            self.assertEqual(result["result"], "GREEN")
            different_build = copy.deepcopy(runtime)
            different_build["game"]["exe_sha256"] = "1" * 64
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(
                    prefix, runtime_capture_lineage=different_build
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_runtime_lineage_mismatch",
            )


if __name__ == "__main__":
    unittest.main()
