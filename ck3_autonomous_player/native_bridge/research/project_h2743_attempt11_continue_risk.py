"""Project the immutable H2743 attempt-11 paused siege timer, without CK3 IO."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


SOURCE_ROOT = Path("D:/ck3-research-artifacts/war31-h2743-20260928/attempt-11-dejure-baseline-no-launch/live-dejure-readonly-v3")
RESULT_SHA = "647D0A2804E6F5E7F6402813332E40885578496E8474129FFC52A45F47B00F8D"
WAR_ID = 16777231
PLAYER_ID = 29829
SIEGE_PROVINCE_ID = 2628


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def project(result: dict[str, object], snapshot: dict[str, object], source_sha: str) -> dict[str, object]:
    from xar_autoplayer.formal_defender_continue_risk_v1 import observe_defender_continue_risk_v1

    if (result.get("status") != "baseline_only_material_unavailable"
            or result.get("cleanup_proven") is not True
            or result.get("gameplay_action_submitted") is not False
            or result.get("before_snapshot_sha256") != source_sha
            or result.get("war_id") != WAR_ID):
        raise ValueError("attempt-11 cleaned read-only result or before-snapshot hash missing")
    frame = result.get("frame")
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    if (not isinstance(frame, dict) or not isinstance(diagnostics, dict)
            or not isinstance(played, dict) or played.get("character_id") != PLAYER_ID
            or {key: snapshot.get(key) for key in (
                "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
                != {key: frame.get(key) for key in (
                    "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
            or diagnostics.get("connection_generation") != frame.get("connection_generation")):
        raise ValueError("snapshot differs from the cleaned H2743 paused frame")
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        raise ValueError("active wars absent")
    matching = [war for war in wars if isinstance(war, dict) and war.get("war_id") == WAR_ID]
    if len(matching) != 1:
        raise ValueError("H2743 war missing or duplicated")
    war = matching[0]
    if (war.get("player_side") != "defender" or war.get("player_is_primary_war_leader") is not True
            or war.get("primary_opponent_character_id") != 30097
            or type(war.get("player_relative_war_score")) is not int):
        raise ValueError("H2743 defender identity or score changed")
    risk_frame = {**frame, "played_character_id": PLAYER_ID, "war_id": WAR_ID,
                  "player_relative_war_score": war["player_relative_war_score"]}
    armies = war.get("enemy_armies")
    if not isinstance(armies, list):
        raise ValueError("enemy army list missing")
    siegers = [army for army in armies if isinstance(army, dict)
               and army.get("current_province_id") == SIEGE_PROVINCE_ID
               and army.get("army_state") == "sieging"
               and army.get("siege_province_in_player_subrealm") is True]
    if len(siegers) != 1 or type(siegers[0].get("siege_days_left")) is not int:
        raise ValueError("exact current siege clock unavailable")
    siege = {"source_frame": risk_frame, "source_sha256": source_sha,
             "province_id": SIEGE_PROVINCE_ID,
             "besieging_army_ids": [siegers[0]["army_id"]],
             "remaining_days_estimate": siegers[0]["siege_days_left"]}
    observation = observe_defender_continue_risk_v1(frame=risk_frame, siege=siege)
    if (observation["material_comparison_ready"] is not False
            or observation["recommended_outcome"] is not None
            or observation["action_literal"] is not None):
        raise ValueError("partial continuation observation unexpectedly authorized exit")
    return {"schema": "xar.ck3.h2743.attempt11-continue-risk-projection.v1",
            "result_sha256": RESULT_SHA, "before_snapshot_sha256": source_sha,
            "observation": observation, "gameplay_action_submitted": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result_path = SOURCE_ROOT / "read-only-result.json"
    before_path = SOURCE_ROOT / "before-payload.json"
    if sha256(result_path) != RESULT_SHA:
        raise SystemExit("exact attempt-11 result changed")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    source_sha = sha256(before_path)
    snapshot = json.loads(before_path.read_text(encoding="utf-8"))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    receipt = project(result, snapshot, source_sha)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": sha256(args.output),
                      "status": receipt["observation"]["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
