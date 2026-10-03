#!/usr/bin/env python3
"""Focused release projection tests with corrupted and excluded inputs."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import independent_mod_release as release


REVISION = "a" * 40
SCRIPT = "events/maintained.txt"
LOCALIZATION = "localization/simp_chinese/maintained_l_simp_chinese.yml"


class IndependentModReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.runtime = {"descriptor.mod", SCRIPT, LOCALIZATION, "thumbnail.png"}
        self.write("descriptor.mod", b'version="1.0.0"\nname="Maintained Mod"\nsupported_version="1.20.0.3"\n')
        self.write(SCRIPT, release.UTF8_BOM + b"namespace = maintained\n")
        self.write(LOCALIZATION, release.UTF8_BOM + 'l_simp_chinese:\n maintained_title:0 "维护版"\n'.encode())
        self.write("thumbnail.png", b"binary-preview-fixture")
        self.write("README.md", b"Source-only README\n")
        self.write("docs/upstream.md", b"source item 3600021457, original remote_file_id preserved outside staging\n")
        self.write("tools/fixture.txt", b"namespace = acceptance\n")
        self.spec = release.ProductSpec("mod_maintained", self.source, self.runtime, "3600021457", "maintained-v")

    def write(self, relative: str, data: bytes) -> Path:
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def build(self, name: str = "build"):
        return release.build(self.spec, self.root / name / self.spec.product_id, REVISION, "3809999999")

    def test_production_projection_and_archive_have_only_reviewed_runtime(self) -> None:
        staging, manifest, archive, payload = self.build()
        self.assertEqual(set(path.relative_to(staging).as_posix() for path in staging.rglob("*") if path.is_file()), self.runtime)
        self.assertEqual(payload["workshop_item_id"], "3809999999")
        self.assertEqual(release.verify_manifest(self.spec, staging, manifest), 4)
        with zipfile.ZipFile(archive) as stream:
            self.assertEqual(set(stream.namelist()), {self.spec.product_id + "/" + path for path in self.runtime})
            for entry in stream.infolist():
                self.assertEqual(entry.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(entry.external_attr >> 16, 0o100644)
                self.assertEqual(stream.read(entry), (self.source / entry.filename.split("/", 1)[1]).read_bytes())

    def test_second_build_matches_manifest_and_zip_even_after_source_mtime_change(self) -> None:
        import os

        first = self.build("first")
        for path in self.source.rglob("*"):
            if path.is_file():
                os.utime(path, (500000000, 500000000))
        second = self.build("second")
        self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
        self.assertEqual(first[2].read_bytes(), second[2].read_bytes())
        checked = release.check_reproducible(self.spec, REVISION, "3809999999")
        self.assertEqual(checked["manifest_sha256"], release.sha256_file(first[1]))
        self.assertEqual(checked["zip_sha256"], release.sha256_file(first[2]))

    def test_extra_runtime_source_file_is_rejected_without_creating_output(self) -> None:
        self.write("events/unreviewed.txt", release.UTF8_BOM + b"namespace = unexpected\n")
        with self.assertRaisesRegex(ValueError, "file outside allowlist"):
            self.build()
        self.assertFalse((self.root / "build").exists())

    def test_runtime_identity_never_reuses_upstream_or_inner_remote_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "upstream Workshop item"):
            release.build(self.spec, self.root / "bad-id", REVISION, "3600021457")
        for payload, message in (
            (b'remote_file_id="3809999999"\n', "remote_file_id"),
            (b"# upstream 3600021457\n", "upstream Workshop identity"),
        ):
            with self.subTest(message=message):
                self.write(SCRIPT, release.UTF8_BOM + payload)
                with self.assertRaisesRegex(ValueError, message):
                    self.build()

    def test_original_product_has_no_upstream_identity_and_accepts_a_new_item(self) -> None:
        original = replace(self.spec, upstream_item_id=None)
        self.assertEqual(release.source_errors(original), [])
        staging, manifest, _, payload = release.build(original, self.root / "original", REVISION, "3600021457")
        self.assertIsNone(original.upstream_item_id)
        self.assertEqual(payload["workshop_item_id"], "3600021457")
        self.assertEqual(release.verify_manifest(original, staging, manifest), 4)
        self.assertNotIn("upstream_item_id", payload)

    def test_bom_and_utf8_contract_rejects_bad_script_localization_and_descriptor(self) -> None:
        original = {path: (self.source / path).read_bytes() for path in (SCRIPT, LOCALIZATION, "descriptor.mod")}
        for path, data, message in (
            (SCRIPT, b"namespace = maintained\n", "lacks UTF-8 BOM"),
            (LOCALIZATION, release.UTF8_BOM + b"\xff", "not UTF-8"),
            ("descriptor.mod", release.UTF8_BOM + original["descriptor.mod"], "descriptor.mod must not have"),
        ):
            with self.subTest(path=path):
                self.write(path, data)
                with self.assertRaisesRegex(ValueError, message):
                    self.build()
                self.write(path, original[path])

    def test_verifier_rejects_same_size_changed_bytes_missing_and_extra_files(self) -> None:
        staging, manifest, _, _ = self.build()
        script = staging / SCRIPT
        original = script.read_bytes()
        script.write_bytes(original[:-1] + b"X")
        with self.assertRaisesRegex(ValueError, "mismatch: events/maintained.txt"):
            release.verify_manifest(self.spec, staging, manifest)
        script.write_bytes(original)
        script.unlink()
        with self.assertRaisesRegex(ValueError, "missing: events/maintained.txt"):
            release.verify_manifest(self.spec, staging, manifest)
        script.write_bytes(original)
        (staging / "unexpected.txt").write_bytes(b"unexpected")
        with self.assertRaisesRegex(ValueError, "extra file: unexpected.txt"):
            release.verify_manifest(self.spec, staging, manifest)

    def test_manifest_rejects_wrong_product_duplicate_inventory_and_boolean_size(self) -> None:
        staging, manifest, _, payload = self.build()
        for field, value, message in (
            ("product_id", "mod_another", "identity mismatch"),
            ("workshop_item_id", "3600021457", "upstream Workshop item"),
            ("files", [*payload["files"], payload["files"][0]], "inventory mismatch"),
            ("files", [{**payload["files"][0], "size": True}, *payload["files"][1:]], "entry is invalid"),
        ):
            with self.subTest(field=field, message=message):
                manifest.write_text(json.dumps({**payload, field: value}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    release.verify_manifest(self.spec, staging, manifest)

    def test_build_does_not_overwrite_output_or_write_inside_source(self) -> None:
        staging, manifest, archive, _ = self.build()
        before = {path: path.read_bytes() for path in (staging / SCRIPT, manifest, archive)}
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.build()
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        for output in (self.source / "dist", self.root):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "must not contain"):
                    release.build(self.spec, output, REVISION)
        self.assertFalse((self.source / "dist").exists())

    def test_specs_reject_escape_case_collision_and_source_only_runtime_paths(self) -> None:
        for paths in (
            {"descriptor.mod", "../escape.txt"},
            {"descriptor.mod", "events/a.txt", "events/A.txt"},
            {"descriptor.mod", "docs/fixture.txt"},
            {"descriptor.mod", "README.md"},
        ):
            with self.subTest(paths=paths):
                with self.assertRaises(ValueError):
                    replace(self.spec, runtime_files=paths)


if __name__ == "__main__":
    unittest.main(verbosity=2)
