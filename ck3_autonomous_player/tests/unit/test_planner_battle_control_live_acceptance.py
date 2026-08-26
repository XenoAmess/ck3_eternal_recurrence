from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_planner_battle_control_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_planner_battle_control_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


SUBJECT = 83_886_341
COMBAT = 335_544_325
QUERY = f"query-battle-control-snapshot-v1-{SUBJECT}"
TERMINATION_QUERY = "query-war-termination-options-16777290"


class _FakePlannerService:
    def __init__(self) -> None:
        self.date_raw = 53_178_264
        self.revision = 5
        self.query_sequence = 0
        self.plan_kinds = [
            "query",
            "termination_query",
            "hold_initial",
            "query",
            "termination_query",
            "hold_verified",
            "query",
            "termination_query",
            "hold_verified",
        ]
        self.executed: list[str] = []

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": f"native:{self.revision}",
            "revision": self.revision,
            "native_revision": self.revision,
            "date_raw": self.date_raw,
            "phase": "map_hud",
            "map_ready": True,
            "paused": True,
            "episode_character_id": 29_829,
            "episode_run_id": "fixture-episode",
            "active_event": None,
            "player_armies": [
                {
                    "army_id": SUBJECT,
                    "controllable": True,
                    "in_combat": True,
                    "retreating": False,
                    "army_state": "combat",
                    "current_province_id": 2586,
                }
            ],
        }

    def _frame_summary(self) -> dict[str, object]:
        return {
            "subject_army_id": SUBJECT,
            "combat_id": COMBAT,
            "snapshot_revision": self.revision,
            "observed_date_raw": self.date_raw,
            "phase": "main",
            "phase_day": self.revision - 1,
        }

    def _transition(self) -> dict[str, object]:
        return {
            "status": "same_combat_advanced",
            "subject_army_id": SUBJECT,
            "before_combat_id": COMBAT,
            "after_combat_id": COMBAT,
            "before_snapshot_revision": self.revision - 1,
            "after_snapshot_revision": self.revision,
            "before_date_raw": self.date_raw - 24,
            "after_date_raw": self.date_raw,
            "phase_day_changed": True,
            "ledger_changed": False,
        }

    def plan_turn(self) -> dict[str, object]:
        kind = self.plan_kinds.pop(0)
        if kind == "query":
            plan = {
                "phase": "native_war_battle_control_query",
                "selected_step": QUERY,
            }
        elif kind == "termination_query":
            plan = {
                "phase": "native_war_termination_query",
                "selected_step": TERMINATION_QUERY,
            }
        else:
            plan = {
                "phase": "native_war_global_battle_control_progress",
                "selected_step": "life-advance",
                "battle_control_frames": [self._frame_summary()],
                "battle_transitions": (
                    [self._transition()]
                    if kind == "hold_verified"
                    else []
                ),
            }
        return {
            "snapshot_id": f"native:{self.revision}",
            "revision": self.revision,
            "plan": plan,
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("fixture revision mismatch")
        self.executed.append(step)
        if step == QUERY:
            self.query_sequence += 1
            frame = {
                "snapshot_revision": self.revision,
                "observed_date_raw": self.date_raw,
                "subject_public_cunit_id": SUBJECT,
                "subject_native_carmy_id": 101,
                "combat_id": COMBAT,
                "province_id": 2586,
                "phase": "main",
                "phase_raw": 1,
                "phase_day": self.revision - 1,
                "winner_side": "none",
                "forced_winner_side": "none",
                "finalized": False,
                "battle_result_id": 553_648_135,
                "attacker": {},
                "defender": {},
            }
            return {
                "step": QUERY,
                "accepted": True,
                "status": "available",
                "query_sequence": self.query_sequence,
                "snapshot_revision": self.revision,
                "battle_control_snapshot": frame,
                "queried_snapshot_id": f"native:{self.revision}",
                "queried_revision": self.revision,
                "queried_native_revision": self.revision,
            }
        if step == TERMINATION_QUERY:
            return {
                "step": TERMINATION_QUERY,
                "accepted": True,
                "status": "available",
                "war_id": 16_777_290,
            }
        if step != "life-advance":
            raise AssertionError(f"unexpected fixture step {step}")
        before = self.date_raw
        self.date_raw += 24
        self.revision += 1
        return {
            "step": "life-advance",
            "starting_date_raw": before,
            "ending_date_raw": self.date_raw,
            "elapsed_days": 1,
            "paused": True,
        }


class _RecordingService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(step)
        return {"step": step, "revision": expected_revision}


class PlannerBattleControlLiveAcceptanceTests(unittest.TestCase):
    def test_two_cycle_loop_is_query_advance_requery_and_same_combat(
        self,
    ) -> None:
        service = _FakePlannerService()

        result = HARNESS._run_planner_cycles(
            service,
            subject_army_id=SUBJECT,
            cycles=2,
            wait_after_advance=lambda: {
                "date_raw": service.date_raw,
                "paused": True,
            },
        )

        self.assertEqual(
            service.executed,
            [
                QUERY,
                TERMINATION_QUERY,
                "life-advance",
                QUERY,
                TERMINATION_QUERY,
                "life-advance",
                QUERY,
                TERMINATION_QUERY,
            ],
        )
        self.assertEqual(result["combat_id"], COMBAT)
        self.assertEqual(
            [row["date_delta_raw"] for row in result["cycles"]],
            [24, 24],
        )
        self.assertTrue(
            result["assertions"]["every_cycle_planner_verified_transition"]
        )
        self.assertTrue(
            result["assertions"]["every_requery_same_combat_id"]
        )
        self.assertEqual(
            result["assertions"]["retreat_actions_executed"], 0
        )
        self.assertTrue(
            result["assertions"][
                "read_only_prerequisites_preserved_native_frame"
            ]
        )
        self.assertEqual(
            result["cycles"][0]["post_advance_frame"]["battle_result_id"],
            553_648_135,
        )

    def test_retreat_literal_is_rejected_before_driver_dispatch(self) -> None:
        service = _RecordingService()
        planned = {
            "revision": 9,
            "plan": {
                "phase": "fixture",
                "selected_step": (
                    "order-active-combat-retreat-v1-1-2-3-4-full_side-5"
                ),
            },
        }

        with self.assertRaisesRegex(RuntimeError, "forbidden"):
            HARNESS._execute_planned(
                service,
                planned,
                allowed_steps=frozenset(
                    {planned["plan"]["selected_step"]}
                ),
            )

        self.assertEqual(service.calls, [])

    def test_profile_clone_excludes_volatile_runtime_and_save_roots(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            target = root / "target"
            (source / "shadercache").mkdir(parents=True)
            (source / "shadercache" / "cache.bin").write_bytes(b"cache")
            (source / "save games").mkdir()
            (source / "save games" / "autosave.ck3").write_bytes(b"save")
            (source / "logs").mkdir()
            (source / "logs" / "debug.log").write_text(
                "volatile", encoding="utf-8"
            )
            (source / "mod-content").mkdir()
            (source / "mod-content" / "old.txt").write_text(
                "old", encoding="utf-8"
            )
            (source / "last_save.ck3").write_bytes(b"save")
            (source / "pdx_settings.txt").write_text(
                "settings", encoding="utf-8"
            )

            HARNESS._copy_source_profile(source, target)

            self.assertTrue((target / "shadercache" / "cache.bin").is_file())
            self.assertTrue((target / "pdx_settings.txt").is_file())
            self.assertFalse((target / "save games").exists())
            self.assertFalse((target / "logs").exists())
            self.assertFalse((target / "mod-content").exists())
            self.assertFalse((target / "last_save.ck3").exists())

    def test_clone_cleanup_requires_exact_nonce_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "owned-clone"
            target.mkdir()
            marker = target / HARNESS._CLONE_MARKER_NAME
            marker.write_text(
                json.dumps(
                    {
                        "kind": "xar_planner_battle_control_clone",
                        "nonce": "expected",
                    }
                ),
                encoding="utf-8",
            )

            rejected = HARNESS._cleanup_clone(
                target,
                clone_nonce="different",
                retain_clone=False,
                session_started=False,
                session_cleanup_proven=False,
            )
            self.assertFalse(rejected["ok"])
            self.assertTrue(target.is_dir())

            accepted = HARNESS._cleanup_clone(
                target,
                clone_nonce="expected",
                retain_clone=False,
                session_started=False,
                session_cleanup_proven=False,
            )
            self.assertTrue(accepted["ok"])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
