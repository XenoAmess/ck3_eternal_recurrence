"""Typed R19 read-only observation boundary; no endpoint, ledger or action IO."""
from __future__ import annotations
from typing import Literal, Protocol, TypedDict


class GhwSceneBinding(TypedDict):
    native_revision: int
    connection_generation: int
    game_pid: int
    played_character_id: int
    date_raw: int
    episode_run_id: str | None


class GhwObservationClient(Protocol):
    def snapshot(self, *, require_event_free: bool = True) -> object: ...

    def execute_plan(self, steps: list[dict[str, object]], name: str,
                     timeout: float | None = None, reserve: int = 90) -> object: ...


DecisionsWindowRoute = Literal["census_unavailable_no_open", "reused_current_visible_readonly",
    "observed_hidden_original_once_opener"]


class GhwObservationBase(TypedDict):
    schema: str
    machine_id: str
    run_id: str
    scope: str
    receipts: dict[str, dict[str, object]]
    errors: dict[str, str]
    launch_confirm_submissions: int
    war_commands_submitted: int
    calendar_countdown_qualified: bool
    target_legality_observed: bool
    director_slot25_complete: bool
    pilgrimage_completion_inferred: bool
    current_group_qualified: bool
    automatic_retry: bool


class GhwObservation(GhwObservationBase, total=False):
    decisions_window_route: DecisionsWindowRoute
    actual_launch_row: dict[str, object] | None
    launch_row_classification: str
    actual_selected_launch_detail: dict[str, object]
    selected_detail_proofs_qualified: bool
    target_condition_policy: str
    religion_before: dict[str, object] | None
    religion_after: dict[str, object] | None
    governance_before: dict[str, object] | None
    governance_after: dict[str, object] | None
    pilgrimage_identities: dict[str, object] | None
    first_ghw: dict[str, object] | None
    second_ghw: dict[str, object] | None
    capture_epoch_is_snapshot_revision: bool
    missing_variable_is_false: bool
    no_ghw_is_world_peace: bool
    independent_final_snapshot: object
    post_event_invalidates_group_comparison: bool


def ghw_object(value: object, description: str) -> dict[str, object]:
    """One checked JSON-object boundary; no implicit bool/int or key coercion."""
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(description + " must be a string-keyed object")
    return {key: item for key, item in value.items()}


def ghw_scene_binding(value: object) -> GhwSceneBinding:
    fields = ghw_object(value, "GHW scene binding")

    def positive(name: str) -> int:
        number = fields.get(name)
        if type(number) is not int or number <= 0:
            raise ValueError("GHW scene binding needs a positive integer " + name)
        return number

    date = fields.get("date_raw")
    run = fields.get("episode_run_id")
    if type(date) is not int or not -(1 << 31) <= date < (1 << 31):
        raise ValueError("GHW scene date must be an actual signed32 integer")
    if "episode_run_id" not in fields or (run is not None and not isinstance(run, str)):
        raise ValueError("GHW scene episode identity must be an explicit string or null")
    return {"native_revision": positive("native_revision"),
        "connection_generation": positive("connection_generation"), "game_pid": positive("game_pid"),
        "played_character_id": positive("played_character_id"), "date_raw": date, "episode_run_id": run}


def ghw_decisions_visible(value: object) -> bool:
    """Admit only the current typed, complete, unique Decisions root."""
    tree = ghw_object(value, "GHW Decisions census")
    if (tree.get("schema") != "ck3-native-gui-window-tree-inspection-v1"
            or tree.get("read_only") is not True or tree.get("window_kind") != "decisions"
            or tree.get("scope_root_name") != "decisions_view"
            or tree.get("root_available") is not True or tree.get("truncated") is not False):
        raise ValueError("GHW Decisions census lacks a complete current root; no opener retry")
    widgets = tree.get("widgets")
    if not isinstance(widgets, list):
        raise ValueError("GHW Decisions census rows are absent")
    roots = [node for node in widgets if isinstance(node, dict) and node.get("child_path") == ""]
    if len(roots) != 1 or roots[0].get("runtime_name") != "decisions_view":
        raise ValueError("GHW actual Decisions root is unverified")
    visible = roots[0].get("effective_visible")
    if type(visible) is not bool:
        raise ValueError("GHW Decisions visibility is unknown; no opener retry")
    return visible

