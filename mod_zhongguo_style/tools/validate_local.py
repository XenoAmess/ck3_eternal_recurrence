#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZhongGuo 361 Style — local static validator (no CK3 launch required).

Checks (plain rule / code hygiene only, scoped to this mod directory):
  1. UTF-8 BOM present on all .txt/.yml/.gui; absent on descriptor.mod.
  2. descriptor.mod required fields; optional picture target exists; no remote_file_id anywhere.
  3. Brace balance for Clausewitz script and GUI files (comments/strings stripped).
  4. Localization: header line matches folder language; unique keys per file;
     all 9 language files expose the identical key set except explicitly
     allowlisted daily-development UI keys authored only in Chinese/English.
  5. Every localization-referenced key found in scripts and GUI exists in
     simp_chinese and english yml.
  6. Runtime regression guards for the decision GUI bridge, appeal settlement,
     and scoreboard registration/data publication.

Exit code 0 = GREEN, 1 = RED.
"""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path

MOD_ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = (
    "english", "simp_chinese", "french", "german", "japanese",
    "korean", "polish", "russian", "spanish",
)
DAILY_CORE_ONLY_LOC_PREFIXES = ("zg361_scoreboard_detail_",)
DAILY_CORE_ONLY_LOC_KEYS = frozenset({"zg361_scoreboard_col_dossier"})
SCOREBOARD_B1_DETAIL_SOURCES = {
    "self_choice": "zg361_b1_self_choice",
    "self_score": "zg361_b1_self_score",
    "self_gap": "zg361_b1_self_gap",
    "shadow_response": "zg361_b1_shadow_response_state",
    "shadow_delta": "zg361_b1_shadow_evidence_delta",
    "peer_n": "zg361_b1_peer_n",
    "peer_mean": "zg361_b1_peer_mean",
    "peer_variance": "zg361_b1_peer_variance",
    "peer_normalized_score": "zg361_b1_peer_normalized_score",
    "peer_shape": "zg361_b1_peer_shape",
    "peer_reciprocity_risk": "zg361_b1_peer_reciprocity_risk",
    "peer_timely_n": "zg361_b1_peer_timely_n",
    "peer_credit_total": "zg361_b1_peer_credit_total",
    "evaluator_credit": "zg361_b1_evaluator_credit",
    "calibration_score": "zg361_b1_calibration_score",
    "calibration_score_before_shadow": "zg361_b1_calibration_score_before_shadow",
    "shadow_to_quota_delta": "zg361_b1_shadow_to_quota_delta",
    "quota_snapshot": "zg361_b1_quota_snapshot",
    "forced_down": "zg361_b1_forced_down",
    "b1_fact_sheet_serial": "zg361_b1_fact_sheet_serial",
    "b1_peer_sealed": "zg361_b1_peer_sealed",
    "b1_self_receipt_serial": "zg361_b1_m004_receipt_serial",
    "b1_peer_receipt_serial": "zg361_b1_m008_receipt_serial",
    "b1_shadow_receipt_serial": "zg361_b1_m001_receipt_serial",
    "b1_band_receipt_serial": "zg361_b1_m145_receipt_serial",
    "b1_141_must_review_marker": "zg361_b1_must_review_object_available",
    "b1_141_agenda_reason": "zg361_b1_must_review_reason_fact",
    "b1_141_review_outcome": "zg361_b1_must_review_judgment_result",
    "b1_142_pending_marker": "zg361_b1_pending_self_safe_marker",
    "b1_142_milestone": "zg361_b1_pending_self_safe_milestone",
    "b1_142_deadline_cycle": "zg361_b1_pending_self_safe_deadline_cycle",
    "b1_142_current_final_unchanged": "zg361_b1_pending_self_safe_current_final_unchanged",
    "b1_142_next_cycle_evidence": "zg361_b1_pending_self_safe_next_cycle_evidence",
    "b1_143_reopen_result": "zg361_b1_reopen_self_a_result",
    "b1_143_reason_code": "zg361_b1_reopen_self_a_reason",
    "b1_143_next_cycle_evidence": "zg361_b1_reopen_self_b_next_cycle_evidence",
    "b1_143_target_cycle": "zg361_b1_reopen_self_b_target_cycle",
    "b1_144_dissent_marker": "zg361_b1_dissent_self_safe_evidence",
    "b1_144_fact_reason": "zg361_b1_dissent_reason_fact",
    "b1_144_review_outcome": "zg361_b1_dissent_final_result",
    "b1_144_consensus_marker": "zg361_b1_consensus_sealed",
    "b1_145_formal_band": "zg361_b1_band_formal_band",
    "b1_145_within_middle_order": "zg361_b1_band_self_public_within_middle_order",
    "b1_145_opportunity_capacity": "zg361_b1_band_self_public_opportunity_capacity",
    "b1_145_opportunity_selected": "zg361_b1_band_self_public_opportunity_selected",
    "b1_145_coaching_selected": "zg361_b1_band_self_public_coaching_selected",
    "b1_145_own_opportunity_selected": "zg361_b1_band_self_private_opportunity_selected",
    "b1_145_appeal_evidence_available": "zg361_b1_band_self_appeal_evidence",
    "b1_145_blackbox_audit": "zg361_b1_band_order_blackbox_risk",
}
SCOREBOARD_HIDDEN_BINDINGS = (
    "case_owner",
    "cycle_serial",
    "case_serial",
    "case_state",
    "b1_case_owner",
    "b1_cycle_serial",
    "b1_case_serial",
    "b1_case_state",
)
SCOREBOARD_RECEIVED_FORBIDDEN = frozenset(
    {
        "evaluator_id",
        "peer_slot_1_evaluator",
        "peer_slot_2_evaluator",
        "peer_slot_3_evaluator",
        "raw_comment",
        "recusal_identity",
        "zg361_b1_peer_slot_1_evaluator",
        "zg361_b1_peer_slot_2_evaluator",
        "zg361_b1_peer_slot_3_evaluator",
        "zg361_b1_raw_comment",
        "zg361_b1_recusal_identity",
    }
)

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def strip_comments_and_strings(text: str) -> str:
    """Remove #-comments and double-quoted strings for brace counting."""
    out_lines = []
    for line in text.splitlines():
        line = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
        hash_pos = line.find("#")
        if hash_pos != -1:
            line = line[:hash_pos]
        out_lines.append(line)
    return "\n".join(out_lines)


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def check_bom() -> None:
    for path in sorted(MOD_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(MOD_ROOT).as_posix()
        if rel.startswith("tools/"):
            continue
        data = path.read_bytes()
        has_bom = data.startswith(b"\xef\xbb\xbf")
        if path.suffix in (".txt", ".yml", ".gui"):
            if not has_bom:
                err(f"missing UTF-8 BOM: {rel}")
        elif path.name == "descriptor.mod":
            if has_bom:
                err(f"descriptor.mod must NOT carry BOM: {rel}")


def check_descriptor() -> None:
    desc = MOD_ROOT / "descriptor.mod"
    text = read_text(desc)
    for field in ('version="', 'name="', 'supported_version="'):
        if field not in text:
            err(f"descriptor.mod missing field token: {field}")
    picture = re.search(r'^picture="([^"]+)"', text, re.M)
    if picture and not (MOD_ROOT / picture.group(1)).is_file():
        err(f"descriptor.mod picture target does not exist: {picture.group(1)}")
    for path in MOD_ROOT.rglob("*"):
        if path.is_file() and path.suffix in (".txt", ".yml", ".gui", ".mod"):
            if b"remote_file_id" in path.read_bytes():
                err(f"remote_file_id must never live inside the repo: {path.relative_to(MOD_ROOT)}")


def check_braces() -> None:
    paths = list(MOD_ROOT.rglob("*.txt")) + list(MOD_ROOT.rglob("*.gui"))
    for path in sorted(paths):
        rel = path.relative_to(MOD_ROOT).as_posix()
        cleaned = strip_comments_and_strings(read_text(path))
        balance = 0
        for ch in cleaned:
            if ch == "{":
                balance += 1
            elif ch == "}":
                balance -= 1
            if balance < 0:
                err(f"unbalanced braces (extra '}}'): {rel}")
                break
        else:
            if balance != 0:
                err(f"unbalanced braces (net {balance:+d}): {rel}")


def check_widget_registrations() -> None:
    folder = MOD_ROOT / "gui" / "scripted_widgets"
    for registry in sorted(folder.glob("*.txt")):
        for lineno, line in enumerate(read_text(registry).splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.fullmatch(r"(gui/[A-Za-z0-9_./-]+\.gui)\s*=\s*([A-Za-z0-9_]+)", stripped)
            if not match:
                err(f"malformed scripted widget registration {registry.name}:{lineno}: {stripped}")
                continue
            gui_rel, window_name = match.groups()
            gui_path = MOD_ROOT / gui_rel
            if not gui_path.is_file():
                err(f"registered GUI file does not exist: {gui_rel}")
                continue
            gui_text = read_text(gui_path)
            if not re.search(rf'\bwindow\s*=\s*\{{.*?\bname\s*=\s*"{re.escape(window_name)}"', gui_text, re.S):
                err(f"registered window {window_name} not found in {gui_rel}")


def parse_yml_keys(path: Path) -> list[str]:
    keys = []
    for lineno, line in enumerate(read_text(path).splitlines(), start=1):
        if lineno == 1 or not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^\s*([A-Za-z0-9_.\-]+):\d+\s*\"(?:[^\"\\]|\\.)*\"\s*$", line)
        if m:
            keys.append(m.group(1))
        else:
            err(f"malformed yml line {lineno} in {path.relative_to(MOD_ROOT)}: {line.strip()[:80]}")
    return keys


def check_localization() -> dict[str, set[str]]:
    loc_dir = MOD_ROOT / "localization"
    key_sets: dict[str, set[str]] = {}
    for lang in LANGUAGES:
        files = sorted((loc_dir / lang).glob(f"zg361*_l_{lang}.yml"))
        if not files:
            err(f"missing localization files for {lang}")
            continue
        keys: list[str] = []
        for yml in files:
            lines = read_text(yml).splitlines()
            if not lines or lines[0].strip() != f"l_{lang}:":
                err(f"bad yml header in {yml.relative_to(MOD_ROOT)}: expected 'l_{lang}:'")
            keys.extend(parse_yml_keys(yml))
        if len(keys) != len(set(keys)):
            dupes = sorted({k for k in keys if keys.count(k) > 1})
            err(f"duplicate localization keys across {lang} files: {dupes}")
        key_sets[lang] = set(keys)
    reference = key_sets.get("english", set())
    for lang, keys in key_sets.items():
        missing = reference - keys
        extra = keys - reference
        allowed_missing = {
            key
            for key in missing
            if key in DAILY_CORE_ONLY_LOC_KEYS
            or key.startswith(DAILY_CORE_ONLY_LOC_PREFIXES)
        }
        # Daily feature work authors only Simplified Chinese and English. The
        # release localization workflow must fill the other seven languages;
        # this narrow exception keeps ordinary L0 honest without pretending
        # those translations already exist.
        if lang in ("english", "simp_chinese"):
            allowed_missing = set()
        unexpected_missing = missing - allowed_missing
        if unexpected_missing or extra:
            err(
                f"localization key set mismatch in {lang}: "
                f"missing={sorted(unexpected_missing)} extra={sorted(extra)}"
            )
    return key_sets


def collect_referenced_keys() -> dict[str, set[str]]:
    """Scan scripts for keys that must exist in localization."""
    refs: dict[str, set[str]] = {"events": set(), "event_options": set(), "plain": set()}

    gr = MOD_ROOT / "common" / "game_rules" / "zg361_game_rules.txt"
    if gr.is_file():
        text = strip_comments_and_strings(read_text(gr))
        for m in re.finditer(r"^(zg361\w*)\s*=\s*\{", text, re.M):
            refs["plain"].add(f"rule_{m.group(1)}")
        for m in re.finditer(r"^[ \t]+(zg361_\w+)\s*=\s*\{", text, re.M):
            refs["plain"].add(f"setting_{m.group(1)}")
            refs["plain"].add(f"setting_{m.group(1)}_desc")

    for sub in ("modifiers", "opinion_modifiers"):
        folder = MOD_ROOT / "common" / sub
        if not folder.is_dir():
            continue
        for f in folder.glob("*.txt"):
            text = strip_comments_and_strings(read_text(f))
            for m in re.finditer(r"^\s*(zg361\w*)\s*=\s*\{", text, re.M):
                refs["plain"].add(m.group(1))
                if sub == "modifiers":
                    refs["plain"].add(f"{m.group(1)}_desc")

    for f in (MOD_ROOT / "common" / "decisions").glob("*.txt"):
        text = strip_comments_and_strings(read_text(f))
        for m in re.finditer(r"^(zg361\w*)\s*=\s*\{", text, re.M):
            refs["plain"].add(m.group(1))
            refs["plain"].add(f"{m.group(1)}_desc")
            refs["plain"].add(f"{m.group(1)}_tooltip")
            refs["plain"].add(f"{m.group(1)}_confirm")

    for f in (MOD_ROOT / "common" / "character_interactions").glob("*.txt"):
        text = strip_comments_and_strings(read_text(f))
        for m in re.finditer(r"^(zg361\w*)\s*=\s*\{", text, re.M):
            refs["plain"].add(m.group(1))
            refs["plain"].add(f"{m.group(1)}_desc")

    for f in (MOD_ROOT / "common" / "decision_group_types").glob("*.txt"):
        text = strip_comments_and_strings(read_text(f))
        for m in re.finditer(r"^(zg361\w*)\s*=\s*\{", text, re.M):
            refs["plain"].add(f"decision_group_type_{m.group(1)}")

    for f in (MOD_ROOT / "common" / "activities" / "activity_types").glob("*.txt"):
        text = strip_comments_and_strings(read_text(f))
        for m in re.finditer(r"^(activity_zg361\w*)\s*=\s*\{", text, re.M):
            key = m.group(1)
            refs["plain"].add(key)
            for suffix in (
                "_desc", "_selection_tooltip", "_conclusion_desc", "_host_desc", "_guest_desc",
                "_destination_selection", "_guest_help_text", "_cooldown", "_predicted_cost", "_host_an_a",
            ):
                refs["plain"].add(f"{key}{suffix}")
        for m in re.finditer(r"desc\s*=\s*(zg361\w+)", text):
            refs["plain"].add(m.group(1))

    ids: set[str] = set()
    for ev in sorted((MOD_ROOT / "events").glob("zg361*.txt")):
        text = strip_comments_and_strings(read_text(ev))
        file_ids = set(re.findall(r"^\s*(zg361m?\.\d+)\s*=\s*\{", text, re.M))
        duplicate_ids = ids & file_ids
        if duplicate_ids:
            err(f"duplicate event ids across zg361 event files: {sorted(duplicate_ids)}")
        ids |= file_ids
        for eid in file_ids:
            refs["events"].add(f"{eid}.t")
            refs["events"].add(f"{eid}.desc")
        for m in re.finditer(r"name\s*=\s*(zg361m?\.\d+\.\w+)", text):
            refs["event_options"].add(m.group(1))
        for m in re.finditer(r"custom_tooltip\s*=\s*(zg361m?\.\d+\.[A-Za-z0-9_.]+)", text):
            refs["plain"].add(m.group(1))
        for m in re.finditer(r"custom_tooltip\s*=\s*(zg361[A-Za-z0-9_.]+)", text):
            refs["plain"].add(m.group(1))
    event_stems = {i.rsplit(".", 1)[0] for i in refs["event_options"]}
    missing_parent = event_stems - ids
    if missing_parent:
        err(f"event options reference unknown events: {sorted(missing_parent)}")

    for f in (MOD_ROOT / "gui").rglob("*.gui"):
        text = read_text(f)
        for m in re.finditer(r'\b(?:text|tooltip)\s*=\s*"(zg361_[A-Za-z0-9_.-]+)"', text):
            refs["plain"].add(m.group(1))
    return refs


def check_runtime_invariants() -> None:
    triggers = read_text(MOD_ROOT / "common" / "scripted_triggers" / "zg361_triggers.txt")
    decisions = read_text(MOD_ROOT / "common" / "decisions" / "zg361_decisions.txt")
    effects = read_text(MOD_ROOT / "common" / "scripted_effects" / "zg361_effects.txt")
    events = read_text(MOD_ROOT / "events" / "zg361_events.txt")
    registrations = read_text(MOD_ROOT / "gui" / "scripted_widgets" / "zg361_scripted_widgets.txt")
    scoreboard_gui = read_text(MOD_ROOT / "gui" / "zg361_scoreboard.gui")
    scripted_guis = read_text(MOD_ROOT / "common" / "scripted_guis" / "zg361_scoreboard_guis.txt")
    on_actions = read_text(MOD_ROOT / "common" / "on_action" / "zg361_on_actions.txt")
    activity = read_text(MOD_ROOT / "common" / "activities" / "activity_types" / "zg361_jingcha.txt")
    mandate_effects = read_text(
        MOD_ROOT / "common" / "scripted_effects" / "zg361_jingcha_mandate_effects.txt"
    )
    mandate_events = read_text(MOD_ROOT / "events" / "zg361_jingcha_events.txt")
    interactions = read_text(
        MOD_ROOT / "common" / "character_interactions" / "zg361_interactions.txt"
    )
    values = read_text(MOD_ROOT / "common" / "script_values" / "zg361_values.txt")

    for event_file in sorted((MOD_ROOT / "events").glob("*.txt")):
        if re.search(r"^\s*hide_window\s*=", read_text(event_file), re.M):
            err(f"CK3 events use 'hidden = yes', not 'hide_window': {event_file.name}")

    if not re.search(
        r"zg361_is_celestial_liege_trigger\s*=\s*\{.*?"
        r"government_has_flag\s*=\s*government_is_celestial.*?"
        r"highest_held_title_tier\s*>=\s*tier_duchy",
        triggers,
        re.S,
    ):
        err("reviewing lieges must be celestial rulers of duchy tier or above")

    # A sub-three roster is exempt from forced distribution and calibration,
    # not from performance review itself. One or two officials must receive a
    # stable rank and neutral 3.5 through the normal settlement/publication path;
    # only an empty roster may leave without a settled year.
    review_effect = re.search(
        r"zg361_run_review_effect\s*=\s*\{(?P<body>.*?)^\}",
        effects,
        re.M | re.S,
    )
    review_body = review_effect.group("body") if review_effect else ""
    small_cohort = re.search(
        r"limit\s*=\s*\{\s*var:zg361_cohort_n\s*>=\s*1\s*\}"
        r"(?P<body>.*?)"
        r'debug_log\s*=\s*"ZG361: small cohort bypassed forced distribution and settled at 3\.5"'
        r"\s*zg361_apply_pending_grades_effect\s*=\s*yes",
        review_body,
        re.S,
    )
    if small_cohort is None:
        err("one-to-two-person cohorts must reach the normal 3.5 settlement path")
    else:
        small_body = small_cohort.group("body")
        for token in (
            "zg361_rank_cohort_effect = yes",
            "name = zg361_last_reviewer value = root",
            "name = zg361_last_review_serial value = root.var:zg361_review_serial",
            "name = zg361_pending_grade value = 2",
            "name = zg361_pending_375_n value = 0",
            "name = zg361_pending_35_n value = var:zg361_cohort_n",
            "name = zg361_pending_325_n value = 0",
        ):
            if token not in small_body:
                err(f"small-cohort neutral settlement contract missing token: {token}")
        if "trigger_event = { id = zg361.10" in small_body:
            err("small cohorts must bypass the forced-distribution calibration event")
    if not re.search(
        r'else\s*=\s*\{\s*debug_log\s*=\s*"ZG361: empty cohort, review skipped"'
        r".*?remove_character_flag\s*=\s*zg361_review_in_progress\s*\}",
        review_body,
        re.S,
    ):
        err("only an empty cohort may leave the review unsettled")

    review_now = re.search(
        r"zg361_review_now_decision\s*=\s*\{(?P<body>.*?)^\}",
        decisions,
        re.M | re.S,
    )
    review_now_body = review_now.group("body") if review_now else ""
    if len(re.findall(r"any_vassal\s*=\s*\{\s*count\s*>=\s*1", review_now_body)) != 2:
        err("review-now decision must accept one or more direct reviewable officials")
    if re.search(r"any_vassal\s*=\s*\{\s*count\s*>=\s*3", review_now_body):
        err("review-now decision must not exclude one-to-two-person cohorts")

    if "trigger_event = { id = zg361.20" in decisions:
        err("review decision must not trigger its event from tooltip-simulated effect")
    if "zg361.20 =" in events:
        err("obsolete review carrier event must not remain orphaned")
    if "add_character_flag = zg361_review_now_pending" not in decisions:
        err("review decision is missing its one-shot GUI bridge flag")
    if len(re.findall(r"\bpicture\s*=\s*\{\s*reference\s*=", decisions, re.S)) != 5:
        err("all five 361 decisions must declare an existing vanilla picture")
    if "zg361_review_now_bridge_gui" not in scripted_guis:
        err("review decision scripted GUI bridge is missing")
    if re.search(r"add_gold\s*=\s*\{\s*value\s*=\s*0\s+subtract", events):
        err("negative add_gold pattern is invalid on CK3 1.19")
    if "trigger = {\n\t\tzg361_is_elimination_candidate_trigger = yes" not in events:
        err("delayed elimination event must re-check candidate status")
    snapshot_effects = read_text(
        MOD_ROOT / "common" / "scripted_effects" / "zg361_generated_scoreboard_snapshots.txt"
    )
    slot_guis = read_text(
        MOD_ROOT / "common" / "scripted_guis" / "zg361_generated_scoreboard_slots.txt"
    )
    for token in (
        "zg361_clear_scoreboard_m_slots_effect", "zg361_write_managed_scoreboard_slot_effect",
        "zg361_copy_received_scoreboard_slots_effect", "zg361_sb_m_01_char", "zg361_sb_r_01_char",
        "zg361_publish_scoreboard_effect",
        "zg361_scoreboard_managed_shown_n", "zg361_scoreboard_received_shown_n",
        "zg361_sb_m_01_title", "zg361_sb_m_01_promotion", "zg361_sb_m_01_pip",
        "gui/zg361_scoreboard.gui = zg361_scoreboard_window",
    ):
        if token not in effects and token not in snapshot_effects and token not in registrations:
            err(f"scoreboard data/registration contract missing token: {token}")
    if not re.search(
        r"name\s*=\s*zg361_scoreboard_managed_shown_n\s+"
        r"value\s*=\s*\{\s*value\s*=\s*var:zg361_cohort_n\s+"
        r"max\s*=\s*80\s*\}",
        effects,
        re.S,
    ):
        err("scoreboard shown count must clamp in one tooltip-safe assignment")
    if not re.search(
        r"ordered_in_list\s*=\s*\{.*?"
        r"list\s*=\s*zg361_scoreboard_candidates.*?"
        r"max\s*=\s*\{\s*"
        r"value\s*=\s*list_size:zg361_scoreboard_candidates\s+"
        r"max\s*=\s*80\s*\}",
        effects,
        re.S,
    ):
        err("scoreboard ordered list must cap against its live list size")
    if "var:zg361_scoreboard_managed_shown_n > 80" in effects:
        err("scoreboard tooltip must not read a variable just written in the same effect")
    if len(re.findall(r"zg361_sb_[mr]_\d{2}_available_gui\s*=\s*\{", slot_guis)) != 160:
        err("immutable scoreboard must expose exactly 80 managed and 80 received slot predicates")
    if len(re.findall(r"zg361_sb_m_\d{2}_select_gui\s*=\s*\{", slot_guis)) != 80:
        err("scoreboard dossier must expose exactly 80 managed frozen-case selectors")
    if slot_guis.count("zg361_sb_self_select_gui = {") != 1:
        err("scoreboard dossier must expose exactly one received-self selector")
    managed_selectors = re.findall(
        r"zg361_sb_m_(?P<slot>\d{2})_select_gui\s*=\s*\{.*?"
        r"is_shown\s*=\s*\{(?P<body>.*?)^\s*\}\s*^\s*effect\s*=\s*\{",
        slot_guis,
        re.M | re.S,
    )
    if len(managed_selectors) != 80:
        err("scoreboard dossier managed selectors must have parseable availability gates")
    for slot, body in managed_selectors:
        for field in ("char", "rank", "case_owner", "cycle_serial", "case_serial"):
            if f"has_variable = zg361_sb_m_{slot}_{field}" not in body:
                err(f"scoreboard managed selector {slot} lacks frozen identity field: {field}")
        for token in (
            "has_variable = zg361_scoreboard_managed_owner",
            "has_variable = zg361_scoreboard_managed_cycle_serial",
            f"var:zg361_sb_m_{slot}_case_owner = var:zg361_scoreboard_managed_owner",
            f"var:zg361_sb_m_{slot}_cycle_serial = var:zg361_scoreboard_managed_cycle_serial",
        ):
            if token not in body:
                err(f"scoreboard managed selector {slot} lacks identity equality: {token}")
    self_selector = re.search(
        r"zg361_sb_self_select_gui\s*=\s*\{.*?"
        r"is_shown\s*=\s*\{(?P<body>.*?)^\s*\}\s*^\s*effect\s*=\s*\{",
        slot_guis,
        re.M | re.S,
    )
    self_selector_body = self_selector.group("body") if self_selector else ""
    for field in ("char", "case_owner", "cycle_serial", "case_serial"):
        if f"has_variable = zg361_sb_self_{field}" not in self_selector_body:
            err(f"scoreboard received-self selector lacks frozen identity field: {field}")
    for field in ("owner", "cycle_serial", "case_serial"):
        if f"has_variable = zg361_scoreboard_received_{field}" not in self_selector_body:
            err(f"scoreboard received-self selector lacks header identity: {field}")
    for field, header in (
        ("case_owner", "owner"),
        ("cycle_serial", "cycle_serial"),
        ("case_serial", "case_serial"),
    ):
        token = (
            f"var:zg361_sb_self_{field} = "
            f"var:zg361_scoreboard_received_{header}"
        )
        if token not in self_selector_body:
            err(f"scoreboard received-self selector lacks identity equality: {field}")
    if "var:zg361_sb_self_char = root" in self_selector_body:
        err("scoreboard received-self selector must not compare a possibly unset sibling variable")
    copy_self = snapshot_effects.split(
        "zg361_copy_received_scoreboard_slots_effect = {", 1
    )[-1].split("\n\tif = {\n\t\tlimit = { scope:zg361_scoreboard_source = { has_variable = zg361_sb_m_01_char", 1)[0]
    owner_guard = "var:zg361_result_case_owner = scope:zg361_scoreboard_source"
    cycle_guard = (
        "var:zg361_scoreboard_managed_cycle_serial = "
        "root.var:zg361_result_cycle_serial"
    )
    case_guard = (
        "name = zg361_scoreboard_received_case_serial "
        "value = var:zg361_result_case_serial"
    )
    self_write = "name = zg361_sb_self_char"
    if not all(
        token in copy_self for token in (owner_guard, cycle_guard, case_guard, self_write)
    ):
        err("received-self dossier buffer lacks owner/cycle/case publication identity gate")
    elif not (
        copy_self.index(owner_guard)
        < copy_self.index(cycle_guard)
        < copy_self.index(case_guard)
        < copy_self.index(self_write)
    ):
        err("received-self dossier identity gates must precede every self-buffer write")
    for field, source in SCOREBOARD_B1_DETAIL_SOURCES.items():
        for token, surface in (
            (source, "snapshot source"),
            (f"zg361_sb_m_01_{field}", "managed frozen slot"),
            (f"zg361_sb_self_{field}", "received-self ACL"),
            (f"zg361_sb_detail_{field}", "selected detail buffer"),
            (f"zg361_scoreboard_detail_field_{field}", "detail GUI row"),
        ):
            haystack = (
                scoreboard_gui
                if surface == "detail GUI row"
                else slot_guis
                if surface == "selected detail buffer"
                else snapshot_effects
            )
            if token not in haystack:
                err(f"scoreboard B1 {surface} missing {field}: {token}")
    for binding in SCOREBOARD_HIDDEN_BINDINGS:
        if f"zg361_sb_detail_{binding}_available_gui" in slot_guis:
            err(f"scoreboard binding must not expose availability GUI: {binding}")
        if f"zg361_scoreboard_detail_field_{binding}" in scoreboard_gui:
            err(f"scoreboard binding must not expose detail row: {binding}")
    for sensitive in SCOREBOARD_RECEIVED_FORBIDDEN:
        if sensitive in copy_self:
            err(f"received-self ACL copies sensitive peer field: {sensitive}")
    phase2_updates = snapshot_effects.split(
        "# Current scope = player official after witnessed/acknowledged 3.25 settlement.",
        1,
    )[-1]
    for token in (
        "var:zg361_sb_m_01_case_serial = scope:zg361_scoreboard_case_entry.var:zg361_result_case_serial",
        "var:zg361_sb_m_80_case_serial = scope:zg361_scoreboard_case_entry.var:zg361_result_case_serial",
        "var:zg361_sb_detail_binding_case_serial = scope:zg361_scoreboard_case_entry.var:zg361_result_case_serial",
        "var:zg361_scoreboard_received_case_serial = var:zg361_result_case_serial",
    ):
        if token not in phase2_updates:
            err(f"scoreboard mutable update lacks frozen case guard: {token}")
    if scoreboard_gui.count('name = "zg361_scoreboard_toggle"') != 1:
        err("scoreboard must retain exactly one top-level HUD toggle")
    if scoreboard_gui.count('name = "zg361_scoreboard_detail_panel"') != 1:
        err("scoreboard must render one shared dossier detail pane")
    for page in ("facts", "peer", "quota", "audit"):
        if scoreboard_gui.count(
            f'name = "zg361_scoreboard_detail_page_{page}"'
        ) != 1:
            err(f"scoreboard dossier page must be unique: {page}")
        if scoreboard_gui.count(
            f'name = "zg361_scoreboard_detail_tab_{page}"'
        ) != 1:
            err(f"scoreboard dossier tab must be unique: {page}")
    for sensitive in SCOREBOARD_RECEIVED_FORBIDDEN:
        if re.search(
            rf"zg361_sb_r_\d{{2}}_{re.escape(sensitive)}",
            snapshot_effects + slot_guis,
        ):
            err(f"received team slots must not copy sensitive dossier field: {sensitive}")
    if re.search(r"Character\.MakeScope\.Var\('zg361_(?:result|b1)_", scoreboard_gui):
        err("scoreboard dossier must read selected frozen buffers, not live case variables")
    if slot_guis.count("zg361_scoreboard_detail_clear_gui = {") != 1:
        err("scoreboard must expose exactly one detail-buffer clear action")
    clear_action = (
        "GetScriptedGui('zg361_scoreboard_detail_clear_gui')."
        "Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)"
    )
    if scoreboard_gui.count(clear_action) < 6:
        err("scoreboard close/reopen paths must clear the selected dossier buffer")
    if not re.search(
        r"hbox\s*=\s*\{.*?button_tertiary\s*=\s*\{.*?"
        r"DefaultOnCharacterClick\(Character\.GetID\).*?^\s*\}.*?"
        r"button_standard\s*=\s*\{\s*name\s*=\s*\"zg361_scoreboard_detail_button_m_01\"",
        scoreboard_gui,
        re.M | re.S,
    ):
        err("scoreboard character and dossier controls must be sibling buttons")
    for source in ("managed", "received"):
        shown_available = f"zg361_scoreboard_{source}_shown_available_gui"
        if shown_available not in slot_guis:
            err(f"scoreboard shown/full compatibility predicate missing: {shown_available}")
        if (
            f"Not(GetScriptedGui('{shown_available}').IsShown" not in scoreboard_gui
            or f"Var('zg361_scoreboard_{source}_n').GetValue" not in scoreboard_gui
        ):
            err(f"legacy scoreboard total fallback missing for {source} tab")
    if "GetList('zg361_scoreboard_managed')" in scoreboard_gui or "GetList('zg361_scoreboard_received')" in scoreboard_gui:
        err("scoreboard GUI must not read live character variable lists")
    for live_field in (
        "Character.MakeScope.Var('zg361_rank')",
        "Character.MakeScope.Var('zg361_kpi')",
        "Character.MakeScope.Var('zg361_values')",
        "Character.MakeScope.Var('zg361_last_grade')",
        "Character.GetPrimaryTitle",
        "GetScriptedGui('zg361_scoreboard_promotion_gui')",
        "GetScriptedGui('zg361_scoreboard_pip_gui')",
    ):
        if live_field in scoreboard_gui:
            err(f"scoreboard snapshot must not read live field: {live_field}")
    for token in ("zg361_scoreboard_managed_available_gui", "zg361_scoreboard_received_available_gui"):
        if token not in scripted_guis:
            err(f"scoreboard availability predicate missing: {token}")
    if not re.search(
        r'blockoverride\s+"button_close"\s*\{.*?shortcut\s*=\s*close_window',
        scoreboard_gui,
        re.S,
    ):
        err("scoreboard modal close button must support the native Escape shortcut")
    if 'shortcut = "close_window"' in scoreboard_gui:
        err("scoreboard Escape shortcut must use the native unquoted identifier")
    if 'position = { -60 90 }' not in scoreboard_gui:
        err("scoreboard HUD toggle must align immediately left of the native main-tab rail")
    toggle_match = re.search(
        r'name\s*=\s*"zg361_scoreboard_toggle"(?P<body>.*?)^\s*\}',
        scoreboard_gui,
        re.M | re.S,
    )
    toggle_body = toggle_match.group("body") if toggle_match else ""
    for gate in (
        "Not(IsPauseMenuShown)",
        "IsDefaultGUIMode",
        "Not(IsGameViewOpen('struggle'))",
        "hide_ui_main_tabs",
        "Not(IsRightWindowOpen)",
        "Not(IsGameViewOpen('outliner'))",
        "Not(IsGameViewOpen('barbershop'))",
    ):
        if gate not in toggle_body:
            err(f"scoreboard HUD toggle is missing native-overlay gate: {gate}")
    modal_match = re.search(
        r'name\s*=\s*"zg361_scoreboard_modal"(?P<body>.*?)^\s*widget\s*=\s*\{',
        scoreboard_gui,
        re.M | re.S,
    )
    modal_body = modal_match.group("body") if modal_match else ""
    for gate in (
        "Not(IsPauseMenuShown)",
        "IsDefaultGUIMode",
        "Not(IsGameViewOpen('struggle'))",
        "hide_ui_main_tabs",
        "Not(IsRightWindowOpen)",
        "Not(IsGameViewOpen('outliner'))",
        "Not(IsGameViewOpen('barbershop'))",
    ):
        if gate not in modal_body:
            err(f"scoreboard modal is missing native-overlay gate: {gate}")
    if toggle_body.count("button_standard = {") != 3:
        err("scoreboard HUD toggle must expose managed, received, and ledger-only variants")
    for token in (
        "zg361_mechanism_ledger_available_gui",
        "GetVariableSystem.Set('zg361_scoreboard_tab', 'system')",
    ):
        if token not in toggle_body:
            err(f"scoreboard ledger-only HUD entry is missing: {token}")
    if len(re.findall(r"has_variable\s*=\s*merit_(?:military|civilian)_career_score_bonus", effects)) != 4:
        err("native appointment score variables must be initialized before change_variable")
    assignment_at = effects.find("zg361_assign_pending_grades_effect = yes")
    calibration_at = effects.find("trigger_event = { id = zg361.10", assignment_at)
    calibration_preflight = (
        effects[assignment_at:calibration_at]
        if assignment_at >= 0 and calibration_at > assignment_at
        else ""
    )
    for counter in (
        "zg361_wild_dog_n",
        "zg361_rabbit_n",
        "zg361_scoreboard_slot_cursor",
    ):
        if f"set_variable = {{ name = {counter} value = 0 }}" not in calibration_preflight:
            err(
                "visible calibration event must pre-initialize tooltip-read counter "
                f"before its delayed trigger: {counter}"
            )

    # A fresh-install bootstrap must not classify every incumbent as a newcomer.
    # Only a reviewer with a completed product baseline may protect a no-snapshot
    # official; that official still enters the cohort and receives a result.
    if not re.search(
        r"every_vassal\s*=\s*\{\s*limit\s*=\s*\{\s*"
        r"zg361_is_reviewable_vassal_trigger\s*=\s*yes\s*\}.*?"
        r"add_character_flag\s*=\s*zg361_newcomer_this_cycle.*?"
        r"zg361_compute_kpi_effect\s*=\s*yes.*?"
        r"add_to_list\s*=\s*zg361_cohort",
        effects,
        re.S,
    ):
        err("new officials must enter their first cohort before snapshot initialization")
    if not re.search(
        r"NOT\s*=\s*\{\s*has_variable\s*=\s*zg361_prev_merit_level\s*\}.*?"
        r"root\s*=\s*\{\s*has_character_flag\s*=\s*"
        r"zg361_review_baseline_initialized\s*\}.*?"
        r"add_character_flag\s*=\s*zg361_newcomer_this_cycle",
        effects,
        re.S,
    ):
        err("newcomer protection must require a previously settled reviewer baseline")
    if not re.search(
        r"zg361_can_calibrate_demote_trigger\s*=.*?"
        r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{\s*"
        r"has_variable\s*=\s*zg361_pending_grade\s*\}\s*"
        r"var:zg361_pending_grade\s*=\s*2.*?"
        r"trigger_else\s*=\s*\{\s*always\s*=\s*no\s*\}.*?"
        r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{\s*"
        r"has_variable\s*=\s*zg361_pending_grade\s*\}\s*"
        r"var:zg361_pending_grade\s*=\s*1.*?"
        r"trigger_else\s*=\s*\{\s*always\s*=\s*no\s*\}",
        triggers,
        re.S,
    ):
        err("calibration availability must guard pending-grade reads during tooltip preview")
    if not re.search(
        r"zg361_is_current_liege_review_record_trigger\s*=\s*\{.*?"
        r"trigger_if\s*=\s*\{\s*limit\s*=\s*\{.*?"
        r"has_variable\s*=\s*zg361_last_reviewer.*?"
        r"has_variable\s*=\s*zg361_last_review_serial.*?"
        r"liege\s*=\s*\{\s*has_variable\s*=\s*zg361_review_serial\s*\}.*?"
        r"var:zg361_last_reviewer\s*=\s*liege.*?"
        r"var:zg361_last_review_serial\s*=\s*liege\.var:zg361_review_serial.*?"
        r"trigger_else\s*=\s*\{\s*always\s*=\s*no\s*\}",
        triggers,
        re.S,
    ):
        err("review-record comparisons must not read unset variables during enumeration")
    assignment_body = re.search(
        r"zg361_assign_pending_grades_effect\s*=\s*\{(?P<body>.*?)^\}",
        effects,
        re.M | re.S,
    )
    if assignment_body is None or not re.search(
        r"every_in_list\s*=\s*\{\s*"
        r"list\s*=\s*zg361_cohort.*?"
        r"limit\s*=\s*\{\s*NOT\s*=\s*\{\s*"
        r"has_character_flag\s*=\s*zg361_newcomer_this_cycle.*?"
        r"add_to_list\s*=\s*zg361_bottom_candidates",
        assignment_body.group("body") if assignment_body else "",
        re.S,
    ):
        err("3.25 bottom-slot assignment must skip first-cycle newcomers")
    bottom_assignment = assignment_body.group("body") if assignment_body else ""
    if not re.search(
        r"ordered_in_list\s*=\s*\{\s*"
        r"list\s*=\s*zg361_bottom_candidates.*?"
        r"max\s*=\s*list_size:zg361_bottom_candidates",
        bottom_assignment,
        re.S,
    ):
        err("bottom-slot ordered list must explicitly iterate its full eligible list")
    zero_based_gate = (
        "root.var:zg361_bottom_cursor < root.var:zg361_bottom_slots"
    )
    bottom_increment = (
        "root = { change_variable = { name = zg361_bottom_cursor add = 1 } }"
    )
    if zero_based_gate not in bottom_assignment or bottom_increment not in bottom_assignment:
        err("bottom slots must use a zero-based cursor with a strict pre-increment gate")
    elif bottom_assignment.index(zero_based_gate) > bottom_assignment.index(bottom_increment):
        err("bottom-slot cursor must be compared before it is incremented")
    if "zg361_bottom_cursor <= root.var:zg361_bottom_slots" in bottom_assignment:
        err("one-based <= bottom-slot cursor reintroduces the 2-slots-to-1-row bug")
    newcomer_assignment_at = effects.find("zg361_assign_pending_grades_effect = yes")
    newcomer_calibration_at = effects.find(
        "trigger_event = { id = zg361.10", newcomer_assignment_at
    )
    if newcomer_assignment_at < 0 or newcomer_calibration_at < 0:
        err("ranked player review must reach the delayed calibration event")
    elif "remove_character_flag = zg361_newcomer_this_cycle" in effects[
        newcomer_assignment_at:newcomer_calibration_at
    ]:
        err("newcomer protection flag must survive the whole calibration window")
    settlement_body = re.search(
        r"zg361_apply_pending_grades_effect\s*=\s*\{(?P<body>.*?)^\}",
        effects,
        re.M | re.S,
    )
    if settlement_body is None or not re.search(
        r"zg361_apply_grade_effect\s*=\s*yes\s*"
        r"remove_character_flag\s*=\s*zg361_newcomer_this_cycle",
        settlement_body.group("body") if settlement_body else "",
    ):
        err("newcomer protection flag must clear only when the pending grade settles")
    if settlement_body is None or (
        "add_character_flag = zg361_review_baseline_initialized"
        not in settlement_body.group("body")
    ):
        err("a completed settlement must initialize the reviewer's newcomer baseline")

    for token in (
        "zg361_can_calibrate_demote_trigger = yes",
        "save_temporary_scope_as = zg361_calibration_demote_target",
        "save_temporary_scope_as = zg361_calibration_rescue_target",
        "NOT = { has_character_flag = zg361_newcomer_this_cycle }",
        "scope:zg361_calibration_rescue_target = {",
        "scope:zg361_calibration_demote_target = {",
        'debug_log = "ZG361: calibration demote atomic grade swap used"',
    ):
        if token not in effects and token not in events:
            err(f"atomic newcomer-safe calibration C contract missing token: {token}")

    # Appeal settlement is a one-shot receipt reversal. Phase two refunds the
    # actual frozen receipt amounts, stops future salary withholding, and posts
    # a case-serial refund token rather than recalculating constants.
    for token in (
        "zg361_appeal_regrade_to_35_effect = {",
        "zg361_apply_receipted_appeal_regrade_effect = yes",
        'debug_log = "ZG361: duplicate or stale appeal regrade ignored"',
        "add_treasury = var:zg361_result_treasury_paid",
        "add_gold = var:zg361_result_gold_paid",
        "change_merit = { value = var:zg361_result_merit_paid }",
        "name = zg361_result_refund_posted_serial value = var:zg361_result_case_serial",
        "name = zg361_result_case_state value = 5",
        "name = zg361_result_salary_cut_active value = 0",
        "remove_character_modifier = zg361_grade_325",
        "remove_character_modifier = zg361_pip",
    ):
        if token not in effects:
            err(f"receipted appeal/idempotence contract missing token: {token}")

    # Jingcha is a periodic, free, semi-mandatory activity for player celestial
    # lieges; AI complies through the same dispatch without opening UI.
    for token in (
        "zg361_jingcha_annual_dispatch_effect = yes",
        "yearly_playable_pulse",
    ):
        if token not in on_actions:
            err(f"periodic jingcha on_action contract missing token: {token}")
    for token in (
        "zg361_issue_jingcha_mandate_effect",
        "is_ai = no",
        "has_variable = zg361_jingcha_pending",
        'debug_log = "ZG361: existing jingcha mandate remains pending; duplicate issuance skipped"',
        "trigger_event = { id = zg361.40",
        "zg361_refuse_jingcha_effect",
        "set_variable = { name = zg361_skipped_jingcha_superior value = var:zg361_jingcha_mandate_reviewer }",
        "set_variable = { name = zg361_jingcha_mandate_superior value = liege }",
        "set_variable = { name = zg361_jingcha_mandate_reviewer value = liege }",
        "ineligible superior opinion penalty recorded without orphan KPI marker",
        "modifier = zg361_refused_jingcha",
        "subtract = zg361_independent_refusal_prestige_cost_value",
    ):
        if token not in mandate_effects:
            err(f"jingcha mandate/refusal contract missing token: {token}")
    if "zg361_is_jingcha_eligible_guest_trigger = {" not in triggers:
        err("Jingcha must define one shared legal-guest predicate")
    for label, body in (
        ("mandate", mandate_effects),
        ("activity", activity),
        ("deadline", mandate_events),
    ):
        if "zg361_is_jingcha_eligible_guest_trigger = yes" not in body:
            err(f"Jingcha {label} must use the shared legal-guest predicate")
        if not re.search(
            r"any_vassal\s*=\s*\{\s*count\s*>=\s*1\s*"
            r"zg361_is_jingcha_eligible_guest_trigger\s*=\s*yes",
            body,
            re.S,
        ):
            err(f"Jingcha {label} must remain available to a one-official cohort")
    if mandate_effects.count(
        "set_variable = { name = zg361_jingcha_pending value = 1 }"
    ) != 1:
        err(
            "Jingcha mandate must create exactly one pending obligation, inside the "
            "one-or-more eligible guest branch; zero guests remain excused"
        )
    for token in (
        "data = activity_type:activity_zg361_jingcha",
        "trigger_event = { id = zg361.41 days = 300 }",
        "has_variable = zg361_jingcha_pending",
    ):
        if token not in mandate_events:
            err(f"jingcha popup/deadline contract missing token: {token}")
    if len(re.findall(r"(?:cost|ui_predicted_cost)\s*=\s*\{\s*treasury\s*=\s*\{\s*value\s*=\s*0", activity, re.S)) != 2:
        err("jingcha activity must declare zero Treasury cost in both runtime and predicted cost")
    if re.search(r"\bgold\s*=", activity):
        err("jingcha activity must not charge personal gold")
    if "zg361_clear_jingcha_mandate_effect = yes" not in activity:
        err("jingcha completion must clear its full mandate lifecycle state")
    for token in (
        "zg361_clear_jingcha_mandate_effect = {",
        "zg361_excuse_jingcha_assembly_effect = {",
        "jingcha assembly excused; active performance season continues",
    ):
        if token not in mandate_effects:
            err(f"jingcha lifecycle cleanup contract missing token: {token}")
    if "zg361_excuse_jingcha_assembly_effect = yes" not in mandate_events:
        err("jingcha deadline must resolve the review when assembly becomes impossible")
    refusal_body = mandate_effects.split("zg361_refuse_jingcha_effect = {", 1)[-1].split(
        "zg361_clear_jingcha_mandate_effect = {", 1
    )[0]
    if (
        "has_variable = zg361_jingcha_mandate_superior" not in refusal_body
        or refusal_body.rfind("zg361_clear_jingcha_mandate_effect = yes")
        < refusal_body.find("has_variable = zg361_jingcha_mandate_superior")
    ):
        err("jingcha refusal must consume saved superior metadata before clearing it")
    cleanup_body = mandate_effects.split(
        "zg361_clear_jingcha_mandate_effect = {", 1
    )[-1].split("zg361_excuse_jingcha_assembly_effect = {", 1)[0]
    for variable in (
        "zg361_jingcha_pending",
        "zg361_jingcha_mandate_superior",
        "zg361_jingcha_mandate_reviewer",
        "zg361_jingcha_mandate_year",
    ):
        if f"remove_variable = {variable}" not in cleanup_body:
            err(f"jingcha lifecycle cleanup omits {variable}")
    if "zg361_jingcha_phase = {" not in activity:
        err("jingcha activity must use its own localized phase key")
    phase_icon = (
        MOD_ROOT
        / "gfx"
        / "interface"
        / "icons"
        / "activity_phases"
        / "zg361_jingcha_phase.dds"
    )
    if not phase_icon.is_file() or phase_icon.stat().st_size == 0:
        err("jingcha custom phase must ship a non-empty icon asset")
    if "cancelled jingcha remains due before mandate deadline" not in activity:
        err("cancelling a jingcha activity must not erase the pending mandate")
    if activity.count("has_variable = zg361_jingcha_pending") < 2:
        err("jingcha activity must be gated by a live mandate in shown and start checks")
    activity_assets = (
        MOD_ROOT / "gfx" / "interface" / "icons" / "activities" / "activity_zg361_jingcha.dds",
        MOD_ROOT / "gfx" / "interface" / "icons" / "activities" / "activity_zg361_jingcha_header.dds",
        MOD_ROOT
        / "gfx"
        / "interface"
        / "illustrations"
        / "activity_header_backgrounds"
        / "activity_zg361_jingcha.dds",
    )
    for asset in activity_assets:
        if not asset.is_file() or asset.stat().st_size == 0:
            err(f"jingcha activity UI asset missing: {asset.relative_to(MOD_ROOT).as_posix()}")
    if not re.search(
        r"on_complete\s*=\s*\{.*?limit\s*=\s*\{\s*this\s*=\s*scope:host\s*\}.*?"
        r"scope:activity\s*=\s*\{.*?every_attending_character",
        activity,
        re.S,
    ):
        err("jingcha completion must run once as host before iterating attendees")
    for obsolete in (
        "zg361_jingcha_last_completed_year",
        "zg361_jingcha_last_excused_year",
        "zg361_jingcha_last_refused_year",
        "zg361_last_review_year",
        "zg361_bottom_cut",
        "zg361_bottom_cut_next",
    ):
        if obsolete in activity or obsolete in mandate_effects or obsolete in effects:
            err(f"unused CK3 telemetry variable must not be written: {obsolete}")
    for token in (
        "zg361_skipped_jingcha_kpi_malus_value = 50",
        "has_variable = zg361_skipped_jingcha_superior",
        "var:zg361_skipped_jingcha_superior = liege",
        "subtract = zg361_skipped_jingcha_kpi_malus_value",
    ):
        if token not in values:
            err(f"one-use skipped-jingcha KPI contract missing token: {token}")
    if not re.search(
        r"zg361_compute_kpi_effect\s*=\s*\{.*?"
        r"set_variable\s*=\s*\{\s*name\s*=\s*zg361_kpi\s+value\s*=\s*zg361_kpi_value\s*\}.*?"
        r"remove_variable\s*=\s*zg361_skipped_jingcha_superior",
        effects,
        re.S,
    ):
        err("skipped-jingcha marker must be consumed immediately after its KPI is calculated")

    if interactions.count("zg361_b1_peer_submission_actor_trigger = yes") != 2:
        err("recommendation and slander must both require the live B1 peer window")
    if interactions.count("zg361_b1_peer_submission_recipient_trigger = yes") != 2:
        err("recommendation and slander must both require a same-cycle recipient slot")

    chinese = read_text(
        MOD_ROOT / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml"
    )
    for token in (
        'zg361.1.t:0 "你主持的考核：名册已定"',
        'zg361.2.t:0 "上司考定：3.75',
        'zg361.3.t:0 "上司考定：3.5',
        'zg361.4.t:0 "上司考定：3.25',
        "TopScope.GetValue('zg361_result_kpi')",
        "TopScope.GetValue('zg361_result_rank')",
        "TopScope.GetValue('zg361_result_cohort_n')",
    ):
        if token not in chinese:
            err(f"personal performance writ must expose its identity and result: {token}")
    if effects.count("save_scope_as = zg361_reviewing_superior") != 1:
        err("player result snapshot helper must freeze its reviewer exactly once")
    for variable in (
        "zg361_result_kpi",
        "zg361_result_rank",
        "zg361_result_cohort_n",
    ):
        if len(re.findall(rf"name\s*=\s*{variable}(?=\s)", effects)) != 1:
            err(
                "player result snapshot helper must freeze loc data exactly once: "
                f"name = {variable}"
            )
    if "liege = { save_scope_as = zg361_reviewing_superior }" in events:
        err("delayed personal result events must not re-read the live liege")
    if events.count(
        "var:zg361_result_case_owner = { save_scope_as = zg361_reviewing_superior }"
    ) != 2:
        err("formal notice and reopenable statement must read the frozen case owner")
    if effects.count("zg361_snapshot_player_result_effect = yes") != 3:
        err("all three grade effects must freeze the delayed personal result payload")


def check_generated_contracts() -> None:
    """Require exact 1..361 coverage and byte-reproducible generated projections."""
    manifest_path = MOD_ROOT / "docs" / "361-mechanism-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        err(f"cannot read 361 mechanism manifest: {error}")
        return
    items = manifest.get("items")
    if not isinstance(items, list):
        err("361 mechanism manifest items must be a list")
        return
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if ids != list(range(1, 362)):
        err("361 mechanism manifest must contain ordered IDs 1..361 exactly once")
    events_path = MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt"
    effects_path = (
        MOD_ROOT / "common" / "scripted_effects" / "zg361_generated_mechanism_effects.txt"
    )
    event_text = read_text(events_path) if events_path.is_file() else ""
    effect_text = read_text(effects_path) if effects_path.is_file() else ""
    event_ids = [int(value) for value in re.findall(r"^zg361m\.(\d+)\s*=\s*\{", event_text, re.M)]
    if event_ids != list(range(1, 362)):
        err("generated mechanism events must define zg361m.1..361 in order")
    for mechanism_id in range(1, 362):
        for choice in ("a", "b", "c"):
            token = f"zg361_mechanism_{mechanism_id:03d}_choice_{choice}_effect = {{"
            if effect_text.count(token) != 1:
                err(f"mechanism {mechanism_id:03d} must define choice {choice} exactly once")
        ai_token = f"zg361_mechanism_{mechanism_id:03d}_ai_effect = {{"
        if effect_text.count(ai_token) != 1:
            err(f"mechanism {mechanism_id:03d} must define one AI path")
    try:
        from gen_361_mechanisms import outputs as mechanism_outputs
        from zg361_mechanism_data import load_mechanisms
        from gen_scoreboard_snapshot import outputs as scoreboard_outputs

        rendered = mechanism_outputs(load_mechanisms(MOD_ROOT))
        rendered.update(scoreboard_outputs())
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in rendered.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        if stale:
            err(f"generated projections are stale: {stale}")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        err(f"cannot reproduce generated projections: {error}")


def check_referenced_keys(key_sets: dict[str, set[str]]) -> None:
    refs = collect_referenced_keys()
    all_refs = refs["events"] | refs["event_options"] | refs["plain"]
    for lang in ("simp_chinese", "english"):
        missing = sorted(all_refs - key_sets.get(lang, set()))
        if missing:
            err(f"keys referenced in scripts but missing from {lang} yml: {missing}")


def main() -> int:
    if not MOD_ROOT.is_dir():
        print(f"mod root missing: {MOD_ROOT}")
        return 1
    check_bom()
    check_descriptor()
    check_braces()
    check_widget_registrations()
    key_sets = check_localization()
    check_referenced_keys(key_sets)
    check_runtime_invariants()
    check_generated_contracts()
    if errors:
        print(f"RED: {len(errors)} problem(s) in mod_zhongguo_style")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("GREEN: mod_zhongguo_style static checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
