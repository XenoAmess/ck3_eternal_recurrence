"""Focused actual-production wiring tests; tiny synthetic state, no Game/RPC.

The original experimental matrix remains separate. These cases qualify only
the new reader, daily gate, barrier, once-custody and closed recovery wiring.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import driver_state_wal_v1 as wal
from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge.driver_state_history_json import DriverStateHistoryJsonCache
from xar_autoplayer.bridge.ingame_decision_outcome_contract import reject_unresolved_claims
from xar_autoplayer.environment import write_bytes_atomic
from xar_autoplayer.errors import AgentError
from xar_autoplayer import native_session


def state():
    return dict(format_version=2, pipe_name=r"\\.\pipe\xar-wal-production-test",
                bridge_pid=12345, episode_character_id=7,
                episode_run_id="native-7-wal-test", last_checkpoint=None,
                command_history=[], rollback_war_failure=None,
                rollback_war_failures=[], managed_restore_transaction=None,
                succession_expectation=None,
                succession_lifecycle=nd.legacy_rogue_one_life_binding_v1(),
                campaign_goal=None)


def driver(directory, *, enabled=True):
    obj = nd.NativeHeadlessGameplayDriver.__new__(nd.NativeHeadlessGameplayDriver)
    obj.state_dir = directory
    obj.pipe_name = state()["pipe_name"]
    obj._driver_state_lock = threading.RLock()
    obj._history_lock = obj._driver_state_lock
    obj._driver_state_write_lock = threading.Lock()
    obj._driver_state_history_json = DriverStateHistoryJsonCache()
    obj._driver_state_dirty = False
    obj._driver_state_error = None
    obj.allow_driver_state_wal_v1 = enabled
    obj._driver_state_wal_document = None
    obj._driver_state_wal_committed_rows = 0
    obj._driver_state_wal_replay_status = None
    obj._driver_state_wal_base_stat = None
    obj._driver_state_wal_base_sha256 = None
    obj._driver_state_wal_base_version = None
    obj._driver_state_wal_barrier_required = True
    obj._driver_state_wal_barrier_generation = 0
    obj._session_bridge_pid = state()["bridge_pid"]
    obj._episode_character_id = state()["episode_character_id"]
    obj._episode_run_id = state()["episode_run_id"]
    obj._last_checkpoint = None
    obj._command_history = []
    obj._rollback_war_failures = []
    obj._rollback_war_failures_migration_required = False
    obj._managed_restore_transaction = None
    obj._succession_expectation = None
    obj._succession_lifecycle = state()["succession_lifecycle"]
    obj._campaign_goal = None
    obj._natural_successor_persistence_unconfirmed = False
    return obj


def daily(start=2400):
    end = start + 24
    return dict(step="life-advance-one-day", starting_date_raw=start,
                ending_date_raw=end, elapsed_days=1, requested_horizon_days=1,
                paused=True, progress_status="postcondition", final_screen="map_hud",
                active_event=None, pending_character_interaction=None, ordinary_events=[],
                exact_day_native_clock={"stopped": dict(
                    state="triggered", mode="terminal_or_sentinel",
                    starting_date_raw=start, target_date_raw=end,
                    last_observed_date_raw=end, trigger_date_raw=end,
                    completed_daily_ticks=1, overshoot_days=0,
                    trigger_reasons=["date_deadline"], trigger_flags=1,
                    pause_wrapper_called=True, pause_observed=True,
                    terminal_observed=False, abnormal=False)})


def record_day(obj, start=2400):
    obj._record_command("life-advance-one-day", ok=True, result=daily(start))


def active(obj):
    obj._persist_driver_state(persistence_reason="fixture_initial_barrier")
    record_day(obj)
    path = obj._native_driver_state_path()
    assert json.loads(path.read_bytes())["format_version"] == 3, obj._driver_state_error
    return path


class ProductionWal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="xar-wal-focused-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_default_off_and_legacy_reader(self):
        # Source is the real constructor; the test fake does not choose default.
        self.assertIn('os.environ.get("XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1") == "1"',
                      inspect.getsource(nd.NativeHeadlessGameplayDriver.__init__))
        obj = driver(self.root, enabled=False)
        obj._persist_driver_state()
        record_day(obj)
        path = obj._native_driver_state_path()
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
        self.assertFalse(path.with_name(wal.FILENAME).exists())
        for version in (1, 2):
            payload = state()
            payload["format_version"] = version
            # Old v1 may omit modern fields. Canonical normalization owns this.
            if version == 1:
                for key in ("rollback_war_failures", "campaign_goal", "succession_lifecycle"):
                    payload.pop(key)
            write_bytes_atomic(path, json.dumps(payload).encode())
            self.assertEqual(obj._read_driver_state(),
                             nd.load_native_driver_state_for_resume_payload(payload, obj.pipe_name))

    def test_daily_deltas_avoid_rewriting_historical_base(self):
        obj = driver(self.root)
        writes = []
        def observed(path, data, **kw):
            writes.append((path.name, len(data)))
            write_bytes_atomic(path, data, **kw)
        with patch.object(nd, "write_bytes_atomic", side_effect=observed):
            path = active(obj)  # Initial v2 plus one v3 activation replace.
            frozen = path.read_bytes()
            writes.clear()
            obj._record_command("query-small-readonly", ok=True, result={"status": "unknown"})
            record_day(obj, 2424)
            record_day(obj, 2448)
        self.assertEqual(path.read_bytes(), frozen)
        self.assertEqual([name for name, _ in writes], [wal.FILENAME, wal.FILENAME])
        replayed, status = wal.load_pair(path)
        self.assertEqual(status, "replayed")
        self.assertEqual(replayed["command_history"], obj._command_history)
        self.assertEqual(nd.load_native_driver_state_for_resume(path, obj.pipe_name)["command_history"],
                         obj._command_history)

    def test_noneligible_and_unknown_rows_cannot_hitchhike_after_failed_barrier(self):
        for ok, command, result in ((False, "submit-once-action", None),
                                    (True, "submit-once-action", {"status": "UNKNOWN"}),
                                    (True, "life-advance", daily())):
            with self.subTest(ok=ok, command=command):
                root = self.root / str(len(list(self.root.iterdir())))
                obj = driver(root)
                path = active(obj)
                with patch.object(nd, "write_bytes_atomic", side_effect=OSError("injected replace failure")):
                    obj._record_command(command, ok=ok, result=result, error=None if ok else "UNKNOWN")
                self.assertTrue(obj._driver_state_wal_barrier_required)
                self.assertIsNotNone(obj._driver_state_error)
                record_day(obj, 2424)
                self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
                self.assertFalse(path.with_name(wal.FILENAME).exists())
                self.assertEqual(json.loads(path.read_bytes())["command_history"], obj._command_history)

    def test_interrupted_or_unproved_day_is_full_barrier(self):
        obj = driver(self.root)
        path = active(obj)
        result = daily(2424)
        result.pop("exact_day_native_clock")
        obj._record_command("life-advance-one-day", ok=True, result=result)
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
        self.assertFalse(path.with_name(wal.FILENAME).exists())

    def test_scope_or_lifecycle_change_is_full_barrier(self):
        obj = driver(self.root)
        path = active(obj)
        obj._episode_run_id = "native-7-new-scope"
        record_day(obj, 2424)
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)

    def test_default_off_still_rejects_bad_or_missing_journal(self):
        obj = driver(self.root)
        path = active(obj)
        journal = path.with_name(wal.FILENAME)
        saved = journal.read_bytes()
        obj.allow_driver_state_wal_v1 = False
        journal.unlink()
        with self.assertRaises(wal.JournalInvalid):
            obj._read_driver_state()
        journal.write_bytes(b"{broken")
        with self.assertRaises(wal.JournalInvalid):
            obj._read_driver_state()
        journal.write_bytes(saved)
        path.unlink()
        with self.assertRaises(wal.JournalInvalid):
            obj._read_driver_state()

    def test_default_off_resume_full_barrier_and_cold_reader(self):
        obj = driver(self.root)
        path = active(obj)
        restarted = driver(self.root, enabled=False)
        restored = restarted._read_driver_state()
        self.assertEqual(restarted._driver_state_wal_replay_status, "replayed")
        self.assertEqual(restored["command_history"], obj._command_history)
        spec = SimpleNamespace(state_dir=self.root)
        with self.assertRaisesRegex(AgentError, "consolidated"):
            native_session.validate_cold_start_checkpoint_for_pipe(spec, obj.pipe_name)
        restarted._command_history = restored["command_history"]
        restarted._persist_driver_state(persistence_reason="same_pid_resume_barrier")
        self.assertIsNone(restarted._driver_state_error)
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
        self.assertFalse(path.with_name(wal.FILENAME).exists())

    def test_activation_crash_empty_header_requires_closed_recovery(self):
        obj = driver(self.root)
        obj._persist_driver_state()
        path = obj._native_driver_state_path()
        def interrupted(target, data, **kw):
            if target == path:
                raise OSError("crash before sealed base replace")
            write_bytes_atomic(target, data, **kw)
        with patch.object(nd, "write_bytes_atomic", side_effect=interrupted):
            record_day(obj)
        fresh = driver(self.root, enabled=False)
        with self.assertRaises(wal.JournalInvalid):
            fresh._read_driver_state()
        with self.assertRaises(wal.JournalInvalid):
            wal.recover_aborted_activation(path, owner_closed=False)
        self.assertEqual(wal.recover_aborted_activation(path, owner_closed=True),
                         "aborted_no_committed_rows")
        self.assertEqual(fresh._read_driver_state()["command_history"], [])

    def test_full_barrier_crash_points_are_not_stale_base_fallback(self):
        for stop in ("before_base", "after_base_before_cleanup"):
            with self.subTest(stop=stop):
                obj = driver(self.root / stop)
                path = active(obj)
                journal_path = path.with_name(wal.FILENAME)
                if stop == "before_base":
                    def fail_base(target, data, **kw):
                        if target == path:
                            raise OSError("crash before full base replace")
                        write_bytes_atomic(target, data, **kw)
                    with patch.object(nd, "write_bytes_atomic", side_effect=fail_base):
                        obj._persist_driver_state()
                    self.assertEqual(wal.load_pair(path)[1], "replayed")
                else:
                    unlink = Path.unlink
                    def fail_cleanup(target, *a, **kw):
                        if target == journal_path:
                            raise OSError("crash before journal cleanup")
                        return unlink(target, *a, **kw)
                    with patch.object(Path, "unlink", fail_cleanup):
                        obj._persist_driver_state()
                    self.assertEqual(wal.load_pair(path)[1], "already_consolidated")
                    self.assertEqual(obj._driver_state_wal_document,
                                     json.loads(journal_path.read_bytes()))
                    # Same process, then a new day: the prior completed marker
                    # is cleaned before any new transition, not a permanent RED.
                    record_day(obj, 2424)
                    self.assertIsNone(obj._driver_state_error)
                    self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
                    self.assertFalse(journal_path.exists())
                    continue
                with self.assertRaises(wal.JournalInvalid):
                    wal.consolidate_closed_pair(path, owner_closed=False, write_atomic=write_bytes_atomic)
                wal.consolidate_closed_pair(path, owner_closed=True, write_atomic=write_bytes_atomic)
                self.assertEqual(json.loads(path.read_bytes())["command_history"], obj._command_history)
                self.assertFalse(journal_path.exists())

    def test_closed_materialize_requires_exact_staged_unknown_claims(self):
        obj = driver(self.root / "source")
        path = active(obj)
        claim_dir = path.parent / "ingame-decision-item-actions"
        claim_dir.mkdir()
        identity = dict(game_pid=12345, actor_id=7, episode_run_id="native-7-wal-test",
                        decision_key="fixture_decision", action="confirm")
        claim = claim_dir / "once.claim.json"
        claim.write_text(json.dumps(dict(action_identity=identity, status="claimed_result_unknown_no_retry")),
                         encoding="utf-8")
        output = self.root / "materialized"
        target_dir = output / "native-session"
        target_dir.mkdir(parents=True)
        args = dict(owner_closed=True, expected_base_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    expected_journal_sha256=hashlib.sha256(path.with_name(wal.FILENAME).read_bytes()).hexdigest())
        with self.assertRaisesRegex(wal.JournalInvalid, "companions differ"):
            wal.materialize_closed_directory(obj.state_dir, output, **args)
        (target_dir / claim_dir.name).mkdir()
        target_claim = target_dir / claim_dir.name / claim.name
        target_claim.write_bytes(b"corrupt")
        with self.assertRaises(wal.JournalInvalid):
            wal.materialize_closed_directory(obj.state_dir, output, **args)
        self.assertFalse((target_dir / "driver-state.json").exists())
        target_claim.write_bytes(claim.read_bytes())
        receipt = wal.materialize_closed_directory(obj.state_dir, output, **args)
        self.assertEqual(receipt["native_session_companions"]["files"], 1)
        self.assertEqual(target_claim.read_bytes(), claim.read_bytes())
        # This is the existing once consumer, not a WAL replacement/retry API.
        with self.assertRaises(ValueError):
            reject_unresolved_claims(target_claim.parent, identity)
        with self.assertRaises(wal.JournalInvalid):
            wal.materialize_closed_directory(obj.state_dir, output, **args)

    def test_save_and_close_are_full_barriers(self):
        obj = driver(self.root)
        path = active(obj)
        checkpoint = dict(name=native_session.NATIVE_SESSION_CHECKPOINT_FILENAME,
                          size=4, sha256=hashlib.sha256(b"save").hexdigest(), date_raw=2424,
                          history_index=len(obj._command_history) + 1,
                          episode_character_id=7, episode_run_id=obj._episode_run_id,
                          succession_lifecycle=obj._succession_lifecycle)
        obj._last_checkpoint = checkpoint
        receipt = obj._record_command("save-checkpoint", ok=True, result={"checkpoint": checkpoint})
        self.assertEqual(receipt["status"], "replaced")
        self.assertTrue(receipt["save_binding_verified"])
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
        profile = self.root / "profile"
        (profile / "save games").mkdir(parents=True)
        (profile / "save games" / checkpoint["name"]).write_bytes(b"save")
        anchor = native_session.validate_cold_start_checkpoint_for_pipe(
            SimpleNamespace(state_dir=self.root, profile_dir=profile), obj.pipe_name)
        self.assertEqual(anchor["sha256"], checkpoint["sha256"])
        record_day(obj, 2424)
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 3)
        closed = []
        obj.endpoint = SimpleNamespace(close=lambda: closed.append(True))
        # M7 provider cleanup is separately qualified; preserve it unchanged.
        with patch.object(obj, "_invalidate_player_heir_provider_v1"), patch(
                "xar_autoplayer.bridge.normal_exit_pending_observer_v1.dispose_normal_exit_observer_v1"):
            obj.close()
        self.assertEqual(closed, [True])
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 2)
        self.assertFalse(path.with_name(wal.FILENAME).exists())

    def test_foreign_or_lost_pair_never_overwritten_by_barrier(self):
        obj = driver(self.root)
        path = active(obj)
        before = path.read_bytes()
        path.with_name(wal.FILENAME).write_bytes(b"foreign unknown pair")
        obj._persist_driver_state()
        self.assertIsNotNone(obj._driver_state_error)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.with_name(wal.FILENAME).read_bytes(), b"foreign unknown pair")
        path.with_name(wal.FILENAME).unlink()
        obj._persist_driver_state()
        self.assertIsNotNone(obj._driver_state_error)
        self.assertEqual(path.read_bytes(), before)

    def test_canonical_invalid_journal_never_becomes_fresh_state(self):
        obj = driver(self.root)
        path = active(obj)
        # Valid hash-chain, invalid canonical lifecycle. Preserve raw failure;
        # the canonical consumer's ValueError must not take legacy fallback.
        base = json.loads(path.read_bytes())
        base["sealed_full_state"]["succession_lifecycle"] = None
        base_bytes = json.dumps(base).encode()
        document = wal.new_journal(base_bytes, base)
        rows = copy.deepcopy(obj._command_history)
        fields = obj._driver_state_wal_scalar_fields_locked_v1()
        fields["succession_lifecycle"] = None
        document = wal.append_delta(document, rows, fields)
        write_bytes_atomic(path, base_bytes)
        wal.publish_journal(path.with_name(wal.FILENAME), document, write_bytes_atomic)
        with self.assertRaisesRegex(wal.JournalInvalid, "canonical validation"):
            obj._read_driver_state()
        document["entries"][0]["state_fields"]["campaign_goal"] = float("nan")
        # Preserve valid structure/hex but let allow_nan=False checksum encoding
        # raise plain ValueError before the loader has assigned replay_status.
        path.with_name(wal.FILENAME).write_bytes(json.dumps(document).encode())
        with self.assertRaisesRegex(wal.JournalInvalid, "journal validation failed"):
            obj._read_driver_state()

    def test_cross_pid_and_invalid_pair_are_terminal_adoption_refusals(self):
        obj = driver(self.root)
        path = active(obj)
        fresh = driver(self.root, enabled=False)
        fresh._session_bridge_pid = None
        with patch.object(fresh, "_invalidate_player_heir_provider_v1"):
            with self.assertRaises(nd._NativeBridgeAdoptionRefusedError) as caught:
                fresh._adopt_bridge_session(54321)
            self.assertEqual(caught.exception.reason, "active_driver_journal_requires_consolidation")
            path.with_name(wal.FILENAME).write_bytes(b"{broken")
            with self.assertRaises(nd._NativeBridgeAdoptionRefusedError) as caught:
                fresh._adopt_bridge_session(12345)
            self.assertEqual(caught.exception.reason, "invalid_driver_journal")
        self.assertIsNone(fresh._session_bridge_pid)

    def test_delta_capacity_uses_existing_full_barrier(self):
        obj = driver(self.root)
        path = active(obj)
        with patch.object(wal, "MAX_DELTA_BYTES", 1):
            record_day(obj, 2424)
        self.assertIsNone(obj._driver_state_error)
        self.assertEqual(json.loads(path.read_bytes())["command_history"], obj._command_history)
        self.assertFalse(path.with_name(wal.FILENAME).exists())

    def test_existing_prefix_edit_invalidation_forces_full_barrier(self):
        obj = driver(self.root)
        obj._record_command("query-prefix", ok=True, result={"old_body": "full"})
        path = active(obj)
        # Existing marriage/market/combat producers invalidate this same cache
        # when replacing a previously persisted body. No new scan is needed.
        obj._command_history[0]["result"] = {"old_body": "existing_summary"}
        obj._driver_state_history_json.invalidate()
        record_day(obj, 2424)
        self.assertEqual(json.loads(path.read_bytes())["command_history"], obj._command_history)
        self.assertFalse(path.with_name(wal.FILENAME).exists())


if __name__ == "__main__":
    unittest.main()
