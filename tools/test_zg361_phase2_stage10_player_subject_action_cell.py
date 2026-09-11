#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zg361_phase2_stage10_player_subject_action_cell as cell
from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_promotion_source_progress_contract import (
    ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY,
    QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY,
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
        self.player = MANAGER
        self.date = 9000
        self.initial_date = self.date
        self.revision = 10
        self.event_id: int | None = None
        self.event_key: str | None = None
        self.independent = False
        self.celestial = True
        self.provider_terminal = True
        self.selections: list[tuple[int, int]] = []
        self.saves = 0
        self.provider_calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
                QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
                QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY,
                ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY,
            ]
        }

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

    def query_campaign_root_context_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("campaign query crossed its fixture frame")
        return {
            "status": "available",
            "unavailable_reason": None,
            "campaign_root_context_ready": True,
            "readiness": {"ready": True},
            "player_character_id": self.player,
            "player_character_alive": True,
            "independent": self.independent,
            "immediate_liege_character_id": None if self.independent else OWNER,
            "primary_title": {"tier_raw": 3, "tier_key": "duchy"},
            "government": {
                "key": "celestial_government",
                "flags": ["government_is_celestial"] if self.celestial else [],
            },
            "selected_game_rule_tokens": ["zg361_on"],
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

    def query_current_event_window_context_v1(
        self, event_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("event query crossed its fixture frame")
        return {
            "status": "available",
            "current_event_window_context": {
                "event_definition_key": self.event_key,
                "current_event_instance_id": event_id,
                "root_scope": scope("root", MANAGER)["scope"],
                "saved_scopes": [
                    scope("zg361_mg_f_ticket_owner", OWNER),
                    scope("zg361_mg_f_ticket_subject", MANAGER),
                ],
                "options": [
                    {"native_option_index": 0, "shown": True, "enabled": True}
                ],
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
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
        self.provider_calls += 1
        state = 5 if self.provider_terminal else 4
        return {
            "status": "available",
            "unavailable_reason": None,
            "player_character_id": self.player,
            "readiness": {"ready": self.provider_terminal},
            "binding": {
                "subject_character_id": subject_character_id,
                "owner_character_id": owner_character_id,
                "subject_binding_kind": "played_character",
            },
            "f_case": {
                "owner_character_id": typed(owner_character_id),
                "subject_character_id": typed(subject_character_id),
                "state": typed(state),
                "active": typed(state != 5),
            },
        }

    def select_event_option(
        self, option: int, *, event_instance_id: int, expected_revision: int
    ) -> dict[str, object]:
        if option != 1 or event_instance_id != self.event_id:
            raise AssertionError("event selection drift")
        self.selections.append((event_instance_id, option))
        self.event_id = None
        self.revision += 1
        return {"accepted": True, "status": "submitted"}


def navigate_to_stage10(service: Service, **kwargs: object) -> dict[str, object]:
    progress = kwargs["evidence_out"]
    assert isinstance(progress, dict)
    assert kwargs["pause_on_event_definition_key"] == cell.STAGE10_EVENT
    assert kwargs["prefer_natural_cycle"] is False
    assert progress["absolute_end_date_raw"] == (
        service.initial_date + cell.MAX_ADVANCE_DAYS * 24
    )
    service.date += 4 * 24
    service.revision += 1
    service.event_id = 12
    service.event_key = cell.STAGE10_EVENT
    return {
        "result": "PAUSED_ON_TARGET",
        "date_raw": service.date,
        "review_action": {"accepted": True},
    }


class Stage10PlayerSubjectTests(unittest.TestCase):
    def run_cell(self, service: Service, directory: Path) -> dict[str, object]:
        return cell.run_stage10_player_subject(
            service,
            evidence_directory=directory,
            request_nonce="fixture.stage10",
            expected_player_manager_character_id=MANAGER,
            expected_owner_character_id=OWNER,
            navigator=navigate_to_stage10,
        )

    def test_player_manager_publication_reaches_bounded_stage10_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            result = self.run_cell(service, Path(temporary))
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(service.player, MANAGER)
            self.assertEqual(service.selections, [(12, 1)])
            self.assertEqual(service.saves, 2)
            self.assertEqual(service.provider_calls, 1)
            gate = result["p1_acceptance_evidence"]["central_stage_10_terminal"]
            self.assertEqual(gate["owner_character_id"], OWNER)
            self.assertEqual(gate["subject_character_id"], MANAGER)
            self.assertEqual(
                gate["role_topology"],
                "superior_owner_to_player_manager_subject",
            )

    def test_independent_player_refuses_before_save_or_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.independent = True
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                self.run_cell(service, Path(temporary))
            self.assertEqual(service.saves, 0)
            self.assertEqual(service.selections, [])

    def test_non_celestial_player_refuses_before_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.celestial = False
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                self.run_cell(service, Path(temporary))
            self.assertEqual(service.saves, 0)

    def test_wrong_terminal_event_keeps_source_only(self) -> None:
        def wrong_event(service: Service, **kwargs: object) -> dict[str, object]:
            result = navigate_to_stage10(service, **kwargs)
            service.event_key = "some.other.event"
            return result

        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                cell.run_stage10_player_subject(
                    service,
                    evidence_directory=Path(temporary),
                    request_nonce="fixture.stage10",
                    expected_player_manager_character_id=MANAGER,
                    expected_owner_character_id=OWNER,
                    navigator=wrong_event,
                )
            self.assertEqual(service.saves, 1)
            self.assertEqual(service.selections, [])

    def test_nonterminal_provider_does_not_acknowledge_stage10(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = Service()
            service.provider_terminal = False
            with self.assertRaises(cell.Stage10PlayerSubjectError):
                self.run_cell(service, Path(temporary))
            self.assertEqual(service.selections, [])
            self.assertEqual(service.saves, 1)
            self.assertEqual(service.event_id, 12)


if __name__ == "__main__":
    unittest.main()
