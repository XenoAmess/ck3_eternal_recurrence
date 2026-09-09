from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from xar_promo.evidence import load_evidence_bundle_v2

from rmtm_promo.audit_evidence import AuditEvidenceError, build_audit_evidence


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class AuditEvidenceTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path]:
        deliverable = root / "deliverables" / "candidate.mp4"
        deliverable.parent.mkdir()
        deliverable.write_bytes(b"candidate video bytes")
        package_dir = root / "review"
        frames_dir = package_dir / "frames"
        frames_dir.mkdir(parents=True)
        rows = []
        for index, (timestamp, roles) in enumerate(
            [
                ("0.000000", ["artifact-first"]),
                ("6.000000", ["boundary-after"]),
                ("11.966667", ["artifact-final"]),
            ],
            start=1,
        ):
            frame = frames_dir / f"frame-{index:06d}.png"
            frame.write_bytes(f"frame {timestamp}".encode("ascii"))
            rows.append(
                {
                    "path": frame.relative_to(package_dir).as_posix(),
                    "timestamp_seconds": timestamp,
                    "roles": roles,
                    "bytes": frame.stat().st_size,
                    "sha256": _sha256(frame),
                }
            )
        package = package_dir / "review-package.json"
        package.write_text(
            json.dumps(
                {
                    "state": "pending-human-review",
                    "approval_granted": False,
                    "is_signoff": False,
                    "artifact": {
                        "bytes": deliverable.stat().st_size,
                        "sha256": _sha256(deliverable),
                    },
                    "frames": rows,
                }
            ),
            encoding="utf-8",
        )
        return deliverable, package

    def test_builds_hash_bound_v2_bundle_without_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            deliverable, package = self._fixture(root)
            output = root / "audit-evidence-a01"
            result = build_audit_evidence(
                project_root=root,
                deliverable=deliverable,
                review_package=package,
                output_directory=output,
                xar_promo_version="test",
            )
            self.assertEqual(3, result["sample_count"])
            self.assertFalse(result["approval_granted"])
            bundle, plan = load_evidence_bundle_v2(
                output / "evidence-bundle.json", project_root=root
            )
            self.assertEqual(3, len(bundle["entries"]))
            self.assertEqual(
                ["0.000000", "6.000000", "11.966667"],
                [row["timestamp_seconds"] for row in plan["samples"]],
            )

    def test_rejects_review_package_that_claims_approval(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            deliverable, package = self._fixture(root)
            payload = json.loads(package.read_text(encoding="utf-8"))
            payload["approval_granted"] = True
            package.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(AuditEvidenceError, "must not contain approval"):
                build_audit_evidence(
                    project_root=root,
                    deliverable=deliverable,
                    review_package=package,
                    output_directory=root / "audit-evidence-a01",
                    xar_promo_version="test",
                )


if __name__ == "__main__":
    unittest.main()
