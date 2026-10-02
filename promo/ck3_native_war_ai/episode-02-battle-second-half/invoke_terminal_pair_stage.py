"""Run a frozen E2-09 capture argv in a fresh directory, never by shell.

Default prints the selected stage without executing it. The no-launch stage
uses capture_session without --capture. The live stage requires --execute,
a new reviewed Steam offline receipt, and an exclusive screen window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def write_new(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-receipt", type=Path, required=True)
    parser.add_argument("--stage", choices=("no-launch", "live"), required=True)
    parser.add_argument("--offline-receipt", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    frozen = json.loads(args.static_receipt.read_text(encoding="utf-8"))
    require(frozen["status"] == "STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY",
            "static receipt is not selected GREEN")
    for key in ("game", "bridge", "injector", "checkpoint_save", "checkpoint_receipt", "capture_script"):
        source = frozen[key]
        require(sha256(Path(source["path"])) == source["sha256"], f"selected {key} bytes changed")
    if args.stage == "no-launch":
        require(args.offline_receipt is None, "no-launch stage does not use Steam receipt")
        argv = list(frozen["preflight_argv_no_capture_flag"])
        require("--capture" not in argv, "no-launch argv unexpectedly launches CK3")
    else:
        require(args.offline_receipt is not None and args.offline_receipt.is_file(),
                "live stage needs current reviewed Steam offline receipt")
        offline = json.loads(args.offline_receipt.read_text(encoding="utf-8"))
        image = (offline.get("screenshot") or {})
        require(offline.get("current_offline_ui_observed") is True and
                isinstance(image.get("path"), str) and
                sha256(Path(image["path"])) == image.get("sha256"),
                "Steam offline screenshot receipt invalid")
        argv = list(frozen["live_argv_without_fresh_steam_offline_receipt"])
        require(argv[-1] == "--capture", "live argv lacks explicit CK3 capture flag")
        argv += ["--steam-offline-receipt", str(args.offline_receipt.resolve())]
        preflight_dir = Path(frozen["preflight_argv_no_capture_flag"][-1])
        receipt = preflight_dir / "preflight.json"
        require(receipt.is_file(), "first run the distinct no-launch preflight stage")
        checked = json.loads(receipt.read_text(encoding="utf-8"))
        require(checked.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
                checked.get("ck3_started") is False and
                checked.get("bridge_dll", {}).get("sha256") == frozen["bridge"]["sha256"],
                "no-launch preflight did not validate selected current DLL")
    require(argv[0] == frozen["interpreter"], "interpreter changed")
    output = Path(argv[argv.index("--output-dir") + 1])
    stage_root = output.parent
    require(not stage_root.exists(), "stage root already exists; use another append-only attempt")
    if not args.execute:
        print(json.dumps({"mode": "plan-only", "stage": args.stage, "argv": argv}, ensure_ascii=False))
        return
    stage_root.mkdir(parents=True, exist_ok=False)
    write_new(stage_root / "invocation.json", {"stage": args.stage,
              "static_receipt": str(args.static_receipt.resolve()), "argv": argv})
    with (stage_root / "invocation.stdout.txt").open("xb") as stdout, \
            (stage_root / "invocation.stderr.txt").open("xb") as stderr:
        process = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    write_new(stage_root / "invocation-result.json", {"stage": args.stage,
              "returncode": process.returncode,
              "stdout_sha256": sha256(stage_root / "invocation.stdout.txt"),
              "stderr_sha256": sha256(stage_root / "invocation.stderr.txt")})
    print(json.dumps({"stage": args.stage, "returncode": process.returncode,
                      "result": str(stage_root / "invocation-result.json")}))
    if process.returncode != 0:
        raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
