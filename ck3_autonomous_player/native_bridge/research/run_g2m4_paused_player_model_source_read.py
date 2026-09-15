"""One bounded private model-source receipt in the CK3 owner's already paused driver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from run_g2m4_paused_player_view_read import run_owned_paused_player_view_read


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _model_issue(record: dict[str, object]) -> str | None:
    frame = record.get("private_probe_frame")
    if not isinstance(frame, dict) or not isinstance(frame.get("result"), dict):
        return "private_probe_result_missing"
    probe = frame["result"].get("private_probe")
    if not isinstance(probe, dict):
        return "private_probe_payload_missing"
    model = probe.get("player_model_sources")
    if not isinstance(model, dict) or model.get("schema_version") != 1:
        return "player_model_receipt_missing"
    if model.get("advertised") is not False or model.get("status") != "sources_available" or model.get("failure") != "none":
        return "player_model_source_unavailable"
    if model.get("view_model_binding_verified") is not True:
        return "player_view_model_source_unbound"
    starting = record.get("starting_frame")
    if not isinstance(starting, dict) or model.get("snapshot_revision") != starting.get("native_revision"):
        return "player_model_stale_revision"
    if model.get("date_raw") != starting.get("date_raw") or model.get("player_character_id") != starting.get("played_character_id"):
        return "player_model_actor_or_date_mismatch"
    if model.get("legal_construction_evaluated") is not False:
        return "player_model_source_claims_unperformed_legality"
    holdings = model.get("directly_held_barony_provinces")
    count = model.get("definition_source_count")
    if not isinstance(holdings, list) or not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return "player_model_source_shape_invalid"
    previous_title_id = -1
    for holding in holdings:
        if not isinstance(holding, dict) or not _positive_int(holding.get("barony_title_id")) or not _positive_int(holding.get("province_id")):
            return "player_model_holding_identity_invalid"
        title_id = holding["barony_title_id"]
        if title_id <= previous_title_id:
            return "player_model_holding_order_or_duplicate_invalid"
        previous_title_id = title_id
    return None


def run_owned_paused_player_model_source_read(
    driver: Any,
    frozen: dict[str, object],
    artifact_path: str | Path,
    *,
    timeout_seconds: float = 12.0,
) -> dict[str, object]:
    """Reuse one root+slot42 paused query and validate its additive private source."""
    artifact = Path(artifact_path)
    cache_artifact = artifact.with_name(artifact.stem + ".cache-view.json")
    record = run_owned_paused_player_view_read(
        driver, frozen, cache_artifact, timeout_seconds=timeout_seconds
    )
    record["package_id"] = "G2-M4-PAUSED-PLAYER-MODEL-SOURCE-READ"
    record["cache_view_artifact"] = str(cache_artifact)
    try:
        if record.get("status") == "cache_branch_observed":
            issue = _model_issue(record)
            if issue:
                record.update(status="red", issue=issue)
            else:
                probe = record["private_probe_frame"]["result"]["private_probe"]
                model = probe["player_model_sources"]
                record["player_model_sources"] = model
                record["construction_legality_ready"] = False
                record["next_read"] = "same_frame_player_native_final_legality_and_cost"
                if model["definition_source_count"] == 0 or not model["directly_held_barony_provinces"]:
                    record.update(status="model_sources_evidence_insufficient", issue="empty_direct_holding_or_definition_source")
                else:
                    record["status"] = "model_sources_observed"
        return record
    except Exception as error:
        record.update(status="red", issue=f"{type(error).__name__}: {error}")
        return record
    finally:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["run_owned_paused_player_model_source_read"]
