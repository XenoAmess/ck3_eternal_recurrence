from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools import g2_preview_operator


class G2PreviewOperatorTest(unittest.TestCase):
    def test_private_faction_round_is_narrowly_forwarded(self) -> None:
        args = g2_preview_operator.parser().parse_args([
            "run",
            "--manifest",
            "manifest.json",
            "--output",
            "attempt",
            "--private-faction-round-id",
            "R765",
        ])
        command = g2_preview_operator.native_auto_run_command(
            ["python", "agent.py"],
            turns=40,
            timeout=7200,
            readiness_timeout=300,
            private_faction_round_id_value=args.private_faction_round_id,
        )
        self.assertEqual(command[-3:], [
            "--allow-private-faction-gift-formal-trial",
            "--private-faction-round-id",
            "R765",
        ])
        self.assertNotIn("--allow-private-faction-gift-formal-trial", g2_preview_operator.native_auto_run_command(
            ["python", "agent.py"],
            turns=40,
            timeout=7200,
            readiness_timeout=300,
            private_faction_round_id_value=None,
        ))
        with self.assertRaises(SystemExit):
            g2_preview_operator.parser().parse_args([
                "run", "--manifest", "manifest.json", "--output", "attempt",
                "--private-faction-round-id", "<ALLOCATED_ROUND>",
            ])

    def test_verify_zip_binds_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "preview.zip"
            archive.write_bytes(b"frozen-preview")
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = g2_preview_operator.command_verify_zip(argparse.Namespace(
                    zip=archive,
                    expected_sha256=expected,
                ))
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())["sha256"], expected)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                g2_preview_operator.command_verify_zip(argparse.Namespace(
                    zip=archive,
                    expected_sha256="0" * 64,
                ))

    def test_stop_request_is_created_once_from_manifest_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            state.mkdir()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "python": str(root / "python.exe"),
                "source_repo": str(root / "repo"),
                "state_dir": str(state),
                "game_dir": str(root / "game"),
                "pipe": r"\\.\pipe\test",
                "dll": str(root / "bridge.dll"),
                "injector": str(root / "injector.exe"),
            }), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = g2_preview_operator.command_request_stop(argparse.Namespace(manifest=manifest))
            self.assertEqual(result, 0)
            stop_path = state / "native-auto-run.stop"
            self.assertEqual(stop_path.read_text(encoding="utf-8"), "stop\n")
            with self.assertRaises(FileExistsError):
                g2_preview_operator.command_request_stop(argparse.Namespace(manifest=manifest))


if __name__ == "__main__":
    unittest.main()
