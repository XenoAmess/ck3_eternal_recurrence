#!/usr/bin/env python3
"""Unit tests for the standalone Vivhite release builder and verifier."""

from __future__ import annotations

import codecs
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from unittest import mock


sys.dont_write_bytecode = True
import build_vivhite_release as release  # noqa: E402


REVISION = "a" * 40
WORKSHOP_ID = "987654321"
DESCRIPTOR = b'version="1.0.0"\r\nname="Vivhite fixture"\r\n'


class VivhiteReleaseTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(prefix="vivhite-builder-test-") as name:
            root = Path(name)
            source = root / "source"
            source.mkdir()
            for relative in sorted(release.RUNTIME_FILES):
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative == "descriptor.mod":
                    data = DESCRIPTOR
                elif path.suffix.lower() in {".txt", ".gui", ".yml"}:
                    data = codecs.BOM_UTF8 + f"ervc_fixture_{path.stem} = {{}}\n".encode()
                else:
                    data = f"fixture:{relative}".encode()
                path.write_bytes(data)
            yield root, source

    def build(
        self,
        root: Path,
        source: Path,
        *,
        parent: str = "build",
        workshop_item_id: str | None = None,
        versioned_sidecars: bool = False,
        git_tag: str | None = None,
    ):
        return release.build_release(
            source,
            root / parent / release.PRODUCT_ID,
            revision=REVISION,
            workshop_item_id=workshop_item_id,
            versioned_sidecars=versioned_sidecars,
            git_tag=git_tag,
        )

    def launcher_descriptor(
        self,
        item_id: str = WORKSHOP_ID,
        *,
        separator: bytes = b"\n",
        final_newline: bool = False,
    ) -> bytes:
        body = separator.join(DESCRIPTOR.splitlines())
        result = body + separator + f'remote_file_id="{item_id}"'.encode()
        if final_newline:
            result += separator
        return result

    def rewrite_manifest(self, path: Path, **updates) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.update(updates)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_runtime_allowlist_is_the_current_27_files(self):
        self.assertEqual(27, len(release.RUNTIME_FILES))
        self.assertNotIn("events", {PurePosixPath(path).parts[0] for path in release.RUNTIME_FILES})
        self.assertFalse(any("erva" in path for path in release.RUNTIME_FILES))

    def test_build_is_byte_deterministic(self):
        with self.fixture() as (root, source):
            first = self.build(root, source, parent="one")
            second = self.build(root, source, parent="two")

            self.assertEqual(first[3], second[3])
            self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
            self.assertEqual(first[2].read_bytes(), second[2].read_bytes())
            self.assertEqual(release.PRODUCT_ID, first[3]["product_id"])
            self.assertIsNone(first[3]["git_tag"])
            self.assertEqual(REVISION, first[3]["git_sha"])
            self.assertEqual(27, len(first[3]["files"]))

            with zipfile.ZipFile(first[2]) as archive:
                infos = archive.infolist()
                self.assertEqual(
                    [
                        f"{release.PRODUCT_ID}/{relative}"
                        for relative in sorted(release.RUNTIME_FILES)
                    ],
                    [info.filename for info in infos],
                )
                self.assertTrue(
                    all(info.date_time == release.ZIP_TIMESTAMP for info in infos)
                )

    def test_reproducibility_check_reports_stable_hashes(self):
        with self.fixture() as (_, source):
            first = release.check_reproducible(source, revision=REVISION)
            second = release.check_reproducible(source, revision=REVISION)
        self.assertEqual(first, second)
        self.assertEqual(27, first["file_count"])
        self.assertRegex(first["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(first["zip_sha256"], r"^[0-9a-f]{64}$")

    def test_exact_manifest_verification_and_strict_file_failures(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(root, source)
            self.assertEqual(27, release.verify_manifest(staging, manifest))

            changed = staging / "gui/ervc_texticons.gui"
            changed.write_bytes(changed.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "mismatch: gui/ervc_texticons.gui"):
                release.verify_manifest(staging, manifest)

            changed.write_bytes(source.joinpath("gui/ervc_texticons.gui").read_bytes())
            staging.joinpath("thumbnail.png").unlink()
            with self.assertRaisesRegex(ValueError, "missing: thumbnail.png"):
                release.verify_manifest(staging, manifest)

            staging.joinpath("thumbnail.png").write_bytes(
                source.joinpath("thumbnail.png").read_bytes()
            )
            staging.joinpath("unexpected.bin").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "extra: unexpected.bin"):
                release.verify_manifest(staging, manifest)

    def test_manifest_identity_and_inventory_are_strict(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(root, source)
            original = manifest.read_bytes()

            for field, value, message in (
                ("product_id", "another-product", "product_id"),
                ("git_tag", "v1.0.0", "git_tag"),
                ("git_sha", "short", "full 40-character"),
                ("format_version", 99, "format_version"),
            ):
                with self.subTest(field=field):
                    manifest.write_bytes(original)
                    self.rewrite_manifest(manifest, **{field: value})
                    with self.assertRaisesRegex(ValueError, message):
                        release.verify_manifest(staging, manifest)

            manifest.write_bytes(original)
            self.rewrite_manifest(manifest, git_tag=["vivhite-v1.0.0"])
            with self.assertRaisesRegex(ValueError, "git_tag must be a string or null"):
                release.verify_manifest(staging, manifest)

            manifest.write_bytes(original)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"] = payload["files"][:-1]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest file inventory mismatch"):
                release.verify_manifest(staging, manifest)

    def test_unknown_cache_source_material_and_events_are_rejected(self):
        cases = (
            ("events/ervc_events.txt", "outside exact runtime allowlist"),
            ("__pycache__/cached.pyc", "Python cache is forbidden"),
            ("tools/helper.py", "tooling or source material"),
            ("images/source.png", "tooling or source material"),
        )
        for relative, message in cases:
            with self.subTest(relative=relative), self.fixture() as (_, source):
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"unexpected")
                errors = release.release_source_errors(source)
                self.assertTrue(any(message in error for error in errors), errors)
                with self.assertRaisesRegex(ValueError, "invalid standalone source"):
                    release.build_release(
                        source,
                        source.parent / "output" / release.PRODUCT_ID,
                        revision=REVISION,
                    )

    def test_original_runtime_identifiers_and_remote_id_are_rejected(self):
        cases = (
            (b"xar_old_effect = {}", "original custom identifier 'xar'"),
            (b"set_variable = { name = xa_old value = 1 }", "prefix 'xa_'"),
            (b'debug_log = "XAR: old"', "original log prefix"),
            (b"3784706360", "original Workshop item ID"),
            (b"erva_acceptance_effect = yes", "acceptance fixture identifier"),
            (b'debug_log = "ERVA: leaked"', "acceptance fixture log prefix"),
            (b"# ERVA_DUAL_ONLY_BEGIN", "acceptance fixture marker prefix"),
            (b'remote_file_id="123"', "canonical runtime contains remote_file_id"),
        )
        for payload, message in cases:
            with self.subTest(payload=payload), self.fixture() as (_, source):
                path = source / "common/decisions/ervc_courtier_creator_decisions.txt"
                path.write_bytes(codecs.BOM_UTF8 + payload)
                errors = release.release_source_errors(source)
                self.assertTrue(any(message in error for error in errors), errors)

    def test_workshop_item_id_is_optional_and_never_defaulted(self):
        with self.fixture() as (root, source):
            normal = self.build(root, source, parent="normal")
            recorded = self.build(
                root,
                source,
                parent="recorded",
                workshop_item_id=WORKSHOP_ID,
            )
            self.assertIsNone(normal[3]["workshop_item_id"])
            self.assertEqual(WORKSHOP_ID, recorded[3]["workshop_item_id"])
            with self.assertRaisesRegex(ValueError, "canonical positive ASCII digits"):
                self.build(root, source, parent="bad", workshop_item_id="not-digits")
            with self.assertRaisesRegex(ValueError, "must not reuse"):
                self.build(
                    root,
                    source,
                    parent="original-id",
                    workshop_item_id=release.ORIGINAL_WORKSHOP_ITEM_ID,
                )
            for index, item_id in enumerate(("0", "0123", "１２３", str(2**64))):
                with self.subTest(item_id=item_id), self.assertRaises(ValueError):
                    self.build(
                        root,
                        source,
                        parent=f"bad-canonical-{index}",
                        workshop_item_id=item_id,
                    )

    def test_candidate_tag_is_null_and_formal_tag_is_explicit(self):
        with self.fixture() as (root, source):
            candidate = self.build(root, source, parent="candidate")
            formal = self.build(
                root,
                source,
                parent="formal",
                git_tag="vivhite-v1.0.0",
            )
            self.assertIsNone(candidate[3]["git_tag"])
            self.assertEqual("vivhite-v1.0.0", formal[3]["git_tag"])
            self.assertEqual(27, release.verify_manifest(formal[0], formal[1]))
            with self.assertRaisesRegex(ValueError, "must be .* or null"):
                self.build(root, source, parent="wrong-tag", git_tag="v1.0.0")

    def test_release_sidecars_are_versioned(self):
        with self.fixture() as (root, source):
            _, manifest, archive, _ = self.build(
                root, source, versioned_sidecars=True
            )
            self.assertEqual(
                f"{release.PRODUCT_ID}-v1.0.0.manifest.json", manifest.name
            )
            self.assertEqual(f"{release.PRODUCT_ID}-v1.0.0.zip", archive.name)

    def test_release_identity_requires_clean_product_tag_at_head(self):
        with self.fixture() as (_, source):
            def clean_git_output(*args, **_kwargs):
                if args[0] == "status":
                    return ""
                if args[0] == "tag":
                    return "v1.0.0\nvivhite-v1.0.0"
                self.fail(f"unexpected git call: {args}")

            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(
                release, "git_sha", return_value=REVISION
            ), mock.patch.object(release, "git_output", side_effect=clean_git_output):
                identity = release.release_identity(source)
            self.assertEqual("vivhite-v1.0.0", identity["git_tag"])

            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(
                release, "git_sha", return_value=REVISION
            ), mock.patch.object(release, "git_output", return_value="dirty"):
                with self.assertRaisesRegex(ValueError, "clean worktree"):
                    release.release_identity(source)

            def missing_tag(*args, **_kwargs):
                return "" if args[0] == "status" else "v1.0.0"

            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(
                release, "git_sha", return_value=REVISION
            ), mock.patch.object(release, "git_output", side_effect=missing_tag):
                with self.assertRaisesRegex(ValueError, "vivhite-v1.0.0"):
                    release.release_identity(source)

    def test_formal_release_rejects_noncanonical_source(self):
        with self.fixture() as (_, source):
            with self.assertRaisesRegex(ValueError, "canonical standalone source"):
                release.release_identity(source)

    def test_workshop_descriptor_normalization_requires_opt_in(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(
                root, source, workshop_item_id=WORKSHOP_ID
            )
            staging.joinpath("descriptor.mod").write_bytes(self.launcher_descriptor())
            with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                release.verify_manifest(staging, manifest)
            self.assertEqual(
                27, release.verify_manifest(staging, manifest, workshop_cache=True)
            )

    def test_workshop_descriptor_accepts_only_line_ending_and_trailing_rewrites(self):
        for separator in (b"\n", b"\r\n"):
            for final_newline in (False, True):
                with self.subTest(
                    separator=separator, final_newline=final_newline
                ), self.fixture() as (root, source):
                    staging, manifest, _, _ = self.build(
                        root, source, workshop_item_id=WORKSHOP_ID
                    )
                    staging.joinpath("descriptor.mod").write_bytes(
                        self.launcher_descriptor(
                            separator=separator, final_newline=final_newline
                        )
                    )
                    self.assertEqual(
                        27,
                        release.verify_manifest(
                            staging, manifest, workshop_cache=True
                        ),
                    )

    def test_workshop_descriptor_rejects_wrong_missing_nonfinal_and_duplicate_ids(self):
        malformed = {
            "wrong": self.launcher_descriptor("123"),
            "missing": DESCRIPTOR,
            "non-final": (
                b'remote_file_id="987654321"\n'
                + b"\n".join(DESCRIPTOR.splitlines())
            ),
            "duplicate": (
                b"\n".join(DESCRIPTOR.splitlines())
                + b'\nremote_file_id="987654321"'
                + b'\nremote_file_id="987654321"'
            ),
            "content-change": (
                b'version="1.0.0"\nname="changed"\n'
                b'remote_file_id="987654321"'
            ),
            "mixed-line-endings": (
                b'version="1.0.0"\r\nname="Vivhite fixture"\n'
                b'remote_file_id="987654321"'
            ),
        }
        for label, descriptor in malformed.items():
            with self.subTest(label=label), self.fixture() as (root, source):
                staging, manifest, _, _ = self.build(
                    root, source, workshop_item_id=WORKSHOP_ID
                )
                staging.joinpath("descriptor.mod").write_bytes(descriptor)
                with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                    release.verify_manifest(
                        staging, manifest, workshop_cache=True
                    )

    def test_workshop_mode_requires_manifest_item_id_and_rejects_extra_files(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(root, source)
            staging.joinpath("descriptor.mod").write_bytes(
                self.launcher_descriptor()
            )
            with self.assertRaisesRegex(ValueError, "non-null numeric"):
                release.verify_manifest(staging, manifest, workshop_cache=True)

        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(
                root, source, workshop_item_id=WORKSHOP_ID
            )
            staging.joinpath("descriptor.mod").write_bytes(
                self.launcher_descriptor()
            )
            staging.joinpath("extra.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "extra: extra.txt"):
                release.verify_manifest(staging, manifest, workshop_cache=True)

    def test_workshop_mode_rejects_nonnumeric_manifest_id(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(
                root, source, workshop_item_id=WORKSHOP_ID
            )
            staging.joinpath("descriptor.mod").write_bytes(
                self.launcher_descriptor()
            )
            self.rewrite_manifest(manifest, workshop_item_id="not-digits")
            with self.assertRaisesRegex(ValueError, "canonical positive ASCII digits"):
                release.verify_manifest(staging, manifest, workshop_cache=True)


if __name__ == "__main__":
    unittest.main()
