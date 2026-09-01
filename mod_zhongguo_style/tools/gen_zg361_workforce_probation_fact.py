#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the isolated Workforce #269 probation/PIP fact producer.

The package does not invent a hire outcome.  A real #274 hire arms the active
projection of a bounded three-generation subject ledger.  Before a later real
hire reuses that compatibility ABI, a fully consumed tombstone is copied into
one of two append-only archive slots.  A later, settled result may publish a
pass, while a 3.25 result can only freeze the evidence and wait for B2's unique
D+365 PIP settlement.  The twelve legacy Workforce aliases exist only while
the strict #269 consumer is being called; canonical source and consumption
receipts remain under this package's prefix.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
PREFIX = "zg361_workforce_probation_fact"
WORKFORCE_PREFIX = "zg361_we"
READINESS = "ck3-script-static-ready-not-live"
HEADER = f"# GENERATED FILE — edit tools/gen_{PREFIX}.py\n"
LEDGER_CAPACITY = 3
LEDGER_ARCHIVE_SLOTS = (1, 2)

# The unsuffixed names remain the active compatibility projection consumed by
# B2, attribution and rehire.  Before that projection is reused, every
# provenance-bearing field is copied to the next append-only archive slot.
# Together the two immutable archives plus the active projection form the
# minimal three-generation ledger needed for old owner -> different owner ->
# old owner #276.
LEDGER_ENTRY_FIELDS = (
    "owner",
    "subject",
    "hire_cycle",
    "hire_case",
    "probation_due_cycle",
    "position_receipt_id",
    "position_receipt_hash",
    "arm_receipt_id",
    "arm_receipt_hash",
    "state",
    "source_result_owner",
    "source_result_subject",
    "source_result_cycle",
    "source_result_case",
    "source_result_state",
    "source_result_settlement_receipt",
    "source_result_grade",
    "source_result_reason",
    "source_result_kpi",
    "source_result_rank",
    "outcome_dimension_1",
    "outcome_dimension_2",
    "outcome_dimension_3",
    "attribution_bps_1",
    "attribution_bps_2",
    "attribution_bps_3",
    "attribution_receipt_id",
    "attribution_receipt_hash",
    "awaiting_pip",
    "source_kind",
    "source_pip_owner",
    "source_pip_subject",
    "source_pip_cycle",
    "source_pip_case",
    "source_pip_state",
    "source_pip_policy_route",
    "source_pip_task_kind",
    "source_pip_settlement_receipt",
    "source_pip_outcome_code",
    "source_pip_result_cycle",
    "source_pip_result_case",
    "source_pip_result_grade",
    "source_pip_case_receipt_id",
    "source_pip_case_receipt_hash",
    "source_pip_closure_receipt_id",
    "source_pip_closure_receipt_hash",
    "source_external_owner",
    "source_external_subject",
    "source_external_cycle",
    "source_external_case",
    "source_external_state",
    "source_external_receipt_id",
    "source_external_receipt_hash",
    "source_external_reason",
    "source_external_former_slot_id",
    "source_external_slot_hash",
    "source_external_position_type_id",
    "source_external_appointment_receipt_id",
    "source_external_appointment_receipt_hash",
    "source_external_native_end_reason",
    "source_external_hc_conservation_verified",
    "outcome_quality",
    "outcome_evidence_count",
    "outcome_evidence_id",
    "outcome_evidence_hash",
    "outcome_observed_cycle",
    "outcome_exclusion_reason",
    "outcome_id",
    "outcome_receipt_hash",
    "published",
    "consumed",
    "legacy_aliases_materialized",
    "retry_pending",
    "consume_receipt_id",
    "consume_receipt_hash",
    "consume_owner",
    "consume_subject",
    "consume_hire_cycle",
    "consume_hire_case",
    "consume_result_cycle",
    "consume_result_case",
    "consume_outcome_id",
    "consume_workforce_choice",
    "consume_workforce_case",
)

LEDGER_ARM_IDENTITY_FIELDS = (
    "owner",
    "subject",
    "hire_cycle",
    "hire_case",
    "probation_due_cycle",
    "position_receipt_id",
    "position_receipt_hash",
    "arm_receipt_id",
    "arm_receipt_hash",
)

LEDGER_TOMBSTONE_REQUIRED_FIELDS = (
    *LEDGER_ARM_IDENTITY_FIELDS,
    "source_result_owner",
    "source_result_subject",
    "source_result_cycle",
    "source_result_case",
    "source_result_state",
    "source_result_settlement_receipt",
    "source_result_grade",
    "source_result_reason",
    "source_result_kpi",
    "source_result_rank",
    "source_kind",
    "outcome_quality",
    "outcome_exclusion_reason",
    "outcome_id",
    "outcome_receipt_hash",
    "outcome_evidence_id",
    "outcome_evidence_hash",
    "consume_receipt_id",
    "consume_receipt_hash",
    "consume_owner",
    "consume_subject",
    "consume_hire_cycle",
    "consume_hire_case",
    "consume_result_cycle",
    "consume_result_case",
    "consume_outcome_id",
    "consume_workforce_choice",
    "consume_workforce_case",
)

LANGUAGES = (
    "english",
    "simp_chinese",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)

LEGACY_ALIAS_TO_FACT = {
    "attribution_bps_2": "attribution_bps_2",
    "attribution_bps_3": "attribution_bps_3",
    "outcome_dimension_1": "outcome_dimension_1",
    "outcome_dimension_2": "outcome_dimension_2",
    "outcome_dimension_3": "outcome_dimension_3",
    "outcome_evidence_count": "outcome_evidence_count",
    "outcome_evidence_hash": "outcome_evidence_hash",
    "outcome_evidence_id": "outcome_evidence_id",
    "outcome_exclusion_reason": "outcome_exclusion_reason",
    "outcome_id": "outcome_id",
    "outcome_observed_cycle": "outcome_observed_cycle",
    "outcome_quality": "outcome_quality",
}


def clean(text: str) -> str:
    """Normalize indentation while keeping generated CK3 source stable."""

    return "\n".join(line.rstrip() for line in textwrap.dedent(text).strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def validate_contract() -> None:
    expected = {
        "attribution_bps_2",
        "attribution_bps_3",
        "outcome_dimension_1",
        "outcome_dimension_2",
        "outcome_dimension_3",
        "outcome_evidence_count",
        "outcome_evidence_hash",
        "outcome_evidence_id",
        "outcome_exclusion_reason",
        "outcome_id",
        "outcome_observed_cycle",
        "outcome_quality",
    }
    if set(LEGACY_ALIAS_TO_FACT) != expected:
        raise ValueError("probation producer must own exactly the 12 frozen aliases")
    if len(LEGACY_ALIAS_TO_FACT) != 12:
        raise ValueError("probation alias count drifted")
    if tuple(LANGUAGES[:2]) != ("english", "simp_chinese") or len(LANGUAGES) != 9:
        raise ValueError("daily localization contract must keep zh/en plus seven placeholders")
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("static package must not claim live readiness")
    if LEDGER_CAPACITY != 3 or LEDGER_ARCHIVE_SLOTS != (1, 2):
        raise ValueError("probation ledger must remain active + two immutable archives")
    if len(LEDGER_ENTRY_FIELDS) != len(set(LEDGER_ENTRY_FIELDS)):
        raise ValueError("probation ledger fields must be unique")
    if not set(LEDGER_ARM_IDENTITY_FIELDS) < set(LEDGER_ENTRY_FIELDS):
        raise ValueError("arm identity must be a strict subset of archived provenance")
    if not set(LEDGER_TOMBSTONE_REQUIRED_FIELDS) <= set(LEDGER_ENTRY_FIELDS):
        raise ValueError("tombstone requirements must all be archived")


def _alias_fragments() -> dict[str, str]:
    set_lines = []
    clear_lines = []
    missing_lines = []
    exact_lines = []
    for alias, fact in LEGACY_ALIAS_TO_FACT.items():
        legacy = f"{WORKFORCE_PREFIX}_ad_external_{alias}"
        canonical = f"{PREFIX}_{fact}"
        set_lines.append(f"set_variable = {{ name = {legacy} value = var:{canonical} }}")
        clear_lines.append(f"remove_variable = {legacy}")
        missing_lines.append(f"has_variable = {legacy}")
        exact_lines.extend(
            (
                f"has_variable = {legacy}",
                f"var:{legacy} = var:{canonical}",
            )
        )
    return {
        "ALIAS_SET": "\n".join(" " * 8 + line for line in set_lines),
        "ALIAS_CLEAR": "\n".join(" " * 8 + line for line in clear_lines),
        "ALIAS_MISSING": "\n".join(" " * 20 + line for line in missing_lines),
        "ALIAS_EXACT": "\n".join(" " * 16 + line for line in exact_lines),
    }


def _ledger_name(slot: int, field: str) -> str:
    return f"{PREFIX}_ledger_slot_{slot}_{field}"


def _ledger_arm_rhs(field: str) -> str:
    mapping = {
        "owner": f"scope:{PREFIX}_arm_owner_scope",
        "subject": "this",
        "hire_cycle": f"var:{WORKFORCE_PREFIX}_m274_write_cycle",
        "hire_case": f"var:{WORKFORCE_PREFIX}_m274_write_case",
        "probation_due_cycle": f"var:{WORKFORCE_PREFIX}_m274_probation_due_cycle",
        "position_receipt_id": f"var:{WORKFORCE_PREFIX}_m274_position_receipt_id",
        "position_receipt_hash": f"var:{WORKFORCE_PREFIX}_m274_position_receipt_hash",
        "arm_receipt_id": f"scope:{PREFIX}_expected_arm_receipt_id",
        "arm_receipt_hash": f"scope:{PREFIX}_expected_arm_receipt_hash",
    }
    return mapping[field]


def _ledger_exact_guard(slot: int | None, indent: int) -> str:
    lines: list[str] = []
    if slot is not None:
        lines.extend(
            (
                f"has_variable = {PREFIX}_ledger_slot_{slot}_active",
                f"var:{PREFIX}_ledger_slot_{slot}_active = 1",
            )
        )
    for field in LEDGER_ARM_IDENTITY_FIELDS:
        name = f"{PREFIX}_{field}" if slot is None else _ledger_name(slot, field)
        lines.extend((f"has_variable = {name}", f"var:{name} = {_ledger_arm_rhs(field)}"))
    return "\n".join(" " * indent + line for line in lines)


def _ledger_logical_guard(slot: int | None, indent: int) -> str:
    lines: list[str] = []
    if slot is not None:
        lines.extend(
            (
                f"has_variable = {PREFIX}_ledger_slot_{slot}_active",
                f"var:{PREFIX}_ledger_slot_{slot}_active = 1",
            )
        )
    for field in ("owner", "subject", "hire_cycle", "hire_case"):
        name = f"{PREFIX}_{field}" if slot is None else _ledger_name(slot, field)
        lines.extend((f"has_variable = {name}", f"var:{name} = {_ledger_arm_rhs(field)}"))
    return "\n".join(" " * indent + line for line in lines)


def _ledger_slot_empty_guard(slot: int, indent: int) -> str:
    names = [
        f"{PREFIX}_ledger_slot_{slot}_active",
        f"{PREFIX}_ledger_slot_{slot}_generation",
        f"{PREFIX}_ledger_slot_{slot}_archive_receipt_id",
        f"{PREFIX}_ledger_slot_{slot}_archive_receipt_hash",
    ]
    lines = ["NOT = {", "    OR = {"]
    lines.extend(f"        has_variable = {name}" for name in names)
    lines.extend(("    }", "}"))
    return "\n".join(" " * indent + line for line in lines)


def _ledger_current_tombstone_guard(indent: int) -> str:
    lines = [
        f"has_variable = {PREFIX}_state",
        f"has_variable = {PREFIX}_published",
        f"has_variable = {PREFIX}_consumed",
        f"var:{PREFIX}_state = 4",
        f"var:{PREFIX}_published = 1",
        f"var:{PREFIX}_consumed = 1",
    ]
    for field in LEDGER_TOMBSTONE_REQUIRED_FIELDS:
        lines.append(f"has_variable = {PREFIX}_{field}")
    lines.extend(
        (
            "trigger_if = {",
            f"    limit = {{ OR = {{ var:{PREFIX}_source_kind = 3 var:{PREFIX}_source_kind = 4 }} }}",
            *(
                f"    has_variable = {PREFIX}_{field}"
                for field in (
                    "source_external_owner",
                    "source_external_subject",
                    "source_external_cycle",
                    "source_external_case",
                    "source_external_state",
                    "source_external_receipt_id",
                    "source_external_receipt_hash",
                    "source_external_reason",
                    "source_external_former_slot_id",
                    "source_external_slot_hash",
                    "source_external_position_type_id",
                    "source_external_appointment_receipt_id",
                    "source_external_appointment_receipt_hash",
                    "source_external_native_end_reason",
                    "source_external_hc_conservation_verified",
                )
            ),
            "}",
            "trigger_else = {",
            f"    OR = {{ var:{PREFIX}_source_kind = 1 var:{PREFIX}_source_kind = 2 }}",
            "}",
        )
    )
    return "\n".join(" " * indent + line for line in lines)


def _ledger_copy_lines(slot: int, indent: int) -> str:
    lines: list[str] = []
    for field in LEDGER_ENTRY_FIELDS:
        lines.append(
            f"if = {{ limit = {{ has_variable = {PREFIX}_{field} }} "
            f"set_variable = {{ name = {_ledger_name(slot, field)} "
            f"value = var:{PREFIX}_{field} }} }}"
        )
    return "\n".join(" " * indent + line for line in lines)


def _ledger_clear_current_lines(indent: int) -> str:
    lines = [f"remove_variable = {PREFIX}_{field}" for field in LEDGER_ENTRY_FIELDS]
    lines.append(f"remove_variable = {PREFIX}_notice_seen")
    return "\n".join(" " * indent + line for line in lines)


def _ledger_replay_branches(indent: int) -> str:
    branches: list[str] = []
    pad = " " * indent
    for slot in LEDGER_ARCHIVE_SLOTS:
        exact = _ledger_exact_guard(slot, indent + 8)
        branches.append(
            f"{pad}else_if = {{\n"
            f"{pad}    limit = {{\n{exact}\n"
            f"{pad}        NOT = {{ has_variable = {PREFIX}_ledger_arm_red_code }}\n"
            f"{pad}    }}\n"
            f"{pad}    set_variable = {{ name = {PREFIX}_ledger_replay_generation value = var:{PREFIX}_ledger_slot_{slot}_generation }}\n"
            f"{pad}    set_variable = {{ name = {PREFIX}_adapter_status value = 2 }} # exact archived arm replay\n"
            f"{pad}}}"
        )
    return "\n".join(branches)


def _ledger_fragments() -> dict[str, str]:
    any_exact = []
    any_logical = []
    for slot in (None, *LEDGER_ARCHIVE_SLOTS):
        any_exact.append(
            " " * 12
            + "AND = {\n"
            + _ledger_exact_guard(slot, 16)
            + "\n"
            + " " * 12
            + "}"
        )
        any_logical.append(
            " " * 12
            + "AND = {\n"
            + _ledger_logical_guard(slot, 16)
            + "\n"
            + " " * 12
            + "}"
        )
    all_slot_names = []
    for slot in LEDGER_ARCHIVE_SLOTS:
        all_slot_names.extend(
            (
                f"{PREFIX}_ledger_slot_{slot}_active",
                f"{PREFIX}_ledger_slot_{slot}_generation",
                f"{PREFIX}_ledger_slot_{slot}_archive_receipt_id",
                f"{PREFIX}_ledger_slot_{slot}_archive_receipt_hash",
            )
        )
    no_ledger_metadata = [
        f"has_variable = {PREFIX}_ledger_version",
        f"has_variable = {PREFIX}_ledger_capacity",
        f"has_variable = {PREFIX}_ledger_generation",
        f"has_variable = {PREFIX}_ledger_entry_count",
        f"has_variable = {PREFIX}_ledger_current_generation",
        *(f"has_variable = {name}" for name in all_slot_names),
    ]
    return {
        "CURRENT_EXACT": _ledger_exact_guard(None, 16),
        "ARCHIVE_REPLAY_BRANCHES": _ledger_replay_branches(4),
        "ANY_EXACT": "\n".join(any_exact),
        "ANY_LOGICAL": "\n".join(any_logical),
        "SLOT_1_EMPTY": _ledger_slot_empty_guard(1, 16),
        "SLOT_2_EMPTY": _ledger_slot_empty_guard(2, 16),
        "SLOT_1_EMPTY_20": _ledger_slot_empty_guard(1, 20),
        "SLOT_2_EMPTY_20": _ledger_slot_empty_guard(2, 20),
        "CURRENT_TOMBSTONE": _ledger_current_tombstone_guard(12),
        "CURRENT_TOMBSTONE_16": _ledger_current_tombstone_guard(16),
        "SLOT_1_COPY": _ledger_copy_lines(1, 8),
        "SLOT_2_COPY": _ledger_copy_lines(2, 8),
        "CURRENT_CLEAR": _ledger_clear_current_lines(4),
        "NO_LEDGER_METADATA": "\n".join(
            " " * 16 + line for line in no_ledger_metadata
        ),
    }


def render_effects() -> bytes:
    fragments = _alias_fragments()
    fragments.update(_ledger_fragments())
    template = r'''
    # ZhongGuo 361 Workforce probation/PIP outcome fact producer for #269.
    # Scope ABI for all public hooks:
    #   current scope (this) = the real hired subject; $OWNER$ = the real #274 owner.
    #   ROOT is deliberately ignored and conveys no authority or identity.
    # Result hook additionally requires actual attribution bps from the caller;
    # the three dimensions are copied from #267's sealed vote-evidence receipts.

    # Persistent subject ledger metadata.  Legacy single-slot saves are adopted
    # as generation 1 without changing their receipt.  New saves start empty.
    # Any partial or contradictory metadata is a typed collision, not repaired.
    @P@_ensure_ledger_metadata_effect = {
        remove_variable = @P@_ledger_metadata_status
        if = {
            limit = {
                NOT = {
                    OR = {
    @NO_LEDGER_METADATA@
                    }
                }
            }
            set_variable = { name = @P@_ledger_version value = 1 }
            set_variable = { name = @P@_ledger_capacity value = 3 }
            if = {
                limit = { has_variable = @P@_state var:@P@_state >= 1 }
                set_variable = { name = @P@_ledger_generation value = 1 }
                set_variable = { name = @P@_ledger_entry_count value = 1 }
                set_variable = { name = @P@_ledger_current_generation value = 1 }
            }
            else = {
                set_variable = { name = @P@_ledger_generation value = 0 }
                set_variable = { name = @P@_ledger_entry_count value = 0 }
                set_variable = { name = @P@_ledger_current_generation value = 0 }
            }
            set_variable = { name = @P@_ledger_metadata_status value = 1 }
        }
        else_if = {
            limit = {
                var:@P@_ledger_version = 1
                var:@P@_ledger_capacity = 3
                OR = {
                    AND = {
                        var:@P@_ledger_generation = 0
                        var:@P@_ledger_entry_count = 0
                        var:@P@_ledger_current_generation = 0
                        OR = { NOT = { has_variable = @P@_state } var:@P@_state = 0 }
    @SLOT_1_EMPTY_20@
    @SLOT_2_EMPTY_20@
                    }
                    AND = {
                        var:@P@_ledger_generation = 1
                        var:@P@_ledger_entry_count = 1
                        var:@P@_ledger_current_generation = 1
                        var:@P@_state >= 1
    @SLOT_1_EMPTY_20@
    @SLOT_2_EMPTY_20@
                    }
                    AND = {
                        var:@P@_ledger_generation = 2
                        var:@P@_ledger_entry_count = 2
                        var:@P@_ledger_current_generation = 2
                        var:@P@_state >= 1
                        var:@P@_ledger_slot_1_active = 1
                        var:@P@_ledger_slot_1_generation = 1
    @SLOT_2_EMPTY_20@
                    }
                    AND = {
                        var:@P@_ledger_generation = 3
                        var:@P@_ledger_entry_count = 3
                        var:@P@_ledger_current_generation = 3
                        var:@P@_state >= 1
                        var:@P@_ledger_slot_1_active = 1
                        var:@P@_ledger_slot_1_generation = 1
                        var:@P@_ledger_slot_2_active = 1
                        var:@P@_ledger_slot_2_generation = 2
                    }
                }
            }
            set_variable = { name = @P@_ledger_metadata_status value = 1 }
        }
        else = {
            set_variable = { name = @P@_ledger_metadata_status value = 5 }
            set_variable = { name = @P@_ledger_arm_red_code value = 1005 }
        }
    }

    # Archive slots are append-only.  active=1 is written last, so a persisted
    # slot always carries the full old owner/subject/cycle/case and all source,
    # outcome and consume receipt identities that existed on the tombstone.
    @P@_archive_current_to_slot_1_effect = {
        remove_variable = @P@_ledger_archive_status
        if = {
            limit = {
                var:@P@_ledger_version = 1
                var:@P@_ledger_capacity = 3
                var:@P@_ledger_generation = 1
                var:@P@_ledger_entry_count = 1
                var:@P@_ledger_current_generation = 1
    @CURRENT_TOMBSTONE_16@
    @SLOT_1_EMPTY@
            }
    @SLOT_1_COPY@
            set_variable = { name = @P@_ledger_slot_1_generation value = var:@P@_ledger_current_generation }
            set_variable = { name = @P@_ledger_slot_1_archive_receipt_id value = var:@P@_ledger_current_generation }
            set_variable = {
                name = @P@_ledger_slot_1_archive_receipt_hash
                value = {
                    value = var:@P@_arm_receipt_hash
                    add = var:@P@_outcome_receipt_hash
                    add = var:@P@_consume_receipt_hash
                    add = var:@P@_ledger_current_generation
                }
            }
            set_variable = { name = @P@_ledger_slot_1_active value = 1 } # commit last
            set_variable = { name = @P@_ledger_archive_status value = 1 }
        }
        else = {
            set_variable = { name = @P@_ledger_archive_status value = 5 }
            set_variable = { name = @P@_ledger_arm_red_code value = 1005 }
        }
    }

    @P@_archive_current_to_slot_2_effect = {
        remove_variable = @P@_ledger_archive_status
        if = {
            limit = {
                var:@P@_ledger_version = 1
                var:@P@_ledger_capacity = 3
                var:@P@_ledger_generation = 2
                var:@P@_ledger_entry_count = 2
                var:@P@_ledger_current_generation = 2
                var:@P@_ledger_slot_1_active = 1
                var:@P@_ledger_slot_1_generation = 1
    @CURRENT_TOMBSTONE_16@
    @SLOT_2_EMPTY@
            }
    @SLOT_2_COPY@
            set_variable = { name = @P@_ledger_slot_2_generation value = var:@P@_ledger_current_generation }
            set_variable = { name = @P@_ledger_slot_2_archive_receipt_id value = var:@P@_ledger_current_generation }
            set_variable = {
                name = @P@_ledger_slot_2_archive_receipt_hash
                value = {
                    value = var:@P@_arm_receipt_hash
                    add = var:@P@_outcome_receipt_hash
                    add = var:@P@_consume_receipt_hash
                    add = var:@P@_ledger_current_generation
                }
            }
            set_variable = { name = @P@_ledger_slot_2_active value = 1 } # commit last
            set_variable = { name = @P@_ledger_archive_status value = 1 }
        }
        else = {
            set_variable = { name = @P@_ledger_archive_status value = 5 }
            set_variable = { name = @P@_ledger_arm_red_code value = 1005 }
        }
    }

    # Only the active compatibility projection is retired after its complete
    # tombstone was appended.  No ledger_slot_* variable is ever removed.
    @P@_retire_current_projection_effect = {
    @CURRENT_CLEAR@
    }

    # Decide whether #274 is an initial append, an exact replay, a collision,
    # or the second/third bounded generation.  The fourth distinct generation
    # is explicitly RED 1003 instead of overwriting an immutable archive.
    @P@_prepare_ledger_arm_effect = {
        remove_variable = @P@_ledger_arm_append_pending
        remove_variable = @P@_ledger_arm_red_code
        remove_variable = @P@_ledger_arm_archived_slot
        remove_variable = @P@_ledger_replay_generation
        if = {
            limit = {
                scope:@P@_arm_subject_scope = { is_alive = yes }
                scope:@P@_arm_owner_scope = {
                    is_alive = yes
                    is_landed = yes
                    zg361_is_celestial_liege_trigger = yes
                }
                has_variable = @W@_m274_write_owner
                has_variable = @W@_m274_write_subject
                has_variable = @W@_m274_write_cycle
                has_variable = @W@_m274_write_case
                has_variable = @W@_m274_write_state
                has_variable = @W@_m274_hired
                has_variable = @W@_m274_hire_case
                has_variable = @W@_m274_probation_due_cycle
                has_variable = @W@_m274_native_appointment_confirmed
                has_variable = @W@_m274_position_receipt_id
                has_variable = @W@_m274_position_receipt_hash
                var:@W@_m274_write_owner = scope:@P@_arm_owner_scope
                var:@W@_m274_write_subject = this
                var:@W@_m274_write_state = 4
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = var:@W@_m274_write_case
                var:@W@_m274_probation_due_cycle > var:@W@_m274_write_cycle
                var:@W@_m274_native_appointment_confirmed = 1
                var:@W@_m274_position_receipt_id > 0
                var:@W@_m274_position_receipt_hash > 0
            }
            @P@_ensure_ledger_metadata_effect = yes
            if = {
                limit = { NOT = { var:@P@_ledger_metadata_status = 1 } }
                set_variable = { name = @P@_ledger_arm_red_code value = 1005 }
            }
            else_if = {
                limit = {
                    OR = {
    @ANY_EXACT@
                    }
                }
                set_variable = { name = @P@_ledger_arm_append_pending value = 0 }
            }
            else_if = {
                limit = {
                    OR = {
    @ANY_LOGICAL@
                    }
                }
                set_variable = { name = @P@_ledger_arm_red_code value = 1002 }
            }
            else_if = {
                limit = {
                    var:@P@_ledger_generation = 0
                    var:@P@_ledger_entry_count = 0
                    var:@P@_ledger_current_generation = 0
                    OR = { NOT = { has_variable = @P@_state } var:@P@_state = 0 }
    @SLOT_1_EMPTY@
    @SLOT_2_EMPTY@
                }
                set_variable = { name = @P@_ledger_arm_append_pending value = 1 }
            }
            else_if = {
                limit = {
                    var:@P@_ledger_generation = 1
                    var:@P@_ledger_entry_count = 1
                    var:@P@_ledger_current_generation = 1
    @CURRENT_TOMBSTONE@
    @SLOT_1_EMPTY@
                }
                @P@_archive_current_to_slot_1_effect = yes
                if = {
                    limit = { var:@P@_ledger_archive_status = 1 }
                    @P@_retire_current_projection_effect = yes
                    set_variable = { name = @P@_ledger_arm_archived_slot value = 1 }
                    set_variable = { name = @P@_ledger_arm_append_pending value = 1 }
                }
                else = { set_variable = { name = @P@_ledger_arm_red_code value = 1005 } }
            }
            else_if = {
                limit = {
                    var:@P@_ledger_generation = 2
                    var:@P@_ledger_entry_count = 2
                    var:@P@_ledger_current_generation = 2
                    var:@P@_ledger_slot_1_active = 1
                    var:@P@_ledger_slot_1_generation = 1
    @CURRENT_TOMBSTONE@
    @SLOT_2_EMPTY@
                }
                @P@_archive_current_to_slot_2_effect = yes
                if = {
                    limit = { var:@P@_ledger_archive_status = 1 }
                    @P@_retire_current_projection_effect = yes
                    set_variable = { name = @P@_ledger_arm_archived_slot value = 2 }
                    set_variable = { name = @P@_ledger_arm_append_pending value = 1 }
                }
                else = { set_variable = { name = @P@_ledger_arm_red_code value = 1005 } }
            }
            else_if = {
                limit = {
                    var:@P@_ledger_generation >= 3
                    var:@P@_ledger_entry_count >= 3
    @CURRENT_TOMBSTONE@
                }
                set_variable = { name = @P@_ledger_arm_red_code value = 1003 }
            }
            else = { set_variable = { name = @P@_ledger_arm_red_code value = 1004 } }
        }
        else = { set_variable = { name = @P@_ledger_arm_red_code value = 1001 } }
    }

    @P@_arm_hire_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_arm_subject_scope
        $OWNER$ = { save_temporary_scope_as = @P@_arm_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_expected_arm_receipt_id
            value = { value = var:@W@_m274_write_case multiply = 1000 add = 274 }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_arm_receipt_hash
            value = {
                value = var:@W@_m274_position_receipt_hash
                add = { value = var:@W@_m274_write_cycle multiply = 1000 }
                add = var:@W@_m274_write_case
                add = 274
            }
        }
        @P@_prepare_ledger_arm_effect = yes
        if = {
            limit = {
                scope:@P@_arm_subject_scope = { is_alive = yes }
                scope:@P@_arm_owner_scope = {
                    is_alive = yes
                    is_landed = yes
                    zg361_is_celestial_liege_trigger = yes
                }
                has_variable = @W@_m274_write_owner
                has_variable = @W@_m274_write_subject
                has_variable = @W@_m274_write_cycle
                has_variable = @W@_m274_write_case
                has_variable = @W@_m274_write_state
                has_variable = @W@_m274_hired
                has_variable = @W@_m274_hire_case
                has_variable = @W@_m274_probation_due_cycle
                has_variable = @W@_m274_native_appointment_confirmed
                has_variable = @W@_m274_position_receipt_id
                has_variable = @W@_m274_position_receipt_hash
                var:@W@_m274_write_owner = scope:@P@_arm_owner_scope
                var:@W@_m274_write_subject = this
                var:@W@_m274_write_state = 4
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = var:@W@_m274_write_case
                var:@W@_m274_probation_due_cycle > var:@W@_m274_write_cycle
                var:@W@_m274_native_appointment_confirmed = 1
                var:@W@_m274_position_receipt_id > 0
                var:@W@_m274_position_receipt_hash > 0
                var:@P@_ledger_arm_append_pending = 1
                var:@P@_ledger_version = 1
                var:@P@_ledger_capacity = 3
                OR = {
                    NOT = { has_variable = @P@_state }
                    var:@P@_state = 0
                }
            }
            set_variable = { name = @P@_owner value = scope:@P@_arm_owner_scope }
            set_variable = { name = @P@_subject value = this }
            set_variable = { name = @P@_hire_cycle value = var:@W@_m274_write_cycle }
            set_variable = { name = @P@_hire_case value = var:@W@_m274_write_case }
            set_variable = { name = @P@_probation_due_cycle value = var:@W@_m274_probation_due_cycle }
            set_variable = { name = @P@_position_receipt_id value = var:@W@_m274_position_receipt_id }
            set_variable = { name = @P@_position_receipt_hash value = var:@W@_m274_position_receipt_hash }
            set_variable = {
                name = @P@_arm_receipt_id
                value = { value = var:@W@_m274_write_case multiply = 1000 add = 274 }
            }
            set_variable = {
                name = @P@_arm_receipt_hash
                value = {
                    value = var:@W@_m274_position_receipt_hash
                    add = { value = var:@W@_m274_write_cycle multiply = 1000 }
                    add = var:@W@_m274_write_case
                    add = 274
                }
            }
            set_variable = { name = @P@_state value = 1 } # armed, no outcome yet
            change_variable = { name = @P@_ledger_generation add = 1 }
            change_variable = { name = @P@_ledger_entry_count add = 1 }
            set_variable = { name = @P@_ledger_current_generation value = var:@P@_ledger_generation }
            set_variable = { name = @P@_ledger_arm_append_pending value = 0 }
            set_variable = { name = @P@_adapter_status value = 1 }
            debug_log = "ZG361WPF: real m274 hire appended to bounded probation ledger"
        }
        else_if = {
            limit = {
                has_variable = @P@_state
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_hire_cycle
                has_variable = @P@_hire_case
                has_variable = @P@_probation_due_cycle
                has_variable = @P@_position_receipt_id
                has_variable = @P@_position_receipt_hash
                has_variable = @P@_arm_receipt_id
                has_variable = @P@_arm_receipt_hash
                NOT = { has_variable = @P@_ledger_arm_red_code }
                var:@P@_state >= 1
                var:@P@_owner = scope:@P@_arm_owner_scope
                var:@P@_subject = this
                var:@P@_hire_cycle = var:@W@_m274_write_cycle
                var:@P@_hire_case = var:@W@_m274_write_case
                var:@P@_probation_due_cycle = var:@W@_m274_probation_due_cycle
                var:@P@_position_receipt_id = var:@W@_m274_position_receipt_id
                var:@P@_position_receipt_hash = var:@W@_m274_position_receipt_hash
                var:@P@_arm_receipt_id = scope:@P@_expected_arm_receipt_id
                var:@P@_arm_receipt_hash = scope:@P@_expected_arm_receipt_hash
            }
            set_variable = { name = @P@_adapter_status value = 2 } # exact arm replay
        }
    @ARCHIVE_REPLAY_BRANCHES@
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            if = {
                limit = { has_variable = @P@_ledger_arm_red_code }
                set_variable = { name = @P@_red_code value = var:@P@_ledger_arm_red_code }
            }
            else = { set_variable = { name = @P@_red_code value = 1001 } }
            debug_log = "ZG361WPF RED: arm is invalid, stale, colliding, active, or beyond ledger capacity"
        }
    }

    # Pending hook 1.  Call immediately after the canonical result settlement
    # while current scope is the subject.  Idempotency key:
    # owner/subject + hire cycle/case + result cycle/case/state/settlement +
    # grade/reason/KPI/rank + three #267 evidence IDs + attribution bps.
    @P@_publish_from_result_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_result_subject_scope
        $OWNER$ = { save_temporary_scope_as = @P@_result_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_expected_attribution_bps_1
            value = {
                value = 10000
                subtract = $ATTRIBUTION_BPS_2$
                subtract = $ATTRIBUTION_BPS_3$
            }
        }
        if = {
            limit = {
                has_variable = @P@_state
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_source_result_owner
                has_variable = @P@_source_result_subject
                has_variable = @P@_source_result_cycle
                has_variable = @P@_source_result_case
                has_variable = @P@_source_result_state
                has_variable = @P@_source_result_settlement_receipt
                has_variable = @P@_source_result_grade
                has_variable = @P@_source_result_reason
                has_variable = @P@_source_result_kpi
                has_variable = @P@_source_result_rank
                has_variable = @P@_outcome_dimension_1
                has_variable = @P@_outcome_dimension_2
                has_variable = @P@_outcome_dimension_3
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
                var:@P@_state >= 2
                var:@P@_owner = scope:@P@_result_owner_scope
                var:@P@_subject = this
                var:@P@_source_result_owner = scope:@P@_result_owner_scope
                var:@P@_source_result_subject = this
                var:@P@_source_result_cycle = var:zg361_result_cycle_serial
                var:@P@_source_result_case = var:zg361_result_case_serial
                var:@P@_source_result_state = var:zg361_result_case_state
                var:@P@_source_result_settlement_receipt = var:zg361_result_settlement_posted_serial
                var:@P@_source_result_grade = var:zg361_result_grade
                var:@P@_source_result_reason = var:zg361_result_grade_reason
                var:@P@_source_result_kpi = var:zg361_result_kpi_frozen
                var:@P@_source_result_rank = var:zg361_result_rank_frozen
                var:@P@_outcome_dimension_1 = var:@W@_m267_vote_evidence_1
                var:@P@_outcome_dimension_2 = var:@W@_m267_vote_evidence_2
                var:@P@_outcome_dimension_3 = var:@W@_m267_vote_evidence_3
                var:@P@_attribution_bps_2 = $ATTRIBUTION_BPS_2$
                var:@P@_attribution_bps_3 = $ATTRIBUTION_BPS_3$
            }
            set_variable = { name = @P@_adapter_status value = 2 }
            if = {
                limit = { var:@P@_state = 3 }
                @P@_schedule_consume_effect = yes
            }
            else_if = {
                limit = { var:@P@_state = 4 }
                set_variable = { name = @P@_adapter_status value = 4 }
            }
        }
        else_if = {
            limit = {
                var:@P@_state = 1
                var:@P@_owner = scope:@P@_result_owner_scope
                var:@P@_subject = this
                has_variable = @P@_hire_cycle
                has_variable = @P@_hire_case
                has_variable = @P@_probation_due_cycle
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_settlement_posted_serial
                has_variable = zg361_result_grade
                has_variable = zg361_result_grade_reason
                has_variable = zg361_result_kpi_frozen
                has_variable = zg361_result_rank_frozen
                var:zg361_result_case_owner = scope:@P@_result_owner_scope
                var:zg361_result_cycle_serial >= var:@P@_probation_due_cycle
                var:zg361_result_cycle_serial > var:@P@_hire_cycle
                OR = {
                    var:zg361_result_case_state = 3
                    var:zg361_result_case_state = 5
                }
                var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
                var:zg361_result_case_serial > 0
                OR = {
                    var:zg361_result_grade = 1
                    var:zg361_result_grade = 2
                    var:zg361_result_grade = 3
                }
                scope:@P@_result_owner_scope = {
                    has_variable = zg361_review_serial
                    var:zg361_review_serial >= scope:@P@_result_subject_scope.var:zg361_result_cycle_serial
                }
                has_variable = @W@_m269_outcome_pending
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_write_owner = scope:@P@_result_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
                var:@W@_m274_hire_case = var:@P@_hire_case
                var:@W@_m267_candidate_frozen = this
                var:@W@_m267_raw_votes_frozen = 1
                has_variable = @W@_m267_interviewer_1
                has_variable = @W@_m267_interviewer_2
                has_variable = @W@_m267_interviewer_3
                NOT = { var:@W@_m267_interviewer_1 = var:@W@_m267_interviewer_2 }
                NOT = { var:@W@_m267_interviewer_1 = var:@W@_m267_interviewer_3 }
                NOT = { var:@W@_m267_interviewer_2 = var:@W@_m267_interviewer_3 }
                has_variable = @W@_m267_vote_evidence_1
                has_variable = @W@_m267_vote_evidence_2
                has_variable = @W@_m267_vote_evidence_3
                var:@W@_m267_vote_evidence_1 > 0
                var:@W@_m267_vote_evidence_2 > 0
                var:@W@_m267_vote_evidence_3 > 0
                NOT = { var:@W@_m267_vote_evidence_1 = var:@W@_m267_vote_evidence_2 }
                NOT = { var:@W@_m267_vote_evidence_1 = var:@W@_m267_vote_evidence_3 }
                NOT = { var:@W@_m267_vote_evidence_2 = var:@W@_m267_vote_evidence_3 }
                $ATTRIBUTION_BPS_2$ >= 0
                $ATTRIBUTION_BPS_3$ >= 0
                scope:@P@_expected_attribution_bps_1 >= 0
            }
            set_variable = { name = @P@_source_result_owner value = scope:@P@_result_owner_scope }
            set_variable = { name = @P@_source_result_subject value = this }
            set_variable = { name = @P@_source_result_cycle value = var:zg361_result_cycle_serial }
            set_variable = { name = @P@_source_result_case value = var:zg361_result_case_serial }
            set_variable = { name = @P@_source_result_state value = var:zg361_result_case_state }
            set_variable = { name = @P@_source_result_settlement_receipt value = var:zg361_result_settlement_posted_serial }
            set_variable = { name = @P@_source_result_grade value = var:zg361_result_grade }
            set_variable = { name = @P@_source_result_reason value = var:zg361_result_grade_reason }
            set_variable = { name = @P@_source_result_kpi value = var:zg361_result_kpi_frozen }
            set_variable = { name = @P@_source_result_rank value = var:zg361_result_rank_frozen }
            set_variable = { name = @P@_outcome_dimension_1 value = var:@W@_m267_vote_evidence_1 }
            set_variable = { name = @P@_outcome_dimension_2 value = var:@W@_m267_vote_evidence_2 }
            set_variable = { name = @P@_outcome_dimension_3 value = var:@W@_m267_vote_evidence_3 }
            set_variable = { name = @P@_attribution_bps_2 value = $ATTRIBUTION_BPS_2$ }
            set_variable = { name = @P@_attribution_bps_3 value = $ATTRIBUTION_BPS_3$ }
            set_variable = { name = @P@_attribution_bps_1 value = scope:@P@_expected_attribution_bps_1 }
            set_variable = {
                name = @P@_attribution_receipt_id
                value = { value = var:zg361_result_case_serial multiply = 1000 add = 269 }
            }
            set_variable = {
                name = @P@_attribution_receipt_hash
                value = {
                    value = var:@W@_m267_vote_evidence_1 multiply = 100000
                    add = { value = var:@W@_m267_vote_evidence_2 multiply = 1000 }
                    add = var:@W@_m267_vote_evidence_3
                    add = { value = $ATTRIBUTION_BPS_2$ multiply = 10 }
                    add = $ATTRIBUTION_BPS_3$
                }
            }
            if = {
                limit = { var:zg361_result_grade = 1 }
                set_variable = { name = @P@_awaiting_pip value = 1 }
                set_variable = { name = @P@_state value = 2 }
                set_variable = { name = @P@_adapter_status value = 3 }
                debug_log = "ZG361WPF: settled 3.25 frozen; real B2 PIP settlement is still required"
            }
            else = {
                set_variable = { name = @P@_source_kind value = 1 } # ordinary settled result
                set_variable = { name = @P@_outcome_quality value = 1 } # pass derived from grade 2/3
                set_variable = { name = @P@_outcome_evidence_count value = 1 }
                set_variable = { name = @P@_outcome_evidence_id value = var:zg361_result_settlement_posted_serial }
                set_variable = {
                    name = @P@_outcome_evidence_hash
                    value = {
                        value = var:zg361_result_case_serial multiply = 1000000
                        add = { value = var:zg361_result_cycle_serial multiply = 10000 }
                        add = { value = var:zg361_result_grade multiply = 1000 }
                        add = { value = var:zg361_result_grade_reason multiply = 10 }
                        add = 269
                    }
                }
                set_variable = { name = @P@_outcome_observed_cycle value = var:zg361_result_cycle_serial }
                set_variable = { name = @P@_outcome_exclusion_reason value = 0 } # typed not-excluded conclusion
                @P@_publish_canonical_effect = yes
            }
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 2001 }
            debug_log = "ZG361WPF RED 2001: result hook lacks exact hire/result/attribution provenance"
        }
    }

    # Pending hook 2.  Call immediately after B2 publishes its unique Workforce
    # PIP settlement, current scope still the subject.  Idempotency key:
    # frozen result key + B2 PIP five-tuple/route/task + settlement/outcome/result
    # tuple + exactly derived B2 case and closure receipt IDs/hashes.
    @P@_publish_from_pip_settlement_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_pip_subject_scope
        $OWNER$ = { save_temporary_scope_as = @P@_pip_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_case_receipt_id
            value = {
                value = var:zg361_b2_pip_case
                multiply = 1000
                add = 15
            }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_case_receipt_hash
            value = {
                value = var:zg361_b2_pip_case
                multiply = 100000
                add = { value = var:zg361_b2_pip_cycle multiply = 1000 }
                add = { value = var:zg361_b2_pip_policy_route multiply = 100 }
                add = { value = var:zg361_b2_pip_task_kind multiply = 10 }
                add = var:zg361_b2_pip_state
            }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_closure_receipt_id
            value = {
                value = var:zg361_b2_pip_settlement_receipt
                multiply = 1000
                add = 17
            }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_pip_closure_receipt_hash
            value = {
                value = scope:@P@_expected_pip_case_receipt_hash
                add = { value = var:zg361_b2_pip_outcome_result_case multiply = 100000 }
                add = { value = var:zg361_b2_pip_outcome_result_cycle multiply = 1000 }
                add = { value = var:zg361_b2_pip_outcome_code multiply = 100 }
                add = { value = var:zg361_b2_pip_state multiply = 10 }
                add = 17
            }
        }
        if = {
            limit = {
                var:@P@_state >= 3
                var:@P@_source_kind = 2
                var:@P@_owner = scope:@P@_pip_owner_scope
                var:@P@_subject = this
                var:@P@_source_pip_owner = scope:@P@_pip_owner_scope
                var:@P@_source_pip_subject = this
                var:@P@_source_pip_cycle = var:zg361_b2_pip_cycle
                var:@P@_source_pip_case = var:zg361_b2_pip_case
                var:@P@_source_pip_state = var:zg361_b2_pip_state
                var:@P@_source_pip_policy_route = var:zg361_b2_pip_policy_route
                var:@P@_source_pip_task_kind = var:zg361_b2_pip_task_kind
                var:@P@_source_pip_settlement_receipt = var:zg361_b2_pip_settlement_receipt
                var:@P@_source_pip_outcome_code = var:zg361_b2_pip_outcome_code
                var:@P@_source_pip_result_cycle = var:zg361_b2_pip_outcome_result_cycle
                var:@P@_source_pip_result_case = var:zg361_b2_pip_outcome_result_case
                var:@P@_source_pip_result_grade = var:zg361_b2_pip_outcome_result_grade
                var:@P@_source_pip_case_receipt_id = var:zg361_b2_workforce_pip_case_id
                var:@P@_source_pip_case_receipt_hash = var:zg361_b2_workforce_pip_case_hash
                var:@P@_source_pip_closure_receipt_id = var:zg361_b2_workforce_pip_closure_receipt_id
                var:@P@_source_pip_closure_receipt_hash = var:zg361_b2_workforce_pip_closure_receipt_hash
            }
            set_variable = { name = @P@_adapter_status value = 2 }
            if = {
                limit = { var:@P@_state = 3 }
                @P@_schedule_consume_effect = yes
            }
            else = { set_variable = { name = @P@_adapter_status value = 4 } }
        }
        else_if = {
            limit = {
                var:@P@_state = 2
                var:@P@_awaiting_pip = 1
                var:@P@_owner = scope:@P@_pip_owner_scope
                var:@P@_subject = this
                var:@P@_source_result_grade = 1
                var:@P@_source_result_owner = scope:@P@_pip_owner_scope
                var:@P@_source_result_subject = this
                has_variable = zg361_b2_pip_owner
                has_variable = zg361_b2_pip_subject
                has_variable = zg361_b2_pip_cycle
                has_variable = zg361_b2_pip_case
                has_variable = zg361_b2_pip_state
                has_variable = zg361_b2_pip_policy_route
                has_variable = zg361_b2_pip_task_kind
                has_variable = zg361_b2_pip_settlement_receipt
                has_variable = zg361_b2_pip_outcome_code
                has_variable = zg361_b2_pip_outcome_result_cycle
                has_variable = zg361_b2_pip_outcome_result_case
                has_variable = zg361_b2_pip_outcome_result_grade
                var:zg361_b2_pip_owner = scope:@P@_pip_owner_scope
                var:zg361_b2_pip_subject = this
                var:zg361_b2_pip_cycle = var:@P@_source_result_cycle
                var:zg361_b2_pip_case > 0
                OR = {
                    var:zg361_b2_pip_policy_route = 1
                    var:zg361_b2_pip_policy_route = 2
                }
                var:zg361_b2_pip_task_kind > 0
                var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case
                var:zg361_b2_pip_outcome_result_cycle > var:zg361_b2_pip_cycle
                var:zg361_b2_pip_outcome_result_cycle >= var:@P@_probation_due_cycle
                var:zg361_b2_pip_outcome_result_case > 0
                OR = {
                    AND = {
                        var:zg361_b2_pip_state = 3
                        var:zg361_b2_pip_outcome_code = 1
                        var:zg361_b2_pip_outcome_result_grade >= 2
                        var:zg361_b2_pip_outcome_result_grade <= 3
                    }
                    AND = {
                        var:zg361_b2_pip_state = 4
                        var:zg361_b2_pip_outcome_code = 2
                        var:zg361_b2_pip_outcome_result_grade = 1
                    }
                }
                has_variable = zg361_b2_workforce_pip_pending
                has_variable = zg361_b2_workforce_pip_consumed
                has_variable = zg361_b2_workforce_pip_owner
                has_variable = zg361_b2_workforce_pip_subject
                has_variable = zg361_b2_workforce_pip_cycle
                has_variable = zg361_b2_workforce_pip_case
                has_variable = zg361_b2_workforce_pip_state
                has_variable = zg361_b2_workforce_pip_case_id
                has_variable = zg361_b2_workforce_pip_case_hash
                has_variable = zg361_b2_workforce_pip_closure_receipt_id
                has_variable = zg361_b2_workforce_pip_closure_receipt_hash
                var:zg361_b2_workforce_pip_pending = 1
                var:zg361_b2_workforce_pip_consumed = 0
                var:zg361_b2_workforce_pip_owner = scope:@P@_pip_owner_scope
                var:zg361_b2_workforce_pip_subject = this
                var:zg361_b2_workforce_pip_cycle = var:zg361_b2_pip_cycle
                var:zg361_b2_workforce_pip_case = var:zg361_b2_pip_case
                var:zg361_b2_workforce_pip_state = var:zg361_b2_pip_state
                var:zg361_b2_workforce_pip_case_id = scope:@P@_expected_pip_case_receipt_id
                var:zg361_b2_workforce_pip_case_hash = scope:@P@_expected_pip_case_receipt_hash
                var:zg361_b2_workforce_pip_closure_receipt_id = scope:@P@_expected_pip_closure_receipt_id
                var:zg361_b2_workforce_pip_closure_receipt_hash = scope:@P@_expected_pip_closure_receipt_hash
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_write_owner = scope:@P@_pip_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
            }
            set_variable = { name = @P@_source_kind value = 2 }
            set_variable = { name = @P@_source_pip_owner value = scope:@P@_pip_owner_scope }
            set_variable = { name = @P@_source_pip_subject value = this }
            set_variable = { name = @P@_source_pip_cycle value = var:zg361_b2_pip_cycle }
            set_variable = { name = @P@_source_pip_case value = var:zg361_b2_pip_case }
            set_variable = { name = @P@_source_pip_state value = var:zg361_b2_pip_state }
            set_variable = { name = @P@_source_pip_policy_route value = var:zg361_b2_pip_policy_route }
            set_variable = { name = @P@_source_pip_task_kind value = var:zg361_b2_pip_task_kind }
            set_variable = { name = @P@_source_pip_settlement_receipt value = var:zg361_b2_pip_settlement_receipt }
            set_variable = { name = @P@_source_pip_outcome_code value = var:zg361_b2_pip_outcome_code }
            set_variable = { name = @P@_source_pip_result_cycle value = var:zg361_b2_pip_outcome_result_cycle }
            set_variable = { name = @P@_source_pip_result_case value = var:zg361_b2_pip_outcome_result_case }
            set_variable = { name = @P@_source_pip_result_grade value = var:zg361_b2_pip_outcome_result_grade }
            set_variable = { name = @P@_source_pip_case_receipt_id value = var:zg361_b2_workforce_pip_case_id }
            set_variable = { name = @P@_source_pip_case_receipt_hash value = var:zg361_b2_workforce_pip_case_hash }
            set_variable = { name = @P@_source_pip_closure_receipt_id value = var:zg361_b2_workforce_pip_closure_receipt_id }
            set_variable = { name = @P@_source_pip_closure_receipt_hash value = var:zg361_b2_workforce_pip_closure_receipt_hash }
            if = {
                limit = { var:zg361_b2_pip_outcome_code = 1 }
                set_variable = { name = @P@_outcome_quality value = 1 } # graduated: pass
            }
            else = {
                set_variable = { name = @P@_outcome_quality value = 2 } # failed: mismatch, not attrition
            }
            set_variable = { name = @P@_outcome_evidence_count value = 2 }
            set_variable = { name = @P@_outcome_evidence_id value = var:zg361_b2_workforce_pip_closure_receipt_id }
            set_variable = { name = @P@_outcome_evidence_hash value = var:zg361_b2_workforce_pip_closure_receipt_hash }
            set_variable = { name = @P@_outcome_observed_cycle value = var:zg361_b2_pip_outcome_result_cycle }
            set_variable = { name = @P@_outcome_exclusion_reason value = 0 } # typed not-excluded conclusion
            set_variable = { name = @P@_awaiting_pip value = 0 }
            @P@_publish_canonical_effect = yes
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 3001 }
            debug_log = "ZG361WPF RED 3001: PIP hook lacks the unique B2 settlement or collides with a published result"
        }
    }

    # Pending hook 3.  A funded #075 route-A normal exit publishes attrition
    # only from its already sealed, consumed and HC-conserved receipt.  The
    # original 3.25 result and signed attribution tuple remain immutable.
    @P@_publish_from_normal_exit_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        var:zg361_workforce_normal_exit_fact_receipt_owner = { save_temporary_scope_as = @P@_normal_exit_owner_scope }
        if = {
            limit = {
                var:@P@_state >= 3
                var:@P@_source_kind = 3
                var:@P@_source_external_receipt_id = var:zg361_workforce_normal_exit_fact_receipt_id
                var:@P@_source_external_receipt_hash = var:zg361_workforce_normal_exit_fact_receipt_hash
            }
            set_variable = { name = @P@_adapter_status value = 2 }
            if = { limit = { var:@P@_state = 3 } @P@_schedule_consume_effect = yes }
            else = { set_variable = { name = @P@_adapter_status value = 4 } }
        }
        else_if = {
            limit = {
                var:@P@_state = 2
                var:@P@_awaiting_pip = 1
                var:@P@_owner = scope:@P@_normal_exit_owner_scope
                var:@P@_subject = this
                var:@P@_source_result_grade = 1
                var:@P@_source_result_owner = scope:@P@_normal_exit_owner_scope
                var:@P@_source_result_subject = this
                has_variable = zg361_workforce_attribution_fact_signature_committed
                has_variable = zg361_workforce_attribution_fact_state
                has_variable = zg361_workforce_attribution_fact_consumed
                has_variable = zg361_workforce_attribution_fact_owner
                has_variable = zg361_workforce_attribution_fact_subject
                has_variable = zg361_workforce_attribution_fact_cycle
                has_variable = zg361_workforce_attribution_fact_case
                has_variable = zg361_workforce_attribution_fact_receipt_id
                has_variable = zg361_workforce_attribution_fact_receipt_hash
                has_variable = zg361_workforce_attribution_fact_receipt_evidence_1
                has_variable = zg361_workforce_attribution_fact_receipt_evidence_2
                has_variable = zg361_workforce_attribution_fact_receipt_evidence_3
                has_variable = zg361_workforce_attribution_fact_attribution_bps_1
                has_variable = zg361_workforce_attribution_fact_attribution_bps_2
                has_variable = zg361_workforce_attribution_fact_attribution_bps_3
                var:zg361_workforce_attribution_fact_signature_committed = 1
                var:zg361_workforce_attribution_fact_state = 3
                var:zg361_workforce_attribution_fact_consumed = 1
                var:zg361_workforce_attribution_fact_owner = scope:@P@_normal_exit_owner_scope
                var:zg361_workforce_attribution_fact_subject = this
                var:zg361_workforce_attribution_fact_cycle = var:@P@_hire_cycle
                var:zg361_workforce_attribution_fact_case = var:@P@_hire_case
                var:zg361_workforce_attribution_fact_receipt_id > 0
                var:zg361_workforce_attribution_fact_receipt_hash > 0
                var:zg361_workforce_attribution_fact_receipt_evidence_1 = var:@P@_outcome_dimension_1
                var:zg361_workforce_attribution_fact_receipt_evidence_2 = var:@P@_outcome_dimension_2
                var:zg361_workforce_attribution_fact_receipt_evidence_3 = var:@P@_outcome_dimension_3
                var:zg361_workforce_attribution_fact_attribution_bps_1 = var:@P@_attribution_bps_1
                var:zg361_workforce_attribution_fact_attribution_bps_2 = var:@P@_attribution_bps_2
                var:zg361_workforce_attribution_fact_attribution_bps_3 = var:@P@_attribution_bps_3
                has_variable = zg361_workforce_normal_exit_fact_receipt_active
                has_variable = zg361_workforce_normal_exit_fact_receipt_sealed
                has_variable = zg361_workforce_normal_exit_fact_receipt_published
                has_variable = zg361_workforce_normal_exit_fact_receipt_consumed
                has_variable = zg361_workforce_normal_exit_fact_receipt_consumed_operation
                has_variable = zg361_workforce_normal_exit_fact_receipt_owner
                has_variable = zg361_workforce_normal_exit_fact_receipt_subject
                has_variable = zg361_workforce_normal_exit_fact_receipt_cycle
                has_variable = zg361_workforce_normal_exit_fact_receipt_case
                has_variable = zg361_workforce_normal_exit_fact_receipt_state
                has_variable = zg361_workforce_normal_exit_fact_receipt_id
                has_variable = zg361_workforce_normal_exit_fact_receipt_hash
                has_variable = zg361_workforce_normal_exit_fact_receipt_exit_source_kind
                has_variable = zg361_workforce_normal_exit_fact_receipt_exit_source_state
                has_variable = zg361_workforce_normal_exit_fact_receipt_exit_class
                has_variable = zg361_workforce_normal_exit_fact_receipt_exit_reason_code
                has_variable = zg361_workforce_normal_exit_fact_receipt_normal_exit_confirmed
                has_variable = zg361_workforce_normal_exit_fact_receipt_forced
                has_variable = zg361_workforce_normal_exit_fact_receipt_neutral_record
                has_variable = zg361_workforce_normal_exit_fact_receipt_actual_exit
                has_variable = zg361_workforce_normal_exit_fact_receipt_hc_ledger_settled
                has_variable = zg361_workforce_normal_exit_fact_receipt_hc_conservation_verified
                has_variable = zg361_workforce_normal_exit_fact_receipt_hc_destination_frozen
                has_variable = zg361_workforce_normal_exit_fact_receipt_formal_hc_active_before
                has_variable = zg361_workforce_normal_exit_fact_receipt_formal_hc_active_after
                has_variable = zg361_workforce_normal_exit_fact_receipt_formal_hc_case
                has_variable = zg361_workforce_normal_exit_fact_receipt_former_slot_id
                has_variable = zg361_workforce_normal_exit_fact_receipt_former_slot_hash
                has_variable = zg361_workforce_normal_exit_fact_receipt_position_type_id
                has_variable = zg361_workforce_normal_exit_fact_receipt_appointment_receipt_id
                has_variable = zg361_workforce_normal_exit_fact_receipt_appointment_receipt_hash
                has_variable = zg361_workforce_normal_exit_fact_receipt_native_end_reason
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_owner
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_subject
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_cycle
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_case
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_state
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_settlement_receipt
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_grade
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_reason
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_kpi
                has_variable = zg361_workforce_normal_exit_fact_receipt_prior_result_rank
                var:zg361_workforce_normal_exit_fact_receipt_active = 1
                var:zg361_workforce_normal_exit_fact_receipt_sealed = 1
                var:zg361_workforce_normal_exit_fact_receipt_published = 1
                var:zg361_workforce_normal_exit_fact_receipt_consumed = 1
                var:zg361_workforce_normal_exit_fact_receipt_consumed_operation = 75
                var:zg361_workforce_normal_exit_fact_receipt_owner = scope:@P@_normal_exit_owner_scope
                var:zg361_workforce_normal_exit_fact_receipt_subject = this
                var:zg361_workforce_normal_exit_fact_receipt_cycle > var:@P@_hire_cycle
                var:zg361_workforce_normal_exit_fact_receipt_case > 0
                var:zg361_workforce_normal_exit_fact_receipt_state = 6
                var:zg361_workforce_normal_exit_fact_receipt_id > 0
                var:zg361_workforce_normal_exit_fact_receipt_hash > 0
                var:zg361_workforce_normal_exit_fact_receipt_exit_source_kind = 75
                var:zg361_workforce_normal_exit_fact_receipt_exit_source_state = 3
                var:zg361_workforce_normal_exit_fact_receipt_exit_class = 1
                var:zg361_workforce_normal_exit_fact_receipt_exit_reason_code = 1
                var:zg361_workforce_normal_exit_fact_receipt_normal_exit_confirmed = 1
                var:zg361_workforce_normal_exit_fact_receipt_forced = 0
                var:zg361_workforce_normal_exit_fact_receipt_neutral_record = 1
                var:zg361_workforce_normal_exit_fact_receipt_actual_exit = 1
                var:zg361_workforce_normal_exit_fact_receipt_hc_ledger_settled = 1
                var:zg361_workforce_normal_exit_fact_receipt_hc_conservation_verified = 1
                var:zg361_workforce_normal_exit_fact_receipt_hc_destination_frozen = 1
                var:zg361_workforce_normal_exit_fact_receipt_formal_hc_active_before = 1
                var:zg361_workforce_normal_exit_fact_receipt_formal_hc_active_after = 0
                var:zg361_workforce_normal_exit_fact_receipt_formal_hc_case = var:@P@_hire_case
                var:zg361_workforce_normal_exit_fact_receipt_former_slot_id > 0
                var:zg361_workforce_normal_exit_fact_receipt_former_slot_hash > 0
                var:zg361_workforce_normal_exit_fact_receipt_position_type_id = 3612741
                var:zg361_workforce_normal_exit_fact_receipt_appointment_receipt_id = var:@P@_position_receipt_id
                var:zg361_workforce_normal_exit_fact_receipt_appointment_receipt_hash = var:@P@_position_receipt_hash
                var:zg361_workforce_normal_exit_fact_receipt_native_end_reason = 1
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_owner = var:@P@_source_result_owner
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_subject = this
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_cycle = var:@P@_source_result_cycle
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_case = var:@P@_source_result_case
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_state = var:@P@_source_result_state
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_settlement_receipt = var:@P@_source_result_settlement_receipt
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_grade = 1
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_reason = var:@P@_source_result_reason
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_kpi = var:@P@_source_result_kpi
                var:zg361_workforce_normal_exit_fact_receipt_prior_result_rank = var:@P@_source_result_rank
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_outcome_settled = 0
                var:@W@_m269_write_owner = scope:@P@_normal_exit_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
                has_variable = @W@_formal_hc_active
                var:@W@_formal_hc_active = 0
            }
            set_variable = { name = @P@_source_kind value = 3 }
            set_variable = { name = @P@_source_external_owner value = scope:@P@_normal_exit_owner_scope }
            set_variable = { name = @P@_source_external_subject value = this }
            set_variable = { name = @P@_source_external_cycle value = var:zg361_workforce_normal_exit_fact_receipt_cycle }
            set_variable = { name = @P@_source_external_case value = var:zg361_workforce_normal_exit_fact_receipt_case }
            set_variable = { name = @P@_source_external_state value = 6 }
            set_variable = { name = @P@_source_external_receipt_id value = var:zg361_workforce_normal_exit_fact_receipt_id }
            set_variable = { name = @P@_source_external_receipt_hash value = var:zg361_workforce_normal_exit_fact_receipt_hash }
            set_variable = { name = @P@_source_external_reason value = var:zg361_workforce_normal_exit_fact_receipt_exit_reason_code }
            set_variable = { name = @P@_source_external_former_slot_id value = var:zg361_workforce_normal_exit_fact_receipt_former_slot_id }
            set_variable = { name = @P@_source_external_slot_hash value = var:zg361_workforce_normal_exit_fact_receipt_former_slot_hash }
            set_variable = { name = @P@_source_external_position_type_id value = var:zg361_workforce_normal_exit_fact_receipt_position_type_id }
            set_variable = { name = @P@_source_external_appointment_receipt_id value = var:zg361_workforce_normal_exit_fact_receipt_appointment_receipt_id }
            set_variable = { name = @P@_source_external_appointment_receipt_hash value = var:zg361_workforce_normal_exit_fact_receipt_appointment_receipt_hash }
            set_variable = { name = @P@_source_external_native_end_reason value = 1 }
            set_variable = { name = @P@_source_external_hc_conservation_verified value = 1 }
            set_variable = { name = @P@_outcome_quality value = 3 }
            set_variable = { name = @P@_outcome_evidence_count value = 3 }
            set_variable = { name = @P@_outcome_evidence_id value = var:zg361_workforce_normal_exit_fact_receipt_id }
            set_variable = { name = @P@_outcome_evidence_hash value = var:zg361_workforce_normal_exit_fact_receipt_hash }
            set_variable = { name = @P@_outcome_observed_cycle value = var:zg361_workforce_normal_exit_fact_receipt_cycle }
            set_variable = { name = @P@_outcome_exclusion_reason value = 0 }
            set_variable = { name = @P@_awaiting_pip value = 0 }
            @P@_publish_canonical_effect = yes
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 3201 }
            debug_log = "ZG361WPF RED 3201: attrition hook lacks exact normal-exit, result, attribution or HC provenance"
        }
    }

    # Pending hook 4.  A native invalidation of the exact long-lived career
    # slot is a role/strategy-change exclusion, not attrition and not #277.
    @P@_publish_from_role_failure_effect = {
        remove_variable = @P@_adapter_status
        remove_variable = @P@_red_code
        var:zg361_workforce_exit_fact_role_failure_receipt_owner = { save_temporary_scope_as = @P@_role_failure_owner_scope }
        if = {
            limit = {
                var:@P@_state >= 3
                var:@P@_source_kind = 4
                var:@P@_source_external_receipt_id = var:zg361_workforce_exit_fact_role_failure_receipt_id
                var:@P@_source_external_receipt_hash = var:zg361_workforce_exit_fact_role_failure_receipt_hash
            }
            set_variable = { name = @P@_adapter_status value = 2 }
            if = { limit = { var:@P@_state = 3 } @P@_schedule_consume_effect = yes }
            else = { set_variable = { name = @P@_adapter_status value = 4 } }
        }
        else_if = {
            limit = {
                var:@P@_state = 2
                var:@P@_awaiting_pip = 1
                var:@P@_owner = scope:@P@_role_failure_owner_scope
                var:@P@_subject = this
                var:@P@_source_result_grade = 1
                var:@P@_source_result_owner = scope:@P@_role_failure_owner_scope
                var:@P@_source_result_subject = this
                var:zg361_workforce_exit_fact_role_failure_receipt_active = 1
                var:zg361_workforce_exit_fact_role_failure_receipt_sealed = 1
                var:zg361_workforce_exit_fact_role_failure_receipt_published = 0
                var:zg361_workforce_exit_fact_role_failure_receipt_consumed = 0
                var:zg361_workforce_exit_fact_role_failure_receipt_owner = scope:@P@_role_failure_owner_scope
                var:zg361_workforce_exit_fact_role_failure_receipt_subject = this
                var:zg361_workforce_exit_fact_role_failure_receipt_hire_cycle = var:@P@_hire_cycle
                var:zg361_workforce_exit_fact_role_failure_receipt_hire_case = var:@P@_hire_case
                var:zg361_workforce_exit_fact_role_failure_receipt_state = 4
                var:zg361_workforce_exit_fact_role_failure_receipt_id > 0
                var:zg361_workforce_exit_fact_role_failure_receipt_hash > 0
                var:zg361_workforce_exit_fact_role_failure_receipt_reason_kind = 1
                var:zg361_workforce_exit_fact_role_failure_receipt_exclusion_reason = 1
                var:zg361_workforce_exit_fact_role_failure_receipt_former_slot_id > 0
                var:zg361_workforce_exit_fact_role_failure_receipt_former_slot_hash > 0
                var:zg361_workforce_exit_fact_role_failure_receipt_position_type_id = 3612741
                var:zg361_workforce_exit_fact_role_failure_receipt_carrier_type_id = 3612771
                var:zg361_workforce_exit_fact_role_failure_receipt_appointment_receipt_id = var:@P@_position_receipt_id
                var:zg361_workforce_exit_fact_role_failure_receipt_appointment_receipt_hash = var:@P@_position_receipt_hash
                var:zg361_workforce_exit_fact_role_failure_receipt_native_end_reason = 2
                var:zg361_workforce_exit_fact_role_failure_receipt_observed_cycle > var:@P@_hire_cycle
                var:zg361_workforce_exit_fact_role_failure_receipt_formal_hc_active = 1
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_conservation_verified = 1
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_authorized = var:zg361_ch_hc_authorized
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_available = var:zg361_ch_hc_available
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_reserved = var:zg361_ch_hc_reserved
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_occupied = var:zg361_ch_hc_occupied
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_frozen = var:zg361_ch_hc_frozen
                var:zg361_workforce_exit_fact_role_failure_receipt_hc_reclaimed = var:zg361_ch_hc_reclaimed
                has_variable = zg361_workforce_attribution_fact_signature_committed
                has_variable = zg361_workforce_attribution_fact_state
                has_variable = zg361_workforce_attribution_fact_consumed
                has_variable = zg361_workforce_attribution_fact_owner
                has_variable = zg361_workforce_attribution_fact_subject
                has_variable = zg361_workforce_attribution_fact_cycle
                has_variable = zg361_workforce_attribution_fact_case
                has_variable = zg361_workforce_attribution_fact_receipt_id
                has_variable = zg361_workforce_attribution_fact_receipt_hash
                has_variable = zg361_workforce_attribution_fact_receipt_evidence_1
                has_variable = zg361_workforce_attribution_fact_receipt_evidence_2
                has_variable = zg361_workforce_attribution_fact_receipt_evidence_3
                has_variable = zg361_workforce_attribution_fact_attribution_bps_1
                has_variable = zg361_workforce_attribution_fact_attribution_bps_2
                has_variable = zg361_workforce_attribution_fact_attribution_bps_3
                var:zg361_workforce_attribution_fact_signature_committed = 1
                var:zg361_workforce_attribution_fact_state = 3
                var:zg361_workforce_attribution_fact_consumed = 1
                var:zg361_workforce_attribution_fact_owner = scope:@P@_role_failure_owner_scope
                var:zg361_workforce_attribution_fact_subject = this
                var:zg361_workforce_attribution_fact_cycle = var:@P@_hire_cycle
                var:zg361_workforce_attribution_fact_case = var:@P@_hire_case
                var:zg361_workforce_attribution_fact_receipt_id > 0
                var:zg361_workforce_attribution_fact_receipt_hash > 0
                var:zg361_workforce_attribution_fact_receipt_evidence_1 = var:@P@_outcome_dimension_1
                var:zg361_workforce_attribution_fact_receipt_evidence_2 = var:@P@_outcome_dimension_2
                var:zg361_workforce_attribution_fact_receipt_evidence_3 = var:@P@_outcome_dimension_3
                var:zg361_workforce_attribution_fact_attribution_bps_1 = var:@P@_attribution_bps_1
                var:zg361_workforce_attribution_fact_attribution_bps_2 = var:@P@_attribution_bps_2
                var:zg361_workforce_attribution_fact_attribution_bps_3 = var:@P@_attribution_bps_3
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_outcome_settled = 0
                var:@W@_m269_write_owner = scope:@P@_role_failure_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
                var:@W@_formal_hc_active = 1
                var:@W@_formal_hc_active_case = var:@P@_hire_case
            }
            set_variable = { name = @P@_source_kind value = 4 }
            set_variable = { name = @P@_source_external_owner value = scope:@P@_role_failure_owner_scope }
            set_variable = { name = @P@_source_external_subject value = this }
            set_variable = { name = @P@_source_external_cycle value = var:zg361_workforce_exit_fact_role_failure_receipt_observed_cycle }
            set_variable = { name = @P@_source_external_case value = var:zg361_workforce_exit_fact_role_failure_receipt_hire_case }
            set_variable = { name = @P@_source_external_state value = 4 }
            set_variable = { name = @P@_source_external_receipt_id value = var:zg361_workforce_exit_fact_role_failure_receipt_id }
            set_variable = { name = @P@_source_external_receipt_hash value = var:zg361_workforce_exit_fact_role_failure_receipt_hash }
            set_variable = { name = @P@_source_external_reason value = 1 }
            set_variable = { name = @P@_source_external_former_slot_id value = var:zg361_workforce_exit_fact_role_failure_receipt_former_slot_id }
            set_variable = { name = @P@_source_external_slot_hash value = var:zg361_workforce_exit_fact_role_failure_receipt_former_slot_hash }
            set_variable = { name = @P@_source_external_position_type_id value = var:zg361_workforce_exit_fact_role_failure_receipt_position_type_id }
            set_variable = { name = @P@_source_external_appointment_receipt_id value = var:zg361_workforce_exit_fact_role_failure_receipt_appointment_receipt_id }
            set_variable = { name = @P@_source_external_appointment_receipt_hash value = var:zg361_workforce_exit_fact_role_failure_receipt_appointment_receipt_hash }
            set_variable = { name = @P@_source_external_native_end_reason value = 2 }
            set_variable = { name = @P@_source_external_hc_conservation_verified value = 1 }
            set_variable = { name = @P@_outcome_quality value = 4 }
            set_variable = { name = @P@_outcome_evidence_count value = 2 }
            set_variable = { name = @P@_outcome_evidence_id value = var:zg361_workforce_exit_fact_role_failure_receipt_id }
            set_variable = { name = @P@_outcome_evidence_hash value = var:zg361_workforce_exit_fact_role_failure_receipt_hash }
            set_variable = { name = @P@_outcome_observed_cycle value = var:zg361_workforce_exit_fact_role_failure_receipt_observed_cycle }
            set_variable = { name = @P@_outcome_exclusion_reason value = 1 }
            set_variable = { name = @P@_awaiting_pip value = 0 }
            @P@_publish_canonical_effect = yes
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 3301 }
            debug_log = "ZG361WPF RED 3301: role-failure hook lacks exact invalidation, attribution or HC provenance"
        }
    }

    # Internal commit: issue one owner-monotonic outcome ID only after a real
    # source guard has populated every canonical payload field.
    @P@_publish_canonical_effect = {
        var:@P@_owner = { save_temporary_scope_as = @P@_publish_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_commit_expected_attribution_bps_1
            value = {
                value = 10000
                subtract = var:@P@_attribution_bps_2
                subtract = var:@P@_attribution_bps_3
            }
        }
        if = {
            limit = {
                OR = { var:@P@_source_kind = 1 var:@P@_source_kind = 2 var:@P@_source_kind = 3 var:@P@_source_kind = 4 }
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_hire_cycle
                has_variable = @P@_hire_case
                has_variable = @P@_source_result_cycle
                has_variable = @P@_source_result_case
                has_variable = @P@_outcome_dimension_1
                has_variable = @P@_outcome_dimension_2
                has_variable = @P@_outcome_dimension_3
                has_variable = @P@_attribution_bps_1
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
                has_variable = @P@_attribution_receipt_id
                has_variable = @P@_attribution_receipt_hash
                has_variable = @P@_outcome_quality
                has_variable = @P@_outcome_evidence_count
                has_variable = @P@_outcome_evidence_id
                has_variable = @P@_outcome_evidence_hash
                has_variable = @P@_outcome_observed_cycle
                has_variable = @P@_outcome_exclusion_reason
                exists = scope:@P@_publish_owner_scope
                var:@P@_subject = this
                var:@P@_outcome_observed_cycle > var:@P@_hire_cycle
                var:@P@_outcome_evidence_count >= 1
                var:@P@_outcome_evidence_id > 0
                var:@P@_outcome_evidence_hash > 0
                OR = {
                    AND = { var:@P@_source_kind = 1 var:@P@_outcome_quality = 1 var:@P@_outcome_exclusion_reason = 0 }
                    AND = { var:@P@_source_kind = 2 OR = { var:@P@_outcome_quality = 1 var:@P@_outcome_quality = 2 } var:@P@_outcome_exclusion_reason = 0 }
                    AND = {
                        var:@P@_source_kind = 3
                        var:@P@_outcome_quality = 3
                        var:@P@_outcome_exclusion_reason = 0
                        var:@P@_source_external_owner = scope:@P@_publish_owner_scope
                        var:@P@_source_external_subject = this
                        var:@P@_source_external_cycle = var:zg361_workforce_normal_exit_fact_receipt_cycle
                        var:@P@_source_external_case = var:zg361_workforce_normal_exit_fact_receipt_case
                        var:@P@_source_external_state = 6
                        var:@P@_source_external_receipt_id = var:zg361_workforce_normal_exit_fact_receipt_id
                        var:@P@_source_external_receipt_hash = var:zg361_workforce_normal_exit_fact_receipt_hash
                        var:@P@_source_external_reason = var:zg361_workforce_normal_exit_fact_receipt_exit_reason_code
                        var:@P@_source_external_former_slot_id = var:zg361_workforce_normal_exit_fact_receipt_former_slot_id
                        var:@P@_source_external_slot_hash = var:zg361_workforce_normal_exit_fact_receipt_former_slot_hash
                        var:@P@_source_external_position_type_id = var:zg361_workforce_normal_exit_fact_receipt_position_type_id
                        var:@P@_source_external_appointment_receipt_id = var:zg361_workforce_normal_exit_fact_receipt_appointment_receipt_id
                        var:@P@_source_external_appointment_receipt_hash = var:zg361_workforce_normal_exit_fact_receipt_appointment_receipt_hash
                        var:@P@_source_external_native_end_reason = 1
                        var:@P@_source_external_hc_conservation_verified = 1
                        var:@P@_outcome_evidence_id = var:@P@_source_external_receipt_id
                        var:@P@_outcome_evidence_hash = var:@P@_source_external_receipt_hash
                    }
                    AND = {
                        var:@P@_source_kind = 4
                        var:@P@_outcome_quality = 4
                        var:@P@_outcome_exclusion_reason = 1
                        var:@P@_source_external_owner = scope:@P@_publish_owner_scope
                        var:@P@_source_external_subject = this
                        var:@P@_source_external_cycle = var:zg361_workforce_exit_fact_role_failure_receipt_observed_cycle
                        var:@P@_source_external_case = var:zg361_workforce_exit_fact_role_failure_receipt_hire_case
                        var:@P@_source_external_state = 4
                        var:@P@_source_external_receipt_id = var:zg361_workforce_exit_fact_role_failure_receipt_id
                        var:@P@_source_external_receipt_hash = var:zg361_workforce_exit_fact_role_failure_receipt_hash
                        var:@P@_source_external_reason = var:zg361_workforce_exit_fact_role_failure_receipt_reason_kind
                        var:@P@_source_external_former_slot_id = var:zg361_workforce_exit_fact_role_failure_receipt_former_slot_id
                        var:@P@_source_external_slot_hash = var:zg361_workforce_exit_fact_role_failure_receipt_former_slot_hash
                        var:@P@_source_external_position_type_id = var:zg361_workforce_exit_fact_role_failure_receipt_position_type_id
                        var:@P@_source_external_appointment_receipt_id = var:zg361_workforce_exit_fact_role_failure_receipt_appointment_receipt_id
                        var:@P@_source_external_appointment_receipt_hash = var:zg361_workforce_exit_fact_role_failure_receipt_appointment_receipt_hash
                        var:@P@_source_external_native_end_reason = 2
                        var:@P@_source_external_hc_conservation_verified = 1
                        var:@P@_outcome_evidence_id = var:@P@_source_external_receipt_id
                        var:@P@_outcome_evidence_hash = var:@P@_source_external_receipt_hash
                    }
                }
                var:@P@_attribution_bps_1 = scope:@P@_commit_expected_attribution_bps_1
                OR = {
                    NOT = { has_variable = @P@_outcome_id }
                    var:@P@_outcome_id = 0
                }
            }
            scope:@P@_publish_owner_scope = {
                if = {
                    limit = { NOT = { has_variable = @P@_owner_outcome_serial } }
                    set_variable = { name = @P@_owner_outcome_serial value = 0 }
                }
                change_variable = { name = @P@_owner_outcome_serial add = 1 }
            }
            set_variable = { name = @P@_outcome_id value = scope:@P@_publish_owner_scope.var:@P@_owner_outcome_serial }
            if = {
                limit = { OR = { var:@P@_source_kind = 3 var:@P@_source_kind = 4 } }
                set_variable = {
                    name = @P@_outcome_receipt_hash
                    value = {
                        value = var:@P@_outcome_id multiply = 1000000
                        add = { value = var:@P@_hire_case multiply = 10000 }
                        add = { value = var:@P@_source_result_case multiply = 100 }
                        add = { value = var:@P@_source_kind multiply = 10 }
                        add = var:@P@_outcome_quality
                        add = var:@P@_source_external_receipt_hash
                    }
                }
            }
            else = {
                set_variable = {
                    name = @P@_outcome_receipt_hash
                    value = {
                        value = var:@P@_outcome_id multiply = 1000000
                        add = { value = var:@P@_hire_case multiply = 10000 }
                        add = { value = var:@P@_source_result_case multiply = 100 }
                        add = { value = var:@P@_source_kind multiply = 10 }
                        add = var:@P@_outcome_quality
                    }
                }
            }
            set_variable = { name = @P@_published value = 1 }
            set_variable = { name = @P@_consumed value = 0 }
            set_variable = { name = @P@_state value = 3 }
            set_variable = { name = @P@_adapter_status value = 1 }
            # Normalize ROOT to the subject through a hidden character event
            # before invoking Workforce's legacy future consumer.
            @P@_schedule_consume_effect = yes
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 3101 }
            debug_log = "ZG361WPF RED 3101: canonical outcome commit rejected incomplete truth"
        }
    }

    # Materialize all twelve legacy aliases only after both the source fact and
    # the exact Workforce #269 pending consumer are ready.  Missing readiness
    # leaves aliases absent, so Workforce continues to fail closed.
    @P@_materialize_and_consume_effect = {
        remove_variable = @P@_red_code
        save_temporary_scope_as = @P@_consume_subject_scope
        var:@P@_owner = { save_temporary_scope_as = @P@_consume_owner_scope }
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                exists = scope:@P@_consume_owner_scope
                var:@P@_subject = this
                scope:@P@_consume_owner_scope = {
                    has_variable = zg361_review_serial
                    var:zg361_review_serial >= scope:@P@_consume_subject_scope.var:@P@_probation_due_cycle
                    var:zg361_review_serial >= scope:@P@_consume_subject_scope.var:@P@_outcome_observed_cycle
                }
                has_variable = @W@_m269_outcome_pending
                var:@W@_m269_outcome_pending = 1
                var:@W@_m269_outcome_settled = 0
                var:@W@_m269_write_owner = scope:@P@_consume_owner_scope
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_hire_cycle
                var:@W@_m269_write_case = var:@P@_hire_case
                var:@W@_m269_write_state = 5
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = var:@P@_hire_case
                var:@W@_m267_candidate_frozen = this
                OR = {
                    AND = {
                        var:@P@_outcome_quality = 3
                        var:@W@_formal_hc_active = 0
                        var:zg361_workforce_normal_exit_fact_receipt_id = var:@P@_source_external_receipt_id
                        var:zg361_workforce_normal_exit_fact_receipt_hash = var:@P@_source_external_receipt_hash
                        var:zg361_workforce_normal_exit_fact_receipt_hc_conservation_verified = 1
                    }
                    AND = {
                        OR = { var:@P@_outcome_quality = 1 var:@P@_outcome_quality = 2 var:@P@_outcome_quality = 4 }
                        var:@W@_formal_hc_active = 1
                        var:@W@_formal_hc_active_case = var:@P@_hire_case
                    }
                }
                OR = {
                    NOT = {
                        OR = {
    @ALIAS_MISSING@
                        }
                    }
                    AND = {
    @ALIAS_EXACT@
                    }
                }
            }
            if = {
                limit = { NOT = { has_variable = @W@_ad_external_outcome_id } }
    @ALIAS_SET@
                set_variable = { name = @P@_legacy_aliases_materialized value = 1 }
            }
            @W@_m269_future_consume_effect = yes
            if = {
                limit = {
                    var:@W@_m269_outcome_settled = 1
                    var:@W@_m269_outcome_pending = 0
                    var:@W@_m269_last_outcome_id = var:@P@_outcome_id
                    var:@W@_m269_consumed_hire_case = var:@P@_hire_case
                    var:@W@_m269_consumed_candidate = this
                    var:@W@_m269_outcome_evidence_id = var:@P@_outcome_evidence_id
                    var:@W@_m269_outcome_evidence_hash = var:@P@_outcome_evidence_hash
                    var:@W@_m269_final_quality = var:@P@_outcome_quality
                }
                @P@_finalize_consumption_receipt_effect = yes
            }
            else = {
                set_variable = { name = @P@_adapter_status value = 5 }
                set_variable = { name = @P@_red_code value = 4003 }
                debug_log = "ZG361WPF RED 4003: Workforce m269 did not acknowledge the exact outcome"
            }
        }
        else_if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@W@_m269_outcome_settled = 1
                var:@W@_m269_outcome_pending = 0
                var:@W@_m269_last_outcome_id = var:@P@_outcome_id
                var:@W@_m269_consumed_hire_case = var:@P@_hire_case
                var:@W@_m269_consumed_candidate = this
                var:@W@_m269_outcome_evidence_id = var:@P@_outcome_evidence_id
                var:@W@_m269_outcome_evidence_hash = var:@P@_outcome_evidence_hash
                var:@W@_m269_final_quality = var:@P@_outcome_quality
                OR = {
                    NOT = {
                        OR = {
    @ALIAS_MISSING@
                        }
                    }
                    AND = {
    @ALIAS_EXACT@
                    }
                }
            }
            @P@_finalize_consumption_receipt_effect = yes
        }
        else_if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                var:@P@_owner = { has_variable = zg361_review_serial }
            }
            set_variable = { name = @P@_adapter_status value = 3 }
            @P@_schedule_consume_retry_effect = yes
        }
        else_if = {
            limit = { var:@P@_state = 4 var:@P@_consumed = 1 }
            set_variable = { name = @P@_adapter_status value = 4 }
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 4001 }
            debug_log = "ZG361WPF RED 4001: source exists but exact Workforce consumer tuple is unavailable"
        }
    }

    @P@_schedule_consume_effect = {
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_consumed = 0
                OR = {
                    NOT = { has_variable = @P@_retry_pending }
                    var:@P@_retry_pending = 0
                }
            }
            set_variable = { name = @P@_retry_pending value = 1 }
            trigger_event = { id = zg361wpf.1 days = 1 }
        }
    }

    @P@_schedule_consume_retry_effect = {
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_consumed = 0
                OR = {
                    NOT = { has_variable = @P@_retry_pending }
                    var:@P@_retry_pending = 0
                }
            }
            set_variable = { name = @P@_retry_pending value = 1 }
            trigger_event = { id = zg361wpf.1 days = 90 }
        }
    }

    @P@_finalize_consumption_receipt_effect = {
        var:@P@_owner = { save_temporary_scope_as = @P@_receipt_owner_scope }
        if = {
            limit = {
                var:@P@_state = 3
                var:@P@_published = 1
                var:@P@_consumed = 0
                exists = scope:@P@_receipt_owner_scope
                var:@P@_subject = this
                var:@W@_m269_outcome_settled = 1
                var:@W@_m269_outcome_pending = 0
                var:@W@_m269_last_outcome_id = var:@P@_outcome_id
                var:@W@_m269_consumed_hire_case = var:@P@_hire_case
                var:@W@_m269_consumed_candidate = this
                var:@W@_m269_outcome_evidence_id = var:@P@_outcome_evidence_id
                var:@W@_m269_outcome_evidence_hash = var:@P@_outcome_evidence_hash
                var:@W@_m269_final_quality = var:@P@_outcome_quality
                has_variable = @W@_m269_receipt_choice
                OR = {
                    var:@W@_m269_receipt_choice = 1
                    var:@W@_m269_receipt_choice = 2
                }
                OR = {
                    NOT = {
                        OR = {
    @ALIAS_MISSING@
                        }
                    }
                    AND = {
    @ALIAS_EXACT@
                    }
                }
            }
            scope:@P@_receipt_owner_scope = {
                if = {
                    limit = { NOT = { has_variable = @P@_owner_consume_serial } }
                    set_variable = { name = @P@_owner_consume_serial value = 0 }
                }
                change_variable = { name = @P@_owner_consume_serial add = 1 }
            }
            set_variable = { name = @P@_consume_receipt_id value = scope:@P@_receipt_owner_scope.var:@P@_owner_consume_serial }
            set_variable = {
                name = @P@_consume_receipt_hash
                value = {
                    value = var:@P@_outcome_id multiply = 1000000
                    add = { value = var:@P@_hire_case multiply = 10000 }
                    add = { value = var:@P@_source_result_case multiply = 100 }
                    add = { value = var:@W@_m269_receipt_choice multiply = 10 }
                    add = 1
                }
            }
            set_variable = { name = @P@_consume_owner value = scope:@P@_receipt_owner_scope }
            set_variable = { name = @P@_consume_subject value = this }
            set_variable = { name = @P@_consume_hire_cycle value = var:@P@_hire_cycle }
            set_variable = { name = @P@_consume_hire_case value = var:@P@_hire_case }
            set_variable = { name = @P@_consume_result_cycle value = var:@P@_source_result_cycle }
            set_variable = { name = @P@_consume_result_case value = var:@P@_source_result_case }
            set_variable = { name = @P@_consume_outcome_id value = var:@P@_outcome_id }
            set_variable = { name = @P@_consume_workforce_choice value = var:@W@_m269_receipt_choice }
            set_variable = { name = @P@_consume_workforce_case value = var:@W@_m269_consumed_hire_case }
            set_variable = { name = @P@_consumed value = 1 }
            set_variable = { name = @P@_published value = 1 }
            set_variable = { name = @P@_retry_pending value = 0 }
            set_variable = { name = @P@_state value = 4 }
            set_variable = { name = @P@_adapter_status value = 4 }
    @ALIAS_CLEAR@
            if = {
                limit = { is_ai = no }
                trigger_event = { id = zg361wpf.2 days = 1 }
            }
            debug_log = "ZG361WPF: canonical outcome consumed once by Workforce m269"
        }
        else_if = {
            limit = { var:@P@_state = 4 var:@P@_consumed = 1 }
            set_variable = { name = @P@_adapter_status value = 4 }
        }
        else = {
            set_variable = { name = @P@_adapter_status value = 5 }
            set_variable = { name = @P@_red_code value = 4101 }
        }
    }
    '''
    # Dedent the static template before inserting column-sensitive generated
    # alias fragments; otherwise their zero-column placeholders would pin the
    # whole CK3 file four spaces to the right.
    template = clean(template)
    for key, value in fragments.items():
        template = template.replace(f"@{key}@", value)
    template = template.replace("@P@", PREFIX).replace("@W@", WORKFORCE_PREFIX)
    return generated(template)


def render_events() -> bytes:
    return generated(
        r'''
        namespace = zg361wpf

        # A retry never publishes truth.  It only replays the strict consumer
        # for a canonical fact that one of the four real outcome hooks wrote.
        zg361wpf.1 = {
            type = character_event
            hidden = yes
            immediate = {
                set_variable = { name = zg361_workforce_probation_fact_retry_pending value = 0 }
                zg361_workforce_probation_fact_materialize_and_consume_effect = yes
            }
        }

        # Subject-only informational receipt.  AI subjects never receive a
        # player event; manager authority is neither requested nor granted.
        zg361wpf.2 = {
            type = character_event
            theme = stewardship
            title = zg361wpf.2.t
            desc = zg361wpf.2.desc
            trigger = {
                is_ai = no
                has_variable = zg361_workforce_probation_fact_state
                has_variable = zg361_workforce_probation_fact_consumed
                has_variable = zg361_workforce_probation_fact_consume_subject
                var:zg361_workforce_probation_fact_state = 4
                var:zg361_workforce_probation_fact_consumed = 1
                var:zg361_workforce_probation_fact_consume_subject = this
            }
            option = {
                name = zg361wpf.2.a
                set_variable = { name = zg361_workforce_probation_fact_notice_seen value = 1 }
            }
        }
        '''
    )


def localization_rows(language: str) -> list[str]:
    english = language != "simp_chinese"
    if english:
        title = "Probation outcome receipt"
        desc = (
            "A settled result, PIP decision, real normal exit, or role-change exclusion "
            "has been bound to this hire. Workforce #269 consumed the same outcome once."
        )
        option = "Keep the receipt with the hire case."
    else:
        title = "试用期结局回执"
        desc = "正式绩效、PIP、真实正常离职或岗位变更排除项，已绑定到这次录用。Workforce #269 只消费同一结局一次。"
        option = "把回执归入本次录用案。"
    return [
        f"l_{language}:",
        f' zg361wpf.2.t:0 "{title}"',
        f' zg361wpf.2.desc:0 "{desc}"',
        f' zg361wpf.2.a:0 "{option}"',
    ]


def render_localization(language: str) -> bytes:
    source = language if language in {"english", "simp_chinese"} else "english"
    rows = localization_rows(source)
    rows[0] = f"l_{language}:"
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered = {
        MOD_ROOT / "common" / "scripted_effects" / f"{PREFIX}_effects.txt": render_effects(),
        MOD_ROOT / "events" / f"{PREFIX}_events.txt": render_events(),
    }
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"{PREFIX}_l_{language}.yml"
        ] = render_localization(language)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    if args.check:
        if stale:
            print("RED: stale Workforce probation fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            return 1
        print("GREEN: Workforce probation fact generated files are current")
        return 0
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce probation fact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
