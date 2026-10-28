"""Exact .3/.4 HUD Decisions opening; no decision-row or product panel action."""
from __future__ import annotations
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Literal, TypedDict
from .version_identity import CK3_12003, CK3_12004, NativeBuildIdentity, require_exact_native_build

STEP = "activate-ingame-decisions-v1"
CAPABILITY = "game.command.activate-ingame-decisions-v1"
EXE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"


def result_build(raw: object) -> NativeBuildIdentity:
    if not isinstance(raw, dict):
        raise ValueError("missing exact native result")
    build = require_exact_native_build(raw.get("game_version"), raw.get("executable_sha256"))
    if build not in (CK3_12003, CK3_12004):
        raise ValueError("requires exact .3/.4 native result")
    return build

def opening_binding(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("missing paused native snapshot")
    character = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise ValueError("missing exact native diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    if not isinstance(hello, dict):
        raise ValueError("missing exact native hello")
    build = require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(character, dict) or character.get("alive") is not True
            or not isinstance(hello, dict) or hello.get("ck3_build_match") is not True
            or hello.get("game_adapter_id") != f"ck3-{build.game_version}-msvc-x64"
            or build not in (CK3_12003, CK3_12004)):
        raise ValueError("requires exact .3/.4 alive paused map")
    values = {"native_revision": snapshot.get("native_revision"),
              "connection_generation": diagnostics.get("connection_generation"),
              "game_pid": hello.get("pid"),
              "played_character_id": character.get("character_id"),
              "date_raw": snapshot.get("date_raw"),
              "episode_run_id": snapshot.get("episode_run_id")}
    for key in ("native_revision", "connection_generation", "game_pid", "played_character_id"):
        val = values[key]
        if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
            raise ValueError(f"invalid {key}")
    if isinstance(values["date_raw"], bool) or not isinstance(values["date_raw"], int):
        raise ValueError("invalid native date")
    return values

def normalize_open_result(raw: object, binding: Mapping[str, object]) -> dict[str, object]:
    result_build(raw)
    if (not isinstance(raw, dict) or raw.get("schema") != "ck3-ingame-decisions-open-v1"
            or raw.get("step") != STEP):
        raise ValueError("malformed exact .3/.4 opening result")
    for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != binding[key]:
            raise ValueError(f"native opening {key} changed")
    for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified",
                "gui_owner_binding_verified", "native_after_read"):
        if raw.get(key) is not True:
            raise ValueError(f"opening proof unavailable: {key}")
    for key in ("before_visible", "dispatch_invoked", "native_after_visible", "native_after_tree_complete", "postcondition_verified", "verification_pending"):
        if type(raw.get(key)) is not bool:
            raise ValueError(f"opening lacks actual {key}")
    if raw["dispatch_invoked"]:
        if (raw["before_visible"] is not False or raw.get("topbar_tree_complete") is not True
                or raw.get("receiver_qualified") is not True):
            raise ValueError("native dispatch lacks complete HUD receiver proof")
    elif raw["before_visible"] is not True:
        raise ValueError("Decisions was neither open nor submitted")
    verified = raw["native_after_tree_complete"] and raw["native_after_visible"]
    if raw["postcondition_verified"] != verified:
        raise ValueError("native visibility proof is inconsistent")
    if raw["verification_pending"] != (raw["dispatch_invoked"] and not verified):
        raise ValueError("native pending proof is inconsistent")
    return dict(raw)

def actual_visible_decisions_tree(tree: object) -> bool:
    if not isinstance(tree, dict) or tree.get("scope_root_name") != "decisions_view" or tree.get("truncated") is not False:
        raise ValueError("Decisions census is incomplete or mismatched")
    if tree.get("root_available") is not True:
        return False
    rows = tree.get("widgets")
    if not isinstance(rows, list):
        raise ValueError("Decisions census rows are absent")
    roots = [row for row in rows if isinstance(row, dict) and row.get("child_path") == ""]
    if len(roots) != 1 or roots[0].get("runtime_name") != "decisions_view":
        raise ValueError("actual Decisions root is unverified")
    return roots[0].get("effective_visible") is True

class DecisionsOpenResultV1(TypedDict):
    schema: Literal["ck3-ingame-decisions-open-v1"]
    proof_kind: Literal["native_open", "current_visibility"]
    status: Literal["verified_visible", "observed_visible_read_only"]
    read_only: bool
    game_version: str
    executable_sha256: str
    native_revision: int
    connection_generation: int
    game_pid: int
    played_character_id: int
    date_raw: int
    episode_run_id: str | None
    queried_revision: int
    postcondition_verified: Literal[True]
    verification_pending: Literal[False]
    dispatch_invoked: bool
    native_ack: dict[str, object] | None
    action_request_id: str | None
    action_claim_path: str | None
    later_decisions_tree: dict[str, object]
    uses_mouse: Literal[False]
    uses_keyboard: Literal[False]
    uses_ocr: Literal[False]


class OpenClaimPinV1(TypedDict):
    path: str
    bytes: int
    sha256: str


class OpenParentV1(TypedDict):
    request_id: str
    claim: OpenClaimPinV1
    result: OpenClaimPinV1
    verified: OpenClaimPinV1


def opening_build_v1(snapshot: object) -> NativeBuildIdentity:
    value = _open_object(snapshot)
    hello = _open_object(_open_object(value.get("diagnostics")).get("hello"))
    return require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))


def opening_public_revision_v1(snapshot: object) -> int:
    return _open_int(_open_object(snapshot).get("revision"), "public revision")


def _open_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ValueError("opening evidence must be an object with string fields")
    return {k: v for k, v in value.items()}


def _open_int(value: object, label: str, *, positive: bool = True) -> int:
    if type(value) is not int or not isinstance(value, int) or (positive and value <= 0):
        raise ValueError("invalid opening integer: " + label)
    return value


def decisions_visibility_v1(tree: object) -> Literal["visible", "hidden"]:
    """Absence or an incomplete census never proves that a window is hidden."""
    value = _open_object(tree)
    rows = value.get("widgets")
    count = value.get("widget_count")
    if (value.get("schema") != "ck3-native-gui-window-tree-inspection-v1"
            or value.get("window_kind") != "decisions" or value.get("read_only") is not True
            or value.get("accepted") is not True or value.get("status") != "available"
            or value.get("scope_root_name") != "decisions_view"
            or value.get("root_available") is not True or value.get("truncated") is not False
            or not isinstance(rows, list) or type(count) is not int
            or not isinstance(count, int) or count != len(rows) or not 1 <= count <= 2048):
        raise ValueError("Decisions visibility requires a complete current native census")
    roots = [_open_object(row) for row in rows if _open_object(row).get("child_path") == ""]
    if len(roots) != 1 or roots[0].get("runtime_name") != "decisions_view":
        raise ValueError("Decisions visibility requires exactly one actual root")
    visible = roots[0].get("effective_visible")
    if type(visible) is not bool:
        raise ValueError("Decisions root visibility must be a boolean")
    return "visible" if visible else "hidden"


def normalize_sdk_open_result(
    raw: object, binding: Mapping[str, object] | None = None,
) -> DecisionsOpenResultV1:
    """Validate SDK UI evidence separately from the unchanged Native ACK contract."""
    value = _open_object(raw)
    if set(value) != set(DecisionsOpenResultV1.__annotations__):
        raise ValueError("SDK Decisions opening fields are missing or unknown")
    result_build(value)
    numbers = {k: _open_int(value.get(k), k, positive=k != "date_raw") for k in (
        "native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw")}
    episode = value.get("episode_run_id")
    if episode is not None and (not isinstance(episode, str) or not episode):
        raise ValueError("invalid opening episode identity")
    if binding is not None and any(value.get(k) != binding.get(k) for k in (*numbers, "episode_run_id")):
        raise ValueError("SDK opening observation crossed its current binding")
    revision = _open_int(value.get("queried_revision"), "queried_revision")
    if (value.get("schema") != "ck3-ingame-decisions-open-v1"
            or value.get("postcondition_verified") is not True
            or value.get("verification_pending") is not False
            or any(value.get(k) is not False for k in ("uses_mouse", "uses_keyboard", "uses_ocr"))
            or decisions_visibility_v1(value.get("later_decisions_tree")) != "visible"):
        raise ValueError("SDK Decisions opening lacks independent current visibility")
    ack: dict[str, object] | None = None
    request: str | None = None
    claim: str | None = None
    dispatch = value.get("dispatch_invoked")
    if type(dispatch) is not bool or not isinstance(dispatch, bool):
        raise ValueError("SDK opening dispatch flag must be boolean")
    kind = value.get("proof_kind")
    if kind == "current_visibility":
        if (value.get("status") != "observed_visible_read_only" or value.get("read_only") is not True
                or dispatch is not False or any(value.get(k) is not None for k in (
                    "native_ack", "action_request_id", "action_claim_path"))
                or any(k not in value for k in ("native_ack", "action_request_id", "action_claim_path"))):
            raise ValueError("read-only visibility must not impersonate a Native action ACK")
        proof: Literal["native_open", "current_visibility"] = "current_visibility"
        status: Literal["verified_visible", "observed_visible_read_only"] = "observed_visible_read_only"
        read_only = True
    elif kind == "native_open":
        ack = normalize_open_result(value.get("native_ack"), numbers)
        if result_build(ack) != result_build(value):
            raise ValueError("SDK opening and Native ACK builds differ")
        request_value, claim_value = value.get("action_request_id"), value.get("action_claim_path")
        if (value.get("status") != "verified_visible" or value.get("read_only") is not False
                or not isinstance(request_value, str) or not request_value.startswith("decisions-")
                or not isinstance(claim_value, str) or not claim_value
                or dispatch != ack["dispatch_invoked"]):
            raise ValueError("Native opening result lacks its exact durable action")
        request, claim = request_value, claim_value
        proof, status, read_only = "native_open", "verified_visible", False
    else:
        raise ValueError("unsupported SDK Decisions proof kind")
    version, sha = value.get("game_version"), value.get("executable_sha256")
    if not isinstance(version, str) or not isinstance(sha, str):
        raise ValueError("missing exact SDK opening build")
    return DecisionsOpenResultV1(
        schema="ck3-ingame-decisions-open-v1", proof_kind=proof, status=status, read_only=read_only,
        game_version=version, executable_sha256=sha, native_revision=numbers["native_revision"],
        connection_generation=numbers["connection_generation"], game_pid=numbers["game_pid"],
        played_character_id=numbers["played_character_id"], date_raw=numbers["date_raw"],
        episode_run_id=episode, queried_revision=revision, postcondition_verified=True,
        verification_pending=False, dispatch_invoked=dispatch, native_ack=ack,
        action_request_id=request, action_claim_path=claim,
        later_decisions_tree=_open_object(value["later_decisions_tree"]),
        uses_mouse=False, uses_keyboard=False, uses_ocr=False)


def _read_open_claim(path: Path) -> tuple[dict[str, object], OpenClaimPinV1]:
    before = path.stat()
    if (before.st_nlink != 1 or getattr(path.lstat(), "st_file_attributes", 0) & 0x400
            or not 0 < before.st_size <= 2097152):
        raise ValueError("opening claim must be a bounded ordinary single-link file")
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("opening evidence changed while reading")
    def fields(rows: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in rows:
            if key in result:
                raise ValueError("duplicate opening JSON field")
            result[key] = item
        return result
    value = _open_object(json.loads(raw, object_pairs_hook=fields))
    return value, OpenClaimPinV1(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def verified_open_parent_v1(directory: Path, identity: Mapping[str, object]) -> OpenParentV1 | None:
    """Read the one successful predecessor chain; never resolve an unknown action."""
    nodes: dict[str, OpenParentV1] = {}
    parents: dict[str, str | None] = {}
    legacy: dict[int, str] = {}
    scope = ("game_pid", "actor_id", "episode_run_id", "decision_key", "action")
    for path in directory.glob("*.claim.json"):
        claim, claim_pin = _read_open_claim(path)
        action = _open_object(claim.get("action_identity"))
        if any(action.get(k) != identity.get(k) for k in scope):
            continue
        if any(type(action.get(k)) is not type(identity.get(k)) for k in scope):
            raise ValueError("opening semantic identity has the wrong JSON type")
        request = claim.get("request_id")
        if not isinstance(request, str) or not request.startswith("decisions-") or request in nodes:
            raise ValueError("invalid or duplicated opening request identity")
        bound = _open_object(claim.get("binding"))
        for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
            _open_int(bound.get(key), key, positive=key != "date_raw")
        if (bound.get("game_pid") != identity.get("game_pid")
                or bound.get("played_character_id") != identity.get("actor_id")
                or bound.get("episode_run_id") != identity.get("episode_run_id")):
            raise ValueError("opening predecessor belongs to a different actor/session")
        receipt, result_pin = _read_open_claim(path.with_suffix(".result.json"))
        verified, verified_pin = _read_open_claim(path.with_suffix(".verified.json"))
        result = _open_object(verified.get("result"))
        if (verified.get("schema") != "ck3-ingame-decision-action-independent-verification-v1"
                or receipt.get("request_id") != request or verified.get("request_id") != request
                or result.get("action_request_id") != request or result.get("action_claim_path") != str(path)
                or result.get("postcondition_verified") is not True or result.get("verification_pending") is not False):
            raise ValueError("opening predecessor verification is invalid")
        native = normalize_open_result(receipt.get("raw"), bound)
        if result.get("native_ack") != native or decisions_visibility_v1(result.get("later_decisions_tree")) != "visible":
            raise ValueError("opening predecessor lacks its original ACK and independent visibility")
        if claim.get("schema") == "ck3-ingame-decisions-once-claim-v1":
            if "proof_kind" in result or "read_only" in result:
                raise ValueError("historical opening evidence cannot declare a new SDK branch")
            sdk = {k: v for k, v in result.items() if k in DecisionsOpenResultV1.__annotations__}
            normalize_sdk_open_result({**sdk, "proof_kind": "native_open", "read_only": False}, bound)
        else:
            normalize_sdk_open_result(result, bound)
        nodes[request] = OpenParentV1(request_id=request, claim=claim_pin, result=result_pin, verified=verified_pin)
        if claim.get("schema") == "ck3-ingame-decisions-once-claim-v1":
            rev = _open_int(action.get("public_revision"), "legacy public revision")
            if rev in legacy:
                raise ValueError("ambiguous historical opening order")
            legacy[rev] = request
        elif claim.get("schema") == "ck3-ingame-decisions-epoch-claim-v2":
            if (any(k not in claim for k in ("parent_request_id", "parent", "closed_observation"))
                    or claim.get("status") != "claimed_result_unknown_no_retry"):
                raise ValueError("opening epoch fields are missing or invalid")
            parent = claim.get("parent_request_id")
            if parent is not None and not isinstance(parent, str):
                raise ValueError("invalid opening parent identity")
            if decisions_visibility_v1(claim.get("closed_observation")) != "hidden":
                raise ValueError("opening epoch lacks its explicit prior Hidden observation")
            parents[request] = parent
        else:
            raise ValueError("unsupported opening claim schema")
    if not nodes:
        return None
    latest = legacy[max(legacy)] if legacy else None
    remaining = dict(parents)
    while remaining:
        children = [r for r, p in remaining.items() if p == latest]
        if len(children) != 1:
            raise ValueError("opening predecessor chain is branched or incomplete")
        latest = children[0]
        child_claim, _ = _read_open_claim(Path(nodes[latest]["claim"]["path"]))
        parent_request = parents[latest]
        expected_parent = None if parent_request is None else nodes.get(parent_request)
        if child_claim.get("parent") != expected_parent:
            raise ValueError("opening epoch parent evidence was changed")
        del remaining[latest]
    if latest is None:
        raise ValueError("opening predecessor chain has no verified head")
    return nodes[latest]


def opening_epoch_key_v1(identity: Mapping[str, object], parent: OpenParentV1 | None) -> str:
    """One CREATE_NEW key per successful parent, independent of revision/reconnect."""
    value = {k: identity[k] for k in ("game_pid", "actor_id", "episode_run_id", "decision_key", "action")}
    value["parent_request_id"] = None if parent is None else parent["request_id"]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()
