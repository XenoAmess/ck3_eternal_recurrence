"""Stat identity boundaries use only a small existing source file."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect
import json
import os
from pathlib import Path
from typing import get_type_hints
import unittest

from tools.g2_saved_campaign.file_stat_identity_v1 import (
    SCHEMA, FileStatIdentityV1, FileStatIdentityWireV1,
    normalize_file_stat_identity_v1 as normalize,
    parse_file_stat_identity_v1 as parse,
)


class FileStatIdentityTests(unittest.TestCase):
    def test_roundtrip_and_large_decimal_inode(self) -> None:
        for inode, mtime in (("0", "0"), (str((1 << 127) + 3), "-1"), ("123", "1234567890")):
            value = FileStatIdentityV1(0, inode, mtime)
            self.assertEqual(parse(json.loads(json.dumps(value.to_wire())), schema=SCHEMA), value)

    def test_reject_numeric_lookalikes(self) -> None:
        for bad in (True, 1.0, -1, "1", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse({"bytes": bad, "file_id": "1", "mtime_ns": "1"}, schema=SCHEMA)

    def test_reject_noncanonical_decimal_or_hex(self) -> None:
        cases: dict[str, tuple[object, ...]] = {
            "file_id": ("", "-1", "+1", "01", "0x01", "ab" * 16, 1, 1.0, True, None),
            "mtime_ns": ("", "-0", "+1", "01", "1.0", "0x01", 1, 1.0, True, None),
        }
        for field, rows in cases.items():
            for bad in rows:
                value: dict[str, object] = {"bytes": 1, "file_id": "1", "mtime_ns": "1"}
                value[field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    parse(value, schema=SCHEMA)

    def test_schema_is_explicit_and_units_are_not_guessed(self) -> None:
        value = {"bytes": 1, "file_id": "1", "mtime_ns": "123456789000"}
        with self.assertRaises(TypeError):
            inspect.signature(parse).bind(value)
        for schema in ("", "unknown", "filetime-100ns", "win-file-id-info-hex128"):
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                parse(value, schema=schema)
        for bad in (None, [], {}, {**value, "mtime_unit": "ns"}):
            with self.assertRaises(ValueError):
                parse(bad, schema=SCHEMA)

    def test_frozen_fields_and_reflection(self) -> None:
        value = FileStatIdentityV1(1, "1", "1")
        with self.assertRaises(FrozenInstanceError):
            setattr(value, "mtime_ns", "2")
        expected = {"bytes": int, "file_id": str, "mtime_ns": str}
        self.assertEqual(get_type_hints(FileStatIdentityV1), expected)
        self.assertEqual(get_type_hints(FileStatIdentityWireV1), expected)
        self.assertIs(get_type_hints(normalize)["return"], FileStatIdentityV1)
        self.assertIs(get_type_hints(parse)["return"], FileStatIdentityV1)
        row = value.to_wire()
        row["mtime_ns"] = "2"
        self.assertEqual(value.mtime_ns, "1")

    def test_actual_small_source_os_stat_matches_mechanically(self) -> None:
        source = Path(__file__).with_name("patch_complete_tool_result_v1.py")
        status = os.stat(source)
        self.assertLess(status.st_size, 4096)
        value = normalize(status)
        self.assertEqual(
            (value.bytes, value.file_id, value.mtime_ns),
            (status.st_size, str(status.st_ino), str(status.st_mtime_ns)),
        )
        self.assertEqual(parse(value.to_wire(), schema=SCHEMA), value)


if __name__ == "__main__":
    unittest.main()
