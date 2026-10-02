"""Isolated-bus tests for the H2743 CAS protocol candidate.

Set H2743_REVIEWED_BUS_SOURCE to the exact reviewed #685 CLI to run these
integration tests. The default suite skips when that separate source is absent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MODULE_PATH = HERE / "h2743_screen_cas_protocol.py"
SPEC = importlib.util.spec_from_file_location("h2743_screen_cas_test_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("H2743 CAS protocol module unavailable")
cas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cas)


class ScreenCasProtocolIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        candidate = os.environ.get("H2743_REVIEWED_BUS_SOURCE")
        if not candidate:
            self.skipTest("exact reviewed #685 CLI was not explicitly supplied")
        self.source = Path(candidate)
        if not self.source.is_file() or cas.sha256(self.source) != cas.REVIEWED_BUS_CLI_SHA256:
            self.fail("injected reviewed #685 CLI SHA differs")
        self.temp = tempfile.TemporaryDirectory(prefix="h2743-cas-temp-bus-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bus = self.root / "bus"
        (self.bus / "tasks").mkdir(parents=True)
        (self.bus / "bin").mkdir()
        (self.bus / ".lock").write_bytes(b"0")
        (self.bus / "events.jsonl").write_bytes(b"")
        (self.bus / "sequence.txt").write_text("0\n", encoding="ascii")
        shutil.copyfile(self.source, self.bus / "bin/codex_task_bus.py")

    def protocol(self, label: str):
        return cas.ScreenCasProtocol(
            source=self.source, bus_dir=self.bus, repo=REPO,
            python=Path(sys.executable), evidence_dir=self.root / label)

    def test_claim_heartbeat_release_exact_readback(self) -> None:
        protocol = self.protocol("attempt-01")
        claim = protocol.claim("h2743-temp-screen-claim-01", "isolated CAS test")
        self.assertEqual(claim["event"]["sequence"], 1)
        self.assertEqual(claim["owners"], ["h2743-temp-screen-claim-01"])
        heartbeat = protocol.heartbeat()
        self.assertEqual(heartbeat["event"]["sequence"], 2)
        with self.assertRaisesRegex(cas.ScreenCasStop, "cleanup"):
            protocol.release("done", cleanup_proven=False)
        released = protocol.release("isolated test cleaned", cleanup_proven=True)
        self.assertEqual(released["event"]["sequence"], 3)
        self.assertEqual(released["owners"], [])
        self.assertTrue(protocol.released)
        self.assertEqual(sorted(path.name for path in (self.root / "attempt-01").iterdir()), [
            "operation-001-registered", "operation-002-heartbeat", "operation-003-completed"])

    def test_unreleased_stale_owner_blocks_new_claim(self) -> None:
        first = self.protocol("attempt-02")
        first.claim("h2743-temp-screen-old", "old temp owner")
        snapshot_path = self.bus / "tasks/h2743-temp-screen-old.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["updated_at_utc"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        before = (self.bus / "events.jsonl").read_bytes()
        second = self.protocol("attempt-03")
        with self.assertRaisesRegex(cas.ScreenCasStop, "refused"):
            second.claim("h2743-temp-screen-new", "must stop")
        self.assertEqual((self.bus / "events.jsonl").read_bytes(), before)
        self.assertTrue(second.uncertain)
        self.assertTrue((self.root / "attempt-03/operation-001-registered/stop.json").is_file())

    def test_done_screen_record_blocks_claim_and_existing_owner_heartbeat(self) -> None:
        first = self.protocol("attempt-10")
        first.claim("h2743-temp-screen-done", "done plus screen test")
        snapshot_path = self.bus / "tasks/h2743-temp-screen-done.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["state"] = "done"
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        events_path = self.bus / "events.jsonl"
        event = json.loads(events_path.read_text(encoding="utf-8").strip())
        event["state"] = "done"
        events_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        before = events_path.read_bytes()
        second = self.protocol("attempt-11")
        with self.assertRaisesRegex(cas.ScreenCasStop, "refused"):
            second.claim("h2743-temp-screen-after-done", "must stop")
        with self.assertRaisesRegex(cas.ScreenCasStop, "receipt event differs"):
            first.heartbeat()
        self.assertEqual(events_path.read_bytes(), before)
        self.assertTrue((self.root / "attempt-11/operation-001-registered/stop.json").is_file())
        self.assertTrue((self.root / "attempt-10/operation-002-heartbeat/stop.json").is_file())

    def test_wrong_expected_sequence_stops_without_a_new_event(self) -> None:
        protocol = self.protocol("attempt-04")
        protocol.claim("h2743-temp-screen-sequence", "sequence test")
        protocol.sequence = 99
        before = (self.bus / "events.jsonl").read_bytes()
        with self.assertRaisesRegex(cas.ScreenCasStop, "refused"):
            protocol.heartbeat()
        self.assertEqual((self.bus / "events.jsonl").read_bytes(), before)
        self.assertTrue(protocol.uncertain)

    def test_installed_sha_mismatch_stops_before_claim(self) -> None:
        protocol = self.protocol("attempt-05")
        (self.bus / "bin/codex_task_bus.py").write_bytes(b"different")
        before = (self.bus / "events.jsonl").read_bytes()
        with self.assertRaisesRegex(cas.ScreenCasStop, "SHA pair absent"):
            protocol.claim("h2743-temp-screen-sha", "must stop")
        self.assertEqual((self.bus / "events.jsonl").read_bytes(), before)
        folder = self.root / "attempt-05/operation-001-registered"
        self.assertTrue((folder / "argv.json").is_file())
        self.assertTrue((folder / "stop.json").is_file())
        self.assertFalse((folder / "process.json").exists())

    def test_event_gap_stops_before_heartbeat_and_forbids_retry(self) -> None:
        protocol = self.protocol("attempt-06")
        protocol.claim("h2743-temp-screen-gap", "gap test")
        (self.bus / "events.jsonl").write_text("", encoding="utf-8")
        with self.assertRaisesRegex(cas.ScreenCasStop, "sequence gap"):
            protocol.heartbeat()
        self.assertTrue(protocol.uncertain)
        with self.assertRaisesRegex(cas.ScreenCasStop, "no blind retry"):
            protocol.heartbeat()
        self.assertEqual(sorted(path.name for path in (self.root / "attempt-06").iterdir()),
                         ["operation-001-registered", "operation-002-heartbeat"])
        self.assertTrue((self.root / "attempt-06/operation-002-heartbeat/stop.json").is_file())
        self.assertFalse((self.root / "attempt-06/operation-002-heartbeat/process.json").exists())

    def test_cli_timeout_preserves_partial_output_and_stops(self) -> None:
        protocol = self.protocol("attempt-07")
        with mock.patch.object(cas.subprocess, "run", side_effect=subprocess.TimeoutExpired(
                cmd="reviewed-cli", timeout=30, output=b"partial stdout", stderr=b"partial stderr")):
            with self.assertRaisesRegex(cas.ScreenCasStop, "timed out"):
                protocol.claim("h2743-temp-screen-timeout", "timeout test")
        folder = self.root / "attempt-07/operation-001-registered"
        self.assertEqual((folder / "stdout.bin").read_bytes(), b"partial stdout")
        self.assertEqual((folder / "stderr.bin").read_bytes(), b"partial stderr")
        self.assertTrue((folder / "stop.json").is_file())
        self.assertTrue(protocol.uncertain)

    def test_authority_path_is_unconditionally_refused(self) -> None:
        with mock.patch.object(cas, "AUTHORITY_BUS", self.bus):
            with self.assertRaisesRegex(cas.ScreenCasStop, "AUTHORITY_STOP"):
                self.protocol("attempt-08")
        self.assertFalse((self.root / "attempt-08").exists())

    def test_alias_retarget_cannot_redirect_a_later_claim(self) -> None:
        alias = self.root / "bus-alias"
        def make_alias(target: Path) -> bool:
            try:
                alias.symlink_to(target, target_is_directory=True)
                return False
            except OSError as error:
                if os.name != "nt":
                    self.skipTest(f"directory alias unavailable: {error}")
                result = subprocess.run(["cmd.exe", "/c", "mklink", "/J",
                                         str(alias), str(target)], capture_output=True,
                                        timeout=15, check=False)
                if result.returncode != 0:
                    self.skipTest("directory symlink and junction unavailable")
                return True

        junction = make_alias(self.bus)
        protocol = cas.ScreenCasProtocol(
            source=self.source, bus_dir=alias, repo=REPO, python=Path(sys.executable),
            evidence_dir=self.root / "attempt-09")
        self.assertEqual(protocol.bus_dir, self.bus.resolve())
        alias.rmdir() if junction else alias.unlink()
        fake_authority = self.root / "fake-authority"
        fake_authority.mkdir()
        junction = make_alias(fake_authority)
        try:
            with mock.patch.object(cas, "AUTHORITY_BUS", fake_authority):
                protocol.claim("h2743-temp-screen-alias", "alias isolation test")
            self.assertTrue((self.bus / "tasks/h2743-temp-screen-alias.json").is_file())
            self.assertEqual(list(fake_authority.iterdir()), [])
        finally:
            alias.rmdir() if junction else alias.unlink()


if __name__ == "__main__":
    unittest.main()
