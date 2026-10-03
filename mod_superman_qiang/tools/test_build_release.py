"""Corruption and reproducibility tests for Superman Qiang's release boundary."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from product import REPO, RUNTIME_FILES, SOURCE, VERSION, spec
import sys

sys.path.insert(0, str(REPO / "tools"))
import independent_mod_release as release

REVISION = "a" * 40


class SupermanReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="sxad-release-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        shutil.copytree(SOURCE, self.source)
        self.product = replace(spec(), source=self.source)

    def build(self, name: str = "build"):
        return release.build(self.product, self.root / name, REVISION, git_tag="superman-qiang-v" + VERSION)

    def test_release_has_exact_allowlist_and_excludes_source_and_fixture_assets(self) -> None:
        fixture = self.source / "tools" / "fixture" / "sxadt_test.txt"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text("namespace = sxadt\n", encoding="utf-8-sig")
        staging, manifest, archive, payload = self.build()
        paths = {path.relative_to(staging).as_posix() for path in staging.rglob("*") if path.is_file()}
        self.assertEqual(paths, RUNTIME_FILES)
        self.assertEqual(len(payload["files"]), len(RUNTIME_FILES))
        self.assertIsNone(payload["workshop_item_id"])
        self.assertEqual(release.verify_manifest(self.product, staging, manifest), len(RUNTIME_FILES))
        self.assertNotIn("remote_file_id", (staging / "descriptor.mod").read_text(encoding="utf-8-sig"))
        with zipfile.ZipFile(archive) as stream:
            self.assertEqual(set(stream.namelist()), {self.product.product_id + "/" + path for path in RUNTIME_FILES})
            for entry in stream.infolist():
                self.assertEqual(entry.date_time, release.ZIP_TIMESTAMP)

    def test_manifest_and_archive_are_byte_reproducible(self) -> None:
        first, second = self.build("one"), self.build("two")
        self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
        self.assertEqual(first[2].read_bytes(), second[2].read_bytes())

    def test_mutated_staging_is_rejected_even_with_same_file_size(self) -> None:
        staging, manifest, _, _ = self.build()
        counter = staging / "common/scripted_effects/sxad_experience_effects.txt"
        original = counter.read_bytes()
        counter.write_bytes(original[:-1] + (b"X" if original[-1:] != b"X" else b"Y"))
        with self.assertRaisesRegex(ValueError, "mismatch"):
            release.verify_manifest(self.product, staging, manifest)

    def test_descriptor_workshop_id_and_unreviewed_runtime_are_rejected(self) -> None:
        descriptor = self.source / "descriptor.mod"
        original = descriptor.read_bytes()
        descriptor.write_bytes(original + b'remote_file_id="3800000000"\n')
        with self.assertRaisesRegex(ValueError, "remote_file_id"):
            self.build()
        descriptor.write_bytes(original)
        extra = self.source / "events" / "sxadt_test.txt"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("namespace = sxadt\n", encoding="utf-8-sig")
        with self.assertRaisesRegex(ValueError, "outside allowlist"):
            self.build()

    def test_existing_attempt_and_wrong_product_tag_are_rejected(self) -> None:
        _, manifest, archive, _ = self.build()
        before = (manifest.read_bytes(), archive.read_bytes())
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.build()
        self.assertEqual(before, (manifest.read_bytes(), archive.read_bytes()))
        with self.assertRaisesRegex(ValueError, "git_tag"):
            release.build(self.product, self.root / "wrong-tag", REVISION, git_tag="v1.0.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
