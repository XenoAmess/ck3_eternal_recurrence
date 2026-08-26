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
    / "run_owner_subset_reinforcement_rejoin_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_owner_subset_reinforcement_rejoin_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


START_DATE = 53_178_624
COMBAT_PROVINCE = 2_586


class _FakeService:
    def __init__(self, checkpoint_dir: Path) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.day = 0
        self.extracted = False
        self.revision = 10
        self.date_raw = START_DATE
        self.query_sequence = 0
        self.calls: list[tuple[object, ...]] = []
        self.query_selected: list[int] = []
        self.reinforcement_transient_once = False
        self.transient_crosses_day = False
        self.post_extract_transition_queries = 0
        self.assignment_roster_drift = False
        self.eta_terminal_boundary_drift = False

    def _assert_revision(self, expected: int) -> None:
        if expected != self.revision:
            raise AssertionError((expected, self.revision))

    def _army(
        self,
        army_id: int,
        *,
        in_combat: bool,
        retreating: bool,
        current: int,
        route: list[int],
    ) -> dict[str, object]:
        return {
            "army_id": army_id,
            "owner_character_id": (
                HARNESS.owner_live.OWNER_SUBSET_CHARACTER_ID
                if army_id == HARNESS.REJOIN_CUNIT_ID
                else HARNESS.owner_live.UNCONTROLLED_ALLY_OWNER_ID
            ),
            "current_province_id": current,
            "move_target_province_id": route[-1] if route else None,
            "move_target_observable": bool(route),
            "route_province_ids": list(route),
            "controllable": army_id == HARNESS.REJOIN_CUNIT_ID,
            "in_combat": in_combat,
            "retreating": retreating,
            "army_state_code": 2 if in_combat else 1,
        }

    def _rejoin_army(self) -> dict[str, object]:
        if not self.extracted:
            return self._army(
                HARNESS.REJOIN_CUNIT_ID,
                in_combat=True,
                retreating=False,
                current=COMBAT_PROVINCE,
                route=[],
            )
        if self.day == 0:
            return self._army(
                HARNESS.REJOIN_CUNIT_ID,
                in_combat=False,
                retreating=True,
                current=COMBAT_PROVINCE,
                route=[HARNESS.RETREAT_TARGET_PROVINCE_ID],
            )
        if self.day == 1:
            return self._army(
                HARNESS.REJOIN_CUNIT_ID,
                in_combat=False,
                retreating=False,
                current=HARNESS.RETREAT_TARGET_PROVINCE_ID,
                route=[COMBAT_PROVINCE],
            )
        return self._army(
            HARNESS.REJOIN_CUNIT_ID,
            in_combat=True,
            retreating=False,
            current=COMBAT_PROVINCE,
            route=[],
        )

    def _anchor_army(self) -> dict[str, object]:
        return self._army(
            HARNESS.ANCHOR_CUNIT_ID,
            in_combat=True,
            retreating=False,
            current=COMBAT_PROVINCE,
            route=[],
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": f"native:{self.revision}",
            "revision": self.revision,
            "native_revision": self.revision,
            "date_raw": self.date_raw,
            "paused": True,
            "map_ready": True,
            "episode_character_id": (
                HARNESS.owner_live.OWNER_SUBSET_CHARACTER_ID
            ),
            "episode_run_id": "owner-subset-rejoin-fake",
            "played_character": {
                "character_id": HARNESS.owner_live.OWNER_SUBSET_CHARACTER_ID
            },
            "player_armies": [self._rejoin_army()],
            "active_wars": [
                {
                    "war_id": 16_777_290,
                    "allied_armies": [],
                    "enemy_armies": [self._anchor_army()],
                }
            ],
        }

    def query_battle_control_snapshot_v1(
        self, army_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        if army_id != HARNESS.REJOIN_CUNIT_ID or self.extracted:
            raise AssertionError("unexpected battle-control query")
        return {
            "status": "available",
            "battle_control_ready": True,
            "selected_public_cunit_id": HARNESS.REJOIN_CUNIT_ID,
            "selected_native_carmy_id": (
                HARNESS.owner_live.OWNER_SUBSET_NATIVE_CARMY_ID
            ),
            "selected_owner_character_id": (
                HARNESS.owner_live.OWNER_SUBSET_CHARACTER_ID
            ),
            "side_index": HARNESS.owner_live.EXPECTED_SIDE_INDEX,
            "side_scope": "owner_subset",
            "affected_public_cunit_ids_in_stored_order": [
                HARNESS.REJOIN_CUNIT_ID
            ],
            "unaffected_same_side_public_cunit_ids_in_stored_order": [
                HARNESS.ANCHOR_CUNIT_ID
            ],
            "battle_control_snapshot": {
                "combat_id": HARNESS.COMBAT_ID,
                "attacker": {
                    "ordered_armies": [
                        {"public_cunit_id": HARNESS.OPPOSITE_CUNIT_ID}
                    ]
                },
                "defender": {
                    "ordered_armies": [
                        {"public_cunit_id": HARNESS.REJOIN_CUNIT_ID},
                        {"public_cunit_id": HARNESS.ANCHOR_CUNIT_ID},
                    ]
                },
            },
        }

    def _battle(self) -> dict[str, object]:
        defenders = (
            [HARNESS.REJOIN_CUNIT_ID, HARNESS.ANCHOR_CUNIT_ID]
            if not self.extracted
            else [
                HARNESS.ANCHOR_CUNIT_ID,
                *([HARNESS.REJOIN_CUNIT_ID] if self.day >= 2 else []),
            ]
        )
        return {
            "status": "available",
            "battle_transition_ready": True,
            "snapshot_revision": self.revision,
            "observed_date_raw": self.date_raw,
            "combat_id": HARNESS.COMBAT_ID,
            "province_id": COMBAT_PROVINCE,
            "phase": "main",
            "phase_raw": 1,
            "phase_day": 12 + self.day,
            "winner_side": "none",
            "winner_raw": -1,
            "forced_winner_side": "none",
            "forced_winner_raw": -1,
            "finalized": False,
            "battle_result_id": HARNESS.COMBAT_ID,
            "attacker_public_cunit_ids_in_stored_order": [
                HARNESS.OPPOSITE_CUNIT_ID
            ],
            "defender_public_cunit_ids_in_stored_order": defenders,
        }

    def query_battle_transition_v1(
        self, combat_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        if combat_id != HARNESS.COMBAT_ID:
            raise AssertionError("wrong CombatID")
        frame = self._battle()
        if self.extracted:
            self.post_extract_transition_queries += 1
            if (
                self.assignment_roster_drift
                and self.day == 0
                and self.post_extract_transition_queries >= 2
            ):
                frame["defender_public_cunit_ids_in_stored_order"] = []
        return {"battle_transition_snapshot": frame}

    def preview_active_combat_retreat_v1(
        self,
        army_id: int,
        target: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        return {
            "status": "available",
            "action_ready": True,
            "combat_id": HARNESS.COMBAT_ID,
            "side_index": HARNESS.owner_live.EXPECTED_SIDE_INDEX,
            "side_scope": "owner_subset",
            "source_binding": {"revision": self.revision},
            "target_preview": {"candidate_token": "A" * 32},
        }

    def order_active_combat_retreat_v1(
        self,
        army_id: int,
        *,
        expected_revision: int,
        expected_combat_id: int,
        expected_side_index: int,
        expected_scope: str,
        target_province_id: int,
        candidate_token: str,
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        self.extracted = True
        self.revision += 1
        return {
            "accepted": True,
            "status": "accepted_verification_pending",
        }

    @staticmethod
    def _rows(assigned: bool) -> list[dict[str, object]]:
        return [
            {
                "public_cunit_ids_in_stored_order": [
                    HARNESS.REJOIN_CUNIT_ID,
                    HARNESS.ANCHOR_CUNIT_ID,
                ],
                "asking_for_help": True,
                "assigned_to_help": assigned,
                "assignment_target_province_id": (
                    COMBAT_PROVINCE if assigned else None
                ),
            }
        ]

    def _reinforcement(self, selected: int) -> dict[str, object]:
        assigned = self.extracted and self.day == 1
        joined = self.extracted and self.day >= 2
        is_rejoin = selected == HARNESS.REJOIN_CUNIT_ID
        semantic = self._rejoin_army() if is_rejoin else self._anchor_army()
        selected_assigned = assigned and is_rejoin
        route_ids = list(semantic["route_province_ids"])
        return {
            "status": "available",
            "battle_reinforcement_assignment_ready": True,
            "snapshot_revision": self.revision,
            "observed_date_raw": self.date_raw,
            "selected_public_cunit_id": selected,
            "selected_native_carmy_id": 344 if is_rejoin else 50_331_769,
            "coordinator_id": 33_554_513,
            "unit_stack_stored_index": 0,
            "subunit_stored_index": 0,
            "signal": {
                "asking_for_help": True,
                "assigned_to_help": selected_assigned,
            },
            "assignment": {
                "assignment_target_province_id": (
                    COMBAT_PROVINCE if selected_assigned else None
                ),
                "target_provenance": (
                    "native_help_override" if selected_assigned else "none"
                ),
                "combat_binding_status": (
                    "already_in_active_combat"
                    if (not is_rejoin or joined)
                    else "unbound_until_contact"
                ),
                "active_combat_id": (
                    HARNESS.COMBAT_ID if (not is_rejoin or joined) else None
                ),
            },
            "route": {
                "current_province_id": semantic["current_province_id"],
                "move_target_province_id": (
                    COMBAT_PROVINCE if selected_assigned else None
                ),
                "route_province_ids": route_ids,
                "route_alignment": (
                    "aligned_to_assignment" if selected_assigned else "no_assignment"
                ),
                "arrival_date_raws": (
                    [START_DATE + 2 * HARNESS.ONE_GAME_DAY_RAW]
                    if selected_assigned
                    else []
                ),
                "assignment_eta_date_raw": (
                    START_DATE + 2 * HARNESS.ONE_GAME_DAY_RAW
                    if selected_assigned
                    else None
                ),
            },
            "native_order": {
                "support_search_province_ids_in_stored_order": [],
                "parent_subunits_in_stored_order": self._rows(assigned),
            },
        }

    def query_battle_reinforcement_assignment_v1(
        self, selected: int, *, expected_revision: int
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        self.query_selected.append(selected)
        if (
            self.reinforcement_transient_once
            and selected == HARNESS.REJOIN_CUNIT_ID
        ):
            self.reinforcement_transient_once = False
            self.revision += 1
            if self.transient_crosses_day:
                self.date_raw += HARNESS.ONE_GAME_DAY_RAW
            raise RuntimeError(
                "native gameplay step failed: battle-reinforcement "
                "snapshot changed; retry after heartbeat"
            )
        self.query_sequence += 1
        return {
            "query_sequence": self.query_sequence,
            "battle_reinforcement_assignment": self._reinforcement(selected),
        }

    def query_battle_terminal_transition_v1(
        self,
        combat_id: int,
        subject: int,
        *,
        expected_revision: int,
        after_terminal_sequence: int | None = None,
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        battle = self._battle()
        prior_attackers = battle[
            "attacker_public_cunit_ids_in_stored_order"
        ]
        if self.eta_terminal_boundary_drift and self.day >= 2:
            prior_attackers = []
        return {
            "battle_terminal_transition": {
                "status": "available",
                "battle_terminal_transition_ready": True,
                "prior_combat_id": HARNESS.COMBAT_ID,
                "terminal_journal": {
                    "requested_after_sequence": after_terminal_sequence,
                    "oldest_available_sequence": 1,
                    "latest_sequence": 4,
                    "event_sequence": None,
                    "event_status": "not_observed",
                },
                "prior": {
                    "combat_id": HARNESS.COMBAT_ID,
                    "terminal_kind": "active_not_terminal",
                    "attacker_public_cunit_ids_in_stored_order": prior_attackers,
                    "defender_public_cunit_ids_in_stored_order": battle[
                        "defender_public_cunit_ids_in_stored_order"
                    ],
                },
                "removal": {"prior_combat_strictly_resolves": True},
            }
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        self._assert_revision(expected_revision)
        if step != "life-advance":
            raise AssertionError(step)
        before = self.date_raw
        self.day += 1
        self.revision += 1
        self.date_raw += HARNESS.ONE_GAME_DAY_RAW
        return {
            "step": step,
            "starting_date_raw": before,
            "ending_date_raw": self.date_raw,
            "elapsed_days": 1,
        }

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self._assert_revision(expected_revision)
        path = self.checkpoint_dir / "xar_checkpoint.ck3"
        path.write_bytes(f"fake-{self.day}".encode("ascii"))
        raw = path.read_bytes()
        return {
            "checkpoint": {
                "status": "saved",
                "path": str(path.resolve()),
                "date_raw": self.date_raw,
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest().upper(),
            }
        }


class OwnerSubsetReinforcementRejoinTests(unittest.TestCase):
    def test_complete_fake_sequence_proves_assignment_and_same_combat_join(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-fake-") as temporary:
            service = _FakeService(Path(temporary))
            result = HARNESS._run_rejoin_sequence(
                service,
                wait_after_advance=service.snapshot,
                max_assignment_days=4,
                max_eta_days=4,
                postcondition_timeout=1.0,
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["outcome"], "same_combat_rejoin")
        self.assertFalse(
            result["assignment_proof"]["requester_identity_claimed"]
        )
        self.assertEqual(
            result["rejoin_proof"]["joined_same_side"],
            [HARNESS.ANCHOR_CUNIT_ID, HARNESS.REJOIN_CUNIT_ID],
        )
        self.assertEqual(
            result["rejoin_proof"]["joined_opposite_side"],
            [HARNESS.OPPOSITE_CUNIT_ID],
        )
        self.assertEqual(
            result["assigned_checkpoint"]["archive_sha256"],
            hashlib.sha256(b"fake-1").hexdigest().upper(),
        )
        self.assertEqual(
            result["joined_checkpoint"]["archive_sha256"],
            hashlib.sha256(b"fake-2").hexdigest().upper(),
        )

    def test_assignment_roster_drift_returns_full_typed_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-drift-") as temporary:
            service = _FakeService(Path(temporary))
            service.assignment_roster_drift = True
            result = HARNESS._run_rejoin_sequence(
                service,
                wait_after_advance=service.snapshot,
                max_assignment_days=4,
                max_eta_days=4,
                postcondition_timeout=1.0,
            )
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["outcome"], "assignment_old_combat_lifecycle_drift"
        )
        diagnostic = result["diagnostic_frame"]
        for key in (
            "snapshot",
            "pair",
            "battle",
            "terminal",
            "boundary",
            "active_roster",
            "observation_retries",
        ):
            self.assertIn(key, diagnostic)
        self.assertFalse(diagnostic["active_roster"]["ok"])
        self.assertTrue(result["daily_pairs"])
        self.assertIn("order-active-combat-retreat-v1", result["commands"])
        self.assertFalse(
            result["readiness_gates"][
                "assignment_reopened_aligned_eta_live_ready"
            ]
        )

    def test_eta_terminal_drift_preserves_assignment_checkpoint_and_frame(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-eta-drift-") as temporary:
            service = _FakeService(Path(temporary))
            service.eta_terminal_boundary_drift = True
            result = HARNESS._run_rejoin_sequence(
                service,
                wait_after_advance=service.snapshot,
                max_assignment_days=4,
                max_eta_days=4,
                postcondition_timeout=1.0,
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["outcome"], "eta_terminal_boundary_drift")
        self.assertTrue(result["assignment_proof"]["ok"])
        self.assertTrue(result["assigned_checkpoint"]["ok"])
        diagnostic = result["diagnostic_frame"]
        self.assertEqual(diagnostic["stage"], "eta")
        self.assertFalse(diagnostic["boundary"]["active"])
        self.assertEqual(
            diagnostic["battle"]["combat_id"], HARNESS.COMBAT_ID
        )
        self.assertIn("save-checkpoint", result["commands"])
        self.assertFalse(
            result["readiness_gates"]["same_combat_rejoin_live_ready"]
        )

    def test_shared_native_subunit_can_ask_and_assign_without_requester_claim(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-pair-") as temporary:
            service = _FakeService(Path(temporary))
            service.extracted = True
            service.day = 1
            service.date_raw += HARNESS.ONE_GAME_DAY_RAW
            snapshot = service.snapshot()
            pair = HARNESS._query_native_pair(service, snapshot)
            proof = HARNESS._assignment_reopened_proof(
                pair,
                snapshot,
                service._battle(),
                combat_id=HARNESS.COMBAT_ID,
                combat_province_id=COMBAT_PROVINCE,
            )
        self.assertTrue(pair["available_order_ready"])
        self.assertTrue(proof["ok"])
        self.assertFalse(proof["requester_identity_claimed"])

    def test_exact_heartbeat_transient_restarts_the_entire_read_only_bundle(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-retry-") as temporary:
            service = _FakeService(Path(temporary))
            service.extracted = True
            service.day = 1
            service.date_raw += HARNESS.ONE_GAME_DAY_RAW
            stale = service.snapshot()
            service.reinforcement_transient_once = True
            fresh, pair, battle, terminal, retries = (
                HARNESS._query_paused_observation_bundle(
                    service,
                    stale,
                    combat_id=HARNESS.COMBAT_ID,
                    terminal_cursor=None,
                    retry_attempts=3,
                    retry_timeout_seconds=1.0,
                )
            )
        self.assertEqual(fresh["revision"], stale["revision"] + 1)
        self.assertTrue(pair["binding_ok"])
        self.assertEqual(battle["combat_id"], HARNESS.COMBAT_ID)
        self.assertEqual(terminal["prior_combat_id"], HARNESS.COMBAT_ID)
        self.assertEqual(
            service.query_selected,
            [
                HARNESS.REJOIN_CUNIT_ID,
                HARNESS.REJOIN_CUNIT_ID,
                HARNESS.ANCHOR_CUNIT_ID,
            ],
        )
        self.assertEqual(len(retries), 1)
        self.assertEqual(
            retries[0]["restart_scope"],
            "reinforcement_pair_then_battle_then_terminal",
        )

    def test_heartbeat_retry_refuses_to_cross_a_game_day(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-retry-day-") as temporary:
            service = _FakeService(Path(temporary))
            stale = service.snapshot()
            service.reinforcement_transient_once = True
            service.transient_crosses_day = True
            with self.assertRaisesRegex(RuntimeError, "crossed a game day"):
                HARNESS._query_paused_observation_bundle(
                    service,
                    stale,
                    combat_id=HARNESS.COMBAT_ID,
                    terminal_cursor=None,
                    retry_attempts=3,
                    retry_timeout_seconds=1.0,
                )

    def test_rejoin_rejects_non_tail_insert_and_opposite_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-tail-") as temporary:
            service = _FakeService(Path(temporary))
            service.extracted = True
            service.day = 2
            service.date_raw += 2 * HARNESS.ONE_GAME_DAY_RAW
            snapshot = service.snapshot()
            pair = HARNESS._query_native_pair(service, snapshot)
            baseline = service._battle()
            baseline["defender_public_cunit_ids_in_stored_order"] = [
                HARNESS.ANCHOR_CUNIT_ID
            ]
            joined = service._battle()
            wrong_tail = copy.deepcopy(joined)
            wrong_tail["defender_public_cunit_ids_in_stored_order"] = [
                HARNESS.REJOIN_CUNIT_ID,
                HARNESS.ANCHOR_CUNIT_ID,
            ]
            proof = HARNESS._same_combat_rejoin_proof(
                baseline,
                baseline,
                wrong_tail,
                pair,
                snapshot,
                combat_id=HARNESS.COMBAT_ID,
                combat_province_id=COMBAT_PROVINCE,
                side_index=1,
            )
            self.assertFalse(proof["ok"])
            drift = copy.deepcopy(joined)
            drift["attacker_public_cunit_ids_in_stored_order"].append(7)
            proof = HARNESS._same_combat_rejoin_proof(
                baseline,
                baseline,
                drift,
                pair,
                snapshot,
                combat_id=HARNESS.COMBAT_ID,
                combat_province_id=COMBAT_PROVINCE,
                side_index=1,
            )
            self.assertFalse(proof["ok"])

    def test_terminal_event_is_a_typed_boundary_not_active_rejoin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-terminal-") as temporary:
            service = _FakeService(Path(temporary))
            service.extracted = True
            battle = service._battle()
            terminal = service.query_battle_terminal_transition_v1(
                HARNESS.COMBAT_ID,
                HARNESS.REJOIN_CUNIT_ID,
                expected_revision=service.revision,
            )["battle_terminal_transition"]
            terminal["terminal_journal"]["event_status"] = "observed"
            terminal["terminal_journal"]["event_sequence"] = 4
            terminal["prior"]["terminal_kind"] = "normal_result"
            terminal["removal"]["prior_combat_strictly_resolves"] = False
            proof = HARNESS._terminal_boundary_proof(
                terminal,
                battle,
                combat_id=HARNESS.COMBAT_ID,
                requested_cursor=None,
            )
        self.assertTrue(proof["boundary_valid"])
        self.assertTrue(proof["terminal_event"])
        self.assertFalse(proof["active"])

    def test_mutation_boundary_never_invokes_native_join_or_constructor(self) -> None:
        proof = HARNESS._mutation_boundary_proof(
            [
                "preview-active-combat-retreat-v1",
                "order-active-combat-retreat-v1",
                "life-advance",
                "save-checkpoint",
                "life-advance",
                "save-checkpoint",
            ]
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["forbidden_native_calls_invoked"], [])
        self.assertIn("0x27FB7C0", proof["forbidden_native_calls"])

    def test_direct_canonical_clones_then_removes_only_disposable_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-direct-") as temporary:
            base = Path(temporary)
            source_state = base / "immutable-source"
            source_profile = source_state / "profile"
            source_profile.mkdir(parents=True)
            source_save = source_profile / "last_save.ck3"
            source_save.write_bytes(b"immutable-canonical")
            source_sha = hashlib.sha256(source_save.read_bytes()).hexdigest().upper()
            target = base / "disposable-target"
            output = base / "artifact.json"

            def prepare_stage(
                *,
                source_profile: Path,
                target_state: Path,
                game_dir: Path,
                save_source: Path,
                save_name: str,
            ) -> tuple[object, dict[str, object]]:
                target_state.mkdir(parents=True)
                profile = target_state / "profile"
                save_dir = profile / "save games"
                save_dir.mkdir(parents=True)
                copy = save_dir / save_name
                copy.write_bytes(save_source.read_bytes())
                return (
                    SimpleNamespace(
                        state_dir=target_state,
                        profile_dir=profile,
                        game_exe=game_dir / "binaries" / "ck3.exe",
                    ),
                    {"copied_sha256": hashlib.sha256(copy.read_bytes()).hexdigest().upper()},
                )

            action = {
                "ok": True,
                "cleanup": {"ok": True},
                "readiness_gates": {
                    "owner_subset_postcondition_live_ready": True,
                    "assignment_reopened_aligned_eta_live_ready": True,
                    "same_combat_rejoin_live_ready": True,
                },
                "sequence": {
                    "assigned_checkpoint": {"ok": True},
                    "joined_checkpoint": {"ok": True},
                },
                "error": None,
            }
            args = SimpleNamespace(
                source_state_dir=source_state,
                state_dir=target,
                game_dir=base / "game",
                battle_save=Path("last_save.ck3"),
                expected_battle_save_sha256=source_sha,
                bridge_pipe="owner-rejoin-direct-fake",
                bridge_dll=base / "bridge.dll",
                bridge_injector=base / "injector.exe",
                output=output,
                timeout=10.0,
                readiness_timeout=2.0,
                postcondition_timeout=1.0,
                max_assignment_days=2,
                max_eta_days=2,
                retain_state=False,
            )
            with (
                mock.patch.object(
                    HARNESS.owner_live, "_prepare_stage", side_effect=prepare_stage
                ),
                mock.patch.object(
                    HARNESS,
                    "_run_action_production_session",
                    return_value=action,
                ),
                mock.patch.object(
                    HARNESS.owner_live, "ck3_processes", return_value=[]
                ),
            ):
                payload, exit_code = HARNESS._run_direct_canonical(args)

            self.assertEqual(exit_code, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(source_save.read_bytes(), b"immutable-canonical")
            self.assertEqual(
                payload["source_save"]["before_sha256"], source_sha
            )
            self.assertEqual(
                payload["source_save"]["after_sha256"], source_sha
            )
            self.assertFalse(target.exists())
            self.assertTrue(payload["state_cleanup"]["ok"])

    def test_direct_canonical_rejects_artifact_under_immutable_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-rejoin-output-") as temporary:
            base = Path(temporary)
            source_state = base / "source"
            profile = source_state / "profile"
            profile.mkdir(parents=True)
            save = profile / "last_save.ck3"
            save.write_bytes(b"canonical")
            sha = hashlib.sha256(save.read_bytes()).hexdigest().upper()
            args = SimpleNamespace(
                source_state_dir=source_state,
                state_dir=base / "target",
                game_dir=base / "game",
                battle_save=Path("last_save.ck3"),
                expected_battle_save_sha256=sha,
                bridge_pipe="never-used",
                bridge_dll=base / "bridge.dll",
                bridge_injector=base / "injector.exe",
                output=source_state / "artifact.json",
                timeout=10.0,
                readiness_timeout=2.0,
                postcondition_timeout=1.0,
                max_assignment_days=2,
                max_eta_days=2,
                retain_state=False,
            )
            with self.assertRaisesRegex(
                HARNESS.owner_live.AgentError, "immutable canonical source"
            ):
                HARNESS._run_direct_canonical(args)


if __name__ == "__main__":
    unittest.main()
