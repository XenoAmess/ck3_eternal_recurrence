#!/usr/bin/env python3
"""Regression tests for the disposable Phase-2 workforce block splitter."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import phase2_workforce_block_segments as splitter  # noqa: E402


class WorkforceBlockSegmentTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
