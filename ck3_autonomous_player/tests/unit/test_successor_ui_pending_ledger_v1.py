"""Synthetic files/endpoints; actual full verifier, Service, owner and ledger.

No Native/Game/SDK/Host operations or real inheritance credit are exercised.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from test_verified_successor_ui_service_v1 import SourceDriver, service, EventHarness, old, owner
from xar_autoplayer import successor_ui_pending_ledger_v1 as journal
from xar_autoplayer.errors import AgentError
from xar_autoplayer.successor_ui_owner_continuation_v1 import continue_verified_successor_ui_v1 as finish
from xar_autoplayer.bridge.driver import BridgeUnavailableError

MACHINE = "synthetic-m7-software-only"
EPOCH = "e" * 64


def identity(driver):
    return {"pid": driver.frame["diagnostics"]["bridge_pid"],
            "creation_date": "synthetic-original-birth", "executable": "synthetic/ck3.exe"}


def store(path, driver, **change):
    args = dict(machine_id=MACHINE, source_epoch=EPOCH, game_identity=identity(driver),
                verify_transition=owner._verify_natural_succession_transition,
                close_validator=owner._ordinary_succession_close_issue,
                timeline_classifier=owner._ordinary_succession_timeline_state)
    args.update(change)
    return journal.SuccessorUIPendingLedger(path, **args)


def verification(driver):
    proof = driver.proof
    result = {"step": "continue-as-reconciled-successor", "accepted": True, "status": "continued",
        "source": "native-played-character-transition", "lifecycle_intent": "natural_succession",
        "succession_lifecycle": proof["succession_lifecycle"], "continue_as_heir_after_death": True,
        "heir_gameplay_actions": 0, "ck3_command_submitted": False, "process_restarted": False,
        **{k: proof[k] for k in ("predecessor_character_id", "successor_character_id",
            "source_episode_run_id", "episode_run_id", "reconciliation")}}
    return {"result": deepcopy(result), "snapshot": deepcopy(driver.frame),
        "binding": deepcopy(proof["successor_episode_binding"]), "before": deepcopy(proof["predecessor_binding"]),
        "succession_lifecycle": deepcopy(proof["succession_lifecycle"])}


def retain(path, driver):
    value = store(path, driver)
    evidence = verification(driver)
    value.begin_transition(evidence["before"], {"selected_step": "continue-as-reconciled-successor",
        **{key: evidence["before"][key] for key in ("snapshot_id", "revision")}})
    value.retain(driver.proof, driver.frame, verification=evidence)
    return value


def run_ui(driver, ledger, transition=None):
    transition = driver.proof if transition is None else transition
    driver._successor_ui_pending_ledger_v1 = ledger
    return finish(service(driver), transition=transition, snapshot=deepcopy(driver.frame), attempt={},
        classify_timeline=owner._ordinary_succession_timeline_state,
        close_issue=owner._ordinary_succession_close_issue, capture_failure=lambda **_: None,
        previous_observation=transition.get("successor_ui_observation"), durability=ledger)


class DurableHarness(EventHarness):
    """The old fake omits generic callbacks; supply canonical Continue's cue."""
    def make_service(self, driver):
        result = super().make_service(driver)
        previous = result.auto_turn
        observe = result.observe_verified_successor_ui_v1
        def observe_registered(**arguments):
            # The older endpoint fixture uses a separate SimpleNamespace for
            # its read transport. Propagate the actual owner ledger object,
            # never a synthetic binding or a replacement source/birth pin.
            observe.__self__.driver._successor_ui_pending_ledger_v1 = getattr(
                driver, "_successor_ui_pending_ledger_v1", None)
            return observe(**arguments)
        result.observe_verified_successor_ui_v1 = observe_registered
        def auto_turn(*, before_submit=None):
            if (before_submit is not None and self.actions
                    and self.actions[0] == "continue_natural_successor"):
                current = self.snapshot()
                step = "continue-as-reconciled-successor"
                intercepted = before_submit({"plan": {"selected_step": step}, "selected_step": step,
                    "snapshot_id": current["snapshot_id"], "revision": current["revision"]})
                if intercepted is not None:
                    return {"status": "intercepted", "selected_step": step, "interception": intercepted}
            return previous(before_submit=before_submit)
        result.auto_turn = auto_turn
        return result


class PendingUIJournalTests(unittest.TestCase):
    def test_real_service_retains_event_cold_loads_then_closes_once_and_unblocks_save(self):
        with tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
            path = Path(temp); driver = SourceDriver()
            self.assertFalse(journal.requires_owner_binding_v1(path))
            ledger = retain(path, driver)
            run_ui(driver, ledger)
            self.assertTrue(journal.requires_owner_binding_v1(path))
            with self.assertRaisesRegex(ValueError, "no ordinary SAVE"):
                ledger.require_resolved_before_save()
            original = deepcopy(driver.proof["successor_episode_binding"])
            driver.event_finished()
            cold = store(path, driver)
            loaded = cold.load(driver.frame)
            self.assertEqual(loaded["successor_episode_binding"], original)
            self.assertEqual(run_ui(driver, cold, loaded)[1:], (False, True, False))
            cold.require_resolved_before_save()
            self.assertFalse(journal.requires_owner_binding_v1(path))
            self.assertEqual(driver.closes, 1)
            self.assertIsNone(store(path, driver).load(driver.frame))
            intent = json.loads(next(path.glob("successor-ui-close-*.json")).read_text(encoding="utf-8"))
            self.assertEqual(intent["status"], "verified")
            self.assertFalse(intent["action_replay_authorized"])

    def test_new_connection_requires_exact_owner_authorization_without_rewriting_old_frame(self):
        with tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
            path = Path(temp); driver = SourceDriver(); ledger = retain(path, driver)
            run_ui(driver, ledger)
            old = deepcopy(driver.proof["successor_ui_observation"])
            driver.frame["diagnostics"]["connection_generation"] += 1
            driver.frame["revision"] = 1  # Explicit SDK public projection reset.
            driver.frame["native_revision"] += 1
            driver.frame["snapshot_id"] = "synthetic:new-sdk"
            driver.context["snapshot_revision"] = driver.frame["native_revision"]
            cold = store(path, driver)
            with self.assertRaisesRegex(ValueError, "explicit owner rebind"):
                cold.load(driver.frame)
            value, pin = journal._read(path / journal.FILE)
            authorization = {"schema": journal.AUTH, "ledger_sha256": pin, "machine_id": MACHINE,
                "source_epoch": EPOCH, "game_identity": identity(driver),
                "old_connection_generation": value["retained_frame"]["connection_generation"],
                "resumed_frame": journal.frame(driver.frame)}
            for key in ("ledger_sha256", "source_epoch"):
                wrong = {**authorization, key: "0" * 64}
                with self.subTest(key=key), self.assertRaises(ValueError):
                    cold.load(driver.frame, reconnect_authorization=wrong)
            loaded = cold.load(driver.frame, reconnect_authorization=authorization)
            self.assertEqual(loaded["successor_ui_observation"], old)
            driver._successor_ui_pending_ledger_v1 = cold
            s = service(driver)
            query = s.query_current_timeline_blocker_context_v1(expected_revision=driver.frame["revision"])
            genuine = loaded["_successor_ui_cold_binding_v1"]
            for key in ("source_epoch", "game_identity"):
                forged = deepcopy(genuine)
                forged[key] = ("0" * 64 if key == "source_epoch"
                               else {**forged[key], "creation_date": "synthetic-forged-birth"})
                forged["binding_sha256"] = journal.digest({k: v for k, v in forged.items() if k != "binding_sha256"})
                with self.subTest(forged=key), self.assertRaisesRegex(ValueError, "not issued"):
                    s.observe_verified_successor_ui_v1(transition=loaded, snapshot=driver.frame,
                        timeline_query=query, previous_observation=old, cold_resume_binding=forged)
            del driver._successor_ui_pending_ledger_v1
            with self.assertRaisesRegex(ValueError, "registered ledger"):
                s.observe_verified_successor_ui_v1(transition=loaded, snapshot=driver.frame,
                    timeline_query=query, previous_observation=old, cold_resume_binding=genuine)
            self.assertEqual(run_ui(driver, cold, loaded)[1:], (True, False, True))
            self.assertEqual(loaded["successor_episode_binding"], driver.proof["successor_episode_binding"])
            driver.event_finished()
            final = store(path, driver)
            self.assertEqual(run_ui(driver, final, final.load(driver.frame))[1:], (False, True, False))
            self.assertEqual(driver.closes, 1)

    def test_machine_source_birth_goal_actor_and_original_full_proof_fail_before_reads(self):
        for kind in ("machine", "source", "birth", "goal", "actor", "episode", "title", "persist"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
                path = Path(temp); driver = SourceDriver(); retain(path, driver)
                changes = {}
                if kind == "machine": changes["machine_id"] = "synthetic-foreign"
                if kind == "source": changes["source_epoch"] = "f" * 64
                if kind == "birth": changes["game_identity"] = {**identity(driver), "creation_date": "different"}
                if kind == "goal": driver.frame["campaign_goal"]["campaign_id"] = "foreign-campaign"
                if kind == "actor": driver.frame["played_character"]["character_id"] = 77
                if kind == "episode": driver.frame["episode_run_id"] = "foreign-episode"
                if kind in ("title", "persist"):
                    value, _ = journal._read(path / journal.FILE)
                    if kind == "title":
                        value["verification"]["result"]["reconciliation"]["title_distribution_match"] = False
                    else:
                        value["verification"]["result"]["driver_state_persistence_diagnostic"] = {"status": "failed"}
                    value["verification_sha256"] = journal.digest(value["verification"])
                    (path / journal.FILE).write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises((ValueError, AgentError)):
                    store(path, driver, **changes).load(driver.frame)
                self.assertEqual((driver.reads, driver.closes), (0, 0))

    def test_unknown_ack_exception_and_result_write_failure_remain_once_locked(self):
        for failure in ("ack", "exception", "result-write"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
                path = Path(temp); driver = SourceDriver(); ledger = retain(path, driver)
                run_ui(driver, ledger); driver.event_finished()
                loaded = ledger.load(driver.frame)
                if failure == "ack": driver.ack_only = True
                def unknown(**_):
                    driver.closes += 1
                    raise BridgeUnavailableError("synthetic command result unknown")
                target = patch.object(driver, "continue_death_succession_modal_private_v1", side_effect=unknown)
                result_failure = patch.object(ledger, "retain_close_result", side_effect=OSError("synthetic result write"))
                with target if failure == "exception" else result_failure if failure == "result-write" else patch.dict({}, {}):
                    with self.assertRaises((AgentError, OSError)):
                        run_ui(driver, ledger, loaded)
                count = driver.reads
                with self.assertRaisesRegex(ValueError, "intent already exists"):
                    store(path, driver).load(driver.frame)
                self.assertEqual((driver.closes, driver.reads), (1, count))
                intent = json.loads(next(path.glob("successor-ui-close-*.json")).read_text(encoding="utf-8"))
                self.assertEqual(intent["status"], "UNKNOWN")

    def test_intent_fsync_failure_and_exclusive_creation_never_submit(self):
        with tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
            path = Path(temp); driver = SourceDriver(); ledger = store(path, driver)
            evidence = verification(driver)
            candidate = {"selected_step": "continue-as-reconciled-successor",
                **{key: evidence["before"][key] for key in ("snapshot_id", "revision")}}
            ledger.begin_transition(evidence["before"], candidate)
            with self.assertRaises(OSError), patch.object(journal, "write_json_atomic", side_effect=OSError("synthetic retain failure")):
                ledger.retain(driver.proof, driver.frame, verification=evidence)
            self.assertTrue(journal.requires_owner_binding_v1(path))
            with self.assertRaisesRegex(ValueError, "unverified"):
                store(path, driver).load(driver.frame)
            self.assertEqual((driver.reads, driver.closes), (0, 0))
        with tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
            path = Path(temp); driver = SourceDriver(); ledger = retain(path, driver)
            run_ui(driver, ledger); driver.event_finished(); loaded = ledger.load(driver.frame)
            with patch.object(journal.os, "fsync", side_effect=[None, OSError("synthetic intent barrier")]):
                with self.assertRaises(OSError):
                    run_ui(driver, ledger, loaded)
            self.assertEqual(driver.closes, 0)
            with self.assertRaisesRegex(ValueError, "intent already exists"):
                store(path, driver).load(driver.frame)
            with self.assertRaises(FileExistsError):
                ledger.begin_close(loaded, driver.frame, {})
            self.assertEqual(driver.closes, 0)

    def test_materialize_checkpoint_gate_runs_before_snapshot_or_submit(self):
        with tempfile.TemporaryDirectory(prefix="m7-ui-") as temp:
            path = Path(temp); driver = SourceDriver(); ledger = retain(path, driver)
            driver._successor_ui_pending_ledger_v1 = ledger
            with self.assertRaisesRegex(ValueError, "no ordinary SAVE"):
                owner._materialize_checkpoint(service(driver), driver, path,
                    session_done=threading.Event(), session_state={}, timeout_seconds=.01, poll_interval_seconds=.001)
            self.assertEqual((driver.reads, driver.closes), (0, 0))

    def test_whole_owner_retains_pending_and_missing_binding_blocks_before_session_start(self):
        base = old.NativeAutoRunTests(); base.setUp()
        original = owner.native_auto_run
        try:
            binding = {"machine_id": MACHINE, "source_epoch": journal.owner_source_epoch_v1()}
            rebound = [False]
            def invoke(*args, **kwargs):
                return original(*args, successor_ui_durability_binding=binding, **kwargs)
            def game(snapshot, _):
                actual = {"pid": snapshot["diagnostics"]["bridge_pid"], "creation_date": "synthetic-owner-birth",
                          "executable": "synthetic/owner-ck3.exe"}
                if rebound[0]:
                    # Synthetic owner-supplied exact fresh rebind authorization;
                    # the production ledger does not manufacture this input.
                    value, pin = journal._read(base.spec.state_dir / journal.FILE)
                    binding["reconnect_authorization"] = {"schema": journal.AUTH, "ledger_sha256": pin,
                        "machine_id": MACHINE, "source_epoch": binding["source_epoch"], "game_identity": actual,
                        "old_connection_generation": value["retained_frame"]["connection_generation"],
                        "resumed_frame": journal.frame(snapshot)}
                return actual
            with patch.object(old, "_NativeAutoRunHarness", DurableHarness), \
                 patch.object(owner, "native_auto_run", side_effect=invoke), \
                 patch.object(journal, "observe_game_identity_v1", side_effect=game):
                report, harness = base._run(["natural_terminal_advance", "continue_natural_successor", "event"],
                    checkpoint_every_eligible_advances=1,
                    succession_lifecycle="ordinary_campaign_succession", ordinary_campaign_no_pact=True)
            self.assertEqual(report["status"], "turn_limit_player_decision_pending", report.get("error"))
            self.assertTrue(journal.requires_owner_binding_v1(base.spec.state_dir))
            self.assertNotIn("save_checkpoint", harness.events)
            with patch.object(owner, "native_session", side_effect=AssertionError("must not start")):
                with self.assertRaisesRegex(AgentError, "before any AUTO/SAVE"):
                    base._run(["advance"], succession_lifecycle="ordinary_campaign_succession",
                              ordinary_campaign_no_pact=True)
            retained, _ = journal._read(base.spec.state_dir / journal.FILE)
            saved_frame = retained["retained_frame"]
            class ResumedHarness(DurableHarness):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.bridge_pid = saved_frame["bridge_pid"]
                    self.connection_generation = saved_frame["connection_generation"] + 1
                    self.native_revision, self.public_revision = saved_frame["native_revision"], 1
                    self.date_raw = saved_frame["date_raw"]
                    self.heartbeat_date_raw = self.date_raw
                    self.played_character_id = self.episode_character_id = saved_frame["actor_character_id"]
                    self.episode_run_id = saved_frame["episode_run_id"]
                    self.ui_goal = deepcopy(retained["campaign_goal"])
                    self.active_event_id = None
                    self.succession_modal_open = True
            rebound[0] = True
            with patch.object(old, "_NativeAutoRunHarness", ResumedHarness), \
                 patch.object(owner, "native_auto_run", side_effect=invoke), \
                 patch.object(journal, "observe_game_identity_v1", side_effect=game):
                resumed, fresh = base._run(["advance"], initial_unready_snapshot=False,
                    succession_lifecycle="ordinary_campaign_succession", ordinary_campaign_no_pact=True)
            self.assertTrue(resumed["ok"], resumed.get("error"))
            self.assertEqual(fresh.events.count("close_successor_timeline"), 1)
            self.assertNotIn("auto_turn:continue_natural_successor", fresh.events)
            self.assertLess(fresh.events.index("close_successor_timeline"), fresh.events.index("auto_turn:advance"))
            self.assertIsNone(resumed["pending_successor_ui"])
            self.assertEqual(resumed["natural_succession_transitions"], [])  # No new succession credit.
        finally:
            base.tearDown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
