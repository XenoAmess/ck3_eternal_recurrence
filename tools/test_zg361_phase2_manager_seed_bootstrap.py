#!/usr/bin/env python3
"""CK3-free tests for typed player-manager seed materialization."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

import zg361_phase2_manager_seed_bootstrap as manager


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "type_key": "character",
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def event_payload() -> dict[str, object]:
    return {
        "event_instance_id": 71,
        "event_definition_key": manager.EVENT_DEFINITION_KEY,
        "query": {
            "step": "query-current-event-window-context-v1",
            "accepted": True,
            "current_event_window_context": {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "snapshot_revision": 90,
                "date_raw": 53147016,
                "current_event_instance_id": 71,
                "window_match_count": 1,
                "event_definition_key": manager.EVENT_DEFINITION_KEY,
                "root_scope": character_scope(55001),
                "saved_scopes": [
                    {
                        "name": manager.MANAGER_SCOPE,
                        "scope": character_scope(55001),
                    },
                    {
                        "name": manager.SUBJECT_SCOPE,
                        "scope": character_scope(44001),
                    },
                ],
                "options": [
                    {
                        "rendered_index": 0,
                        "native_option_index": 0,
                        "shown": True,
                        "enabled": True,
                    }
                ],
            },
        },
    }


def snapshot_payload(revision: int = 90) -> dict[str, object]:
    return {
        "snapshot": {
            "revision": revision,
            "date_raw": 53147016,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 55001, "alive": True},
        }
    }


def close_payload() -> dict[str, object]:
    return {
        "step": "select-event-option-1",
        "accepted": True,
        "status": "submitted",
        "option_number": 1,
        "option_index": 0,
        "event_selection": {
            "postcondition_verified": True,
            "old_event_instance_id": 71,
            "new_event_instance_id": None,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "ending_revision": 91,
        },
    }


def main() -> int:
    capture = manager.extract_event_capture(event_payload())
    # Deliberately differ from the blocked base request's han_6875/29037. The
    # candidate must preserve the typed CharacterID and must not guess a
    # historical database key for it.
    assert capture["played_character_id"] == 55001
    assert capture["manager_entry"] == {
        "schema_version": 1,
        "manager_character_id": 55001,
        "reviewable_subject_character_id": 44001,
        "manager_scope": manager.MANAGER_SCOPE,
        "subject_scope": manager.SUBJECT_SCOPE,
        "human": True,
        "alive": True,
        "landed": True,
        "celestial_liege": True,
        "game_rule_enabled": True,
        "existing_direct_reviewable_vassal_count_minimum": 1,
        "b1_active": False,
        "central_active": False,
        "pp_active": False,
        "review_now_eligible": True,
    }

    wrong_manager = event_payload()
    scopes = wrong_manager["query"]["current_event_window_context"]["saved_scopes"]
    scopes[0]["scope"] = character_scope(99999)
    try:
        manager.extract_event_capture(wrong_manager)
    except manager.ManagerSeedBootstrapError as error:
        assert "differs from the played event root" in str(error)
    else:
        raise AssertionError("non-player manager scope was accepted")

    self_subject = event_payload()
    self_subject["query"]["current_event_window_context"]["saved_scopes"][1][
        "scope"
    ] = character_scope(55001)
    try:
        manager.extract_event_capture(self_subject)
    except manager.ManagerSeedBootstrapError as error:
        assert "identical" in str(error)
    else:
        raise AssertionError("self-subject manager seed was accepted")

    duplicate = event_payload()
    duplicate["query"]["current_event_window_context"]["saved_scopes"].append(
        copy.deepcopy(
            duplicate["query"]["current_event_window_context"]["saved_scopes"][0]
        )
    )
    try:
        manager.extract_event_capture(duplicate)
    except manager.ManagerSeedBootstrapError as error:
        assert "repeated" in str(error)
    else:
        raise AssertionError("duplicate manager scope was accepted")

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        profile = root / "profile"
        save = profile / "save games" / "xar_checkpoint.ck3"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"SAV0101" + b"\0" * 12 + b"1.19.0.6" + b"\0" * 128)
        save_sha = hashlib.sha256(save.read_bytes()).hexdigest()
        checkpoint = {
            "step": "save-checkpoint",
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": str(save),
                "size": save.stat().st_size,
                "sha256": save_sha,
                "date_raw": 53147016,
                "episode_character_id": 55001,
                "strategy": "native-autosave-command-v1",
            },
        }
        checkpoint_path = root / "checkpoint.json"
        write_json(checkpoint_path, checkpoint)

        class FakeService:
            def __init__(self) -> None:
                self.closed = False
                self.calls: list[tuple[object, ...]] = []

            def snapshot(self) -> dict[str, object]:
                value = copy.deepcopy(snapshot_payload(91 if self.closed else 90)["snapshot"])
                value["active_event"] = (
                    None
                    if self.closed
                    else {"instance_id": 71, "option_count": 1}
                )
                self.calls.append(("snapshot", value["revision"]))
                return value

            def query_current_event_window_context_v1(
                self, event_instance_id: int, *, expected_revision: int
            ) -> dict[str, object]:
                self.calls.append(("query", event_instance_id, expected_revision))
                return copy.deepcopy(event_payload()["query"])

            def select_event_option(
                self,
                option_number: int,
                *,
                event_instance_id: int,
                expected_revision: int,
            ) -> dict[str, object]:
                self.calls.append(
                    ("select", option_number, event_instance_id, expected_revision)
                )
                self.closed = True
                return close_payload()

            def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
                self.calls.append(("save", expected_revision))
                return json.loads(checkpoint_path.read_text(encoding="utf-8"))

        captured_dir = root / "captured"
        service = FakeService()
        captured = manager.capture_mcp_evidence(service, captured_dir)
        assert captured["result"] == "GREEN"
        assert captured["manager_entry"] == capture["manager_entry"]
        assert service.calls == [
            ("snapshot", 90),
            ("query", 71, 90),
            ("snapshot", 90),
            ("select", 1, 71, 90),
            ("snapshot", 91),
            ("save", 91),
        ]

        output = root / "candidate"
        result = manager.materialize_candidate(
            event_context_path=Path(captured["event_context_path"]),
            paused_snapshot_path=Path(captured["paused_snapshot_path"]),
            event_close_path=Path(captured["event_close_path"]),
            checkpoint_response_path=Path(captured["checkpoint_response_path"]),
            profile=profile,
            output_dir=output,
            base_contract_path=manager.DEFAULT_BASE_CONTRACT,
            source_git_commit="a" * 40,
            product_tree_sha256="b" * 64,
            fixture_tree_sha256="c" * 64,
        )
        assert result["result"] == "GREEN"
        assert result["ready"] is True
        contract = json.loads(
            Path(result["contract_path"]).read_text(encoding="utf-8")
        )
        assert contract["kind"] == "zg361_phase2_player_manager_paused_seed"
        assert contract["seed_purpose"] == "player-manager"
        assert contract["source"]["sha256"] == save_sha
        assert contract["saved_state"]["played_character_id"] == 55001
        assert contract["saved_state"]["player_history_id"] is None
        assert contract["manager_entry"] == capture["manager_entry"]
        assert contract["domain_query_matrix"] == {
            "schema_version": 1,
            "b2_pip_owner_character_id": 55001,
            "incident_owner_character_id": 55001,
            "workforce_owner_character_id": 55001,
            "ai_owned_case_owner_character_id": 55001,
            "ai_owned_case_subject_character_id": 44001,
        }
        report = json.loads(Path(result["report_path"]).read_text(encoding="utf-8"))
        assert report["product_receipts_written_by_fixture"] is False
        assert report["fixture_opened_product_b1"] is False
        assert report["mcp_only"] is True

    print("GREEN: typed player-manager seed materializer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
