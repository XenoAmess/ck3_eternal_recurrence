"""Ordering and stock identity checks for the private bookmark start route."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_frontend_gui_route_v1_live_acceptance as route  # noqa: E402


def model(
    *,
    selected: int = -1,
    government: str | None = None,
    target: str = "bookmark_rags_to_riches_petty_king_murchad",
):
    profile = route.PRIVATE_BOOKMARK_PROFILES[target]
    keys = [
        "bookmark_rags_to_riches_petty_king_murchad",
        "bookmark_rags_to_riches_duchess_matilda",
        "bookmark_rags_to_riches_emir_yahya",
        "bookmark_rags_to_riches_duke_vratislav",
        "bookmark_rags_to_riches_duke_robert",
    ]
    if target == "bookmark_adventurers_rurik_rurikid":
        keys = ["bookmark_adventurers_ivar_the_boneless", target]
    government = government or profile["government_key"]
    return {
        "private_scope": "exact-build-bookmarks-model-v1",
        "status": "identity_ready",
        "candidate_identity_ready": True,
        "setup_view_matches_bookmarks_root": True,
        "verified_owner_route": "gui_context_registry",
        "selected_bookmark_group_key": None,
        "selected_bookmark_key": profile["bookmark_key"],
        "selected_date_raw": (0xFFFFFFFF << 32) | profile["date_low_raw"],
        "selected_date_low_raw": profile["date_low_raw"],
        "supported_1066_government_key": government,
        "supported_1066_feudal": government == "feudal_government",
        "supported_1066_date_matches": True,
        "candidate_keys": keys,
        "bookmark_character_count": len(keys),
        "supported_1066_candidate_index": keys.index(target),
        "selected_character_index": selected,
    }


def action(step: str, *, acknowledged: bool = True):
    return {
        "step": step,
        "submitted": True,
        "is_error": not acknowledged,
        "structured_content": {
            "step": step,
            "accepted": acknowledged,
            "status": (
                "acknowledged_verification_pending"
                if acknowledged
                else "unconfirmed"
            ),
        },
    }


class FakeDriver:
    def __init__(
        self,
        root: Path,
        *,
        pump_epochs: list[int] | None = None,
        succession_lifecycle: dict[str, object] | None = None,
        target: str = "bookmark_rags_to_riches_petty_king_murchad",
    ):
        self.save = root / "xar_checkpoint.ck3"
        self.state = root / "native_driver_state.json"
        self.executed: list[str] = []
        self.pump_epochs = pump_epochs or [10, 11]
        self.snapshot_reads = 0
        self.root_queries = 0
        self.succession_lifecycle = succession_lifecycle
        self.date_raw = route.PRIVATE_BOOKMARK_PROFILES[target]["date_low_raw"]
        self.government_key = route.PRIVATE_BOOKMARK_PROFILES[target]["government_key"]
        # An actual runtime identity deliberately distinct from source history IDs.
        self.runtime_actor = 42

    def take_snapshot(self):
        epoch = self.pump_epochs[
            min(self.snapshot_reads, len(self.pump_epochs) - 1)
        ]
        self.snapshot_reads += 1
        return {
            "paused": True,
            "map_ready": True,
            "snapshot_id": "native:3",
            "native_revision": 3,
            "revision": 3,
            "date_raw": self.date_raw,
            "played_character": {"character_id": self.runtime_actor},
            "diagnostics": {
                "bridge_pid": 99,
                "connection_generation": 1,
                "last_heartbeat": {
                    "main_thread_query_mailbox_v1": {"pump_epochs": epoch}
                },
            },
        }

    def _execute_campaign_root_context_v1_query(self, *, expected_revision):
        self.root_queries += 1
        assert expected_revision is None
        return {
            "campaign_root_context_ready": True,
            "queried_native_revision": 3,
            "date_raw": self.date_raw,
            "player_character_id": self.runtime_actor,
            "government": {"key": self.government_key},
            "selected_game_rule_tokens": (
                ["normal_difficulty", "xar_off"]
                if self.succession_lifecycle is not None
                else []
            ),
            "readiness": {
                "selected_game_rule_tokens_ready": True,
            },
        }

    def execute_step(self, step: str):
        self.executed.append(step)
        if step == "save-checkpoint":
            self.save.write_bytes(b"checkpoint-fixture")
            checkpoint = {
                "status": "saved",
                "succession_lifecycle": self.succession_lifecycle,
                "history_index": 1,
            }
            result = {
                "step": step,
                "status": "saved",
                "checkpoint": checkpoint,
            }
            self.state.write_text(
                json.dumps(
                    {
                        "goal": "1066 campaign",
                        "succession_lifecycle": self.succession_lifecycle,
                        "last_checkpoint": checkpoint,
                        "command_history": [
                            {
                                "index": 1,
                                "command": "save-checkpoint",
                                "ok": True,
                                "result": result,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            return result
        raise AssertionError(f"unexpected gameplay step: {step}")

    def _checkpoint_path(self):
        return self.save

    def _native_driver_state_path(self):
        return self.state


class PrivateFeudalStartOrderingTests(unittest.TestCase):
    @staticmethod
    def _ordinary_lifecycle() -> dict[str, object]:
        return route.bind_succession_lifecycle_from_environment_v1(
            {
                "environment_sha256": "d" * 64,
                "rules": {
                    "profile": [
                        {"rule": "xar_enabled", "setting": "xar_off"}
                    ]
                },
            },
            lifecycle=route.ORDINARY_CAMPAIGN_SUCCESSION,
            ordinary_campaign_no_pact=True,
        )

    def test_source_model_failure_never_submits_an_action(self):
        with mock.patch.object(route, "_call_private_frontend_action") as submit:
            result = route._controlled_private_feudal_start(
                object(), model(government="clan_government"), 1.0
            )
        self.assertFalse(result["ok"])
        self.assertFalse(result["selector_submitted"])
        self.assertFalse(result["start_submitted"])
        submit.assert_not_called()

    def test_yahya_clan_uses_its_target_steps_and_actual_runtime_actor(self):
        target = "bookmark_rags_to_riches_emir_yahya"
        steps = [
            "select-frontend-bookmark-character-yahya-v1",
            "activate-frontend-start-selected-bookmark-yahya-v1",
        ]
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(Path(directory), target=target)
            with (
                mock.patch.object(
                    route, "_call_private_frontend_action",
                    side_effect=[action(step) for step in steps],
                ) as submit,
                mock.patch.object(
                    route, "_call_private_bookmarks_model",
                    return_value={
                        "is_error": False,
                        "structured_content": model(selected=2, target=target),
                    },
                ) as requery,
            ):
                result = route._controlled_private_feudal_start(
                    driver, model(selected=0, target=target), 1.0,
                    expected_character_name_key=target,
                )
            self.assertTrue(result["ok"], result.get("error"))
            self.assertFalse(result["bookmark_switch_submitted"])
            self.assertEqual(submit.call_count, 2)
            self.assertEqual(
                [call.args[1] for call in submit.call_args_list], steps
            )
            self.assertEqual(
                requery.call_args.kwargs["step"],
                "probe-frontend-bookmark-model-yahya-v1",
            )
            self.assertEqual(
                result["public_campaign_root"]["government"]["key"],
                "clan_government",
            )
            self.assertEqual(
                result["public_campaign_root"]["player_character_id"], 42
            )
            self.assertNotEqual(
                result["public_campaign_root"]["player_character_id"], 3924
            )
            self.assertEqual(driver.executed, ["save-checkpoint"])

    def test_rurik_switch_is_once_then_independent_selection_and_tribal_map(self):
        target = "bookmark_adventurers_rurik_rurikid"
        steps = [
            "activate-frontend-select-bookmark-rurik-v1",
            "select-frontend-bookmark-character-rurik-v1",
            "activate-frontend-start-selected-bookmark-rurik-v1",
        ]
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(Path(directory), target=target)
            with (
                mock.patch.object(
                    route, "_call_private_frontend_action",
                    side_effect=[action(step) for step in steps],
                ) as submit,
                mock.patch.object(
                    route, "_call_private_bookmarks_model",
                    side_effect=[
                        {"is_error": False, "structured_content": model(target=target)},
                        {"is_error": False, "structured_content": model(selected=1, target=target)},
                    ],
                ) as requery,
            ):
                result = route._controlled_private_feudal_start(
                    driver, model(), 1.0, expected_character_name_key=target,
                )
            self.assertTrue(result["ok"], result.get("error"))
            self.assertTrue(result["bookmark_switch_submitted"])
            self.assertTrue(result["independent_selected_model_verified"])
            self.assertEqual(
                [call.args[1] for call in submit.call_args_list], steps
            )
            self.assertEqual(requery.call_count, 2)
            self.assertEqual(
                {call.kwargs["step"] for call in requery.call_args_list},
                {"probe-frontend-bookmark-model-rurik-v1"},
            )
            self.assertEqual(result["public_campaign_root"]["date_raw"], 51394920)
            self.assertEqual(
                result["public_campaign_root"]["government"]["key"],
                "tribal_government",
            )
            self.assertNotEqual(
                result["public_campaign_root"]["player_character_id"], 40605
            )
            self.assertEqual(driver.executed, ["save-checkpoint"])

    def test_wrong_post_switch_bookmark_never_submits_selection_or_start(self):
        target = "bookmark_adventurers_rurik_rurikid"
        switch_step = "activate-frontend-select-bookmark-rurik-v1"
        with (
            mock.patch.object(
                route, "_call_private_frontend_action",
                return_value=action(switch_step),
            ) as submit,
            mock.patch.object(
                route, "_call_private_bookmarks_model",
                return_value={"is_error": False, "structured_content": model()},
            ),
        ):
            result = route._controlled_private_feudal_start(
                object(), model(), 1.0, expected_character_name_key=target,
            )
        self.assertFalse(result["ok"])
        self.assertTrue(result["bookmark_switch_submitted"])
        self.assertFalse(result["selector_submitted"])
        self.assertFalse(result["start_submitted"])
        self.assertEqual(submit.call_count, 1)

    def test_clan_native_model_rejects_wrong_government_or_source_date(self):
        target = "bookmark_rags_to_riches_emir_yahya"
        wrong_government = model(target=target, government="tribal_government")
        wrong_date = model(target=target)
        wrong_date["selected_date_low_raw"] += 24
        for invalid in (wrong_government, wrong_date):
            with self.subTest(model=invalid), mock.patch.object(
                route, "_call_private_frontend_action"
            ) as submit:
                result = route._controlled_private_feudal_start(
                    object(), invalid, 1.0, expected_character_name_key=target,
                )
                self.assertFalse(result["ok"])
                submit.assert_not_called()

    def test_clan_selected_model_cannot_substitute_for_actual_root_government(self):
        target = "bookmark_rags_to_riches_emir_yahya"
        step = "activate-frontend-start-selected-bookmark-yahya-v1"
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(Path(directory), target=target)
            driver.government_key = "feudal_government"
            with (
                mock.patch.object(
                    route, "_call_private_frontend_action",
                    return_value=action(step),
                ) as submit,
                mock.patch.object(
                    route, "_call_private_bookmarks_model",
                    return_value={
                        "is_error": False,
                        "structured_content": model(selected=2, target=target),
                    },
                ),
            ):
                result = route._controlled_private_feudal_start(
                    driver, model(selected=2, target=target), 1.0,
                    expected_character_name_key=target,
                )
            self.assertFalse(result["ok"])
            self.assertEqual(submit.call_count, 1)
            self.assertEqual(driver.root_queries, 1)
            self.assertEqual(driver.executed, [])

    def test_cli_accepts_stock_targets_and_explicit_latest_executable_pin(self):
        required = [
            "--source-profile", "source",
            "--state-dir", "state",
            "--game-dir", "game",
            "--bridge-pipe", "test-pipe",
            "--bridge-dll", "bridge.dll",
            "--bridge-injector", "injector.exe",
            "--output", "output",
        ]
        latest_sha = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
        for target in (
            "bookmark_rags_to_riches_emir_yahya",
            "bookmark_adventurers_rurik_rurikid",
        ):
            with self.subTest(target=target):
                parsed = route._parser().parse_args(required + [
                    "--bookmark-character-key", target,
                    "--expected-ck3-sha256", latest_sha,
                ])
                self.assertEqual(parsed.bookmark_character_key, target)
                self.assertEqual(parsed.expected_ck3_sha256, latest_sha)
        self.assertEqual(
            route._parser().parse_args(required).expected_ck3_sha256,
            route.EXPECTED_CK3_SHA256,
        )

    def test_robert_mismatch_stops_before_typed_selection(self):
        robert = "bookmark_rags_to_riches_duke_robert"
        with mock.patch.object(route, "_call_private_frontend_action") as submit:
            result = route._controlled_private_feudal_start(
                object(), model(), 1.0,
                expected_character_name_key=robert,
            )
        self.assertFalse(result["ok"])
        self.assertFalse(result["selector_submitted"])
        submit.assert_not_called()

    def test_robert_can_replace_current_murchad_selection(self):
        robert = "bookmark_rags_to_riches_duke_robert"
        steps = [
            "select-frontend-supported-1066-character-v1",
            "activate-frontend-start-selected-bookmark-v1",
        ]
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(Path(directory))
            with (
                mock.patch.object(
                    route, "_call_private_frontend_action",
                    side_effect=[action(step) for step in steps],
                ) as submit,
                mock.patch.object(
                    route, "_call_private_bookmarks_model",
                    return_value={
                        "is_error": False,
                        "structured_content": model(selected=4, target=robert),
                    },
                ),
            ):
                result = route._controlled_private_feudal_start(
                    driver,
                    model(selected=0, target=robert),
                    1.0,
                    expected_character_name_key=robert,
                )
            self.assertTrue(result["ok"], result.get("error"))
            self.assertEqual(result["expected_character_name_key"], robert)
            self.assertEqual(result["native_target_index_before"], 4)
            self.assertEqual(submit.call_count, 2)
            self.assertEqual(driver.executed, ["save-checkpoint"])

    def test_lost_selection_ack_stops_without_retry_or_start(self):
        step = "select-frontend-supported-1066-character-v1"
        with mock.patch.object(
            route, "_call_private_frontend_action",
            return_value=action(step, acknowledged=False),
        ) as submit:
            result = route._controlled_private_feudal_start(
                object(), model(), 1.0
            )
        self.assertFalse(result["ok"])
        self.assertTrue(result["selector_submitted"])
        self.assertFalse(result["start_submitted"])
        self.assertEqual(submit.call_count, 1)

    def test_new_model_that_did_not_select_role_blocks_start(self):
        first_step = "select-frontend-supported-1066-character-v1"
        with (
            mock.patch.object(
                route, "_call_private_frontend_action",
                return_value=action(first_step),
            ) as submit,
            mock.patch.object(
                route, "_call_private_bookmarks_model",
                return_value={
                    "is_error": False,
                    "structured_content": model(selected=-1),
                },
            ),
        ):
            result = route._controlled_private_feudal_start(
                object(), model(), 1.0
            )
        self.assertFalse(result["ok"])
        self.assertTrue(result["selector_submitted"])
        self.assertFalse(result["start_submitted"])
        self.assertEqual(submit.call_count, 1)

    def test_independent_model_map_root_and_pair_complete_candidate(self):
        steps = [
            "select-frontend-supported-1066-character-v1",
            "activate-frontend-start-selected-bookmark-v1",
        ]
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(Path(directory))
            with (
                mock.patch.object(
                    route, "_call_private_frontend_action",
                    side_effect=[action(step) for step in steps],
                ) as submit,
                mock.patch.object(
                    route, "_call_private_bookmarks_model",
                    return_value={
                        "is_error": False,
                        "structured_content": model(selected=0),
                    },
                ) as requery,
            ):
                result = route._controlled_private_feudal_start(
                    driver, model(), 1.0
                )
            self.assertTrue(result["ok"])
            self.assertTrue(result["independent_selected_model_verified"])
            self.assertTrue(result["independent_campaign_root_verified"])
            self.assertEqual(submit.call_count, 2)
            self.assertEqual(requery.call_count, 1)
            self.assertEqual(driver.executed, ["save-checkpoint"])
            self.assertEqual(driver.root_queries, 1)
            self.assertEqual(result["post_ready_pump"]["baseline_epoch"], 10)
            self.assertEqual(result["post_ready_pump"]["last_epoch"], 11)
            self.assertEqual(
                result["public_campaign_root"]["player_character_id"], 42
            )
            self.assertEqual(len(result["paired_checkpoint"]["game_save_sha256"]), 64)

    def test_frozen_post_start_pump_blocks_public_query_and_checkpoint(self):
        steps = [
            "select-frontend-supported-1066-character-v1",
            "activate-frontend-start-selected-bookmark-v1",
        ]
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(Path(directory), pump_epochs=[5390])
            with (
                mock.patch.object(
                    route, "_call_private_frontend_action",
                    side_effect=[action(step) for step in steps],
                ) as submit,
                mock.patch.object(
                    route, "_call_private_bookmarks_model",
                    return_value={
                        "is_error": False,
                        "structured_content": model(selected=0),
                    },
                ),
            ):
                result = route._controlled_private_feudal_start(
                    driver, model(), 0.04
                )
            self.assertFalse(result["ok"])
            self.assertTrue(result["independent_selected_model_verified"])
            self.assertEqual(result["post_ready_pump"]["baseline_epoch"], 5390)
            self.assertEqual(result["post_ready_pump"]["last_epoch"], 5390)
            self.assertEqual(driver.root_queries, 0)
            self.assertEqual(driver.executed, [])
            self.assertEqual(submit.call_count, 2)

    def test_ordinary_seed_persists_exact_lifecycle_in_checkpoint_pair(self):
        steps = [
            "select-frontend-supported-1066-character-v1",
            "activate-frontend-start-selected-bookmark-v1",
        ]
        lifecycle = self._ordinary_lifecycle()
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[4]
        ) as directory:
            driver = FakeDriver(
                Path(directory), succession_lifecycle=lifecycle
            )
            with (
                mock.patch.object(
                    route,
                    "_call_private_frontend_action",
                    side_effect=[action(step) for step in steps],
                ),
                mock.patch.object(
                    route,
                    "_call_private_bookmarks_model",
                    return_value={
                        "is_error": False,
                        "structured_content": model(selected=0),
                    },
                ),
            ):
                result = route._controlled_private_feudal_start(
                    driver,
                    model(),
                    1.0,
                    expected_succession_lifecycle=lifecycle,
                )

        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(result["succession_lifecycle"], lifecycle)
        self.assertEqual(
            result["checkpoint_result"]["checkpoint"][
                "succession_lifecycle"
            ],
            lifecycle,
        )


if __name__ == "__main__":
    unittest.main()
