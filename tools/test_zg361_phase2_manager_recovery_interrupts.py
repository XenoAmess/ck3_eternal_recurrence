#!/usr/bin/env python3
"""Purpose-split contracts for incidental manager-cycle event drains."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


def _scope(
    name: str,
    type_key: str,
    character_id: int | None = None,
    *,
    unavailable_character: bool = False,
) -> dict[str, object]:
    if character_id is not None:
        typed_identity: dict[str, object] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    else:
        typed_identity = {
            "status": "unavailable",
            "reason": (
                "character_scope_identity_unavailable"
                if unavailable_character
                else "generic_scope_payload_identity_not_closed"
            ),
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": typed_identity,
        },
    }


def _context(
    *,
    event_key: str,
    instance_id: int,
    date_raw: int,
    player: int,
    scopes: list[dict[str, object]],
    native_option_indices: tuple[int, ...],
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": event_key,
        "current_event_instance_id": instance_id,
        "date_raw": date_raw,
        "root_scope": _scope("root", "character", player)["scope"],
        "saved_scopes": scopes,
        "options": [
            {
                "rendered_index": rendered,
                "native_option_index": native,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for rendered, native in enumerate(native_option_indices)
        ],
    }


def _manager_contract(event_key: str, *, player: int) -> dict[str, object]:
    contract = production._manager_recovery_contract(
        production.KNOWN_TIMELINE_INTERRUPTS[event_key],
        player=player,
        event_key=event_key,
    )
    return production._timeline_contract_for_window(
        contract,
        starting_date=53147016,
    )


class ManagerRecoveryInterruptTests(unittest.TestCase):
    def test_nonfounder_culture_notification_selects_other_acknowledgement(
        self,
    ) -> None:
        event_key = "culture_notification.1111"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53148048,
            player=32904,
            scopes=[
                _scope("founder", "character", 35761),
                _scope("parent_culture_1", "culture"),
                _scope("new_culture", "culture"),
                _scope("parent_1", "culture"),
                _scope("ethos", "flag"),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148048,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["scope_types"]["founder"], "character")
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148048,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_concubine_tribute_declines_person_without_court_mutation(self) -> None:
        event_key = "tribute_mission.1002"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53150160,
            player=32904,
            scopes=[
                _scope("actor", "character", 34077),
                _scope("recipient", "character", 32904),
                _scope(
                    "secondary_actor",
                    "character",
                    unavailable_character=True,
                ),
                _scope("secondary_recipient", "character", 54393),
                _scope(
                    "intermediary",
                    "character",
                    unavailable_character=True,
                ),
                _scope("tribute_mission_target", "character", 32904),
                _scope("tributary_scope", "character", 34077),
                _scope("overlord_scope", "character", 32904),
                _scope("receiving_character", "character", 32904),
                _scope("opinion_of_tributary", "value"),
                _scope("concubine_character", "character", 54393),
                _scope("human_tribute", "character", 54393),
                _scope("tribute_reward_type_treasury", "value"),
                _scope("saved_innovation", "culture_innovation"),
            ],
            native_option_indices=(0, 1, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150160,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"] = drifted["saved_scopes"][:-1]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150160,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])
        self.assertFalse(drift_checks["saved_scope_count"])


if __name__ == "__main__":
    unittest.main()
