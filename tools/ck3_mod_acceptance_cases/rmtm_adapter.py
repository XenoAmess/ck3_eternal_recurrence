"""RMTM original business phases on the one selected common runtime."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json

from ._business import (case_config, final_root_evidence, literals, observe,
                        original_day, pin, require, review, write_once)


def prepare_case(context):
    from tools.ck3_mod_acceptance_prepare import invoke_fixture_prepare, materialize_fixture_profile
    config = case_config(context)
    require(context["case"] in ("core", "threshold_ui"), "Unknown original RMTM case")
    days = config["fixture_recent_independence_override_days"]
    require(type(days) is int and 10 <= days <= 30, "Use the existing producer timer admission")
    require(config["natural_game_day_limit"] == 14, "Original fourteen-day cap is required")
    repo = Path(context["repo_root"])
    fixture = Path(context["run_dir"]) / "fixture"
    arguments = [
        "--repo", repo, "--output", fixture, "--ui-checkpoints",
        "--compressed-days", str(days), "--game-dir", context["game_dir"],
    ]
    if context["case"] == "threshold_ui":
        arguments.append("--threshold-ui")
    emitter = invoke_fixture_prepare(context, repo / "tools/prepare_reclaim_the_motherland_1_20_fixture.py", arguments)
    prepared = materialize_fixture_profile(context, fixture, context["case_inputs"]["product_dir"],
                                           context["case_inputs"]["plain_configuration"])
    return {"startup": {"mode": "fixture", "state_dir": prepared["state_dir"],
                        "fixture_start_policy": prepared["fixture_start_policy"]["path"],
                        "frontend_rules_plan": context["case_inputs"]["frontend_rules_plan"]},
            "initial_plan": str(repo / "tools/ck3_mod_acceptance_cases/common_readonly_start.plan.json"),
            "fixtures": {"emitter": emitter, "profile": prepared,
                         "compressed_days": days, "natural_day_cap": 14},
            "business_pass": False}


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
         "args": law.phase_literals(phase), "fresh_revision": True},
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
    client.wait_hold()
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
    if context["case"] == "threshold_ui":
        return _threshold_ui_case(context, client)
    config = case_config(context)
    require(context["case"] == "core", "Independent threshold adapter remains pending")
    client.wait_hold()
    initial, _ = observe(client, "rmtm-D0-qualified")
    start = initial["date_raw"]
    for day in (1, 2, 3):
        original_day(client, "rmtm-D" + str(day), start, config["natural_game_day_limit"])
    d3, d3_verdict = _law_phase(client, "d3")
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
    })
    return {"status": "business_phases_observed_normal_close_pending", "business_pass": False,
            "law_phases": [d3_verdict, predeath_verdict, postdeath_verdict], "natural_day_cap": 14}


def verify_case(context):
    from tools import reclaim_the_motherland_effective_law_acceptance as caller
    output = Path(context["output"])
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
    return {"case_contract_qualified": True, "gui_contract_qualified": True, "business_contract_applicable": True, "marker_and_law_contract_qualified": True, "original_family_count": 36,
            "actual_review_evidence": proofs, "source_pass": False, "business_pass": False,
            "requires_shared_normal_close_and_independent_threshold_UI": True}
