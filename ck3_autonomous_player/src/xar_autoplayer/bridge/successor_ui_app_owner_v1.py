"""App-owned, same-Game natural succession; never replay an uncertain action.

The registered MCP and its Service share this object. Queue JSON is evidence,
not authority. The existing full handoff/Close/timeline validators stay intact.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import threading

from .. import successor_ui_pending_ledger_v1 as journal
from ..errors import AgentError
from ..strategy import continue_ordinary_campaign_goal_v1, normalize_ordinary_campaign_goal_v1
from ..successor_ui_owner_continuation_v1 import continue_verified_successor_ui_v1

STEP = "continue-as-reconciled-successor"


def _machine_id():
    # Exact source projection of tools/ck3_live_run_id.py travels inside the
    # Python package. Installed/frozen SDKs do not assume a ../tools directory.
    from ..ck3_live_run_identity_v1 import current_machine_id
    return current_machine_id()


def _game_identity(snapshot):
    from ..runtime import _process_identity
    pid = snapshot.get("diagnostics", {}).get("bridge_pid")
    actual = _process_identity(pid) if type(pid) is int and pid > 0 else None
    if (not isinstance(actual, dict) or actual.get("pid") != pid
            or not actual.get("creation_date") or not actual.get("executable")):
        raise ValueError("successor App lacks the actual native Game birth/image")
    return {"pid": pid, "creation_date": actual["creation_date"],
            "executable": os.path.normcase(os.path.abspath(actual["executable"]))}


def episode_binding(snapshot, capabilities):
    diagnostics = capabilities.get("diagnostics", {})
    control = capabilities.get("native_session_control", {})
    played = snapshot.get("played_character", {})
    value = {key: snapshot.get(key) for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
        "episode_character_id", "one_life_terminal", "one_life_terminal_reason")}
    value.update(played_character_id=played.get("character_id"), played_character_alive=played.get("alive"),
                 episode_binding_state=control.get("episode_binding_state"),
                 driver_state_restore_kind=control.get("driver_state_restore_kind"))
    for key in ("bridge_pid", "connection_generation"):
        value[key] = diagnostics.get(key)
        if (type(value[key]) is not int or value[key] <= 0
                or snapshot.get("diagnostics", {}).get(key) != value[key]):
            raise ValueError("successor App capabilities differ from its actual snapshot")
    return value


class SuccessorUIAppOwner:
    def __init__(self, service, *, before_submit=None):
        from .. import native_auto_run as validators
        self.service, self.driver = service, service.driver
        self.before_submit = before_submit
        self.root = Path(self.driver.state_dir)
        self.machine = _machine_id()
        self.epoch = journal.owner_source_epoch_v1()
        self.validators = validators
        self.ledger = None
        self.ticket = None
        self.transition = None
        self.lock = threading.RLock()
        self._auto_scope = None
        self._auto_thread = None
        self._continue_dispatch_permit = None
        self.executing_close = False

    def snapshot(self):
        return self.service.snapshot(include_native_command_history=False)

    def ensure(self, snapshot):
        if getattr(self, "_completed_retirement_error_v1", None):
            raise ValueError("completed successor retirement remains unverified: " + self._completed_retirement_error_v1)
        game = _game_identity(snapshot)
        path = self.root / journal.FILE
        if path.exists():
            previous, _ = journal._read(path)
            if (previous.get("status") == "resolved" and (previous.get("game_identity") != game
                    or previous.get("source_epoch") != self.epoch)):
                from .. import successor_ui_checkpoint_lineage_v1 as lineage
                anchor, _ = journal._read(self.root / lineage.COMPLETION_FILE)
                cold = lineage.observe_native_cold_checkpoint_v1(self, snapshot=snapshot,
                    expected_executable=game["executable"])
                plan = lineage.plan_resolved_checkpoint_retirement_v1(self, anchor=anchor, cold=cold)
                self._completed_retirement_v1 = lineage.retire_completed_checkpoint_v1(self, plan)
                self.ledger, self.transition = None, None
        if self.ledger is None:
            self.ledger = journal.SuccessorUIPendingLedger(self.root, machine_id=self.machine,
                source_epoch=self.epoch, game_identity=game,
                verify_transition=self.validators._verify_natural_succession_transition,
                close_validator=self.validators._ordinary_succession_close_issue,
                timeline_classifier=self.validators._ordinary_succession_timeline_state)
            self.driver._successor_ui_pending_ledger_v1 = self.ledger
        elif game != self.ledger.game:
            raise ValueError("successor App Game birth/image changed; no same-Game migration")
        return self.ledger

    def pending(self):
        return journal.requires_owner_binding_v1(self.root)

    def before_continue(self, planned):
        if planned.get("plan", {}).get("selected_step") != STEP:
            return
        if self._auto_scope is None or self._auto_thread != threading.get_ident():
            raise ValueError("natural Continue requires the original active App AUTO scope")
        before = self.snapshot()
        source = self.service._observed_planning_source_frame(before)
        if (source.get("status") != "complete" or source != planned.get("planning_source_frame")
                or before.get("snapshot_id") != planned.get("snapshot_id")
                or before.get("revision") != planned.get("revision")
                or before.get("paused") is not True or before.get("map_ready") is not True):
            raise ValueError("successor App pre-Continue frame differs from the actual plan")
        lifecycle = before.get("succession_lifecycle")
        if lifecycle != self.driver._succession_lifecycle:
            raise ValueError("successor App lifecycle differs from its registered driver")
        goal = normalize_ordinary_campaign_goal_v1(before.get("campaign_goal"))
        binding = episode_binding(before, self.service.capabilities())
        if goal["current_character_id"] != binding["episode_character_id"]:
            raise ValueError("successor App lost its predecessor campaign goal")
        ledger = self.ensure(before)
        ledger.begin_transition(binding, {"selected_step": STEP,
            "snapshot_id": before["snapshot_id"], "revision": before["revision"]})
        # A durable intent exists even if execution/revision/readback later fails.
        self.ticket = {"before": binding, "goal": goal, "succession_lifecycle": deepcopy(lifecycle)}
        self._continue_dispatch_permit = self._auto_scope

    def after_continue(self, planned, outcome):
        if planned.get("plan", {}).get("selected_step") != STEP or self.ticket is None:
            return outcome
        original = deepcopy(outcome)
        try:
            result = outcome.get("result")
            persistence = result.get("driver_state_persistence_diagnostic") if isinstance(result, dict) else None
            if isinstance(persistence, dict) and persistence.get("status") == "failed":
                raise ValueError("original Continue persistence failed; original result retained")
            after = self.snapshot()
            self.ensure(after)
            binding = episode_binding(after, self.service.capabilities())
            evidence = {"result": deepcopy(result), "snapshot": deepcopy(after), "binding": binding,
                        "before": deepcopy(self.ticket["before"]),
                        "succession_lifecycle": deepcopy(self.ticket["succession_lifecycle"])}
            transition = self.validators._verify_natural_succession_transition(result,
                snapshot=after, binding=binding, before=evidence["before"],
                succession_lifecycle=evidence["succession_lifecycle"])
            expected = continue_ordinary_campaign_goal_v1(self.ticket["goal"], result["reconciliation"])
            if normalize_ordinary_campaign_goal_v1(after.get("campaign_goal")) != expected:
                raise ValueError("successor App goal differs from the original exact continuation")
            self.ledger.retain(transition, after, verification=evidence)
            self.transition = transition
            diagnostic = {"status": "pending", "replay_authorized": False,
                          "successor_character_id": transition["successor_character_id"],
                          "episode_run_id": transition["episode_run_id"]}
        except Exception as error:
            # Never turn an already applied Continue into an exception without
            # its original receipt, nor clear its durable once marker.
            diagnostic = {"status": "handoff_unverified", "replay_authorized": False,
                          "error_type": type(error).__name__, "error": str(error)}
        self.ticket = None
        return {**original, "successor_ui_obligation_v1": diagnostic}

    def _load(self, snapshot):
        ledger = self.ensure(snapshot)
        authorization = None
        if ledger.path.exists():
            value, pin = journal._read(ledger.path)
            if value.get("status") == "pending":
                # Only this actual owner can authorize a new SDK connection.
                # The source epoch, real OS birth/image and full original proof
                # are rechecked by load; no queue/client JSON grants authority.
                authorization = {"schema": journal.AUTH, "ledger_sha256": pin,
                    "machine_id": self.machine, "source_epoch": self.epoch,
                    "game_identity": ledger.game,
                    "old_connection_generation": value["retained_frame"]["connection_generation"],
                    "resumed_frame": journal.frame(snapshot)}
        self.transition = ledger.load(snapshot, reconnect_authorization=authorization)
        return self.transition

    def resume(self, *, expected_revision=None, allow_close=True):
        with self.lock:
            current = self.snapshot()
            if expected_revision is not None and current.get("revision") != expected_revision:
                raise ValueError("successor UI resume revision changed")
            if not self.pending():
                return {"status": "clear", "pending": False, "snapshot": current, "transition": None}
            transition = self._load(current)
            cold_binding = deepcopy(self.ledger._issued_cold_binding)
            attempt, failures = {}, []
            def capture_failure(**value):
                error = value.pop("error", None)
                if error is not None:
                    value.update(error_type=type(error).__name__, error=str(error))
                failures.append(value)
            try:
                self.executing_close = True
                current, decision, advanced, pending = continue_verified_successor_ui_v1(
                    self.service, transition=transition, snapshot=current, attempt=attempt,
                    classify_timeline=self.validators._ordinary_succession_timeline_state,
                    close_issue=self.validators._ordinary_succession_close_issue,
                    capture_failure=capture_failure,
                    previous_observation=transition.get("successor_ui_observation"), durability=self.ledger,
                    before_close=self.before_submit, allow_close=allow_close)
            except AgentError as error:
                # An ambiguous read is retried on a later ordinary call, never
                # by restarting the agent or guessing a Close/SAVE permission.
                if attempt.get("stage") != "ordinary_successor_timeline_query":
                    raise
                return {"status": "ui_unresolved", "pending": True, "player_decision_pending": False,
                        "snapshot": current, "transition": deepcopy(transition),
                        "cold_resume_binding": cold_binding,
                        "diagnostic": {"error": str(error), "failures": failures}, "action_submitted": False}
            finally:
                self.executing_close = False
            status = "deferred_player_decision" if pending else "clear"
            if pending and transition.get("timeline_blocker_continuation", {}).get("status") == "close_required":
                status = "close_required"
            return {"status": status, "pending": pending,
                    "player_decision_pending": decision, "date_advanced": advanced,
                    "snapshot": current, "transition": deepcopy(transition), "cold_resume_binding": cold_binding}

    def auto_turn(self, *, before_submit=None):
        # MCP HTTP clients may overlap; serialize the whole plan/once/execute.
        with self.lock:
            if self.pending():
                resumed = self.resume()
                if (resumed["status"] == "ui_unresolved" or resumed.get("date_advanced")
                        or resumed["pending"] and not resumed.get("player_decision_pending")):
                    return {"status": "successor_ui_pending" if resumed["pending"] else "successor_ui_resumed",
                            "selected_step": None, "successor_ui_obligation_v1": resumed,
                            "result": resumed.get("transition", {}).get("timeline_blocker_continuation", {}).get("close_result")}
            if self._auto_scope is not None:
                raise ValueError("App AUTO is already active; no nested continuation scope")
            self._auto_scope = object()
            self._auto_thread = threading.get_ident()
            try:
                return self.service.auto_turn(before_submit=before_submit)
            finally:
                # The ticket preserves evidence, never submission authority.
                # Driver exceptions must not leave a reusable public permit.
                self._continue_dispatch_permit = None
                self._auto_scope = None
                self._auto_thread = None

    def require_save(self):
        if self.pending():
            # Do not perform a hidden Close or change a revision-bound SAVE.
            raise ValueError("successor UI obligation remains unresolved; no ordinary SAVE")
        path = self.root / journal.FILE
        if path.exists():
            from ..successor_ui_checkpoint_lineage_v1 import _completion
            record, _ = journal._read(path)
            original = journal.SuccessorUIPendingLedger(self.root, machine_id=self.machine,
                source_epoch=record["source_epoch"], game_identity=record["game_identity"],
                verify_transition=self.validators._verify_natural_succession_transition,
                close_validator=self.validators._ordinary_succession_close_issue,
                timeline_classifier=self.validators._ordinary_succession_timeline_state)
            # In particular a stale UNKNOWN Close cannot gain another SAVE or
            # even the one optional resolved-SAVE observation.
            _completion(original)

    def driver_step(self, step, *, expected_revision):
        with self.lock:
            completed_save_frame = None
            if step == "save-checkpoint":
                self.require_save()
                path = self.root / journal.FILE
                if path.exists():
                    from .native_driver import NativeHeadlessGameplayDriver
                    if isinstance(self.driver, NativeHeadlessGameplayDriver):
                        # One rare resolved SAVE observation, never per AUTO.
                        # Retain this actual pre-frame; do not fabricate it from
                        # the already-applied SAVE's result or replace receipt.
                        completed_save_frame = self.snapshot()
                        self.ensure(completed_save_frame)
            if step == STEP:
                if (self.ticket is None or self._auto_scope is None
                        or self._auto_thread != threading.get_ident()
                        or self._continue_dispatch_permit is not self._auto_scope):
                    raise ValueError("natural Continue has no unconsumed original App AUTO dispatch permit")
                # Consume before entering the original driver, including its
                # throw-before-dispatch and unknown-after-apply outcomes.
                self._continue_dispatch_permit = None
            original = self.driver.execute_step(step, expected_revision=expected_revision)
            if completed_save_frame is not None and self.ledger is not None and self.ledger.path.exists():
                try:
                    from ..successor_ui_checkpoint_lineage_v1 import write_completed_checkpoint_v1
                    diagnostic = write_completed_checkpoint_v1(self, ledger=self.ledger,
                        save_result=original, snapshot=completed_save_frame)
                except Exception as error:
                    # The original SAVE has happened. Preserve its complete
                    # receipt and never retry it because this evidence failed.
                    diagnostic = {"status": "capture_failed", "error_type": type(error).__name__,
                        "error": str(error), "extra_history_free_observations": 1,
                        "action_replay_authorized": False}
                return {**original, "successor_ui_completed_checkpoint_v1": diagnostic}
            return original

    def public_close(self, arguments):
        if not self.pending():
            raise ValueError("successor typed Close requires the App's verified pending transition")
        with self.lock:
            current = self.snapshot()
            if (arguments["expected_revision"] != current.get("revision")
                    or arguments["expected_played_character_id"] != current.get("episode_character_id")
                    or arguments["expected_episode_run_id"] != current.get("episode_run_id")):
                raise ValueError("successor typed Close request differs from its actual successor")
            resumed = self.resume(expected_revision=arguments["expected_revision"])
            transition = resumed.get("transition") or {}
            result = transition.get("timeline_blocker_continuation", {}).get("close_result")
            if result is None:
                raise ValueError("successor UI has no currently legal verified modal Close")
            return result


def install_successor_ui_app_owner_v1(service, *, before_submit=None):
    driver = service.driver
    lifecycle = getattr(driver, "_succession_lifecycle", {})
    if (not isinstance(lifecycle, dict) or lifecycle.get("lifecycle") != "ordinary_campaign_succession"
            or getattr(driver, "allow_private_death_succession_modal_continue", False) is not True):
        # Existing rogue/experimental qualification policy is unchanged.
        if getattr(driver, "state_dir", None) is not None and journal.requires_owner_binding_v1(driver.state_dir):
            raise ValueError("existing successor UI obligation requires its qualified ordinary App owner")
        return None
    if getattr(driver, "state_dir", None) is None:
        raise ValueError("ordinary successor App requires a persistent state directory")
    owner = SuccessorUIAppOwner(service, before_submit=before_submit)
    service._successor_ui_app_owner_v1 = owner
    return owner
