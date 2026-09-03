from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zhongguo_phase2_promo_delivery_queue as queue  # noqa: E402
from zhongguo_phase2_promo_cuts import CUTS  # noqa: E402


def _runbook(cut_id: str, *, footage: str = "RED", blockers: list[str] | None = None) -> dict[str, object]:
    cut = next(item for item in CUTS if item.cut_id == cut_id)
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_final_promo_deterministic_runbook",
        "result": "GREEN" if footage == "GREEN" and not blockers else "RED",
        "status": "COMPLETE" if footage == "GREEN" and not blockers else "waiting-for-inputs",
        "reason_code": None if footage == "GREEN" and not blockers else (blockers or ["footage_pending"])[0],
        "blockers": list(blockers or ([] if footage == "GREEN" else ["footage_pending"])),
        "cut": {
            "id": cut_id,
            "run_id": cut.default_run_id,
            "deliverable_artifact_id": cut.deliverable_artifact_id,
            "deliverable_relative_path": cut.deliverable_relative_path.as_posix(),
        },
        "editorial_plan": {"chapter_order": list(cut.editorial_chapter_order)},
        "project": {"checks": {"project_shape": True}},
        "authoring_claim_ledger": {"checks": {"ledger_shape": True}},
        "completion_gate": {"checks": {"candidate": footage == "GREEN"}},
        "inputs": {
            "capture": {
                "result": footage,
                "capture_root": None,
            }
        },
    }


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Phase2PromoDeliveryQueueTests(unittest.TestCase):
    def test_missing_capture_exposes_each_span_and_shared_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            character = root / "character.json"
            institution = root / "institution.json"
            _write(character, _runbook("character-led"))
            _write(institution, _runbook("institution-led"))

            report = queue.build_delivery_queue(character, institution)

        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["status"], "BLOCKED")
        shared = report["shared"]
        self.assertEqual(shared["spans_green"], 0)
        self.assertEqual(shared["spans_total"], 8)
        self.assertEqual(len(shared["missing_span_ids"]), 8)
        self.assertEqual(shared["next_action"]["id"], "capture_eight_clean_spans")
        self.assertEqual(len(shared["span_status"]), 8)
        self.assertTrue(all(row["status"] == "pending" for row in shared["span_status"]))
        self.assertTrue(all(row["mcp_queries"] for row in shared["span_status"]))
        self.assertTrue(all(row["next_action"]["id"] == "capture_eight_clean_spans" for row in report["cuts"]))
        self.assertFalse(report["execution_attestation"]["ck3_started"])
        self.assertFalse(report["execution_attestation"]["ffmpeg_started"])

    def test_green_capture_moves_queue_to_cut_specific_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            character = root / "character.json"
            institution = root / "institution.json"
            _write(character, _runbook("character-led", footage="GREEN", blockers=["publish_target_pending"]))
            _write(institution, _runbook("institution-led", footage="GREEN", blockers=["publish_target_pending"]))
            # A minimal intake object is injected through the module boundary
            # to test queue logic without manufacturing a capture bundle.
            original = queue.validate_footage_intake
            queue.validate_footage_intake = lambda _path: {
                "result": "GREEN",
                "reason_code": None,
                "spans": [
                    {
                        "span_id": scenario.span_id,
                        "clean_gate_green": True,
                        "postcondition_green": True,
                    }
                    for scenario in queue.PHASE2_CAPTURE_SCENARIOS
                ],
            }
            try:
                report = queue.build_delivery_queue(character, institution)
            finally:
                queue.validate_footage_intake = original

        self.assertEqual(report["shared"]["spans_green"], 8)
        self.assertEqual(report["shared"]["next_action"]["id"], "complete")
        for cut in report["cuts"]:
            self.assertEqual(cut["status"], "IN_PROGRESS")
            self.assertEqual(cut["next_action"]["id"], "source_footage_human_review_1x")
        self.assertEqual(report["status"], "IN_PROGRESS")

    def test_wrong_cut_order_is_invalid_and_never_reported_complete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            character = root / "character.json"
            institution = root / "institution.json"
            _write(character, _runbook("institution-led", footage="GREEN"))
            _write(institution, _runbook("character-led", footage="GREEN"))
            original = queue.validate_footage_intake
            queue.validate_footage_intake = lambda _path: {
                "result": "GREEN",
                "reason_code": None,
                "spans": [
                    {
                        "span_id": scenario.span_id,
                        "clean_gate_green": True,
                        "postcondition_green": True,
                    }
                    for scenario in queue.PHASE2_CAPTURE_SCENARIOS
                ],
            }
            try:
                report = queue.build_delivery_queue(character, institution)
            finally:
                queue.validate_footage_intake = original

        self.assertEqual(report["result"], "RED")
        self.assertIn("cut_order_must_be_character_then_institution", report["shared"]["errors"])
        self.assertTrue(all(cut["status"] == "INVALID" for cut in report["cuts"]))

    def test_green_capture_walks_declared_dependencies_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            character = root / "character.json"
            institution = root / "institution.json"
            _write(character, _runbook("character-led", footage="GREEN"))
            _write(institution, _runbook("institution-led", footage="GREEN"))
            paths = {
                "source_review_receipt": root / "source-review.json",
                "promoted_project_config": root / "promoted-project.json",
                "media_preflight_receipt": root / "media-preflight.json",
                "tts_prime_receipt": root / "tts-prime.json",
                "candidate_run_manifest": root / "candidate" / "run-manifest.json",
                "automated_audit_report": root / "candidate" / "audit.json",
                "claims_source_review_receipt": root / "candidate" / "review-1.json",
                "final_candidate_review_receipt": root / "candidate" / "review-2.json",
                "export_directory": root / "export",
            }
            for runbook_path in (character, institution):
                payload = json.loads(runbook_path.read_text(encoding="utf-8"))
                payload["planned_paths"] = {
                    key: str(path.resolve()) for key, path in paths.items()
                }
                payload["inputs"]["publish_target_authority"] = {"result": "RED"}
                _write(runbook_path, payload)

            original = queue.validate_footage_intake
            queue.validate_footage_intake = lambda _path: {
                "result": "GREEN",
                "reason_code": None,
                "spans": [
                    {
                        "span_id": scenario.span_id,
                        "clean_gate_green": True,
                        "postcondition_green": True,
                    }
                    for scenario in queue.PHASE2_CAPTURE_SCENARIOS
                ],
            }
            try:
                def current_action() -> str:
                    return queue.build_delivery_queue(character, institution)["cuts"][0]["next_action"]["id"]

                expected = (
                    ("source_review_receipt", "source_footage_human_review_1x"),
                    ("promoted_project_config", "promote_reviewed_authoring_into_project"),
                    ("media_preflight_receipt", "refresh_media_receipt_after_fetch"),
                    ("tts_prime_receipt", "prime_reviewed_xiaoxiao_cache"),
                    ("candidate_run_manifest", "build_unreviewed_candidate"),
                    ("automated_audit_report", "claims_audit_pending"),
                    ("claims_source_review_receipt", "review_round_1_pending"),
                    ("final_candidate_review_receipt", "review_round_2_pending"),
                )
                for path_name, action_id in expected:
                    self.assertEqual(current_action(), action_id)
                    path = paths[path_name]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("{}\n", encoding="utf-8")
                self.assertEqual(current_action(), "export_pending")
                paths["export_directory"].mkdir(parents=True)
                (paths["export_directory"] / "release-bundle-manifest.json").write_text(
                    "{}\n", encoding="utf-8"
                )
                self.assertEqual(current_action(), "publish_target_pending")
                for runbook_path in (character, institution):
                    payload = json.loads(runbook_path.read_text(encoding="utf-8"))
                    payload["inputs"]["publish_target_authority"] = {"result": "GREEN"}
                    payload["result"] = "GREEN"
                    payload["status"] = "COMPLETE"
                    _write(runbook_path, payload)
                self.assertEqual(current_action(), "complete")
            finally:
                queue.validate_footage_intake = original


if __name__ == "__main__":
    unittest.main()
