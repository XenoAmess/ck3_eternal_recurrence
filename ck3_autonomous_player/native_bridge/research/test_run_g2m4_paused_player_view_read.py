"""Protocol-shaped tests for the owner-process-only paused player read."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_g2m4_paused_player_view_read import (
    EXACT_EXE_SHA256,
    PRIVATE_STEP,
    ROOT_STEP,
    run_owned_paused_player_view_read,
)


ACTOR_ID = 4567
REVISION = 12
DATE_RAW = 81457


def snapshot(*, war: bool = False) -> dict[str, object]:
    return {
        "snapshot_id": "paused-feudal-12",
        "native_revision": REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": ACTOR_ID, "alive": True},
        "active_wars": [{"war_id": 71}] if war else [],
        "player_armies": [],
        "active_event": None,
        "pending_character_interaction": None,
    }


def root_result(*, actor_id: int = ACTOR_ID, government: str = "feudal_government") -> dict[str, object]:
    return {
        "step": ROOT_STEP,
        "accepted": True,
        "status": "available",
        "snapshot_revision": REVISION,
        "campaign_root_context": {
            "status": "available",
            "snapshot_revision": REVISION,
            "date_raw": DATE_RAW,
            "player_character_id": actor_id,
            "player_character_alive": True,
            "government": {"key": government},
            "held_title_partition": [
                {"title": {"title_id": 900, "tier_key": "county"}, "primary": False}
            ],
            "capital_province_id": 44,
            "provenance": {"executable_sha256": EXACT_EXE_SHA256},
        },
    }


def probe_result(*, count: int = 0, visibility: str = "hidden") -> dict[str, object]:
    assert visibility in {"hidden", "visible", "unavailable"}
    return {
        "step": PRIVATE_STEP,
        "accepted": True,
        "status": "private construction cache branch observed",
        "private_probe": {
            "schema_version": 1,
            "private_key": PRIVATE_STEP,
            "advertised": False,
            "status": "view_candidate_cache_empty" if count == 0 else "view_candidate_cache_present",
            "failure": "none",
            "view_present": True,
            "candidate_capacity": max(count, 4),
            "cached_candidate_count": count,
            "snapshot_revision": REVISION,
            "date_raw": DATE_RAW,
            "holding_view_visibility": {
                "widget_key": "holding_view",
                "status": "unavailable" if visibility == "unavailable" else "available",
                "effective_visible": None if visibility == "unavailable" else visibility == "visible",
            },
            "executor_invocations": 1,
        },
    }


class FakeDriver:
    def __init__(self, frames: dict[str, dict[str, object] | None], *, war: bool = False):
        self.frames = frames
        self.sent: list[dict[str, object]] = []
        self.current_request: dict[str, object] | None = None
        self.snapshot_value = snapshot(war=war)
        self.endpoint = self
        self.state = self

    def semantic_snapshot(self) -> dict[str, object]:
        return self.snapshot_value

    def send(self, frame: dict[str, object]) -> None:
        assert frame["type"] == "execute_step"
        assert frame["protocol_version"] == 1
        assert frame["expected_revision"] == REVISION
        self.sent.append(frame)
        self.current_request = frame

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object] | None:
        assert timeout_seconds == 12.0
        assert self.current_request is not None
        assert self.current_request["request_id"] == request_id
        result = self.frames.get(str(self.current_request["step"]))
        if result is None:
            return None
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": result,
        }


def frozen() -> dict[str, object]:
    result: dict[str, object] = {
        "candidate_id": "controlled-feudal-peace",
        "round_id": "R696",
        "seed": "feudal-peace-seed",
        "source_save_path": "frozen-source.ck3",
        "source_save_sha256": "a" * 64,
        "ck3_exe_path": "ck3.exe",
        "ck3_exe_sha256": EXACT_EXE_SHA256,
        "agent_commit": "bfa2fab4",
        "native_dll_path": "xar_ck3_bridge.dll",
        "native_dll_sha256": "b" * 64,
        "dlc_mod_load_order": [],
        "configuration": {"speed": 0},
    }
    return result


class PausedPlayerReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.artifact = Path(self.temporary.name) / "result.json"

    def _run(self, driver: FakeDriver, manifest: dict[str, object]) -> dict[str, object]:
        result = run_owned_paused_player_view_read(driver, manifest, self.artifact)
        self.assertEqual(json.loads(self.artifact.read_text(encoding="utf-8")), result)
        return result

    def test_cache_present_with_same_frame_closed_view_receipt(self) -> None:
        driver = FakeDriver({ROOT_STEP: root_result(), PRIVATE_STEP: probe_result(count=3)})
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "cache_branch_observed")
        self.assertEqual(result["cache_branch"], "view_candidate_cache_present")
        self.assertTrue(result["closed_county_view_bound"])
        self.assertEqual(result["holding_view_visibility_receipt"]["widget_key"], "holding_view")
        self.assertIs(result["holding_view_visibility_receipt"]["effective_visible"], False)
        self.assertFalse(result["capital_province_holder_observed"])
        self.assertEqual([frame["step"] for frame in driver.sent], [ROOT_STEP, PRIVATE_STEP])

    def test_empty_cache_with_unreadable_gui_flags_is_not_no_legal_building(self) -> None:
        driver = FakeDriver({
            ROOT_STEP: root_result(),
            PRIVATE_STEP: probe_result(visibility="unavailable"),
        })
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "closed_view_evidence_insufficient")
        self.assertEqual(result["cache_branch"], "view_candidate_cache_empty")
        self.assertEqual(result["next_read"], "player_model_holding_enumerator")
        self.assertIsNone(result["holding_view_visibility_receipt"]["effective_visible"])

    def test_visible_holding_view_is_an_open_scene_not_closed_view_green(self) -> None:
        driver = FakeDriver({
            ROOT_STEP: root_result(),
            PRIVATE_STEP: probe_result(count=2, visibility="visible"),
        })
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "open_view_scene")
        self.assertFalse(result["closed_county_view_bound"])

    def test_wrong_native_visibility_revision_keeps_red(self) -> None:
        bad = probe_result()
        bad["private_probe"]["snapshot_revision"] = REVISION + 1
        driver = FakeDriver({ROOT_STEP: root_result(), PRIVATE_STEP: bad})
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["issue"], "private_probe_stale_frame")

    def test_war_scene_never_sends_private_query(self) -> None:
        driver = FakeDriver({}, war=True)
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "ineligible_scene")
        self.assertEqual(result["issue"], "not_peaceful_or_residual_army")
        self.assertEqual(driver.sent, [])

    def test_campaign_root_actor_mismatch_keeps_red(self) -> None:
        driver = FakeDriver({ROOT_STEP: root_result(actor_id=ACTOR_ID + 1)})
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["issue"], "campaign_root_actor_or_date_mismatch")
        self.assertEqual(len(driver.sent), 1)

    def test_timeout_is_recorded_and_private_query_not_retried(self) -> None:
        driver = FakeDriver({ROOT_STEP: None})
        result = self._run(driver, frozen())
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["issue"], "campaign_root_query_timeout")
        self.assertEqual(len(driver.sent), 1)


if __name__ == "__main__":
    unittest.main()
