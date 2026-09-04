#!/usr/bin/env python3
"""Freeze the current binary/product G2 cleanup-expiry live command.

This verifier is deliberately no-launch. It checks the exact native candidate,
its source archive and build flags, the production projection, the retained
pre-war ticket, and one fresh short-path command for the exclusive CK3 slot.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Callable


RESEARCH_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPO_ROOT / "ck3_autonomous_player" / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in os.sys.path:
        os.sys.path.insert(0, str(candidate))

import prepare_g2_postwar_retention_expiry_capture as retention  # noqa: E402


DEFAULT_MANIFEST = (
    RESEARCH_ROOT
    / "fixtures"
    / "g2_postwar_cleanup_expiry_current_pin_live_manifest.json"
)
EXPECTED_SCHEMA = (
    "xar.ck3.g2_postwar_cleanup_expiry_current_pin_live_manifest.v1"
)
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_TICKET_ID = (
    "E0A93DDC584BB2313BC03CE076779BAFD261ABBABB69E9DE3BEF284DFE14823A"
)
SELECTED_OPTIONS = {
    "XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1": "ON",
    "XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1": "ON",
}
OFF_OPTIONS = (
    "XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2",
    "XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1",
    "XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1",
    "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1",
    "XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1",
    "XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1",
)


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_hash(value: object, name: str) -> str:
    result = str(value).upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise ValueError(f"{name} must be a SHA-256")
    return result


def _load_json(path: Path, name: str) -> dict[str, Any]:
    try:
        return _mapping(
            json.loads(path.read_text(encoding="utf-8-sig")), name
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read {name}: {error}") from error


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def _resolve(value: object, repo_root: Path) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _cache_value(cache: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}:[^=]+=(.*)$", cache)
    return match.group(1).strip() if match else None


def _tree_digest(root: Path) -> tuple[str, int]:
    snapshot = {
        path.relative_to(root).as_posix(): {
            "size": path.stat().st_size,
            "sha256": _sha256_file(path).lower(),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }
    raw = json.dumps(
        snapshot, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest().upper(), len(snapshot)


def _verify_release_tree(
    staging: Path, manifest_path: Path, source_commit: str
) -> dict[str, object]:
    release = _load_json(manifest_path, "release manifest")
    entries = release.get("files")
    if not isinstance(entries, list):
        raise ValueError("release manifest files must be an array")
    expected: dict[str, dict[str, object]] = {}
    for raw in entries:
        entry = _mapping(raw, "release entry")
        relative = str(entry.get("path", ""))
        if not relative or relative in expected:
            raise ValueError("release manifest has an empty/duplicate path")
        expected[relative] = entry
    actual = {
        path.relative_to(staging).as_posix(): path
        for path in staging.rglob("*")
        if path.is_file()
    }
    exact = set(actual) == set(expected)
    if exact:
        exact = all(
            path.stat().st_size == expected[relative].get("size")
            and _sha256_file(path).lower()
            == str(expected[relative].get("sha256", "")).lower()
            for relative, path in actual.items()
        )
    return {
        "format_version": release.get("format_version"),
        "git_sha": release.get("git_sha"),
        "expected_source_commit": source_commit,
        "file_count": len(entries),
        "files_exact": exact,
    }


def _process_inventory() -> dict[str, object]:
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("could not inventory CK3/injector processes")
    names = {"ck3.exe", "xar_ck3_bridge_injector.exe"}
    counts = {name: 0 for name in sorted(names)}
    for row in csv.reader(io.StringIO(completed.stdout)):
        if row and row[0].strip().lower() in names:
            counts[row[0].strip().lower()] += 1
    return {"counts": counts, "all_zero": all(v == 0 for v in counts.values())}


def _ps_quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def validate_manifest_contract(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("unexpected current-pin manifest schema")
    if manifest.get("state") != "static-ready-live-pending":
        raise ValueError("current-pin manifest is not live-pending")
    identity = _mapping(manifest.get("identity"), "identity")
    if identity != {
        "war_id": 50_331_699,
        "character_id": 29_829,
        "opponent_character_id": 36_769,
        "date_raw": 53_223_936,
    }:
        raise ValueError("frozen G2 identity changed")
    build = _mapping(manifest.get("build_contract"), "build_contract")
    if build.get("selected_options") != SELECTED_OPTIONS:
        raise ValueError("selected private candidate options changed")
    if build.get("required_off_options") != list(OFF_OPTIONS):
        raise ValueError("adjacent OFF option list changed")
    if build.get("expected_ctest_count") != 94:
        raise ValueError("expected native test count changed")
    boundaries = _mapping(manifest.get("boundaries"), "boundaries")
    if not boundaries or any(value is not False for value in boundaries.values()):
        raise ValueError("public/action/live boundaries must all remain false")
    dependency = _mapping(manifest.get("b7_dependency"), "b7_dependency")
    if (
        dependency.get("required_as_g2_runtime_input") is not False
        or dependency.get("new_freeze_required") is not False
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(dependency.get("integrated_commit", ""))
        )
    ):
        raise ValueError("B7 dependency boundary changed")
    command = _mapping(manifest.get("live_command"), "live_command")
    argv = command.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or argv.count("--authorize-private-live") != 1
        or command.get("unique") is not True
        or command.get("execute_during_preflight") is not False
    ):
        raise ValueError("live command authorization boundary changed")


def build_command(manifest: dict[str, Any]) -> str:
    argv = _mapping(manifest["live_command"], "live_command")["argv"]
    return " ".join(["&", *(_ps_quote(value) for value in argv)])


def run_preflight(
    manifest_path: Path,
    report_path: Path,
    *,
    repo_root: Path = REPO_ROOT,
    process_inventory: Callable[[], dict[str, object]] = _process_inventory,
) -> dict[str, object]:
    manifest_path = manifest_path.expanduser().resolve()
    report_path = report_path.expanduser().resolve()
    if report_path.exists():
        raise FileExistsError(f"preflight report already exists: {report_path}")
    manifest = _load_json(manifest_path, "current-pin manifest")
    validate_manifest_contract(manifest)
    paths = _mapping(manifest["paths"], "paths")
    hashes = _mapping(manifest["sha256"], "sha256")
    source_expected = _mapping(manifest["source_sha256"], "source_sha256")
    source_commit = str(manifest["candidate_source_commit"])
    attempt = Path(str(paths["fresh_attempt"])).expanduser().resolve()
    if report_path == attempt or attempt in report_path.parents:
        raise ValueError("preflight report must remain outside the future attempt")

    resolved = {
        name: _resolve(paths[name], repo_root)
        for name in (
            "python",
            "preflight",
            "runner",
            "base_runner",
            "adapter",
            "retention_manifest",
            "cleanup_source_contract",
            "expiry_source_contract",
            "source_checkpoint",
            "source_driver_state",
            "game_executable",
            "bridge_dll",
            "bridge_injector",
            "cmake_cache",
            "native_ctest",
            "source_zip",
            "product_staging",
            "product_manifest",
            "product_zip",
        )
    }
    actual_hashes = {
        name: _sha256_file(path) if path.is_file() else None
        for name, path in resolved.items()
        if name != "product_staging"
    }
    hash_checks = {
        name: actual_hashes[name] == _expected_hash(hashes[name], name)
        for name in actual_hashes
    }
    source_actual = {
        relative: (
            _sha256_file((repo_root / relative).resolve())
            if (repo_root / relative).is_file()
            else None
        )
        for relative in source_expected
    }
    source_checks = {
        relative: source_actual[relative]
        == _expected_hash(expected, relative)
        for relative, expected in source_expected.items()
    }

    cache = (
        _read_text(resolved["cmake_cache"])
        if resolved["cmake_cache"].is_file()
        else ""
    )
    ctest = (
        _read_text(resolved["native_ctest"])
        if resolved["native_ctest"].is_file()
        else ""
    )
    release = (
        _verify_release_tree(
            resolved["product_staging"],
            resolved["product_manifest"],
            source_commit,
        )
        if resolved["product_staging"].is_dir()
        and resolved["product_manifest"].is_file()
        else {}
    )
    tree_sha256, product_count = (
        _tree_digest(resolved["product_staging"])
        if resolved["product_staging"].is_dir()
        else ("", 0)
    )
    retention_manifest = (
        _load_json(resolved["retention_manifest"], "retention manifest")
        if resolved["retention_manifest"].is_file()
        else {}
    )
    ticket: dict[str, object] = {}
    ticket_error: str | None = None
    try:
        ticket = retention.build_retention_ticket(
            retention_manifest, repo_root=repo_root
        )
    except BaseException as error:
        ticket_error = f"{type(error).__name__}: {error}"

    cleanup_contract = (
        _load_json(resolved["cleanup_source_contract"], "cleanup contract")
        if resolved["cleanup_source_contract"].is_file()
        else {}
    )
    expiry_contract = (
        _load_json(resolved["expiry_source_contract"], "expiry contract")
        if resolved["expiry_source_contract"].is_file()
        else {}
    )
    before = process_inventory()
    cleanup_semantics = str(
        _mapping(
            cleanup_contract.get("exact_native_store_contract"),
            "exact_native_store_contract",
        ).get("cleanup", "")
    )
    checks = {
        "all_input_hashes": all(hash_checks.values()),
        "all_source_hashes": all(source_checks.values()),
        "exact_game_build": actual_hashes.get("game_executable")
        == EXPECTED_EXE_SHA256,
        "selected_candidate_options_on": all(
            _cache_value(cache, name) == expected
            for name, expected in SELECTED_OPTIONS.items()
        ),
        "adjacent_candidates_off": all(
            _cache_value(cache, name) == "OFF" for name in OFF_OPTIONS
        ),
        "native_ctest_green": (
            "100% tests passed, 0 tests failed out of 94" in ctest
            and "94/94 Test" in ctest
        ),
        "cleanup_source_default_off": cleanup_contract.get("default_enabled")
        is False,
        "cleanup_never_infers_destroyed_from_war_absence": (
            "WarID absence" in cleanup_semantics
            and "never the destroyed result" in cleanup_semantics
        ),
        "expiry_source_default_off": expiry_contract.get("default_enabled")
        is False,
        "retention_ticket_exact": ticket_error is None
        and ticket.get("retention_ticket_id") == EXPECTED_TICKET_ID,
        "release_manifest_exact": release.get("format_version") == 2
        and release.get("git_sha") == source_commit
        and release.get("file_count") == 86
        and release.get("files_exact") is True,
        "production_tree_exact": product_count == 86
        and tree_sha256
        == _expected_hash(
            manifest["product_contract"]["production_tree_sha256"],
            "production tree",
        ),
        "exclusive_process_slot_empty_before": before.get("all_zero") is True,
        "future_attempt_absent": not attempt.exists(),
        "b7_new_freeze_not_required": manifest["b7_dependency"][
            "new_freeze_required"
        ]
        is False,
        "preflight_did_not_prepare_attach_or_launch": True,
    }
    after = process_inventory()
    checks["exclusive_process_slot_empty_after"] = after.get("all_zero") is True
    ok = all(checks.values())
    payload = {
        "schema": "xar.ck3.g2_postwar_cleanup_expiry_current_pin_preflight.v1",
        "status": "READY_TO_SERIAL_LIVE" if ok else "RED",
        "ok": ok,
        "candidate_source_commit": source_commit,
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "report": str(report_path),
        "attempt_dir": str(attempt),
        "ck3_started": False,
        "process_attached": False,
        "profile_prepared": False,
        "process_inventory_before": before,
        "process_inventory_after": after,
        "actual_hashes": actual_hashes,
        "hash_checks": hash_checks,
        "source_hashes": source_actual,
        "source_checks": source_checks,
        "product": {
            **release,
            "production_tree_sha256": tree_sha256,
            "tree_file_count": product_count,
        },
        "retention_ticket": ticket,
        "retention_ticket_error": ticket_error,
        "checks": checks,
        "boundaries": manifest["boundaries"],
        "b7_dependency": manifest["b7_dependency"],
        "unique_powershell_command": build_command(manifest),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_name(report_path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, report_path)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = run_preflight(args.manifest, args.report)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=os.sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "report": payload["report"],
                "unique_powershell_command": payload[
                    "unique_powershell_command"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
