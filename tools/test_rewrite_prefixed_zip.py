"""Synthetic-only contracts for the pure prefixed single-member ZIP rewrite."""
from __future__ import annotations

import io
import unittest
import zipfile

from rewrite_prefixed_zip import rewrite_single_member_zip


def archive(prefix=b"", *, attribute=0, absolute=False, method=zipfile.ZIP_DEFLATED):
    buffer = io.BytesIO()
    if absolute:
        buffer.write(prefix)
    with zipfile.ZipFile(buffer, "w") as output:
        info = zipfile.ZipInfo("payload", (2020, 2, 3, 4, 5, 6))
        info.compress_type = method
        info.create_system = 0
        info.external_attr = attribute
        info.internal_attr = 1
        info.comment = b"member-note"
        info.extra = b"\xfe\xca\x02\x00ok"
        output.comment = b"archive-note"
        output.writestr(info, b"before-contents")
        output.getinfo("payload").external_attr = attribute
    return buffer.getvalue() if absolute else prefix + buffer.getvalue()


class RewriteContracts(unittest.TestCase):
    def check_rewrite(self, source, prefix, attribute):
        output, receipt = rewrite_single_member_zip(source, "payload", lambda raw: raw.replace(b"before", b"after"))
        self.assertEqual(output[:len(prefix)], prefix)
        with zipfile.ZipFile(io.BytesIO(source)) as old, zipfile.ZipFile(io.BytesIO(output)) as new:
            self.assertEqual(new.read("payload"), b"after-contents")
            self.assertEqual(new.getinfo("payload").external_attr, attribute)
            for key in ["filename", "date_time", "compress_type", "flag_bits", "create_system", "create_version", "extract_version", "internal_attr", "external_attr", "extra", "comment"]:
                self.assertEqual(getattr(old.getinfo("payload"), key), getattr(new.getinfo("payload"), key), key)
            self.assertEqual(old.comment, new.comment)
        self.assertTrue(receipt["source_and_output_full_CRC_read"])
        self.assertTrue(receipt["prefix_byte_exact"])
        return receipt

    def test_prefixed_relative_zero_attribute(self):
        prefix = b"OPAQUE\x00\xffmetadata\r\n"
        receipt = self.check_rewrite(archive(prefix), prefix, 0)
        self.assertTrue(receipt["relative_offsets"])

    def test_prefixed_absolute_normal_attribute(self):
        prefix = b"prefix with absolute offsets\n"
        receipt = self.check_rewrite(archive(prefix, absolute=True, attribute=1234), prefix, 1234)
        self.assertFalse(receipt["relative_offsets"])

    def test_plain_stored_archive(self):
        self.check_rewrite(archive(method=zipfile.ZIP_STORED), b"", 0)

    def test_multiple_members_refused_before_transform(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            output.writestr("payload", b"first")
            output.writestr("second", b"other")
        calls = []
        with self.assertRaises(ValueError):
            rewrite_single_member_zip(buffer.getvalue(), "payload", lambda raw: calls.append(raw) or raw)
        self.assertEqual(calls, [])

    def test_wrong_member_refused(self):
        with self.assertRaises(ValueError):
            rewrite_single_member_zip(archive(), "different", lambda raw: raw)

    def test_descriptor_shape_refused_before_transform(self):
        raw = bytearray(archive())
        with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
            central = zipped.start_dir
        raw[6:8] = (8).to_bytes(2, "little")
        raw[central + 8:central + 10] = (8).to_bytes(2, "little")
        with self.assertRaises(ValueError):
            rewrite_single_member_zip(bytes(raw), "payload", lambda data: self.fail("transform must not run"))

    def test_crc_corruption_refused(self):
        raw = bytearray(archive(method=zipfile.ZIP_STORED))
        with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
            info = zipped.getinfo("payload")
            start = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
        raw[start] ^= 1
        with self.assertRaises(zipfile.BadZipFile):
            rewrite_single_member_zip(bytes(raw), "payload", lambda data: data)

    def test_transform_type_refused(self):
        with self.assertRaises(TypeError):
            rewrite_single_member_zip(archive(), "payload", lambda raw: "text")


if __name__ == "__main__":
    unittest.main()
