from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_battle_reinforcement_join_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_battle_reinforcement_join_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


COMBAT_ID = 335_544_325
START_DATE = 53_175_816


class _FakeReinforcementService:
    def __init__(
        self,
        checkpoint_dir: Path,
        *,
        contact_day: int = 2,
        assignment_day: int = 3,
        join_day: int = 5,
        date_delta_raw: int = 24,
    ) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.contact_day = contact_day
        self.assignment_day = assignment_day
        self.join_day = join_day
        self.date_delta_raw = date_delta_raw
        self.day = 0
        self.revision = 7
        self.date_raw = START_DATE
        self.player_route_cleared = False
        self.query_sequence = 0
        self.calls: list[tuple[object, ...]] = []
        self.revision_bindings: list[tuple[str, int, int]] = []

    def _assert_revision(self, kind: str, expected: int) -> None:
        self.revision_bindings.append((kind, expected, self.revision))
        if expected != self.revision:
            raise AssertionError(
                f"{kind} expected revision {expected}, current {self.revision}"
            )

    @staticmethod
    def _army(
        army_id: int,
        current: int,
        route: list[int],
        *,
        controllable: bool,
        in_combat: bool,
    ) -> dict[str, object]:
        return {
            "army_id": army_id,
            "owner_character_id": 29_829 if controllable else 36_108,
            "soldiers": 1_000,
            "current_province_id": current,
            "move_target_province_id": route[-1] if route else None,
            "move_target_observable": bool(route),
            "controllable": controllable,
            "source": "native",
            "route_province_ids": list(route),
            "in_combat": in_combat,
            "retreating": False,
            "army_state": "combat" if in_combat else "moving",
            "army_state_code": 2 if in_combat else 1,
        }

    def _player(self) -> dict[str, object]:
        route = [] if self.player_route_cleared else list(
            HARNESS.EXPECTED_PLAYER_ROUTE
        )
        return self._army(
            HARNESS.PLAYER_CUNIT_ID,
            HARNESS.TARGET_PROVINCE_ID,
            route,
            controllable=True,
            in_combat=self.day >= self.contact_day,
        )

    def _requester(self) -> dict[str, object]:
        if self.day == 0:
            current = 2564
            route = list(HARNESS.EXPECTED_REQUESTER_ROUTE)
        elif self.day < self.contact_day:
            current = 2587
            route = [2597, HARNESS.TARGET_PROVINCE_ID]
        else:
            current = HARNESS.TARGET_PROVINCE_ID
            route = []
        return self._army(
            HARNESS.REQUESTER_CUNIT_ID,
            current,
            route,
            controllable=False,
            in_combat=self.day >= self.contact_day,
        )

    def _helper(self) -> dict[str, object]:
        if self.day == 0:
            current = 2564
            route = list(HARNESS.EXPECTED_HELPER_ROUTE)
        elif self.day < self.assignment_day:
            current = 2564
            route = [2581]
        elif self.day < self.join_day - 1:
            current = 2582
            route = [2587, 2597, HARNESS.TARGET_PROVINCE_ID]
        elif self.day < self.join_day:
            current = 2597
            route = [HARNESS.TARGET_PROVINCE_ID]
        else:
            current = HARNESS.TARGET_PROVINCE_ID
            route = []
        return self._army(
            HARNESS.HELPER_CUNIT_ID,
            current,
            route,
            controllable=False,
            in_combat=self.day >= self.join_day,
        )

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
            "episode_run_id": "reinforcement-join-fixture",
            "active_event": None,
            "player_armies": [self._player()],
            "active_wars": [
                {
                    "war_id": 16_777_290,
                    "allied_armies": [],
                    "enemy_armies": [self._requester(), self._helper()],
                }
            ],
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("execute", step, expected_revision))
        self._assert_revision(step, expected_revision)
        if step == (
            f"preview-move-army-{HARNESS.PLAYER_CUNIT_ID}-to-"
            f"{HARNESS.TARGET_PROVINCE_ID}"
        ):
            return {
                "step": step,
                "accepted": True,
                "status": "available",
                "route_preview": {
                    "status": "available",
                    "army_id": HARNESS.PLAYER_CUNIT_ID,
                    "origin_province_id": HARNESS.TARGET_PROVINCE_ID,
                    "target_province_id": HARNESS.TARGET_PROVINCE_ID,
                    "route_province_ids": [],
                },
            }
        if step != "life-advance":
            raise AssertionError(f"unexpected execute step {step}")
        before = self.date_raw
        self.day += 1
        self.revision += 1
        self.date_raw += self.date_delta_raw
        return {
            "step": "life-advance",
            "accepted": True,
            "starting_date_raw": before,
            "ending_date_raw": self.date_raw,
            "elapsed_days": self.date_delta_raw // 24,
            "paused": True,
        }

    def move_army(
        self,
        army_id: int,
        target_province_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append(
            ("move", army_id, target_province_id, expected_revision)
        )
        self._assert_revision("move", expected_revision)
        if (
            army_id != HARNESS.PLAYER_CUNIT_ID
            or target_province_id != HARNESS.TARGET_PROVINCE_ID
        ):
            raise AssertionError("runner changed fixed move geometry")
        self.player_route_cleared = True
        self.revision += 1
        return {
            "step": (
                f"move-army-{army_id}-to-{target_province_id}"
            ),
            "accepted": True,
            "status": "accepted",
            "war_action": {
                "status": "arrived",
                "army_id": army_id,
                "target_province_id": target_province_id,
            },
        }

    def _native_rows(self) -> list[dict[str, object]]:
        requester_asking = self.day >= self.contact_day
        helper_assigned = (
            self.assignment_day <= self.day < self.join_day
        )
        return [
            {
                "public_cunit_ids_in_stored_order": [
                    HARNESS.REQUESTER_CUNIT_ID
                ],
                "asking_for_help": requester_asking,
                "assigned_to_help": False,
                "assignment_target_province_id": None,
            },
            {
                "public_cunit_ids_in_stored_order": [HARNESS.HELPER_CUNIT_ID],
                "asking_for_help": False,
                "assigned_to_help": helper_assigned,
                "assignment_target_province_id": (
                    HARNESS.TARGET_PROVINCE_ID if helper_assigned else None
                ),
            },
        ]

    def _reinforcement_frame(self, selected: int) -> dict[str, object]:
        requester = selected == HARNESS.REQUESTER_CUNIT_ID
        active = (
            self.day >= self.contact_day
            if requester
            else self.day >= self.join_day
        )
        helper_assigned = (
            not requester
            and self.assignment_day <= self.day < self.join_day
        )
        semantic = self._requester() if requester else self._helper()
        route_ids = list(semantic["route_province_ids"])
        if helper_assigned:
            eta = START_DATE + self.join_day * 24
            arrivals = [
                eta - (len(route_ids) - index - 1) * 24
                for index in range(len(route_ids))
            ]
            route_alignment = "aligned_to_assignment"
            native_target = HARNESS.TARGET_PROVINCE_ID
        else:
            eta = None
            arrivals = [
                self.date_raw + (index + 1) * 24
                for index in range(len(route_ids))
            ]
            route_alignment = "no_assignment"
            native_target = (
                semantic["move_target_province_id"]
                if route_ids
                else None
            )
        rows = self._native_rows()
        signal_row = rows[0 if requester else 1]
        return {
            "schema_version": 1,
            "contract_stage": "production_exact_ai_reinforcement_assignment",
            "status": "available",
            "unavailable_reason": None,
            "battle_reinforcement_assignment_ready": True,
            "snapshot_revision": self.revision,
            "observed_date_raw": self.date_raw,
            "selected_public_cunit_id": selected,
            "selected_native_carmy_id": 344 if requester else 50_331_769,
            "coordinator_id": 33_554_513,
            "unit_stack_stored_index": 0,
            "subunit_stored_index": 0 if requester else 1,
            "signal": {
                "asking_for_help": signal_row["asking_for_help"],
                "assigned_to_help": signal_row["assigned_to_help"],
                "asking_changed_last_evaluation": False,
                "request_power_basis_raw": (
                    5_278_400_000
                    if signal_row["asking_for_help"]
                    else None
                ),
                "cross_coordinator_request_valid_raw": 0,
                "cross_coordinator_request_power_raw": None,
                "first_route_edge_remaining_duration_q100000": (
                    100_000 if route_ids else None
                ),
            },
            "assignment": {
                "assignment_target_province_id": (
                    HARNESS.TARGET_PROVINCE_ID if helper_assigned else None
                ),
                "target_provenance": (
                    "native_help_override" if helper_assigned else "none"
                ),
                "combat_binding_status": (
                    "already_in_active_combat"
                    if active
                    else "unbound_until_contact"
                ),
                "active_combat_id": COMBAT_ID if active else None,
            },
            "route": {
                "current_province_id": semantic["current_province_id"],
                "move_target_province_id": native_target,
                "route_province_ids": route_ids,
                "route_alignment": route_alignment,
                "arrival_date_raws": arrivals,
                "assignment_eta_date_raw": eta,
            },
            "native_order": {
                "support_search_province_ids_in_stored_order": [],
                "parent_subunits_in_stored_order": rows,
            },
            "contact_projection": {
                "status": "not_applicable",
                "temporal_semantics": "present_time_only_not_future_binding",
                "current_target_compatible_combat_ids_in_stored_order": [],
                "contact_if_now_selected_combat_id": None,
            },
        }

    def query_battle_reinforcement_assignment_v1(
        self, selected_public_cunit_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(
            ("reinforcement", selected_public_cunit_id, expected_revision)
        )
        self._assert_revision("reinforcement", expected_revision)
        self.query_sequence += 1
        frame = self._reinforcement_frame(selected_public_cunit_id)
        return {
            "status": "available",
            "query_sequence": self.query_sequence,
            "snapshot_revision": self.revision,
            "battle_reinforcement_assignment": frame,
        }

    def _battle_frame(self) -> dict[str, object]:
        joined = self.day >= self.join_day
        return {
            "schema_version": 1,
            "contract_stage": "production_exact_combat_lifecycle",
            "status": "available",
            "battle_transition_ready": True,
            "snapshot_revision": self.revision,
            "observed_date_raw": self.date_raw,
            "combat_id": COMBAT_ID,
            "province_id": HARNESS.TARGET_PROVINCE_ID,
            "phase": "main",
            "phase_raw": 1,
            "phase_day": max(0, self.day - self.contact_day),
            "winner_side": "none",
            "winner_raw": -1,
            "forced_winner_side": "none",
            "forced_winner_raw": -1,
            "finalized": False,
            "battle_result_id": None,
            "attacker_public_cunit_ids_in_stored_order": [
                HARNESS.REQUESTER_CUNIT_ID,
                *([HARNESS.HELPER_CUNIT_ID] if joined else []),
            ],
            "defender_public_cunit_ids_in_stored_order": [
                HARNESS.PLAYER_CUNIT_ID
            ],
        }

    def query_battle_transition_v1(
        self, combat_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("battle", combat_id, expected_revision))
        self._assert_revision("battle", expected_revision)
        if combat_id != COMBAT_ID or self.day < self.contact_day:
            raise AssertionError("unexpected combat query")
        return {
            "status": "available",
            "query_sequence": self.query_sequence + 1,
            "battle_transition_snapshot": self._battle_frame(),
        }

    def query_battle_terminal_transition_v1(
        self,
        prior_combat_id: int,
        subject_public_cunit_id: int,
        *,
        expected_revision: int,
        after_terminal_sequence: int | None = None,
    ) -> dict[str, object]:
        self.calls.append(
            (
                "terminal",
                prior_combat_id,
                subject_public_cunit_id,
                expected_revision,
                after_terminal_sequence,
            )
        )
        self._assert_revision("terminal", expected_revision)
        battle = self._battle_frame()
        return {
            "status": "available",
            "battle_terminal_transition": {
                "status": "available",
                "battle_terminal_transition_ready": True,
                "prior_combat_id": COMBAT_ID,
                "subject_public_cunit_id": HARNESS.REQUESTER_CUNIT_ID,
                "terminal_journal": {
                    "requested_after_sequence": after_terminal_sequence,
                    "oldest_available_sequence": 1,
                    "latest_sequence": 4,
                    "event_sequence": None,
                    "event_status": "not_observed",
                },
                "prior": {
                    "combat_id": COMBAT_ID,
                    "terminal_kind": "active_not_terminal",
                    "attacker_public_cunit_ids_in_stored_order": battle[
                        "attacker_public_cunit_ids_in_stored_order"
                    ],
                    "defender_public_cunit_ids_in_stored_order": battle[
                        "defender_public_cunit_ids_in_stored_order"
                    ],
                },
                "removal": {"prior_combat_strictly_resolves": True},
            },
        }

    def save_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("save", expected_revision))
        self._assert_revision("save", expected_revision)
        path = self.checkpoint_dir / "xar_checkpoint.ck3"
        path.write_bytes(f"checkpoint-day-{self.day}".encode("ascii"))
        payload = path.read_bytes()
        return {
            "step": "save-checkpoint",
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": str(path.resolve()),
                "name": path.name,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest().upper(),
                "date_raw": self.date_raw,
            },
        }


class BattleReinforcementJoinLiveAcceptanceTests(unittest.TestCase):
    def _run(
        self,
        service: _FakeReinforcementService,
        *,
        route_clear_timeout: float = 0.05,
    ) -> dict[str, object]:
        return HARNESS._run_reinforcement_join_sequence(
            service,
            wait_after_advance=service.snapshot,
            max_contact_days=5,
            max_assignment_days=5,
            max_eta_days=5,
            route_clear_timeout=route_clear_timeout,
        )

    def test_full_sequence_proves_assignment_eta_and_actual_tail_join(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _FakeReinforcementService(Path(temporary))

            result = self._run(service)

            self.assertTrue(result["ok"])
            self.assertEqual(result["contact_combat_id"], COMBAT_ID)
            self.assertEqual(result["assigned_date_raw"], START_DATE + 3 * 24)
            self.assertEqual(
                result["assignment_eta_date_raw"], START_DATE + 5 * 24
            )
            self.assertEqual(result["joined_date_raw"], START_DATE + 5 * 24)
            self.assertTrue(result["assignment_proof"]["ok"])
            self.assertTrue(result["join_proof"]["ok"])
            self.assertEqual(
                result["join_proof"]["same_side_joined"],
                [HARNESS.REQUESTER_CUNIT_ID, HARNESS.HELPER_CUNIT_ID],
            )
            self.assertEqual(len(result["advances"]), 5)
            self.assertTrue(
                all(row["date_delta_raw"] == 24 for row in result["advances"])
            )
            self.assertTrue(
                Path(result["assigned_checkpoint"]["archive_path"]).is_file()
            )
            self.assertTrue(
                Path(result["joined_checkpoint"]["archive_path"]).is_file()
            )
            reinforcement_calls = [
                row[1] for row in service.calls if row[0] == "reinforcement"
            ]
            self.assertEqual(
                reinforcement_calls,
                [
                    HARNESS.REQUESTER_CUNIT_ID,
                    HARNESS.HELPER_CUNIT_ID,
                ]
                * 6,
            )
            self.assertTrue(
                all(expected == current for _, expected, current in service.revision_bindings)
            )

    def test_arrived_shortcut_does_not_replace_fresh_route_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _FakeReinforcementService(Path(temporary))
            before = service.snapshot()
            preview = service.execute_step(
                f"preview-move-army-{HARNESS.PLAYER_CUNIT_ID}-to-"
                f"{HARNESS.TARGET_PROVINCE_ID}",
                expected_revision=service.revision,
            )
            move = {
                "accepted": True,
                "war_action": {
                    "status": "arrived",
                    "army_id": HARNESS.PLAYER_CUNIT_ID,
                    "target_province_id": HARNESS.TARGET_PROVINCE_ID,
                },
            }
            service.revision += 1
            stale_after = service.snapshot()

            proof = HARNESS._route_clear_proof(
                before, preview, move, stale_after
            )

            self.assertFalse(proof["ok"])
            self.assertFalse(
                proof["checks"]["fresh_native_target_cleared"]
            )
            self.assertFalse(proof["checks"]["fresh_native_route_cleared"])

    def test_native_parent_order_accepts_two_cunits_in_one_subunit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _FakeReinforcementService(Path(temporary))
            snapshot = service.snapshot()
            requester = service.query_battle_reinforcement_assignment_v1(
                HARNESS.REQUESTER_CUNIT_ID,
                expected_revision=service.revision,
            )
            helper = service.query_battle_reinforcement_assignment_v1(
                HARNESS.HELPER_CUNIT_ID,
                expected_revision=service.revision,
            )
            combined = [
                {
                    "public_cunit_ids_in_stored_order": [
                        HARNESS.REQUESTER_CUNIT_ID,
                        HARNESS.HELPER_CUNIT_ID,
                    ],
                    "asking_for_help": False,
                    "assigned_to_help": False,
                    "assignment_target_province_id": None,
                }
            ]
            for result in (requester, helper):
                frame = result["battle_reinforcement_assignment"]
                frame["subunit_stored_index"] = 0
                frame["native_order"][
                    "parent_subunits_in_stored_order"
                ] = copy.deepcopy(combined)

            proof = HARNESS._native_parent_order_proof(
                snapshot, requester, helper
            )

            self.assertTrue(proof["ok"])
            self.assertEqual(
                proof["observed_parent_flattened_public_cunit_order"],
                [HARNESS.REQUESTER_CUNIT_ID, HARNESS.HELPER_CUNIT_ID],
            )
            self.assertTrue(
                proof["checks"][
                    "selected_subunit_indices_match_native_rows"
                ]
            )

    def test_loop_rejects_more_than_one_day_per_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _FakeReinforcementService(
                Path(temporary), date_delta_raw=48
            )

            with self.assertRaisesRegex(RuntimeError, "exactly one CK3 day"):
                self._run(service)

    def test_assignment_proof_rejects_wrong_provenance_or_eta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _FakeReinforcementService(Path(temporary))
            service.player_route_cleared = True
            service.day = service.assignment_day
            service.date_raw = START_DATE + service.day * 24
            pair = HARNESS._query_native_parent_pair(
                service, service.snapshot()
            )
            valid = HARNESS._assignment_proof(
                pair, service.snapshot(), combat_id=COMBAT_ID
            )
            self.assertTrue(valid["ok"])

            wrong_provenance = copy.deepcopy(pair)
            wrong_provenance["helper_frame"]["assignment"][
                "target_provenance"
            ] = "none"
            self.assertFalse(
                HARNESS._assignment_proof(
                    wrong_provenance,
                    service.snapshot(),
                    combat_id=COMBAT_ID,
                )["ok"]
            )

            wrong_eta = copy.deepcopy(pair)
            wrong_eta["helper_frame"]["route"][
                "assignment_eta_date_raw"
            ] += 24
            self.assertFalse(
                HARNESS._assignment_proof(
                    wrong_eta, service.snapshot(), combat_id=COMBAT_ID
                )["ok"]
            )

    def test_join_proof_rejects_non_tail_or_opposite_side_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _FakeReinforcementService(Path(temporary))
            service.player_route_cleared = True
            service.day = service.contact_day
            service.date_raw = START_DATE + service.day * 24
            baseline = service._battle_frame()
            before = copy.deepcopy(baseline)
            service.day = service.join_day
            service.date_raw = START_DATE + service.day * 24
            joined = service._battle_frame()
            helper = service._reinforcement_frame(HARNESS.HELPER_CUNIT_ID)
            valid = HARNESS._join_proof(
                baseline,
                before,
                joined,
                helper,
                service.snapshot(),
                combat_id=COMBAT_ID,
            )
            self.assertTrue(valid["ok"])

            non_tail = copy.deepcopy(joined)
            non_tail["attacker_public_cunit_ids_in_stored_order"] = [
                HARNESS.HELPER_CUNIT_ID,
                HARNESS.REQUESTER_CUNIT_ID,
            ]
            self.assertFalse(
                HARNESS._join_proof(
                    baseline,
                    before,
                    non_tail,
                    helper,
                    service.snapshot(),
                    combat_id=COMBAT_ID,
                )["ok"]
            )

            opposite_changed = copy.deepcopy(joined)
            opposite_changed["defender_public_cunit_ids_in_stored_order"].append(
                123
            )
            self.assertFalse(
                HARNESS._join_proof(
                    baseline,
                    before,
                    opposite_changed,
                    helper,
                    service.snapshot(),
                    combat_id=COMBAT_ID,
                )["ok"]
            )

    def test_command_boundary_forbids_direct_contact_and_constructor(self) -> None:
        commands = [
            f"preview-move-army-{HARNESS.PLAYER_CUNIT_ID}-to-"
            f"{HARNESS.TARGET_PROVINCE_ID}",
            f"move-army-{HARNESS.PLAYER_CUNIT_ID}-to-"
            f"{HARNESS.TARGET_PROVINCE_ID}",
            "life-advance",
            "save-checkpoint",
            "life-advance",
            "save-checkpoint",
        ]

        proof = HARNESS._mutation_boundary_proof(commands)

        self.assertTrue(proof["ok"])
        self.assertIn("0x2208320", proof["forbidden_native_calls"])
        self.assertIn("0x27FB7C0", proof["forbidden_native_calls"])
        self.assertEqual(proof["forbidden_native_calls_invoked"], [])
        self.assertFalse(
            HARNESS._mutation_boundary_proof(
                [*commands, "restore-checkpoint"]
            )["ok"]
        )

    def test_capability_gate_requires_exact_same_province_actions(self) -> None:
        required_bridge = [
            HARNESS.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
            HARNESS.QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
            HARNESS.QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
            HARNESS.PREVIEW_MOVE_ARMY_CAPABILITY,
            HARNESS.MOVE_ARMY_CAPABILITY,
        ]
        current_preview = (
            f"preview-move-army-{HARNESS.PLAYER_CUNIT_ID}-to-"
            f"{HARNESS.TARGET_PROVINCE_ID}"
        )
        current_move = (
            f"move-army-{HARNESS.PLAYER_CUNIT_ID}-to-"
            f"{HARNESS.TARGET_PROVINCE_ID}"
        )
        capabilities = {
            "bridge_capabilities": required_bridge,
            "action_steps": [
                current_preview,
                current_move,
                "life-advance",
                "save-checkpoint",
            ],
            "battle_reinforcement_assignment_v1_query_supported": True,
            "battle_terminal_transition_v1_query_supported": True,
            "diagnostics": {
                "hello": {"capabilities": required_bridge},
            },
        }

        self.assertTrue(HARNESS._capability_proof(capabilities)["ok"])
        self.assertNotIn(
            "game.command.life-advance", required_bridge
        )
        self.assertNotIn(
            "game.command.save-checkpoint", required_bridge
        )

        missing_current_move = copy.deepcopy(capabilities)
        missing_current_move["action_steps"].remove(current_move)
        proof = HARNESS._capability_proof(missing_current_move)
        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["exact_action_steps"])

    def test_source_hash_and_clone_cleanup_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "source" / "profile"
            save = profile / "save games" / "fixture.ck3"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"frozen-reinforcement-checkpoint")
            expected = hashlib.sha256(save.read_bytes()).hexdigest().upper()
            resolved, identity = HARNESS._resolve_source_save(
                profile, Path("save games/fixture.ck3"), expected
            )
            self.assertEqual(resolved, save.resolve())
            self.assertEqual(identity["sha256"], expected)

            clone = root / "clone"
            clone.mkdir()
            nonce = "fixture-nonce"
            (clone / HARNESS._CLONE_MARKER_NAME).write_text(
                json.dumps(
                    {
                        "kind": "xar_battle_reinforcement_join_clone",
                        "nonce": nonce,
                    }
                ),
                encoding="utf-8",
            )
            (clone / "payload.txt").write_text("fixture", encoding="utf-8")
            cleanup = HARNESS._cleanup_clone(
                clone,
                clone_nonce=nonce,
                retain_state=False,
                session_started=False,
                session_cleanup_proven=False,
            )
            self.assertTrue(cleanup["ok"])
            self.assertFalse(clone.exists())

    def test_clone_is_retained_when_process_cleanup_is_unproven(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "clone"
            clone.mkdir()

            cleanup = HARNESS._cleanup_clone(
                clone,
                clone_nonce="unused",
                retain_state=False,
                session_started=True,
                session_cleanup_proven=False,
            )

            self.assertFalse(cleanup["ok"])
            self.assertFalse(cleanup["attempted"])
            self.assertTrue(clone.exists())


if __name__ == "__main__":
    unittest.main()
