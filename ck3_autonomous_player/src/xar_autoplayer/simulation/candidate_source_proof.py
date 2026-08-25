"""Exact-build candidate-source sequence proof shared by bridge and evaluator."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


CANDIDATE_SOURCE_PROOF_POLICY = (
    "ccombat_side_commanders_then_knights_native_source_equivalence_v1"
)
_PROOF_KEYS = {
    "policy",
    "source_vector_equivalence",
    "sequence_sha256",
    "ordered_sources",
}
_ROW_KEYS = {
    "role",
    "source_army_id",
    "source_regiment_id",
    "character_id",
}


class CandidateSourceProofError(ValueError):
    """A proof does not match the frozen native sequence contract."""


def candidate_source_sequence_preimage(
    side_index: int,
    ordered_sources: list[dict[str, object]],
) -> bytes:
    """Rebuild the byte-exact C++ digest preimage in native key order."""

    index = _side_index(side_index, "side_index")
    rows = [
        _normalize_source_row(row, name=f"ordered_sources[{ordinal}]")
        for ordinal, row in enumerate(ordered_sources)
    ]
    canonical = {
        "policy": CANDIDATE_SOURCE_PROOF_POLICY,
        "side_index": index,
        "ordered_sources": [
            {
                "role": row["role"],
                "source_army_id": row["source_army_id"],
                "source_regiment_id": row["source_regiment_id"],
                "character_id": row["character_id"],
            }
            for row in rows
        ],
    }
    return json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def candidate_source_sequence_sha256(
    side_index: int,
    ordered_sources: list[dict[str, object]],
) -> str:
    return hashlib.sha256(
        candidate_source_sequence_preimage(side_index, ordered_sources)
    ).hexdigest().upper()


def normalize_candidate_source_proof(
    value: object,
    *,
    side_index: int,
) -> dict[str, object]:
    """Validate exact keys, native ordering rules, and canonical digest."""

    if not isinstance(value, Mapping) or set(value) != _PROOF_KEYS:
        raise CandidateSourceProofError("candidate source proof schema is malformed")
    if value.get("policy") != CANDIDATE_SOURCE_PROOF_POLICY:
        raise CandidateSourceProofError("candidate source proof policy drifted")
    if value.get("source_vector_equivalence") is not True:
        raise CandidateSourceProofError(
            "candidate source vector equivalence was not proven"
        )
    raw_sources = value.get("ordered_sources")
    if not isinstance(raw_sources, list):
        raise CandidateSourceProofError(
            "candidate source ordered_sources must be an array"
        )
    rows = [
        _normalize_source_row(row, name=f"ordered_sources[{ordinal}]")
        for ordinal, row in enumerate(raw_sources)
    ]
    reached_knights = False
    for row in rows:
        if row["role"] == "commander":
            if reached_knights:
                raise CandidateSourceProofError(
                    "candidate commander appeared after native knight rows"
                )
        else:
            reached_knights = True
    claimed = value.get("sequence_sha256")
    expected = candidate_source_sequence_sha256(side_index, rows)
    if claimed != expected:
        raise CandidateSourceProofError(
            "candidate source sequence SHA-256 mismatch"
        )
    return {
        "policy": CANDIDATE_SOURCE_PROOF_POLICY,
        "source_vector_equivalence": True,
        "sequence_sha256": expected,
        "ordered_sources": rows,
    }


def _normalize_source_row(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _ROW_KEYS:
        raise CandidateSourceProofError(f"{name} schema is malformed")
    role = value.get("role")
    if role not in {"commander", "knight"}:
        raise CandidateSourceProofError(f"{name}.role is malformed")
    army_id = _positive_int32(value.get("source_army_id"), f"{name}.source_army_id")
    character_id = _positive_int32(value.get("character_id"), f"{name}.character_id")
    regiment_value = value.get("source_regiment_id")
    if role == "commander":
        if regiment_value is not None:
            raise CandidateSourceProofError(
                f"{name} commander RegimentID must be null"
            )
        regiment_id = None
    else:
        regiment_id = _positive_int32(
            regiment_value, f"{name}.source_regiment_id"
        )
    return {
        "role": role,
        "source_army_id": army_id,
        "source_regiment_id": regiment_id,
        "character_id": character_id,
    }


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(1 << 31) <= value <= (1 << 31) - 1
    ):
        raise CandidateSourceProofError(f"{name} must be signed int32")
    return value


def _positive_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result <= 0:
        raise CandidateSourceProofError(f"{name} must be a positive full ID")
    return result


def _side_index(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result not in {0, 1}:
        raise CandidateSourceProofError(f"{name} must be side index 0 or 1")
    return result


__all__ = [
    "CANDIDATE_SOURCE_PROOF_POLICY",
    "CandidateSourceProofError",
    "candidate_source_sequence_preimage",
    "candidate_source_sequence_sha256",
    "normalize_candidate_source_proof",
]
