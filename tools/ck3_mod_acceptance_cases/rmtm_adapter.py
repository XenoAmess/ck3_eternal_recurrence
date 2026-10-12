"""RMTM original business phases on the one selected common runtime."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json

from ._business import (case_config, final_root_evidence, literals, observe,
                        original_day, pin, require, review, write_once, check_evidence)


PHASE4_OPTION = "phase4_pre_send_gui_qualification"
PHASE4_QUALIFY = "rmtm-phase4-pre-send-qualification"
PHASE4_SEND = "rmtm-phase4-original-probe-once"
PHASE4_QUALIFY_FACTS = [
    "same_original_saved_A_B_full_character_and_title_ids",
    "same_d3_actor_full_later_title_and_paused_date",
    "both_actual_default_flags_complete_unchanged",
    "both_actual_GetAnswerScore_strictly_negative",
    "both_complete_actual_GetAnswerReason_captured",
    "both_offers_Cancelled_without_send",
    "no_probe_send_no_target_reselection_no_date_advance",
]
PHASE4_SEND_FACTS = [
    "same_qualified_original_A_B_no_reselection",
    "original_probe_ScriptedGui_clicked_once_after_qualification",
    "actual_probe_outcome_observed_not_input_ACK",
    "same_d3_actor_full_later_title_and_paused_date",
]


def phase4_enabled(context):
    value = context.get("case_inputs", {}).get(PHASE4_OPTION, False)
    require(type(value) is bool, PHASE4_OPTION + " must be a strict JSON boolean")
    require(not value or context["case"] == "core", "Pre-send qualification is core-only, not threshold_ui")
    return value


def validate_contract(context, *, require_prepared=False):
    """Validate the pure contract; bound preparations also require full receipts."""
    enabled = phase4_enabled(context)
    config = case_config(context)
    require(config["natural_game_day_limit"] == 14 and config["fixture_recent_independence_override_days"] == 10,
            "Original timer contract changed")
    if context["case"] == "core":
        require((config["original_family_count"], config["unchanged_family_count"],
                 config["physical_qualified_family_count"]) == (36, 33, 3), "Original36 contract changed")
    inputs = context.get("case_inputs", {})
    # Public unprepared preflight has no materialized profile yet. A real
    # preparation binds these inputs; never use receipt.exists() to skip a
    # missing/deleted receipt of an otherwise bound prepared case.
    if require_prepared or any(key in inputs for key in ("product_dir", "plain_configuration")):
        return _validate_prepared_materialization(context, enabled)
    return {"phase4_pre_send_gui_qualification": enabled, "runtime_status": "NOT_RUN", "business_pass": False}


def _validate_prepared_materialization(context, enabled):
    """Actual receipt/inverse/load-order checks, never a pure planning gate."""
    from tools import prepare_reclaim_the_motherland_1_20_fixture as emitter
    from tools import reclaim_the_motherland_scope_witness as witness
    state = Path(context["state_dir"])
    startup = json.loads((state / "preparation.json").read_text(encoding="utf-8-sig"))
    preparation = check_evidence(startup["preparation"])
    profile = json.loads(Path(preparation["path"]).read_text(encoding="utf-8-sig"))
    provenance = profile["provenance"]
    require(provenance["kind"] == "case-emitter-and-exact-formal-staging", "Original materialization required")
    fixture = Path(provenance["fixture"])
    product = Path(context["case_inputs"]["product_dir"])
    require(Path(provenance["product"]).resolve() == product.resolve(), "Selected formal product differs")
    receipt = json.loads(fixture.with_suffix(".prepare.json").read_text(encoding="utf-8-sig"))
    require(receipt["ui_checkpoints"] is True and receipt["threshold_ui"] is (context["case"] == "threshold_ui"),
            "Prepared core/UI flags differ")
    source = Path(context["repo_root"]) / "tools/fixtures/reclaim_the_motherland_acceptance"
    original = emitter.events(True).encode("utf-8-sig")
    support = emitter.phase4_support(source) if enabled else {}
    if enabled:
        widget = support[emitter.PHASE4_GUI_RELATIVE]
        require(b"on_start" not in widget and b"trigger_when" not in widget and widget.count(b".Execute(") == 1,
                "Diagnostic widget must have only one manual onclick action")
    expected_driver = emitter.phase4_project(original) if enabled else original
    if enabled:
        require(receipt.get(PHASE4_OPTION) == emitter.phase4_projection_receipt(source, original, expected_driver, support),
                "Pre-send projection receipt/inverse differs or claims runtime credit")
    else:
        require(PHASE4_OPTION not in receipt, "Prepared flag is enabled but case_inputs is disabled")
    expected = {"events/rqa120_events.txt": expected_driver, **support}
    for relative, kind, source_path in (
        (witness.FIXTURE_RELATIVE, "execute", source / witness.FIXTURE_RELATIVE),
        (witness.CALLBACK_RELATIVE, "callback", product / witness.CALLBACK_RELATIVE),
    ):
        raw = source_path.read_bytes()
        projected, proof = witness.project(raw, kind)
        require(witness.restore(projected, kind) == raw, "Original business bytes were not restored")
        declared = [row for row in receipt["scope_witness_projection"]["projections"] if row["relative"] == relative]
        require(len(declared) == 1 and all(declared[0].get(key) == value for key, value in proof.items()),
                "Existing three-dump witness receipt changed")
        expected[relative] = projected
    require(receipt["scope_witness_projection"]["scope_dump_count"] == 3,
            "Only the original three source dumps are allowed")
    for relative, raw in expected.items():
        require((fixture / relative).read_bytes() == raw and
                (state / "profile/mod-content/fixture" / relative).read_bytes() == raw,
                "Prepared/loaded fixture projection differs: " + relative)
        require(receipt["prepared_file_sha256"][relative] == witness.byte_pin(raw)["sha256"],
                "Full prepared inventory omitted or changed a projection")
    for relative in ("gui/rqa_bridge.gui", "common/scripted_guis/rqa_guis.txt"):
        require(relative not in receipt["prepared_file_sha256"], "Automatic original bridge must not be loaded")
    if not enabled:
        require(not any("rqa120_phase4" in name for name in receipt["prepared_file_sha256"]),
                "Disabled option must not load diagnostic support files")
    load = json.loads((state / "profile/dlc_load.json").read_text(encoding="utf-8-sig"))
    require(load["enabled_mods"] == ["mod/product.mod", "mod/fixture.mod"], "Original formal-then-fixture load order changed")
    return {"phase4_pre_send_gui_qualification": enabled, "runtime_status": "NOT_RUN", "business_pass": False}


def prepare_case(context):
    from tools.ck3_mod_acceptance_prepare import invoke_fixture_prepare, materialize_fixture_profile
    config = case_config(context)
    require(context["case"] in ("core", "threshold_ui"), "Unknown original RMTM case")
    qualified_phase4 = phase4_enabled(context)
    days = config["fixture_recent_independence_override_days"]
    require(type(days) is int and 10 <= days <= 30, "Use the existing producer timer admission")
    require(config["natural_game_day_limit"] == 14, "Original fourteen-day cap is required")
    repo = Path(context["repo_root"])
    fixture = Path(context["run_dir"]) / "fixture"
    arguments = [
        "--repo", repo, "--output", fixture, "--ui-checkpoints",
        "--compressed-days", str(days), "--game-dir", context["game_dir"],
        "--formal-product-dir", context["case_inputs"]["product_dir"],
    ]
    if context["case"] == "threshold_ui":
        arguments.append("--threshold-ui")
    if qualified_phase4:
        arguments.append("--phase4-pre-send-gui-qualification")
    emitter = invoke_fixture_prepare(context, repo / "tools/prepare_reclaim_the_motherland_1_20_fixture.py", arguments)
    fixture_receipt = fixture.with_suffix(".prepare.json")
    scope_witness = {"receipt": pin(fixture_receipt), "projection": json.loads(
        fixture_receipt.read_text(encoding="utf-8-sig"))["scope_witness_projection"]}
    prepared = materialize_fixture_profile(context, fixture, context["case_inputs"]["product_dir"],
                                           context["case_inputs"]["plain_configuration"])
    validate_contract(context, require_prepared=True)
    return {"startup": {"mode": "fixture", "state_dir": prepared["state_dir"],
                        "fixture_start_policy": prepared["fixture_start_policy"]["path"],
                        "frontend_rules_plan": context["case_inputs"]["frontend_rules_plan"]},
            "initial_plan": str(repo / "tools/ck3_mod_acceptance_cases/common_readonly_start.plan.json"),
            "fixtures": {"emitter": emitter, "profile": prepared,
                          "scope_witness_projection": scope_witness,
                         "compressed_days": days, "natural_day_cap": 14},
            "business_pass": False}


def validate_phase4_review(response, d3):
    require(response.get("status") == "complete" and isinstance(response.get("facts"), dict) and
            all(response["facts"].get(key) is True for key in PHASE4_QUALIFY_FACTS),
            "GAP: original A/B qualification facts missing; never send or reselect")
    require(isinstance(response.get("evidence"), list) and response["evidence"], "Actual GUI evidence required, not ACK")
    for row in response["evidence"]:
        check_evidence(row)
    record = response.get("phase4_qualification")
    require(isinstance(record, dict), "GAP: actual default Offer score/identity record missing")
    require(record.get("actor_character_id") == d3["actor_character_id"] and
            record.get("later_title_id") == d3["title_id"] and record.get("date_raw") == d3["date_raw"],
            "GAP: qualification crossed original D3 actor/full Later/date")
    targets = record.get("targets")
    require(isinstance(targets, list) and len(targets) == 2, "GAP: both original targets required")
    ids = []
    for slot, row in zip(("A", "B"), targets):
        require(isinstance(row, dict) and row.get("slot") == slot, "GAP: original A/B order differs")
        for field in ("character_id", "primary_title_id"):
            require(type(row.get(field)) is int and 0 < row[field] < 0xFFFFFFFF, "GAP: full original target IDs required")
        require(type(row.get("answer_score")) is int and row["answer_score"] < 0,
                "GAP: original target default GUI total is unknown/nonnegative; do not send or reselect")
        require(isinstance(row.get("answer_reason"), str) and row["answer_reason"].strip(),
                "GAP: complete actual GetAnswerReason text missing")
        flags = row.get("default_flags")
        require(isinstance(flags, list) and all(isinstance(flag, dict) and set(flag) == {"name", "selected"} and
                isinstance(flag["name"], str) and flag["name"] and type(flag["selected"]) is bool for flag in flags),
                "GAP: actual complete default option flags required (empty only if GUI has none)")
        require(len({flag["name"] for flag in flags}) == len(flags), "Duplicate default option flag")
        ids.append(row["character_id"])
    require(ids[0] != ids[1] and d3["actor_character_id"] not in ids, "GAP: two distinct original recipients required")
    return record


def _phase4_pre_send(context, client, d3):
    from tools import reclaim_the_motherland_effective_law_contract as law
    from tools import prepare_reclaim_the_motherland_1_20_fixture as emitter
    config = case_config(context)
    literals(client, "rmtm-phase4-pre-send-ready", [emitter.PHASE4_READY], config["forbidden_markers"])
    response = review(client, PHASE4_QUALIFY, PHASE4_QUALIFY_FACTS, {
        "d3": d3, "target_binding": "Read the same original saved A/B via the manual widget character links; full character AND primary title IDs must match the actual dialogs.",
        "response_field": {"phase4_qualification": {"actor_character_id": "actual D3", "later_title_id": "actual D3",
            "date_raw": "actual D3", "targets": [{"slot": "A or B (in order)", "character_id": "actual full ID",
            "primary_title_id": "actual full ID", "answer_score": "actual GUI integer <0",
            "answer_reason": "complete actual GetAnswerReason text", "default_flags": [{"name": "actual flag", "selected": "actual bool"}]}]}},
        "stop": "Any missing/nonnegative/default-option change/identity mismatch is GAP; Cancel, never send, never pick other targets. No production -50/rank+10 change.",
    })
    record = validate_phase4_review(response, d3)
    frame, _ = observe(client, "rmtm-phase4-qualified-paused")
    require(list(law.frame(frame)[:4]) == d3["frame"][:4], "Pre-send GUI advanced date or crossed owner/process")
    review(client, PHASE4_SEND, PHASE4_SEND_FACTS, {
        "qualified_review": pin(Path(client.output) / (PHASE4_QUALIFY + "-accepted.json")),
        "original_targets": record["targets"], "manual_button": "rqa120_phase4_original_probe_once",
        "action": "Click the unchanged original rqa_execute_vassalization_probe_gui once only; no ad-hoc run_interaction or alternate target.",
        "remaining_gate": "Default GUI totals are qualification only; original D4 actual two-refusal marker is still mandatory.",
    })
    frame, _ = observe(client, "rmtm-phase4-probe-paused")
    require(list(law.frame(frame)[:4]) == d3["frame"][:4], "Original probe crossed D3 owner/date/process")
    literals(client, "rmtm-phase4-original-probe-paths", ["RQA: TEST PASS phase4_offer_vassalization_paths_valid"], config["forbidden_markers"])
    return {"qualification": pin(Path(client.output) / (PHASE4_QUALIFY + "-accepted.json")),
            "probe_once": pin(Path(client.output) / (PHASE4_SEND + "-accepted.json"))}


def _law_phase(client, phase):
    from tools import reclaim_the_motherland_effective_law_contract as law
    prefix = "rmtm-effective-law-" + phase
    root_row = client.execute_plan([{
        "id": prefix + "-root", "tool": "ck3_query_campaign_root_context_v1",
        "args": {}, "fresh_revision": True,
    }], prefix + "-root")[0]
    context = root_row["result"].get("campaign_root_context", {})
    title = context.get("primary_title", {}).get("title_id")
    require(type(title) is int and 0 < title < 0xFFFFFFFF,
            "Fresh independently read full current primary TitleID required")
    rows = client.execute_plan([
        {"id": prefix + "-physical", "tool": "ck3_query_title_own_laws_v1",
         "args": {"title_id": title}, "fresh_revision": True},
        {"id": prefix + "-script", "tool": "ck3_query_engine_log_literals_v1",
         "args": {"log_name": "debug.log", **law.phase_literals(phase)}, "fresh_revision": True},
    ], prefix + "-witnesses")
    evidence = {"schema": "rmtm-effective-single-heir-phase-actual-rows-v1", "phase": phase,
                "root_record": root_row, "physical_record": rows[0], "script_record": rows[1]}
    # The report object is actual, not a synthesized query result. Preserve it
    # once, and prove every copied row is present verbatim in that object.
    actual_report = client.read_report()
    for row in (root_row, *rows):
        require([entry for entry in actual_report["steps"] if entry["id"] == row["id"]] == [row],
                "Managed row differs from actual shared report")
    frozen_report = client.checkpoint(prefix + "-actual-report-object", actual_report)
    evidence["source_report"] = pin(frozen_report)
    evidence["source_report_representation"] = "JSON serialization of actual report object; not lexical raw slice"
    evidence["original_report_path"] = str(client.report_path)
    path = client.checkpoint(prefix + "-evidence", evidence)
    verdict = law.evaluate_phase(evidence)  # Fail closed on any pending/unknown physical fact.
    client.checkpoint(prefix + "-qualification", verdict)
    return path, verdict


def _threshold_ui_case(context, client):
    config = case_config(context)
    initial, _ = observe(client, "rmtm-threshold-D0-qualified")
    start = initial["date_raw"]
    for day in (1, 2, 3):
        original_day(client, "rmtm-threshold-D" + str(day), start, config["natural_game_day_limit"])
    d3, law = _law_phase(client, "d3")
    original_day(client, "rmtm-threshold-D4", start, config["natural_game_day_limit"])
    literals(client, "rmtm-threshold-stage4-ready", ["RQA120: TEST READY ui_after_chaos"], config["forbidden_markers"])
    review(client, "rmtm-threshold-50", ["original_fixture_prepare50_confirmed_once", "actual50_production_restoration_unavailable"], {
        "original_fixture_decision": "rqaui_prepare_fifty_decision",
        "original_source_boundary": "Setup changes only the original external test county inputs; inspect real production decision validity at50. Never execute production restoration here.",
    })
    literals(client, "rmtm-threshold-50-source", ["RQAUI: TEST READY actual_restoration_50_ui"], config["forbidden_markers"])
    review(client, "rmtm-threshold-51-and-production", [
        "original_fixture_prepare51_confirmed_once", "actual51_production_restoration_enabled",
        "actual_stock_claim_mandate_unavailable", "actual_production_confirmation_and_outcome",
        "original_fixture_verify_actual_outcome_confirmed_once",
    ], {"original_fixture_decisions": ["rqaui_prepare_fiftyone_decision", "rqaui_verify_actual_restoration_decision"],
        "production_rule": "Confirm the actual production restoration once; the fixture merely observes the actual title outcome."})
    source = literals(client, "rmtm-threshold-original-final", config["required_markers"], config["forbidden_markers"])
    client.checkpoint("rmtm-threshold-verdict-input", {"d3": str(d3), "law": law, "actual_source_row": source,
                                                     "case": "threshold_ui", "business_pass": False, "normal_close_pending": True})
    return {"status": "independent_threshold_GUI_observed_normal_close_pending", "business_pass": False,
            "full36_core_or_death_credit": False}


def run_case(context, client):
    validate_contract(context, require_prepared=True)
    if context["case"] == "threshold_ui":
        return _threshold_ui_case(context, client)
    config = case_config(context)
    require(context["case"] == "core", "Independent threshold adapter remains pending")
    initial, _ = observe(client, "rmtm-D0-qualified")
    start = initial["date_raw"]
    for day in (1, 2, 3):
        original_day(client, "rmtm-D" + str(day), start, config["natural_game_day_limit"])
    d3, d3_verdict = _law_phase(client, "d3")
    phase4 = _phase4_pre_send(context, client, d3_verdict) if phase4_enabled(context) else None
    original_day(client, "rmtm-D4", start, config["natural_game_day_limit"])
    literals(client, "rmtm-original-ui-ready", ["RQA120: TEST READY ui_after_chaos"], config["forbidden_markers"])
    review(client, "rmtm-C1-C5", [
        "later_empty_dejure_personal_land_loyal_subtree", "nine_exact_incumbents_real_budget_cancel",
        "continue_actual_A_B_names", "offer_A_minus50_rank10_total_no_hegemony_perks_cancel",
        "offer_B_minus50_rank10_total_no_hegemony_perks_cancel",
    ], {"scope": "Original GUI C1-C5; typed readiness never substitutes for actual UI",
        "next": "Open the real fixture Continue decision only after these views are captured."})
    review(client, "rmtm-Continue-once", ["original_continue_confirmed_once", "paused_before_next_day_execute"], {
        "original_predeath_boundary": "Continue scheduling checkpoint, not an immediately adjacent execute-time death witness",
        "no_native_player_death_Continue_credit": True,
    })
    predeath, predeath_verdict = _law_phase(client, "predeath")
    # Original driver schedules the successor before switching player and
    # killing the real predecessor. Observe actual new owner; never fix law/heir.
    for day in (5, 6, 7):
        original_day(client, "rmtm-D" + str(day), start, config["natural_game_day_limit"], allow_actor_change=True)
    review(client, "rmtm-real-succession", [
        "original_execute_time_expected_engine_heir_independently_proven", "real_predecessor_death",
        "same_full_later_title_recovery_original_callback", "actual_new_player_equals_expected_heir",
    ], {"predeath_qualification": predeath_verdict,
        "forbidden_credit": "Changing player is not predecessor-death proof; no fictitious public liveness API."})
    # The original execute effect schedules the two-day succession probe.
    # Its three pending families must exist before the physical postdeath join.
    postdeath, postdeath_verdict = _law_phase(client, "postdeath")
    for day in range(8, config["natural_game_day_limit"] + 1):
        raw = client.log_bytes()
        if b"RQA120: TEST DONE core" in raw:
            break
        original_day(client, "rmtm-D" + str(day), start, config["natural_game_day_limit"], allow_actor_change=True)
    debug = Path(client.output) / "rmtm-final-debug.log.raw"
    with debug.open("xb") as stream:
        stream.write(client.log_bytes())
    review(client, "rmtm-original-final-business", [
        "original_14day_cap", "same_full_title_personal_county_loyal_tree_and_nine_ministers",
        "two_real_offer_paths_and_refusals", "natural_both_title_timer_expiry",
        "original50_51_source_boundaries_and_actual_restoration_outcome",
    ], {"independent_threshold_UI_case_still_required": True})
    client.checkpoint("rmtm-verdict-input", {
        "d3": str(d3), "predeath": str(predeath), "postdeath": str(postdeath), "debug_log": pin(debug),
        "initial_date_raw": start, "last_date_raw": postdeath_verdict["date_raw"],
        "business_pass": False, "normal_close_pending": True,
        **({PHASE4_OPTION: phase4} if phase4 is not None else {}),
    })
    return {"status": "business_phases_observed_normal_close_pending", "business_pass": False,
            "law_phases": [d3_verdict, predeath_verdict, postdeath_verdict], "natural_day_cap": 14}


def verify_case(context):
    from tools import reclaim_the_motherland_effective_law_acceptance as caller
    output = Path(context["output"])
    validate_contract(context, require_prepared=True)
    if context["case"] == "threshold_ui":
        data = json.loads((output / "rmtm-threshold-verdict-input.json").read_text(encoding="utf-8-sig"))
        evidence = caller.phase_evidence(Path(data["d3"]))
        caller.load_helper().evaluate_phase(evidence)
        config = case_config(context)
        matches = data["actual_source_row"]["result"]["matches"]
        for literal, expected in [(item, 1) for item in config["required_markers"]] + [(item, 0) for item in config["forbidden_markers"]]:
            found = [row for row in matches if row["literal"] == literal]
            require(len(found) == 1 and found[0]["line_count"] == expected, "Original independent threshold source gate rejected")
        proofs = final_root_evidence(context, ["rmtm-threshold-50", "rmtm-threshold-51-and-production"])
        return {"case_contract_qualified": True, "gui_contract_qualified": True, "business_contract_applicable": True, "actual_threshold_source_and_GUI_observed": True,
                "actual_review_evidence": proofs, "business_pass": False, "requires_shared_normal_close": True,
                "full36_core_or_death_credit": False}
    data = json.loads((output / "rmtm-verdict-input.json").read_text(encoding="utf-8-sig"))
    require(pin(data["debug_log"]["path"]) == data["debug_log"], "Original final frozen log changed")
    verdict_path = output / "rmtm-original36-and-effective-law-verdict.json"
    args = SimpleNamespace(d3=Path(data["d3"]), predeath=Path(data["predeath"]),
                           postdeath=Path(data["postdeath"]), debug_log=Path(data["debug_log"]["path"]), output=verdict_path)
    code = caller.final(args, caller.load_helper())
    require(code == 0, "Original33 plus all three actual physical-gated families rejected")
    proofs = final_root_evidence(context, ["rmtm-C1-C5", "rmtm-Continue-once", "rmtm-real-succession", "rmtm-original-final-business"])
    if phase4_enabled(context):
        phase4 = data.get(PHASE4_OPTION)
        require(isinstance(phase4, dict) and set(phase4) == {"qualification", "probe_once"},
                "Enabled pre-send qualification missing from actual run")
        extra = final_root_evidence(context, [PHASE4_QUALIFY, PHASE4_SEND])
        require([phase4["qualification"], phase4["probe_once"]] == extra, "Actual phase4 review pins differ")
        d3 = caller.load_helper().evaluate_phase(caller.phase_evidence(Path(data["d3"])))
        validate_phase4_review(json.loads(Path(extra[0]["path"]).read_text(encoding="utf-8-sig")), d3)
        probe = json.loads(Path(extra[1]["path"]).read_text(encoding="utf-8-sig"))
        require(all(probe.get("facts", {}).get(key) is True for key in PHASE4_SEND_FACTS),
                "Actual once-only original GUI probe facts missing")
        proofs += extra
    else:
        require(PHASE4_OPTION not in data, "Run/verify phase4 option differs")
    return {"case_contract_qualified": True, "gui_contract_qualified": True, "business_contract_applicable": True, "marker_and_law_contract_qualified": True, "original_family_count": 36,
            "actual_review_evidence": proofs, "source_pass": False, "business_pass": False,
            "requires_shared_normal_close_and_independent_threshold_UI": True}
