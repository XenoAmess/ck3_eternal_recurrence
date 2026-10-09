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

from PIL import Image, ImageDraw

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

    def review_fixture(self):
        before, moved = self.root / "before.png", self.root / "moved.png"
        original = Image.new("RGB", (100, 80), "black")
        ImageDraw.Draw(original).rectangle((10, 10, 59, 59), fill="white")
        original.save(before)
        current = Image.new("RGB", original.size, "black")
        ImageDraw.Draw(current).rectangle((30, 10, 79, 59), fill="white")
        current.save(moved)
        frame = self.write("fresh-frame.json", {
            "schema": "ck3.steam_fresh_desktop_frame.v1", "captured_at_utc": (self.now - timedelta(seconds=4)).isoformat(),
            "steam_pid": 123, "before_path": str(before), "moved_path": str(moved),
            "before_sha256": keeper.pin(before)["sha256"], "moved_sha256": keeper.pin(moved)["sha256"],
            "before_rect": [10, 10, 60, 60], "moved_rect": [30, 10, 80, 60],
            "restored_rect": [10, 10, 60, 60], "desktop_size": [100, 80],
            "moving_edge_changed": True, "clock_check": None})
        frozen_path = self.write("frozen.json", {"run_id": "synthetic-only", "argv": ["unused"]})
        inputs = self.write("keeper/inputs.json", {"synthetic": True})
        review_image = self.root / "direct-review.png"
        current.save(review_image)
        nonce = "a" * 32
        frozen = {"run_id": "synthetic-only", "screen_task": "synthetic-screen",
                  "_checked_frozen_argv": keeper.pin(frozen_path)}
        challenge = self.write("challenge.json", {
            "schema": "ck3-mod-acceptance-review-challenge-v1", "created_at_utc": (self.now - timedelta(seconds=3)).isoformat(),
            "nonce": nonce, "run_id": frozen["run_id"], "screen_task": frozen["screen_task"],
            "frozen_argv": keeper.pin(frozen_path), "keeper_root": str(inputs.parent),
            "keeper_inputs": keeper.pin(inputs), "frame": keeper.pin(frame),
            "image": keeper.pin(moved), "review_image": keeper.pin(review_image)})
        proof = self.write("proof.json", {
            "schema": "ck3-mod-acceptance-direct-review-v1", "reviewed_at_utc": (self.now - timedelta(seconds=2)).isoformat(),
            "reviewer": "synthetic-operator", "direct_image_review": True, "steam_offline_confirmed": True,
            "observed_nonce": nonce, "run_id": frozen["run_id"], "screen_task": frozen["screen_task"],
            "frozen_argv": keeper.pin(frozen_path), "challenge": keeper.pin(challenge),
            "image": keeper.pin(moved), "review_image": keeper.pin(review_image)})
        return frozen, inputs.parent, proof, challenge, nonce

    def test_fresh_bound_direct_review_and_nonce(self):
        frozen, root, proof, challenge, nonce = self.review_fixture()
        result = launcher.validate_review(frozen, root, proof, challenge, nonce, "synthetic-operator", now=self.now)
        self.assertEqual(result["screen_task"], frozen["screen_task"])
        with self.assertRaisesRegex(ValueError, "nonce"):
            launcher.validate_review(frozen, root, proof, challenge, "b" * 32, "synthetic-operator", now=self.now)
        with self.assertRaisesRegex(ValueError, "stale"):
            launcher.validate_review(frozen, root, proof, challenge, nonce, "synthetic-operator", now=self.now + timedelta(minutes=11))
        changed = copy.deepcopy(frozen); changed["run_id"] = "other-run"
        with self.assertRaisesRegex(ValueError, "another"):
            launcher.validate_review(changed, root, proof, challenge, nonce, "synthetic-operator", now=self.now)

    def test_mutated_original_image_rejects_previously_reviewed_proof(self):
        frozen, root, proof, challenge, nonce = self.review_fixture()
        image = Path(keeper.read_json(challenge)["image"]["path"])
        image.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Pinned input changed"):
            launcher.validate_review(frozen, root, proof, challenge, nonce, "synthetic-operator", now=self.now)

    def test_missing_direct_review_or_offline_assertion_rejected(self):
        frozen, root, proof, challenge, nonce = self.review_fixture()
        value = keeper.read_json(proof)
        for field in ("direct_image_review", "steam_offline_confirmed"):
            changed = copy.deepcopy(value); changed[field] = False
            path = self.write(field + ".json", changed)
            with self.assertRaisesRegex(ValueError, "direct Steam offline"):
                launcher.validate_review(frozen, root, path, challenge, nonce, "synthetic-operator", now=self.now)

    def test_frozen_input_pin_changes_block_before_any_launch(self):
        source = self.root / "input.txt"; source.write_bytes(b"original")
        files = {str(source): keeper.pin(source)}
        for name in ("ck3_mod_acceptance_launcher.py", "ck3_mod_acceptance_keeper.py", "ck3_mod_acceptance_queue.py"):
            path = Path(launcher.__file__).with_name(name).resolve(); files[str(path)] = keeper.pin(path)
        frozen_path = self.write("frozen-argv.json", {
            "run_id": "synthetic-only", "argv": ["unused", str(source), "--agent-source-root", "unused"], "files": files,
            "launch_requires_fresh_owned_cas_and_offline_direct_review": True,
            "previous_session_closed": True, "previous_screen_released": True,
            "runtime_manifest": keeper.pin(source)})
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

    def test_original_harmless_child_returncode_is_preserved(self):
        script = self.root / "harmless.py"; script.write_text("raise SystemExit(7)\n", encoding="utf-8")
        frozen = {"argv": [sys.executable, "-B", str(script)], "lease_anchor": str(self.root), "run_id": "synthetic-only"}
        # The portable static runner need not install desktop process tools.
        # Only optional creation-time metadata is synthetic. Popen, PID, its
        # retained handle and wait()/returncode all remain the real OS child.
        metadata_only = SimpleNamespace(
            Process=lambda _pid: SimpleNamespace(create_time=lambda: None),
            NoSuchProcess=type("SyntheticNoSuchProcess", (Exception,), {}))
        with patch.dict(sys.modules, {"psutil": metadata_only}):
            result = launcher.retain_host(self.root, frozen, {}, {"lease": {"synthetic": True}})
        self.assertEqual(result, 1)
        self.assertIsNone(keeper.read_json(self.root / "host-started.json")["create_time"])
        actual = keeper.read_json(self.root / "host-original-process-exit.json")
        self.assertEqual(actual["returncode"], 7)
        self.assertIs(actual["actual_original_popen_wait"], True)
        self.assertIs(actual["normal_ck3_exit_inferred"], False)


if __name__ == "__main__":
    unittest.main()
