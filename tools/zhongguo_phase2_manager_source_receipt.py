#!/usr/bin/env python3
"""Validate the real player-manager source used by the Phase2 promo span."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path


SOURCE_RECEIPT_KIND = "zg361_stage10_player_publication_source_v7"
EVENT_FREE_SOURCE_KEY = "event_free_map:stage10_player_manager_source"


class Phase2ManagerSourceReceiptError(RuntimeError):
    """A fail-closed manager-source receipt error."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Phase2ManagerSourceReceiptError(f"{label} is not an object")
    return value


def _positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise Phase2ManagerSourceReceiptError(f"{label} is not a positive integer")
    return value


def _checked_locator(value: object, label: str) -> tuple[Path, int, str]:
    locator = _mapping(value, label)
    raw_path = locator.get("path")
    size = locator.get("bytes")
    sha256 = str(locator.get("sha256", "")).upper()
    if not isinstance(raw_path, str) or not raw_path:
        raise Phase2ManagerSourceReceiptError(f"{label} path is missing")
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise Phase2ManagerSourceReceiptError(f"{label} file is absent: {path}")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise Phase2ManagerSourceReceiptError(f"{label} byte count is invalid")
    if len(sha256) != 64 or any(c not in "0123456789ABCDEF" for c in sha256):
        raise Phase2ManagerSourceReceiptError(f"{label} SHA-256 is invalid")
    if path.stat().st_size != size or _sha256(path) != sha256:
        raise Phase2ManagerSourceReceiptError(f"{label} bytes differ from receipt")
    return path, size, sha256


def validate_phase2_manager_source_receipt(
    receipt_path: Path,
    *,
    expected_product_tree_sha256: str,
) -> dict[str, object]:
    """Return a normalized, byte-bound player-manager source contract."""

    path = Path(receipt_path).expanduser().resolve()
    if not path.is_file():
        raise Phase2ManagerSourceReceiptError(
            f"manager source receipt is absent: {path}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Phase2ManagerSourceReceiptError(
            f"cannot read manager source receipt: {type(error).__name__}: {error}"
        ) from error
    receipt = _mapping(payload, "manager source receipt")
    expected_tree = str(expected_product_tree_sha256).upper()
    if len(expected_tree) != 64:
        raise Phase2ManagerSourceReceiptError("expected product tree SHA-256 is invalid")

    topology = _mapping(receipt.get("offline_topology"), "offline topology")
    player_state = _mapping(
        receipt.get("offline_player_state"), "offline player state"
    )
    fixed_tail = _mapping(receipt.get("fixed_tail_contract"), "fixed tail")
    product_fix = _mapping(receipt.get("product_fix_contract"), "product fix")
    manager = _positive(
        topology.get("player_manager_character_id"), "player manager CharacterID"
    )
    owner = _positive(
        topology.get("immediate_liege_character_id"), "owner CharacterID"
    )
    if manager == owner:
        raise Phase2ManagerSourceReceiptError("manager and owner must differ")
    checkpoint_path, checkpoint_bytes, checkpoint_sha256 = _checked_locator(
        receipt.get("checkpoint"), "manager source checkpoint"
    )
    live_path, _, _ = _checked_locator(
        receipt.get("live_source_provenance"), "live source provenance"
    )
    try:
        live = _mapping(
            json.loads(live_path.read_text(encoding="utf-8-sig")),
            "live source provenance",
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Phase2ManagerSourceReceiptError(
            f"cannot read live source provenance: {type(error).__name__}: {error}"
        ) from error
    binding = _mapping(live.get("target_binding"), "live target binding")
    campaign = _mapping(live.get("target_campaign_root"), "live campaign root")
    live_checkpoint = _mapping(
        live.get("target_checkpoint"), "live target checkpoint"
    )
    date_raw = binding.get("date_raw")
    if isinstance(date_raw, bool) or not isinstance(date_raw, int):
        raise Phase2ManagerSourceReceiptError("manager source date_raw is invalid")

    checks = {
        "receipt_identity": receipt.get("schema_version") == 1
        and receipt.get("kind") == SOURCE_RECEIPT_KIND
        and receipt.get("result") == "GREEN",
        "production_source": receipt.get("fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("selection_attempted") is False,
        "exact_build": receipt.get("game_version") == "1.19.0.6"
        and receipt.get("source_container_header") == "SAV0101",
        "single_player_binding": player_state.get("meta_number_of_players") == 1
        and player_state.get("played_character_records")
        == [{"character_id": manager, "player_id": 1}]
        and player_state.get("currently_played_character_ids") == [manager],
        "manager_topology": topology.get("player_primary_title_tier") == 4
        and topology.get("player_government") == "celestial_government"
        and isinstance(topology.get("direct_landed_vassal_character_ids"), list)
        and bool(topology.get("direct_landed_vassal_character_ids")),
        "product_tree_bound": str(
            receipt.get("product_tree_sha256", "")
        ).upper()
        == expected_tree
        and str(product_fix.get("repaired_product_tree_sha256", "")).upper()
        == expected_tree,
        "bounded_tail": dict(fixed_tail)
        == {
            "source_b1_state": 7,
            "first_pending_event": "zg361b1.122",
            "first_pending_event_days": 30,
            "maximum_action_days": 120,
        },
        "live_source": live.get("schema_version") == 1
        and live.get("kind") == "zg361_stage10_player_source_capture_v1"
        and live.get("result") == "GREEN"
        and live.get("production_live") is True
        and live.get("mcp_native_save") is True
        and live.get("fixture_used") is False
        and live.get("console_used") is False
        and live.get("game_time_advanced") is False,
        "live_binding": binding.get("player_character_id") == manager
        and binding.get("paused") is True
        and binding.get("map_ready") is True
        and binding.get("active_event") is None,
        "live_topology": campaign.get("player_character_id") == manager
        and campaign.get("immediate_liege_character_id") == owner
        and campaign.get("independent") is False
        and campaign.get("campaign_root_context_ready") is True,
        "live_checkpoint": Path(str(live_checkpoint.get("path", ""))).resolve()
        == checkpoint_path
        and live_checkpoint.get("bytes") == checkpoint_bytes
        and str(live_checkpoint.get("sha256", "")).upper()
        == checkpoint_sha256,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise Phase2ManagerSourceReceiptError(
            "manager source receipt failed checks: " + ", ".join(failed)
        )

    receipt_sha256 = _sha256(path)
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_promo_manager_source_v1",
        "result": "GREEN",
        "receipt": {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": receipt_sha256,
        },
        "checkpoint": {
            "path": str(checkpoint_path),
            "bytes": checkpoint_bytes,
            "sha256": checkpoint_sha256,
            "save_lineage_id": (
                "zg361-stage10-player-manager-" + checkpoint_sha256.lower()
            ),
        },
        "player_manager_character_id": manager,
        "owner_character_id": owner,
        "date_raw": date_raw,
        "expected_event_definition_key": EVENT_FREE_SOURCE_KEY,
        "product_tree_sha256": expected_tree,
        "checks": checks,
        "fixture_used": False,
        "console_used": False,
    }


__all__ = [
    "EVENT_FREE_SOURCE_KEY",
    "Phase2ManagerSourceReceiptError",
    "SOURCE_RECEIPT_KIND",
    "validate_phase2_manager_source_receipt",
]
