from __future__ import annotations

import hashlib
import importlib.util
import inspect
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_three_cunit_owner_subset_reassignment_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_three_cunit_owner_subset_reassignment_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


DATE_RAW = 53_175_816
COMBAT_ID = 335_544_399
SIBLING_ID = 67_108_901


def _army(
    public_id: int,
    owner_id: int,
    *,
    controllable: bool,
    in_combat: bool = False,
    retreating: bool = False,
    current: int = 2_564,
    target: int | None = None,
    route: list[int] | None = None,
) -> dict[str, object]:
    return {
        "army_id": public_id,
        "owner_character_id": owner_id,
        "current_province_id": current,
        "move_target_province_id": target,
        "route_province_ids": list(route or []),
        "controllable": controllable,
        "in_combat": in_combat,
        "retreating": retreating,
        "army_state_code": 6 if retreating else 2 if in_combat else 3,
    }


def _snapshot(
    armies: list[dict[str, object]],
    *,
    played: int = HARNESS.RETAINED_CHARACTER_ID,
    revision: int = 10,
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}",
        "revision": revision + 1,
        "native_revision": revision,
        "date_raw": DATE_RAW,
        "paused": True,
        "episode_run_id": "three-cunit-fake",
        "played_character": {"character_id": played},
        "player_armies": armies,
        "active_wars": [],
    }


def _native_rows(*, collapsed: bool = False) -> list[dict[str, object]]:
    ids = [
        HARNESS.REQUESTER_CUNIT_ID,
        HARNESS.ANCHOR_CUNIT_ID,
        SIBLING_ID,
    ]
    groups = [[ids[0]], [ids[1], ids[2]]] if collapsed else [[value] for value in ids]
    return [
        {
            "public_cunit_ids_in_stored_order": group,
            "asking_for_help": False,
            "assigned_to_help": False,
            "assignment_target_province_id": None,
        }
        for group in groups
    ]


def _membership_result(
    selected: int,
    sequence: int,
    *,
    collapsed: bool = False,
) -> dict[str, object]:
    rows = _native_rows(collapsed=collapsed)
    selected_row = next(
        index
        for index, row in enumerate(rows)
        if selected in row["public_cunit_ids_in_stored_order"]
    )
    return {
        "query_sequence": sequence,
        "battle_reinforcement_assignment": {
            "status": "available",
            "unavailable_reason": None,
            "battle_reinforcement_assignment_ready": True,
            "selected_public_cunit_id": selected,
            # This identifies the selected CUnit's own native CArmy, not the
            # shared CAIUnitStack parent.  Keep the three fixtures distinct so
            # the parent proof cannot regress to comparing these IDs.
            "selected_native_carmy_id": 1_000 + sequence,
            "coordinator_id": 33_554_513,
            "unit_stack_stored_index": 0,
            "subunit_stored_index": selected_row,
            "snapshot_revision": 10,
            "observed_date_raw": DATE_RAW,
            "native_order": {
                "support_search_province_ids_in_stored_order": [2_596],
                "parent_subunits_in_stored_order": rows,
            },
        },
    }


def _battle() -> dict[str, object]:
    return {
        "status": "available",
        "battle_transition_ready": True,
        "combat_id": COMBAT_ID,
        "province_id": 2_596,
        "phase_raw": 1,
        "phase_day": 0,
        "winner_raw": -1,
        "finalized": False,
        "attacker_public_cunit_ids_in_stored_order": [
            HARNESS.OPPOSITE_CUNIT_ID
        ],
        "defender_public_cunit_ids_in_stored_order": [
            HARNESS.ANCHOR_CUNIT_ID,
            SIBLING_ID,
            HARNESS.REQUESTER_CUNIT_ID,
        ],
    }


class ThreeCunitOwnerSubsetTests(unittest.TestCase):
    def test_dynamic_ally_switch_discovers_unique_nonprimary_defender(self) -> None:
        effect = HARNESS._dynamic_ally_switch_effect()
        self.assertIn("every_character_war", effect)
        self.assertIn("primary_defender", effect)
        self.assertIn("every_war_defender", effect)
        self.assertIn(f"global_var:{HARNESS.ALLY_CANDIDATE_COUNT} = 1", effect)
        self.assertIn("set_player_character = scope:", effect)
        self.assertNotIn("character:28180", effect)
        self.assertNotIn("play 28180", effect)

    def test_split_postcondition_requires_exact_dynamic_plus_one(self) -> None:
        anchor = _army(
            HARNESS.ANCHOR_CUNIT_ID,
            HARNESS.RETAINED_CHARACTER_ID,
            controllable=True,
        )
        sibling = _army(
            SIBLING_ID,
            HARNESS.RETAINED_CHARACTER_ID,
            controllable=True,
        )
        before = _snapshot([anchor], revision=9)
        after = _snapshot([anchor, sibling], revision=10)
        result = {
            "accepted": True,
            "war_action": {
                "status": "split_applied",
                "source_army_id": HARNESS.ANCHOR_CUNIT_ID,
                "sibling_army_id": SIBLING_ID,
            },
        }
        proof = HARNESS._split_postcondition_proof(before, after, result)
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["sibling_cunit_id"], SIBLING_ID)
        extra = _army(
            SIBLING_ID + 1,
            HARNESS.RETAINED_CHARACTER_ID,
            controllable=True,
        )
        self.assertFalse(
            HARNESS._split_postcondition_proof(
                before, _snapshot([anchor, sibling, extra], revision=10), result
            )["ok"]
        )

    def test_pre_split_control_gate_rejects_noncontrollable_anchor(self) -> None:
        snapshot = _snapshot(
            [
                _army(
                    HARNESS.ANCHOR_CUNIT_ID,
                    HARNESS.RETAINED_CHARACTER_ID,
                    controllable=False,
                )
            ]
        )
        proof = HARNESS._precontact_army_proof(
            snapshot,
            HARNESS.ANCHOR_CUNIT_ID,
            owner_character_id=HARNESS.RETAINED_CHARACTER_ID,
            controllable=True,
        )
        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["control"])

    def test_capability_proof_keeps_lifecycle_steps_out_of_bridge_claims(self) -> None:
        split_step = HARNESS.split_army_half_step(HARNESS.ANCHOR_CUNIT_ID)
        capabilities = {
            "bridge_capabilities": [HARNESS.SPLIT_ARMY_HALF_CAPABILITY],
            "diagnostics": {
                "hello": {
                    "capabilities": [HARNESS.SPLIT_ARMY_HALF_CAPABILITY]
                }
            },
            "action_steps": [split_step, "life-advance", "save-checkpoint"],
        }
        proof = HARNESS._stage_capability_proof(
            capabilities,
            exact_steps=[split_step, "life-advance", "save-checkpoint"],
            required=[HARNESS.SPLIT_ARMY_HALF_CAPABILITY],
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(
            proof["required_bridge_capabilities"],
            [HARNESS.SPLIT_ARMY_HALF_CAPABILITY],
        )
        self.assertNotIn("life-advance", proof["required_bridge_capabilities"])
        self.assertNotIn("save-checkpoint", proof["required_bridge_capabilities"])

    def test_three_cunit_parent_requires_three_distinct_native_rows(self) -> None:
        snapshot = _snapshot([], revision=10)
        results = [
            _membership_result(HARNESS.REQUESTER_CUNIT_ID, 11),
            _membership_result(HARNESS.ANCHOR_CUNIT_ID, 12),
            _membership_result(SIBLING_ID, 13),
        ]
        proof = HARNESS._three_cunit_parent_proof(
            snapshot,
            results,
            _battle(),
            sibling_cunit_id=SIBLING_ID,
            combat_id=COMBAT_ID,
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(
            len(
                {
                    row["battle_reinforcement_assignment"][
                        "selected_native_carmy_id"
                    ]
                    for row in results
                }
            ),
            3,
        )
        self.assertEqual(proof["requester_parent_subunit_count"], 3)
        self.assertEqual(
            proof["retained_same_side_order"],
            [HARNESS.ANCHOR_CUNIT_ID, SIBLING_ID],
        )

        collapsed = [
            _membership_result(
                HARNESS.REQUESTER_CUNIT_ID, 11, collapsed=True
            ),
            _membership_result(HARNESS.ANCHOR_CUNIT_ID, 12, collapsed=True),
            _membership_result(SIBLING_ID, 13, collapsed=True),
        ]
        red = HARNESS._three_cunit_parent_proof(
            snapshot,
            collapsed,
            _battle(),
            sibling_cunit_id=SIBLING_ID,
            combat_id=COMBAT_ID,
        )
        self.assertFalse(red["ok"])
        self.assertEqual(red["classification"], "fixture_subunit_structure_insufficient")
        self.assertFalse(
            red["checks"]["requester_parent_has_at_least_three_subunit_rows"]
        )
        self.assertFalse(red["checks"]["three_expected_cunits_in_distinct_rows"])
        inconsistent = [dict(row) for row in results]
        inconsistent[2] = {
            **results[2],
            "battle_reinforcement_assignment": {
                **results[2]["battle_reinforcement_assignment"],
                "unit_stack_stored_index": 1,
            },
        }
        different_parent = HARNESS._three_cunit_parent_proof(
            snapshot,
            inconsistent,
            _battle(),
            sibling_cunit_id=SIBLING_ID,
            combat_id=COMBAT_ID,
        )
        self.assertFalse(different_parent["ok"])
        self.assertFalse(
            different_parent["checks"]["same_requester_parent_identity"]
        )

    def test_requester_query_restarts_only_after_fresh_same_day_heartbeat(self) -> None:
        stale = _snapshot([], revision=9)
        fresh = _snapshot([], revision=10)
        result = _membership_result(HARNESS.REQUESTER_CUNIT_ID, 4)

        class FakeService:
            query_calls = 0

            def query_battle_reinforcement_assignment_v1(
                self, public_id: int, *, expected_revision: int
            ) -> dict[str, object]:
                self.query_calls += 1
                self.assertions.append((public_id, expected_revision))
                if self.query_calls == 1:
                    raise RuntimeError(
                        "battle-reinforcement snapshot changed; retry after heartbeat"
                    )
                return result

            def snapshot(self) -> dict[str, object]:
                return fresh

            def __init__(self) -> None:
                self.assertions: list[tuple[int, int]] = []

        service = FakeService()
        observed, returned, retries = HARNESS._query_requester_membership(
            service, stale, retry_attempts=2, retry_timeout_seconds=1.0
        )
        self.assertIs(observed, fresh)
        self.assertIs(returned, result)
        self.assertEqual(
            service.assertions,
            [
                (HARNESS.REQUESTER_CUNIT_ID, stale["revision"]),
                (HARNESS.REQUESTER_CUNIT_ID, fresh["revision"]),
            ],
        )
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0]["restart_scope"], "requester_membership_query")

    def test_retained_parent_capacity_requires_two_distinct_rows(self) -> None:
        frame = _membership_result(HARNESS.ANCHOR_CUNIT_ID, 1)[
            "battle_reinforcement_assignment"
        ]
        pair = {"anchor_frame": frame}
        proof = HARNESS._retained_parent_capacity_proof(
            pair, sibling_cunit_id=SIBLING_ID
        )
        self.assertTrue(proof["ok"])
        self.assertGreaterEqual(proof["subunit_count"], 2)
        collapsed = _membership_result(
            HARNESS.ANCHOR_CUNIT_ID, 1, collapsed=True
        )["battle_reinforcement_assignment"]
        red = HARNESS._retained_parent_capacity_proof(
            {"anchor_frame": collapsed}, sibling_cunit_id=SIBLING_ID
        )
        self.assertFalse(red["ok"])

    def test_same_day_switch_and_ai_control_gates_are_semantic(self) -> None:
        precontact = [
            _army(
                HARNESS.OPPOSITE_CUNIT_ID,
                HARNESS.ORIGINAL_CHARACTER_ID,
                controllable=False,
            ),
            _army(
                HARNESS.REQUESTER_CUNIT_ID,
                HARNESS.REQUESTER_CHARACTER_ID,
                controllable=False,
            ),
            _army(
                HARNESS.ANCHOR_CUNIT_ID,
                HARNESS.RETAINED_CHARACTER_ID,
                controllable=True,
            ),
        ]
        switched = HARNESS._single_anchor_switch_proof(
            _snapshot(precontact, played=HARNESS.RETAINED_CHARACTER_ID),
            played_character_id=HARNESS.RETAINED_CHARACTER_ID,
            anchor_controllable=True,
        )
        self.assertTrue(switched["ok"])

        post_retreat = _snapshot(
            [
                _army(
                    HARNESS.REQUESTER_CUNIT_ID,
                    HARNESS.REQUESTER_CHARACTER_ID,
                    controllable=False,
                    retreating=True,
                    current=2_586,
                    target=HARNESS.RETREAT_PROVINCE_ID,
                    route=[HARNESS.RETREAT_PROVINCE_ID],
                ),
                _army(
                    HARNESS.ANCHOR_CUNIT_ID,
                    HARNESS.RETAINED_CHARACTER_ID,
                    controllable=False,
                    in_combat=True,
                ),
                _army(
                    SIBLING_ID,
                    HARNESS.RETAINED_CHARACTER_ID,
                    controllable=False,
                    in_combat=True,
                ),
            ],
            played=HARNESS.ORIGINAL_CHARACTER_ID,
        )
        ai = HARNESS._post_retreat_switch_proof(
            post_retreat,
            played_character_id=HARNESS.ORIGINAL_CHARACTER_ID,
            sibling_cunit_id=SIBLING_ID,
        )
        self.assertTrue(ai["ok"])
        post_retreat["player_armies"] = [post_retreat["player_armies"][0]]
        post_retreat["player_armies"][0]["controllable"] = True
        self.assertFalse(
            HARNESS._post_retreat_switch_proof(
                post_retreat,
                played_character_id=HARNESS.ORIGINAL_CHARACTER_ID,
                sibling_cunit_id=SIBLING_ID,
            )["ok"]
        )

    def test_split_and_retreat_calls_are_textually_after_hard_gates(self) -> None:
        split_source = inspect.getsource(HARNESS._run_split_route_stage)
        self.assertLess(
            split_source.index("before_split_control ="),
            split_source.index("split_result = service.execute_step"),
        )
        self.assertIn("before_split_control.get(\"ok\") is True", split_source)
        retreat_source = inspect.getsource(HARNESS._run_contact_retreat_stage)
        hard_gate = retreat_source.index("retreat loop escaped without all hard gates")
        retreat_call = retreat_source.index(
            "preview = service.preview_active_combat_retreat_v1"
        )
        self.assertLess(hard_gate, retreat_call)
        self.assertIn("parent_proof.get(\"ok\") is True", retreat_source)
        self.assertIn("control_proof.get(\"ok\") is True", retreat_source)

    def test_orchestrator_preserves_seven_stage_order_and_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-three-cunit-stages-") as temporary:
            base = Path(temporary)
            source_state = base / "source"
            source_profile = source_state / "profile"
            source_profile.mkdir(parents=True)
            source_save = source_profile / "last_save.ck3"
            source_save.write_bytes(b"immutable-precontact")
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
                profile = target_state / "profile"
                (profile / "save games").mkdir(parents=True)
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

            def stage(name: str, body: dict[str, object], payload: bytes):
                def run(**kwargs: object) -> dict[str, object]:
                    calls.append((name, kwargs.get("expected_date_raw")))
                    if name != "final":
                        checkpoint(kwargs["spec"], payload)
                    return {"ok": True, "cleanup": {"ok": True}, "body": body}

                return run

            seed_names = iter(
                [
                    ("ally", b"ally"),
                    ("requester", b"requester"),
                    ("return", b"return"),
                ]
            )

            def seed_stage(**kwargs: object) -> dict[str, object]:
                name, payload = next(seed_names)
                calls.append((name, kwargs.get("expected_date_raw")))
                checkpoint(kwargs["spec"], payload)
                return {
                    "ok": True,
                    "cleanup": {"ok": True},
                    "body": {"ok": True},
                }

            args = SimpleNamespace(
                source_state_dir=source_state,
                state_dir=target,
                game_dir=base / "game",
                battle_save=Path("last_save.ck3"),
                expected_battle_save_sha256=source_sha,
                bridge_pipe="three-cunit-fake",
                bridge_dll=base / "bridge.dll",
                bridge_injector=base / "injector.exe",
                max_split_wait_days=2,
                max_contact_days=2,
                max_assignment_days=2,
                max_eta_days=2,
                timeout=10.0,
                readiness_timeout=2.0,
                seed_timeout=2.0,
                postcondition_timeout=1.0,
                route_timeout=1.0,
                output=base / "artifact.json",
                retain_state=False,
            )
            with (
                mock.patch.object(HARNESS.owner_live, "_prepare_stage", side_effect=prepare_stage),
                mock.patch.object(HARNESS.owner_live, "_install_seed_bridge", return_value={"ok": True}),
                mock.patch.object(HARNESS, "_run_route_clear_stage", side_effect=stage("route", {"ok": True, "date_raw": DATE_RAW}, b"route")),
                mock.patch.object(
                    HARNESS, "_run_seed_switch_stage", side_effect=seed_stage
                ),
                mock.patch.object(HARNESS, "_run_split_route_stage", side_effect=stage("split", {
                    "ok": True,
                    "date_raw": DATE_RAW + HARNESS.ONE_GAME_DAY_RAW,
                    "sibling_cunit_id": SIBLING_ID,
                    "before_split_control_proof": {"ok": True},
                }, b"split")),
                mock.patch.object(HARNESS, "_run_contact_retreat_stage", side_effect=stage("retreat", {
                    "ok": True,
                    "date_raw": DATE_RAW + 2 * HARNESS.ONE_GAME_DAY_RAW,
                    "combat_id": COMBAT_ID,
                    "combat_province_id": 2_596,
                    "retained_same_side_order": [HARNESS.ANCHOR_CUNIT_ID, SIBLING_ID],
                    "parent_proof_immediately_before_retreat": {"ok": True},
                    "control_proof_immediately_before_retreat": {"ok": True},
                }, b"retreat")),
                mock.patch.object(HARNESS, "_run_final_reassignment_stage", side_effect=stage("final", {
                    "ok": True,
                    "readiness_gates": {
                        "retained_parent_can_ask_live_ready": True,
                        "assignment_reopened_aligned_eta_live_ready": True,
                        "same_combat_rejoin_live_ready": True,
                        "one_pid_generation_live_ready": True,
                    },
                }, b"final")),
                mock.patch.object(HARNESS, "ck3_processes", return_value=[]),
            ):
                payload, exit_code = HARNESS._run(args)

            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(source_save.read_bytes(), b"immutable-precontact")
            self.assertEqual(payload["source_save"]["before_sha256"], source_sha)
            self.assertEqual(payload["source_save"]["after_sha256"], source_sha)
            self.assertEqual(
                [row[0] for row in calls if row[0] != "prepare"],
                [
                    "route",
                    "ally",
                    "split",
                    "requester",
                    "retreat",
                    "return",
                    "final",
                ],
            )
            self.assertEqual(
                [
                    row[1]
                    for row in calls
                    if row[0] in {"ally", "requester", "return", "final"}
                ],
                [
                    DATE_RAW,
                    DATE_RAW + HARNESS.ONE_GAME_DAY_RAW,
                    DATE_RAW + 2 * HARNESS.ONE_GAME_DAY_RAW,
                    DATE_RAW + 2 * HARNESS.ONE_GAME_DAY_RAW,
                ],
            )
            self.assertFalse(target.exists())
            self.assertTrue(payload["state_cleanup"]["ok"])


if __name__ == "__main__":
    unittest.main()
