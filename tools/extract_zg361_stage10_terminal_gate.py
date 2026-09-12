#!/usr/bin/env python3
"""Extract a Stage 10 P1 gate from a preserved contract-mismatch RED.

This tool does not reinterpret a product failure.  It only accepts the narrow
case where the live run already paused on the real ``zg361mg.120`` window and
the same native snapshot proves the bound F case is terminal.  The source RED
remains immutable and hash-bound in the resulting receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


EVENT_KEY = "zg361mg.120"
GAME_VERSION = "1.19.0.6"
HEX64 = re.compile(r"[0-9A-Fa-f]{64}\Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def checked_file(path: Path, expected_sha256: str, label: str) -> dict[str, str]:
    require(path.is_file(), f"{label} is not a file")
    require(HEX64.fullmatch(expected_sha256) is not None, f"{label} SHA-256 is invalid")
    actual = sha256(path)
    require(actual.lower() == expected_sha256.lower(), f"{label} SHA-256 mismatch")
    return {"path": str(path), "sha256": actual}


def character_id(scope: object) -> int | None:
    if not isinstance(scope, Mapping):
        return None
    typed = scope.get("typed_identity")
    if not isinstance(typed, Mapping):
        return None
    if typed.get("status") != "available" or typed.get("kind") != "character":
        return None
    value = typed.get("character_id")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def typed_value(container: object, key: str) -> object:
    if not isinstance(container, Mapping):
        return None
    value = container.get(key)
    if not isinstance(value, Mapping) or value.get("status") != "available":
        return None
    return value.get("value")


def saved_character(context: Mapping[str, Any], name: str) -> int | None:
    values = [
        character_id(item.get("scope"))
        for item in context.get("saved_scopes", [])
        if isinstance(item, Mapping) and item.get("name") == name
    ]
    return values[0] if len(values) == 1 else None


def extract_gate(
    source: Mapping[str, Any],
    *,
    source_record: Mapping[str, str],
    activation: Mapping[str, Any],
    activation_record: Mapping[str, str],
) -> dict[str, Any]:
    require(source.get("result") == "RED", "source is not a preserved RED")
    require(source.get("red_preserved") is True, "source RED is not marked preserved")
    require(source.get("video_lock_touched") is False, "source touched the video lock")
    evidence = source.get("evidence")
    snapshot = source.get("failure_snapshot")
    require(isinstance(evidence, Mapping), "source evidence is absent")
    require(isinstance(snapshot, Mapping), "failure snapshot is absent")
    require(
        evidence.get("kind") == "zg361_phase2_stage10_player_subject_action_cell",
        "unexpected source evidence kind",
    )
    require(evidence.get("result") == "RED", "inner evidence is not RED")
    require(
        evidence.get("failure_reason")
        == "ValueError: Stage 10 player-subject F case is not terminal",
        "source RED was not the superseded aggregate-readiness failure",
    )
    require(
        evidence.get("action_ack_is_business_postcondition") is False,
        "source contract treated ACK as a business postcondition",
    )
    manager = evidence.get("expected_player_manager_character_id")
    owner = evidence.get("expected_owner_character_id")
    require(
        isinstance(manager, int) and not isinstance(manager, bool) and manager > 0,
        "expected manager is invalid",
    )
    require(
        isinstance(owner, int) and not isinstance(owner, bool) and owner > 0 and owner != manager,
        "expected owner is invalid",
    )

    hashes = activation.get("expected_hashes")
    require(isinstance(hashes, Mapping), "activation expected hashes are absent")
    code_commit = hashes.get("code_commit")
    product_sha = hashes.get("product_tree_sha256")
    game_exe_sha = hashes.get("game_exe_sha256")
    require(isinstance(code_commit, str) and len(code_commit) == 40, "activation code commit is invalid")
    require(isinstance(product_sha, str) and HEX64.fullmatch(product_sha), "product tree SHA is invalid")
    require(isinstance(game_exe_sha, str) and HEX64.fullmatch(game_exe_sha), "game EXE SHA is invalid")

    source_binding = evidence.get("source_binding")
    progress = evidence.get("progress")
    require(isinstance(source_binding, Mapping), "source binding is absent")
    require(isinstance(progress, Mapping), "bounded progress is absent")
    pid = source_binding.get("bridge_pid")
    generation = source_binding.get("connection_generation")
    origin = progress.get("timeline_origin_date_raw")
    deadline = progress.get("absolute_end_date_raw")
    require(pid in source.get("ck3_pids", []), "source PID does not match RED inventory")
    require(isinstance(generation, int) and generation > 0, "connection generation is invalid")
    require(source_binding.get("player_character_id") == manager, "source player mismatch")
    require(
        isinstance(origin, int)
        and isinstance(deadline, int)
        and deadline == origin + 120 * 24,
        "120-day absolute bound is invalid",
    )
    require(progress.get("result") == "GREEN", "navigator did not reach its target")
    require(progress.get("readiness") == "paused-real-zg361mg.120", "target readiness is absent")
    require(progress.get("fixture_used") is False, "fixture was used")
    require(progress.get("console_used") is False, "console was used")
    require(progress.get("action_ack_used_as_state_evidence") is False, "ACK was used as state evidence")

    played = snapshot.get("played_character")
    active_event = snapshot.get("active_event")
    require(snapshot.get("paused") is True and snapshot.get("map_ready") is True, "terminal snapshot is not paused/map-ready")
    require(isinstance(played, Mapping) and played.get("character_id") == manager, "terminal player mismatch")
    require(isinstance(active_event, Mapping), "terminal active event is absent")
    instance_id = active_event.get("instance_id")
    terminal_date = snapshot.get("date_raw")
    require(isinstance(instance_id, int) and instance_id > 0, "terminal event instance is invalid")
    require(isinstance(terminal_date, int) and origin <= terminal_date <= deadline, "terminal date exceeded the bound")

    target_binding = progress.get("target_binding")
    require(isinstance(target_binding, Mapping), "target binding is absent")
    require(
        target_binding.get("snapshot_id") == snapshot.get("snapshot_id")
        and target_binding.get("revision") == snapshot.get("revision")
        and target_binding.get("native_revision") == snapshot.get("native_revision")
        and target_binding.get("event_instance_id") == instance_id
        and target_binding.get("date_raw") == terminal_date
        and target_binding.get("player_character_id") == manager
        and target_binding.get("connection_generation") == generation,
        "target binding does not match the failure snapshot",
    )

    history = snapshot.get("native_command_history")
    require(isinstance(history, list), "native command history is absent")
    event_matches: list[tuple[int, Mapping[str, Any], Mapping[str, Any]]] = []
    provider_matches: list[tuple[int, Mapping[str, Any], Mapping[str, Any]]] = []
    for position, item in enumerate(history):
        if not isinstance(item, Mapping) or item.get("ok") is not True:
            continue
        result = item.get("result")
        if not isinstance(result, Mapping) or result.get("accepted") is not True:
            continue
        context = result.get("current_event_window_context")
        if isinstance(context, Mapping) and context.get("event_definition_key") == EVENT_KEY:
            event_matches.append((position, result, context))
        provider = result.get("zhongguo_manager_governance_snapshot")
        if isinstance(provider, Mapping):
            provider_matches.append((position, result, provider))
    require(event_matches, "real zg361mg.120 query is absent")
    event_position, event_result, context = event_matches[-1]
    require(event_result.get("status") == "available", "event query is unavailable")
    require(
        event_result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
        and event_result.get("queried_revision") == snapshot.get("revision")
        and event_result.get("queried_native_revision") == snapshot.get("native_revision"),
        "event query is not from the terminal snapshot",
    )
    require(context.get("date_raw") == terminal_date, "event date mismatch")
    require(context.get("current_event_instance_id") == instance_id, "event instance mismatch")
    require(character_id(context.get("root_scope")) == manager, "event root is not the player manager")
    require(saved_character(context, "zg361_mg_f_ticket_owner") == owner, "event F-ticket owner mismatch")
    require(saved_character(context, "zg361_mg_f_ticket_subject") == manager, "event F-ticket subject mismatch")
    options = context.get("options")
    require(
        isinstance(options, list)
        and len(options) == 1
        and isinstance(options[0], Mapping)
        and options[0].get("native_option_index") == 0
        and options[0].get("shown") is True
        and options[0].get("enabled") is True,
        "target event option is not the expected enabled native option 0",
    )

    providers = [item for item in provider_matches if item[0] > event_position]
    require(providers, "same-snapshot terminal provider query is absent")
    provider_position, provider_result, provider = providers[-1]
    require(provider_result.get("status") == "available", "provider query is unavailable")
    require(
        provider_result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
        and provider_result.get("queried_revision") == snapshot.get("revision")
        and provider_result.get("queried_native_revision") == snapshot.get("native_revision")
        and provider_result.get("queried_connection_generation") == generation,
        "provider query is not from the target snapshot lineage",
    )
    readiness = provider.get("readiness")
    binding = provider.get("subject_binding")
    f_case = provider.get("f_case")
    require(provider.get("status") == "available" and provider.get("unavailable_reason") is None, "provider payload is unavailable")
    require(provider.get("date_raw") == terminal_date and provider.get("paused") is True, "provider frame mismatch")
    require(provider.get("player_character_id") == manager and provider.get("subject_character_id") == manager, "provider subject mismatch")
    require(provider.get("requested_owner_character_id") == owner, "provider requested owner mismatch")
    require(
        isinstance(readiness, Mapping)
        and readiness.get("subject_binding_ready") is True
        and readiness.get("case_identity_ready") is True
        and readiness.get("same_frame_ready") is True,
        "Stage 10-specific provider readiness is incomplete",
    )
    require(
        isinstance(binding, Mapping)
        and binding.get("kind") == "played_character"
        and typed_value(binding, "manager_character_id") == manager
        and typed_value(binding, "owner_character_id") == owner,
        "provider player-subject binding mismatch",
    )
    require(
        typed_value(f_case, "owner_character_id") == owner
        and typed_value(f_case, "subject_character_id") == manager
        and typed_value(f_case, "state") == 5
        and typed_value(f_case, "active") is False,
        "provider F case is not terminal",
    )
    provenance = provider.get("provenance")
    require(
        isinstance(provenance, Mapping)
        and provenance.get("game_version") == GAME_VERSION
        and str(provenance.get("executable_sha256", "")).lower() == game_exe_sha.lower(),
        "provider exact-build provenance mismatch",
    )
    require(
        all(
            not (
                isinstance(item, Mapping)
                and str(item.get("command", "")).startswith("select-event-option-")
            )
            for item in history[event_position + 1 :]
        ),
        "target event was acknowledged before extraction",
    )

    elapsed_days = (terminal_date - origin) // 24
    return {
        "schema_version": 1,
        "kind": "zg361_stage10_terminal_from_preserved_contract_red_v1",
        "result": "GREEN",
        "production_live": True,
        "event_definition_key": EVENT_KEY,
        "stage": 10,
        "provider_domain": "manager_governance",
        "terminal_state": "complete",
        "provider_observed": True,
        "terminal_postcondition_verified": True,
        "owner_character_id": owner,
        "subject_character_id": manager,
        "role_topology": "superior_owner_to_player_manager_subject",
        "source_trigger": "real_player_b1_publication",
        "action_ack_is_business_postcondition": False,
        "target_acknowledged": False,
        "elapsed_game_days": elapsed_days,
        "max_advance_days": 120,
        "terminal_binding": {
            "bridge_pid": pid,
            "connection_generation": generation,
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
            "date_raw": terminal_date,
            "event_instance_id": instance_id,
        },
        "provider_observation": {
            "f_case": {
                "owner_character_id": owner,
                "subject_character_id": manager,
                "cycle_serial": typed_value(f_case, "cycle_serial"),
                "case_serial": typed_value(f_case, "case_serial"),
                "state": 5,
                "active": False,
                "revision": typed_value(f_case, "revision"),
            },
            "specific_readiness": {
                key: readiness.get(key)
                for key in ("subject_binding_ready", "case_identity_ready", "same_frame_ready")
            },
            "aggregate_readiness": readiness.get("ready"),
            "game_version": GAME_VERSION,
            "executable_sha256": game_exe_sha.lower(),
            "event_history_index": event_position,
            "provider_history_index": provider_position,
        },
        "preserved_red": {
            **dict(source_record),
            "source_result": "RED",
            "failure_reason": evidence.get("failure_reason"),
            "resolution": "aggregate provider readiness exceeded the Stage 10 terminal contract",
            "product_red": False,
        },
        "activation": {**dict(activation_record), "code_commit": code_commit, "product_tree_sha256": product_sha.lower()},
        "video_lock_touched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_red", type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--activation", type=Path, required=True)
    parser.add_argument("--activation-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_path = args.source_red.resolve()
    activation_path = args.activation.resolve()
    output = args.output.resolve()
    try:
        source_record = checked_file(source_path, args.source_sha256, "source RED")
        activation_record = checked_file(activation_path, args.activation_sha256, "activation")
        gate = extract_gate(
            read_object(source_path),
            source_record=source_record,
            activation=read_object(activation_path),
            activation_record=activation_record,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result": "RED", "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(json.dumps({"result": "GREEN", "output": str(output), "sha256": sha256(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
