#!/usr/bin/env python3
"""Unit tests for the ZhongGuo 361 Style deterministic release builder."""

from __future__ import annotations

import codecs
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from unittest import mock


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_mod_zhongguo_style_release as release  # noqa: E402
sys.path.insert(0, str(release.DEFAULT_SOURCE / "tools"))
import gen_361_workforce_endgame_runtime as workforce_gen  # noqa: E402


REVISION = "a" * 40
WORKSHOP_ID = "987654321"
DESCRIPTOR = (
    b'version="0.3.0"\n'
    b'tags={\n\t"Gameplay"\n}\n'
    b'name="ZhongGuo 361 fixture"\n'
    b'picture="thumbnail.png"\n'
    b'supported_version="1.19.0.6"\n'
)
WORKFORCE_LEGACY_EFFECT_FILENAME = "zg361_workforce_endgame_runtime_effects.txt"
WORKFORCE_SHARD_GLOB = "zg361_workforce_endgame_*_effects.txt"
WORKFORCE_SHARD_COUNT = 83
WORKFORCE_EFFECT_COUNT = 324
WORKFORCE_EVENT_SHARD_COUNT = 39
WORKFORCE_EVENT_COUNT = 149


def thumbnail_bytes(width: int = 640, height: int = 640) -> bytes:
    # The builder verifies the PNG signature/IHDR dimensions and the Steam size
    # limit; image decoding belongs to the asset compositor/static validator.
    return release.PNG_SIGNATURE + b"\x00\x00\x00\x0dIHDR" + struct.pack(">II", width, height) + b"fixture"


def paradox_top_level_assignment_names(text: str) -> tuple[str, ...]:
    """Parse true top-level ``name = { ... }`` assignments by brace depth."""

    names: list[str] = []
    depth = 0
    index = 0

    def skip_layout(cursor: int) -> int:
        while cursor < len(text):
            if text[cursor].isspace():
                cursor += 1
                continue
            if text[cursor] == "#":
                newline = text.find("\n", cursor)
                cursor = len(text) if newline < 0 else newline + 1
                continue
            break
        return cursor

    while index < len(text):
        char = text[index]
        if char == "#":
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline + 1
            continue
        if char == '"':
            index += 1
            escaped = False
            while index < len(text):
                char = text[index]
                index += 1
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    break
            else:
                raise AssertionError("unterminated quoted string in Paradox script")
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            if depth < 0:
                raise AssertionError("unexpected closing brace in Paradox script")
            index += 1
            continue
        if depth != 0 or char.isspace():
            index += 1
            continue

        start = index
        while index < len(text) and not (
            text[index].isspace() or text[index] in '=\"#{}'
        ):
            index += 1
        if index == start:
            index += 1
            continue
        name = text[start:index]
        cursor = skip_layout(index)
        if cursor >= len(text) or text[cursor] != "=":
            index = cursor
            continue
        cursor = skip_layout(cursor + 1)
        if cursor >= len(text) or text[cursor] != "{":
            index = cursor
            continue
        names.append(name)
        depth = 1
        index = cursor + 1

    if depth != 0:
        raise AssertionError(f"unclosed brace depth {depth} in Paradox script")
    return tuple(names)


class ZhongGuo361ReleaseTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(prefix="zhongguo-361-builder-test-") as name:
            root = Path(name)
            source = root / "source"
            source.mkdir()
            source.joinpath("descriptor.mod").write_bytes(DESCRIPTOR)
            source.joinpath("thumbnail.png").write_bytes(thumbnail_bytes())

            runtime = {
                "common/decisions/zg361_sample.txt": "zg361_sample_decision = {}\n",
                "events/zg361_sample_events.txt": "namespace = zg361_sample\n",
                "gui/zg361_sample.gui": "window = {}\n",
            }
            for relative, text in runtime.items():
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(codecs.BOM_UTF8 + text.encode("utf-8"))
            gfx = source / "gfx/interface/zg361_sample.dds"
            gfx.parent.mkdir(parents=True)
            gfx.write_bytes(b"DDS fixture")
            for language in sorted(release.REQUIRED_LOCALIZATION_LANGUAGES):
                path = source / f"localization/{language}/zg361_sample_l_{language}.yml"
                path.parent.mkdir(parents=True)
                path.write_bytes(
                    codecs.BOM_UTF8
                    + f"l_{language}:\n zg361_sample:0 \"Sample\"\n".encode("utf-8")
                )

            source.joinpath("README.md").write_text("public README", encoding="utf-8")
            for directory, relative in (
                ("docs", "release-checklist.md"),
                ("tools", "generator.py"),
                ("fixtures", "acceptance.txt"),
                ("workshop", "description.bbcode"),
                ("images", "thumbnail-source.png"),
                ("promo", "storyboard.md"),
                ("artifacts", "raw-capture.txt"),
            ):
                path = source / directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("source-only remote_file_id documentation", encoding="utf-8")
            yield root, source

    @staticmethod
    def build(root: Path, source: Path, **kwargs):
        parent = kwargs.pop("parent", "build")
        return release.build_release(
            source,
            root / parent / release.PRODUCT_ID,
            revision=REVISION,
            **kwargs,
        )

    def assert_workforce_shard_inventory(
        self, product_root: Path
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        effects = product_root / "common/scripted_effects"
        self.assertFalse(
            effects.joinpath(WORKFORCE_LEGACY_EFFECT_FILENAME).exists(),
            f"legacy workforce effect monolith leaked into {product_root}",
        )
        expected_files = tuple(group.filename for group in workforce_gen.EFFECT_GROUPS)
        self.assertEqual(WORKFORCE_SHARD_COUNT, len(expected_files))
        self.assertEqual(WORKFORCE_SHARD_COUNT, len(set(expected_files)))
        shards = tuple(sorted(effects.glob(WORKFORCE_SHARD_GLOB)))
        self.assertEqual(WORKFORCE_SHARD_COUNT, len(shards))
        self.assertEqual(tuple(sorted(expected_files)), tuple(path.name for path in shards))

        definitions: list[str] = []
        for path in shards:
            names = paradox_top_level_assignment_names(
                path.read_text(encoding="utf-8-sig")
            )
            self.assertTrue(names, f"workforce effect shard is empty: {path.name}")
            definitions.extend(names)
        counts = Counter(definitions)
        duplicates = sorted(name for name, count in counts.items() if count != 1)
        self.assertEqual([], duplicates, "duplicate workforce top-level effects")
        self.assertEqual(WORKFORCE_EFFECT_COUNT, len(definitions))
        self.assertEqual(WORKFORCE_EFFECT_COUNT, len(counts))
        return tuple(path.name for path in shards), tuple(definitions)

    def assert_workforce_event_shard_inventory(
        self, product_root: Path
    ) -> tuple[
        tuple[str, ...], tuple[str, ...], tuple[tuple[str, bytes], ...]
    ]:
        events = product_root / "events"
        self.assertFalse(
            events.joinpath(workforce_gen.LEGACY_EVENT_FILENAME).exists(),
            f"legacy workforce event monolith leaked into {product_root}",
        )
        expected_groups = tuple(workforce_gen.EVENT_GROUPS)
        expected_files = tuple(group.filename for group in expected_groups)
        self.assertEqual(WORKFORCE_EVENT_SHARD_COUNT, len(expected_files))
        self.assertEqual(WORKFORCE_EVENT_SHARD_COUNT, len(set(expected_files)))

        actual_files = tuple(
            sorted(path.name for path in events.glob(workforce_gen.EVENT_SHARD_GLOB))
        )
        self.assertEqual(tuple(sorted(expected_files)), actual_files)

        definitions: list[str] = []
        payloads: list[tuple[str, bytes]] = []
        for group in expected_groups:
            path = events / group.filename
            payload = path.read_bytes()
            names = paradox_top_level_assignment_names(
                payload.decode("utf-8-sig")
            )
            expected_names = tuple(
                f"{workforce_gen.NAMESPACE}.{event_id}"
                for event_id in group.event_ids
            )
            self.assertEqual(
                expected_names,
                names,
                f"workforce event shard order/content mismatch: {path.name}",
            )
            definitions.extend(names)
            payloads.append((group.filename, payload))

        counts = Counter(definitions)
        duplicates = sorted(name for name, count in counts.items() if count != 1)
        self.assertEqual([], duplicates, "duplicate workforce top-level events")
        self.assertEqual(WORKFORCE_EVENT_COUNT, len(definitions))
        self.assertEqual(WORKFORCE_EVENT_COUNT, len(counts))
        return expected_files, tuple(definitions), tuple(payloads)

    @staticmethod
    def launcher_descriptor(
        item_id: str = WORKSHOP_ID, separator: bytes = b"\n", final_newline: bool = False
    ) -> bytes:
        result = separator.join(DESCRIPTOR.splitlines())
        result += separator + f'remote_file_id="{item_id}"'.encode("ascii")
        return result + (separator if final_newline else b"")

    @staticmethod
    def write_localization_audit(source: Path) -> Path:
        def records(paths: tuple[str, ...]) -> list[dict[str, object]]:
            result: list[dict[str, object]] = []
            for relative in paths:
                path = source / PurePosixPath(relative).relative_to(release.PRODUCT_ID)
                if not path.is_file():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(codecs.BOM_UTF8 + b'l_fixture:\n key:0 "Value"\n')
                result.append(
                    {
                        "path": relative,
                        "size": path.stat().st_size,
                        "sha256": release.sha256_file(path),
                    }
                )
            return result

        payload = {
            "format_version": release.LOCALIZATION_AUDIT_FORMAT_VERSION,
            "product_id": release.PRODUCT_ID,
            "result": "GREEN",
            "checks": list(release.LOCALIZATION_AUDIT_CHECKS),
            "source_files": records(release.LOCALIZATION_AUDIT_SOURCE_PATHS),
            "target_files": records(release.LOCALIZATION_AUDIT_TARGET_PATHS),
        }
        path = source / release.LOCALIZATION_AUDIT_RELATIVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_projection_is_deterministic_and_excludes_every_source_only_tree(self):
        with self.fixture() as (root, source):
            first = self.build(root, source, parent="first")
            second = self.build(root, source, parent="second")
            self.assertEqual(first[3], second[3])
            self.assertEqual(first[1].read_bytes(), second[1].read_bytes())
            self.assertEqual(first[2].read_bytes(), second[2].read_bytes())
            self.assertEqual(15, release.verify_manifest(first[0], first[1]))
            paths = [entry["path"] for entry in first[3]["files"]]
            self.assertEqual(paths, sorted(paths))
            self.assertFalse(
                any(
                    PurePosixPath(path).parts[0]
                    in release.SOURCE_ONLY_DIRECTORIES | release.SOURCE_ONLY_ROOT_FILES
                    for path in paths
                )
            )
            self.assertFalse(any("remote_file_id" in path.read_text(encoding="utf-8-sig", errors="ignore") for path in first[0].rglob("*") if path.is_file()))
            with zipfile.ZipFile(first[2]) as archive:
                self.assertEqual(
                    [f"{release.PRODUCT_ID}/{path}" for path in paths],
                    [item.filename for item in archive.infolist()],
                )
                self.assertTrue(all(item.date_time == release.ZIP_TIMESTAMP for item in archive.infolist()))

    def test_workforce_effect_shards_are_exact_in_canonical_and_release_trees(self):
        canonical = release.DEFAULT_SOURCE.resolve()
        canonical_files, canonical_definitions = self.assert_workforce_shard_inventory(
            canonical
        )
        with tempfile.TemporaryDirectory(prefix="zhongguo-361-workforce-release-test-") as name:
            staging, _, _, _ = release.build_release(
                canonical,
                Path(name) / release.PRODUCT_ID,
                revision=REVISION,
            )
            release_files, release_definitions = self.assert_workforce_shard_inventory(
                staging
            )
        self.assertEqual(canonical_files, release_files)
        self.assertEqual(canonical_definitions, release_definitions)

    def test_workforce_event_shards_are_exact_in_canonical_and_release_trees(self):
        canonical = release.DEFAULT_SOURCE.resolve()
        canonical_inventory = self.assert_workforce_event_shard_inventory(canonical)
        with tempfile.TemporaryDirectory(prefix="zhongguo-361-workforce-event-release-test-") as name:
            staging, _, _, _ = release.build_release(
                canonical,
                Path(name) / release.PRODUCT_ID,
                revision=REVISION,
            )
            release_inventory = self.assert_workforce_event_shard_inventory(staging)
        self.assertEqual(canonical_inventory, release_inventory)

    def test_reproducibility_api_and_versioned_sidecars(self):
        with self.fixture() as (root, source):
            result = release.check_reproducible(source, revision=REVISION)
            self.assertEqual(15, result["file_count"])
            self.assertRegex(result["manifest_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(result["zip_sha256"], r"^[0-9a-f]{64}$")
            _, manifest, archive, details = self.build(
                root,
                source,
                parent="formal",
                versioned_sidecars=True,
                git_tag="zhongguo-361-v0.3.0",
            )
            self.assertEqual("mod_zhongguo_style-v0.3.0.manifest.json", manifest.name)
            self.assertEqual("mod_zhongguo_style-v0.3.0.zip", archive.name)
            self.assertEqual("zhongguo-361-v0.3.0", details["git_tag"])

    def test_thumbnail_descriptor_localization_and_bom_are_release_gates(self):
        with self.fixture() as (_, source):
            source.joinpath("thumbnail.png").unlink()
            self.assertTrue(any("thumbnail.png" in error for error in release.release_source_errors(source)))
        with self.fixture() as (_, source):
            source.joinpath("thumbnail.png").write_bytes(thumbnail_bytes(900, 500))
            self.assertTrue(any("640x640" in error for error in release.release_source_errors(source)))
        with self.fixture() as (_, source):
            source.joinpath("descriptor.mod").write_bytes(DESCRIPTOR.replace(b'picture="thumbnail.png"\n', b""))
            self.assertTrue(any("picture" in error for error in release.release_source_errors(source)))
        with self.fixture() as (_, source):
            missing = source / "localization/spanish"
            for path in missing.rglob("*"):
                if path.is_file():
                    path.unlink()
            missing.rmdir()
            self.assertTrue(any("localization/spanish" in error for error in release.release_source_errors(source)))
        with self.fixture() as (_, source):
            path = source / "events/zg361_sample_events.txt"
            path.write_text("namespace = zg361_sample\n", encoding="utf-8")
            self.assertTrue(any("missing UTF-8 BOM" in error for error in release.release_source_errors(source)))

    def test_fixture_paths_remote_id_and_existing_item_ids_fail_closed(self):
        for relative in (
            "common/fixtures/zg361_acceptance.txt",
            "common/scripted_effects/zg361_acceptance_effects.txt",
            "events/zg361_live_test_events.txt",
        ):
            with self.subTest(relative=relative), self.fixture() as (_, source):
                path = source / PurePosixPath(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(codecs.BOM_UTF8 + b"fixture = {}\n")
                self.assertTrue(
                    any(
                        "fixture/test path" in error
                        for error in release.release_source_errors(source)
                    )
                )
        with self.fixture() as (_, source):
            path = source / "common/decisions/zg361_sample.txt"
            path.write_bytes(codecs.BOM_UTF8 + b'remote_file_id="123"\n')
            self.assertTrue(any("remote_file_id" in error for error in release.release_source_errors(source)))
        for old_id in sorted(release.FORBIDDEN_WORKSHOP_ITEM_IDS):
            with self.subTest(old_id=old_id), self.fixture() as (root, source):
                with self.assertRaisesRegex(ValueError, "must not reuse"):
                    self.build(root, source, parent=old_id, workshop_item_id=old_id)

    def test_workshop_descriptor_normalization_is_the_only_cache_exception(self):
        with self.fixture() as (root, source):
            staging, manifest, _, details = self.build(
                root, source, workshop_item_id=WORKSHOP_ID
            )
            self.assertEqual(WORKSHOP_ID, details["workshop_item_id"])
            staging.joinpath("descriptor.mod").write_bytes(
                self.launcher_descriptor(separator=b"\r\n", final_newline=True)
            )
            self.assertEqual(15, release.verify_manifest(staging, manifest, workshop_cache=True))
            with self.assertRaisesRegex(ValueError, "mismatch: descriptor.mod"):
                release.verify_manifest(staging, manifest)
            for malformed in (
                self.launcher_descriptor("123"),
                DESCRIPTOR,
                b'remote_file_id="987654321"\n' + b"\n".join(DESCRIPTOR.splitlines()),
                b"\n".join(DESCRIPTOR.splitlines())
                + b'\nremote_file_id="987654321"\nremote_file_id="987654321"',
            ):
                staging.joinpath("descriptor.mod").write_bytes(malformed)
                with self.subTest(malformed=malformed), self.assertRaisesRegex(
                    ValueError, "mismatch: descriptor.mod"
                ):
                    release.verify_manifest(staging, manifest, workshop_cache=True)
            for bad in ("0", "0123", "not-digits", str(2**64)):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    self.build(root, source, parent="bad", workshop_item_id=bad)

    def test_manifest_inventory_and_formal_identity_are_strict(self):
        with self.fixture() as (root, source):
            staging, manifest, _, _ = self.build(root, source)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"] = payload["files"][:-1]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "extra:"):
                release.verify_manifest(staging, manifest)

            self.write_localization_audit(source)

            def clean_git(*args, **_kwargs):
                if args[0] == "status":
                    return ""
                if args[0] == "cat-file":
                    return "tag"
                return "zhongguo-361-v0.3.0"

            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(
                release, "git_sha", return_value=REVISION
            ), mock.patch.object(release, "git_output", side_effect=clean_git):
                identity = release.release_identity(source)
            self.assertEqual("zhongguo-361-v0.3.0", identity["git_tag"])
            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(
                release, "git_sha", return_value=REVISION
            ), mock.patch.object(release, "git_output", return_value="dirty"):
                with self.assertRaisesRegex(ValueError, "clean worktree"):
                    release.release_identity(source)

            def lightweight_git(*args, **_kwargs):
                if args[0] == "status":
                    return ""
                if args[0] == "cat-file":
                    return "commit"
                return "zhongguo-361-v0.3.0"

            with mock.patch.object(release, "DEFAULT_SOURCE", source), mock.patch.object(
                release, "git_sha", return_value=REVISION
            ), mock.patch.object(release, "git_output", side_effect=lightweight_git):
                with self.assertRaisesRegex(ValueError, "annotated tag"):
                    release.release_identity(source)

    def test_formal_localization_audit_requires_exact_current_4_plus_14_inventory(self):
        with self.fixture() as (_, source):
            with self.assertRaisesRegex(ValueError, "requires localization audit report"):
                release.verify_release_localization_audit(source)

            report = self.write_localization_audit(source)
            payload = release.verify_release_localization_audit(source)
            self.assertEqual(4, len(payload["source_files"]))
            self.assertEqual(14, len(payload["target_files"]))

            target = (
                source
                / PurePosixPath(release.LOCALIZATION_AUDIT_TARGET_PATHS[0]).relative_to(
                    release.PRODUCT_ID
                )
            )
            target.write_bytes(target.read_bytes() + b"# stale\n")
            with self.assertRaisesRegex(ValueError, "audit is stale"):
                release.verify_release_localization_audit(source)

            self.write_localization_audit(source)
            document = json.loads(report.read_text(encoding="utf-8"))
            document["target_files"] = document["target_files"][:-1]
            report.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly cover 14"):
                release.verify_release_localization_audit(source)


if __name__ == "__main__":
    unittest.main()
