#!/usr/bin/env python3
"""Audit the current root/open_kaishek compatibility pin without CK3.

The verifier is deliberately source-level.  It checks the root's descriptive
G2 binding, default-OFF war-loss/actual-expiry metadata, the fixture-only
postwar cleanup/expiry adapter, projects-metrics schema delta, and
promotion-source fail-closed transports against the companion Java profiles.
When the external checkout is available, it also checks source files and
read-only Git refs.  It never starts or attaches to CK3 and never changes a
Paradox opcode allow-list.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = (
    PROJECT_ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_open_kaishek_compatibility_v1.json"
)
ROOT_BINDING_PATH = (
    PROJECT_ROOT
    / "ck3_autonomous_player"
    / "src"
    / "xar_autoplayer"
    / "bridge"
    / "raiktor_surrender_truce_contract.py"
)
_ROOT_CONSTANT_RE = re.compile(
    r"(?m)^\s*{name}\s*(?::\s*Final)?\s*=\s*\(?\s*\"([^\"]+)\""
)
_JAVA_PROFILE_ID_RE = re.compile(
    r"(?m)^\s*public\s+static\s+final\s+String\s+ID\s*=\s*\"([^\"]+)\""
)
_JAVA_CAPABILITY_RE = re.compile(
    r"new\s+CapabilityDescriptor\s*\(\s*"
    r"\"(?P<id>[^\"]+)\"\s*,\s*ID\s*,\s*"
    r"List\.of\((?P<fields>.*?)\)\s*,\s*"
    r"List\.of\((?P<invariants>.*?)\)\s*,\s*"
    r"(?P<read_only>true|false)\s*,\s*"
    r"(?P<deterministic>true|false)\s*,\s*"
    r"(?P<native_certified>true|false)\s*,\s*"
    r"(?P<runtime_certified>true|false)\s*\)\s*;",
    re.DOTALL,
)
_JAVA_BUILD_CONSTANT_RE = re.compile(
    r"(?m)^\s*public\s+static\s+final\s+String\s+{name}\s*=\s*"
    r"\(?\s*\"([^\"]+)\""
)
_JAVA_BOOLEAN_CONSTANT_RE = re.compile(
    r"(?m)^\s*public\s+static\s+final\s+boolean\s+{name}\s*=\s*"
    r"(true|false)\s*;"
)
_JAVA_INT_CONSTANT_RE = re.compile(
    r"(?m)^\s*public\s+static\s+final\s+int\s+{name}\s*=\s*"
    r"([0-9]+)\s*;"
)
_PROVIDER_STRING_CONSTANTS = {
    "root_provider_commit": "ROOT_PROVIDER_COMMIT",
    "root_production_candidate_commit": "ROOT_PRODUCTION_CANDIDATE_COMMIT",
    "root_source_contract_sha256": "ROOT_SOURCE_CONTRACT_SHA256",
    "root_production_manifest_sha256": "ROOT_PRODUCTION_MANIFEST_SHA256",
    "root_provider_source_sha256": "ROOT_PROVIDER_SOURCE_SHA256",
    "root_provider_header_sha256": "ROOT_PROVIDER_HEADER_SHA256",
    "production_live_report_sha256": "PRODUCTION_LIVE_REPORT_SHA256",
    "production_tree_sha256": "PRODUCTION_TREE_SHA256",
    "production_bridge_dll_sha256": "PRODUCTION_BRIDGE_DLL_SHA256",
    "production_bridge_injector_sha256": "PRODUCTION_BRIDGE_INJECTOR_SHA256",
}
_PROVIDER_BOOLEAN_CONSTANTS = {
    "public_schema_changed": "PUBLIC_SCHEMA_CHANGED",
    "private_leaf_reader_live_observed": "PRIVATE_LEAF_READER_LIVE_OBSERVED",
    "default_production_leaf_reader_installed": (
        "DEFAULT_PRODUCTION_LEAF_READER_INSTALLED"
    ),
    "default_production_binary_live_validated": (
        "DEFAULT_PRODUCTION_BINARY_LIVE_VALIDATED"
    ),
    "production_live_read_only_primitive": "PRODUCTION_LIVE_READ_ONLY_PRIMITIVE",
    "expiry_observable": "EXPIRY_OBSERVABLE",
    "termination_action_enabled": "TERMINATION_ACTION_ENABLED",
    "full_decision_ready": "FULL_DECISION_READY",
    "automatic_surrender_ready": "AUTOMATIC_SURRENDER_READY",
    "gen_034_closed": "GEN_034_CLOSED",
}
_WAR_LOSS_STRING_CONSTANTS = {
    "id": "ID",
    "root_integration_commit": "ROOT_INTEGRATION_COMMIT",
    "root_candidate_commit": "ROOT_CANDIDATE_COMMIT",
    "root_static_artifact_sha256": "ROOT_STATIC_ARTIFACT_SHA256",
    "root_source_contract_sha256": "ROOT_SOURCE_CONTRACT_SHA256",
    "root_header_sha256": "ROOT_HEADER_SHA256",
    "root_source_sha256": "ROOT_SOURCE_SHA256",
}
_WAR_LOSS_INT_CONSTANTS = {
    "frozen_pre_termination_soldiers": "FROZEN_PRE_TERMINATION_SOLDIERS",
    "destroyed_post_termination_soldiers": (
        "DESTROYED_POST_TERMINATION_SOLDIERS"
    ),
    "proven_boundary_soldiers_lost": "PROVEN_BOUNDARY_SOLDIERS_LOST",
}
_WAR_LOSS_BOOLEAN_CONSTANTS = {
    "default_enabled": "DEFAULT_ENABLED",
    "read_only": "READ_ONLY",
    "public_capability_added": "PUBLIC_CAPABILITY_ADDED",
    "public_wire_changed": "PUBLIC_WIRE_CHANGED",
    "source_specific_attribution_ready": "SOURCE_SPECIFIC_ATTRIBUTION_READY",
    "termination_action_bound": "TERMINATION_ACTION_BOUND",
    "surrender_causality_proven": "SURRENDER_CAUSALITY_PROVEN",
    "public_terms_ready": "PUBLIC_TERMS_READY",
    "automatic_surrender_ready": "AUTOMATIC_SURRENDER_READY",
    "production_live": "PRODUCTION_LIVE",
    "gen_034_resolved": "GEN_034_RESOLVED",
}
_PROJECTS_STRING_CONSTANTS = {
    "root_commit": "PROJECTS_METRICS_ROOT_COMMIT",
    "root_source_contract_sha256": "PROJECTS_METRICS_SOURCE_CONTRACT_SHA256",
    "root_abi_sha256": "PROJECTS_METRICS_ABI_SHA256",
    "root_schema_sha256": "PROJECTS_METRICS_SCHEMA_SHA256",
    "root_python_contract_sha256": (
        "PROJECTS_METRICS_PYTHON_CONTRACT_SHA256"
    ),
    "allowlist_id": "PROJECTS_METRICS_ALLOWLIST_ID",
}
_PROJECTS_BOOLEAN_CONSTANTS = {
    "checkpoint_state_required": "PROJECTS_METRICS_CHECKPOINT_STATE_REQUIRED",
    "default_candidate_enabled": "PROJECTS_METRICS_DEFAULT_CANDIDATE_ENABLED",
    "production_live": "PROJECTS_METRICS_PRODUCTION_LIVE",
}
_PROMOTION_STRING_CONSTANTS = {
    "profile_id": "ID",
    "query_capability_id": "QUERY_CAPABILITY_ID",
    "query_transport_capability_id": "QUERY_TRANSPORT_CAPABILITY_ID",
    "query_step_id": "QUERY_STEP_ID",
    "action_capability_id": "ACTION_CAPABILITY_ID",
    "action_transport_capability_id": "ACTION_TRANSPORT_CAPABILITY_ID",
    "action_step_id": "ACTION_STEP_ID",
    "allowlist_id": "ALLOWLIST_ID",
    "game_version": "GAME_VERSION",
    "executable_sha256": "EXECUTABLE_SHA256",
    "root_integration_commit": "ROOT_INTEGRATION_COMMIT",
    "root_source_contract_sha256": "ROOT_SOURCE_CONTRACT_SHA256",
    "root_abi_sha256": "ROOT_ABI_SHA256",
    "root_python_contract_sha256": "ROOT_PYTHON_CONTRACT_SHA256",
}
_PROMOTION_BOOLEAN_CONSTANTS = {
    "query_production_capability_advertised": (
        "QUERY_PRODUCTION_CAPABILITY_ADVERTISED"
    ),
    "action_production_capability_advertised": (
        "ACTION_PRODUCTION_CAPABILITY_ADVERTISED"
    ),
    "production_live_ready": "PRODUCTION_LIVE_READY",
    "action_ack_is_state_evidence": "ACTION_ACK_IS_STATE_EVIDENCE",
}
_ACTUAL_EXPIRY_STRING_CONSTANTS = {
    "id": "ID",
    "capability_id": "CAPABILITY_ID",
    "step_prefix": "STEP_PREFIX",
    "backend_id": "BACKEND_ID",
    "cmake_option": "CMAKE_OPTION",
    "game_version": "GAME_VERSION",
    "executable_sha256": "EXECUTABLE_SHA256",
    "root_integration_commit": "ROOT_INTEGRATION_COMMIT",
    "root_retention_commit": "ROOT_RETENTION_COMMIT",
    "root_source_contract_sha256": "ROOT_SOURCE_CONTRACT_SHA256",
    "root_abi_sha256": "ROOT_ABI_SHA256",
    "root_python_contract_sha256": "ROOT_PYTHON_CONTRACT_SHA256",
    "root_header_sha256": "ROOT_HEADER_SHA256",
    "root_source_sha256": "ROOT_SOURCE_SHA256",
    "retention_manifest_sha256": "RETENTION_MANIFEST_SHA256",
    "retention_runner_sha256": "RETENTION_RUNNER_SHA256",
    "retention_ticket_id": "RETENTION_TICKET_ID",
    "frozen_generation_sha256": "FROZEN_GENERATION_SHA256",
}
_ACTUAL_EXPIRY_INT_CONSTANTS = {
    "retained_pre_termination_soldiers": (
        "RETAINED_PRE_TERMINATION_SOLDIERS"
    ),
    "retained_evaluated_days": "RETAINED_EVALUATED_DAYS",
}
_ACTUAL_EXPIRY_BOOLEAN_CONSTANTS = {
    "default_enabled": "DEFAULT_ENABLED",
    "capability_advertised_by_default": "CAPABILITY_ADVERTISED_BY_DEFAULT",
    "read_only": "READ_ONLY",
    "ack_sufficient": "ACK_SUFFICIENT",
    "native_certified": "NATIVE_CERTIFIED",
    "runtime_certified": "RUNTIME_CERTIFIED",
    "production_live": "PRODUCTION_LIVE",
    "retention_live_authorized": "RETENTION_LIVE_AUTHORIZED",
    "termination_action_bound": "TERMINATION_ACTION_BOUND",
    "actual_expiry_observable": "ACTUAL_EXPIRY_OBSERVABLE",
    "decision_ready": "DECISION_READY",
    "automatic_surrender_ready": "AUTOMATIC_SURRENDER_READY",
    "gen_034_resolved": "GEN_034_RESOLVED",
}
_CLEANUP_ADAPTER_STRING_CONSTANTS = {
    "id": "ID",
    "manifest_schema": "MANIFEST_SCHEMA",
    "fixture_schema": "FIXTURE_SCHEMA",
    "status": "STATUS",
    "root_integration_commit": "ROOT_INTEGRATION_COMMIT",
    "root_source_commit": "ROOT_SOURCE_COMMIT",
    "root_candidate_source_commit": "ROOT_CANDIDATE_SOURCE_COMMIT",
    "query_step": "QUERY_STEP",
    "retention_ticket_id": "RETENTION_TICKET_ID",
    "root_runner_sha256": "ROOT_RUNNER_SHA256",
    "root_manifest_sha256": "ROOT_MANIFEST_SHA256",
    "root_fixture_sha256": "ROOT_FIXTURE_SHA256",
    "root_preflight_sha256": "ROOT_PREFLIGHT_SHA256",
    "root_synthetic_receipt_sha256": "ROOT_SYNTHETIC_RECEIPT_SHA256",
}
_CLEANUP_ADAPTER_INT_CONSTANTS = {
    "war_id": "WAR_ID",
    "player_character_id": "PLAYER_CHARACTER_ID",
    "primary_defender_character_id": "PRIMARY_DEFENDER_CHARACTER_ID",
    "pre_termination_soldiers": "PRE_TERMINATION_SOLDIERS",
    "post_termination_soldiers": "POST_TERMINATION_SOLDIERS",
    "proven_boundary_soldiers_lost": "PROVEN_BOUNDARY_SOLDIERS_LOST",
}
_CLEANUP_ADAPTER_BOOLEAN_CONSTANTS = {
    "metadata_only": "METADATA_ONLY",
    "default_enabled": "DEFAULT_ENABLED",
    "synthetic_fixture": "SYNTHETIC_FIXTURE",
    "fixture_is_live": "FIXTURE_IS_LIVE",
    "public_capability_added": "PUBLIC_CAPABILITY_ADDED",
    "actual_expiry_query_dispatch_present": (
        "ACTUAL_EXPIRY_QUERY_DISPATCH_PRESENT"
    ),
    "cleanup_candidate_library_present": "CLEANUP_CANDIDATE_LIBRARY_PRESENT",
    "cleanup_query_dispatch_present": "CLEANUP_QUERY_DISPATCH_PRESENT",
    "same_lifecycle_native_cleanup_required": (
        "SAME_LIFECYCLE_NATIVE_CLEANUP_REQUIRED"
    ),
    "old_war_absence_sufficient": "OLD_WAR_ABSENCE_SUFFICIENT",
    "python_adapter_may_infer_cleanup": "PYTHON_ADAPTER_MAY_INFER_CLEANUP",
    "live_authorized": "LIVE_AUTHORIZED",
    "public_readiness_promoted": "PUBLIC_READINESS_PROMOTED",
    "action_readiness_promoted": "ACTION_READINESS_PROMOTED",
    "runtime_cleanup_ready": "RUNTIME_CLEANUP_READY",
    "source_specific_attribution_ready": "SOURCE_SPECIFIC_ATTRIBUTION_READY",
    "decision_ready": "DECISION_READY",
    "automatic_surrender_ready": "AUTOMATIC_SURRENDER_READY",
    "gen_034_resolved": "GEN_034_RESOLVED",
}


def _quoted_values(fragment: str) -> list[str]:
    return re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', fragment)


def _root_constant(source: str, name: str) -> str:
    match = re.search(_ROOT_CONSTANT_RE.pattern.format(name=re.escape(name)), source)
    if match is None:
        raise ValueError(f"root constant {name} is missing")
    return match.group(1)


def parse_root_binding(path: Path = ROOT_BINDING_PATH) -> dict[str, str]:
    """Read the three descriptive constants from the root Python module."""

    source = path.read_text(encoding="utf-8")
    return {
        "capability_id": _root_constant(source, "OPEN_KAISHEK_G2_CAPABILITY_ID"),
        "profile_id": _root_constant(source, "OPEN_KAISHEK_G2_PROFILE_ID"),
        "open_kaishek_commit": _root_constant(
            source, "OPEN_KAISHEK_G2_PROFILE_COMMIT"
        ),
    }


def parse_capability_source(path: Path) -> dict[str, Any]:
    """Extract the static capability descriptor from the Java source."""

    source = path.read_text(encoding="utf-8")
    profile_match = _JAVA_PROFILE_ID_RE.search(source)
    capability_match = _JAVA_CAPABILITY_RE.search(source)
    if profile_match is None:
        raise ValueError("open_kaishek capability profile ID is missing")
    if capability_match is None:
        raise ValueError("open_kaishek capability descriptor is missing")
    groups = capability_match.groupdict()
    provider_transition: dict[str, str | bool] = {}
    for key, name in _PROVIDER_STRING_CONSTANTS.items():
        match = re.search(
            _JAVA_BUILD_CONSTANT_RE.pattern.format(name=re.escape(name)), source
        )
        if match is None:
            raise ValueError(f"open_kaishek provider constant {name} is missing")
        provider_transition[key] = match.group(1)
    for key, name in _PROVIDER_BOOLEAN_CONSTANTS.items():
        match = re.search(
            _JAVA_BOOLEAN_CONSTANT_RE.pattern.format(name=re.escape(name)), source
        )
        if match is None:
            raise ValueError(f"open_kaishek provider constant {name} is missing")
        provider_transition[key] = match.group(1) == "true"
    return {
        "profile_id": profile_match.group(1),
        "capability_id": groups["id"],
        "required_fields": _quoted_values(groups["fields"]),
        "invariants": _quoted_values(groups["invariants"]),
        "read_only": groups["read_only"] == "true",
        "deterministic": groups["deterministic"] == "true",
        "native_certified": groups["native_certified"] == "true",
        "runtime_certified": groups["runtime_certified"] == "true",
        "provider_transition": provider_transition,
    }


def parse_ck3_profile_source(path: Path) -> dict[str, str]:
    """Extract the exact CK3 build identity from the Java profile source."""

    source = path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for name in ("GAME_VERSION", "EXE_SHA256"):
        match = re.search(
            _JAVA_BUILD_CONSTANT_RE.pattern.format(name=re.escape(name)), source
        )
        if match is None:
            raise ValueError(f"open_kaishek build constant {name} is missing")
        values[name.lower()] = match.group(1)
    return values


def _parse_java_constants(
    source: str,
    *,
    strings: dict[str, str],
    integers: dict[str, str] | None = None,
    booleans: dict[str, str] | None = None,
) -> dict[str, str | int | bool]:
    values: dict[str, str | int | bool] = {}
    for key, name in strings.items():
        match = re.search(
            _JAVA_BUILD_CONSTANT_RE.pattern.format(name=re.escape(name)), source
        )
        if match is None:
            raise ValueError(f"open_kaishek constant {name} is missing")
        values[key] = match.group(1)
    for key, name in (integers or {}).items():
        match = re.search(
            _JAVA_INT_CONSTANT_RE.pattern.format(name=re.escape(name)), source
        )
        if match is None:
            raise ValueError(f"open_kaishek constant {name} is missing")
        values[key] = int(match.group(1))
    for key, name in (booleans or {}).items():
        match = re.search(
            _JAVA_BOOLEAN_CONSTANT_RE.pattern.format(name=re.escape(name)), source
        )
        if match is None:
            raise ValueError(f"open_kaishek constant {name} is missing")
        values[key] = match.group(1) == "true"
    return values


def parse_war_bound_loss_source(path: Path) -> dict[str, str | int | bool]:
    """Extract the default-OFF war-bound loss candidate metadata."""

    source = path.read_text(encoding="utf-8")
    return _parse_java_constants(
        source,
        strings=_WAR_LOSS_STRING_CONSTANTS,
        integers=_WAR_LOSS_INT_CONSTANTS,
        booleans=_WAR_LOSS_BOOLEAN_CONSTANTS,
    )


def parse_projects_metrics_source(path: Path) -> dict[str, str | bool]:
    """Extract the public checkpoint-state delta and internal source pins."""

    source = path.read_text(encoding="utf-8")
    values = _parse_java_constants(
        source,
        strings=_PROJECTS_STRING_CONSTANTS,
        booleans=_PROJECTS_BOOLEAN_CONSTANTS,
    )
    capability = re.search(
        r"PROJECTS_METRICS\s*=\s*descriptor\(\s*\"([^\"]+)\"", source
    )
    if capability is None:
        raise ValueError("projects metrics capability ID is missing")
    checkpoint_field = "checkpoint_state"
    checkpoint_invariant = "cp26_ready_p3_absent_exposes_no_p3_result"
    if f'"{checkpoint_field}"' not in source:
        raise ValueError("projects metrics checkpoint_state field is missing")
    if f'"{checkpoint_invariant}"' not in source:
        raise ValueError("projects metrics checkpoint invariant is missing")
    values.update(
        {
            "capability_id": capability.group(1),
            "checkpoint_state_field": checkpoint_field,
            "checkpoint_absent_invariant": checkpoint_invariant,
        }
    )
    return values


def _parse_named_capability(
    source: str, name: str, capability_constant: str
) -> dict[str, object]:
    pattern = re.compile(
        rf"{re.escape(name)}\s*=\s*new\s+CapabilityDescriptor\s*\(\s*"
        rf"{re.escape(capability_constant)}\s*,\s*ID\s*,\s*"
        r"List\.of\((?P<fields>.*?)\)\s*,\s*"
        r"List\.of\((?P<invariants>.*?)\)\s*,\s*"
        r"(?P<read_only>true|false)\s*,\s*"
        r"(?P<deterministic>true|false)\s*,\s*"
        r"(?P<native_certified>true|false)\s*,\s*"
        r"(?P<runtime_certified>true|false)\s*\)\s*;",
        re.DOTALL,
    )
    match = pattern.search(source)
    if match is None:
        raise ValueError(f"open_kaishek capability {name} is missing")
    groups = match.groupdict()
    return {
        "required_fields": _quoted_values(groups["fields"]),
        "invariants": _quoted_values(groups["invariants"]),
        "read_only": groups["read_only"] == "true",
        "deterministic": groups["deterministic"] == "true",
        "native_certified": groups["native_certified"] == "true",
        "runtime_certified": groups["runtime_certified"] == "true",
    }


def parse_promotion_source_transport(path: Path) -> dict[str, object]:
    """Extract the two advertised transports and closed product flags."""

    source = path.read_text(encoding="utf-8")
    values: dict[str, object] = _parse_java_constants(
        source,
        strings=_PROMOTION_STRING_CONSTANTS,
        booleans=_PROMOTION_BOOLEAN_CONSTANTS,
    )
    widgets_match = re.search(
        r"FIXED_WIDGETS\s*=\s*List\.of\((?P<widgets>.*?)\)\s*;",
        source,
        re.DOTALL,
    )
    if widgets_match is None:
        raise ValueError("open_kaishek fixed promotion widget list is missing")
    values["fixed_widgets"] = _quoted_values(widgets_match.group("widgets"))
    values["query_transport"] = _parse_named_capability(
        source, "QUERY_TRANSPORT", "QUERY_TRANSPORT_CAPABILITY_ID"
    )
    values["action_transport"] = _parse_named_capability(
        source, "ACTION_TRANSPORT", "ACTION_TRANSPORT_CAPABILITY_ID"
    )
    return values


def parse_actual_truce_expiry_source(
    path: Path,
) -> dict[str, str | int | bool]:
    """Extract the default-OFF persisted-expiry metadata and ticket pins."""

    source = path.read_text(encoding="utf-8")
    return _parse_java_constants(
        source,
        strings=_ACTUAL_EXPIRY_STRING_CONSTANTS,
        integers=_ACTUAL_EXPIRY_INT_CONSTANTS,
        booleans=_ACTUAL_EXPIRY_BOOLEAN_CONSTANTS,
    )


def parse_postwar_cleanup_expiry_adapter_source(
    path: Path,
) -> dict[str, str | int | bool]:
    """Extract fixture-only cleanup/expiry adapter pins and closed gates."""

    source = path.read_text(encoding="utf-8")
    return _parse_java_constants(
        source,
        strings=_CLEANUP_ADAPTER_STRING_CONSTANTS,
        integers=_CLEANUP_ADAPTER_INT_CONSTANTS,
        booleans=_CLEANUP_ADAPTER_BOOLEAN_CONSTANTS,
    )


def _git_ref(checkout: Path, ref: str) -> tuple[str | None, str | None]:
    """Return a read-only Git ref and an error string, if any."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", ref],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        return None, f"{type(error).__name__}: {error}"
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return None, detail or f"git rev-parse exited {completed.returncode}"
    return completed.stdout.strip(), None


def _git_clean(checkout: Path) -> tuple[bool | None, str | None]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(checkout), "status", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        return None, f"{type(error).__name__}: {error}"
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return None, detail or f"git status exited {completed.returncode}"
    return not bool(completed.stdout.strip()), None


def _first_environment(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _resolve_checkout(fixture: dict[str, Any], checkout: str | os.PathLike[str] | None) -> Path:
    if checkout is not None:
        return Path(checkout).expanduser()
    value = _first_environment("XAR_OPEN_KAISHEK_ROOT", "OPEN_KAISHEK_ROOT")
    if value:
        return Path(value).expanduser()
    return Path(str(fixture["open_kaishek"]["default_root"])).expanduser()


def _equal(checks: dict[str, bool], name: str, actual: Any, expected: Any) -> None:
    checks[name] = actual == expected


def audit(
    *,
    checkout: str | os.PathLike[str] | None = None,
    require_checkout: bool = False,
    require_clean: bool = False,
) -> dict[str, Any]:
    """Run the static cross-repository audit and return a JSON-safe report."""

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    errors: list[str] = []
    root_binding: dict[str, str] | None = None
    try:
        root_binding = parse_root_binding()
    except (OSError, ValueError) as error:
        errors.append(f"root-binding: {type(error).__name__}: {error}")
    expected_root = fixture["root_binding"]
    if root_binding is None:
        checks["root_constants_parse"] = False
    else:
        checks["root_constants_parse"] = True
        _equal(checks, "root_capability_matches_fixture", root_binding["capability_id"], expected_root["capability_id"])
        _equal(checks, "root_profile_matches_fixture", root_binding["profile_id"], expected_root["profile_id"])
        _equal(checks, "root_commit_matches_fixture", root_binding["open_kaishek_commit"], expected_root["open_kaishek_commit"])

    expected_open = fixture["open_kaishek"]
    # The fixture has two identity views on purpose: ``root_binding`` is the
    # value exported by the Python side, while ``open_kaishek`` describes the
    # companion profile.  Keep a cross-section check here so a stale edit to
    # either half cannot produce a locally-GREEN but globally-drifted audit.
    checks["fixture_root_profile_matches_open_kaishek"] = (
        expected_root.get("profile_id") == expected_open.get("profile_id")
    )
    checks["fixture_root_capability_matches_open_kaishek"] = (
        expected_root.get("capability_id") == expected_open.get("capability_id")
    )
    checks["fixture_schema"] = fixture.get("schema") == "xar.ck3.g2_open_kaishek_compatibility.v1"
    checks["fixture_capability_status"] = (
        fixture.get("status") == "production-live-read-only-primitive"
    )
    for key in (
        "profile_id",
        "capability_id",
        "required_fields",
        "invariants",
        "read_only",
        "deterministic",
        "native_certified",
        "runtime_certified",
    ):
        checks[f"fixture_{key}_present"] = key in expected_open
    checks["fixture_duration_certification_live"] = (
        expected_open.get("native_certified") is True
        and expected_open.get("runtime_certified") is True
    )
    expected_provider = fixture.get("provider_transition", {})
    checks["fixture_provider_transition_shape"] = set(expected_provider) == {
        *_PROVIDER_STRING_CONSTANTS,
        *_PROVIDER_BOOLEAN_CONSTANTS,
    }
    checks["fixture_provider_readiness_bounded"] = (
        expected_provider.get("public_schema_changed") is False
        and expected_provider.get("private_leaf_reader_live_observed") is True
        and expected_provider.get("default_production_leaf_reader_installed")
        is True
        and expected_provider.get("default_production_binary_live_validated")
        is True
        and expected_provider.get("production_live_read_only_primitive") is True
        and expected_provider.get("expiry_observable") is False
        and expected_provider.get("termination_action_enabled") is False
        and expected_provider.get("full_decision_ready") is False
        and expected_provider.get("automatic_surrender_ready") is False
        and expected_provider.get("gen_034_closed") is False
    )
    expected_war_loss = fixture.get("war_bound_loss_candidate", {})
    checks["fixture_war_loss_shape"] = set(expected_war_loss) == {
        "source",
        *_WAR_LOSS_STRING_CONSTANTS,
        *_WAR_LOSS_INT_CONSTANTS,
        *_WAR_LOSS_BOOLEAN_CONSTANTS,
    }
    checks["fixture_war_loss_contract_bounded"] = (
        expected_war_loss.get("frozen_pre_termination_soldiers") == 598
        and expected_war_loss.get("destroyed_post_termination_soldiers") == 0
        and expected_war_loss.get("proven_boundary_soldiers_lost") == 598
        and expected_war_loss.get("read_only") is True
        and all(
            expected_war_loss.get(key) is False
            for key in _WAR_LOSS_BOOLEAN_CONSTANTS
            if key != "read_only"
        )
    )
    expected_projects = fixture.get("projects_metrics_delta", {})
    checks["fixture_projects_metrics_shape"] = set(expected_projects) == {
        "source",
        "capability_id",
        "checkpoint_state_field",
        "checkpoint_absent_invariant",
        *_PROJECTS_STRING_CONSTANTS,
        *_PROJECTS_BOOLEAN_CONSTANTS,
    }
    checks["fixture_projects_metrics_bounded"] = (
        expected_projects.get("checkpoint_state_required") is True
        and expected_projects.get("default_candidate_enabled") is False
        and expected_projects.get("production_live") is False
    )
    expected_promotion = fixture.get("promotion_source_transport", {})
    checks["fixture_promotion_transport_shape"] = set(expected_promotion) == {
        "source",
        "fixed_widgets",
        "query_transport",
        "action_transport",
        *_PROMOTION_STRING_CONSTANTS,
        *_PROMOTION_BOOLEAN_CONSTANTS,
    }
    checks["fixture_promotion_product_readiness_closed"] = all(
        expected_promotion.get(key) is False
        for key in _PROMOTION_BOOLEAN_CONSTANTS
    )
    checks["fixture_promotion_query_transport_bounded"] = (
        expected_promotion.get("query_transport", {}).get("read_only") is True
        and expected_promotion.get("query_transport", {}).get("deterministic")
        is True
        and expected_promotion.get("query_transport", {}).get(
            "native_certified"
        ) is False
        and expected_promotion.get("query_transport", {}).get(
            "runtime_certified"
        ) is False
    )
    checks["fixture_promotion_action_transport_bounded"] = all(
        expected_promotion.get("action_transport", {}).get(key) is False
        for key in (
            "read_only",
            "deterministic",
            "native_certified",
            "runtime_certified",
        )
    )
    expected_expiry = fixture.get("actual_truce_expiry_candidate", {})
    checks["fixture_actual_expiry_shape"] = set(expected_expiry) == {
        "source",
        *_ACTUAL_EXPIRY_STRING_CONSTANTS,
        *_ACTUAL_EXPIRY_INT_CONSTANTS,
        *_ACTUAL_EXPIRY_BOOLEAN_CONSTANTS,
    }
    checks["fixture_actual_expiry_readiness_closed"] = (
        expected_expiry.get("retained_pre_termination_soldiers") == 598
        and expected_expiry.get("retained_evaluated_days") == 1825
        and expected_expiry.get("read_only") is True
        and all(
            expected_expiry.get(key) is False
            for key in _ACTUAL_EXPIRY_BOOLEAN_CONSTANTS
            if key != "read_only"
        )
    )
    expected_cleanup = fixture.get("postwar_cleanup_expiry_adapter", {})
    checks["fixture_cleanup_adapter_shape"] = set(expected_cleanup) == {
        "source",
        *_CLEANUP_ADAPTER_STRING_CONSTANTS,
        *_CLEANUP_ADAPTER_INT_CONSTANTS,
        *_CLEANUP_ADAPTER_BOOLEAN_CONSTANTS,
    }
    cleanup_true_keys = {
        "metadata_only",
        "synthetic_fixture",
        "actual_expiry_query_dispatch_present",
        "cleanup_candidate_library_present",
        "same_lifecycle_native_cleanup_required",
    }
    checks["fixture_cleanup_adapter_live_blocked"] = (
        expected_cleanup.get("status")
        == "GREEN_STATIC_ADAPTER_LIVE_BLOCKED_ON_CLEANUP_DISPATCH"
        and expected_cleanup.get("pre_termination_soldiers") == 598
        and expected_cleanup.get("post_termination_soldiers") == 0
        and expected_cleanup.get("proven_boundary_soldiers_lost") == 598
        and all(expected_cleanup.get(key) is True for key in cleanup_true_keys)
        and all(
            expected_cleanup.get(key) is False
            for key in _CLEANUP_ADAPTER_BOOLEAN_CONSTANTS
            if key not in cleanup_true_keys
        )
    )
    checks["fixture_boundaries_closed"] = fixture.get("boundaries") == {
        "ck3_started": False,
        "process_attached": False,
        "save_mutated": False,
        "mutation_sent": False,
        "paradox_opcode_added": False,
        "allowlist_changed": False,
        "native_query_added": False,
        "readiness_promoted": True,
    }

    resolved_checkout = _resolve_checkout(fixture, checkout)
    external: dict[str, Any] = {
        "path": str(resolved_checkout),
        "available": resolved_checkout.is_dir(),
    }
    if not resolved_checkout.is_dir():
        checks["checkout_available"] = not require_checkout
        checks["checkout_required_policy"] = not require_checkout
        external["status"] = "not-available"
    else:
        checks["checkout_available"] = True
        external["status"] = "checked"
        capability_path = resolved_checkout / expected_open["capability_source"]
        ck3_profile_path = resolved_checkout / expected_open["ck3_profile_source"]
        war_loss_path = resolved_checkout / expected_war_loss["source"]
        projects_path = resolved_checkout / expected_projects["source"]
        promotion_path = resolved_checkout / expected_promotion["source"]
        expiry_path = resolved_checkout / expected_expiry["source"]
        cleanup_path = resolved_checkout / expected_cleanup["source"]
        try:
            capability = parse_capability_source(capability_path)
            checks["capability_source_parse"] = True
            for key in (
                "profile_id",
                "capability_id",
                "required_fields",
                "invariants",
                "read_only",
                "deterministic",
                "native_certified",
                "runtime_certified",
            ):
                _equal(checks, f"capability_{key}_matches", capability[key], expected_open[key])
            _equal(
                checks,
                "capability_provider_transition_matches",
                capability["provider_transition"],
                expected_provider,
            )
            external["capability"] = capability
        except (OSError, ValueError) as error:
            checks["capability_source_parse"] = False
            errors.append(f"capability-source: {type(error).__name__}: {error}")
        try:
            build = parse_ck3_profile_source(ck3_profile_path)
            checks["ck3_profile_source_parse"] = True
            _equal(checks, "ck3_game_version_matches", build["game_version"], expected_open["game_version"])
            _equal(checks, "ck3_exe_sha256_matches", build["exe_sha256"], expected_open["exe_sha256"])
            external["ck3_profile"] = build
        except (OSError, ValueError) as error:
            checks["ck3_profile_source_parse"] = False
            errors.append(f"ck3-profile-source: {type(error).__name__}: {error}")
        try:
            war_loss = parse_war_bound_loss_source(war_loss_path)
            checks["war_loss_source_parse"] = True
            _equal(
                checks,
                "war_loss_metadata_matches",
                war_loss,
                {
                    key: value
                    for key, value in expected_war_loss.items()
                    if key != "source"
                },
            )
            external["war_bound_loss_candidate"] = war_loss
        except (OSError, ValueError) as error:
            checks["war_loss_source_parse"] = False
            errors.append(f"war-loss-source: {type(error).__name__}: {error}")
        try:
            projects = parse_projects_metrics_source(projects_path)
            checks["projects_metrics_source_parse"] = True
            _equal(
                checks,
                "projects_metrics_delta_matches",
                projects,
                {
                    key: value
                    for key, value in expected_projects.items()
                    if key != "source"
                },
            )
            external["projects_metrics_delta"] = projects
        except (OSError, ValueError) as error:
            checks["projects_metrics_source_parse"] = False
            errors.append(f"projects-metrics-source: {type(error).__name__}: {error}")
        try:
            promotion = parse_promotion_source_transport(promotion_path)
            checks["promotion_transport_source_parse"] = True
            _equal(
                checks,
                "promotion_transport_contract_matches",
                promotion,
                {
                    key: value
                    for key, value in expected_promotion.items()
                    if key != "source"
                },
            )
            external["promotion_source_transport"] = promotion
        except (OSError, ValueError) as error:
            checks["promotion_transport_source_parse"] = False
            errors.append(
                f"promotion-transport-source: {type(error).__name__}: {error}"
            )
        try:
            expiry = parse_actual_truce_expiry_source(expiry_path)
            checks["actual_expiry_source_parse"] = True
            _equal(
                checks,
                "actual_expiry_metadata_matches",
                expiry,
                {
                    key: value
                    for key, value in expected_expiry.items()
                    if key != "source"
                },
            )
            external["actual_truce_expiry_candidate"] = expiry
        except (OSError, ValueError) as error:
            checks["actual_expiry_source_parse"] = False
            errors.append(
                f"actual-expiry-source: {type(error).__name__}: {error}"
            )
        try:
            cleanup = parse_postwar_cleanup_expiry_adapter_source(cleanup_path)
            checks["cleanup_adapter_source_parse"] = True
            _equal(
                checks,
                "cleanup_adapter_metadata_matches",
                cleanup,
                {
                    key: value
                    for key, value in expected_cleanup.items()
                    if key != "source"
                },
            )
            external["postwar_cleanup_expiry_adapter"] = cleanup
        except (OSError, ValueError) as error:
            checks["cleanup_adapter_source_parse"] = False
            errors.append(
                f"cleanup-adapter-source: {type(error).__name__}: {error}"
            )

        head, head_error = _git_ref(resolved_checkout, "HEAD")
        origin, origin_error = _git_ref(resolved_checkout, "origin/main")
        external["head"] = head
        external["origin_main"] = origin
        checks["checkout_head_matches_fixture"] = head == expected_root["open_kaishek_commit"]
        checks["checkout_origin_main_matches_fixture"] = origin == expected_root["open_kaishek_commit"]
        if head_error:
            errors.append(f"git-head: {head_error}")
        if origin_error:
            errors.append(f"git-origin-main: {origin_error}")
        clean, clean_error = _git_clean(resolved_checkout)
        external["clean"] = clean
        checks["checkout_clean"] = clean is True if require_clean else True
        if clean_error:
            errors.append(f"git-status: {clean_error}")

    # These are policy boundaries, not inferred capabilities.  Keep them in
    # every report so downstream consumers cannot mistake a static GREEN for
    # a live evaluator result.
    boundaries = dict(fixture["boundaries"])
    all_checks = all(checks.values()) and not errors
    if all_checks:
        status = "GREEN_STATIC" if external["available"] else "GREEN_STATIC_NO_CHECKOUT"
    else:
        status = "RED"
    native_certified = expected_open.get("native_certified") is True
    runtime_certified = expected_open.get("runtime_certified") is True
    production_live = (
        expected_provider.get("production_live_read_only_primitive") is True
    )
    report = {
        "schema": "xar.ck3.g2_open_kaishek_compatibility_audit.v1",
        "status": status,
        "ok": all_checks,
        "fixture": str(FIXTURE_PATH),
        "root_binding": root_binding,
        "external": external,
        "checks": checks,
        "errors": errors,
        "readiness": {
            "stage": (
                "production-live primitive"
                if all_checks and production_live
                else "static-blocked"
            ),
            "native_certified": native_certified,
            "runtime_certified": runtime_certified,
            "production_live": production_live,
        },
        "boundaries": boundaries,
    }
    return report


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, help="open_kaishek checkout to inspect")
    parser.add_argument("--output", type=Path, help="write the JSON audit here")
    parser.add_argument("--require-checkout", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    report = audit(
        checkout=args.checkout,
        require_checkout=args.require_checkout,
        require_clean=args.require_clean,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        write_json(args.output.expanduser().resolve(), report)
    print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
