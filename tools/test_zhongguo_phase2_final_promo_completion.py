from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zhongguo_phase2_final_promo_completion as completion  # noqa: E402


PUBLISH_TARGET = {
    "result": "GREEN",
    "authority": {"sha256": "B" * 64},
    "target": {
        "target_id": "video-target",
        "platform": "video-platform",
        "account_id": "publisher-account",
        "locator_prefix": "https://media.project-owner.net/watch/",
    },
}


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }


def _fixture(root: Path) -> Path:
    attempt_id = "phase2-final-001"
    candidate = root / "candidate" / "zhongguo-361-phase2.mp4"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"TEST-ONLY-NONMEDIA-CANDIDATE-BYTES")
    media = _record(candidate)
    probe = root / "candidate" / "bound-probe.json"
    _write(
        probe,
        {
            "format_version": 1,
            "kind": "xar-promo-bound-media-probe",
            "subject": {"bytes": media["bytes"], "sha256": media["sha256"]},
            "ffprobe": {
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "pix_fmt": "yuv420p",
                        "width": 1920,
                        "height": 1080,
                    },
                    {
                        "codec_type": "audio",
                        "codec_name": "aac",
                        "sample_rate": "48000",
                        "channels": 2,
                    },
                ],
                "format": {
                    "filename": str(candidate.resolve()),
                    "size": str(media["bytes"]),
                    "duration": "90.000",
                },
            },
        },
    )
    run = root / "candidate" / "run-manifest.json"
    _write(
        run,
        {
            "format_version": 1,
            "kind": "xar_promo_run_manifest",
            "run": {"id": attempt_id},
            "artifacts": [
                {
                    "id": completion.DELIVERABLE_ID,
                    "role": "deliverable",
                    "path": candidate.name,
                    "bytes": media["bytes"],
                    "sha256": media["sha256"],
                }
            ],
            "signoffs": [
                {
                    "artifact_id": completion.DELIVERABLE_ID,
                    "artifact_bytes": media["bytes"],
                    "artifact_sha256": media["sha256"],
                    "reviewer": "Release Owner",
                    "decision": "approved",
                    "reviewed_at": "2026-09-02T20:00:00+08:00",
                }
            ],
        },
    )
    audit = root / "candidate" / "claims-audit.json"
    _write(
        audit,
        {
            "format_version": 1,
            "kind": "xar_promo_audit_report",
            "subject": {"bytes": media["bytes"], "sha256": media["sha256"]},
            "automated_audit": {
                "status": "passed",
                "subject_sha256": media["sha256"],
                "manual_approval_granted": False,
            },
            "manual_signoff": {
                "state": "approved",
                "record": {
                    "artifact_bytes": media["bytes"],
                    "artifact_sha256": media["sha256"],
                },
            },
        },
    )
    reviews = []
    for index, (scope, reviewer) in enumerate(
        (
            ("claims-and-source-pass", "Reviewer One"),
            ("final-candidate-pass", "Reviewer Two"),
        ),
        start=1,
    ):
        receipt = root / "candidate" / f"review-{index}.json"
        _write(
            receipt,
            {
                "schema_version": 1,
                "kind": completion.REVIEW_KIND,
                "result": "GREEN",
                "attempt_id": attempt_id,
                "scope": scope,
                "playback_speed": 1,
                "full_duration_reviewed": True,
                "decision": "approved",
                "reviewer": reviewer,
                "reviewed_at": f"2026-09-02T2{index}:00:00+08:00",
                "candidate_media": {
                    "bytes": media["bytes"],
                    "sha256": media["sha256"],
                },
                "claims_audit_sha256": _record(audit)["sha256"],
            },
        )
        reviews.append(_record(receipt))
    bundle = root / "export"
    exported = bundle / "zhongguo-361-phase2.mp4"
    exported.parent.mkdir(parents=True)
    exported.write_bytes(candidate.read_bytes())
    export_manifest = bundle / completion.EXPORT_MANIFEST_NAME
    _write(
        export_manifest,
        {
            "format_version": 1,
            "kind": "xar_promo_release_bundle",
            "source_run": {
                "run_id": attempt_id,
                "bytes": _record(run)["bytes"],
                "sha256": _record(run)["sha256"],
                "project_config_sha256": "A" * 64,
            },
            "operations": {
                "network_used": False,
                "publish_performed": False,
                "source_material_mutated": False,
            },
            "files": [
                {
                    "category": "deliverable",
                    "path": exported.name,
                    "bytes": media["bytes"],
                    "sha256": media["sha256"],
                    "source": {
                        "kind": "run-artifact",
                        "artifact_id": completion.DELIVERABLE_ID,
                        "role": "deliverable",
                        "bytes": media["bytes"],
                        "sha256": media["sha256"],
                    },
                }
            ],
        },
    )
    publication = root / "publication.json"
    _write(
        publication,
        {
            "schema_version": 1,
            "kind": completion.PUBLISH_KIND,
            "result": "GREEN",
            "attempt_id": attempt_id,
            "target_id": "video-target",
            "platform": "video-platform",
            "account_id": "publisher-account",
            "target_authority_sha256": "B" * 64,
            "published_at": "2026-09-02T23:00:00+08:00",
            "locator": "https://media.project-owner.net/watch/phase2-final-001",
            "remote_verified": True,
            "candidate_media": {
                "bytes": media["bytes"],
                "sha256": media["sha256"],
            },
            "exported_media": {
                "bytes": media["bytes"],
                "sha256": media["sha256"],
            },
            "export_manifest": {
                "bytes": _record(export_manifest)["bytes"],
                "sha256": _record(export_manifest)["sha256"],
            },
        },
    )
    attestation = root / "completion-attestation.json"
    _write(
        attestation,
        {
            "schema_version": 1,
            "kind": completion.ATTESTATION_KIND,
            "attempt_id": attempt_id,
            "candidate": {
                "media": media,
                "bound_probe": _record(probe),
                "run_manifest": _record(run),
            },
            "claims_audit": _record(audit),
            "reviews": reviews,
            "export": {
                "bundle_root": str(bundle.resolve()),
                "manifest": _record(export_manifest),
            },
            "publication": _record(publication),
        },
    )
    return attestation


class FinalPromoCompletionTests(unittest.TestCase):
    def test_missing_attestation_has_typed_pending_gates(self) -> None:
        report = completion.validate_final_promo_completion(
            None, footage_intake={"result": "RED"}, publish_target={"result": "RED"}
        )
        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["reason_codes"][0], "footage_pending")
        self.assertEqual(tuple(report["reason_codes"][1:]), completion.PENDING_CODES)
        self.assertFalse(report["execution_attestation"]["media_generated"])

    def test_all_cross_bound_final_receipts_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            attestation = _fixture(Path(raw))
            report = completion.validate_final_promo_completion(
                attestation,
                footage_intake={"result": "GREEN"},
                publish_target=PUBLISH_TARGET,
            )
        self.assertEqual(report["result"], "GREEN", report)
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["reason_codes"], [])
        self.assertTrue(all(report["checks"].values()))

    def test_publish_locator_tamper_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            attestation = _fixture(root)
            outer = json.loads(attestation.read_text(encoding="utf-8"))
            publish_path = Path(outer["publication"]["path"])
            publish = json.loads(publish_path.read_text(encoding="utf-8"))
            publish["locator"] = "local-only"
            _write(publish_path, publish)
            outer["publication"] = _record(publish_path)
            _write(attestation, outer)
            report = completion.validate_final_promo_completion(
                attestation,
                footage_intake={"result": "GREEN"},
                publish_target=PUBLISH_TARGET,
            )
        self.assertEqual(report["result"], "RED")
        self.assertIn("publish_pending", report["reason_codes"])
        self.assertFalse(report["checks"]["publish_verified"])

    def test_missing_publish_target_blocks_otherwise_complete_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            attestation = _fixture(Path(raw))
            report = completion.validate_final_promo_completion(
                attestation,
                footage_intake={"result": "GREEN"},
                publish_target={"result": "RED", "reason_code": "publish_target_pending"},
            )
        self.assertEqual(report["result"], "RED")
        self.assertIn("publish_target_pending", report["reason_codes"])
        self.assertFalse(report["checks"]["publish_target_verified"])
        self.assertFalse(report["checks"]["publish_verified"])


if __name__ == "__main__":
    unittest.main()
