"""Root-only consumer of the unique complete actual4 retained-terminal packets.

The producer supplies every native field. Only request_id is correlated, as on
the real transport. This tool has not been imported or executed by its author.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))

from xar_autoplayer.bridge.active_scheme_sway_completion_private_transport import (
    normalize_active_scheme_sway_completion_v1,
    query_active_scheme_sway_completion_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004


class WholePacketDriver:
    allow_private_active_scheme_sway_completion_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        native = packet["result"]["sway_completion"]
        self.snapshot = {
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"] + 1,
            "native_revision": native["snapshot_revision"],
            "date_raw": native["date_raw"], "paused": True, "map_ready": True,
            "played_character": {"character_id": native["actor_character_id"], "alive": True},
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def run(directory: Path) -> dict[str, object]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8-sig"))
    check(manifest["native_packets"] == ["current.json", "terminated.json", "reused.json", "purged.json"],
          "consume this unique whole-producer FIRST")
    check(manifest["stale_handler_rejected"] is True and manifest["command_submissions"] == 0,
          "producer exercised the real stale handler and submitted no game commands")
    observations = {}
    for name in manifest["native_packets"]:
        packet = json.loads((directory / name).read_text(encoding="utf-8-sig"))
        native = packet["result"]["sway_completion"]
        check(native["build_version"] == CK3_12004.game_version
              and native["executable_sha256"] == CK3_12004.executable_sha256
              and native["adapter_id"] == "ck3-1.20.0.4-msvc-x64",
              "complete production renderer published actual4 identity")
        driver = WholePacketDriver(packet)
        value = query_active_scheme_sway_completion_private_v1(
            driver, expected_revision=driver.snapshot["revision"],
            target_character_id=34333, scheme_instance_id=134217986,
        )
        check({key: value[key] for key in native} == native,
              "existing production consumer preserved every native field")
        check(value["scheme_instance_generation"] == 8
              and value["actor_character_id"] == 29829 and value["target_character_id"] == 34333
              and value["scheme_instance_id"] == 134217986,
              "complete original instance/player identity survived the transport")
        check(len(driver.sent) == 1
              and driver.sent[0]["step"] == "query-sway-completion-v1-private"
              and driver.sent[0]["expected_revision"] == native["snapshot_revision"],
              "public revision was converted to the exact native revision")
        check(value["native_success_chance_observed"] is False
              and value["native_success_chance_raw"] is None
              and value["native_can_continue_observed"] is False
              and value["native_can_continue"] is None
              and value["terminal_cause_observed"] is False
              and value["terminal_cause"] == "unknown",
              "no unmapped roll input or invented terminal cause")
        observations[name] = value
    check(observations["current.json"]["instance_present"] is True
          and observations["current.json"]["native_status_raw"] == 0
          and observations["current.json"]["native_terminal_state_observed"] is False,
          "current row remains current")
    terminal = observations["terminated.json"]
    check(terminal["native_status_raw"] == 1 and terminal["owner_cleared"] is True
          and terminal["exact_instance_join_ready"] is True
          and terminal["native_status_key"] == "terminated_unattributed"
          and terminal["native_terminal_state_observed"] is True,
          "only a matched retained status1 row publishes unattributed terminal")
    check(observations["reused.json"]["storage_slot_reused"] is True,
          "replacement generation is observed")
    for name in ("reused.json", "purged.json"):
        check(observations[name]["instance_present"] is False
              and observations[name]["native_terminal_state_observed"] is False,
              "absence or replacement cannot prove completion")
    terminal_packet = json.loads((directory / "terminated.json").read_text(encoding="utf-8-sig"))
    wrong_frame = deepcopy(WholePacketDriver(terminal_packet).snapshot)
    wrong_frame["native_revision"] += 1
    try:
        normalize_active_scheme_sway_completion_v1(
            terminal_packet["result"]["sway_completion"], snapshot=wrong_frame,
            target_character_id=34333, scheme_instance_id=134217986,
        )
    except ValueError as error:
        check("exact instance/player frame" in str(error),
              "stale rejection belongs to the actual frame comparison")
        stale_consumer_rejected = True
    else:
        raise AssertionError("consumer must reject a packet from a previous native frame")
    return {
        "status": "GREEN", "qualification": "Unique offline whole-producer/consumer FIRST; not live",
        "whole_native_packets": len(observations), "compound_cases": 1,
        "producer_stale_handler_rejected": True,
        "consumer_stale_native_frame_rejected": stale_consumer_rejected,
        "semantic_terminal": "terminated_unattributed", "cause_observed": False,
        "game_sdk_commands": 0, "source_packets": str(directory),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.packets)
        code = 0
    except Exception as error:
        result = {"status": "RED", "qualification": "Offline FIRST", "error": str(error)}
        code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
