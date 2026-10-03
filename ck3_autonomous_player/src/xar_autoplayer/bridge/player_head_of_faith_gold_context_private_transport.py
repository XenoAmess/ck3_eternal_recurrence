"""Read one native ordinary clergy-gold request; never send or select an option."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-head-of-faith-gold-context-v1"
DOMAIN_KEY = "player_head_of_faith_gold_context_v1"
SCHEMA = "ck3_12003_player_head_of_faith_gold_context_v1"
PERMISSION = "allow_private_player_religion_context_query"


def _sampled_group(value: Mapping[str, object], key: str) -> Mapping[str, object]:
    group = value.get(key)
    if not isinstance(group, Mapping) or type(group.get("available")) is not bool:
        raise ValueError(f"native clergy-gold sample group is malformed: {key}")
    reason = group.get("reason")
    if (group["available"] and reason not in (None, "none")) or (
            not group["available"] and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"native clergy-gold sample reason is malformed: {key}")
    return group


def normalize_player_head_of_faith_gold_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve independently sampled native groups and stock-qualified fees."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("native clergy-gold context schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native clergy-gold context belongs to another build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value.get("played_character_id") != actor.get("character_id")
            or value.get("date_raw") != snapshot.get("date_raw")
            or value.get("raw_scale") != 100000
            or type(value.get("available")) is not bool
            or type(value.get("capture_epoch")) is not int
            or value["capture_epoch"] <= 0):
        raise ValueError("native clergy-gold context differs from its queried player frame")
    if not value["available"]:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("native clergy-gold context lost its unavailable reason")
    elif value.get("unavailable_reason") not in (None, "none"):
        raise ValueError("available native clergy-gold context has an unavailable reason")
    identity = _sampled_group(value, "identity")
    if identity["available"] and any(type(identity.get(key)) is not int for key in (
            "requested_head_character_id", "effective_actor_id", "effective_recipient_id")):
        raise ValueError("native clergy-gold requested/effective roles are malformed")
    options = _sampled_group(value, "options")
    if options["available"] and (options.get("all_unselected") is not True
            or type(options.get("declared_count")) is not int
            or options.get("selected_count") != 0):
        raise ValueError("native clergy-gold context is not the ordinary request")
    for key in ("shown", "can_send", "auto_accept"):
        group = _sampled_group(value, key)
        if (group["available"] and type(group.get("value")) is not bool) or (
                not group["available"] and group.get("value") is not None):
            raise ValueError(f"native clergy-gold boolean sample is malformed: {key}")
    costs = _sampled_group(value, "declared_costs")
    raw = costs.get("raw")
    if costs["available"] and (not isinstance(raw, list) or len(raw) != 10
            or any(type(item) is not int for item in raw)
            or costs.get("raw_scale") != 100000 or costs.get("timing") != "on_send"):
        raise ValueError("native clergy-gold declared cost sample is malformed")
    if not costs["available"] and raw is not None:
        raise ValueError("native clergy-gold unsampled declared costs are not null")
    acceptance = value.get("acceptance_preview")
    if not isinstance(acceptance, Mapping):
        raise ValueError("native clergy-gold acceptance preview is malformed")
    for prefix, field in (("recipient_score", "recipient_score_raw"),
                          ("intermediary_score", "intermediary_score_raw"),
                          ("outer", "outer_status")):
        sampled = acceptance.get(prefix + "_available")
        reason = acceptance.get(prefix + "_reason")
        scalar = acceptance.get(field)
        if type(sampled) is not bool or (sampled and (reason not in (None, "none") or type(scalar) is not int)) or (
                not sampled and (not isinstance(reason, str) or not reason or scalar is not None)):
            raise ValueError(f"native clergy-gold acceptance sample is malformed: {prefix}")
    if acceptance["outer_available"] and acceptance["outer_status"] not in (0, 1, 2):
        raise ValueError("native clergy-gold outer answer status is malformed")
    quote = _sampled_group(value, "gold_proceeds")
    if quote["available"] and (quote.get("key") != "hof_ask_for_gold_request_value"
            or quote.get("raw_scale") != 100000 or type(quote.get("amount_raw")) is not int
            or quote.get("root_character_id") != identity.get("effective_recipient_id")
            or quote.get("recipient_character_id") != identity.get("effective_recipient_id")
            or quote.get("actor_character_id") != identity.get("effective_actor_id")):
        raise ValueError("native clergy-gold quote lost its effective-recipient scopes")
    if not quote["available"] and quote.get("amount_raw") is not None:
        raise ValueError("native clergy-gold unsampled quote is not null")
    effect = _sampled_group(value, "acceptance_effect_consequence")
    if effect["available"] and (effect.get("source") != "stock_qualified"
            or effect.get("timing") != "on_accept" or effect.get("raw_scale") != 100000
            or effect.get("piety_raw") != 25000000 or effect.get("hook_selected") is not False):
        raise ValueError("native clergy-gold effect fee lost its stock qualification")
    # The production reader owns group sampling/legality/quote evaluation. Keep
    # the complete native result intact, including false values and null values
    # for unreached groups; do not infer a free request from declared cost0.
    return dict(value)


def query_player_head_of_faith_gold_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-head-of-faith-gold-context-v1",
        )
        if (build != CK3_12003 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native clergy-gold envelope differs from the queried build/frame")
        value = normalize_player_head_of_faith_gold_context_v1(
            result.get("player_head_of_faith_gold_context"), snapshot=before,
        )
        expected_status = "observed" if value["available"] else "unavailable"
        if result.get("status") != expected_status:
            raise ValueError("native clergy-gold envelope lost its source status")
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
