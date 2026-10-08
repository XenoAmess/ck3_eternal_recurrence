"""Source-prepared sole consumer for Root's fresh whole siege fixture packets.

Run once after the native whole producer. No game transport or old GREEN is used.
The arrived-subject scenes are synthetic, not a prediction of R76 army movement.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.war_occupation_targets_contract import (
        QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY,
        normalize_war_occupation_targets_v1,
        query_war_occupation_targets_v1_step,
    )
    from xar_autoplayer.bridge.war_contract import normalize_objective_province_states
    from xar_autoplayer.strategy import _current_exact_siege_status, _rank_exact_objectives

    subject = {"army_id": 218104048, "controllable": True,
               "current_province_id": 2608, "move_target_province_id": None,
               "route_province_ids": []}

    class Replay(NativeHeadlessGameplayDriver):
        def __init__(self, packet: dict[str, object]):
            self.packet = deepcopy(packet)
            envelope = packet["result"]
            value = envelope["war_occupation_targets_v1"]
            self.frame = {
                "paused": True, "map_ready": True, "revision": 3,
                "native_revision": envelope["snapshot_revision"], "snapshot_id": "native:2",
                "date_raw": envelope["date_raw"], "episode_run_id": "siege-selection-whole-fixture",
                "diagnostics": {"connection_generation": 1},
                "played_character": {"character_id": 29829, "alive": True},
                "player_armies": [deepcopy(subject)],
                "active_wars": [{"war_id": value["war_id"], "player_side": "attacker"}],
            }
            self.endpoint = self.state = self
            self._request_sequence = 0
            self.command_timeout_seconds = 1.0
            self.requests: list[dict[str, object]] = []

        def take_snapshot(self):
            return deepcopy(self.frame)

        def capabilities(self):
            return {"bridge_capabilities": [QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY],
                    "action_steps": _action_steps([QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY],
                        active_wars=self.frame["active_wars"], paused=True),
                    "backend_id": "native-headless"}

        def send(self, request):
            self.requests.append(deepcopy(request))

        def wait_for_command_result(self, request_id, timeout):
            packet = deepcopy(self.packet)
            packet["request_id"] = request_id
            return packet

        def _record_command(self, step, *, ok, result=None, error=None):
            pass

    async def consume():
        reports = []
        scenes = ("foreign_leader_own_eligible", "foreign_leader_own_excluded",
                  "no_selected_army", "selection_unavailable")
        for scene in scenes:
            path = args.native_dir / f"{scene}.json"
            packet = json.loads(path.read_text(encoding="utf-8-sig"))
            envelope = packet["result"]
            expected = normalize_war_occupation_targets_v1(
                envelope["war_occupation_targets_v1"], expected_war_id=100663329,
                expected_actor_character_id=29829,
                expected_snapshot_revision=envelope["snapshot_revision"],
                expected_date_raw=envelope["date_raw"], expected_player_side="attacker")
            replay = Replay(packet)
            response = await create_server(replay).call_tool(
                "ck3_query_war_occupation_targets_v1", {"war_id": 100663329, "expected_revision": 3})
            require(getattr(response, "is_error", False) is False, "registered existing siege MCP failed")
            observed = response.structured_content
            require(observed["war_occupation_targets_v1"] == expected,
                    "production driver, service and registered MCP lost the selection observation")
            require(len(replay.requests) == 1 and replay.requests[0]["step"] ==
                    query_war_occupation_targets_v1_step(100663329), "whole scene submitted extra reads")
            rows = expected["rows"]
            states = normalize_objective_province_states(rows, objective_province_ids=[2606, 2608])
            by_id = {row["province_id"]: row for row in states}
            current = by_id[2608]
            siege = current["active_siege"]
            require(siege["current_work"]["raw"] == 0 and siege["total_work"]["raw"] == 51353725
                    and siege["remaining_work"]["raw"] == 51353725,
                    "zero current work was confused with total or remaining work")
            require(siege["player_army_besieging"] is False,
                    "fixture replaced foreign stored leadership with player leadership")
            status = _current_exact_siege_status(
                {"war_objective_siege_progress_supported": True,
                 "war_objective_garrison_supported": True},
                tactical_war_id=100663329, province_id=2608,
                objective_state_by_id=by_id, commands=[], subject_army=deepcopy(subject))
            selection = current["current_besieging_army_selection"]
            if scene == "foreign_leader_own_eligible":
                require(selection == {"native_carmy_id": 352321570,
                                      "public_unit_id": 335544362, "controllable": False},
                        "native CArmy and public CUnit identities were conflated")
                require(status["status"] == "progressing" and
                        status["subject_contribution"]["native_carmy_id"] == 67109093 and
                        status["subject_contribution"]["matches_current_selection"] is False,
                        "ordinary consumer rejected native eligible contribution solely on foreign leadership")
            elif scene == "foreign_leader_own_excluded":
                require(status["status"] == "not_player_besieging" and
                        status["subject_contribution"]["status"] == "excluded",
                        "native exclusion was incorrectly admitted as eligible contribution")
            elif scene == "no_selected_army":
                require(selection == {"native_carmy_id": None, "public_unit_id": None,
                                      "controllable": False}, "native-1 empty result became failed read")
            else:
                require(selection is None and status["subject_contribution"]["status"] == "eligible",
                        "failed selection read erased independently measured qualification")
            ranked = _rank_exact_objectives([2608, 2606], by_id,
                fort_supported=True, garrison_supported=True)
            require(ranked == [2606, 2608], "existing measured fort/garrison target order changed")
            reports.append({"scene": scene, "packet": str(path), "status": "PASS",
                            "selection": selection, "ordinary_consumer": status,
                            "existing_objective_rank": ranked})
        return reports

    try:
        report = {"status": "PASS", "readiness": "fixture-live", "cases": asyncio.run(consume()),
                  "game_operations": 0, "sdk_calls_to_game": 0,
                  "actual_future_selection_observed": False, "old_GREEN_replayed": False}
    except Exception as error:
        report = {"status": "FAIL", "classification": "whole-fixture-or-consumer",
                  "error": f"{type(error).__name__}: {error}", "game_operations": 0,
                  "sdk_calls_to_game": 0, "actual_future_selection_observed": False}
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
