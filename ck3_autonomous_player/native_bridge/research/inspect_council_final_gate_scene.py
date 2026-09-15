"""Classify a frozen private Council gate result without launching CK3.

This is scene triage, not paused-live gate acceptance or an action capability.
Only the sole CK3 operator may collect the result in a controlled run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ENVELOPE = "xar.ck3.council-application-main/v1"
GATES = "xar.ck3.private.council-final-gates/v1"
PUBLIC = "xar.ck3.council-composition-candidates/v1"
QUERY = "private-query-council-final-gates-v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def inspect(terminal: Path, expected_sha256: str) -> dict[str, object]:
    terminal = terminal.resolve()
    require(terminal.is_file(), "frozen terminal result is absent")
    actual_sha256 = sha256(terminal)
    require(actual_sha256 == expected_sha256.upper(),
            "frozen terminal result SHA-256 differs")
    message = json.loads(terminal.read_text(encoding="utf-8"))
    require(isinstance(message, dict) and message.get("type") == "command_result"
            and message.get("ok") is True, "private gate command was not GREEN")
    envelope = message.get("result")
    require(isinstance(envelope, dict) and envelope.get("schema") == ENVELOPE
            and envelope.get("step") == QUERY and envelope.get("status") == "available"
            and envelope.get("accepted") is True and envelope.get("private") is True
            and envelope.get("advertised") is False
            and type(envelope.get("native_helper_invocations_delta")) is int
            and envelope["native_helper_invocations_delta"] == 0,
            "private gate envelope is unavailable, advertised, or acted")
    gates = envelope.get("council_final_gates")
    require(isinstance(gates, dict) and gates.get("schema") == GATES
            and gates.get("status") == "available"
            and gates.get("unavailable_reason") == "none",
            "native final gates are unavailable")
    public = gates.get("council_composition_candidates")
    require(isinstance(public, dict) and public.get("schema") == PUBLIC
            and public.get("status") == "available"
            and public.get("candidate_collection_complete") is True,
            "same-frame public projection is incomplete")
    exact = public.get("exact_build")
    require(isinstance(exact, dict) and exact.get("game_version") == "1.19.0.6"
            and exact.get("executable_sha256") == EXE_SHA256,
            "exact CK3 build differs")
    snapshot = public.get("snapshot")
    require(isinstance(snapshot, dict) and snapshot.get("paused") is True
            and type(snapshot.get("native_revision")) is int
            and snapshot["native_revision"] > 0
            and snapshot.get("public_revision") == snapshot["native_revision"]
            and snapshot.get("snapshot_id") == f"native:{snapshot['native_revision']}"
            and envelope.get("snapshot_revision") == snapshot["public_revision"]
            and type(snapshot.get("date_raw")) is int,
            "native/public paused frame binding differs")
    position = public.get("position")
    require(isinstance(position, dict)
            and position.get("position_key") == "councillor_steward"
            and type(public.get("owner_character_id")) is int
            and public["owner_character_id"] > 0
            and type(position.get("vacant")) is bool,
            "owner/position is not a standard steward frame")
    candidates = public.get("candidates")
    rows = gates.get("rows")
    require(isinstance(candidates, list) and isinstance(rows, list)
            and type(gates.get("candidate_count")) is int
            and len(candidates) == len(rows) == gates["candidate_count"],
            "native gate vector is partial")
    by_id: dict[int, dict[str, object]] = {}
    fireability: set[bool] = set()
    for candidate, row in zip(candidates, rows):
        require(isinstance(candidate, dict) and isinstance(row, dict),
                "candidate/gate row is untyped")
        candidate_id = candidate.get("character_id")
        require(type(candidate_id) is int and candidate_id > 0
                and row.get("character_id") == candidate_id
                and type(row.get("native_collection_ordinal")) is int
                and row["native_collection_ordinal"] ==
                candidate.get("native_collection_ordinal")
                and candidate_id not in by_id,
                "candidate/gate identity or ordinal differs")
        for field in ("final_gate_available", "candidate_already_councillor",
                      "candidate_is_guest", "pending_character_interaction",
                      "incumbent_fireability_evaluated", "incumbent_can_be_fired"):
            require(type(row.get(field)) is bool,
                    f"{field} is unknown, not a native boolean")
        require(row["final_gate_available"] is True,
                "a candidate final gate is unavailable")
        if position["vacant"]:
            require(row["incumbent_fireability_evaluated"] is False,
                    "vacant position unexpectedly evaluated incumbent fireability")
        else:
            require(row["incumbent_fireability_evaluated"] is True,
                    "occupied incumbent fireability was not evaluated")
            fireability.add(row["incumbent_can_be_fired"])
        by_id[candidate_id] = row
    require(len(fireability) <= 1,
            "one incumbent has inconsistent native fireability across rows")
    require(position["vacant"] or
            (type(position.get("incumbent_character_id")) is int
             and position["incumbent_character_id"] > 0),
            "occupied position has no full incumbent identity")
    classified = {
        "already_councillor_positive_ids": [],
        "isolated_already_councillor_rejection_ids": [],
        "guest_positive_ids": [],
        "isolated_guest_rejection_ids": [],
        "candidate_pending_positive_ids": [],
        "isolated_candidate_pending_rejection_ids": [],
        "replacement_fireability_denial_candidate_ids": [],
        "isolated_replacement_fireability_denial_ids": [],
        "ordinary_assign_candidate_ids": [],
    }
    for candidate_id, row in by_id.items():
        fireable_or_vacant = position["vacant"] or row["incumbent_can_be_fired"]
        if row["candidate_already_councillor"]:
            classified["already_councillor_positive_ids"].append(candidate_id)
            if (not row["candidate_is_guest"]
                    and not row["pending_character_interaction"]
                    and fireable_or_vacant):
                classified["isolated_already_councillor_rejection_ids"].append(
                    candidate_id)
        if row["candidate_is_guest"]:
            classified["guest_positive_ids"].append(candidate_id)
            if (not row["candidate_already_councillor"]
                    and not row["pending_character_interaction"]
                    and fireable_or_vacant):
                classified["isolated_guest_rejection_ids"].append(candidate_id)
        if row["pending_character_interaction"]:
            classified["candidate_pending_positive_ids"].append(candidate_id)
            if (not row["candidate_already_councillor"]
                    and not row["candidate_is_guest"]
                    and fireable_or_vacant):
                classified["isolated_candidate_pending_rejection_ids"].append(
                    candidate_id)
        if not position["vacant"] and not row["incumbent_can_be_fired"]:
            classified["replacement_fireability_denial_candidate_ids"].append(
                candidate_id)
            if (not row["candidate_already_councillor"]
                    and not row["candidate_is_guest"]
                    and not row["pending_character_interaction"]):
                classified["isolated_replacement_fireability_denial_ids"].append(
                    candidate_id)
        if (not row["candidate_already_councillor"]
                and not row["candidate_is_guest"]
                and not row["pending_character_interaction"]
                and fireable_or_vacant):
            classified["ordinary_assign_candidate_ids"].append(candidate_id)
    for ids in classified.values():
        ids.sort()
    return {
        "status": "scene_classification_only",
        "terminal_sha256": actual_sha256,
        "owner_character_id": public["owner_character_id"],
        "position_key": position["position_key"],
        "incumbent_character_id": position.get("incumbent_character_id"),
        "vacant": position["vacant"],
        "snapshot": snapshot,
        "candidate_count": len(by_id),
        "native_helper_invocations_delta": 0,
        "public_registered_or_advertised": False,
        "typed_action_or_game_result_verified": False,
        **classified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-terminal", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    arguments = parser.parse_args()
    try:
        result = inspect(arguments.gate_terminal, arguments.expected_sha256)
    except (OSError, ValueError, json.JSONDecodeError) as failure:
        print(json.dumps({"status": "evidence_insufficient",
                          "reason": str(failure)}, sort_keys=True),
              file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
