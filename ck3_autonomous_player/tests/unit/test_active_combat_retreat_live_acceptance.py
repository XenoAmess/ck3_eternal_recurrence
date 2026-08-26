from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_active_combat_retreat_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_active_combat_retreat_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


SUBJECT = 83_886_341
OWNER_SUBJECT = 357
OWNER_ALLY = 33_554_657
COMBAT = 335_544_325


def _pre(*, side_index: int = 0, scope: str = "full_side") -> dict[str, object]:
    affected = [SUBJECT] if scope == "full_side" else [OWNER_SUBJECT]
    unaffected = [] if scope == "full_side" else [OWNER_ALLY]
    return {
        "side_index": side_index,
        "side_scope": scope,
        "affected_public_cunit_ids_in_stored_order": affected,
        "unaffected_same_side_public_cunit_ids_in_stored_order": unaffected,
        "battle_control_snapshot": {
            "combat_id": COMBAT,
            "attacker": {
                "ordered_armies": [{"public_cunit_id": SUBJECT}]
            },
            "defender": {
                "ordered_armies": [
                    {"public_cunit_id": OWNER_SUBJECT},
                    {"public_cunit_id": OWNER_ALLY},
                ]
            },
        },
    }


def _transition(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "status": "available",
        "battle_transition_ready": True,
        "combat_id": COMBAT,
        "phase": "pursuit",
        "winner_side": "defender",
        "attacker_public_cunit_ids_in_stored_order": [SUBJECT],
        "defender_public_cunit_ids_in_stored_order": [357, 33_554_657],
    }
    value.update(overrides)
    return value


class ActiveCombatRetreatLiveAcceptanceTests(unittest.TestCase):
    def test_opposite_winner_pursuit_is_full_side_terminal(self) -> None:
        self.assertTrue(
            HARNESS._full_side_transition_ready(
                _transition(), _pre(), SUBJECT
            )
        )

    def test_defender_retreat_requires_attacker_winner(self) -> None:
        self.assertTrue(
            HARNESS._full_side_transition_ready(
                _transition(
                    winner_side="attacker",
                    attacker_public_cunit_ids_in_stored_order=[357],
                    defender_public_cunit_ids_in_stored_order=[SUBJECT],
                ),
                _pre(side_index=1),
                SUBJECT,
            )
        )

    def test_generation_checked_removal_is_terminal(self) -> None:
        self.assertTrue(
            HARNESS._full_side_transition_ready(
                _transition(
                    status="combat_not_found",
                    phase=None,
                    winner_side=None,
                    attacker_public_cunit_ids_in_stored_order=[],
                    defender_public_cunit_ids_in_stored_order=[],
                ),
                _pre(),
                SUBJECT,
            )
        )

    def test_same_day_join_reopen_requires_departed_subject(self) -> None:
        reopened = _transition(
            phase="main",
            winner_side="none",
            attacker_public_cunit_ids_in_stored_order=[16_777_300],
        )
        self.assertTrue(
            HARNESS._full_side_transition_ready(reopened, _pre(), SUBJECT)
        )
        reopened["attacker_public_cunit_ids_in_stored_order"] = [SUBJECT]
        self.assertFalse(
            HARNESS._full_side_transition_ready(reopened, _pre(), SUBJECT)
        )

    def test_wrong_winner_or_phase_is_not_terminal(self) -> None:
        self.assertFalse(
            HARNESS._full_side_transition_ready(
                _transition(winner_side="attacker"), _pre(), SUBJECT
            )
        )
        self.assertFalse(
            HARNESS._full_side_transition_ready(
                _transition(phase="main"), _pre(), SUBJECT
            )
        )

    def test_scope_identity_and_readiness_are_bound(self) -> None:
        self.assertFalse(
            HARNESS._full_side_transition_ready(
                _transition(), _pre(scope="owner_subset"), SUBJECT
            )
        )
        self.assertFalse(
            HARNESS._full_side_transition_ready(
                _transition(combat_id=COMBAT + 1), _pre(), SUBJECT
            )
        )
        self.assertFalse(
            HARNESS._full_side_transition_ready(
                _transition(battle_transition_ready=False), _pre(), SUBJECT
            )
        )

    def test_pre_action_combat_id_uses_real_nested_service_frame(self) -> None:
        self.assertEqual(HARNESS._battle_combat_id(_pre()), COMBAT)
        self.assertEqual(
            HARNESS._battle_combat_id({"combat_id": COMBAT}), COMBAT
        )
        self.assertIsNone(
            HARNESS._battle_combat_id(
                {"battle_control_snapshot": {"combat_id": True}}
            )
        )

    def test_owner_subset_requires_affected_departure_and_ally_retention(
        self,
    ) -> None:
        transition = _transition(
            phase="main",
            winner_side="none",
            attacker_public_cunit_ids_in_stored_order=[SUBJECT],
            defender_public_cunit_ids_in_stored_order=[OWNER_ALLY],
        )
        pre = _pre(side_index=1, scope="owner_subset")
        self.assertTrue(
            HARNESS._owner_subset_transition_ready(
                transition, pre, OWNER_SUBJECT
            )
        )
        transition["defender_public_cunit_ids_in_stored_order"] = [
            OWNER_SUBJECT,
            OWNER_ALLY,
        ]
        self.assertFalse(
            HARNESS._owner_subset_transition_ready(
                transition, pre, OWNER_SUBJECT
            )
        )

    def test_owner_subset_rejects_missing_ally_or_opponent(self) -> None:
        pre = _pre(side_index=1, scope="owner_subset")
        missing_ally = _transition(
            phase="main",
            winner_side="none",
            attacker_public_cunit_ids_in_stored_order=[SUBJECT],
            defender_public_cunit_ids_in_stored_order=[],
        )
        self.assertFalse(
            HARNESS._owner_subset_transition_ready(
                missing_ally, pre, OWNER_SUBJECT
            )
        )
        missing_opponent = dict(missing_ally)
        missing_opponent["defender_public_cunit_ids_in_stored_order"] = [
            OWNER_ALLY
        ]
        missing_opponent["attacker_public_cunit_ids_in_stored_order"] = []
        self.assertFalse(
            HARNESS._owner_subset_transition_ready(
                missing_opponent, pre, OWNER_SUBJECT
            )
        )

    def test_expected_scope_dispatch_is_strict(self) -> None:
        transition = _transition(
            phase="main",
            winner_side="none",
            attacker_public_cunit_ids_in_stored_order=[SUBJECT],
            defender_public_cunit_ids_in_stored_order=[OWNER_ALLY],
        )
        pre = _pre(side_index=1, scope="owner_subset")
        self.assertTrue(
            HARNESS._expected_scope_transition_ready(
                "owner_subset", transition, pre, OWNER_SUBJECT
            )
        )
        self.assertFalse(
            HARNESS._expected_scope_transition_ready(
                "unexpected", transition, pre, OWNER_SUBJECT
            )
        )


if __name__ == "__main__":
    unittest.main()
