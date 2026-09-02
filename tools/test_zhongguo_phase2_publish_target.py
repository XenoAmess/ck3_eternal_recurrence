from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zhongguo_phase2_publish_target as target  # noqa: E402


def _authority() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": target.AUTHORITY_KIND,
        "target_id": "owner-selected-video-destination",
        "platform": "owner-selected-platform",
        "account_id": "owner-selected-account",
        "locator_prefix": "https://video.example.test.invalid/watch/",
        "authorization": {
            "upload_authorized": True,
            "approved_by": "Project Owner",
            "approved_at": "2026-09-02T23:00:00+08:00",
        },
        "credentials": {
            "reference": "operator-secret-store:item",
            "availability_verified": True,
            "verified_at": "2026-09-02T23:01:00+08:00",
        },
        "publication_receipt": {
            "schema_version": 1,
            "kind": target.RECEIPT_KIND,
            "remote_verification_required": True,
        },
    }


class PublishTargetTests(unittest.TestCase):
    def test_missing_authority_is_typed_pending_and_read_only(self) -> None:
        report = target.validate_publish_target_authority(None)
        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["reason_code"], "publish_target_pending")
        self.assertFalse(report["execution_attestation"]["network_used"])
        self.assertFalse(report["execution_attestation"]["upload_performed"])

    def test_complete_explicit_authority_is_green(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "authority.json"
            payload = _authority()
            payload["locator_prefix"] = "https://media.project-owner.net/watch/"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = target.validate_publish_target_authority(path)
        self.assertEqual(report["result"], "GREEN", report)
        self.assertEqual(report["target"]["target_id"], payload["target_id"])

    def test_placeholder_locator_and_missing_credential_stay_pending(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "authority.json"
            payload = _authority()
            payload["credentials"]["reference"] = ""
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = target.validate_publish_target_authority(path)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["locator_prefix_explicit"])
        self.assertFalse(report["checks"]["credential_reference_present"])


if __name__ == "__main__":
    unittest.main()
