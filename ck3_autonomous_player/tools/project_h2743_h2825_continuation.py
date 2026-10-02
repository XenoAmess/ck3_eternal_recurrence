"""Project one already completed Robert continuation without starting CK3.

This historical delta is evidence about observed risk, not an exit forecast or
a substitute for current de-jure surrender terms. All inputs are exact frozen
sources. The output path is exclusive so a retry cannot overwrite an attempt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


WAR_ID = 16777231
EXPECTED = {
    "h2743_save": "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9",
    "h2743_driver": "F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069",
    "h2825_save": "231513D308A7D62D2F9CBF354D872C9F15FF1FB2B24B2CCAFF2480CF5E14B13D",
    "h2825_driver": "B8E50A281AFB9A5DAA7AC1ED55DD68C4305816302B71B14EDF79F1060177D872",
}


def _verified_bytes(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")
    return data


def _verified_file(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest().upper() != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")


def _row(history: list[dict[str, object]], index: int) -> dict[str, object]:
    if index > len(history) or history[index - 1].get("index") != index:
        raise ValueError(f"driver history index {index} is unavailable")
    return history[index - 1]


def _options(history: list[dict[str, object]], index: int) -> dict[str, object]:
    row = _row(history, index)
    result = row.get("result")
    if row.get("command") != f"query-war-termination-options-{WAR_ID}" or row.get("ok") is not True or not isinstance(result, dict):
        raise ValueError(f"native options history row {index} is invalid")
    options = result.get("war_termination_options")
    if not isinstance(options, dict) or not (
        options.get("source") == "native"
        and options.get("war_id") == WAR_ID
        and options.get("player_side") == "defender"
        and options.get("player_is_primary_war_leader") is True
        and options.get("active_casus_belli_identity")
        == {"database_index": 17, "canonical_key": "individual_county_de_jure_cb"}
    ):
        raise ValueError(f"native options identity row {index} drifted")
    breakdown = options.get("war_score_breakdown")
    score = options.get("player_relative_war_score")
    if not isinstance(breakdown, dict) or set(breakdown) != {
        "battles", "imprisonment", "occupation", "ticking"
    } or any(
        isinstance(breakdown.get(key), bool)
        or not isinstance(breakdown.get(key), int)
        for key in ("battles", "imprisonment", "occupation", "ticking")
    ) or isinstance(score, bool) or not isinstance(score, int) or sum(breakdown.values()) != -score:
        raise ValueError(f"native options score row {index} is invalid")
    return {
        "history_index": index,
        "snapshot_id": result.get("queried_snapshot_id"),
        "player_relative_war_score": score,
        "attacker_perspective_breakdown": dict(breakdown),
    }


def _army_query(path: Path) -> dict[int, dict[str, object]]:
    query = json.loads(path.read_text(encoding="utf-8"))
    if not (
        query.get("step") == "query-army-strengths-v1"
        and query.get("accepted") is True
        and query.get("status") == "available"
        and query.get("backend_id") == "native-headless"
        and query.get("queried_snapshot_id") == "native:3"
        and query.get("queried_revision") == 4
        and query.get("queried_native_revision") == 3
    ):
        raise ValueError(f"army query frame invalid: {path}")
    armies = query.get("army_strengths")
    if not isinstance(armies, list) or len(armies) != 3:
        raise ValueError(f"army query cardinality invalid: {path}")
    rows = {row["army_id"]: row for row in armies if isinstance(row, dict) and row.get("status") == "available"}
    if set(rows) != {83886367, 50331920, 83886484}:
        raise ValueError(f"army query identity invalid: {path}")
    return rows


def _paired_snapshot(
    path: Path, *, date_raw: int, armies: dict[int, dict[str, object]]
) -> dict[str, object]:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if not (
        snapshot.get("paused") is True
        and snapshot.get("snapshot_id") == "native:3"
        and snapshot.get("revision") == 4
        and snapshot.get("native_revision") == 3
        and snapshot.get("date_raw") == date_raw
        and snapshot.get("episode_run_id") == "native-29829-2bc2d599f7f9"
        and snapshot.get("played_character", {}).get("character_id") == 29829
        and snapshot.get("army_strengths_status") == "available"
        and snapshot.get("army_strengths_queried_snapshot_id") == "native:3"
        and snapshot.get("army_strengths") == list(armies.values())
    ):
        raise ValueError(f"army query and current snapshot are not paired: {path}")
    wars = snapshot.get("active_wars")
    matching = [war for war in wars if isinstance(war, dict) and war.get("war_id") == WAR_ID] if isinstance(wars, list) else []
    expected_score = -12 if date_raw == 53217264 else -24
    if len(matching) != 1 or matching[0].get("player_relative_war_score") != expected_score:
        raise ValueError(f"active war is not bound to snapshot: {path}")
    resources = {}
    for key in ("played_character_gold", "played_character_prestige"):
        value = snapshot.get(key)
        if not isinstance(value, dict) or value.get("scale") != 100000 or isinstance(value.get("raw"), bool) or not isinstance(value.get("raw"), int):
            raise ValueError(f"current {key} is unavailable: {path}")
        resources[key] = value["raw"]
    return resources


def project(
    *, h2743_save: Path, h2743_driver: Path, h2743_armies: Path,
    h2743_snapshot: Path, h2825_save: Path, h2825_driver: Path,
    h2825_armies: Path, h2825_snapshot: Path,
) -> dict[str, object]:
    for name, path in (
        ("h2743_save", h2743_save), ("h2825_save", h2825_save)
    ):
        _verified_file(path, EXPECTED[name])
    before = json.loads(_verified_bytes(h2743_driver, EXPECTED["h2743_driver"]))
    after = json.loads(_verified_bytes(h2825_driver, EXPECTED["h2825_driver"]))
    before_history = before["command_history"]
    after_history = after["command_history"]
    if not (
        before.get("episode_run_id") == after.get("episode_run_id")
        == "native-29829-2bc2d599f7f9"
        and before["last_checkpoint"]["sha256"].upper() == EXPECTED["h2743_save"]
        and after["last_checkpoint"]["sha256"].upper() == EXPECTED["h2825_save"]
        and before["last_checkpoint"]["history_index"] == 2743
        and after["last_checkpoint"]["history_index"] == 2825
        and before_history[:2742] == after_history[:2742]
        and _row(after_history, 2744).get("command") == "restore-checkpoint"
        and _row(after_history, 2744).get("ok") is True
    ):
        raise ValueError("H2743 to H2825 source lineage is not proven")
    for row in after_history[2743:2825]:
        if isinstance(row.get("command"), str) and (
            row["command"].startswith(
                ("surrender-war-", "offer-white-peace-", "enforce-demands-")
            )
            or row["command"] == "war-enforce-demands"
        ):
            raise ValueError("a terminal war action appears in continuation")
    first = _options(after_history, 2751)
    day_one = _options(after_history, 2767)
    last = _options(after_history, 2828)
    if (first["snapshot_id"], day_one["snapshot_id"], last["snapshot_id"]) != ("native:3", "native:7", "native:40"):
        raise ValueError("native frame lineage drifted")
    advances = []
    for row in after_history[2743:2825]:
        result = row.get("result")
        if not isinstance(result, dict) or not row.get("command", "").startswith((
            "advance-route-contact-horizon-v1-", "war-objective-hold-sentinel-advance-"
        )):
            continue
        if row.get("ok") is not True or result.get("progress_status") != "postcondition":
            raise ValueError(f"continuation advance {row.get('index')} is not qualified")
        before_wars = result["war_progress_before"]["wars"]
        after_wars = result["war_progress_after"]["wars"]
        if len(before_wars) != 1 or len(after_wars) != 1 or before_wars[0]["war_id"] != WAR_ID or after_wars[0]["war_id"] != WAR_ID:
            raise ValueError("continuation WarID drifted")
        advances.append({
            "history_index": row["index"],
            "start_date_raw": result["starting_date_raw"],
            "end_date_raw": result["ending_date_raw"],
            "score_before": before_wars[0]["player_relative_war_score"],
            "score_after": after_wars[0]["player_relative_war_score"],
        })
    if not advances or advances[0]["start_date_raw"] != 53217264 or advances[-1]["end_date_raw"] != 53217624:
        raise ValueError("continuation date coverage incomplete")
    if any(left["end_date_raw"] != right["start_date_raw"] or left["score_after"] != right["score_before"] for left, right in zip(advances, advances[1:])):
        raise ValueError("continuation advances are not contiguous")
    if advances[0]["score_before"] != first["player_relative_war_score"] or advances[-1]["score_after"] != last["player_relative_war_score"]:
        raise ValueError("continuation score endpoints do not match options")
    before_armies = _army_query(h2743_armies)
    after_armies = _army_query(h2825_armies)
    before_resources = _paired_snapshot(
        h2743_snapshot, date_raw=53217264, armies=before_armies
    )
    after_resources = _paired_snapshot(
        h2825_snapshot, date_raw=53217624, armies=after_armies
    )
    army_deltas = [
        {
            "army_id": army_id,
            "before_soldiers": before_armies[army_id]["current_soldiers"],
            "after_soldiers": after_armies[army_id]["current_soldiers"],
            "net_soldier_delta": after_armies[army_id]["current_soldiers"] - before_armies[army_id]["current_soldiers"],
        }
        for army_id in (83886367, 50331920, 83886484)
    ]
    return {
        "schema": "xar.ck3.h2743-h2825-observed-continuation-delta/v1",
        "source_sha256": {
            **EXPECTED,
            **{
                name: hashlib.sha256(path.read_bytes()).hexdigest().upper()
                for name, path in (
                    ("h2743_armies", h2743_armies),
                    ("h2743_snapshot", h2743_snapshot),
                    ("h2825_armies", h2825_armies),
                    ("h2825_snapshot", h2825_snapshot),
                )
            },
        },
        "episode_run_id": before["episode_run_id"],
        "war_id": WAR_ID,
        "days_observed": (53217624 - 53217264) // 24,
        "score_samples": {"h2743": first, "day_one": day_one, "h2825": last},
        "score_delta_player_relative": last["player_relative_war_score"] - first["player_relative_war_score"],
        "occupation_score_delta_attacker_perspective": last["attacker_perspective_breakdown"]["occupation"] - first["attacker_perspective_breakdown"]["occupation"],
        "ticking_score_delta_attacker_perspective": last["attacker_perspective_breakdown"]["ticking"] - first["attacker_perspective_breakdown"]["ticking"],
        "advances": advances,
        "army_net_deltas": army_deltas,
        "observed_player_resource_net_deltas_raw_scale_100000": {
            name: {
                "before": before_resources[name],
                "after": after_resources[name],
                "net_delta": after_resources[name] - before_resources[name],
            }
            for name in ("played_character_gold", "played_character_prestige")
        },
        "scope": "observed historical continuation on the exact Robert lineage; not a future combat forecast, surrender counterfactual, or signed resource delta",
        "exit_action_submitted_in_segment": False,
        "h2743_surrender_terms_observed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("h2743_save", "h2743_driver", "h2743_armies", "h2743_snapshot", "h2825_save", "h2825_driver", "h2825_armies", "h2825_snapshot", "output"):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    args = parser.parse_args()
    result = project(**{name: getattr(args, name) for name in (
        "h2743_save", "h2743_driver", "h2743_armies", "h2743_snapshot",
        "h2825_save", "h2825_driver", "h2825_armies", "h2825_snapshot"
    )})
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
