#!/usr/bin/env python3
"""Unit tests for strict release-manifest verification."""

import json
import tempfile
import unittest
from pathlib import Path

import build_release


class ManifestVerificationTests(unittest.TestCase):
    DESCRIPTOR = b'version="1.0.0"\r\n'

    def fixture(self, descriptor, extra=False):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        target = root / "mod"
        target.mkdir()
        (target / "descriptor.mod").write_bytes(descriptor)
        if extra:
            (target / "unexpected.txt").write_text("extra", encoding="utf-8")
        manifest = {
            "format_version": 2,
            "mod_version": "1.0.0",
            "git_tag": "v1.0.0",
            "git_sha": "0" * 40,
            "workshop_item_id": build_release.WORKSHOP_ITEM_ID,
            "files": [{
                "path": "descriptor.mod",
                "size": len(self.DESCRIPTOR),
                "sha256": build_release.sha256_bytes(self.DESCRIPTOR),
            }],
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return temporary, target, manifest_path

    def test_exact_manifest_passes(self):
        temporary, target, manifest = self.fixture(self.DESCRIPTOR)
        with temporary:
            self.assertEqual(1, build_release.verify_manifest(target, manifest))

    def test_launcher_metadata_requires_opt_in(self):
        descriptor = (self.DESCRIPTOR.replace(b"\r\n", b"\n")
                      + b'remote_file_id="3784706360"')
        temporary, target, manifest = self.fixture(descriptor)
        with temporary:
            with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                build_release.verify_manifest(target, manifest)
            self.assertEqual(
                1, build_release.verify_manifest(
                    target, manifest, workshop_cache=True))

    def test_wrong_workshop_id_is_rejected(self):
        descriptor = self.DESCRIPTOR + b'remote_file_id="1"\r\n'
        temporary, target, manifest = self.fixture(descriptor)
        with temporary:
            with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                build_release.verify_manifest(
                    target, manifest, workshop_cache=True)

    def test_extra_file_is_rejected(self):
        descriptor = (self.DESCRIPTOR
                      + b'remote_file_id="3784706360"\r\n')
        temporary, target, manifest = self.fixture(descriptor, extra=True)
        with temporary:
            with self.assertRaisesRegex(ValueError, "extra: unexpected.txt"):
                build_release.verify_manifest(
                    target, manifest, workshop_cache=True)

    def test_descriptor_content_change_is_rejected(self):
        descriptor = (b'version="1.0.0"\nname="changed"\n'
                      b'remote_file_id="3784706360"')
        temporary, target, manifest = self.fixture(descriptor)
        with temporary:
            with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                build_release.verify_manifest(
                    target, manifest, workshop_cache=True)

    def test_remote_id_must_be_the_final_line(self):
        descriptor = (b'remote_file_id="3784706360"\n'
                      b'version="1.0.0"\n')
        temporary, target, manifest = self.fixture(descriptor)
        with temporary:
            with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                build_release.verify_manifest(
                    target, manifest, workshop_cache=True)


if __name__ == "__main__":
    unittest.main()
