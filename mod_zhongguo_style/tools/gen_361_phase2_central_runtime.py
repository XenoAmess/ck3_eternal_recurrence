#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the Zhongguo 361 phase-two central serial dispatcher.

This package owns orchestration only.  It calls each domain's documented
public adapter, freezes one post-B1 subject, and never edits domain runtimes.
Generated source is static-ready evidence, not CK3/MCP live evidence.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Final


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_361_phase2_central_runtime.py\n"
READINESS = "static-ready"
LEGACY_EFFECT_FILENAME = "zg361_phase2_central_runtime_effects.txt"
LEGACY_EFFECT_PATH = MOD_ROOT / "common" / "scripted_effects" / LEGACY_EFFECT_FILENAME
EFFECT_SHARD_GLOB = "zg361_phase2_central_*_effects.txt"
HISTORICAL_EFFECT_BYTES = 126_811
HISTORICAL_EFFECT_SHA256 = "94D893631FCF1C6FDF25F19D536C99664112E6C16AC39BFC2D4EDC36C13B3CEB"
HISTORICAL_EFFECT_COUNT = 32
EFFECT_TARGET_MAX = 10
EFFECT_HARD_MAX = 20
# A future shard above the hard principle is allowed only when this map names
# that exact shard and supplies both its cohesion reason and concrete CK3 live
# evidence.  The current purpose split needs no exception.
EFFECT_HARD_LIMIT_EXCEPTIONS: Final[dict[str, tuple[str, str]]] = {}


@dataclass(frozen=True)
class EffectGroup:
    filename: str
    purpose: str
    effect_names: tuple[str, ...]

LANGUAGES = (
    ("english", "l_english"),
    ("french", "l_french"),
    ("german", "l_german"),
    ("japanese", "l_japanese"),
    ("korean", "l_korean"),
    ("polish", "l_polish"),
    ("russian", "l_russian"),
    ("simp_chinese", "l_simp_chinese"),
    ("spanish", "l_spanish"),
)

STAGES = (
    (1, "career_hc", "zg361_career_hc_open_portfolio_effect"),
    (2, "compensation", "zg361_comp_portfolio_open_next_effect"),
    (3, "feedback_promotion_pip", "zg361_pp_manager_portfolio_adapter_effect"),
    (4, "incident_x", "zg361_ip_open_x_case_effect"),
    (5, "incident_y", "zg361_ip_open_y_case_effect"),
    (6, "incident_z", "zg361_ip_open_z_case_effect"),
    (7, "metrics_delivery", "zg361_p3_open_portfolio_effect"),
    (8, "credit_project", "zg361_cp_open_portfolio_effect"),
    (9, "career_learning", "zg361_cl_dispatch_direct_reports_effect"),
    (10, "manager_governance", "zg361_mg_dispatch_subordinate_managers_effect"),
    (11, "workforce_endgame", "zg361_we_open_portfolio_effect"),
)


# Keep this ordered exactly like ``render_effects()``.  The boundaries are
# operational: each file owns one coherent source, dispatcher, lifecycle or
# stage family, and every shard remains inside the 1..10 target (and therefore
# the <=20 hard principle) without cutting a top-level definition.
EFFECT_GROUPS = (
    EffectGroup(
        "zg361_phase2_central_001_m360_source_effects.txt",
        "M360 route-neutral source clearing, envelope freezing and cohort preparation",
        (
            "zg361_p2c_clear_m360_source_effect",
            "zg361_p2c_freeze_m360_source_envelope_effect",
            "zg361_p2c_prepare_m360_source_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_002_m275_requisition_effects.txt",
        "M275 runner-up requisition scheduling and immutable source production",
        (
            "zg361_p2c_schedule_m275_runner_requisition_effect",
            "zg361_p2c_open_m275_runner_requisition_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_003_dispatch_control_effects.txt",
        "serial lane, pump scheduling, summary and terminal status controls",
        (
            "zg361_p2c_mark_lane_busy_effect",
            "zg361_p2c_schedule_pump_effect",
            "zg361_p2c_queue_summary_effect",
            "zg361_p2c_record_stage_effect",
            "zg361_p2c_record_red_effect",
            "zg361_p2c_mark_external_wait_effect",
            "zg361_p2c_abort_stale_effect",
            "zg361_p2c_finish_effect",
            "zg361_p2c_suspend_external_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_004_lifecycle_hooks_effects.txt",
        "B1 publication initialization and exact delivered-result wake-up hooks",
        (
            "zg361_p2c_on_review_published_effect",
            "zg361_p2c_on_result_delivered_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_005_stage01_03_effects.txt",
        "career, compensation and feedback promotion PIP adapters and stages",
        (
            "zg361_p2c_call_career_hc_adapter_effect",
            "zg361_p2c_call_compensation_adapter_effect",
            "zg361_p2c_call_pp_adapter_effect",
            "zg361_p2c_stage_01_career_hc_effect",
            "zg361_p2c_stage_02_compensation_effect",
            "zg361_p2c_stage_03_feedback_promotion_pip_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_006_incident_stages_effects.txt",
        "ordered incident X, Y and Z stages",
        (
            "zg361_p2c_stage_04_x_effect",
            "zg361_p2c_stage_05_y_effect",
            "zg361_p2c_stage_06_z_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_007_stage07_09_effects.txt",
        "metrics delivery, credit project and career learning stages",
        (
            "zg361_p2c_stage_07_metrics_delivery_effect",
            "zg361_p2c_stage_08_credit_project_effect",
            "zg361_p2c_stage_09_career_learning_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_008_stage10_manager_governance_effects.txt",
        "manager governance strict-lag stage",
        ("zg361_p2c_stage_10_manager_governance_effect",),
    ),
    EffectGroup(
        "zg361_phase2_central_009_stage11_workforce_endgame_effects.txt",
        "workforce adapter and workforce endgame stage",
        (
            "zg361_p2c_call_workforce_adapter_effect",
            "zg361_p2c_stage_11_workforce_endgame_effect",
        ),
    ),
    EffectGroup(
        "zg361_phase2_central_010_serial_pump_effects.txt",
        "single-stage serial pump dispatcher",
        ("zg361_p2c_pump_effect",),
    ),
)

M360_FREEZE_GLOBAL_FIELDS = (
    "status",
    "reason",
    "upstream_reason",
    "owner",
    "subject",
    "p2c_cycle",
    "p2c_case",
    "al_cycle",
    "al_case",
    "cohort_count",
    "total_quota",
)

M360_FREEZE_COHORT_FIELDS = (
    "manager",
    "b1_cycle",
    "b1_case",
    "b1_source_id",
    "b1_source_hash",
    "quota",
    "mg_cycle",
    "mg_case",
    "mg_snapshot_source_serial",
    "mg_snapshot_revision",
)

M360_SOURCE_STATUS = {
    "none": 0,
    "ready": 1,
    "consumed": 2,
    "red": 4,
    "wait": 5,
    "structural_na": 7,
}


def m360_slot_guard(slot: int) -> str:
    """Return one conditional proof for a READY B1 forced-C slot."""

    base = f"zg361_b1_m360_source_forced_{slot}"
    return f'''trigger_if = {{
    limit = {{ var:zg361_b1_m360_source_quota >= {slot} }}
    has_variable = {base}_character
    has_variable = {base}_processing_order
    has_variable = {base}_m357_receipt_id
    has_variable = {base}_m357_receipt_hash
    has_variable = {base}_b1_owner
    has_variable = {base}_b1_subject
    has_variable = {base}_b1_cycle
    has_variable = {base}_b1_case
    has_variable = {base}_result_owner
    has_variable = {base}_result_subject
    has_variable = {base}_result_cycle
    has_variable = {base}_result_case
    var:{base}_processing_order >= 1
    var:{base}_processing_order <= var:zg361_b1_m360_source_member_count
    var:{base}_m357_receipt_id > 0
    var:{base}_m357_receipt_hash > 0
    var:{base}_b1_owner = this
    var:{base}_b1_subject = var:{base}_character
    var:{base}_b1_cycle = var:zg361_b1_m360_source_cycle
    var:{base}_b1_case = var:zg361_b1_m360_source_case
    var:{base}_result_owner = this
    var:{base}_result_subject = var:{base}_character
    var:{base}_result_cycle = var:zg361_b1_m360_source_cycle
    var:{base}_result_case > 0
}}
trigger_else = {{ always = yes }}'''


def render_m360_triggers() -> str:
    """Render Central's exact B1+MG candidate and frozen-drift guards."""

    slot_guards = "\n".join(m360_slot_guard(slot) for slot in range(1, 7))
    return HEADER + f'''# Route-neutral #360 source validation.  Central freezes only product-owned
# manager/source identities; Workforce later materializes the route-specific
# partition after A/B is selected.

zg361_p2c_m360_candidate_ready_trigger = {{
    zg361_is_celestial_liege_trigger = yes
    liege = $EXPECTED_OWNER$
    has_variable = zg361_p2c_mg_frozen_owner
    has_variable = zg361_p2c_mg_frozen_cycle
    has_variable = zg361_p2c_mg_frozen_case
    has_variable = zg361_p2c_mg_frozen_order
    var:zg361_p2c_mg_frozen_owner = $EXPECTED_OWNER$
    var:zg361_p2c_mg_frozen_cycle = $EXPECTED_P2C_CYCLE$
    var:zg361_p2c_mg_frozen_case = $EXPECTED_P2C_CASE$
    var:zg361_p2c_mg_frozen_order >= 1

    has_variable = zg361_b1_m360_source_status
    has_variable = zg361_b1_m360_source_available
    has_variable = zg361_b1_m360_source_sealed
    has_variable = zg361_b1_m360_source_manager
    has_variable = zg361_b1_m360_source_cycle
    has_variable = zg361_b1_m360_source_case
    has_variable = zg361_b1_m360_source_state
    has_variable = zg361_b1_m360_source_id
    has_variable = zg361_b1_m360_source_hash
    has_variable = zg361_b1_m360_source_member_count
    has_variable = zg361_b1_m360_source_member_hash
    has_variable = zg361_b1_m360_source_agenda_count
    has_variable = zg361_b1_m360_source_agenda_hash
    has_variable = zg361_b1_m360_source_quota
    has_variable = zg361_b1_m360_source_all_meet_receipt_serial
    has_variable = zg361_b1_m360_source_forced_count
    var:zg361_b1_m360_source_status = 1
    var:zg361_b1_m360_source_available = 1
    var:zg361_b1_m360_source_sealed = 1
    var:zg361_b1_m360_source_manager = this
    var:zg361_b1_m360_source_cycle > 0
    var:zg361_b1_m360_source_case > 0
    var:zg361_b1_m360_source_state = 8
    var:zg361_b1_m360_source_id > 0
    var:zg361_b1_m360_source_hash > 0
    var:zg361_b1_m360_source_member_count >= 1
    var:zg361_b1_m360_source_member_hash > 0
    var:zg361_b1_m360_source_agenda_count = var:zg361_b1_m360_source_member_count
    var:zg361_b1_m360_source_agenda_hash = var:zg361_b1_m360_source_member_hash
    var:zg361_b1_m360_source_quota >= 1
    var:zg361_b1_m360_source_quota <= 6
    var:zg361_b1_m360_source_quota <= var:zg361_b1_m360_source_member_count
    var:zg361_b1_m360_source_forced_count = var:zg361_b1_m360_source_quota
    var:zg361_b1_m360_source_all_meet_receipt_serial > 0
{slot_guards.replace(chr(10), chr(10) + '    ')}

    has_variable = zg361_case_f_owner
    has_variable = zg361_case_f_subject
    has_variable = zg361_case_f_cycle_serial
    has_variable = zg361_case_f_case_serial
    has_variable = zg361_case_f_state
    has_variable = zg361_case_f_active
    var:zg361_case_f_owner = $EXPECTED_OWNER$
    var:zg361_case_f_subject = this
    var:zg361_case_f_cycle_serial = $EXPECTED_P2C_CYCLE$
    var:zg361_case_f_case_serial > 0
    var:zg361_case_f_state = 5
    var:zg361_case_f_active = 0
    has_variable = zg361_mg_team_snapshot_status
    has_variable = zg361_mg_team_snapshot_owner
    has_variable = zg361_mg_team_snapshot_subject
    has_variable = zg361_mg_team_snapshot_cycle
    has_variable = zg361_mg_team_snapshot_case
    has_variable = zg361_mg_team_snapshot_revision
    has_variable = zg361_mg_snapshot_source_serial
    has_variable = zg361_mg_team_snapshot_b1_available
    has_variable = zg361_mg_team_snapshot_b1_manager
    has_variable = zg361_mg_team_snapshot_b1_cycle
    has_variable = zg361_mg_team_snapshot_b1_case
    has_variable = zg361_mg_team_n
    has_variable = zg361_mg_team_bottom_n
    var:zg361_mg_team_snapshot_status = 1
    var:zg361_mg_team_snapshot_owner = $EXPECTED_OWNER$
    var:zg361_mg_team_snapshot_subject = this
    var:zg361_mg_team_snapshot_cycle = var:zg361_case_f_cycle_serial
    var:zg361_mg_team_snapshot_case = var:zg361_case_f_case_serial
    var:zg361_mg_team_snapshot_revision > 0
    var:zg361_mg_snapshot_source_serial = var:zg361_b1_m360_source_cycle
    var:zg361_mg_team_snapshot_b1_available = 1
    var:zg361_mg_team_snapshot_b1_manager = this
    var:zg361_mg_team_snapshot_b1_cycle = var:zg361_b1_m360_source_cycle
    var:zg361_mg_team_snapshot_b1_case = var:zg361_b1_m360_source_case
    var:zg361_mg_team_n = var:zg361_b1_m360_source_member_count
    var:zg361_mg_team_bottom_n = var:zg361_b1_m360_source_quota
    has_variable = zg361_mg_m036_receipt_owner
    has_variable = zg361_mg_m036_receipt_subject
    has_variable = zg361_mg_m036_receipt_cycle
    has_variable = zg361_mg_m036_receipt_case
    has_variable = zg361_mg_m036_receipt_state
    has_variable = zg361_mg_m036_receipt_choice
    var:zg361_mg_m036_receipt_owner = $EXPECTED_OWNER$
    var:zg361_mg_m036_receipt_subject = this
    var:zg361_mg_m036_receipt_cycle = var:zg361_case_f_cycle_serial
    var:zg361_mg_m036_receipt_case = var:zg361_case_f_case_serial
    var:zg361_mg_m036_receipt_state = 4
    OR = {{ var:zg361_mg_m036_receipt_choice = 1 var:zg361_mg_m036_receipt_choice = 2 }}
}}

zg361_p2c_m360_frozen_manager_exact_trigger = {{
    zg361_p2c_m360_candidate_ready_trigger = {{
        EXPECTED_OWNER = $EXPECTED_OWNER$
        EXPECTED_P2C_CYCLE = $EXPECTED_P2C_CYCLE$
        EXPECTED_P2C_CASE = $EXPECTED_P2C_CASE$
    }}
    var:zg361_b1_m360_source_cycle = $EXPECTED_B1_CYCLE$
    var:zg361_b1_m360_source_case = $EXPECTED_B1_CASE$
    var:zg361_b1_m360_source_id = $EXPECTED_B1_SOURCE_ID$
    var:zg361_b1_m360_source_hash = $EXPECTED_B1_SOURCE_HASH$
    var:zg361_b1_m360_source_quota = $EXPECTED_QUOTA$
    var:zg361_case_f_cycle_serial = $EXPECTED_MG_CYCLE$
    var:zg361_case_f_case_serial = $EXPECTED_MG_CASE$
    var:zg361_mg_snapshot_source_serial = $EXPECTED_MG_SOURCE_SERIAL$
    var:zg361_mg_team_snapshot_revision = $EXPECTED_MG_REVISION$
}}
'''


def incident_na_guard(domain: str) -> str:
    """Return the exact no-incident receipt accepted as stage status 3."""

    return f'''has_variable = zg361_ip_{domain}_final_applicable
                has_variable = zg361_ip_{domain}_final_na_owner
                has_variable = zg361_ip_{domain}_final_na_subject
                has_variable = zg361_ip_{domain}_final_na_cycle
                has_variable = zg361_ip_{domain}_final_na_reason
                has_variable = zg361_ip_{domain}_final_na_probe_serial
                has_variable = zg361_ip_{domain}_final_na_receipt
                has_variable = zg361_ip_{domain}_na_receipt_serial
                has_variable = zg361_ip_{domain}_final_kpi_staged
                has_variable = zg361_ip_probe_owner
                has_variable = zg361_ip_probe_subject
                has_variable = zg361_ip_probe_cycle
                has_variable = zg361_ip_probe_serial
                has_variable = zg361_ip_probe_result
                has_variable = zg361_ip_probe_source_kind
                has_variable = zg361_ip_probe_consequence_kind
                var:zg361_ip_{domain}_final_applicable = 0
                var:zg361_ip_{domain}_final_na_owner = root
                var:zg361_ip_{domain}_final_na_subject = this
                var:zg361_ip_{domain}_final_na_cycle = root.var:zg361_p2c_cycle
                var:zg361_ip_{domain}_final_na_reason = 1
                var:zg361_ip_{domain}_final_na_probe_serial = var:zg361_ip_probe_serial
                var:zg361_ip_{domain}_final_na_receipt = var:zg361_ip_{domain}_na_receipt_serial
                var:zg361_ip_{domain}_final_na_probe_serial > 0
                var:zg361_ip_{domain}_final_na_receipt > 0
                var:zg361_ip_{domain}_na_receipt_serial > 0
                var:zg361_ip_{domain}_final_kpi_staged = 0
                var:zg361_ip_probe_owner = root
                var:zg361_ip_probe_subject = this
                var:zg361_ip_probe_cycle = root.var:zg361_p2c_cycle
                var:zg361_ip_probe_result = 0
                var:zg361_ip_probe_source_kind = 0
                var:zg361_ip_probe_consequence_kind = 0
                var:zg361_ip_probe_serial > 0
                trigger_if = {{ limit = {{ has_variable = zg361_case_{domain}_active }} var:zg361_case_{domain}_active = 0 }}
                trigger_else = {{ always = yes }}'''


def incident_stage(stage: int, domain: str, terminal_state: int) -> str:
    return f"""
# Stage {stage}: one incident domain only.  The all-domain portfolio ABI is
# intentionally not used, so X/Y/Z can never flood the player together.
zg361_p2c_stage_{stage:02d}_{domain}_effect = {{
    if = {{
        limit = {{
            var:zg361_p2c_subject = {{
                has_variable = zg361_ip_{domain}_final_owner
                has_variable = zg361_ip_{domain}_final_subject
                has_variable = zg361_ip_{domain}_final_cycle
                has_variable = zg361_ip_{domain}_final_case
                has_variable = zg361_ip_{domain}_final_state
                has_variable = zg361_ip_{domain}_final_applicable
                has_variable = zg361_ip_{domain}_final_incident_serial
                has_variable = zg361_ip_{domain}_final_source_kind
                has_variable = zg361_ip_{domain}_final_consequence_kind
                has_variable = zg361_ip_{domain}_final_kpi_staged
                var:zg361_ip_{domain}_final_owner = root
                var:zg361_ip_{domain}_final_subject = this
                var:zg361_ip_{domain}_final_cycle = root.var:zg361_p2c_cycle
                var:zg361_ip_{domain}_final_state = {terminal_state}
                var:zg361_ip_{domain}_final_applicable = 1
                var:zg361_ip_{domain}_final_incident_serial > 0
                var:zg361_ip_{domain}_final_source_kind > 0
                var:zg361_ip_{domain}_final_consequence_kind > 0
                var:zg361_ip_{domain}_final_kpi_staged = 1
                var:zg361_case_{domain}_active = 0
                var:zg361_ip_{domain}_final_case = var:zg361_case_{domain}_case_serial
            }}
        }}
        zg361_p2c_record_stage_effect = {{ STATUS = 2 STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }}
    }}
    else_if = {{
        limit = {{
            var:zg361_p2c_subject = {{
                {incident_na_guard(domain)}
            }}
        }}
        zg361_p2c_record_stage_effect = {{ STATUS = 3 STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }}
    }}
    else_if = {{
        limit = {{
            var:zg361_p2c_subject = {{
                has_variable = zg361_case_{domain}_owner
                has_variable = zg361_case_{domain}_subject
                has_variable = zg361_case_{domain}_cycle_serial
                has_variable = zg361_case_{domain}_case_serial
                has_variable = zg361_case_{domain}_active
                var:zg361_case_{domain}_owner = root
                var:zg361_case_{domain}_subject = this
                var:zg361_case_{domain}_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_case_{domain}_active = 1
            }}
        }}
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = {{ DAYS = 2 }}
    }}
    else_if = {{
        limit = {{ var:zg361_p2c_stage_status = 0 }}
        zg361_ip_open_{domain}_case_effect = {{ SUBJECT = var:zg361_p2c_subject }}
        if = {{
            limit = {{
                var:zg361_p2c_subject = {{
                    has_variable = zg361_case_{domain}_owner
                    has_variable = zg361_case_{domain}_subject
                    has_variable = zg361_case_{domain}_cycle_serial
                    has_variable = zg361_case_{domain}_active
                    var:zg361_case_{domain}_owner = root
                    var:zg361_case_{domain}_subject = this
                    var:zg361_case_{domain}_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_{domain}_active = 1
                }}
            }}
            set_variable = {{ name = zg361_p2c_stage_status value = 1 }}
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = {{ DAYS = 2 }}
        }}
        else_if = {{
            limit = {{
                var:zg361_p2c_subject = {{
                    {incident_na_guard(domain)}
                }}
            }}
            zg361_p2c_record_stage_effect = {{ STATUS = 3 STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }}
        }}
        else = {{ zg361_p2c_record_red_effect = {{ CODE = {400 + stage} STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }} }}
    }}
    else = {{ zg361_p2c_record_red_effect = {{ CODE = {450 + stage} STAGE_VAR = zg361_p2c_stage_{stage:02d}_status }} }}
}}
"""


def m360_clear_source_lines() -> str:
    fields = [
        *(f"zg361_p2c_m360_source_{field}" for field in M360_FREEZE_GLOBAL_FIELDS),
        *(
            f"zg361_p2c_m360_source_c{cohort}_{field}"
            for cohort in (1, 2, 3)
            for field in M360_FREEZE_COHORT_FIELDS
        ),
    ]
    return "\n".join(f"remove_variable = {field}" for field in fields)


def m360_freeze_cohort_lines(cohort: int, source: str) -> str:
    """Freeze one manager's route-neutral B1/MG identity on Central owner."""

    mapping = {
        "manager": source,
        "b1_cycle": f"{source}.var:zg361_b1_m360_source_cycle",
        "b1_case": f"{source}.var:zg361_b1_m360_source_case",
        "b1_source_id": f"{source}.var:zg361_b1_m360_source_id",
        "b1_source_hash": f"{source}.var:zg361_b1_m360_source_hash",
        "quota": f"{source}.var:zg361_b1_m360_source_quota",
        "mg_cycle": f"{source}.var:zg361_case_f_cycle_serial",
        "mg_case": f"{source}.var:zg361_case_f_case_serial",
        "mg_snapshot_source_serial": f"{source}.var:zg361_mg_snapshot_source_serial",
        "mg_snapshot_revision": f"{source}.var:zg361_mg_team_snapshot_revision",
    }
    return "\n".join(
        f"set_variable = {{ name = zg361_p2c_m360_source_c{cohort}_{field} value = {value} }}"
        for field, value in mapping.items()
    )


def m360_frozen_manager_call(cohort: int) -> str:
    return f'''var:zg361_p2c_m360_source_c{cohort}_manager = {{
    zg361_p2c_m360_frozen_manager_exact_trigger = {{
        EXPECTED_OWNER = root
        EXPECTED_P2C_CYCLE = root.var:zg361_p2c_m360_source_p2c_cycle
        EXPECTED_P2C_CASE = root.var:zg361_p2c_m360_source_p2c_case
        EXPECTED_B1_CYCLE = root.var:zg361_p2c_m360_source_c{cohort}_b1_cycle
        EXPECTED_B1_CASE = root.var:zg361_p2c_m360_source_c{cohort}_b1_case
        EXPECTED_B1_SOURCE_ID = root.var:zg361_p2c_m360_source_c{cohort}_b1_source_id
        EXPECTED_B1_SOURCE_HASH = root.var:zg361_p2c_m360_source_c{cohort}_b1_source_hash
        EXPECTED_QUOTA = root.var:zg361_p2c_m360_source_c{cohort}_quota
        EXPECTED_MG_CYCLE = root.var:zg361_p2c_m360_source_c{cohort}_mg_cycle
        EXPECTED_MG_CASE = root.var:zg361_p2c_m360_source_c{cohort}_mg_case
        EXPECTED_MG_SOURCE_SERIAL = root.var:zg361_p2c_m360_source_c{cohort}_mg_snapshot_source_serial
        EXPECTED_MG_REVISION = root.var:zg361_p2c_m360_source_c{cohort}_mg_snapshot_revision
    }}
}}'''


def render_m360_source_effects() -> str:
    """Render Central's route-neutral selection/freeze state machine."""

    clear = m360_clear_source_lines()
    freeze_c1 = m360_freeze_cohort_lines(1, "var:zg361_p2c_subject")
    freeze_c2 = m360_freeze_cohort_lines(2, "scope:zg361_p2c_m360_candidate_2")
    freeze_c3 = m360_freeze_cohort_lines(3, "scope:zg361_p2c_m360_candidate_3")
    frozen_guards = "\n".join(m360_frozen_manager_call(cohort) for cohort in (1, 2, 3))
    return f'''# Clear only Central-owned #360 route-neutral identity.  Product B1/MG
# sources and Workforce business objects remain immutable in their own scopes.
zg361_p2c_clear_m360_source_effect = {{
{clear.replace(chr(10), chr(10) + '    ')}
    set_variable = {{ name = zg361_p2c_m360_source_status value = 0 }}
    set_variable = {{ name = zg361_p2c_m360_source_reason value = 0 }}
}}

# Bind every terminal pre-materialization result to the same Central/AL case.
# A structural N/A or pre-freeze RED must not be replayed against a newer AL
# case merely because no cohort payload was produced.
zg361_p2c_freeze_m360_source_envelope_effect = {{
    set_variable = {{ name = zg361_p2c_m360_source_owner value = this }}
    set_variable = {{ name = zg361_p2c_m360_source_subject value = var:zg361_p2c_subject }}
    set_variable = {{ name = zg361_p2c_m360_source_p2c_cycle value = var:zg361_p2c_cycle }}
    set_variable = {{ name = zg361_p2c_m360_source_p2c_case value = var:zg361_p2c_case_serial }}
    set_variable = {{ name = zg361_p2c_m360_source_al_cycle value = var:zg361_p2c_subject.var:zg361_case_al_cycle_serial }}
    set_variable = {{ name = zg361_p2c_m360_source_al_case value = var:zg361_p2c_subject.var:zg361_case_al_case_serial }}
}}

# Freeze C1 as the primary assessed manager, then the first viable ordered C2/C3
# pair from stage 10's immutable manager list.  A pair over the six-slot product
# cap is skipped as a whole; no quota or member list is truncated.
zg361_p2c_prepare_m360_source_effect = {{
    if = {{
        limit = {{
            has_variable = zg361_p2c_m360_source_status
            var:zg361_p2c_m360_source_status = 1
        }}
        if = {{
            limit = {{
                has_variable = zg361_p2c_m360_source_owner
                has_variable = zg361_p2c_m360_source_subject
                has_variable = zg361_p2c_m360_source_p2c_cycle
                has_variable = zg361_p2c_m360_source_p2c_case
                has_variable = zg361_p2c_m360_source_al_cycle
                has_variable = zg361_p2c_m360_source_al_case
                has_variable = zg361_p2c_m360_source_cohort_count
                has_variable = zg361_p2c_m360_source_total_quota
                var:zg361_p2c_m360_source_owner = this
                var:zg361_p2c_m360_source_subject = var:zg361_p2c_subject
                var:zg361_p2c_m360_source_p2c_cycle = var:zg361_p2c_cycle
                var:zg361_p2c_m360_source_p2c_case = var:zg361_p2c_case_serial
                var:zg361_p2c_m360_source_al_cycle = var:zg361_p2c_subject.var:zg361_case_al_cycle_serial
                var:zg361_p2c_m360_source_al_case = var:zg361_p2c_subject.var:zg361_case_al_case_serial
                var:zg361_p2c_m360_source_cohort_count = 3
                var:zg361_p2c_m360_source_total_quota >= 1
                var:zg361_p2c_m360_source_total_quota <= 6
{frozen_guards.replace(chr(10), chr(10) + '                ')}
            }}
            # Exact READY replay is a no-op.
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 0 }}
        }}
        else = {{
            set_variable = {{ name = zg361_p2c_m360_source_status value = 4 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360495 }}
            debug_log = "ZG361P2C RED: frozen M360 manager/source tuple drifted"
        }}
    }}
    else_if = {{
        limit = {{
            has_variable = zg361_p2c_m360_source_status
            OR = {{
                var:zg361_p2c_m360_source_status = 2
                var:zg361_p2c_m360_source_status = 4
                var:zg361_p2c_m360_source_status = 7
            }}
        }}
        # Consumed, RED and structural N/A are terminal and never reselect.
    }}
    else_if = {{
        limit = {{
            var:zg361_p2c_subject = {{
                zg361_case_kernel_full_guard_trigger = {{
                    OWNER_VAR = zg361_case_al_owner SUBJECT_VAR = zg361_case_al_subject
                    CYCLE_VAR = zg361_case_al_cycle_serial CASE_VAR = zg361_case_al_case_serial
                    STATE_VAR = zg361_case_al_state ACTIVE_VAR = zg361_case_al_active
                    EXPECTED_OWNER = root EXPECTED_SUBJECT = this
                    EXPECTED_CYCLE = root.var:zg361_p2c_cycle
                    EXPECTED_CASE = var:zg361_case_al_case_serial EXPECTED_STATE = 4
                }}
                has_variable = zg361_we_al_external_stage_receipts_verified
                var:zg361_we_al_external_stage_receipts_verified = 1
                var:zg361_we_al_external_receipt_owner = root
                var:zg361_we_al_external_receipt_subject = this
                var:zg361_we_al_external_receipt_cycle = root.var:zg361_p2c_cycle
                var:zg361_we_al_external_receipt_case = var:zg361_case_al_case_serial
                var:zg361_we_al_external_receipt_state = 4
                var:zg361_we_al_external_receipt_count = 3
                var:zg361_we_al_external_last_operation = 359
            }}
        }}
        set_variable = {{ name = zg361_p2c_m360_probe_primary_in_frozen value = 0 }}
        set_variable = {{ name = zg361_p2c_m360_probe_valid_n value = 0 }}
        set_variable = {{ name = zg361_p2c_m360_probe_structural_na_n value = 0 }}
        set_variable = {{ name = zg361_p2c_m360_probe_wait_n value = 0 }}
        set_variable = {{ name = zg361_p2c_m360_probe_invalid_n value = 0 }}
        every_in_list = {{
            variable = zg361_p2c_mg_subjects
            if = {{
                limit = {{ this = root.var:zg361_p2c_subject }}
                root = {{ set_variable = {{ name = zg361_p2c_m360_probe_primary_in_frozen value = 1 }} }}
            }}
            if = {{
                limit = {{
                    has_variable = zg361_b1_m360_source_status
                    var:zg361_b1_m360_source_status = 3
                }}
                root = {{ change_variable = {{ name = zg361_p2c_m360_probe_invalid_n add = 1 }} }}
            }}
            else_if = {{
                limit = {{
                    has_variable = zg361_b1_m360_source_status
                    var:zg361_b1_m360_source_status = 2
                }}
                root = {{ change_variable = {{ name = zg361_p2c_m360_probe_structural_na_n add = 1 }} }}
            }}
            else_if = {{
                limit = {{
                    has_variable = zg361_b1_m360_source_status
                    var:zg361_b1_m360_source_status = 1
                }}
                if = {{
                    limit = {{
                        zg361_p2c_m360_candidate_ready_trigger = {{
                            EXPECTED_OWNER = root
                            EXPECTED_P2C_CYCLE = root.var:zg361_p2c_cycle
                            EXPECTED_P2C_CASE = root.var:zg361_p2c_case_serial
                        }}
                    }}
                    root = {{ change_variable = {{ name = zg361_p2c_m360_probe_valid_n add = 1 }} }}
                }}
                else = {{ root = {{ change_variable = {{ name = zg361_p2c_m360_probe_invalid_n add = 1 }} }} }}
            }}
            else_if = {{
                limit = {{
                    has_variable = zg361_b1_cycle_state
                    has_variable = zg361_b1_closure_state
                    var:zg361_b1_cycle_state = 8
                    var:zg361_b1_closure_state = 4
                }}
                root = {{ change_variable = {{ name = zg361_p2c_m360_probe_invalid_n add = 1 }} }}
            }}
            else = {{ root = {{ change_variable = {{ name = zg361_p2c_m360_probe_wait_n add = 1 }} }} }}
        }}
        if = {{
            limit = {{
                var:zg361_p2c_subject = {{ NOT = {{ zg361_is_celestial_liege_trigger = yes }} }}
            }}
            zg361_p2c_freeze_m360_source_envelope_effect = yes
            set_variable = {{ name = zg361_p2c_m360_source_status value = 7 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360421 }}
        }}
        else_if = {{
            limit = {{ var:zg361_p2c_m360_probe_primary_in_frozen = 0 }}
            zg361_p2c_freeze_m360_source_envelope_effect = yes
            set_variable = {{ name = zg361_p2c_m360_source_status value = 7 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360422 }}
        }}
        else_if = {{
            limit = {{ var:zg361_p2c_m360_probe_invalid_n > 0 }}
            zg361_p2c_freeze_m360_source_envelope_effect = yes
            set_variable = {{ name = zg361_p2c_m360_source_status value = 4 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360492 }}
        }}
        else_if = {{
            limit = {{
                var:zg361_p2c_subject = {{
                    has_variable = zg361_b1_m360_source_status
                    var:zg361_b1_m360_source_status = 2
                }}
            }}
            zg361_p2c_freeze_m360_source_envelope_effect = yes
            set_variable = {{ name = zg361_p2c_m360_source_status value = 7 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360424 }}
            set_variable = {{ name = zg361_p2c_m360_source_upstream_reason value = var:zg361_p2c_subject.var:zg361_b1_m360_source_reason }}
        }}
        else_if = {{
            limit = {{ var:zg361_p2c_m360_probe_wait_n > 0 }}
            set_variable = {{ name = zg361_p2c_m360_source_status value = 5 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360410 }}
        }}
        else_if = {{
            limit = {{ var:zg361_p2c_m360_probe_valid_n < 3 }}
            zg361_p2c_freeze_m360_source_envelope_effect = yes
            set_variable = {{ name = zg361_p2c_m360_source_status value = 7 }}
            set_variable = {{ name = zg361_p2c_m360_source_reason value = 360423 }}
        }}
        else = {{
            set_variable = {{ name = zg361_p2c_m360_selection_found value = 0 }}
            ordered_in_list = {{
                variable = zg361_p2c_mg_subjects
                order_by = {{ value = var:zg361_p2c_mg_frozen_order multiply = -1 }}
                max = {{ value = var:zg361_p2c_mg_expected max = 80 }}
                if = {{
                    limit = {{
                        root.var:zg361_p2c_m360_selection_found = 0
                        NOT = {{ this = root.var:zg361_p2c_subject }}
                        zg361_p2c_m360_candidate_ready_trigger = {{
                            EXPECTED_OWNER = root
                            EXPECTED_P2C_CYCLE = root.var:zg361_p2c_cycle
                            EXPECTED_P2C_CASE = root.var:zg361_p2c_case_serial
                        }}
                    }}
                    save_temporary_scope_as = zg361_p2c_m360_candidate_2
                    root = {{
                        save_scope_value_as = {{
                            name = zg361_p2c_m360_remaining_quota
                            value = {{ value = 6 subtract = var:zg361_p2c_subject.var:zg361_b1_m360_source_quota subtract = scope:zg361_p2c_m360_candidate_2.var:zg361_b1_m360_source_quota }}
                        }}
                        ordered_in_list = {{
                            variable = zg361_p2c_mg_subjects
                            order_by = {{ value = var:zg361_p2c_mg_frozen_order multiply = -1 }}
                            max = {{ value = var:zg361_p2c_mg_expected max = 80 }}
                            if = {{
                                limit = {{
                                    root.var:zg361_p2c_m360_selection_found = 0
                                    NOT = {{ this = root.var:zg361_p2c_subject }}
                                    NOT = {{ this = scope:zg361_p2c_m360_candidate_2 }}
                                    var:zg361_b1_m360_source_quota <= scope:zg361_p2c_m360_remaining_quota
                                    zg361_p2c_m360_candidate_ready_trigger = {{
                                        EXPECTED_OWNER = root
                                        EXPECTED_P2C_CYCLE = root.var:zg361_p2c_cycle
                                        EXPECTED_P2C_CASE = root.var:zg361_p2c_case_serial
                                    }}
                                }}
                                save_temporary_scope_as = zg361_p2c_m360_candidate_3
                                root = {{
{freeze_c1.replace(chr(10), chr(10) + '                                    ')}
{freeze_c2.replace(chr(10), chr(10) + '                                    ')}
{freeze_c3.replace(chr(10), chr(10) + '                                    ')}
                                    set_variable = {{ name = zg361_p2c_m360_source_status value = 1 }}
                                    set_variable = {{ name = zg361_p2c_m360_source_reason value = 0 }}
                                    set_variable = {{ name = zg361_p2c_m360_source_owner value = this }}
                                    set_variable = {{ name = zg361_p2c_m360_source_subject value = var:zg361_p2c_subject }}
                                    set_variable = {{ name = zg361_p2c_m360_source_p2c_cycle value = var:zg361_p2c_cycle }}
                                    set_variable = {{ name = zg361_p2c_m360_source_p2c_case value = var:zg361_p2c_case_serial }}
                                    set_variable = {{ name = zg361_p2c_m360_source_al_cycle value = var:zg361_p2c_subject.var:zg361_case_al_cycle_serial }}
                                    set_variable = {{ name = zg361_p2c_m360_source_al_case value = var:zg361_p2c_subject.var:zg361_case_al_case_serial }}
                                    set_variable = {{ name = zg361_p2c_m360_source_cohort_count value = 3 }}
                                    set_variable = {{ name = zg361_p2c_m360_source_total_quota value = {{ value = var:zg361_p2c_subject.var:zg361_b1_m360_source_quota add = scope:zg361_p2c_m360_candidate_2.var:zg361_b1_m360_source_quota add = scope:zg361_p2c_m360_candidate_3.var:zg361_b1_m360_source_quota }} }}
                                    set_variable = {{ name = zg361_p2c_m360_selection_found value = 1 }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            if = {{
                limit = {{ var:zg361_p2c_m360_selection_found = 0 }}
                zg361_p2c_freeze_m360_source_envelope_effect = yes
                set_variable = {{ name = zg361_p2c_m360_source_status value = 7 }}
                set_variable = {{ name = zg361_p2c_m360_source_reason value = 360425 }}
            }}
        }}
    }}
    else = {{
        set_variable = {{ name = zg361_p2c_m360_source_status value = 4 }}
        set_variable = {{ name = zg361_p2c_m360_source_reason value = 360491 }}
        debug_log = "ZG361P2C RED: M360 preparation lost the exact AL tuple"
    }}
}}
'''


def render_effects() -> str:
    incidents = "".join(
        incident_stage(stage, domain, terminal)
        for stage, domain, terminal in ((4, "x", 8), (5, "y", 6), (6, "z", 6))
    )
    return HEADER + render_m360_source_effects() + r'''

# Zhongguo 361 phase-two central runtime: serial adapters only.
# Status: 0 unopened, 1 running, 2 success, 3 not-applicable,
# 4 typed RED, 5 external dependency.  Managers are celestial dukes+;
# counts/barons remain valid assessed subjects but can never be ROOT.

# #275-A is a standalone Central product, not a stage-11 poll.  Workforce's
# D+90 due consumer calls this scheduler while the refused original candidate
# still owns the hold.  The three delayed frames deliberately separate source
# commit, Workforce consume and Central receipt close; no frame relies on a
# same-effect write-then-read result.
zg361_p2c_schedule_m275_runner_requisition_effect = {
    if = {
        limit = {
            this = $TICKET_SUBJECT$
            $TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
            has_variable = zg361_we_m275_runner_reopen_pending
            var:zg361_we_m275_runner_reopen_pending = 1
            has_variable = zg361_we_m275_hold_pending
            var:zg361_we_m275_hold_pending = 1
        }
        if = { limit = { NOT = { has_variable = zg361_p2c_m275_ingress_ticket_serial } } set_variable = { name = zg361_p2c_m275_ingress_ticket_serial value = 0 } }
        change_variable = { name = zg361_p2c_m275_ingress_ticket_serial add = 1 }
        $TICKET_OWNER$ = { save_scope_as = zg361_p2c_m275_ingress_owner }
        save_scope_as = zg361_p2c_m275_ingress_subject
        save_scope_value_as = { name = zg361_p2c_m275_ingress_cycle value = $TICKET_CYCLE$ }
        save_scope_value_as = { name = zg361_p2c_m275_ingress_case value = $TICKET_CASE$ }
        save_scope_value_as = { name = zg361_p2c_m275_ingress_identity value = var:zg361_p2c_m275_ingress_ticket_serial }
        trigger_event = { id = zg361p2c.4 days = 1 }
    }
}

# Subject-scoped canonical producer.  The owner-local cursor never wraps or
# resets.  Exact replay schedules the same committed source without allocating
# another identity; any different live tuple is a collision and cannot
# overwrite the immutable source envelope.
zg361_p2c_open_m275_runner_requisition_effect = {
    remove_variable = zg361_p2c_m275_requisition_last_call_status
    if = {
        limit = {
            has_variable = zg361_p2c_m275_requisition_committed
            var:zg361_p2c_m275_requisition_committed = 1
            has_variable = zg361_p2c_m275_requisition_pending
            has_variable = zg361_p2c_m275_requisition_consumed
            has_variable = zg361_p2c_m275_requisition_owner
            has_variable = zg361_p2c_m275_requisition_original_subject
            has_variable = zg361_p2c_m275_requisition_source_cycle
            has_variable = zg361_p2c_m275_requisition_source_case
            has_variable = zg361_p2c_m275_requisition_source_state
            has_variable = zg361_p2c_m275_requisition_runner_up
            has_variable = zg361_p2c_m275_requisition_runner_evidence
            has_variable = zg361_p2c_m275_requisition_hc_lineage_receipt
            has_variable = zg361_p2c_m275_requisition_hc_flight_case
            has_variable = zg361_p2c_m275_requisition_serial
            has_variable = zg361_p2c_m275_requisition_new_case
            has_variable = zg361_p2c_m275_requisition_new_state
            has_variable = zg361_p2c_m275_requisition_receipt_id
            has_variable = zg361_p2c_m275_requisition_receipt_hash
            has_variable = zg361_p2c_m275_requisition_opened
            var:zg361_p2c_m275_requisition_owner = $TICKET_OWNER$
            var:zg361_p2c_m275_requisition_original_subject = $TICKET_SUBJECT$
            var:zg361_p2c_m275_requisition_source_cycle = $TICKET_CYCLE$
            var:zg361_p2c_m275_requisition_source_case = $TICKET_CASE$
            var:zg361_p2c_m275_requisition_source_state = 4
            var:zg361_p2c_m275_requisition_runner_up = var:zg361_we_m275_runner_up
            var:zg361_p2c_m275_requisition_runner_evidence = var:zg361_we_m275_runner_up_evidence
            var:zg361_p2c_m275_requisition_hc_lineage_receipt = var:zg361_we_m275_hc_lineage_receipt
            var:zg361_p2c_m275_requisition_hc_flight_case = $TICKET_CASE$
            var:zg361_p2c_m275_requisition_serial > 0
            var:zg361_p2c_m275_requisition_new_case > 0
            NOT = { var:zg361_p2c_m275_requisition_new_case = $TICKET_CASE$ }
            var:zg361_p2c_m275_requisition_new_state = 1
            var:zg361_p2c_m275_requisition_receipt_id > 0
            var:zg361_p2c_m275_requisition_receipt_hash > 0
            var:zg361_p2c_m275_requisition_opened = 1
            OR = {
                AND = { var:zg361_p2c_m275_requisition_pending = 1 var:zg361_p2c_m275_requisition_consumed = 0 }
                AND = { var:zg361_p2c_m275_requisition_pending = 0 var:zg361_p2c_m275_requisition_consumed = 1 }
            }
        }
        if = {
            limit = { var:zg361_p2c_m275_requisition_pending = 1 var:zg361_p2c_m275_requisition_consumed = 0 }
            set_variable = { name = zg361_p2c_m275_requisition_last_call_status value = 1 }
            save_scope_as = zg361_p2c_m275_dispatch_subject
            $TICKET_OWNER$ = { save_scope_as = zg361_p2c_m275_dispatch_owner }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_cycle value = $TICKET_CYCLE$ }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_case value = $TICKET_CASE$ }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_serial value = var:zg361_p2c_m275_requisition_serial }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_new_case value = var:zg361_p2c_m275_requisition_new_case }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_receipt value = var:zg361_p2c_m275_requisition_receipt_id }
            trigger_event = { id = zg361p2c.5 days = 1 }
        }
        else = { set_variable = { name = zg361_p2c_m275_requisition_last_call_status value = 2 } }
    }
    else_if = {
        limit = {
            this = $TICKET_SUBJECT$
            trigger_if = { limit = { has_variable = zg361_p2c_m275_requisition_committed } var:zg361_p2c_m275_requisition_committed = 0 }
            trigger_else = { always = yes }
            $TICKET_OWNER$ = {
                zg361_is_celestial_liege_trigger = yes
                has_variable = zg361_review_serial
                var:zg361_review_serial >= root.var:zg361_we_m275_hold_due_cycle
                has_variable = zg361_we_ad_hc_flight_pending
                var:zg361_we_ad_hc_flight_pending = 1
                var:zg361_we_ad_hc_flight_subject = $TICKET_SUBJECT$
                var:zg361_we_ad_hc_flight_cycle = $TICKET_CYCLE$
                var:zg361_we_ad_hc_flight_case = $TICKET_CASE$
            }
            has_variable = zg361_we_m275_business_object_created
            has_variable = zg361_we_m275_object_owner
            has_variable = zg361_we_m275_object_subject
            has_variable = zg361_we_m275_object_cycle
            has_variable = zg361_we_m275_object_case
            has_variable = zg361_we_m275_object_state
            has_variable = zg361_we_m275_object_consumed
            has_variable = zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275
            var:zg361_we_m275_business_object_created = 1
            var:zg361_we_m275_object_owner = $TICKET_OWNER$
            var:zg361_we_m275_object_subject = $TICKET_SUBJECT$
            var:zg361_we_m275_object_cycle = $TICKET_CYCLE$
            var:zg361_we_m275_object_case = $TICKET_CASE$
            var:zg361_we_m275_object_state = 4
            var:zg361_we_m275_object_consumed = 1
            var:zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275 = 1
            has_variable = zg361_we_m275_receipt_choice
            has_variable = zg361_we_m275_refusal
            has_variable = zg361_we_m275_not_applicable_hired
            has_variable = zg361_we_m275_original_candidate
            has_variable = zg361_we_m275_hold_pending
            has_variable = zg361_we_m275_runner_reopen_pending
            has_variable = zg361_we_m275_runner_up
            has_variable = zg361_we_m275_runner_up_evidence
            has_variable = zg361_we_m275_hc_lineage_receipt
            has_variable = zg361_we_m266_hc_reservation_active
            has_variable = zg361_we_m266_hc_receipt
            has_variable = zg361_we_candidate_active
            var:zg361_we_m275_receipt_choice = 1
            var:zg361_we_m275_refusal = 1
            var:zg361_we_m275_not_applicable_hired = 0
            var:zg361_we_m275_original_candidate = $TICKET_SUBJECT$
            var:zg361_we_m275_hold_pending = 1
            var:zg361_we_m275_runner_reopen_pending = 1
            NOT = { var:zg361_we_m275_runner_up = $TICKET_SUBJECT$ }
            var:zg361_we_m275_runner_up_evidence > 0
            var:zg361_we_m275_hc_lineage_receipt = $TICKET_CASE$
            var:zg361_we_m266_hc_reservation_active = 1
            var:zg361_we_m266_hc_receipt = $TICKET_CASE$
            var:zg361_we_candidate_active = 0
            has_variable = zg361_ch_hc_reserved
            var:zg361_ch_hc_reserved >= 1
        }
        $TICKET_OWNER$ = {
            save_temporary_scope_as = zg361_p2c_m275_requisition_cursor_owner
            if = { limit = { NOT = { has_variable = zg361_p2c_m275_requisition_cursor } } set_variable = { name = zg361_p2c_m275_requisition_cursor value = 0 } }
            change_variable = { name = zg361_p2c_m275_requisition_cursor add = 1 }
        }
        save_temporary_scope_value_as = {
            name = zg361_p2c_m275_expected_new_case
            value = { value = $TICKET_CASE$ multiply = 100000 add = { value = scope:zg361_p2c_m275_requisition_cursor_owner.var:zg361_p2c_m275_requisition_cursor multiply = 10 } add = 5 }
        }
        save_temporary_scope_value_as = { name = zg361_p2c_m275_expected_receipt_id value = { value = scope:zg361_p2c_m275_expected_new_case multiply = 10 add = 5 } }
        save_temporary_scope_value_as = {
            name = zg361_p2c_m275_expected_receipt_hash
            value = {
                value = scope:zg361_p2c_m275_requisition_cursor_owner.var:zg361_p2c_m275_requisition_cursor multiply = 100000000
                add = { value = $TICKET_CYCLE$ multiply = 1000000 }
                add = { value = $TICKET_CASE$ multiply = 1000 }
                add = { value = var:zg361_we_m275_runner_up_evidence multiply = 10 }
                add = 275
            }
        }
        if = {
            limit = {
                scope:zg361_p2c_m275_expected_new_case > 0
                NOT = { scope:zg361_p2c_m275_expected_new_case = $TICKET_CASE$ }
                scope:zg361_p2c_m275_expected_receipt_id > 0
                scope:zg361_p2c_m275_expected_receipt_hash > 0
            }
            set_variable = { name = zg361_p2c_m275_requisition_pending value = 1 }
            set_variable = { name = zg361_p2c_m275_requisition_consumed value = 0 }
            set_variable = { name = zg361_p2c_m275_requisition_status value = 1 }
            set_variable = { name = zg361_p2c_m275_requisition_owner value = $TICKET_OWNER$ }
            set_variable = { name = zg361_p2c_m275_requisition_original_subject value = $TICKET_SUBJECT$ }
            set_variable = { name = zg361_p2c_m275_requisition_source_cycle value = $TICKET_CYCLE$ }
            set_variable = { name = zg361_p2c_m275_requisition_source_case value = $TICKET_CASE$ }
            set_variable = { name = zg361_p2c_m275_requisition_source_state value = 4 }
            set_variable = { name = zg361_p2c_m275_requisition_runner_up value = var:zg361_we_m275_runner_up }
            set_variable = { name = zg361_p2c_m275_requisition_runner_evidence value = var:zg361_we_m275_runner_up_evidence }
            set_variable = { name = zg361_p2c_m275_requisition_hc_lineage_receipt value = var:zg361_we_m275_hc_lineage_receipt }
            set_variable = { name = zg361_p2c_m275_requisition_hc_flight_case value = $TICKET_CASE$ }
            set_variable = { name = zg361_p2c_m275_requisition_serial value = scope:zg361_p2c_m275_requisition_cursor_owner.var:zg361_p2c_m275_requisition_cursor }
            set_variable = { name = zg361_p2c_m275_requisition_new_case value = scope:zg361_p2c_m275_expected_new_case }
            set_variable = { name = zg361_p2c_m275_requisition_new_state value = 1 }
            set_variable = { name = zg361_p2c_m275_requisition_receipt_id value = scope:zg361_p2c_m275_expected_receipt_id }
            set_variable = { name = zg361_p2c_m275_requisition_receipt_hash value = scope:zg361_p2c_m275_expected_receipt_hash }
            set_variable = { name = zg361_p2c_m275_requisition_opened value = 1 }
            set_variable = { name = zg361_p2c_m275_requisition_last_call_status value = 1 }
            set_variable = { name = zg361_p2c_m275_requisition_committed value = 1 } # source commit last
            save_scope_as = zg361_p2c_m275_dispatch_subject
            $TICKET_OWNER$ = { save_scope_as = zg361_p2c_m275_dispatch_owner }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_cycle value = $TICKET_CYCLE$ }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_case value = $TICKET_CASE$ }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_serial value = var:zg361_p2c_m275_requisition_serial }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_new_case value = var:zg361_p2c_m275_requisition_new_case }
            save_scope_value_as = { name = zg361_p2c_m275_dispatch_receipt value = var:zg361_p2c_m275_requisition_receipt_id }
            trigger_event = { id = zg361p2c.5 days = 1 }
        }
        else = {
            set_variable = { name = zg361_p2c_m275_requisition_last_call_status value = 4 }
            set_variable = { name = zg361_p2c_m275_requisition_collision_code value = 27542 }
        }
    }
    else = {
        set_variable = { name = zg361_p2c_m275_requisition_last_call_status value = 4 }
        set_variable = { name = zg361_p2c_m275_requisition_collision_code value = 27541 }
    }
}

zg361_p2c_mark_lane_busy_effect = {
    set_variable = { name = zg361_p2c_stage_status value = 1 }
    if = { limit = { is_ai = no } set_variable = { name = zg361_p2c_ui_lane_busy value = 1 } }
    else = { set_variable = { name = zg361_p2c_ui_lane_busy value = 0 } }
}

# Every delayed poll carries manager + central case + cycle + stage + ticket.
# Scheduling a newer ticket makes every older delayed copy a strict no-op.
zg361_p2c_schedule_pump_effect = {
    if = {
        limit = { var:zg361_p2c_active = 1 }
        if = { limit = { NOT = { has_variable = zg361_p2c_ticket_serial } } set_variable = { name = zg361_p2c_ticket_serial value = 0 } }
        change_variable = { name = zg361_p2c_ticket_serial add = 1 }
        save_scope_as = zg361_p2c_ticket_manager
        save_scope_value_as = { name = zg361_p2c_ticket_cycle value = var:zg361_p2c_cycle }
        save_scope_value_as = { name = zg361_p2c_ticket_case value = var:zg361_p2c_case_serial }
        save_scope_value_as = { name = zg361_p2c_ticket_stage value = var:zg361_p2c_stage }
        save_scope_value_as = { name = zg361_p2c_ticket_identity value = var:zg361_p2c_ticket_serial }
        trigger_event = { id = zg361p2c.1 days = $DAYS$ }
    }
}

zg361_p2c_queue_summary_effect = {
    if = {
        limit = { is_ai = no NOT = { has_variable = zg361_p2c_summary_pending } }
        set_variable = { name = zg361_p2c_summary_pending value = 1 }
        save_scope_value_as = { name = zg361_p2c_summary_cycle value = var:zg361_p2c_cycle }
        save_scope_value_as = { name = zg361_p2c_summary_case value = var:zg361_p2c_case_serial }
        trigger_event = { id = zg361p2c.2 days = 1 }
    }
    else_if = { limit = { is_ai = yes } debug_log = "ZG361P2C: eligible AI central portfolio completed silently" }
}

zg361_p2c_record_stage_effect = {
    set_variable = { name = $STAGE_VAR$ value = $STATUS$ }
    set_variable = { name = zg361_p2c_stage_status value = $STATUS$ }
    if = { limit = { var:zg361_p2c_stage_status = 2 } change_variable = { name = zg361_p2c_success_n add = 1 } }
    else_if = { limit = { var:zg361_p2c_stage_status = 3 } change_variable = { name = zg361_p2c_na_n add = 1 } }
    else_if = { limit = { var:zg361_p2c_stage_status = 4 } change_variable = { name = zg361_p2c_red_n add = 1 } }
    change_variable = { name = zg361_p2c_stage add = 1 }
    set_variable = { name = zg361_p2c_stage_status value = 0 }
    set_variable = { name = zg361_p2c_wait_reason value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    zg361_p2c_schedule_pump_effect = { DAYS = 2 }
}

zg361_p2c_record_red_effect = {
    set_variable = { name = zg361_p2c_last_red_code value = $CODE$ }
    zg361_p2c_record_stage_effect = { STATUS = 4 STAGE_VAR = $STAGE_VAR$ }
}

zg361_p2c_mark_external_wait_effect = {
    if = {
        limit = { NOT = { var:zg361_p2c_wait_reason = $REASON$ } }
        change_variable = { name = zg361_p2c_external_n add = 1 }
    }
    set_variable = { name = $STAGE_VAR$ value = 5 }
    set_variable = { name = zg361_p2c_stage_status value = 5 }
    set_variable = { name = zg361_p2c_wait_reason value = $REASON$ }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    zg361_p2c_schedule_pump_effect = { DAYS = 2 }
}

# A frozen primary subject dying, changing direct manager, or changing its
# owner/cycle/case tuple aborts the central case.  It never silently substitutes
# another official and never writes into a new B1 season.
zg361_p2c_abort_stale_effect = {
    set_variable = { name = zg361_p2c_last_red_code value = $CODE$ }
    set_variable = { name = zg361_p2c_stage_status value = 4 }
    change_variable = { name = zg361_p2c_red_n add = 1 }
    set_variable = { name = zg361_p2c_active value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    set_variable = { name = zg361_p2c_terminal_state value = 4 }
    set_variable = { name = zg361_p2c_completed_cycle value = var:zg361_p2c_cycle }
    zg361_p2c_queue_summary_effect = yes
    debug_log = "ZG361P2C: frozen central tuple became stale; typed RED"
}

zg361_p2c_finish_effect = {
    set_variable = { name = zg361_p2c_active value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    set_variable = { name = zg361_p2c_terminal_state value = 2 }
    if = { limit = { var:zg361_p2c_red_n > 0 } set_variable = { name = zg361_p2c_terminal_state value = 4 } }
    set_variable = { name = zg361_p2c_completed_cycle value = var:zg361_p2c_cycle }
    zg361_p2c_queue_summary_effect = yes
    debug_log = "ZG361P2C: serial phase-two portfolio reached a terminal summary"
}

# A package-level dependency may make further progress impossible without a
# public domain seam.  Suspend honestly: no central completed-cycle marker and
# no repeated poll, but one summary records terminal_state=external.
zg361_p2c_suspend_external_effect = {
    if = { limit = { NOT = { var:zg361_p2c_wait_reason = $REASON$ } } change_variable = { name = zg361_p2c_external_n add = 1 } }
    set_variable = { name = $STAGE_VAR$ value = 5 }
    set_variable = { name = zg361_p2c_stage_status value = 5 }
    set_variable = { name = zg361_p2c_wait_reason value = $REASON$ }
    set_variable = { name = zg361_p2c_active value = 0 }
    set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
    set_variable = { name = zg361_p2c_terminal_state value = 5 }
    set_variable = { name = zg361_p2c_suspended_cycle value = var:zg361_p2c_cycle }
    zg361_p2c_queue_summary_effect = yes
    debug_log = "ZG361P2C: central portfolio suspended on an external domain dependency"
}

# Hook 1: called only after B1 is published and review_in_progress is cleared.
# It freezes one deterministic current-result subject and merely queues D+2;
# no domain adapter is opened inside the publication stack.
zg361_p2c_on_review_published_effect = {
    # A newer B1 publication may arrive while an older central portfolio is
    # still active.  Terminate the old immutable tuple first; never overwrite
    # its case/stage/ticket in place.
    if = {
        limit = {
            has_variable = zg361_p2c_active
            var:zg361_p2c_active = 1
            has_variable = zg361_p2c_cycle
            has_variable = zg361_review_serial
            NOT = { var:zg361_p2c_cycle = var:zg361_review_serial }
        }
        set_variable = { name = zg361_p2c_previous_aborted_cycle value = var:zg361_p2c_cycle }
        set_variable = { name = zg361_p2c_deferred_reinit_cycle value = var:zg361_review_serial }
        set_variable = { name = zg361_p2c_deferred_reinit_b1_case value = var:zg361_b1_case_serial }
        set_variable = { name = zg361_p2c_deferred_reinit value = 1 }
        zg361_p2c_abort_stale_effect = { CODE = 9101 }
        trigger_event = { id = zg361p2c.3 days = 2 }
    }
    if = {
        limit = {
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
            has_variable = zg361_b1_cycle_serial
            has_variable = zg361_b1_case_serial
            has_variable = zg361_b1_cycle_state
            has_variable = zg361_b1_closure_state
            var:zg361_b1_cycle_serial = var:zg361_review_serial
            var:zg361_b1_cycle_state = 8
            var:zg361_b1_closure_state = 4
            # Publication closure has exactly one proof route selected by the
            # explicit M013 mode.  A stale/current receipt can never satisfy
            # route C, and policy debt can never substitute for route A/B.
            OR = {
                AND = {
                    has_variable = zg361_b1_m013_mode
                    var:zg361_b1_m013_mode != 3
                    has_variable = zg361_b1_m013_receipt_serial
                    var:zg361_b1_m013_receipt_serial = var:zg361_b1_case_serial
                }
                AND = {
                    has_variable = zg361_b1_m013_mode
                    var:zg361_b1_m013_mode = 3
                    has_variable = zg361_b1_m013_policy_debt_serial
                    var:zg361_b1_m013_policy_debt_serial = var:zg361_b1_case_serial
                }
            }
            NOT = { has_character_flag = zg361_review_in_progress }
            NOT = { has_variable = zg361_p2c_deferred_reinit }
            trigger_if = {
                limit = { has_variable = zg361_p2c_active }
                var:zg361_p2c_active = 0
            }
            trigger_else = { always = yes }
            trigger_if = {
                limit = { has_variable = zg361_p2c_started_cycle }
                NOT = { var:zg361_p2c_started_cycle = var:zg361_review_serial }
            }
            trigger_else = { always = yes }
            trigger_if = {
                limit = { has_variable = zg361_p2c_completed_cycle }
                NOT = { var:zg361_p2c_completed_cycle = var:zg361_review_serial }
            }
            trigger_else = { always = yes }
            any_vassal = {
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                has_variable = zg361_b1_case_owner
                has_variable = zg361_b1_case_subject
                has_variable = zg361_b1_cycle_serial
                has_variable = zg361_b1_case_serial
                has_variable = zg361_b1_case_state
                var:zg361_b1_case_owner = root
                var:zg361_b1_case_subject = this
                var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
                var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
                var:zg361_b1_case_state = 8
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_grade
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
            }
        }
        if = { limit = { NOT = { has_variable = zg361_p2c_case_cursor } } set_variable = { name = zg361_p2c_case_cursor value = 0 } }
        if = { limit = { var:zg361_p2c_case_cursor >= 999999 } set_variable = { name = zg361_p2c_case_cursor value = 0 } }
        change_variable = { name = zg361_p2c_case_cursor add = 1 }
        ordered_vassal = {
            limit = {
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                var:zg361_b1_case_owner = root
                var:zg361_b1_case_subject = this
                var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial
                var:zg361_b1_case_serial = root.var:zg361_b1_case_serial
                var:zg361_b1_case_state = 8
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_grade
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
            }
            order_by = stewardship
            position = 0
            save_temporary_scope_as = zg361_p2c_selected_subject
            root = {
                set_variable = { name = zg361_p2c_started_cycle value = var:zg361_review_serial }
                set_variable = { name = zg361_p2c_active value = 1 }
                set_variable = { name = zg361_p2c_case_serial value = var:zg361_p2c_case_cursor }
                set_variable = { name = zg361_p2c_b1_owner value = this }
                set_variable = { name = zg361_p2c_b1_cycle value = var:zg361_b1_cycle_serial }
                set_variable = { name = zg361_p2c_b1_case value = var:zg361_b1_case_serial }
                set_variable = { name = zg361_p2c_cycle value = var:zg361_review_serial }
                set_variable = { name = zg361_p2c_subject value = scope:zg361_p2c_selected_subject }
                set_variable = { name = zg361_p2c_result_owner value = this }
                set_variable = { name = zg361_p2c_result_subject value = scope:zg361_p2c_selected_subject }
                set_variable = { name = zg361_p2c_result_cycle value = scope:zg361_p2c_selected_subject.var:zg361_result_cycle_serial }
                set_variable = { name = zg361_p2c_result_case value = scope:zg361_p2c_selected_subject.var:zg361_result_case_serial }
                set_variable = { name = zg361_p2c_result_state_at_publish value = scope:zg361_p2c_selected_subject.var:zg361_result_case_state }
                set_variable = { name = zg361_p2c_result_grade_at_publish value = scope:zg361_p2c_selected_subject.var:zg361_result_grade }
                set_variable = { name = zg361_p2c_stage value = 1 }
                set_variable = { name = zg361_p2c_stage_status value = 0 }
                set_variable = { name = zg361_p2c_wait_reason value = 0 }
                set_variable = { name = zg361_p2c_ticket_serial value = 0 }
                set_variable = { name = zg361_p2c_ui_lane_busy value = 0 }
                set_variable = { name = zg361_p2c_success_n value = 0 }
                set_variable = { name = zg361_p2c_na_n value = 0 }
                set_variable = { name = zg361_p2c_red_n value = 0 }
                set_variable = { name = zg361_p2c_external_n value = 0 }
                remove_variable = zg361_p2c_last_red_code
                remove_variable = zg361_p2c_summary_pending
                zg361_p2c_clear_m360_source_effect = yes
                if = { limit = { has_variable_list = zg361_p2c_mg_subjects } clear_variable_list = zg361_p2c_mg_subjects }
                set_variable = { name = zg361_p2c_mg_expected value = 0 }
                set_variable = { name = zg361_p2c_mg_completed value = 0 }
                set_variable = { name = zg361_p2c_mg_invalid value = 0 }
                set_variable = { name = zg361_p2c_last_noop_code value = 0 }
                zg361_p2c_schedule_pump_effect = { DAYS = 2 }
            }
        }
        debug_log = "ZG361P2C: post-publication central tuple frozen; first pump D+2"
    }
    else_if = {
        limit = {
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_review_serial
            OR = {
                AND = { has_variable = zg361_p2c_started_cycle var:zg361_p2c_started_cycle = var:zg361_review_serial }
                AND = { has_variable = zg361_p2c_completed_cycle var:zg361_p2c_completed_cycle = var:zg361_review_serial }
            }
        }
        set_variable = { name = zg361_p2c_last_noop_code value = 1 }
        debug_log = "ZG361P2C: duplicate publication hook ignored"
    }
    else = { debug_log = "ZG361P2C: unauthorized or incomplete publication hook ignored" }
}

# Hook 2: called in subject scope only after the 3.25 settlement receipt and B2
# delivery hook.  It can only invalidate/reschedule the exact waiting central
# ticket; it cannot initialize a case or change the frozen subject.
zg361_p2c_on_result_delivered_effect = {
    if = {
        limit = {
            has_variable = zg361_result_case_owner
            has_variable = zg361_result_cycle_serial
            has_variable = zg361_result_case_serial
            has_variable = zg361_result_case_state
            var:zg361_result_case_state = 3
        }
        save_temporary_scope_as = zg361_p2c_delivered_subject
        var:zg361_result_case_owner = {
            if = {
                limit = {
                    zg361_is_celestial_liege_trigger = yes
                    has_variable = zg361_p2c_active
                    var:zg361_p2c_active = 1
                    has_variable = zg361_p2c_subject
                    has_variable = zg361_p2c_cycle
                    has_variable = zg361_p2c_result_case
                    var:zg361_p2c_subject = scope:zg361_p2c_delivered_subject
                    var:zg361_p2c_cycle = scope:zg361_p2c_delivered_subject.var:zg361_result_cycle_serial
                    var:zg361_p2c_result_case = scope:zg361_p2c_delivered_subject.var:zg361_result_case_serial
                    OR = { var:zg361_p2c_stage = 2 var:zg361_p2c_stage = 7 }
                    var:zg361_p2c_wait_reason = 325
                }
                set_variable = { name = zg361_p2c_stage_status value = 0 }
                set_variable = { name = zg361_p2c_wait_reason value = 0 }
                zg361_p2c_schedule_pump_effect = { DAYS = 1 }
                debug_log = "ZG361P2C: exact delivered 3.25 woke its waiting central case"
            }
        }
    }
}

# The next three domain ABIs are manager-scoped and select their own first
# eligible subject.  Preflight the exact deterministic selection before the
# call, so eligibility drift can produce a central RED without ever opening an
# orphan case on somebody other than the frozen primary.
zg361_p2c_call_career_hc_adapter_effect = {
    set_variable = { name = zg361_p2c_adapter_called value = 0 }
    remove_variable = zg361_p2c_adapter_candidate
    ordered_vassal = {
        limit = {
            zg361_is_reviewable_vassal_trigger = yes
            liege = root
            trigger_if = { limit = { has_variable = zg361_ch_portfolio_cycle } NOT = { var:zg361_ch_portfolio_cycle = root.var:zg361_review_serial } }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_d_active } var:zg361_case_d_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_m_active } var:zg361_case_m_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_n_active } var:zg361_case_n_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_o_active } var:zg361_case_o_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_p_active } var:zg361_case_p_active = 0 }
            trigger_else = { always = yes }
            trigger_if = { limit = { has_variable = zg361_case_q_active } var:zg361_case_q_active = 0 }
            trigger_else = { always = yes }
        }
        order_by = stewardship
        position = 0
        save_temporary_scope_as = zg361_p2c_preflight_candidate
        root = { set_variable = { name = zg361_p2c_adapter_candidate value = scope:zg361_p2c_preflight_candidate } }
    }
    if = {
        limit = { has_variable = zg361_p2c_adapter_candidate var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject }
        zg361_career_hc_open_portfolio_effect = yes
        set_variable = { name = zg361_p2c_adapter_called value = 1 }
    }
}

zg361_p2c_call_compensation_adapter_effect = {
    set_variable = { name = zg361_p2c_adapter_called value = 0 }
    if = {
        limit = {
            has_variable = zg361_comp_portfolio_subject
            var:zg361_comp_portfolio_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_owner = root
            var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
        }
        zg361_comp_portfolio_open_next_effect = yes
        set_variable = { name = zg361_p2c_adapter_called value = 1 }
    }
    else_if = {
        limit = {
            OR = {
                NOT = { has_variable = zg361_comp_portfolio_domain }
                var:zg361_comp_portfolio_domain = 1
            }
            NOT = { has_variable = zg361_comp_portfolio_subject }
        }
        remove_variable = zg361_p2c_adapter_candidate
        ordered_vassal = {
            limit = {
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_grade
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_review_serial
                var:zg361_result_case_state >= 3
                OR = { var:zg361_result_grade = 1 var:zg361_result_grade = 2 var:zg361_result_grade = 3 }
            }
            order_by = stewardship
            position = 0
            save_temporary_scope_as = zg361_p2c_preflight_candidate
            root = { set_variable = { name = zg361_p2c_adapter_candidate value = scope:zg361_p2c_preflight_candidate } }
        }
        if = {
            limit = { has_variable = zg361_p2c_adapter_candidate var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject }
            zg361_comp_portfolio_open_next_effect = yes
            set_variable = { name = zg361_p2c_adapter_called value = 1 }
        }
    }
}

zg361_p2c_call_pp_adapter_effect = {
    set_variable = { name = zg361_p2c_adapter_called value = 0 }
    remove_variable = zg361_p2c_adapter_candidate
    ordered_vassal = {
        limit = { zg361_is_reviewable_vassal_trigger = yes liege = root }
        order_by = stewardship
        position = 0
        save_temporary_scope_as = zg361_p2c_preflight_candidate
        root = { set_variable = { name = zg361_p2c_adapter_candidate value = scope:zg361_p2c_preflight_candidate } }
    }
    if = {
        limit = { has_variable = zg361_p2c_adapter_candidate var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject }
        zg361_pp_manager_portfolio_adapter_effect = yes
        set_variable = { name = zg361_p2c_adapter_called value = 1 }
    }
}

# Stage 1: Career/HC owns the same deterministic primary subject later consumed
# by Workforce.  Completion requires both manager and subject terminal markers.
zg361_p2c_stage_01_career_hc_effect = {
    if = {
        limit = {
            var:zg361_ch_manager_portfolio_completed_cycle = var:zg361_p2c_cycle
            var:zg361_p2c_subject = {
                var:zg361_ch_portfolio_closed = 1
                var:zg361_ch_portfolio_owner = root
                var:zg361_ch_portfolio_subject = this
                var:zg361_ch_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_01_status }
    }
    else_if = {
        limit = {
            has_variable = zg361_ch_manager_portfolio_active
            var:zg361_ch_manager_portfolio_active = 1
            var:zg361_p2c_subject = {
                var:zg361_ch_portfolio_owner = root
                var:zg361_ch_portfolio_subject = this
                var:zg361_ch_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        zg361_p2c_call_career_hc_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_adapter_called = 1
                var:zg361_ch_portfolio_applied = 1
                var:zg361_ch_manager_portfolio_active = 1
                var:zg361_p2c_subject = {
                    var:zg361_ch_portfolio_owner = root
                    var:zg361_ch_portfolio_subject = this
                    var:zg361_ch_portfolio_cycle = root.var:zg361_p2c_cycle
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 101 STAGE_VAR = zg361_p2c_stage_01_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 151 STAGE_VAR = zg361_p2c_stage_01_status } }
}

# Stage 2: compensation consumes the exact delivered result.  Its public
# open-next adapter is intentionally called again after each domain ACK.
zg361_p2c_stage_02_compensation_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                OR = { var:zg361_result_case_state = 1 var:zg361_result_case_state = 2 }
            }
        }
        zg361_p2c_mark_external_wait_effect = { REASON = 325 STAGE_VAR = zg361_p2c_stage_02_status }
    }
    else_if = {
        limit = {
            var:zg361_comp_portfolio_completed_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_owner = root
            var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
            var:zg361_comp_portfolio_result_state >= 3
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_02_status }
    }
    else_if = {
        limit = {
            has_character_flag = zg361_comp_portfolio_active
            var:zg361_comp_portfolio_result_owner = root
            var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
            var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
            var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                var:zg361_result_case_state >= 3
            }
        }
        zg361_p2c_call_compensation_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_adapter_called = 1
                OR = {
                    has_character_flag = zg361_comp_portfolio_active
                    AND = { has_variable = zg361_comp_portfolio_completed_cycle var:zg361_comp_portfolio_completed_cycle = var:zg361_p2c_cycle }
                }
                var:zg361_comp_portfolio_result_owner = root
                var:zg361_comp_portfolio_result_subject = var:zg361_p2c_subject
                var:zg361_comp_portfolio_result_cycle = var:zg361_p2c_cycle
                var:zg361_comp_portfolio_result_case = var:zg361_p2c_result_case
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 202 STAGE_VAR = zg361_p2c_stage_02_status } }
    }
    else = { zg361_p2c_abort_stale_effect = { CODE = 252 } }
}

# Stage 3: T -> U -> V -> W -> complete.  Each central pump can call the
# public adapter only once, and it waits while the package owns its queue lock.
zg361_p2c_stage_03_feedback_promotion_pip_effect = {
    if = {
        limit = {
            var:zg361_pp_portfolio_complete_cycle = var:zg361_p2c_cycle
            var:zg361_p2c_subject = {
                var:zg361_pp_t_portfolio_done_cycle = root.var:zg361_p2c_cycle
                var:zg361_pp_u_portfolio_done_cycle = root.var:zg361_p2c_cycle
                var:zg361_pp_v_portfolio_done_cycle = root.var:zg361_p2c_cycle
                var:zg361_pp_w_portfolio_done_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_03_status }
    }
    else_if = {
        limit = { has_variable = zg361_pp_portfolio_queue_active var:zg361_pp_portfolio_queue_active = 1 }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else = {
        zg361_p2c_call_pp_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_adapter_called = 1
                OR = {
                    AND = { has_variable = zg361_pp_portfolio_complete_cycle var:zg361_pp_portfolio_complete_cycle = var:zg361_p2c_cycle }
                    AND = { has_variable = zg361_pp_portfolio_queue_active var:zg361_pp_portfolio_queue_active = 1 }
                }
                var:zg361_p2c_subject = {
                    OR = {
                        AND = { has_variable = zg361_pp_t_portfolio_done_cycle var:zg361_pp_t_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_t_active var:zg361_case_t_active = 1 var:zg361_case_t_owner = root var:zg361_case_t_cycle_serial = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_pp_u_portfolio_done_cycle var:zg361_pp_u_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_u_active var:zg361_case_u_active = 1 var:zg361_case_u_owner = root var:zg361_case_u_cycle_serial = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_pp_v_portfolio_done_cycle var:zg361_pp_v_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_v_active var:zg361_case_v_active = 1 var:zg361_case_v_owner = root var:zg361_case_v_cycle_serial = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_pp_w_portfolio_done_cycle var:zg361_pp_w_portfolio_done_cycle = root.var:zg361_p2c_cycle }
                        AND = { has_variable = zg361_case_w_active var:zg361_case_w_active = 1 var:zg361_case_w_owner = root var:zg361_case_w_cycle_serial = root.var:zg361_p2c_cycle }
                    }
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 303 STAGE_VAR = zg361_p2c_stage_03_status } }
    }
}
''' + incidents + r'''
# Stage 7: P3 is gated by the same exact delivered result as compensation.
zg361_p2c_stage_07_metrics_delivery_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                OR = { var:zg361_result_case_state = 1 var:zg361_result_case_state = 2 }
            }
        }
        zg361_p2c_mark_external_wait_effect = { REASON = 325 STAGE_VAR = zg361_p2c_stage_07_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_p3_portfolio_closed = 1
                var:zg361_p3_portfolio_owner = root
                var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_owner = root
                var:zg361_p3_portfolio_result_subject = this
                var:zg361_p3_portfolio_result_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case
                var:zg361_p3_final_owner = root
                var:zg361_p3_final_subject = this
                var:zg361_p3_final_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_final_conservation_ok = 1
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_07_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_p3_portfolio_owner = root
                var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                OR = { var:zg361_case_aa_active = 1 var:zg361_case_ag_active = 1 var:zg361_case_aj_active = 1 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        # AA -> AG -> AJ use D+1 edges.  During the bounded edge gap no case is
        # active, but the frozen portfolio tuple is still authoritative.
        limit = {
            var:zg361_p2c_stage_status = 1
            var:zg361_p2c_subject = {
                var:zg361_p3_portfolio_closed = 0
                var:zg361_p3_portfolio_owner = root
                var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_owner = root
                var:zg361_p3_portfolio_result_subject = this
                var:zg361_p3_portfolio_result_cycle = root.var:zg361_p2c_cycle
                var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = {
            var:zg361_p2c_stage_status != 1
            var:zg361_p2c_subject = {
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
                var:zg361_result_case_state >= 3
            }
        }
        zg361_p3_open_portfolio_effect = { SUBJECT = var:zg361_p2c_subject }
        if = {
            limit = {
                var:zg361_p2c_subject = {
                    var:zg361_p3_portfolio_owner = root
                    var:zg361_p3_portfolio_cycle = root.var:zg361_p2c_cycle
                    var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case
                    var:zg361_case_aa_active = 1
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 707 STAGE_VAR = zg361_p2c_stage_07_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 757 STAGE_VAR = zg361_p2c_stage_07_status } }
}

# Stage 8: a distinct cross reviewer is mandatory.  A one-subject realm whose
# manager has no eligible celestial superior is honestly N/A, never bypassed.
zg361_p2c_stage_08_credit_project_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_cp_portfolio_closed = 1
                var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_cp_final_owner = root
                var:zg361_cp_final_subject = this
                var:zg361_cp_final_cycle = root.var:zg361_p2c_cycle
                var:zg361_cp_final_conservation_ok = 1
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_08_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_stage_status = 0
            NOR = {
                any_vassal = { zg361_is_reviewable_vassal_trigger = yes NOT = { this = root.var:zg361_p2c_subject } }
                liege = { zg361_is_celestial_liege_trigger = yes }
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_08_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
                OR = { var:zg361_case_e_active = 1 var:zg361_case_i_active = 1 var:zg361_case_j_active = 1 var:zg361_case_r_active = 1 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        # E -> I -> J -> R also crosses D+1 edges.  Keep polling the exact
        # frozen subject portfolio instead of converting a healthy gap to RED.
        limit = {
            var:zg361_p2c_stage_status = 1
            var:zg361_p2c_subject = {
                var:zg361_cp_portfolio_closed = 0
                var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        zg361_cp_open_portfolio_effect = { SUBJECT = var:zg361_p2c_subject }
        if = {
            limit = {
                var:zg361_p2c_subject = {
                    var:zg361_cp_portfolio_cycle = root.var:zg361_p2c_cycle
                    var:zg361_case_e_owner = root
                    var:zg361_case_e_subject = this
                    var:zg361_case_e_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_e_active = 1
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 808 STAGE_VAR = zg361_p2c_stage_08_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 858 STAGE_VAR = zg361_p2c_stage_08_status } }
}

# Stage 9: dispatches all current direct reports once, then waits for exact
# expected/completed counters.  A player digest must be ACKed before advancing.
zg361_p2c_stage_09_career_learning_effect = {
    if = {
        limit = {
            has_variable = zg361_p2c_cl_partial_open
            var:zg361_p2c_cl_partial_open = 1
            var:zg361_cl_portfolio_cycle = var:zg361_p2c_cycle
            var:zg361_cl_portfolio_ah_completed >= var:zg361_cl_portfolio_ah_expected
            var:zg361_cl_portfolio_ai_completed >= var:zg361_cl_portfolio_ai_expected
            trigger_if = { limit = { is_ai = no } NOT = { has_variable = zg361_cl_digest_pending } }
            trigger_else = { always = yes }
        }
        zg361_p2c_record_red_effect = { CODE = 910 STAGE_VAR = zg361_p2c_stage_09_status }
    }
    else_if = {
        limit = {
            var:zg361_cl_portfolio_cycle = var:zg361_p2c_cycle
            var:zg361_p2c_cl_frozen_count > 0
            var:zg361_cl_portfolio_ah_expected = var:zg361_p2c_cl_frozen_count
            var:zg361_cl_portfolio_ai_expected = var:zg361_p2c_cl_frozen_count
            var:zg361_cl_portfolio_ah_completed >= var:zg361_cl_portfolio_ah_expected
            var:zg361_cl_portfolio_ai_completed >= var:zg361_cl_portfolio_ai_expected
            trigger_if = { limit = { is_ai = no } NOT = { has_variable = zg361_cl_digest_pending } }
            trigger_else = { always = yes }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_09_status }
    }
    else_if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        if = { limit = { has_variable_list = zg361_p2c_cl_subjects } clear_variable_list = zg361_p2c_cl_subjects }
        set_variable = { name = zg361_p2c_cl_frozen_count value = 0 }
        remove_variable = zg361_p2c_cl_partial_open
        every_vassal = {
            limit = { zg361_is_reviewable_vassal_trigger = yes liege = root }
            save_temporary_scope_as = zg361_p2c_cl_subject_to_store
            root = {
                add_to_variable_list = { name = zg361_p2c_cl_subjects target = scope:zg361_p2c_cl_subject_to_store }
                change_variable = { name = zg361_p2c_cl_frozen_count add = 1 }
            }
        }
        zg361_cl_dispatch_direct_reports_effect = yes
        if = {
            limit = {
                var:zg361_cl_portfolio_cycle = var:zg361_p2c_cycle
                var:zg361_p2c_cl_frozen_count > 0
                var:zg361_cl_portfolio_ah_expected = var:zg361_p2c_cl_frozen_count
                var:zg361_cl_portfolio_ai_expected = var:zg361_p2c_cl_frozen_count
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = {
            # Some reports may already own live AH/AI cases.  Let those exact
            # cases close before recording the partial-open RED, so no player
            # window or delayed ticket is orphaned by the central layer.
            set_variable = { name = zg361_p2c_cl_partial_open value = 1 }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
    }
    else = {
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
}

# Stage 10 freezes only subordinate celestial managers whose own review serial
# strictly lags the owner.  Counts/barons never enter this manager cohort.
zg361_p2c_stage_10_manager_governance_effect = {
    if = {
        limit = { var:zg361_p2c_stage_status = 0 }
        if = { limit = { has_variable_list = zg361_p2c_mg_subjects } clear_variable_list = zg361_p2c_mg_subjects }
        set_variable = { name = zg361_p2c_mg_expected value = 0 }
        set_variable = { name = zg361_p2c_mg_frozen_order_cursor value = 0 }
        every_vassal = {
            limit = {
                zg361_is_celestial_liege_trigger = yes
                liege = root
                has_variable = zg361_review_serial
                var:zg361_review_serial < root.var:zg361_p2c_cycle
            }
            save_temporary_scope_as = zg361_p2c_mg_subject_to_store
            root = {
                change_variable = { name = zg361_p2c_mg_frozen_order_cursor add = 1 }
                add_to_variable_list = { name = zg361_p2c_mg_subjects target = scope:zg361_p2c_mg_subject_to_store }
                change_variable = { name = zg361_p2c_mg_expected add = 1 }
            }
            set_variable = { name = zg361_p2c_mg_frozen_owner value = root }
            set_variable = { name = zg361_p2c_mg_frozen_cycle value = root.var:zg361_p2c_cycle }
            set_variable = { name = zg361_p2c_mg_frozen_case value = root.var:zg361_p2c_case_serial }
            set_variable = { name = zg361_p2c_mg_frozen_order value = root.var:zg361_p2c_mg_frozen_order_cursor }
        }
        if = {
            limit = { var:zg361_p2c_mg_expected = 0 }
            zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else = {
            zg361_mg_dispatch_subordinate_managers_effect = yes
            set_variable = { name = zg361_p2c_mg_started value = 0 }
            set_variable = { name = zg361_p2c_mg_active value = 0 }
            every_in_list = {
                variable = zg361_p2c_mg_subjects
                if = {
                    limit = {
                        has_variable = zg361_case_f_owner
                        has_variable = zg361_case_f_subject
                        has_variable = zg361_case_f_cycle_serial
                        has_variable = zg361_case_f_active
                        has_variable = zg361_case_ak_owner
                        has_variable = zg361_case_ak_subject
                        has_variable = zg361_case_ak_cycle_serial
                        has_variable = zg361_case_ak_active
                        var:zg361_case_f_owner = root
                        var:zg361_case_f_subject = this
                        var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                        var:zg361_case_ak_owner = root
                        var:zg361_case_ak_subject = this
                        var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                    }
                    root = { change_variable = { name = zg361_p2c_mg_started add = 1 } }
                }
                if = {
                    limit = {
                        OR = {
                            AND = { has_variable = zg361_case_f_owner var:zg361_case_f_owner = root has_variable = zg361_case_f_cycle_serial var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_f_active var:zg361_case_f_active = 1 }
                            AND = { has_variable = zg361_case_ak_owner var:zg361_case_ak_owner = root has_variable = zg361_case_ak_cycle_serial var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_ak_active var:zg361_case_ak_active = 1 }
                        }
                    }
                    root = { change_variable = { name = zg361_p2c_mg_active add = 1 } }
                }
            }
            set_variable = { name = zg361_p2c_mg_open_failed value = 0 }
            if = {
                limit = { var:zg361_p2c_mg_started < var:zg361_p2c_mg_expected }
                set_variable = { name = zg361_p2c_mg_open_failed value = 1 }
            }
            set_variable = { name = zg361_p2c_stage_status value = 1 }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
    }
    else = {
        set_variable = { name = zg361_p2c_mg_completed value = 0 }
        set_variable = { name = zg361_p2c_mg_invalid value = 0 }
        set_variable = { name = zg361_p2c_mg_started value = 0 }
        set_variable = { name = zg361_p2c_mg_active value = 0 }
        every_in_list = {
            variable = zg361_p2c_mg_subjects
            if = {
                limit = {
                    has_variable = zg361_case_f_owner
                    has_variable = zg361_case_f_subject
                    has_variable = zg361_case_f_cycle_serial
                    has_variable = zg361_case_f_active
                    has_variable = zg361_case_ak_owner
                    has_variable = zg361_case_ak_subject
                    has_variable = zg361_case_ak_cycle_serial
                    has_variable = zg361_case_ak_active
                    var:zg361_case_f_owner = root
                    var:zg361_case_f_subject = this
                    var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ak_owner = root
                    var:zg361_case_ak_subject = this
                    var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                }
                root = { change_variable = { name = zg361_p2c_mg_started add = 1 } }
            }
            if = {
                limit = {
                    OR = {
                        AND = { has_variable = zg361_case_f_owner var:zg361_case_f_owner = root has_variable = zg361_case_f_cycle_serial var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_f_active var:zg361_case_f_active = 1 }
                        AND = { has_variable = zg361_case_ak_owner var:zg361_case_ak_owner = root has_variable = zg361_case_ak_cycle_serial var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle has_variable = zg361_case_ak_active var:zg361_case_ak_active = 1 }
                    }
                }
                root = { change_variable = { name = zg361_p2c_mg_active add = 1 } }
            }
            if = {
                limit = {
                    is_alive = yes
                    liege = root
                    zg361_is_celestial_liege_trigger = yes
                    var:zg361_case_f_owner = root
                    var:zg361_case_f_subject = this
                    var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_f_state = 5
                    var:zg361_case_f_active = 0
                    var:zg361_case_ak_owner = root
                    var:zg361_case_ak_subject = this
                    var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ak_state = 6
                    var:zg361_case_ak_active = 0
                }
                root = { change_variable = { name = zg361_p2c_mg_completed add = 1 } }
            }
            else_if = {
                limit = { OR = { is_alive = no NOT = { liege = root } NOT = { zg361_is_celestial_liege_trigger = yes } } }
                root = { change_variable = { name = zg361_p2c_mg_invalid add = 1 } }
            }
            else_if = {
                limit = {
                    has_variable = zg361_case_f_owner
                    has_variable = zg361_case_f_cycle_serial
                    has_variable = zg361_case_f_state
                    has_variable = zg361_case_f_active
                    has_variable = zg361_case_ak_owner
                    has_variable = zg361_case_ak_cycle_serial
                    has_variable = zg361_case_ak_state
                    has_variable = zg361_case_ak_active
                    var:zg361_case_f_owner = root
                    var:zg361_case_f_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_f_active = 0
                    var:zg361_case_ak_owner = root
                    var:zg361_case_ak_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ak_active = 0
                    OR = { var:zg361_case_f_state != 5 var:zg361_case_ak_state != 6 }
                }
                root = { change_variable = { name = zg361_p2c_mg_invalid add = 1 } }
            }
        }
        if = {
            limit = { var:zg361_p2c_mg_invalid > 0 }
            zg361_p2c_record_red_effect = { CODE = 1010 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else_if = {
            limit = {
                var:zg361_p2c_mg_open_failed = 1
                var:zg361_p2c_mg_active = 0
            }
            zg361_p2c_record_red_effect = { CODE = 1011 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else_if = {
            limit = {
                var:zg361_p2c_mg_open_failed = 0
                var:zg361_p2c_mg_started >= var:zg361_p2c_mg_expected
                var:zg361_p2c_mg_completed >= var:zg361_p2c_mg_expected
            }
            zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_10_status }
        }
        else = {
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
    }
}

# The Workforce seam is written once here; mutually exclusive start/resume
# branches below call this wrapper, preserving one public opener per pump.
zg361_p2c_call_workforce_adapter_effect = {
    zg361_we_open_portfolio_effect = { SUBJECT = var:zg361_p2c_subject }
}

# Stage 11: ordinary assessed counts/barons are valid initial Workforce
# subjects.  Only the domain's later #360/#361 resume guard may require a
# manager subject.  status 5 is a real external wait, never completion.
zg361_p2c_stage_11_workforce_endgame_effect = {
    if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 1
                var:zg361_we_portfolio_status = 6
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_we_final_conservation_ok = 1
            }
        }
        if = {
            limit = { var:zg361_p2c_m360_source_status = 1 }
            set_variable = { name = zg361_p2c_m360_source_status value = 2 }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_11_status }
    }
    else_if = {
        # Cycles one/two (and a non-top third cycle) have genuinely consumed
        # #360 but do not yet expose #361.  Status 8 is a valid
        # history-accruing close, not RED and not fabricated success.
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 1
                var:zg361_we_portfolio_status = 8
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_we_portfolio_terminal_history_accruing = 1
                var:zg361_we_portfolio_history_cycle_count >= 1
                var:zg361_we_portfolio_history_cycle_count <= 3
                var:zg361_we_portfolio_terminal_owned_operations = 39
                var:zg361_we_portfolio_terminal_skipped_charter = 1
                var:zg361_we_portfolio_terminal_success = 0
                var:zg361_we_final_conservation_ok = 1
                var:zg361_case_al_active = 0
                var:zg361_case_al_state = 8
            }
        }
        if = {
            limit = { var:zg361_p2c_m360_source_status = 1 }
            set_variable = { name = zg361_p2c_m360_source_status value = 2 }
        }
        zg361_p2c_record_stage_effect = { STATUS = 2 STAGE_VAR = zg361_p2c_stage_11_status }
    }
    else_if = {
        # Workforce owns the non-manager close: 38 ordinary operations settle,
        # manager-only #360/#361 write no receipt, AL is closed, and status 7 is
        # N/A rather than business success.
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 1
                var:zg361_we_portfolio_status = 7
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                var:zg361_we_portfolio_terminal_na = 1
                OR = {
                    var:zg361_we_portfolio_terminal_reason = 360361
                    var:zg361_we_portfolio_terminal_reason = 360362
                }
                var:zg361_we_portfolio_terminal_owned_operations = 38
                var:zg361_we_portfolio_terminal_skipped_manager_only = 2
                var:zg361_we_portfolio_terminal_success = 0
                var:zg361_we_final_conservation_ok = 1
                var:zg361_case_al_active = 0
            }
        }
        zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_11_status }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_status = 5
                var:zg361_we_awaiting_al_357_359 = 1
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
            }
        }
        # The only automatic resume attempt consumes source receipts minted by
        # the real B1 facts/quota close and B2 appeal/quota-return consumers.
        # It cannot manufacture ids/hashes and route-C debts remain waiting.
        if = {
            limit = {
                var:zg361_p2c_subject = { zg361_is_celestial_liege_trigger = yes }
            }
            var:zg361_p2c_subject = {
                zg361_b2_submit_completed_al_receipts_effect = {
                    TICKET_OWNER = root TICKET_SUBJECT = this
                    TICKET_CYCLE = root.var:zg361_p2c_cycle
                    TICKET_CASE = var:zg361_case_al_case_serial
                }
            }
        }
        # Once exact external receipts advance AL to state 4, Central freezes a
        # route-neutral three-manager source.  It never calls the old opener,
        # because that opener could expose #360 before this source is READY.
        if = {
            limit = {
                var:zg361_p2c_subject = { zg361_is_celestial_liege_trigger = yes }
                var:zg361_p2c_subject = {
                    var:zg361_we_al_external_stage_receipts_verified = 1
                    var:zg361_we_al_external_receipt_owner = root
                    var:zg361_we_al_external_receipt_subject = this
                    var:zg361_we_al_external_receipt_cycle = root.var:zg361_p2c_cycle
                    var:zg361_we_al_external_receipt_case = var:zg361_case_al_case_serial
                    var:zg361_we_al_external_receipt_count = 3
                    var:zg361_we_al_external_last_operation = 359
                    OR = { var:zg361_case_al_state = 4 var:zg361_case_al_state = 5 }
                }
            }
            zg361_p2c_prepare_m360_source_effect = yes
            if = {
                limit = { var:zg361_p2c_m360_source_status = 1 }
                zg361_we_resume_m360_from_central_source_effect = {
                    TICKET_OWNER = root
                    TICKET_SUBJECT = var:zg361_p2c_subject
                    TICKET_CYCLE = var:zg361_p2c_cycle
                    TICKET_CASE = var:zg361_p2c_subject.var:zg361_case_al_case_serial
                }
                set_variable = { name = zg361_p2c_stage_status value = 1 }
                zg361_p2c_mark_lane_busy_effect = yes
                zg361_p2c_schedule_pump_effect = { DAYS = 2 }
            }
            else_if = {
                limit = { var:zg361_p2c_m360_source_status = 5 }
                zg361_p2c_mark_external_wait_effect = { REASON = 360410 STAGE_VAR = zg361_p2c_stage_11_status }
            }
            else_if = {
                limit = { var:zg361_p2c_m360_source_status = 7 }
                var:zg361_p2c_subject = {
                    zg361_we_finalize_manager_collective_na_effect = {
                        TICKET_OWNER = root
                        TICKET_SUBJECT = this
                        TICKET_CYCLE = root.var:zg361_p2c_cycle
                        TICKET_CASE = var:zg361_case_al_case_serial
                        REASON = 360362
                    }
                }
                if = {
                    limit = {
                        var:zg361_p2c_subject = {
                            var:zg361_we_portfolio_closed = 1
                            var:zg361_we_portfolio_status = 7
                            var:zg361_we_portfolio_terminal_reason = 360362
                            var:zg361_we_final_conservation_ok = 1
                            var:zg361_case_al_active = 0
                        }
                    }
                    zg361_p2c_record_stage_effect = { STATUS = 3 STAGE_VAR = zg361_p2c_stage_11_status }
                }
                else = { zg361_p2c_record_red_effect = { CODE = 1192 STAGE_VAR = zg361_p2c_stage_11_status } }
            }
            else = { zg361_p2c_record_red_effect = { CODE = 1191 STAGE_VAR = zg361_p2c_stage_11_status } }
        }
        else_if = {
            # #360/#361 are manager-only by contract.  Without a Workforce
            # public N/A-close seam, a count/baron cannot legally close AL.
            # Suspend the central case as an external blocker: no success,
            # no completed-cycle marker, and no permanent D+2 retry loop.
            limit = {
                var:zg361_p2c_subject = { NOT = { zg361_is_celestial_liege_trigger = yes } }
            }
            zg361_p2c_suspend_external_effect = { REASON = 360361 STAGE_VAR = zg361_p2c_stage_11_status }
        }
        else = { zg361_p2c_mark_external_wait_effect = { REASON = 357359 STAGE_VAR = zg361_p2c_stage_11_status } }
    }
    else_if = {
        limit = {
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                OR = { var:zg361_case_ab_active = 1 var:zg361_case_ac_active = 1 var:zg361_case_ad_active = 1 var:zg361_case_al_active = 1 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        # AB -> AC -> AD -> AL has the same D+1 transition gap semantics.
        limit = {
            var:zg361_p2c_stage_status = 1
            var:zg361_p2c_subject = {
                var:zg361_we_portfolio_closed = 0
                var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                NOT = { var:zg361_we_portfolio_status = 5 }
            }
        }
        zg361_p2c_mark_lane_busy_effect = yes
        zg361_p2c_schedule_pump_effect = { DAYS = 2 }
    }
    else_if = {
        limit = {
            var:zg361_p2c_stage_status = 0
            var:zg361_p2c_subject = {
                has_variable = zg361_ch_hc_authorized
                has_variable = zg361_ch_hc_available
                has_variable = zg361_ch_hc_reserved
                has_variable = zg361_ch_hc_occupied
                has_variable = zg361_ch_hc_frozen
                has_variable = zg361_ch_hc_reclaimed
            }
        }
        zg361_p2c_call_workforce_adapter_effect = yes
        if = {
            limit = {
                var:zg361_p2c_subject = {
                    var:zg361_we_portfolio_cycle = root.var:zg361_p2c_cycle
                    var:zg361_case_ab_owner = root
                    var:zg361_case_ab_subject = this
                    var:zg361_case_ab_cycle_serial = root.var:zg361_p2c_cycle
                    var:zg361_case_ab_active = 1
                }
            }
            zg361_p2c_mark_lane_busy_effect = yes
            zg361_p2c_schedule_pump_effect = { DAYS = 2 }
        }
        else = { zg361_p2c_record_red_effect = { CODE = 1111 STAGE_VAR = zg361_p2c_stage_11_status } }
    }
    else = { zg361_p2c_record_red_effect = { CODE = 1161 STAGE_VAR = zg361_p2c_stage_11_status } }
}

# One entry point and one else-if chain: a single pump can dispatch at most one
# stage, and each stage body calls at most one public adapter/domain opener.
zg361_p2c_pump_effect = {
    if = {
        limit = {
            has_game_rule = zg361_on
            zg361_is_celestial_liege_trigger = yes
            has_variable = zg361_p2c_active
            var:zg361_p2c_active = 1
            has_variable = zg361_p2c_case_serial
            has_variable = zg361_p2c_b1_cycle
            has_variable = zg361_p2c_b1_case
            has_variable = zg361_p2c_cycle
            has_variable = zg361_p2c_subject
            has_variable = zg361_p2c_result_case
            has_variable = zg361_review_serial
            has_variable = zg361_b1_cycle_serial
            has_variable = zg361_b1_case_serial
            has_variable = zg361_b1_closure_state
            var:zg361_review_serial = var:zg361_p2c_cycle
            var:zg361_b1_cycle_serial = var:zg361_p2c_b1_cycle
            var:zg361_b1_case_serial = var:zg361_p2c_b1_case
            var:zg361_b1_closure_state = 4
            var:zg361_p2c_subject = {
                is_alive = yes
                zg361_is_reviewable_vassal_trigger = yes
                liege = root
                var:zg361_b1_case_owner = root
                var:zg361_b1_case_subject = this
                var:zg361_b1_cycle_serial = root.var:zg361_p2c_b1_cycle
                var:zg361_b1_case_serial = root.var:zg361_p2c_b1_case
                var:zg361_b1_case_state = 8
                var:zg361_result_case_owner = root
                var:zg361_result_cycle_serial = root.var:zg361_p2c_cycle
                var:zg361_result_case_serial = root.var:zg361_p2c_result_case
            }
        }
        if = { limit = { var:zg361_p2c_stage = 1 } zg361_p2c_stage_01_career_hc_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 2 } zg361_p2c_stage_02_compensation_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 3 } zg361_p2c_stage_03_feedback_promotion_pip_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 4 } zg361_p2c_stage_04_x_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 5 } zg361_p2c_stage_05_y_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 6 } zg361_p2c_stage_06_z_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 7 } zg361_p2c_stage_07_metrics_delivery_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 8 } zg361_p2c_stage_08_credit_project_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 9 } zg361_p2c_stage_09_career_learning_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 10 } zg361_p2c_stage_10_manager_governance_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage = 11 } zg361_p2c_stage_11_workforce_endgame_effect = yes }
        else_if = { limit = { var:zg361_p2c_stage >= 12 } zg361_p2c_finish_effect = yes }
        else = { zg361_p2c_abort_stale_effect = { CODE = 9002 } }
    }
    else_if = {
        limit = { has_variable = zg361_p2c_active var:zg361_p2c_active = 1 }
        zg361_p2c_abort_stale_effect = { CODE = 9001 }
    }
    else = { debug_log = "ZG361P2C: inactive central pump ignored" }
}
'''


def historical_effect_payload() -> bytes:
    """Return the pre-shard aggregate exactly as it was written on disk."""

    return BOM + render_effects().replace("\r\n", "\n").encode("utf-8")


def _skip_quoted_string(text: str, index: int) -> int:
    index += 1
    escaped = False
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return index + 1
        index += 1
    raise ValueError("unterminated quoted string in phase-two central effects")


def _skip_comment(text: str, index: int) -> int:
    newline = text.find("\n", index)
    return len(text) if newline < 0 else newline + 1


def _block_end(text: str, open_brace: int) -> int:
    depth = 0
    index = open_brace
    while index < len(text):
        char = text[index]
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                raise ValueError("unbalanced phase-two central effect block")
        index += 1
    raise ValueError("unterminated phase-two central effect block")


def top_level_effect_blocks(payload: bytes | str) -> tuple[tuple[str, str], ...]:
    """Return complete top-level definitions without changing their bytes."""

    text = (
        payload.decode("utf-8-sig")
        if isinstance(payload, bytes)
        else payload.lstrip("\ufeff")
    )
    blocks: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if not (char.isalpha() or char == "_"):
            index += 1
            continue
        start = index
        index += 1
        while index < len(text) and (
            text[index].isalnum() or text[index] in "_."
        ):
            index += 1
        name = text[start:index]
        cursor = index
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "=":
            continue
        cursor += 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            continue
        end = _block_end(text, cursor)
        blocks.append((name, text[start:end]))
        index = end
    return tuple(blocks)


def _validate_effect_groups(
    source: str,
    source_blocks: tuple[tuple[str, str], ...],
) -> None:
    payload = BOM + source.replace("\r\n", "\n").encode("utf-8")
    if len(payload) != HISTORICAL_EFFECT_BYTES:
        raise ValueError(
            "phase-two central aggregate byte count drifted: "
            f"{len(payload)} != {HISTORICAL_EFFECT_BYTES}"
        )
    digest = hashlib.sha256(payload).hexdigest().upper()
    if digest != HISTORICAL_EFFECT_SHA256:
        raise ValueError(
            "phase-two central aggregate SHA-256 drifted: "
            f"{digest} != {HISTORICAL_EFFECT_SHA256}"
        )

    source_names = tuple(name for name, _block in source_blocks)
    configured_names = tuple(
        name for group in EFFECT_GROUPS for name in group.effect_names
    )
    filenames = tuple(group.filename for group in EFFECT_GROUPS)
    if len(source_names) != HISTORICAL_EFFECT_COUNT:
        raise ValueError(
            f"phase-two central aggregate must contain {HISTORICAL_EFFECT_COUNT} "
            f"top-level effects, found {len(source_names)}"
        )
    if len(source_names) != len(set(source_names)):
        raise ValueError("phase-two central aggregate contains duplicate effects")
    if len(filenames) != len(set(filenames)):
        raise ValueError("phase-two central effect shard filenames must be unique")
    if source_names != configured_names:
        missing = sorted(set(source_names) - set(configured_names))
        unexpected = sorted(set(configured_names) - set(source_names))
        raise ValueError(
            "phase-two central effect groups must preserve exact source order and coverage; "
            f"missing={missing}, unexpected={unexpected}"
        )
    for group in EFFECT_GROUPS:
        count = len(group.effect_names)
        if not group.purpose.strip():
            raise ValueError(f"{group.filename} must declare a purpose")
        if count < 1:
            raise ValueError(f"{group.filename} must contain at least one effect")

    over_hard = {
        group.filename
        for group in EFFECT_GROUPS
        if len(group.effect_names) > EFFECT_HARD_MAX
    }
    if set(EFFECT_HARD_LIMIT_EXCEPTIONS) != over_hard:
        raise ValueError(
            "phase-two central effect hard-limit exceptions must exactly match "
            "shards above the hard principle"
        )
    for filename in sorted(over_hard):
        reason, live_evidence = EFFECT_HARD_LIMIT_EXCEPTIONS[filename]
        if not reason.strip() or not live_evidence.strip():
            raise ValueError(
                f"{filename} exceeds {EFFECT_HARD_MAX} effects without reason "
                "and CK3 live evidence"
            )


def render_effect_parts() -> dict[str, str]:
    """Project the frozen aggregate into purpose-cohesive definition shards."""

    source = render_effects()
    source_blocks = top_level_effect_blocks(source)
    _validate_effect_groups(source, source_blocks)
    by_name = dict(source_blocks)
    parts: dict[str, str] = {}
    for group in EFFECT_GROUPS:
        body = "\n\n".join(by_name[name] for name in group.effect_names)
        parts[group.filename] = (
            HEADER
            + f"# PURPOSE: {group.purpose}.\n"
            + f"# READINESS: {READINESS}. No CK3 parser, paused snapshot or live evidence is claimed.\n\n"
            + body
            + "\n"
        )
    return parts


def render_events() -> str:
    return HEADER + r'''namespace = zg361p2c

# Exact delayed poll.  Old tickets never mutate a newer central case.
zg361p2c.1 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                exists = scope:zg361_p2c_ticket_manager
                this = scope:zg361_p2c_ticket_manager
                has_variable = zg361_p2c_active
                var:zg361_p2c_active = 1
                var:zg361_p2c_cycle = scope:zg361_p2c_ticket_cycle
                var:zg361_p2c_case_serial = scope:zg361_p2c_ticket_case
                var:zg361_p2c_stage = scope:zg361_p2c_ticket_stage
                var:zg361_p2c_ticket_serial = scope:zg361_p2c_ticket_identity
            }
            zg361_p2c_pump_effect = yes
        }
        else = { debug_log = "ZG361P2C: stale or replayed central poll ignored" }
    }
}

# The only central visible event.  Domain packages retain their own bounded
# cards; the central layer emits one terminal aggregate and nothing per stage.
zg361p2c.2 = {
    type = character_event
    title = zg361_p2c_summary_title
    desc = zg361_p2c_summary_desc
    theme = stewardship
    trigger = {
        is_ai = no
        has_variable = zg361_p2c_summary_pending
        var:zg361_p2c_cycle = scope:zg361_p2c_summary_cycle
        var:zg361_p2c_case_serial = scope:zg361_p2c_summary_case
    }
    option = {
        name = zg361_p2c_summary_ack
        remove_variable = zg361_p2c_summary_pending
    }
}

# A new B1 season that collides with an old active central case is initialized
# only after the old typed-RED summary had one full day to be acknowledged.
zg361p2c.3 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                has_variable = zg361_p2c_deferred_reinit
                var:zg361_p2c_deferred_reinit = 1
                has_variable = zg361_review_serial
                has_variable = zg361_b1_case_serial
                var:zg361_review_serial = var:zg361_p2c_deferred_reinit_cycle
                var:zg361_b1_case_serial = var:zg361_p2c_deferred_reinit_b1_case
            }
            remove_variable = zg361_p2c_deferred_reinit
            zg361_p2c_on_review_published_effect = yes
        }
        else = { debug_log = "ZG361P2C: stale deferred central reinitialization ignored" }
    }
}

# #275-A ingress.  The due consumer has already committed the refused-hold
# ticket, but still owns hold_pending and the original owner HC flight.
zg361p2c.4 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                exists = scope:zg361_p2c_m275_ingress_owner
                exists = scope:zg361_p2c_m275_ingress_subject
                exists = scope:zg361_p2c_m275_ingress_cycle
                exists = scope:zg361_p2c_m275_ingress_case
                exists = scope:zg361_p2c_m275_ingress_identity
                this = scope:zg361_p2c_m275_ingress_subject
                has_variable = zg361_p2c_m275_ingress_ticket_serial
                var:zg361_p2c_m275_ingress_ticket_serial = scope:zg361_p2c_m275_ingress_identity
                has_variable = zg361_we_m275_runner_reopen_pending
                var:zg361_we_m275_runner_reopen_pending = 1
                has_variable = zg361_we_m275_hold_pending
                var:zg361_we_m275_hold_pending = 1
            }
            zg361_p2c_open_m275_runner_requisition_effect = {
                TICKET_OWNER = scope:zg361_p2c_m275_ingress_owner
                TICKET_SUBJECT = scope:zg361_p2c_m275_ingress_subject
                TICKET_CYCLE = scope:zg361_p2c_m275_ingress_cycle
                TICKET_CASE = scope:zg361_p2c_m275_ingress_case
            }
        }
        else = { debug_log = "ZG361P2C: stale M275 runner requisition ingress ignored" }
    }
}

# The producer's committed source is consumed one frame later.  This event
# never trusts caller-supplied runner/case/receipt values: Workforce joins the
# canonical subject-local source directly.
zg361p2c.5 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                exists = scope:zg361_p2c_m275_dispatch_owner
                exists = scope:zg361_p2c_m275_dispatch_subject
                exists = scope:zg361_p2c_m275_dispatch_cycle
                exists = scope:zg361_p2c_m275_dispatch_case
                exists = scope:zg361_p2c_m275_dispatch_serial
                exists = scope:zg361_p2c_m275_dispatch_new_case
                exists = scope:zg361_p2c_m275_dispatch_receipt
                this = scope:zg361_p2c_m275_dispatch_subject
                has_variable = zg361_p2c_m275_requisition_committed
                has_variable = zg361_p2c_m275_requisition_pending
                has_variable = zg361_p2c_m275_requisition_consumed
                var:zg361_p2c_m275_requisition_committed = 1
                var:zg361_p2c_m275_requisition_pending = 1
                var:zg361_p2c_m275_requisition_consumed = 0
                var:zg361_p2c_m275_requisition_owner = scope:zg361_p2c_m275_dispatch_owner
                var:zg361_p2c_m275_requisition_original_subject = scope:zg361_p2c_m275_dispatch_subject
                var:zg361_p2c_m275_requisition_source_cycle = scope:zg361_p2c_m275_dispatch_cycle
                var:zg361_p2c_m275_requisition_source_case = scope:zg361_p2c_m275_dispatch_case
                var:zg361_p2c_m275_requisition_serial = scope:zg361_p2c_m275_dispatch_serial
                var:zg361_p2c_m275_requisition_new_case = scope:zg361_p2c_m275_dispatch_new_case
                var:zg361_p2c_m275_requisition_receipt_id = scope:zg361_p2c_m275_dispatch_receipt
            }
            zg361_we_consume_m275_runner_reopen_effect = {
                TICKET_OWNER = scope:zg361_p2c_m275_dispatch_owner
                TICKET_SUBJECT = scope:zg361_p2c_m275_dispatch_subject
                TICKET_CYCLE = scope:zg361_p2c_m275_dispatch_cycle
                TICKET_CASE = scope:zg361_p2c_m275_dispatch_case
            }
            save_scope_as = zg361_p2c_m275_verify_subject
            scope:zg361_p2c_m275_dispatch_owner = { save_scope_as = zg361_p2c_m275_verify_owner }
            save_scope_value_as = { name = zg361_p2c_m275_verify_cycle value = scope:zg361_p2c_m275_dispatch_cycle }
            save_scope_value_as = { name = zg361_p2c_m275_verify_case value = scope:zg361_p2c_m275_dispatch_case }
            save_scope_value_as = { name = zg361_p2c_m275_verify_serial value = scope:zg361_p2c_m275_dispatch_serial }
            save_scope_value_as = { name = zg361_p2c_m275_verify_new_case value = scope:zg361_p2c_m275_dispatch_new_case }
            save_scope_value_as = { name = zg361_p2c_m275_verify_receipt value = scope:zg361_p2c_m275_dispatch_receipt }
            trigger_event = { id = zg361p2c.6 days = 1 }
        }
        else = { debug_log = "ZG361P2C: stale M275 runner requisition dispatch ignored" }
    }
}

# Central consumes its source only after a later-frame exact check of
# Workforce's durable result.  A failed adapter leaves both source pending and
# the original HC flight inspectable.
zg361p2c.6 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                exists = scope:zg361_p2c_m275_verify_owner
                exists = scope:zg361_p2c_m275_verify_subject
                exists = scope:zg361_p2c_m275_verify_cycle
                exists = scope:zg361_p2c_m275_verify_case
                exists = scope:zg361_p2c_m275_verify_serial
                exists = scope:zg361_p2c_m275_verify_new_case
                exists = scope:zg361_p2c_m275_verify_receipt
                this = scope:zg361_p2c_m275_verify_subject
                has_variable = zg361_p2c_m275_requisition_committed
                has_variable = zg361_p2c_m275_requisition_pending
                has_variable = zg361_p2c_m275_requisition_consumed
                var:zg361_p2c_m275_requisition_committed = 1
                var:zg361_p2c_m275_requisition_pending = 1
                var:zg361_p2c_m275_requisition_consumed = 0
                var:zg361_p2c_m275_requisition_owner = scope:zg361_p2c_m275_verify_owner
                var:zg361_p2c_m275_requisition_original_subject = scope:zg361_p2c_m275_verify_subject
                var:zg361_p2c_m275_requisition_source_cycle = scope:zg361_p2c_m275_verify_cycle
                var:zg361_p2c_m275_requisition_source_case = scope:zg361_p2c_m275_verify_case
                var:zg361_p2c_m275_requisition_serial = scope:zg361_p2c_m275_verify_serial
                var:zg361_p2c_m275_requisition_new_case = scope:zg361_p2c_m275_verify_new_case
                var:zg361_p2c_m275_requisition_receipt_id = scope:zg361_p2c_m275_verify_receipt
            }
            if = {
                limit = {
                    has_variable = zg361_we_m275_runner_reopen_consumed
                    has_variable = zg361_we_m275_runner_new_case
                    has_variable = zg361_we_m275_runner_requisition_receipt_id
                    has_variable = zg361_we_m275_runner_requisition_receipt_hash
                    has_variable = zg361_we_m275_runner_requisition_candidate
                    has_variable = zg361_we_m275_runner_requisition_evidence
                    has_variable = zg361_we_candidate_active
                    has_variable = zg361_we_candidate_active_owner
                    has_variable = zg361_we_candidate_active_case
                    has_variable = zg361_we_candidate_active_character
                    has_variable = zg361_we_m275_hold_pending
                    has_variable = zg361_we_m275_runner_reopen_pending
                    var:zg361_we_m275_runner_reopen_consumed = 1
                    var:zg361_we_m275_runner_new_case = var:zg361_p2c_m275_requisition_new_case
                    var:zg361_we_m275_runner_requisition_receipt_id = var:zg361_p2c_m275_requisition_receipt_id
                    var:zg361_we_m275_runner_requisition_receipt_hash = var:zg361_p2c_m275_requisition_receipt_hash
                    var:zg361_we_m275_runner_requisition_candidate = var:zg361_p2c_m275_requisition_runner_up
                    var:zg361_we_m275_runner_requisition_evidence = var:zg361_p2c_m275_requisition_runner_evidence
                    var:zg361_we_candidate_active = 1
                    var:zg361_we_candidate_active_owner = scope:zg361_p2c_m275_verify_owner
                    var:zg361_we_candidate_active_case = scope:zg361_p2c_m275_verify_new_case
                    var:zg361_we_candidate_active_character = var:zg361_p2c_m275_requisition_runner_up
                    var:zg361_we_m275_hold_pending = 0
                    var:zg361_we_m275_runner_reopen_pending = 0
                    has_variable = zg361_we_m266_hc_reservation_active
                    has_variable = zg361_we_m266_hc_receipt
                    var:zg361_we_m266_hc_reservation_active = 1
                    var:zg361_we_m266_hc_receipt = var:zg361_p2c_m275_requisition_hc_lineage_receipt
                    scope:zg361_p2c_m275_verify_owner = {
                        zg361_is_celestial_liege_trigger = yes
                        has_variable = zg361_we_ad_hc_flight_pending
                        var:zg361_we_ad_hc_flight_pending = 1
                        var:zg361_we_ad_hc_flight_subject = scope:zg361_p2c_m275_verify_subject
                        var:zg361_we_ad_hc_flight_cycle = scope:zg361_p2c_m275_verify_cycle
                        var:zg361_we_ad_hc_flight_case = scope:zg361_p2c_m275_verify_new_case
                    }
                }
                set_variable = { name = zg361_p2c_m275_requisition_status value = 2 }
                set_variable = { name = zg361_p2c_m275_requisition_pending value = 0 }
                set_variable = { name = zg361_p2c_m275_requisition_consumed value = 1 } # source close commit last
            }
            else = {
                set_variable = { name = zg361_p2c_m275_requisition_verify_status value = 4 }
                set_variable = { name = zg361_p2c_m275_requisition_collision_code value = 27543 }
                debug_log = "ZG361P2C RED: M275 runner source was not consumed exactly"
            }
        }
        else = { debug_log = "ZG361P2C: stale or replayed M275 runner verification ignored" }
    }
}
'''


def render_localization(language: str, header: str) -> str:
    chinese = language == "simp_chinese"
    if chinese:
        title = "二期绩效流水线：终于跑完了"
        desc = (
            "公示后的二期案卷已经串行收口。成功域：#high "
            "[ROOT.MakeScope.Var('zg361_p2c_success_n').GetValue|0]#!；不适用："
            "[ROOT.MakeScope.Var('zg361_p2c_na_n').GetValue|0]；RED："
            "[ROOT.MakeScope.Var('zg361_p2c_red_n').GetValue|0]；曾等待外部依赖："
            "[ROOT.MakeScope.Var('zg361_p2c_external_n').GetValue|0]。好消息是没有九个部门同时弹窗，"
            "坏消息是它们确实都留下了表格。"
        )
        ack = "很好，把这摞表从我桌上拿走。"
    else:
        title = "Phase-Two Performance Pipeline: Finally Closed"
        desc = (
            "The post-publication phase-two portfolio has closed serially. Successful domains: #high "
            "[ROOT.MakeScope.Var('zg361_p2c_success_n').GetValue|0]#!; not applicable: "
            "[ROOT.MakeScope.Var('zg361_p2c_na_n').GetValue|0]; RED: "
            "[ROOT.MakeScope.Var('zg361_p2c_red_n').GetValue|0]; external waits encountered: "
            "[ROOT.MakeScope.Var('zg361_p2c_external_n').GetValue|0]. The good news is that nine teams did not "
            "open nine windows at once. The bad news is that every team still produced a spreadsheet."
        )
        ack = "Excellent. Remove this stack from my desk."
    return f'{header}:\n # GENERATED FILE — edit tools/gen_361_phase2_central_runtime.py\n zg361_p2c_summary_title:0 "{title}"\n zg361_p2c_summary_desc:0 "{desc}"\n zg361_p2c_summary_ack:0 "{ack}"\n'


def render_spec() -> str:
    return """# 361 二期中央串行调度层：CK3 runtime 合同

Readiness: `static-ready`

MCP evidence: `none`

CK3 live evidence: `none`

## 1. 权限和冻结身份

- 中央 ROOT 必须通过 `zg361_is_celestial_liege_trigger`：天朝制、在世、有地、公爵及以上。
- 伯爵和男爵可以作为直属受评 subject，但永远不能成为中央 manager。
- B1 公示后，从本轮已冻结结果 cohort 里按 `stewardship / position = 0` 冻结一个 primary subject。
- 中央案固定 `manager + B1 cycle/case + review cycle + subject + result case`；死亡、调任、换 owner/cycle/case 都 typed RED，绝不换人续跑。
- #360 的 C1 必须就是该 primary subject 且其本人为天朝制公爵以上经理；C2/C3 只能从 stage 10 已冻结的
  `zg361_p2c_mg_subjects` 按冻结序号选择。首个三人总 quota 在 1..6 的完整组合被冻结；超限组合整体跳过，绝不截断 quota 或成员。
- #360 只冻结 manager 以及 B1/MG source identity，不预先决定 forced/exception partition。A/B 选项提交后才由
  Workforce 产品 wrapper 读取三组真实 source 并 materialize；C 不 begin、不 append、不 seal。

## 2. 两阶段 hook

1. `zg361_apply_pending_grades_effect` 先完成榜单、`zg361_b1_mark_published_effect`、清除 `zg361_review_in_progress`，随后只调用 `zg361_p2c_on_review_published_effect`。它只初始化并排 D+2 pump，不开领域。
2. `zg361_settle_delivered_325_effect` 先写 state 3、settlement receipt，并调用 `zg361_b2_on_notice_delivered_effect`，随后调用 `zg361_p2c_on_result_delivered_effect`。它仅用 exact owner/subject/cycle/result-case 唤醒正在等待的 Compensation/P3。

B1 open、D+180、事实冻结以及未送达的 3.25 都不是二期入口。
M013 公示闭合证明按显式 mode 严格互斥：route A/B 必须同时满足 `m013_mode` 存在且 `mode!=3`、`receipt_serial=current case`；合法 route C 必须同时满足 `mode=3`、`policy_debt_serial=current case`。`mode=3` 即使遗留或伪造了本轮 receipt 也不能走 A/B，`mode!=3` 即使存在本轮 policy debt 也不能走 C；缺失 mode 同样不能初始化中央案。延期披露不会丢掉合法 route C 的二期链。

## 3. 串行顺序

| Stage | 领域 | Public ABI | 中央终态 |
|---:|---|---|---|
| 1 | Career/HC | `zg361_career_hc_open_portfolio_effect` | manager completed cycle + 同一 subject closed |
| 2 | Compensation/LTI | `zg361_comp_portfolio_open_next_effect` | exact result snapshot + completed cycle；每域 ACK 后重复 pump |
| 3 | Feedback/Promotion/PIP | `zg361_pp_manager_portfolio_adapter_effect` | T→U→V→W→complete，五次单 adapter pump |
| 4–6 | Incident X/Y/Z | 三个 public domain opener | 严格 X→Y→Z；正案必须携带真实事故与后果、next-KPI staged receipt；无事故只认 exact probe/N/A tuple 并记 status 3；禁止 all-domain opener |
| 7 | Metrics/Delivery | `zg361_p3_open_portfolio_effect` | 同 result case、closed、conservation OK |
| 8 | Credit/Project | `zg361_cp_open_portfolio_effect` | closed + conservation OK；无 distinct reviewer 为 N/A |
| 9 | Career/Learning | `zg361_cl_dispatch_direct_reports_effect` | expected/completed 全齐；玩家 digest 已 ACK |
| 10 | Manager/Governance | `zg361_mg_dispatch_subordinate_managers_effect` | 冻结带 owner/cycle/case/order 的 strict-lag manager cohort，全部 F/AK terminal；空集 N/A |
| 11 | Workforce/Endgame | 初始 `zg361_we_open_portfolio_effect`；#360 `zg361_we_resume_m360_from_central_source_effect` | status 6 success；status 8 为真实 history-accruing terminal；status 7 为 count/baron 或 manager structural N/A；status 5 是外部等待 |

每次中央 pump 的 `if/else_if` 只进入一个 stage；每个 stage 每次最多调用一个 public adapter/domain opener。玩家与 AI 走同一业务 ABI 和同一顺序，差异仅是玩家 UI lane 与最终摘要；AI 后台静默。

## 4. UI、等待与 replay

- 公示后 D+2 才开首域；领域 terminal 后再 D+2 才进下一域，给 D+1 完成卡留出 ACK 时间。
- PP 的 queue lock、Compensation 的 active flag、Career/Learning 的 digest pending 都是中央真实等待条件。
- Incident X/Y/Z 的 success 额外要求 `applicable=1`、positive incident/source/consequence 与 `final_kpi_staged=1`；N/A 必须同时冻结 owner/subject/cycle、reason=1、probe/receipt serial，并回指同周期 `probe_result/source/consequence=0/0/0`。缺字段或任意旧零值都不能冒充 N/A。
- Career/HC、Compensation、PP 的 manager-only ABI 会先按各自同一筛选器预选；只有候选仍等于 frozen primary 才调用，防止资格漂移在别人身上留下 active orphan。
- Career/Learning 冻结直属 cohort/count，AH/AI expected 必须各自等于该 count；partial open 等已开案终态后记 RED。Manager/Governance 同样核对 frozen cohort 的 exact F/AK started/active/terminal，failed open 不会无限轮询。
- #360 source status 严格分为 READY=1、consumed=2、RED=4、WAIT=5、structural N/A=7。B1 status 2 的 route C、
  zero quota、absolute-grade C、单 cohort quota>6 只排除该 manager；B1 status 3 的 agenda/member/#137/#357/
  result/hash/quota 不一致是 RED，禁止换一组经理掩盖。未发布且合法流程仍 active 才是 WAIT；同轮 B1 已 terminal
  却没有 diagnostic status 同样是 RED。
- READY 同时要求每名 manager 的 exact B1 source、六槽以内真实 #357 candidate，以及同一 Central cycle 的 MG F/m036
  terminal snapshot；`team_n/member_count`、`team_bottom_n/quota` 与 snapshot 的 B1 source serial 必须一致。冻结后任一
  manager、B1 source id/hash/quota 或 MG case/revision 漂移立即 RED，绝不重选。
- delayed poll 带 `manager + cycle + central case + stage + ticket serial`；新 ticket 使旧事件 strict no-op。
- #275-A runner-up 招聘是独立于 stage 11 的 Central 产品入口：旧 AD 案 D+90 到期后只排
  `zg361p2c.4`，再以三个自然帧完成 canonical source commit → Workforce consume → Central verify/close。
  source 在拒绝候选 subject 上冻结 owner、original subject、runner/evidence、cycle/old case/state、旧 HC flight、
  m266 lineage、专用 owner 单调 serial、distinct new case 与自产 receipt/hash；`committed=1` 是 source 最后业务写。
  exact replay 不增 serial、不重签，碰撞只写诊断且不覆盖 source。
- Workforce adapter 成功前 `m275_hold_pending=1`、旧 candidate inactive、旧 owner HC flight 不变；成功后才一次性激活
  runner-up、把 `candidate_active_case` 和 owner flight 切到新案并清两个 pending。`m266_hc_receipt` 与 reserved 数量保持
  原值，不重跑 #266、不 reserve/release HC。Central 只在下一帧核对完整 durable result 后消费 source；中断重入只修复
  未完成的 consume/verify。route B 仍只走 remediation release，route C 只退役 source/debt，二者都不调用本 producer。
- 新一轮 B1 公示若撞上旧中央案，会先把旧 immutable tuple 记为 typed RED，给旧摘要 D+1 ACK 窗口，再在 D+2 精确初始化新案；禁止原地覆盖或清掉旧摘要。
- P3、Credit/Project 与 Workforce 的 D+1 域切换空档只轮询同一 portfolio tuple，不会误判 RED。
- 3.25 state 1/2 以及 Workforce status 5 都记录 external wait，绝不伪装 success。manager 的 status 5 会先调用
  `zg361_b2_submit_completed_al_receipts_effect`：它只读取 B1 #357 与 B2 #358/#359 已由真实 consumer 发布的来源票据，中央不能
  传入 receipt ID/hash；strict bridge 验证成功后才准备 route-neutral source。只有 READY 才调用新的 gated resume seam；
  WAIT 不弹窗，structural N/A 调用不造 collective 的 manager N/A close seam，RED 不再 resume。
- `zg361_we_portfolio_status=8` 必须同时带 history-accruing、39 owned operations、skipped-charter、success=0、守恒和
  closed AL state 8；中央把它当合法完成推进，而不是误落 `RED 1161`。
- 最终每名玩家 manager 只收到一张中央聚合摘要；AI 不收到中央可见事件。

## 5. 已知外部依赖

- Workforce 357–359 的 B1/B2 真实来源、产品 adapter 与中央调用已经接线；但同案 receipt 尚未到达（例如没有已裁决申诉、
  翻案后尚未完成配额回流，或走 policy route C）时，本中央案仍会诚实停在 stage 11/status 5，不会生成完成标记。
- Central 已冻结 `zg361_p2c_m360_source_*` route-neutral ABI，并引用两个同批 Workforce public ABI：
  `zg361_we_resume_m360_from_central_source_effect` 与 `zg361_we_finalize_manager_collective_na_effect`。它们必须由 Workforce
  生成器在同一集成批次实现后，本候选树才可称为可加载；旧 opener 不得承担 #360 READY resume，以免提前弹玩家事件。
- Workforce runtime 的初始 AB/AC/AD 必须允许普通 assessed count/baron；只有 #360/#361 resume 才可追加 manager 条件。中央层已经按此权限合同调用 public seam，但不修改该并发领域文件。
- 普通 count/baron 的 N/A-close seam 必须冻结 `terminal_na=1/reason=360361/owned_operations=38/skipped_manager_only=2/success=0`、`final_conservation_ok=1`、清 AL active 并写 closed=1/status=7；中央据此把 stage 11 记为 N/A。旧 runtime 若没有该 seam，中央仍以 `terminal_state=5` 外部阻点暂停：不调用无权限 ABI、不写 completed-cycle、不伪造 Workforce success，也不每两日永久重试。
- 所有结论目前只是生成可复现、静态语法/结构测试证据；尚未经过 MCP-first CK3 paused snapshot、存读档或多轮实机验收。

## 6. 测试口径

`tools/test_zg361_phase2_central_runtime.py` 静态证明：两处 hook 顺序、M013 proof 互斥、D+2 初始化、exact 3.25 wake、
单 opener、PP/Incident 顺序、权限边界、stale ticket、CP N/A、CL digest、MG strict lag、#360 frozen-order 组合、
B1 diagnostic WAIT/N/A/RED、B1+MG exact source、READY-only gated resume、manager structural-N/A、status 8 history terminal、
AI/玩家共同业务路径、#275-A 三帧 distinct requisition/receipt/hash 与 HC 守恒、BOM 与生成可复现。它不构成
fixture-live 或 production-live 证据。
"""


def outputs() -> dict[Path, str]:
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / filename: content
        for filename, content in render_effect_parts().items()
    }
    rendered.update({
        MOD_ROOT / "common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt": render_m360_triggers(),
        MOD_ROOT / "events/zg361_phase2_central_runtime_events.txt": render_events(),
        MOD_ROOT / "docs/361-phase2-central-runtime-spec.md": render_spec(),
    })
    for language, header in LANGUAGES:
        rendered[MOD_ROOT / f"localization/{language}/zg361_phase2_central_l_{language}.yml"] = render_localization(language, header)
    return rendered


def unexpected_effect_paths(rendered: dict[Path, str]) -> tuple[Path, ...]:
    """Return legacy or stale central effect projections on disk."""

    effects_dir = MOD_ROOT / "common" / "scripted_effects"
    expected = {path for path in rendered if path.parent == effects_dir}
    unexpected = set(effects_dir.glob(EFFECT_SHARD_GLOB)) - expected
    if LEGACY_EFFECT_PATH.is_file():
        unexpected.add(LEGACY_EFFECT_PATH)
    return tuple(sorted(unexpected))


def write_or_check(check: bool) -> int:
    rendered = outputs()
    stale: list[str] = []
    for path, content in rendered.items():
        payload = BOM + content.replace("\r\n", "\n").encode("utf-8")
        if check:
            if not path.exists() or path.read_bytes() != payload:
                stale.append(path.relative_to(MOD_ROOT).as_posix())
    unexpected = unexpected_effect_paths(rendered)
    if check and (stale or unexpected):
        print("stale generated phase-two central files:")
        for item in stale:
            print(f"  {item}")
        for path in unexpected:
            print(f"  unexpected effect projection: {path.relative_to(MOD_ROOT).as_posix()}")
        return 1
    if not check:
        for path in unexpected:
            path.unlink()
        for path, content in rendered.items():
            payload = BOM + content.replace("\r\n", "\n").encode("utf-8")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_or_check(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
