"""Bind one H3937 paused query to fresh source, native pair and root GO.

The existing no-launch preparation and native build receipt supply the pair.
This entry never allocates an ID, claims a screen, creates GO, or runs a planner.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from . import h3937_cold_observer_once_enable as cold
from . import h3937_stationary_route_contact_query_run as query
from .environment import EnvironmentSpec
from .h3937_run_config import apply_run_config, screen_keeper_for_runner
from .runtime import NativeBridgeLaunchConfig

SCHEMA = "xar.h3937.single-query-run-config.v1"
JOB = "h3937-route-contact-once"
EXTRA_FIELDS = frozenset({
    "native_source_checkout", "native_source_head", "native_build_receipt",
    "native_build_receipt_sha256", "bridge_dll_sha256", "bridge_injector_sha256",
})
GO_OPTIONS = {
    "go_schema": "xar.war.h3937-single-query-once-go.v1",
    "decision": "GO_READ_ONLY_H3937_ROUTE_CONTACT_ONCE",
    "authorized_scope": "one_paused_route_contact_query",
    "maximum_query_actions": 1,
    "cold_load_observer_enabled": False,
}
ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "ck3_autonomous_player/h3937_single_query_once.py"


def _configure(path: Path) -> dict[str, object]:
    config = apply_run_config(cold, path, additional_fields=EXTRA_FIELDS, schema=SCHEMA)
    for name in EXTRA_FIELDS:
        value = config[name]
        if name.endswith("_sha256") and re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
            raise ValueError(f"single-query config has invalid {name}")
    if re.fullmatch(r"[0-9a-f]{40}", config["native_source_head"]) is None:
        raise ValueError("single-query native source HEAD is invalid")
    for name in ("native_source_checkout", "native_build_receipt"):
        if not Path(config[name]).is_absolute():
            raise ValueError(f"single-query {name} must be an absolute path")
    return config


def _build_artifact(value: object) -> Path:
    if not isinstance(value, dict):
        raise ValueError("single-query build artifact is not an object")
    path = Path(str(value.get("path", "")))
    size, digest = value.get("size_bytes"), value.get("sha256")
    if (not path.is_absolute() or type(size) is not int or size <= 0
            or not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None
            or path.stat().st_size != size or cold._sha(path) != digest.upper()):
        raise ValueError("single-query build artifact bytes differ")
    return path


def _native_build(config: dict[str, object]) -> dict[str, object]:
    """Consume the actual sole-builder manifest; never builds or runs a fixture."""
    path = Path(config["native_build_receipt"])
    if cold._sha(path) != config["native_build_receipt_sha256"].upper():
        raise ValueError("single-query native build receipt bytes differ")
    build = cold._read_json(path)
    if not (
        build.get("schema") == "xar.war.h3937.release-pair-noncanonical-diagnostics-static.v1"
        and build.get("status") == "STATIC_GREEN_LIVE_PENDING"
        and build.get("build_status") == "STATIC_READY_NO_CK3_LAUNCH"
        and build.get("source_commit") == config["native_source_head"]
        and isinstance(build.get("source_fingerprint_sha256"), str)
        and re.fullmatch(r"[0-9a-fA-F]{64}", build["source_fingerprint_sha256"]) is not None
        and build.get("configuration") == "Release"
        and build.get("cmake_option") == "XAR_CK3_ENABLE_H3937_PHYSICAL_INVENTORY_MAILBOX_V1=ON"
        and build.get("no_ck3_launch") is True and build.get("screen_acquired") is False
        and build.get("authorization_actions") == 0 and build.get("gameplay_actions") == 0
    ):
        raise ValueError("single-query native build source/options/status differ")
    for name, field in (("dll", "bridge_dll_sha256"), ("injector", "bridge_injector_sha256")):
        _build_artifact(build.get(name))
        if (build[name]["sha256"].upper() != config[field].upper()
                or build.get(name + "_sha256") != build[name]["sha256"]):
            raise ValueError("single-query native build pair differs from config")
    author = cold._read_json(_build_artifact(build.get("author_config")))
    fixture = cold._read_json(_build_artifact(build.get("focused_fixture")))
    review = cold._read_json(_build_artifact(build.get("independent_review")))
    _build_artifact(build.get("source_freeze"))
    fingerprint = build["source_fingerprint_sha256"]
    ctest = build.get("ctest")
    if not (
        author.get("head") == fixture.get("head") == review.get("head") == config["native_source_head"]
        and author.get("native_source_fingerprint_sha256") == fingerprint
        and fixture.get("native_source_fingerprint_sha256") == fingerprint
        and author.get("source_freeze") == build.get("source_freeze")
        and author.get("focused_fixture") == build.get("focused_fixture")
        and author.get("review") == build.get("independent_review")
        and fixture.get("status") == "FOCUSED_NATIVE_FIXTURE_PASS_NO_DLL_BUILD_NO_GAME"
        and fixture.get("passed") == fixture.get("total") == 1
        and fixture.get("ck3_started") is False and fixture.get("mcp_started") is False
        and fixture.get("screen_acquired") is False
        and review.get("status") == "CODE_ONLY_GREEN_NATIVE_DIAGNOSTICS_CONSUMER_ADAPT_SEPARATE"
        and isinstance(ctest, dict) and ctest.get("executed_in_this_full_build") is False
        and ctest.get("same_source_focused_fixture") == build.get("focused_fixture")
        and ctest.get("exit_code") == 0 and ctest.get("passed") == ctest.get("total") == 1
    ):
        raise ValueError("single-query native author/fixture/review binding differs")
    return build


def _preparation(config: dict[str, object]) -> dict[str, object]:
    """Read only the fresh source-matched preparation, without touching CK3."""
    entry = cold._require_entry_blob(ENTRY)
    prep_path = cold.NO_LAUNCH / "preparation.json"
    prep = cold._read_json(prep_path)
    if not (
        prep.get("status") == "READY_NO_LAUNCH_ID_PENDING"
        and prep.get("candidate_head") == entry["head"]
        and Path(str(prep.get("candidate_checkout"))).resolve() == ROOT.resolve()
        and Path(str(prep.get("state_dir"))).resolve() == cold.STATE.resolve()
        and prep.get("bridge_pipe") == cold.PIPE
        and Path(str(prep.get("python"))).resolve() == cold.FROZEN_PYTHON.resolve()
        and prep.get("python_version") == cold.FROZEN_PYTHON_VERSION
        and prep.get("ck3_launch_attempted") is False
        and prep.get("desktop_interaction") is False
    ):
        raise ValueError("single-query preparation differs from its consumer/config")
    native_root = Path(config["native_source_checkout"])
    import subprocess
    native_head = subprocess.check_output(
        ["git", "-C", str(native_root), "rev-parse", "HEAD"], text=True).strip()
    native_dirty = subprocess.check_output(
        ["git", "-C", str(native_root), "status", "--porcelain=v1"], text=True).strip()
    if native_head != config["native_source_head"] or native_dirty:
        raise ValueError("single-query native source differs from its frozen build input")
    build = Path(config["native_build_receipt"])
    native_build = _native_build(config)
    native_tree = subprocess.check_output(
        ["git", "-C", str(native_root), "rev-parse", "HEAD:ck3_autonomous_player/native_bridge"],
        text=True).strip()
    if native_tree != native_build.get("native_bridge_tree"):
        raise ValueError("single-query native tree differs from the actual build")
    for name, key, target, expected in (
        ("xar_ck3_bridge.dll", "dll", cold.DLL, config["bridge_dll_sha256"]),
        ("xar_ck3_bridge_injector.exe", "injector", cold.INJECTOR, config["bridge_injector_sha256"]),
    ):
        source = prep.get("source", {}).get(name)
        if (not isinstance(source, dict) or source.get("sha256", "").upper() != expected.upper()
                or Path(source["source"]).resolve() != Path(native_build[key]["path"]).resolve()
                or cold._sha(target) != expected.upper()
                or cold._sha(Path(source["source"])) != expected.upper()):
            raise ValueError("single-query source-verified native pair differs")
    spec = EnvironmentSpec(state_dir=cold.STATE, game_dir=cold.GAME)
    for name, prepared, expected in (
        ("xar_checkpoint.ck3", spec.profile_dir / "save games/xar_checkpoint.ck3", query.CHECKPOINT_SHA256),
        ("driver-state.json", None, query.RAW_SOURCE_DRIVER_SHA256),
        ("player-child-matrilineal-formal-v1.json", cold.STATE / "player-child-matrilineal-formal-v1.json",
         query.CHILD_PENDING_SIDECAR_SHA256),
    ):
        source = prep.get("source", {}).get(name)
        if (not isinstance(source, dict) or source.get("sha256", "").upper() != expected
                or cold._sha(cold.NO_LAUNCH / "source-verified" / name) != expected
                or cold._sha(Path(source["source"])) != expected
                or (prepared is not None and cold._sha(prepared) != expected)):
            raise ValueError("single-query original frozen H3937 source pair differs")
    preflight_path = Path(prep["preflight_report"])
    rebind_path = Path(prep["rebind_receipt"])
    if (cold._sha(preflight_path) != prep["preflight_report_sha256"]
            or cold._sha(rebind_path) != prep["rebind_receipt_sha256"]):
        raise ValueError("single-query prepared receipts changed")
    preflight = cold._read_json(preflight_path)
    if (preflight.get("ok") is not True or preflight.get("status") != "ready"
            or preflight.get("ck3_launch_attempted") is not False
            or preflight.get("desktop_interaction") is not False):
        raise ValueError("single-query formal native preflight is not ready/no-launch")
    checkpoint = query.validate_cold_start_checkpoint_for_pipe(spec, cold.PIPE)
    prepared_driver = cold.STATE / "native-session/driver-state.json"
    if cold._sha(prepared_driver) != prep["prepared_driver_sha256"]:
        raise ValueError("single-query prepared driver has already been consumed or changed")
    if not query._exact_prepared_rebind(
        cold._read_json(rebind_path), prepared_driver_sha256=prep["prepared_driver_sha256"],
        pipe_name=cold.PIPE, state_dir=cold.STATE, profile_dir=spec.profile_dir,
        environment_sha256=prep["environment_sha256"],
    ) or checkpoint.get("history_index") != 3937 or checkpoint.get("saved_date_raw") != 53219928:
        raise ValueError("single-query exact original H3937 rebind/checkpoint differs")
    query._bind_exact_h3937_ordinary_lifecycle(spec, checkpoint, query._read_driver_state(prepared_driver))
    if cold.OUTPUT.exists():
        raise ValueError("single-query output has already been consumed")
    return {"head": entry["head"], "preparation": prep,
            "preparation_sha256": cold._sha(prep_path),
            "native_build_receipt_sha256": cold._sha(build),
            "preflight_sha256": cold._sha(preflight_path),
            "rebind_sha256": cold._sha(rebind_path)}


def _source_blobs() -> dict[str, str]:
    paths = {"source_module_single_entry": ENTRY, "source_module_single_module": Path(__file__),
             "source_module_single_query_module": Path(query.__file__),
             "source_module_screen_go_module": Path(cold.__file__)}
    paths.update({"source_module_" + name: ROOT / "ck3_autonomous_player/src/xar_autoplayer" /
                  (name.removeprefix(".").replace(".", "/") + ".py")
                  for name in cold.outer._SOURCE_MODULES})
    _head, blobs = cold.outer._clean_checkout_and_blob_identity(paths)
    return blobs


def bind_admission(config: dict[str, object]) -> dict[str, object]:
    ready = _preparation(config)
    sys.path.insert(0, str(ROOT / "tools"))
    import ck3_live_run_id
    identity = ck3_live_run_id.load_live_run_identity(cold.LIVE_RUN_ID, "vanilla")
    if identity.execution_id != cold.LIVE_EXECUTION_ID or identity.sequence != cold.LIVE_SEQUENCE:
        raise ValueError("single-query tuple differs from the root-allocated live identity")
    cold._write_json(cold.LIVE_IDENTITY, identity.to_dict())
    prep = ready["preparation"]
    admission = {
        "schema": "xar.war.h3937-single-query-no-launch-admission.v1",
        "candidate_head": ready["head"], "candidate_checkout": str(ROOT),
        "config_sha256": cold.RUN_CONFIG_SHA256,
        "live_run_id": cold.LIVE_RUN_ID, "live_run_identity_sha256": cold._sha(cold.LIVE_IDENTITY),
        "preparation_sha256": ready["preparation_sha256"],
        "native_source_head": config["native_source_head"],
        "native_build_receipt_sha256": ready["native_build_receipt_sha256"],
        "dll_sha256": config["bridge_dll_sha256"].upper(),
        "injector_sha256": config["bridge_injector_sha256"].upper(),
        "preflight_sha256": ready["preflight_sha256"], "rebind_sha256": ready["rebind_sha256"],
        "source_git_blobs": _source_blobs(),
        "prepared_driver_sha256": prep["prepared_driver_sha256"],
        "environment_sha256": prep["environment_sha256"],
        "maximum_query_actions": 1, "six_read_contracts_completed": 0,
        "live_authorized": False, "ck3_launch_attempted": False,
        "date_move_attack_authorized": False,
    }
    cold._write_json(cold.NO_LAUNCH / "admission.json", admission)
    cold._write_json(cold.NO_LAUNCH / "operator-manifest.json", {
        **admission, "schema": "xar.war.h3937-single-query-operator-manifest.v1",
        "bridge_dll": str(cold.DLL), "bridge_injector": str(cold.INJECTOR),
        "state_dir": str(cold.STATE), "output_dir": str(cold.OUTPUT), "job": JOB,
    })
    return preflight(config)


def preflight(config: dict[str, object]) -> dict[str, object]:
    ready = _preparation(config)
    admission_path = cold.NO_LAUNCH / "admission.json"
    manifest_path = cold.NO_LAUNCH / "operator-manifest.json"
    admission = cold._read_json(admission_path)
    manifest = cold._read_json(manifest_path)
    for name, expected in (
        ("candidate_head", ready["head"]), ("config_sha256", cold.RUN_CONFIG_SHA256),
        ("preparation_sha256", ready["preparation_sha256"]),
        ("native_source_head", config["native_source_head"]),
        ("native_build_receipt_sha256", ready["native_build_receipt_sha256"]),
        ("dll_sha256", config["bridge_dll_sha256"].upper()),
        ("injector_sha256", config["bridge_injector_sha256"].upper()),
        ("source_git_blobs", _source_blobs()), ("maximum_query_actions", 1),
        ("live_authorized", False), ("date_move_attack_authorized", False),
        ("live_run_id", cold.LIVE_RUN_ID),
        ("live_run_identity_sha256", cold._sha(cold.LIVE_IDENTITY)),
        ("preflight_sha256", ready["preflight_sha256"]), ("rebind_sha256", ready["rebind_sha256"]),
    ):
        if admission.get(name) != expected or manifest.get(name) != expected:
            raise ValueError(f"single-query admission/manifest differs: {name}")
    if (admission.get("schema") != "xar.war.h3937-single-query-no-launch-admission.v1"
            or manifest.get("schema") != "xar.war.h3937-single-query-operator-manifest.v1"
            or manifest.get("job") != JOB
            or Path(manifest["bridge_dll"]).resolve() != cold.DLL.resolve()
            or Path(manifest["bridge_injector"]).resolve() != cold.INJECTOR.resolve()):
        raise ValueError("single-query admission/manifest schema or native paths differ")
    return {"status": "READY_NO_LAUNCH", "ok": True, "head": ready["head"],
            "admission_sha256": cold._sha(admission_path), "manifest_sha256": cold._sha(manifest_path),
            "preflight_sha256": ready["preflight_sha256"], "rebind_sha256": ready["rebind_sha256"],
            "live_run_identity_sha256": cold._sha(cold.LIVE_IDENTITY),
            "maximum_query_actions": 1, "six_read_contracts_completed": 0,
            "ck3_launch_attempted": False, "date_move_attack_authorized": False}


def freeze_profile(config: dict[str, object], output: Path, operator_state: Path) -> dict[str, object]:
    identity = preflight(config)
    if not output.is_absolute() or not operator_state.is_absolute():
        raise ValueError("single-query profile and operator state paths must be absolute")
    required = {ENTRY, Path(__file__), cold.RUN_CONFIG_PATH, cold.FROZEN_PYTHON,
                cold.DLL, cold.INJECTOR, Path(config["native_build_receipt"]),
                cold.NO_LAUNCH / "admission.json", cold.NO_LAUNCH / "operator-manifest.json",
                cold.NO_LAUNCH / "preparation.json", ROOT / "tools/process_watchdog.py",
                ROOT / "tools/codex_task_bus.py", ROOT / "tools/build_release.py",
                ROOT / "promo/ck3_native_war_ai/integration/screen_bus_lease.py",
                *ROOT.joinpath("ck3_autonomous_player/src/xar_autoplayer").rglob("*.py")}
    profile = {"schema_version": 1,
               "target": {"id": "h3937-single-" + cold.ROUND,
                          "display_name": "H3937 one paused route-contact query",
                          "expected": {"token_user": "1", "desktop": "WinSta0\\Default",
                                       "machine": "DESKTOP-3FEVHD2"}},
               "endpoint": {"transport": "stdio", "host": "127.0.0.1", "port": 8766},
               "state_directory": str(operator_state),
               "jobs": {JOB: {"command": [str(cold.FROZEN_PYTHON), "-B", str(ENTRY),
                                          "--config", str(cold.RUN_CONFIG_PATH), "--live"],
                              "working_directory": str(ROOT),
                              "exclusive_process_names": list(cold.INVENTORY_IMAGES),
                              "required_paths": [{"path": str(path.resolve()), "kind": "file",
                                                  "size": path.stat().st_size, "sha256": cold._sha(path)}
                                                 for path in sorted(required, key=str)],
                              "absent_paths": [str(cold.OUTPUT), str(cold.STATE / "control/unsafe-cleanup.json")],
                              "controls": {}}}}
    from .operator_mcp import load_operator_profile
    cold._write_json(output, profile)
    load_operator_profile(output)
    return {"profile": str(output), "sha256": cold._sha(output), "admission": identity,
            "job": JOB, "job_started": False, "go_created": False}


def run_once(config: dict[str, object]) -> dict[str, object]:
    identity = preflight(config)
    _go, go_sha = cold._require_go(identity, **GO_OPTIONS)
    cold._require_bus_cli_pair()
    cold._require_zero_live_inventory()
    cold._require_pipe_server_absent()
    owner = cold._require_live_screen_lease()
    cold.OUTPUT.mkdir(parents=True, exist_ok=False)
    (cold.OUTPUT / "run-config.snapshot.json").write_bytes(cold.RUN_CONFIG_BYTES)
    keeper = screen_keeper_for_runner(cold, owner["last_sequence"])
    raw_path = cold.OUTPUT / "raw-query-envelope.json"
    native_raw_path = cold.OUTPUT / "native-query-result.json"
    decoded_path = cold.OUTPUT / "decoded-command-result.json"
    report = None
    error = None
    def query_gate() -> None:
        if keeper.abort.is_set() or cold._sha(cold.GO) != go_sha:
            raise ValueError("single-query root GO/lease changed")
        cold._require_live_screen_lease()
    try:
        keeper.start()
        report = query.query_h3937_stationary_route_contact_once(
            EnvironmentSpec(state_dir=cold.STATE, game_dir=cold.GAME),
            timeout_seconds=1890, readiness_timeout_seconds=1800,
            ownership_round_id=cold.ROUND, cold_start_checkpoint=True,
            native_bridge=NativeBridgeLaunchConfig(mode="native-headless", pipe_name=cold.PIPE,
                                                  dll_path=cold.DLL, injector_path=cold.INJECTOR),
            admitted_pair={"dll_sha256": config["bridge_dll_sha256"],
                           "injector_sha256": config["bridge_injector_sha256"],
                           "admission_sha256": identity["admission_sha256"], "go_sha256": go_sha},
            before_process_create=keeper.process_create_gate,
            managed_stop_event=keeper.abort, query_gate=query_gate,
            raw_query_envelope_path=raw_path,
            native_raw_result_path=native_raw_path,
            decoded_command_result_path=decoded_path,
        )
        cold._write_json(cold.OUTPUT / "query-report.json", report)
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        try:
            keeper.stop()
            cold._write_json(cold.OUTPUT / "screen-lease-keeper.json", keeper.report())
        except BaseException as caught:
            error = error or f"screen keeper cleanup: {type(caught).__name__}: {caught}"
    after = {image: cold._image_inventory(image) for image in cold.INVENTORY_IMAGES}
    gone = all(value["returncode"] == 0 and value["found"] is False for value in after.values())
    ok = (error is None and isinstance(report, dict) and report.get("ok") is True and gone
          and keeper.report().get("failure") is None and cold._sha(cold.GO) == go_sha)
    result = {"schema": "xar.war.h3937-single-query-completion.v1", "ok": ok,
              "status": "GREEN_READ_ONLY_QUERY" if ok else "RED", "error": error,
              "round": cold.ROUND, "live_run_id": cold.LIVE_RUN_ID,
              "report_path": str(cold.OUTPUT / "query-report.json") if report else None,
              "report_sha256": cold._sha(cold.OUTPUT / "query-report.json") if report else None,
              "raw_query_envelope_path": str(raw_path) if raw_path.is_file() else None,
              "raw_query_envelope_sha256": cold._sha(raw_path) if raw_path.is_file() else None,
              "native_query_result_path": str(native_raw_path) if native_raw_path.is_file() else None,
              "native_query_result_sha256": cold._sha(native_raw_path) if native_raw_path.is_file() else None,
              "decoded_command_result_path": str(decoded_path) if decoded_path.is_file() else None,
              "decoded_command_result_sha256": cold._sha(decoded_path) if decoded_path.is_file() else None,
              "process_inventory_after": after, "processes_gone": gone,
              "six_read_contracts_completed": 0, "action_authorized": False,
              "date_advance_authorized": False}
    cold._write_json(cold.OUTPUT / "completion.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--preflight", action="store_true", help="read-only; never launches or consumes output")
    action.add_argument("--live", action="store_true", help="one query only; requires fresh root GO and exclusive screen lease")
    action.add_argument("--bind-admission", action="store_true", help="create-only; uses an already allocated identity")
    action.add_argument("--issue-screen-challenge", action="store_true")
    action.add_argument("--freeze-operator-profile", type=Path)
    parser.add_argument("--operator-state-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        config = _configure(args.config)
        if args.bind_admission:
            result = bind_admission(config)
        elif args.issue_screen_challenge:
            preflight(config)
            result = cold.issue_screen_challenge(ENTRY)
        elif args.freeze_operator_profile:
            if args.operator_state_dir is None:
                raise ValueError("--freeze-operator-profile requires --operator-state-dir")
            result = freeze_profile(config, args.freeze_operator_profile, args.operator_state_dir)
        else:
            result = run_once(config) if args.live else preflight(config)
    except (OSError, ValueError, RuntimeError, query.AgentError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result.get("ok", True) is True else 1
