#!/usr/bin/env python3
"""Prepare RMTM's disposable official-engine fixture; never launch or inject CK3."""
from __future__ import annotations

import argparse
import codecs
import json
from pathlib import Path

import fixture_engine_prepare as prep
import reclaim_the_motherland_scope_witness as witness

START = 'on_game_start_after_lobby = { on_actions = { rqa120_start } }\nrqa120_start = {\n    effect = {\n        debug_log = "RQA120: TEST BEGIN engine_startup"\n        set_global_variable = rqa120_stock_join_dispatch_armed\n        rqa120_try_dispatch_after_stock_join_effect = yes\n    }\n}\n'

STOCK_JOIN_HELPER = 'rqa120_try_dispatch_after_stock_join_effect = {\n    if = {\n        limit = {\n            exists = global_var:rqa120_stock_join_dispatch_armed\n            NOT = { exists = global_var:rqa120_stock_join_dispatched }\n        }\n        character:han_8052 = {\n            if = {\n                limit = {\n                    has_title = title:h_china\n                    any_character_situation = { situation_type = dynastic_cycle }\n                }\n                if = {\n                    limit = { exists = top_participant_group:dynastic_cycle }\n                    top_participant_group:dynastic_cycle = {\n                        if = {\n                            limit = { participant_group_type = hegemon_ruler }\n                            # Disarm before the original initializer can recalculate groups.\n                            set_global_variable = rqa120_stock_join_dispatched\n                            remove_global_variable = rqa120_stock_join_dispatch_armed\n                            debug_log = "RQA_INIT_DIAG_V1 real_song_membership_dispatch_once"\n                            random_player = { trigger_event = { id = rqa120.1 } }\n                        }\n                        else = { debug_log = "RQA_INIT_DIAG_V1 waiting_song_hegemon_type" }\n                    }\n                }\n                else = { debug_log = "RQA_INIT_DIAG_V1 waiting_song_top_group" }\n            }\n            else = { debug_log = "RQA_INIT_DIAG_V1 waiting_song_real_membership" }\n        }\n    }\n}\n'
STOCK_JOIN_HOOK = '\t\t\t\t# RQA external fixture: observe real engine membership, never create it.\n\t\t\t\tif = {\n\t\t\t\t\tlimit = { this = character:han_8052 }\n\t\t\t\t\tdebug_log = "RQA_INIT_DIAG_V1 stock_hegemon_on_join_song"\n\t\t\t\t\trqa120_try_dispatch_after_stock_join_effect = yes\n\t\t\t\t}'
STOCK_START_HOOK = '\t\t# RQA external fixture: observe completed stock initial setup; never create membership.\n\t\tdebug_log = "RQA_INIT_DIAG_V1 stock_on_start_completed_dispatch_check"\n\t\trqa120_try_dispatch_after_stock_join_effect = yes'
STOCK_NATURAL_CHAOS_HOOK = '\t\t\t\t\t\t# RQA observer only: the preceding stock statement emitted the natural event.\n\t\t\t\t\t\tif = {\n\t\t\t\t\t\t\tlimit = {\n\t\t\t\t\t\t\t\tthis = character:han_8052\n\t\t\t\t\t\t\t\thas_character_flag = rqa_waiting_for_chaos\n\t\t\t\t\t\t\t\tNOT = { has_character_flag = rqa120_natural_chaos_callback_observed }\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\tadd_character_flag = rqa120_natural_chaos_callback_observed\n\t\t\t\t\t\t\tdebug_log = "RQA_INIT_DIAG_V2 natural_chaos_callback_observed_once"\n\t\t\t\t\t\t}'


def project_stock_observers(game_dir: Path) -> tuple[str, dict]:
    """Append only the three qualified observers to the selected actual stock file."""
    source = game_dir / "game/common/situation/situations/tgp_dynastic_cycle.txt"
    raw = source.read_bytes()
    stock = raw.decode("utf-8-sig").replace("\r\n", "\n")
    if any(token in stock for token in ("rqa120_", "RQA_INIT_DIAG")):
        raise ValueError("stock input already contains an acceptance overlay")
    groups = prep.balanced_excerpt(stock, r"^\tparticipant_groups\s*=\s*\{")
    group = prep.balanced_excerpt(groups, r"^\t\thegemon_ruler\s*=\s*\{")
    join = prep.balanced_excerpt(group, r"^\s*on_join\s*=\s*\{")
    joined = join[:join.rfind("}")] + STOCK_JOIN_HOOK + "\n\t\t\t" + join[join.rfind("}"):]
    stock = prep.replace_once(stock, group, prep.replace_once(group, join, joined))
    start = prep.balanced_excerpt(stock, r"^\ton_start\s*=\s*\{")
    started = start[:start.rfind("}")] + STOCK_START_HOOK + "\n\t" + start[start.rfind("}"):]
    stock = prep.replace_once(stock, start, started)
    marker = "trigger_event = tgp_dynastic_cycle.0081 # China shatters"
    stock = prep.replace_once(stock, marker, marker + "\n" + STOCK_NATURAL_CHAOS_HOOK)
    return stock, {"file": "game/common/situation/situations/tgp_dynastic_cycle.txt",
                   "stock_file_sha256": prep.digest(source), "observer_hooks": 3,
                   "changes_membership_or_repeats_event": False}

CONTINUE = '''rqa120_continue_decision = {
    picture = { reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }
    decision_group_type = rqa_acceptance
    sort_order = 1
    ai_check_interval = 0
    desc = rqa120_continue_decision_desc
    selection_tooltip = rqa120_continue_decision_tooltip
    is_shown = { is_ai = no has_character_flag = rqa120_ui_checkpoint }
    is_valid = { rmtm_holds_restoration_hegemony_trigger = yes }
    effect = {
        rqa_observe_predeath_law_effect = yes
        remove_character_flag = rqa120_ui_checkpoint
        set_variable = { name = rqa120_stage value = 5 }
        trigger_event = { id = rqa120.2 days = 1 }
    }
    ai_potential = { always = no }
}
'''


PHASE4_OPTION = "phase4_pre_send_gui_qualification"
PHASE4_READY = "RQA120: TEST READY phase4_pre_send_gui_qualification"
PHASE4_SEND = b"            rqa_execute_vassalization_probe_effect = yes\n"
PHASE4_WAIT = ('            debug_log = "' + PHASE4_READY + '"\n').encode("ascii")
PHASE4_PROBE = "rqa_execute_vassalization_probe_gui"
PHASE4_GUI_RELATIVE = "gui/rqa120_phase4_manual.gui"
PHASE4_MANUAL_GUI = '''window = {
    name = "rqa120_phase4_manual_window"
    alwaystransparent = yes
    size = { 560 180 }
    layer = tutorial
    parentanchor = top
    position = { 0 80 }
    visible = "[GetPlayer.IsValid]"
    vbox = {
        alwaystransparent = yes
        size = { 100% 100% }
        visible = "[GetScriptedGui('rqa_execute_vassalization_probe_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        text_multi = { text = "rqa120_phase4_instructions" autoresize = yes }
        text_multi = { text = "[GetPlayer.MakeScope.Var('rqa_vassalization_target_a').Char.GetShortUIName]" autoresize = yes }
        text_multi = { raw_text = "A character_id=[GetPlayer.MakeScope.Var('rqa_vassalization_target_a').Char.GetID] primary_title_id=[GetPlayer.MakeScope.Var('rqa_vassalization_target_a').Char.GetPrimaryTitle.GetID]" autoresize = yes }
        text_multi = { text = "[GetPlayer.MakeScope.Var('rqa_vassalization_target_b').Char.GetShortUIName]" autoresize = yes }
        text_multi = { raw_text = "B character_id=[GetPlayer.MakeScope.Var('rqa_vassalization_target_b').Char.GetID] primary_title_id=[GetPlayer.MakeScope.Var('rqa_vassalization_target_b').Char.GetPrimaryTitle.GetID]" autoresize = yes }
        button_standard = {
            name = "rqa120_phase4_original_probe_once"
            size = { 100% 40 }
            text = "rqa120_phase4_original_probe_once"
            onclick = "[GetScriptedGui('rqa_execute_vassalization_probe_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
        }
    }
}
'''


FOCUSED_OPTION = "focused_keypaths"
FOCUSED_DONE = "RQA120: TEST DONE owned_core"
FOCUSED_EDITS = (
    (PHASE4_SEND, b"            add_character_flag = rqa_ready_for_succession # owned keypaths; no vanilla Offer probe\n"),
    (b"            limit = { var:rqa120_stage = 4 has_character_flag = rqa_waiting_for_vassalization_probe }\n",
     b"            limit = { var:rqa120_stage = 4 has_character_flag = rqa_ready_for_succession } # owned keypaths\n"),
    (b"            rqa_verify_vassalization_probe_effect = yes\n",
     b"            # owned keypaths: no stochastic vanilla double-refusal assertion\n"),
    (b"                var:rqa_defecting_direct.primary_title = {\n"
     b"                    NOT = { exists = var:rmtm_recently_independent_from_restoration_hegemony }\n"
     b"                }\n"
     b"                var:rqa_control_ruler.primary_title = {\n"
     b"                    NOT = { exists = var:rmtm_recently_independent_from_restoration_hegemony }\n"
     b"                }\n",
     b"                # owned core completes after the original succession aggregate, not timer expiry\n"),
    (b"            rqa_verify_recent_independence_expiry_effect = yes\n"
     b"            add_character_flag = rqa_threshold_pending\n"
     b"            rqa_prepare_threshold_effect = yes\n"
     b"            set_variable = { name = rqa120_stage value = 7 }\n",
     b"            set_variable = { name = rqa120_stage value = 99 }\n"
     b'            debug_log = "' + FOCUSED_DONE.encode("ascii") + b'"\n'),
)


def focused_project(raw: bytes, *, inverse=False) -> bytes:
    """Skip vanilla Offer and duplicate expiry/threshold tail; keep succession timing."""
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    for before, after in FOCUSED_EDITS:
        before, after = (value.replace(b"\n", newline) for value in (before, after))
        old, new = (after, before) if inverse else (before, after)
        if raw.count(old) != 1 or new in raw:
            raise ValueError("Exact owned-keypaths fixture anchor changed")
        raw = raw.replace(old, new, 1)
    return raw


def focused_projection_receipt(raw: bytes, projected: bytes) -> dict:
    inverse = focused_project(projected, inverse=True)
    if inverse != raw or focused_project(raw) != projected:
        raise ValueError("Owned-keypaths inverse changed the original fixture")
    return {"schema": "rmtm-owned-keypaths-fixture-projection-v1", "enabled": True,
            "original_driver": witness.byte_pin(raw), "projected_driver": witness.byte_pin(projected),
            "inverse_driver": witness.byte_pin(inverse), "inverse_byte_exact": True,
            "vanilla_offer_actions_executed": False, "production_modified": False,
            "scope_dump_count_unchanged": 3,
            "completion_scope": "original succession aggregate only; independent threshold UI remains required",
            "completion_marker": FOCUSED_DONE,
            "runtime_status": "NOT_RUN", "business_pass": False}


def phase4_enabled(value=False, *, ui_checkpoints=True, threshold_ui=False) -> bool:
    if type(value) is not bool:
        raise ValueError("phase4_pre_send_gui_qualification must be a strict JSON boolean")
    if value and (not ui_checkpoints or threshold_ui):
        raise ValueError("phase4 pre-send qualification requires core with UI checkpoints")
    return value


def phase4_project(raw: bytes, *, inverse=False) -> bytes:
    """Exchange only the original stage3 send line; no timer/effect changes."""
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    send, wait = (line.replace(b"\n", newline) for line in (PHASE4_SEND, PHASE4_WAIT))
    old, new = (wait, send) if inverse else (send, wait)
    if raw.count(old) != 1 or new in raw:
        raise ValueError("Exact unique phase4 stage3 projection anchor changed")
    return raw.replace(old, new, 1)


def phase4_support(source: Path) -> dict[str, bytes]:
    """Load one unchanged original ScriptedGui, never the automatic bridge."""
    original = (source / "common/scripted_guis/rqa_guis.txt").read_bytes()
    block = prep.balanced_excerpt(original.decode("utf-8-sig"),
                                  r"^rqa_execute_vassalization_probe_gui\s*=\s*\{")
    payload = block.encode("utf-8")
    if payload not in original:
        raise ValueError("Original probe GUI excerpt is not byte-exact")
    support = {
        "common/scripted_guis/rqa120_phase4_probe_gui.txt": codecs.BOM_UTF8 + payload + b"\n",
        PHASE4_GUI_RELATIVE: PHASE4_MANUAL_GUI.encode("utf-8-sig"),
        "gui/scripted_widgets/rqa120_phase4_manual.txt": (
            PHASE4_GUI_RELATIVE + " = rqa120_phase4_manual_window\n").encode("utf-8-sig"),
    }
    for language, instructions, button in (
        ("english", "Inspect both original targets' default Offer Vassalization scores and complete reasons; Cancel both. Only after the operator qualifies both negative totals, send the original probe once.", "Send ORIGINAL A/B probe once"),
        ("simp_chinese", "先核原目标A/B的默认提议附庸完整理由及负总分，分别取消。仅在操作者确认两人资格后，单击一次原始探针。", "仅发送一次原始A/B探针"),
    ):
        support[f"localization/{language}/rqa120_phase4_l_{language}.yml"] = (
            f'l_{language}:\n rqa120_phase4_instructions:0 "{instructions}"\n'
            f' rqa120_phase4_original_probe_once:0 "{button}"\n').encode("utf-8-sig")
    return support


def phase4_projection_receipt(source: Path, raw: bytes, projected: bytes,
                              support: dict[str, bytes]) -> dict:
    inverse = phase4_project(projected, inverse=True)
    if inverse != raw or projected != phase4_project(raw):
        raise ValueError("Phase4 inverse did not restore the complete original driver")
    return {
        "schema": "rmtm-phase4-pre-send-gui-qualification-projection-v1",
        "enabled": True, "runtime_status": "NOT_RUN", "business_pass": False,
        "original_driver": witness.byte_pin(raw), "projected_driver": witness.byte_pin(projected),
        "inverse_driver": witness.byte_pin(inverse), "inverse_byte_exact": True,
        "original_probe_source": {"path": str((source / "common/scripted_guis/rqa_guis.txt").resolve()),
                                  "sha256": prep.digest(source / "common/scripted_guis/rqa_guis.txt")},
        "added_files": {name: witness.byte_pin(value) for name, value in support.items()},
        "automatic_probe_action": False, "canonical_business_effects_modified": False,
        "original_d4_two_refusals_still_required": True, "scope_dump_count_unchanged": 3,
        "target_selection": "same original A/B; unknown/nonnegative/mismatched target stops as GAP; never reselect",
        "default_flags_semantics": "Actual GUI readback required; no inferred ai_accept syntax or ACK credit",
    }


def event(name: str, body: str) -> str:
    return f"{name} = {{\n    type = character_event\n    hidden = yes\n    immediate = {{\n{body}\n    }}\n}}\n"


def events(ui_checkpoints: bool) -> str:
    initialize = '''        add_character_flag = rqa_initialize_pending
        rqa_initialize_effect = yes
        random_player = {
            set_variable = { name = rqa120_stage value = 1 }
            set_variable = { name = rqa120_ticks value = 0 }
            trigger_event = { id = rqa120.2 days = 1 }
        }'''
    checkpoint = ('''            add_character_flag = rqa120_ui_checkpoint
            set_variable = { name = rqa120_stage value = 90 }
            debug_log = "RQA120: TEST READY ui_after_chaos"''' if ui_checkpoints else
                  '''            rqa_observe_predeath_law_effect = yes
            set_variable = { name = rqa120_stage value = 5 }''')
    tick = '''        change_variable = { name = rqa120_ticks add = 1 }
        if = {
            limit = { var:rqa120_stage = 1 has_character_flag = rqa_ready_to_enter_chaos }
            add_character_flag = rqa_chaos_pending
            rqa_enter_chaos_effect = yes
            set_variable = { name = rqa120_stage value = 2 }
        }
        else_if = {
            limit = { var:rqa120_stage = 2 has_character_flag = rqa_dispatch_chaos_event_pending }
            rqa_dispatch_chaos_event_effect = yes
            set_variable = { name = rqa120_stage value = 3 }
        }
        else_if = {
            limit = {
                var:rqa120_stage = 3
                has_character_flag = rqa_waiting_for_chaos
                NOT = { has_title = title:h_china }
                rmtm_holds_restoration_hegemony_trigger = yes
            }
            rqa_verify_chaos_effect = yes
            if = {
                limit = {
                    government_has_flag = government_is_celestial
                    government_has_flag = government_uses_ministry_budget
                    tgp_has_access_to_ministry_trigger = yes
                    primary_title = global_var:rmtm_ministry_entitlement_title
                }
                debug_log = "RQA120: TEST PASS later_ministry_budget_gate"
            }
            else = { debug_log = "RQA120: TEST FAIL later_ministry_budget_gate" }
            rqa_execute_vassalization_probe_effect = yes
            set_variable = { name = rqa120_stage value = 4 }
        }
        else_if = {
            limit = { var:rqa120_stage = 4 has_character_flag = rqa_waiting_for_vassalization_probe }
            rqa_verify_vassalization_probe_effect = yes
CHECKPOINT
        }
        else_if = {
            limit = { var:rqa120_stage = 5 has_character_flag = rqa_ready_for_succession }
            primary_title.current_heir = {
                set_variable = { name = rqa120_stage value = 6 }
                set_variable = { name = rqa120_ticks value = 0 }
                trigger_event = { id = rqa120.2 days = 3 }
            }
            add_character_flag = rqa_succession_pending
            # The existing effect changes the player and kills this predecessor.
            rqa_execute_succession_effect = yes
            set_variable = { name = rqa120_stage value = 99 }
        }
        else_if = {
            limit = {
                var:rqa120_stage = 6
                has_character_flag = rqa_waiting_for_recent_independence_expiry
                var:rqa_defecting_direct.primary_title = {
                    NOT = { exists = var:rmtm_recently_independent_from_restoration_hegemony }
                }
                var:rqa_control_ruler.primary_title = {
                    NOT = { exists = var:rmtm_recently_independent_from_restoration_hegemony }
                }
            }
            rqa_verify_recent_independence_expiry_effect = yes
            add_character_flag = rqa_threshold_pending
            rqa_prepare_threshold_effect = yes
            set_variable = { name = rqa120_stage value = 7 }
        }
        else_if = {
            limit = { var:rqa120_stage = 7 has_character_flag = rqa_waiting_for_restoration }
            rqa120_production_restoration_effect = yes
            if = {
                limit = { NOT = { exists = var:rqa_later_title.holder } }
                debug_log = "RQA120: TEST PASS restoration_later_title_unheld"
            }
            else = { debug_log = "RQA120: TEST FAIL restoration_later_title_unheld" }
            rqa_verify_restoration_effect = yes
            set_variable = { name = rqa120_stage value = 99 }
            debug_log = "RQA120: TEST DONE core"
        }
        if = {
            limit = { is_alive = yes var:rqa120_stage < 90 }
            if = {
                limit = { var:rqa120_ticks < 60 }
                trigger_event = { id = rqa120.2 days = 1 }
            }
            else = {
                debug_log = "RQA120: TEST FAIL driver_timeout"
                set_variable = { name = rqa120_stage value = 99 }
            }
        }'''.replace("CHECKPOINT", checkpoint)
    return "namespace = rqa120\n\n" + event("rqa120.1", initialize) + "\n" + event("rqa120.2", tick)


def prepare(repo: Path, output: Path, ui_checkpoints: bool, duration: int, game_dir: Path | None = None, threshold_ui: bool = False, formal_product_dir: Path | None = None, phase4_pre_send_gui_qualification: bool = False, focused_keypaths: bool = False) -> dict:
    qualified_phase4 = phase4_enabled(phase4_pre_send_gui_qualification,
                                    ui_checkpoints=ui_checkpoints, threshold_ui=threshold_ui)
    if type(focused_keypaths) is not bool or (focused_keypaths and (qualified_phase4 or not ui_checkpoints)):
        raise ValueError("Owned keypaths require UI checkpoints without the legacy Offer qualification")
    if formal_product_dir is None:
        raise ValueError("Scope-witness callback projection requires the selected formal product directory")
    formal_event = formal_product_dir.resolve() / witness.CALLBACK_RELATIVE
    fixture_source = repo / "tools/fixtures/reclaim_the_motherland_acceptance" / witness.FIXTURE_RELATIVE
    projected_fixture, fixture_proof = witness.project(fixture_source.read_bytes(), "execute")
    projected_event, callback_proof = witness.project(formal_event.read_bytes(), "callback")
    scope_witness_proof = {
        "schema": "rmtm-readonly-succession-scope-witness-projection-v1",
        "projector": {"path": str(Path(witness.__file__).resolve()), "sha256": prep.digest(Path(witness.__file__))},
        "scope_dump_count": 3, "temporary_scopes_and_logs_only": True,
        "scope_dump_count_basis": "One original fixture execute and one original hidden rmtm.2001 callback; duplicates are not suppressed or credited",
        "callback_observer_guard": "Existing fixture rqa_waiting_for_succession flag; original product call is not guarded",
        "formal_staging_modified": False,
        "effective_formal_file_override": witness.CALLBACK_RELATIVE,
        "fixture_overlay_loaded_after_formal_product": True,
        "projections": [
            {"relative": witness.FIXTURE_RELATIVE, "source_path": str(fixture_source.resolve()), **fixture_proof},
            {"relative": witness.CALLBACK_RELATIVE, "source_path": str(formal_event), **callback_proof},
        ],
        "current_build_scope_dump_format": "NOT_OBSERVED",
        "runtime_status": "NOT_RUN", "business_pass": False,
    }
    repo, output = prep.checked_output(repo, output)
    if not 10 <= duration <= 30:
        raise ValueError("compressed political-memory duration must be between 10 and 30 days")
    source = repo / "tools/fixtures/reclaim_the_motherland_acceptance"
    files = [source / "descriptor.mod", source / "common/scripted_effects/rqa_effects.txt",
             source / "common/scripted_triggers/rqa_triggers.txt", source / "common/script_values/rqa_values.txt",
             source / "common/decision_group_types/rqa_decision_group_types.txt", source / "events/rqa_events.txt",
             *sorted((source / "localization").rglob("*.yml"))]
    prep.copy_files(source, output, files)
    (output / witness.FIXTURE_RELATIVE).write_bytes(projected_fixture)
    with (output / witness.CALLBACK_RELATIVE).open("xb") as stream:
        stream.write(projected_event)
    prep.write_script(output, "common/script_values/rqa_values.txt",
                      f"# External acceptance-only timer compression: production remains 1825 days.\nrmtm_recent_independence_duration_days = {duration}\n")
    body, proof = prep.decision_effect(repo, "mod_reclaim_the_motherland", "common/decisions/rmtm_restoration_decisions.txt", "rmtm_claim_restoration_decision")
    prep.write_script(output, "common/scripted_effects/rqa120_production_effects.txt", f"# Exact production decision-effect excerpt; UI/validity is not executed.\nrqa120_production_restoration_effect = {{\n{body}\n}}\n")
    stock, stock_proof = project_stock_observers(game_dir or repo / "Crusader Kings III")
    prep.write_script(output, "common/situation/situations/tgp_dynastic_cycle.txt", stock)
    with (output / "common/scripted_effects/rqa120_production_effects.txt").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("\n" + STOCK_JOIN_HELPER)
    prep.write_script(output, "common/on_action/rqa120_on_actions.txt", START)
    original_driver = events(ui_checkpoints).encode("utf-8-sig")
    phase4_receipt = {}
    if focused_keypaths:
        projected_driver = focused_project(original_driver)
        phase4_receipt[FOCUSED_OPTION] = focused_projection_receipt(original_driver, projected_driver)
        with (output / "events/rqa120_events.txt").open("xb") as stream:
            stream.write(projected_driver)
    elif qualified_phase4:
        projected_driver = phase4_project(original_driver)
        support = phase4_support(source)
        phase4_receipt[PHASE4_OPTION] = phase4_projection_receipt(source, original_driver, projected_driver, support)
        with (output / "events/rqa120_events.txt").open("xb") as stream:
            stream.write(projected_driver)
        for relative, raw in support.items():
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
    else:
        prep.write_script(output, "events/rqa120_events.txt", events(ui_checkpoints))
    if ui_checkpoints:
        prep.write_script(output, "common/decisions/rqa120_decisions.txt", CONTINUE)
        for language, title, confirm, description in (
            ("english", "Continue RMTM Core Acceptance", "Continue with the succession", "Observe the ministry budget and offer acceptance reasons first. Released targets: [ROOT.Var('rqa_vassalization_target_a').Char.GetShortUIName] and [ROOT.Var('rqa_vassalization_target_b').Char.GetShortUIName]. Continue after capturing the UI."),
            ("simp_chinese", "继续重整河山核心验收", "继续继承验收", "先查看三省六部预算与提议附庸的接受理由。已释放目标：[ROOT.Var('rqa_vassalization_target_a').Char.GetShortUIName]、[ROOT.Var('rqa_vassalization_target_b').Char.GetShortUIName]。完成界面取证后继续。"),
        ):
            if focused_keypaths:
                description = ("Inspect the Later title, retained personal/loyal realm and nine ministers; inspect then cancel the budget. Continue once for real succession." if language == "english" else
                               "先核后朝头衔、保留的亲领与忠臣树及九席；预算只查看并取消。取证后仅继续一次真实继承。")
            loc = f'l_{language}:\n rqa120_continue_decision:0 "{title}"\n rqa120_continue_decision_desc:0 "{description}"\n rqa120_continue_decision_tooltip:0 "{title}"\n rqa120_continue_decision_confirm:0 "{confirm}"\n'
            prep.write_script(output, f"localization/{language}/rqa120_l_{language}.yml", loc)
    if threshold_ui:
        if not ui_checkpoints:
            raise ValueError("threshold UI requires the original stage4 checkpoint")
        ui_source = source / "ui"
        if len([path for path in ui_source.rglob("*") if path.is_file()]) != 4:
            raise ValueError("all four original threshold UI data files are required")
        for path in sorted(ui_source.rglob("*")):
            if path.is_file():
                target = output / path.relative_to(ui_source)
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(path.read_bytes())
    markers = prep.required_markers(repo / "tools/run_reclaim_the_motherland_acceptance.py")
    # These three family credits require the actual managed-row physical gate.
    pending_families = [
        ("TEST", "later_dynasty_single_heir_law_and_heir_ready"),
        ("PROBE", "phase3_succession_title"),
        ("TEST", "phase3_later_dynasty_realm_and_ministry_inherited"),
    ]
    old_law_markers = {f"RQA: {kind} PASS {name}" for kind, name in pending_families}
    markers = [marker for marker in markers if marker not in old_law_markers]
    if focused_keypaths:
        markers = [marker for marker in markers if not any(name in marker for name in (
            "phase4_offer_vassalization_paths_valid", "phase4_two_released_rulers_refused_immediate_vassalization",
            "phase4_recent_independence_expired", "china_control_reset", "fifty_percent_below_claim_threshold",
            "original_fifty_one_percent_threshold_reached", "restoration_decision_ready",
            "original_mandate_effect_plus_later_title_destroyed", "TEST DONE reclaim"))]
    markers += [f"RQA: {kind} PENDING_PHYSICAL {name}" for kind, name in pending_families]
    effective_law_contract = {
        "schema": "rmtm-effective-single-heir-actual-rows-v1",
        "helper": "tools/reclaim_the_motherland_effective_law_contract.py",
        "helper_sha256": prep.digest(repo / "tools/reclaim_the_motherland_effective_law_contract.py"),
        "actual_rows_caller": "tools/reclaim_the_motherland_effective_law_acceptance.py",
        "actual_rows_caller_sha256": prep.digest(repo / "tools/reclaim_the_motherland_effective_law_acceptance.py"),
        "phases": ["d3", "predeath", "postdeath"],
        "physical_pending_families": [name for _, name in pending_families],
        "credit_requires_recomputed_three_phase_AND": True,
        "predeath_boundary": "Continue/stage4 scheduling checkpoint; original next-day execute-time heir and real predecessor death must be proven separately",
        "source_pass": False,
        "business_pass": False,
    }
    markers += ["RQA120: TEST BEGIN engine_startup", "RQA120: TEST PASS later_ministry_budget_gate"]
    markers += ([FOCUSED_DONE] if focused_keypaths else
                ["RQA120: TEST PASS restoration_later_title_unheld", "RQA120: TEST DONE core"])
    if ui_checkpoints:
        markers.append("RQA120: TEST READY ui_after_chaos")
    core_markers = list(markers)
    if threshold_ui:
        markers = ["RQA120: TEST BEGIN engine_startup", "RQA120: TEST READY ui_after_chaos",
                   "RQAUI: TEST PASS china_control_reset",
                   "RQAUI: TEST PASS fifty_percent_below_claim_threshold",
                   "RQAUI: TEST READY actual_restoration_50_ui",
                   "RQAUI: TEST PASS original_fifty_one_percent_threshold_reached",
                   "RQAUI: TEST PASS restoration_decision_ready",
                   "RQAUI: TEST READY actual_restoration_51_ui",
                   "RQAUI: TEST PASS actual_production_restoration_effect_observed",
                   "RQAUI: TEST DONE threshold_ui"]
    return prep.finish_receipt(repo, source, output, files, {
        "product":"mod_reclaim_the_motherland", "ui_checkpoints":ui_checkpoints, "threshold_ui":threshold_ui,
        "effective_law_contract":effective_law_contract,
        "scope_witness_projection":scope_witness_proof,
        **phase4_receipt,
        "core_marker_inventory":core_markers if threshold_ui else None,
        "threshold_UI_does_not_credit_core36":threshold_ui,
        "bookmark":"1066-09-15; begin as any human ruler except the Song emperor",
        "entry":"on_game_start_after_lobby -> rqa120.1 -> daily hidden rqa120.2; successor driver is explicitly scheduled before predecessor death",
        "expected_game_days":8 if focused_keypaths and not threshold_ui else duration + 2, "max_game_days":14,
        "completion_within_day_cap":"must be proved by actual markers; configured duration does not grant expiry credit",
        "game_rules":{"rmtm_hegemon_fate":"rmtm_reclaim_the_motherland", "rmtm_pro_hegemon_choice":"rmtm_divided_hearts"},
        "required_markers":markers, "reject_markers":["RQA: TEST FAIL", "RQA120: TEST FAIL"],
        "production_effect_projections":[proof], "stock_observer_projection":stock_proof,
        "timer_compression":{"production_days":1825, "prepared_fixture_days":duration, "reason":("Original fixture duration preserved; owned core does not wait for expiry or duplicate threshold UI." if focused_keypaths else "preserve recent independence through the daily driver, then observe actual engine expiry")},
        "coverage":("Owned qualification/Chaos/Later/personal land/loyal tree/ministry/succession/death; expiry and duplicate restoration tail excluded; independent threshold UI still required." if focused_keypaths else "Existing production shattering/offer interaction/succession/restoration consequences and ministry entitlement/budget flags. Government budget UI, numeric acceptance reasons and production decision clicks remain separate UI checks."),
        "ui_steps":(["Observe the actual Chaos event once; preserve the D3 physical law/title conjunction.",
                     "At D4 inspect Later empty de jure, personal/loyal realm, nine incumbents and budget; Cancel budget without executing it.",
                     "Continue once; prove execute-time heir, real predecessor death and same-title recovery. The separate threshold_ui cell uses the real 50/51 production GUI."] if focused_keypaths else ["Close the native Chaos notification to allow time to advance.",
                    "At READY ui_after_chaos pause, inspect Later title empty de jure and retained personal/loyal realm.",
                    "Open Three Departments and Six Ministries; capture nine incumbents and the budget controls.",
                    "Use the target names in Continue RMTM Core Acceptance to open the real offer-vassalization dialog; capture recent independence -50, fixed ordinary rank +10 when difference >1, and absence of celestial/hegemony perks.",
                    "Click the fixture Continue decision after UI capture; close informational events as needed; advance until core DONE.",
                    "In an additional UI attempt inspect the production restoration decision validity and confirmation at its threshold state."]),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ui-checkpoints", action="store_true")
    parser.add_argument("--compressed-days", type=int, required=True)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--threshold-ui", action="store_true")
    parser.add_argument("--formal-product-dir", type=Path, required=True)
    parser.add_argument("--phase4-pre-send-gui-qualification", action="store_true")
    parser.add_argument("--focused-keypaths", action="store_true")
    args = parser.parse_args()
    receipt = prepare(args.repo, args.output, args.ui_checkpoints, args.compressed_days, args.game_dir, args.threshold_ui, args.formal_product_dir, args.phase4_pre_send_gui_qualification, args.focused_keypaths)
    print(json.dumps({"prepared_fixture":receipt["prepared_fixture"], "runtime_status":"NOT_RUN", "ui_checkpoints":args.ui_checkpoints}))


if __name__ == "__main__":
    main()
