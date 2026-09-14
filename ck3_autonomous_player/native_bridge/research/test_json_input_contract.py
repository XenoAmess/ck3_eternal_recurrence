"""Positive and negative tests for the shared JSON input contract."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_input_contract import (
    JsonInputContractError,
    load_json_document,
    load_json_object,
)


class JsonInputContractTests(unittest.TestCase):
    def write(self, root: Path, name: str, payload: bytes) -> Path:
        path = root / name
        path.write_bytes(payload)
        return path

    def test_accepts_bom_free_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            path = self.write(
                Path(raw_root),
                "plain.json",
                b'{"schema":"example/v1","candidates":[1,2]}',
            )
            self.assertEqual(
                load_json_object(path, expected_schema="example/v1")["candidates"],
                [1, 2],
            )

    def test_accepts_one_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            path = self.write(
                Path(raw_root),
                "bom.json",
                b"\xef\xbb\xbf" + b'{"schema":"example/v1","candidates":[30784]}',
            )
            self.assertEqual(
                load_json_object(path, expected_schema="example/v1")["candidates"],
                [30784],
            )

    def test_reproduces_legacy_utf8_reader_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            path = self.write(Path(raw_root), "legacy.json", b"\xef\xbb\xbf{\"ok\":true}")
            with self.assertRaises(json.JSONDecodeError):
                json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(load_json_document(path), {"ok": True})

    def test_rejects_malformed_json_with_typed_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            path = self.write(Path(raw_root), "broken.json", b"{not-json}")
            with self.assertRaises(JsonInputContractError):
                load_json_document(path)

    def test_rejects_utf16_and_wrong_schema(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            utf16 = self.write(root, "utf16.json", '{"ok":true}'.encode("utf-16"))
            with self.assertRaises(JsonInputContractError):
                load_json_document(utf16)
            wrong = self.write(root, "wrong.json", b'{"schema":"other/v1"}')
            with self.assertRaises(JsonInputContractError):
                load_json_object(wrong, expected_schema="example/v1")


if __name__ == "__main__":
    unittest.main()
