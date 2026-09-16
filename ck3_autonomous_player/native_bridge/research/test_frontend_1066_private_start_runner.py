"""Focused ordering checks for the controlled exact-build 1066 route."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_frontend_gui_route_v1_live_acceptance as route  # noqa: E402


def model(*, selected: int = -1, government: str = "feudal_government"):
    return {
        "private_scope": "exact-build-bookmarks-model-v1",
        "status": "identity_ready",
        "candidate_identity_ready": True,
        "setup_view_matches_bookmarks_root": True,
        "verified_owner_route": "gui_context_registry",
        "selected_bookmark_group_key": None,
        "selected_bookmark_key": "bm_1066_rags_to_riches",
        "selected_date_raw": 0xFFFFFFFF032AEB08,
        "selected_date_low_raw": 0x032AEB08,
        "supported_1066_government_key": government,
        "supported_1066_date_matches": True,
        "candidate_keys": [
            "bookmark_rags_to_riches_petty_king_murchad",
            "bookmark_rags_to_riches_duchess_matilda",
            "bookmark_rags_to_riches_emir_yahya",
            "bookmark_rags_to_riches_duke_vratislav",
            "bookmark_rags_to_riches_duke_robert",
        ],
        "bookmark_character_count": 5,
        "supported_1066_candidate_index": 0,
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
    ):
        self.save = root / "xar_checkpoint.ck3"
        self.state = root / "native_driver_state.json"
        self.executed: list[str] = []
        self.pump_epochs = pump_epochs or [10, 11]
        self.snapshot_reads = 0
        self.root_queries = 0
        self.succession_lifecycle = succession_lifecycle

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
            "date_raw": 0x032AEB08,
            "played_character": {"character_id": 42},
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
            "date_raw": 0x032AEB08,
            "player_character_id": 42,
            "government": {"key": "feudal_government"},
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
