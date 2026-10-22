"""Retained native R19 Faith: observe real HoF terms, optionally Confirm once."""
from __future__ import annotations
from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import faith_e02_hof_queue as queue
from ck3_mod_acceptance_client import write_once
from ck3_mod_acceptance_cases.faith_e02_d1_readonly_adapter import shared_opening_binding

CASE = "faith-engine-e02-r19-spiritual-head-v1"
PRODUCT = "faith-engine"
SAVE_BYTES = 69030069
SAVE_SHA256 = "de0f97b142ea88f13797d2f025380a52c5bab396b3d4986b8be6bf3ef653cc07"
READONLY_TOOLS = frozenset({"ck3_query_player_religion_context_v1",
    "ck3_query_player_rite_governance_v1", "ck3_query_player_holy_site_v1"})
SCENE_TOOLS = READONLY_TOOLS | {"ck3_take_snapshot", "ck3_get_capabilities",
    "ck3_open_ingame_decisions_v1", "ck3_inspect_gui_window_tree_v1",
    queue.QUERY, "ck3_select_ingame_decision_item_v1", queue.EVENT_CONTEXT, queue.EVENT_SELECT}
LIFECYCLE_TOOLS = frozenset({"ck3_query_normal_exit_context_v1",
    "ck3_request_normal_exit_v1", "ck3_observe_normal_exit_v1"})
ACTION_OPT_INS = ("opt_in_holy_site_creation_ui", "opt_in_holy_site_creation_create_once",
    "opt_in_holy_site_relic_actions", "opt_in_player_rite_creation_actions",
    "opt_in_player_pilgrimage_execution")
require = queue.require


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_contract(context):
    c = context["case_contract"]
    require(c.get("schema") == "faith-engine-e02-r19-spiritual-head-case-v1"
        and c.get("product") == context.get("product") == PRODUCT
        and c.get("case") == context.get("case") == CASE, "R19 HoF case identity differs")
    saved = c.get("saved_input", {})
    require(set(saved) == {"save", "bytes", "sha256", "player_id", "date_raw"}
        and saved["bytes"] == SAVE_BYTES and type(saved["bytes"]) is int
        and saved["sha256"] == SAVE_SHA256 and saved["player_id"] == 31254
        and saved["date_raw"] == 53144328, "R19 original native save identity differs")
    require(c.get("profile") == {"enabled_mods": [], "product_files": []}
        and c.get("historical_expectation") == {"actor": 31254, "faith": 103, "rite": 150,
            "date_raw": 53144328, "fresh_head_absence_not_yet_proven": True},
        "R19 source and historical/native distinction differs")
    require(type(c.get("confirm_once_when_ready")) is bool
        and c.get("max_confirm_submissions") == 1
        and c.get("decision_key") == queue.DECISION
        and c.get("funds_may_not_be_fabricated") is True
        and isinstance(c.get("machine_id"), str) and bool(c["machine_id"]) and c["machine_id"] != "unknown",
        "R19 finite confirmation contract differs")
    ledger = c.get("once_ledger_root")
    require(isinstance(ledger, str) and Path(ledger).is_absolute(),
        "R19 needs one stable absolute once ledger reused across attempts")
    spec = context["case_spec"]
    require(all(spec.get(key) is False for key in ACTION_OPT_INS), "R19 unrelated action permission opened")
    required = SCENE_TOOLS | LIFECYCLE_TOOLS | ({queue.CONFIRM} if c["confirm_once_when_ready"] else set())
    require(set(spec.get("required_mcp_tools", [])) == required
        and set(spec.get("opt_in_read_only_mcp_tools", [])) == READONLY_TOOLS,
        "R19 finite required/read-only tools differ")
    return c


def prepare_case(context):
    from ck3_live_run_id import current_machine_id
    from ck3_mod_acceptance_prepare import finish_product_profile
    c = validate_contract(context)
    require(current_machine_id() == c["machine_id"], "R19 executing machine differs")
    admission = context["case_inputs"]["storage_admission"]
    grant = queue.read_pin(admission)
    require(grant.get("machine_id") == c["machine_id"] and grant.get("active") is True,
        "R19 current storage admission absent")
    expiry = datetime.fromisoformat(grant["expires_at_utc"].replace("Z", "+00:00"))
    require(expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry, "R19 storage admission expired")
    saved = c["saved_input"]
    require(context["saved_campaign"] == saved, "R19 prepare selected another save")
    source = Path(saved["save"])
    require(source.is_file() and not source.is_symlink(), "R19 original native save absent")
    before = source.stat()
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    require(before.st_size == saved["bytes"] and digest.hexdigest() == saved["sha256"]
        and source.stat().st_mtime_ns == before.st_mtime_ns, "R19 source save changed")
    profile = materialize_saved_profile_v2(context, None, context["case_inputs"]["configuration"], source_role=None)
    profile = finish_product_profile(context, profile, provenance={
        "machine_id": c["machine_id"], "kind": "faith-e02-R19-retained-native-Faith",
        "saved_input": saved, "storage_admission": admission, "preparation_mod_mounted": False,
        "fresh_restore_observed": False, "fresh_head_absence_observed": False,
        "prior_setup_disclosure": c["prior_setup_disclosure"]})
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
        "saved_campaign": {**saved, "product_inventory": profile["product_inventory"]["path"]}},
        "profile": profile, "initial_plan": context["case_spec"]["initial_plan"],
        "runtime_status": "NOT_RUN", "business_pass": False}


def wallet(frame):
    return {key: frame.get("played_character_" + key) for key in ("gold", "treasury", "piety")}


def same_scene(frame, binding, reader, *, allow_event=False):
    current = reader(frame)
    for key in ("played_character_id", "date_raw", "game_pid", "connection_generation", "episode_run_id"):
        require(current[key] == binding[key], "R19 scene changed " + key)
    require(allow_event or frame.get("active_event") is None, "R19 has a real event requiring its ordinary policy")


def require_identity(religion, governance, *, no_head):
    require(religion.get("available") is True and religion.get("played_character_id") == 31254
        and religion.get("faith_id") == 103 and religion.get("rite_id") == 150
        and religion.get("faith_main_rite_id") == 150, "R19 fresh Faith/Rite differs")
    heads = governance.get("heads", {})
    require(governance.get("frame_available") is True and heads.get("available") is True
        and heads.get("played_character_id") == 31254 and heads.get("faith_id") == 103
        and heads.get("actor_rite_id") == 150 and heads.get("faith_main_rite_id") == 150,
        "R19 actual Faith/head component unavailable")
    if no_head:
        require(heads.get("faith_religious_head_holder_character_id") is None,
            "R19 already has a Faith head; never recreate or remove it")
    return heads


def _call(client, name, tool, args=None, *, claim=None, event_claim=None):
    step = {"id": name, "tool": tool, "args": args or {},
            "fresh_revision": True, "continue_on_error": True}
    plan = {"steps": [step]}
    queue.validate(plan, claim_path=claim, event_path=event_claim)
    rows = client.execute_plan(plan["steps"], name)
    require(isinstance(rows, list) and len(rows) == 1, "R19 actual step result absent")
    return rows[0]


def _result(row):
    require(row.get("ok") is True and not row.get("error") and isinstance(row.get("result"), dict),
        "R19 actual query/action rejected: " + str(row.get("error")))
    return row["result"]


def _review(client, context, name, payload):
    result = client.root_checkpoint(name, payload, reserve=120)
    require(result.get("run_id") == context["run_id"] and result.get("reviewer") == client.operator_reviewer
        and result.get("status") == "complete", "R19 current Root recording checkpoint differs")
    return result


def drain_current_events(context, client, frame, binding, reader):
    """Current native first displayed options only; never advances a day."""
    output = Path(context["output"])
    result = {"status": "DRAINED", "events": [], "automatic_retry": False,
              "offline_analysis_required_after_batch": True}
    for number in range(8):
        active = frame.get("active_event")
        if active is None:
            return result
        receipt = {"active_event": active, "frame": frame, "submission_attempted": False}
        result["events"].append(receipt)
        prefix = "hof-r19-post-event-" + str(number + 1).zfill(2)
        try:
            same_scene(frame, binding, reader, allow_event=True)
            instance = active.get("instance_id")
            require(type(instance) is int and instance > 0, "Actual native event instance absent")
            row = _call(client, prefix + "-context", queue.EVENT_CONTEXT,
                        {"event_instance_id": instance})
            capture = {"schema": "faith-e02-R19-first-event-claim-v1",
                "machine_id": context["case_contract"]["machine_id"], "run_id": context["run_id"],
                "frame": row.get("before_snapshot", frame),
                "query_receipt": queue.pin(output / (prefix + "-context.actual-results.json")),
                "offline_analysis_required_after_batch": True}
            path = output / (prefix + "-offline-analysis-and-once-claim.json")
            write_once(path, capture)
            instance, option = queue.first_event_option(capture)
            receipt.update(event_instance_id=instance, selected_option_number=option,
                           offline_analysis_input=queue.pin(path))
            plan = {"steps": [{"id": prefix + "-select-once", "tool": queue.EVENT_SELECT,
                "args": {"event_instance_id": instance, "option_number": option},
                "fresh_revision": True, "continue_on_error": True}]}
            queue.admit_event_choice(plan, path)
            receipt["submission_attempted"] = True
            try:
                chosen = _call(client, prefix + "-select-once", queue.EVENT_SELECT,
                    {"event_instance_id": instance, "option_number": option}, event_claim=path)
                ack = _result(chosen)
                receipt["ack_accepted"] = (ack.get("accepted") is True
                    and ack.get("event_instance_id") == instance and ack.get("option_number") == option
                    and ack.get("option_index") == option - 1)
            except Exception as error:
                receipt["submission_outcome_unknown"] = type(error).__name__ + ": " + str(error)
            # Observe once after any submitted outcome; never replay the choice.
            after = client.snapshot(require_event_free=False)
            same_scene(after, binding, reader, allow_event=True)
            receipt["independent_after_snapshot"] = after
            gone = (after.get("active_event") or {}).get("instance_id") != instance
            receipt["old_instance_gone"] = gone
            write_once(output / (prefix + "-post-observation.json"), receipt)
            if receipt.get("ack_accepted") is not True or not gone:
                result["status"] = "UNKNOWN_OR_UNCONSUMED_NO_REPLAY"
                return result
            frame = after
        except Exception as error:
            receipt["diagnostic"] = type(error).__name__ + ": " + str(error)
            result["status"] = "PARTIAL_NATIVE_EVENT_CONTRACT_GAP"
            return result
    result["status"] = "FINITE_EVENT_CAP_REACHED"
    return result


def run_case(context, client):
    c = validate_contract(context)
    output = Path(context["output"])
    initial = client.snapshot()
    first = {"schema": "faith-e02-R19-first-native-identity-v1", "machine_id": c["machine_id"],
        "run_id": context["run_id"], "saved_input": c["saved_input"], "actual_snapshot": initial,
        "fresh_identity_validated": False, "business_pass": False}
    try:
        reader, sources = shared_opening_binding(context)
        binding = reader(initial)
        require(binding["played_character_id"] == 31254, "R19 actual actor differs from source save")
        same_scene(initial, binding, reader)
    except (ValueError, KeyError, ImportError) as error:
        first["rejection_reason"] = str(error)
        write_once(output / "r19-first-native-identity.json", first)
        raise
    first.update(fresh_identity_validated=True, scene_binding=binding, opening_binding_sources=sources)
    write_once(output / "r19-first-native-identity.json", first)
    result = {"schema": "faith-e02-R19-hof-result-v1", "machine_id": c["machine_id"],
        "run_id": context["run_id"], "case": CASE, "scene_binding": binding,
        "readonly_eligibility_observed": False, "confirm_dispatch_attempts": 0,
        "head_creation_observed": False, "business_pass": False, "automatic_retry": False}
    client.checkpoint("hof-r19-before", initial)
    try:
        religion = _result(_call(client, "hof-r19-religion-before", "ck3_query_player_religion_context_v1"))
        gov = _result(_call(client, "hof-r19-governance-before", "ck3_query_player_rite_governance_v1"))
        heads = require_identity(religion, gov, no_head=True)
        result["head_before"] = heads
        site = _result(_call(client, "hof-r19-site-before", "ck3_query_player_holy_site_v1", {"holy_site_id": 32}))
        require(32 in site.get("current_faith_holy_site_ids", []),
            "R19 adopted Nadjaf association not observed in current Faith")
        _result(_call(client, "hof-r19-open", "ck3_open_ingame_decisions_v1"))
        _call(client, "hof-r19-decisions-tree", "ck3_inspect_gui_window_tree_v1", {"window_kind": "decisions"})
        row = _result(_call(client, "hof-r19-keyed-before", queue.QUERY, {"decision_key": queue.DECISION}))
        require(row.get("available") is True and row.get("decision_key") == queue.DECISION
            and row.get("matching_row_count") == 1, "R19 create_hof actual row absent or ambiguous")
        _result(_call(client, "hof-r19-select", "ck3_select_ingame_decision_item_v1", {"decision_key": queue.DECISION}))
        frame_a = client.snapshot()
        same_scene(frame_a, binding, reader)
        quote_a = _call(client, "hof-r19-quote-a", queue.QUERY, {"decision_key": queue.DECISION})
        result["first_actual_keyed_result"] = quote_a.get("result")
        terms_a = queue.quote_terms(quote_a, 31254, binding["date_raw"])
        result.update(readonly_eligibility_observed=True, first_terms=terms_a,
            wallet_before=wallet(frame_a))
    except (ValueError, KeyError) as error:
        result.update(rejection_reason=str(error), world_submit_performed=False)
        _review(client, context, "hof-r19-eligibility-review", result)
        write_once(output / "r19-hof-result.json", result)
        return result
    _review(client, context, "hof-r19-eligibility-review", result)
    if not c["confirm_once_when_ready"]:
        result["confirmation_policy"] = "readonly_only"
        write_once(output / "r19-hof-result.json", result)
        return result
    # Recheck current identity and wallet after the recording hold, then obtain
    # a second real quote. The claim and submit marker are never reset on errors.
    preconfirm = client.snapshot()
    same_scene(preconfirm, binding, reader)
    religion = _result(_call(client, "hof-r19-religion-preconfirm", "ck3_query_player_religion_context_v1"))
    gov = _result(_call(client, "hof-r19-governance-preconfirm", "ck3_query_player_rite_governance_v1"))
    require_identity(religion, gov, no_head=True)
    quote_b = _call(client, "hof-r19-quote-b", queue.QUERY, {"decision_key": queue.DECISION})
    queue.quote_terms(quote_b, 31254, binding["date_raw"])
    intent = hashlib.sha256((SAVE_SHA256 + ":31254:103:" + queue.DECISION).encode("ascii")).hexdigest()
    root = Path(c["once_ledger_root"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    claim_path = root / (intent + ".claim.json")
    claim = {"schema": "faith-e02-R19-hof-once-claim-v1", "machine_id": c["machine_id"],
        "run_id": context["run_id"], "actor": 31254, "faith": 103, "date_raw": binding["date_raw"],
        "decision_key": queue.DECISION, "intent_key": intent, "once_ledger_root": str(root),
        "quote_receipts": [queue.pin(output / (name + ".actual-results.json"))
            for name in ("hof-r19-quote-a", "hof-r19-quote-b")],
        "unknown_must_not_repeat": True}
    queue.verify_quote_pair(claim)
    with claim_path.open("x", encoding="utf-8") as stream:
        json.dump(claim, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    confirm = {"steps": [{"id": "hof-r19-confirm-once", "tool": queue.CONFIRM,
        "args": {"decision_key": queue.DECISION, "expected_outcome": "decision_closed"},
        "fresh_revision": True, "continue_on_error": True}]}
    queue.admit_confirm(confirm, claim_path)
    result["confirm_dispatch_attempts"] = 1
    result["intent_claim"] = queue.pin(claim_path)
    try:
        result["confirm_actual_row"] = _call(client, "hof-r19-confirm-once", queue.CONFIRM,
            {"decision_key": queue.DECISION, "expected_outcome": "decision_closed"}, claim=claim_path)
    except Exception as error:
        result["submission_outcome_unknown"] = type(error).__name__ + ": " + str(error)
        write_once(output / "r19-confirm-unknown.json", result)
        # Never resend. A timeout may follow an actual office creation.
    # Read independent post-state before handling any actual event. Each read
    # is bounded and attempted even if a different post-state read failed.
    errors, after, post_religion, post_gov, post = {}, None, None, None, None
    try:
        after = client.snapshot(require_event_free=False)
        same_scene(after, binding, reader, allow_event=True)
    except Exception as error:
        errors["snapshot"] = type(error).__name__ + ": " + str(error)
    for key, tool in (("religion", "ck3_query_player_religion_context_v1"),
                      ("governance", "ck3_query_player_rite_governance_v1")):
        try:
            value = _result(_call(client, "hof-r19-" + key + "-after", tool))
            if key == "religion":
                post_religion = value
            else:
                post_gov = value
        except Exception as error:
            errors[key] = type(error).__name__ + ": " + str(error)
    try:
        post = require_identity(post_religion or {}, post_gov or {}, no_head=False)
    except (ValueError, KeyError) as error:
        errors["post_identity"] = str(error)
    created = not errors and post is not None and all(
        type(post.get(key)) is int and 0 <= post[key] < 0xFFFFFFFF
        for key in ("faith_religious_head_holder_character_id", "faith_religious_head_title_id"))
    before_wallet, after_wallet = wallet(preconfirm), wallet(after or {})
    deltas = {}
    for key in ("gold", "piety"):
        a, b = before_wallet[key], after_wallet[key]
        if (isinstance(a, dict) and isinstance(b, dict)
                and type(a.get("raw")) is int and type(b.get("raw")) is int
                and a.get("scale") == b.get("scale") == 100000):
            deltas[key] = b["raw"] - a["raw"]
    complete_wallet = set(deltas) == {"gold", "piety"} and "snapshot" not in errors
    result.update(head_after=post, wallet_preconfirm=wallet(preconfirm), wallet_after=after_wallet,
        wallet_delta_raw=deltas, wallet_observation_complete=complete_wallet,
        head_creation_observed=bool(created), business_pass=bool(created and complete_wallet),
        quote_settlement_resource_index_join_verified=False,
        world_mutation_absence_proven=False, post_observation_errors=errors,
        independent_post_snapshot=after, independent_post_religion=post_religion,
        independent_post_governance=post_gov, poststate_captured_before_event_policy=True,
        post_active_event=(after or {}).get("active_event"))
    write_once(output / "r19-hof-independent-poststate.json", result)
    if after is not None and "snapshot" not in errors:
        result["event_policy"] = drain_current_events(context, client, after, binding, reader)
    else:
        result["event_policy"] = {"status": "INCONCLUSIVE_NO_QUALIFIED_SNAPSHOT", "automatic_retry": False}
    client.checkpoint("hof-r19-after", after or {"post_observation_errors": errors})
    _review(client, context, "hof-r19-post-observation", result)
    write_once(output / "r19-hof-result.json", result)
    return result


def verify_case(context):
    c = validate_contract(context)
    result = read(Path(context["output"]) / "r19-hof-result.json")
    require(result.get("run_id") == context["run_id"] and result.get("machine_id") == c["machine_id"]
        and result.get("case") == CASE, "R19 result belongs to another run")
    return {"readonly_eligibility_observed": result.get("readonly_eligibility_observed") is True,
        "head_creation_observed": result.get("head_creation_observed") is True,
        "business_pass": result.get("business_pass") is True,
        "product_release_pass": False, "automatic_retry": False}
