#!/usr/bin/env python3
"""Focused tests for protected-storage hashing in terminal acceptance."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_terminal_acceptance as terminal


class FileDigestTests(unittest.TestCase):
    def test_hashes_the_exact_read_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "protected.bin"
            path.write_bytes(b"protected-storage")

            self.assertEqual(
                terminal.file_digest(path),
                {
                    "size": 17,
                    "sha256": hashlib.sha256(b"protected-storage").hexdigest(),
                },
            )

    def test_retries_a_transient_permission_error(self) -> None:
        path = Path("remotecache.vdf")
        with (
            mock.patch.object(
                Path,
                "read_bytes",
                side_effect=[PermissionError("locked"), b"released"],
            ),
            mock.patch.object(terminal.time, "sleep") as sleep,
        ):
            digest = terminal.file_digest(path, retry_seconds=1)

        self.assertEqual(digest["size"], 8)
        self.assertEqual(digest["sha256"], hashlib.sha256(b"released").hexdigest())
        sleep.assert_called_once()

    def test_persistent_permission_error_remains_red(self) -> None:
        path = Path("remotecache.vdf")
        with mock.patch.object(
            Path, "read_bytes", side_effect=PermissionError("still locked")
        ):
            with self.assertRaises(PermissionError):
                terminal.file_digest(path, retry_seconds=0)


if __name__ == "__main__":
    unittest.main()
