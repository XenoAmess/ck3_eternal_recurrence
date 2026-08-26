from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_owner_subset_ai_reassignment_rejoin_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_owner_subset_ai_reassignment_rejoin_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


DATE_RAW = 53_178_624
PROVINCE_ID = 2_586


def _army(*, controllable: bool) -> dict[str, object]:
    return {
        "army_id": HARNESS.REJOIN_CUNIT_ID,
        "owner_character_id": HARNESS.OWNER_SUBSET_CHARACTER_ID,
        "current_province_id": HARNESS.RETREAT_TARGET_PROVINCE_ID,
        "move_target_province_id": HARNESS.RETREAT_TARGET_PROVINCE_ID,
        "move_target_observable": True,
        "route_province_ids": [HARNESS.RETREAT_TARGET_PROVINCE_ID],
        "controllable": controllable,
        "in_combat": False,
        "retreating": True,
        "army_state_code": 6,
    }


def _snapshot(*, controllable: bool = False) -> dict[str, object]:
    return {
        "snapshot_id": "native:9",
        "revision": 10,
        "native_revision": 9,
        "date_raw": DATE_RAW,
        "paused": True,
        "episode_run_id": "native-29829-ai-return",
        "played_character": {"character_id": HARNESS.ORIGINAL_CHARACTER_ID},
        "player_armies": ([_army(controllable=True)] if controllable else []),
        "active_wars": [
            {
                "war_id": 16_777_290,
                "player_side": "attacker",
                "primary_opponent_character_id": (
                    HARNESS.OWNER_SUBSET_CHARACTER_ID
                ),
                "allied_armies": [],
                "enemy_armies": [_army(controllable=controllable)],
            }
        ],
    }


def _battle(
    *, phase_raw: int = 2, winner_raw: int = 0
) -> dict[str, object]:
    return {
        "status": "available",
        "battle_transition_ready": True,
        "combat_id": HARNESS.COMBAT_ID,
        "province_id": PROVINCE_ID,
        "phase_raw": phase_raw,
        "phase_day": 0,
        "winner_raw": winner_raw,
        "finalized": False,
        "attacker_public_cunit_ids_in_stored_order": [
            HARNESS.OPPOSITE_CUNIT_ID
        ],
        "defender_public_cunit_ids_in_stored_order": [
            HARNESS.ANCHOR_CUNIT_ID
        ],
    }


def _terminal(
    battle: dict[str, object], *, requested_cursor: int | None = None
) -> dict[str, object]:
    return {
        "status": "available",
        "battle_terminal_transition_ready": True,
        "prior_combat_id": HARNESS.COMBAT_ID,
        "terminal_journal": {
            "requested_after_sequence": requested_cursor,
            "oldest_available_sequence": 1,
            "latest_sequence": 4,
            "event_sequence": None,
            "event_status": "not_observed",
        },
        "prior": {
            "combat_id": HARNESS.COMBAT_ID,
            "terminal_kind": "active_not_terminal",
            "attacker_public_cunit_ids_in_stored_order": battle[
                "attacker_public_cunit_ids_in_stored_order"
            ],
            "defender_public_cunit_ids_in_stored_order": battle[
                "defender_public_cunit_ids_in_stored_order"
            ],
        },
        "removal": {"prior_combat_strictly_resolves": True},
    }


def _pair(
    *,
    available: bool = True,
    retreating_mismatch: bool = False,
    cross_stack: bool = False,
) -> dict[str, object]:
    rejoin_status = "available" if available else "unavailable"
    anchor_status = (
        "available" if available or retreating_mismatch else "unavailable"
    )
    shared_rows = [
        {
            "public_cunit_ids_in_stored_order": [
                HARNESS.REJOIN_CUNIT_ID,
                HARNESS.ANCHOR_CUNIT_ID,
            ],
            "asking_for_help": False,
            "assigned_to_help": False,
            "assignment_target_province_id": None,
        }
    ]

    def native_fields(*, rejoin: bool) -> dict[str, object]:
        selected = (
            HARNESS.REJOIN_CUNIT_ID if rejoin else HARNESS.ANCHOR_CUNIT_ID
        )
        rows = (
            [
                {
                    "public_cunit_ids_in_stored_order": [selected],
                    "asking_for_help": False,
                    "assigned_to_help": False,
                    "assignment_target_province_id": None,
                }
            ]
            if cross_stack
            else shared_rows
        )
        return {
            "selected_native_carmy_id": (
                344 if rejoin or not cross_stack else 50_331_769
            ),
            "coordinator_id": 33_554_513,
            "unit_stack_stored_index": 1 if rejoin and cross_stack else 0,
            "subunit_stored_index": 0,
            "native_order": {
                "support_search_province_ids_in_stored_order": [PROVINCE_ID],
                "parent_subunits_in_stored_order": rows,
            },
        }

    rejoin_native = native_fields(rejoin=True) if available else {}
    anchor_native = (
        native_fields(rejoin=False)
        if anchor_status == "available"
        else {}
    )
    return {
        "available_order_ready": available and not cross_stack,
        "binding_ok": True,
        "rejoin_frame": {
            "status": rejoin_status,
            "unavailable_reason": (
                "subunit_backlink_mismatch" if retreating_mismatch else None
            ),
            "battle_reinforcement_assignment_ready": available,
            "selected_public_cunit_id": HARNESS.REJOIN_CUNIT_ID,
            **rejoin_native,
        },
        "anchor_frame": {
            "status": anchor_status,
            "unavailable_reason": None,
            "battle_reinforcement_assignment_ready": anchor_status
            == "available",
            "selected_public_cunit_id": HARNESS.ANCHOR_CUNIT_ID,
            **anchor_native,
        },
        "native_rows": (
            rejoin_native.get("native_order", {}).get(
                "parent_subunits_in_stored_order", []
            )
            if available
            else []
        ),
    }


class OwnerSubsetAiReassignmentTests(unittest.TestCase):
    def test_return_effect_uses_dynamic_province_owner_and_unique_guard(self) -> None:
        effect = HARNESS._return_switch_effect()
        self.assertIn(
            f"province:{HARNESS.RETURN_CHARACTER_ANCHOR_PROVINCE_ID} = {{",
            effect,
        )
        self.assertIn("province_owner = {", effect)
        self.assertIn(
            "set_player_character = scope:xar_fixture_owner_subset_return_target",
            effect,
        )
        self.assertIn(HARNESS.RETURN_SWITCH_MARKER, effect)
        self.assertIn(HARNESS.RETURN_GUARD_VARIABLE, effect)
        self.assertNotIn("character:29829", effect)
        self.assertNotIn("play 29829", effect)

    def test_waiting_old_combat_accepts_live_pursuit_winner(self) -> None:
        proof = HARNESS._waiting_old_combat_proof(_battle())
        self.assertTrue(proof["ok"])
        invalid = _battle(phase_raw=1, winner_raw=0)
        self.assertFalse(HARNESS._waiting_old_combat_proof(invalid)["ok"])

    def test_ai_control_gate_requires_noncontrollable_and_available_pair(self) -> None:
        battle = _battle()
        proof = HARNESS._ai_control_proof(
            _snapshot(),
            _pair(),
            battle,
            _terminal(battle),
            expected_date_raw=DATE_RAW,
            requested_cursor=None,
        )
        self.assertTrue(proof["ok"])
        controllable = HARNESS._ai_control_proof(
            _snapshot(controllable=True),
            _pair(),
            battle,
            _terminal(battle),
            expected_date_raw=DATE_RAW,
            requested_cursor=None,
        )
        self.assertFalse(controllable["ok"])
        unavailable = HARNESS._ai_control_proof(
            _snapshot(),
            _pair(available=False),
            battle,
            _terminal(battle),
            expected_date_raw=DATE_RAW,
            requested_cursor=None,
        )
        self.assertFalse(unavailable["ok"])

    def test_v4_ai_control_accepts_typed_mismatch_while_retreating(self) -> None:
        battle = _battle()
        proof = HARNESS._ai_control_proof(
            _snapshot(),
            _pair(available=False, retreating_mismatch=True),
            battle,
            _terminal(battle),
            expected_date_raw=DATE_RAW,
            requested_cursor=None,
        )
        self.assertTrue(proof["ok"])
        self.assertFalse(proof["native_pair_available"])
        self.assertEqual(
            proof["membership_classification"],
            "retreating_subunit_backlink_mismatch",
        )
        self.assertTrue(proof["retreating_membership_transient"]["ok"])
        invalid_snapshot = _snapshot()
        invalid_snapshot["active_wars"][0]["enemy_armies"][0][
            "retreating"
        ] = False
        invalid_snapshot["active_wars"][0]["enemy_armies"][0][
            "army_state_code"
        ] = 3
        invalid = HARNESS._ai_control_proof(
            invalid_snapshot,
            _pair(available=False, retreating_mismatch=True),
            battle,
            _terminal(battle),
            expected_date_raw=DATE_RAW,
            requested_cursor=None,
        )
        self.assertFalse(invalid["ok"])

    def test_v4_native_pair_reopen_requires_later_same_episode_frame(self) -> None:
        snapshot = _snapshot()
        transient = HARNESS._retreating_membership_transient_proof(
            snapshot, _pair(available=False, retreating_mismatch=True)
        )
        later = _snapshot()
        later["date_raw"] = DATE_RAW + HARNESS.ONE_GAME_DAY_RAW
        context = HARNESS._daily_ai_context_proof(
            later,
            expected_date_raw=DATE_RAW + HARNESS.ONE_GAME_DAY_RAW,
            expected_episode_run_id=snapshot["episode_run_id"],
        )
        reopened = HARNESS._native_pair_reopened_proof(
            transient, _pair(cross_stack=True), context, day_index=1
        )
        self.assertTrue(reopened["ok"])
        self.assertEqual(
            reopened["native_membership_pair"]["parent_relationship"],
            "cross_stack_same_coordinator",
        )
        self.assertFalse(
            reopened["native_membership_pair"][
                "legacy_same_parent_order_ready"
            ]
        )
        self.assertFalse(
            HARNESS._native_pair_reopened_proof(
                transient, _pair(cross_stack=True), context, day_index=0
            )["ok"]
        )

    def test_cross_stack_assignment_keeps_all_strict_assignment_gates(self) -> None:
        snapshot = _snapshot()
        subject = snapshot["active_wars"][0]["enemy_armies"][0]
        subject["current_province_id"] = HARNESS.RETREAT_TARGET_PROVINCE_ID
        subject["move_target_province_id"] = PROVINCE_ID
        subject["route_province_ids"] = [PROVINCE_ID]
        subject["retreating"] = False
        subject["army_state_code"] = 1
        pair = _pair(cross_stack=True)
        rejoin = pair["rejoin_frame"]
        anchor = pair["anchor_frame"]
        rejoin["signal"] = {
            "asking_for_help": False,
            "assigned_to_help": True,
        }
        anchor["signal"] = {
            "asking_for_help": True,
            "assigned_to_help": False,
        }
        rejoin["assignment"] = {
            "assignment_target_province_id": PROVINCE_ID,
            "target_provenance": "native_help_override",
            "combat_binding_status": "unbound_until_contact",
            "active_combat_id": None,
        }
        anchor["assignment"] = {
            "assignment_target_province_id": None,
            "target_provenance": "none",
            "combat_binding_status": "already_in_active_combat",
            "active_combat_id": HARNESS.COMBAT_ID,
        }
        rejoin["route"] = {
            "current_province_id": HARNESS.RETREAT_TARGET_PROVINCE_ID,
            "move_target_province_id": PROVINCE_ID,
            "route_province_ids": [PROVINCE_ID],
            "route_alignment": "aligned_to_assignment",
            "arrival_date_raws": [DATE_RAW + HARNESS.ONE_GAME_DAY_RAW],
            "assignment_eta_date_raw": DATE_RAW
            + HARNESS.ONE_GAME_DAY_RAW,
        }
        proof = HARNESS._independent_assignment_reopened_proof(
            pair,
            snapshot,
            _battle(phase_raw=1, winner_raw=-1),
            combat_id=HARNESS.COMBAT_ID,
            combat_province_id=PROVINCE_ID,
        )
        self.assertTrue(proof["ok"])
        self.assertFalse(proof["legacy_same_parent_order_observed"])
        self.assertTrue(proof["checks"]["cross_stack_same_coordinator"])
        self.assertTrue(proof["checks"]["native_help_override_target"])
        self.assertTrue(proof["checks"]["aligned_route"])
        self.assertTrue(proof["checks"]["typed_eta"])
        self.assertFalse(proof["requester_identity_claimed"])

    def test_bound_classifies_singleton_requester_parent_cannot_ask(self) -> None:
        observations: list[dict[str, object]] = []
        for day_index in range(1, 31):
            pair = _pair(cross_stack=True)
            rejoin = pair["rejoin_frame"]
            anchor = pair["anchor_frame"]
            rejoin["signal"] = {
                "asking_for_help": False,
                "assigned_to_help": False,
            }
            anchor["signal"] = {
                "asking_for_help": False,
                "assigned_to_help": False,
            }
            rejoin["assignment"] = {
                "assignment_target_province_id": None,
                "target_provenance": "none",
                "combat_binding_status": "unbound_until_contact",
                "active_combat_id": None,
            }
            anchor["assignment"] = {
                "assignment_target_province_id": None,
                "target_provenance": "none",
                "combat_binding_status": "already_in_active_combat",
                "active_combat_id": HARNESS.COMBAT_ID,
            }
            observations.append(
                {
                    "day_index": day_index,
                    "snapshot": {
                        "date_raw": DATE_RAW
                        + day_index * HARNESS.ONE_GAME_DAY_RAW
                    },
                    "pair": pair,
                    "battle": {
                        "phase_raw": 1 if day_index <= 27 else 2,
                        "phase_day": day_index + 12 if day_index <= 27 else day_index - 28,
                    },
                    "boundary": {"active": True},
                    "roster": {"ok": True},
                }
            )
        proof = HARNESS._singleton_requester_parent_cannot_ask_proof(
            observations,
            {"ok": True, "available_day_index": 1},
            max_assignment_days=30,
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(
            proof["classification"],
            "singleton_requester_parent_cannot_ask",
        )
        self.assertEqual(proof["post_reopen_observation_count"], 30)
        self.assertEqual(proof["first_date_raw"], DATE_RAW + 24)
        self.assertEqual(proof["last_date_raw"], DATE_RAW + 30 * 24)
        self.assertFalse(proof["requester_identity_claimed"])
        drifted = copy.deepcopy(observations)
        drifted[10]["pair"]["anchor_frame"]["signal"][
            "asking_for_help"
        ] = True
        self.assertFalse(
            HARNESS._singleton_requester_parent_cannot_ask_proof(
                drifted,
                {"ok": True, "available_day_index": 1},
                max_assignment_days=30,
            )["ok"]
        )

    def test_v4_sequence_waits_for_pair_reopen_before_assignment(self) -> None:
        day0 = _snapshot()
        day1 = copy.deepcopy(day0)
        day1["date_raw"] = DATE_RAW + HARNESS.ONE_GAME_DAY_RAW
        day1_army = day1["active_wars"][0]["enemy_armies"][0]
        day1_army["retreating"] = False
        day1_army["army_state_code"] = 1
        day1_army["move_target_province_id"] = PROVINCE_ID
        day1_army["route_province_ids"] = [PROVINCE_ID]
        day2 = copy.deepcopy(day1)
        day2["date_raw"] = DATE_RAW + 2 * HARNESS.ONE_GAME_DAY_RAW
        day2_army = day2["active_wars"][0]["enemy_armies"][0]
        day2_army["in_combat"] = True
        day2_army["army_state_code"] = 2
        day2_army["current_province_id"] = PROVINCE_ID

        battle0 = _battle(phase_raw=1, winner_raw=-1)
        battle1 = copy.deepcopy(battle0)
        battle2 = copy.deepcopy(battle1)
        battle2["defender_public_cunit_ids_in_stored_order"] = [
            HARNESS.ANCHOR_CUNIT_ID,
            HARNESS.REJOIN_CUNIT_ID,
        ]
        mismatch = _pair(available=False, retreating_mismatch=True)
        available = _pair(cross_stack=True)
        bundles = [
            (day0, mismatch, battle0, _terminal(battle0), []),
            (day1, available, battle1, _terminal(battle1, requested_cursor=4), []),
            (day2, available, battle2, _terminal(battle2, requested_cursor=4), []),
        ]

        class FakeService:
            snapshot_calls = 0

            def snapshot(self) -> dict[str, object]:
                self.snapshot_calls += 1
                return day0 if self.snapshot_calls == 1 else day1

            def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
                return {"expected_revision": expected_revision}

        advances = [
            (
                day1,
                {
                    "ok": True,
                    "before_date_raw": DATE_RAW,
                    "after_date_raw": DATE_RAW + HARNESS.ONE_GAME_DAY_RAW,
                },
            ),
            (
                day2,
                {
                    "ok": True,
                    "before_date_raw": DATE_RAW + HARNESS.ONE_GAME_DAY_RAW,
                    "after_date_raw": DATE_RAW
                    + 2 * HARNESS.ONE_GAME_DAY_RAW,
                },
            ),
        ]
        assignment = {
            "ok": True,
            "assignment_eta_date_raw": DATE_RAW
            + 2 * HARNESS.ONE_GAME_DAY_RAW,
            "requester_identity_claimed": False,
        }
        with (
            mock.patch.object(
                HARNESS.rejoin_live,
                "_query_paused_observation_bundle",
                side_effect=bundles,
            ),
            mock.patch.object(
                HARNESS.rejoin_live, "_advance_one_day", side_effect=advances
            ),
            mock.patch.object(
                HARNESS.rejoin_live,
                "_assignment_reopened_proof",
                return_value=assignment,
            ) as assignment_proof,
            mock.patch.object(
                HARNESS.rejoin_live,
                "_same_combat_rejoin_proof",
                return_value={"ok": True},
            ),
            mock.patch.object(
                HARNESS.rejoin_live,
                "_archive_checkpoint",
                side_effect=[{"ok": True}, {"ok": True}],
            ),
        ):
            result = HARNESS._run_ai_assignment_sequence(
                FakeService(),
                wait_after_advance=lambda: day1,
                max_assignment_days=3,
                max_eta_days=3,
                expected_date_raw=DATE_RAW,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["native_pair_reopened_proof"]["ok"])
        self.assertEqual(
            [row["classification"] for row in result["membership_observations"]],
            [
                "retreating_subunit_backlink_mismatch",
                "native_pair_available",
            ],
        )
        self.assertEqual(assignment_proof.call_count, 1)
        self.assertTrue(
            result["readiness_gates"]["native_pair_reopened_live_ready"]
        )
        self.assertTrue(
            result["readiness_gates"][
                "assignment_reopened_aligned_eta_live_ready"
            ]
        )

    def test_final_boundary_allows_only_daily_advance_and_two_saves(self) -> None:
        proof = HARNESS._final_mutation_boundary(
            [
                "life-advance",
                "save-checkpoint",
                "life-advance",
                "save-checkpoint",
            ]
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["forbidden_native_calls_invoked"], [])
        self.assertIn("0x27FB7C0", proof["forbidden_native_calls"])
        self.assertFalse(
            HARNESS._final_mutation_boundary(
                ["life-advance", "direct-join", "save-checkpoint"]
            )["ok"]
        )

    def test_orchestrator_preserves_stage_order_date_source_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-ai-return-stages-") as temporary:
            base = Path(temporary)
            source_state = base / "source"
            source_profile = source_state / "profile"
            source_profile.mkdir(parents=True)
            source_save = source_profile / "last_save.ck3"
            source_save.write_bytes(b"pre-retreat-canonical")
            source_sha = hashlib.sha256(source_save.read_bytes()).hexdigest().upper()
            target = base / "disposable"
            calls: list[tuple[object, ...]] = []

            def prepare_stage(
                *,
                source_profile: Path,
                target_state: Path,
                game_dir: Path,
                save_source: Path,
                save_name: str,
            ) -> tuple[object, dict[str, object]]:
                calls.append(("prepare", target_state.name, save_source.name))
                target_state.mkdir(parents=True)
                profile = target_state / "profile"
                save_dir = profile / "save games"
                save_dir.mkdir(parents=True)
                (save_dir / save_name).write_bytes(save_source.read_bytes())
                return (
                    SimpleNamespace(
                        state_dir=target_state,
                        profile_dir=profile,
                        game_exe=game_dir / "binaries" / "ck3.exe",
                    ),
                    {"stage": target_state.name},
                )

            def checkpoint(spec: object, payload: bytes) -> None:
                path = HARNESS.owner_live._checkpoint_path(spec)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)

            def retreat_stage(**kwargs: object) -> dict[str, object]:
                spec = kwargs["spec"]
                calls.append(("retreat",))
                checkpoint(spec, b"retreated")
                return {
                    "ok": True,
                    "cleanup": {"ok": True},
                    "body": {"date_raw": DATE_RAW},
                }

            def seed_stage(**kwargs: object) -> dict[str, object]:
                spec = kwargs["spec"]
                calls.append(("seed", kwargs["expected_date_raw"]))
                checkpoint(spec, b"returned")
                return {"ok": True, "cleanup": {"ok": True}, "body": {}}

            def canonical_stage(**kwargs: object) -> dict[str, object]:
                spec = kwargs["spec"]
                calls.append(("canonical", kwargs["expected_date_raw"]))
                checkpoint(spec, b"ai-canonical")
                return {
                    "ok": True,
                    "cleanup": {"ok": True},
                    "body": {
                        "ai_control_proof": {
                            "ok": True,
                            "retreating_membership_transient": {"ok": True},
                        }
                    },
                }

            def final_stage(**kwargs: object) -> dict[str, object]:
                calls.append(("final", kwargs["expected_date_raw"]))
                return {
                    "ok": True,
                    "cleanup": {"ok": True},
                    "body": {
                        "sequence": {
                            "native_pair_reopened_proof": {"ok": True},
                            "assignment_proof": {"ok": True},
                            "join_proof": {"ok": True},
                        }
                    },
                }

            args = SimpleNamespace(
                source_state_dir=source_state,
                state_dir=target,
                game_dir=base / "game",
                battle_save=Path("last_save.ck3"),
                expected_battle_save_sha256=source_sha,
                bridge_pipe="ai-return-stage-fake",
                bridge_dll=base / "bridge.dll",
                bridge_injector=base / "injector.exe",
                output=base / "artifact.json",
                timeout=10.0,
                readiness_timeout=2.0,
                seed_timeout=2.0,
                postcondition_timeout=1.0,
                max_assignment_days=2,
                max_eta_days=2,
                retain_state=False,
            )
            with (
                mock.patch.object(
                    HARNESS.owner_live,
                    "_prepare_stage",
                    side_effect=prepare_stage,
                ),
                mock.patch.object(
                    HARNESS.owner_live,
                    "_install_seed_bridge",
                    return_value={"ok": True},
                ),
                mock.patch.object(
                    HARNESS,
                    "_run_retreat_checkpoint_stage",
                    side_effect=retreat_stage,
                ),
                mock.patch.object(
                    HARNESS,
                    "_run_return_seed_stage",
                    side_effect=seed_stage,
                ),
                mock.patch.object(
                    HARNESS,
                    "_run_ai_canonical_stage",
                    side_effect=canonical_stage,
                ),
                mock.patch.object(
                    HARNESS,
                    "_run_final_assignment_stage",
                    side_effect=final_stage,
                ),
                mock.patch.object(
                    HARNESS.owner_live, "ck3_processes", return_value=[]
                ),
            ):
                payload, exit_code = HARNESS._run(args)

            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(source_save.read_bytes(), b"pre-retreat-canonical")
            self.assertEqual(payload["source_save"]["before_sha256"], source_sha)
            self.assertEqual(payload["source_save"]["after_sha256"], source_sha)
            self.assertEqual(
                [row[0] for row in calls if row[0] != "prepare"],
                ["retreat", "seed", "canonical", "final"],
            )
            self.assertEqual(
                [row[1] for row in calls if row[0] in {"seed", "canonical", "final"}],
                [DATE_RAW, DATE_RAW, DATE_RAW],
            )
            self.assertFalse(target.exists())
            self.assertTrue(payload["state_cleanup"]["ok"])


if __name__ == "__main__":
    unittest.main()
