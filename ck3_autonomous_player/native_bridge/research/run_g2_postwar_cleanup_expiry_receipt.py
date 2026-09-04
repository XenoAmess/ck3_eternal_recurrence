#!/usr/bin/env python3
"""Bind one private postwar cleanup and persisted-expiry receipt.

The CLI is a no-launch fixture preflight.  The async collector is the runtime
seam: a caller invokes it only after one real surrender and a native cleanup
provider have produced their same-session inputs.  It then proves the old
WarID is absent, issues the retained defender query twice on one paused frame,
and consumes the committed retention ticket.  Nothing here enables public
surrender or promotes G2 readiness.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
for path in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import prepare_g2_postwar_retention_expiry_capture as retention  # noqa: E402
from xar_autoplayer.bridge.raiktor_actual_truce_expiry_contract import (  # noqa: E402
    QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
    QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX,
    normalize_raiktor_actual_truce_expiry_v1,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (  # noqa: E402
    normalize_raiktor_war_bound_regiment,
)
from xar_autoplayer.bridge.raiktor_war_bound_loss_cleanup_contract import (  # noqa: E402
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX,
    normalize_raiktor_war_bound_loss_cleanup_v1,
)


DEFAULT_MANIFEST = (
    RESEARCH_ROOT
    / "fixtures"
    / "g2_postwar_cleanup_expiry_adapter_v1_manifest.json"
)
EXPECTED_EXE_SHA256 = retention.EXPECTED_EXE_SHA256
ACTUAL_EXPIRY_SOURCE = "persisted_native_truce_row"
ADAPTER_SCHEMA = "xar.ck3.g2_postwar_cleanup_expiry_adapter.v1"
PREFLIGHT_SCHEMA = "xar.ck3.g2_postwar_cleanup_expiry_preflight.v1"


class AdapterError(RuntimeError):
    """A runtime binding, immutable input, or receipt was not proven."""


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AdapterError(f"{name} must be an object")
    return value


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdapterError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise AdapterError(f"{name} must be >= {minimum}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _load_object(path: Path, name: str) -> dict[str, object]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), name)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AdapterError(f"could not read {name}: {error}") from error


def _resolve(value: object, *, repo_root: Path) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _default_process_inventory() -> list[dict[str, object]]:
    completed = subprocess.run(
        ["tasklist.exe", "/FI", "IMAGENAME eq ck3.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise AdapterError("could not inventory CK3 processes")
    return [
        {"raw": line.strip()}
        for line in completed.stdout.splitlines()
        if line.strip().lower().startswith('"ck3.exe"')
    ]


def _snapshot_binding(snapshot: object, name: str) -> dict[str, object]:
    value = _object(snapshot, name)
    diagnostics = _object(value.get("diagnostics"), f"{name}.diagnostics")
    played = _object(value.get("played_character"), f"{name}.played_character")
    active_wars = value.get("active_wars")
    if not isinstance(active_wars, list) or any(
        not isinstance(row, dict) for row in active_wars
    ):
        raise AdapterError(f"{name}.active_wars must be an object list")
    run_id = value.get("episode_run_id")
    snapshot_id = value.get("snapshot_id")
    if not isinstance(run_id, str) or not run_id:
        raise AdapterError(f"{name}.episode_run_id must be nonempty")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise AdapterError(f"{name}.snapshot_id must be nonempty")
    return {
        "snapshot_id": snapshot_id,
        "revision": _integer(value.get("revision"), f"{name}.revision", minimum=0),
        "native_revision": _integer(
            value.get("native_revision"), f"{name}.native_revision", minimum=1
        ),
        "date_raw": _integer(value.get("date_raw"), f"{name}.date_raw"),
        "paused": value.get("paused") is True,
        "episode_run_id": run_id,
        "connection_generation": _integer(
            diagnostics.get("connection_generation"),
            f"{name}.connection_generation",
            minimum=1,
        ),
        "ck3_pid": _integer(
            diagnostics.get("bridge_pid"), f"{name}.bridge_pid", minimum=1
        ),
        "character_id": _integer(
            played.get("character_id"), f"{name}.character_id", minimum=1
        ),
        "active_wars": copy.deepcopy(active_wars),
    }


def _same_session(left: dict[str, object], right: dict[str, object]) -> bool:
    return all(
        left.get(key) == right.get(key)
        for key in (
            "ck3_pid",
            "connection_generation",
            "episode_run_id",
            "character_id",
        )
    )


def _same_paused_frame(left: dict[str, object], right: dict[str, object]) -> bool:
    return bool(
        left.get("paused") is True
        and right.get("paused") is True
        and _same_session(left, right)
        and all(
            left.get(key) == right.get(key)
            for key in ("snapshot_id", "revision", "native_revision", "date_raw")
        )
    )


def _war_row(binding: dict[str, object], war_id: int) -> dict[str, object] | None:
    matches = [
        row
        for row in binding["active_wars"]
        if isinstance(row, dict) and row.get("war_id") == war_id
    ]
    if len(matches) > 1:
        raise AdapterError("snapshot contains duplicate full-generation WarID")
    return matches[0] if matches else None


def _normalize_pre(
    ticket: dict[str, object], pre: object
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    value = _object(pre, "pre")
    binding = _snapshot_binding(value.get("snapshot"), "pre.snapshot")
    observation = value.get("war_bound_observation")
    try:
        normalized = normalize_raiktor_war_bound_regiment(
            observation,
            expected_war_id=_integer(ticket["war_id"], "ticket.war_id"),
            expected_attacker_character_id=_integer(
                ticket["character_id"], "ticket.character_id"
            ),
            expected_defender_character_id=_integer(
                ticket["opponent_character_id"], "ticket.opponent_character_id"
            ),
            expected_snapshot_revision=_integer(
                binding["revision"], "pre revision", minimum=0
            ),
            expected_native_revision=_integer(
                binding["native_revision"], "pre native_revision", minimum=1
            ),
            expected_date_raw=_integer(binding["date_raw"], "pre date_raw"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise AdapterError(f"pre war-bound observation rejected: {error}") from error
    generations = retention._generation_vector(normalized)
    soldiers = _object(normalized.get("soldiers"), "pre soldiers")
    active_war = _war_row(binding, _integer(ticket["war_id"], "ticket.war_id"))
    checks = {
        "paused": binding["paused"] is True,
        "character": binding["character_id"] == ticket["character_id"],
        "date": binding["date_raw"] == ticket["date_raw"],
        "active_war": isinstance(active_war, dict),
        "defender": isinstance(active_war, dict)
        and active_war.get("primary_opponent_character_id")
        == ticket["opponent_character_id"],
        "second_terms_query": value.get("terms_query_sequence") == 2,
        "receipt_sequence": value.get("receipt_sequence") == 2,
        "soldiers": soldiers.get("observed_current_soldiers")
        == ticket["pre_termination_soldiers"],
        "generation_vector": generations == ticket["frozen_generations"],
        "generation_hash": _sha256_json(generations)
        == ticket["frozen_generation_sha256"],
        "no_pre_cleanup": _object(normalized.get("cleanup"), "pre cleanup").get(
            "observable"
        )
        is False,
    }
    if not all(checks.values()):
        raise AdapterError(f"pre retention binding failed: {checks}")
    return binding, normalized, generations


def _normalize_cleanup(
    ticket: dict[str, object],
    pre_binding: dict[str, object],
    cleanup: object,
    post_binding: dict[str, object],
) -> dict[str, object]:
    try:
        normalized = normalize_raiktor_war_bound_regiment(
            cleanup,
            expected_war_id=_integer(ticket["war_id"], "ticket.war_id"),
            expected_attacker_character_id=_integer(
                ticket["character_id"], "ticket.character_id"
            ),
            expected_defender_character_id=_integer(
                ticket["opponent_character_id"], "ticket.opponent_character_id"
            ),
            expected_snapshot_revision=_integer(
                pre_binding["revision"], "pre revision", minimum=0
            ),
            expected_native_revision=_integer(
                pre_binding["native_revision"], "pre native_revision", minimum=1
            ),
            expected_date_raw=_integer(pre_binding["date_raw"], "pre date_raw"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise AdapterError(f"postwar cleanup observation rejected: {error}") from error
    frame = _object(normalized.get("postwar_frame"), "cleanup postwar_frame")
    vector = retention._generation_vector(normalized)
    checks = {
        "post_frame": frame
        == {
            "snapshot_revision": post_binding["revision"],
            "native_revision": post_binding["native_revision"],
            "date_raw": post_binding["date_raw"],
            "paused": True,
            "frozen_war_id": ticket["war_id"],
            "frozen_war_absent_from_active_wars": True,
        },
        "destroyed": _object(normalized.get("cleanup"), "cleanup").get("status")
        == "destroyed",
        "vector": vector == ticket["frozen_generations"],
        "vector_hash": _sha256_json(vector)
        == ticket["frozen_generation_sha256"],
        "all_persistent_destroyed": all(
            isinstance(row, dict)
            and row.get("postwar_persistent_state") == "destroyed"
            for row in normalized.get("regiments", [])
        ),
    }
    if not all(checks.values()):
        raise AdapterError(f"postwar cleanup binding failed: {checks}")
    return normalized


def _normalize_expiry_read(
    value: object, *, expected_step: str, expected_native_revision: int
) -> tuple[dict[str, object], int]:
    result = _object(value, "actual expiry read")
    wire_keys = {
        "step",
        "accepted",
        "query_sequence",
        "snapshot_revision",
        "raiktor_actual_truce_expiry",
        "backend_id",
    }
    if not wire_keys <= set(result):
        raise AdapterError("actual expiry read lacks the native wire envelope")
    wire = {key: copy.deepcopy(result[key]) for key in wire_keys}
    try:
        normalized = normalize_raiktor_actual_truce_expiry_v1(
            wire,
            expected_step=expected_step,
            expected_snapshot_revision=expected_native_revision,
        )
    except ValueError as error:
        raise AdapterError(f"actual expiry read rejected: {error}") from error
    proof = result.get("actual_truce_expiry_proof")
    if proof is not None and proof != normalized:
        raise AdapterError("driver actual-expiry proof differs from native wire")
    sequence = _integer(result.get("query_sequence"), "expiry query_sequence", minimum=1)
    return normalized, sequence


def _normalize_cleanup_read(
    value: object,
    *,
    ticket: dict[str, object],
    pre_binding: dict[str, object],
    post_binding: dict[str, object],
) -> dict[str, object]:
    result = _object(value, "war-bound cleanup read")
    step = QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX + str(
        ticket["war_id"]
    )
    try:
        normalized = normalize_raiktor_war_bound_loss_cleanup_v1(
            result,
            expected_step=step,
            expected_war_id=_integer(ticket["war_id"], "ticket.war_id"),
            expected_attacker_character_id=_integer(
                ticket["character_id"], "ticket.character_id"
            ),
            expected_defender_character_id=_integer(
                ticket["opponent_character_id"], "ticket.opponent_character_id"
            ),
            expected_active_public_revision=_integer(
                pre_binding["revision"], "pre revision", minimum=1
            ),
            expected_active_native_revision=_integer(
                pre_binding["native_revision"], "pre native_revision", minimum=1
            ),
            expected_active_date_raw=_integer(
                pre_binding["date_raw"], "pre date_raw"
            ),
            expected_post_public_revision=_integer(
                post_binding["revision"], "post revision", minimum=1
            ),
            expected_post_native_revision=_integer(
                post_binding["native_revision"],
                "post native_revision",
                minimum=1,
            ),
            expected_post_date_raw=_integer(
                post_binding["date_raw"], "post date_raw"
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise AdapterError(
            f"native war-bound cleanup read rejected: {error}"
        ) from error
    return _object(normalized.get("observation"), "cleanup observation")


def build_postwar_receipt(
    *,
    ticket: dict[str, object],
    pre: object,
    termination_result: object,
    post_snapshots: object,
    cleanup_observation: object,
    expiry_reads: object,
    cleanup_read: object | None = None,
) -> dict[str, object]:
    """Build and validate one private action-bound receipt from observed inputs."""
    pre_binding, _pre_observation, generations = _normalize_pre(ticket, pre)
    termination = _object(termination_result, "termination_result")
    post_values = post_snapshots if isinstance(post_snapshots, list) else []
    if len(post_values) != 3:
        raise AdapterError("post_snapshots must contain before/between/after")
    post_bindings = [
        _snapshot_binding(value, f"post_snapshots[{index}]")
        for index, value in enumerate(post_values)
    ]
    post = post_bindings[0]
    war_id = _integer(ticket["war_id"], "ticket.war_id")
    post_checks = {
        "same_session_as_pre": _same_session(pre_binding, post),
        "same_paused_double_read_frame": all(
            _same_paused_frame(post, current) for current in post_bindings[1:]
        ),
        "successor_public_revision": post["revision"] > pre_binding["revision"],
        "successor_native_revision": post["native_revision"]
        > pre_binding["native_revision"],
        "nondecreasing_date": post["date_raw"] >= pre_binding["date_raw"],
        "old_war_absent": all(
            _war_row(current, war_id) is None for current in post_bindings
        ),
    }
    if not all(post_checks.values()):
        raise AdapterError(f"postwar snapshot binding failed: {post_checks}")

    expected_action = f"surrender-war-{war_id}"
    if not (
        termination.get("step") == expected_action
        and termination.get("accepted") is True
        and termination.get("status") in {"submitted", "applied"}
        and termination.get("backend_id") == "native-headless"
    ):
        raise AdapterError("termination result is not the one native surrender ACK")

    normalized_cleanup = _normalize_cleanup(
        ticket, pre_binding, cleanup_observation, post
    )
    read_values = expiry_reads if isinstance(expiry_reads, list) else []
    if len(read_values) != 2:
        raise AdapterError("expiry_reads must contain exactly two reads")
    expiry_step = (
        QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
        + str(ticket["opponent_character_id"])
    )
    first_expiry, first_sequence = _normalize_expiry_read(
        read_values[0],
        expected_step=expiry_step,
        expected_native_revision=_integer(
            post["native_revision"], "post native_revision", minimum=1
        ),
    )
    second_expiry, second_sequence = _normalize_expiry_read(
        read_values[1],
        expected_step=expiry_step,
        expected_native_revision=_integer(
            post["native_revision"], "post native_revision", minimum=1
        ),
    )
    expiry_checks = {
        "sequence_successor": second_sequence == first_sequence + 1,
        "stable_payload": first_expiry == second_expiry,
        "available": first_expiry.get("status") == "available"
        and first_expiry.get("readiness") is True,
        "owner": first_expiry.get("owner_character_id")
        == ticket["character_id"],
        "retained_defender": first_expiry.get("toward_character_id")
        == ticket["opponent_character_id"],
        "post_date": first_expiry.get("current_date_raw") == post["date_raw"],
    }
    if not all(expiry_checks.values()):
        raise AdapterError(f"persisted expiry double-read failed: {expiry_checks}")

    action_receipt_id = _sha256_json(
        {
            "ticket": ticket["retention_ticket_id"],
            "session": {
                key: pre_binding[key]
                for key in ("ck3_pid", "connection_generation", "episode_run_id")
            },
            "pre_snapshot_id": pre_binding["snapshot_id"],
            "step": expected_action,
            "post_snapshot_id": post["snapshot_id"],
        }
    )
    receipt = {
        "schema": retention.EXPECTED_RECEIPT_SCHEMA,
        "status": retention.EXPECTED_RECEIPT_STATUS,
        "retention_ticket_id": ticket["retention_ticket_id"],
        "exact_build": {"game_executable_sha256": EXPECTED_EXE_SHA256},
        "session_binding": {
            "ck3_pid": pre_binding["ck3_pid"],
            "connection_generation": pre_binding["connection_generation"],
            "episode_run_id": pre_binding["episode_run_id"],
            "character_id": ticket["character_id"],
            "war_id": war_id,
        },
        "pre": {
            "source_report_sha256": ticket["source_report_sha256"],
            "snapshot_id": pre_binding["snapshot_id"],
            "revision": pre_binding["revision"],
            "native_revision": pre_binding["native_revision"],
            "date_raw": pre_binding["date_raw"],
            "terms_query_sequence": 2,
            "receipt_sequence": 2,
            "ck3_pid": pre_binding["ck3_pid"],
            "connection_generation": pre_binding["connection_generation"],
            "episode_run_id": pre_binding["episode_run_id"],
            "pre_termination_soldiers": ticket["pre_termination_soldiers"],
            "frozen_generation_sha256": ticket["frozen_generation_sha256"],
            "frozen_generations": generations,
        },
        "termination": {
            "submitted": True,
            "accepted": True,
            "step": expected_action,
            "war_id": war_id,
            "receipt_sequence": 3,
            "receipt_id": action_receipt_id,
            "ck3_pid": pre_binding["ck3_pid"],
            "connection_generation": pre_binding["connection_generation"],
            "episode_run_id": pre_binding["episode_run_id"],
            "native_result": copy.deepcopy(termination),
        },
        "post": {
            "revision": post["revision"],
            "native_revision": post["native_revision"],
            "date_raw": post["date_raw"],
            "receipt_sequence": 4,
            "ck3_pid": post["ck3_pid"],
            "connection_generation": post["connection_generation"],
            "episode_run_id": post["episode_run_id"],
            "paused": True,
            "war_id": war_id,
            "old_full_generation_war_id_absent": True,
            "war_bound_cleanup": {
                "observable": True,
                "status": "destroyed",
                "frozen_generations": generations,
                "post_termination_soldiers": 0,
                "proven_boundary_soldiers_lost": ticket[
                    "pre_termination_soldiers"
                ],
                "native_observation": normalized_cleanup,
            },
            "truce_expiry": {
                "observable": True,
                "source": ACTUAL_EXPIRY_SOURCE,
                "formula_derived": False,
                "from_character_id": ticket["character_id"],
                "to_character_id": ticket["opponent_character_id"],
                "evaluated_days": ticket["evaluated_days"],
                "queried_at_date_raw": post["date_raw"],
                "expiry_date_raw": first_expiry["expiry_date_raw"],
                "query_step": expiry_step,
                "query_sequences": [first_sequence, second_sequence],
                "temporal_semantics": first_expiry["temporal_semantics"],
            },
        },
        "mutation_commands": [expected_action],
        "private_capture": {
            "adapter_schema": ADAPTER_SCHEMA,
            "expiry_capability": QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
            "cleanup_capability": (
                QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY
            ),
            "cleanup_read": copy.deepcopy(cleanup_read),
            "expiry_reads": copy.deepcopy(read_values),
            "post_snapshots": copy.deepcopy(post_values),
        },
        "boundaries": {
            "private_default_off": True,
            "source_specific_attribution_ready": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }
    validation = retention.validate_postwar_receipt(receipt, ticket)
    if validation.get("ok") is not True:
        raise AdapterError(f"retention ticket rejected receipt: {validation}")
    receipt["ticket_validation"] = validation
    return receipt


def _structured(result: Any, name: str) -> dict[str, object]:
    value = getattr(result, "structured_content", None)
    if not isinstance(value, dict):
        raise AdapterError(f"{name} returned no structured_content")
    if bool(getattr(result, "is_error", False)):
        raise AdapterError(f"{name} returned an MCP error")
    return copy.deepcopy(value)


async def collect_after_surrender(
    client: Any,
    *,
    ticket: dict[str, object],
    pre: object,
    termination_result: object,
    authorize_private_live: bool = False,
) -> dict[str, object]:
    """Run only the post-surrender query tail on an existing MCP session."""
    if authorize_private_live is not True:
        raise AdapterError("private live postwar collector is default-OFF")
    pre_binding, _pre_observation, _generations = _normalize_pre(ticket, pre)
    expiry_step = (
        QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
        + str(ticket["opponent_character_id"])
    )
    cleanup_step = (
        QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX
        + str(ticket["war_id"])
    )
    before_result = await client.call_tool("ck3_take_snapshot", {})
    before = _structured(before_result, "postwar snapshot before")
    before_binding = _snapshot_binding(before, "postwar snapshot before")
    if _war_row(before_binding, int(ticket["war_id"])) is not None:
        raise AdapterError("old full-generation WarID still exists before expiry query")
    revision = before_binding["revision"]
    cleanup_result = await client.call_tool(
        "ck3_execute_step",
        {"step": cleanup_step, "expected_revision": revision},
    )
    cleanup_wire = _structured(cleanup_result, "native war-bound cleanup query")
    cleanup_observation = _normalize_cleanup_read(
        cleanup_wire,
        ticket=ticket,
        pre_binding=pre_binding,
        post_binding=before_binding,
    )
    first_result = await client.call_tool(
        "ck3_execute_step", {"step": expiry_step, "expected_revision": revision}
    )
    first = _structured(first_result, "first actual-expiry query")
    between_result = await client.call_tool("ck3_take_snapshot", {})
    between = _structured(between_result, "postwar snapshot between")
    second_result = await client.call_tool(
        "ck3_execute_step", {"step": expiry_step, "expected_revision": revision}
    )
    second = _structured(second_result, "second actual-expiry query")
    after_result = await client.call_tool("ck3_take_snapshot", {})
    after = _structured(after_result, "postwar snapshot after")
    return build_postwar_receipt(
        ticket=ticket,
        pre=pre,
        termination_result=termination_result,
        post_snapshots=[before, between, after],
        cleanup_observation=cleanup_observation,
        expiry_reads=[first, second],
        cleanup_read=cleanup_wire,
    )


def _destroyed_cleanup_fixture(
    active: dict[str, object], post_snapshot: dict[str, object]
) -> dict[str, object]:
    """Create the explicitly synthetic destroyed branch for static tests only."""
    value = copy.deepcopy(active)
    value["postwar_frame"] = {
        "snapshot_revision": post_snapshot["revision"],
        "native_revision": post_snapshot["native_revision"],
        "date_raw": post_snapshot["date_raw"],
        "paused": True,
        "frozen_war_id": active["war_id"],
        "frozen_war_absent_from_active_wars": True,
    }
    value["cleanup"] = {"observable": True, "status": "destroyed"}
    value["readiness"]["postwar_cleanup_ready"] = True
    for regiment in value["regiments"]:
        regiment["postwar_persistent_state"] = "destroyed"
        for row in regiment["composition_rows"]:
            if row["current_army_regiment_id"] is None:
                row["current_army_regiment_state"] = "not_present"
                row["raised_carmy_state"] = "not_present"
                row["frozen_carmy_roster_evidence"] = "not_present"
            else:
                row["current_army_regiment_state"] = "destroyed"
                row["raised_carmy_state"] = "destroyed"
                row["frozen_carmy_roster_evidence"] = "frozen_army_destroyed"
    return value


def _fixture_receipt(
    fixture: dict[str, object], ticket: dict[str, object], *, repo_root: Path
) -> dict[str, object]:
    source_report = _load_object(
        _resolve(fixture["source_report"], repo_root=repo_root), "source report"
    )
    expected = _object(
        _load_object(
            _resolve(fixture["retention_manifest"], repo_root=repo_root),
            "retention manifest",
        ).get("pre_binding"),
        "pre_binding",
    )
    active, _ = retention._validate_source_report(source_report, expected)
    pre = {
        "snapshot": copy.deepcopy(fixture["pre_snapshot"]),
        "terms_query_sequence": 2,
        "receipt_sequence": 2,
        "war_bound_observation": active,
    }
    post_snapshots = copy.deepcopy(fixture["post_snapshots"])
    cleanup = _destroyed_cleanup_fixture(active, post_snapshots[0])
    return build_postwar_receipt(
        ticket=ticket,
        pre=pre,
        termination_result=fixture["termination_result"],
        post_snapshots=post_snapshots,
        cleanup_observation=cleanup,
        expiry_reads=fixture["expiry_reads"],
    )


def run_no_launch_preflight(
    manifest_path: Path,
    output_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    process_inventory: Callable[[], list[dict[str, object]]] = (
        _default_process_inventory
    ),
) -> dict[str, object]:
    before = process_inventory()
    if before:
        raise AdapterError("CK3 must be absent during adapter preflight")
    manifest = _load_object(manifest_path.resolve(), "adapter manifest")
    if (
        manifest.get("schema")
        != "xar.ck3.g2_postwar_cleanup_expiry_adapter_manifest.v1"
        or manifest.get("default_off") is not True
        or manifest.get("live_authorized") is not False
        or manifest.get("public_readiness_promoted") is not False
        or manifest.get("action_readiness_promoted") is not False
        or manifest.get("gen034_closed") is not False
    ):
        raise AdapterError("adapter manifest boundary is invalid")
    paths = _object(manifest.get("paths"), "paths")
    hashes = _object(manifest.get("sha256"), "sha256")
    checked: dict[str, Path] = {}
    for name in (
        "runner",
        "fixture",
        "retention_manifest",
        "retention_runner",
        "actual_expiry_contract",
        "actual_expiry_source_contract",
        "cleanup_contract",
        "cleanup_dispatch_source_contract",
        "candidate_dll",
        "candidate_native_test",
    ):
        path = _resolve(paths[name], repo_root=repo_root)
        expected_hash = str(hashes.get(name, "")).upper()
        if not path.is_file() or re.fullmatch(r"[0-9A-F]{64}", expected_hash) is None:
            raise AdapterError(f"{name} path/hash is invalid")
        actual_hash = _sha256_file(path)
        if actual_hash != expected_hash:
            raise AdapterError(f"{name} hash differs: {actual_hash} != {expected_hash}")
        checked[name] = path
    attempt = _resolve(paths["fresh_attempt"], repo_root=repo_root)
    if attempt.exists():
        raise AdapterError(f"fresh attempt path already exists: {attempt}")

    retention_manifest = _load_object(checked["retention_manifest"], "retention manifest")
    ticket = retention.build_retention_ticket(retention_manifest, repo_root=repo_root)
    fixture = _load_object(checked["fixture"], "adapter fixture")
    if fixture.get("synthetic") is not True or fixture.get("live") is not False:
        raise AdapterError("adapter fixture must remain explicit synthetic evidence")
    receipt = _fixture_receipt(fixture, ticket, repo_root=repo_root)
    source_contract = _load_object(
        checked["actual_expiry_source_contract"], "actual expiry source contract"
    )
    cleanup_source_contract = _load_object(
        checked["cleanup_dispatch_source_contract"],
        "cleanup dispatch source contract",
    )
    provider_checks = {
        "static_ready_live_pending": source_contract.get("status")
        == "static-ready_live-pending",
        "default_off": source_contract.get("default_enabled") is False,
        "double_read_required": _object(
            source_contract.get("green_contract"), "green_contract"
        ).get("requires_same_frame_double_read")
        is True,
        "persisted_future_required": _object(
            source_contract.get("green_contract"), "green_contract"
        ).get("requires_persisted_future_expiry")
        is True,
        "cleanup_dispatch_exact_build": cleanup_source_contract.get(
            "game_executable_sha256"
        )
        == EXPECTED_EXE_SHA256,
        "cleanup_dispatch_default_off": cleanup_source_contract.get(
            "default_enabled"
        )
        is False,
        "cleanup_dispatch_source_hashes_green": cleanup_source_contract.get(
            "source_hashes_green"
        )
        is True,
    }
    runtime_seam = _object(manifest.get("runtime_seam"), "runtime_seam")
    seam_checks = {
        "expiry_query_dispatch_present": runtime_seam.get(
            "actual_expiry_query_dispatch_present"
        )
        is True,
        "cleanup_dispatch_present": runtime_seam.get(
            "war_bound_cleanup_query_dispatch_present"
        )
        is True,
        "baseline_from_terms": runtime_seam.get(
            "baseline_frozen_from_same_connection_terms"
        )
        is True,
        "surrender_ack_gate": runtime_seam.get(
            "same_connection_surrender_ack_required"
        )
        is True,
        "cleanup_read_consumed_once": runtime_seam.get(
            "successful_cleanup_consumes_action_binding"
        )
        is True,
        "cleanup_input_required": runtime_seam.get(
            "same_lifecycle_native_cleanup_observation_required"
        )
        is True,
    }
    after = process_inventory()
    if after:
        raise AdapterError("CK3 appeared during adapter preflight")
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "status": "GREEN_STATIC_LIFECYCLE_READY_LIVE_NOT_RUN",
        "ok": all(provider_checks.values()) and all(seam_checks.values()),
        "ck3_started_or_attached": False,
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": _sha256_file(manifest_path.resolve()),
        "process_inventory_before": before,
        "process_inventory_after": after,
        "fresh_attempt_absent": not attempt.exists(),
        "retention_ticket_id": ticket["retention_ticket_id"],
        "fixture_receipt_sha256": _sha256_json(receipt),
        "fixture_ticket_validation": receipt["ticket_validation"],
        "actual_expiry_provider_checks": provider_checks,
        "runtime_seam_checks": seam_checks,
        "boundaries": {
            "fixture_only": True,
            "live_authorized": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
        "next_gate": (
            "run one exclusive action-bound CK3 capture with this exact "
            "candidate DLL; a native destroyed cleanup result plus two equal "
            "persisted-expiry reads are still required"
        ),
    }
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, output_path)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        report = run_no_launch_preflight(arguments.manifest, arguments.output)
    except (AdapterError, retention.PreflightError) as error:
        print(f"RED: {error}")
        return 2
    print(
        f"{report['status']} ticket={report['retention_ticket_id']} "
        "live_authorized=false"
    )
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
