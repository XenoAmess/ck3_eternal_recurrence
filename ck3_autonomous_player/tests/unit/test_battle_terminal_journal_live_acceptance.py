from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_battle_terminal_journal_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_battle_terminal_journal_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

from xar_autoplayer.bridge.battle_terminal_transition_contract import (  # noqa: E402
    normalize_battle_terminal_transition_v1,
)


COMBAT = 335_544_325
SUBJECT = 83_886_341
ALLY = 33_554_657
ENEMY = 357
PROVINCE = 2586


class _FakeTerminalService:
    def __init__(
        self,
        *,
        terminal_day: int = 3,
        date_delta_raw: int = 24,
        terminal_kind: str = "normal_result",
    ) -> None:
        self.day = 0
        self.terminal_day = terminal_day
        self.date_delta_raw = date_delta_raw
        self.terminal_kind = terminal_kind
        self.revision = 7
        self.date_raw = 53_178_240
        self.terminal_query_sequence = 0
        self.calls: list[tuple[object, ...]] = []

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
            "episode_run_id": "terminal-fixture",
            "active_event": None,
        }

    def query_battle_transition_v1(
        self, combat_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("old", combat_id, expected_revision))
        if expected_revision != self.revision:
            raise AssertionError("old query revision differs")
        available = self.day < self.terminal_day
        frame = {
            "status": "available" if available else "combat_not_found",
            "combat_id": combat_id,
            "finalized": False if available else None,
            "attacker_public_cunit_ids_in_stored_order": (
                [SUBJECT, ALLY] if available else []
            ),
            "defender_public_cunit_ids_in_stored_order": (
                [ENEMY] if available else []
            ),
        }
        return {
            "status": frame["status"],
            "query_sequence": len(self.calls),
            "battle_transition_snapshot": frame,
        }

    def _terminal_frame(
        self, after_terminal_sequence: int | None
    ) -> dict[str, object]:
        active = self.day < self.terminal_day
        journal = {
            "requested_after_sequence": after_terminal_sequence,
            "oldest_available_sequence": 1,
            "latest_sequence": 4 if active else 5,
            "event_sequence": None if active else 5,
            "event_status": "not_observed" if active else "observed",
        }
        if active:
            return {
                "schema_version": 1,
                "contract_stage": (
                    "production_exact_battle_terminal_transition"
                ),
                "status": "available",
                "unavailable_reason": None,
                "battle_terminal_transition_ready": True,
                "snapshot_revision": self.revision,
                "observed_date_raw": self.date_raw,
                "prior_combat_id": COMBAT,
                "subject_public_cunit_id": SUBJECT,
                "terminal_journal": journal,
                "prior": {
                    "combat_id": COMBAT,
                    "terminal_kind": "active_not_terminal",
                    "terminal_date_raw": None,
                    "suppress_normal_result_envelopes": None,
                    "phase_raw": 1,
                    "phase_day": self.day,
                    "winner_raw": -1,
                    "finalized_before": False,
                    "daily_guard_raw": 0,
                    "province_id": PROVINCE,
                    "battle_result_id": None,
                    "wipe_raw": None,
                    "attacker_primary_participant_character_id": 29_829,
                    "defender_primary_participant_character_id": 36_108,
                    "attacker_public_cunit_ids_in_stored_order": [
                        SUBJECT,
                        ALLY,
                    ],
                    "defender_public_cunit_ids_in_stored_order": [ENEMY],
                    "battle_warscore": {
                        "status": "unavailable",
                        "war_id": None,
                        "war_battle_row_index": None,
                        "value_raw_q100000": None,
                        "winner_is_war_attacker": None,
                        "combat_side0_is_war_attacker": None,
                        "attacker_relative_delta_raw_q100000": None,
                    },
                },
                "removal": {
                    "prior_combat_strictly_resolves": True,
                    "prior_province_strictly_resolves": True,
                    "prior_province_contains_prior_combat_id": True,
                    "result_strictly_resolves": None,
                    "result_relevant_player_count": None,
                },
                "subject": {
                    "exists": True,
                    "current_province_id": PROVINCE,
                    "native_carmy_id": 91,
                    "combat_backlink_id": COMBAT,
                    "active_combat_id": COMBAT,
                    "movement_or_retreat_state_raw": 1,
                    "move_target_province_id": None,
                    "route_province_ids_in_stored_order": [],
                    "ai_membership_status": "unavailable",
                    "coordinator_id": None,
                    "unit_stack_stored_index": None,
                    "subunit_stored_index": None,
                    "blocked_by_active_combat": True,
                },
                "successor": {
                    "state": "unavailable",
                    "matching_combat_ids_in_native_order": [],
                    "selected_successor_combat_id": None,
                    "participant_overlap_public_cunit_ids_in_prior_order": [],
                },
            }
        suppress = self.terminal_kind != "normal_result"
        return {
            "schema_version": 1,
            "contract_stage": "production_exact_battle_terminal_transition",
            "status": "available",
            "unavailable_reason": None,
            "battle_terminal_transition_ready": True,
            "snapshot_revision": self.revision,
            "observed_date_raw": self.date_raw,
            "prior_combat_id": COMBAT,
            "subject_public_cunit_id": SUBJECT,
            "terminal_journal": journal,
            "prior": {
                "combat_id": COMBAT,
                "terminal_kind": self.terminal_kind,
                "terminal_date_raw": self.date_raw,
                "suppress_normal_result_envelopes": suppress,
                "phase_raw": 3,
                "phase_day": self.terminal_day,
                "winner_raw": 0,
                "finalized_before": False,
                "daily_guard_raw": 1,
                "province_id": PROVINCE,
                "battle_result_id": 553_648_135,
                "wipe_raw": False,
                "attacker_primary_participant_character_id": 29_829,
                "defender_primary_participant_character_id": 36_108,
                "attacker_public_cunit_ids_in_stored_order": [
                    SUBJECT,
                    ALLY,
                ],
                "defender_public_cunit_ids_in_stored_order": [ENEMY],
                "battle_warscore": {
                    "status": "recorded",
                    "war_id": 16_777_290,
                    "war_battle_row_index": 4,
                    "value_raw_q100000": 800_000,
                    "winner_is_war_attacker": True,
                    "combat_side0_is_war_attacker": True,
                    "attacker_relative_delta_raw_q100000": 800_000,
                },
            },
            "removal": {
                "prior_combat_strictly_resolves": False,
                "prior_province_strictly_resolves": True,
                "prior_province_contains_prior_combat_id": False,
                "result_strictly_resolves": True,
                "result_relevant_player_count": 1,
            },
            "subject": {
                "exists": True,
                "current_province_id": PROVINCE,
                "native_carmy_id": 91,
                "combat_backlink_id": None,
                "active_combat_id": None,
                "movement_or_retreat_state_raw": 3,
                "move_target_province_id": 2581,
                "route_province_ids_in_stored_order": [2581],
                "ai_membership_status": "unavailable",
                "coordinator_id": None,
                "unit_stack_stored_index": None,
                "subunit_stored_index": None,
                "blocked_by_active_combat": False,
            },
            "successor": {
                "state": "subject_retreating",
                "matching_combat_ids_in_native_order": [],
                "selected_successor_combat_id": None,
                "participant_overlap_public_cunit_ids_in_prior_order": [],
            },
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
        if expected_revision != self.revision:
            raise AssertionError("terminal query revision differs")
        self.terminal_query_sequence += 1
        return {
            "status": "available",
            "query_sequence": self.terminal_query_sequence,
            "battle_terminal_transition": self._terminal_frame(
                after_terminal_sequence
            ),
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("execute", step, expected_revision))
        if step != "life-advance":
            raise AssertionError(f"unexpected mutation step {step}")
        if expected_revision != self.revision:
            raise AssertionError("advance revision differs")
        before = self.date_raw
        self.day += 1
        self.revision += 1
        self.date_raw += self.date_delta_raw
        return {
            "step": step,
            "starting_date_raw": before,
            "ending_date_raw": self.date_raw,
            "elapsed_days": 1,
            "paused": True,
        }


class _FallbackTerminalService(_FakeTerminalService):
    def __init__(
        self,
        *,
        candidate_modes: dict[int, str],
        mismatch_kind: str | None = None,
        mismatch_subject_id: int = ALLY,
    ) -> None:
        super().__init__(terminal_day=1)
        self.candidate_modes = candidate_modes
        self.mismatch_kind = mismatch_kind
        self.mismatch_subject_id = mismatch_subject_id

    def _subject_terminal_frame(
        self,
        after_terminal_sequence: int | None,
        subject_public_cunit_id: int,
    ) -> dict[str, object]:
        frame = deepcopy(self._terminal_frame(after_terminal_sequence))
        frame["subject_public_cunit_id"] = subject_public_cunit_id
        subject = frame["subject"]
        successor = frame["successor"]
        subject["native_carmy_id"] = 91 + subject_public_cunit_id % 10
        subject["combat_backlink_id"] = None
        subject["active_combat_id"] = None
        subject["movement_or_retreat_state_raw"] = 0
        subject["move_target_province_id"] = None
        subject["route_province_ids_in_stored_order"] = []
        subject["blocked_by_active_combat"] = False
        mode = (
            "unavailable"
            if subject_public_cunit_id == SUBJECT
            else self.candidate_modes[subject_public_cunit_id]
        )
        if mode == "strong":
            subject["ai_membership_status"] = "observed"
            subject["coordinator_id"] = 1000 + subject_public_cunit_id
            subject["unit_stack_stored_index"] = 0
            subject["subunit_stored_index"] = 0
            successor["state"] = "subject_assignment_reopened"
        elif mode == "unavailable":
            subject["ai_membership_status"] = "unavailable"
            subject["coordinator_id"] = None
            subject["unit_stack_stored_index"] = None
            subject["subunit_stored_index"] = None
            successor["state"] = "unavailable"
        else:
            raise AssertionError(f"unexpected candidate mode {mode!r}")
        successor["matching_combat_ids_in_native_order"] = []
        successor["selected_successor_combat_id"] = None
        successor[
            "participant_overlap_public_cunit_ids_in_prior_order"
        ] = []

        if subject_public_cunit_id == self.mismatch_subject_id:
            if self.mismatch_kind == "revision":
                frame["snapshot_revision"] += 1
            elif self.mismatch_kind == "event":
                frame["terminal_journal"]["event_sequence"] += 1
                frame["terminal_journal"]["latest_sequence"] += 1
        return frame

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
        if expected_revision != self.revision:
            raise AssertionError("terminal query revision differs")
        self.terminal_query_sequence += 1
        frame = (
            self._terminal_frame(after_terminal_sequence)
            if self.day < self.terminal_day
            else self._subject_terminal_frame(
                after_terminal_sequence, subject_public_cunit_id
            )
        )
        return {
            "status": "available",
            "query_sequence": self.terminal_query_sequence,
            "battle_terminal_transition": frame,
        }


class BattleTerminalJournalLiveAcceptanceTests(unittest.TestCase):
    def test_mock_frames_obey_canonical_python_contract(self) -> None:
        active = _FakeTerminalService(terminal_day=2)
        active_frame = active._terminal_frame(None)
        normalized_active = normalize_battle_terminal_transition_v1(
            active_frame,
            expected_prior_combat_id=COMBAT,
            expected_subject_public_cunit_id=SUBJECT,
            expected_after_terminal_sequence=None,
            expected_observed_date_raw=active.date_raw,
            expected_snapshot_revision=active.revision,
        )
        terminal = _FakeTerminalService(terminal_day=0)
        terminal_frame = terminal._terminal_frame(4)
        normalized_terminal = normalize_battle_terminal_transition_v1(
            terminal_frame,
            expected_prior_combat_id=COMBAT,
            expected_subject_public_cunit_id=SUBJECT,
            expected_after_terminal_sequence=4,
            expected_observed_date_raw=terminal.date_raw,
            expected_snapshot_revision=terminal.revision,
        )

        self.assertEqual(
            normalized_active["prior"]["terminal_kind"],
            "active_not_terminal",
        )
        self.assertEqual(
            normalized_terminal["prior"]["terminal_kind"],
            "normal_result",
        )
        self.assertEqual(
            normalized_terminal["subject"]["ai_membership_status"],
            "unavailable",
        )

    def test_loop_cross_checks_active_then_observes_normal_terminal(self) -> None:
        service = _FakeTerminalService(terminal_day=3)

        result = HARNESS._run_terminal_loop(
            service,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            max_days=5,
            wait_after_advance=lambda: service.snapshot(),
        )

        self.assertEqual(result["days_advanced"], 3)
        self.assertEqual(result["after_terminal_sequence"], 4)
        self.assertEqual(
            [row["terminal_kind"] for row in result["days"]],
            ["active_not_terminal", "active_not_terminal", "normal_result"],
        )
        self.assertTrue(result["terminal_proof"]["ok"])
        self.assertEqual(
            result["terminal_proof"]["journal_event_sequence"], 5
        )
        self.assertTrue(
            result["assertions"]["every_advance_exactly_one_day"]
        )
        self.assertTrue(
            result["assertions"]["only_life_advance_mutated_gameplay"]
        )
        self.assertEqual(
            [call[1] for call in service.calls if call[0] == "execute"],
            ["life-advance", "life-advance", "life-advance"],
        )

    def test_loop_queries_terminal_surface_after_every_day(self) -> None:
        service = _FakeTerminalService(terminal_day=2)

        HARNESS._run_terminal_loop(
            service,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            max_days=3,
            wait_after_advance=lambda: service.snapshot(),
        )

        terminal_calls = [row for row in service.calls if row[0] == "terminal"]
        self.assertEqual(len(terminal_calls), 4)
        self.assertIsNone(terminal_calls[0][4])
        self.assertEqual([row[4] for row in terminal_calls[1:]], [4, 4, 4])

    def test_player_strong_reentry_skips_corroborating_queries(self) -> None:
        service = _FakeTerminalService(terminal_day=1)

        result = HARNESS._run_terminal_loop(
            service,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            max_days=2,
            wait_after_advance=lambda: service.snapshot(),
        )

        proof = result["terminal_proof"]
        terminal_subjects = [
            call[2] for call in service.calls if call[0] == "terminal"
        ]
        self.assertTrue(proof["ok"])
        self.assertTrue(proof["player_reentry_ready"])
        self.assertFalse(proof["corroboration_attempted"])
        self.assertFalse(proof["corroborating_subject_reentry_ready"])
        self.assertEqual(proof["corroborating_subjects"], [])
        self.assertEqual(terminal_subjects, [SUBJECT, SUBJECT, SUBJECT])

    def test_membership_fallback_accepts_one_strong_ai_subject(self) -> None:
        service = _FallbackTerminalService(
            candidate_modes={ALLY: "strong", ENEMY: "unavailable"}
        )

        result = HARNESS._run_terminal_loop(
            service,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            max_days=2,
            wait_after_advance=lambda: service.snapshot(),
        )

        proof = result["terminal_proof"]
        fallback_subjects = [
            call[2]
            for call in service.calls
            if call[0] == "terminal" and call[2] != SUBJECT
        ]
        self.assertTrue(proof["ok"])
        self.assertTrue(proof["player_terminal_core_ok"])
        self.assertFalse(proof["player_reentry_ready"])
        self.assertTrue(proof["corroboration_attempted"])
        self.assertTrue(proof["corroborating_subject_reentry_ready"])
        self.assertEqual(proof["corroborating_subject_ids"], [ALLY])
        self.assertEqual(fallback_subjects, [ALLY, ENEMY])
        self.assertTrue(
            result["terminal_query_pair"]["immediate_frame_equal"]
        )
        self.assertEqual(
            result["terminal_query_pair"]["first"][
                "battle_terminal_transition"
            ],
            result["terminal_query_pair"]["second"][
                "battle_terminal_transition"
            ],
        )

    def test_membership_fallback_rejects_all_unavailable_subjects(
        self,
    ) -> None:
        service = _FallbackTerminalService(
            candidate_modes={ALLY: "unavailable", ENEMY: "unavailable"}
        )

        with self.assertRaisesRegex(
            RuntimeError, "no corroborating prior participant"
        ):
            HARNESS._run_terminal_loop(
                service,
                prior_combat_id=COMBAT,
                subject_public_cunit_id=SUBJECT,
                max_days=2,
                wait_after_advance=lambda: service.snapshot(),
            )

        fallback_subjects = [
            call[2]
            for call in service.calls
            if call[0] == "terminal" and call[2] != SUBJECT
        ]
        self.assertEqual(fallback_subjects, [ALLY, ENEMY])

    def test_membership_fallback_rejects_cross_revision_or_event(
        self,
    ) -> None:
        for mismatch_kind in ("revision", "event"):
            with self.subTest(mismatch_kind=mismatch_kind):
                service = _FallbackTerminalService(
                    candidate_modes={
                        ALLY: "strong",
                        ENEMY: "unavailable",
                    },
                    mismatch_kind=mismatch_kind,
                )

                with self.assertRaisesRegex(
                    RuntimeError,
                    "crossed revision or terminal event facts",
                ):
                    HARNESS._run_terminal_loop(
                        service,
                        prior_combat_id=COMBAT,
                        subject_public_cunit_id=SUBJECT,
                        max_days=2,
                        wait_after_advance=lambda: service.snapshot(),
                    )

                fallback_subjects = [
                    call[2]
                    for call in service.calls
                    if call[0] == "terminal" and call[2] != SUBJECT
                ]
                self.assertEqual(fallback_subjects, [ALLY, ENEMY])

    def test_loop_rejects_more_than_one_day_from_one_advance(self) -> None:
        service = _FakeTerminalService(
            terminal_day=1, date_delta_raw=48
        )

        with self.assertRaisesRegex(RuntimeError, "exactly one CK3 day"):
            HARNESS._run_terminal_loop(
                service,
                prior_combat_id=COMBAT,
                subject_public_cunit_id=SUBJECT,
                max_days=2,
                wait_after_advance=lambda: service.snapshot(),
            )

    def test_loop_rejects_no_normal_terminal_within_bound(self) -> None:
        service = _FakeTerminalService(terminal_day=99)

        with self.assertRaisesRegex(RuntimeError, "not observed within 2"):
            HARNESS._run_terminal_loop(
                service,
                prior_combat_id=COMBAT,
                subject_public_cunit_id=SUBJECT,
                max_days=2,
                wait_after_advance=lambda: service.snapshot(),
            )

    def test_loop_rejects_no_normal_result_event(self) -> None:
        service = _FakeTerminalService(
            terminal_day=1, terminal_kind="no_normal_result"
        )

        with self.assertRaisesRegex(RuntimeError, "postconditions failed"):
            HARNESS._run_terminal_loop(
                service,
                prior_combat_id=COMBAT,
                subject_public_cunit_id=SUBJECT,
                max_days=2,
                wait_after_advance=lambda: service.snapshot(),
            )

    def test_normal_terminal_proof_rejects_unordered_overlap(self) -> None:
        service = _FakeTerminalService(terminal_day=0)
        frame = service._terminal_frame(4)
        frame["successor"] = {
            "state": "residual_new_combat",
            "matching_combat_ids_in_native_order": [COMBAT + 1],
            "selected_successor_combat_id": COMBAT + 1,
            "participant_overlap_public_cunit_ids_in_prior_order": [
                ENEMY,
                SUBJECT,
            ],
        }
        frame["subject"]["active_combat_id"] = COMBAT + 1
        frame["subject"]["blocked_by_active_combat"] = True

        proof = HARNESS._normal_terminal_proof(
            frame,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            requested_after_sequence=4,
            initial_participants=[SUBJECT, ALLY, ENEMY],
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(
            proof["checks"][
                "successor_overlap_is_prior_ordered_subsequence"
            ]
        )

    def test_normal_terminal_proof_uses_canonical_independent_side_keys(
        self,
    ) -> None:
        service = _FakeTerminalService(terminal_day=0)
        frame = service._terminal_frame(4)
        self.assertNotIn(
            "side_public_cunit_ids_in_stored_order", frame["prior"]
        )

        proof = HARNESS._normal_terminal_proof(
            frame,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            requested_after_sequence=4,
            initial_participants=[SUBJECT, ALLY, ENEMY],
        )

        self.assertTrue(proof["ok"])
        self.assertTrue(
            proof["checks"][
                "journal_prior_participants_match_initial"
            ]
        )

    def test_membership_unavailable_keeps_terminal_core_typed_but_not_ready(
        self,
    ) -> None:
        service = _FakeTerminalService(terminal_day=0)
        frame = service._terminal_frame(4)
        frame["subject"]["movement_or_retreat_state_raw"] = 0
        frame["successor"] = {
            "state": "unavailable",
            "matching_combat_ids_in_native_order": [],
            "selected_successor_combat_id": None,
            "participant_overlap_public_cunit_ids_in_prior_order": [],
        }

        normalized = normalize_battle_terminal_transition_v1(
            frame,
            expected_prior_combat_id=COMBAT,
            expected_subject_public_cunit_id=SUBJECT,
            expected_after_terminal_sequence=4,
            expected_observed_date_raw=service.date_raw,
            expected_snapshot_revision=service.revision,
        )
        proof = HARNESS._normal_terminal_proof(
            normalized,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
            requested_after_sequence=4,
            initial_participants=[SUBJECT, ALLY, ENEMY],
        )

        self.assertEqual(normalized["status"], "available")
        self.assertEqual(
            proof["subject_ai_membership_status"], "unavailable"
        )
        self.assertTrue(proof["core_ok"])
        self.assertTrue(
            proof["checks"]["successor_state_contract_consistent"]
        )
        self.assertFalse(
            proof["checks"]["successor_or_reentry_state_observed"]
        )
        self.assertFalse(proof["ok"])

    def test_active_cursor_requires_old_combat_to_resolve(self) -> None:
        service = _FakeTerminalService(terminal_day=2)
        frame = service._terminal_frame(None)
        frame["removal"]["prior_combat_strictly_resolves"] = False

        proof = HARNESS._active_terminal_cursor_proof(
            frame,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
        )

        self.assertFalse(proof["ok"])

    def test_empty_journal_cursor_stays_none_for_wire_zero(self) -> None:
        service = _FakeTerminalService(terminal_day=2)
        frame = service._terminal_frame(None)
        frame["terminal_journal"]["oldest_available_sequence"] = 0
        frame["terminal_journal"]["latest_sequence"] = 0

        proof = HARNESS._active_terminal_cursor_proof(
            frame,
            prior_combat_id=COMBAT,
            subject_public_cunit_id=SUBJECT,
        )

        self.assertTrue(proof["ok"])
        self.assertIsNone(proof["cursor"])

    def test_runner_boundary_allows_only_life_advance(self) -> None:
        proof = HARNESS._runner_boundary_proof()

        self.assertTrue(proof["ok"])
        self.assertEqual(proof["allowed_mutation_steps"], ["life-advance"])
        self.assertIn("0x27FB7C0", proof["forbidden_native_calls"])
        self.assertEqual(proof["forbidden_native_calls_invoked"], [])

    def test_same_process_proof_rejects_reconnected_bridge(self) -> None:
        before = {
            "diagnostics": {
                "bridge_pid": 4242,
                "connection_generation": 9,
                "connected": True,
            }
        }
        same = {
            "diagnostics": {
                "bridge_pid": 4242,
                "connection_generation": 9,
                "connected": True,
            }
        }
        reconnected = {
            "diagnostics": {
                "bridge_pid": 4242,
                "connection_generation": 10,
                "connected": True,
            }
        }

        self.assertTrue(HARNESS._same_process_proof(before, same)["ok"])
        self.assertFalse(
            HARNESS._same_process_proof(before, reconnected)["ok"]
        )

    def test_resolve_source_save_binds_hash_inside_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary) / "profile"
            save = profile / "save games" / "fixture.ck3"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"immutable-battle")
            expected = HARNESS._sha256_file(save)

            resolved, identity = HARNESS._resolve_source_save(
                profile, Path("save games/fixture.ck3"), expected
            )

            self.assertEqual(resolved, save.resolve())
            self.assertEqual(identity["sha256"], expected)

    def test_clone_cleanup_requires_marker_and_removes_only_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "xar-terminal-clone"
            target.mkdir()
            nonce = "fixture-nonce"
            (target / HARNESS._CLONE_MARKER_NAME).write_text(
                json.dumps(
                    {
                        "kind": "xar_battle_terminal_journal_clone",
                        "nonce": nonce,
                    }
                ),
                encoding="utf-8",
            )
            (target / "payload.txt").write_text("fixture", encoding="utf-8")

            cleanup = HARNESS._cleanup_clone(
                target,
                clone_nonce=nonce,
                retain_state=False,
                session_started=False,
                session_cleanup_proven=False,
            )

            self.assertTrue(cleanup["ok"])
            self.assertFalse(target.exists())

    def test_clone_is_retained_when_managed_cleanup_is_unproven(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "xar-terminal-clone"
            target.mkdir()

            cleanup = HARNESS._cleanup_clone(
                target,
                clone_nonce="unused",
                retain_state=False,
                session_started=True,
                session_cleanup_proven=False,
            )

            self.assertFalse(cleanup["ok"])
            self.assertTrue(target.exists())
            self.assertFalse(cleanup["attempted"])


if __name__ == "__main__":
    unittest.main()
