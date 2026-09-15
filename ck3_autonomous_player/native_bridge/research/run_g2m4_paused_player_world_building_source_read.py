"""Bounded exact-build M4 world definitions/player eligibility in an owned paused driver.

The CK3 owner invokes this with the frozen manifest and existing native driver.
It sends only the existing campaign-root and default-OFF private slot42 reads;
it does not launch CK3, open the county view, or submit construction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from run_g2m4_paused_player_view_read import run_owned_paused_player_view_read


def _integer(value: object, *, positive: bool = False) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and (
        value > 0 if positive else value >= 0
    )


def _world_issue(record: dict[str, object]) -> str | None:
    frame = record.get("private_probe_frame")
    starting = record.get("starting_frame")
    if not isinstance(frame, dict) or not isinstance(starting, dict):
        return "private_world_frame_missing"
    result = frame.get("result")
    probe = result.get("private_probe") if isinstance(result, dict) else None
    if not isinstance(probe, dict):
        return "private_world_probe_missing"
    world = probe.get("player_world_building_sources")
    if not isinstance(world, dict) or world.get("schema_version") != 1:
        return "private_world_receipt_missing"
    if (world.get("advertised") is not False or world.get("read_only") is not True
            or world.get("status") != "source_available"
            or world.get("failure") != "none"):
        return "private_world_source_unavailable"
    if (world.get("snapshot_revision") != starting.get("native_revision")
            or world.get("date_raw") != starting.get("date_raw")
            or world.get("player_character_id") != starting.get("played_character_id")):
        return "private_world_frame_actor_mismatch"
    if world.get("cost_ready") is not False or world.get("construction_action_ready") is not False:
        return "private_world_claims_unobserved_cost_or_action"
    definitions = world.get("definition_source_count")
    checks = world.get("final_legality_checks")
    if not _integer(definitions) or not _integer(checks):
        return "private_world_count_shape_invalid"
    if not isinstance(world.get("checks_truncated"), bool) or not isinstance(
            world.get("native_final_legality_evaluated"), bool):
        return "private_world_legality_shape_invalid"
    if world["native_final_legality_evaluated"] != (checks > 0):
        return "private_world_legality_claim_mismatch"
    holdings = world.get("directly_held_barony_provinces")
    samples = world.get("legal_samples")
    if not isinstance(holdings, list) or not isinstance(samples, list):
        return "private_world_rows_missing"
    held_pairs: set[tuple[int, int]] = set()
    previous_title_id = -1
    for holding in holdings:
        if not isinstance(holding, dict) or not _integer(holding.get("barony_title_id"), positive=True) or not _integer(holding.get("province_id"), positive=True):
            return "private_world_holding_identity_invalid"
        pair = (holding["barony_title_id"], holding["province_id"])
        if pair[0] <= previous_title_id or pair in held_pairs:
            return "private_world_holding_order_or_duplicate"
        previous_title_id = pair[0]
        held_pairs.add(pair)
    model = probe.get("player_model_sources")
    if (not isinstance(model, dict) or model.get("status") != "sources_available"
            or model.get("failure") != "none"
            or model.get("view_model_binding_verified") is not True
            or model.get("directly_held_barony_provinces") != holdings):
        return "private_world_held_model_binding_mismatch"
    seen_samples: set[tuple[int, int, int, int]] = set()
    for sample in samples:
        if not isinstance(sample, dict) or any(
                not _integer(sample.get(key), positive=key in {
                    "barony_title_id", "province_id"
                })
                for key in ("barony_title_id", "province_id", "building_type_id", "slot_index")):
            return "private_world_legal_sample_identity_invalid"
        if checks == 0 or (sample["barony_title_id"], sample["province_id"]) not in held_pairs:
            return "private_world_legal_sample_unbound"
        row = (sample["barony_title_id"], sample["province_id"],
               sample["building_type_id"], sample["slot_index"])
        if row in seen_samples:
            return "private_world_legal_sample_duplicate"
        seen_samples.add(row)
    return None


def run_owned_paused_player_world_building_source_read(
    driver: Any, frozen: dict[str, object], artifact_path: str | Path,
    *, timeout_seconds: float = 12.0,
) -> dict[str, object]:
    artifact = Path(artifact_path)
    view_artifact = artifact.with_name(artifact.stem + ".view.json")
    record = run_owned_paused_player_view_read(
        driver, frozen, view_artifact, timeout_seconds=timeout_seconds
    )
    record["package_id"] = "G2-M4-DEFINITION0-WORLD-PLAYER-READ"
    record["view_artifact"] = str(view_artifact)
    try:
        if record.get("status") == "cache_branch_observed":
            issue = _world_issue(record)
            if issue:
                record.update(status="red", issue=issue)
            else:
                world = record["private_probe_frame"]["result"]["private_probe"]["player_world_building_sources"]
                record["player_world_building_sources"] = world
                record["construction_action_ready"] = False
                record["next_read"] = "stock_player_row_cost_and_resources_then_formal_policy"
                record["status"] = (
                    "world_player_legality_observed"
                    if world["definition_source_count"] > 0 and
                    world["final_legality_checks"] > 0 and world["legal_samples"]
                    else "world_source_evidence_insufficient"
                )
                if record["status"] == "world_source_evidence_insufficient":
                    record["issue"] = "no_nonempty_native_legal_sample_in_bounded_read"
        return record
    except Exception as error:
        record.update(status="red", issue=f"{type(error).__name__}: {error}")
        return record
    finally:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


__all__ = ["run_owned_paused_player_world_building_source_read"]
