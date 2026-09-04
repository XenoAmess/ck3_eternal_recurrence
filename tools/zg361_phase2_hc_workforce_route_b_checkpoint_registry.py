#!/usr/bin/env python3
"""Strict registry consumer for a real HC-workforce Route-B checkpoint.

The registry is an index over evidence that was already captured by CK3.  It
does not create a checkpoint, infer a case identity, or turn an option ACK into
a gameplay result.  The formal runner uses this module before launch and again
after installing the exact transition-fixture projection.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Final, Mapping

from zg361_phase2_hc_workforce_route_b_checkpoint import (
    RouteBCaseIdentity,
    WORKFORCE_REQUIRED_FACTS,
)


ROUTE_B_CHECKPOINT_REGISTRY_KIND: Final = (
    "zg361_hc_workforce_route_b_checkpoint_registry"
)
ROUTE_B_CHECKPOINT_REGISTRY_SCHEMA_VERSION: Final = 1
_CAPTURE_KIND: Final = "zg361_hc_workforce_route_b_pre_action_checkpoint"
_POSTCONDITION_KIND: Final = "zg361_hc_workforce_route_b_postconditions"
_EVENT_DEFINITION_KEY: Final = "zg361we.360"
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")


class RouteBCheckpointRegistryError(RuntimeError):
    """A fail-closed registry error with a stable reason code."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"HC-workforce Route-B registry RED [{reason_code}]")


@dataclass(frozen=True, slots=True)
class RegisteredRouteBCheckpoint:
    seed_lineage_id: str
    checkpoint_path: Path
    checkpoint_bytes: int
    checkpoint_sha256: str
    date_raw: int
    owner_character_id: int
    subject_character_id: int
    case_identity: RouteBCaseIdentity
    projection_binding: Mapping[str, object]
    checkpoint_capture: Mapping[str, object]
    sealed_postconditions: Mapping[str, object]


def _positive(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 1 <= value <= 2**31 - 1
    )


def _integer(value: object, *, minimum: int = 0) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= 2**63 - 1
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _projection(value: object) -> dict[str, object]:
    projection = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    valid = (
        projection.get("schema_version") == 1
        and projection.get("kind")
        == "zg361_current_cumulative_product_projection"
        and isinstance(projection.get("source_git_commit"), str)
        and _GIT_SHA_RE.fullmatch(
            str(projection.get("source_git_commit", "")).lower()
        )
        is not None
        and isinstance(projection.get("product_tree_sha256"), str)
        and _SHA256_RE.fullmatch(
            str(projection.get("product_tree_sha256", "")).lower()
        )
        is not None
        and isinstance(
            projection.get("transition_fixture_tree_sha256"), str
        )
        and _SHA256_RE.fullmatch(
            str(
                projection.get("transition_fixture_tree_sha256", "")
            ).lower()
        )
        is not None
        and projection.get("transition_fixture_enabled_mod")
        == "mod/zga_phase2_workforce_action_fixture.mod"
        and projection.get("fixture_acceptance_only") is True
    )
    if not valid:
        raise RouteBCheckpointRegistryError(
            "projection_binding_invalid", {"projection_binding": projection}
        )
    return projection


def _case_identity(value: object) -> RouteBCaseIdentity:
    case = dict(value) if isinstance(value, Mapping) else {}
    if not (
        _positive(case.get("owner_character_id"))
        and _positive(case.get("subject_character_id"))
        and case.get("owner_character_id") != case.get("subject_character_id")
        and _integer(case.get("cycle_serial"), minimum=1)
        and _integer(case.get("case_serial"), minimum=1)
    ):
        raise RouteBCheckpointRegistryError(
            "sealed_case_identity_invalid", {"case_identity": case}
        )
    return RouteBCaseIdentity(
        owner_character_id=int(case["owner_character_id"]),
        subject_character_id=int(case["subject_character_id"]),
        cycle_serial=int(case["cycle_serial"]),
        case_serial=int(case["case_serial"]),
    )


def _parse_registry(
    registry: Mapping[str, object] | None,
) -> RegisteredRouteBCheckpoint:
    if registry is None:
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_registry_missing",
            {
                "required_registry_kind": ROUTE_B_CHECKPOINT_REGISTRY_KIND,
                "checkpoint_found": False,
            },
        )
    value = copy.deepcopy(dict(registry))
    capture = value.get("checkpoint_capture")
    capture = copy.deepcopy(dict(capture)) if isinstance(capture, Mapping) else {}
    sealed = value.get("sealed_postconditions")
    sealed = copy.deepcopy(dict(sealed)) if isinstance(sealed, Mapping) else {}
    if not (
        value.get("schema_version")
        == ROUTE_B_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        and value.get("registry_kind") == ROUTE_B_CHECKPOINT_REGISTRY_KIND
        and value.get("result") == "GREEN"
        and value.get("evidence_class") == "real_ck3"
        and value.get("fixture_used") is True
        and value.get("console_used") is False
        and value.get("action_ack_is_business_postcondition") is False
        and isinstance(value.get("seed_lineage_id"), str)
        and bool(value.get("seed_lineage_id"))
    ):
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_registry_header_invalid",
            {
                "registry_kind": value.get("registry_kind"),
                "evidence_class": value.get("evidence_class"),
                "fixture_used": value.get("fixture_used"),
                "console_used": value.get("console_used"),
            },
        )

    projection = _projection(capture.get("projection_binding"))
    owner = capture.get("owner_character_id")
    subject = capture.get("subject_character_id")
    binding = capture.get("event_binding")
    binding = dict(binding) if isinstance(binding, Mapping) else {}
    context = capture.get("event_context")
    context = dict(context) if isinstance(context, Mapping) else {}
    checkpoint = capture.get("checkpoint")
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    save_receipt = capture.get("native_save_receipt")
    save_receipt = dict(save_receipt) if isinstance(save_receipt, Mapping) else {}
    native_checkpoint = save_receipt.get("checkpoint")
    native_checkpoint = (
        dict(native_checkpoint) if isinstance(native_checkpoint, Mapping) else {}
    )
    transition = capture.get("subject_to_owner_transition")
    transition = dict(transition) if isinstance(transition, Mapping) else {}
    transition_post = transition.get("native_played_character_postcondition")
    transition_post = (
        dict(transition_post) if isinstance(transition_post, Mapping) else {}
    )
    raw_path = checkpoint.get("path")
    path = Path(str(raw_path)).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = checkpoint.get("bytes")
    expected_sha = str(checkpoint.get("sha256", "")).lower()
    date_raw = binding.get("date_raw")
    capture_valid = (
        capture.get("schema_version") == 1
        and capture.get("kind") == _CAPTURE_KIND
        and capture.get("result") == "GREEN"
        and capture.get("route") == "B"
        and capture.get("option_number") == 2
        and capture.get("native_option_index") == 1
        and capture.get("gameplay_action_executed") is False
        and capture.get("business_postcondition_claimed") is False
        and _positive(owner)
        and _positive(subject)
        and owner != subject
        and binding.get("player_character_id") == owner
        and _integer(binding.get("revision"))
        and _integer(binding.get("native_revision"), minimum=1)
        and _integer(date_raw)
        and _positive(binding.get("event_instance_id"))
        and context.get("event_definition_key") == _EVENT_DEFINITION_KEY
        and context.get("current_event_instance_id")
        == binding.get("event_instance_id")
        and transition.get("result") == "GREEN"
        and transition.get("owner_character_id") == owner
        and transition.get("subject_character_id") == subject
        and transition.get("expected_player_before") == subject
        and transition.get("expected_player_after") == owner
        and transition.get("ack_used_as_identity_postcondition") is False
        and transition_post.get("played_character_id") == owner
        and transition_post.get("date_raw") == date_raw
        and isinstance(raw_path, str)
        and path.is_absolute()
        and path.is_file()
        and _integer(expected_bytes, minimum=1)
        and path.stat().st_size == expected_bytes
        and _SHA256_RE.fullmatch(expected_sha) is not None
        and _sha256(path) == expected_sha
        and checkpoint.get("date_raw") == date_raw
        and checkpoint.get("owner_character_id") == owner
        and checkpoint.get("subject_character_id") == subject
        and checkpoint.get("event_instance_id")
        == binding.get("event_instance_id")
        and checkpoint.get("product_tree_sha256")
        == projection.get("product_tree_sha256")
        and checkpoint.get("transition_fixture_tree_sha256")
        == projection.get("transition_fixture_tree_sha256")
        and save_receipt.get("accepted") is True
        and native_checkpoint.get("status") == "saved"
        and native_checkpoint.get("size") == expected_bytes
        and str(native_checkpoint.get("sha256", "")).lower() == expected_sha
        and native_checkpoint.get("date_raw") == date_raw
        and native_checkpoint.get("episode_character_id") == owner
    )
    if not capture_valid:
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_capture_invalid",
            {
                "checkpoint_path": str(path),
                "checkpoint_exists": path.is_file(),
                "owner_character_id": owner,
                "subject_character_id": subject,
                "event_definition_key": context.get("event_definition_key"),
                "action_executed_before_freeze": capture.get(
                    "gameplay_action_executed"
                ),
            },
        )

    identity = _case_identity(sealed.get("case_identity"))
    facts = sealed.get("workforce_required_facts")
    action = sealed.get("owner_action")
    action = dict(action) if isinstance(action, Mapping) else {}
    action_binding = action.get("binding")
    action_binding = (
        dict(action_binding) if isinstance(action_binding, Mapping) else {}
    )
    workforce = sealed.get("workforce_provider")
    workforce = dict(workforce) if isinstance(workforce, Mapping) else {}
    workforce_projection = workforce.get("postcondition")
    workforce_projection = (
        dict(workforce_projection)
        if isinstance(workforce_projection, Mapping)
        else {}
    )
    sealed_valid = (
        sealed.get("schema_version") == 1
        and sealed.get("kind") == _POSTCONDITION_KIND
        and sealed.get("result") == "GREEN"
        and str(sealed.get("checkpoint_sha256", "")).lower() == expected_sha
        and sealed.get("action_ack_is_business_postcondition") is False
        and sealed.get("provider_seal_scope") == "m360_current_cycle_route_b"
        and sealed.get("m361_charter_required") is False
        and isinstance(facts, Mapping)
        and set(facts) == set(WORKFORCE_REQUIRED_FACTS)
        and all(facts.get(name) is True for name in WORKFORCE_REQUIRED_FACTS)
        and action.get("result") == "ACKED"
        and action.get("business_receipt_claimed") is False
        and action_binding.get("route") == "B"
        and action_binding.get("option_number") == 2
        and action_binding.get("owner_character_id") == owner
        and action_binding.get("subject_character_id") == subject
        and action_binding.get("date_raw") == date_raw
        and workforce.get("result") == "GREEN"
        and workforce.get("m361_charter_required") is False
        and workforce_projection.get("m361_charter_required") is False
        and workforce_projection.get("owner_character_id") == owner
        and workforce_projection.get("subject_character_id") == subject
        and workforce_projection.get("cycle_serial") == identity.cycle_serial
        and workforce_projection.get("case_serial") == identity.case_serial
        and identity.owner_character_id == owner
        and identity.subject_character_id == subject
        and sealed.get("case_identity", {}).get("source")
        == "workforce_provider_post_action"
        and str(
            sealed.get("case_identity", {}).get("checkpoint_sha256", "")
        ).lower()
        == expected_sha
    )
    if not sealed_valid:
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_postconditions_invalid",
            {
                "checkpoint_sha256": expected_sha,
                "action_result": action.get("result"),
                "action_business_receipt_claimed": action.get(
                    "business_receipt_claimed"
                ),
                "workforce_result": workforce.get("result"),
                "case_identity": (
                    {
                        "owner_character_id": identity.owner_character_id,
                        "subject_character_id": identity.subject_character_id,
                        "cycle_serial": identity.cycle_serial,
                        "case_serial": identity.case_serial,
                    }
                ),
            },
        )

    return RegisteredRouteBCheckpoint(
        seed_lineage_id=str(value["seed_lineage_id"]),
        checkpoint_path=path,
        checkpoint_bytes=int(expected_bytes),
        checkpoint_sha256=expected_sha,
        date_raw=int(date_raw),
        owner_character_id=int(owner),
        subject_character_id=int(subject),
        case_identity=identity,
        projection_binding=projection,
        checkpoint_capture=capture,
        sealed_postconditions=sealed,
    )


class RouteBCheckpointRegistryProvider:
    """Validate one already-sealed real checkpoint for formal replay."""

    def __init__(
        self,
        registry: Mapping[str, object] | None,
        *,
        expected_seed_lineage_id: str | None,
        expected_source_git_commit: str | None,
    ) -> None:
        self.registry = (
            copy.deepcopy(dict(registry))
            if isinstance(registry, Mapping)
            else None
        )
        self.expected_seed_lineage_id = expected_seed_lineage_id
        self.expected_source_git_commit = (
            expected_source_git_commit.lower()
            if isinstance(expected_source_git_commit, str)
            else None
        )
        self._entry: RegisteredRouteBCheckpoint | None = None

    def preflight(
        self,
        *,
        current_projection_binding: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        entry = _parse_registry(self.registry)
        source_commit = str(
            entry.projection_binding.get("source_git_commit", "")
        ).lower()
        checks = {
            "seed_lineage_matches": (
                isinstance(self.expected_seed_lineage_id, str)
                and bool(self.expected_seed_lineage_id)
                and entry.seed_lineage_id == self.expected_seed_lineage_id
            ),
            "source_git_commit_matches": (
                isinstance(self.expected_source_git_commit, str)
                and _GIT_SHA_RE.fullmatch(self.expected_source_git_commit)
                is not None
                and source_commit == self.expected_source_git_commit
            ),
            "current_projection_matches": True,
        }
        if current_projection_binding is not None:
            current = _projection(current_projection_binding)
            checks["current_projection_matches"] = current == dict(
                entry.projection_binding
            )
        failed = [name for name, passed in checks.items() if passed is not True]
        if failed:
            raise RouteBCheckpointRegistryError(
                "route_b_checkpoint_registry_lineage_mismatch",
                {
                    "failed_checks": failed,
                    "checks": checks,
                    "registered_seed_lineage_id": entry.seed_lineage_id,
                    "expected_seed_lineage_id": self.expected_seed_lineage_id,
                    "registered_source_git_commit": source_commit,
                    "expected_source_git_commit": self.expected_source_git_commit,
                },
            )
        self._entry = entry
        return {
            "schema_version": 1,
            "result": "GREEN",
            "registry_kind": ROUTE_B_CHECKPOINT_REGISTRY_KIND,
            "evidence_class": "real_ck3",
            "checkpoint_sha256": entry.checkpoint_sha256,
            "checkpoint_bytes": entry.checkpoint_bytes,
            "owner_character_id": entry.owner_character_id,
            "subject_character_id": entry.subject_character_id,
            "case_identity": {
                "owner_character_id": entry.case_identity.owner_character_id,
                "subject_character_id": entry.case_identity.subject_character_id,
                "cycle_serial": entry.case_identity.cycle_serial,
                "case_serial": entry.case_identity.case_serial,
            },
            "fixture_used": True,
            "console_used": False,
            "action_ack_is_business_postcondition": False,
            "checks": checks,
        }

    def checkpoint(
        self,
        *,
        current_projection_binding: Mapping[str, object] | None = None,
    ) -> RegisteredRouteBCheckpoint:
        self.preflight(current_projection_binding=current_projection_binding)
        assert self._entry is not None
        return self._entry


def write_route_b_checkpoint_registry(
    output_path: Path,
    *,
    seed_lineage_id: str,
    source_git_commit: str,
    checkpoint_capture: Mapping[str, object],
    sealed_postconditions: Mapping[str, object],
) -> dict[str, object]:
    """Validate and atomically publish one provider-sealed real checkpoint.

    This writer deliberately has no ACK-only or partial-capture mode.  The
    same strict consumer used by the formal replay validates the checkpoint
    bytes, event/owner/subject/date binding and the complete Workforce
    provider seal before a registry file can appear.
    """

    destination = Path(output_path).expanduser().resolve()
    if destination.exists():
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_registry_already_exists",
            {"registry_path": str(destination)},
        )
    capture = copy.deepcopy(dict(checkpoint_capture))
    sealed = copy.deepcopy(dict(sealed_postconditions))
    value: dict[str, object] = {
        "schema_version": ROUTE_B_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "registry_kind": ROUTE_B_CHECKPOINT_REGISTRY_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "fixture_used": True,
        "console_used": False,
        "action_ack_is_business_postcondition": False,
        "seed_lineage_id": seed_lineage_id,
        "checkpoint_capture": capture,
        "sealed_postconditions": sealed,
    }
    projection = capture.get("projection_binding")
    RouteBCheckpointRegistryProvider(
        value,
        expected_seed_lineage_id=seed_lineage_id,
        expected_source_git_commit=source_git_commit,
    ).preflight(current_projection_binding=(
        projection if isinstance(projection, Mapping) else None
    ))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    if temporary.exists():
        raise RouteBCheckpointRegistryError(
            "route_b_checkpoint_registry_temporary_exists",
            {"temporary_path": str(temporary)},
        )
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return value


__all__ = [
    "ROUTE_B_CHECKPOINT_REGISTRY_KIND",
    "ROUTE_B_CHECKPOINT_REGISTRY_SCHEMA_VERSION",
    "RegisteredRouteBCheckpoint",
    "RouteBCheckpointRegistryError",
    "RouteBCheckpointRegistryProvider",
    "write_route_b_checkpoint_registry",
]
