"""Join existing read-only military F inputs before a normal T0 save.

No query, planner action, mutation or historical-credit grant occurs here.
The caller binds files to one Root-owned process/create-time lifetime. Compact
MCP strength summaries are intentionally insufficient; pass the complete Driver
result once, expanded/normalized through the existing contract below.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from .driver import BridgeUnavailableError

from .army_commander_candidates import normalize_army_commander_candidates_v1
from .army_split_merge_observation_12004 import read_bound_current_commander
from .army_strengths_manager_shared_wire import expand_army_strengths_manager_inputs
from .army_strengths_profile_contract import validate_army_strengths_profile_coverage
from .war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1
from .war_contract import normalize_army_strengths
from .public_unit_contract import public_cunit_id
from .war_occupation_targets_contract import (
    normalize_war_occupation_targets_v1, query_war_occupation_targets_v1_step,
)

EXE_12004 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"


def _need(ok: object, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _id(value: object, name: str) -> int:
    _need(type(value) is int and 0 <= value < 2**31, name + " must be an observed full ID")
    return value


def _sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def _normal_source_receipt_sha256(binding: Mapping[str, object]) -> str:
    """Accept a neutral source pin; keep the old Robert key for Robert only."""
    neutral = binding.get("normal_source_receipt_sha256")
    legacy_robert = binding.get("normal_robert_source_receipt_sha256")
    _need(neutral is not None or legacy_robert is not None,
          "normal source receipt SHA-256 required")
    if neutral is not None:
        _need(_sha(neutral), "normal source receipt SHA-256 malformed")
    if legacy_robert is not None:
        _need(binding.get("actor_id") == 31254,
              "legacy Robert source key is valid only for Robert 31254")
        _need(_sha(legacy_robert), "legacy Robert source receipt SHA-256 malformed")
        if neutral is not None:
            _need(neutral.lower() == legacy_robert.lower(),
                  "neutral and legacy Robert source receipts differ")
    return str(neutral if neutral is not None else legacy_robert).lower()


def ready_t0_readonly_requests_12004(
    frame: Mapping[str, object], *, army_id: int, war_id: int,
) -> list[dict[str, object]]:
    """Return actual existing MCP calls; the caller executes none implicitly.

    On stale revision or a changed frame, take a new F and rebuild this list.
    Keep the complete strengths result without copying it for every consumer.
    """
    public_cunit_id(army_id, "army_id"); _id(war_id, "war_id")
    revision = frame.get("revision")
    _need(type(revision) is int and revision > 0, "fresh public revision required")
    return [
        {"tool": "ck3_query_army_strengths", "arguments": {
            "army_ids": [army_id], "expected_revision": revision,
            "ordered_refill_entry_mode": "observed_prepared",
            "ordered_besieging_entry_mode": "observed_prepared",
            "profile": "observed_history_full_v1"}},
        {"tool": "ck3_query_army_commander_candidates_v1", "arguments": {
            "army_id": army_id, "expected_revision": revision}},
        {"tool": "ck3_query_war_cash_current_resources_private_v1", "arguments": {
            "expected_revision": revision}},
        {"tool": "ck3_execute_step", "arguments": {
            "step": query_war_occupation_targets_v1_step(war_id),
            "expected_revision": revision}},
        {"tool": "ck3_take_snapshot", "arguments": {}},
    ]


def _army(frame: Mapping[str, object], army_id: int) -> Mapping[str, object]:
    rows = frame.get("player_armies")
    matches = [r for r in rows if isinstance(r, Mapping) and r.get("army_id") == army_id] if isinstance(rows, list) else []
    _need(len(matches) == 1, "selected Army is absent or ambiguous in independent F")
    return matches[0]


def _bound(packet: Mapping[str, object], frame: Mapping[str, object], name: str) -> None:
    _need(isinstance(packet, Mapping), name + " complete query is missing")
    for query_key, frame_key in (
        ("queried_snapshot_id", "snapshot_id"), ("queried_revision", "revision"),
        ("queried_native_revision", "native_revision"),
    ):
        _need(packet.get(query_key) == frame.get(frame_key) and frame.get(frame_key) is not None
              and type(packet.get(query_key)) is type(frame.get(frame_key)),
              name + " is not bound to this exact paused frame")
    for query_key, expected in (
        ("queried_episode_run_id", frame.get("episode_run_id")),
        ("queried_connection_generation", frame.get("diagnostics", {}).get("connection_generation")),
    ):
        # Older current-cash packets expose only the three revision keys.
        # Their missing epoch is covered by the explicit caller-owned receipt.
        if query_key in packet:
            _need(packet[query_key] == expected, name + " belongs to another journal lifetime")


def _frame_pair(before, after, binding, army_id, expected_province_id):
    _need(isinstance(binding, Mapping) and isinstance(binding.get("machine_id"), str)
          and bool(binding["machine_id"]), "Root source binding/machine_id required")
    _need(type(binding.get("process_creation_filetime_100ns")) is int
          and binding["process_creation_filetime_100ns"] > 0, "Root process creation-time receipt required")
    _need(binding.get("game_version") == "1.20.0.4"
          and str(binding.get("executable_sha256", "")).lower() == EXE_12004,
          "exact actual4 source binding required")
    _id(binding.get("actor_id"), "Root-bound actor_id")
    _need(all(type(binding.get(k)) is int and binding[k] > 0 for k in ("pid", "connection_generation"))
          and isinstance(binding.get("episode_run_id"), str) and bool(binding["episode_run_id"]),
          "positive Root PID/generation and episode required")
    _normal_source_receipt_sha256(binding)
    _need(isinstance(binding.get("director_scope_revision"), str) and bool(binding["director_scope_revision"]),
          "normal source/director scope revision required")
    for f in (before, after):
        _need(isinstance(f, Mapping) and f.get("paused") is True and f.get("map_ready") is True,
              "independent F must remain paused/map-ready")
        _need(f.get("active_event") is None and f.get("pending_character_interaction") is None,
              "process pending event/interaction before freezing T0")
        actor = f.get("played_character", {})
        _need(isinstance(actor, Mapping) and actor.get("alive") is True and actor.get("character_id") == binding.get("actor_id"),
              "Root-bound living Robert differs")
        diag = f.get("diagnostics", {})
        _need(isinstance(diag, Mapping) and diag.get("bridge_pid") == binding.get("pid")
              and diag.get("connection_generation") == binding.get("connection_generation")
              and f.get("episode_run_id") == binding.get("episode_run_id"),
              "Root-bound process/connection/episode differs")
        a = _army(f, army_id)
        _need(a.get("source") == "native" and a.get("controllable") is True
              and a.get("owner_character_id") == binding["actor_id"], "selected native Army owner/control unavailable")
        _need(a.get("in_combat") is False and a.get("retreating") is False,
              "selected Army is in combat/retreat or unknown")
        _need(a.get("army_state") in ("regular", "sieging")
              and a.get("army_state_code") == {"regular": 1, "sieging": 3}.get(a.get("army_state")),
              "selected Army has not reached a ready land state")
        _need(a.get("route_read_status") == "complete_empty" and a.get("route_province_ids") == []
              and a.get("route_source_count") == 0, "selected Army has not independently stopped")
        _need(a.get("current_province_id") == expected_province_id, "selected Army is not at the declared T0 staging province")
    _need(before.get("date_raw") == after.get("date_raw"), "F advanced a game date")
    for k in ("revision", "native_revision"):
        _need(type(before.get(k)) is int and type(after.get(k)) is int and after[k] >= before[k], "F revision moved backwards/unknown")
    _need(all(isinstance(f.get("snapshot_id"), str) and bool(f["snapshot_id"]) for f in (before, after)),
          "F snapshot identity missing")
    first, last = _army(before, army_id), _army(after, army_id)
    _need(all(first.get(k) == last.get(k) for k in (
        "owner_character_id", "current_province_id", "army_state", "army_state_code",
        "in_combat", "retreating", "route_province_ids", "route_read_status")), "selected Army changed across read-only F")


def evaluate_episode04_ready_t0_12004(
    *, before: Mapping[str, object], after: Mapping[str, object],
    strengths: Mapping[str, object], commander: Mapping[str, object],
    cash: Mapping[str, object], occupation: Mapping[str, object],
    source_binding: Mapping[str, object], army_id: int, native_carmy_id: int,
    war_id: int, goal_province_id: int, staging_province_id: int,
    agreed_commander_id: int, checkpoint: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Require existing typed facts, retaining interval/credit/policy boundaries.

    All arguments are semantic bodies, not MCP response strings. A successful F
    is military decision readiness, not R01 closure: final goal/rest decisions,
    original campaign authority and normal save still retain their own evidence.
    No candidate ranking or assignment is performed. Unrelated armies may be in
    combat; only the explicitly selected subject is admitted to this window.
    """
    result = {"military_t0_frame_ready": False, "normal_t0_saved": False,
              "r01_research_core_closed": False, "loss_sampling_ready": False,
              "missing_inputs": [], "loss_sampling_missing_inputs": [],
              "remaining_policy_inputs": ["freeze agreed goal and surrounding land/sea/rest locations with actual native previews",
                                          "bind this F and the normal save as the chosen R01 T0"],
              "new_live_credit": False, "actual_loss_observed": False, "actual_ADD_observed": False}
    try:
        public_cunit_id(army_id, "army_id")
        _need(type(native_carmy_id) is int and -(2**31) <= native_carmy_id < 2**31 and native_carmy_id != -1,
              "native_carmy_id must retain its signed full generation")
        for name, value in (("war_id", war_id),
                            ("goal_province_id", goal_province_id), ("staging_province_id", staging_province_id),
                            ("agreed_commander_id", agreed_commander_id)):
            _id(value, name)
        _frame_pair(before, after, source_binding, army_id, staging_province_id)
        for name, packet in (("strengths", strengths), ("commander", commander), ("cash", cash), ("occupation", occupation)):
            _bound(packet, before, name)
        _need(strengths.get("accepted") is True and "army_strengths" in strengths,
              "complete Driver strength result required; compact MCP summary is insufficient")
        q = expand_army_strengths_manager_inputs(dict(strengths), detached=True)
        _need(q.get("queried_date_raw") == before["date_raw"], "strengths queried date differs")
        validate_army_strengths_profile_coverage(q, expected_profile=q["army_strengths_profile"])
        normalized = normalize_army_strengths(q["army_strengths"])
        rows = [r for r in normalized if r["army_id"] == army_id]
        _need(len(rows) == 1 and rows[0]["status"] == "available"
              and rows[0]["native_carmy_id"] == native_carmy_id, "selected complete Army/CArmy map unavailable")
        row = rows[0];roster = row.get("regiment_strengths");data = row.get("regiment_replenishment_records_v1")
        _need(isinstance(roster, list) and len(roster) == row["regiment_count"]
              and isinstance(data, list), "complete roster/full DATA required")
        ids = [r["army_regiment_id"] for r in roster]
        _need(len(ids) == len(set(ids)) and len(data) == len(ids)
              and {d["army_regiment_id"] for d in data} == set(ids), "full DATA/roster coverage differs")
        for d in data:
            _need(d["status"] == "available" and d["ready"] is True
                  and d["native_data_record_count"] == len(d["records"])
                  and all(x["status"] == "available" and x.get("chunk_army_regiment_id") == d["army_regiment_id"] for x in d["records"]),
                  "partial/unread DATA or backlink cannot be replaced by zero")
        _need(type(row.get("current_supply_raw")) is int and row.get("current_supply_scale") == 100000,
              "current stock read unavailable")
        _need(type(row.get("current_supply_capacity_raw")) is int and row.get("current_supply_capacity_scale") == 100000,
              "current stock capacity read unavailable")
        cmd = normalize_army_commander_candidates_v1(
            commander.get("army_commander_candidates"), expected_army_id=army_id,
            expected_snapshot_revision=before["native_revision"], expected_date_raw=before["date_raw"])
        _need(cmd.get("owner_character_id") == source_binding["actor_id"], "typed commander owner differs")
        assigned = read_bound_current_commander(commander, before, army_id=army_id, native_carmy_id=native_carmy_id)
        _need(assigned == agreed_commander_id, "actual commander differs from explicitly agreed current commander")
        money = normalize_war_cash_current_resources_v1(dict(cash), snapshot=before)
        _id(money.get("played_character_id"), "cash played_character_id")
        _need(set(money["active_war_ids"]) == {w["war_id"] for w in before.get("active_wars", [])},
              "cash actual war scope differs from independent F")
        _need(isinstance(money.get("current_treasury"), Mapping), "current treasury read unavailable")
        wars = [w for w in before.get("active_wars", []) if w.get("war_id") == war_id]
        _need(len(wars) == 1, "selected actual war absent/ambiguous")
        war = normalize_war_occupation_targets_v1(
            occupation.get("war_occupation_targets_v1"), expected_war_id=war_id,
            expected_actor_character_id=source_binding["actor_id"],
            expected_snapshot_revision=before["native_revision"], expected_date_raw=before["date_raw"],
            expected_player_side=wars[0].get("player_side"))
        _need(war.get("game_version") == "1.20.0.4"
              and war.get("executable_sha256") == EXE_12004, "occupation source is not actual4")
        _need(war["available"] is True and war["collection_complete"] is True,
              "independent complete actual war occupation required")
        goals = [g for g in war["rows"] if g["province_id"] == goal_province_id]
        _need(len(goals) == 1, "chosen actual war goal missing/ambiguous in occupation collection")
        _need(goals[0]["territory_side"] != war["player_side"], "chosen goal is not opposing territory in this actual war")
        result.update(military_t0_frame_ready=True, epoch=deepcopy(dict(source_binding)),
                      date_raw=before["date_raw"], source_snapshot_id=before["snapshot_id"],
                      selected_army_id=army_id, native_carmy_id=native_carmy_id, war_id=war_id,
                      staging_province_id=staging_province_id, goal_province_id=goal_province_id,
                      current_commander_id=assigned, full_regiment_ids=ids,
                      strength={k: row[k] for k in ("current_soldiers", "maximum_soldiers", "current_supply_raw", "current_supply_scale",
                                                   "current_supply_capacity_raw", "current_supply_capacity_scale")},
                      current_treasury=deepcopy(money["current_treasury"]),
                      full_DATA_count=sum(len(d["records"]) for d in data),
                      full_DATA_empty_regiment_ids=[d["army_regiment_id"] for d in data if d["native_data_record_count"] == 0])
        # Historical overwrite is recorded; it does not forbid a new retained
        # positive invocation in the next window. Existing causal selectors
        # keep their own complete-physical, parent and source-budget gates.
        fences = {}
        for family, key in (("actual_supply_callback_observations_v1", "callback_after_sequence"),
                            ("actual_loss_writer_observations_v1", "loss_after_sequence")):
            journal = row.get(family)
            if not isinstance(journal, Mapping) or journal.get("status") != "available" or journal.get("observer_installed") is not True:
                result["loss_sampling_missing_inputs"].append(family + ": installed available journal required")
            else:
                fences[key] = journal["latest_sequence"]
        clock = row.get("army_update_clock_v1")
        if not isinstance(clock, Mapping) or clock.get("ready") is not True:
            result["loss_sampling_missing_inputs"].append("army_update_clock_v1: actual clock unavailable")
        result["loss_sampling_ready"] = not result["loss_sampling_missing_inputs"]
        result["loss_observation_seed"] = {"game_version": "1.20.0.4", "executable_sha256": EXE_12004,
            **fences, "date_raw_min_exclusive": before["date_raw"],
            "clock_inputs": deepcopy(clock), "current_loss_application_inputs": deepcopy(row.get("loss_application_inputs_v1")),
            "next_date_pair_inputs": deepcopy(row.get("source_derived_next_daily_supply_frame_inputs_v1")),
            "next_successful_callback_guaranteed": False, "last_supply_188_is_interval_gate": False}
        if checkpoint is not None:
            _need(isinstance(checkpoint, Mapping), "normal save receipt body required")
            save = checkpoint.get("checkpoint", {})
            _need(isinstance(save, Mapping), "normal save is still pending/unavailable; read its result, do not resubmit")
            life = save.get("succession_lifecycle", {})
            _need(isinstance(life, Mapping), "normal save lifecycle receipt unavailable")
            result["normal_t0_saved"] = bool(
                save.get("status") == "saved" and save.get("date_raw") == before["date_raw"]
                and save.get("episode_character_id") == source_binding["actor_id"]
                and save.get("episode_run_id") == source_binding["episode_run_id"]
                and type(save.get("size")) is int and save["size"] > 0
                and _sha(save.get("sha256"))
                and life.get("lifecycle") == "ordinary_campaign_succession"
                and life.get("xar_enabled") == "xar_off")
            if not result["normal_t0_saved"]:
                result["missing_inputs"].append("normal save receipt does not bind this exact T0/actor/episode")
    except (ValueError, TypeError, KeyError, BridgeUnavailableError) as error:
        result["missing_inputs"].append(str(error))
    return result
