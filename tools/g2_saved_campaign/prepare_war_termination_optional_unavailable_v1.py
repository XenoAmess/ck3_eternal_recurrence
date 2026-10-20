"""Build a war-only candidate from Source28; never edit an installed SDK."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Literal, TypedDict


class CandidateSourcesV1(TypedDict):
    native_driver: bytes
    strategy: bytes
    war_contract: bytes


class ExactRefV1(TypedDict):
    path: str
    bytes: int
    sha256: str


class CandidateLeafV1(TypedDict):
    relative: str
    before_pin: ExactRefV1
    after_pin: ExactRefV1


class CandidateManifestV1(TypedDict):
    schema: Literal["xar.Source28-war-only-candidate/v1"]
    machine_id: str
    observed_at_utc: str
    status: Literal["CANDIDATE_NOT_DEPLOYED"]
    parent_commit: Literal["442beeae4676bad9a9d53cb7070a01f06e965761"]
    source28_anchor: ExactRefV1
    source28_BASE: ExactRefV1
    producer_ref: ExactRefV1
    source_leaf_reads: int
    input_counter_scope: Literal["one_build_candidate_call_excludes_producer_and_output_hashes"]
    source_bytes_read: int
    source_sha256_bytes_processed: int
    canonical_metadata_bytes_read: int
    canonical_metadata_sha256_bytes_processed: int
    candidate_bytes_readback_and_compared: int
    runtime_writes: Literal[0]
    Game_SDK_RPC_calls: Literal[0]
    old_encoder_changed: Literal[False]
    candidatePatch: Literal["optional_war_termination_completion_read_unavailable_v1"]
    files: list[CandidateLeafV1]
    new_runtime_leaf_count: Literal[0]
    no_retroactive_recovery_or_credit: Literal[True]


class CandidateWrittenV1(TypedDict):
    manifest: ExactRefV1
    candidate: CandidateManifestV1


SOURCE28_PINS: dict[str, tuple[int, str]] = {
    "xar_autoplayer/bridge/native_driver.py": (1645459, "6929ba6be2532808c7401189b9222870de6a23cc1fc1989a1c1117a818d2e944"),
    "xar_autoplayer/bridge/war_contract.py": (226160, "c2e500e5bf923a6618004d8cdd027c5826a119d33c9bbc58846030b63917eb6a"),
    "xar_autoplayer/strategy.py": (1049102, "2a7213f1ec6aa05a31fd144f6ed59071d2c2f31537020ee8c5fa8e2d8dd4c597"),
}

WAR_CONTRACT_ADDITION_V1 = r'''

# Optional query failure is neither an empty option set nor a native-negative lease.
from collections.abc import Iterable as _WTUIterable
from typing import Literal as _WTULiteral, TypedDict as _WTUTypedDict


class WarQueryWarSignatureV1(_WTUTypedDict):
    war_id: int
    player_side: _WTULiteral["attacker", "defender"]
    player_is_primary_war_leader: bool | None
    primary_opponent_character_id: int | None
    player_relative_war_score: int
    targeted_title_ids: list[int]


class WarQuerySourceFrameV1(_WTUTypedDict):
    snapshot_id: str
    revision: int
    native_revision: int
    date_raw: int
    actor_character_id: int
    episode_run_id: str
    bridge_pid: int
    connection_generation: int
    active_war_signature: list[WarQueryWarSignatureV1]


class WarQueryRequestV1(_WTUTypedDict):
    type: _WTULiteral["execute_step"]
    protocol_version: _WTULiteral[1]
    request_id: str
    step: str
    expected_revision: int


class WarQueryRejectionV1(_WTUTypedDict):
    request: WarQueryRequestV1
    response_error: _WTULiteral["war-termination completion snapshot read failed"]
    response_request_id: str
    response_protocol_version: _WTULiteral[1]
    response_ok: _WTULiteral[False]
    response_result_presence: _WTULiteral["absent"]


class WarTerminationUnavailableV1(_WTUTypedDict):
    schema: _WTULiteral["xar.war-termination-readonly-unavailable/v1"]
    step: str
    accepted: _WTULiteral[False]
    available: _WTULiteral[False]
    status: _WTULiteral["unavailable"]
    read_only: _WTULiteral[True]
    business_submission: _WTULiteral[False]
    replay_allowed: _WTULiteral[False]
    replan_required: _WTULiteral[True]
    war_id: int
    war_termination_options: None
    unavailable_reason: _WTULiteral["native_termination_completion_snapshot_read_failed"]
    source_frame: WarQuerySourceFrameV1
    native_rejection: WarQueryRejectionV1
    semantic_publication_rechecked: _WTULiteral[True]
    fresh_native_completion_proved: _WTULiteral[False]


class WarQueryUnavailableDeferV1(_WTUTypedDict):
    schema: _WTULiteral["xar.war-termination-optional-query-defer/v1"]
    war_id: int
    date_raw: int
    reason: _WTULiteral["same_day_optional_material_unavailable"]
    native_negative_assessment: _WTULiteral[False]
    war_termination_options: None
    business_submission: _WTULiteral[False]
    replay_allowed: _WTULiteral[False]
    source_request_id: str


def _wtu_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("war query object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("war query text keys required")
        result[key] = item
    return result


def _wtu_uint(value: object, maximum: int = 2**53 - 1) -> int:
    if type(value) is not int or not 0 < value <= maximum:
        raise ValueError("war query exact safe positive integer required")
    return value


def _wtu_text(value: object) -> str:
    if type(value) is not str or not value or len(value) > 256:
        raise ValueError("war query bounded nonempty text required")
    return value


def _wtu_step(value: object) -> tuple[str, int]:
    step = _wtu_text(value)
    prefix = "query-war-termination-options-"
    suffix = step.removeprefix(prefix)
    if (not step.startswith(prefix) or not suffix.isascii()
            or not suffix.isdecimal() or suffix.startswith("0")):
        raise ValueError("canonical optional war query required")
    war_id = _wtu_uint(int(suffix), 2**31 - 1)
    return step, war_id


def _wtu_request_id(value: object) -> str:
    identity = _wtu_text(value)
    parts = identity.split("-")
    if (len(parts) != 3 or parts[0] != "step" or not parts[1].isascii()
            or not parts[1].isdecimal() or parts[1].startswith("0")
            or len(parts[2]) != 12 or any(ch not in "0123456789abcdef" for ch in parts[2])):
        raise ValueError("canonical native step request identity required")
    _wtu_uint(int(parts[1]))
    return identity


def _wtu_wars(value: object) -> list[WarQueryWarSignatureV1]:
    if type(value) is not list or not value:
        raise ValueError("active war signature required")
    result: list[WarQueryWarSignatureV1] = []
    seen: set[int] = set()
    for item in value:
        row = _wtu_object(item)
        if not {"war_id", "player_side", "player_is_primary_war_leader",
                "primary_opponent_character_id", "player_relative_war_score",
                "targeted_title_ids"} <= set(row):
            raise ValueError("all nullable war identity fields required")
        war_id = _wtu_uint(row.get("war_id"), 2**32 - 1)
        side = row.get("player_side")
        if type(side) is not str or (side != "attacker" and side != "defender"):
            raise ValueError("war side required")
        typed_side: _WTULiteral["attacker", "defender"] = "attacker" if side == "attacker" else "defender"
        primary = row.get("player_is_primary_war_leader")
        if primary is not None and type(primary) is not bool:
            raise ValueError("war primary flag required")
        opponent_value = row.get("primary_opponent_character_id")
        opponent = None if opponent_value is None else _wtu_uint(opponent_value, 2**32 - 1)
        score = row.get("player_relative_war_score")
        if type(score) is not int or abs(score) > 2**53 - 1:
            raise ValueError("exact safe war score required")
        targets_value = row.get("targeted_title_ids")
        if type(targets_value) is not list:
            raise ValueError("war targets list required")
        targets = [_wtu_uint(target, 2**32 - 1) for target in targets_value]
        if len(set(targets)) != len(targets) or war_id in seen:
            raise ValueError("unique war identities required")
        seen.add(war_id)
        result.append({"war_id": war_id, "player_side": typed_side,
            "player_is_primary_war_leader": primary,
            "primary_opponent_character_id": opponent,
            "player_relative_war_score": score, "targeted_title_ids": targets})
    return sorted(result, key=lambda row: row["war_id"])


def _wtu_frame(snapshot: object) -> WarQuerySourceFrameV1:
    row = _wtu_object(snapshot)
    played = _wtu_object(row.get("played_character"))
    diagnostics = _wtu_object(row.get("diagnostics"))
    if (row.get("paused") is not True or row.get("map_ready") is not True
            or played.get("alive") is not True):
        raise ValueError("paused playable map required")
    native_revision = _wtu_uint(row.get("native_revision"))
    snapshot_id = _wtu_text(row.get("snapshot_id"))
    if snapshot_id != "native:" + str(native_revision):
        raise ValueError("snapshot/native revision binding differs")
    return {"snapshot_id": snapshot_id,
        "revision": _wtu_uint(row.get("revision")),
        "native_revision": native_revision,
        "date_raw": _wtu_uint(row.get("date_raw")),
        "actor_character_id": _wtu_uint(played.get("character_id"), 2**32 - 1),
        "episode_run_id": _wtu_text(row.get("episode_run_id")),
        "bridge_pid": _wtu_uint(diagnostics.get("bridge_pid"), 2**32 - 1),
        "connection_generation": _wtu_uint(diagnostics.get("connection_generation")),
        "active_war_signature": _wtu_wars(row.get("active_wars"))}


def _wtu_bound_result(step: str, request: object, response: object,
                      frame: WarQuerySourceFrameV1) -> WarTerminationUnavailableV1:
    canonical, war_id = _wtu_step(step)
    if not any(row["war_id"] == war_id for row in frame["active_war_signature"]):
        raise ValueError("queried war must remain active")
    asked = _wtu_object(request)
    if set(asked) != {"type", "protocol_version", "request_id", "step", "expected_revision"}:
        raise ValueError("exact original query request required")
    request_id = _wtu_request_id(asked.get("request_id"))
    if (asked.get("type") != "execute_step" or type(asked.get("protocol_version")) is not int
            or asked["protocol_version"] != 1 or asked.get("step") != canonical
            or _wtu_uint(asked.get("expected_revision")) != frame["native_revision"]):
        raise ValueError("original native query binding differs")
    reply = _wtu_object(response)
    if (set(reply) != {"type", "protocol_version", "request_id", "ok", "error"}
            or reply.get("type") != "command_result"
            or type(reply.get("protocol_version")) is not int or reply["protocol_version"] != 1
            or reply.get("request_id") != request_id or reply.get("ok") is not False
            or reply.get("error") != "war-termination completion snapshot read failed"):
        raise ValueError("exact native query rejection required")
    return {"schema": "xar.war-termination-readonly-unavailable/v1", "step": canonical,
        "accepted": False, "available": False, "status": "unavailable", "read_only": True,
        "business_submission": False, "replay_allowed": False, "replan_required": True,
        "war_id": war_id, "war_termination_options": None,
        "unavailable_reason": "native_termination_completion_snapshot_read_failed",
        "source_frame": frame, "native_rejection": {"request": {
            "type": "execute_step", "protocol_version": 1, "request_id": request_id,
            "step": canonical, "expected_revision": frame["native_revision"]},
            "response_error": "war-termination completion snapshot read failed",
            "response_request_id": request_id, "response_protocol_version": 1, "response_ok": False,
            "response_result_presence": "absent"},
        "semantic_publication_rechecked": True, "fresh_native_completion_proved": False}


def war_termination_optional_unavailable_v1(*, step: str, native_error: str,
        native_request_id: object, request: object, response: object,
        starting: object, current: object) -> WarTerminationUnavailableV1 | None:
    """Match one explicit read-only rejection; a publication recheck is not a native fence."""
    if native_error != "war-termination completion snapshot read failed":
        return None
    try:
        before = _wtu_frame(starting)
        after = _wtu_frame(current)
        if before != after:
            return None
        result = _wtu_bound_result(step, request, response, before)
        if _wtu_request_id(native_request_id) != result["native_rejection"]["request"]["request_id"]:
            return None
        return result
    except (ValueError, KeyError, OverflowError):
        return None


def _wtu_parse_stored_result(value: object) -> WarTerminationUnavailableV1:
    row = _wtu_object(value)
    frame = _wtu_object(row.get("source_frame"))
    # Reconstruct the one canonical JSON type domain before comparing evidence.
    snapshot: dict[str, object] = {key: frame.get(key) for key in
        ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
    snapshot.update(paused=True, map_ready=True,
        played_character={"character_id": frame.get("actor_character_id"), "alive": True},
        diagnostics={"bridge_pid": frame.get("bridge_pid"), "connection_generation": frame.get("connection_generation")},
        active_wars=frame.get("active_war_signature"))
    parsed_frame = _wtu_frame(snapshot)
    if frame != dict(parsed_frame):
        raise ValueError("stored source frame differs")
    evidence = _wtu_object(row.get("native_rejection"))
    response: dict[str, object] = {
        "type": "command_result", "protocol_version": evidence.get("response_protocol_version"),
        "request_id": evidence.get("response_request_id"), "ok": evidence.get("response_ok"),
        "error": evidence.get("response_error")}
    presence = evidence.get("response_result_presence")
    if presence != "absent":
        raise ValueError("original response result presence required")
    expected = _wtu_bound_result(_wtu_text(row.get("step")), evidence.get("request"), response, parsed_frame)
    # Python numeric equality is deliberately insufficient at this wire boundary.
    import json as _wtu_json
    if _wtu_json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) != _wtu_json.dumps(expected, sort_keys=True, separators=(",", ":"), allow_nan=False):
        raise ValueError("stored unavailable result differs")
    return expected


def war_termination_optional_query_defer_v1(snapshot: object, war: object,
        recent_records: _WTUIterable[object]) -> WarQueryUnavailableDeferV1 | None:
    """Avoid repeating a failed optional read on unchanged same-day war inputs."""
    try:
        current = _wtu_frame(snapshot)
        war_id = _wtu_uint(_wtu_object(war).get("war_id"), 2**32 - 1)
        query_step = "query-war-termination-options-" + str(war_id)
        for index, value in enumerate(recent_records):
            if index >= 512:
                return None
            row = _wtu_object(value)
            step = _wtu_text(row.get("step"))
            if step == query_step:
                if row.get("ok") is not False:
                    return None
                result = _wtu_parse_stored_result(row.get("result"))
                previous = result["source_frame"]
                current_row: dict[str, object] = dict(current)
                previous_row: dict[str, object] = dict(previous)
                if any(current_row[key] != previous_row[key] for key in (
                        "date_raw", "actor_character_id", "episode_run_id", "bridge_pid",
                        "connection_generation", "active_war_signature")):
                    return None
                return {"schema": "xar.war-termination-optional-query-defer/v1",
                    "war_id": war_id, "date_raw": current["date_raw"],
                    "reason": "same_day_optional_material_unavailable",
                    "native_negative_assessment": False, "war_termination_options": None,
                    "business_submission": False, "replay_allowed": False,
                    "source_request_id": result["native_rejection"]["request"]["request_id"]}
            if step.startswith(("restore-", "load-", "surrender-", "white-peace-",
                    "offer-white-peace-", "war-enforce-demands", "enforce-")):
                return None
            if row.get("ok") is False:
                other = _wtu_parse_stored_result(row.get("result"))
                if other["step"] != step:
                    return None
                current_scope: dict[str, object] = dict(current)
                other_scope: dict[str, object] = dict(other["source_frame"])
                if any(current_scope[key] != other_scope[key] for key in (
                        "date_raw", "actor_character_id", "episode_run_id", "bridge_pid",
                        "connection_generation", "active_war_signature")):
                    return None
            elif row.get("ok") is not True:
                return None
        return None
    except (ValueError, KeyError, OverflowError, TypeError):
        return None


def parse_war_termination_optional_unavailable_v1(value: object) -> WarTerminationUnavailableV1 | None:
    """Validate a retained DTO for a future nonmaterial Queue consumer."""
    try:
        return _wtu_parse_stored_result(value)
    except (ValueError, KeyError, OverflowError, TypeError):
        return None
'''


def _one(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError("one accepted war-only source seam required: " + before[:100])
    result = source.replace(before, after, 1)
    if result.replace(after, before, 1) != source:
        raise ValueError("war-only seam inverse differs")
    return result


def project_war_optional_query_unavailable_v1(native_driver: bytes, strategy: bytes,
        war_contract: bytes) -> CandidateSourcesV1:
    """Project only the three reviewed war-query seams; no I/O or SDK imports."""
    driver = native_driver.decode("utf-8")
    policy = strategy.decode("utf-8")
    contract = war_contract.decode("utf-8")
    if "WarTerminationUnavailableV1" in contract:
        raise ValueError("unpatched war contract required")
    driver = _one(driver, "from .war_contract import (\n",
        "from .war_contract import (\n    war_termination_optional_unavailable_v1,\n")
    before = """            except _NativeCommandRejectedError as error:
                if error.native_error not in (
                    _WAR_TERMINATION_REVISION_RETRY_ERRORS
                ):"""
    after = """            except _NativeCommandRejectedError as error:
                if error.native_error == "war-termination completion snapshot read failed":
                    current = self.take_internal_semantic_snapshot()
                    unavailable = war_termination_optional_unavailable_v1(
                        step=step, native_error=error.native_error,
                        native_request_id=error.native_request_id,
                        request=error.native_request_frame,
                        response=error.native_command_result_frame,
                        starting=starting, current=current)
                    if unavailable is not None:
                        return dict(unavailable)
                if error.native_error not in (
                    _WAR_TERMINATION_REVISION_RETRY_ERRORS
                ):"""
    driver = _one(driver, before, after)
    before = '                        or (parse_query_battle_control_snapshot_v1_step(step) is not None\n'
    after = ('                        or (parse_query_war_termination_options_step(step) is not None\n'
        '                            and result.get("schema") == "xar.war-termination-readonly-unavailable/v1"\n'
        '                            and result.get("status") == "unavailable")\n' + before)
    driver = _one(driver, before, after)
    policy = _one(policy, "from .bridge.war_contract import (\n",
        "from .bridge.war_contract import (\n    war_termination_optional_query_defer_v1,\n")
    before = '                policy_defer = war_termination_query_policy_defer_v1(\n'
    after = '''                optional_defer = war_termination_optional_query_defer_v1(
                    snapshot, war, ({"step": _effective_command(row),
                        "ok": row.get("ok"), "result": _effective_command_result(row)}
                        for row in reversed(rows)))
                if optional_defer is not None:
                    summary = next((item for item in war_summary
                        if item.get("war_id") == war_id), None)
                    if isinstance(summary, dict):
                        summary["war_termination_optional_query_defer"] = dict(optional_defer)
                    continue
''' + before
    policy = _one(policy, before, after)
    result: CandidateSourcesV1 = {"native_driver": driver.encode(),
        "strategy": policy.encode(), "war_contract": (contract + WAR_CONTRACT_ADDITION_V1).encode()}
    typed_values: dict[str, bytes] = {"native_driver": result["native_driver"],
        "strategy": result["strategy"], "war_contract": result["war_contract"]}
    for name, body in typed_values.items():
        compile(body, name, "exec")
    return result


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ref(path: Path, raw: bytes) -> ExactRefV1:
    return {"path": str(path), "bytes": len(raw), "sha256": _sha(raw)}


def _read_exact(reference: ExactRefV1, limit: int) -> bytes:
    if (set(reference) != {"path", "bytes", "sha256"}
            or type(reference["path"]) is not str or type(reference["bytes"]) is not int
            or not 0 < reference["bytes"] <= limit
            or type(reference["sha256"]) is not str or len(reference["sha256"]) != 64
            or any(ch not in "0123456789abcdef" for ch in reference["sha256"])):
        raise ValueError("bounded exact reference required")
    path = Path(reference["path"])
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or len(raw) != reference["bytes"] or _sha(raw) != reference["sha256"]):
        raise ValueError("stable exact reference differs")
    return raw


def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON text key required")
        result[key] = item
    return result


def build_candidate_v1(source_root: Path, target_root: Path, *,
        source28_anchor: ExactRefV1, source28_BASE: ExactRefV1,
        machine_id: str) -> CandidateWrittenV1:
    """Create exactly three independent SDK leaves and one bounded candidate manifest."""
    if not machine_id or target_root.exists():
        raise ValueError("machine and absent candidate root required")
    anchor_raw = _read_exact(source28_anchor, 32768)
    base_raw = _read_exact(source28_BASE, 524288)
    if ((len(anchor_raw), _sha(anchor_raw)) != (17555, "3f0f25f46e6e0e9a260c9fa24b3c9ae2f9b7febeaf1c7d91c58b7c39f9b16dac")
            or (len(base_raw), _sha(base_raw)) != (411438, "0d903bb46616b91e4947ee838c64662ddcf3be14c89999bd1a5272f01c48f585")):
        raise ValueError("actual canonical Source28 metadata required")
    anchor = _json_object(json.loads(anchor_raw))
    if (anchor.get("schema") != "xar.source28.canonical-git-anchor/v1"
            or anchor.get("status") != "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            or anchor.get("machine_id") != machine_id
            or anchor.get("commit") != "442beeae4676bad9a9d53cb7070a01f06e965761"):
        raise ValueError("actual Source28 canonical identity differs")
    base = _json_object(json.loads(base_raw))
    source_path = base.get("source_root")
    files_value = base.get("files")
    if (base.get("business_source_commit") != anchor["commit"]
            or base.get("machine_id") != machine_id or type(source_path) is not str
            or Path(source_path).resolve() != source_root.resolve()
            or not isinstance(files_value, list)):
        raise ValueError("Source28 BASE source identity differs")
    base_rows = [_json_object(item) for item in files_value]
    loaded: dict[str, bytes] = {}
    before: dict[str, ExactRefV1] = {}
    for relative, expected in SOURCE28_PINS.items():
        path = source_root / relative
        matches = [item for item in base_rows if item.get("relative") == relative]
        if (len(matches) != 1 or type(matches[0].get("bytes")) is not int
                or (matches[0]["bytes"], matches[0].get("sha256")) != expected):
            raise ValueError("Source28 BASE row differs: " + relative)
        raw = _read_exact({"path": str(path), "bytes": expected[0], "sha256": expected[1]}, 2097152)
        loaded[relative] = raw
        before[relative] = _ref(path, raw)
    values = project_war_optional_query_unavailable_v1(
        loaded["xar_autoplayer/bridge/native_driver.py"], loaded["xar_autoplayer/strategy.py"],
        loaded["xar_autoplayer/bridge/war_contract.py"])
    mapping = {"native_driver": "xar_autoplayer/bridge/native_driver.py",
        "war_contract": "xar_autoplayer/bridge/war_contract.py", "strategy": "xar_autoplayer/strategy.py"}
    target_root.mkdir(parents=True, exist_ok=False)
    rows: list[CandidateLeafV1] = []
    typed_values: dict[str, bytes] = {"native_driver": values["native_driver"],
        "strategy": values["strategy"], "war_contract": values["war_contract"]}
    for key, body in typed_values.items():
        relative = mapping[key]
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        readback = target.read_bytes()
        if readback != body:
            raise ValueError("candidate readback differs")
        rows.append({"relative": relative, "before_pin": before[relative],
            "after_pin": _ref(target, readback)})
    manifest: CandidateManifestV1 = {"schema": "xar.Source28-war-only-candidate/v1",
        "machine_id": machine_id, "status": "CANDIDATE_NOT_DEPLOYED",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source28_anchor": source28_anchor, "source28_BASE": source28_BASE,
        "parent_commit": "442beeae4676bad9a9d53cb7070a01f06e965761",
        "producer_ref": _ref(Path(__file__).resolve(), Path(__file__).read_bytes()),
        "input_counter_scope": "one_build_candidate_call_excludes_producer_and_output_hashes",
        "source_leaf_reads": len(loaded), "source_bytes_read": sum(map(len, loaded.values())),
        "source_sha256_bytes_processed": 2 * sum(map(len, loaded.values())),
        "canonical_metadata_bytes_read": len(anchor_raw) + len(base_raw),
        "canonical_metadata_sha256_bytes_processed": 2 * (len(anchor_raw) + len(base_raw)),
        "candidate_bytes_readback_and_compared": sum(len(body) for body in typed_values.values()),
        "runtime_writes": 0, "Game_SDK_RPC_calls": 0, "old_encoder_changed": False,
        "candidatePatch": "optional_war_termination_completion_read_unavailable_v1",
        "files": rows, "new_runtime_leaf_count": 0,
        "no_retroactive_recovery_or_credit": True}
    encoded = (json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    if len(encoded) > 32768:
        raise ValueError("bounded candidate manifest required")
    path = target_root / "CANDIDATE-PATCH01.json"
    with path.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != encoded:
        raise ValueError("manifest readback differs")
    return {"manifest": _ref(path, encoded), "candidate": manifest}
