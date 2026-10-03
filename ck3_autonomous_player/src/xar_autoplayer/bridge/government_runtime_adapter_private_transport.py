"""Read the native government and feature adapter from one paused frame."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity
from .version_identity import require_exact_native_build


STEP = "query-government-runtime-adapter-v1"
SCHEMA = "government-runtime-adapter-v1"


def normalize_government_runtime_adapter_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve the actual native adapter verdict, including unsupported families."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or value.get("schema_version") != 1:
        raise ValueError("government runtime adapter schema is unavailable")
    build = value.get("build")
    if not isinstance(build, Mapping):
        raise ValueError("government runtime adapter lacks build identity")
    identity = require_exact_native_build(build.get("version"), build.get("exe_sha256"))
    if identity != private_native_build_identity(snapshot):
        raise ValueError("government runtime adapter belongs to another native build")
    provenance = value.get("provenance")
    expected_sources = {
        "backend_id": f"ck3-{identity.game_version}-private-government-runtime-adapter-v1",
        "campaign_backend_id": identity.backend_id("campaign-root-context-v1"),
        "feature_backend_id": identity.backend_id("loaded-feature-manifest-v1"),
    }
    if not isinstance(provenance, Mapping) or any(provenance.get(key) != expected for key, expected in expected_sources.items()):
        raise ValueError("government runtime adapter lacks its native source identities")
    status = value.get("status")
    readiness = value.get("readiness")
    if status not in {"available", "not_present", "unavailable"} or not isinstance(readiness, Mapping):
        raise ValueError("government runtime adapter status is malformed")
    if any(type(readiness.get(key)) is not bool for key in ("same_frame_ready", "core_adapter_ready")):
        raise ValueError("government runtime adapter readiness is malformed")
    if value.get("snapshot_revision") != snapshot.get("native_revision"):
        raise ValueError("government runtime adapter revision differs from the query frame")
    if status == "unavailable":
        if not isinstance(value.get("unavailable_reason"), str) or readiness["same_frame_ready"] or readiness["core_adapter_ready"]:
            raise ValueError("government runtime adapter lost its unavailable result")
        return deepcopy(value)
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or value.get("player_character_id") != actor.get("character_id")
            or value.get("date_raw") != snapshot.get("date_raw") or readiness["same_frame_ready"] is not True):
        raise ValueError("government runtime adapter does not match the paused player frame")
    government = value.get("government")
    features = value.get("effective_feature_flags")
    adapter = value.get("adapter")
    if (not isinstance(government, Mapping) or not isinstance(government.get("key"), str)
            or not isinstance(government.get("flags"), list)
            or not isinstance(features, Mapping) or not isinstance(features.get("items"), list)
            or not isinstance(adapter, Mapping) or not isinstance(adapter.get("status"), str)
            or type(adapter.get("requirements_met")) is not bool):
        raise ValueError("government runtime adapter observation is malformed")
    rows = features["items"]
    if features.get("native_count") != len(rows) or len(rows) != 44:
        raise ValueError("government runtime adapter feature count is malformed")
    keys: set[str] = set()
    for index, row in enumerate(rows):
        if (not isinstance(row, Mapping) or row.get("native_index") != index
                or not isinstance(row.get("key"), str) or not row["key"] or row["key"] in keys
                or type(row.get("enabled")) is not bool):
            raise ValueError("government runtime adapter feature identity is malformed")
        keys.add(row["key"])
    expected_core = status == "available" and adapter["status"] == "core_supported" and adapter["requirements_met"]
    if readiness["core_adapter_ready"] != expected_core:
        raise ValueError("government runtime adapter disagrees with its native core verdict")
    return deepcopy(value)


def query_government_runtime_adapter_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_government_runtime_adapter_query", False) is not True:
        raise UnsupportedStepError("private government runtime adapter query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    read = (getattr(driver, "take_internal_semantic_snapshot", None)
            or getattr(driver, "take_snapshot"))
    before = read()
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision or before.get("paused") is not True
            or before.get("map_ready") is not True or not isinstance(actor, Mapping)
            or actor.get("alive") is not True or type(native_revision) is not int or native_revision <= 0):
        raise BridgeUnavailableError("government runtime adapter requires a living paused player")
    request_id = "government-read-" + uuid.uuid4().hex
    driver.endpoint.send({"type": "execute_step", "protocol_version": 1,
                          "request_id": request_id, "step": STEP,
                          "expected_revision": native_revision})
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, Mapping) or frame.get("type") != "command_result"
            or frame.get("request_id") != request_id or frame.get("ok") is not True):
        raise BridgeUnavailableError("government runtime adapter command_result unavailable")
    envelope = frame.get("result")
    if (not isinstance(envelope, Mapping) or envelope.get("step") != STEP
            or envelope.get("accepted") is not True or envelope.get("private_build") is not True
            or envelope.get("read_only") is not True or envelope.get("advertised") is not False):
        raise BridgeUnavailableError("government runtime adapter envelope is malformed")
    try:
        value = normalize_government_runtime_adapter_v1(envelope.get("government_runtime_adapter"), snapshot=before)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    after = read()
    if (after.get("paused") is not True or after.get("date_raw") != before.get("date_raw")
            or after.get("played_character") != actor):
        raise BridgeUnavailableError("government runtime adapter crossed its paused player frame")
    return {**value, "queried_revision": expected_revision,
            "queried_native_revision": native_revision,
            "queried_snapshot_id": before.get("snapshot_id"),
            "post_snapshot_id": after.get("snapshot_id")}
