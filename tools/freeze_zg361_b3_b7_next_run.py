#!/usr/bin/env python3
"""Freeze one B3 promotion-source checkpoint command without starting CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Sequence


PROMOTION_SWITCH = (
    "XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1"
)
PROMOTION_CAPABILITY = (
    "game.command.query-zhongguo-promotion-compensation-postcondition-v1"
)
RESULT_CASE_CAPABILITY = "game.command.query-zhongguo-result-case-snapshot-v1"
PROJECTION_NAME = "b3-current-reachable-schema3-current-core"
EXPECTED_PRODUCT_TREE = (
    "a6c70f0648e7a8142d6e34d2a41affd214ed8fe993b4153bf4c93b073194576d"
)
EXPECTED_PROJECTION_SHA256 = (
    "0a405fd653c1be44b7d8d7917be5fba9dab190d3dc30bbf87719b3c94cb55f23"
)
EXPECTED_CLOSURE_SHA256 = (
    "40bdbce78107d42063710a88eb103c0a7d43c6aecc691f6b23eaad4f2bd02833"
)
PIPE_TOKEN = re.compile(r"[0-9a-f]{32}\Z")
MOUNT_PATH_LIMIT = 250


class FreezeError(ValueError):
    """A no-launch input or authorization condition drifted."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def record(path: Path) -> dict[str, object]:
    path = path.resolve()
    if not path.is_file():
        raise FreezeError(f"required file is missing: {path}")
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def native_source_fingerprint(native_root: Path) -> tuple[int, str]:
    paths = [native_root / "CMakeLists.txt"]
    for tree in (native_root / "include", native_root / "src"):
        paths.extend(
            path
            for path in tree.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".cpp", ".hpp", ".h", ".c"}
        )
    paths = sorted(paths, key=lambda value: str(value).lower())
    prefix = str(native_root.resolve())
    rows = []
    for path in paths:
        relative = str(path.resolve())[len(prefix) :].lstrip("\\/")
        rows.append(f"{relative}\0{sha256(path).upper()}")
    digest = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest().lower()
    return len(paths), digest


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise FreezeError(f"JSON root is not an object: {path}")
    return value


def nested_object(value: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: object = value
    for key in keys:
        if not isinstance(current, dict) or not isinstance(current.get(key), dict):
            raise FreezeError("bridge manifest lacks " + ".".join(keys))
        current = current[key]
    return current


def resolve_manifest_path(manifest_path: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise FreezeError(f"bridge manifest lacks {label}")
    path = Path(value)
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


def verify_hashed_file(path: Path, row: dict[str, Any], label: str) -> dict[str, object]:
    observed = record(path)
    expected = row.get("sha256")
    if not isinstance(expected, str) or observed["sha256"] != expected.lower():
        raise FreezeError(f"{label} SHA-256 drifted")
    expected_bytes = row.get("bytes")
    if not isinstance(expected_bytes, int) or observed["bytes"] != expected_bytes:
        raise FreezeError(f"{label} size drifted")
    return observed


def verify_product(
    source: Path,
    projection_path: Path,
    closure_path: Path,
) -> dict[str, object]:
    if sha256(projection_path) != EXPECTED_PROJECTION_SHA256:
        raise FreezeError("explicit-AND projection manifest SHA-256 drifted")
    projection = load_json(projection_path)
    if (
        projection.get("kind") != "zg361_phase2_product_projection"
        or projection.get("projection") != PROJECTION_NAME
        or projection.get("source_tree_sha256") != EXPECTED_PRODUCT_TREE
    ):
        raise FreezeError("explicit-AND projection identity drifted")
    rows = projection.get("files")
    if not isinstance(rows, list) or len(rows) != 634:
        raise FreezeError("explicit-AND projection file inventory drifted")
    relative_paths: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise FreezeError("projection contains an invalid file row")
        relative = row["path"]
        path = source / Path(*relative.split("/"))
        if (
            not path.is_file()
            or path.stat().st_size != row.get("bytes")
            or sha256(path) != str(row.get("sha256", "")).lower()
        ):
            raise FreezeError(f"explicit-AND product file drifted: {relative}")
        relative_paths.append(relative)
    if sha256(closure_path) != EXPECTED_CLOSURE_SHA256:
        raise FreezeError("schema-3 closure evidence SHA-256 drifted")
    closure = load_json(closure_path)
    localization = closure.get("localization_closure")
    widget_gui = closure.get("scripted_widget_gui_closure")
    selected_canonical = closure.get("selected_canonical_files")
    current_core = closure.get("current_core_effect_shards")
    current_core_files = (
        current_core.get("updated_files", [])
        if isinstance(current_core, dict)
        else []
    )
    closure_checks = {
        "kind": closure.get("kind")
        == "zg361_phase2_b3_material_custom_call_closure_expansion",
        "schema_v3": closure.get("schema_version") == 3,
        "green": closure.get("green") is True,
        "candidate_source": Path(
            str(closure.get("candidate_source", ""))
        ).resolve()
        == source.resolve(),
        "effect_count": closure.get("final_effect_definition_count") == 3706,
        "event_count": closure.get("final_event_definition_count") == 988,
        "trigger_count": closure.get("final_trigger_definition_count") == 24,
        "no_missing_effects": closure.get("final_missing_effects") == [],
        "no_missing_events": closure.get("final_missing_events") == [],
        "no_missing_triggers": closure.get("final_missing_triggers") == [],
        "selected_canonical_files_green": isinstance(
            selected_canonical, dict
        )
        and selected_canonical.get("green") is True
        and selected_canonical.get("provider_files_exact") is True
        and selected_canonical.get("selected_file_count") == 630,
        "localization_green": isinstance(localization, dict)
        and localization.get("green") is True,
        "localization_keys": isinstance(localization, dict)
        and localization.get("required_key_count") == 936,
        "localization_files": isinstance(localization, dict)
        and localization.get("provider_file_count") == 63,
        "scripted_widget_gui_green": isinstance(widget_gui, dict)
        and widget_gui.get("green") is True,
        "scripted_widget_gui_files": isinstance(widget_gui, dict)
        and widget_gui.get("required_file_count") == 4
        and "gui/zg361_promotion_source_bridge.gui"
        in widget_gui.get("required_files", []),
        "current_core_shards_green": isinstance(current_core, dict)
        and current_core.get("green") is True
        and current_core.get("canonical_blocks_exact") is True,
        "current_core_shards_bounded": isinstance(current_core, dict)
        and current_core.get("definition_count") == 26
        and current_core.get("max_effects_per_file") == 9
        and len(current_core_files) == 4,
    }
    if not all(closure_checks.values()):
        failed = [name for name, value in closure_checks.items() if not value]
        raise FreezeError("schema-3 closure evidence RED: " + ", ".join(failed))
    return {
        "source": str(source),
        "file_count": len(rows),
        "source_tree_sha256": projection["source_tree_sha256"],
        "formal_overlay_tree_sha256": projection.get(
            "formal_overlay_tree_sha256"
        ),
        "file_list_sha256": projection.get("file_list_sha256"),
        "projection_manifest": record(projection_path),
        "closure_evidence": record(closure_path),
        "closure_checks": closure_checks,
        "relative_paths": relative_paths,
    }


def verify_canonical_contract(root: Path) -> dict[str, object]:
    native = root / "ck3_autonomous_player" / "native_bridge"
    cmake_path = native / "CMakeLists.txt"
    adapter_path = native / "src" / "ck3_11906_adapter.cpp"
    game_adapter_path = native / "src" / "game_adapter.cpp"
    runner_path = root / "tools" / "run_zhongguo_acceptance.py"
    promotion_contract_path = (
        root
        / "ck3_autonomous_player"
        / "src"
        / "xar_autoplayer"
        / "bridge"
        / "zhongguo_promotion_compensation_postcondition_contract.py"
    )
    result_contract_path = (
        root
        / "ck3_autonomous_player"
        / "src"
        / "xar_autoplayer"
        / "bridge"
        / "zhongguo_result_case_snapshot_contract.py"
    )
    cmake = cmake_path.read_text(encoding="utf-8")
    adapter = adapter_path.read_text(encoding="utf-8")
    game_adapter = game_adapter_path.read_text(encoding="utf-8")
    runner = runner_path.read_text(encoding="utf-8")
    promotion_contract = promotion_contract_path.read_text(encoding="utf-8")
    result_contract = result_contract_path.read_text(encoding="utf-8")
    action_steps = re.search(
        r"PHASE2_REQUIRED_ACTION_STEPS\s*=\s*\{(?P<body>.*?)\n\}",
        runner,
        re.DOTALL,
    )
    capture_bridge_labels = re.search(
        r"PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_BRIDGE_CAPABILITY_LABELS"
        r"\s*=\s*\((?P<body>.*?)\n\)",
        runner,
        re.DOTALL,
    )
    capture_query_labels = re.search(
        r"PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_QUERY_FLAG_LABELS"
        r"\s*=\s*\((?P<body>.*?)\n\)",
        runner,
        re.DOTALL,
    )
    capture_action_labels = re.search(
        r"PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_ACTION_STEP_LABELS"
        r"\s*=\s*\((?P<body>.*?)\n\)",
        runner,
        re.DOTALL,
    )
    checks = {
        "promotion_option_default_off": re.search(
            rf"option\(\s*{PROMOTION_SWITCH}\s*.*?\s+OFF\s*\)",
            cmake,
            re.DOTALL,
        )
        is not None,
        "promotion_compile_definition_wired": (
            f"if({PROMOTION_SWITCH})" in cmake
            and f"{PROMOTION_SWITCH}=1" in cmake
        ),
        "promotion_capability_descriptor_guarded": (
            f"#if defined({PROMOTION_SWITCH})" in adapter
            and "kZhongguoPromotionCompensationPostconditionV1Capability,"
            in adapter
        ),
        "promotion_step_provider_wired": (
            "ParseZhongguoPromotionCompensationPostconditionV1Step(step)"
            in game_adapter
        ),
        "result_case_capability_descriptor_enabled": (
            "kZhongguoResultCaseSnapshotV1Capability," in adapter
        ),
        "runner_requires_promotion": (
            "QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY" in runner
            and "zhongguo_promotion_compensation_v1_query_supported" in runner
        ),
        "runner_requires_result_case": (
            "QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY" in runner
            and "zhongguo_result_case_snapshot_v1_query_supported" in runner
        ),
        "runner_does_not_materialize_typed_result_query_as_zero_arg_action": (
            action_steps is not None
            and "result_case_snapshot" not in action_steps.group("body")
            and "QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP"
            not in action_steps.group("body")
        ),
        "promotion_source_transport_capabilities_advertised": (
            "kZhongguoPromotionSourceProgressV1TransportCapability," in adapter
            and "kZhongguoReviewNowActionV1TransportCapability," in adapter
        ),
        "focused_capture_transport_gate_wired": (
            capture_bridge_labels is not None
            and "promotion_source_progress_transport"
            in capture_bridge_labels.group("body")
            and "review_now_action_transport"
            in capture_bridge_labels.group("body")
        ),
        "focused_capture_query_gate_wired": (
            capture_query_labels is not None
            and "current_event_context" in capture_query_labels.group("body")
        ),
        "focused_capture_action_gate_wired": (
            capture_action_labels is not None
            and all(
                label in capture_action_labels.group("body")
                for label in (
                    "save_checkpoint",
                    "pause_timeline",
                    "resume_timeline",
                    "bounded_timeline_speed",
                )
            )
        ),
        "promotion_contract_literal_matches": PROMOTION_CAPABILITY
        in promotion_contract,
        "result_case_contract_literal_matches": RESULT_CASE_CAPABILITY
        in result_contract,
    }
    if not all(checks.values()):
        failed = [name for name, value in checks.items() if not value]
        raise FreezeError("canonical provider contract RED: " + ", ".join(failed))
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        encoding="ascii",
        capture_output=True,
        check=True,
    ).stdout.strip()
    native_file_count, native_fingerprint = native_source_fingerprint(native)
    return {
        "root": str(root),
        "git_commit": head,
        "runner": record(runner_path),
        "cmake": record(cmake_path),
        "adapter": record(adapter_path),
        "game_adapter": record(game_adapter_path),
        "native_source_file_count": native_file_count,
        "native_source_fingerprint_sha256": native_fingerprint,
        "checks": checks,
    }


def verify_bridge_manifest(
    manifest_path: Path,
    canonical: dict[str, object],
) -> dict[str, object]:
    manifest = load_json(manifest_path)
    build_key = "live_candidate_build" if isinstance(
        manifest.get("live_candidate_build"), dict
    ) else "build"
    build = nested_object(manifest, build_key)
    bridge_row = nested_object(manifest, build_key, "bridge")
    injector_row = nested_object(manifest, build_key, "injector")
    source = nested_object(manifest, "source")
    tests_key = (
        "live_candidate_full_native"
        if build_key == "live_candidate_build"
        else "full_native"
    )
    tests = nested_object(manifest, "tests", tests_key)
    cache_path = resolve_manifest_path(
        manifest_path, build.get("cmake_cache_path"), "build.cmake_cache_path"
    )
    bridge_path = resolve_manifest_path(
        manifest_path, bridge_row.get("path"), "build.bridge.path"
    )
    injector_path = resolve_manifest_path(
        manifest_path, injector_row.get("path"), "build.injector.path"
    )
    cache = cache_path.read_text(encoding="utf-8", errors="strict")
    cache_line = f"{PROMOTION_SWITCH}:BOOL=ON"
    if re.search(rf"(?m)^{re.escape(cache_line)}$", cache) is None:
        raise FreezeError("frozen B7 bridge did not enable promotion compensation")
    if tests.get("result") != "GREEN" or tests.get("failed") != 0:
        raise FreezeError("frozen B7 full native tests are not GREEN")
    candidate_commit = source.get("candidate_commit")
    canonical_commit = canonical.get("git_commit")
    canonical_root = canonical.get("root")
    if not all(
        isinstance(value, str)
        for value in (candidate_commit, canonical_commit, canonical_root)
    ):
        raise FreezeError("B7/canonical commit binding is malformed")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", candidate_commit, canonical_commit],
        cwd=canonical_root,
        capture_output=True,
        check=False,
    )
    if ancestry.returncode != 0:
        raise FreezeError("frozen B7 source commit is not a canonical ancestor")
    frozen_fingerprint = source.get("native_source_fingerprint_sha256")
    if not isinstance(frozen_fingerprint, str) or (
        frozen_fingerprint.lower()
        != canonical.get("native_source_fingerprint_sha256")
    ):
        raise FreezeError("frozen B7 native source differs from current canonical")
    if source.get("native_source_file_count") != canonical.get(
        "native_source_file_count"
    ):
        raise FreezeError("frozen B7 native source file count drifted")
    frozen_files = source.get("frozen_files")
    if not isinstance(frozen_files, dict):
        raise FreezeError("frozen B7 manifest lacks source.frozen_files")
    expected_adapter = canonical["adapter"]
    if not isinstance(expected_adapter, dict):
        raise FreezeError("canonical adapter record is malformed")
    frozen_adapter = frozen_files.get(
        "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
    )
    if not isinstance(frozen_adapter, str) or (
        frozen_adapter.lower() != expected_adapter["sha256"]
    ):
        raise FreezeError("frozen B7 adapter source is not current canonical")
    return {
        "manifest": record(manifest_path),
        "kind": manifest.get("kind"),
        "candidate_commit": source.get("candidate_commit"),
        "selected_build": build_key,
        "cmake_cache": record(cache_path),
        "promotion_candidate_switch": cache_line,
        "full_native_tests": tests,
        "bridge": verify_hashed_file(bridge_path, bridge_row, "bridge DLL"),
        "injector": verify_hashed_file(
            injector_path, injector_row, "bridge injector"
        ),
    }


def verify_paths(
    artifacts: Path, relative_paths: list[str]
) -> dict[str, object]:
    state_dir = Path(str(artifacts) + "_native_state")
    if artifacts.exists() or state_dir.exists():
        raise FreezeError("fresh live artifacts/state path already exists")
    mount_root = state_dir / "profile" / "mod-content" / "zhongguo_361"
    mounted = [mount_root / Path(*relative.split("/")) for relative in relative_paths]
    longest = max(mounted, key=lambda path: len(str(path)))
    maximum = len(str(longest))
    if maximum >= MOUNT_PATH_LIMIT:
        raise FreezeError(
            f"materialized mount path is not below {MOUNT_PATH_LIMIT}: {maximum}"
        )
    return {
        "artifacts": str(artifacts),
        "state_dir": str(state_dir),
        "mount_root": str(mount_root),
        "longest_mounted_path": str(longest),
        "longest_mounted_path_characters": maximum,
        "required_strictly_below": MOUNT_PATH_LIMIT,
        "green": True,
    }


def freeze(args: argparse.Namespace) -> dict[str, object]:
    output = args.output.resolve()
    root = args.canonical_root.resolve()
    artifacts = args.artifacts.resolve()
    source = args.product_source.resolve()
    projection_path = args.projection_manifest.resolve()
    closure_path = args.closure_evidence.resolve()
    manifest_path = args.bridge_manifest.resolve()
    python = args.python.resolve()
    ck3_exe = args.ck3_exe.resolve()
    if output.exists():
        raise FreezeError(f"fresh freeze output already exists: {output}")
    if not source.is_dir():
        raise FreezeError(f"explicit-AND product is missing: {source}")
    if PIPE_TOKEN.fullmatch(args.pipe_token) is None:
        raise FreezeError("pipe token must be exactly 32 lowercase hex characters")

    canonical = verify_canonical_contract(root)
    product = verify_product(source, projection_path, closure_path)
    relative_paths = product.pop("relative_paths")
    assert isinstance(relative_paths, list)
    path_gate = verify_paths(artifacts, relative_paths)
    bridge = verify_bridge_manifest(manifest_path, canonical)
    python_record = record(python)
    ck3_record = record(ck3_exe)
    seed_contract = root / "tools" / "zg361_phase2_seed_contract.json"
    seed_record = record(seed_contract)
    bridge_dll = Path(str(bridge["bridge"]["path"]))
    injector = Path(str(bridge["injector"]["path"]))
    runner = Path(str(canonical["runner"]["path"]))
    pipe = rf"\\.\pipe\xar_ck3_bridge_zg361_{args.pipe_token}"
    base = [
        str(python),
        str(runner),
        "--phase2-promotion-source-checkpoint-live",
        "--phase2-promotion-source-checkpoint-timeout-seconds",
        "1800",
        "--bridge-dll",
        str(bridge_dll),
        "--bridge-injector",
        str(injector),
        "--bridge-pipe",
        pipe,
        "--phase2-seed-contract",
        str(seed_contract),
        "--phase2-product-source",
        str(source),
        "--phase2-product-projection",
        PROJECTION_NAME,
        "--phase2-product-projection-manifest",
        str(projection_path),
        "--phase2-frontend-first-load-save-name",
        "autosave",
        "--phase2-frontend-first-timeout-seconds",
        "180",
    ]
    preflight_argv = [base[0], base[1], "--preflight", *base[2:]]
    environment = os.environ.copy()
    environment["XAR_CK3_EXE"] = str(ck3_exe)
    output.mkdir(parents=True)
    completed = subprocess.run(
        preflight_argv,
        cwd=root,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    log_path = output / "formal-no-launch-preflight.txt"
    log_path.write_text(
        completed.stdout + completed.stderr, encoding="utf-8", newline="\n"
    )
    if (
        completed.returncode != 0
        or "ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN" not in completed.stdout
    ):
        raise FreezeError("canonical runner formal no-launch preflight is RED")
    if artifacts.exists() or Path(str(artifacts) + "_native_state").exists():
        raise FreezeError("preflight unexpectedly created live artifacts/state")

    launch_argv = [
        *base,
        "--artifacts-dir",
        str(artifacts),
        "--discard-userdir",
    ]
    return {
        "schema_version": 1,
        "kind": "zg361_b3_explicit_and_b7_promotion_source_next_run_freeze",
        "status": "READY_NO_LAUNCH",
        "ck3_started": False,
        "canonical": canonical,
        "product": product,
        "bridge_candidate": bridge,
        "provider_capability_verdict": {
            "promotion_compensation": "candidate_enabled",
            "result_case_snapshot": "enabled",
            "runner_requires_both": True,
            "exercised_by_this_focused_run": False,
            "green": True,
        },
        "focused_capture": {
            "mode": "phase2-promotion-source-checkpoint-live",
            "expected_source_transition": (
                "review-now -> zg361pp.146 option 1 -> D+1 zg361pp.147"
            ),
            "expected_output": "one real schema-2 source checkpoint merge input",
            "complete_registry_claimed": False,
            "full_phase2_claimed": False,
        },
        "path_gate": path_gate,
        "inputs": {
            "python": python_record,
            "ck3_exe": ck3_record,
            "seed_contract": seed_record,
        },
        "formal_no_launch_preflight": {
            "argv": preflight_argv,
            "returncode": completed.returncode,
            "green": True,
            "log": record(log_path),
        },
        "launch": {
            "authorized_command_count": 1,
            "executed": False,
            "pipe": pipe,
            "argv": launch_argv,
            "windows_command": subprocess.list2cmdline(launch_argv),
        },
        "claim_boundary": (
            "This freeze authorizes one serial CK3 attempt to capture only the "
            "first real promotion source checkpoint. It does not claim B3, a "
            "complete source registry, full Phase2, T0, or footage completion."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--bridge-manifest", type=Path, required=True)
    parser.add_argument("--product-source", type=Path, required=True)
    parser.add_argument("--projection-manifest", type=Path, required=True)
    parser.add_argument("--closure-evidence", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--pipe-token", required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--ck3-exe", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = freeze(args)
        manifest_path = args.output.resolve() / "next-run-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        digest = sha256(manifest_path)
        (args.output.resolve() / "next-run-manifest.sha256").write_text(
            f"{digest}  next-run-manifest.json\n",
            encoding="ascii",
            newline="\n",
        )
    except (
        FreezeError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"RED: {type(error).__name__}: {error}")
        return 1
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "ck3_started": False,
                "output": str(args.output.resolve()),
                "manifest_sha256": digest,
                "command": manifest["launch"]["windows_command"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
