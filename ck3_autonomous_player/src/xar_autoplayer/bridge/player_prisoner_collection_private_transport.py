"""Unadvertised paused native prisoner collection and narrow lineage values."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance
from .prisoner_keeper_opinion_contract_12004 import normalize_prisoner_keeper_opinion_12004
from .prisoner_release_material_opinion_contract_12004 import (
    normalize_prisoner_release_material_opinion_12004,
)
from .prisoner_release_preview_contract_12003 import normalize_prisoner_release_preview_12003
from .prisoner_native_kinship_contract_12003 import normalize_prisoner_native_kinship_12003
from .prisoner_negotiated_preview_contract_12003 import (
    normalize_prisoner_negotiated_preview_12003, release_option_mask_12003,
)
from .timeline_blocker_private_transport import _binding
from .version_identity import CK3_12003, CK3_12004


STEP = "query-player-prisoner-collection-private-v1"
RANSOM_ORDINAL_STEP_PREFIX = STEP + "-ransom-ordinal-"
SCHEMA = "player-prisoner-collection-private-v1"
_ENVELOPE_KEYS = {
    "step", "accepted", "status", "query_sequence", "observation_revision",
    "snapshot_revision", "player_prisoner_collection", "private_build",
    "read_only", "advertised", "backend_id",
}
_VALUE_KEYS = {
    "schema", "schema_version", "snapshot_revision", "status",
    "unavailable_reason", "date_raw", "played_character_id", "total_count",
    "returned_count", "collection_complete", "prisoners",
}
_VALUE_KEYS_V3 = _VALUE_KEYS | {"played_house_id", "played_dynasty_id"}
_VALUE_KEYS_V4 = _VALUE_KEYS_V3
_VALUE_KEYS_V5 = _VALUE_KEYS_V4
_VALUE_KEYS_V6 = _VALUE_KEYS_V5 | {"played_dread_raw"}
_ROW_KEYS = {"source_ordinal", "prisoner_character_id", "collection_owner_character_id", "jailer_character_id", "custody_relation_verified"}
_LINEAGE_KEYS = {"house_id", "dynasty_id", "same_house", "same_dynasty"}
_CHILD_RELATION_KEYS = {"is_child_of_played_character"}
_TITLE_TIER_KEYS = {"primary_title_tier_raw"}
_RANSOM_QUOTE_KEYS = {
    "private_build", "read_only", "advertised", "action_surface_present",
    "status", "unavailable_reason", "snapshot_id", "public_revision",
    "native_revision", "proof_epoch",
    "date_raw", "definition_key", "jailer_character_id",
    "payer_character_id", "prisoner_character_id", "selected_option",
    "can_send", "quoted_gold_raw", "raw_scale", "recipient_acceptance_raw",
    "recipient_answer_status_raw", "would_accept_now",
    "amount_is_acceptance_time_quote",
}


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _lineage_id(value: object) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0)


def query_player_prisoner_collection_private_v1(
    driver: object, *, expected_revision: int, ransom_ordinal: int = 0,
    release_option_keys: list[str] | None = None,
    release_material_target_character_id: int | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_prisoner_collection_query", False) is not True:
        raise UnsupportedStepError("private prisoner collection query is disabled")
    if not _positive_int(expected_revision):
        raise ValueError("expected_revision must be a positive integer")
    if type(ransom_ordinal) is not int or not 0 <= ransom_ordinal < 64:
        raise ValueError("ransom_ordinal must be an integer from 0 through 63")
    if release_material_target_character_id is not None and (
        type(release_material_target_character_id) is not int
        or not 0 < release_material_target_character_id < 2**32 - 1
    ):
        raise ValueError("release material target must be a positive full character ID")
    release_option_mask_bits = None
    requested_release_option_keys = None
    if release_option_keys is not None:
        release_option_mask_bits = release_option_mask_12003(release_option_keys)
        requested_release_option_keys = list(release_option_keys)
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    played = before.get("played_character")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not _positive_int(native_revision)
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not isinstance(played, Mapping)
        or played.get("alive") is not True
        or not _positive_int(played.get("character_id"))
    ):
        raise BridgeUnavailableError("prisoner collection requires a living player on a paused map frame")
    request_id = "prisoner-collection-" + uuid.uuid4().hex
    provenance = private_native_provenance(before)
    if release_material_target_character_id is not None and (
        provenance.get("exact_ck3_build") != CK3_12004.game_version
        or release_material_target_character_id == played["character_id"]
    ):
        raise BridgeUnavailableError("release material requires an actual4 distinct player-target pair")
    step = STEP if ransom_ordinal == 0 else f"{RANSOM_ORDINAL_STEP_PREFIX}{ransom_ordinal}"
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
    }
    if release_option_mask_bits is not None:
        request["release_option_mask_bits"] = release_option_mask_bits
    if release_material_target_character_id is not None:
        request["release_material_target_character_id"] = release_material_target_character_id
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("private prisoner collection command_result timed out")
    if not isinstance(frame, dict) or frame.get("type") != "command_result" or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id:
        raise BridgeUnavailableError("private prisoner collection command_result is malformed")
    if frame.get("ok") is not True:
        native_error = frame.get("error")
        if not isinstance(native_error, str) or not native_error:
            native_error = "unknown native error"
        raise BridgeUnavailableError(
            f"private prisoner collection native RED: {native_error}"
        )
    envelope = frame.get("result")
    expected_envelope_keys = _ENVELOPE_KEYS
    if release_material_target_character_id is not None:
        expected_envelope_keys = _ENVELOPE_KEYS | {"prisoner_release_material_opinion"}
        if isinstance(envelope, dict) and "prisoner_keeper_opinion" in envelope:
            expected_envelope_keys = expected_envelope_keys | {"prisoner_keeper_opinion"}
    if (
        not isinstance(envelope, dict) or set(envelope) != expected_envelope_keys
        or envelope.get("step") != step or envelope.get("accepted") is not True
        or envelope.get("snapshot_revision") != native_revision
        or envelope.get("private_build") is not True
        or envelope.get("read_only") is not True
        or envelope.get("advertised") is not False
        or envelope.get("backend_id") != "native-headless"
        or not _positive_int(envelope.get("query_sequence"))
        or not _positive_int(envelope.get("observation_revision"))
    ):
        raise BridgeUnavailableError("private prisoner collection envelope is malformed")
    value = envelope.get("player_prisoner_collection")
    if (
        not isinstance(value, dict) or set(value) != (_VALUE_KEYS_V6 if value.get("schema_version") in (6, 7) else (_VALUE_KEYS_V5 if value.get("schema_version") == 5 else (_VALUE_KEYS_V4 if value.get("schema_version") == 4 else (_VALUE_KEYS_V3 if value.get("schema_version") == 3 else _VALUE_KEYS))))
        or value.get("schema") != SCHEMA
        or value.get("schema_version") not in (1, 2, 3, 4, 5, 6, 7)
        or value.get("snapshot_revision") != native_revision
        or value.get("status") != envelope.get("status")
    ):
        raise BridgeUnavailableError("private prisoner collection payload is malformed")
    if value["status"] == "available":
        preview_version = value["schema_version"] in (2, 3, 4, 5, 6, 7)
        lineage_version = value["schema_version"] in (3, 4, 5, 6, 7)
        ransom_version = value["schema_version"] in (4, 5, 6, 7)
        child_relation_version = value["schema_version"] in (5, 6, 7)
        title_tier_version = value["schema_version"] in (6, 7)
        kinship_version = value["schema_version"] == 7
        count = value.get("total_count")
        rows = value.get("prisoners")
        if (
            value.get("unavailable_reason") is not None
            or value.get("date_raw") != date_raw
            or value.get("played_character_id") != played["character_id"]
            or not isinstance(count, int) or isinstance(count, bool)
            or not 0 <= count <= 64 or value.get("returned_count") != count
            or value.get("collection_complete") is not True
            or not isinstance(rows, list) or len(rows) != count
            or (lineage_version and (
                not _lineage_id(value.get("played_house_id"))
                or not _lineage_id(value.get("played_dynasty_id"))
                or (value.get("played_house_id") is None and value.get("played_dynasty_id") is not None)
            ))
            or (title_tier_version and (
                type(value.get("played_dread_raw")) is not int
                or value["played_dread_raw"] < 0
            ))
        ):
            raise BridgeUnavailableError("private prisoner collection count or binding is malformed")
        if ransom_ordinal and (not ransom_version or ransom_ordinal >= count):
            raise BridgeUnavailableError("requested prisoner ransom ordinal is absent")
        if release_option_mask_bits is not None and ransom_ordinal >= count:
            raise BridgeUnavailableError("requested negotiated release ordinal is absent")
        seen: set[int] = set()
        for ordinal, row in enumerate(rows):
            if (
                not isinstance(row, dict)
                or set(row) != (_ROW_KEYS | ({"unconditional_release_preview"} if preview_version else set()) | (_LINEAGE_KEYS if lineage_version else set()) | ({"ransom_quote_preview"} if ransom_version else set()) | (_CHILD_RELATION_KEYS if child_relation_version else set()) | (_TITLE_TIER_KEYS if title_tier_version else set()) | ({"native_kinship"} if kinship_version else set()) | ({"negotiated_release_preview"} if release_option_mask_bits is not None else set()))
                or row.get("source_ordinal") != ordinal
                or not _positive_int(row.get("prisoner_character_id"))
                or row["prisoner_character_id"] > 0xFFFFFFFF
                or row["prisoner_character_id"] == played["character_id"]
                or row["prisoner_character_id"] in seen
                or row.get("collection_owner_character_id") != played["character_id"]
                or row.get("jailer_character_id") != played["character_id"]
                or row.get("custody_relation_verified") is not True
            ):
                raise BridgeUnavailableError("private prisoner collection row is malformed")
            if lineage_version:
                house_id = row.get("house_id")
                dynasty_id = row.get("dynasty_id")
                if (
                    not _lineage_id(house_id)
                    or not _lineage_id(dynasty_id)
                    or (house_id is None and dynasty_id is not None)
                    or type(row.get("same_house")) is not bool
                    or type(row.get("same_dynasty")) is not bool
                    or row["same_house"] != (house_id is not None and house_id == value["played_house_id"])
                    or row["same_dynasty"] != (dynasty_id is not None and dynasty_id == value["played_dynasty_id"])
                ):
                    raise BridgeUnavailableError("private prisoner lineage is malformed")
            if child_relation_version and type(row.get("is_child_of_played_character")) is not bool:
                raise BridgeUnavailableError("private prisoner child relation is malformed")
            if title_tier_version and (
                row.get("primary_title_tier_raw") is not None
                and (type(row["primary_title_tier_raw"]) is not int
                     or not 1 <= row["primary_title_tier_raw"] <= 6)
            ):
                raise BridgeUnavailableError("private prisoner title tier is malformed")
            if preview_version:
                preview = row["unconditional_release_preview"]
                if (provenance.get("exact_ck3_build"), provenance.get("exe_sha256")) in {
                    (CK3_12003.game_version, CK3_12003.executable_sha256),
                    (CK3_12004.game_version, CK3_12004.executable_sha256),
                }:
                    try:
                        preview = normalize_prisoner_release_preview_12003(
                            preview, native_revision=native_revision, date_raw=date_raw,
                            player_character_id=played["character_id"],
                            prisoner_character_id=row["prisoner_character_id"],
                        )
                    except ValueError as error:
                        raise BridgeUnavailableError(str(error)) from error
                    if preview.get("status") == "available" and preview["proof_epoch"] != envelope["observation_revision"]:
                        raise BridgeUnavailableError("private release preview differs from its collection observation")
                    row["unconditional_release_preview"] = preview
                if (
                    not isinstance(preview, dict)
                    or preview.get("private_build") is not True
                    or preview.get("read_only") is not True
                    or preview.get("advertised") is not False
                    or preview.get("action_surface_present") is not False
                ):
                    raise BridgeUnavailableError("private release preview envelope is malformed")
                if preview.get("status") == "available":
                    definition = preview.get("definition")
                    roles = preview.get("roles")
                    acceptance = preview.get("acceptance")
                    costs = preview.get("costs")
                    readiness = preview.get("readiness")
                    if (
                        preview.get("snapshot_id") != f"native:{native_revision}"
                        or preview.get("public_revision") != native_revision
                        or preview.get("native_revision") != native_revision
                        or preview.get("date_raw") != date_raw
                        or not isinstance(definition, dict)
                        or definition.get("canonical_key") != "release_from_prison_interaction"
                        or preview.get("payload_shape") != "two_role_all_release_options_off"
                        or not isinstance(roles, dict)
                        or roles.get("actor_character_id") != played["character_id"]
                        or roles.get("recipient_character_id") != row["prisoner_character_id"]
                        or preview.get("unconditional_prisoner_release") is not True
                        or type(preview.get("can_send")) is not bool
                        or not isinstance(acceptance, dict)
                        or acceptance.get("kind") != "auto_accept"
                        or acceptance.get("auto_accept") is not True
                        or acceptance.get("would_accept_now") is not True
                        or not isinstance(costs, dict)
                        or costs.get("raw_scale") != 100_000
                        or not isinstance(costs.get("entries"), list)
                        or len(costs["entries"]) != 10
                        or not isinstance(readiness, dict)
                        or readiness.get("same_frame_ready") is not True
                    ):
                        raise BridgeUnavailableError("private release final preview is malformed")
                elif preview.get("status") == "unavailable":
                    if set(preview) != {"private_build", "read_only", "advertised", "action_surface_present", "status", "unavailable_reason"} or not isinstance(preview.get("unavailable_reason"), str) or not preview["unavailable_reason"]:
                        raise BridgeUnavailableError("private release unavailable preview is malformed")
                else:
                    raise BridgeUnavailableError("private release preview status is malformed")
            if ransom_version:
                quote = row["ransom_quote_preview"]
                if (
                    not isinstance(quote, dict)
                    or quote.get("private_build") is not True
                    or quote.get("read_only") is not True
                    or quote.get("advertised") is not False
                    or quote.get("action_surface_present") is not False
                ):
                    raise BridgeUnavailableError("private ransom quote envelope is malformed")
                if quote.get("status") == "available":
                    option = quote.get("selected_option")
                    answer = quote.get("recipient_answer_status_raw")
                    if (
                        set(quote) != _RANSOM_QUOTE_KEYS
                        or quote.get("unavailable_reason") is not None
                        or quote.get("snapshot_id") != f"native:{native_revision}"
                        or quote.get("public_revision") != native_revision
                        or quote.get("native_revision") != native_revision
                        or quote.get("proof_epoch") != envelope["observation_revision"]
                        or quote.get("date_raw") != date_raw
                        or quote.get("definition_key") != "ransom_interaction"
                        or quote.get("jailer_character_id") != played["character_id"]
                        or quote.get("prisoner_character_id") != row["prisoner_character_id"]
                        or not _positive_int(quote.get("payer_character_id"))
                        or quote["payer_character_id"] == played["character_id"]
                        or option not in ("gold", "current_gold")
                        or quote.get("can_send") is not True
                        or not _positive_int(quote.get("quoted_gold_raw"))
                        or quote.get("raw_scale") != 100_000
                        or type(quote.get("recipient_acceptance_raw")) is not int
                        or type(answer) is not int or answer not in (0, 1, 2)
                        or quote.get("would_accept_now") is not (answer != 2)
                        or quote.get("amount_is_acceptance_time_quote") is not (option == "current_gold")
                    ):
                        raise BridgeUnavailableError("private ransom final quote is malformed")
                elif quote.get("status") == "unavailable":
                    count_mismatch = quote.get("unavailable_reason") == "option_definition_count_unexpected"
                    mask_unexpected = quote.get("unavailable_reason") == "option_mask_unexpected"
                    mask_diagnostic = mask_unexpected and (
                        "requested_option_index" in quote
                        or "observed_option_mask_bits" in quote
                    )
                    expected_keys = {"private_build", "read_only", "advertised", "action_surface_present", "status", "unavailable_reason"}
                    if count_mismatch:
                        expected_keys |= {"observed_definition_option_count", "observed_context_option_count"}
                    if mask_diagnostic:
                        expected_keys |= {"requested_option_index", "observed_option_mask_bits"}
                    definition_count = quote.get("observed_definition_option_count")
                    context_count = quote.get("observed_context_option_count")
                    requested_option = quote.get("requested_option_index")
                    observed_mask = quote.get("observed_option_mask_bits")
                    if (
                        set(quote) != expected_keys
                        or not isinstance(quote.get("unavailable_reason"), str)
                        or not quote["unavailable_reason"]
                        or (count_mismatch and (
                            type(definition_count) is not int
                            or not -(2 ** 31) <= definition_count < 2 ** 31
                            or (context_count is not None and (
                                type(context_count) is not int
                                or not -(2 ** 31) <= context_count < 2 ** 31
                            ))
                        ))
                        or (mask_diagnostic and (
                            type(requested_option) is not int
                            or requested_option not in (0, 1, 2, 3)
                            or type(observed_mask) is not int
                            or not 1 <= observed_mask <= 0xFF
                            or observed_mask == 1 << requested_option
                        ))
                    ):
                        raise BridgeUnavailableError("private ransom unavailable quote is malformed")
                else:
                    raise BridgeUnavailableError("private ransom quote status is malformed")
            if kinship_version:
                try:
                    row["native_kinship"] = normalize_prisoner_native_kinship_12003(
                        row["native_kinship"], native_revision=native_revision,
                        date_raw=date_raw, proof_epoch=envelope["observation_revision"],
                        player_character_id=played["character_id"],
                        prisoner_character_id=row["prisoner_character_id"],
                        source_ordinal=ordinal, selected_ordinal=ransom_ordinal,
                    )
                except ValueError as error:
                    raise BridgeUnavailableError(str(error)) from error
            if release_option_mask_bits is not None:
                try:
                    negotiated = normalize_prisoner_negotiated_preview_12003(
                        row["negotiated_release_preview"],
                        native_revision=native_revision, date_raw=date_raw,
                        player_character_id=played["character_id"],
                        prisoner_character_id=row["prisoner_character_id"],
                        requested_option_mask_bits=release_option_mask_bits,
                    )
                except ValueError as error:
                    raise BridgeUnavailableError(str(error)) from error
                if negotiated.get("status") == "available" and negotiated["proof_epoch"] != envelope["observation_revision"]:
                    raise BridgeUnavailableError("negotiated release differs from its collection observation")
                if (negotiated.get("unavailable_reason") == "not_evaluated") is (ordinal == ransom_ordinal):
                    raise BridgeUnavailableError("negotiated release evaluated the wrong prisoner ordinal")
                row["negotiated_release_preview"] = negotiated
            seen.add(row["prisoner_character_id"])
        if ransom_version and ransom_ordinal:
            for ordinal, row in enumerate(rows):
                quote = row["ransom_quote_preview"]
                if (quote.get("unavailable_reason") == "not_evaluated") is (ordinal == ransom_ordinal):
                    raise BridgeUnavailableError("private ransom quote evaluated the wrong prisoner ordinal")
    elif value["status"] == "unavailable":
        if (
            not isinstance(value.get("unavailable_reason"), str)
            or not value["unavailable_reason"]
            or any(value.get(key) is not None for key in (
                "date_raw", "played_character_id", "total_count", "returned_count",
                "played_house_id", "played_dynasty_id", "played_dread_raw",
            ))
            or value.get("collection_complete") is not False
            or value.get("prisoners") != []
        ):
            raise BridgeUnavailableError("private prisoner collection unavailable result is malformed")
    else:
        raise BridgeUnavailableError("private prisoner collection status is malformed")
    if release_material_target_character_id is not None:
        try:
            envelope["prisoner_release_material_opinion"] = normalize_prisoner_release_material_opinion_12004(
                envelope["prisoner_release_material_opinion"], native_revision=native_revision,
                date_raw=date_raw, player_character_id=played["character_id"],
                target_character_id=release_material_target_character_id,
            )
            if "prisoner_keeper_opinion" in envelope:
                envelope["prisoner_keeper_opinion"] = normalize_prisoner_keeper_opinion_12004(
                    envelope["prisoner_keeper_opinion"], native_revision=native_revision,
                    date_raw=date_raw, player_character_id=played["character_id"],
                    target_character_id=release_material_target_character_id,
                )
        except ValueError as error:
            raise BridgeUnavailableError(str(error)) from error
    if _binding(driver.take_snapshot()) != _binding(before):
        raise BridgeUnavailableError("private prisoner collection crossed its paused frame")
    result = {**envelope, **provenance,
              "queried_snapshot_id": before.get("snapshot_id"),
              "queried_revision": before.get("revision"),
              "queried_native_revision": native_revision}
    if release_material_target_character_id is not None:
        result["queried_release_material_target_character_id"] = release_material_target_character_id
    if release_option_mask_bits is not None:
        result.update({
            "queried_release_option_keys": requested_release_option_keys,
            "queried_release_option_mask_bits": release_option_mask_bits,
        })
    return result
