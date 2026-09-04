#!/usr/bin/env python3
"""Plan or materialize the boundary-only B3 effect-file A/B fallback.

The B candidate moves complete top-level scripted-effect definitions into
small purpose files.  It never edits an effect body.  The source tree passed
to this tool is candidate A, so a later semantic correction is retained byte
for byte when B is produced from that corrected tree.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
if str(MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(MOD_TOOLS))

from zg361_effect_sharding import EffectEntry, top_level_effect_entries  # noqa: E402


BOM = b"\xef\xbb\xbf"
EFFECT_ROOT = Path("common/scripted_effects")
TARGET_MAX = 10
HARD_MAX = 20
LARGE_FILE_BYTES = 200_000
LARGE_BLOCK_BYTES = 100_000
CALL_RE = re.compile(r"\b(zg361_[a-z0-9_]+_effect)\s*=", re.IGNORECASE)

MECHANISM_OWNER = "zg361_generated_mechanism_effects.txt"
B1_OWNER = "zg361_b1_runtime_effects.txt"
B1_PART2_OWNER = "zg361_b1_runtime_effects_part2.txt"
TARGET_OWNERS = (MECHANISM_OWNER, B1_OWNER, B1_PART2_OWNER)

R3_IDENTITY = {
    "artifact": "b3e-27b66b3-20260904-063948Z",
    "projection_sha256": (
        "b769ca3e36e42cb30ae667b91b7f7b54b7648b5ab3c0f28144b18a4c82d9c0ad"
    ),
    "effect_file_count": 401,
    "effect_definition_count": 3581,
    "owners": {
        MECHANISM_OWNER: {
            "bytes": 1_019_397,
            "effects": 1449,
            "sha256": (
                "9e0479b33b322c3d51921180b5a4c34adc13bb9cea9f0f7a70d577a945edd052"
            ),
        },
        B1_OWNER: {
            "bytes": 255_586,
            "effects": 41,
            "sha256": (
                "7e373996a4789f64df5bdb85448f01494a63902abc883df2731dc8318f966247"
            ),
        },
        B1_PART2_OWNER: {
            "bytes": 240_700,
            "effects": 36,
            "sha256": (
                "1f2d76436de74fb37698103f90adc029bac2ac16dd75b29e98d428e3e33f663c"
            ),
        },
    },
}

B1_PURPOSE_GROUPS = (
    (
        "01_case_bootstrap_policy_kpi",
        (
            "zg361_b1_classify_function_effect",
            "zg361_b1_freeze_001_013_policy_effect",
            "zg361_b1_freeze_135_145_policy_effect",
            "zg361_b1_consume_manager_liabilities_as_subject_effect",
            "zg361_b1_snapshot_owner_bound_kpi_effect",
            "zg361_b1_materialize_departed_kpi_effect",
            "zg361_b1_apply_departed_grade_effect",
            "zg361_b1_initialize_subject_case_effect",
        ),
    ),
    (
        "02_cycle_self_review",
        (
            "zg361_b1_open_cycle_effect",
            "zg361_b1_midcycle_dispatcher_effect",
            "zg361_b1_finalize_self_review_effect",
            "zg361_b1_record_self_honest_effect",
            "zg361_b1_record_self_exaggerated_effect",
            "zg361_b1_record_self_conservative_effect",
            "zg361_b1_submit_self_honest_ticket_effect",
            "zg361_b1_submit_self_exaggerated_ticket_effect",
            "zg361_b1_submit_self_conservative_ticket_effect",
        ),
    ),
    (
        "03_peer_facts_shadow",
        (
            "zg361_b1_peer_window_dispatcher_effect",
            "zg361_b1_prepare_facts_effect",
            "zg361_b1_finalize_subject_facts_effect",
            "zg361_b1_record_shadow_accept_effect",
            "zg361_b1_record_shadow_supplement_effect",
            "zg361_b1_submit_shadow_accept_ticket_effect",
            "zg361_b1_submit_shadow_supplement_ticket_effect",
            "zg361_b1_freeze_blind_named_diff_effect",
            "zg361_b1_open_shadow_effect",
        ),
    ),
    (
        "04_quota_bank_debt",
        (
            "zg361_b1_register_common_superior_bank_effect",
            "zg361_b1_compute_exact_quota_effect",
            "zg361_b1_audit_frozen_roster_effect",
            "zg361_b1_audit_locked_roster_additions_effect",
            "zg361_b1_rebuild_local_quota_effect",
            "zg361_b1_settle_due_debt_effect",
            "zg361_b1_execute_unique_pool_trade_effect",
            "zg361_b1_submit_quota_book_effect",
        ),
    ),
    (
        "05_huddle_agenda",
        (
            "zg361_b1_prepare_bank_huddle_effect",
            "zg361_b1_prepare_bank_must_review_effect",
            "zg361_b1_close_common_superior_bank_legacy_unused_effect",
            "zg361_b1_close_common_superior_bank_effect",
            "zg361_b1_apply_local_quota_effect",
            "zg361_b1_rerank_frozen_quota_book_effect",
            "zg361_b1_build_agenda_and_attention_effect",
        ),
    ),
)

B1_PART2_PURPOSE_GROUPS = (
    (
        "06_agenda_dissent_publication",
        (
            "zg361_b1_finalize_agenda_audit_effect",
            "zg361_b1_finalize_huddle_diff_effect",
            "zg361_b1_consume_must_review_effect",
            "zg361_b1_record_named_dissent_effect",
            "zg361_b1_finalize_named_dissent_effect",
            "zg361_b1_refresh_individual_publications_effect",
        ),
    ),
    (
        "07_pending_reopen",
        (
            "zg361_b1_open_pending_slots_effect",
            "zg361_b1_resolve_pending_subject_effect",
            "zg361_b1_verify_frozen_quota_conservation_effect",
            "zg361_b1_prepare_reopen_gate_effect",
            "zg361_b1_materialize_reopen_a_self_safe_effect",
            "zg361_b1_resolve_reopen_batch_effect",
            "zg361_b1_apply_symmetric_reopen_effect",
            "zg361_b1_apply_final_gray_leaver_effect",
        ),
    ),
    (
        "08_calibration_finish_recusal",
        (
            "zg361_b1_pay_frozen_pending_rewards_effect",
            "zg361_b1_finish_calibration_effect",
            "zg361_b1_freeze_conflict_recusals_effect",
            "zg361_b1_apply_recusal_replacement_reviews_effect",
        ),
    ),
    (
        "09_calibration_controls_publish",
        (
            "zg361_b1_apply_atomic_calibration_swap_effect",
            "zg361_b1_apply_bottom_protection_effect",
            "zg361_b1_prepare_skip_level_return_effect",
            "zg361_b1_freeze_band_order_effect",
            "zg361_b1_open_calibration_effect",
            "zg361_b1_mark_published_effect",
        ),
    ),
    (
        "10_appeal_peer_submission",
        (
            "zg361_b1_on_appeal_corrected_effect",
            "zg361_b1_prepare_shared_war_peer_task_effect",
            "zg361_b1_submit_peer_recommendation_effect",
            "zg361_b1_submit_peer_positive_effect",
            "zg361_b1_submit_peer_negative_effect",
        ),
    ),
    (
        "11_peer_slot_consumption",
        (
            "zg361_b1_consume_peer_slot_1_effect",
            "zg361_b1_consume_peer_slot_2_effect",
            "zg361_b1_consume_peer_slot_3_effect",
        ),
    ),
    (
        "12_appeal_credit_m360_source",
        (
            "zg361_b1_apply_appeal_credit_slot_1_effect",
            "zg361_b1_apply_appeal_credit_slot_2_effect",
            "zg361_b1_apply_appeal_credit_slot_3_effect",
            "zg361_b1_publish_m360_cohort_source_effect",
        ),
    ),
)


class EffectSplitFallbackError(ValueError):
    """The A source or requested B projection violates the frozen contract."""


@dataclass(frozen=True)
class Shard:
    source_owner: str
    output_name: str
    purpose: str
    entries: tuple[EffectEntry, ...]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _entries(path: Path) -> tuple[EffectEntry, ...]:
    if not path.is_file():
        raise EffectSplitFallbackError(f"missing effect owner: {path}")
    try:
        return top_level_effect_entries(path.read_bytes())
    except (OSError, UnicodeError, ValueError) as error:
        raise EffectSplitFallbackError(f"cannot parse effect owner {path}: {error}") from error


def _expected_mechanism_names() -> tuple[str, ...]:
    names = ["zg361_init_org_ledger_effect"]
    for mechanism_id in range(1, 362):
        prefix = f"zg361_mechanism_{mechanism_id:03d}"
        names.extend(
            (
                f"{prefix}_choice_a_effect",
                f"{prefix}_choice_b_effect",
                f"{prefix}_choice_c_effect",
                f"{prefix}_ai_effect",
            )
        )
    names.extend(
        (
            "zg361_mechanism_dispatch_next_effect",
            "zg361_mechanism_ai_batch_effect",
            "zg361_adopt_reference_charter_effect",
            "zg361_refresh_org_climate_effect",
        )
    )
    return tuple(names)


def _group_entries(
    owner: str,
    entries: tuple[EffectEntry, ...],
    groups: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[Shard, ...]:
    expected = tuple(name for _purpose, names in groups for name in names)
    observed = tuple(entry.name for entry in entries)
    if observed != expected:
        raise EffectSplitFallbackError(
            f"{owner} purpose anchors drifted; refresh the B fallback plan"
        )
    by_name = {entry.name: entry for entry in entries}
    prefix = "zg361_ab_b3_b1"
    return tuple(
        Shard(
            source_owner=owner,
            output_name=f"{prefix}_{purpose}_effects.txt",
            purpose=purpose,
            entries=tuple(by_name[name] for name in names),
        )
        for purpose, names in groups
    )


def _mechanism_shards(entries: tuple[EffectEntry, ...]) -> tuple[Shard, ...]:
    observed = tuple(entry.name for entry in entries)
    if observed != _expected_mechanism_names():
        raise EffectSplitFallbackError(
            f"{MECHANISM_OWNER} definition anchors drifted; refresh the B fallback plan"
        )
    shards = [
        Shard(
            source_owner=MECHANISM_OWNER,
            output_name="zg361_ab_b3_mechanism_000_ledger_bootstrap_effects.txt",
            purpose="ledger_bootstrap",
            entries=(entries[0],),
        )
    ]
    cursor = 1
    for first_id in range(1, 362, 2):
        last_id = min(first_id + 1, 361)
        count = (last_id - first_id + 1) * 4
        shards.append(
            Shard(
                source_owner=MECHANISM_OWNER,
                output_name=(
                    "zg361_ab_b3_mechanism_"
                    f"{first_id:03d}_{last_id:03d}_policy_choices_effects.txt"
                ),
                purpose=f"mechanism_{first_id:03d}_{last_id:03d}_policy_choices",
                entries=entries[cursor : cursor + count],
            )
        )
        cursor += count
    helper_names = (
        ("362_player_dispatch", "zg361_mechanism_dispatch_next_effect"),
        ("363_ai_batch", "zg361_mechanism_ai_batch_effect"),
        ("364_reference_charter", "zg361_adopt_reference_charter_effect"),
        ("365_org_climate", "zg361_refresh_org_climate_effect"),
    )
    for purpose, expected_name in helper_names:
        entry = entries[cursor]
        if entry.name != expected_name:
            raise EffectSplitFallbackError(
                f"{MECHANISM_OWNER} helper boundary drifted at {expected_name}"
            )
        shards.append(
            Shard(
                source_owner=MECHANISM_OWNER,
                output_name=f"zg361_ab_b3_mechanism_{purpose}_effects.txt",
                purpose=purpose,
                entries=(entry,),
            )
        )
        cursor += 1
    if cursor != len(entries):
        raise EffectSplitFallbackError("mechanism sharding did not consume every effect")
    return tuple(shards)


def build_shards(source_root: Path) -> tuple[Shard, ...]:
    effect_root = source_root / EFFECT_ROOT
    mechanism = _entries(effect_root / MECHANISM_OWNER)
    b1 = _entries(effect_root / B1_OWNER)
    b1_part2 = _entries(effect_root / B1_PART2_OWNER)
    shards = (
        *_mechanism_shards(mechanism),
        *_group_entries(B1_OWNER, b1, B1_PURPOSE_GROUPS),
        *_group_entries(B1_PART2_OWNER, b1_part2, B1_PART2_PURPOSE_GROUPS),
    )
    output_names = tuple(shard.output_name for shard in shards)
    if len(set(output_names)) != len(output_names):
        raise EffectSplitFallbackError("B fallback output filenames are not unique")
    counts = tuple(len(shard.entries) for shard in shards)
    if not counts or min(counts) < 1 or max(counts) > TARGET_MAX:
        raise EffectSplitFallbackError("B fallback violates the 1-10 target")
    return tuple(shards)


def _render_shard(shard: Shard) -> bytes:
    header = (
        "# B3 A/B FALLBACK — boundary-only projection; effect bodies unchanged.\n"
        f"# Source owner: {shard.source_owner}; purpose: {shard.purpose}.\n"
    )
    body = "\n\n".join(entry.block for entry in shard.entries) + "\n"
    return BOM + header.encode("utf-8") + body.encode("utf-8")


def _effect_rows(effect_root: Path) -> tuple[dict[str, object], ...]:
    rows = []
    for path in sorted(effect_root.glob("*.txt"), key=lambda item: item.name.casefold()):
        payload = path.read_bytes()
        try:
            entries = top_level_effect_entries(payload)
        except ValueError:
            entries = ()
        rows.append(
            {
                "file": path.name,
                "bytes": len(payload),
                "effects": len(entries),
                "sha256": sha256_bytes(payload),
            }
        )
    return tuple(rows)


def _definition_surface(entries: Iterable[EffectEntry]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (entry.name, sha256_bytes(entry.block.encode("utf-8"))) for entry in entries
    )


def _call_graph(entries: Iterable[EffectEntry]) -> dict[str, tuple[str, ...]]:
    graph = {}
    for entry in entries:
        body = entry.block.split("\n", 1)[1] if "\n" in entry.block else ""
        graph[entry.name] = tuple(sorted(CALL_RE.findall(body)))
    return graph


def _json_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(payload)


def build_report(source_root: Path) -> dict[str, object]:
    source_root = source_root.resolve()
    effect_root = source_root / EFFECT_ROOT
    if not effect_root.is_dir():
        raise EffectSplitFallbackError(f"scripted-effect root is missing: {effect_root}")
    rows = _effect_rows(effect_root)
    shards = build_shards(source_root)
    original_entries = {
        owner: _entries(effect_root / owner) for owner in TARGET_OWNERS
    }
    original_flat = tuple(
        entry for owner in TARGET_OWNERS for entry in original_entries[owner]
    )
    projected_flat = tuple(entry for shard in shards for entry in shard.entries)
    source_surface = _definition_surface(original_flat)
    projected_surface = _definition_surface(projected_flat)
    source_graph = _call_graph(original_flat)
    projected_graph = _call_graph(projected_flat)
    owner_rows = {str(row["file"]): row for row in rows}
    input_rows = []
    for owner in TARGET_OWNERS:
        row = owner_rows[owner]
        expected = R3_IDENTITY["owners"][owner]
        input_rows.append(
            {
                **row,
                "r3_expected": expected,
                "matches_r3": all(row[key] == expected[key] for key in expected),
            }
        )

    untouched_counts = [
        int(row["effects"]) for row in rows if row["file"] not in TARGET_OWNERS
    ]
    projected_counts = [*untouched_counts, *(len(shard.entries) for shard in shards)]
    target_misses = [count for count in projected_counts if count > TARGET_MAX]
    violations = [count for count in projected_counts if count > HARD_MAX]
    total_effects = sum(int(row["effects"]) for row in rows)
    projected_effects = sum(projected_counts)
    all_definitions = []
    for path in sorted(effect_root.glob("*.txt")):
        try:
            all_definitions.extend(entry.name for entry in top_level_effect_entries(path.read_bytes()))
        except ValueError:
            pass
    target_names = [entry.name for entry in original_flat]
    unique_target_ownership = all(all_definitions.count(name) == 1 for name in target_names)
    shard_rows = [
        {
            "source_owner": shard.source_owner,
            "output": shard.output_name,
            "purpose": shard.purpose,
            "effects": len(shard.entries),
            "bytes": len(_render_shard(shard)),
            "first_effect": shard.entries[0].name,
            "last_effect": shard.entries[-1].name,
        }
        for shard in shards
    ]
    large_indivisible = []
    for path in sorted(effect_root.glob("*.txt")):
        try:
            entries = top_level_effect_entries(path.read_bytes())
        except ValueError:
            continue
        for entry in entries:
            block_bytes = len(entry.block.encode("utf-8"))
            if block_bytes >= LARGE_BLOCK_BYTES:
                large_indivisible.append(
                    {"file": path.name, "effect": entry.name, "bytes": block_bytes}
                )
    large_indivisible.sort(key=lambda row: int(row["bytes"]), reverse=True)
    checks = {
        "definition_names_and_bodies_byte_identical": source_surface
        == projected_surface,
        "call_graph_identical": source_graph == projected_graph,
        "effect_definition_count_identical": total_effects == projected_effects,
        "targeted_definitions_have_one_global_owner": unique_target_ownership,
        "all_B_shards_have_1_to_10_effects": bool(shard_rows)
        and all(1 <= int(row["effects"]) <= TARGET_MAX for row in shard_rows),
        "no_B_shard_exceeds_20_effects": all(
            int(row["effects"]) <= HARD_MAX for row in shard_rows
        ),
        "whole_candidate_has_no_1_to_10_target_miss": not target_misses,
        "whole_candidate_has_no_over_20_violation": not violations,
    }
    report = {
        "schema_version": 1,
        "kind": "zg361_b3_effect_boundary_ab_fallback_plan",
        "result": "GREEN" if all(checks.values()) else "RED",
        "source_root": str(source_root),
        "r3_identity": R3_IDENTITY,
        "input_matches_r3": all(bool(row["matches_r3"]) for row in input_rows),
        "input_owners": input_rows,
        "inventory": {
            "effect_file_count": len(rows),
            "effect_definition_count": total_effects,
            "effect_bytes": sum(int(row["bytes"]) for row in rows),
            "largest_by_effect_count": sorted(
                rows, key=lambda row: (int(row["effects"]), int(row["bytes"])), reverse=True
            )[:10],
            "largest_by_bytes": sorted(
                rows, key=lambda row: int(row["bytes"]), reverse=True
            )[:10],
            "large_indivisible_effects": large_indivisible,
        },
        "candidate_B": {
            "removed_owner_count": len(TARGET_OWNERS),
            "created_shard_count": len(shards),
            "effect_file_delta": len(shards) - len(TARGET_OWNERS),
            "projected_effect_file_count": len(rows) - len(TARGET_OWNERS) + len(shards),
            "projected_effect_definition_count": projected_effects,
            "target_miss_count": len(target_misses),
            "over_20_violation_count": len(violations),
            "maximum_effects_per_file": max(projected_counts, default=0),
            "definition_surface_sha256": _json_sha256(source_surface),
            "call_graph_sha256": _json_sha256(source_graph),
            "shards": shard_rows,
        },
        "checks": checks,
        "live_claimed": False,
        "ck3_started": False,
    }
    return report


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


def materialize_candidate(
    source_root: Path,
    output_root: Path,
    manifest_path: Path,
    *,
    require_r3_identity: bool = False,
) -> dict[str, object]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    manifest_path = manifest_path.resolve()
    if output_root.exists():
        raise EffectSplitFallbackError(f"output already exists: {output_root}")
    if manifest_path.exists():
        raise EffectSplitFallbackError(f"manifest already exists: {manifest_path}")
    try:
        output_root.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise EffectSplitFallbackError("output must not be inside the A source tree")
    for forbidden_root, label in (
        (source_root, "A source tree"),
        (output_root, "B candidate tree"),
    ):
        try:
            manifest_path.relative_to(forbidden_root)
        except ValueError:
            continue
        raise EffectSplitFallbackError(f"manifest must be outside the {label}")

    report = build_report(source_root)
    if report["result"] != "GREEN":
        raise EffectSplitFallbackError("A source failed the boundary-only B plan")
    if require_r3_identity and report["input_matches_r3"] is not True:
        raise EffectSplitFallbackError("A source does not match the frozen r3 inputs")
    shards = build_shards(source_root)
    source_hashes = _tree_hashes(source_root)
    shutil.copytree(source_root, output_root)
    output_effect_root = output_root / EFFECT_ROOT
    for owner in TARGET_OWNERS:
        (output_effect_root / owner).unlink()
    for shard in shards:
        (output_effect_root / shard.output_name).write_bytes(_render_shard(shard))

    rendered_entries = tuple(
        entry
        for shard in shards
        for entry in _entries(output_effect_root / shard.output_name)
    )
    source_entries = tuple(
        entry
        for owner in TARGET_OWNERS
        for entry in _entries(source_root / EFFECT_ROOT / owner)
    )
    output_hashes = _tree_hashes(output_root)
    expected_unchanged = {
        path: digest
        for path, digest in source_hashes.items()
        if Path(path).name not in TARGET_OWNERS
    }
    observed_unchanged = {
        path: digest
        for path, digest in output_hashes.items()
        if not Path(path).name.startswith("zg361_ab_b3_")
    }
    materialization_checks = {
        "source_tree_unchanged": _tree_hashes(source_root) == source_hashes,
        "original_owners_absent_from_B": all(
            not (output_effect_root / owner).exists() for owner in TARGET_OWNERS
        ),
        "all_declared_shards_present": all(
            (output_effect_root / shard.output_name).is_file() for shard in shards
        ),
        "non_target_files_byte_identical": expected_unchanged == observed_unchanged,
        "definition_names_and_bodies_byte_identical": _definition_surface(source_entries)
        == _definition_surface(rendered_entries),
        "call_graph_identical": _call_graph(source_entries)
        == _call_graph(rendered_entries),
        "all_rendered_files_have_utf8_bom": all(
            (output_effect_root / shard.output_name).read_bytes().startswith(BOM)
            for shard in shards
        ),
        "all_rendered_files_have_1_to_10_effects": all(
            1
            <= len(_entries(output_effect_root / shard.output_name))
            <= TARGET_MAX
            for shard in shards
        ),
    }
    receipt = {
        **report,
        "kind": "zg361_b3_effect_boundary_B_materialization",
        "result": "GREEN" if all(materialization_checks.values()) else "RED",
        "candidate_B_root": str(output_root),
        "materialization_checks": materialization_checks,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if receipt["result"] != "GREEN":
        raise EffectSplitFallbackError("materialized B failed equivalence verification")
    return receipt


def _summary(report: Mapping[str, object]) -> str:
    inventory = report["inventory"]
    candidate = report["candidate_B"]
    assert isinstance(inventory, Mapping) and isinstance(candidate, Mapping)
    return (
        f"{report['result']}: A={inventory['effect_file_count']} files/"
        f"{inventory['effect_definition_count']} effects; "
        f"B={candidate['projected_effect_file_count']} files/"
        f"{candidate['projected_effect_definition_count']} effects; "
        f"new shards={candidate['created_shard_count']}; "
        f"max={candidate['maximum_effects_per_file']}; "
        f"target misses={candidate['target_miss_count']}; "
        f">20={candidate['over_20_violation_count']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--require-r3-identity", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if (args.output_root is None) != (args.manifest is None):
            raise EffectSplitFallbackError(
                "--output-root and --manifest must be supplied together"
            )
        if args.output_root is None:
            report = build_report(args.source_root)
            if args.require_r3_identity and report["input_matches_r3"] is not True:
                raise EffectSplitFallbackError(
                    "source does not match the frozen r3 inputs"
                )
        else:
            report = materialize_candidate(
                args.source_root,
                args.output_root,
                args.manifest,
                require_r3_identity=args.require_r3_identity,
            )
        print(
            json.dumps(report, ensure_ascii=False, indent=2)
            if args.json
            else _summary(report)
        )
        return 0 if report["result"] == "GREEN" else 1
    except (EffectSplitFallbackError, OSError, UnicodeError) as error:
        print(f"RED: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
