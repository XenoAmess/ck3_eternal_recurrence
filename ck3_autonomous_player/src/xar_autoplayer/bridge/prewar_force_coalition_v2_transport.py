"""Formal single-request coalition query with a detached current-frame cache.

Read-capability advertisement permits a query. DECLARE eligibility is derived
separately from the actual schema2 observation and an explicit force-risk policy.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .prewar_force_coalition_transport import _frame_binding, _integer, current_prewar_declaration_source

STEP = "query-prewar-force-coalition-coverage-v2"
CAPABILITY = "game.command.query-prewar-force-coalition-coverage-v2-N"
DOMAIN_KEY = "prewar_force_coalition_coverage_v2"
CACHE_SCHEMA = "prewar-force-coalition-v2-cache-v1"
_TOP_KEYS = {"type", "protocol_version", "request_id", "ok", "execution_receipt", "result"}
_RESULT_KEYS = {"step", "accepted", "status", "private_build", "read_only", "advertised", "domain_key", DOMAIN_KEY}
_RECEIPT_KEYS = {"ticket", "query_sequence", "capture_epoch"}
_UINT64_MAX = (1 << 64) - 1


def validate_prewar_force_coalition_v2_execution_receipt(
    frame: object, *, expected_request_id: str,
) -> tuple[dict[str, object], Mapping[str, object]]:
    if not isinstance(frame, Mapping) or set(frame) != _TOP_KEYS:
        raise ValueError("prewar v2 command_result top-level shape is malformed")
    if (frame["type"] != "command_result" or type(frame["protocol_version"]) is not int
            or frame["protocol_version"] != 1 or frame["request_id"] != expected_request_id
            or not isinstance(expected_request_id, str) or not expected_request_id or frame["ok"] is not True):
        raise ValueError("prewar v2 command_result request binding mismatch")
    raw = frame["execution_receipt"]
    if not isinstance(raw, Mapping) or set(raw) != _RECEIPT_KEYS:
        raise ValueError("prewar v2 independent execution receipt is missing or malformed")
    receipt = {key: _integer(raw[key], f"v2 execution_receipt.{key}", 1, _UINT64_MAX) for key in _RECEIPT_KEYS}
    if receipt["query_sequence"] != receipt["ticket"]:
        raise ValueError("prewar v2 execution sequence differs from its actual ticket")
    result = frame["result"]
    if (not isinstance(result, Mapping) or set(result) != _RESULT_KEYS
            or result["step"] != STEP or result["accepted"] is not True
            or type(result["status"]) is not str or result["status"] not in {"partial", "available"}
            or result["private_build"] is not False or result["read_only"] is not True
            or result["advertised"] is not True or result["domain_key"] != DOMAIN_KEY):
        raise ValueError("prewar v2 formal result envelope is malformed")
    return receipt, result


def query_prewar_force_coalition_coverage_v2(
    driver: object, declaration_id: str, *, expected_revision: int,
    timeout_seconds: float = 35.0,
) -> dict[str, object]:
    _integer(expected_revision, "v2 expected_revision", 1, _UINT64_MAX)
    if not isinstance(declaration_id, str) or not declaration_id:
        raise ValueError("declaration_id must be a nonempty canonical string")
    if type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("prewar v2 query timeout must be finite and positive")
    before = driver.take_internal_semantic_snapshot()
    try:
        binding = _frame_binding(before)
        if binding["revision"] != expected_revision:
            raise PreSubmissionRevisionMismatchError("prewar v2 source revision is stale")
        capabilities = driver.state.capabilities().get("bridge_capabilities")
        if not isinstance(capabilities, list) or CAPABILITY not in capabilities:
            raise UnsupportedStepError("Native does not advertise formal prewar v2 read support")
        _, expected, declaration_sequence = current_prewar_declaration_source(driver, before, declaration_id)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    request_id = "prewar-coalition-v2-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": STEP, "expected_revision": binding["native_revision"],
        "expected_public_revision": binding["revision"], "declaration_id": declaration_id,
        "selected_declaration": {key: expected[key] for key in (
            "target_character_id", "casus_belli_index", "casus_belli_key",
            "configuration_index", "claimant_character_id", "target_title_ids",
        )},
    }
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("prewar v2 command_result timed out")
    if isinstance(frame, Mapping) and frame.get("request_id") == request_id and frame.get("ok") is False:
        if (set(frame) != {"type", "protocol_version", "request_id", "ok", "error"}
                or frame.get("type") != "command_result" or type(frame.get("protocol_version")) is not int
                or frame.get("protocol_version") != 1 or not isinstance(frame.get("error"), str)):
            raise BridgeUnavailableError("prewar v2 refusal envelope is malformed")
        raise BridgeUnavailableError(f"Native prewar v2 query refused: {frame['error']}")
    try:
        receipt, result = validate_prewar_force_coalition_v2_execution_receipt(frame, expected_request_id=request_id)
        after = driver.take_internal_semantic_snapshot()
        if _frame_binding(after) != binding:
            raise ValueError("prewar v2 crossed its paused frame lease")
        current_proof, current_expected, current_sequence = current_prewar_declaration_source(driver, after, declaration_id)
        if current_expected != expected or current_sequence != declaration_sequence:
            raise ValueError("prewar v2 selected declaration source lease changed")
        from .prewar_force_coalition_v2_contract import normalize_prewar_force_coalition_v2
        request_binding = {"request_id": request_id, **receipt}
        domain = normalize_prewar_force_coalition_v2(
            result[DOMAIN_KEY], snapshot=current_proof, expected_declaration=expected,
            expected_request_binding=request_binding, expected_request_id=request_id,
        )
        if domain.get("status") != result["status"]:
            raise ValueError("prewar v2 envelope status disagrees with its actual domain")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **dict(result), DOMAIN_KEY: domain, "backend_id": "native-headless",
        "execution_receipt": receipt, "native_request_id": request_id,
        "queried_snapshot_id": binding["snapshot_id"], "queried_revision": binding["revision"],
        "queried_native_revision": binding["native_revision"], "queried_date_raw": binding["date_raw"],
        "queried_actor_character_id": binding["actor_character_id"],
        "queried_connection_generation": binding["connection_generation"],
        "queried_episode_run_id": binding["episode_run_id"],
        "selected_declaration_source": expected, "declaration_query_sequence": declaration_sequence,
    }


def publish_prewar_force_coalition_v2_query(
    driver: object, result: Mapping[str, object], *, attempt_token: int,
) -> bool:
    """Privately detach one fully validated result from the query caller."""
    entry = {
        "validation_schema": CACHE_SCHEMA,
        "frame_binding": {key: result[key] for key in (
            "queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_date_raw",
            "queried_actor_character_id", "queried_connection_generation", "queried_episode_run_id",
        )},
        "selected_declaration": deepcopy(result["selected_declaration_source"]),
        "declaration_query_sequence": result["declaration_query_sequence"],
        "result": deepcopy(dict(result)),
    }
    with driver._driver_state_lock:
        if driver._prewar_force_coalition_v2_attempt != attempt_token:
            return False
        driver._prewar_force_coalition_v2_query = entry
        return True


def get_current_prewar_force_coalition_coverage_v2(
    driver: object, declaration_id: str, snapshot: Mapping[str, object],
) -> dict[str, object] | None:
    """Compare current leases and detach once; never normalize cached DTOs again."""
    try:
        current = _frame_binding(snapshot)
    except ValueError:
        with driver._driver_state_lock:
            driver._prewar_force_coalition_v2_query = None
        return None
    with driver._driver_state_lock:
        entry = getattr(driver, "_prewar_force_coalition_v2_query", None)
        if not isinstance(entry, Mapping):
            return None
        binding = entry.get("frame_binding")
        keys = {
            "queried_snapshot_id": "snapshot_id", "queried_revision": "revision",
            "queried_native_revision": "native_revision", "queried_date_raw": "date_raw",
            "queried_actor_character_id": "actor_character_id",
            "queried_connection_generation": "connection_generation", "queried_episode_run_id": "episode_run_id",
        }
        if (entry.get("validation_schema") != CACHE_SCHEMA or not isinstance(binding, Mapping)
                or set(binding) != set(keys) or any(binding[key] != current[value] for key, value in keys.items())):
            driver._prewar_force_coalition_v2_query = None
            return None
        expected = entry.get("selected_declaration")
        if not isinstance(expected, Mapping) or expected.get("declaration_id") != declaration_id:
            return None
        try:
            _, selected, sequence = current_prewar_declaration_source(driver, dict(snapshot), declaration_id)
        except ValueError:
            driver._prewar_force_coalition_v2_query = None
            return None
        if selected != expected or sequence != entry.get("declaration_query_sequence"):
            driver._prewar_force_coalition_v2_query = None
            return None
        return deepcopy(entry["result"])


def prewar_force_coalition_v2_history_summary(result: Mapping[str, object]) -> dict[str, object]:
    domain = result[DOMAIN_KEY]
    return {
        "schema": "prewar-force-coalition-v2-history-summary-v1", "schema_version": 1,
        "step": STEP, "accepted": result["accepted"], "status": result["status"], "read_only": True,
        "full_result_preserved": False, "unavailable_reason": "domain_details_omitted_from_command_history",
        "native_request_id": result["native_request_id"], "execution_receipt": dict(result["execution_receipt"]),
        "declaration_id": domain["declaration_id"], "actor_lower_soldiers": domain["actor_lower_soldiers"],
        "enemy_upper_soldiers": domain["enemy_upper_soldiers"],
        "enemy_force_coverage_complete": domain["enemy_force_coverage_complete"],
        "complete_initial_participants_ready": domain["complete_initial_participants_ready"],
        "owner_force_rows": len(domain["owner_forces"]),
    }
