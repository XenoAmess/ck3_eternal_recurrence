"""A monthly Sway opportunity before an already proved stationary war wait."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, Protocol, TypeGuard, TypedDict, runtime_checkable

from .war_contract import normalize_route_contact_horizon, parse_advance_route_contact_horizon_step

SCHEMA: Final = "xar.war-stationary-sway-opportunity/v1"
PHASE = "native_war_stationary_contact_horizon_progress"


class WindowV1(TypedDict):
    schema: Literal["xar.war-stationary-sway-opportunity/v1"]
    original_selected_step: str
    snapshot_id: str
    revision: int
    native_revision: int
    date_raw: int
    actor_character_id: int
    episode_run_id: str
    bridge_pid: int
    connection_generation: int
    contact_horizon: dict[str, object]


@dataclass(frozen=True)
class _Frame:
    snapshot_id: str
    revision: int
    native_revision: int
    date_raw: int
    actor_character_id: int
    episode_run_id: str
    bridge_pid: int
    connection_generation: int


def _mapping(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        return None
    return {key: item for key, item in value.items()}


def _integer(value: object) -> TypeGuard[int]:
    return type(value) is int


def _positive(value: object) -> TypeGuard[int]:
    return type(value) is int and 0 < value <= 0xFFFFFFFF


def _text(value: object) -> TypeGuard[str]:
    return type(value) is str and bool(value)


def _binding(value: object, *, window: bool = False) -> _Frame | None:
    row = _mapping(value)
    if row is None:
        return None
    played = _mapping(row.get("played_character"))
    diag = _mapping(row.get("diagnostics"))
    actor = row.get("actor_character_id") if window else played.get("character_id") if played else None
    pid = row.get("bridge_pid") if window else diag.get("bridge_pid") if diag else None
    generation = row.get("connection_generation") if window else diag.get("connection_generation") if diag else None
    sid, revision, native, date, episode = (row.get(key) for key in
        ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
    if (not _text(sid) or not _positive(revision) or not _positive(native)
            or not _integer(date) or not _positive(actor) or not _text(episode)
            or not _positive(pid) or not _positive(generation)):
        return None
    return _Frame(sid, revision, native, date, actor, episode, pid, generation)


def _quiet(snapshot: object, *, subject: int, province: int, hostiles: tuple[int, ...]) -> bool:
    row = _mapping(snapshot)
    if row is None:
        return False
    played = _mapping(row.get("played_character"))
    context = _mapping(row.get("active_context"))
    if "active_context" not in row and {"active_event", "pending_character_interaction"} <= set(row):
        context = {key: row[key] for key in ("active_event", "pending_character_interaction")}
    hint = _mapping(row.get("top_exclusive_modal_choice_hint"))
    if (row.get("paused") is not True or row.get("map_ready") is not True
            or row.get("episode_identity_pending") is not False
            or "one_life_terminal_reason" not in row or row["one_life_terminal_reason"] is not None
            or played is None or played.get("alive") is not True
            or type(row.get("episode_character_id")) is not int
            or row["episode_character_id"] != played.get("character_id")
            or context is None or not {"active_event", "pending_character_interaction"} <= set(context)
            or context.get("active_event") is not None or context.get("pending_character_interaction") is not None
            or hint is None or hint.get("status") != "absent" or hint.get("owner_verified") is not True
            or row.get("one_life_terminal") is not False):
        return False
    armies, wars = row.get("player_armies"), row.get("active_wars")
    if not isinstance(armies, list) or len(armies) != 1 or not isinstance(wars, list) or not wars:
        return False
    army = _mapping(armies[0])
    if (army is None or type(army.get("army_id")) is not int or army["army_id"] != subject
            or type(army.get("owner_character_id")) is not int
            or army["owner_character_id"] != played.get("character_id") or army.get("controllable") is not True
            or army.get("army_state") != "regular" or army.get("in_combat") is not False
            or army.get("retreating") is not False
            or type(army.get("current_province_id")) is not int or army["current_province_id"] != province
            or army.get("move_target_observable") is not False or army.get("move_target_province_id") is not None
            or army.get("route_read_status") != "complete_empty" or army.get("route_province_ids") != []
            or type(army.get("route_source_count")) is not int or army["route_source_count"] != 0):
        return False
    ids: set[int] = set()
    for raw_war in wars:
        war = _mapping(raw_war)
        enemies = war.get("enemy_armies") if war else None
        if war is None or not _positive(war.get("war_id")) or not isinstance(enemies, list):
            return False
        for raw_enemy in enemies:
            enemy = _mapping(raw_enemy)
            identity = enemy.get("army_id") if enemy else None
            if not _positive(identity):
                return False
            ids.add(identity)
    return tuple(sorted(ids)) == hostiles


def parse_window_v1(value: object) -> WindowV1 | None:
    row = _mapping(value)
    keys = set(WindowV1.__annotations__)
    if row is None or set(row) != keys or row.get("schema") != SCHEMA:
        return None
    frame = _binding(row, window=True)
    step = row.get("original_selected_step")
    request = parse_advance_route_contact_horizon_step(step)
    if frame is None or not _text(step) or request is None:
        return None
    subject, province, hostiles = request
    try:
        proof = normalize_route_contact_horizon(row.get("contact_horizon"),
            expected_subject_army_id=subject, expected_target_province_id=province,
            expected_hostile_army_ids=hostiles, expected_date_raw=frame.date_raw,
            expected_snapshot_revision=frame.native_revision)
    except ValueError:
        return None
    route = _mapping(proof.get("subject_route"))
    if (proof.get("one_day_contact_free") is not True or proof.get("conflicts") != []
            or route is None or route.get("current_province_id") != province
            or route.get("route_province_ids") != [] or route.get("arrival_date_raws") != []):
        return None
    return WindowV1(schema=SCHEMA, original_selected_step=step,
        snapshot_id=frame.snapshot_id, revision=frame.revision,
        native_revision=frame.native_revision, date_raw=frame.date_raw,
        actor_character_id=frame.actor_character_id, episode_run_id=frame.episode_run_id,
        bridge_pid=frame.bridge_pid, connection_generation=frame.connection_generation,
        contact_horizon=proof)


def require_current_window_v1(window: object, snapshot: object) -> bool:
    """Consumer admission: reread actual current paused state before a new intent."""
    parsed = parse_window_v1(window)
    if parsed is None or _binding(parsed, window=True) != _binding(snapshot):
        return False
    request = parse_advance_route_contact_horizon_step(parsed["original_selected_step"])
    if request is None:
        return False
    return _quiet(snapshot, subject=request[0], province=request[1], hostiles=request[2])


def build_window_v1(planned: object) -> WindowV1 | None:
    row = _mapping(planned)
    plan = _mapping(row.get("plan")) if row else None
    source = _mapping(row.get("_ordinary_sway_input_v1")) if row else None
    snapshot = _mapping(source.get("snapshot")) if source else None
    frame = _binding(snapshot)
    if plan is None or plan.get("phase") != PHASE or frame is None:
        return None
    if (row is None or not _text(row.get("snapshot_id")) or row.get("snapshot_id") != frame.snapshot_id
            or not _positive(row.get("revision")) or row.get("revision") != frame.revision):
        return None
    origin = _mapping(row.get("planning_source_frame"))
    if (origin is None or origin.get("schema") != "xar.ck3.planning-source-frame/v1"
            or origin.get("status") != "complete" or _binding(origin, window=True) != frame):
        return None
    audit = _mapping(plan.get("route_audit"))
    if audit is None or audit.get("status") != "safe_one_day_stationary_contact_horizon":
        return None
    value = {"schema": SCHEMA, "original_selected_step": plan.get("selected_step"),
        "snapshot_id": frame.snapshot_id, "revision": frame.revision,
        "native_revision": frame.native_revision, "date_raw": frame.date_raw,
        "actor_character_id": frame.actor_character_id, "episode_run_id": frame.episode_run_id,
        "bridge_pid": frame.bridge_pid, "connection_generation": frame.connection_generation,
        "contact_horizon": audit.get("contact_horizon")}
    parsed = parse_window_v1(value)
    return parsed if parsed is not None and require_current_window_v1(parsed, snapshot) else None

def project_safety_inputs_v1(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Copy only existing small safety fields inside the planning-view lock."""
    result: dict[str, object] = {key: snapshot[key] for key in
        ("episode_identity_pending", "one_life_terminal") if key in snapshot}
    for key, fields in (("diagnostics", ("bridge_pid", "connection_generation")),
            ("top_exclusive_modal_choice_hint", ("status", "owner_verified"))):
        value = _mapping(snapshot.get(key))
        if key in snapshot:
            result[key] = {field: value[field] for field in fields if field in value} if value is not None else None
    armies = snapshot.get("player_armies")
    result["player_armies"] = [
        {key: (list(field_value) if isinstance(field_value := row.get(key), list) else field_value) for key in
         ("army_id", "owner_character_id", "controllable", "army_state", "in_combat", "retreating", "current_province_id",
          "move_target_observable", "move_target_province_id", "route_read_status", "route_source_count", "route_province_ids")}
        if (row := _mapping(raw)) is not None else None for raw in armies
    ] if isinstance(armies, list) else None
    wars = snapshot.get("active_wars")
    projected: list[object] = []
    if isinstance(wars, list):
        for raw in wars:
            row = _mapping(raw)
            enemies = row.get("enemy_armies") if row else None
            projected.append({"war_id": row.get("war_id"),
                "enemy_armies": [{"army_id": enemy.get("army_id")} if
                    (enemy := _mapping(item)) is not None else None for item in enemies]
                    if isinstance(enemies, list) else None} if row else None)
        result["active_wars"] = projected
    else:
        result["active_wars"] = None
    return result

BeforeSubmitV1 = Callable[[dict[str, object]], dict[str, object] | None] | None


@runtime_checkable
class DriverV1(Protocol):
    def query_active_scheme_sway_target_private_v1(self, *, expected_revision: int,
            target_character_id: int) -> dict[str, object]: ...


@runtime_checkable
class ServiceV1(Protocol):
    driver: DriverV1

    def _strategy_state_dir(self) -> Path | None: ...
    def snapshot(self, *, include_native_command_history: bool = False) -> dict[str, object]: ...
    def _plan_turn_internal(self) -> dict[str, object]: ...
    def _execute_planned_turn(self, planned: dict[str, object], *, before_submit: BeforeSubmitV1 = None) -> dict[str, object]: ...


def object_v1(value: object) -> dict[str, object]:
    row = _mapping(value)
    if row is None:
        raise ValueError("Sway internal JSON object is malformed")
    return row

def service_v1(value: object) -> ServiceV1:
    """Concentrate the legacy dynamic Service boundary; no unchecked cast."""
    if not isinstance(value, ServiceV1) or not isinstance(value.driver, DriverV1):
        raise ValueError("ordinary Sway requires the existing native Service methods")
    return value
