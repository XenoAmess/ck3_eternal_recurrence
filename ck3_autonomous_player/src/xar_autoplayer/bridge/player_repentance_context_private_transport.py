"""Read one native ordinary repentance request; never send or select an option."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-repentance-context-v1"
DOMAIN_KEY = "player_repentance_context_v1"
SCHEMA = "ck3_12003_player_repentance_context_v1"
PERMISSION = "allow_private_player_religion_context_query"


def _sampled_group(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    group = value.get(key)
    if not isinstance(group, Mapping) or type(group.get("available")) is not bool:
        raise ValueError(f"native repentance sample group is malformed: {key}")
    reason = group.get("reason")
    if (group["available"] and reason not in (None, "none")) or (
            not group["available"] and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"native repentance sample reason is malformed: {key}")
    return group


def normalize_player_repentance_context_v1(
    value: object, *, snapshot: Mapping[str, object],
    _candidate_recipient: int | None = None,
) -> dict[str, object]:
    """Preserve independently sampled native groups and single-trait and final request terms."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("native repentance context schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native repentance context belongs to another build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value.get("played_character_id") != actor.get("character_id")
            or value.get("date_raw") != snapshot.get("date_raw")
            or value.get("raw_scale") != 100000
            or type(value.get("available")) is not bool
            or type(value.get("capture_epoch")) is not int
            or value["capture_epoch"] <= 0):
        raise ValueError("native repentance context differs from its queried player frame")
    if not value["available"]:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("native repentance context lost its unavailable reason")
    elif value.get("unavailable_reason") not in (None, "none"):
        raise ValueError("available native repentance context has an unavailable reason")
    identity = _sampled_group(value, "identity")
    if identity["available"] and any(type(identity.get(key)) is not int for key in (
            "requested_recipient_character_id", "effective_actor_id", "effective_recipient_id")):
        raise ValueError("native repentance requested/effective roles are malformed")
    options = _sampled_group(value, "options")
    if options["available"] and (options.get("all_unselected") is not True
            or type(options.get("declared_count")) is not int
            or options.get("selected_count") != 0):
        raise ValueError("native repentance context is not the ordinary request")
    for key in ("shown", "can_send", "auto_accept"):
        group = _sampled_group(value, key)
        if (group["available"] and type(group.get("value")) is not bool) or (
                not group["available"] and group.get("value") is not None):
            raise ValueError(f"native repentance boolean sample is malformed: {key}")
    costs = _sampled_group(value, "declared_costs")
    raw = costs.get("raw")
    if costs["available"] and (not isinstance(raw, list) or len(raw) != 10
            or any(type(item) is not int for item in raw)
            or costs.get("raw_scale") != 100000 or costs.get("timing") != "on_send"):
        raise ValueError("native repentance declared cost sample is malformed")
    if not costs["available"] and raw is not None:
        raise ValueError("native repentance unsampled declared costs are not null")
    acceptance = value.get("acceptance_preview")
    if not isinstance(acceptance, Mapping):
        raise ValueError("native repentance acceptance preview is malformed")
    for prefix, field in (("recipient_score", "recipient_score_raw"),
                          ("intermediary_score", "intermediary_score_raw"),
                          ("outer", "outer_status")):
        sampled = acceptance.get(prefix + "_available")
        reason = acceptance.get(prefix + "_reason")
        scalar = acceptance.get(field)
        if type(sampled) is not bool or (sampled and (reason not in (None, "none") or type(scalar) is not int)) or (
                not sampled and (not isinstance(reason, str) or not reason or scalar is not None)):
            raise ValueError(f"native repentance acceptance sample is malformed: {prefix}")
    if acceptance["outer_available"] and acceptance["outer_status"] not in (0, 1, 2):
        raise ValueError("native repentance outer answer status is malformed")
    trait = _sampled_group(value, "player_excommunication")
    if (trait["available"] and type(trait.get("value")) is not bool) or (
            not trait["available"] and trait.get("value") is not None):
        raise ValueError("native repentance single-trait sample is malformed")
    source = "faith_religious_head_holder_candidate" if _candidate_recipient is None else "native_role_candidate"
    scope = "faith_head_only" if _candidate_recipient is None else "one_observed_role"
    if (value.get("definition_key") != "declaration_of_repentance_interaction"
            or value.get("recipient_source") != source
            or value.get("candidate_scope") != scope
            or (_candidate_recipient is not None and identity.get("requested_recipient_character_id") != _candidate_recipient)):
        raise ValueError("native repentance key/candidate source is malformed")
    ready = (value["available"] and trait.get("value") is True
             and value["shown"].get("value") is True
             and value["can_send"].get("value") is True)
    if type(value.get("ordinary_request_terms_ready")) is not bool or value["ordinary_request_terms_ready"] != ready:
        raise ValueError("native repentance readiness differs from final native terms")
    if _candidate_recipient is None and "recipient_candidates" in value:
        candidates = value["recipient_candidates"]
        if (not isinstance(candidates, Mapping)
                or candidates.get("schema") != "ck3_12003_repentance_recipient_candidates_v1"
                or candidates.get("capture_epoch") != value["capture_epoch"]
                or candidates.get("date_raw") != value["date_raw"]
                or candidates.get("played_character_id") != value["played_character_id"]
                or candidates.get("coverage") not in ("native_current_roles_only", "native_current_roles_and_stock_fallback")
                or candidates.get("complete_stock_preferred_selector") is not False):
            raise ValueError("native repentance candidate scope differs from the queried frame")
        roles = candidates.get("roles")
        rows = candidates.get("candidates")
        if not isinstance(roles, list) or len(roles) != 5 or not isinstance(rows, list):
            raise ValueError("native repentance candidate role collection is malformed")
        for role in roles:
            if (not isinstance(role, Mapping) or type(role.get("available")) is not bool
                    or (role["available"] and type(role.get("character_id")) is not int)
                    or (not role["available"] and role.get("character_id") is not None)):
                raise ValueError("native repentance candidate role sample is malformed")
        first = None
        seen = set()
        for row in rows:
            if not isinstance(row, Mapping) or type(row.get("requested_recipient_character_id")) is not int:
                raise ValueError("native repentance candidate identity is malformed")
            recipient = row["requested_recipient_character_id"]
            if recipient in seen or not isinstance(row.get("sources"), list) or not row["sources"]:
                raise ValueError("native repentance candidate aliases are malformed")
            seen.add(recipient)
            terms = normalize_player_repentance_context_v1(
                row.get("terms"), snapshot=snapshot, _candidate_recipient=recipient & 0xffffffff,
            )
            if first is None and terms["ordinary_request_terms_ready"]:
                first = recipient
        if (candidates.get("first_observed_ordinary_legal_recipient_character_id") != first
                or candidates.get("any_observed_ordinary_request_terms_ready") is not (first is not None)):
            raise ValueError("native repentance candidate readiness differs from final terms")
    if _candidate_recipient is None:
        extensions = {
            "repentance_fallback_sources": "ck3_12003_repentance_fallback_sources_v1",
            "repentance_recovery_inputs": "ck3_12003_repentance_recovery_inputs_v1",
            "repentance_pam_route": "ck3_12003_repentance_pam_route_v1",
            "ordinary_recovery_readiness": "ck3_12003_ordinary_repentance_decision_readiness_v1",
        }
        for key, schema in extensions.items():
            if key not in value:
                continue
            sidecar = value[key]
            if (not isinstance(sidecar, Mapping) or sidecar.get("schema") != schema
                    or sidecar.get("capture_epoch") != value["capture_epoch"]
                    or sidecar.get("played_character_id") != value["played_character_id"]
                    or sidecar.get("date_raw") != value["date_raw"]):
                raise ValueError(f"native repentance sidecar differs from its owner frame: {key}")
        raw_inputs = value.get("repentance_recovery_inputs")
        if isinstance(raw_inputs, Mapping):
            for key in ("pope_excom", "any_held_title_has_clerical_region"):
                group = _sampled_group(raw_inputs, key)
                if (group["available"] and type(group.get("value")) is not bool) or (
                        not group["available"] and group.get("value") is not None):
                    raise ValueError(f"native repentance raw route input is malformed: {key}")
            tier = _sampled_group(raw_inputs, "highest_held_title_tier")
            if (tier["available"] and type(tier.get("value")) is not int) or (
                    not tier["available"] and tier.get("value") is not None):
                raise ValueError("native repentance highest title tier is malformed")
            for key in ("recent_excommunication", "promised_pilgrimage_to_clergy"):
                group = _sampled_group(raw_inputs, key)
                if (group["available"] and type(group.get("present")) is not bool) or (
                        not group["available"] and group.get("present") is not None):
                    raise ValueError(f"native repentance modifier sample is malformed: {key}")
                for field in ("expiry_date_raw", "remaining_calendar_days"):
                    if group.get(field) is not None and type(group[field]) is not int:
                        raise ValueError(f"native repentance modifier expiry is malformed: {key}")
        pam = value.get("repentance_pam_route")
        if isinstance(pam, Mapping):
            if pam.get("evaluator") != "stock_exact_typed_inputs" or pam.get("compiled_named_trigger_invoked") is not False:
                raise ValueError("native repentance PAM route evaluator is malformed")
            for key in ("has_pam_dlc", "faith_qualifies_for_pam_clergy_route",
                        "religious_authority_exists", "capital_clerical_holder_is_religious_authority",
                        "capital_clerical_holder_is_actor", "petition_head_of_faith_repentance_requires_petition",
                        "need_hof_for_clergy_interaction", "is_archbishop_or_higher",
                        "faith_has_central_sacraments", "faith_main_rite_spiritual_head_of_faith"):
                group = _sampled_group(pam, key)
                if (group["available"] and type(group.get("value")) is not bool) or (
                        not group["available"] and group.get("value") is not None):
                    raise ValueError(f"native repentance PAM input is malformed: {key}")
        readiness = value.get("ordinary_recovery_readiness")
        if isinstance(readiness, Mapping):
            candidates = value.get("recipient_candidates")
            if not isinstance(candidates, Mapping) or not isinstance(raw_inputs, Mapping) or not isinstance(pam, Mapping):
                raise ValueError("native ordinary repentance readiness lost its input groups")
            complete = candidates.get("source_candidate_evaluation_complete") is True
            decision_ready = (trait["available"] and raw_inputs.get("available") is True
                              and pam.get("available") is True and complete)
            legal = candidates.get("any_observed_ordinary_request_terms_ready") is True
            if (readiness.get("ordinary_candidate_collection_complete") is not complete
                    or readiness.get("ordinary_recovery_decision_inputs_ready") is not decision_ready
                    or readiness.get("any_observed_ordinary_request_terms_ready") is not legal
                    or readiness.get("ordinary_request_route_currently_absent") != (not legal if decision_ready else None)
                    or readiness.get("first_observed_ordinary_legal_recipient_character_id") != candidates.get("first_observed_ordinary_legal_recipient_character_id")
                    or readiness.get("selected_repentance_petition_terms_ready") is not False):
                raise ValueError("native ordinary repentance decision readiness differs from observed inputs")
    # The production reader owns group sampling/legality/quote evaluation. Keep
    # the complete native result intact, including false values and null values
    # for unreached groups; effect costs and PAM route are separate stock inputs.
    return dict(value)


def query_player_repentance_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-repentance-context-v1",
        )
        if (build != CK3_12003 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native repentance envelope differs from the queried build/frame")
        value = normalize_player_repentance_context_v1(
            result.get("player_repentance_context"), snapshot=before,
        )
        expected_status = "observed" if value["available"] else "unavailable"
        if result.get("status") != expected_status:
            raise ValueError("native repentance envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value,
        **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"],
        "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
