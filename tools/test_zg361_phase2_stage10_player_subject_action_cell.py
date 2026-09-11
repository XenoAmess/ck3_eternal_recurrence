#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zg361_phase2_stage10_player_subject_action_cell as cell
from xar_autoplayer.bridge.set_played_character_contract import (
    SET_PLAYED_CHARACTER_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_manager_subordinate_selector_contract import (
    QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY,
)


OWNER = 101
MANAGER = 202


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def scope(name: str, character_id: int) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            }
        },
    }


class Service:
    def __init__(self) -> None:
        self.player = OWNER
        self.date = 9000
        self.initial_date = self.date
        self.revision = 10
        self.event_id: int | None = 11
        self.event_key = cell.STAGE9_EVENT
        self.selector_available = True
        self.opening_case_available = True
        self.provider_terminal = True
        self.selections: list[tuple[int, int]] = []
        self.switches: list[int] = []
        self.saves = 0
        self.provider_query_players: list[int] = []

    def capabilities(self) -> dict[str, object]:
        return {"bridge_capabilities": [
            QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY,
            QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
            SET_PLAYED_CHARACTER_V1_CAPABILITY,
        ]}

    def snapshot(self) -> dict[str, object]:
        return {
            "paused": True,
            "map_ready": True,
            "snapshot_id": f"fixture:{self.revision}",
            "revision": self.revision,
            "native_revision": self.revision,
            "date_raw": self.date,
            "played_character": {"character_id": self.player, "alive": True},
            "diagnostics": {"bridge_pid": 303, "connection_generation": 4},
            "active_event": (
                {"instance_id": self.event_id} if self.event_id is not None else None
            ),
        }

    def query_current_event_window_context_v1(
        self, event_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("event query crossed its fixture frame")
        saved = []
        if self.event_key == cell.STAGE10_EVENT:
            saved = [
                scope("zg361_mg_f_ticket_owner", OWNER),
                scope("zg361_mg_f_ticket_subject", MANAGER),
            ]
        return {
            "status": "available",
            "current_event_window_context": {
                "event_definition_key": self.event_key,
                "current_event_instance_id": event_id,
                "root_scope": scope("root", self.player)["scope"],
                "saved_scopes": saved,
                "options": [{
                    "native_option_index": 0, "shown": True, "enabled": True
                }],
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
        }

    def query_zhongguo_manager_subordinate_selector_v1(
        self, nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("selector revision drift")
        if not self.selector_available:
            return {
                "status": "unavailable",
                "provider_observed": False,
                "readiness": {"ready": False},
                "selection": None,
            }
        return {
            "status": "available",
            "provider_observed": True,
            "readiness": {"ready": True},
            "selection": {
                "manager_character_id": MANAGER,
                "subordinate_character_id": 404,
            },
        }

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("save revision drift")
        self.saves += 1
        return {
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": f"fixture-{self.saves}.ck3",
                "size": 1,
                "sha256": str(self.saves) * 64,
                "date_raw": self.date,
            },
        }

    def select_event_option(
        self, option: int, *, event_instance_id: int, expected_revision: int
    ) -> dict[str, object]:
        if option != 1 or event_instance_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("event selection drift")
        self.selections.append((event_instance_id, option))
        self.event_id = None
        self.revision += 1
        return {"accepted": True, "status": "submitted"}

    def set_player_character_v1(
        self, character_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("switch revision drift")
        self.player = character_id
        self.switches.append(character_id)
        self.revision += 1
        return {
            "accepted": True,
            "status": "switched",
            "to_character_id": character_id,
            "postcondition_verified": True,
        }

    def query_zhongguo_manager_governance_snapshot_v1(
        self,
        nonce: str,
        *,
        expected_revision: int,
        subject_character_id: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("provider revision drift")
        self.provider_query_players.append(self.player)
        terminal_query = self.player == MANAGER
        state = 5 if terminal_query and self.provider_terminal else (
            4 if terminal_query else (1 if self.opening_case_available else 0)
        )
        binding_kind = (
            "played_character" if terminal_query else "bounded_ai_direct_manager"
        )
        return {
            "status": "available",
            "unavailable_reason": None,
            "player_character_id": self.player,
            "readiness": {"ready": terminal_query and self.provider_terminal},
            "binding": {
                "subject_character_id": subject_character_id,
                "owner_character_id": owner_character_id,
                "subject_binding_kind": binding_kind,
            },
            "f_case": {
                "owner_character_id": typed(owner_character_id),
                "subject_character_id": typed(subject_character_id),
                "state": typed(state),
                "active": typed(state not in {0, 5}),
            },
        }


def navigate_to_stage10(service: Service, **kwargs: object) -> dict[str, object]:
    progress = kwargs["evidence_out"]
    assert isinstance(progress, dict)
    assert kwargs["pause_on_event_definition_key"] == cell.STAGE10_EVENT
    assert progress["absolute_end_date_raw"] == service.initial_date + cell.MAX_ADVANCE_DAYS * 24
    probe = kwargs.get("terminal_observation_probe")
    if callable(probe):
        service.date += 2 * 24
        service.revision += 1
        observed = probe(service.snapshot())
        return {
            "result": "TERMINAL_OBSERVATION",
            "date_raw": service.date,
            "terminal_observation": observed,
        }
    service.date += 4 * 24
    service.revision += 1
    service.event_id = 12
    service.event_key = cell.STAGE10_EVENT
    return {"result": "PAUSED_ON_TARGET", "date_raw": service.date}


class Stage10PlayerSubjectTests(unittest.TestCase):
    def run_cell(self, service: Service, directory: Path) -> dict[str, object]:
        return cell.run_stage10_player_subject(
            service,
            evidence_directory=directory,
            request_nonce="fixture.stage10",
            navigator=navigate_to_stage10,
        )

    def test_exact_stage9_source_switches_before_bounded_stage10_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            result = self.run_cell(service, Path(temporary))
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(service.switches, [MANAGER])
            self.assertEqual(service.selections, [(11, 1), (12, 1)])
            self.assertEqual(service.saves, 2)
            self.assertEqual(service.provider_query_players, [OWNER, MANAGER])
            gate = result["p1_acceptance_evidence"]["central_stage_10_terminal"]
            self.assertTrue(gate["provider_observed"])
            self.assertEqual(gate["owner_character_id"], OWNER)
            self.assertEqual(gate["subject_character_id"], MANAGER)
            self.assertEqual(
                gate["role_topology"],
                "ai_central_owner_to_player_manager_subject",
            )

    def test_wrong_source_event_refuses_before_selector_or_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.event_key = "some.other.event"
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                self.run_cell(service, Path(temporary))
            self.assertEqual(service.switches, [])
            self.assertEqual(service.selections, [])
            self.assertEqual(service.saves, 0)

    def test_missing_manager_refuses_before_stage9_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.selector_available = False
            with self.assertRaises(cell.Stage10PlayerSubjectError) as raised:
                self.run_cell(service, Path(temporary))
            self.assertEqual(raised.exception.reason_code, "eligible_manager_unavailable")
            self.assertEqual(service.switches, [])
            self.assertEqual(service.selections, [])
            self.assertEqual(service.saves, 0)

    def test_missing_open_case_never_switches_player(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.opening_case_available = False
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                self.run_cell(service, Path(temporary))
            self.assertEqual(service.switches, [])
            self.assertEqual(service.selections, [(11, 1)])
            self.assertEqual(service.saves, 1)

    def test_nonterminal_provider_does_not_acknowledge_stage10(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.provider_terminal = False
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                self.run_cell(service, Path(temporary))
            self.assertEqual(service.selections, [(11, 1)])
            self.assertEqual(service.saves, 1)
            evidence = copy.deepcopy(service.snapshot())
            self.assertEqual(evidence["active_event"]["instance_id"], 12)


if __name__ == "__main__":
    unittest.main()
