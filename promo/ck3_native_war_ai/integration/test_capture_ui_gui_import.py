"""No-screen tests for the candidate UI-saved GUI block importer."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from capture_session import import_ui_saved_gui_block


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


class UiGuiImportTest(unittest.TestCase):
    template = '"Graphics"={}\n"Audio"={}\n'
    block = (b'"GUI"={\r\n\t"scale"={\r\n\t\tversion=1\r\n'
             b'\t\tvalue="1"\r\n\t}\r\n}\r\n')

    def test_exact_block_and_non_gui_template_are_bound(self) -> None:
        source = b'"Graphics"={\r\n}\r\n' + self.block + b'"Audio"={\r\n}\r\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "ui-saved-full-settings.pdx.txt"
            source_path.write_bytes(source)
            target_dir = root / "new-profile"
            target_dir.mkdir()
            output = root / "evidence"
            output.mkdir()
            target = target_dir / "pdx_settings.txt"
            row = import_ui_saved_gui_block(target, self.template, source_path,
                                            sha(source), output, requested_scale="1.0")
            self.assertEqual(target.read_bytes(), self.template.encode() + self.block)
            self.assertEqual(source_path.read_bytes(), source)
            self.assertEqual(row["source_snapshot"]["sha256"], sha(source))
            self.assertEqual(row["source_gui_block"]["sha256"], sha(self.block))
            self.assertEqual(row["source_gui_block"]["sha256"],
                             "F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593")
            self.assertEqual(row["vanilla_non_gui_template"]["sha256"],
                             sha(self.template.encode()))
            self.assertEqual(row["prepared_settings"]["sha256"],
                             sha(self.template.encode() + self.block))
            self.assertEqual(row["status"], "GREEN_DISK_ONLY")
            self.assertEqual(row["requested_scale"], "1.0")
            self.assertEqual(row["native_ui_serialized_scale"], "1")
            self.assertFalse(row["recording_authorized_by_this_receipt"])
            self.assertTrue((output / "gui-settings-ui-block-import.json").is_file())
            self.assertEqual((output / "gui-settings-ui-import-prepared.pdx.txt").read_bytes(),
                             target.read_bytes())
            self.assertFalse(Path(row["staging_path"]).exists())

    def test_preserves_every_vanilla_template_byte(self) -> None:
        template = self.template + "\n\n"
        source = self.template.encode() + self.block
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.txt"
            source_path.write_bytes(source)
            output = root / "evidence"
            output.mkdir()
            target = root / "pdx_settings.txt"
            row = import_ui_saved_gui_block(target, template, source_path, sha(source),
                                            output, requested_scale="1.0")
            self.assertEqual(target.read_bytes(), template.encode() + self.block)
            self.assertEqual(row["vanilla_non_gui_template"]["bytes"], len(template.encode()))
            self.assertEqual(row["vanilla_non_gui_template"]["sha256"], sha(template.encode()))

    def test_exact_frozen_a04_ui_snapshot_when_available(self) -> None:
        source_path = Path(
            r"D:\workspace\ck3_native_war_ai_promo_work\episode02-e2-04-d05-screen-lease-20260928-a04"
            r"\native-ui-saved-settings-a01.pdx.txt")
        if not source_path.is_file():
            self.skipTest("Exact external a04 UI-saved snapshot is unavailable")
        source = source_path.read_bytes()
        self.assertEqual(len(source), 6891)
        self.assertEqual(sha(source),
                         "E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D")
        self.assertEqual(source.count(b'"GUI"='), 1)
        self.assertEqual(source[6642:6696], self.block)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            output.mkdir()
            target = root / "pdx_settings.txt"
            row = import_ui_saved_gui_block(target, self.template, source_path,
                                            sha(source), output, requested_scale="1.0")
            self.assertEqual(row["source_gui_block"]["sha256"],
                             "F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593")
            self.assertEqual(target.read_bytes(), self.template.encode() + self.block)
            self.assertFalse(row["recording_authorized_by_this_receipt"])

    def test_rejects_unreviewed_requested_scale(self) -> None:
        source = self.template.encode() + self.block
        for requested in ("1", "1.00", "1.3", None):
            with self.subTest(requested=requested), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_path = root / "source.txt"
                source_path.write_bytes(source)
                output = root / "evidence"
                output.mkdir()
                target = root / "pdx_settings.txt"
                with self.assertRaisesRegex(Exception, "explicit 1.0 capture request"):
                    import_ui_saved_gui_block(target, self.template, source_path,
                                              sha(source), output, requested_scale=requested)
                self.assertFalse(target.exists())
                self.assertEqual(json.loads(
                    (output / "gui-settings-ui-block-import.json").read_text())["status"], "RED")

    def test_rejects_mismatched_or_missing_sha_before_writing(self) -> None:
        source = self.block
        for claimed in ("0" * 64, "", "xyz"):
            with self.subTest(claimed=claimed), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_path = root / "source.txt"
                source_path.write_bytes(source)
                target = root / "pdx_settings.txt"
                output = root / "evidence"
                output.mkdir()
                with self.assertRaises(Exception):
                    import_ui_saved_gui_block(target, self.template, source_path,
                                              claimed, output, requested_scale="1.0")
                self.assertFalse(target.exists())
                self.assertEqual(json.loads(
                    (output / "gui-settings-ui-block-import.json").read_text())["status"], "RED")

    def test_rejects_unreviewed_gui_syntax(self) -> None:
        cases = {
            "gui_fragment_only": self.block,
            "missing": b'"Graphics"={}\n',
            "duplicate": self.block + self.block,
            "indented_duplicate": self.block + b"\t" + self.block,
            "extra_key": b'"GUI"={\n"scale"={ version=1 value="1.0" }\n"opacity"=1\n}\n',
            "wrong_scale": b'"Graphics"={}\n' + self.block.replace(b'value="1"', b'value="1.3"'),
            "old_text_scale": b'"Graphics"={}\n' + self.block.replace(b'value="1"', b'value="1.0"'),
            "padded_scale": b'"Graphics"={}\n' + self.block.replace(b'value="1"', b'value="01"'),
            "numeric_scale": b'"Graphics"={}\n' + self.block.replace(b'value="1"', b'value=1'),
            "wrong_version": self.block.replace(b'version=1', b'version=2'),
            "trailing_other_key": self.block.replace(b'}\r\n', b'}\r\n"opacity"=1\r\n', 1),
        }
        for name, source in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_path = root / "source.txt"
                source_path.write_bytes(source)
                target = root / "pdx_settings.txt"
                output = root / "evidence"
                output.mkdir()
                with self.assertRaises(Exception):
                    import_ui_saved_gui_block(target, self.template, source_path,
                                              sha(source), output, requested_scale="1.0")
                self.assertFalse(target.exists())
                self.assertEqual(json.loads(
                    (output / "gui-settings-ui-block-import.json").read_text())["status"], "RED")

    def test_rejects_existing_target_and_duplicate_template_gui(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source_bytes = self.template.encode() + self.block
            source.write_bytes(source_bytes)
            target = root / "pdx_settings.txt"
            existing_output = root / "existing-evidence"
            existing_output.mkdir()
            target.write_bytes(b"old target")
            with self.assertRaisesRegex(Exception, "Target settings already exist"):
                import_ui_saved_gui_block(target, self.template, source,
                                          sha(source_bytes), existing_output,
                                          requested_scale="1.0")
            self.assertEqual(target.read_bytes(), b"old target")
            self.assertEqual(json.loads(
                (existing_output / "gui-settings-ui-block-import.json").read_text())["status"], "RED")
            target.unlink()
            duplicate_output = root / "duplicate-evidence"
            duplicate_output.mkdir()
            with self.assertRaisesRegex(Exception, "Vanilla template already defines GUI"):
                import_ui_saved_gui_block(target, self.template + '"GUI"={}\n',
                                          source, sha(source_bytes), duplicate_output,
                                          requested_scale="1.0")
            self.assertFalse(target.exists())
            self.assertEqual(json.loads(
                (duplicate_output / "gui-settings-ui-block-import.json").read_text())["status"], "RED")

    def test_atomic_publish_failure_keeps_red_receipt_and_no_partial_target(self) -> None:
        source_bytes = self.template.encode() + self.block
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_bytes(source_bytes)
            output = root / "evidence"
            output.mkdir()
            target = root / "pdx_settings.txt"
            with mock.patch("capture_session.os.link", side_effect=OSError("link rejected")):
                with self.assertRaisesRegex(OSError, "link rejected"):
                    import_ui_saved_gui_block(target, self.template, source,
                                              sha(source_bytes), output, requested_scale="1.0")
            self.assertFalse(target.exists())
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual((output / "gui-settings-ui-import-prepared.pdx.txt").read_bytes(),
                             self.template.encode() + self.block)
            receipt = json.loads(
                (output / "gui-settings-ui-block-import.json").read_text())
            self.assertEqual(receipt["status"], "RED")
            self.assertFalse(receipt["atomic_exclusive_publish"])
            self.assertTrue(Path(receipt["staging_path"]).is_file())

    def test_rejects_symlink_source_if_platform_allows_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_bytes(self.block)
            link = root / "link.txt"
            try:
                link.symlink_to(source)
            except OSError:
                self.skipTest("Symlink creation unavailable on this host")
            output = root / "evidence"
            output.mkdir()
            target = root / "pdx_settings.txt"
            with self.assertRaises(Exception):
                import_ui_saved_gui_block(target, self.template, link,
                                          sha(self.block), output, requested_scale="1.0")
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
