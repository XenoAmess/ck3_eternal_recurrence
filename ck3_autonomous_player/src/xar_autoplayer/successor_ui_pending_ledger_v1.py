"""Caller-owned successor UI obligation, with a create-only Close intent.

This stores evidence, not a Game checkpoint or a new inheritance. Cold SDK
connections require an explicit source-bound rebind; a new Game never qualifies.
File fsync/readback is checked. Directory/power-loss durability is not claimed.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

from .environment import write_json_atomic
from .strategy import normalize_ordinary_campaign_goal_v1

FILE = "successor-ui-pending-v1.json"
SCHEMA = "xar.ck3.successor-ui-pending/v1"
COLD = "xar.ck3.successor-ui-cold-binding/v1"
AUTH = "xar.ck3.successor-ui-connection-rebind/v1"
LIMIT = 262144
FRAME = ("bridge_pid", "connection_generation", "snapshot_id", "revision", "native_revision", "date_raw")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def transition_digest(transition):
    from .bridge.verified_successor_ui_service_v1 import PROOF
    return digest({key: transition.get(key) for key in PROOF})


def owner_source_epoch_v1():
    """Hash only at owner initialization, never on the ordinary-turn path."""
    root = Path(__file__).resolve().parent
    names = ("native_auto_run.py", "successor_ui_pending_ledger_v1.py",
             "successor_ui_owner_continuation_v1.py", "bridge/service.py",
             "bridge/verified_successor_ui_service_v1.py", "bridge/succession_ui_observation_v1.py",
             "bridge/successor_ui_app_owner_v1.py", "bridge/mcp_server.py", "ck3_live_run_identity_v1.py",
             "bridge/native_driver.py", "strategy.py")
    return digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names})


def _read(path):
    if path.stat().st_size > LIMIT:
        raise ValueError("successor UI evidence exceeds its small-ledger contract")
    raw = path.read_bytes()
    if len(raw) > LIMIT:
        raise ValueError("successor UI ledger grew during read")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("successor UI evidence is not an object")
    return value, hashlib.sha256(raw).hexdigest()


def requires_owner_binding_v1(state_dir):
    path = Path(state_dir) / FILE
    if not path.exists():
        return False
    value, _ = _read(path)
    if value.get("schema") != SCHEMA or value.get("status") not in {"handoff_unverified", "pending", "resolved"}:
        raise ValueError("successor UI ledger is malformed; do not bypass it")
    return value["status"] != "resolved"


def observe_game_identity_v1(snapshot, expected_executable):
    """Use the original process reader; no Native/GUI/action or binary hashing."""
    from .runtime import _process_identity
    diagnostics = snapshot.get("diagnostics", {})
    pid = diagnostics.get("bridge_pid")
    identity = _process_identity(pid) if type(pid) is int and pid > 0 else None
    if (not isinstance(identity, Mapping) or identity.get("pid") != pid
            or not isinstance(identity.get("creation_date"), str) or not identity["creation_date"]
            or not isinstance(identity.get("executable"), str)
            or os.path.normcase(os.path.abspath(identity["executable"]))
            != os.path.normcase(os.path.abspath(expected_executable))):
        raise ValueError("successor UI lacks the actual Game birth/image identity")
    return {"pid": pid, "creation_date": identity["creation_date"],
            "executable": os.path.normcase(os.path.abspath(identity["executable"]))}


def frame(snapshot):
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    if (not isinstance(diagnostics, Mapping) or not isinstance(played, Mapping)
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("one_life_terminal_reason") is not None
            or snapshot.get("episode_identity_pending") is not False
            or played.get("alive") is not True
            or snapshot.get("episode_character_id") != played.get("character_id")):
        raise ValueError("successor UI requires the actual stable living successor")
    row = {key: snapshot.get(key) for key in FRAME}
    row.update({key: diagnostics.get(key) for key in FRAME[:2]})
    row.update(actor_character_id=played.get("character_id"), episode_run_id=snapshot.get("episode_run_id"))
    if (not isinstance(row["snapshot_id"], str) or not row["snapshot_id"]
            or not isinstance(row["episode_run_id"], str) or not row["episode_run_id"]
            or any(type(row[key]) is not int or row[key] < 0 for key in (
                "bridge_pid", "connection_generation", "revision", "native_revision", "date_raw", "actor_character_id"))
            or any(row[key] <= 0 for key in ("bridge_pid", "native_revision", "actor_character_id"))):
        raise ValueError("successor UI frame is incomplete")
    return row


def validate_cold_ui_binding_v1(binding, *, transition, previous_observation, snapshot):
    """Validate the explicit new connection without rewriting the old proof/frame."""
    if not isinstance(binding, Mapping) or binding.get("schema") != COLD:
        raise ValueError("successor UI cold binding is missing")
    current = frame(snapshot)
    old, start = binding.get("retained_frame"), binding.get("resumed_frame")
    expected_old = (previous_observation.get("frame") if isinstance(previous_observation, Mapping)
                    else transition.get("successor_episode_binding"))
    if (binding.get("transition_sha256") != transition_digest(transition)
            or binding.get("observation_sha256") != digest(previous_observation)
            or not isinstance(old, Mapping) or not isinstance(start, Mapping)
            or any(old.get(key) != expected_old.get(key) for key in FRAME)
            or binding.get("binding_sha256") != digest({k: v for k, v in binding.items() if k != "binding_sha256"})
            or not isinstance(binding.get("source_epoch"), str) or len(binding["source_epoch"]) != 64
            or binding.get("game_identity", {}).get("pid") != current["bridge_pid"]
            or current["bridge_pid"] != old.get("bridge_pid")
            or current["connection_generation"] != start.get("connection_generation")
            or current["actor_character_id"] != transition["successor_character_id"]
            or current["episode_run_id"] != transition["episode_run_id"]
            or any(type(start.get(key)) is not int or current[key] < start[key]
                   for key in ("revision", "native_revision", "date_raw"))
            or any(type(old.get(key)) is not int or current[key] < old[key]
                   for key in ("native_revision", "date_raw"))):
        raise ValueError("successor UI cold binding differs from retained proof/current frame")
    return current


class SuccessorUIPendingLedger:
    def __init__(self, state_dir, *, machine_id, source_epoch, game_identity, verify_transition,
                 close_validator, timeline_classifier):
        if (not isinstance(machine_id, str) or not machine_id or machine_id == "unknown"
                or not isinstance(source_epoch, str) or len(source_epoch) != 64
                or not isinstance(game_identity, Mapping) or type(game_identity.get("pid")) is not int
                or not game_identity.get("creation_date") or not game_identity.get("executable")):
            raise ValueError("successor UI owner binding is incomplete")
        self.root = Path(state_dir)
        self.path = self.root / FILE
        self.machine_id, self.epoch = machine_id, source_epoch
        self.game = dict(game_identity)
        self.verify = verify_transition
        self.close_validator, self.timeline_classifier = close_validator, timeline_classifier
        self.record = None
        self._issued_cold_binding = None

    def _write(self, value):
        value = {**value, "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
        if len(json.dumps(value).encode()) > LIMIT:
            raise ValueError("successor UI retained evidence exceeds its bound")
        write_json_atomic(self.path, value)
        # Preserve the common atomic writer; require the file barrier/readback
        # before permitting a later command. No directory-fsync claim follows.
        with self.path.open("r+b") as stream:
            os.fsync(stream.fileno())
        actual, _ = _read(self.path)
        if actual != value:
            raise ValueError("successor UI ledger write/readback differs")
        self.record = deepcopy(value)

    def _checked(self):
        value, pin = _read(self.path)
        if (value.get("schema") != SCHEMA or value.get("machine_id") != self.machine_id
                or value.get("source_epoch") != self.epoch or value.get("game_identity") != self.game):
            raise ValueError("successor UI owner/source/Game differs; no automatic migration")
        if value.get("status") == "handoff_unverified":
            raise ValueError("original Continue proof remains unverified; collect its result, never resend")
        if value.get("status") not in {"pending", "resolved"}:
            raise ValueError("successor UI ledger status is malformed")
        evidence = value.get("verification")
        if not isinstance(evidence, dict) or value.get("verification_sha256") != digest(evidence):
            raise ValueError("successor UI lost its original verification inputs")
        persistence = evidence.get("result", {}).get("driver_state_persistence_diagnostic")
        if isinstance(persistence, Mapping) and persistence.get("status") == "failed":
            raise ValueError("original Continue persistence failed; do not reconsume/replay it")
        original = self.verify(evidence["result"], snapshot=evidence["snapshot"], binding=evidence["binding"],
                               before=evidence["before"], succession_lifecycle=evidence["succession_lifecycle"])
        if (transition_digest(original) != value.get("transition_sha256")
                or transition_digest(value.get("transition", {})) != value["transition_sha256"]):
            raise ValueError("successor UI original full verification no longer matches")
        self.record = deepcopy(value)
        return value, pin

    def _intent_path(self):
        return self.root / ("successor-ui-close-" + self.record["transition_sha256"] + ".json")

    def begin_transition(self, before, candidate):
        """A durable marker precedes the original logical Continue, not its proof."""
        if (candidate.get("selected_step") != "continue-as-reconciled-successor"
                or any(candidate.get(key) != before.get(key) for key in ("snapshot_id", "revision"))
                or before.get("bridge_pid") != self.game["pid"]
                or before.get("one_life_terminal") is not True
                or before.get("one_life_terminal_reason") != "played_character_changed"):
            raise ValueError("successor UI preintent is not the original terminal Continue frame")
        if self.path.exists():
            value, _ = self._checked()
            if value["status"] != "resolved":
                raise ValueError("original handoff/UI obligation is already pending; do not resend")
        self._write({"schema": SCHEMA, "machine_id": self.machine_id, "source_epoch": self.epoch,
            "game_identity": self.game, "status": "handoff_unverified", "before": deepcopy(before),
            "candidate": {key: candidate[key] for key in ("selected_step", "snapshot_id", "revision")},
            "action_replay_authorized": False,
            "durability_scope": "FILE_FSYNC_READBACK_NOT_DIRECTORY_FSYNC"})

    def retain(self, transition, snapshot, *, verification):
        current = frame(snapshot)
        if current["bridge_pid"] != self.game["pid"]:
            raise ValueError("successor UI Game differs before retaining the obligation")
        if not self.path.exists():
            raise ValueError("successor UI lost its pre-Continue intent")
        old, _ = _read(self.path)
        if (old.get("schema") != SCHEMA or old.get("status") != "handoff_unverified"
                or old.get("source_epoch") != self.epoch or old.get("machine_id") != self.machine_id
                or old.get("game_identity") != self.game or old.get("before") != verification["before"]):
            raise ValueError("successor UI differs from its retained pre-Continue intent")
        original = self.verify(verification["result"], snapshot=verification["snapshot"],
            binding=verification["binding"], before=verification["before"],
            succession_lifecycle=verification["succession_lifecycle"])
        persistence = verification["result"].get("driver_state_persistence_diagnostic")
        if isinstance(persistence, Mapping) and persistence.get("status") == "failed":
            raise ValueError("original Continue persistence failed; no verified UI obligation")
        if transition_digest(original) != transition_digest(transition):
            raise ValueError("successor UI retain differs from original full verifier")
        self._write({"schema": SCHEMA, "machine_id": self.machine_id, "source_epoch": self.epoch,
            "game_identity": self.game, "status": "pending", "transition_sha256": transition_digest(transition),
            "verification": deepcopy(verification), "verification_sha256": digest(verification),
            "campaign_goal": normalize_ordinary_campaign_goal_v1(snapshot.get("campaign_goal")),
            "retained_frame": current, "transition": deepcopy(transition),
            "durability_scope": "FILE_FSYNC_READBACK_NOT_DIRECTORY_FSYNC"})

    def load(self, snapshot, *, reconnect_authorization=None):
        if not self.path.exists():
            return None
        value, pin = self._checked()
        if value["status"] == "resolved":
            return None
        if self._intent_path().exists():
            raise ValueError("successor Close intent already exists; collect original result, never resend")
        current = frame(snapshot)
        transition = deepcopy(value["transition"])
        old = value["retained_frame"]
        if (current["bridge_pid"] != self.game["pid"] or current["actor_character_id"] != transition["successor_character_id"]
                or current["episode_run_id"] != transition["episode_run_id"]
                or normalize_ordinary_campaign_goal_v1(snapshot.get("campaign_goal")) != value["campaign_goal"]
                or current["native_revision"] < old["native_revision"] or current["date_raw"] < old["date_raw"]):
            raise ValueError("successor UI cold frame/goal differs from the retained obligation")
        if current["connection_generation"] != old["connection_generation"]:
            expected = {"schema": AUTH, "ledger_sha256": pin, "machine_id": self.machine_id,
                "source_epoch": self.epoch, "game_identity": self.game,
                "old_connection_generation": old["connection_generation"], "resumed_frame": current}
            if reconnect_authorization != expected:
                raise ValueError("successor UI new SDK connection lacks its exact explicit owner rebind")
        elif current["revision"] < old["revision"]:
            raise ValueError("successor UI same connection regressed its public revision")
        previous = transition.get("successor_ui_observation")
        retained = previous.get("frame") if isinstance(previous, Mapping) else transition["successor_episode_binding"]
        cold = {"schema": COLD, "transition_sha256": value["transition_sha256"],
            "observation_sha256": digest(previous), "retained_frame": deepcopy(retained), "resumed_frame": current,
            "machine_id": self.machine_id, "source_epoch": self.epoch, "game_identity": self.game,
            "ledger_sha256": pin, "connection_rebound": current["connection_generation"] != old["connection_generation"]}
        cold["binding_sha256"] = digest(cold)
        # A digest is integrity, not authority. The actual driver's trusted
        # ledger instance must have issued this exact value during its load.
        self._issued_cold_binding = deepcopy(cold)
        transition["_successor_ui_cold_binding_v1"] = cold
        return transition

    def validate_service_binding(self, binding, *, transition, previous_observation, snapshot):
        if self._issued_cold_binding is None or binding != self._issued_cold_binding:
            raise ValueError("successor UI cold binding was not issued by this driver's ledger")
        value, pin = self._checked()
        if (value["status"] != "pending" or pin != binding.get("ledger_sha256")
                or binding.get("source_epoch") != self.epoch or binding.get("machine_id") != self.machine_id
                or binding.get("game_identity") != self.game):
            raise ValueError("successor UI cold binding no longer matches its original ledger/source/Game")
        return validate_cold_ui_binding_v1(binding, transition=transition,
            previous_observation=previous_observation, snapshot=snapshot)

    def update(self, transition, snapshot):
        value, _ = self._checked()
        current = frame(snapshot)
        if value["status"] != "pending" or transition_digest(transition) != value["transition_sha256"]:
            raise ValueError("successor UI update lost its pending original transition")
        if (current["bridge_pid"] != self.game["pid"] or current["actor_character_id"] != transition["successor_character_id"]
                or current["episode_run_id"] != transition["episode_run_id"]
                or normalize_ordinary_campaign_goal_v1(snapshot.get("campaign_goal")) != value["campaign_goal"]):
            raise ValueError("successor UI update changed its Game/actor/episode/goal")
        self._write({**value, "transition": deepcopy(transition), "retained_frame": current})

    def begin_close(self, transition, snapshot, arguments):
        self.update(transition, snapshot)
        path = self._intent_path()
        intent = {"schema": "xar.ck3.successor-ui-close-intent/v1", "status": "UNKNOWN",
            "machine_id": self.machine_id, "source_epoch": self.epoch, "game_identity": self.game,
            "transition_sha256": self.record["transition_sha256"], "request": deepcopy(arguments),
            "frame": frame(snapshot), "result": None, "action_replay_authorized": False,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
        # Exclusive creation is the uniqueness guard; partial writes also keep
        # the filename occupied and therefore forbid a later submission.
        with path.open("x", encoding="utf-8") as stream:
            json.dump(intent, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        if _read(path)[0] != intent:
            raise ValueError("successor Close intent readback differs")

    def retain_close_result(self, result):
        path = self._intent_path()
        intent, _ = _read(path)
        write_json_atomic(path, {**intent, "result": deepcopy(result)})
        # UNKNOWN remains until the caller passes its original full Close and
        # independent successor postcondition. This is not an ACK success.

    def resolve(self, transition, snapshot):
        self.update(transition, snapshot)
        value = self.record
        path = self._intent_path()
        if path.exists():
            intent, _ = _read(path)
            result = intent.get("result")
            if (self.close_validator(result, starting_date_raw=intent["frame"]["date_raw"],
                    successor_character_id=transition["successor_character_id"]) is not None
                    or any(snapshot.get(key) != result.get(ending) for key, ending in (
                        ("revision", "ending_revision"), ("native_revision", "ending_native_revision"),
                        ("date_raw", "ending_date_raw")))
                    or transition.get("timeline_blocker_continuation", {}).get("status") != "materially_cleared"):
                raise ValueError("successor UI cannot resolve an unverified Close")
            write_json_atomic(path, {**intent, "status": "verified", "independent_post_frame": frame(snapshot)})
        else:
            continuation = transition.get("timeline_blocker_continuation", {})
            if (continuation.get("status") != "already_clear"
                    or self.timeline_classifier(continuation.get("initial_query")) != "already_clear"
                    or snapshot.get("active_event") is not None
                    or snapshot.get("pending_character_interaction") is not None):
                raise ValueError("successor UI lacks independent clear evidence")
        self._write({**value, "status": "resolved", "transition": deepcopy(transition),
                     "resolved_frame": frame(snapshot), "business_cycle_credit": 0})

    def require_resolved_before_save(self):
        if not self.path.exists():
            return
        value, _ = self._checked()
        if value["status"] != "resolved":
            raise ValueError("successor UI obligation remains unresolved; no ordinary SAVE")
