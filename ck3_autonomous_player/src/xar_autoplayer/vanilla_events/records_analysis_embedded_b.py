"""Reusable analysis metadata for embedded vanilla-event records 28--53.

This module migrates only conclusions already recorded in the legacy embedded
contracts.  It deliberately does not claim a fresh exhaustive definition
review and does not invent source-file hashes.
"""

from __future__ import annotations

from typing import Final

from .records_embedded import EMBEDDED_VANILLA_TIMELINE_CONTRACTS
from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


_MIGRATION_BOUNDARY = (
    "Migrated from the existing embedded contract comment and contract shape; "
    "no new exhaustive vanilla-definition review was performed."
)


def _record(
    review_summary: str,
    option_number: int,
    native_option_index: int,
    rationale: str,
    *known_boundaries: str,
    classification: str = "least-invasive-existing-contract-route",
) -> dict[str, object]:
    """Build one detached, JSON-safe metadata record."""

    return {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "migrated_from": {
            "module": "xar_autoplayer.vanilla_events.records_embedded",
            "symbol": "EMBEDDED_VANILLA_TIMELINE_CONTRACTS",
            "evidence": "existing contract comments and contract shape",
            "review_kind": "migration-only-no-new-full-definition-review",
        },
        "review_summary": review_summary,
        "safe_option": {
            "selected_option_number": option_number,
            "selected_native_option_index": native_option_index,
            "classification": classification,
            "rationale": rationale,
        },
        "known_boundaries": [_MIGRATION_BOUNDARY, *known_boundaries],
    }


def _fail_closed_record(
    review_summary: str,
    *known_boundaries: str,
) -> dict[str, object]:
    """Build metadata for an event for which no safe continuation exists."""

    return {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "migrated_from": {
            "module": "xar_autoplayer.vanilla_events.records_embedded",
            "symbol": "EMBEDDED_VANILLA_TIMELINE_CONTRACTS",
            "evidence": "existing contract comments and contract shape",
            "review_kind": "migration-only-no-new-full-definition-review",
        },
        "review_summary": review_summary,
        "safe_option": None,
        "known_boundaries": [_MIGRATION_BOUNDARY, *known_boundaries],
    }


_VANILLA_EMBEDDED_B_ANALYSIS: dict[str, dict[str, object]] = {
    "epidemic_events.5007": _record(
        "Plague-yearly accusation against a court herbalist.",
        3,
        2,
        "Native 2 avoids branding and imprisoning the herbalist and confines "
        "the result to authored opinion, stress, and possible friend progress.",
        "Native 0 is trait-gated, so the observed two-button and full "
        "three-button projections are both accepted.",
        "The contract treats delivery as repeatable within the bounded product "
        "observation window.",
    ),
    "epidemic_events.5009": _record(
        "Plague-market offer for a generated herbal sachet artifact.",
        4,
        3,
        "Native 3 buys nothing and avoids the artifact transfer, gold payment, "
        "and long-lived protection modifiers of the purchase routes.",
        "The legacy record binds one observed generated artifact and merchant "
        "frame and caps that campaign lineage at one occurrence.",
    ),
    "learn_language_outcome.1001": _record(
        "Response after another character successfully learns the player's language.",
        1,
        0,
        "Native 0 is the non-hostile response, creating positive respect or "
        "friend progress instead of insult or rival progress.",
        "Neither authored route starts a follow-up event; both still change "
        "mutual opinion or relationship progress.",
        "The legacy record caps the observed campaign lineage at one occurrence.",
    ),
    "hostile_scheme_discovery.2001": _record(
        "Notification that a hostile scheme against a court member was discovered.",
        1,
        0,
        "The sole authored option is required to continue; it exposes the "
        "already-discovered scheme and notifies its owner.",
        "There is no acknowledgement-only alternative, so this is an unavoidable "
        "effect rather than a no-op.",
        "The owner, target, and spymaster are bound as distinct non-player roles.",
        classification="only-authored-route",
    ),
    "ep3_story_cycle_admin_eunuch.1001": _record(
        "Administrative-eunuch story opener after its immediate setup has run.",
        2,
        1,
        "Native 1 is empty and avoids replacing or granting the chief-eunuch "
        "court position after the immediate effects.",
        "Employment, eunuch upgrades, and starting influence occur before the "
        "modal and cannot be avoided by the selected option.",
        "The legacy record caps the observed story opener at one occurrence.",
    ),
    "ep3_story_cycle_admin_eunuch.2050": _record(
        "Eunuch-story boon proposal with optional target-dependent branches.",
        2,
        1,
        "Native 1 refuses the external boon and avoids its tax, succession, hook, "
        "or imprisonment mutation, retaining only downgrade and stress effects.",
        "The contract admits the finite no-target and target-specific saved-scope "
        "envelope already documented by the source-shaped branches.",
        "Delivery is repeatable within the bounded product observation window.",
    ),
    "ep3_story_cycle_admin_eunuch.2051": _record(
        "Eunuch-story proposal concerning a selected secret.",
        2,
        1,
        "Native 1 does not reveal the secret to the player and does not start a "
        "follow-up, retaining only downgrade, opinion, and stress effects.",
        "The immediate block may already reveal the secret to the eunuch.",
        "secret_target and shared story roles are optional within the finite "
        "contract envelope; delivery is repeatable in the bounded window.",
    ),
    "ep3_story_cycle_admin_eunuch.2052": _record(
        "Eunuch-story proposal to expose a selected hostile scheme.",
        2,
        1,
        "Native 1 leaves the hostile scheme untouched and confines the response "
        "to story downgrade, opinion, and stress effects.",
        "The owner and optional target must remain non-player and distinct from "
        "the eunuch according to the existing scope envelope.",
        "No one-shot gate was recorded; validate each delivery in the bounded window.",
    ),
    "ep3_story_cycle_admin_eunuch.2060": _record(
        "Court-position demand made by the story eunuch.",
        2,
        1,
        "Native 1 refuses the demand and avoids assigning the generated position "
        "or removing its old holder.",
        "Optional shared-story roles and old_holder form a finite accepted scope "
        "envelope; delivery is repeatable in the bounded window.",
    ),
    "ep3_story_cycle_admin_eunuch.2061": _record(
        "Court-position demand for a close family member of the story eunuch.",
        2,
        1,
        "Native 1 refuses the appointment and returns the recruited family member "
        "to their house head or the pool instead of displacing an old holder.",
        "The family member is already moved to the player's court in immediate.",
        "Optional shared-story roles and old_holder are contract-bounded; delivery "
        "is repeatable in the product observation window.",
    ),
    "ep3_story_cycle_admin_eunuch.2040": _record(
        "Eunuch petition for a council seat.",
        2,
        1,
        "Native 1 refuses, preserving the council roster and retaining only the "
        "authored story downgrade, opinion, and stress effects.",
        "An incumbent second_party exists only when the selected seat is occupied; "
        "shared story roles are independently optional.",
        "Delivery is repeatable within the bounded product observation window.",
    ),
    "ep3_story_cycle_admin_eunuch.2041": _record(
        "Eunuch-family petition for a council seat.",
        2,
        1,
        "Native 1 refuses and avoids firing the incumbent, assigning and protecting "
        "the family candidate, or upgrading the story.",
        "The family candidate is already selected or recruited before the modal.",
        "Vanilla's recorded five-year cooldown permits repeat delivery inside a "
        "long enough product observation window.",
    ),
    "ep3_story_cycle_admin_eunuch.2021": _record(
        "Eunuch-family request for a governorship.",
        2,
        1,
        "Native 1 avoids title transfer, appointment-investment changes, heir "
        "opinion mutation, and the five-year family-boon flag.",
        "The selected family member, title, and non-root heir are required roles.",
        "The legacy record caps this observed campaign lineage at one occurrence.",
    ),
    "ep3_story_cycle_admin_eunuch.3010": _record(
        "Eunuch-rival story node after rival creation or recruitment.",
        1,
        0,
        "The sole option only displays the already-applied rivalry as a tooltip.",
        "The rivalry, recruitment, and story storage happen before the modal.",
        "origin_liege is only type-bound because the origin helper may select a "
        "neighboring realm owner or the root fallback.",
        classification="acknowledge-already-applied-result",
    ),
    "ep3_story_cycle_admin_eunuch.3001": _record(
        "Eunuch-student node after student setup has completed.",
        1,
        0,
        "The sole authored option is empty and only acknowledges the existing result.",
        "Recruitment, mentor relation, skill gains, and story storage occur before "
        "the modal and cannot be avoided by the option.",
        "origin_liege and origin exist only in the new-student branch.",
        classification="acknowledge-already-applied-result",
    ),
    "ep3_story_cycle_admin_eunuch.5010": _record(
        "Upset-family node after a family rival has been chosen.",
        1,
        0,
        "Native 0 avoids the extra durable story downgrade and retains only the "
        "authored opinion and stress effects.",
        "Rivalry creation and upset-courtiers storage happen before the modal.",
        "Delivery is repeatable within the bounded product observation window.",
    ),
    "ep3_story_cycle_admin_eunuch.4000": _record(
        "Spouse-accusation node with the known-secret option hidden in the observed frame.",
        1,
        0,
        "Native 0 investigates and may reveal a secret, but avoids native 2's "
        "unconditional double imprisonment and tyranny.",
        "This is a bounded comparative choice, not a no-effect branch.",
        "The observed two-button projection maps to native indices 0 and 2.",
    ),
    "ep3_story_cycle_admin_eunuch.4010": _record(
        "Seduction or murder-plot node involving the ruler's spouse.",
        3,
        2,
        "Native 2 avoids the intrigue duel, triple imprisonment, and major tyranny, "
        "leaving only the authored prestige and stress cost.",
        "The immediate block may already create a lover relation or murder scheme.",
        "Had-sex aliases and generated memory or secret exist only in one optional branch.",
    ),
    "ep3_story_cycle_admin_eunuch.5020": _record(
        "Puppet-heir node after a close-family puppet has been selected.",
        1,
        0,
        "The sole option is required to continue and grants the ten-year puppet "
        "modifier plus appointment investment.",
        "There is no decline route; friendship and story storage already occur in immediate.",
        "The contract proves puppet and current heir are distinct non-player characters.",
        classification="only-authored-route-with-durable-effect",
    ),
    "ep3_story_cycle_admin_eunuch.8030": _record(
        "Terminal event after the story eunuch has moved away.",
        4,
        3,
        "Native 3 clears the two story modifiers and ends the incidental story "
        "without recruiting or replacing the eunuch or starting a follow-up.",
        "Student and rival replacement buttons are independently conditional, so "
        "the existing contract admits the recorded two-, three-, and four-button shapes.",
        "The legacy record caps the terminal event at one occurrence.",
    ),
    "ep3_interactions_events.0630": _fail_closed_record(
        "Governor-removal letter whose sole option executes the title-transfer effect.",
        "No safe option exists: selecting the only button removes the played manager's "
        "governor position and invalidates the required stable roster.",
        "The existing handling policy is scenario-invalidating-fail-closed; preserve "
        "the event paused instead of reporting a product RED or mutating gameplay.",
        "Three stale generic interaction slots are intentionally unavailable rather "
        "than assigned fabricated character identities.",
    ),
    "ep3_admin_events.0002": _record(
        "Notice that the player received a new governorship.",
        3,
        2,
        "Native 2 avoids the three-year development modifier and free-inspection "
        "flag, retaining only minuscule stress loss.",
        "Previous-holder identities are dynamic aliases rather than frozen people.",
        "Appointment succession may add optional county and succession title scopes.",
    ),
    "ep3_governor_yearly.8060": _record(
        "Independent yearly governor event observed after the product response.",
        4,
        3,
        "Native 3 performs no scripted resource, modifier, duel, or follow-up-event "
        "mutation and retains only trait-dependent stress impact.",
        "The embedded record is a fixed campaign observation without a generalized "
        "product-window occurrence policy.",
    ),
    "ep3_governor_yearly.8010": _record(
        "Independent governor bargain involving a requesting governor and titles.",
        3,
        2,
        "Native 2 refuses the bargain, avoiding hooks, candidacies, influence or gold "
        "exchange and the reverse branch's skill duel.",
        "Refusal still applies the requesting governor's opinion loss and "
        "trait-dependent stress.",
        "The embedded record freezes one observed three-character campaign frame.",
    ),
    "ep3_governor_yearly.8100": _record(
        "Independent yearly governor event with one authored option hidden.",
        4,
        3,
        "Native 3 avoids appointment-investment, influence, and rivalry mutations, "
        "retaining only trait-dependent stress impact.",
        "The observed rendered buttons map to native indices 0, 1, and 3.",
        "Governor roles are random selectors; the embedded record retains a fixed "
        "player-family target and campaign-specific date.",
    ),
    "ep3_governor_yearly.8110": _record(
        "Independent pugnacious-peers event involving two non-player governors.",
        2,
        1,
        "Native 1 is the bounded branch: it avoids spending influence, a random duel, "
        "and merit mutation, while applying symmetric opinion modifiers and stress.",
        "No empty branch exists, and the embedded record freezes one observed pair "
        "of governors.",
    ),
}


EMBEDDED_B_EVENT_KEYS: Final[tuple[str, ...]] = tuple(
    _VANILLA_EMBEDDED_B_ANALYSIS
)


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _existing_boundaries(
    contract: dict[str, object], notes: list[str]
) -> dict[str, object]:
    occurrence: dict[str, object]
    if "occurrence_policy" in contract:
        occurrence = {"occurrence_policy": contract["occurrence_policy"]}
    elif "max_occurrences" in contract:
        occurrence = {"max_occurrences": contract["max_occurrences"]}
    else:
        occurrence = {"status": "not-specified-in-existing-contract"}

    option_projection = {
        key: _json_safe(contract[key])
        for key in (
            "option_count",
            "snapshot_option_count",
            "native_option_indices",
            "option_variants",
        )
        if key in contract
    }
    return {
        "date_policy": contract.get("date_policy", "legacy-fixed-date"),
        "occurrence": occurrence,
        "option_projection": option_projection,
        "campaign_specific_binding_fields": [
            key
            for key in ("date_raw", "date_raw_range", "root_character_id")
            if key in contract
        ],
        "notes": list(notes),
    }


def _finalize_analysis() -> dict[str, dict[str, object]]:
    expected = tuple(EMBEDDED_VANILLA_TIMELINE_CONTRACTS)[27:53]
    if EMBEDDED_B_EVENT_KEYS != expected:
        raise RuntimeError(
            "embedded-B analysis no longer matches default records 28 through 53"
        )

    result: dict[str, dict[str, object]] = {}
    for order, event_id in enumerate(EMBEDDED_B_EVENT_KEYS, start=28):
        record = dict(_VANILLA_EMBEDDED_B_ANALYSIS[event_id])
        notes = record.pop("known_boundaries")
        migrated_from = dict(record["migrated_from"])
        migrated_from["default_order_1_based"] = order
        record["migrated_from"] = migrated_from
        record["existing_boundaries"] = _existing_boundaries(
            EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_id],
            notes,
        )
        result[event_id] = record
    return result


VANILLA_EMBEDDED_B_ANALYSIS: Final[dict[str, dict[str, object]]] = (
    _finalize_analysis()
)


__all__ = ["EMBEDDED_B_EVENT_KEYS", "VANILLA_EMBEDDED_B_ANALYSIS"]
