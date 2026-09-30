"""Temporary-bus tests for the recovery CAS fence; no real desktop operation."""

from __future__ import annotations

from argparse import Namespace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import codex_task_bus as bus_module
import desktop_steam_offline_recovery as recovery


TASK = "desktop-recovery-fixture"


class RecoveryCasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state_dir = self.root / "state"
        (self.state_dir / "control").mkdir(parents=True)
        self.output_dir = self.root / "attempt"
        self.bus_dir = self.root / "bus"
        (self.bus_dir / "bin").mkdir(parents=True)
        (self.bus_dir / "tasks").mkdir()
        (self.bus_dir / ".lock").write_bytes(b"0")
        (self.bus_dir / "events.jsonl").write_bytes(b"")
        (self.bus_dir / "sequence.txt").write_text("0\n", encoding="ascii")
        self.installed = self.bus_dir / "bin" / "codex_task_bus.py"
        shutil.copyfile(recovery.BUS_SOURCE, self.installed)
        self.authority_pin = patch.object(recovery, "DEFAULT_BUS", self.installed)
        self.contract_pin = patch.object(
            recovery, "APPROVED_RECOVERY_CONTRACT_SHA256", "A" * 64)
        self.authority_pin.start()
        self.contract_pin.start()
        self.addCleanup(self.contract_pin.stop)
        self.addCleanup(self.authority_pin.stop)
        self.cli_sha = hashlib.sha256(recovery.BUS_SOURCE.read_bytes()).hexdigest().upper()
        task, _ = bus_module.update_task(
            self.bus_dir, TASK, state="running", summary="synthetic screen owner",
            next_step="", repo=Path(__file__).resolve().parent.parent,
            resources=[recovery.SCREEN_RESOURCE], kind="registered",
            expected_cli_sha256=self.cli_sha,
        )
        self.sequence = task["last_sequence"]
        self.marker = self.state_dir / "control" / recovery.RECOVERY_MARKER_NAME
        self.args = Namespace(
            state_dir=self.state_dir, recovery_marker=self.marker,
            recovery_marker_sha256="", expected_cli_sha256=self.cli_sha,
            expected_sequence=self.sequence, task_bus=self.installed,
            task_id=TASK, output_dir=self.output_dir,
        )
        self.write_marker()

    def write_marker(self, **changes: object) -> None:
        marker = {
            "schema": recovery.MARKER_SCHEMA,
            "purpose": "steam_offline_desktop_recovery",
            "task_id": TASK,
            "state_dir": str(self.state_dir.resolve()),
            "output_dir": str(self.output_dir.resolve()),
            "task_bus": str(self.installed.resolve()),
            "bus_cli_sha256": self.cli_sha,
            "expected_sequence": self.sequence,
            "authority_contract_sha256": "A" * 64,
            "expires_at_utc": (datetime.now(timezone.utc)
                               + timedelta(minutes=5)).isoformat(),
        }
        marker.update(changes)
        self.marker.write_text(json.dumps(marker), encoding="utf-8")
        self.args.recovery_marker_sha256 = hashlib.sha256(
            self.marker.read_bytes()).hexdigest().upper()

    def event_bytes(self) -> bytes:
        return (self.bus_dir / "events.jsonl").read_bytes()

    def test_exact_fixture_owner_heartbeat_and_readback(self) -> None:
        lease = recovery.recovery_authorization(self.args)
        with patch.object(recovery, "ck3_pids", return_value=[]):
            recovery.require_exclusive_screen(self.args, lease)
        self.assertEqual(lease["sequence"], self.sequence + 1)
        task = bus_module.read_json(bus_module.task_path(self.bus_dir, TASK))
        self.assertEqual(task["last_sequence"], lease["sequence"])

    def test_missing_pins_unsafe_marker_and_expired_marker_stop_before_heartbeat(self) -> None:
        unsafe = self.state_dir / "control" / recovery.UNSAFE_MARKER_NAME
        cases = (
            lambda: setattr(self.args, "expected_cli_sha256", None),
            lambda: unsafe.write_text("unresolved", encoding="utf-8"),
            lambda: self.write_marker(expires_at_utc=(
                datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()),
        )
        for index, change in enumerate(cases):
            with self.subTest(index=index):
                self.args.expected_cli_sha256 = self.cli_sha
                unsafe.unlink(missing_ok=True)
                self.write_marker()
                before = self.event_bytes()
                change()
                with self.assertRaises((RuntimeError, ValueError)):
                    recovery.recovery_authorization(self.args)
                self.assertEqual(self.event_bytes(), before)

    def test_installed_or_source_sha_drift_stops_authorization(self) -> None:
        self.installed.write_bytes(b"old authority CLI")
        with self.assertRaisesRegex(RuntimeError, "SHA differs"):
            recovery.recovery_authorization(self.args)
        self.assertEqual(len(bus_module.read_events(self.bus_dir)), 1)

    def test_private_bus_and_self_minted_marker_are_not_authority(self) -> None:
        with patch.object(recovery, "DEFAULT_BUS", self.root / "fixed-authority" / "bin"
                          / "codex_task_bus.py"):
            with self.assertRaisesRegex(RuntimeError, "fixed authority CLI"):
                recovery.recovery_authorization(self.args)
        with patch.object(recovery, "APPROVED_RECOVERY_CONTRACT_SHA256", None):
            with self.assertRaisesRegex(RuntimeError, "not approved"):
                recovery.recovery_authorization(self.args)
        self.assertEqual(len(bus_module.read_events(self.bus_dir)), 1)

    def test_symlinked_cli_alias_cannot_divert_cas_to_private_bus(self) -> None:
        alias_dir = self.root / "alias"
        (alias_dir / "bin").mkdir(parents=True)
        (alias_dir / "tasks").mkdir()
        (alias_dir / ".lock").write_bytes(b"0")
        (alias_dir / "events.jsonl").write_bytes(b"")
        (alias_dir / "sequence.txt").write_text("0\n", encoding="ascii")
        alias = alias_dir / "bin" / "codex_task_bus.py"
        try:
            alias.symlink_to(self.installed)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        self.args.task_bus = alias
        with self.assertRaisesRegex(RuntimeError, "fixed authority CLI"):
            recovery.recovery_authorization(self.args)
        self.assertEqual((alias_dir / "sequence.txt").read_text(encoding="ascii"), "0\n")
        self.assertEqual((self.bus_dir / "sequence.txt").read_text(encoding="ascii"),
                         f"{self.sequence}\n")

    def test_hardlink_cli_alias_with_identical_bytes_is_not_authority(self) -> None:
        alias = self.root / "other-bin" / "codex_task_bus.py"
        alias.parent.mkdir()
        alias.hardlink_to(self.installed)
        self.args.task_bus = alias
        with self.assertRaisesRegex(RuntimeError, "fixed authority CLI"):
            recovery.recovery_authorization(self.args)
        self.assertEqual(len(bus_module.read_events(self.bus_dir)), 1)

    def test_missing_marker_blocks_recover_before_any_desktop_or_service_mutation(self) -> None:
        self.marker.unlink()
        self.args.bring_steam_forward = False
        self.args.restart_running_todesk_on_stale = True
        self.args.service_timeout_seconds = 2
        with (patch.object(recovery, "ck3_pids", return_value=[]),
              patch.object(recovery, "service_state", return_value={"status": "running"}),
              patch.object(recovery.steam_offline_fresh_frame, "_steam_windows",
                           return_value=[(123, 456)]),
              patch.object(recovery, "ensure_service_running") as ensure,
              patch.object(recovery, "restart_running_service") as restart,
              patch.object(recovery, "capture_fresh_frame") as capture):
            report = recovery.recover(self.args)
        self.assertEqual(report["outcome"], "blocked")
        ensure.assert_not_called()
        restart.assert_not_called()
        capture.assert_not_called()

    def test_recover_rejects_private_bus_before_executing_its_script(self) -> None:
        private = self.root / "private-bus" / "bin" / "codex_task_bus.py"
        private.parent.mkdir(parents=True)
        (private.parent.parent / "tasks").mkdir()
        (private.parent.parent / ".lock").write_bytes(b"0")
        sentinel = self.root / "untrusted-script-ran"
        private.write_text(
            "from pathlib import Path\n"
            f"Path({str(sentinel)!r}).write_text('ran')\n",
            encoding="utf-8",
        )
        self.args.task_bus = private
        report = recovery.recover(self.args)
        self.assertEqual(report["outcome"], "blocked")
        self.assertFalse(sentinel.exists())
        self.assertEqual(report["preflight"]["inspection_skipped"],
                         "recovery_authorization_invalid")

    def test_stale_foreign_owner_stops_before_desktop_even_if_cas_writes(self) -> None:
        other = bus_module.read_json(bus_module.task_path(self.bus_dir, TASK)).copy()
        other["task_id"] = "old-stale-owner"
        other["updated_at_utc"] = (datetime.now(timezone.utc)
                                   - timedelta(days=30)).isoformat()
        other["pid"] = 2696
        bus_module.write_json_atomic(bus_module.task_path(self.bus_dir, "old-stale-owner"),
                                     other)
        lease = recovery.recovery_authorization(self.args)
        with patch.object(recovery, "ck3_pids", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "screen owner changed"):
                recovery.require_exclusive_screen(self.args, lease)
        self.assertEqual(recovery.screen_owners(recovery.task_bus_tasks(self.installed)),
                         [TASK, "old-stale-owner"])

    def test_fresh_foreign_owner_rejects_cas_without_write(self) -> None:
        other = bus_module.read_json(bus_module.task_path(self.bus_dir, TASK)).copy()
        other["task_id"] = "other-owner"
        bus_module.write_json_atomic(bus_module.task_path(self.bus_dir, "other-owner"),
                                     other)
        before = self.event_bytes()
        lease = recovery.recovery_authorization(self.args)
        with patch.object(recovery, "ck3_pids", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "CAS rejected"):
                recovery.require_exclusive_screen(self.args, lease)
        self.assertEqual(self.event_bytes(), before)

    def test_task_snapshot_divergence_after_cas_rejects(self) -> None:
        lease = recovery.recovery_authorization(self.args)
        original = recovery.task_bus_tasks

        def forked_tasks(path: Path) -> list[dict]:
            tasks = original(path)
            tasks[0]["last_sequence"] = -1
            return tasks

        with (patch.object(recovery, "ck3_pids", return_value=[]),
              patch.object(recovery, "task_bus_tasks", side_effect=forked_tasks)):
            with self.assertRaisesRegex(RuntimeError, "readback differs"):
                recovery.require_exclusive_screen(self.args, lease)

    def test_event_tail_divergence_after_cas_rejects(self) -> None:
        lease = recovery.recovery_authorization(self.args)
        original = recovery.task_bus_tasks

        def forked_event(path: Path) -> list[dict]:
            tasks = original(path)
            (self.bus_dir / "sequence.txt").write_text("999\n", encoding="ascii")
            return tasks

        with (patch.object(recovery, "ck3_pids", return_value=[]),
              patch.object(recovery, "task_bus_tasks", side_effect=forked_event)):
            with self.assertRaisesRegex(RuntimeError, "ledger readback differs"):
                recovery.require_exclusive_screen(self.args, lease)


if __name__ == "__main__":
    unittest.main()
