#!/usr/bin/env python3
"""Regression tests for the disposable Phase-2 workforce block splitter."""

from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import phase2_workforce_block_segments as splitter  # noqa: E402


class WorkforceBlockSegmentTests(unittest.TestCase):
    HISTORICAL_BYTES = 4_636_271
    HISTORICAL_SHA256 = "926453fe4b3621b5381743d61f5d03ac29c1d498181702e05a9532739d334d8a"

    def test_bom_offsets_preserve_exact_block_bytes(self) -> None:
        source = (
            b"\xef\xbb\xbf# generated header\r\n"
            b"# keep this comment byte-exact\r\n\r\n"
            b"first_effect = {\r\n"
            b"\tset_variable = { name = first value = 1 }\r\n"
            b"}\r\n\r\n"
            b"second_effect = {\r\n"
            b"\tif = { limit = { always = yes } }\r\n"
            b"}\r\n"
        )

        header, blocks = splitter.find_blocks(source)

        self.assertEqual(header, b"\xef\xbb\xbf# generated header\r\n# keep this comment byte-exact\r\n\r\n")
        self.assertEqual([block["name"] for block in blocks], ["first_effect", "second_effect"])
        self.assertEqual(blocks[0]["start_byte"], len(header))

        extracted = []
        for block in blocks:
            start = int(block["start_byte"])
            end = int(block["end_byte"])
            payload = source[start:end]
            extracted.append(payload)
            self.assertEqual(int(block["bytes"]), len(payload))
            self.assertEqual(str(block["sha256"]), hashlib.sha256(payload).hexdigest())
            self.assertTrue(payload.endswith(b"}\r\n"))

        # The splitter intentionally omits inter-block whitespace/comments;
        # each emitted payload must nevertheless be the exact source slice.
        # This is the invariant that prevents three-byte BOM drift or boundary
        # garbage from entering a disposable launch projection.
        self.assertEqual(
            header + b"".join(extracted),
            header + b"first_effect = {\r\n"
            b"\tset_variable = { name = first value = 1 }\r\n}\r\n"
            b"second_effect = {\r\n"
            b"\tif = { limit = { always = yes } }\r\n}\r\n",
        )

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "part.txt"
            row = splitter.write_segment(output, header, blocks, source)
            expected = header + b"".join(extracted)
            self.assertEqual(output.read_bytes(), expected)
            self.assertEqual(int(row["bytes"]), len(expected))
            self.assertEqual(str(row["sha256"]), hashlib.sha256(expected).hexdigest())

    def test_non_bom_offsets_remain_zero_based(self) -> None:
        source = b"header\nfirst = {\n}\n"
        header, blocks = splitter.find_blocks(source)
        self.assertEqual(header, b"header\n")
        self.assertEqual(int(blocks[0]["start_byte"]), len(header))
        self.assertEqual(source[int(blocks[0]["start_byte"]) : int(blocks[0]["end_byte"])], b"first = {\n}\n")

    def test_default_source_is_frozen_historical_renderer_aggregate(self) -> None:
        data, metadata = splitter.load_source(None)

        self.assertEqual(len(data), self.HISTORICAL_BYTES)
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.HISTORICAL_SHA256)
        self.assertEqual(metadata["source_kind"], "synthetic_historical_renderer")
        self.assertEqual(metadata["snapshot_name"], splitter.DEFAULT_SNAPSHOT_NAME)
        renderer = metadata["source_renderer"]
        self.assertEqual(renderer["path"], str(splitter.DEFAULT_GENERATOR_PATH.resolve()))
        self.assertEqual(renderer["callable"], "render_effects()")
        self.assertIn("never purpose-shard concatenation", renderer["ordering"])
        _header, blocks = splitter.find_blocks(data)
        self.assertEqual(len(blocks), 324)

    def test_default_manifest_names_synthetic_historical_renderer(self) -> None:
        source = b"\xef\xbb\xbf# historical aggregate\nonly_effect = {\n}\n"
        metadata = {
            "source_kind": "synthetic_historical_renderer",
            "read_only_source": "generator.py:render_effects()",
            "snapshot_name": splitter.DEFAULT_SNAPSHOT_NAME,
            "source_renderer": {
                "path": "generator.py",
                "callable": "render_effects()",
                "ordering": "historical aggregate renderer order; never purpose-shard concatenation",
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "segments"
            argv = [
                "phase2_workforce_block_segments.py",
                "--output",
                str(output),
                "--ranges",
                "0",
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(splitter, "load_source", return_value=(source, metadata)),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(splitter.main(), 0)

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_kind"], "synthetic_historical_renderer")
            self.assertEqual(manifest["source_renderer"]["callable"], "render_effects()")
            self.assertIn("never purpose-shard concatenation", manifest["source_renderer"]["ordering"])
            self.assertEqual(
                (output / "source" / splitter.DEFAULT_SNAPSHOT_NAME).read_bytes(),
                source,
            )

    def test_explicit_source_remains_file_backed(self) -> None:
        source = b"# explicit file\nfirst = {\n}\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "explicit.txt"
            output = root / "segments"
            source_path.write_bytes(source)
            argv = [
                "phase2_workforce_block_segments.py",
                "--source",
                str(source_path),
                "--output",
                str(output),
                "--ranges",
                "0",
            ]
            with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                self.assertEqual(splitter.main(), 0)

            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_kind"], "file")
            self.assertEqual(manifest["read_only_source"], str(source_path.resolve()))
            self.assertNotIn("source_renderer", manifest)
            self.assertEqual((output / "source" / source_path.name).read_bytes(), source)


if __name__ == "__main__":
    unittest.main()
