"""Exact .4 RiteCreationWindow actions; private adapter, never a legality model.

The native owner mints the preview identity. Python neither hashes a guessed draft
nor treats an ACK as a new Faith/Rite. Final confirmation has a durable no-retry
claim before the existing real primitive sends its first request.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import ntpath
import sys
from threading import RLock
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .ingame_decisions_open_contract import opening_binding
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

STEP = "player-rite-creation-action-v1"
CAPABILITY = "player_rite_creation_action_v1"
DOMAIN_KEY = CAPABILITY
BODY_KEY = "rite_creation_action"
SCHEMA = "ck3_12004_rite_creation_action_v1"
OPERATIONS = frozenset(("open_create_draft", "open_edit_current_rite_draft", "select_core_tenet",
    "select_doctrine", "set_name_field", "preview", "prepare_confirmation", "confirm_once"))
NAME_FIELDS = frozenset(("name", "adjective", "adherent", "adherent_plural", "description"))
KINDS = frozenset(("create_faith", "create_rite", "edit_rite"))
_KEY = re.compile(r"[a-z0-9_]{1,128}\Z")
_IDENTITY = re.compile(r"[0-9a-f]{64}\Z")
_CLAIM_LOCK = RLock()


def _integer(value: object, label: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid " + label)
    return value


def request_fields(operation: str, expected_source_rite_id: int, **selectors: object) -> dict[str, object]:
    """Definition keys are selectors; actor/Faith/pointers/paths never enter JSON."""
    if operation not in OPERATIONS:
        raise ValueError("unknown Rite creation operation")
    _integer(expected_source_rite_id, "expected_source_rite_id", 0, 0xFFFFFFFE)
    expected = {
        "select_core_tenet": {"core_slot_index", "tenet_key"},
        "select_doctrine": {"group_key", "doctrine_key"},
        "set_name_field": {"name_field", "text"},
        "prepare_confirmation": {"expected_preview_identity", "expected_outcome_kind"},
        "confirm_once": {"expected_preview_identity", "expected_outcome_kind"},
    }.get(operation, set())
    if set(selectors) != expected:
        raise ValueError("unexpected or missing Rite creation selector")
    for key in ("tenet_key", "group_key", "doctrine_key"):
        if key in selectors and (type(selectors[key]) is not str or not _KEY.fullmatch(selectors[key])):
            raise ValueError("invalid definition key: " + key)
    if operation == "select_core_tenet":
        _integer(selectors["core_slot_index"], "core_slot_index", 0, 63)
    if operation == "set_name_field":
        name, text = selectors["name_field"], selectors["text"]
        if type(name) is not str or name not in NAME_FIELDS or type(text) is not str:
            raise ValueError("invalid actual name field")
        maximum = 4096 if name == "description" else 256
        if len(text.encode("utf-8")) > maximum or any(ord(c) < 32 and not (name == "description" and c in "\n\t") for c in text):
            raise ValueError("name text exceeds bounded UTF-8 input or contains control bytes")
    if operation in ("prepare_confirmation", "confirm_once"):
        token, kind = selectors["expected_preview_identity"], selectors["expected_outcome_kind"]
        if type(token) is not str or not _IDENTITY.fullmatch(token) or kind not in KINDS:
            raise ValueError("invalid original preview identity/outcome assertion")
    return {"operation": operation, "expected_source_rite_id": expected_source_rite_id, **selectors}


def _binding(snapshot: Mapping[str, object], expected_revision: int) -> dict[str, object]:
    _integer(expected_revision, "expected_revision", 1, (1 << 64) - 1)
    if snapshot.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("Rite creation public revision changed")
    try:
        bound = opening_binding(snapshot)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    hello = snapshot["diagnostics"]["hello"]
    if require_exact_native_build(hello["expected_ck3_version"], hello["expected_ck3_sha256"]) != CK3_12004:
        raise BridgeUnavailableError("Rite creation actions require exact .4")
    if snapshot.get("episode_projection") == "native_campaign":
        from .title_map_navigation_contract import managed_campaign_title_map_navigation_v1_binding
        try:
            managed_campaign_title_map_navigation_v1_binding(snapshot)
        except ValueError as error:
            raise BridgeUnavailableError(str(error)) from error
        managed = deepcopy(snapshot["managed_campaign_run_binding"])
        # Use the allocator's real persistent state directory. Run ID, frozen
        # argv, connection, date and preview changes cannot create a fresh
        # confirmation scope after an unknown result. This is not a one-life
        # episode and the snapshot/episode_run_id are never rewritten.
        bound["managed_campaign_run_binding"] = managed
        bound["intent_scope"] = {"kind": "managed_campaign_state_v1",
            "state_dir": ntpath.normcase(ntpath.normpath(managed["state_dir"]))}
    elif type(bound["episode_run_id"]) is not str or not bound["episode_run_id"]:
        raise BridgeUnavailableError("Rite creation requires a durable actual episode or verified managed campaign")
    return bound


def _intent_identity_v1(binding: Mapping[str, object], source_rite_id: int) -> dict[str, object]:
    identity = {"played_character_id": binding["played_character_id"], "source_rite_id": source_rite_id}
    if "intent_scope" in binding:
        identity["managed_campaign_intent_scope"] = deepcopy(binding["intent_scope"])
    else:
        identity["episode_run_id"] = binding["episode_run_id"]
    return identity


def normalize_result(raw: object, *, binding: Mapping[str, object], fields: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError("missing original Rite action result")
    if require_exact_native_backend(raw.get("game_version"), raw.get("executable_sha256"),
            raw.get("backend_id"), suffix="rite-creation-action-v1") != CK3_12004:
        raise ValueError("foreign Rite action build")
    if (raw.get("step") != STEP or raw.get("domain_key") != DOMAIN_KEY
            or raw.get("accepted") is not True or raw.get("private_build") is not True
            or raw.get("advertised") is not False
            or raw.get("snapshot_revision") != binding["native_revision"]
            or raw.get("date_raw") != binding["date_raw"]
            or raw.get("read_only") is not (fields["operation"] == "preview")):
        raise ValueError("Rite action envelope frame/operation changed")
    leaf = raw.get(BODY_KEY)
    if not isinstance(leaf, dict) or leaf.get("schema") != SCHEMA or leaf.get("operation") != fields["operation"]:
        raise ValueError("malformed original Rite action leaf")
    for key in ("available", "native_dispatch_attempted", "dispatch_invoked", "verification_pending",
            "original_writer_may_have_been_queued", "business_outcome_observed", "preview_identity_available",
            "complete_command_payload_observed", "original_writer_inputs_observed"):
        if type(leaf.get(key)) is not bool:
            raise ValueError("missing actual Rite action flag: " + key)
    if leaf["business_outcome_observed"] is not False:
        raise ValueError("writer return cannot prove a new Faith/Rite")
    if not leaf["available"] and (type(leaf.get("unavailable_reason")) is not str or not leaf["unavailable_reason"]):
        raise ValueError("unavailable native action lost its diagnostic")
    if leaf["available"] and leaf.get("unavailable_reason") is not None:
        raise ValueError("available native action retains failure")
    if leaf["dispatch_invoked"] and not leaf["native_dispatch_attempted"]:
        raise ValueError("native dispatch flags disagree")
    if fields["operation"] != "confirm_once" and leaf["original_writer_may_have_been_queued"]:
        raise ValueError("preparing the modal is not final submission")
    frame = leaf.get("frame")
    if not isinstance(frame, dict):
        raise ValueError("missing native Rite action frame")
    for key in ("connection_generation", "native_revision", "date_raw", "played_character_id"):
        if type(frame.get(key)) is not int or frame[key] != binding[key]:
            raise ValueError("original Rite action frame changed: " + key)
    _integer(frame.get("capture_epoch"), "capture_epoch", 1, (1 << 64) - 1)
    for key in ("draft", "modal", "full_can", "quote"):
        if not isinstance(leaf.get(key), dict) or type(leaf[key].get("observed")) is not bool:
            raise ValueError("missing actual Rite action component: " + key)
    draft, modal, can, quote = (leaf[key] for key in ("draft", "modal", "full_can", "quote"))
    if draft["observed"] and draft.get("source_rite_id") != fields["expected_source_rite_id"]:
        raise ValueError("actual source Rite differs from assertion")
    for key in ("can_create", "can_edit"):
        if can.get(key) is not None and type(can[key]) is not bool:
            raise ValueError("malformed full native Can")
        if not can["observed"] and can.get(key) is not None:
            raise ValueError("unobserved native Can was filled")
    if quote.get("raw_scale") != 100000:
        raise ValueError("Rite quote raw scale changed")
    for key in ("piety_cost_raw", "piety_missing_signed_raw"):
        if quote.get(key) is not None:
            _integer(quote[key], key, -(1 << 63), (1 << 63) - 1)
    if quote.get("has_enough_piety") is not None and type(quote["has_enough_piety"]) is not bool:
        raise ValueError("malformed original piety admission")
    token = leaf.get("preview_identity")
    if leaf["preview_identity_available"]:
        if (type(token) is not str or not _IDENTITY.fullmatch(token)
                or not all(leaf[key]["observed"] for key in ("draft", "modal", "full_can", "quote"))
                or draft.get("actual_outcome_kind") not in KINDS
                or leaf.get("complete_command_payload_observed") is not True
                or leaf.get("original_writer_inputs_observed") is not True
                or type(leaf.get("native_command_text_bytes")) is not int or leaf["native_command_text_bytes"] <= 0
                or type(leaf.get("native_command_text_sha256")) is not str
                or not _IDENTITY.fullmatch(leaf["native_command_text_sha256"])):
            raise ValueError("preview identity lacks actual native components")
        if (any(type(can.get(key)) is not bool for key in ("can_create", "can_edit"))
                or any(type(quote.get(key)) is not int for key in ("piety_cost_raw", "piety_missing_signed_raw"))
                or type(quote.get("has_enough_piety")) is not bool
                or modal.get("stage") not in ("none", "confirmation")
                or not isinstance(draft.get("names"), dict) or set(draft["names"]) != NAME_FIELDS
                or any(type(value) is not str for value in draft["names"].values())
                or not isinstance(draft.get("selected_core_tenets"), list)
                or not isinstance(draft.get("selected_doctrines"), list)):
            raise ValueError("preview identity filled incomplete original draft/Can/quote inputs")
        for key in ("source_rite_id", "source_faith_id", "actor_faith_id"):
            _integer(draft.get(key), key, 0, 0xFFFFFFFE)
    elif token is not None:
        raise ValueError("unavailable preview identity was invented")
    if fields["operation"] == "confirm_once" and leaf.get("action_id") != fields.get("action_id"):
        raise ValueError("native confirmation action identity changed")
    return {**deepcopy(raw), "business_outcome_verified": False, "action_ready": False,
        "automatic_retry": False, "source_and_runtime_qualification_distinct": True}


def _machine_id() -> str:
    """Reuse the canonical allocator; no copied machine-ID algorithm."""
    path = Path(__file__).resolve().parents[4] / "tools/ck3_live_run_id.py"
    if not path.is_file():
        raise BridgeUnavailableError("canonical machine ID helper is unavailable")
    name = "_xar_rite_creation_live_run_id"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module.current_machine_id()


def _save_exclusive(path: Path, record: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _release_known_unsubmitted(claim: Path, request_id: str, reason: str) -> None:
    """Retain the complete intent before releasing an authoritatively unsent one."""
    with _CLAIM_LOCK:
        original = json.loads(claim.read_text(encoding="utf-8"))
        if original.get("request_id") != request_id:
            raise BridgeUnavailableError("Rite claim changed during known-no-dispatch resolution")
        _save_exclusive(claim.parent / (request_id + ".safe-no-dispatch.json"), {
            "schema": "xar.ck3-rite-confirm-known-no-dispatch.v1", "machine_id": original["machine_id"],
            "observed_at_utc": datetime.now(timezone.utc).isoformat(), "reason": reason, "original_claim": original,
            "automatic_retry": False})
        claim.unlink()


def execute_private_v1(driver: object, *, operation: str, expected_revision: int,
        expected_source_rite_id: int, observed_preview: Mapping[str, object] | None = None,
        **selectors: object) -> dict[str, object]:
    fields = request_fields(operation, expected_source_rite_id, **selectors)
    if getattr(driver, "allow_private_player_rite_creation_actions", False) is not True:
        raise BridgeUnavailableError("private Rite creation actions are disabled")
    if CAPABILITY not in set(driver.capabilities().get("bridge_capabilities", [])):
        raise UnsupportedStepError("this DLL does not implement the exact .4 Rite action candidate")
    before = driver.take_snapshot_without_native_command_history()
    bound = _binding(before, expected_revision)
    root = driver._native_driver_state_path().parent / "rite-creation-actions"
    root.mkdir(parents=True, exist_ok=True)
    request_id = "rite-action-" + uuid.uuid4().hex
    claim = None
    if operation == "confirm_once":
        if observed_preview is None:
            observed_preview = getattr(driver, "_rite_creation_observed_preview_v1", None)
        if not isinstance(observed_preview, Mapping):
            raise BridgeUnavailableError("final confirmation requires an actual post-modal preview")
        preview = normalize_result(dict(observed_preview), binding=bound,
            fields={"operation": "preview", "expected_source_rite_id": expected_source_rite_id})[BODY_KEY]
        draft, modal, can = preview["draft"], preview["modal"], preview["full_can"]
        kind = fields["expected_outcome_kind"]
        if (preview["preview_identity_available"] is not True
                or preview["preview_identity"] != fields["expected_preview_identity"]
                or draft.get("actual_outcome_kind") != kind
                or modal.get("stage") != "confirmation" or modal.get("active") is not True
                or modal.get("same_draft_window_bound") is not True or modal.get("native_can_accept") is not True
                or can.get("can_edit" if kind == "edit_rite" else "can_create") is not True):
            raise BridgeUnavailableError("actual original confirmation/modal/full Can proof is unavailable")
        # Native revision, connection, quote, preview token and requested outcome
        # deliberately do not create a fresh retry scope after an unknown result.
        identity = _intent_identity_v1(bound, expected_source_rite_id)
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        evidence = root / (key + "." + request_id + ".native-result.json")
        claim = root / (key + ".claim.json")
        fields["action_id"] = request_id
        try:
            with _CLAIM_LOCK:
                _save_exclusive(claim, {"schema": "xar.ck3-rite-confirm-once.v1", "machine_id": _machine_id(),
                    "observed_at_utc": datetime.now(timezone.utc).isoformat(), "request_id": request_id,
                    "identity": identity, "binding": bound, "fields": fields,
                    "status": "claimed_result_unknown_no_retry", "native_result_file": evidence.name})
        except FileExistsError as error:
            raise BridgeUnavailableError("Rite confirmation already claimed for this actual source/episode; no retry") from error
    else:
        evidence = root / (request_id + ".native-result.json")
    if operation != "preview":
        driver._rite_creation_observed_preview_v1 = None
    # The existing primitive maps public expected_revision to the real native
    # revision. Its preserved raw command_result retains the native backend_id;
    # its normal return projects that field to native-headless, so is not proof.
    try:
        driver._execute_primitive_step(STEP, expected_revision=expected_revision, required_capability=CAPABILITY,
            request_fields={**fields, "expected_connection_generation": bound["connection_generation"],
                "expected_date_raw": bound["date_raw"], "expected_player_character_id": bound["played_character_id"]},
            include_native_command_history=False, protocol_request_id=request_id,
            protocol_result_evidence_path=evidence)
    except (UnsupportedStepError, PreSubmissionRevisionMismatchError):
        # These exact primitive errors precede endpoint.send. Generic errors,
        # rejection exceptions and timeouts remain unknown and retain the claim.
        if claim is not None:
            _release_known_unsubmitted(claim, request_id, "existing_primitive_rejected_before_endpoint_send")
        raise
    packet = json.loads(evidence.read_text(encoding="utf-8"))
    if (packet.get("type") != "command_result" or packet.get("protocol_version") != 1
            or packet.get("request_id") != request_id or packet.get("ok") is not True):
        raise BridgeUnavailableError("Rite action retained result mismatch; no retry")
    try:
        result = normalize_result(packet.get("result"), binding=bound, fields=fields)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    if operation == "preview" and result[BODY_KEY]["preview_identity_available"]:
        driver._rite_creation_observed_preview_v1 = deepcopy(packet["result"])
    known_no_dispatch = (claim is not None and not result[BODY_KEY]["native_dispatch_attempted"]
        and not result[BODY_KEY]["original_writer_may_have_been_queued"])
    if known_no_dispatch:
        _release_known_unsubmitted(claim, request_id, "matching_original_native_result_proves_no_dispatch_and_no_possible_queue")
    managed_provenance = ({"managed_campaign_run_binding": deepcopy(bound["managed_campaign_run_binding"]),
        "intent_scope": deepcopy(bound["intent_scope"])} if "intent_scope" in bound else {})
    return {**result, **managed_provenance, "episode_run_id": bound["episode_run_id"], "queried_revision": expected_revision,
        "known_no_dispatch_intent_released": known_no_dispatch,
        "native_result_receipt": str(evidence), "action_request_id": request_id,
        "uses_mouse": False, "uses_keyboard": False, "uses_ocr": False}


def collect_private_result_v1(driver: object, *, action_request_id: str,
        timeout_seconds: float = 0.0) -> dict[str, object]:
    """Collect only the retained original result; never dispatch or clear a claim."""
    if type(action_request_id) is not str or not re.fullmatch(r"rite-action-[0-9a-f]{32}", action_request_id):
        raise ValueError("invalid original Rite action request ID")
    if type(timeout_seconds) not in (int, float) or not 0 <= timeout_seconds <= 30:
        raise ValueError("invalid bounded result collection timeout")
    root = driver._native_driver_state_path().parent / "rite-creation-actions"
    matches = []
    for index, path in enumerate(root.glob("*.claim.json")):
        if index >= 128:
            raise BridgeUnavailableError("bounded Rite claim lookup exceeded; retain original request, do not resend")
        claim = json.loads(path.read_text(encoding="utf-8"))
        if claim.get("request_id") == action_request_id:
            matches.append((path, claim))
    if not matches:
        resolved = root / (action_request_id + ".safe-no-dispatch.json")
        if resolved.is_file():
            matches.append((None, json.loads(resolved.read_text(encoding="utf-8"))["original_claim"]))
    if len(matches) != 1 or matches[0][1].get("machine_id") != _machine_id():
        raise BridgeUnavailableError("original local Rite claim is missing or ambiguous")
    claim_path, claim = matches[0]
    filename = claim.get("native_result_file")
    if type(filename) is not str or Path(filename).name != filename:
        raise BridgeUnavailableError("retained Rite claim path is malformed")
    evidence = root / filename
    if evidence.is_file():
        packet = json.loads(evidence.read_text(encoding="utf-8"))
    else:
        if claim_path is None:
            return {"status": "known_no_dispatch", "action_request_id": action_request_id,
                "known_no_dispatch_intent_released": True, "automatic_retry": False,
                "business_outcome_verified": False, "action_ready": False}
        packet = driver.state.wait_for_command_result(action_request_id, float(timeout_seconds))
        if packet is None:
            return {"status": "pending_unknown", "action_request_id": action_request_id,
                "automatic_retry": False, "business_outcome_verified": False, "action_ready": False}
        _save_exclusive(evidence, packet)
    if (packet.get("type") != "command_result" or packet.get("protocol_version") != 1
            or packet.get("request_id") != action_request_id or packet.get("ok") is not True):
        raise BridgeUnavailableError("original Rite result rejected or malformed; claim retained, no resend")
    try:
        result = normalize_result(packet.get("result"), binding=claim["binding"], fields=claim["fields"])
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    known_no_dispatch = (not result[BODY_KEY]["native_dispatch_attempted"]
        and not result[BODY_KEY]["original_writer_may_have_been_queued"])
    if claim_path is not None and known_no_dispatch:
        _release_known_unsubmitted(claim_path, action_request_id, "matching_late_native_result_proves_no_dispatch_and_no_possible_queue")
    return {**result, "status_scope": "original_request_result_only_not_current_legality",
        "known_no_dispatch_intent_released": known_no_dispatch,
        "action_request_id": action_request_id, "native_result_receipt": str(evidence)}


def evaluate_independent_poststate_v1(*, before_snapshot: Mapping[str, object],
        after_snapshot: Mapping[str, object], before_context: Mapping[str, object],
        after_context: Mapping[str, object], expected_outcome_kind: str,
        quoted_piety_cost_raw: int | None) -> dict[str, object]:
    """Use existing actual context/snapshot readers; this function sends nothing.

An identity pattern and a wallet/quote comparison are separate observations.
They do not prove selected doctrine parameters, or that adoption is now legal.
"""
    from .player_religion_context_private_transport import _CONTEXT_KEYS, normalize_player_religion_context_v1
    if expected_outcome_kind not in KINDS:
        raise ValueError("unknown expected native outcome")
    bound = [_binding(snapshot, snapshot.get("revision")) for snapshot in (before_snapshot, after_snapshot)]
    for key in ("connection_generation", "game_pid", "played_character_id", "date_raw", "episode_run_id",
            "intent_scope", "managed_campaign_run_binding"):
        if bound[0].get(key) != bound[1].get(key):
            raise ValueError("poststate crossed owner, actor, episode or paused date")
    contexts = []
    for value, snapshot in ((before_context, before_snapshot), (after_context, after_snapshot)):
        if (value.get("read_only") is not True or value.get("domain_key") != "player_religion_context_v1"
                or value.get("queried_revision") != snapshot.get("revision")
                or value.get("snapshot_revision") != snapshot.get("native_revision")):
            raise ValueError("independent religion query provenance/frame is missing")
        if require_exact_native_backend(value.get("game_version"), value.get("executable_sha256"),
                value.get("backend_id"), suffix="player-religion-context-v1") != CK3_12004:
            raise ValueError("poststate religion query belongs to another build")
        contexts.append(normalize_player_religion_context_v1({key: value[key] for key in _CONTEXT_KEYS}, snapshot=snapshot))
    first, last = contexts
    ids = ("rite_id", "faith_id", "religion_id", "faith_main_rite_id")
    complete = all(value["available"] and all(type(value[key]) is int and value[key] != 0xFFFFFFFF for key in ids) for value in contexts)
    matches = None
    if complete:
        same_religion = first["religion_id"] == last["religion_id"]
        if expected_outcome_kind == "create_faith":
            matches = same_religion and last["faith_id"] != first["faith_id"] and last["rite_id"] != first["rite_id"]
        elif expected_outcome_kind == "create_rite":
            matches = same_religion and last["faith_id"] == first["faith_id"] and last["rite_id"] != first["rite_id"]
        else:
            matches = all(first[key] == last[key] for key in ids)
    wallets = []
    for snapshot in (before_snapshot, after_snapshot):
        wallet = snapshot.get("played_character_piety")
        if wallet is None:
            wallets.append(None)
        elif not isinstance(wallet, dict) or set(wallet) != {"raw", "scale"} or wallet["scale"] != 100000:
            raise ValueError("actual piety wallet is malformed")
        else:
            wallets.append(_integer(wallet["raw"], "piety wallet", -(1 << 63), (1 << 63) - 1))
    if quoted_piety_cost_raw is not None:
        _integer(quoted_piety_cost_raw, "quoted piety cost", -(1 << 63), (1 << 63) - 1)
    delta = wallets[1] - wallets[0] if all(value is not None for value in wallets) else None
    comparison = "unknown" if delta is None or quoted_piety_cost_raw is None else (
        "equal" if delta == -quoted_piety_cost_raw else "different")
    return {"scope": "independent religion identity and actual piety wallet comparison",
        "expected_outcome_kind": expected_outcome_kind, "identity_pattern_matches": matches,
        "before_ids": {key: first[key] for key in ids}, "after_ids": {key: last[key] for key in ids},
        "after_current_rite_is_main": (last["rite_id"] == last["faith_main_rite_id"]) if complete else None,
        "piety_before_raw": wallets[0], "piety_after_raw": wallets[1], "piety_delta_raw": delta,
        "quoted_piety_cost_raw": quoted_piety_cost_raw, "piety_quote_comparison": comparison,
        "edit_payload_changed_observed": False, "other_resource_effects_verified": False,
        "doctrine_parameters_verified": False, "adoption_native_permission_verified": False,
        "business_outcome_verified": False, "action_ready": False,
        "follow_up": "Read actual current/main Rite core and parameter bags, directional hostility and normal adoption Can; edit also requires actual changed payload readback."}
