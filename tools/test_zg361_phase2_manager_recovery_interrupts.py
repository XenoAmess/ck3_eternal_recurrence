#!/usr/bin/env python3
"""Purpose-split contracts for incidental manager-cycle event drains."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import re
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


def _extract_block(source: str, header: str) -> str:
    header_index = source.index(header)
    open_index = source.index("{", header_index + len(header))
    depth = 0
    for index in range(open_index, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[header_index:index + 1]
    raise AssertionError(f"unterminated source block: {header}")


def _human_tribute_scopes() -> list[dict[str, object]]:
    return [
        _scope("actor", "character", 34077),
        _scope("recipient", "character", 32904),
        _scope("secondary_actor", "character", unavailable_character=True),
        _scope("secondary_recipient", "character", 54393),
        _scope("intermediary", "character", unavailable_character=True),
        _scope("tribute_mission_target", "character", 32904),
        _scope("tributary_scope", "character", 34077),
        _scope("overlord_scope", "character", 32904),
        _scope("receiving_character", "character", 32904),
        _scope("opinion_of_tributary", "value"),
        _scope("concubine_character", "character", 54393),
        _scope("human_tribute", "character", 54393),
        _scope("tribute_reward_type_treasury", "value"),
        _scope("saved_innovation", "culture_innovation"),
    ]


class ManagerRecoveryInterruptTests(unittest.TestCase):
    def test_clean_boundary_recovery_keeps_known_vanilla_contract(self) -> None:
        contract = production._resolve_timeline_interrupt_contract(
            "tribute_mission.1002",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=True,
        )

        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract["root_character_id"], 32904)
        self.assertTrue(contract["manager_recovery_only"])
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["saved_scope_count"], 14)

        pp_fallback = production._resolve_timeline_interrupt_contract(
            "zg361pp.146",
            player=32904,
            starting_date=53147016,
            stop_at_clean_review_boundary=True,
        )
        self.assertIsNotNone(pp_fallback)
        assert pp_fallback is not None
        self.assertEqual(pp_fallback["selected_native_option_index"], 0)

        self.assertIsNone(
            production._resolve_timeline_interrupt_contract(
                "unreviewed_vanilla.1",
                player=32904,
                starting_date=53147016,
                stop_at_clean_review_boundary=True,
            )
        )

    def test_random_bad_nickname_uses_only_visible_authored_option(self) -> None:
        event_key = "lifestyle_nicknames.1000"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=24,
            date_raw=53158896,
            player=32904,
            scopes=[
                _scope("possible_conqueror", "character", 32904),
                _scope("toggle_null_result", "boolean"),
                _scope("nickname_root_scope", "character", 32904),
                _scope("had_nick_the_mad", "boolean"),
                _scope("nickname_getter", "character", 32904),
                _scope("informer", "character", 28314),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53158896,
                "active_event": {"option_count": 6},
            },
            event={"event_instance_id": 24},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["character_scopes"],
            {
                "possible_conqueror": 32904,
                "nickname_root_scope": 32904,
                "nickname_getter": 32904,
            },
        )
        self.assertEqual(contract["snapshot_option_count"], 6)
        self.assertEqual(contract["native_option_indices"], (1,))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["max_occurrences"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"] = drifted["saved_scopes"][:-1]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53158896,
                "active_event": {"option_count": 6},
            },
            event={"event_instance_id": 24},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:informer:type"])
        self.assertFalse(drift_checks["scope:informer:unique_third_party"])
        self.assertFalse(drift_checks["saved_scope_names_exact"])
        self.assertFalse(drift_checks["saved_scope_count"])

    def test_fallback_secret_discovery_reveals_only_bound_secret(self) -> None:
        event_key = "spymaster_task.0359"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=69,
            date_raw=53168112,
            player=32904,
            scopes=[
                _scope("scheme", "scheme"),
                _scope("owner", "character", 29889),
                _scope("artifact", "artifact"),
                _scope("target", "character", 28667),
                _scope("councillor_liege", "character", 32904),
                _scope("target_character", "character", 28667),
                _scope("councillor", "character", 29889),
                _scope("active_councillor", "character", 29889),
                _scope("secret_holder", "character", 29503),
                _scope("secret_to_reveal", "secret"),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53168112,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 69},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"], {"councillor_liege": 32904})
        self.assertEqual(contract["saved_scope_count"], 10)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["max_occurrences"], 2)

        first_repeat = copy.deepcopy(context)
        first_repeat["current_event_instance_id"] = 91
        first_repeat["date_raw"] = 53178192
        first_repeat_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53178192,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 91},
            context=first_repeat,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(first_repeat_checks.values()), first_repeat_checks)

        second = copy.deepcopy(context)
        second["current_event_instance_id"] = 92
        second["date_raw"] = 53178912
        second["saved_scopes"][8] = _scope(
            "secret_holder", "character", 28677,
        )
        second_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53178912,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 92},
            context=second,
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(second_checks.values()), second_checks)

        completed = [
            {"event_definition_key": event_key, "event_instance_id": 91},
            {"event_definition_key": event_key, "event_instance_id": 92},
        ]
        max_occurrences = int(contract["max_occurrences"])

        def next_occurrence_allowed(rows: list[dict[str, object]]) -> bool:
            occurrence_count = sum(
                row.get("event_definition_key") == event_key for row in rows
            )
            return occurrence_count < max_occurrences

        self.assertTrue(next_occurrence_allowed([]))
        self.assertTrue(next_occurrence_allowed(completed[:1]))
        self.assertFalse(next_occurrence_allowed(completed))

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][5] = _scope(
            "target_character", "character", 29503,
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53168112,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 69},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:target:matches_any"])
        self.assertFalse(drift_checks["scope:target_character:matches_any"])

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

    def test_chancellor_truce_cancel_binds_only_authored_route(self) -> None:
        event_key = "chancellor_task.1102"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53151120,
            player=32904,
            scopes=[
                _scope("councillor", "character", 28761),
                _scope("councillor_liege", "character", 32904),
                _scope("target", "character", 30921),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53151120,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"]["councillor_liege"], 32904)
        self.assertEqual(contract["scope_types"]["councillor"], "character")
        self.assertEqual(contract["scope_types"]["target"], "character")
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2]["scope"]["type_key"] = "landed_title"
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53151120,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:target:type"])

    def test_celestial_study_uses_friendship_progress_route(self) -> None:
        event_key = "tgp_movement_events.0070"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53150712,
            player=32904,
            scopes=[
                _scope("my_movement", "situation_participant_group"),
                _scope("councillor", "character", 29889),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["scope_types"]["my_movement"],
            "situation_participant_group",
        )
        self.assertEqual(contract["scope_types"]["councillor"], "character")
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["options"][2]["native_option_index"] = 3
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_family_subsidy_uses_terminal_hidden_option_route(self) -> None:
        event_key = "tgp_movement_events.0080"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=206,
            date_raw=53205336,
            player=32904,
            scopes=[
                _scope("root_scope", "character", 32904),
                _scope("my_movement", "situation_participant_group"),
                _scope("family_member", "character", 31137),
            ],
            native_option_indices=(1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 206},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"]["root_scope"], 32904)
        self.assertEqual(
            contract["scope_types"]["my_movement"],
            "situation_participant_group",
        )
        self.assertEqual(contract["scope_types"]["family_member"], "character")
        self.assertEqual(contract["snapshot_option_count"], 4)
        self.assertEqual(contract["native_option_indices"], (1, 2, 3))
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "family_member", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53205336,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 206},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:family_member:unique_third_party"])

    def test_shinto_visitor_uses_deterministic_welcome_route(self) -> None:
        event_key = "tgp_movement_events.0150"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53150712,
            player=32904,
            scopes=[
                _scope("other_ruler", "character", 29646),
                _scope("monk", "character", 16783528),
            ],
            native_option_indices=(1, 2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["saved_scope_count"], 2)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150712,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_ep1_language_quarrel_binds_r289_frame_and_positive_route(self) -> None:
        event_key = "ep1_flavor.0021"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=205,
            date_raw=53215344,
            player=32904,
            scopes=[
                _scope("rival_realm", "landed_title"),
                _scope("rival_monarch", "character", 36310),
                _scope("nitpicker", "character", 37929),
            ],
            native_option_indices=(0, 1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53215344,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 205},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(contract["saved_scope_count"], 3)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "nitpicker", "character", 36310
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53215344,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 205},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:rival_monarch:differs_from"])
        self.assertFalse(drift_checks["scope:nitpicker:differs_from"])

    def test_ck3_11906_ep1_language_route_b_avoids_duel_and_modifier(self) -> None:
        event_source = (
            ROOT
            / "Crusader Kings III"
            / "game"
            / "events"
            / "dlc"
            / "ep1"
            / "ep1_flavor_events.txt"
        )
        if not event_source.is_file():
            self.skipTest("CK3 1.19.0.6 source is not present on this machine")
        self.assertEqual(
            hashlib.sha256(event_source.read_bytes()).hexdigest().upper(),
            "CC4CD67B77F9FA7B83E3B7A5534045F0DBFC1E724C53182E19ED7884BAD10924",
        )
        event_block = _extract_block(
            event_source.read_text(encoding="utf-8-sig"),
            "ep1_flavor.0021 =",
        )
        self.assertEqual(
            re.findall(
                r"(?m)^\t\tname = (ep1_flavor\.0021\.[abc])$",
                event_block,
            ),
            [
                "ep1_flavor.0021.a",
                "ep1_flavor.0021.b",
                "ep1_flavor.0021.c",
            ],
        )
        route_b_start = event_block.index("\toption =", event_block.index("\toption =") + 1)
        route_b = _extract_block(event_block[route_b_start:], "\toption =")
        self.assertIn("progress_towards_friend_effect", route_b)
        self.assertIn("minor_cultural_acceptance_gain", route_b)
        self.assertNotIn("\t\tduel =", route_b)
        self.assertNotIn("add_character_modifier", route_b)
        self.assertNotIn("trigger_event", route_b)

    def test_military_aid_letter_acknowledges_exact_governor_pair(self) -> None:
        event_key = "tgp_interaction_event.0015"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53156904,
            player=32904,
            scopes=[
                _scope("actor", "character", 30987),
                _scope("recipient", "character", 32904),
                _scope("secondary_actor", "character", unavailable_character=True),
                _scope("secondary_recipient", "character", 28664),
                _scope("intermediary", "character", unavailable_character=True),
                _scope("governor_at_war", "character", 32904),
                _scope("governor_joining", "character", 28664),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156904,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["character_scopes"]["recipient"], 32904)
        self.assertEqual(contract["character_scopes"]["governor_at_war"], 32904)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][-1] = _scope(
            "governor_joining", "character", 28665
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53156904,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:governor_joining:matches_any"]
        )

    def test_boiling_anger_response_uses_only_visible_stress_relief(self) -> None:
        event_key = "stress_threshold.2202"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53148288,
            player=32904,
            scopes=[
                _scope("stress_character", "character", 26849),
                _scope("character_to_yell_at", "character", 32904),
            ],
            native_option_indices=(1,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148288,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(
            contract["character_scopes"]["character_to_yell_at"],
            32904,
        )
        self.assertEqual(contract["scope_types"]["stress_character"], "character")
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        drifted = copy.deepcopy(context)
        drifted["options"][0]["native_option_index"] = 0
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148288,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_dynasty_birth_notice_only_acknowledges_bound_family(self) -> None:
        event_key = "birth.1010"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=16,
            date_raw=53154408,
            player=32904,
            scopes=[
                _scope("child", "character", 16790642),
                _scope("father", "character", 36354),
                _scope("real_father", "character", 36354),
                _scope("mother", "character", 35997),
                _scope("is_bastard", "boolean"),
                _scope("is_child_of_concubine", "boolean"),
                _scope("matrilineal", "boolean"),
                _scope("spouse_of_mother", "character", 36354),
            ],
            native_option_indices=(0,),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53154408,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(contract["max_occurrences"], 2)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope(
            "real_father", "character", 36355
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53154408,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 16},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:real_father:matches_any"])

    def test_epidemic_notice_avoids_physician_followup_chain(self) -> None:
        event_key = "epidemic_events.1100"
        contract = _manager_contract(event_key, player=32904)
        for native_indices in ((0, 1), (0, 2)):
            with self.subTest(native_indices=native_indices):
                context = _context(
                    event_key=event_key,
                    instance_id=14,
                    date_raw=53148360,
                    player=32904,
                    scopes=[
                        _scope("epidemic", "epidemic"),
                        _scope("province", "province"),
                        _scope("infected_county", "landed_title"),
                    ],
                    native_option_indices=native_indices,
                )
                checks = production._known_interrupt_checks(
                    snapshot={
                        "date_raw": 53148360,
                        "active_event": {"option_count": 3},
                    },
                    event={"event_instance_id": 14},
                    context=context,
                    event_key=event_key,
                    contract=contract,
                )
                self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53148360,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("province", "province"),
                _scope("infected_county", "landed_title"),
            ],
            native_option_indices=(0, 2),
        )
        drifted = copy.deepcopy(context)
        drifted["options"][1]["native_option_index"] = 3
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53148360,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 14},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["authored_options_exact"])

    def test_epidemic_scapegoat_response_slows_witch_trials(self) -> None:
        event_key = "epidemic_events.1060"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=212,
            date_raw=53225568,
            player=32904,
            scopes=[
                _scope("epidemic", "epidemic"),
                _scope("epidemic_scope", "epidemic"),
                _scope("story_scope", "story"),
            ],
            native_option_indices=(1, 2),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225568,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 212},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(contract["max_occurrences"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][2] = _scope("story_scope", "situation")
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53225568,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 212},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["scope:story_scope:type"])

    def test_populist_ultimatum_refuses_immediate_title_transfer(self) -> None:
        event_key = "faction_demand.1001"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=214,
            date_raw=53229048,
            player=32904,
            scopes=[
                _scope("faction", "faction"),
                _scope("peasant_county", "landed_title"),
                _scope("faction_target", "character", 32904),
                _scope("target_title", "landed_title"),
                _scope("peasant_leader", "character", 16820110),
            ],
            native_option_indices=(2, 3),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229048,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 214},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertEqual(contract["max_occurrences"], 1)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"][4] = _scope(
            "peasant_leader", "character", 32904
        )
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53229048,
                "active_event": {"option_count": 4},
            },
            event={"event_instance_id": 214},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(
            drift_checks["scope:peasant_leader:unique_third_party"]
        )

    def test_concubine_tribute_declines_person_without_court_mutation(self) -> None:
        event_key = "tribute_mission.1002"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=14,
            date_raw=53150160,
            player=32904,
            scopes=_human_tribute_scopes(),
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

    def test_tribute_reward_uses_no_player_resource_cost_route(self) -> None:
        event_key = "tribute_mission.1005"
        contract = _manager_contract(event_key, player=32904)
        context = _context(
            event_key=event_key,
            instance_id=15,
            date_raw=53150184,
            player=32904,
            scopes=[
                *_human_tribute_scopes(),
                _scope("rejected_concubine", "flag"),
                _scope("decided_on_treasury_reward", "flag"),
            ],
            native_option_indices=(0, 1, 2, 3, 5, 6),
        )
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150184,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 15},
            context=context,
            event_key=event_key,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 6)
        self.assertEqual(contract["selected_native_option_index"], 5)

        compact = copy.deepcopy(context)
        compact["saved_scopes"] = [
            row
            for row in compact["saved_scopes"]
            if row["name"] not in {"concubine_character", "rejected_concubine"}
        ]
        compact_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150400,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 15},
            context={**compact, "date_raw": 53150400},
            event_key=event_key,
            contract=contract,
        )
        self.assertTrue(all(compact_checks.values()), compact_checks)

        drifted = copy.deepcopy(context)
        drifted["saved_scopes"] = drifted["saved_scopes"][:-1]
        drift_checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53150184,
                "active_event": {"option_count": 7},
            },
            event={"event_instance_id": 15},
            context=drifted,
            event_key=event_key,
            contract=contract,
        )
        self.assertFalse(drift_checks["saved_scope_names_exact"])


if __name__ == "__main__":
    unittest.main()
