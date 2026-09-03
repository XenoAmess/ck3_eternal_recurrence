#!/usr/bin/env python3
"""Audit the frozen root/open_kaishek G2 binding without launching CK3.

The verifier is deliberately source-level.  It checks the root's descriptive
binding against the companion Java profile and exact-build profile, then (when
the external checkout is available) checks its source files and read-only Git
refs.  It never starts or attaches to CK3 and never changes a Paradox opcode
allow-list.
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
    return {
        "profile_id": profile_match.group(1),
        "capability_id": groups["id"],
        "required_fields": _quoted_values(groups["fields"]),
        "invariants": _quoted_values(groups["invariants"]),
        "read_only": groups["read_only"] == "true",
        "deterministic": groups["deterministic"] == "true",
        "native_certified": groups["native_certified"] == "true",
        "runtime_certified": groups["runtime_certified"] == "true",
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
    checks["fixture_static_status"] = fixture.get("status") == "static-observation-only"
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
    checks["fixture_certification_closed"] = (
        expected_open.get("native_certified") is False
        and expected_open.get("runtime_certified") is False
    )
    checks["fixture_boundaries_closed"] = fixture.get("boundaries") == {
        "ck3_started": False,
        "process_attached": False,
        "save_mutated": False,
        "mutation_sent": False,
        "paradox_opcode_added": False,
        "allowlist_changed": False,
        "native_query_added": False,
        "readiness_promoted": False,
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
            "stage": "static-ready" if all_checks else "static-blocked",
            "native_certified": False,
            "runtime_certified": False,
            "production_live": False,
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
