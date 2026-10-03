"""Finite UI assistance within the original operator's existing custody.

The injected backend only observes the existing process and sends the two
reviewed keys. No launch, attach, SDK, native command, focus activation, lease
claim/renewal, save mutation, game-date parsing, or success grading occurs here.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
import json
from pathlib import Path
import shutil
import time
import uuid

from .evidence import NeedsOperator, append, checked_file, now, require, sha256, write_new
from .pixels import PixelRouter, same_action, same_window


def assist(profile: dict, backend: object, *, execute: bool = False, max_actions: int = 1,
           timeout: float = 60, sleep=time.sleep, clock=time.monotonic) -> dict:
    require(type(max_actions) is int and 1 <= max_actions <= 30 and 0 < timeout <= 600,
            "bounded 1..30 actions and <=600 seconds required")
    require(execute or max_actions == 1, "read-only analysis supports one step")
    require(max_actions <= profile.get("reviewed_max_actions", 1), "configured reviewed budget exceeded")
    root = Path(profile["evidence_directory"])
    root.mkdir(parents=True, exist_ok=True)
    attempt = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:10])
    attempt.mkdir()
    write_new(attempt / "profile.json", profile)
    if profile.get("profile_source"):
        shutil.copyfile(checked_file(profile["profile_source"]), attempt / "profile-input.json")
    result = {"schema": "ck3.stability-ui-attempt.v1", "attempt": str(attempt),
              "run_id": profile["owner"]["run_id"], "mode": "execute" if execute else "read-only",
              "status": "NEEDS_OPERATOR", "steps": [], "business_result": "NOT_VERIFIED",
              "century_credit": "NONE_FROM_UI_ASSIST", "state_truth": "NOT_READ"}
    lock, locked = root / "operator.lock", False
    deadline = clock() + timeout
    journal, ledger = attempt / "journal.jsonl", root / "action-ledger.jsonl"
    try:
        write_new(lock, {"pid": os.getpid(), "attempt": str(attempt), "at_utc": now()})
        locked = True
        backend.guard(profile, initial=True)
        router = PixelRouter(profile["routing"])
        prior = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
        for inherited in profile.get("inherited_ledgers", []):
            source = checked_file(inherited)
            prior.extend(json.loads(line) for line in source.read_text(encoding="utf-8").splitlines())

        def capture(step: Path, label: str, allow_unknown: bool = False) -> tuple[dict | None, dict]:
            before = backend.guard(profile)
            path = step / (label + ".png")
            receipt = backend.capture(path)
            after = backend.guard(profile)
            require(before == after, "owner/process/focus changed during capture")
            require(tuple(receipt["size"]) == tuple(profile["routing"]["frame_size"]), "raw frame size changed")
            require(sha256(path) == receipt["sha256"], "captured bytes changed")
            write_new(step / (label + ".json"), {"capture": receipt, "owner": after})
            try:
                route = router.route(path)
            except NeedsOperator as error:
                write_new(step / (label + "-route.json"), {"refusal": str(error)})
                if allow_unknown:
                    return None, receipt
                raise
            write_new(step / (label + "-route.json"), route)
            return route, receipt

        def budget() -> None:
            require(clock() < deadline, "UI assistance timeout; operator must save/exit normally")
            due = datetime.fromisoformat(profile["normal_save_due_utc"])
            require(datetime.now(timezone.utc) < due, "normal-save deadline reached; no further input")

        for index in range(max_actions):
            budget()
            step = attempt / f"step-{index + 1:02d}"
            step.mkdir()
            first, first_image = capture(step, "before-a")
            while first["kind"] == "MAP_WAIT":
                if not execute or not profile.get("allow_readonly_map_wait", False):
                    result["status"] = "READ_ONLY_MAP_WAIT"
                    break
                budget()
                sleep(min(5, max(0, deadline - clock())))
                label = "wait-" + uuid.uuid4().hex[:8]
                first, first_image = capture(step, label)
            if first["kind"] == "MAP_WAIT":
                break
            sleep(.4)
            second, second_image = capture(step, "before-b")
            require(same_window(first, second), "two-frame window identity unstable")
            require(not any(same_action(second, row["routing_identity"]) for row in prior),
                    "same uncertain action already reserved; operator review required")
            record = {"step": index + 1, "route": second, "before_sha256": second_image["sha256"],
                      "status": "READY_FOR_REVIEW", "business_result": "NOT_VERIFIED"}
            result["steps"].append(record)
            if not execute:
                result["status"] = "READY_FOR_OPERATOR_REVIEW"
                break
            budget()
            backend.guard(profile)
            write_new(step / "intent.json", record)
            append(journal, {"phase": "intent-before-input", **record})
            reserved = {"phase": "reserved-before-uncertain-input", "attempt": str(attempt),
                        "step": index + 1, "routing_identity": second}
            append(ledger, reserved)
            prior.append(reserved)
            ack = backend.send_key(second["action"], profile, step)
            record["ack"] = ack
            append(journal, {"phase": "input-return", "ack": ack, "business_result": "NOT_VERIFIED"})
            sleep(.5)
            after_a, _ = capture(step, "after-a", allow_unknown=True)
            sleep(.3)
            after_b, _ = capture(step, "after-b", allow_unknown=True)
            require(after_a is not None and after_b is not None, "unknown post window; no further input")
            if after_a["kind"] == "MAP_WAIT" and after_b["kind"] == "MAP_WAIT":
                record["status"] = "UI_DISAPPEARED_ROUTING_ONLY"
            else:
                if (after_a["kind"] == "MAP_WAIT" or after_b["kind"] == "MAP_WAIT"
                        or not same_window(after_a, after_b)):
                    record["status"] = "UNCONFIRMED_PENDING_NEXT_STABLE_ROUTE"
                else:
                    require(not same_window(second, after_b) and not same_action(second, after_b),
                            "window/action unchanged; no automatic retry")
                    record["status"] = "UI_TRANSITION_ROUTING_ONLY"
            record["next_input_requires_independent_stable_route"] = True
            result["status"] = record["status"]
            append(journal, {"phase": record["status"], "business_result": "NOT_VERIFIED"})
    except Exception as error:
        result.update(status="NEEDS_OPERATOR", error=f"{type(error).__name__}: {error}")
    finally:
        result["observed_at_utc"] = now()
        write_new(attempt / "result.json", result)
        if locked:
            os.replace(lock, attempt / "closed-operator-lock.json")
    return result
