from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import project_delivery_state as state  # noqa: E402


class ProjectDeliveryStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = json.loads(state.DEFAULT_SOURCE.read_text(encoding="utf-8"))

    def _red_indexes(self) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
        indexes: dict[str, dict[str, object]] = {}
        refs: dict[str, dict[str, object]] = {}
        for raw_spec in self.source["red_indexes"]:
            index = state.build_red_index(
                raw_spec,
                repo_root=state.ROOT,
                workspace_root=state.ROOT.parent,
            )
            red_id = index["red_id"]
            output = state.DEFAULT_RED_INDEX_DIR / raw_spec["output_name"]
            indexes[red_id] = index
            refs[red_id] = state.artifact_ref_from_bytes(
                output, state._json_bytes(index), root=state.ROOT
            )
        return indexes, refs

    def _ledger(self) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
        _indexes, refs = self._red_indexes()
        source = copy.deepcopy(self.source["p2"])
        source["updated_at"] = self.source["updated_at"]
        return state.build_p2_ledger(source, red_index_refs=refs), refs

    def test_canonical_projection_keeps_fixed_denominators_separate(self) -> None:
        ledger, _refs = self._ledger()
        self.assertEqual(
            ledger["shared"]["source_lineage"]["summary"],
            {"result": "GREEN", "passed": 4, "required": 4, "red": 0},
        )
        self.assertEqual(
            ledger["shared"]["raw_capture"]["summary"],
            {"result": "PENDING", "passed": 0, "required": 8, "red": 0},
        )
        self.assertEqual(ledger["cut_stage_summaries"]["publication"], {"passed": 0, "required": 2})
        self.assertTrue(ledger["invariants"]["source_lineage_is_not_raw_footage"])
        self.assertEqual(ledger["result"], "ACTIVE")

    def test_compact_red_index_has_three_axes_and_no_product_result(self) -> None:
        indexes, _refs = self._red_indexes()
        index = indexes["R506-source-event-scalar-scope-invalid"]
        self.assertEqual(index["result"], "RED")
        self.assertEqual(index["red_class"], "HARNESS_RED")
        self.assertEqual(index["axes"], {
            "business_result": "NOT_EVALUATED",
            "harness_result": "RED",
            "lifecycle_result": "ACTIVE",
        })
        self.assertNotIn("product_result", index)
        self.assertFalse(index["input_attempted"])
        self.assertFalse(index["resolution"]["current_blocker"])
        self.assertEqual(index["resolution"]["closing_round"], "R508")
        self.assertLess(len(state._json_bytes(index)), 10 * 1024)

    def test_artifact_verification_uses_content_address_not_locator_alone(self) -> None:
        spec = copy.deepcopy(self.source["red_indexes"][0])
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            detail = workspace / "detail.json"
            detail.write_text("{}\n", encoding="utf-8")
            spec["detail_artifact_ref"] = {
                "base": "workspace_root",
                "locator": "detail.json",
                "bytes": detail.stat().st_size,
                "sha256": "0" * 64,
            }
            with self.assertRaisesRegex(state.ProjectionError, "SHA-256 changed"):
                state.build_red_index(
                    spec,
                    repo_root=state.ROOT,
                    workspace_root=workspace,
                    verify_artifacts=True,
                )

    def test_signed_p1_cannot_be_silently_reopened_or_undercounted(self) -> None:
        ledger, refs = self._ledger()
        source = copy.deepcopy(self.source)
        source["t0_p1"]["passed"] = 8
        p2_ref = state.artifact_ref_from_bytes(
            state.DEFAULT_P2_LEDGER, state._json_bytes(ledger), root=state.ROOT
        )
        with self.assertRaisesRegex(state.ProjectionError, "must remain 9/9"):
            state.build_current_state(
                source,
                p2_ledger=ledger,
                p2_ledger_ref=p2_ref,
                red_index_refs=refs,
            )

    def test_checked_in_outputs_match_the_single_source(self) -> None:
        ledger, refs = self._ledger()
        p2_bytes = state._json_bytes(ledger)
        p2_ref = state.artifact_ref_from_bytes(
            state.DEFAULT_P2_LEDGER, p2_bytes, root=state.ROOT
        )
        current = state.build_current_state(
            self.source,
            p2_ledger=ledger,
            p2_ledger_ref=p2_ref,
            red_index_refs=refs,
        )
        self.assertEqual(state.DEFAULT_P2_LEDGER.read_bytes(), p2_bytes)
        self.assertEqual(state.DEFAULT_CURRENT.read_bytes(), state._json_bytes(current))
        self.assertIsNone(current["red"]["current"])
        self.assertEqual(current["red"]["unresolved_count"], 0)
        self.assertIsNone(current["ck3"]["stable_projection"]["live_round"])
        self.assertEqual(current["ck3"]["stable_projection"]["instance_count"], 0)
        for raw_spec in self.source["red_indexes"]:
            output = state.DEFAULT_RED_INDEX_DIR / raw_spec["output_name"]
            red_id = raw_spec["red_id"]
            indexes, _refs = self._red_indexes()
            self.assertEqual(output.read_bytes(), state._json_bytes(indexes[red_id]))

    def test_work_package_declares_resources_and_coordinator_report_writers(self) -> None:
        package = json.loads(
            (
                state.ROOT
                / "docs/project-state/work-packages/2026-09-12-workflow-state-projection.json"
            ).read_text(encoding="utf-8")
        )
        validated = state.validate_work_package_resource(package)
        self.assertFalse(validated["requires_ck3"])
        self.assertEqual(validated["report_writers"]["daily"], "coordinator")
        bad = copy.deepcopy(package)
        bad["report_writers"]["weekly"] = "worker"
        with self.assertRaisesRegex(state.ProjectionError, "weekly report"):
            state.validate_work_package_resource(bad)


if __name__ == "__main__":
    unittest.main()
