"""Root-only episode04 paused sampling queue, with an explicit bounded advance.

Import and --help do not open a driver, SDK, process, screen, or game. Live modes
publish once to the existing bootstrap owner. A mutation is never resubmitted.
"""
import argparse
import hashlib
import math
import subprocess
import time
import uuid
import json
from pathlib import Path
import re
import sys

ASSETS = None
REPO = Path(__file__).resolve().parents[4]
PYTHON = Path(sys.executable)
BOOTSTRAP = Path(__file__).with_name("capture_bootstrap.py")
ACTOR = None
RUN = None
STOP_FILE = None
EXE_SHA = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"


class OperationError(RuntimeError):
    pass

def require(condition, message):
    if not condition:
        raise OperationError(message)

def emit(value):
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")), flush=True)

def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write("\n")

def integer(value, label, minimum=0, maximum=2147483647):
    require(type(value) is int and minimum <= value <= maximum,
            label + " must be an actual bounded integer")
    return value

def validate_schema(value, schema, label="arguments"):
    """Small strict validator for the actual SDK schema (no coercion)."""
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                validate_schema(value, branch, label)
                return
            except OperationError:
                pass
        raise OperationError(label + " does not match any schema branch")
    if "enum" in schema:
        require(any(type(value) is type(v) and value == v for v in schema["enum"]),
                label + " is not an allowed enum value")
    kind = schema.get("type")
    valid = {
        "integer": type(value) is int,
        "number": type(value) in (int, float) and math.isfinite(value),
        "boolean": type(value) is bool,
        "null": value is None,
        "string": type(value) is str,
        "array": type(value) is list,
        "object": type(value) is dict,
    }
    require(kind in valid and valid[kind], label + " has incorrect or unsupported schema type")
    if kind in ("integer", "number"):
        for bound, operator in (("minimum", lambda a, b: a >= b), ("maximum", lambda a, b: a <= b)):
            require(bound not in schema or operator(value, schema[bound]), label + " violates " + bound)
    if kind == "string":
        require("minLength" not in schema or len(value) >= schema["minLength"], label + " is too short")
        require("maxLength" not in schema or len(value) <= schema["maxLength"], label + " is too long")
    if kind == "array":
        for i, item in enumerate(value):
            validate_schema(item, schema.get("items", {}), label + "[" + str(i) + "]")
    if kind == "object":
        properties = schema.get("properties", {})
        require(all(key in value for key in schema.get("required", [])), label + " lacks required fields")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], label + "." + key)
            else:
                # Only explicitly free-form nested objects admit arbitrary fields.
                require(schema.get("additionalProperties") is True, label + " contains unknown field " + key)

def snapshot_guard(snapshot):
    require(type(snapshot) is dict, "snapshot body must be an object")
    require(snapshot.get("map_ready") is True and snapshot.get("paused") is True,
            "fresh snapshot must show paused map")
    actor = snapshot.get("played_character") or {}
    require(type(actor.get("character_id")) is int and actor["character_id"] == ACTOR
            and actor.get("alive") is True, "fresh actor is not living William 33388")
    require(snapshot.get("source") == "injected-dll-named-pipe", "snapshot is not this native backend")
    integer(snapshot.get("revision"), "snapshot revision")
    return snapshot

def wait_stable(path, timeout):
    deadline = time.monotonic() + timeout
    observed = None
    since = None
    last_problem = "response absent"
    while time.monotonic() < deadline:
        try:
            before = path.stat()
            raw = path.read_bytes()
            after = path.stat()
            signature = (raw, after.st_size, after.st_mtime_ns)
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                observed, since = None, None
            elif signature != observed:
                observed, since = signature, time.monotonic()
            elif time.monotonic() - since >= 0.15:
                try:
                    row = json.loads(raw.decode("utf-8-sig"))
                    require(type(row) is dict, "response root is not an object")
                except (UnicodeError, ValueError, OperationError) as error:
                    last_problem = repr(error)
                else:
                    if path.read_bytes() == raw:
                        return raw, row
                    observed, since = None, None
        except OSError as error:
            last_problem = repr(error)
            observed, since = None, None
        time.sleep(0.05)
    raise OperationError("response timeout; DO NOT resubmit this request: " + str(path) + "; " + last_problem)

class Queue:
    def require_running(self):
            require(not (RUN / "bootstrap-result.json").exists(), "native bootstrap already completed")
            require(not STOP_FILE.exists(), "root stop marker present: " + str(STOP_FILE))
            for path in (RUN / "requests").glob("*.json"):
                try:
                    request = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    raise OperationError("unreadable published queue request: " + str(path))
                require(request.get("tool") != "stop", "bootstrap stop request already published")

    def call(self, tool, arguments, phase):
            self.require_running()
            require(tool in self.tools, "tool absent from this actual SDK: " + tool)
            validate_schema(arguments, self.tools[tool]["input_schema"])
            self.sequence += 1
            label = f"{self.sequence:03d}-{phase}"
            request_id = self.args.tag + "-" + f"{self.sequence:03d}" + "-" + uuid.uuid4().hex[:16]
            arguments_file = self.attempt / (label + ".arguments.json")
            write_new(arguments_file, arguments)
            argv = [str(PYTHON), "-B", "-X", "utf8", str(BOOTSTRAP), "request", "--run-dir", str(RUN),
                    "--tool", tool, "--arguments-file", str(arguments_file), "--request-id", request_id]
            response_path = RUN / "responses" / (request_id + ".json")
            request_path = RUN / "requests" / (request_id + ".json")
            record = {"sequence": self.sequence, "phase": phase, "tool": tool, "request_id": request_id,
                      "response_path": str(response_path), "request_path": str(request_path), "argv": argv}
            self.calls.append(record)
            write_new(self.attempt / (label + ".submission.json"), record)
            # One call only. Even nonzero submission may have published a request.
            try:
                result = subprocess.run(argv, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        timeout=30, check=False)
            except subprocess.TimeoutExpired as error:
                (self.attempt / (label + ".stdout.bin")).write_bytes(error.stdout or b"")
                (self.attempt / (label + ".stderr.bin")).write_bytes(error.stderr or b"")
                raise OperationError("submission timeout; request may exist; no resubmit: " + str(request_path))
            (self.attempt / (label + ".stdout.bin")).write_bytes(result.stdout)
            (self.attempt / (label + ".stderr.bin")).write_bytes(result.stderr)
            require(result.returncode == 0, "bootstrap request exited nonzero; no retry; see " + label)
            require(request_path.exists(), "bootstrap returned without exact request file; no retry")
            (self.attempt / (label + ".request.json")).write_bytes(request_path.read_bytes())
            try:
                raw, response = wait_stable(response_path, self.args.timeout)
            except OperationError:
                if response_path.exists():
                    (self.attempt / (label + ".partial-response.bin")).write_bytes(response_path.read_bytes())
                raise
            (self.attempt / (label + ".response.json")).write_bytes(raw)
            require(response.get("request") == {"request_id": request_id, "tool": tool, "arguments": arguments},
                    "response identity does not match this single request")
            write_new(self.attempt / (label + ".receipt.json"), {"request": pin(request_path),
                "response": pin(response_path), "preserved_response": pin(self.attempt / (label + ".response.json")),
                "is_error": response.get("is_error"), "mutation_resubmitted": False})
            if response.get("is_error") is not False:
                emit({"phase": phase, "tool": tool, "is_error": response.get("is_error"),
                      "content": response.get("content"), "full_response": str(self.attempt / (label + ".response.json"))})
                raise OperationError("SDK returned an error; no mutation resubmit")
            body = response.get("body")
            require(type(body) is dict, "SDK response body is not a JSON object; preserved in full")
            emit({"phase": phase, "tool": tool, "request_id": request_id, "status": concise(body),
                  "full_response": str(self.attempt / (label + ".response.json"))})
            return body

    def fresh(self, phase):
            return snapshot_guard(self.call("ck3_take_snapshot", {}, phase))

def concise(body):
    if type(body) is not dict:
        return {"body_type": type(body).__name__}
    return {key: body.get(key) for key in ("snapshot_id", "revision", "native_revision", "date_raw", "paused", "map_ready", "status", "accepted", "player_armies") if key in body}


def load_base():
    return sys.modules[__name__]


def setup(base, args):
    base.ASSETS = args.assets_root.resolve()
    base.require(not base.ASSETS.is_relative_to(REPO.resolve()), "Large process assets must stay outside source repository")
    base.BASE, base.REPO, base.RUN = base.ASSETS, REPO, args.run_dir.resolve()
    base.PYTHON, base.BOOTSTRAP, base.ACTOR = PYTHON, BOOTSTRAP, args.actor_id
    base.STOP_FILE = args.run_dir / "root-native-operation.stop"
    base.require(Path(sys.executable).resolve() == PYTHON.resolve(), "Explicit verified main venv required")
    base.require(base.pin(BOOTSTRAP)["sha256"] == args.bootstrap_sha256.lower(), "Reviewed bootstrap changed")
    base.require(base.RUN.is_relative_to(ASSETS.resolve()), "Actual SDK run must be in new episode04 assets root")
    base.require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", args.tag) is not None, "Invalid unique sample tag")
    base.require(1 <= args.timeout <= 600, "Bounded response timeout required")
    ready = json.loads((base.RUN / "sdk-ready.json").read_text(encoding="utf-8"))
    runtime = ready.get("runtime_identity") or {}
    base.require(Path(runtime.get("bootstrap_file", "")).resolve() == BOOTSTRAP.resolve(), "SDK belongs to another bootstrap")
    base.require(Path(runtime.get("sys_executable", "")).resolve() == PYTHON.resolve(), "SDK interpreter differs")
    base.require(ready.get("pipe_name") == args.pipe_name, "Actual SDK pipe differs")
    sdk = json.loads((base.RUN / "sdk-tools.json").read_text(encoding="utf-8"))
    queue = object.__new__(base.Queue)
    queue.tools = {tool["name"]: tool for tool in sdk["tools"]}
    queue.attempt = args.output_dir.resolve() / args.tag
    base.require(queue.attempt.is_relative_to(ASSETS.resolve()), "Sample output escaped new assets root")
    queue.attempt.parent.mkdir(parents=True, exist_ok=True)
    queue.attempt.mkdir(exist_ok=False)
    queue.args, queue.sequence, queue.calls = args, 0, []
    base.write_new(queue.attempt / "context.json", {
        "source": base.pin(__file__), "queue_implementation_origin": "Episode03 preserved single-publication helper; portable copy removes external legacy runtime dependency",
        "bootstrap": base.pin(BOOTSTRAP), "run": str(base.RUN), "repo": str(REPO), "pipe_name": args.pipe_name,
        "actor_id": args.actor_id, "initial_expected_date_raw": args.expected_date_raw,
        "sdk_ready": base.pin(base.RUN / "sdk-ready.json"), "sdk_tools": base.pin(base.RUN / "sdk-tools.json"),
        "interpreter": str(PYTHON), "command_argv": sys.argv,
        "operations_require_root": True, "game_outcome_certified": False,
        "open_kaishek": {"status": "not-applicable", "reason": "Native SDK DTO/cached getters and explicit production clock steps; no mod-script corpus semantics"}})
    return queue


def map_guard(base, snapshot, actor, expected_date=None):
    base.snapshot_guard(snapshot)
    base.require((snapshot.get("played_character") or {}).get("character_id") == actor, "Sample actor mismatch")
    base.integer(snapshot.get("date_raw"), "snapshot date_raw")
    if expected_date is not None:
        base.require(snapshot["date_raw"] == expected_date, "Starting actual date differs from frozen condition")
    return snapshot


def roster(base, snapshot):
    rows = snapshot.get("player_armies")
    base.require(type(rows) is list and rows, "Actual player armies absent")
    ids = [base.integer(row.get("army_id"), "public CUnit army_id") for row in rows]
    base.require(len(ids) == len(set(ids)), "Duplicate actual player army ID")
    return ids


def same_frame(base, before, after):
    for key in ("date_raw", "map_ready", "paused", "played_character"):
        base.require(before.get(key) == after.get(key), "Paused frame identity changed at " + key)
    base.require(roster(base, before) == roster(base, after), "Paused army roster changed")


def sample(base, queue, args, label, expected_date=None):
    before = map_guard(base, queue.call("ck3_take_snapshot", {}, label + "-before"), args.actor_id, expected_date)
    ids = roster(base, before)
    health = queue.call("ck3_query_army_strengths", {"army_ids": ids, "expected_revision": before["revision"]}, label + "-health")
    source = health.get("source") or {}
    # Null game-version/EXE fields in this production leaf stay null. Root's
    # frozen prepared/runtime manifest supplies build identity separately.
    for key in ("snapshot_id", "revision", "native_revision", "date_raw", "paused"):
        base.require(source.get(key) == before.get(key), "Health query source frame differs at " + key)
    rows = health.get("army_strengths")
    base.require(type(rows) is list and [row.get("army_id") for row in rows] == ids, "Health rows not bound to requested actual roster")
    after = map_guard(base, queue.call("ck3_take_snapshot", {}, label + "-after-health"), args.actor_id)
    same_frame(base, before, after)
    cash = None
    if args.include_cash:
        cash = queue.call("ck3_query_war_cash_current_resources_private_v1", {"expected_revision": after["revision"]}, label + "-cash")
        final = map_guard(base, queue.call("ck3_take_snapshot", {}, label + "-after-cash"), args.actor_id)
        same_frame(base, before, final)
        after = final
    record = {"sample": label, "date_raw": before["date_raw"], "snapshot_id": before.get("snapshot_id"),
              "initial_public_revision": before["revision"], "after_public_revision": after["revision"],
              "native_revision": before.get("native_revision"), "actor_id": args.actor_id,
              "army_ids": ids, "army_roster": before["player_armies"], "army_health": rows,
              "health_status": health.get("status"), "health_source": source, "cash_response": cash,
              "active_event": before.get("active_event"), "pending_character_interaction": before.get("pending_character_interaction"),
              "cost_scope": "actor-global snapshot, not allocated to ArmyID; no fabricated embark payment",
              "casualty_causality": "soldier differences are net changes; attribution requires independent experiment",
              "supplementary_build_sha256": EXE_SHA, "leaf_null_build_fields_preserved": True,
              "actual_daily_tick_claim": False, "human_approval": False}
    base.write_new(queue.attempt / (label + ".json"), record)
    with (queue.attempt / "sample-timeline.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
    return after, record


def boundary(base, snapshot):
    base.require("active_event" in snapshot and "pending_character_interaction" in snapshot, "Event/interaction state absent")
    if snapshot["active_event"] is not None or snapshot["pending_character_interaction"] is not None:
        return "event-or-interaction"
    for army in snapshot["player_armies"]:
        base.require(type(army.get("in_combat")) is bool and type(army.get("retreating")) is bool, "Combat state unobservable")
        if army["in_combat"] or army["retreating"]:
            return "combat-or-retreat"
    return None


def run(base, queue, args):
    current, first = sample(base, queue, args, "000", args.expected_date_raw)
    if args.command == "sample":
        return {"status": "OBSERVED_PAUSED", "samples": 1, "final_date_raw": current["date_raw"]}
    base.require(1 <= args.count <= 90, "At most90 explicit advance steps")
    caps = queue.call("ck3_get_capabilities", {}, "capabilities")
    base.require("life-advance" in (caps.get("action_steps") or []), "Current SDK backend lacks life-advance")
    baseline_ids = roster(base, current)
    raw_start = current["date_raw"]
    increments = []
    reason = "bounded-request-count"
    for index in range(1, args.count + 1):
        reason = boundary(base, current)
        if reason:
            break
        date_before = current["date_raw"]
        response = queue.call("ck3_execute_step", {"step": "life-advance", "expected_revision": current["revision"]}, f"{index:03}-advance")
        current, observed = sample(base, queue, args, f"{index:03}")
        delta = current["date_raw"] - date_before
        increments.append(delta)
        # This legacy step has previously advanced8 or11 days. Do not silently
        # label it daily: preserve final observation and stop on any mismatch.
        if delta != args.expected_day_raw_units:
            return {"status": "RED_DAY_INCREMENT", "stop": "actual-step-increment-differs", "raw_start": raw_start,
                    "final_date_raw": current["date_raw"], "actual_increments_raw": increments,
                    "expected_day_raw_units": args.expected_day_raw_units, "samples": 1 + len(increments),
                    "one_day_validated": False, "rollback_or_retry_attempted": False}
        if roster(base, current) != baseline_ids:
            reason = "army-roster-changed"
            break
        if response.get("ordinary_events"):
            reason = "ordinary-event-processed"
            break
    else:
        reason = "bounded-request-count"
    return {"status": "BOUNDED_OBSERVED", "stop": reason, "raw_start": raw_start,
            "final_date_raw": current["date_raw"], "actual_increments_raw": increments,
            "expected_day_raw_units": args.expected_day_raw_units, "samples": 1 + len(increments),
            "daily_calendar_mapping_scope": "root-reviewed same-year raw anchor only; no new complete calendar formatter",
            "causal_supply_or_casualty_claim": False}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("sample", "advance-samples"))
    p.add_argument("--assets-root", required=True, type=Path)
    p.add_argument("--run-dir", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--pipe-name", required=True)
    p.add_argument("--actor-id", required=True, type=int)
    p.add_argument("--expected-date-raw", required=True, type=int)
    p.add_argument("--bootstrap-sha256", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--timeout", type=float, default=180)
    p.add_argument("--include-cash", action="store_true")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--expected-day-raw-units", type=int, default=24)
    return p


def main():
    args = parser().parse_args()
    base = load_base()
    queue = None
    try:
        queue = setup(base, args)
        result = run(base, queue, args)
        result.update({"attempt": str(queue.attempt), "request_count": len(queue.calls), "mutation_resubmitted": False,
                       "game_outcome_certified": False, "human_approval": False})
        base.write_new(queue.attempt / "result.json", result)
        base.emit(result)
        return 1 if result["status"].startswith("RED") else 0
    except Exception as error:
        result = {"status": "RED_RETAINED", "error": repr(error), "mutation_resubmitted": False,
                  "instruction": "Inspect exact preserved request/response; no mutation retry or rollback"}
        if queue is not None:
            base.write_new(queue.attempt / "failure.json", {**result, "request_count": len(queue.calls)})
        base.emit(result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
