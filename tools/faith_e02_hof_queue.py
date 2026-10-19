"""Finite R19 HoF observation and one durable original Confirm; no game bypass."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

DECISION = "create_hof_decision"
QUERY = "ck3_query_ingame_decision_item_v1"
CONFIRM = "ck3_confirm_ingame_decision_outcome_v1"
EVENT_CONTEXT = "ck3_query_current_event_window_context_v1"
EVENT_SELECT = "ck3_select_event_option"
READS = frozenset({"ck3_take_snapshot", "ck3_get_capabilities",
    "ck3_query_player_religion_context_v1", "ck3_query_player_rite_governance_v1",
    "ck3_query_player_holy_site_v1", "ck3_inspect_gui_window_tree_v1", QUERY, EVENT_CONTEXT})


def require(value, message):
    if not value:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_pin(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "bytes", "sha256"},
            "HoF requires an exact original receipt pin")
    require(pin(ref["path"]) == ref, "HoF original receipt changed")
    return json.loads(Path(ref["path"]).read_text(encoding="utf-8-sig"))


def quote_terms(row, actor, date_raw):
    require(row.get("ok") is True and not row.get("error"), "HoF actual quote query failed")
    value = row.get("result")
    require(isinstance(value, dict) and value.get("available") is True
        and value.get("decision_key") == DECISION and value.get("matching_row_count") == 1,
        "HoF actual keyed decision is absent or ambiguous")
    for key in ("detail_definition_matches_target", "detail_tree_complete",
                "detail_root_visible", "detail_actor_binding_verified"):
        require(value.get(key) is True, "HoF selected detail proof unavailable: " + key)
    require(value.get("detail_actor_reference_key") == actor
        and value.get("played_character_id") == actor and value.get("date_raw") == date_raw,
        "HoF selected detail actor/date changed")
    terms = value.get("selected_terms")
    require(isinstance(terms, dict) and terms.get("available") is True
        and terms.get("schema") == "ck3-selected-decision-terms-v1"
        and terms.get("decision_key") == DECISION
        and terms.get("played_character_id") == actor and terms.get("date_raw") == date_raw
        and terms.get("read_only") is True and terms.get("action_ready") is False
        and terms.get("decision_confirm_invoked") is False
        and terms.get("context_verified") is True
        and terms.get("named_parameter_count") == 0
        and terms.get("context_adapter") == "actual_empty_named_parameters_only",
        "HoF actual selected empty-parameter terms unavailable")
    require(terms.get("requirements_bypass_observed") is True
        and type(terms.get("requirements_bypass_raw")) is int and terms["requirements_bypass_raw"] == 0
        and terms.get("ordinary_legality_observed") is True
        and terms.get("ordinary_can_confirm") is True and terms.get("can_confirm") is True,
        "HoF original ordinary legality rejected; do not add resources or bypass")
    require(terms.get("requirements_description_available") is True
        and terms.get("cost_description_available") is True
        and isinstance(terms.get("requirements_description"), str)
        and isinstance(terms.get("cost_description"), str)
        and terms.get("resource_quote_available") is True, "HoF complete real terms or quote missing")
    quote = terms.get("resource_quote")
    require(isinstance(quote, dict) and set(quote) == {"raw_scale", "resource_vector_raw", "native_affordable"}
        and type(quote.get("raw_scale")) is int and quote["raw_scale"] == 100000
        and quote.get("native_affordable") is True
        and isinstance(quote.get("resource_vector_raw"), list) and len(quote["resource_vector_raw"]) == 10
        and all(type(n) is int and -(1 << 63) <= n < (1 << 63) for n in quote["resource_vector_raw"]),
        "HoF actual full10 quote is unavailable or unaffordable")
    return terms


def verify_quote_pair(claim):
    require(claim.get("schema") == "faith-e02-R19-hof-once-claim-v1"
        and claim.get("decision_key") == DECISION, "HoF finite once claim differs")
    refs = claim.get("quote_receipts")
    require(isinstance(refs, list) and len(refs) == 2 and refs[0]["path"] != refs[1]["path"],
            "HoF requires two independent original quote receipts")
    values = []
    for ref in refs:
        packet = read_pin(ref)
        require(isinstance(packet.get("rows"), list) and len(packet["rows"]) == 1,
                "HoF quote receipt must contain one actual query")
        values.append(quote_terms(packet["rows"][0], claim["actor"], claim["date_raw"]))
    for field in ("resource_quote", "requirements_description", "cost_description"):
        require(values[0][field] == values[1][field], "HoF actual quotes changed: " + field)
    return values


def validate(plan, *, claim_path=None, event_path=None):
    require(isinstance(plan, dict) and set(plan) == {"steps"} and isinstance(plan["steps"], list)
        and 1 <= len(plan["steps"]) <= 8, "HoF finite plan must have 1..8 steps")
    ids = []
    for step in plan["steps"]:
        require(isinstance(step, dict) and set(step) <= {
            "id", "kind", "tool", "args", "fresh_revision", "continue_on_error"}
            and step.get("kind", "tool") == "tool" and step.get("continue_on_error") is True
            and step.get("fresh_revision") is True and isinstance(step.get("id"), str),
            "HoF rejects raw, day, save, stale, lifecycle or unbounded operations")
        ids.append(step["id"])
        args, tool = step.get("args", {}), step.get("tool")
        require(isinstance(args, dict), "HoF args must be an object")
        if "expected_revision" in args:
            require(type(args["expected_revision"]) is int and args["expected_revision"] > 0,
                "HoF revision must be an actual positive integer")
        allowed = {"expected_revision"}
        if tool in {QUERY, "ck3_select_ingame_decision_item_v1"}:
            allowed.add("decision_key")
            require(args.get("decision_key") == DECISION, "HoF decision key differs")
        elif tool == EVENT_CONTEXT:
            allowed.add("event_instance_id")
            require(type(args.get("event_instance_id")) is int and args["event_instance_id"] > 0,
                    "HoF needs the actual current event instance")
        elif tool == EVENT_SELECT:
            allowed.update({"event_instance_id", "option_number"})
            require(event_path is not None and len(plan["steps"]) == 1,
                    "HoF first-option choice needs its actual context claim")
            instance, number = first_event_option(json.loads(Path(event_path).read_text(encoding="utf-8-sig")))
            require(args.get("event_instance_id") == instance and type(args.get("option_number")) is int
                and args["option_number"] == number, "HoF rejects a guessed or non-first event option")
        elif tool == CONFIRM:
            allowed.update({"decision_key", "expected_outcome"})
            require(claim_path is not None and len(plan["steps"]) == 1
                and args.get("decision_key") == DECISION and args.get("expected_outcome") == "decision_closed",
                "HoF Confirm needs its durable claim and exact closed outcome")
            verify_quote_pair(json.loads(Path(claim_path).read_text(encoding="utf-8-sig")))
        elif tool == "ck3_inspect_gui_window_tree_v1":
            allowed.add("window_kind")
            require(args.get("window_kind") in {"decisions", "decision_detail"}, "HoF finite window differs")
        elif tool == "ck3_query_player_holy_site_v1":
            allowed.add("holy_site_id")
            require(args.get("holy_site_id") == 32, "R19 only reads its adopted Nadjaf site")
        elif tool == "ck3_take_snapshot":
            allowed.add("include_native_command_history")
            require(args.get("include_native_command_history", False) is False, "HoF omits command history")
        elif tool == "ck3_open_ingame_decisions_v1":
            pass
        else:
            require(tool in READS, "HoF tool is outside the finite scope: " + str(tool))
        require(set(args) <= allowed, "HoF args include an unlisted actor, pointer or operation")
    require(len(ids) == len(set(ids)), "HoF step identity reused")
    return {"capture_policy_validated": True, "native_legality_or_success_inferred": False}


def first_event_option(claim):
    require(claim.get("schema") == "faith-e02-R19-first-event-claim-v1",
            "HoF event claim identity differs")
    frame = claim["frame"]
    packet = read_pin(claim["query_receipt"])
    require(isinstance(packet.get("rows"), list) and len(packet["rows"]) == 1,
            "HoF actual event query receipt missing")
    row = packet["rows"][0]
    require(row.get("ok") is True and not row.get("error"), "HoF event query failed")
    value = row["result"]
    typed = value.get("current_event_window_context", {})
    instance = (frame.get("active_event") or {}).get("instance_id")
    require(type(instance) is int and instance > 0
        and value.get("accepted") is True and value.get("current_event_window_context_ready") is True
        and typed.get("schema") == "current-event-window-context-v1" and typed.get("status") == "available"
        and typed.get("current_event_instance_id") == instance
        and typed.get("date_raw") == frame["date_raw"]
        and typed.get("snapshot_revision") == frame["native_revision"]
        and isinstance(typed.get("event_definition_key"), str) and bool(typed["event_definition_key"])
        and typed.get("readiness", {}).get("option_presentation_ready") is True,
        "HoF native current event definition/options not qualified")
    options = typed.get("options")
    require(isinstance(options, list) and 1 <= len(options) <= 64
        and [o.get("rendered_index") for o in options] == list(range(len(options))),
        "HoF actual rendered option order missing")
    first = options[0]
    index = first.get("native_option_index")
    require(first.get("shown") is True and first.get("enabled") is True
        and type(index) is int and index >= 0
        and any(o.get("option_number") == index + 1 and o.get("enabled") is True
                for o in frame["active_event"].get("options", [])),
        "HoF native first displayed option disabled or inconsistent")
    return instance, index + 1


def admit_event_choice(plan, path):
    validate(plan, event_path=path)
    marker = Path(path).with_suffix(".submit-once.json")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"claim": pin(path), "unknown_must_not_repeat": True}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return marker


def admit_confirm(plan, claim_path):
    validate(plan, claim_path=claim_path)
    claim_path = Path(claim_path).resolve()
    claim = json.loads(claim_path.read_text(encoding="utf-8-sig"))
    require(claim_path.parent == Path(claim["once_ledger_root"]).resolve()
        and claim_path.name == claim["intent_key"] + ".claim.json", "HoF stable once ledger changed")
    marker = claim_path.with_name(claim["intent_key"] + ".submit-once.json")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"schema": "faith-e02-R19-hof-original-submit-once-v1", "claim": pin(claim_path),
                   "unknown_must_not_repeat": True}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return marker


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--live", type=Path)
    parser.add_argument("--queue-name")
    parser.add_argument("--once-claim", type=Path)
    args = parser.parse_args(argv)
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    validate(plan, claim_path=args.once_claim)
    if args.queue_name:
        require(args.live is not None, "HoF dispatch needs its current allocated live directory")
        if any(step["tool"] == CONFIRM for step in plan["steps"]):
            admit_confirm(plan, args.once_claim)
        entry = Path(__file__).resolve().with_name("ck3_mod_acceptance_queue_control.py")
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(entry), "--live", str(args.live),
            "--plan", str(args.plan), "--name", args.queue_name], check=False).returncode
    print(json.dumps({"policy_validated": True, "submitted": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
