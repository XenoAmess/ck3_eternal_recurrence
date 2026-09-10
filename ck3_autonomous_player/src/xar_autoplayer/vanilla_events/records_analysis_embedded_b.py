"""Reusable analysis metadata for embedded vanilla-event records 28--53.

This module migrates conclusions already recorded in the legacy embedded
contracts.  It does not claim a fresh exhaustive definition review; each
record does carry the exact-build definition-file fingerprint needed to
detect source drift on another machine.
"""

from __future__ import annotations

from typing import Final

from .records_embedded_b import (
    EMBEDDED_B_LEGACY_BINDING_OBSERVATIONS,
    EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS,
)
from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


_MIGRATION_BOUNDARY = (
    "Migrated from the existing embedded contract comment and contract shape; "
    "the exact-build definition file was fingerprinted, but no new exhaustive "
    "option or caller review was performed."
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
        "Exact source and two R372 deliveries prove a repeatable ten-year "
        "cooldown rather than a one-occurrence campaign boundary.",
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
            *[
                key
                for key in ("date_raw", "date_raw_range")
                if key in contract
            ],
            *(
                ["root_character_id"]
                if contract.get("root_character_id") != PLAYER_SENTINEL
                else []
            ),
        ],
        "notes": list(notes),
    }


def _finalize_analysis() -> dict[str, dict[str, object]]:
    expected = tuple(EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS)
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
            EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS[event_id],
            notes,
        )
        result[event_id] = record
    return result


VANILLA_EMBEDDED_B_ANALYSIS: Final[dict[str, dict[str, object]]] = (
    _finalize_analysis()
)

_SOURCE_SHA256_BY_PREFIX: Final[
    tuple[tuple[str, str, str], ...]
] = (
    (
        "epidemic_events.",
        "events/dlc/ce1/epidemic_events.txt",
        "FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E",
    ),
    (
        "learn_language_outcome.",
        (
            "events/scheme_events/learn_language_scheme/"
            "learn_language_outcome_events.txt"
        ),
        "6C3947B39A48C18E674207FF10D257C6853D126B6697AC6DFEC924FADBF39131",
    ),
    (
        "hostile_scheme_discovery.",
        "events/scheme_events/hostile_scheme_discovery_events.txt",
        "C5232383E70F16D125347FA124F260974CF61334CE42EFA4F87981C86DDE736D",
    ),
    (
        "ep3_story_cycle_admin_eunuch.",
        "events/dlc/ep3/ep3_story_cycle_admin_eunuch_events.txt",
        "AD0EAC903C87FBE869A70709F8C674C6557862B28E14BD242B6EF0FB3D946734",
    ),
    (
        "ep3_interactions_events.",
        "events/dlc/ep3/ep3_interactions_events.txt",
        "B36D7898D6F60983CD3EA359C768925EFE26DB6E9A0734D99A4C614EDE8AB1C4",
    ),
    (
        "ep3_admin_events.",
        "events/dlc/ep3/ep3_admin_events.txt",
        "FC11520AC7D3C9FE500A36F0B6DADFDA38B1EDEE7BB19CDEA65EE7E60BE355FB",
    ),
    (
        "ep3_governor_yearly.",
        "events/dlc/ep3/ep3_governor_yearly_8.txt",
        "DA8B840BD0A71705421ABE2FB1C743C451253156917BAB1DC0F6165074194789",
    ),
)


def _definition_source_sha256(event_id: str) -> dict[str, str]:
    for prefix, source_path, source_sha256 in _SOURCE_SHA256_BY_PREFIX:
        if event_id.startswith(prefix):
            return {source_path: source_sha256}
    raise RuntimeError(f"missing embedded-B source fingerprint: {event_id}")


for _event_id, _analysis in VANILLA_EMBEDDED_B_ANALYSIS.items():
    _analysis.setdefault("source_sha256", _definition_source_sha256(_event_id))
    _analysis["existing_boundaries"]["campaign_specific_binding_fields"] = []
    if _analysis["migrated_from"]["review_kind"] == (
        "migration-only-no-new-full-definition-review"
    ):
        _analysis["migrated_from"]["review_kind"] = (
            "migration-with-exact-build-definition-fingerprint"
        )
        _analysis["migrated_from"]["evidence"] = (
            "existing contract review plus exact-build definition-file SHA-256"
        )

_epidemic_5009 = VANILLA_EMBEDDED_B_ANALYSIS["epidemic_events.5009"]
_epidemic_5009["migrated_from"]["review_kind"] = (
    "exact-build-original-definition-and-live-repeat-review"
)
_epidemic_5009["migrated_from"]["evidence"] = (
    "exact definition, caller chain, and two R372 live deliveries"
)
_epidemic_5009["existing_boundaries"]["campaign_specific_binding_fields"] = []
_epidemic_5009["existing_boundaries"]["notes"] = [
    "Exact-build source and R372 repeat evidence supersede the legacy "
    "one-occurrence campaign binding."
]
_epidemic_5009.update({
    "source_sha256": {
        "events/dlc/ce1/epidemic_events.txt": (
            "FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E"
        ),
        "common/on_action/ce1_on_actions.txt": (
            "96B42FA1A542836171A2A608B7155A8A80D30B0D8F8D9742EBE8AFF231B85E16"
        ),
        "common/epidemics/00_epidemics.txt": (
            "090607AC30E86817A709A6A8F5F2B5FC785AF11C352873B823CF2C3AA5A77E7F"
        ),
    },
    "definition_lines": "7112-7329",
    "caller_semantics": (
        "the sole direct caller is epidemic_ongoing_events at weight 100; "
        "each active vanilla epidemic invokes that pool monthly with a 95 "
        "percent chance of no event"
    ),
    "frequency_boundary": (
        "monthly eligibility is not daily delivery, and the event-local "
        "ten-year cooldown prevents the same character receiving it again "
        "before that interval"
    ),
    "trigger_boundary": (
        "an available character whose sub-realm contains an infected province "
        "held personally or within the source-defined capital-distance bound"
    ),
    "immediate_effect": (
        "selects the epidemic, obtains or creates a dynamic merchant, and "
        "creates a merchant-owned pressed-flower artifact with stress and "
        "trash metadata before the choice"
    ),
    "option_semantics": {
        "0": (
            "trait-gated bulk purchase; transfers the artifact, pays tiny "
            "gold, and adds overly_fragrant for fifteen years"
        ),
        "1": (
            "transfers the artifact, pays tiny gold, and adds "
            "sachet_protection for ten years"
        ),
        "2": "adds sachet_protection for ten years without buying the artifact",
        "3": "buys nothing and applies only trait-dependent stress impact",
    },
    "after_effect": (
        "silently removes the dynamic merchant after every authored route"
    ),
    "repeatability": (
        "the event has a ten-year cooldown and no one-shot flag or variable; "
        "R372 observed its second legal delivery about 10.23 years after the first"
    ),
})


_admin_eunuch_1001 = VANILLA_EMBEDDED_B_ANALYSIS[
    "ep3_story_cycle_admin_eunuch.1001"
]
_admin_eunuch_1001["migrated_from"]["review_kind"] = (
    "exact-build-original-definition-and-live-scope-review"
)
_admin_eunuch_1001["migrated_from"]["evidence"] = (
    "exact definition and caller chain plus the R374 generated-family RED"
)
_admin_eunuch_1001["existing_boundaries"][
    "campaign_specific_binding_fields"
] = []
_admin_eunuch_1001["existing_boundaries"]["notes"] = [
    "Only the legacy six-scope frame and R374's exact twenty-scope "
    "generated-family frame are accepted.",
    "Source-defined mother, sibling/nibling, existing-parent and absent "
    "noble-family-group branches remain unaccepted until a real RED supplies "
    "their exact saved-scope shape.",
]
_admin_eunuch_1001.update({
    "source_sha256": {
        "events/dlc/ep3/ep3_story_cycle_admin_eunuch_events.txt": (
            "AD0EAC903C87FBE869A70709F8C674C6557862B28E14BD242B6EF0FB3D946734"
        ),
        "common/on_action/ep3_on_actions.txt": (
            "107D8695BFE25DAF20E058D5EB34579FDB586A172E81D30E052A4662D8E90EA1"
        ),
        "common/on_action/yearly_on_actions.txt": (
            "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
        ),
        "common/scripted_effects/07_dlc_ep3_scripted_effects.txt": (
            "D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D"
        ),
    },
    "definition_lines": "556-671",
    "source_helper_lines": {
        "create_story": "82-96",
        "save_origin": "98-125",
        "create_eunuch": "127-190",
        "create_child": "192-255",
        "create_family": "257-358",
        "upgrade_eunuch": "360-379",
        "bootstrap_event_1000": "465-553",
        "create_noble_family": "3359-3499",
        "upgrade_helper": "7613-7674",
        "ep3_on_actions": "1-80",
        "yearly_on_actions": "2522-2563",
    },
    "caller_semantics": (
        "the yearly pulse reaches hidden bootstrap event .1000 at weight 250; "
        ".1000 chooses or creates the eunuch lineage and then schedules .1001"
    ),
    "frequency_boundary": (
        "the bootstrap has a ten-year cooldown and its primary-title variable "
        "lasts twenty-five years; eligibility is not daily delivery"
    ),
    "immediate_effect": (
        "before the modal, the source creates or resolves the eunuch and "
        "origin, creates family and noble-family/title state when needed, "
        "starts the story, employs and upgrades the eunuch, and grants "
        "starting influence"
    ),
    "option_semantics": {
        "0": (
            "when shown, grants or replaces the chief-eunuch court position "
            "and applies grateful opinion"
        ),
        "1": "empty acknowledgement with no additional gameplay effect",
    },
    "repeatability": (
        "the source uses a ten-year cooldown and contains no one-shot gate; "
        "the twenty-five-year title variable and primary-title changes alter "
        "future eligibility but do not make the event campaign-unique"
    ),
    "saved_scope_boundary": (
        "strictly accepts the legacy six-scope lineage and R374's exact "
        "twenty-scope generated-father/noble-family lineage; other source "
        "branches remain evidence-ledger entries rather than loose optionals"
    ),
})


_ADMIN_EUNUCH_LIVE_OBSERVATION: Final[dict[str, object]] = {
    "exemplars": [{
        "run": "R374",
        "kind": "pre-selection-live-red",
        "artifact": (
            "_runtime/p2r374-active-boundary-continuation-live/"
            "ep3-story-cycle-admin-eunuch-1001-red-report.json"
        ),
        "artifact_sha256": (
            "FAEFEF7A2F09099A697CE4A0215AECF6CCE080013D2822BBFD65BBB8B38B7116"
        ),
        "park_artifact": (
            "_runtime/p2r374-active-boundary-continuation-live/"
            "hot-recovery-park-2.json"
        ),
        "park_artifact_sha256": (
            "F2265333D99B4E996CBAAFD5F31C616291E03438A976E3D85CD4262D4C9889D0"
        ),
        "driver_state_artifact": (
            "_runtime/p2r374-active-boundary-continuation-live/"
            "driver-state-park-2-snapshot.json"
        ),
        "driver_state_artifact_sha256": (
            "446605FC4AB05D1DDED330929E57B2D04A73E91A601E58B4320D6E2037ED9548"
        ),
        "date_raw": 53513184,
        "event_instance_id": 988,
        "root_character_id": 32904,
        "saved_character_ids": {
            "origin_liege": 63082,
            "eunuch": 16850194,
            "parent": 67186091,
            "eunuch_father": 67186091,
            "newly_created_character": 67186058,
            "family_head": 67186091,
            "new_noble_family_holder": 67186091,
            "government_giver": 67186091,
            "noble_family_head": 67186091,
            "liege": 32904,
            "candidate": 16850194,
        },
        "saved_scope_raw_types": {
            "origin_liege": 4,
            "origin": 5,
            "eunuch": 4,
            "parent_min_age": 1,
            "parent_max_age": 1,
            "parent": 4,
            "eunuch_father": 4,
            "count": 1,
            "min_age": 1,
            "max_age": 1,
            "newly_created_character": 4,
            "story": 17,
            "family_head": 4,
            "new_noble_family_holder": 4,
            "government_giver": 4,
            "new_title": 5,
            "noble_family_head": 4,
            "liege": 4,
            "candidate": 4,
            "modifier_type": 3,
        },
        "rendered_native_option_indices": [0, 1],
        "selection_attempted": False,
        "connection_generation": 1,
        "bridge_pid": 51852,
        "process_restart_required": False,
    }],
}


VANILLA_EMBEDDED_B_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    event_id: {
        "exemplars": [dict(exemplar) for exemplar in observation["exemplars"]]
    }
    for event_id, observation in EMBEDDED_B_LEGACY_BINDING_OBSERVATIONS.items()
}
VANILLA_EMBEDDED_B_OBSERVATIONS[
    "ep3_story_cycle_admin_eunuch.1001"
] = _ADMIN_EUNUCH_LIVE_OBSERVATION


__all__ = [
    "EMBEDDED_B_EVENT_KEYS",
    "VANILLA_EMBEDDED_B_ANALYSIS",
    "VANILLA_EMBEDDED_B_OBSERVATIONS",
]
