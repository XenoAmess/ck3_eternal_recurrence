"""Private guardian factory-source capture through an already-connected driver.

Portable SDK module: no external recipe, runtime resource, SDK import, listener,
or Game action is performed on import. Native controls the two stock keys.
Original pure capture function retained from the qualified source recipe.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def capture_with_connected_driver(
    driver: object, *, owned_game_pid: int, output_directory: Path,
    timeout_seconds: float,
) -> dict[str, object]:
    """Use the same already-connected driver, without creating a listener."""
    diagnostics = driver.diagnostics()
    if diagnostics.get("connected") is not True:
        raise RuntimeError("Root driver is not connected")
    if diagnostics.get("bridge_pid") != owned_game_pid:
        raise RuntimeError("connected native hello PID differs from Root-owned PID")
    before = driver.take_internal_semantic_snapshot()
    native_revision = before.get("native_revision")
    if before.get("paused") is not True:
        raise RuntimeError("capture requires the actual paused native frame")
    if type(native_revision) is not int or native_revision <= 0:
        raise RuntimeError("capture requires an actual positive native revision")
    sidecar_path = output_directory / "guardian-two-factory-source.json"
    if sidecar_path.exists():
        raise FileExistsError("capture requires a fresh Root sidecar path")
    family = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=native_revision,
        guardian_factory_sidecar_path=sidecar_path,
        timeout_seconds=timeout_seconds,
    )
    # Preserve the ordinary family result independently from discovery status.
    family_path = output_directory / "family-result.json"
    write_json(family_path, family)
    if not sidecar_path.is_file():
        raise RuntimeError(
            "family query produced no private sidecar; retain family-result.json"
        )
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if not isinstance(sidecar, dict):
        raise RuntimeError("native discovery sidecar is not an object")
    rows = sidecar.get("factories")
    if sidecar.get("schema") != "xar.ck3.guardian-factory-discovery.v1" or not (
        isinstance(rows, list) and len(rows) == 2
        and [row.get("key") for row in rows if isinstance(row, dict)]
        == ["has_relation_guardian", "has_relation_ward"]
    ):
        raise RuntimeError("native sidecar lacks the exact two fixed source records")
    return {
        "status": (
            "FRAME_QUALIFIED_DISCOVERY_WRITTEN"
            if sidecar.get("qualified") is True else "DISCOVERY_UNAVAILABLE"
        ),
        "family_result_path": str(family_path),
        "native_sidecar_path": str(sidecar_path),
        "owned_game_pid": owned_game_pid,
        "actual_native_revision_before": native_revision,
        "actual_public_revision_before": before.get("revision"),
        "actual_date_raw_before": before.get("date_raw"),
        "actual_played_character_id_before": before.get("played_character_id"),
        "sidecar_request_id": sidecar.get("request_id"),
        "sidecar_native_revision": sidecar.get("native_revision"),
        "sidecar_frame_qualified": sidecar.get("qualified") is True,
        "actual_factory_found_count": sum(
            row.get("status") == "found" for row in rows
        ),
        "fixed_record_statuses": [
            {"key": row["key"], "status": row.get("status"),
             "unavailable_reason": row.get("unavailable_reason")}
            for row in rows
        ],
        "public_family_result_changed": False,
        "registered_MCP_consumer_count": 0,
        "guardian_membership_observed": False,
        "guardian_pair_ready": False,
        "G2_outcome_credit": 0,
    }


def capture_with_runtime_owner_driver(
    driver: object, *, owned_game_pid: int, output_directory: Path,
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Create one fresh output leaf and reuse the owner's same connected driver."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=False)
    receipt: dict[str, object] = {
        "schema": "xar.guardian.private-current-capture-result.v1",
        "started_at_utc": now(),
        "status": "RED",
        "owned_game_pid": owned_game_pid,
        "new_driver_constructions": 0,
        "new_listeners": 0,
        "Game_launch_injection_pause_focus_close": 0,
        "guardian_membership_observed": False,
        "guardian_pair_ready": False,
        "G2_outcome_credit": 0,
    }
    try:
        receipt.update(capture_with_connected_driver(
            driver, owned_game_pid=owned_game_pid,
            output_directory=output_directory,
            timeout_seconds=timeout_seconds,
        ))
    except Exception as error:
        receipt["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        receipt["ended_at_utc"] = now()
        # Preserve the already-delivered relative receipt name for server61.
        write_json(output_directory / "ROOT-NATIVE71-GUARDIAN-CAPTURE-RESULT.json", receipt)
    return receipt
