"""Real-file regression for pip --target RECORD script relocation."""
from __future__ import annotations

import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from faith_power_promo.record_validation import (
    InstalledRecordSpec, ScriptMapping, validate_installed_record,
)


class InstalledRecordValidationTests(unittest.TestCase):
    def _record(self, root: Path, relative: str, data: bytes) -> Path:
        directory = root / 'sample-1.0.dist-info'
        directory.mkdir(exist_ok=True)
        encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        record = directory / 'RECORD'
        record.write_text(relative + ',sha256=' + encoded + ',' + str(len(data)) + '\n', encoding='utf-8')
        return record

    def test_target_script_relocation_preserves_exact_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bin').mkdir()
            payload = b'exact-installed-script'
            script = root / 'bin/voice.exe'
            script.write_bytes(payload)
            record = self._record(root, '../../bin/voice.exe', payload)
            # This is the original failing consumer's real path, not a mock.
            self.assertFalse((root / '../../bin/voice.exe').is_file())
            result = validate_installed_record(InstalledRecordSpec(root, record,
                (ScriptMapping('../../bin/voice.exe', 'bin/voice.exe'),)))
            self.assertEqual(result.checked_payloads, 1)
            self.assertEqual(result.mapped_scripts[0].actual_path, str(script.resolve()))
            self.assertEqual(result.mapped_scripts[0].sha256, hashlib.sha256(payload).hexdigest())

    def test_target_mapping_does_not_skip_tampered_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bin').mkdir()
            (root / 'bin/voice.exe').write_bytes(b'tampered')
            record = self._record(root, '../../bin/voice.exe', b'original')
            with self.assertRaisesRegex(ValueError, 'digest or size mismatch'):
                validate_installed_record(InstalledRecordSpec(root, record,
                    (ScriptMapping('../../bin/voice.exe', 'bin/voice.exe'),)))

    def test_unknown_escape_is_rejected_without_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self._record(root, '../../bin/unknown.exe', b'payload')
            with self.assertRaisesRegex(ValueError, 'Unmapped installed RECORD escape'):
                validate_installed_record(InstalledRecordSpec(root, record))

    def test_missing_mapped_script_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self._record(root, '../../bin/voice.exe', b'payload')
            with self.assertRaises(FileNotFoundError):
                validate_installed_record(InstalledRecordSpec(root, record,
                    (ScriptMapping('../../bin/voice.exe', 'bin/voice.exe'),)))

    def test_normal_package_payload_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'pkg').mkdir()
            (root / 'pkg/file.py').write_bytes(b'package-payload')
            record = self._record(root, 'pkg/file.py', b'package-payload')
            result = validate_installed_record(InstalledRecordSpec(root, record))
            self.assertEqual(result.checked_payloads, 1)
            self.assertEqual(result.mapped_scripts, ())


if __name__ == '__main__':
    unittest.main()
