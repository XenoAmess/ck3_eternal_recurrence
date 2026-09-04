"""Pure contract for the read-only Raiktor attacker-defeat truce primitive."""

from __future__ import annotations

import re
from typing import Final


_KEYS = {
    "schema_version",
    "backend_id",
    "status",
    "failure",
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "owner_character_id",
    "toward_character_id",
    "evaluated_days",
    "pointer_shape_verified",
    "evaluator_double_read_stable",
    "same_frame_stable",
    "expiry_observable",
    "expiry_date_raw",
}

BACKEND_ID = "ck3-1.19.0.6-native-raiktor-surrender-truce-v1"
PASSIVE_POSTPROCESS_CONTRACT = (
    "g2-truce-native-callsite-observer-live-postprocess-v1"
)
PASSIVE_SOURCE_COMMIT = "36fafd811b29bba11758d1ebc3929be8cbd4c9d4"
PASSIVE_MANIFEST_SHA256 = (
    "469ACAC772AFBA730FD4C669ADE3CFB2728AC0F81B796C9BEF88B5C093B64FDD"
)
PASSIVE_SOURCE_ZIP_SHA256 = (
    "F3F3E81EFFE0D832A280A81AF96FC2FB267BE6D9A134AB3A0F35F3BA95841E17"
)
PASSIVE_CALL_RVAS = (0x2EDAF0F, 0x2EDB59E)

# Cross-project compatibility binding maintained with the open_kaishek G2
# profile.  The profile certifies only the production-live evaluated-days
# observation primitive; it does not promote expiry or any termination action.
OPEN_KAISHEK_G2_CAPABILITY_ID: Final = (
    "game.command.query-g2-truce-evaluated-days-v1"
)
OPEN_KAISHEK_G2_PROFILE_ID: Final = "ck3-1.19.0.6-g2-truce-evaluator-v1"
OPEN_KAISHEK_G2_PROFILE_COMMIT: Final = (
    "1394dca6976c79913da740367898c0fd35e102e7"
)


def normalize_raiktor_surrender_truce(
    value: object,
    *,
    expected_war_id: int,
    expected_snapshot_revision: int,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_attacker_character_id: int,
    expected_defender_character_id: int,
) -> dict[str, object]:
    """Validate one exact-build, paused, stable evaluator observation.

    Version 1 deliberately exposes evaluated days but no inferred expiry date.
    The caller must not convert ``date_raw + 24 * days`` into a persisted-truce
    claim until that engine semantic has its own production observation.
    """
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native Raiktor surrender truce has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("backend_id") != BACKEND_ID
        or value.get("status") != "available"
        or value.get("failure") is not None
    ):
        raise ValueError("native Raiktor surrender truce is unavailable")

    war_id = _positive_int32(value.get("war_id"), "war_id")
    snapshot_revision = _positive_uint64(
        value.get("snapshot_revision"), "snapshot_revision"
    )
    native_revision = _positive_uint64(
        value.get("native_revision"), "native_revision"
    )
    date_raw = _signed_int32(value.get("date_raw"), "date_raw")
    attacker = _positive_int32(
        value.get("owner_character_id"), "owner_character_id"
    )
    defender = _positive_int32(
        value.get("toward_character_id"), "toward_character_id"
    )
    _non_negative_int32(
        value.get("active_casus_belli_database_index"),
        "active_casus_belli_database_index",
    )
    days = _non_negative_int32(value.get("evaluated_days"), "evaluated_days")
    if (
        war_id != _positive_int32(expected_war_id, "expected_war_id")
        or snapshot_revision
        != _positive_uint64(
            expected_snapshot_revision, "expected_snapshot_revision"
        )
        or native_revision
        != _positive_uint64(expected_native_revision, "expected_native_revision")
        or date_raw != _signed_int32(expected_date_raw, "expected_date_raw")
        or attacker
        != _positive_int32(
            expected_attacker_character_id,
            "expected_attacker_character_id",
        )
        or defender
        != _positive_int32(
            expected_defender_character_id,
            "expected_defender_character_id",
        )
    ):
        raise ValueError("native Raiktor surrender truce binding disagrees")
    if attacker == defender:
        raise ValueError("Raiktor surrender truce direction collapsed")
    if value.get("active_casus_belli_key") != "raiktor_claim_cb":
        raise ValueError("Raiktor surrender truce CB is not exact")
    if (
        value.get("paused") is not True
        or value.get("pointer_shape_verified") is not True
        or value.get("evaluator_double_read_stable") is not True
        or value.get("same_frame_stable") is not True
    ):
        raise ValueError("Raiktor surrender truce stability gate failed")
    if value.get("expiry_observable") is not False:
        raise ValueError("Raiktor surrender truce v1 must not claim expiry")
    if value.get("expiry_date_raw") is not None:
        raise ValueError("Raiktor surrender truce v1 invented an expiry date")

    # Keep the validated value lossless for later composition into the shared
    # war-termination response.  ``days`` is intentionally validated above.
    del days
    return dict(value)


def project_raiktor_surrender_truce_from_passive_observer(
    value: object,
    *,
    expected_snapshot_id: str,
    expected_snapshot_revision: int,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_connection_generation: int,
    expected_episode_run_id: str,
    expected_process_id: int,
    expected_war_id: int,
    expected_casus_belli_database_index: int,
    expected_attacker_character_id: int,
    expected_defender_character_id: int,
) -> dict[str, object] | None:
    """Project one identity-bound passive GREEN into the existing truce v1.

    Any postprocessor or binding failure remains typed unavailable to the
    caller.  The passive return never invents persisted expiry or changes an
    action-readiness field.
    """

    try:
        if not isinstance(value, dict):
            return None
        input_evidence = value.get("input_evidence")
        proofs = value.get("proofs")
        observer = value.get("observer")
        evaluated = value.get("evaluated_days")
        session = value.get("session_identity")
        readiness = value.get("readiness")
        boundaries = value.get("boundaries")
        if not all(
            isinstance(item, dict)
            for item in (
                input_evidence,
                proofs,
                observer,
                evaluated,
                session,
                readiness,
                boundaries,
            )
        ):
            return None
        manifest_proof = proofs.get("manifest")
        runner_proof = proofs.get("runner_policy")
        session_proof = proofs.get("session_identity")
        rows = observer.get("final_callsites")
        if (
            value.get("contract") != PASSIVE_POSTPROCESS_CONTRACT
            or value.get("status") != "GREEN"
            or value.get("classification") != "two_site_return_observed"
            or not _sha256(input_evidence.get("runner_report_sha256"))
            or input_evidence.get("manifest_sha256")
            != PASSIVE_MANIFEST_SHA256
            or input_evidence.get("expected_manifest_sha256")
            != PASSIVE_MANIFEST_SHA256
            or input_evidence.get("source_commit") != PASSIVE_SOURCE_COMMIT
            or input_evidence.get("source_zip_sha256")
            != PASSIVE_SOURCE_ZIP_SHA256
            or not isinstance(manifest_proof, dict)
            or manifest_proof.get("ok") is not True
            or not isinstance(runner_proof, dict)
            or runner_proof.get("ok") is not True
            or not isinstance(session_proof, dict)
            or session_proof.get("ok") is not True
            or proofs.get("samples_bounded") is not True
            or proofs.get("sample_errors") != []
            or proofs.get("counter_regressions") != []
            or proofs.get("stable_two_final_samples") is not True
            or readiness.get("promoted") is not False
            or readiness.get("public_readiness_changed") is not False
            or boundaries.get("direct_evaluator_invoked_by_postprocessor")
            is not False
            or boundaries.get("context_effect_executed") is not False
            or boundaries.get("mutation_executed") is not False
            or not isinstance(rows, list)
            or len(rows) != 2
        ):
            return None

        days = evaluated.get("site_0")
        if (
            evaluated.get("observable") is not True
            or evaluated.get("source") != "native return EAX"
            or not _non_negative(days)
            or evaluated.get("site_1") != days
        ):
            return None
        for index, row in enumerate(rows):
            if (
                not isinstance(row, dict)
                or row.get("call_instruction_rva") != PASSIVE_CALL_RVAS[index]
                or not _positive(row.get("post_call_count"))
                or row.get("last_return_eax") != days
            ):
                return None

        expected_session = {
            "snapshot_id": expected_snapshot_id,
            "snapshot_revision": expected_snapshot_revision,
            "native_revision": expected_native_revision,
            "date_raw": expected_date_raw,
            "connection_generation": expected_connection_generation,
            "episode_run_id": expected_episode_run_id,
            "episode_character_id": expected_attacker_character_id,
            "process_id": expected_process_id,
        }
        if session != expected_session:
            return None

        projected = {
            "schema_version": 1,
            "backend_id": BACKEND_ID,
            "status": "available",
            "failure": None,
            "snapshot_revision": expected_snapshot_revision,
            "native_revision": expected_native_revision,
            "date_raw": expected_date_raw,
            "paused": True,
            "war_id": expected_war_id,
            "active_casus_belli_database_index": (
                expected_casus_belli_database_index
            ),
            "active_casus_belli_key": "raiktor_claim_cb",
            "owner_character_id": expected_attacker_character_id,
            "toward_character_id": expected_defender_character_id,
            "evaluated_days": days,
            "pointer_shape_verified": True,
            "evaluator_double_read_stable": True,
            "same_frame_stable": True,
            "expiry_observable": False,
            "expiry_date_raw": None,
        }
        return normalize_raiktor_surrender_truce(
            projected,
            expected_war_id=expected_war_id,
            expected_snapshot_revision=expected_snapshot_revision,
            expected_native_revision=expected_native_revision,
            expected_date_raw=expected_date_raw,
            expected_attacker_character_id=expected_attacker_character_id,
            expected_defender_character_id=expected_defender_character_id,
        )
    except (TypeError, ValueError):
        return None


def _positive_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value <= 0 or value > 2**31 - 1:
        raise ValueError(f"{label} is outside positive int32")
    return value


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _non_negative(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= 2**31 - 1
    )


def _sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9A-F]{64}", value) is not None
    )


def _non_negative_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < 0 or value > 2**31 - 1:
        raise ValueError(f"{label} is outside non-negative int32")
    return value


def _signed_int32(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < -(2**31) or value > 2**31 - 1:
        raise ValueError(f"{label} is outside int32")
    return value


def _positive_uint64(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value <= 0 or value > 2**64 - 1:
        raise ValueError(f"{label} is outside positive uint64")
    return value
