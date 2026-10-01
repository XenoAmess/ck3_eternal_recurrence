from __future__ import annotations

import hashlib
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import stage_nonwar_12002_pair_files as stage_files
from xar_autoplayer import environment


class PairFileTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1] / ".task-tmp/nonwar-pair-file-tests"
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.save = self.source / "profile/save games/xar_checkpoint.ck3"
        self.driver = self.source / "native-session/driver-state.json"
        self.save.parent.mkdir(parents=True)
        self.driver.parent.mkdir(parents=True)
        with zipfile.ZipFile(self.save, "w") as archive:
            archive.writestr("gamestate", "fake-only fixture, not a live seed")
        self.pipe = r"\\.\pipe\xar_pair_fake"
        self.save_sha = hashlib.sha256(self.save.read_bytes()).hexdigest()
        checkpoint = {"name": "xar_checkpoint.ck3", "size": self.save.stat().st_size,
                      "sha256": self.save_sha, "date_raw": 123, "history_index": 1,
                      "episode_character_id": 100, "episode_run_id": "fake-100"}
        self.driver.write_text(json.dumps({
            "format_version": 2, "pipe_name": self.pipe, "bridge_pid": 99,
            "episode_character_id": 100, "episode_run_id": "fake-100",
            "last_checkpoint": checkpoint,
            "command_history": [{"index": 1, "command": "save-checkpoint", "ok": True,
                                 "result": {"checkpoint": checkpoint}}],
            "rollback_war_failures": [], "rollback_war_failure": None,
            "managed_restore_transaction": None,
        }), encoding="utf-8")
        self.driver_sha = hashlib.sha256(self.driver.read_bytes()).hexdigest()

    def args(self):
        return stage_files.parser().parse_args([
            "--source-save", str(self.save), "--source-driver", str(self.driver),
            "--target-state", str(self.root / "target"), "--pipe", self.pipe,
            "--expected-save-sha256", self.save_sha,
            "--expected-driver-sha256", self.driver_sha,
            "--expected-character-id", "100", "--expected-episode-run-id", "fake-100",
            "--expected-date-raw", "123", "--expected-history-index", "1"])

    def test_real_file_validators_and_byte_preserving_copy_without_process_access(self) -> None:
        with (mock.patch.object(environment, "ck3_processes", side_effect=RuntimeError("CK3 forbidden")),
              mock.patch.object(environment, "ck3_process_inventory", side_effect=RuntimeError("CK3 forbidden"))):
            result = stage_files.stage(self.args())
        self.assertEqual(result["status"], "PASS_STATIC_FILE_PAIR")
        self.assertEqual((self.root / "target/profile/save games/xar_checkpoint.ck3").read_bytes(), self.save.read_bytes())
        self.assertEqual((self.root / "target/native-session/driver-state.json").read_bytes(), self.driver.read_bytes())
        self.assertFalse(result["pipe_episode_history_rewritten"])
        self.assertFalse(result["official_zero_process_preflight_completed"])
        self.assertEqual(result["robert_credit_days"], 0)

    def test_mismatched_canonical_pin_rejects_before_copy(self) -> None:
        args = self.args()
        args.expected_save_sha256 = "f" * 64
        original_driver = self.driver.read_bytes()
        with self.assertRaisesRegex(ValueError, "save_sha"):
            stage_files.stage(args)
        self.assertFalse(args.target_state.exists())
        self.assertEqual(self.driver.read_bytes(), original_driver)

    def test_refused_existing_target_keeps_its_files_unchanged(self) -> None:
        args = self.args()
        args.target_state.mkdir()
        marker = args.target_state / "existing.txt"
        marker.write_text("existing archive", encoding="utf-8")
        argv = []
        for name, value in vars(args).items():
            if value is None or value is False:
                continue
            argv.extend(["--" + name.replace("_", "-"), str(value)])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(stage_files.main(argv), 1)
        self.assertEqual(list(args.target_state.iterdir()), [marker])
        self.assertEqual(marker.read_text(encoding="utf-8"), "existing archive")


if __name__ == "__main__":
    unittest.main()
