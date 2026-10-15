"""Query Steam's CK3 Betas UI; switch an exact branch and verify installed bytes.

No Steam configuration is written and no game is launched. The client must
already be in the authorized network mode; this program never changes it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

from steam_versions_core import (SCHEMA, VERSION_PATTERN, VersionError, discover_installation,
    label_branch, observe_installation, resolve_target, sha256_file, utc_now, wait_installed)


class Receipt:
    def __init__(self, path, limit):
        self.path = Path(path).resolve()
        self.limit = limit
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(self.path.parent).free < limit:
            raise VersionError("insufficient free bytes for the declared receipt budget")
        self.path.mkdir(exist_ok=False)
        self.used = 0

    def require_room(self, extra):
        self.used = sum(path.stat().st_size for path in self.path.rglob("*") if path.is_file())
        if self.used + extra > self.limit - 32768:
            raise VersionError("receipt budget exhausted; retain this attempt and use a new admitted budget")

    def emit(self, kind, **fields):
        value = {"at_utc": utc_now(), "kind": kind, **fields}
        raw = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        self.require_room(len(raw))
        with (self.path / "events.jsonl").open("ab") as stream:
            stream.write(raw)
            stream.flush()
        self.used += len(raw)
        if kind != "uia_tree":
            print(json.dumps(value, ensure_ascii=False), flush=True)

    def finish(self, value):
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if self.used + len(raw) > self.limit:
            # A failed wait can have a large last observation in its error;
            # retain that detail in the already-written event stream.
            value = {**value, "error": str(value.get("error", ""))[:4096]}
            raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with (self.path / "result.json").open("xb") as stream:
            stream.write(raw)
        print(json.dumps(value, ensure_ascii=False), flush=True)


def screen_guard(args):
    if args.task_bus:
        if not args.task_id:
            raise VersionError("--task-id is required with --task-bus")
        reply = subprocess.run([sys.executable, "-B", "-X", "utf8", str(args.task_bus), "list"],
                               capture_output=True, timeout=20, check=True)
        payload = json.loads(reply.stdout.decode("utf-8"))
        if payload.get("ok") is not True:
            raise VersionError("task bus list failed")
        owners = [task["task_id"] for task in payload.get("tasks", [])
                  if task.get("state") == "running" and "ck3-screen:acquired" in task.get("resources", [])]
        if owners != [args.task_id]:
            raise VersionError(f"exclusive screen lease is not held by this task: {owners!r}")
    elif not args.exclusive_screen_confirmed:
        raise VersionError("UI actions require a task-bus lease or --exclusive-screen-confirmed on unmanaged machines")


def network_permission(args, ui, receipt):
    observation = ui.network_observation()
    receipt.emit("network_mode_observed", **observation)
    if observation["state"] == "offline":
        raise VersionError("Steam is offline: tool will not take it online; authorize and prepare online mode separately")
    if not args.allow_download:
        raise VersionError("switch requires --allow-download; selecting a branch may replace installed CK3 files")
    if args.network_state != "online" or args.network_evidence is None:
        raise VersionError("online mode requires --network-state online and a fresh reviewed --network-evidence file")
    evidence = args.network_evidence.resolve()
    if not evidence.is_file():
        raise VersionError("network evidence file missing")
    age = datetime.now(timezone.utc).timestamp() - evidence.stat().st_mtime
    if not 0 <= age <= 300:
        raise VersionError("reviewed network evidence must be captured within the last 300 seconds")
    receipt.emit("network_mode_operator_review", state="online", path=str(evidence),
                 sha256=sha256_file(evidence), age_seconds=age,
                 warning="mtime proves neither freshness nor mode; caller must review actual current pixels/state")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("command", choices=["inspect", "list", "switch", "wait"])
    result.add_argument("--steam-dir", type=Path, help="otherwise use STEAM_DIR or Windows Steam registry")
    result.add_argument("--library", type=Path, help="disambiguate multiple installed CK3 libraries")
    result.add_argument("--receipt-dir", type=Path, required=True, help="new directory; never overwrite an attempt")
    result.add_argument("--receipt-budget-bytes", type=int, default=2 * 1024 * 1024)
    result.add_argument("--target", help="exact branch, full display label, unambiguous exact version, or public")
    result.add_argument("--expected-version", help="exact installed launcher rawVersion, independently verified")
    result.add_argument("--expected-build-id", type=int)
    result.add_argument("--timeout-seconds", type=float, default=3600)
    result.add_argument("--poll-seconds", type=float, default=2)
    result.add_argument("--settle-seconds", type=float, default=8)
    result.add_argument("--selectors", type=Path, help="optional exact UIA selectors/localized tab names JSON")
    result.add_argument("--coordinate-mapper", type=Path,
                        help="optional explicit sanctioned mapper script for actual UIA no-effect/unsupported controls")
    result.add_argument("--task-bus", type=Path, help="optional project task bus Python CLI; checked before each action")
    result.add_argument("--task-id")
    result.add_argument("--exclusive-screen-confirmed", action="store_true",
                        help="unmanaged machine only: operator has checked exclusive screen ownership")
    result.add_argument("--account-idle-confirmed", action="store_true",
                        help="operator checked account/other machines are not playing; never evict a session")
    result.add_argument("--allow-download", action="store_true", help="explicit permission for Steam to replace CK3 files")
    result.add_argument("--network-state", choices=["online", "offline", "unknown"], default="unknown")
    result.add_argument("--network-evidence", type=Path, help="fresh directly reviewed online-state evidence; no automatic login")
    return result


def main(argv=None):
    arguments = parser()
    args = arguments.parse_args(argv)
    if any(value <= 0 for value in [args.timeout_seconds, args.poll_seconds, args.settle_seconds]):
        arguments.error("timeouts, poll and settle intervals must be positive")
    if args.poll_seconds > 30:
        arguments.error("--poll-seconds must not exceed 30")
    if args.receipt_budget_bytes < 65536:
        arguments.error("receipt budget must be at least 65536 bytes")
    if args.command in {"switch", "wait"} and not args.target:
        arguments.error("switch/wait require --target")
    receipt = None
    outcome = {"schema": SCHEMA, "command": args.command, "started_at_utc": utc_now(),
               "ok": False, "steam_mode_mutated": False, "game_launched": False,
               "manifest_or_client_config_written": False,
               "restore_offline_required": args.command == "switch" and args.network_state == "online"}
    try:
        receipt = Receipt(args.receipt_dir, args.receipt_budget_bytes)
        receipt.emit("attempt_started", argv=sys.argv[1:] if argv is None else argv)
        installation = discover_installation(args.steam_dir, args.library)
        before = observe_installation(installation)
        receipt.emit("installation_observed", installation=installation, snapshot=before)
        outcome["installation"] = installation
        if args.command == "inspect":
            outcome.update(ok=True, status="local_installation_observed", snapshot=before,
                           available_versions_queried=False)
        elif args.command == "wait":
            # This mode is read-only and can resume a timed-out download. It
            # does not assert that a preceding UI selection ever happened.
            branch = "public" if args.target.casefold() in {"public", "none", "stable"} else label_branch(args.target)
            if branch is None:
                raise VersionError("wait requires an exact branch identity or public, not an unrecognized display label")
            version = args.expected_version or (branch if VERSION_PATTERN.fullmatch(branch) else None)
            final = wait_installed(installation, branch, expected_version=version,
                expected_build=args.expected_build_id, timeout=args.timeout_seconds,
                poll_seconds=args.poll_seconds, settle_seconds=args.settle_seconds, emit=receipt.emit)
            outcome.update(ok=True, status="installed_verified", installed=final, selection_verified=False)
        else:
            from steam_versions_uia import SteamUI, require_no_ck3
            def guard():
                screen_guard(args)
                require_no_ck3()
            guard()
            selectors = json.loads(args.selectors.read_text(encoding="utf-8")) if args.selectors else None
            ui = SteamUI(installation, guard=guard, emit=receipt.emit, selectors=selectors,
                         coordinate_mapper=args.coordinate_mapper, receipt_dir=receipt.path,
                         budget_check=receipt.require_room)
            ui.open_properties()
            branches = ui.list_branches()
            outcome["branches"] = branches
            if args.command == "list":
                outcome.update(ok=True, status="available_branches_observed", installed_verified=False)
            else:
                if not args.account_idle_confirmed:
                    raise VersionError("switch requires current --account-idle-confirmed, including other machines")
                network_permission(args, ui, receipt)
                target = resolve_target(branches["labels"], args.target, rows=branches.get("rows"))
                if args.expected_version:
                    target["expected_version"] = args.expected_version
                receipt.emit("exact_target_resolved", **target)
                selection = ui.choose(target["label"])
                outcome.update(target=target, selection=selection, selection_verified=True)
                final = wait_installed(installation, target["branch"], expected_version=target["expected_version"],
                    expected_build=args.expected_build_id, timeout=args.timeout_seconds,
                    poll_seconds=args.poll_seconds, settle_seconds=args.settle_seconds, emit=receipt.emit)
                outcome.update(ok=True, status="installed_verified", installed=final)
                outcome["restore_offline_required"] = True
                outcome["native_runtime_requalification_required"] = (
                    before["numbers"].get("buildid") != final["numbers"].get("buildid")
                    or before["launcher"] != final["launcher"]
                    or any(before["executable"].get(key) != final["executable"].get(key)
                           for key in ("bytes", "mtime_ns")))
        code = 0
    except Exception as error:
        # UIA COM/element-disconnected exceptions do not share one Python
        # exception base with filesystem/manifest errors. Preserve the same
        # durable incomplete receipt rather than dropping out mid-selection.
        outcome.update(status="blocked_or_incomplete", error_type=type(error).__name__, error=str(error))
        code = 2
    except KeyboardInterrupt:
        outcome.update(status="interrupted_no_rollback", error="Steam may continue downloading; inspect/wait before retrying")
        code = 130
    outcome["completed_at_utc"] = utc_now()
    if receipt:
        receipt.finish(outcome)
    else:
        print(json.dumps(outcome, ensure_ascii=False), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
