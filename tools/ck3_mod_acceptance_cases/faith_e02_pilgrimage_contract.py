"""Frozen native identities for the shared pilgrimage filming adapter."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from pathlib import Path
import hashlib
import json
import re
from ck3_mod_acceptance_background_types import FilePin, file_pin, json_object as _json_object


def json_object(value: object, label: str) -> dict[str, object]:
    try:
        return {k: v for k, v in _json_object(value).items()}
    except ValueError as error:
        raise ValueError(label + ": " + str(error)) from error

LegacyCase = Literal["faith-engine-e02-d1-ordinary-pilgrimage-v1"]
MechanismCase = Literal["faith-engine-e02-pilgrimage-mechanism-v2"]
OptionKey = Literal["pilgrimage_type_pious", "pilgrimage_type_worldly", "pilgrimage_type_hajj"]
LEGACY_CASE: LegacyCase = "faith-engine-e02-d1-ordinary-pilgrimage-v1"
MECHANISM_CASE: MechanismCase = "faith-engine-e02-pilgrimage-mechanism-v2"


@dataclass(frozen=True)
class PilgrimageIdentity:
    case: LegacyCase | MechanismCase
    actor_character_id: int
    date_raw: int
    faith_id: int
    rite_id: int | None
    option_key: OptionKey


@dataclass(frozen=True)
class PilgrimagePolicyCaps:
    max_days: int
    max_public_requests: int
    max_day_requests: int = 1024


@dataclass(frozen=True)
class ConsumedPilgrimageEvent:
    event_id: str
    query: FilePin
    selection: FilePin


@dataclass(frozen=True)
class PilgrimageResume:
    predecessor_run_id: str
    original_start: FilePin
    predecessor_runtime: FilePin
    activity_id: int
    host_character_id: int
    consumed_events: tuple[ConsumedPilgrimageEvent, ...]

    def activity_json(self) -> dict[str, object]:
        return {"activity_id": self.activity_id, "host_character_id": self.host_character_id,
            "type_key": "activity_pilgrimage"}


@dataclass(frozen=True)
class PilgrimageResumeOrigin:
    bridge_pid: int
    connection_generation: int
    start_date_raw: int
    source_commit: str
    consumed_event_definitions: tuple[str, ...]


def _closed_pin(value: object) -> FilePin:
    pin = file_pin(value)
    if not isinstance(value, Mapping) or set(value) != {"path", "bytes", "sha256"} or not Path(pin["path"]).is_absolute():
        raise ValueError("resume evidence requires a closed absolute FilePin")
    return pin


def pilgrimage_resume(value: object) -> PilgrimageResume | None:
    """Absent mode is the existing once-only Start; resume is an explicit v2 branch."""
    if not isinstance(value, Mapping):
        raise ValueError("pilgrimage entry requires an object")
    mode = value.get("entry_mode", "new_start")
    if mode == "new_start" and type(mode) is str:
        if "resume_existing" in value:
            raise ValueError("new_start cannot carry resume_existing")
        return None
    if type(mode) is not str or mode != "resume_existing" or value.get("case") != MECHANISM_CASE:
        raise ValueError("only the mechanism case supports explicit resume_existing")
    raw = value.get("resume_existing")
    if not isinstance(raw, Mapping) or set(raw) != {"predecessor_run_id", "original_start", "predecessor_runtime", "activity", "consumed_events"}:
        raise ValueError("resume_existing requires its exact provenance and activity fields")
    run = raw["predecessor_run_id"]
    if type(run) is not str or not run.strip():
        raise ValueError("resume predecessor run must be a nonempty string")
    activity = raw["activity"]
    if not isinstance(activity, Mapping) or set(activity) != {"activity_id", "host_character_id", "type_key"} or activity["type_key"] != "activity_pilgrimage":
        raise ValueError("resume requires the full pilgrimage identity, including valid activity ID zero")
    rows = raw["consumed_events"]
    if not isinstance(rows, list) or len(rows) > 256:
        raise ValueError("resume consumed_events must be an explicit bounded array")
    events: list[ConsumedPilgrimageEvent] = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"event_id", "query", "selection"}:
            raise ValueError("resume consumed event requires definition, query and successful selection pins")
        key = row["event_id"]
        if type(key) is not str or re.fullmatch(r"[a-zA-Z0-9_]+\.[0-9]+", key) is None or key in [e.event_id for e in events]:
            raise ValueError("resume consumed event definition is malformed or duplicated")
        events.append(ConsumedPilgrimageEvent(key, _closed_pin(row["query"]), _closed_pin(row["selection"])))
    return PilgrimageResume(run, _closed_pin(raw["original_start"]), _closed_pin(raw["predecessor_runtime"]),
        _integer(activity["activity_id"], "activity"), _integer(activity["host_character_id"], "activity host", 1), tuple(events))


def _pinned_object(pin: FilePin) -> dict[str, object]:
    if pin["bytes"] > 16 * 1024 * 1024:
        raise ValueError("resume small provenance input exceeds 16MiB")
    raw = Path(pin["path"]).read_bytes()
    if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("resume evidence bytes differ: " + pin["path"])
    return json_object(json.loads(raw.decode("utf-8-sig")), "resume evidence")


def _result_row(pin: FilePin) -> dict[str, object]:
    rows = _pinned_object(pin).get("rows")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("resume event evidence must contain one actual public result")
    row = json_object(rows[0], "resume actual result row")
    if row.get("ok") is not True or row.get("error"):
        raise ValueError("resume cannot consume a failed public result")
    return row


def _previous_frame_owner(frame: dict[str, object], *, pid: int, generation: int, actor: int, date: int) -> None:
    diagnostics = json_object(frame.get("diagnostics"), "previous native frame diagnostics")
    hello = json_object(diagnostics.get("hello"), "previous native frame hello")
    who = json_object(frame.get("played_character"), "previous native frame actor")
    if (any(type(row.get(key)) is not int or row.get(key) != wanted
            for row, key, wanted in ((diagnostics, "bridge_pid", pid), (diagnostics, "connection_generation", generation),
                (hello, "pid", pid), (hello, "connection_generation", generation),
                (who, "character_id", actor), (frame, "date_raw", date)))
            or "active_event" not in frame):
        raise ValueError("previous native frame lacks the exact owner/date/explicit active_event")
    active = frame["active_event"]
    if active is not None:
        window = json_object(active, "previous active event")
        _integer(window.get("instance_id"), "previous active event instance", 1)
        options = window.get("options")
        count = _integer(window.get("option_count"), "previous active event option count")
        if not isinstance(options, list) or count != len(options) or count > 64:
            raise ValueError("previous active event options are not an actual typed window")
        for raw_option in options:
            option = json_object(raw_option, "previous active event option")
            _integer(option.get("option_number"), "previous event option number", 1)
            if type(option.get("enabled")) is not bool:
                raise ValueError("previous active event option readiness is unavailable")


def verify_pilgrimage_resume_origin(resume: PilgrimageResume, *, identity: PilgrimageIdentity,
        machine_id: str, run_id: str, preferred_destination_id: object) -> PilgrimageResumeOrigin:
    """Read actual pinned Start/source/selection evidence; never upgrade an old journey flag."""
    origin = _pinned_object(resume.original_start)
    binding = json_object(origin.get("binding"), "predecessor native binding")
    start = json_object(origin.get("start_response"), "predecessor original Start")
    planner = json_object(start.get("planner"), "predecessor Start planner")
    hosted = json_object(origin.get("hosted_identity"), "predecessor hosted identity")
    if (resume.predecessor_run_id == run_id or origin.get("run_id") != resume.predecessor_run_id
            or binding.get("run_id") != resume.predecessor_run_id or origin.get("machine_id") != machine_id
            or binding.get("machine_id") != machine_id or binding.get("actor_character_id") != identity.actor_character_id
            or type(binding.get("actor_character_id")) is not int
            or origin.get("native_ledger_state_reconciled") is not True
            or start.get("invoked") is not True or start.get("operation") != "start"
            or type(start.get("played_character_id")) is not int or start["played_character_id"] != identity.actor_character_id
            or planner.get("selected_option_key") != identity.option_key
            or type(planner.get("destination_province_id")) is not int
            or planner["destination_province_id"] != preferred_destination_id
            or any(type(hosted.get(k)) is not type(v) or hosted.get(k) != v for k, v in resume.activity_json().items())
            or resume.host_character_id != identity.actor_character_id):
        raise ValueError("resume original Start owner, option, destination or hosted identity differs")
    pid = _integer(binding.get("bridge_pid"), "predecessor PID", 1)
    generation = _integer(binding.get("connection_generation"), "predecessor generation", 1)
    date = _integer(start.get("date_raw"), "original Start date", 1)
    if date > identity.date_raw:
        raise ValueError("resume save predates its original Start")
    runtime = _pinned_object(resume.predecessor_runtime)
    manifest = _pinned_object(_closed_pin(runtime.get("manifest")))
    paths = json_object(runtime.get("paths"), "predecessor runtime paths")
    source = json_object(manifest.get("source_index"), "predecessor source index pin")
    source_path = paths.get("source_index")
    if set(source) != {"path_key", "bytes", "sha256"} or source.get("path_key") != "source_index":
        raise ValueError("resume predecessor source index binding differs")
    index = _pinned_object(_closed_pin({"path": source_path, "bytes": source.get("bytes"), "sha256": source.get("sha256")}))
    commit = manifest.get("source_commit")
    if (runtime.get("schema") != "ck3-mod-acceptance-runtime-v1" or runtime.get("machine_id") != machine_id
            or manifest.get("machine_id") != machine_id or type(commit) is not str
            or re.fullmatch(r"[0-9a-f]{40}", commit) is None or index.get("source_commit") != commit):
        raise ValueError("resume predecessor runtime/source binding differs")
    for event in resume.consumed_events:
        query_row, selected_row = _result_row(event.query), _result_row(event.selection)
        query = json_object(query_row.get("result"), "consumed typed query")
        typed = json_object(query.get("current_event_window_context"), "consumed typed event")
        query_after = json_object(query_row.get("after_snapshot"), "consumed query after-frame")
        selection = json_object(selected_row.get("result"), "consumed event selection")
        post = json_object(selection.get("event_selection"), "consumed native postcondition")
        after = json_object(selected_row.get("after_snapshot"), "consumed selection after-frame")
        actor = json_object(after.get("played_character"), "consumed selection actor")
        plan = json_object(selected_row.get("plan"), "consumed selection plan")
        args = json_object(plan.get("args"), "consumed selection arguments")
        instance = _integer(typed.get("current_event_instance_id"), "consumed old event instance", 1)
        event_date = _integer(typed.get("date_raw"), "consumed event date", 1)
        _previous_frame_owner(query_after, pid=pid, generation=generation,
            actor=identity.actor_character_id, date=event_date)
        _previous_frame_owner(after, pid=pid, generation=generation,
            actor=identity.actor_character_id, date=event_date)
        active_after = after.get("active_event")
        if (query.get("accepted") is not True or typed.get("status") != "available"
                or typed.get("event_definition_key") != event.event_id or not date <= event_date <= identity.date_raw
                or selection.get("accepted") is not True or post.get("postcondition_verified") is not True
                or post.get("status") != "event_instance_advanced" or type(post.get("old_event_instance_id")) is not int
                or post["old_event_instance_id"] != instance or post.get("bridge_pid") != pid
                or type(post.get("bridge_pid")) is not int or post.get("connection_generation") != generation
                or type(post.get("connection_generation")) is not int or plan.get("tool") != "ck3_select_event_option"
                or args.get("event_instance_id") != instance or type(args.get("event_instance_id")) is not int
                or type(args.get("option_number")) is not int or args["option_number"] != post.get("selected_option_number")
                or actor.get("character_id") != identity.actor_character_id or type(actor.get("character_id")) is not int
                or after.get("date_raw") != event_date or type(after.get("date_raw")) is not int
                or (isinstance(active_after, Mapping) and active_after.get("instance_id") == instance)):
            raise ValueError("resume consumed event lacks a bound successful native postcondition")
    return PilgrimageResumeOrigin(pid, generation, date, commit, tuple(e.event_id for e in resume.consumed_events))


def pilgrimage_policy_caps(case_id: object) -> PilgrimagePolicyCaps:
    if type(case_id) is not str:
        raise ValueError("pilgrimage finite policy requires an exact case string")
    if case_id == LEGACY_CASE:
        return PilgrimagePolicyCaps(max_days=366, max_public_requests=1024)
    if case_id == MECHANISM_CASE:
        return PilgrimagePolicyCaps(max_days=730, max_public_requests=4096)
    raise ValueError("unknown pilgrimage case for finite policy")


def _integer(value: object, label: str, low: int = 0) -> int:
    if type(value) is not int or not low <= value < 2**32 - 1:
        raise ValueError(label + " must be a frozen exact integer identity")
    return value


def pilgrimage_identity(value: object) -> PilgrimageIdentity:
    if not isinstance(value, Mapping):
        raise ValueError("pilgrimage contract must be an object")
    actor = _integer(value.get("expected_actor_character_id"), "actor", 1)
    date = _integer(value.get("prior_scene_date_raw"), "date", 1)
    if value.get("case") == LEGACY_CASE:
        if value.get("schema") != "faith-engine-e02-d1-ordinary-pilgrimage-case-v1":
            raise ValueError("legacy D1 contract schema differs")
        if any(key in value for key in ("option_key", "expected_faith_id", "expected_rite_id")):
            raise ValueError("legacy D1 contract cannot acquire mechanism overrides")
        return PilgrimageIdentity(LEGACY_CASE, actor, date, 13, 0, "pilgrimage_type_pious")
    if value.get("case") != MECHANISM_CASE or value.get("schema") != "faith-engine-e02-pilgrimage-mechanism-case-v2":
        raise ValueError("unknown pilgrimage case/schema")
    if not {"option_key", "expected_faith_id", "expected_rite_id"} <= value.keys():
        raise ValueError("mechanism contract requires actual faith, nullable rite and option")
    faith = _integer(value["expected_faith_id"], "faith", 1)
    raw_rite = value["expected_rite_id"]
    rite = None if raw_rite is None else _integer(raw_rite, "rite")
    key = value["option_key"]
    if key == "pilgrimage_type_pious":
        option: OptionKey = "pilgrimage_type_pious"
    elif key == "pilgrimage_type_worldly":
        option = "pilgrimage_type_worldly"
    elif key == "pilgrimage_type_hajj":
        option = "pilgrimage_type_hajj"
    else:
        raise ValueError("unsupported original pilgrimage option identity")
    return PilgrimageIdentity(MECHANISM_CASE, actor, date, faith, rite, option)


NaturalAdvanceMode = Literal["one_day", "native_horizon"]
NATURAL_HORIZON_MAX_DAYS = 30
NATURAL_HORIZON_RESERVE_HOURS = 48


def pilgrimage_natural_advance_mode(case_id: object, policy: object) -> NaturalAdvanceMode:
    pilgrimage_policy_caps(case_id)
    if not isinstance(policy, Mapping):
        raise ValueError("Pilgrimage natural-advance policy must be an object")
    if "natural_advance_mode" not in policy:
        return "one_day"
    if case_id != MECHANISM_CASE:
        raise ValueError("Legacy D1 cannot acquire a natural-advance override")
    mode = policy["natural_advance_mode"]
    if type(mode) is not str:
        raise ValueError("Natural-advance mode must be an exact string")
    if mode == "one_day":
        return "one_day"
    if mode == "native_horizon":
        return "native_horizon"
    raise ValueError("Unknown natural-advance mode")


def require_pilgrimage_natural_capabilities(value: object) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("Actual natural-advance capabilities must be an object")
    for field in ("action_steps", "composite_action_steps"):
        rows = value.get(field)
        if not isinstance(rows, list) or not all(type(row) is str for row in rows):
            raise ValueError("Actual native capability list is malformed: " + field)
        if "life-advance" not in rows:
            raise ValueError("Actual shared life-advance composite is unavailable")
    if value.get("current_event_window_context_v1_query_supported") is not True:
        raise ValueError("Natural horizon requires the actual typed event observer")


@dataclass(frozen=True)
class PilgrimageNaturalInterval:
    requested_horizon_days: int
    elapsed_hours: int
    boundary: Literal["event", "interaction", "none"]
    progress_status: str

    def to_json(self) -> dict[str, object]:
        return {"requested_horizon_days": self.requested_horizon_days,
            "elapsed_hours": self.elapsed_hours, "boundary": self.boundary,
            "progress_status": self.progress_status}


def parse_pilgrimage_natural_interval(
        value: object, *, before_date_raw: int, after_date_raw: int,
        has_event: bool, has_interaction: bool, remaining_hours: int,
) -> PilgrimageNaturalInterval:
    if (type(before_date_raw) is not int or type(after_date_raw) is not int
            or type(remaining_hours) is not int or remaining_hours < 1
            or type(has_event) is not bool or type(has_interaction) is not bool):
        raise ValueError("Exact natural interval owner dates, remaining hours and boundary flags required")
    if not isinstance(value, Mapping):
        raise ValueError("Original life-advance result must be an object")
    if not {"active_event", "pending_character_interaction"} <= value.keys():
        raise ValueError("Natural interval must retain explicit nullable native boundaries")
    if (value.get("step") != "life-advance" or value.get("source") != "native-composite"
            or value.get("backend_id") != "native-headless" or value.get("paused") is not True
            or type(value.get("starting_date_raw")) is not int
            or type(value.get("ending_date_raw")) is not int
            or value["starting_date_raw"] != before_date_raw
            or value["ending_date_raw"] != after_date_raw):
        raise ValueError("Original paused natural interval dates/source differ")
    horizon = value.get("requested_horizon_days")
    if type(horizon) is not int or not 1 <= horizon <= NATURAL_HORIZON_MAX_DAYS:
        raise ValueError("Original requested natural horizon must be an exact 1..30 day integer")
    hours = after_date_raw - before_date_raw
    if (horizon * 24 > remaining_hours or not 0 <= hours <= remaining_hours
            or hours > NATURAL_HORIZON_MAX_DAYS * 24 + NATURAL_HORIZON_RESERVE_HOURS):
        raise ValueError("Original requested/actual interval crossed the finite remaining duration")
    elapsed_days = value.get("elapsed_days")
    if type(elapsed_days) is not int or elapsed_days != hours // 24:
        raise ValueError("Natural elapsed-day projection differs from the actual raw-hour interval")
    status = value.get("progress_status")
    if type(status) is not str or status not in {
            "postcondition", "modal_interrupted", "wall_timeout_with_date_progress", "boundary_interrupted"}:
        raise ValueError("Original natural progress status unavailable")
    if value.get("ordinary_events") != []:
        raise ValueError("Natural interval must leave all event choices to the shared journey")
    resolution = value.get("event_resolution")
    raw_event = value.get("active_event")
    if raw_event is not None:
        if not isinstance(raw_event, Mapping) or not has_event or resolution != "typed_query_required":
            raise ValueError("Natural interval event selection was not retained for typed drain")
    elif resolution != "none":
        raise ValueError("Natural interval reports an event outcome without its original event")
    # An event can first appear in the public after-snapshot, after the Driver
    # returned a modal-free result at this same ending date. Drain that fresh
    # window; do not invent another day or require a prior result to know it.
    raw_interaction = value["pending_character_interaction"]
    if raw_interaction is not None and (not isinstance(raw_interaction, Mapping) or not has_interaction):
        raise ValueError("Original native interaction vanished before the journey drained it")
    if status in {"modal_interrupted", "boundary_interrupted"} and not (has_event or has_interaction):
        raise ValueError("Unbound exclusive modal cannot enter another natural interval")
    if hours == 0 and not (has_event or has_interaction):
        raise ValueError("Zero-hour natural interval lacks an actual interruption")
    boundary: Literal["event", "interaction", "none"] = (
        "event" if has_event else "interaction" if has_interaction else "none")
    return PilgrimageNaturalInterval(horizon, hours, boundary, status)
