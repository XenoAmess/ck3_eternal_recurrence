"""Exact no-launch byte seal for the E2-06 d11 managed live entry.

Seal and verify are read-only with respect to the original attempt. A lock is
created exclusively in a separate evidence directory. It does not authorize
gameplay, recording, or the one-day action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


CHECKOUT = Path(__file__).resolve().parents[3]
CAPTURE_SCRIPT = Path(__file__).with_name("capture_session.py")
D11_SAVE_SHA = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"
D11_RECEIPT_SHA = "DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCE_ROOT = Path("D:/workspace/ck3_native_war_ai_promo_work/episode01-full-edge-attempt-004")
SAVE = SOURCE_ROOT / "trace-d11-immutable.ck3"
RECEIPT = SOURCE_ROOT / "ck3-output/interactive-requests-responses/trace-d11-save.json"
GUI_ROOT = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-screen-lease-20260928-a04")
GUI_SETTINGS = GUI_ROOT / "native-ui-saved-settings-a01.pdx.txt"
GUI_RECEIPT = GUI_ROOT / "native-ui-saved-settings-a01.json"
VARIABLE_VALUE_FLAGS = ("--state-dir", "--output-dir", "--pipe-name",
                        "--steam-offline-receipt", "--d11-admission-lock",
                        "--screen-task-id", "--screen-expected-sequence",
                        "--screen-cli-sha256")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest().upper()}


def read(path: Path) -> dict[str, Any]:
    row = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(row, dict), f"expected JSON object: {path}")
    return row


def same_path(actual: str, expected: Path, label: str) -> None:
    require(Path(actual).resolve() == expected.resolve(), f"{label} path differs")


def value(argv: list[str], flag: str) -> str:
    require(argv.count(flag) == 1, f"{flag} missing or repeated")
    index = argv.index(flag)
    require(index + 1 < len(argv) and not argv[index + 1].startswith("--"),
            f"{flag} has no value")
    return argv[index + 1]


def current_head() -> str:
    head = subprocess.run(["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(CHECKOUT), "status", "--porcelain",
                            "--untracked-files=no"], check=True, capture_output=True,
                           text=True).stdout
    require(not dirty, "current checkout has tracked changes")
    return head


def no_launch_binding(attempt: Path) -> dict[str, Any]:
    require(attempt.name.startswith("episode02-e2-06-d11-recap-preflight-") and
            attempt.is_dir(), "fresh d11 no-launch attempt required")
    head = current_head()
    paths = {
        "runner": attempt / "run_no_launch.py",
        "argv": attempt / "run-argv.json",
        "result": attempt / "run-result.json",
        "stdout": attempt / "run-stdout.txt",
        "stderr": attempt / "run-stderr.txt",
        "command": attempt / "ck3-output/command.json",
        "preflight": attempt / "ck3-output/preflight.json",
        "static_strings": attempt / "ck3-output/static-capability-strings.json",
        "capture_script": CAPTURE_SCRIPT,
        "admission_script": Path(__file__),
        "save": SAVE,
        "receipt": RECEIPT,
        "gui_settings": GUI_SETTINGS,
        "gui_receipt": GUI_RECEIPT,
    }
    run = read(paths["argv"])
    result = read(paths["result"])
    command = read(paths["command"])
    preflight = read(paths["preflight"])
    argv = run.get("argv")
    require(isinstance(argv, list) and all(isinstance(x, str) for x in argv)
            and len(argv) >= 4, "no-launch argv malformed")
    same_path(argv[1], CAPTURE_SCRIPT, "capture script")
    require(command.get("python") == argv[0] and command.get("argv") == argv[1:],
            "command differs from original argv")
    require("--capture" not in argv and
            argv.count("--enable-private-phase-trace") == 1 and
            argv.count("--import-a04-ui-gui-100") == 1 and
            "--d11-admission-lock" not in argv,
            "no-launch flags differ")
    for flag, path in (("--checkpoint-save", SAVE),
                       ("--checkpoint-receipt", RECEIPT),
                       ("--a04-ui-settings-snapshot", GUI_SETTINGS),
                       ("--a04-ui-preservation-receipt", GUI_RECEIPT),
                       ("--output-dir", attempt / "ck3-output"),
                       ("--state-dir", attempt / "ck3-state")):
        same_path(value(argv, flag), path, flag)
    require(value(argv, "--gui-scale") == "1.0", "GUI scale differs")
    dll = Path(value(argv, "--bridge-dll"))
    injector = Path(value(argv, "--bridge-injector"))
    pair = Path(value(argv, "--battle-control-pair-manifest"))
    paths.update({"dll": dll, "injector": injector, "pair": pair})
    files = {name: identity(path) for name, path in paths.items()}
    require(run.get("capture") is False and run.get("checkout_head") == head and
            run.get("capture_script_sha256") == files["capture_script"]["sha256"] and
            run.get("battle_control_pair_manifest_sha256") == files["pair"]["sha256"],
            "no-launch run is not bound to current checkout/script/pair")
    require(result.get("exit_code") == 0 and result.get("ck3_started_by_command") is False and
            result.get("stdout_sha256") == files["stdout"]["sha256"] and
            result.get("stderr_sha256") == files["stderr"]["sha256"],
            "no-launch result or stdio differs")
    require(preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
            preflight.get("ck3_started") is False and
            preflight.get("runtime_capabilities_verified") is False and
            not (preflight.get("process_inventory") or {}).get("processes"),
            "no-launch preflight is not static READY")
    source = preflight.get("checkpoint_source") or {}
    require(source.get("save") == files["save"] and
            source.get("receipt") == files["receipt"] and
            source.get("actor") == 29829 and source.get("date_raw") == 53146488 and
            files["save"]["sha256"] == D11_SAVE_SHA and
            files["receipt"]["sha256"] == D11_RECEIPT_SHA,
            "d11 save/sidecar source differs")
    require(preflight.get("bridge_dll") == files["dll"] and
            preflight.get("bridge_injector") == files["injector"] and
            (preflight.get("game") or {}).get("sha256") == EXE_SHA,
            "preflight binary pair or game differs")
    gui = preflight.get("a04_ui_gui_source_binding") or {}
    require(gui.get("opt_in") is True and
            gui.get("source_snapshot") == files["gui_settings"] and
            gui.get("preservation_receipt") == files["gui_receipt"] and
            (gui.get("target") or {}).get("track") == "e2-06-d11",
            "preflight GUI source binding differs")
    pair_row = preflight.get("d11_battle_control_pair") or {}
    report_row = pair_row.get("build_report") or {}
    report_path = Path(report_row.get("path", ""))
    files["report"] = identity(report_path)
    require(pair_row.get("manifest") == files["pair"] and
            report_row == files["report"] and
            run.get("candidate_manifest_sha256") == files["report"]["sha256"] and
            pair_row.get("wire_markers_present") is True and
            pair_row.get("private_phase_trace_static_ready") is True and
            pair_row.get("native_query_verified") is False,
            "d11 pair/static trace receipt differs")
    require(run.get("xar_promo_version") and run.get("xar_promo_wheel_sha256") and
            (run.get("open_kaishek_preflight") or {}).get("result") == "not-applicable",
            "toolchain/applicability receipt missing")
    return {"schema": "xar.war-promo.e206-d11-no-launch-admission/v1",
            "checkout_head": head, "attempt": str(attempt.resolve()),
            "run_argv": argv, "files": files, "ck3_started": False,
            "native_query_verified": False}


def seal(attempt: Path, lock: Path) -> dict[str, Any]:
    require(lock.parent.is_dir() and lock.parent.resolve() != attempt.resolve() and
            not lock.exists(), "new external lock path required")
    binding = no_launch_binding(attempt)
    with lock.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(binding, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {"lock": identity(lock), "binding": binding}


def verify_lock(lock: Path) -> dict[str, Any]:
    row = read(lock)
    require(row.get("schema") == "xar.war-promo.e206-d11-no-launch-admission/v1",
            "d11 admission lock schema differs")
    attempt = Path(row.get("attempt", ""))
    require(lock.resolve().parent != attempt.resolve(), "lock must be external")
    current = no_launch_binding(attempt)
    require(row == current, "d11 admission lock differs from current exact bytes")
    return {"lock": identity(lock), "binding": current}


def strip_live_variants(argv: list[str]) -> list[str]:
    result = []
    index = 0
    while index < len(argv):
        item = argv[index]
        if item in VARIABLE_VALUE_FLAGS:
            value(argv, item)
            index += 2
        elif item == "--capture":
            index += 1
        else:
            result.append(item)
            index += 1
    return result


def verify_live_admission(lock: Path | None, argv: list[str]) -> dict[str, Any]:
    require(lock is not None, "d11 live capture requires an admission lock")
    prior = verify_lock(lock)
    live = [sys.executable, str(CAPTURE_SCRIPT), *argv]
    frozen = prior["binding"]["run_argv"]
    require(live.count("--capture") == 1 and
            live.count("--enable-private-phase-trace") == 1 and
            live.count("--d11-admission-lock") == 1,
            "d11 live flags are not explicit and unique")
    same_path(value(live, "--d11-admission-lock"), lock, "admission lock")
    require(strip_live_variants(live) == strip_live_variants(frozen),
            "d11 live argv differs from sealed no-launch options")
    attempt = Path(prior["binding"]["attempt"])
    for name in ("--state-dir", "--output-dir"):
        target = Path(value(live, name)).resolve()
        require(target != Path(value(frozen, name)).resolve() and
                attempt.resolve() not in target.parents,
                f"{name} must use a fresh live root")
    require(value(live, "--pipe-name") != value(frozen, "--pipe-name"),
            "d11 live pipe must be new")
    offline = Path(value(live, "--steam-offline-receipt"))
    require(offline.is_file(), "fresh Steam offline receipt path is missing")
    return {"schema": "xar.war-promo.e206-d11-live-admission/v1",
            "lock": prior["lock"], "no_launch_attempt": prior["binding"]["attempt"],
            "checkout_head": prior["binding"]["checkout_head"],
            "capture_script": prior["binding"]["files"]["capture_script"],
            "dll": prior["binding"]["files"]["dll"],
            "injector": prior["binding"]["files"]["injector"],
            "save": prior["binding"]["files"]["save"],
            "sidecar": prior["binding"]["files"]["receipt"],
            "pair": prior["binding"]["files"]["pair"],
            "recording_authorized": False, "date_action_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("seal", "verify"))
    parser.add_argument("--attempt", type=Path)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "seal":
        require(args.attempt is not None, "seal needs --attempt")
        row = seal(args.attempt, args.lock)
    else:
        require(args.attempt is None, "verify reads attempt path from lock")
        row = verify_lock(args.lock)
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
