"""Summarize existing CASE-W JSON receipts; never contact CK3 or rewrite inputs.

This extractor proves only equality, identity and changes present in supplied
public snapshots. Route submission is separate from observed province progress.
It does not recover native candidate scores, reinforcement policy or causality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal


FRAME_KEYS = ("snapshot_id", "revision", "native_revision", "date_raw", "paused")
ARMY_KEYS = ("army_id", "owner_character_id", "controllable", "current_province_id",
             "move_target_province_id", "move_target_observable", "route_province_ids",
             "army_state", "army_state_code", "in_combat", "retreating", "soldiers")
POWER_KEYS = ("distance_raw", "actor_power_base_raw", "actor_network_contribution_raw",
              "actor_power_total_raw", "target_power_base_raw", "target_network_contribution_raw",
              "target_pre_adjustment_total_raw", "target_adjustment_delta_raw",
              "target_power_total_raw", "actual_power_ratio_raw")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def frame(snapshot: dict) -> dict:
    return {key: snapshot.get(key) for key in FRAME_KEYS}


def identity(snapshot: dict) -> dict:
    diagnostics = snapshot.get("diagnostics", {})
    return {
        "actor_character_id": snapshot.get("played_character", {}).get("character_id"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
    }


def army_events(previous: dict | None, current: dict, *, before: dict | None, after: dict) -> list[dict]:
    """Compare the same visible full public CUnit and owner; no successor guessing."""
    common = {"public_cunit_id": current["army_id"],
              "owner_character_id": current["owner_character_id"],
              "before": before, "after": after}
    if previous is None:
        return [{**common, "kind": "public_enemy_row_appeared", "current": current}]
    require((previous["army_id"], previous["owner_character_id"]) ==
            (current["army_id"], current["owner_character_id"]), "unit/owner identity changed")
    events = []
    if previous.get("army_state") != current.get("army_state"):
        events.append({**common, "kind": "state_changed",
                       "from": previous.get("army_state"), "to": current.get("army_state")})
    route_keys = ("move_target_province_id", "route_province_ids", "move_target_observable")
    if any(previous.get(key) != current.get(key) for key in route_keys):
        events.append({**common, "kind": "route_fields_changed",
                       "from": {key: previous.get(key) for key in route_keys},
                       "to": {key: current.get(key) for key in route_keys},
                       "current_province_changed": previous.get("current_province_id") != current.get("current_province_id")})
    old_province, new_province = previous.get("current_province_id"), current.get("current_province_id")
    if old_province is not None and new_province is not None and old_province != new_province:
        on_route = new_province in (previous.get("route_province_ids") or [])
        events.append({**common, "kind": "province_changed",
                       "from": old_province, "to": new_province,
                       "new_province_in_previous_remaining_route": on_route,
                       "evidence_scope": "observed public location change; no target-score or movement-reason inference"})
    return events


def extract(case_dir: Path, responses_dir: Path, run_identity_path: Path,
            war_id: int, end_receipt_path: Path | None = None,
            last_response_sequence: int | None = None,
            extra_evidence_paths: tuple[Path, ...] = ()) -> dict:
    sources = {}

    def load(path: Path):
        path = path.resolve()
        data = path.read_bytes()
        sources[str(path)] = {"path": str(path), "bytes": len(data),
                              "sha256": hashlib.sha256(data).hexdigest()}
        return json.loads(data)

    run_identity = load(run_identity_path)
    run_ids = [row["run_id"] for row in run_identity["identities"]]
    require(len(run_ids) == 1, "exactly one official run identity is required")
    preparation = load(case_dir / "preparation.json")
    baseline = preparation["after"]
    binding = identity(baseline)
    require(all(value is not None for value in binding.values()), "baseline session identity incomplete")
    base_date = baseline["date_raw"]
    points = []

    def add_snapshot(snapshot: dict, path: Path, pointer: str, at=None):
        require(identity(snapshot) == binding, f"cross-session snapshot: {path.name}{pointer}")
        require(snapshot.get("map_ready") is True, f"not a map snapshot: {path.name}{pointer}")
        if snapshot.get("paused") is not True:
            return
        wars = [war for war in snapshot.get("active_wars", []) if war.get("war_id") == war_id]
        require(len(wars) <= 1, "duplicate WarID in public snapshot")
        war = wars[0] if wars else None
        points.append({"source": str(path.resolve()), "json_pointer": pointer, "at": at,
                       **frame(snapshot), "days_after_baseline": str(Decimal(snapshot["date_raw"]-base_date)/24),
                       "war_present": war is not None,
                       "war": None if war is None else {key: war.get(key) for key in (
                           "war_id", "player_side", "primary_opponent_character_id",
                           "war_objective_province_ids", "player_relative_war_score", "objective_province_states")},
                       "enemy_armies": [] if war is None else [
                           {key: row.get(key) for key in ARMY_KEYS} for row in war.get("enemy_armies", [])],
                       "allied_armies": [] if war is None else [
                           {key: row.get(key) for key in ARMY_KEYS} for row in war.get("allied_armies", [])]})

    add_snapshot(baseline, case_dir / "preparation.json", "/after", preparation.get("at"))
    operations = []
    for stem in ("declaration", "raise", "move"):
        path = case_dir / f"{stem}-result.json"
        if path.is_file():
            obj = load(path)
            operations.append({"kind": f"operator_{stem}", "source": str(path.resolve()),
                               "response": obj["response"], "snapshot": frame(obj["snapshot"])})
            add_snapshot(obj["snapshot"], path, "/snapshot")
        intent = case_dir / f"{stem}-intent.json"
        if intent.is_file():
            load(intent)

    assessment_path = case_dir / "assessment-result.json"
    assessment = load(assessment_path)
    require(identity(assessment["snapshot"]) == binding, "assessment snapshot is from another session")
    query = assessment["result"]
    assessment_frame = assessment["snapshot"]
    for key in ("snapshot_id", "revision", "native_revision"):
        require(query.get("queried_"+key) == assessment_frame[key], "strategic assessment frame mismatch")
    strategic = query["war_entry_assessments"]
    require(strategic["actor_character_id"] == binding["actor_character_id"]
            and strategic["date_raw"] == assessment_frame["date_raw"], "strategic assessment identity/date mismatch")
    strategic_rows = [{"raw": row,
                       "q100000_display": {key: str(Decimal(row[key])/100000) for key in POWER_KEYS}}
                      for row in strategic["assessments"]]

    advances = []
    for path in sorted(case_dir.glob("advance-*.json")):
        obj = load(path)
        add_snapshot(obj["start"], path, "/start", obj.get("at"))
        add_snapshot(obj["end"], path, "/end", obj.get("at"))
        advances.append({"source": str(path.resolve()), "requested_days": obj["requested_days"],
                         "observed_date_delta": obj["end"]["date_raw"]-obj["start"]["date_raw"],
                         "reason": obj.get("reason"), "start": frame(obj["start"]), "end": frame(obj["end"])})

    narrow = []
    projection_differences = []
    for path in sorted(case_dir.glob("enemy-observation-*.json")):
        obj = load(path)
        snapshot = obj["snapshot"]
        add_snapshot(snapshot, path, "/snapshot", obj.get("at"))
        for name in ("strength", "assignment"):
            query = obj[name]
            for key in ("snapshot_id", "revision", "native_revision"):
                require(query.get("queried_"+key) == snapshot[key], f"{name} frame mismatch: {path.name}")
        narrow.append({"source": str(path.resolve()), "snapshot": frame(snapshot),
                       "strength": obj["strength"], "assignment": obj["assignment"]})
        assignment = obj["assignment"]
        if assignment.get("status") == "available" and isinstance(assignment.get("route"), dict):
            selected = assignment.get("selected_public_cunit_id")
            rows = [row for war in snapshot.get("active_wars", []) if war.get("war_id") == war_id
                    for row in war.get("enemy_armies", []) if row.get("army_id") == selected]
            require(len(rows) == 1, "available narrow result lacks unique same-war enemy row")
            for key in ("current_province_id", "move_target_province_id", "route_province_ids"):
                if rows[0].get(key) != assignment["route"].get(key):
                    projection_differences.append({"source": str(path.resolve()), "snapshot": frame(snapshot),
                                                   "public_cunit_id": selected, "field": key,
                                                   "snapshot_value": rows[0].get(key),
                                                   "narrow_value": assignment["route"].get(key),
                                                   "narrow_ready": assignment.get("battle_reinforcement_assignment_ready"),
                                                   "resolution": "unresolved; values retained without reconciliation"})

    formal_responses = []
    for path in sorted(responses_dir.glob("w*.json")):
        number = path.name.split("-", 1)[0][1:]
        if not number.isdigit():
            continue
        if last_response_sequence is not None and int(number) > last_response_sequence:
            continue
        obj = load(path)
        body = obj.get("body")
        formal_responses.append({"source": str(path.resolve()), "at": obj.get("at"),
                                 "result": obj.get("result"), "step": body.get("step") if isinstance(body, dict) else None,
                                 "status": body.get("status") if isinstance(body, dict) else None,
                                 "error": obj.get("error")})
        if path.name.endswith("-take_snapshot.json") and isinstance(body, dict):
            add_snapshot(body, path, "/body", obj.get("at"))

    # A public revision identifies the published sample. Query caches can differ
    # while the military projection remains identical; retain all source refs.
    samples = {}
    for point in points:
        key = (point["snapshot_id"], point["revision"], point["native_revision"], point["date_raw"])
        ref = {key: point[key] for key in ("source", "json_pointer", "at")}
        projection = {key: value for key, value in point.items() if key not in ref}
        if key in samples:
            require(samples[key]["projection"] == projection, "same published frame has conflicting army projection")
            samples[key]["sources"].append(ref)
        else:
            samples[key] = {"projection": projection, "sources": [ref]}
    ordered = sorted(samples.values(), key=lambda item: (item["projection"]["date_raw"], item["projection"]["revision"]))
    previous = {}
    previous_frame = None
    events = []
    owners = set()
    for sample in ordered:
        point = sample["projection"]
        current = {}
        for row in point["enemy_armies"]:
            require(row["controllable"] is False, "enemy row unexpectedly player-controllable")
            key = (row["army_id"], row["owner_character_id"])
            require(key not in current, "duplicate public enemy unit/owner")
            current[key] = row
            owners.add(row["owner_character_id"])
            events.extend(army_events(previous.get(key), row, before=previous_frame,
                                     after={**frame(point), "sources": sample["sources"]}))
        previous = current
        previous_frame = {**frame(point), "sources": sample["sources"]}

    ending = load(end_receipt_path) if end_receipt_path else None
    if ending is not None:
        last_date = ending["final_observed_date_raw"]
        require(all(sample["projection"]["date_raw"] <= last_date for sample in ordered),
                "sample extends past the declared CASE-W observation window")
        require(ordered[-1]["projection"]["date_raw"] == last_date, "final observation date missing")
    extra_evidence = [{"source": str(path.resolve()), "receipt": load(path)} for path in extra_evidence_paths]
    return {
        "schema": "ck3-war-film.case-w-existing-readback.v1",
        "created_at": datetime.now(timezone.utc).isoformat(), "run_id": run_ids[0],
        "status": "existing-files-extracted", "run_end_receipt_supplied": ending is not None,
        "evidence_scope": "JSON receipt projection only; no game access or inferred decision policy",
        "binding": binding, "baseline_date_raw": base_date, "war_id": war_id,
        "operator_interventions": operations, "strategic_assessment": {
            "source": str(assessment_path.resolve()), "frame": frame(assessment_frame),
            "status": strategic["status"], "readiness": strategic["readiness"], "rows": strategic_rows},
        "advances": advances, "samples": ordered, "enemy_events": events,
        "enemy_owner_ids_observed_in_public_rows": sorted(owners), "narrow_queries": narrow,
        "projection_differences": projection_differences,
        "formal_responses": formal_responses, "last_response_sequence": last_response_sequence,
        "end_receipt": ending, "extra_evidence": extra_evidence,
        "nonclaims": ["natural NPC declaration", "reason for ally/participant entry",
                      "target scoring or objective-selection cause", "movement progress from route fields alone",
                      "ordinary reinforcement request-to-assignment chain", "battle or peace result without its own observation",
                      "frame-synchronous video", "human review or film readiness"],
        "sources": list(sources.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--responses-dir", type=Path, required=True)
    parser.add_argument("--run-identity", type=Path, required=True)
    parser.add_argument("--war-id", type=int, required=True)
    parser.add_argument("--end-receipt", type=Path)
    parser.add_argument("--last-response-sequence", type=int)
    parser.add_argument("--extra-evidence", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output_dir.exists(), "output directory already exists; use a new attempt")
    result = extract(args.case_dir, args.responses_dir, args.run_identity,
                     args.war_id, args.end_receipt, args.last_response_sequence,
                     tuple(args.extra_evidence))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / "result.json").open("xb") as stream:
        stream.write((json.dumps(result, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
    print(json.dumps({"output": str(args.output_dir / "result.json"), "status": result["status"],
                      "samples": len(result["samples"]), "events": len(result["enemy_events"])}))


if __name__ == "__main__":
    main()
