#!/usr/bin/env python3
"""Run the isolated XQOL defensive auto-call matrix without earlier UI stages."""

from __future__ import annotations

import argparse
import time

import run_acceptance as acceptance
import run_xenoamess_quality_of_life_acceptance as base
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.errors import AgentError


DEFENSE_MARKERS = (
    "ZQA: TEST BEGIN xqol_defense",
    "ZQA: TEST PASS exact_build_song_emperor",
    "ZQA: TEST PASS switched_to_supported_player",
    "ZQA: TEST PASS defense_fixture_setup",
    "ZQA: TEST PASS defense_regular_ally_called",
    "ZQA: TEST PASS defense_overlap_ally_called",
    "ZQA: TEST PASS defense_paid_dynasty_member_excluded",
    "ZQA: TEST PASS defense_overlap_dedup_and_replay_idempotent",
    "ZQA: TEST PASS defense_resources_not_decreased",
    "ZQA: TEST PASS defense_matrix_done",
    "ZQA: TEST DONE xqol",
)


def run_defense_scenario(
    service: GameplayBridgeService,
    stream: base.MarkerStream,
    artifacts: base.Path,
) -> dict[str, object]:
    before = service.snapshot()
    base.write_json(artifacts / "05_mcp_before_fixture.json", before)
    base.click_decision(
        service,
        "开始自动召集防御专项验收",
        "切换至宋帝并开战",
        artifacts,
        "05_initialize_defense",
        scroll_steps=-1,
    )
    stream.wait("ZQA: TEST PASS switched_to_supported_player")
    base.isolated.wait_for_gameplay_hud(artifacts)
    stream.wait("ZQA: TEST READY defense_auto_call", 30)
    base.ensure_bridge_paused(service, artifacts, "06_defense_pre_advance")
    defense_advance = base.advance_until_marker(
        service,
        stream,
        artifacts,
        "07_defense_war_advance",
        "ZQA: TEST DONE xqol",
        120,
    )
    final_snapshot = service.snapshot()
    if final_snapshot.get("paused") is not True:
        service.execute_step(
            "pause-map", expected_revision=int(final_snapshot["revision"])
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            final_snapshot = service.snapshot()
            if final_snapshot.get("paused") is True:
                break
            time.sleep(0.1)
    base.write_json(artifacts / "08_mcp_final_paused.json", final_snapshot)
    acceptance.ImageGrab.grab().save(artifacts / "08_final_paused.png")
    stream.validate()
    return {
        "mcp_first": True,
        "mcp_controlled_operations": [
            "readiness",
            "snapshot-before",
            "resume-defense-settlement",
            "pause-after-defense-settlement",
            "snapshot-final",
        ],
        "defense_advance": defense_advance,
        "fixture_engine_assertions": list(DEFENSE_MARKERS),
        "initial_snapshot_id": before.get("snapshot_id"),
        "final_snapshot_id": final_snapshot.get("snapshot_id"),
        "final_paused": final_snapshot.get("paused") is True,
    }


def main(args: argparse.Namespace) -> int:
    base.REQUIRED_MARKERS = DEFENSE_MARKERS
    base.run_scenario = run_defense_scenario
    return base.main(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--source")
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--bridge-dll")
    parser.add_argument("--bridge-injector")
    parser.add_argument("--bridge-pipe")
    try:
        raise SystemExit(main(parser.parse_args()))
    except (acceptance.RunnerError, AgentError, OSError, ValueError) as error:
        print(f"XQOL DEFENSE ACCEPTANCE FAILED: {error}")
        raise SystemExit(1)
