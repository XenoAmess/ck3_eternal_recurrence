"""Regression for the real Windows LF/CRLF host-freezer admission failure."""
from pathlib import Path
import hashlib
import tempfile
import unittest

from ck3_host_projection import checked_effective_host, freeze_host_projection


class HostProjectionTests(unittest.TestCase):
    def test_windows_text_writer_failure_is_reproduced(self):
        source = "def answer():\n    return 42\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old-host.py"
            raw = source.replace("\n", "\r\n").encode("utf-8")
            path.write_bytes(raw)
            config = {"original_host": {"path": str(path), "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest()}, "edits": [],
                "effective_host_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest()}
            with self.assertRaisesRegex(ValueError, "Effective host differs"):
                checked_effective_host(config)

    def test_frozen_crlf_input_passes_actual_wrapper_semantics_and_executes(self):
        source = "def answer():\r\n    return '原生42'\r\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new-host.py"
            config = freeze_host_projection(path, source, [("原生42", "原生43")])
            self.assertNotIn(b"\r\n", path.read_bytes())
            namespace = {}
            exec(compile(checked_effective_host(config), str(path), "exec"), namespace)
            self.assertEqual(namespace["answer"](), "原生43")


if __name__ == "__main__":
    unittest.main()
