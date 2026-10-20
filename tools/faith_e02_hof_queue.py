"""Finite R19 HoF observation and one durable original Confirm; no game bypass."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

# The standalone CLI can use the adjacent reviewed source without an installed
# SDK or importing bridge.__init__ (which loads gameplay implementations).
_SDK_SOURCE = Path(__file__).resolve().parents[1] / "ck3_autonomous_player" / "src"
if str(_SDK_SOURCE) not in sys.path:
    sys.path.insert(0, str(_SDK_SOURCE))
from xar_autoplayer.selected_decision_terms_v1 import (
    FilePinV1, HofQuoteTermsV1, file_pin_v1, hof_quote_claim_v1,
    hof_quote_terms_v1, is_json_object, json_array, json_object,
    require as require,
    selected_parameter_context_verified_v1 as selected_parameter_context_verified_v1,
    strict_integer,
)

DECISION = "create_hof_decision"
QUERY = "ck3_query_ingame_decision_item_v1"
CONFIRM = "ck3_confirm_ingame_decision_outcome_v1"
EVENT_CONTEXT = "ck3_query_current_event_window_context_v1"
EVENT_SELECT = "ck3_select_event_option"
READS = frozenset({"ck3_take_snapshot", "ck3_get_capabilities",
    "ck3_query_player_religion_context_v1", "ck3_query_player_rite_governance_v1",
    "ck3_query_player_holy_site_v1", "ck3_inspect_gui_window_tree_v1", QUERY, EVENT_CONTEXT})
FilePath = str | os.PathLike[str]


def pin(path: FilePath) -> FilePinV1:
    resolved = Path(path).resolve()
    data = resolved.read_bytes()
    return {"path": str(resolved), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_pin(ref: object) -> dict[str, object]:
    checked = file_pin_v1(ref)
    require(pin(checked["path"]) == checked, "HoF original receipt changed")
    decoded: object = json.loads(Path(checked["path"]).read_text(encoding="utf-8-sig"))
    return json_object(decoded, "HoF original receipt must contain a JSON object")


def quote_terms(row: object, actor: int, date_raw: int) -> HofQuoteTermsV1:
    return hof_quote_terms_v1(row, actor, date_raw)


def verify_quote_pair(claim: object) -> list[HofQuoteTermsV1]:
    checked = hof_quote_claim_v1(claim)
    values: list[HofQuoteTermsV1] = []
    for ref in checked["quote_receipts"]:
        packet = read_pin(ref)
        rows = json_array(packet.get("rows"), "HoF quote receipt must contain one actual query")
        require(len(rows) == 1, "HoF quote receipt must contain one actual query")
        values.append(quote_terms(rows[0], checked["actor"], checked["date_raw"]))
    # The wire is preserved, including unknown fields and missing vs null.
    first = json_object(values[0], "HoF original quote must remain an object")
    second = json_object(values[1], "HoF original quote must remain an object")
    for field in ("resource_quote", "requirements_description", "cost_description",
                  "context_adapter", "named_parameter_count", "stock_default_parameter"):
        require(first.get(field) == second.get(field), "HoF actual quotes changed: " + field)
    return values


def validate(
    plan: object, *, claim_path: FilePath | None = None,
    event_path: FilePath | None = None,
) -> dict[str, bool]:
    p = json_object(plan, "HoF finite plan must have 1..8 steps")
    steps = json_array(p.get("steps"), "HoF finite plan must have 1..8 steps")
    require(set(p) == {"steps"} and 1 <= len(steps) <= 8, "HoF finite plan must have 1..8 steps")
    ids: list[str] = []
    for raw in steps:
        step = json_object(raw, "HoF rejects raw, day, save, stale, lifecycle or unbounded operations")
        step_id = step.get("id")
        require(set(step) <= {"id", "kind", "tool", "args", "fresh_revision", "continue_on_error"}
            and step.get("kind", "tool") == "tool" and step.get("continue_on_error") is True
            and step.get("fresh_revision") is True and isinstance(step_id, str),
            "HoF rejects raw, day, save, stale, lifecycle or unbounded operations")
        if not isinstance(step_id, str):
            raise ValueError("HoF finite step identity must be a string")
        ids.append(step_id)
        args = json_object(step.get("args", {}), "HoF args must be an object")
        tool = step.get("tool")
        if "expected_revision" in args:
            revision = strict_integer(args["expected_revision"], "HoF revision must be an actual positive integer")
            require(revision > 0, "HoF revision must be an actual positive integer")
        allowed = {"expected_revision"}
        if tool in {QUERY, "ck3_select_ingame_decision_item_v1"}:
            allowed.add("decision_key")
            require(args.get("decision_key") == DECISION, "HoF decision key differs")
        elif tool == EVENT_CONTEXT:
            allowed.add("event_instance_id")
            require(strict_integer(args.get("event_instance_id"), "HoF needs the actual current event instance") > 0,
                    "HoF needs the actual current event instance")
        elif tool == EVENT_SELECT:
            allowed.update({"event_instance_id", "option_number"})
            if event_path is None or len(steps) != 1:
                raise ValueError("HoF first-option choice needs its actual context claim")
            decoded: object = json.loads(Path(event_path).read_text(encoding="utf-8-sig"))
            instance, number = first_event_option(decoded)
            require(type(args.get("event_instance_id")) is int and args["event_instance_id"] == instance
                and type(args.get("option_number")) is int and args["option_number"] == number,
                "HoF rejects a guessed or non-first event option")
        elif tool == CONFIRM:
            allowed.update({"decision_key", "expected_outcome"})
            if claim_path is None or len(steps) != 1 or args.get("decision_key") != DECISION or args.get("expected_outcome") != "decision_closed":
                raise ValueError("HoF Confirm needs its durable claim and exact closed outcome")
            decoded = json.loads(Path(claim_path).read_text(encoding="utf-8-sig"))
            verify_quote_pair(decoded)
        elif tool == "ck3_inspect_gui_window_tree_v1":
            allowed.add("window_kind")
            require(args.get("window_kind") in {"decisions", "decision_detail"}, "HoF finite window differs")
        elif tool == "ck3_query_player_holy_site_v1":
            allowed.add("holy_site_id")
            require(type(args.get("holy_site_id")) is int and args["holy_site_id"] == 32, "R19 only reads its adopted Nadjaf site")
        elif tool == "ck3_take_snapshot":
            allowed.add("include_native_command_history")
            require(args.get("include_native_command_history", False) is False, "HoF omits command history")
        elif tool == "ck3_open_ingame_decisions_v1":
            pass
        else:
            require(isinstance(tool, str) and tool in READS, "HoF tool is outside the finite scope: " + str(tool))
        require(set(args) <= allowed, "HoF args include an unlisted actor, pointer or operation")
    require(len(ids) == len(set(ids)), "HoF step identity reused")
    return {"capture_policy_validated": True, "native_legality_or_success_inferred": False}


def first_event_option(claim: object) -> tuple[int, int]:
    c = json_object(claim, "HoF event claim identity differs")
    require(c.get("schema") == "faith-e02-R19-first-event-claim-v1", "HoF event claim identity differs")
    frame = json_object(c.get("frame"), "HoF event frame missing")
    packet = read_pin(c.get("query_receipt"))
    rows = json_array(packet.get("rows"), "HoF actual event query receipt missing")
    require(len(rows) == 1, "HoF actual event query receipt missing")
    row = json_object(rows[0], "HoF event query failed")
    require(row.get("ok") is True and not row.get("error"), "HoF event query failed")
    value = json_object(row.get("result"), "HoF event query result missing")
    typed = json_object(value.get("current_event_window_context", {}), "HoF native event context missing")
    active = json_object(frame.get("active_event"), "HoF actual active event missing")
    instance = strict_integer(active.get("instance_id"), "HoF actual event instance must be an integer")
    definition = typed.get("event_definition_key")
    readiness = json_object(typed.get("readiness", {}), "HoF actual event readiness missing")
    require(instance > 0 and value.get("accepted") is True and value.get("current_event_window_context_ready") is True
        and typed.get("schema") == "current-event-window-context-v1" and typed.get("status") == "available"
        and type(typed.get("current_event_instance_id")) is int and typed["current_event_instance_id"] == instance
        and type(typed.get("date_raw")) is int and typed.get("date_raw") == frame.get("date_raw")
        and type(typed.get("snapshot_revision")) is int and typed.get("snapshot_revision") == frame.get("native_revision")
        and isinstance(definition, str) and bool(definition) and readiness.get("option_presentation_ready") is True,
        "HoF native current event definition/options not qualified")
    options = [json_object(o, "HoF actual rendered option order missing")
               for o in json_array(typed.get("options"), "HoF actual rendered option order missing")]
    require(1 <= len(options) <= 64 and all(type(o.get("rendered_index")) is int and o["rendered_index"] == i for i, o in enumerate(options)),
        "HoF actual rendered option order missing")
    first = options[0]
    index = strict_integer(first.get("native_option_index"), "HoF first native option index missing")
    frame_options = [json_object(o, "HoF actual event frame option missing")
                     for o in json_array(active.get("options", []), "HoF actual event options missing")]
    require(first.get("shown") is True and first.get("enabled") is True and index >= 0
        and any(type(o.get("option_number")) is int and o["option_number"] == index + 1 and o.get("enabled") is True for o in frame_options),
        "HoF native first displayed option disabled or inconsistent")
    return instance, index + 1


def admit_event_choice(plan: object, path: FilePath) -> Path:
    validate(plan, event_path=path)
    marker = Path(path).with_suffix(".submit-once.json")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"claim": pin(path), "unknown_must_not_repeat": True}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return marker


def admit_confirm(plan: object, claim_path: FilePath) -> Path:
    validate(plan, claim_path=claim_path)
    path = Path(claim_path).resolve()
    decoded: object = json.loads(path.read_text(encoding="utf-8-sig"))
    claim = json_object(decoded, "HoF original claim must be an object")
    root, intent = claim.get("once_ledger_root"), claim.get("intent_key")
    if not isinstance(root, str) or not isinstance(intent, str):
        raise ValueError("HoF stable once ledger changed")
    require(path.parent == Path(root).resolve() and path.name == intent + ".claim.json", "HoF stable once ledger changed")
    marker = path.with_name(intent + ".submit-once.json")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"schema": "faith-e02-R19-hof-original-submit-once-v1", "claim": pin(path), "unknown_must_not_repeat": True}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return marker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--live", type=Path)
    parser.add_argument("--queue-name")
    parser.add_argument("--once-claim", type=Path)
    args = parser.parse_args(argv)
    plan_path: object = args.plan
    live: object = args.live
    queue_name: object = args.queue_name
    claim_path: object = args.once_claim
    if not isinstance(plan_path, Path) or (live is not None and not isinstance(live, Path)) or (claim_path is not None and not isinstance(claim_path, Path)) or (queue_name is not None and not isinstance(queue_name, str)):
        raise ValueError("HoF CLI arguments differ from parsed paths/queue name")
    decoded: object = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    validate(decoded, claim_path=claim_path)
    if queue_name:
        if live is None:
            raise ValueError("HoF dispatch needs its current allocated live directory")
        plan = json_object(decoded, "HoF actual plan must be an object")
        steps = json_array(plan.get("steps"), "HoF actual plan steps missing")
        if any(is_json_object(s) and s.get("tool") == CONFIRM for s in steps):
            if claim_path is None:
                raise ValueError("HoF Confirm needs its durable claim")
            admit_confirm(decoded, claim_path)
        entry = Path(__file__).resolve().with_name("ck3_mod_acceptance_queue_control.py")
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(entry), "--live", str(live),
            "--plan", str(plan_path), "--name", queue_name], check=False).returncode
    print(json.dumps({"policy_validated": True, "submitted": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
