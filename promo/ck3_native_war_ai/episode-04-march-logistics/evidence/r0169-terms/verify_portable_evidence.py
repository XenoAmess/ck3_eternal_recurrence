"""Offline R0169 evidence verification; never opens external media or CK3."""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), f"expected JSON object: {path.name}")
    return value


def body(packet: dict) -> dict:
    value = packet.get("body", packet)
    require(isinstance(value, dict), "packet body malformed")
    if "is_error" in packet:
        require(packet["is_error"] is False, "actual packet contains tool error")
    return value


def validate_encoded(candidate: dict, review: dict, index: dict) -> int:
    flattened = [(group["label"], frame) for group in candidate["results"] for frame in group["candidates"]]
    require(len(flattened) == 24 and len(review["frames"]) == 8, "actual candidate/review counts changed")
    seen = set()
    for reviewed in review["frames"]:
        matches = [(label, frame) for label, frame in flattened
                   if frame["decoded_png"]["sha256"] == reviewed["frame"]["sha256"]]
        require(len(matches) == 1, "reviewed PNG lacks unique actual extraction source")
        label, source = matches[0]
        require(label == reviewed["group"], "review group differs from extraction group")
        require(source["decoded_png"] == reviewed["frame"], "reviewed exact PNG identity changed")
        require(Decimal(source["seconds"]) == Decimal(str(reviewed["actual_encoded_pts_seconds"])), "actual PTS mismatch")
        require(reviewed["content_review"] == "directly-reviewed", "not an actual Root content review")
        require(reviewed["continuous_span_credit"] is False, "single-frame review promoted to span")
        seen.add(reviewed["frame"]["sha256"])
    require(review["unreviewed_other_candidates"] == 16, "unreviewed count changed")
    require(review["clean_spans_certified"] is False and review["human_1x_full_review"] is False and review["signoff"] is False, "review boundaries changed")
    projected = index["encoded_candidates"]
    require(len(projected) == 24, "portable candidate projection incomplete")
    require(sum(item["root_content_review"] is not None for item in projected) == 8, "portable review authority count changed")
    for item in projected:
        should_be_reviewed = item["decoded_png"]["sha256"] in seen
        require((item["root_content_review"] is not None) == should_be_reviewed, "unreviewed PNG gained content authority")
    return 8


def selected(snapshot: dict, army_id: int) -> dict:
    rows = [row for row in snapshot["player_armies"] if row["army_id"] == army_id]
    require(len(rows) == 1, "FullID not unique in fresh actual roster")
    return rows[0]


def validate_lock(snapshots: list[dict], query: dict) -> int:
    expected = (53147496, True, "native:16", 17, 16, "native-33388-06e1bad08e3a", 33388)
    for snapshot in snapshots:
        actual = (snapshot["date_raw"], snapshot["paused"], snapshot["snapshot_id"],
                  snapshot["revision"], snapshot["native_revision"], snapshot["episode_run_id"],
                  snapshot["played_character"]["character_id"])
        require(actual == expected, "locked original/native paused identity mismatch")
        army = selected(snapshot, 33554436)
        require(army["owner_character_id"] == 33388 and army["current_province_id"] == 1506,
                "locked Army owner/location mismatch")
        require(army["route_province_ids"] == [1508] and army["route_read_status"] == "complete_nonempty", "locked actual route mismatch")
    require((query["queried_snapshot_id"], query["queried_revision"], query["queried_native_revision"]) == ("native:16", 17, 16), "query frame mismatch")
    source = query["source"]
    require((source["date_raw"], source["paused"], source["snapshot_id"], source["revision"], source["native_revision"]) == expected[:5], "query source frame mismatch")
    rows = [row for row in query["army_strengths"] if row["army_id"] == 33554436]
    require(len(rows) == 1 and rows[0]["status"] == "available", "actual locked Army strength missing")
    movement = rows[0]["current_movement_progress"]
    require(movement["status"] == "available", "native progress unavailable")
    require(movement["normalized_edge_progress"] == {"raw": 61875, "scale": 100000}, "actual normalized progress changed")
    require(movement["first_route_edge_remaining_duration"] == {"raw": 308080, "scale": 100000}, "actual remaining duration changed")
    require(rows[0]["army_update_clock_v1"]["current_date_raw"] == 53147496, "clock disagrees with paused frame")
    return len(snapshots) + 1


def actual_vector(query: dict) -> dict[int, tuple[int, int]]:
    vector = {}
    for row in query["army_strengths"]:
        require(row["status"] == "available", "actual Army strength unavailable")
        actual_rows = row["regiment_strengths"]
        require(len(actual_rows) == row["regiment_count"], "actual regiment rows truncated")
        require(sum(item["current_soldiers"] for item in actual_rows) == row["current_soldiers"], "actual current SUM differs from native Army getter")
        require(sum(item["maximum_soldiers"] for item in actual_rows) == row["maximum_soldiers"], "actual max SUM differs from native Army getter")
        for item in actual_rows:
            rid = item["army_regiment_id"]
            require(rid not in vector and item["scale"] == 1, "actual FullID collision or soldier scale mismatch")
            vector[rid] = (item["current_soldiers"], item["maximum_soldiers"])
    return vector


def validate_local_b(baseline: dict, arrival: dict, before: dict, after: dict) -> int:
    old, new = actual_vector(baseline), actual_vector(arrival)
    require(len(old) == len(new) == 27 and old == new, "27 actual FullID current/max vector differs")
    require(sum(x[0] for x in new.values()) == 6746 and sum(x[1] for x in new.values()) == 6747, "actual aggregate changed")
    require(baseline["source"]["date_raw"] == 53147376, "baseline date changed")
    for snapshot in [before, after]:
        require((snapshot["date_raw"], snapshot["paused"], snapshot["snapshot_id"], snapshot["revision"], snapshot["native_revision"], snapshot["episode_run_id"]) == (53147592, True, "native:26", 27, 26, "native-33388-06e1bad08e3a"), "arrival paused bracket mismatch")
    require((arrival["queried_snapshot_id"], arrival["queried_revision"], arrival["queried_native_revision"]) == ("native:26", 27, 26), "arrival query revision mismatch")
    require(arrival["source"]["paused"] is True and arrival["source"]["date_raw"] == 53147592, "arrival query not same paused day")
    expected = {0: (3371, 3371, -438596, 30000000, 1506), 33554436: (3375, 3376, -877192, 10000000, 1508)}
    require({r["army_id"] for r in arrival["army_strengths"]} == set(expected), "arrival actual Army scope differs")
    record_count = 0
    for row in arrival["army_strengths"]:
        current, maximum, monthly, cap, location = expected[row["army_id"]]
        require((row["current_soldiers"], row["maximum_soldiers"], row["current_supply_change_monthly_raw"], row["current_supply_capacity_raw"]) == (current, maximum, monthly, cap), "arrival integer/supply inputs changed")
        require(row["current_supply_raw"] == 11651751 and monthly <= 0, "local B qualification changed")
        groups = row["regiment_replenishment_records_v1"]
        require(len(groups) == row["regiment_count"], "full DATA group scope truncated")
        require({g["army_regiment_id"] for g in groups} == {r["army_regiment_id"] for r in row["regiment_strengths"]}, "DATA group identity differs from actual Army regiments")
        for group in groups:
            require(group["status"] == "available" and group["ready"] is True and len(group["records"]) == group["native_data_record_count"], "DATA records partial or unavailable")
            record_count += len(group["records"])
        for snapshot in [before, after]:
            army = selected(snapshot, row["army_id"])
            require(army["owner_character_id"] == 33388 and army["current_province_id"] == location and army["route_province_ids"] == [], "actual stationary arrival/location mismatch")
    require(record_count == 37, "complete DATA record total changed")
    return 27


def verify(root: Path) -> dict:
    index = read_json(root / "index.json")
    for item in index["portable_files"]:
        target = (root / item["path"]).resolve()
        require(target.is_relative_to(root.resolve()), "portable path escapes evidence directory")
        raw = target.read_bytes()
        require(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], f"portable bytes/SHA mismatch: {item['path']}")
    def get(label: str) -> dict:
        return read_json(root / index["source_files"][label])
    archive = get("archived_halt_spans")
    require(archive["exe_sha256"] == index["executable_sha256_from_prior_exact_binding"], "archived native exact EXE identity changed")
    span = next(item for item in archive["spans"] if item["rva"].lower() == "0x24aa750")
    require(hashlib.sha256(bytes.fromhex(span["bytes"])).hexdigest() == span["sha256"], "bounded native span bytes/SHA differ")
    require(any("jle 0x1424aa7bb" in line for line in span["instructions"]), "strict native branch proof missing")
    require(index["native_static_lock_theorem"]["current_runtime_loaded_cutoff"] is None, "static stock value promoted to runtime loaded observation")
    for copied in index["original_source_copies"]:
        label = copied["label"]
        if copied.get("copy_mode", "original_bytes") == "metadata_projection":
            require(label == "original_locked_native_join", "unexpected evidence projection")
            projection = get(label)
            require(projection["schema"] == "xar.ck3.evidence.metadata-projection/v1", "projection schema mismatch")
            require(projection["original_source"] == copied["original"], "projection original identity differs")
            transform = projection["transform"]
            require(transform == copied["transform"] and transform["source_key_utf8_hex"] == "706f7765727368656c6c", "projection transform differs")
            require(transform["serialization"] == {"encoding": "utf-8", "ensure_ascii": False, "indent": 2, "line_ending": "CRLF", "terminal_newline": True}, "projection serializer differs")
            require(projection["native_query_and_snapshot_original_bytes_changed"] is False, "projection modifies primary native bytes")
            restored = copy.deepcopy(projection["projected_report"])
            old_key = bytes.fromhex(transform["source_key_utf8_hex"]).decode("utf-8")
            new_key = transform["target_key"]
            require(new_key == "disallowed_windows_shell_used" and restored["environment"][new_key] is False, "projection changed disabled marker value")
            restored["environment"] = {old_key if key == new_key else key: value for key, value in restored["environment"].items()}
            raw = (json.dumps(restored, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")
            require(len(raw) == copied["original"]["bytes"] and hashlib.sha256(raw).hexdigest() == copied["original"]["sha256"], "projection cannot reconstruct exact original source")
        else:
            require(copied["portable"]["bytes"] == copied["original"]["bytes"] and copied["portable"]["sha256"] == copied["original"]["sha256"], "original byte copy relabeled or changed")
    encoded = validate_encoded(get("candidate_index"), get("root_encoded_review"), index)
    snapshots = [get(label) for label in ["lock_before", "lock_after", "concept_before", "concept_after", "lock_query_before", "lock_query_after"]]
    locked = validate_lock(snapshots, get("lock_query"))
    count = validate_local_b(body(get("b_baseline")), body(get("b_arrival_query")), body(get("b_arrival_before")), body(get("b_arrival_after")))
    require(len(index["terms"]) == 11 and all(term["original_research_gate_complete"] is True for term in index["terms"]), "original TERM denominator/gates changed")
    require(sum(term["encoded_gate_complete"] is True for term in index["terms"]) == 10, "encoded TERM gate count changed")
    term08 = next(term for term in index["terms"] if term["id"] == "TERM-08")
    require(term08["new_locked_native_join_encoded"] is None, "postfinish original assigned an encoded frame")
    media, bootstrap = get("media_report"), get("bootstrap_result")
    require(media["state"] == "PASS" and media["full_human_viewing_performed"] is False and media["human_signoff"] is False, "media audit boundary changed")
    require("No space left on device" in bootstrap["screen_lease"]["failure"], "D-full failure was lost")
    require(bootstrap["sdk_thread_exited"] is True and bootstrap["session"]["shutdown"]["cleanup_proven"] is True and bootstrap["session"]["shutdown"]["job_active_processes_final"] == 0, "cleanup proof changed")
    require(index["abc_completed_runs"] == 0 and index["formal_weighted_research_percent"] is None and index["clean_spans_certified"] is False and index["full_human_1x_review"] is False and index["human_signoff"] is False, "unearned completion credit")
    return {"status": "PASS", "portable_files_verified": len(index["portable_files"]), "root_reviewed_encoded_frames": encoded, "unreviewed_encoded_frames": 16, "locked_join_snapshots_and_query": locked, "unchanged_actual_regiments": count, "original_term_gates": "11/11", "encoded_term_gates": "10/11", "external_media_opened": 0, "sdk_calls": 0, "git_calls": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
