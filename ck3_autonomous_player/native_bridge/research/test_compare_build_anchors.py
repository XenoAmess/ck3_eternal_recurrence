"""Synthetic PE regression tests for version-explicit migration candidates."""
import hashlib
import struct
import unittest

from compare_build_anchors import compare_builds
from scan_anchors import PeImage

OLD_CODE = bytes.fromhex("48 8B 05 12 34 56 78 E8 12 34 56 78 48 83 C0 17 C3")
NEW_CODE = bytes.fromhex("48 8B 05 78 56 34 12 E8 78 56 34 12 48 83 C0 17 C3")


def image(rva=0x1000, code=OLD_CODE, duplicate=False):
    data = bytearray(0x600)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 2, 42, 0, 0, 0xF0, 0)
    optional = 0x98
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<Q", data, optional + 24, 0x140000000)
    struct.pack_into("<I", data, optional + 56, 0x8000)
    table = optional + 0xF0
    for index, (name, va, raw, flags) in enumerate([
            (b".text", rva, 0x200, 0x60000020),
            (b".rdata", 0x6000, 0x400, 0x40000040)]):
        entry = table + index * 40
        data[entry:entry + len(name)] = name
        struct.pack_into("<IIII", data, entry + 8, 0x200, va, 0x200, raw)
        struct.pack_into("<I", data, entry + 36, flags)
    data[0x240:0x240 + len(code)] = code
    data[0x440:0x440 + len(code)] = code  # Same data bytes must not be a candidate.
    if duplicate:
        data[0x280:0x280 + len(code)] = code
    return bytes(data)


def manifest(data):
    pe = PeImage(data)
    return {"build": {"product_version": "fixture-source", "sha256":
            hashlib.sha256(data).hexdigest(), "file_size": len(data),
            "pe_timestamp": pe.timestamp, "image_base": hex(pe.image_base),
            "size_of_image": pe.size_of_image}, "signature_anchors": [
            {"name": "only_explicit_function", "rva": "0x1040",
             "pattern": OLD_CODE.hex(" ")}]}


class MigrationCandidateTests(unittest.TestCase):
    def test_masks_relocations_and_searches_actual_executable_sections(self):
        old = image()
        report = compare_builds(old, image(0x3000, NEW_CODE), manifest(old))
        self.assertFalse(report["implicit_historical_anchors"])
        self.assertEqual(len(report["anchors"]), 1)
        row = report["anchors"][0]
        self.assertEqual(row["candidate_rvas"], ["0x3040"])
        self.assertFalse(row["abi_verified"])
        self.assertFalse(row["live_verified"])

    def test_duplicate_signatures_remain_unresolved(self):
        old = image()
        row = compare_builds(old, image(0x3000, NEW_CODE, True), manifest(old))["anchors"][0]
        self.assertEqual(row["candidate_rvas"], ["0x3040", "0x3080"])
        self.assertEqual(row["status"], "unresolved")
        self.assertNotIn("disassembly", row)

    def test_source_identity_and_anchor_bytes_are_mandatory(self):
        old = image()
        for field in ["sha256", "file_size", "pe_timestamp", "image_base", "size_of_image"]:
            m = manifest(old)
            m["build"][field] = "0" if field == "sha256" else 0
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare_builds(old, image(0x3000), m)
        for pattern in ["", "90 90"]:
            m = manifest(old)
            m["signature_anchors"][0]["pattern"] = pattern
            with self.assertRaises(ValueError):
                compare_builds(old, image(0x3000), m)

    def test_non_executable_target_and_duplicate_names_fail_closed(self):
        old = image()
        target = bytearray(image(0x3000))
        struct.pack_into("<I", target, 0x98 + 0xF0 + 36, 0x40000040)
        with self.assertRaises(ValueError):
            compare_builds(old, bytes(target), manifest(old))
        m = manifest(old)
        m["signature_anchors"] *= 2
        with self.assertRaises(ValueError):
            compare_builds(old, image(0x3000), m)


if __name__ == "__main__":
    unittest.main()
