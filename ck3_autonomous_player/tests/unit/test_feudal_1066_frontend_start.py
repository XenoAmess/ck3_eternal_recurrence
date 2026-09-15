from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.frontend_gui_route_contract import (
    ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
    ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
    QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP,
    normalize_frontend_selected_1066_feudal_candidate_v1,
    normalize_frontend_start_selected_bookmark_v1,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


def _before() -> dict[str, object]:
    return {"route": "bookmarks"}


def _ack() -> dict[str, object]:
    return {
        "step": ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
        "accepted": True,
        "status": "acknowledged_verification_pending",
        "backend_id": "native-headless",
    }


def _paused_map() -> dict[str, object]:
    return {
        "paused": True,
        "native_revision": 3,
        "revision": 3,
        "date_raw": 53178312,
        "played_character": {"character_id": 83355},
    }


def _root() -> dict[str, object]:
    return {
        "campaign_root_context_ready": True,
        "queried_native_revision": 3,
        "date_raw": 53178312,
        "player_character_id": 83355,
        "government": {"key": "feudal_government"},
    }


def _candidate_raw() -> dict[str, object]:
    return {
        "step": QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP,
        "accepted": True,
        "status": "ready",
        "route": "bookmarks",
        "selected_bookmark_group_key": "bm_group_1066",
        "selected_bookmark_key": "bm_1066_rags_to_riches",
        "selected_character_name_key":
            "bookmark_rags_to_riches_petty_king_murchad",
        "selected_character_government_key": "feudal_government",
        "selected_bookmark_start_date_raw": 53178312,
        "query_sequence": 1,
    }


def _candidate() -> dict[str, object]:
    return normalize_frontend_selected_1066_feudal_candidate_v1(
        _candidate_raw()
    )


class FeudalSelectedBookmarkStartTests(unittest.TestCase):
    def test_ack_only_or_other_government_cannot_verify_start(self) -> None:
        incomplete = _candidate_raw()
        incomplete["selected_character_name_key"] = None
        with self.assertRaises(ValueError):
            normalize_frontend_selected_1066_feudal_candidate_v1(incomplete)
        wrong_source = _candidate()
        wrong_source["selected_bookmark_key"] = "bm_1066_the_conqueror"
        with self.assertRaises(ValueError):
            normalize_frontend_start_selected_bookmark_v1(
                _ack(), before=_before(),
                selected_candidate=wrong_source,
                after_snapshot=_paused_map(), campaign_root=_root(),
            )
        with self.assertRaises(ValueError):
            normalize_frontend_start_selected_bookmark_v1(
                _ack(), before=_before(), after_snapshot={},
                campaign_root={}, selected_candidate=_candidate(),
            )
        non_feudal = _root()
        non_feudal["government"] = {"key": "clan_government"}
        with self.assertRaises(ValueError):
            normalize_frontend_start_selected_bookmark_v1(
                _ack(), before=_before(),
                after_snapshot=_paused_map(),
                campaign_root=non_feudal, selected_candidate=_candidate(),
            )
        wrong_player = _root()
        wrong_player["player_character_id"] = 1
        with self.assertRaises(ValueError):
            normalize_frontend_start_selected_bookmark_v1(
                _ack(), before=_before(),
                after_snapshot=_paused_map(),
                campaign_root=wrong_player, selected_candidate=_candidate(),
            )

    def test_submitted_start_requires_independent_paused_root(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.frontend_transition_timeout_seconds = 0.02
        calls: list[dict[str, object]] = []
        driver.query_frontend_gui_route_v1 = _before
        driver.query_frontend_selected_1066_feudal_candidate_v1 = _candidate
        driver.take_snapshot = _paused_map
        driver._execute_campaign_root_context_v1_query = (
            lambda *, expected_revision: _root()
        )

        def execute(
            step: str, *, expected_revision: int,
            required_capability: str,
            allow_frontend_revision_zero: bool,
        ) -> dict[str, object]:
            calls.append({
                "step": step,
                "expected_revision": expected_revision,
                "required_capability": required_capability,
                "allow_frontend_revision_zero":
                    allow_frontend_revision_zero,
            })
            return _ack()

        driver._execute_primitive_step = execute
        result = driver.activate_frontend_start_selected_bookmark_v1()
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["postcondition_verified"])
        self.assertEqual(result["campaign_root"]["government"]["key"],
                         "feudal_government")
        self.assertEqual(calls, [{
            "step": ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP,
            "expected_revision": 0,
            "required_capability":
                ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
            "allow_frontend_revision_zero": True,
        }])

    def test_lost_postcondition_does_not_repeat_start(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.frontend_transition_timeout_seconds = 0.001
        calls: list[str] = []
        driver.query_frontend_gui_route_v1 = _before
        driver.query_frontend_selected_1066_feudal_candidate_v1 = _candidate
        driver.take_snapshot = lambda: (_ for _ in ()).throw(
            BridgeUnavailableError("map loading")
        )
        driver._execute_primitive_step = (
            lambda step, **_: calls.append(step) or _ack()
        )
        with self.assertRaisesRegex(
            BridgeUnavailableError, "submitted but no paused player map"
        ):
            driver.activate_frontend_start_selected_bookmark_v1()
        self.assertEqual(
            calls, [ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_STEP]
        )

    def test_missing_native_identity_query_stops_before_start(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.query_frontend_gui_route_v1 = _before
        calls: list[str] = []
        driver._execute_primitive_step = (
            lambda step, **_: calls.append(step) or _ack()
        )
        with self.assertRaises(BridgeUnavailableError):
            driver.activate_frontend_start_selected_bookmark_v1()
        self.assertEqual(
            calls,
            [QUERY_FRONTEND_SELECTED_1066_FEUDAL_CANDIDATE_V1_STEP],
        )


if __name__ == "__main__":
    unittest.main()
