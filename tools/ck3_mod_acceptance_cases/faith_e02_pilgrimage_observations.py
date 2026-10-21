"""Optional milestone reads with one validated JSON and persisted-field contract."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
from typing import Literal, NamedTuple, NotRequired, Protocol, TypeAlias, TypedDict

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]
Presence: TypeAlias = Literal["missing", "null", "value"]
Status: TypeAlias = Literal["not_attempted", "observed", "unavailable_source_binding",
    "skipped_original_budget_or_quit_reserve", "skipped_foreign_or_unavailable_native_event",
    "original_read_failed_or_unavailable"]
RELIGION = "ck3_query_player_religion_context_v1"
KEY_EVENTS = frozenset({"pilgrimage.5001", "pilgrimage.7000", "pilgrimage.9001"})
LIMIT = 8


class MilestoneBinding(TypedDict):
    run_id: str
    machine_id: str
    actor_character_id: int
    bridge_pid: int
    connection_generation: int
    episode_run_id: str | None


class EvidencePin(TypedDict):
    path: str
    bytes: int
    sha256: str


class ResourceRaw(TypedDict):
    raw: int
    scale: Literal[100000]


class FrameStamp(TypedDict):
    date_raw: int
    revision: int
    native_revision: int
    played_character_piety: NotRequired[JSONValue]


class PietyObservation(TypedDict):
    observed: bool
    before: ResourceRaw | None
    after: ResourceRaw | None


class UnboundTraitExperience(TypedDict):
    observed: Literal[False]
    raw: None
    unknown_reason: Literal["native_trait_experience_reader_unbound"]


class UnboundLocation(TypedDict):
    observed: Literal[False]
    province_id: None
    unknown_reason: Literal["native_current_location_reader_unbound"]


class MilestoneMetrics(TypedDict):
    source_frame_bound: bool
    piety: PietyObservation
    religion_context_raw: JSONObject | None
    devotion_profile_raw: JSONObject | None
    devotion_observed: bool
    fulfillment_progress_raw: JSONObject | None
    fulfillment_observed: bool
    field_presence: dict[str, Presence]
    trait_experience: UnboundTraitExperience
    current_location: UnboundLocation


class EventReference(TypedDict):
    definition_key: JSONValue
    instance_id: JSONValue
    root_scope: JSONValue


class MilestoneObservation(TypedDict):
    schema: Literal["faith-e02-pilgrimage-milestone-observation-v1"]
    milestone: str
    machine_id: str
    run_id: str
    binding: MilestoneBinding
    observed_at_utc: str
    status: Status
    before_frame: FrameStamp | None
    after_frame: FrameStamp | None
    query_source: EvidencePin | None
    metrics: MilestoneMetrics | None
    event: EventReference | None
    activity_identity: JSONObject | None
    rewards_paid_by_click_claimed: Literal[False]
    delta_attributed_to_main_reward: Literal[False]
    seventeen_slots_closed: Literal[False]
    error: NotRequired[str]
    evidence: NotRequired[EvidencePin]


class ReadArguments(TypedDict):
    expected_revision: int


class MilestoneReadStep(TypedDict):
    id: str
    tool: Literal["ck3_query_player_religion_context_v1"]
    args: ReadArguments
    fresh_revision: Literal[False]
    continue_on_error: Literal[True]


class MilestoneClient(Protocol):
    output: Path

    def remaining(self) -> float: ...
    def guard(self, reserve: int) -> None: ...
    def snapshot(self, *, require_event_free: bool) -> object: ...
    def execute_plan(self, steps: list[MilestoneReadStep], name: str) -> object: ...
    def checkpoint(self, name: str, value: object) -> str | Path: ...


class NativeFrame(NamedTuple):
    """Memory-only validated wrapper; persistence uses FrameStamp dictionaries."""
    raw: JSONObject
    date_raw: int
    revision: int
    native_revision: int


def json_value(value: object) -> JSONValue:
    """Validate the JSON type domain; tuples, nonfinite floats and nonstr keys fail."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if type(value) is int:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Nonfinite JSON number")
        return value
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        result: JSONObject = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            result[key] = json_value(item)
        return result
    raise ValueError("Value is outside the JSON type domain")


def _object(value: object) -> JSONObject:
    parsed = json_value(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON object required")
    return parsed


def _integer(value: object, low: int = -(2**63), high: int = 2**63 - 1) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Exact integer required in range")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty string required")
    return value


def parse_binding(value: object) -> MilestoneBinding:
    raw = _object(value)
    if set(raw) != {"run_id", "machine_id", "actor_character_id", "bridge_pid",
                    "connection_generation", "episode_run_id"}:
        raise ValueError("Exact milestone binding fields required")
    episode = raw["episode_run_id"]
    if episode is not None:
        episode = _text(episode)
    return {"run_id": _text(raw["run_id"]), "machine_id": _text(raw["machine_id"]),
        "actor_character_id": _integer(raw["actor_character_id"], 1, 2**32 - 2),
        "bridge_pid": _integer(raw["bridge_pid"], 1, 2**32 - 1),
        "connection_generation": _integer(raw["connection_generation"], 1, 2**53 - 1),
        "episode_run_id": episode}


def milestone_event(typed: object, binding: object) -> bool:
    """An actual same-actor native event, never a source-script prediction."""
    try:
        owner, event = parse_binding(binding), _object(typed)
        root = _object(event.get("root_scope"))
        who = _object(root.get("typed_identity"))
        return (event.get("schema") == "current-event-window-context-v1"
            and event.get("status") == "available" and event.get("event_definition_key") in KEY_EVENTS
            and _integer(event.get("current_event_instance_id"), 1, 2**32 - 1) > 0
            and root.get("status") == "available" and _integer(root.get("raw_type_index")) == 4
            and root.get("type_key") == "character" and who.get("status") == "available"
            and who.get("kind") == "character"
            and _integer(who.get("character_id"), 1, 2**32 - 2) == owner["actor_character_id"])
    except (ValueError, TypeError):
        return False


def _frame(value: object, binding: MilestoneBinding) -> NativeFrame | None:
    try:
        raw = _object(value)
        actor, diagnostic = _object(raw.get("played_character")), _object(raw.get("diagnostics"))
        hello = _object(diagnostic.get("hello"))
        if not (_integer(actor.get("character_id"), 1, 2**32 - 2) == binding["actor_character_id"]
                and actor.get("alive") is True and actor.get("source") == "native"
                and _integer(diagnostic.get("bridge_pid"), 1) == _integer(hello.get("pid"), 1) == binding["bridge_pid"]
                and _integer(diagnostic.get("connection_generation"), 1) ==
                    _integer(hello.get("connection_generation"), 1) == binding["connection_generation"]
                and type(raw.get("episode_run_id")) is type(binding["episode_run_id"])
                and raw.get("episode_run_id") == binding["episode_run_id"]
                and raw.get("paused") is True and raw.get("map_ready") is True
                and raw.get("backend_id") == "native-headless" and raw.get("source") == "injected-dll-named-pipe"
                and hello.get("ck3_build_match") is True and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64"):
            return None
        return NativeFrame(raw, _integer(raw.get("date_raw")), _integer(raw.get("revision"), 1),
                           _integer(raw.get("native_revision"), 1))
    except (ValueError, TypeError):
        return None


def _stamp(frame: NativeFrame | None) -> FrameStamp | None:
    if frame is None:
        return None
    result: FrameStamp = {"date_raw": frame.date_raw, "revision": frame.revision,
                         "native_revision": frame.native_revision}
    if "played_character_piety" in frame.raw:
        result["played_character_piety"] = deepcopy(frame.raw["played_character_piety"])
    return result


def _resource(value: object) -> ResourceRaw | None:
    try:
        raw = _object(value)
        amount = _integer(raw.get("raw"))
        if _integer(raw.get("scale")) != 100000:
            return None
        return {"raw": amount, "scale": 100000}
    except ValueError:
        return None


def _presence(raw: JSONObject, key: str) -> Presence:
    return "missing" if key not in raw else "null" if raw[key] is None else "value"


def _addon(value: object, context: JSONObject) -> JSONObject | None:
    if value is None:
        return None
    try:
        raw = _object(value)
        for key in ("capture_epoch", "date_raw", "played_character_id"):
            if _integer(raw.get(key)) != _integer(context.get(key)):
                return None
        if type(raw.get("available")) is not bool:
            return None
        for key, number in raw.items():
            if key.endswith("_raw") or key in {"raw_scale", "effective_level", "effective_cap", "runtime_threshold_count", "active_level_index", "level_count"}:
                if number is not None:
                    _integer(number)
        return raw
    except ValueError:
        return None


def project_observation(binding: object, before: object, value: object, after: object) -> MilestoneMetrics:
    """Validate inputs then preserve raw values; no reward or delta arithmetic."""
    result: MilestoneMetrics = {"source_frame_bound": False,
        "piety": {"observed": False, "before": None, "after": None},
        "religion_context_raw": None, "devotion_profile_raw": None, "devotion_observed": False,
        "fulfillment_progress_raw": None, "fulfillment_observed": False, "field_presence": {},
        "trait_experience": {"observed": False, "raw": None, "unknown_reason": "native_trait_experience_reader_unbound"},
        "current_location": {"observed": False, "province_id": None, "unknown_reason": "native_current_location_reader_unbound"}}
    try:
        owner, context = parse_binding(binding), _object(value)
        first, last = _frame(before, owner), _frame(after, owner)
        if not (first is not None and last is not None and first.date_raw == last.date_raw
                and context.get("read_only") is True
                and _integer(context.get("played_character_id"), 1, 2**32 - 2) == owner["actor_character_id"]
                and _integer(context.get("snapshot_revision"), 1) == first.native_revision
                and _integer(context.get("queried_revision"), 1) == first.revision
                and _integer(context.get("date_raw")) == _integer(context.get("query_date_raw")) == first.date_raw
                and _integer(context.get("capture_epoch"), 1, 2**64 - 1) > 0):
            return result
        for key in ("rite_id", "faith_id", "faith_main_rite_id"):
            if key in context and context[key] is not None:
                _integer(context[key], 0, 2**32 - 1)
        if "spiritual_fulfillment_raw" in context and context["spiritual_fulfillment_raw"] is not None:
            _integer(context["spiritual_fulfillment_raw"])
        if "raw_scale" in context and context["raw_scale"] is not None:
            _integer(context["raw_scale"])
        if "available" in context and type(context["available"]) is not bool:
            return result
        result["source_frame_bound"] = True
        for key in ("spiritual_fulfillment_raw", "player_piety_devotion_profile", "player_spiritual_fulfillment_progress"):
            result["field_presence"][key] = _presence(context, key)
        result["field_presence"]["piety_before"] = _presence(first.raw, "played_character_piety")
        result["field_presence"]["piety_after"] = _presence(last.raw, "played_character_piety")
        p_before, p_after = _resource(first.raw.get("played_character_piety")), _resource(last.raw.get("played_character_piety"))
        if p_before is not None and p_after is not None:
            result["piety"] = {"observed": True, "before": p_before, "after": p_after}
        keys = ("schema", "available", "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
            "rite_id", "faith_id", "faith_main_rite_id", "spiritual_fulfillment_raw", "raw_scale")
        result["religion_context_raw"] = {key: deepcopy(context[key]) for key in keys if key in context}
        fulfillment = context.get("spiritual_fulfillment_raw")
        result["fulfillment_observed"] = (context.get("available") is True and type(fulfillment) is int
            and context.get("raw_scale") == 100000 and type(context.get("raw_scale")) is int)
        devotion = _addon(context.get("player_piety_devotion_profile"), context)
        result["devotion_profile_raw"] = devotion
        result["fulfillment_progress_raw"] = _addon(context.get("player_spiritual_fulfillment_progress"), context)
        if devotion is not None:
            result["devotion_observed"] = (devotion.get("available") is True
                and type(devotion.get("current_devotion_total_raw")) is int
                and type(devotion.get("effective_level")) is int and devotion.get("raw_scale") == 100000)
    except (ValueError, TypeError):
        return result
    return result


def _pin(path: str | Path) -> EvidencePin:
    actual = Path(path)
    raw = actual.read_bytes()
    return {"path": str(actual), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def observe_milestone(context: object, client: MilestoneClient, binding: object,
        observations: list[MilestoneObservation], label: str, *, event: object = None,
        identity: object = None) -> tuple[MilestoneObservation | None, JSONObject | None]:
    """One read attempt and two counted controls; malformed boundary input fails closed."""
    owner, config = parse_binding(binding), _object(context)
    _text(label)
    event_raw = _object(event) if event is not None else None
    identity_raw = _object(identity) if identity is not None else None
    if identity_raw is not None:
        _integer(identity_raw.get("activity_id"), 0, 2**32 - 2)
        if _integer(identity_raw.get("host_character_id"), 1, 2**32 - 2) != owner["actor_character_id"]:
            raise ValueError("Activity identity owner differs")
    if label in {row["milestone"] for row in observations} or len(observations) >= LIMIT:
        return None, None
    event_ref: EventReference | None = None
    if event_raw is not None:
        event_ref = {"definition_key": event_raw.get("event_definition_key"),
            "instance_id": event_raw.get("current_event_instance_id"), "root_scope": deepcopy(event_raw.get("root_scope"))}
    entry: MilestoneObservation = {"schema": "faith-e02-pilgrimage-milestone-observation-v1", "milestone": label,
        "machine_id": owner["machine_id"], "run_id": owner["run_id"], "binding": owner,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "not_attempted",
        "before_frame": None, "after_frame": None, "query_source": None, "metrics": None,
        "event": event_ref, "activity_identity": identity_raw, "rewards_paid_by_click_claimed": False,
        "delta_attributed_to_main_reward": False, "seventeen_slots_closed": False}
    observations.append(entry)
    name = "ordinary-pilgrimage-milestone-" + str(len(observations)).zfill(2) + "-" + label.replace(".", "-")
    first: NativeFrame | None = None
    last: NativeFrame | None = None
    try:
        contract = _object(config.get("case_contract"))
        if config.get("run_id") != owner["run_id"] or contract.get("machine_id") != owner["machine_id"]:
            raise ValueError("Milestone run/machine differs")
        reserve = _integer(_object(contract.get("policy")).get("quit_reserve_seconds"), 90, 600)
        used: object = getattr(client, "public_requests_used", None)
        cap: object = getattr(client, "public_requests_cap", None)
        if ((type(used) is int and type(cap) is int and used + 2 > cap) or client.remaining() <= reserve + 35):
            entry["status"] = "skipped_original_budget_or_quit_reserve"
        elif event_raw is not None and not milestone_event(event_raw, owner):
            entry["status"] = "skipped_foreign_or_unavailable_native_event"
        else:
            client.guard(reserve)
            first = _frame(client.snapshot(require_event_free=False), owner)
            entry["before_frame"] = _stamp(first)
            if first is None:
                raise ValueError("Fresh native milestone owner differs")
            if event_raw is not None and label.endswith("-window") and (
                    _object(first.raw.get("active_event")).get("instance_id") != event_raw["current_event_instance_id"]):
                raise ValueError("Original key window is no longer current")
            step: MilestoneReadStep = {"id": name, "tool": "ck3_query_player_religion_context_v1",
                "args": {"expected_revision": first.revision}, "fresh_revision": False, "continue_on_error": True}
            rows = json_value(client.execute_plan([step], name))
            path = client.output / (name + ".actual-results.json")
            if path.is_file():
                entry["query_source"] = _pin(path)
            if not isinstance(rows, list) or len(rows) != 1:
                raise ValueError("Original read result unavailable; no retry")
            row = _object(rows[0])
            if row.get("ok") is not True or row.get("error") or not isinstance(row.get("result"), dict):
                raise ValueError("Original read result unavailable; no retry")
            last = _frame(row.get("after_snapshot"), owner)
            entry["after_frame"] = _stamp(last)
            metrics = project_observation(owner, first.raw, row["result"], last.raw if last else None)
            entry["metrics"] = metrics
            entry["status"] = "observed" if metrics["source_frame_bound"] else "unavailable_source_binding"
    except Exception as error:
        entry["status"] = "original_read_failed_or_unavailable"
        entry["error"] = type(error).__name__ + ": " + str(error)
    entry["evidence"] = _pin(client.checkpoint(name, entry))
    latest = last.raw if first is not None and last is not None and first.date_raw == last.date_raw else None
    return entry, latest
