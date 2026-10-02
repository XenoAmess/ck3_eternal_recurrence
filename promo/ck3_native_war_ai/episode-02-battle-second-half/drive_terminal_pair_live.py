"""Bounded day-27 terminal observer for a *new* managed E2-09 capture session.

Default is a read-only plan. --execute sends requests to the already-running
capture_session hot service; it does not launch CK3 or record the desktop. A
separate raw recorder and screen lease are required for film footage.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import traceback


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper()}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--ready-seconds", type=int, default=600)
    parser.add_argument("--request-seconds", type=int, default=150)
    parser.add_argument("--total-seconds", type=int, default=1800)
    parser.add_argument("--max-day", type=int, default=36)
    args = parser.parse_args()
    require(30 <= args.ready_seconds <= 900 and 30 <= args.request_seconds <= 180 and
            60 <= args.total_seconds <= 2100 and 32 <= args.max_day <= 36, "bounded timers/day invalid")
    frozen = json.loads(args.static_receipt.read_text(encoding="utf-8"))
    require(frozen["status"] == "STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY",
            "selected static receipt is not GREEN")
    if not args.execute:
        print(json.dumps({"mode": "plan-only-no-CK3-access", "run_root": str(args.run_root),
                          "source_save_sha256": frozen["checkpoint_save"]["sha256"],
                          "bridge_sha256": frozen["bridge"]["sha256"],
                          "max_day": args.max_day, "total_seconds": args.total_seconds}))
        return

    expected_root = Path(frozen["live_argv_without_fresh_steam_offline_receipt"][-2]).parent
    # The prepared argv ends with --output-dir PATH --capture. Require exact
    # new live root, so this driver can never write to historical attempt-024.
    require(args.run_root.resolve() == expected_root.resolve(), "run root differs from frozen live plan")
    output = args.run_root / "ck3-output"
    preflight_path = output / "preflight.json"
    require(preflight_path.is_file(), "managed live preflight absent")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    require(preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
            preflight.get("bridge_dll", {}).get("sha256") == frozen["bridge"]["sha256"] and
            preflight.get("bridge_injector", {}).get("sha256") == frozen["injector"]["sha256"] and
            preflight.get("game", {}).get("sha256") == frozen["game"]["sha256"] and
            preflight.get("checkpoint_source", {}).get("save", {}).get("sha256") ==
            frozen["checkpoint_save"]["sha256"], "live preflight identity differs from static plan")
    require((output / "command.json").is_file(), "managed capture command missing")
    events = args.run_root / "terminal-pair-driver-events.jsonl"
    result_path = args.run_root / "terminal-pair-driver-result.json"
    require(not events.exists() and not result_path.exists(), "driver attempt files already exist")
    requests = output / "interactive-requests"
    responses = output / "interactive-requests-responses"
    began = time.monotonic()
    deadline = began + args.total_seconds
    result: dict = {"schema": "ck3.episode02.terminal-pair-driver.v1", "status": "started",
                    "created_utc": utc_now(), "static_receipt": identity(args.static_receipt),
                    "live_preflight": identity(preflight_path), "days": []}

    with events.open("x", encoding="utf-8", newline="\n") as journal:
        def emit(kind: str, **data: object) -> None:
            journal.write(json.dumps({"kind": kind, "at_utc": utc_now(),
                                      "monotonic_ns": time.monotonic_ns(), **data},
                                     ensure_ascii=False) + "\n")
            journal.flush()

        def call(label: str, tool: str, arguments: dict | None = None) -> tuple[dict, dict]:
            require(time.monotonic() < deadline, "total driver deadline elapsed")
            request = requests / f"{label}.json"
            response = responses / f"{label}.json"
            temporary = output / f"{label}.pending"
            require(not request.exists() and not response.exists() and not temporary.exists(),
                    f"request label already used: {label}")
            with temporary.open("x", encoding="utf-8") as stream:
                json.dump({"action": "mcp", "tool": tool, "arguments": arguments or {}}, stream)
                stream.write("\n")
            emit("mcp_submit", label=label, tool=tool)
            os.replace(temporary, request)
            until = min(deadline, time.monotonic() + args.request_seconds)
            while time.monotonic() < until:
                if response.exists():
                    try:
                        row = json.loads(response.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        time.sleep(0.2)
                        continue
                    receipt = identity(response)
                    emit("mcp_response", label=label, result=row.get("result"),
                         response_sha256=receipt["sha256"])
                    require(row.get("result") == "CALL_COMPLETED" and isinstance(row.get("body"), dict),
                            f"native MCP request failed: {label}")
                    return row["body"], receipt
                time.sleep(0.2)
            raise TimeoutError(label)

        try:
            ready_until = min(deadline, time.monotonic() + args.ready_seconds)
            while time.monotonic() < ready_until and not (requests.is_dir() and responses.is_dir()):
                time.sleep(0.5)
            require(requests.is_dir() and responses.is_dir(), "interactive service never became ready")
            emit("driver_ready")
            for day in range(27, args.max_day + 1):
                prefix = f"e2t-d{day:02d}"
                snapshot, snapshot_receipt = call(prefix + "-snapshot", "ck3_take_snapshot")
                require(snapshot.get("paused") is True and snapshot.get("map_ready") is True,
                        f"day {day} map not paused/ready")
                expected_date = frozen["checkpoint_date_raw"] + 24 * (day - 27)
                require(snapshot.get("date_raw") == expected_date, f"day {day} source date drifted")
                revision = snapshot.get("revision")
                require(type(revision) is int, "snapshot revision missing")
                current: dict = {"day_index": day, "date_raw": expected_date,
                                 "snapshot_revision": revision,
                                 "snapshot_receipt_sha256": snapshot_receipt["sha256"]}
                if day <= 31:
                    body, receipt = call(prefix + "-control", "ck3_query_battle_control_snapshot_v1",
                                         {"subject_army_id": 18, "expected_revision": revision})
                    control = body.get("battle_control_snapshot") or {}
                    require(control.get("status") == "available" and
                            control.get("combat_id") == frozen["expected_combat_id"],
                            f"day {day} combat control identity unavailable")
                    current.update({"control_receipt_sha256": receipt["sha256"],
                                    "battle_phase": control.get("phase"),
                                    "winner_raw": control.get("winner_raw")})
                    revision = body.get("queried_revision")
                else:
                    body, receipt = call(prefix + "-terminal", "ck3_query_battle_terminal_transition_v1",
                                         {"prior_combat_id": frozen["expected_combat_id"],
                                          "subject_public_cunit_id": 18, "expected_revision": revision})
                    terminal = body.get("battle_terminal_transition") or {}
                    prior = terminal.get("prior") or {}
                    current.update({"terminal_receipt_sha256": receipt["sha256"],
                                    "terminal_kind": prior.get("terminal_kind"),
                                    "hard_loss_inputs": prior.get("hard_loss_inputs"),
                                    "battle_warscore": prior.get("battle_warscore")})
                    revision = body.get("queried_revision")
                    if current["terminal_kind"] in ("normal_result", "no_normal_result"):
                        result["days"].append(current)
                        score = current["battle_warscore"] or {}
                        denominator = score.get("denominator_inputs") or {}
                        participants = denominator.get("participants") or []
                        require(current["terminal_kind"] == "normal_result" and
                                isinstance(current["hard_loss_inputs"], dict) and
                                type(current["hard_loss_inputs"].get("hard_loss_raw")) is int and
                                score.get("status") == "recorded" and
                                score.get("war_id") == frozen["expected_war_id"] and
                                type(score.get("value_raw_q100000")) is int and
                                type(score.get("attacker_relative_delta_raw_q100000")) is int and
                                type(denominator.get("after_minimum_int32")) is int and
                                isinstance(participants, list) and bool(participants) and
                                all(isinstance(row, dict) and
                                    len(row.get("buckets_native_add_order_int32", [])) == 8
                                    for row in participants) and
                                type(score.get("selected_cb_battle_scale_raw_q100000")) is int,
                                "terminal captured but E2-09 native writer inputs incomplete")
                        result["status"] = "new-run-native-writer-inputs-captured-not-yet-projected"
                        break
                require(day < args.max_day, "bounded day limit reached without normal terminal")
                require(type(revision) is int, "queried revision missing")
                advance, advance_receipt = call(prefix + "-advance", "ck3_execute_step",
                                                {"step": "life-advance", "expected_revision": revision})
                require(advance.get("starting_date_raw") == expected_date and
                        advance.get("ending_date_raw") == expected_date + 24,
                        f"day {day} life advance did not move one native day")
                current["advance_receipt_sha256"] = advance_receipt["sha256"]
                result["days"].append(current)
                emit("advanced_exactly_one_day", day=day, date_raw=expected_date + 24)
            else:
                raise ValueError("terminal not captured within bounded replay")
        except Exception:
            result["status"] = "red-preserved"
            result["error"] = traceback.format_exc()
            emit("driver_red", error=result["error"])
            raise
        finally:
            result["finished_utc"] = utc_now()
            result["events"] = identity(events)
            write_new(result_path, result)
    print(json.dumps({"status": result["status"], "days": len(result["days"]),
                      "result": str(result_path)}))


if __name__ == "__main__":
    main()
