#!/usr/bin/env python3
"""Deterministic tests for typed phase-two seed materialization."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

import zg361_phase2_seed_bootstrap as bootstrap


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def event_payload() -> dict[str, object]:
    scope_ids = {
        "zga_phase2_b2_owner": 32904,
        "zga_phase2_incident_owner": 32904,
        "zga_phase2_workforce_owner": 32904,
        "zga_phase2_ai_owned_owner": 32904,
        "zga_phase2_ai_owned_subject": 29037,
    }
    return {
        "event_instance_id": 17,
        "event_definition_key": bootstrap.EVENT_DEFINITION_KEY,
        "query": {
            "step": "query-current-event-window-context-v1",
            "accepted": True,
            "status": "available",
            "current_event_window_context": {
                "schema": "current-event-window-context-v1",
                "schema_version": 1,
                "status": "available",
                "snapshot_revision": 80,
                "date_raw": 53147016,
                "current_event_instance_id": 17,
                "window_match_count": 1,
                "event_definition_key": bootstrap.EVENT_DEFINITION_KEY,
                "root_scope": character_scope(29037),
                "options": [
                    {
                        "rendered_index": 0,
                        "native_option_index": 0,
                        "shown": True,
                        "enabled": True,
                    }
                ],
                "saved_scopes": [
                    {
                        "name": name,
                        "name_identifier": index + 100,
                        "scope": character_scope(character_id),
                    }
                    for index, (name, character_id) in enumerate(
                        scope_ids.items()
                    )
                ],
            },
        },
    }


def close_payload() -> dict[str, object]:
    return {
        "step": "select-event-option-1",
        "accepted": True,
        "status": "submitted",
        "option_number": 1,
        "option_index": 0,
        "event_selection": {
            "status": "event_instance_advanced",
            "postcondition_verified": True,
            "old_event_instance_id": 17,
            "new_event_instance_id": None,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "ending_revision": 82,
        },
    }


def paused_snapshot_payload() -> dict[str, object]:
    return {
        "snapshot": {
            "revision": 81,
            "date_raw": 53147016,
            "paused": True,
            "map_ready": True,
            "played_character": {
                "character_id": 29037,
                "alive": True,
            },
        }
    }


def provider_probes_payload() -> dict[str, object]:
    selectors = {
        "schema_version": 1,
        "b2_pip_owner_character_id": 32904,
        "incident_owner_character_id": 32904,
        "workforce_owner_character_id": 32904,
        "ai_owned_case_owner_character_id": 32904,
        "ai_owned_case_subject_character_id": 29037,
    }
    readiness = {
        "b2_pip_ready": True,
        "incident_profiles_ready": True,
        "incident_mixed_na_positive": True,
        "workforce_collective_ready": True,
        "ai_owned_case_ready": True,
    }
    available = {"status": "available", "readiness": {"ready": True}}
    return {
        "schema_version": 1,
        "result": "captured",
        "mcp_only": True,
        "snapshot": {
            "revision": 82,
            "date_raw": 53147016,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 29037, "alive": True},
        },
        "selectors": selectors,
        "responses": {
            "b2_pip": {"response": copy.deepcopy(available)},
            "incident_x": {
                "response": {
                    **copy.deepcopy(available),
                    "terminal": {"kind": "na"},
                }
            },
            "incident_y": {
                "response": {
                    **copy.deepcopy(available),
                    "terminal": {"kind": "incident"},
                }
            },
            "incident_z": {
                "response": {
                    **copy.deepcopy(available),
                    "terminal": {"kind": "incident"},
                }
            },
            "workforce_collective": {"response": copy.deepcopy(available)},
            "ai_owned_case": {"response": copy.deepcopy(available)},
        },
        "readiness": readiness,
        "all_product_providers_ready": True,
    }


def main() -> int:
    capture = bootstrap.extract_event_capture(event_payload())
    assert capture["played_character_id"] == 29037
    assert capture["domain_query_matrix"] == {
        "schema_version": 1,
        "b2_pip_owner_character_id": 32904,
        "incident_owner_character_id": 32904,
        "workforce_owner_character_id": 32904,
        "ai_owned_case_owner_character_id": 32904,
        "ai_owned_case_subject_character_id": 29037,
    }
    assert bootstrap.validate_event_close(
        close_payload(), event_instance_id=17
    )["postcondition_verified"] is True
    assert bootstrap.validate_paused_snapshot(
        paused_snapshot_payload(),
        expected_date_raw=53147016,
        expected_character_id=29037,
    )["map_ready"] is True

    missing_scope = event_payload()
    missing_scope["query"]["current_event_window_context"]["saved_scopes"].pop()
    try:
        bootstrap.extract_event_capture(missing_scope)
    except bootstrap.SeedBootstrapError as error:
        assert "lacks required saved scopes" in str(error)
    else:
        raise AssertionError("missing selector scope was accepted")

    duplicate_scope = event_payload()
    duplicate_scope["query"]["current_event_window_context"][
        "saved_scopes"
    ].append(
        copy.deepcopy(
            duplicate_scope["query"]["current_event_window_context"][
                "saved_scopes"
            ][0]
        )
    )
    try:
        bootstrap.extract_event_capture(duplicate_scope)
    except bootstrap.SeedBootstrapError as error:
        assert "repeated required saved scopes" in str(error)
    else:
        raise AssertionError("ambiguous selector scope was accepted")

    fabricated_id = event_payload()
    fabricated_id["query"]["current_event_window_context"]["saved_scopes"][0][
        "scope"
    ]["typed_identity"]["character_id"] = True
    try:
        bootstrap.extract_event_capture(fabricated_id)
    except bootstrap.SeedBootstrapError as error:
        assert "positive CharacterID" in str(error)
    else:
        raise AssertionError("boolean/fabricated CharacterID was accepted")

    wrong_close = close_payload()
    wrong_close["option_number"] = 2
    try:
        bootstrap.validate_event_close(wrong_close, event_instance_id=17)
    except bootstrap.SeedBootstrapError as error:
        assert "sole option" in str(error)
    else:
        raise AssertionError("wrong event option was accepted")

    unpaused = paused_snapshot_payload()
    unpaused["snapshot"]["paused"] = False
    try:
        bootstrap.validate_paused_snapshot(
            unpaused,
            expected_date_raw=53147016,
            expected_character_id=29037,
        )
    except bootstrap.SeedBootstrapError as error:
        assert "paused snapshot" in str(error)
    else:
        raise AssertionError("unpaused seed snapshot was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        profile = root / "profile"
        save = profile / "save games" / "xar_checkpoint.ck3"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"SAV0101" + b"\0" * 12 + b"1.19.0.6" + b"\0" * 128)
        save_sha256 = hashlib.sha256(save.read_bytes()).hexdigest()
        event_path = root / "raw-event.json"
        snapshot_path = root / "raw-snapshot.json"
        close_path = root / "raw-close.json"
        checkpoint_path = root / "raw-checkpoint.json"
        write_json(event_path, event_payload())
        write_json(snapshot_path, paused_snapshot_payload())
        write_json(close_path, close_payload())
        write_json(
            checkpoint_path,
            {
                "step": "save-checkpoint",
                "accepted": True,
                "checkpoint": {
                    "status": "saved",
                    "path": str(save),
                    "size": save.stat().st_size,
                    "sha256": save_sha256,
                    "date_raw": 53147016,
                    "episode_character_id": 29037,
                    "strategy": "native-autosave-command-v1",
                },
            },
        )

        class FakeService:
            def __init__(self) -> None:
                self.closed = False
                self.calls: list[tuple[object, ...]] = []

            def snapshot(self) -> dict[str, object]:
                snapshot = copy.deepcopy(paused_snapshot_payload()["snapshot"])
                snapshot["revision"] = 82 if self.closed else 81
                snapshot["active_event"] = (
                    None
                    if self.closed
                    else {"instance_id": 17, "option_count": 1}
                )
                self.calls.append(("snapshot", snapshot["revision"]))
                return snapshot

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
                    (
                        "select",
                        option_number,
                        event_instance_id,
                        expected_revision,
                    )
                )
                self.closed = True
                return close_payload()

            def save_checkpoint(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                self.calls.append(("save", expected_revision))
                return bootstrap.read_json(checkpoint_path)

        capture_dir = root / "captured"
        fake_service = FakeService()
        captured = bootstrap.capture_mcp_evidence(fake_service, capture_dir)
        assert captured["result"] == "GREEN"
        assert captured["played_character_id"] == 29037
        assert fake_service.calls == [
            ("snapshot", 81),
            ("query", 17, 81),
            ("snapshot", 81),
            ("select", 1, 17, 81),
            ("snapshot", 82),
            ("save", 82),
        ]
        assert set(path.name for path in capture_dir.iterdir()) == {
            "event-context.json",
            "paused-snapshot.json",
            "event-close.json",
            "save-checkpoint.json",
        }

        output_dir = root / "materialized"
        result = bootstrap.materialize_candidate(
            event_context_path=Path(captured["event_context_path"]),
            paused_snapshot_path=Path(captured["paused_snapshot_path"]),
            event_close_path=Path(captured["event_close_path"]),
            checkpoint_response_path=Path(captured["checkpoint_response_path"]),
            profile=profile,
            output_dir=output_dir,
            base_contract_path=bootstrap.DEFAULT_BASE_CONTRACT,
            source_git_commit="a" * 40,
            product_tree_sha256="b" * 64,
            fixture_tree_sha256="c" * 64,
        )
        assert result["result"] == "GREEN"
        assert result["status"] == bootstrap.READY_STATUS
        assert result["ready"] is True
        assert result["blocker"] == ""
        assert result["provider_baseline_ready"] is False
        contract_path = Path(result["contract_path"])
        contract = bootstrap.read_json(contract_path)
        assert contract["ready"] is True
        assert contract["status"] == "ready"
        assert contract["blocker"] == ""
        assert contract["saved_state"]["played_character_id"] == 29037
        assert contract["saved_state"]["player_history_id"] == "han_6875"
        assert contract["domain_query_matrix"] == capture[
            "domain_query_matrix"
        ]
        assert contract["source"]["absolute_save"] == str(save.resolve())
        assert contract["source"]["sha256"] == save_sha256
        report = bootstrap.read_json(Path(result["report_path"]))
        scenario = report["cell"]["scenario_evidence"]
        assert scenario["ocr_used"] is False
        assert scenario["test_decision_used"] is False
        assert scenario["historical_subjects_manufactured_by_fixture"] is False
        assert scenario["phase2_seed_bootstrap_attestation"]["mcp_only"] is True
        for preserved in (
            "event-context.json",
            "paused-snapshot.json",
            "event-close.json",
            "save-checkpoint.json",
            "report.json",
            "evidence-index.json",
        ):
            assert (output_dir / preserved).is_file()

        provider_path = root / "provider-probes.json"
        write_json(provider_path, provider_probes_payload())
        ready_output = root / "materialized-ready"
        ready_result = bootstrap.materialize_candidate(
            event_context_path=Path(captured["event_context_path"]),
            paused_snapshot_path=Path(captured["paused_snapshot_path"]),
            event_close_path=Path(captured["event_close_path"]),
            checkpoint_response_path=Path(captured["checkpoint_response_path"]),
            provider_probes_path=provider_path,
            profile=profile,
            output_dir=ready_output,
            base_contract_path=bootstrap.DEFAULT_BASE_CONTRACT,
            source_git_commit="a" * 40,
            product_tree_sha256="b" * 64,
            fixture_tree_sha256="c" * 64,
        )
        assert ready_result["status"] == bootstrap.READY_STATUS
        assert ready_result["ready"] is True
        assert ready_result["blocker"] == ""
        assert ready_result["provider_baseline_ready"] is True
        ready_contract = bootstrap.read_json(Path(ready_result["contract_path"]))
        assert ready_contract["status"] == "ready"
        assert ready_contract["ready"] is True
        assert ready_contract["blocker"] == ""
        assert (ready_output / "provider-probes.json").is_file()
        ready_report = bootstrap.read_json(Path(ready_result["report_path"]))
        provider_attestation = ready_report["cell"]["scenario_evidence"][
            "phase2_product_provider_attestation"
        ]
        assert provider_attestation["all_product_providers_ready"] is True
        assert all(provider_attestation["readiness"].values())

        contradictory_providers = provider_probes_payload()
        contradictory_providers["readiness"]["workforce_collective_ready"] = False
        write_json(provider_path, contradictory_providers)
        try:
            bootstrap.validate_provider_probes(
                bootstrap.read_json(provider_path),
                expected_selectors=capture["domain_query_matrix"],
                expected_date_raw=53147016,
                expected_character_id=29037,
            )
        except bootstrap.SeedBootstrapError as error:
            assert "declared readiness differs" in str(error)
        else:
            raise AssertionError("contradictory provider readiness was accepted")

        contradictory_checkpoint = bootstrap.read_json(checkpoint_path)
        contradictory_checkpoint["checkpoint"]["date_raw"] += 1
        write_json(checkpoint_path, contradictory_checkpoint)
        try:
            bootstrap.validate_checkpoint(
                bootstrap.read_json(checkpoint_path),
                expected_date_raw=53147016,
                expected_character_id=29037,
            )
        except bootstrap.SeedBootstrapError as error:
            assert "size/hash/date" in str(error)
        else:
            raise AssertionError("contradictory checkpoint date was accepted")

    print("GREEN: typed phase-two selector/checkpoint materializer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
