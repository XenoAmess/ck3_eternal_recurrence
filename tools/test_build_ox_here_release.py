#!/usr/bin/env python3
"""Unit tests for the standalone Ox Here! release builder."""

from __future__ import annotations

import codecs
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from unittest import mock


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ox_here_release as release  # noqa: E402


REVISION = "a" * 40
WORKSHOP_ID = "987654321"
DESCRIPTOR = b'version="1.0.1"\r\nname="Ox Here fixture"\r\npicture="thumbnail.png"\r\n'


class OxHereReleaseTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(prefix="ox-here-builder-test-") as name:
            root = Path(name)
            source = root / "source"
            source.mkdir()
            for relative in sorted(release.RUNTIME_FILES):
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative == "descriptor.mod":
                    data = DESCRIPTOR
                elif path.suffix.lower() in {".txt", ".yml"}:
                    data = codecs.BOM_UTF8 + f"ox_here_fixture_{path.stem} = {{}}\n".encode()
                else:
                    data = b"fixture thumbnail bytes"
                path.write_bytes(data)
            yield root, source

    def build(self, root, source, **kwargs):
        return release.build_release(
            source, root / kwargs.pop("parent", "build") / release.PRODUCT_ID,
            revision=REVISION, **kwargs
        )

    @staticmethod
    def launcher_descriptor(item_id=WORKSHOP_ID, separator=b"\n", final_newline=False):
        result = separator.join(DESCRIPTOR.splitlines()) + separator + f'remote_file_id="{item_id}"'.encode()
        return result + (separator if final_newline else b"")

    def test_exact_inventory_and_deterministic_build(self):
        self.assertEqual(17, len(release.RUNTIME_FILES))
        self.assertEqual(9, sum(path.startswith("localization/") for path in release.RUNTIME_FILES))
        with self.fixture() as (root, source):
            first = self.build(root, source, parent="first")
            second = self.build(root, source, parent="second")
            self.assertEqual(first[3], second[3])
            self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
            self.assertEqual(first[2].read_bytes(), second[2].read_bytes())
            self.assertEqual(17, release.verify_manifest(first[0], first[1]))
            self.assertEqual(release.PRODUCT_ID, first[3]["product_id"])
            self.assertIsNone(first[3]["workshop_item_id"])
            with zipfile.ZipFile(first[2]) as archive:
                self.assertEqual([f"ox_here/{path}" for path in sorted(release.RUNTIME_FILES)], [item.filename for item in archive.infolist()])
                self.assertTrue(all(item.date_time == release.ZIP_TIMESTAMP for item in archive.infolist()))

    def test_check_reproducible_and_versioned_sidecars(self):
        with self.fixture() as (root, source):
            result = release.check_reproducible(source, revision=REVISION)
            self.assertEqual(17, result["file_count"])
            self.assertRegex(result["manifest_sha256"], r"^[0-9a-f]{64}$")
            _, manifest, archive, details = self.build(root, source, parent="formal", versioned_sidecars=True, git_tag="ox-here-v1.0.1")
            self.assertEqual("ox_here-v1.0.1.manifest.json", manifest.name)
            self.assertEqual("ox_here-v1.0.1.zip", archive.name)
            self.assertEqual("ox-here-v1.0.1", details["git_tag"])

    def test_missing_assets_languages_and_any_extra_file_fail_closed(self):
        with self.fixture() as (_, source):
            source.joinpath("thumbnail.png").unlink()
            errors = release.release_source_errors(source)
            self.assertTrue(any("required runtime file missing: thumbnail.png" in error for error in errors))
        for relative in ("notes.md", "workshop/description.bbcode", "tools/helper.py", "events/ox_here.txt", "__pycache__/cached.pyc"):
            with self.subTest(relative=relative), self.fixture() as (_, source):
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"extra")
                errors = release.release_source_errors(source)
                self.assertTrue(any("outside exact runtime allowlist" in error for error in errors), errors)

    def test_source_readme_is_explicitly_excluded_from_staging(self):
        with self.fixture() as (root, source):
            source.joinpath("README.md").write_text("development notes", encoding="utf-8")
            self.assertEqual([], release.release_source_errors(source))
            staging, _, _, _ = self.build(root, source)
            self.assertFalse(staging.joinpath("README.md").exists())
            source.joinpath("README.md").unlink()
            source.joinpath("README.md").write_text("development notes", encoding="utf-8")
            self.assertTrue(any("outside exact runtime allowlist" in error for error in release.release_source_errors(source, allow_source_only_files=False)))

    def test_remote_id_and_both_existing_item_ids_are_rejected(self):
        for payload, message in ((b'remote_file_id="123"', "remote_file_id"), (b"3784706360", "3784706360"), (b"3787304042", "3787304042")):
            with self.subTest(payload=payload), self.fixture() as (_, source):
                path = source / "common/decisions/ox_here_decisions.txt"
                path.write_bytes(codecs.BOM_UTF8 + payload)
                self.assertTrue(any(message in error for error in release.release_source_errors(source)))
        with self.fixture() as (root, source):
            for old in sorted(release.FORBIDDEN_WORKSHOP_ITEM_IDS):
                with self.subTest(old=old), self.assertRaisesRegex(ValueError, "must not reuse"):
                    self.build(root, source, parent=old, workshop_item_id=old)

    def test_item_id_normalization_and_workshop_descriptor_exception_are_strict(self):
        with self.fixture() as (root, source):
            staging, manifest, _, details = self.build(root, source, workshop_item_id=WORKSHOP_ID)
            self.assertEqual(WORKSHOP_ID, details["workshop_item_id"])
            staging.joinpath("descriptor.mod").write_bytes(self.launcher_descriptor(separator=b"\r\n", final_newline=True))
            self.assertEqual(17, release.verify_manifest(staging, manifest, workshop_cache=True))
            self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod", release.verify_manifest, staging, manifest)
            for malformed in (
                self.launcher_descriptor("123"),
                DESCRIPTOR,
                b'remote_file_id="987654321"\n' + b"\n".join(DESCRIPTOR.splitlines()),
                b"\n".join(DESCRIPTOR.splitlines()) + b'\nremote_file_id="987654321"\nremote_file_id="987654321"',
            ):
                staging.joinpath("descriptor.mod").write_bytes(malformed)
                with self.subTest(malformed=malformed), self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                    release.verify_manifest(staging, manifest, workshop_cache=True)
            for bad in ("0", "0123", "not-digits", str(2**64)):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    self.build(root, source, parent="bad", workshop_item_id=bad)

    def test_manifest_and_formal_release_identity_are_strict(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(root, source)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"] = payload["files"][:-1]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                release.verify_manifest(staging, manifest)

            def clean_git(*args, **_kwargs):
                return "" if args[0] == "status" else "ox-here-v1.0.1"

            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(release, "git_sha", return_value=REVISION), mock.patch.object(release, "git_output", side_effect=clean_git):
                identity = release.release_identity(source)
            self.assertEqual("ox-here-v1.0.1", identity["git_tag"])
            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(release, "git_sha", return_value=REVISION), mock.patch.object(release, "git_output", return_value="dirty"):
                with self.assertRaisesRegex(ValueError, "clean worktree"):
                    release.release_identity(source)


if __name__ == "__main__":
    unittest.main()
