from __future__ import annotations

import copy
import unittest

import extract_zg361_stage10_terminal_gate as extractor


MANAGER = 27181
OWNER = 36354
EXE = "2" * 64


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def char_scope(value: int) -> dict[str, object]:
    return {
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": value,
        }
    }


def fixture() -> tuple[dict[str, object], dict[str, object]]:
    context = {
        "event_definition_key": extractor.EVENT_KEY,
        "date_raw": 1024,
        "current_event_instance_id": 28,
        "root_scope": char_scope(MANAGER),
        "saved_scopes": [
            {"name": "zg361_mg_f_ticket_owner", "scope": char_scope(OWNER)},
            {"name": "zg361_mg_f_ticket_subject", "scope": char_scope(MANAGER)},
        ],
        "options": [
            {"native_option_index": 0, "shown": True, "enabled": True}
        ],
    }
    provider = {
        "status": "available",
        "unavailable_reason": None,
        "date_raw": 1024,
        "paused": True,
        "player_character_id": MANAGER,
        "subject_character_id": MANAGER,
        "requested_owner_character_id": OWNER,
        "subject_binding": {
            "kind": "played_character",
            "manager_character_id": typed(MANAGER),
            "owner_character_id": typed(OWNER),
        },
        "f_case": {
            "owner_character_id": typed(OWNER),
            "subject_character_id": typed(MANAGER),
            "cycle_serial": typed(6),
            "case_serial": typed(1),
            "state": typed(5),
            "active": typed(False),
            "revision": typed(10),
        },
        "readiness": {
            "subject_binding_ready": True,
            "case_identity_ready": True,
            "same_frame_ready": True,
            "ready": False,
        },
        "provenance": {"game_version": extractor.GAME_VERSION, "executable_sha256": EXE},
    }
    query_binding = {
        "queried_snapshot_id": "native:52",
        "queried_revision": 53,
        "queried_native_revision": 52,
    }
    source = {
        "result": "RED",
        "red_preserved": True,
        "video_lock_touched": False,
        "ck3_pids": [214796],
        "evidence": {
            "kind": "zg361_phase2_stage10_player_subject_action_cell",
            "result": "RED",
            "failure_reason": "ValueError: Stage 10 player-subject F case is not terminal",
            "action_ack_is_business_postcondition": False,
            "expected_player_manager_character_id": MANAGER,
            "expected_owner_character_id": OWNER,
            "source_binding": {
                "bridge_pid": 214796,
                "connection_generation": 1,
                "player_character_id": MANAGER,
            },
            "progress": {
                "timeline_origin_date_raw": 160,
                "absolute_end_date_raw": 3040,
                "result": "GREEN",
                "readiness": "paused-real-zg361mg.120",
                "fixture_used": False,
                "console_used": False,
                "action_ack_used_as_state_evidence": False,
                "target_binding": {
                    "snapshot_id": "native:52",
                    "revision": 53,
                    "native_revision": 52,
                    "date_raw": 1024,
                    "event_instance_id": 28,
                    "player_character_id": MANAGER,
                    "connection_generation": 1,
                },
            },
        },
        "failure_snapshot": {
            "date_raw": 1024,
            "paused": True,
            "map_ready": True,
            "snapshot_id": "native:52",
            "revision": 53,
            "native_revision": 52,
            "played_character": {"character_id": MANAGER},
            "active_event": {"instance_id": 28},
            "native_command_history": [
                {
                    "ok": True,
                    "command": "query-current-event-window-context-v1",
                    "result": {
                        "accepted": True,
                        "status": "available",
                        **query_binding,
                        "current_event_window_context": context,
                    },
                },
                {
                    "ok": True,
                    "command": "query-zhongguo-manager-governance-snapshot-v1",
                    "result": {
                        "accepted": True,
                        "status": "available",
                        **query_binding,
                        "queried_connection_generation": 1,
                        "zhongguo_manager_governance_snapshot": provider,
                    },
                },
            ],
        },
    }
    activation = {
        "expected_hashes": {
            "code_commit": "1" * 40,
            "product_tree_sha256": "3" * 64,
            "game_exe_sha256": EXE,
        }
    }
    return source, activation


class ExtractStage10TerminalGateTests(unittest.TestCase):
    def extract(self, source: dict[str, object]) -> dict[str, object]:
        _, activation = fixture()
        return extractor.extract_gate(
            source,
            source_record={"path": "red.json", "sha256": "4" * 64},
            activation=activation,
            activation_record={"path": "activation.json", "sha256": "5" * 64},
        )

    def test_specific_terminal_readiness_recovers_gate_while_aggregate_is_false(self) -> None:
        source, _ = fixture()
        gate = self.extract(source)
        self.assertEqual(gate["result"], "GREEN")
        self.assertTrue(gate["terminal_postcondition_verified"])
        self.assertFalse(gate["provider_observation"]["aggregate_readiness"])
        self.assertEqual(gate["elapsed_game_days"], 36)
        self.assertEqual(gate["preserved_red"]["source_result"], "RED")

    def test_active_f_case_is_rejected(self) -> None:
        source, _ = fixture()
        provider = source["failure_snapshot"]["native_command_history"][1]["result"]["zhongguo_manager_governance_snapshot"]
        provider["f_case"]["active"] = typed(True)
        with self.assertRaisesRegex(ValueError, "not terminal"):
            self.extract(source)

    def test_target_ack_after_event_query_is_rejected(self) -> None:
        source, _ = fixture()
        history = source["failure_snapshot"]["native_command_history"]
        history.append({"ok": True, "command": "select-event-option-1"})
        with self.assertRaisesRegex(ValueError, "acknowledged"):
            self.extract(source)


if __name__ == "__main__":
    unittest.main()
