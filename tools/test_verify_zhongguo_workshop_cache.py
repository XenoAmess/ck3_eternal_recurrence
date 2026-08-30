#!/usr/bin/env python3
"""Unit tests for the ZhongGuo 361 fresh Workshop-cache verifier."""

from __future__ import annotations

import codecs
import contextlib
import io
import json
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_mod_zhongguo_style_release as release  # noqa: E402
import verify_zhongguo_workshop_cache as verifier  # noqa: E402


REVISION = "b" * 40
WORKSHOP_ID = "987654321"
VERSION = "0.3.0"
TAG = f"zhongguo-361-v{VERSION}"
DESCRIPTOR = (
    f'version="{VERSION}"\n'
    'tags={\n\t"Gameplay"\n}\n'
    'name="ZhongGuo 361 cache fixture"\n'
    'picture="thumbnail.png"\n'
    'supported_version="1.19.0.6"\n'
).encode("utf-8")


def thumbnail_bytes() -> bytes:
    return (
        release.PNG_SIGNATURE
        + b"\x00\x00\x00\x0dIHDR"
        + struct.pack(">II", 640, 640)
        + b"fixture"
    )


class WorkshopCacheVerifierTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(prefix="zg361-workshop-cache-test-") as name:
            root = Path(name)
            source = root / "source"
            source.mkdir()
            source.joinpath("descriptor.mod").write_bytes(DESCRIPTOR)
            source.joinpath("thumbnail.png").write_bytes(thumbnail_bytes())
            runtime = {
                "common/decisions/zg361_sample.txt": codecs.BOM_UTF8 + b"sample = {}\n",
                "events/zg361_sample.txt": codecs.BOM_UTF8 + b"namespace = sample\n",
                "gfx/interface/zg361_sample.dds": b"DDS fixture",
                "gui/zg361_sample.gui": codecs.BOM_UTF8 + b"window = {}\n",
            }
            for relative, data in runtime.items():
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            for language in sorted(release.REQUIRED_LOCALIZATION_LANGUAGES):
                for family in release.LOCALIZATION_FAMILIES:
                    path = source / f"localization/{language}/{family}_l_{language}.yml"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(
                        codecs.BOM_UTF8
                        + f'l_{language}:\n key:0 "Value"\n'.encode("utf-8")
                    )

            staging, manifest, archive, _details = release.build_release(
                source,
                root / "formal" / release.PRODUCT_ID,
                revision=REVISION,
                version=VERSION,
                workshop_item_id=WORKSHOP_ID,
                versioned_sidecars=True,
                git_tag=TAG,
            )
            cache = root / "steamapps/workshop/content/1158310" / WORKSHOP_ID
            cache.parent.mkdir(parents=True)
            shutil.copytree(staging, cache)
            yield root, cache, manifest, archive

    @staticmethod
    def inject_launcher_descriptor(cache: Path, item_id: str = WORKSHOP_ID) -> None:
        canonical = cache.joinpath("descriptor.mod").read_bytes()
        injected = b"\r\n".join(canonical.splitlines())
        injected += b'\r\nremote_file_id="' + item_id.encode("ascii") + b'"\r\n'
        cache.joinpath("descriptor.mod").write_bytes(injected)

    def verify(self, cache: Path, manifest: Path, archive: Path, policy: str):
        return verifier.verify_workshop_cache(
            cache_leaf=cache,
            manifest_path=manifest,
            archive_path=archive,
            descriptor_policy=policy,
        )

    def test_canonical_cache_and_formal_zip_are_green(self):
        with self.fixture() as (_root, cache, manifest, archive):
            report = self.verify(cache, manifest, archive, "canonical")
            self.assertEqual("GREEN", report["result"])
            self.assertEqual(TAG, report["manifest"]["git_tag"])
            self.assertEqual(WORKSHOP_ID, report["manifest"]["workshop_item_id"])
            self.assertEqual(len(report["files"]), report["cache"]["file_count"])
            self.assertFalse(report["descriptor"]["canonical_rebuild_required"])
            self.assertIsNone(report["descriptor"]["remote_file_id"])

    def test_exact_launcher_injection_is_green_and_marks_rebuild_boundary(self):
        with self.fixture() as (_root, cache, manifest, archive):
            self.inject_launcher_descriptor(cache)
            report = self.verify(cache, manifest, archive, "launcher-injected")
            self.assertEqual("GREEN", report["result"])
            self.assertEqual(WORKSHOP_ID, report["descriptor"]["remote_file_id"])
            self.assertTrue(report["descriptor"]["canonical_rebuild_required"])
            descriptor = next(item for item in report["files"] if item["path"] == "descriptor.mod")
            self.assertEqual("launcher-injected", descriptor["cache_match_mode"])
            self.assertNotEqual(descriptor["expected_sha256"], descriptor["cache_sha256"])

    def test_wrong_or_duplicate_launcher_id_is_rejected(self):
        for variant in ("wrong", "duplicate"):
            with self.subTest(variant=variant), self.fixture() as (
                _root,
                cache,
                manifest,
                archive,
            ):
                self.inject_launcher_descriptor(
                    cache, "123456789" if variant == "wrong" else WORKSHOP_ID
                )
                if variant == "duplicate":
                    path = cache / "descriptor.mod"
                    path.write_bytes(
                        path.read_bytes()
                        + f'remote_file_id="{WORKSHOP_ID}"\r\n'.encode("ascii")
                    )
                with self.assertRaisesRegex(
                    verifier.VerificationError, "exact permitted launcher injection"
                ):
                    self.verify(cache, manifest, archive, "launcher-injected")

        with self.fixture() as (_root, cache, manifest, archive):
            self.inject_launcher_descriptor(cache)
            with self.assertRaisesRegex(
                verifier.VerificationError, "canonical cache descriptor.mod"
            ):
                self.verify(cache, manifest, archive, "canonical")

    def test_missing_tampered_and_extra_cache_files_are_rejected(self):
        mutations = ("missing", "tampered", "extra")
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.fixture() as (
                _root,
                cache,
                manifest,
                archive,
            ):
                target = cache / "events/zg361_sample.txt"
                if mutation == "missing":
                    target.unlink()
                elif mutation == "tampered":
                    target.write_bytes(target.read_bytes() + b"tampered")
                else:
                    cache.joinpath("unexpected.txt").write_text("extra", encoding="utf-8")
                with self.assertRaisesRegex(
                    verifier.VerificationError, f"cache (?:{mutation}|content mismatch)"
                ):
                    self.verify(cache, manifest, archive, "canonical")

    def test_zip_extra_member_and_nonformal_manifest_are_rejected(self):
        with self.fixture() as (_root, cache, manifest, archive):
            with zipfile.ZipFile(archive, "a") as target:
                target.writestr(f"{release.PRODUCT_ID}/unexpected.txt", b"extra")
            with self.assertRaisesRegex(verifier.VerificationError, "ZIP extra"):
                self.verify(cache, manifest, archive, "canonical")

        with self.fixture() as (root, cache, manifest, archive):
            tampered = root / "tampered.zip"
            with zipfile.ZipFile(archive) as source, zipfile.ZipFile(tampered, "w") as target:
                for info in source.infolist():
                    data = source.read(info)
                    if info.filename.endswith("events/zg361_sample.txt"):
                        data += b"tampered"
                    target.writestr(info, data)
            with self.assertRaisesRegex(verifier.VerificationError, "ZIP content mismatch"):
                self.verify(cache, manifest, tampered, "canonical")

        with self.fixture() as (root, cache, manifest, archive):
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["git_tag"] = None
            informal = root / "informal.manifest.json"
            informal.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(verifier.VerificationError, "formal manifest"):
                self.verify(cache, informal, archive, "canonical")

    def test_cli_emits_json_exit_codes_and_external_report(self):
        with self.fixture() as (root, cache, manifest, archive):
            report_path = root / "evidence" / "fresh-cache-report.json"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = verifier.main(
                    [
                        "--cache-leaf",
                        str(cache),
                        "--manifest",
                        str(manifest),
                        "--zip",
                        str(archive),
                        "--descriptor-policy",
                        "canonical",
                        "--report",
                        str(report_path),
                    ]
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(verifier.EXIT_GREEN, code)
            self.assertEqual("GREEN", payload["result"])
            self.assertEqual(payload, json.loads(report_path.read_text(encoding="utf-8")))

            report_path.write_text("different", encoding="utf-8")
            with self.assertRaisesRegex(
                verifier.VerificationError, "refusing to overwrite existing report"
            ):
                verifier._write_report(report_path, payload, cache)

            cache.joinpath("unexpected.txt").write_text("extra", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = verifier.main(
                    [
                        "--cache-leaf",
                        str(cache),
                        "--manifest",
                        str(manifest),
                        "--zip",
                        str(archive),
                        "--descriptor-policy",
                        "canonical",
                    ]
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(verifier.EXIT_RED, code)
            self.assertEqual("RED", payload["result"])
            self.assertIn("cache extra", payload["errors"][0])


if __name__ == "__main__":
    unittest.main()
