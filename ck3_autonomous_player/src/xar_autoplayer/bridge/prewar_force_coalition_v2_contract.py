"""Declaration-bound current inventory evidence and an explicit force policy.

V2 can qualify a complete same-frame force comparison. Its actor floor is the
actual native mobilization-qualified lower: the maximum of proven raisable
unraised troops and independently commandable owned current troops. It does
not sum components whose physical separation has not been established.
It is not an arrival prediction or a combat guarantee. The
underlying physical inventory floor alone cannot supply this action credit.
Its enemy ceiling is
the union of currently owned inventory for all observed potential initial
defenders. Future recruitment, regeneration, hires and movement are outside
this inventory scope; they are not implicit permanent missing domains.

The caller independently leases the before-query snapshot and declaration.
Request binding comes from the current envelope's independent TOP execution
receipt after matching its fresh request ID, never from this domain or a
historical cache. Connection/episode and after-query leases remain outside.
No second native query or predicted mailbox ticket is required.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .prewar_force_coalition_contract import (
    _boolean,
    _character,
    _count,
    _declaration,
    _integer,
    _native_character,
    _object,
    _reason,
    _selected,
)
from .version_identity import CK3_12004, require_exact_native_build


SCHEMA_VERSION = 2
INVENTORY_SCOPE = "same_frame_owned_current_inventory_v1"
FINAL_ROLES_SOURCE = "finalized_selected_cb_context"
_UINT64_MAX = (1 << 64) - 1
_INT64_MAX = (1 << 63) - 1
_INT32_MAX = (1 << 31) - 1
_FIELDS = frozenset({
    "schema_version", "status", "read_only", "game_version",
    "executable_sha256", "capture_epoch", "native_revision",
    "public_revision", "date_raw", "actor_character_id", "declaration_id",
    "selected_declaration", "effective_target_character_id", "ticket",
    "query_sequence", "two_round_observation", "final_cb_roles",
    "potential_enemy_participants", "owner_forces", "actor_lower_soldiers",
    "enemy_upper_soldiers", "enemy_force_coverage_complete",
    "complete_initial_participants_ready", "missing_required_domains",
    "native_mobilization_qualification",
})
_REQUEST_FIELDS = frozenset({"request_id", "ticket", "query_sequence", "capture_epoch"})
_ROUND_FIELDS = frozenset({
    "round_count", "complete_dto_equal", "frame_binding_equal", "unavailable_reason",
})
_ROLE_FIELDS = frozenset({
    "available", "unavailable_reason", "primary_attacker_character_id",
    "primary_defender_character_id", "source", "native_fallback", "final_can_send",
})
_PARTICIPANTS_FIELDS = frozenset({
    "available", "unavailable_reason", "collection_complete", "participants",
    "current_allies_complete", "holy_joiners_complete",
    "additional_supporters_complete", "selected_cb_initial_complete",
})
_PARTICIPANT_FIELDS = frozenset({"character_id", "sources"})
_OWNER_FIELDS = frozenset({
    "owner_character_id", "actor_lower_soldiers", "actor_lower_ready",
    "inventory_upper_soldiers", "inventory_upper_ready", "inventory_scope",
    "unavailable_reasons",
})
MOBILIZATION_SOURCE = "actual4_raise_command_final_validator_and_owned_current_rosters"
_MOBILIZATION_FIELDS = frozenset({
    "available", "unavailable_reason", "source", "native_raise_legal",
    "default_raise_province_id", "unraised_lower_soldiers", "unraised_lower_ready",
    "raised_commandable_lower_soldiers", "raised_lower_ready",
    "executable_lower_soldiers", "executable_lower_ready",
    "physical_inventory_lower_soldiers", "native_unraised_stock_soldiers",
    "native_unraised_stock_ready", "component_combination",
})
PARTICIPANT_SOURCES = frozenset({
    "primary_defender", "current_ally", "holy_war_joiner", "contract_subject",
    "contract_suzerain", "confederation_member", "same_house", "immediate_liege",
    "top_liege", "diarch", "religious_authority", "religious_follower",
    "forced_initial_participant",
})
_COMPLETE_DOMAINS = (
    ("current_allies_complete", "potential_enemy_current_allies"),
    ("holy_joiners_complete", "potential_enemy_holy_joiners"),
    ("additional_supporters_complete", "potential_enemy_additional_supporters"),
    ("selected_cb_initial_complete", "selected_cb_initial_participants"),
)
MISSING_REQUIRED_DOMAINS = frozenset({
    "same_frame_two_round_observation", "final_cb_roles",
    "potential_enemy_participants", "potential_enemy_current_allies",
    "potential_enemy_holy_joiners", "potential_enemy_additional_supporters",
    "selected_cb_initial_participants", "actor_current_inventory_lower",
    "enemy_current_inventory_upper", "enemy_upper_aggregate_overflow",
    "native_mobilization_qualification",
})
_POLICY_FIELDS = frozenset({
    "policy_id", "scope", "minimum_actor_to_enemy_ratio_numerator",
    "minimum_actor_to_enemy_ratio_denominator", "assumption",
})
DEFAULT_PREWAR_FORCE_RISK_POLICY_V2 = MappingProxyType({
    "policy_id": "prewar-current-inventory-force-risk-3-to-2-v1",
    "scope": INVENTORY_SCOPE,
    "minimum_actor_to_enemy_ratio_numerator": 3,
    "minimum_actor_to_enemy_ratio_denominator": 2,
    "assumption": "policy_margin_not_calibrated_probability",
})


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"prewar v2 {name} must be nonempty text without surrounding whitespace")
    return value


def _texts(value: object, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"prewar v2 {name} must be a text array")
    result = [_text(item, f"{name}[{index}]") for index, item in enumerate(value)]
    if len(set(result)) != len(result):
        raise ValueError(f"prewar v2 {name} repeats an entry")
    return result


def _native_role(value: object, name: str) -> int | None:
    return None if value is None else _native_character(value, name)


def _mobilization(value: object) -> dict[str, object]:
    row = _object(value, _MOBILIZATION_FIELDS, "native_mobilization_qualification")
    available = _boolean(row["available"], "native_mobilization_qualification.available")
    reason = _reason(row["unavailable_reason"], "native_mobilization_qualification.unavailable_reason", available)
    if row["source"] != MOBILIZATION_SOURCE:
        raise ValueError("prewar v2 mobilization must come from actual native command validation and owned rosters")
    if row["component_combination"] != "maximum_proven_component":
        raise ValueError("prewar v2 mobilization cannot sum components without a distinct physical-source proof")
    physical = _count(row["physical_inventory_lower_soldiers"], "native_mobilization_qualification.physical_inventory_lower_soldiers", nullable=True)
    stock = row["native_unraised_stock_soldiers"]
    if stock is not None:
        _integer(stock, "native_mobilization_qualification.native_unraised_stock_soldiers", -(1 << 31), _INT32_MAX)
    stock_ready = _boolean(row["native_unraised_stock_ready"], "native_mobilization_qualification.native_unraised_stock_ready")
    if stock_ready and (stock is None or stock < 0):
        raise ValueError("prewar v2 ready native unraised stock requires a nonnegative actual int32 count")
    legal = _boolean(row["native_raise_legal"], "native_mobilization_qualification.native_raise_legal", nullable=True)
    province = row["default_raise_province_id"]
    if province is not None:
        _integer(province, "native_mobilization_qualification.default_raise_province_id", 1, _INT32_MAX)
    if legal is not None and province is None:
        raise ValueError("prewar v2 a native raise verdict requires its actual default province")
    unraised_ready = _boolean(row["unraised_lower_ready"], "native_mobilization_qualification.unraised_lower_ready")
    unraised = _count(row["unraised_lower_soldiers"], "native_mobilization_qualification.unraised_lower_soldiers", nullable=True)
    raised_ready = _boolean(row["raised_lower_ready"], "native_mobilization_qualification.raised_lower_ready")
    raised = _count(row["raised_commandable_lower_soldiers"], "native_mobilization_qualification.raised_commandable_lower_soldiers", nullable=True)
    executable_ready = _boolean(row["executable_lower_ready"], "native_mobilization_qualification.executable_lower_ready")
    executable = _count(row["executable_lower_soldiers"], "native_mobilization_qualification.executable_lower_soldiers", nullable=True)
    if (
        unraised_ready is not (unraised is not None)
        or raised_ready is not (raised is not None)
        or executable_ready is not (executable is not None)
        or available is not executable_ready
    ):
        raise ValueError("prewar v2 mobilization readiness contradicts a nullable certified bound")
    expected_unraised_ready = physical is not None and stock_ready is True
    if unraised_ready is not expected_unraised_ready or unraised != (
        min(physical, stock) if expected_unraised_ready else None
    ):
        raise ValueError("prewar v2 unraised floor must be bounded by actual native unraised stock and physical inventory")
    if executable_ready:
        contributions: list[int] = []
        if raised_ready:
            contributions.append(raised)
        if legal is True and unraised_ready:
            contributions.append(unraised)
        if not contributions or executable != max(contributions):
            raise ValueError("prewar v2 executable lower must be the maximum actually proven component")
    return {
        "available": available, "unavailable_reason": reason, "source": MOBILIZATION_SOURCE,
        "native_raise_legal": legal, "default_raise_province_id": province,
        "unraised_lower_soldiers": unraised, "unraised_lower_ready": unraised_ready,
        "raised_commandable_lower_soldiers": raised, "raised_lower_ready": raised_ready,
        "executable_lower_soldiers": executable, "executable_lower_ready": executable_ready,
        "physical_inventory_lower_soldiers": physical,
        "native_unraised_stock_soldiers": stock, "native_unraised_stock_ready": stock_ready,
        "component_combination": "maximum_proven_component",
    }


def _rounds(value: object) -> tuple[dict[str, object], bool]:
    row = _object(value, _ROUND_FIELDS, "two_round_observation")
    count = _integer(row["round_count"], "two_round_observation.round_count", 2, 2)
    equal = _boolean(row["complete_dto_equal"], "two_round_observation.complete_dto_equal")
    frame_equal = _boolean(row["frame_binding_equal"], "two_round_observation.frame_binding_equal")
    ready = equal is True and frame_equal is True
    reason = _reason(row["unavailable_reason"], "two_round_observation.unavailable_reason", ready)
    return {
        "round_count": count, "complete_dto_equal": equal,
        "frame_binding_equal": frame_equal, "unavailable_reason": reason,
    }, ready


def _roles(value: object) -> dict[str, object]:
    row = _object(value, _ROLE_FIELDS, "final_cb_roles")
    available = _boolean(row["available"], "final_cb_roles.available")
    reason = _reason(row["unavailable_reason"], "final_cb_roles.unavailable_reason", available)
    if row["source"] != FINAL_ROLES_SOURCE:
        raise ValueError("prewar v2 final CB roles must come from the finalized selected context")
    attacker = _native_role(row["primary_attacker_character_id"], "final_cb_roles.primary_attacker_character_id")
    defender = _native_role(row["primary_defender_character_id"], "final_cb_roles.primary_defender_character_id")
    fallback = _boolean(row["native_fallback"], "final_cb_roles.native_fallback", nullable=True)
    can_send = _boolean(row["final_can_send"], "final_cb_roles.final_can_send", nullable=True)
    if available and (attacker is None or defender is None):
        raise ValueError("prewar v2 ready final CB roles lost an actual receiver")
    if attacker is not None and attacker == defender:
        raise ValueError("prewar v2 final CB primary sides collapse")
    # A legitimate native fallback can settle actual roles. The observed
    # nullable fallback flag itself is not a universal false-only gate.
    return {
        "available": available, "unavailable_reason": reason,
        "primary_attacker_character_id": attacker,
        "primary_defender_character_id": defender, "source": FINAL_ROLES_SOURCE,
        "native_fallback": fallback, "final_can_send": can_send,
    }


def _participants(value: object, roles: Mapping[str, object]) -> tuple[dict[str, object], bool]:
    row = _object(value, _PARTICIPANTS_FIELDS, "potential_enemy_participants")
    available = _boolean(row["available"], "potential_enemy_participants.available")
    complete = _boolean(row["collection_complete"], "potential_enemy_participants.collection_complete")
    reason = _reason(row["unavailable_reason"], "potential_enemy_participants.unavailable_reason", available)
    if available is not complete:
        raise ValueError("prewar v2 participant availability must describe the complete potential collection")
    completeness = {
        key: _boolean(row[key], f"potential_enemy_participants.{key}")
        for key, _ in _COMPLETE_DOMAINS
    }
    raw = row["participants"]
    if not isinstance(raw, list):
        raise ValueError("prewar v2 participants must preserve the observed participant array")
    participants: list[dict[str, object]] = []
    seen: set[int] = set()
    primary_rows = 0
    for index, item in enumerate(raw):
        name = f"potential_enemy_participants.participants[{index}]"
        participant = _object(item, _PARTICIPANT_FIELDS, name)
        character = _native_character(participant["character_id"], f"{name}.character_id")
        sources = _texts(participant["sources"], f"{name}.sources")
        if character in seen or not sources or not set(sources) <= PARTICIPANT_SOURCES:
            raise ValueError("prewar v2 participants repeat an owner or lose known provenance")
        seen.add(character)
        if "primary_defender" in sources:
            primary_rows += 1
            defender = roles["primary_defender_character_id"]
            if defender is not None and character != defender:
                raise ValueError("prewar v2 primary-defender provenance differs from finalized CB roles")
        participants.append({"character_id": character, "sources": sources})
    if primary_rows > 1:
        raise ValueError("prewar v2 potential participants repeat primary-defender provenance")
    if available and (
        roles["available"] is not True or primary_rows != 1
        or not all(value is True for value in completeness.values())
    ):
        raise ValueError("prewar v2 complete participants lack finalized roles or a required supporter domain")
    ready = available is True and roles["available"] is True
    return {
        "available": available, "unavailable_reason": reason,
        "collection_complete": complete, "participants": participants,
        **completeness,
    }, ready


def _owners(
    value: object, *, actor: int, roles: Mapping[str, object],
    participants: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[int, dict[str, object]]]:
    if not isinstance(value, list):
        raise ValueError("prewar v2 owner_forces must be an array")
    enemy_owners = {row["character_id"] for row in participants}
    expected = {actor, *enemy_owners}
    for key in ("primary_attacker_character_id", "primary_defender_character_id"):
        if roles[key] is not None:
            expected.add(roles[key])
    by_owner: dict[int, dict[str, object]] = {}
    result: list[dict[str, object]] = []
    for index, raw in enumerate(value):
        name = f"owner_forces[{index}]"
        row = _object(raw, _OWNER_FIELDS, name)
        owner = _native_character(row["owner_character_id"], f"{name}.owner_character_id")
        if owner in by_owner or owner not in expected:
            raise ValueError("prewar v2 owner_forces repeat an owner or invent a scope member")
        lower_ready = _boolean(row["actor_lower_ready"], f"{name}.actor_lower_ready")
        lower = _count(row["actor_lower_soldiers"], f"{name}.actor_lower_soldiers", nullable=True)
        upper_ready = _boolean(row["inventory_upper_ready"], f"{name}.inventory_upper_ready")
        upper = _count(row["inventory_upper_soldiers"], f"{name}.inventory_upper_soldiers", nullable=True)
        reasons = _texts(row["unavailable_reasons"], f"{name}.unavailable_reasons")
        if row["inventory_scope"] != INVENTORY_SCOPE:
            raise ValueError("prewar v2 owner inventory has a different force-bound scope")
        if lower_ready is not (lower is not None) or upper_ready is not (upper is not None):
            raise ValueError("prewar v2 owner bound readiness disagrees with its nullable count")
        if owner != actor and (lower_ready is not False or lower is not None):
            raise ValueError("prewar v2 nonactor inventory cannot claim the actor floor")
        if owner == actor and lower_ready is False and not reasons:
            raise ValueError("prewar v2 unknown actor floor requires its unavailable reason")
        if owner in enemy_owners and upper_ready is False and not reasons:
            raise ValueError("prewar v2 unknown enemy inventory requires its unavailable reason")
        if owner == actor and lower_ready is True and upper_ready is True and lower > upper:
            raise ValueError("prewar v2 executable actor floor exceeds its same-scope physical inventory ceiling")
        normalized = {
            "owner_character_id": owner, "actor_lower_soldiers": lower,
            "actor_lower_ready": lower_ready, "inventory_upper_soldiers": upper,
            "inventory_upper_ready": upper_ready, "inventory_scope": INVENTORY_SCOPE,
            "unavailable_reasons": reasons,
        }
        by_owner[owner] = normalized
        result.append(normalized)
    if set(by_owner) != expected:
        raise ValueError("prewar v2 owner_forces omitted a primary role or observed participant")
    return result, by_owner


def _metadata(
    root: Mapping[str, object], *, snapshot: Mapping[str, object],
    expected_declaration: Mapping[str, object], expected_request_binding: Mapping[str, object],
    expected_request_id: str, expected_capture_epoch: int | None,
) -> tuple[int, dict[str, object]]:
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ValueError("prewar v2 schema_version is malformed")
    if not isinstance(root["status"], str) or root["status"] not in {"partial", "available"} or root["read_only"] is not True:
        raise ValueError("prewar v2 must remain a read-only typed observation")
    if not isinstance(snapshot, Mapping) or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("prewar v2 requires the independently leased paused map snapshot")
    build = require_exact_native_build(root["game_version"], root["executable_sha256"])
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    if not isinstance(hello, Mapping) or build != CK3_12004 or build != require_exact_native_build(
        hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"),
    ):
        raise ValueError("prewar v2 exact build differs from its leased snapshot")
    binding = _object(expected_request_binding, _REQUEST_FIELDS, "expected_request_binding")
    request_id = _text(expected_request_id, "expected_request_id")
    if _text(binding["request_id"], "expected_request_binding.request_id") != request_id:
        raise ValueError("prewar v2 independent TOP receipt differs from the fresh request ID")
    for key in ("ticket", "query_sequence", "capture_epoch"):
        if _integer(root[key], key, 1, _UINT64_MAX) != _integer(
            binding[key], f"expected_request_binding.{key}", 1, _UINT64_MAX,
        ):
            raise ValueError(f"prewar v2 independent TOP receipt {key} mismatch")
    if expected_capture_epoch is not None and root["capture_epoch"] != _integer(
        expected_capture_epoch, "expected_capture_epoch", 1, _UINT64_MAX,
    ):
        raise ValueError("prewar v2 expected capture epoch mismatch")
    if "capture_epoch" in snapshot and root["capture_epoch"] != _integer(
        snapshot["capture_epoch"], "snapshot.capture_epoch", 1, _UINT64_MAX,
    ):
        raise ValueError("prewar v2 leased snapshot capture epoch mismatch")
    for wire, snapshot_key in (("native_revision", "native_revision"), ("public_revision", "revision")):
        if _integer(root[wire], wire, 1, _UINT64_MAX) != _integer(
            snapshot.get(snapshot_key), f"snapshot.{snapshot_key}", 1, _UINT64_MAX,
        ):
            raise ValueError(f"prewar v2 leased {wire} mismatch")
    if _integer(root["date_raw"], "date_raw", -(1 << 31), _INT32_MAX) != _integer(
        snapshot.get("date_raw"), "snapshot.date_raw", -(1 << 31), _INT32_MAX,
    ):
        raise ValueError("prewar v2 leased date mismatch")
    played = snapshot.get("played_character")
    if not isinstance(played, Mapping) or played.get("alive") is not True:
        raise ValueError("prewar v2 requires the current living played character")
    actor = _character(root["actor_character_id"], "actor_character_id")
    if actor != _character(played.get("character_id"), "snapshot.played_character.character_id"):
        raise ValueError("prewar v2 leased actor mismatch")
    declaration_id, selected = _declaration(expected_declaration, "expected_declaration")
    if root["declaration_id"] != declaration_id or _selected(root["selected_declaration"], "selected_declaration") != selected:
        raise ValueError("prewar v2 independent selected declaration mismatch")
    current = snapshot.get("declarable_wars")
    if not isinstance(current, list):
        raise ValueError("prewar v2 leased snapshot lost the declaration catalogue")
    matches = [row for row in current if isinstance(row, Mapping) and row.get("declaration_id") == declaration_id]
    if len(matches) != 1 or _declaration(matches[0], "snapshot.declarable_wars")[1] != selected:
        raise ValueError("prewar v2 selected declaration is absent, ambiguous or stale")
    # Generic WarEntry effective target is optional diagnostic context. It is
    # neither an external prerequisite nor the finalized CB defender identity.
    generic = root["effective_target_character_id"]
    if generic is not None:
        _character(generic, "effective_target_character_id")
    return actor, selected


def normalize_prewar_force_coalition_v2(
    value: object, *, snapshot: Mapping[str, object],
    expected_declaration: Mapping[str, object], expected_request_binding: Mapping[str, object],
    expected_request_id: str, expected_capture_epoch: int | None = None,
) -> dict[str, object]:
    """Validate the bare v2 body against independent request and before leases.

    Expected declaration needs its canonical ID and ordered full six-field
    tuple, not a generic WarEntry effective-target expectation. Final CB roles
    come from this query's selected-context two-round source. The receipt must
    be the actual independent TOP receipt for ``expected_request_id``. This
    pure validator cannot authenticate a caller that obtains both expectations
    from the domain or skips outer connection/episode/after-lease checks.
    """
    root = _object(value, _FIELDS, "prewar_force_coalition_v2")
    actor, selected = _metadata(
        root, snapshot=snapshot, expected_declaration=expected_declaration,
        expected_request_binding=expected_request_binding,
        expected_request_id=expected_request_id, expected_capture_epoch=expected_capture_epoch,
    )
    rounds, round_ready = _rounds(root["two_round_observation"])
    roles = _roles(root["final_cb_roles"])
    participants, participant_ready = _participants(root["potential_enemy_participants"], roles)
    forces, by_owner = _owners(
        root["owner_forces"], actor=actor, roles=roles,
        participants=participants["participants"],
    )
    mobilization = _mobilization(root["native_mobilization_qualification"])
    missing: list[str] = []
    if not round_ready:
        missing.append("same_frame_two_round_observation")
    if roles["available"] is not True:
        missing.append("final_cb_roles")
    if not participant_ready:
        missing.append("potential_enemy_participants")
    for key, domain in _COMPLETE_DOMAINS:
        if participants[key] is not True:
            missing.append(domain)
    actor_force = by_owner[actor]
    if (
        actor_force["actor_lower_ready"] is not mobilization["executable_lower_ready"]
        or actor_force["actor_lower_soldiers"] != mobilization["executable_lower_soldiers"]
    ):
        raise ValueError("prewar v2 actor owner bound must be the actual mobilization executable lower")
    if mobilization["available"] is not True:
        missing.append("native_mobilization_qualification")
    if actor_force["actor_lower_ready"] is not True:
        missing.append("actor_current_inventory_lower")
    enemy_ids = [row["character_id"] for row in participants["participants"]]
    upper_ready = all(by_owner[owner]["inventory_upper_ready"] is True for owner in enemy_ids)
    if not upper_ready:
        missing.append("enemy_current_inventory_upper")
    upper_sum = sum(by_owner[owner]["inventory_upper_soldiers"] for owner in enemy_ids) if upper_ready else None
    if upper_sum is not None and upper_sum > _INT64_MAX:
        missing.append("enemy_upper_aggregate_overflow")
        upper_sum = None
    initial_ready = round_ready and participant_ready
    enemy_complete = initial_ready and upper_ready and upper_sum is not None
    expected_lower = actor_force["actor_lower_soldiers"] if round_ready and actor_force["actor_lower_ready"] is True else None
    expected_upper = upper_sum if enemy_complete else None
    lower = _count(root["actor_lower_soldiers"], "actor_lower_soldiers", nullable=True)
    upper = _count(root["enemy_upper_soldiers"], "enemy_upper_soldiers", nullable=True)
    if lower != expected_lower or upper != expected_upper:
        raise ValueError("prewar v2 force aggregates differ from the complete owner-bound scope")
    if _boolean(root["enemy_force_coverage_complete"], "enemy_force_coverage_complete") is not enemy_complete:
        raise ValueError("prewar v2 enemy force completeness overclaims or suppresses its observed scope")
    if _boolean(root["complete_initial_participants_ready"], "complete_initial_participants_ready") is not initial_ready:
        raise ValueError("prewar v2 initial participant completeness differs from finalized source coverage")
    declared_missing = _texts(root["missing_required_domains"], "missing_required_domains")
    if not set(declared_missing) <= MISSING_REQUIRED_DOMAINS or set(declared_missing) != set(missing):
        raise ValueError("prewar v2 missing domains disagree with the current inventory scope")
    expected_status = "partial" if missing else "available"
    if root["status"] != expected_status:
        raise ValueError("prewar v2 status differs from its actual required-domain coverage")
    return {
        **dict(root), "executable_sha256": CK3_12004.executable_sha256,
        "selected_declaration": selected, "two_round_observation": rounds,
        "final_cb_roles": roles, "potential_enemy_participants": participants,
        "owner_forces": forces, "missing_required_domains": declared_missing,
        "native_mobilization_qualification": mobilization,
    }


def _policy(value: object) -> dict[str, object]:
    config = DEFAULT_PREWAR_FORCE_RISK_POLICY_V2 if value is None else value
    row = _object(config, _POLICY_FIELDS, "force_risk_policy")
    policy_id = _text(row["policy_id"], "force_risk_policy.policy_id")
    numerator = _integer(row["minimum_actor_to_enemy_ratio_numerator"], "force_risk_policy.minimum_actor_to_enemy_ratio_numerator", 1, _INT64_MAX)
    denominator = _integer(row["minimum_actor_to_enemy_ratio_denominator"], "force_risk_policy.minimum_actor_to_enemy_ratio_denominator", 1, _INT64_MAX)
    if row["scope"] != INVENTORY_SCOPE or row["assumption"] != "policy_margin_not_calibrated_probability":
        raise ValueError("prewar v2 force risk policy changes the inventory scope or claims calibration")
    if policy_id == DEFAULT_PREWAR_FORCE_RISK_POLICY_V2["policy_id"] and (numerator, denominator) != (3, 2):
        raise ValueError("prewar v2 a changed margin needs a distinct explicit policy ID")
    return {
        "policy_id": policy_id, "scope": INVENTORY_SCOPE,
        "minimum_actor_to_enemy_ratio_numerator": numerator,
        "minimum_actor_to_enemy_ratio_denominator": denominator,
        "assumption": "policy_margin_not_calibrated_probability",
    }


def assess_prewar_force_risk_v2(
    value: object, *, snapshot: Mapping[str, object],
    expected_declaration: Mapping[str, object], expected_request_binding: Mapping[str, object],
    expected_request_id: str, expected_capture_epoch: int | None = None,
    policy: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Apply a declared integer margin after revalidating the same DTO.

    This is a force risk qualification, not calibrated odds or an execution
    permit. The ordinary planner must retain legality, economy, faction,
    controller and actual mobilization checks. Revalidation is entirely pure
    and does not issue another native query. The default 3/2 margin is an
    explicit policy assumption, not an engine constant or estimated win rate.
    """
    observation = normalize_prewar_force_coalition_v2(
        value, snapshot=snapshot, expected_declaration=expected_declaration,
        expected_request_binding=expected_request_binding,
        expected_request_id=expected_request_id, expected_capture_epoch=expected_capture_epoch,
    )
    config = _policy(policy)
    lower = observation["actor_lower_soldiers"]
    upper = observation["enemy_upper_soldiers"]
    missing = observation["missing_required_domains"]
    qualified = False
    if missing:
        status = "unknown"
        reason = "required_current_inventory_evidence_unavailable"
    else:
        # Python integer products retain the exact inequality even at int64
        # input bounds. A complete zero enemy inventory needs no division.
        qualified = lower > 0 and lower * config["minimum_actor_to_enemy_ratio_denominator"] >= upper * config["minimum_actor_to_enemy_ratio_numerator"]
        status = "qualified" if qualified else "risk_rejected"
        reason = (
            "complete_current_inventory_force_margin_passed" if qualified
            else "actor_current_inventory_floor_is_zero" if lower == 0
            else "complete_current_inventory_force_margin_insufficient"
        )
    return {
        "status": status, "force_risk_qualified": qualified, "reason": reason,
        "policy": config, "actor_lower_soldiers": lower,
        "enemy_upper_soldiers": upper, "missing_required_domains": list(missing),
    }


def is_prewar_force_coalition_current_v2(
    value: object, *, snapshot: Mapping[str, object],
    expected_declaration: Mapping[str, object], expected_request_binding: Mapping[str, object],
    expected_request_id: str, expected_capture_epoch: int | None = None,
) -> bool:
    """Check typed evidence binding without asserting a complete outer lease."""
    try:
        normalize_prewar_force_coalition_v2(
            value, snapshot=snapshot, expected_declaration=expected_declaration,
            expected_request_binding=expected_request_binding,
            expected_request_id=expected_request_id, expected_capture_epoch=expected_capture_epoch,
        )
    except ValueError:
        return False
    return True
