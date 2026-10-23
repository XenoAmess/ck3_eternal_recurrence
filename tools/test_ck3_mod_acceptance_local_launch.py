"""Offline regressions for shared admission and once-only control publication.

All desktop images, tasks and processes are synthetic. No Steam/CK3/bus call.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dataclasses import replace
from ck3_mod_acceptance_background_types import CONTROL_QUEUE_MODULE_ORDER_V1
from ck3_mod_acceptance_test_background_fixture import BackgroundSteamFixtureV1, FixtureIdentityReader, make_background_fixture
from ck3_mod_acceptance_steam_gate import recheck_before_popen, validate_observation

import ck3_mod_acceptance_keeper as keeper
import ck3_mod_acceptance_launcher as launcher
import ck3_mod_acceptance_queue as queue


class LocalLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.now = datetime.now(timezone.utc)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        keeper.write_new(path, value)
        return path

    def background_fixture(self) -> BackgroundSteamFixtureV1:
        fixture = make_background_fixture(self.root, now=self.now)
        fixture.write_receipt()
        return fixture

    def test_fresh_bound_background_observation_and_generation(self) -> None:
        fixture = self.background_fixture()
        wire = fixture.result.to_wire()
        admitted = fixture.admission()
        self.assertEqual(admitted["receipt"]["path"], str(fixture.receipt_path))
        self.assertEqual(admitted["steam_pid"], fixture.steam.pid)
        self.assertEqual(validate_observation(wire, machine_id=fixture.result.machine_id,
            reader=fixture.reader, now=self.now), fixture.result)
        with self.assertRaises(ValueError):
            validate_observation(wire, machine_id="other-machine", reader=fixture.reader, now=self.now)
        with self.assertRaises(ValueError):
            validate_observation(wire, machine_id=fixture.result.machine_id, reader=fixture.reader,
                now=self.now + timedelta(seconds=31))
        changed = FixtureIdentityReader(replace(fixture.steam, birth_filetime="134000000000000002"))
        with self.assertRaises(ValueError):
            validate_observation(wire, machine_id=fixture.result.machine_id, reader=changed, now=self.now)

    def test_mutated_receipt_rejects_previously_admitted_observation(self) -> None:
        fixture = self.background_fixture()
        admitted = fixture.admission()
        fixture.receipt_path.write_bytes(fixture.receipt_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "receipt (changed|content changed)"):
            recheck_before_popen(admitted, reader=fixture.reader)

    def test_missing_or_crossed_native_observation_is_rejected(self) -> None:
        fixture = self.background_fixture()
        for field, value in (("native_evidence", None), ("offline_mode", False),
                             ("observation_method", "cef_app_getters")):
            wire = copy.deepcopy(fixture.result.to_wire())
            wire[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_observation(wire, machine_id=fixture.result.machine_id,
                                     reader=fixture.reader, now=self.now)
        wire = copy.deepcopy(fixture.result.to_wire())
        del wire["native_evidence"]
        with self.assertRaises(ValueError):
            validate_observation(wire, machine_id=fixture.result.machine_id,
                                 reader=fixture.reader, now=self.now)

    def test_frozen_input_pin_changes_block_before_any_launch(self) -> None:
        source = self.root / "input.txt"; source.write_bytes(b"original")
        manifest = self.write("runtime-manifest.json", {"schema": "ck3-mod-acceptance-shared-runtime-v1"})
        files = {str(source): keeper.pin(source)}
        for module_name in CONTROL_QUEUE_MODULE_ORDER_V1:
            name = module_name + ".py"
            path = Path(launcher.__file__).with_name(name).resolve(); files[str(path)] = keeper.pin(path)
        frozen_path = self.write("frozen-argv.json", {
            "run_id": "synthetic-only", "argv": ["unused", str(source), "--agent-source-root", "unused"], "files": files,
            "launch_requires_fresh_owned_cas_and_background_offline": True,
            "previous_session_closed": True, "previous_screen_released": True,
            "runtime_manifest": keeper.pin(manifest)})
        self.write("ready-context.json", {"run_id": "synthetic-only", "run_dir": str(self.root),
                   "frozen_argv": keeper.pin(frozen_path)})
        launcher.frozen_run(self.root)
        source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Pinned input changed"):
            launcher.frozen_run(self.root)

    def test_stopped_keeper_is_rejected_without_any_bus_operation(self):
        root = self.root / "keeper"; root.mkdir()
        (root / "STOP").touch()
        with patch.object(keeper, "load_lease_module", side_effect=AssertionError("must not touch bus")):
            with self.assertRaisesRegex(ValueError, "stopped"):
                keeper.live_lease(root)

    def test_wrong_or_stale_actual_cas_owner_is_rejected(self):
        root = self.root / "keeper"; root.mkdir()
        repo = self.root / "repo"; repo.mkdir()
        module_file = repo / "lease.py"; module_file.write_bytes(b"synthetic source")
        head, task = "a" * 40, "synthetic-screen"
        lease = {"task_id": task, "checkout_head": head, "sequence": 5, "cli_sha256": keeper.BUS_SHA}
        inputs = self.write("keeper/inputs.json", {"repo": str(repo), "checkout_head": head, "task_id": task,
            "source_cli": str(repo / "unused.py"), "bus_dir": str(repo / "unused-bus"),
            "bus_cli_sha256": keeper.BUS_SHA, "lease_module": keeper.pin(module_file)})
        self.write("keeper/ready.json", {"inputs": keeper.pin(inputs), "lease": lease})
        (root / "journal.jsonl").write_text(json.dumps({"result": "OWNED_CAS", "lease": lease}) + "\n", encoding="utf-8")
        actual_module = keeper.load_lease_module(Path(__file__).resolve().parents[1])
        owner = {"schema": "codex.task_bus.v1", "task_id": task, "state": "running", "resources": ["ck3-screen:acquired"],
            "last_sequence": 5, "repo": str(repo), "git": {"head": head, "dirty_entries": 0},
            "updated_at_utc": self.now.isoformat(), "stale": False}
        for change in ({"last_sequence": 6}, {"updated_at_utc": (self.now - timedelta(seconds=601)).isoformat()}):
            changed = {**owner, **change}
            module = SimpleNamespace(checkout_head=lambda _: head, checked_owner=actual_module.checked_owner,
                                     call_bus=lambda *a, **kw: {"tasks": [changed]})
            with patch.object(keeper, "load_lease_module", return_value=module):
                with self.assertRaises(RuntimeError): keeper.live_lease(root, now=self.now)

    def test_once_ledger_rejects_same_content_and_same_id_under_new_name(self):
        raw = b'{"steps":[{"id":"one","tool":"snapshot"}]}'
        ledger = self.root / "ledger"
        queue.claim_plan(ledger, "one.json", raw, ["one"])
        with self.assertRaisesRegex(ValueError, "never replay"):
            queue.claim_plan(ledger, "another.json", raw, ["one"])
        with self.assertRaisesRegex(ValueError, "never replay"):
            queue.claim_plan(ledger, "third.json", b"different original bytes", ["one"])

    def test_current_metadata_and_unfinished_controls_are_enforced(self):
        report = {"steps": [], "mcp_tools": {"tools": [{"name": "snapshot", "inputSchema": {
            "type": "object", "properties": {"expected_revision": {"type": "integer"}, "include": {"type": "boolean"}},
            "required": ["expected_revision"], "additionalProperties": False}}]}}
        good = [{"id": "one", "tool": "snapshot", "args": {"include": False}}]
        self.assertEqual(queue.validate_steps(good, report), ["one"])
        self.assertNotIn("expected_revision", good[0]["args"])
        for bad in ([{"id": "one", "tool": "absent"}], [{"id": "one", "kind": "unqualified"}]):
            with self.assertRaises(ValueError): queue.validate_steps(bad, report)
        unfinished = copy.deepcopy(report); unfinished["steps"] = [{"id": "old"}]
        with self.assertRaisesRegex(ValueError, "in flight"):
            queue.validate_steps(good, unfinished)
        with self.assertRaises(Exception):
            queue.validate_steps([{"id": "one", "tool": "snapshot", "args": {"include": "false"}}], report)

    def test_host_exit_zero_is_not_native_game_exit_proof(self):
        host = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
        frozen = {"argv": ["unused", str(host), "--agent-source-root", "unused"],
                  "files": {str(host): keeper.pin(host)}}
        self.assertIsNone(queue.native_zero_proof(frozen, {"returncode": 0, "actual_original_popen_wait": True}))

    def test_original_harmless_child_returncode_is_preserved(self) -> None:
        script = self.root / "harmless.py"; script.write_text("raise SystemExit(7)\n", encoding="utf-8")
        frozen = {"argv": [sys.executable, "-B", str(script)], "lease_anchor": str(self.root), "run_id": "synthetic-only"}
        # The portable static runner need not install desktop process tools.
        # Only optional creation-time metadata is synthetic. Popen, PID, its
        # retained handle and wait()/returncode all remain the real OS child.
        metadata_only = SimpleNamespace(
            Process=lambda _pid: SimpleNamespace(create_time=lambda: None),
            NoSuchProcess=type("SyntheticNoSuchProcess", (Exception,), {}))
        fixture = self.background_fixture()
        with fixture.os_boundaries(), patch.dict(sys.modules, {"psutil": metadata_only}):
            result = launcher.retain_host(self.root, frozen, fixture.admission(), {"lease": {"synthetic": True}})
        self.assertEqual(result, 1)
        self.assertIsNone(keeper.read_json(self.root / "host-started.json")["create_time"])
        actual = keeper.read_json(self.root / "host-original-process-exit.json")
        self.assertEqual(actual["returncode"], 7)
        self.assertIs(actual["actual_original_popen_wait"], True)
        self.assertIs(actual["normal_ck3_exit_inferred"], False)


if __name__ == "__main__":
    unittest.main()
