"""Session binding for the read-only Raiktor six-domain aggregate.

This contract composes fields that the Python bridge already publishes.  It
does not read CK3 memory and does not synthesize an identity.  A missing or
cross-frame field produces a typed unavailable result so an otherwise complete
six-domain payload cannot be promoted across a connection, episode, or CK3
process boundary.
"""

from __future__ import annotations

from xar_autoplayer.bridge.raiktor_surrender_six_domain_contract import (
    normalize_raiktor_surrender_six_domain,
)


BACKEND_ID = "ck3-1.19.0.6-raiktor-six-domain-session-binding-v1"

_SNAPSHOT_FIELDS = (
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "paused",
    "episode_run_id",
    "episode_character_id",
)
_RECEIPT_FIELDS = (
    "queried_snapshot_id",
    "queried_revision",
    "queried_native_revision",
    "queried_connection_generation",
    "episode_run_id",
)
_DIAGNOSTIC_FIELDS = ("connection_generation", "bridge_pid")
_BINDING_KEYS = {
    "snapshot_id",
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "connection_generation",
    "episode_run_id",
    "episode_character_id",
    "process_id",
    "war_id",
}


def bind_raiktor_surrender_aggregate_session(
    snapshot_value: object,
    query_receipt_value: object,
    aggregate_value: object,
) -> dict[str, object]:
    """Bind an aggregate to one existing paused query session.

    Boundary errors are data, not exceptions: all missing or mismatched source
    fields produce ``status=unavailable`` with a stable failure code.  The
    normalized binding is returned only when every source agrees.
    """

    observed, missing = _observed_binding(snapshot_value, query_receipt_value)
    if missing:
        return _unavailable(
            "missing_binding_fields",
            missing,
            observed_binding=observed,
        )

    invalid = _invalid_binding_fields(observed)
    if invalid:
        return _unavailable(
            "invalid_binding_fields",
            invalid,
            observed_binding=observed,
        )

    drift = _binding_drift_fields(observed)
    if drift:
        return _unavailable(
            "session_binding_mismatch",
            drift,
            observed_binding=observed,
        )

    aggregate_frame = _aggregate_frame(aggregate_value)
    if aggregate_frame is None:
        return _unavailable(
            "aggregate_frame_unavailable",
            ["aggregate.frame"],
            observed_binding=observed,
        )
    aggregate_drift = _aggregate_binding_drift(observed, aggregate_frame)
    if aggregate_drift:
        return _unavailable(
            "aggregate_frame_mismatch",
            aggregate_drift,
            observed_binding=observed,
        )

    try:
        aggregate = normalize_raiktor_surrender_six_domain(
            aggregate_value,
            expected_war_id=aggregate_frame["war_id"],
            expected_snapshot_revision=aggregate_frame["snapshot_revision"],
            expected_native_revision=aggregate_frame["native_revision"],
            expected_date_raw=aggregate_frame["date_raw"],
            expected_attacker_character_id=aggregate_frame[
                "primary_attacker_character_id"
            ],
            expected_defender_character_id=aggregate_frame[
                "primary_defender_character_id"
            ],
            expected_claimant_character_id=aggregate_frame[
                "claimant_character_id"
            ],
        )
    except (KeyError, TypeError, ValueError):
        return _unavailable(
            "aggregate_contract_unavailable",
            ["aggregate"],
            observed_binding=observed,
        )

    binding = {
        "snapshot_id": observed["snapshot.snapshot_id"],
        "snapshot_revision": observed["snapshot.revision"],
        "native_revision": observed["snapshot.native_revision"],
        "date_raw": observed["snapshot.date_raw"],
        "connection_generation": observed[
            "diagnostics.connection_generation"
        ],
        "episode_run_id": observed["snapshot.episode_run_id"],
        "episode_character_id": observed[
            "snapshot.episode_character_id"
        ],
        # The bridge hello PID is CK3's existing process identity.  Rename it
        # only at this contract boundary; never generate or discover a PID.
        "process_id": observed["diagnostics.bridge_pid"],
        "war_id": aggregate_frame["war_id"],
    }
    if set(binding) != _BINDING_KEYS:
        raise AssertionError("Raiktor session binding implementation drifted")
    return {
        "schema_version": 1,
        "backend_id": BACKEND_ID,
        "status": "available",
        "failure": None,
        "binding": binding,
        "aggregate": aggregate,
        "readiness": {
            "snapshot_binding_ready": True,
            "query_receipt_binding_ready": True,
            "same_frame_revision_ready": True,
            "episode_owner_ready": True,
            "process_binding_ready": True,
            "aggregate_session_binding_ready": True,
        },
    }


def normalize_raiktor_surrender_aggregate_session_binding(
    value: object,
    *,
    expected_snapshot_id: str,
    expected_snapshot_revision: int,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_connection_generation: int,
    expected_episode_run_id: str,
    expected_episode_character_id: int,
    expected_process_id: int,
    expected_war_id: int,
) -> dict[str, object]:
    """Strictly consume an available binding at the execution boundary."""

    if not isinstance(value, dict):
        raise ValueError("Raiktor aggregate session binding must be an object")
    if (
        value.get("schema_version") != 1
        or value.get("backend_id") != BACKEND_ID
        or value.get("status") != "available"
        or value.get("failure") is not None
        or not isinstance(value.get("aggregate"), dict)
    ):
        raise ValueError("Raiktor aggregate session binding is unavailable")
    binding = value.get("binding")
    if not isinstance(binding, dict) or set(binding) != _BINDING_KEYS:
        raise ValueError("Raiktor aggregate session binding schema drifted")
    expected = {
        "snapshot_id": _nonempty_string(
            expected_snapshot_id, "expected_snapshot_id"
        ),
        "snapshot_revision": _positive_int(
            expected_snapshot_revision, "expected_snapshot_revision"
        ),
        "native_revision": _positive_int(
            expected_native_revision, "expected_native_revision"
        ),
        "date_raw": _int(expected_date_raw, "expected_date_raw"),
        "connection_generation": _positive_int(
            expected_connection_generation,
            "expected_connection_generation",
        ),
        "episode_run_id": _nonempty_string(
            expected_episode_run_id, "expected_episode_run_id"
        ),
        "episode_character_id": _positive_int(
            expected_episode_character_id,
            "expected_episode_character_id",
        ),
        "process_id": _positive_int(expected_process_id, "expected_process_id"),
        "war_id": _positive_int(expected_war_id, "expected_war_id"),
    }
    if binding != expected:
        raise ValueError("Raiktor aggregate session binding disagrees")
    readiness = value.get("readiness")
    expected_readiness = {
        "snapshot_binding_ready": True,
        "query_receipt_binding_ready": True,
        "same_frame_revision_ready": True,
        "episode_owner_ready": True,
        "process_binding_ready": True,
        "aggregate_session_binding_ready": True,
    }
    if readiness != expected_readiness:
        raise ValueError("Raiktor aggregate session readiness overclaims")
    return dict(value)


def _observed_binding(
    snapshot_value: object, query_receipt_value: object
) -> tuple[dict[str, object], list[str]]:
    snapshot = snapshot_value if isinstance(snapshot_value, dict) else {}
    receipt = (
        query_receipt_value if isinstance(query_receipt_value, dict) else {}
    )
    diagnostics_value = snapshot.get("diagnostics")
    diagnostics = diagnostics_value if isinstance(diagnostics_value, dict) else {}
    observed = {
        **{f"snapshot.{name}": snapshot.get(name) for name in _SNAPSHOT_FIELDS},
        **{f"receipt.{name}": receipt.get(name) for name in _RECEIPT_FIELDS},
        **{
            f"diagnostics.{name}": diagnostics.get(name)
            for name in _DIAGNOSTIC_FIELDS
        },
    }
    missing = sorted(key for key, value in observed.items() if value is None)
    return observed, missing


def _invalid_binding_fields(observed: dict[str, object]) -> list[str]:
    invalid: list[str] = []
    for key in (
        "snapshot.snapshot_id",
        "snapshot.episode_run_id",
        "receipt.queried_snapshot_id",
        "receipt.episode_run_id",
    ):
        if not isinstance(observed[key], str) or not str(observed[key]).strip():
            invalid.append(key)
    for key in (
        "snapshot.revision",
        "snapshot.native_revision",
        "snapshot.episode_character_id",
        "receipt.queried_revision",
        "receipt.queried_native_revision",
        "receipt.queried_connection_generation",
        "diagnostics.connection_generation",
        "diagnostics.bridge_pid",
    ):
        value = observed[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            invalid.append(key)
    if (
        isinstance(observed["snapshot.date_raw"], bool)
        or not isinstance(observed["snapshot.date_raw"], int)
    ):
        invalid.append("snapshot.date_raw")
    if observed["snapshot.paused"] is not True:
        invalid.append("snapshot.paused")
    return sorted(invalid)


def _binding_drift_fields(observed: dict[str, object]) -> list[str]:
    pairs = (
        ("snapshot.snapshot_id", "receipt.queried_snapshot_id"),
        ("snapshot.revision", "receipt.queried_revision"),
        ("snapshot.native_revision", "receipt.queried_native_revision"),
        (
            "diagnostics.connection_generation",
            "receipt.queried_connection_generation",
        ),
        ("snapshot.episode_run_id", "receipt.episode_run_id"),
    )
    drift: list[str] = []
    for left, right in pairs:
        if observed[left] != observed[right]:
            drift.extend((left, right))
    return sorted(set(drift))


def _aggregate_frame(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    frame = value.get("frame")
    return dict(frame) if isinstance(frame, dict) else None


def _aggregate_binding_drift(
    observed: dict[str, object], frame: dict[str, object]
) -> list[str]:
    comparisons = (
        ("snapshot.revision", "snapshot_revision"),
        ("snapshot.native_revision", "native_revision"),
        ("snapshot.date_raw", "date_raw"),
        ("snapshot.paused", "paused"),
        ("snapshot.episode_character_id", "primary_attacker_character_id"),
    )
    return sorted(
        f"aggregate.frame.{aggregate_key}"
        for observed_key, aggregate_key in comparisons
        if observed[observed_key] != frame.get(aggregate_key)
    )


def _unavailable(
    code: str,
    fields: list[str],
    *,
    observed_binding: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "backend_id": BACKEND_ID,
        "status": "unavailable",
        "failure": {"code": code, "fields": sorted(set(fields))},
        "binding": None,
        "aggregate": None,
        "observed_binding": dict(observed_binding),
        "readiness": {
            "snapshot_binding_ready": False,
            "query_receipt_binding_ready": False,
            "same_frame_revision_ready": False,
            "episode_owner_ready": False,
            "process_binding_ready": False,
            "aggregate_session_binding_ready": False,
        },
    }


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _positive_int(value: object, name: str) -> int:
    result = _int(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result
