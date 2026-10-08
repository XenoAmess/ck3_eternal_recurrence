"""TED core and immutable-save GUI tails on the single common runtime."""
from __future__ import annotations

import json
from pathlib import Path

from ._business import (case_config, check_evidence, final_root_evidence, literals,
                        observe, original_day, pin, require, review)


def prepare_case(context):
    from tools.ck3_mod_acceptance_prepare import (invoke_fixture_prepare, materialize_fixture_profile,
                                                  materialize_product_profile)
    repo = Path(context["repo_root"])
    inputs = context["case_inputs"]
    if context["case"] == "saved_gui_tail":
        # Host owns a single CLI load and save copy. This preparation has no
        # fixture registrar, source setup, war, or Save/Load replay.
        for key in ("prior_source13_evidence", "prior_save_load_evidence", "prior_s_contract_gui_evidence"):
            check_evidence(inputs[key])
        prepared = materialize_product_profile(context, inputs["product_dir"], inputs["plain_configuration"])
        require(prepared["product_file_count"] == 17 and prepared["fixture_mounted"] is False,
                "TED exact formal16 plus one outer descriptor required")
        saved = dict(context["saved_campaign"])
        require(set(saved) == {"save", "bytes", "sha256", "player_id", "date_raw", "product_inventory"},
                "Exactly six saved-campaign inputs required")
        check_evidence({"path": saved["save"], "bytes": saved["bytes"], "sha256": saved["sha256"]})
        saved["product_inventory"] = prepared["product_inventory"]["path"]
        return {"startup": {"mode": "saved_campaign", "state_dir": prepared["state_dir"], "saved_campaign": saved},
                "initial_plan": str(repo / "tools/ck3_mod_acceptance_cases/common_readonly_start.plan.json"),
                "fixtures": {"profile": prepared, "no_source_business_replay": True}, "business_pass": False}
    require(context["case"] == "core", "Independent production UI initializer is pending; never run core effects in its place")
    fixture = Path(context["run_dir"]) / "fixture"
    emitter = invoke_fixture_prepare(context, repo / "tools/prepare_tributary_expansion_1_20_fixture.py", [
        "--repo", repo, "--output", fixture,
    ])
    prepared = materialize_fixture_profile(context, fixture, inputs["product_dir"], inputs["plain_configuration"])
    return {"startup": {"mode": "fixture", "state_dir": prepared["state_dir"],
                        "fixture_start_policy": prepared["fixture_start_policy"]["path"],
                        "frontend_rules_plan": inputs["frontend_rules_plan"]},
            "initial_plan": str(repo / "tools/ck3_mod_acceptance_cases/common_readonly_start.plan.json"),
            "fixtures": {"emitter": emitter, "profile": prepared}, "business_pass": False}


def _saved_gui_tail(context, client):
    inputs = context["case_inputs"]
    frame, _ = observe(client, "ted-saved-tail-qualified")
    saved = context["saved_campaign"]
    require(frame["played_character"]["character_id"] == saved["player_id"] and frame["date_raw"] == saved["date_raw"],
            "Actual saved current actor/date differs; do not construct a fixture identity")
    # Target full ID is an explicitly reviewed immutable-save datum, not a
    # hard-coded historical county, name lookup, or guessed template ID.
    target = inputs["target_title_id"]
    require(type(target) is int and 0 < target < 0xFFFFFFFF, "Reviewed saved target full TitleID required")
    check_evidence(inputs["target_identity_evidence"])
    rows = client.execute_plan([
        {"id": "ted-saved-target-holder", "tool": "ck3_query_title_holder_v1", "args": {"title_id": target}, "fresh_revision": True},
        {"id": "ted-saved-target-camera", "tool": "ck3_center_map_on_landed_title_v1", "args": {"title_id": target}, "fresh_revision": True},
    ], "ted-saved-target-holder-camera")
    review(client, "ted-saved-GUI-tail", ["actual_target_county_holder_and_realm_GUI",
                                             "actual_attacker_to_defender_truce_direction_and_expiry_GUI"], {
        "actual_target_rows": rows, "saved_current_actor": frame["played_character"],
        "reviewed_expected_roles": inputs["expected_roles"],
        "reuse_only": {key: inputs[key] for key in ("prior_source13_evidence", "prior_save_load_evidence", "prior_s_contract_gui_evidence")},
        "no_repeat": ["source13", "setup", "war", "SaveLoad", "advance five years"],
        "next": "Normal menu Quit; retained actual OS0/native0 remains a separate shared lifecycle gate.",
    })
    client.checkpoint("ted-verdict-input", {"case": "saved_gui_tail", "business_pass": False,
                                           "normal_close_pending": True, "prior_evidence": {
                                               key: inputs[key] for key in ("prior_source13_evidence", "prior_save_load_evidence", "prior_s_contract_gui_evidence")}})
    return {"status": "original_missing_GUI_observed_normal_close_pending", "business_pass": False,
            "source13_and_SaveLoad_replayed": False}


def run_case(context, client):
    client.wait_hold()
    if context["case"] == "saved_gui_tail":
        return _saved_gui_tail(context, client)
    require(context["case"] == "core", "Production UI must use its own original qualified initializer")
    config = case_config(context)
    initial, _ = observe(client, "ted-D0-qualified")
    # Preserve the existing two hidden daily setup/attacker callbacks. TED has
    # no invented RMTM fourteen-day cap and actor change is an actual source step.
    for day in (1, 2):
        original_day(client, "ted-D" + str(day), initial["date_raw"], allow_actor_change=True)
    source = literals(client, "ted-original13", config["required_markers"], config["forbidden_markers"])
    client.checkpoint("ted-original13-actual-row", source)
    review(client, "ted-real-war-and-save-load", [
        "actual_attacker_defender_target_and_participants", "real_war_surrender",
        "attacker_to_defender_directed_truce_and_actual_expiry", "target_defender_side_holder_and_realm",
        "Song_direct_tributary_attacker_and_real_contract_GUI",
        "actual_same_PID_GUI_Save_then_Load_and_independent_before_after_facts",
    ], {"original_source13": source, "original_GAP_retained": config["retain_gap"],
        "no_fake_tools": "war/truce/wallet use existing actual GUI; no invented typed provider",
        "same_PID_note": "A CLI restore or replacement PID is not same-live GUI SaveLoad credit."})
    client.checkpoint("ted-verdict-input", {"case": "core", "original13": pin(Path(client.output) / "ted-original13-actual-row.json"),
                                           "business_pass": False, "normal_close_pending": True})
    return {"status": "original_core_and_real_tail_observed_normal_close_pending", "original_source_marker_count": 13,
            "business_pass": False, "production_UI_case_still_required": True}


def verify_case(context):
    data = json.loads((Path(context["output"]) / "ted-verdict-input.json").read_text(encoding="utf-8-sig"))
    if data["case"] == "saved_gui_tail":
        for row in data["prior_evidence"].values():
            check_evidence(row)
        proofs = final_root_evidence(context, ["ted-saved-GUI-tail"])
        return {"case_contract_qualified": True, "original_remaining_GUI_contract_observed": True, "prior_evidence": data["prior_evidence"],
                "actual_review_evidence": proofs, "business_pass": False,
                "requires_shared_normal_close_and_independent_production_UI": True}
    config = case_config(context)
    check_evidence(data["original13"])
    row = json.loads(Path(data["original13"]["path"]).read_text(encoding="utf-8-sig"))
    matches = row["result"]["matches"]
    require(row["ok"] is True and not row.get("error"), "Original13 actual query failed")
    for literal, count in [(value, 1) for value in config["required_markers"]] + [(value, 0) for value in config["forbidden_markers"]]:
        found = [item for item in matches if item.get("literal") == literal]
        require(len(found) == 1 and found[0]["line_count"] == count, "Original13 actual exact marker gate rejected")
    proofs = final_root_evidence(context, ["ted-real-war-and-save-load"])
    return {"case_contract_qualified": True, "original13_and_real_tail_contract_observed": True, "original_source_marker_count": 13,
            "actual_review_evidence": proofs, "business_pass": False,
            "requires_shared_normal_close_and_independent_production_UI": True}
