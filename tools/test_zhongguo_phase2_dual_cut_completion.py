from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zhongguo_phase2_dual_cut_completion as dual  # noqa: E402
from test_zhongguo_phase2_final_promo_completion import (  # noqa: E402
    PUBLISH_TARGET,
    _fixture as single_receipt_fixture,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }


def _single_report(root: Path, role: str, marker: bytes, run_id: str) -> Path:
    name = dual.OUTPUT_NAMES[role]
    candidate = root / "candidate" / name
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(marker)
    media = _record(candidate)
    bundle = root / "export"
    exported = bundle / name
    exported.parent.mkdir(parents=True)
    exported.write_bytes(marker)
    export_manifest = bundle / "release-bundle-manifest.json"
    _write(
        export_manifest,
        {
            "format_version": 1,
            "kind": "xar_promo_release_bundle",
            "files": [
                {
                    "category": "deliverable",
                    "path": name,
                    "bytes": media["bytes"],
                    "sha256": media["sha256"],
                }
            ],
        },
    )
    attestation = root / "completion-attestation.json"
    _write(
        attestation,
        {
            "schema_version": 1,
            "kind": "zg361_phase2_final_promo_completion_attestation",
            "attempt_id": run_id,
            "candidate": {"media": media},
            "export": {
                "bundle_root": str(bundle.resolve()),
                "manifest": _record(export_manifest),
            },
        },
    )
    report = root / "completion-report.json"
    _write(
        report,
        {
            "schema_version": 1,
            "kind": "zg361_phase2_final_promo_completion",
            "result": "GREEN",
            "status": "COMPLETE",
            "reason_codes": [],
            "deliverable_artifact_id": dual.DELIVERABLE_IDS[role],
            "attestation": _record(attestation),
            "candidate_media": media,
            "checks": {
                "footage_green": True,
                "candidate_media_verified": True,
                "claims_audit_verified": True,
                "review_round_1_verified": True,
                "review_round_2_verified": True,
                "export_verified": True,
                "publish_target_verified": True,
                "publish_verified": True,
            },
        },
    )
    return report


def _dual_fixture(root: Path) -> Path:
    shared = root / "shared-eight-spans"
    source_rows = []
    for index, span_id in enumerate(
        row.span_id for row in dual.PHASE2_CAPTURE_SCENARIOS
    ):
        media = shared / f"{index + 1:02d}-{span_id}.mkv"
        media.parent.mkdir(parents=True, exist_ok=True)
        media.write_bytes(f"REAL-SOURCE-SPAN-{span_id}".encode())
        source_rows.append({"span_id": span_id, "media": _record(media)})
    cuts = []
    for role, marker, run_id in (
        ("character-led", b"CHARACTER-CUT", "phase2-character-001"),
        ("institution-led", b"INSTITUTION-CUT", "phase2-institution-001"),
    ):
        work = root / role
        report = _single_report(work, role, marker, run_id)
        cuts.append(
            {
                "role": role,
                "output_name": dual.OUTPUT_NAMES[role],
                "work_dir": str(work.resolve()),
                "completion": {"mode": "report", "report": _record(report)},
                "source_spans": source_rows,
            }
        )
    attestation = root / "dual-attestation.json"
    _write(
        attestation,
        {
            "schema_version": 1,
            "kind": dual.ATTESTATION_KIND_DUAL,
            "cuts": cuts,
        },
    )
    return attestation


class DualCutCompletionTests(unittest.TestCase):
    def test_two_independent_cuts_may_share_exact_eight_source_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            report = dual.validate_dual_cut_completion(_dual_fixture(Path(raw)))
        self.assertEqual(report["result"], "GREEN", report)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(
            report["cuts"][0]["source_spans"],
            report["cuts"][1]["source_spans"],
        )
        self.assertEqual(
            [row["deliverable_artifact_id"] for row in report["cuts"]],
            [dual.DELIVERABLE_IDS[role] for role in dual.ROLES],
        )

    def test_report_with_wrong_deliverable_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _dual_fixture(root)
            outer = json.loads(attestation.read_text(encoding="utf-8"))
            report_path = Path(outer["cuts"][0]["completion"]["report"]["path"])
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["deliverable_artifact_id"] = dual.DELIVERABLE_IDS[
                "institution-led"
            ]
            _write(report_path, report)
            outer["cuts"][0]["completion"]["report"] = _record(report_path)
            _write(attestation, outer)
            result = dual.validate_dual_cut_completion(attestation)
        self.assertEqual(result["result"], "RED")
        self.assertIn(
            "deliverable_artifact_id_invalid", result["cuts"][0]["errors"]
        )

    def test_same_candidate_sha_cannot_impersonate_two_cuts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _dual_fixture(root)
            outer = json.loads(attestation.read_text(encoding="utf-8"))
            second = outer["cuts"][1]
            second_report_path = Path(second["completion"]["report"]["path"])
            second_report = json.loads(second_report_path.read_text(encoding="utf-8"))
            first_report_path = Path(outer["cuts"][0]["completion"]["report"]["path"])
            first_report = json.loads(first_report_path.read_text(encoding="utf-8"))
            second_report["candidate_media"]["sha256"] = first_report["candidate_media"]["sha256"]
            second_report["candidate_media"]["bytes"] = first_report["candidate_media"]["bytes"]
            # A forged summary cannot satisfy the underlying file binding.
            _write(second_report_path, second_report)
            second["completion"]["report"] = _record(second_report_path)
            _write(attestation, outer)
            report = dual.validate_dual_cut_completion(attestation)
        self.assertEqual(report["result"], "RED")
        self.assertIn("both_cuts_pending", report["reason_codes"])

    def test_duplicate_run_id_and_work_dir_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _dual_fixture(root)
            outer = json.loads(attestation.read_text(encoding="utf-8"))
            first_work = outer["cuts"][0]["work_dir"]
            outer["cuts"][1]["work_dir"] = first_work
            second_report_path = Path(outer["cuts"][1]["completion"]["report"]["path"])
            second_report = json.loads(second_report_path.read_text(encoding="utf-8"))
            second_attestation_path = Path(second_report["attestation"]["path"])
            second_attestation = json.loads(second_attestation_path.read_text(encoding="utf-8"))
            second_attestation["attempt_id"] = "phase2-character-001"
            _write(second_attestation_path, second_attestation)
            second_report["attestation"] = _record(second_attestation_path)
            _write(second_report_path, second_report)
            outer["cuts"][1]["completion"]["report"] = _record(second_report_path)
            _write(attestation, outer)
            report = dual.validate_dual_cut_completion(attestation)
        self.assertFalse(report["checks"]["run_ids_distinct"])
        self.assertFalse(report["checks"]["work_dirs_distinct"])
        self.assertEqual(report["status"], "pending")

    def test_one_incomplete_cut_blocks_dual_completion(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _dual_fixture(root)
            outer = json.loads(attestation.read_text(encoding="utf-8"))
            report_path = Path(outer["cuts"][1]["completion"]["report"]["path"])
            single = json.loads(report_path.read_text(encoding="utf-8"))
            single["result"] = "RED"
            single["status"] = "pending"
            single["reason_codes"] = ["publish_pending"]
            _write(report_path, single)
            outer["cuts"][1]["completion"]["report"] = _record(report_path)
            _write(attestation, outer)
            report = dual.validate_dual_cut_completion(attestation)
        self.assertFalse(report["checks"]["both_individually_complete"])
        self.assertEqual(report["result"], "RED")

    def test_a_changed_source_span_is_not_the_shared_immutable_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _dual_fixture(root)
            outer = json.loads(attestation.read_text(encoding="utf-8"))
            changed = root / "changed-span.mkv"
            changed.write_bytes(b"DIFFERENT-SOURCE")
            outer["cuts"][1]["source_spans"][3]["media"] = _record(changed)
            _write(attestation, outer)
            report = dual.validate_dual_cut_completion(attestation)
        self.assertFalse(report["checks"]["same_eight_immutable_source_spans"])
        self.assertEqual(report["result"], "RED")

    def test_exact_receipt_mode_reuses_the_existing_single_cut_gate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = single_receipt_fixture(root / "single")
            footage = root / "footage.json"
            target = root / "target.json"
            _write(footage, {"result": "GREEN"})
            _write(target, PUBLISH_TARGET)
            report, error = dual._single_report(
                {
                    "completion": {
                        "mode": "receipts",
                        "attestation": _record(attestation),
                        "footage_intake": _record(footage),
                        "publish_target": _record(target),
                    }
                }
            )
        self.assertEqual(error, "")
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "COMPLETE")

    def test_receipt_mode_rejects_another_roles_deliverable_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = single_receipt_fixture(root / "single")
            footage = root / "footage.json"
            target = root / "target.json"
            _write(footage, {"result": "GREEN"})
            _write(target, PUBLISH_TARGET)
            report, error = dual._single_report(
                {
                    "completion": {
                        "mode": "receipts",
                        "attestation": _record(attestation),
                        "footage_intake": _record(footage),
                        "publish_target": _record(target),
                        "deliverable_id": dual.DELIVERABLE_IDS[
                            "institution-led"
                        ],
                    }
                },
                "character-led",
            )
        self.assertIsNone(report)
        self.assertEqual(error, "completion_deliverable_id_invalid")

    def test_cli_refuses_to_overwrite_existing_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _dual_fixture(root)
            output = root / "result.json"
            output.write_text("KEEP", encoding="utf-8")
            process = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "zhongguo_phase2_dual_cut_completion.py"),
                    "--input",
                    str(attestation),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("refusing to overwrite", process.stderr)


if __name__ == "__main__":
    unittest.main()
