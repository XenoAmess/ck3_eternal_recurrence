#!/usr/bin/env python3
"""Drive the exact product path to paused ``zg361pp.147`` without CK3 launch."""

from __future__ import annotations

import copy
import time
from collections.abc import Callable, Mapping
from typing import Protocol

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
)
from xar_autoplayer.bridge.zhongguo_promotion_source_progress_contract import (
    verify_review_now_independent_postcondition_v1,
    widget_visible,
)
from zg361_phase2_promotion_compensation_action_cell import _snapshot_binding
from zg361_phase2_promotion_career_hc_contracts import (
    CAREER_HC_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_compensation_contracts import (
    COMPENSATION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_central_contracts import CENTRAL_TIMELINE_CONTRACTS


M146 = "zg361pp.146"
M147 = "zg361pp.147"
B1_AUTHORED_ADVANCE_DAYS = 400
# R54 first proved that a real player publication can occur at the end of the
# authored B1 window.  Preserve that bound and add a separate, finite window
# for the D+2 central pumps and player-visible stage-3 source event.
POST_PUBLICATION_OBSERVATION_DAYS = 150
MAX_ADVANCE_DAYS = (
    B1_AUTHORED_ADVANCE_DAYS + POST_PUBLICATION_OBSERVATION_DAYS
)
HOURS_PER_DAY = 24
# Native bridge snapshots publish on a 250 ms heartbeat. A just-submitted
# pause can become visible to Python before the next heartbeat has replaced
# every cached Snapshot field used by the query's direct-read equality gate.
PAUSED_PROGRESS_SETTLE_SECONDS = 0.35
MAX_PRE_SUBMISSION_REBIND_ATTEMPTS = 4
_TRANSIENT_PROGRESS_BINDING_ERRORS = (
    "promotion source progress lacks a stable paused player binding",
    "ZhongGuo promotion source progress binding changed or is not ready",
    "promotion source progress is not bound to the requested frame",
)

# These are not namespace-wide allowlists.  They are exact pending events
# already proven on the immutable phase-two seed lineage.  Each contract binds
# the paused date, played root, typed saved scopes and complete enabled option
# shape before one fixed, source-reviewed option is sent.
KNOWN_TIMELINE_INTERRUPTS: dict[str, dict[str, object]] = {
    "zg361b2.40": {
        "date_raw": 53147040,
        "date_policy": "exact-authored-anchor",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_reviewing_superior": 32904,
            "zg361_b2_pip_prompt_owner": 32904,
            "zg361_b2_pip_prompt_subject": 29037,
            "zga_personal_result_target": 29037,
        },
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_governor_yearly.8120": {
        # Independent vanilla flood/storm event.  The disaster county loses
        # control/development in immediate regardless of the choice.  Option
        # 1 adds a random stewardship duel and governance/modifier outcome;
        # option 2 spends treasury/gold and adds a county modifier.  Option 3
        # avoids both and is confined to minor piety, a fixed character
        # modifier and trait-dependent stress, so it is the least disruptive
        # route for the promotion-source lineage.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {"disaster_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "bp1_yearly.9007": {
        # Independent vanilla doppelganger encounter.  Visible option 1 adds
        # the generated character to court and creates a follow-up story;
        # authored option 2 (murder) is hidden for this non-sadistic frame.
        # Visible option 2 maps to native index 2 and only dismisses the
        # temporary character, avoiding the durable court/story mutation.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "bp1_yearly_9007_doppelganger": 16779978,
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_interactions_events.0630": {
        # Vanilla governor-removal letter with one option. IMPORTANT: that
        # option executes governor_resignation_title_transfer_effect; it is
        # not a no-op acknowledgement of a previously completed title change.
        # Three generic interaction slots retain their names/type after the
        # referenced characters have gone stale; bind that exact degraded
        # identity shape instead of fabricating character IDs.
        "date_raw": (53147256, 53151600),
        # Two live runs delivered the same single-option interaction
        # letter on different ticks while every semantic field stayed exact.
        "date_raw_range": (53147256, 53151600),
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
        },
        # ``actor`` is the live governor-removal interaction initiator.  The
        # exact source uses it as sender and title-transfer owner, but does
        # not freeze one historical character.  R94 observed 32904 and the
        # later R97 retained lineage observed 36354 after realm turnover.
        # Bind the source invariant (one non-player actor) instead of the
        # first run's incidental ID.
        "unique_character_scope_excludes": {
            "actor": (29037,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "scope_types": {"force_retirement_treasury_cost": "value"},
        "boolean_scopes": ("hook",),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_admin_events.0002": {
        # Vanilla new-governorship notice.  The first two branches install a
        # three-year development modifier or a free-inspection flag; authored
        # option 3 is the bounded acknowledgement with only minuscule stress
        # loss.
        "date_raw": 53147280,
        "root_character_id": 29037,
        "character_scopes": {
            "new_holder": 29037,
        },
        # Both identities come from the title's live previous holder (source
        # line 282), so realm turnover changes the character while preserving
        # the alias.  R97 also arrived through appointment succession and
        # retained two additional typed title scopes that were absent in the
        # earlier transfer shape.
        "unique_character_scope_excludes": {
            "previous_holder": (29037,),
            "previous_governor": (29037,),
        },
        "character_scope_matches_any": {
            "previous_holder": ("previous_governor",),
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "nf_gov_type": "government_type",
            "governor_title": "landed_title",
        },
        "optional_scope_types": {
            "county_title": "landed_title",
            "appointment_succession": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "title",
                "previous_holder",
                "new_holder",
                "transfer_type",
                "nf_gov_type",
                "governor_title",
                "previous_governor",
            ),
            (
                "title",
                "previous_holder",
                "new_holder",
                "transfer_type",
                "county_title",
                "nf_gov_type",
                "governor_title",
                "previous_governor",
                "appointment_succession",
            ),
        ),
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_governor_yearly.8060": {
        # Independent vanilla yearly governor event observed after the PIP
        # response on this immutable timeline.  Option 4 performs no scripted
        # resource, modifier, duel or follow-up-event mutation; only its
        # vanilla trait-dependent stress impact remains.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8010": {
        # Independent vanilla governor bargain.  Accept/reverse can exchange
        # hooks, candidacies, influence or gold (the reverse branch also runs
        # an intrigue/diplomacy duel).  Refusal confines the mutation to the
        # typed requesting governor's -10 opinion plus trait-dependent stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "governor": 29347,
            "their_title_receiver": 30938,
            "title_receiver": 29067,
        },
        "scope_types": {
            "their_title": "landed_title",
            "title": "landed_title",
            "governor_request": "flag",
            "governor_offer": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 7,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_governor_yearly.8100": {
        # Independent vanilla yearly governor event observed on the same
        # immutable date as .8060 in a different run.  Authored option 3 is
        # hidden for this root, so the three rendered buttons map to native
        # indices 0, 1 and 3.  The final rendered option only retains its
        # vanilla trait-dependent stress impact; the others also mutate
        # appointment investment, influence or a rival relationship.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "target_family_member": 31647,
        },
        # Vanilla chooses both roles with random_* selectors when the event
        # fires.  R28/R49 observed 28598/62537 and 27181/36175 respectively,
        # while the exact role names, types, fixed root-family target and
        # authored option shape remained stable.
        "unique_character_scope_excludes": {
            "governor": (29037, 31647),
            "neighboring_promoted_char": (29037, 31647),
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8110": {
        # Independent vanilla pugnacious-peers event.  No empty branch exists:
        # option 1 spends influence and starts a random duel; option 4 changes
        # influence, merit and both opinions.  Option 2 is the bounded branch,
        # applying only symmetric +/-15 opinion modifiers involving the two
        # typed non-player governors plus trait-dependent stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "governor_1": 28598,
            "governor_2": 27181,
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 4,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "tgp_dynastic_cycle_events.0040": {
        # Independent vanilla Silk Road investment event.  Options 1 and 2
        # spend treasury/gold and add a long modifier or fascination progress;
        # option 3 only retains its vanilla trait-dependent stress impact.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"steward": 31003},
        "scope_types": {
            "my_situation": "situation",
            "silk_road_situation": "situation",
            "my_movement": "situation_participant_group",
        },
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0010": {
        # Independent vanilla charlatan-poet event.  Authored option 4 is
        # hidden in this frame.  Option 1 changes merit/dread and option 2
        # recruits the generated character with a five-year modifier; the
        # final rendered option only grants minor Confucian education XP (or
        # trait-dependent stress) and disposes of the temporary character.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # The event creates this temporary character in its immediate block.
        # R26/R47 observed different valid IDs (16780004/16780149), while the
        # exact name/type/count/option shape remained stable.
        "unique_character_scope_excludes": {
            "starving_lowborn": (29037,),
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0005": {
        # Independent vanilla grieving-child event.  Option 1 changes court,
        # guardian, prestige and influence state; option 2 adds merit and can
        # perturb the promotion source under test.  Visible option 3 maps to
        # native index 2 and only grants minor Confucian XP (or stress when
        # absent) while disposing of the temporary child.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # Vanilla creates/selects every role in immediate, so their numeric
        # identities can legitimately change when the seed is reinstalled.
        # R50 and R56 retained the exact role/type/count/option shape with
        # different IDs.  Bind the source-defined relationships instead of
        # treating allocator output as product drift.
        "unique_character_scope_excludes": {
            "grieving_child": (29037,),
            "orphan_mother": (29037,),
            "orphan_father": (29037,),
            "parent": (29037,),
            "guardian": (29037,),
            "messenger": (29037,),
        },
        "character_scope_matches_any": {
            "parent": ("orphan_mother", "orphan_father"),
        },
        "boolean_scopes": (),
        "saved_scope_count": 6,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0015": {
        # Independent vanilla merchant-dispute event.  Authored option 4 is
        # hidden in this frame.  Options 1 and 2 change merit and/or treasury;
        # the final rendered option only grants minor Confucian education XP
        # (or trait-dependent stress), while hidden/after cleanup removes both
        # temporary merchants.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        # Both merchants are created in this event's immediate block. Their
        # allocator IDs legitimately change on each seed reinstall; the
        # stable source contract is two distinct non-player Characters.
        "unique_character_scope_excludes": {
            "market_vendor": (29037,),
            "traveling_merchant": (29037,),
        },
        "character_scope_differs_from": {
            "market_vendor": ("traveling_merchant",),
            "traveling_merchant": ("market_vendor",),
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "tgp_china_yearly.0020": {
        # Independent vanilla unpaid-tax event.  Neither branch is a no-op.
        # Option 1 lowers control in the typed county and grants the liege
        # treasury/opinion (plus trait-dependent stress); option 2 instead
        # costs the player major influence and installs a five-year county
        # modifier.  Select the first bounded branch without the long modifier.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "tax_official": 29346,
            "tax_liege": 32904,
        },
        "scope_types": {"taxless_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 2,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_emperor_yearly.2200": {
        # Independent vanilla emperor-yearly embezzlement offer.  Option 1
        # grants gold but installs a ten-year embezzling flag, lowers
        # governance by four, and can force the disloyal trait.  Refusal has
        # no authored mutation beyond trait-dependent stress, so take it.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"liege": 32904},
        "scope_types": {
            "governorship": "landed_title",
            "capital": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "ep3_emperor_yearly.2240": {
        # Independent vanilla scholar encounter.  Option 1 starts a learning
        # duel with influence consequences and option 2 mutates dread,
        # influence and gold.  Authored option 3 is the explicit opt-out and
        # only applies a fixed minor stress loss.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"the_scholar": 56656},
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep1_flavor.1200": {
        # Independent vanilla learned-eunuch event.  The first three branches
        # pay gold and install a fifteen-year player modifier.  Refusal keeps
        # player resources/skills unchanged and confines the mutation to the
        # typed event character's opinion/potential rivalry plus stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {"eunuch_target": 16780004},
        "scope_types": {"eunuch_target_culture": "culture"},
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.3060": {
        # Independent vanilla imperial-succession event.  Authored option 1
        # is hidden in this frame; rendered option 3 maps to native index 3
        # and has no scripted effect, unlike the political support/detractor
        # branches.
        "date_raw": (53148048, 53149416, 53152368, 53156640),
        # This independent vanilla succession notice has now appeared from
        # early through late in the same bounded product observation.  Bind
        # only its date to that run's finite window; every identity, type,
        # scope-count and option-shape check remains exact.
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "previous_holder": 32904,
            "new_holder": 36354,
            "emperor": 36354,
            "root_scope": 29037,
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "nf_gov_type": "government_type",
            "emp_location": "province",
        },
        "boolean_scopes": (),
        "saved_scope_count": 8,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8130": {
        # Independent vanilla arbitrary-tax event.  Option 4 avoids the
        # modifier, treasury, influence and governance mutations in the first
        # three branches; only its trait-dependent stress impact remains.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "ep3_governor_yearly.8160": {
        # Independent vanilla equitable-access event.  The first two branches
        # alter treasury/influence/governance/cultural acceptance, dread,
        # relationships, county modifiers or court membership.  Authored
        # option 3 is an empty dismissal; the common after block disposes of
        # the event-created administrator.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 31003,
            "culture": 29037,
        },
        # `create_character` allocates a fresh administrator every time this
        # event opens.  Bind its event-local relationship, never a historical
        # allocator ID from one prior run.
        "unique_character_scope_excludes": {
            "administrator": (29037,),
        },
        "character_scope_differs_from": {
            "administrator": ("councillor",),
        },
        "scope_types": {"minority_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 3,
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "ep3_governor_yearly.8170": {
        # Independent vanilla local-defense event.  Options 1-3 spend treasury,
        # alter governance or enter martial/diplomacy duels with broader
        # modifier/truce/influence outcomes.  Refusal confines the mutation to
        # the typed marshal's -15 opinion toward root plus trait-dependent
        # stress.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "governor": 29037,
            "marshal": 29575,
            "raider": 32922,
        },
        "scope_types": {"raid_county": "landed_title"},
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
    },
    "zg361.40": {
        # Product Jingcha mandate at D+161 and again one exact year later
        # inside the 550-day observation window.  The legal default opens the
        # activity planner and schedules its hidden compliance deadline 300
        # days later.  Refusal would write manager-governance facts and a
        # next-review KPI penalty, so it is not neutral for this capture
        # lineage.  R59 observed the second delivery exactly 8,760 hours
        # after the first, matching the yearly playable pulse source.
        "date_raw": (53150880, 53159640),
        "date_policy": "yearly-pulse-in-observation-window",
        "date_raw_anchor": 53150880,
        "date_period_hours": 8760,
        "max_occurrences": 2,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "option_count": 2,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361b1.200": {
        # Product B1 self-review receipt at the authored D+240 stage. The
        # absolute delivery date depends on which manager cycle enrolled the
        # player, so bind it to this client's finite product observation window.
        # The honest branch records
        # the already frozen mid-cycle evidence without the +15/-15 bias of
        # the exaggerated/conservative branches, while advancing the same
        # ticket-guarded review state machine.
        # The player's reviewing manager is selected by the manager-rooted
        # peer window and varies across live runs.  The acceptance-only seed
        # scope can also remain attached to the first frame, but is absent
        # from the product-authored ticket itself.  R68 proved that when the
        # manager review is reached through the common-superior bank close,
        # that event's four bank-ticket *names* remain on the descendant
        # self-review frame. R71 then proved that their inherited payloads are
        # no longer reliable bindings on that descendant: all three values had
        # lost their value type and the bank owner no longer aliased the active
        # review manager. The .200 source never reads those outer bank scopes;
        # bind their exact presence, but bind types/identities only for the
        # nine self-review/manager ticket fields that .200 actually consumes.
        "date_raw": (53152728, 53156256),
        "date_raw_range": (53152728, 53156256),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_b1_self_ticket_subject": 29037,
        },
        "optional_character_scopes": {
            "zga_phase2_seed_player": 29037,
        },
        "unique_character_scope_excludes": {
            "zg361_b1_ticket_owner": (29037,),
            "zg361_b1_self_ticket_owner": (29037,),
        },
        "character_scope_matches_any": {
            "zg361_b1_ticket_owner": ("zg361_b1_self_ticket_owner",),
        },
        "scope_types": {
            "zg361_b1_ticket_cycle": "value",
            "zg361_b1_ticket_case": "value",
            "zg361_b1_ticket_state": "value",
            "zg361_b1_self_ticket_cycle": "value",
            "zg361_b1_self_ticket_case": "value",
            "zg361_b1_self_ticket_state": "value",
        },
        "saved_scope_name_sets": (
            (
                "zg361_b1_ticket_owner",
                "zg361_b1_ticket_cycle",
                "zg361_b1_ticket_case",
                "zg361_b1_ticket_state",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_self_ticket_subject",
                "zg361_b1_self_ticket_cycle",
                "zg361_b1_self_ticket_case",
                "zg361_b1_self_ticket_state",
            ),
            (
                "zga_phase2_seed_player",
                "zg361_b1_ticket_owner",
                "zg361_b1_ticket_cycle",
                "zg361_b1_ticket_case",
                "zg361_b1_ticket_state",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_self_ticket_subject",
                "zg361_b1_self_ticket_cycle",
                "zg361_b1_self_ticket_case",
                "zg361_b1_self_ticket_state",
            ),
            (
                "zg361_b1_bank_ticket_owner",
                "zg361_b1_bank_ticket_season",
                "zg361_b1_bank_ticket_case",
                "zg361_b1_bank_ticket_state",
                "zg361_b1_ticket_owner",
                "zg361_b1_ticket_cycle",
                "zg361_b1_ticket_case",
                "zg361_b1_ticket_state",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_self_ticket_subject",
                "zg361_b1_self_ticket_cycle",
                "zg361_b1_self_ticket_case",
                "zg361_b1_self_ticket_state",
            ),
            (
                "zga_phase2_seed_player",
                "zg361_b1_bank_ticket_owner",
                "zg361_b1_bank_ticket_season",
                "zg361_b1_bank_ticket_case",
                "zg361_b1_bank_ticket_state",
                "zg361_b1_ticket_owner",
                "zg361_b1_ticket_cycle",
                "zg361_b1_ticket_case",
                "zg361_b1_ticket_state",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_self_ticket_subject",
                "zg361_b1_self_ticket_cycle",
                "zg361_b1_self_ticket_case",
                "zg361_b1_self_ticket_state",
            ),
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361b1.201": {
        # Product B1 non-final shadow-grade response.  Option 1 accepts the
        # frozen shadow record and adds no calibration delta; it is the
        # canonical target-directed path already fixed by the production
        # choreography.  Only the five shadow ticket scopes are consumed by
        # this event.  The manager/self/bank ticket names may remain inherited
        # from the exact preceding .102/.200 chain, so admit only the four
        # already-proven inheritance shapes plus the five shadow fields.
        "date_raw": (53157672,),
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_b1_shadow_ticket_subject": 29037,
        },
        "unique_character_scope_excludes": {
            "zg361_b1_shadow_ticket_owner": (29037,),
        },
        "character_scope_matches_any": {
            "zg361_b1_shadow_ticket_owner": (
                "zg361_b1_ticket_owner",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_bank_ticket_owner",
            ),
        },
        "scope_types": {
            "zg361_b1_shadow_ticket_cycle": "value",
            "zg361_b1_shadow_ticket_case": "value",
            "zg361_b1_shadow_ticket_state": "value",
        },
        "saved_scope_name_sets": tuple(
            tuple(names)
            + (
                "zg361_b1_shadow_ticket_owner",
                "zg361_b1_shadow_ticket_subject",
                "zg361_b1_shadow_ticket_cycle",
                "zg361_b1_shadow_ticket_case",
                "zg361_b1_shadow_ticket_state",
            )
            for names in (
                (
                    "zg361_b1_ticket_owner",
                    "zg361_b1_ticket_cycle",
                    "zg361_b1_ticket_case",
                    "zg361_b1_ticket_state",
                    "zg361_b1_self_ticket_owner",
                    "zg361_b1_self_ticket_subject",
                    "zg361_b1_self_ticket_cycle",
                    "zg361_b1_self_ticket_case",
                    "zg361_b1_self_ticket_state",
                ),
                (
                    "zga_phase2_seed_player",
                    "zg361_b1_ticket_owner",
                    "zg361_b1_ticket_cycle",
                    "zg361_b1_ticket_case",
                    "zg361_b1_ticket_state",
                    "zg361_b1_self_ticket_owner",
                    "zg361_b1_self_ticket_subject",
                    "zg361_b1_self_ticket_cycle",
                    "zg361_b1_self_ticket_case",
                    "zg361_b1_self_ticket_state",
                ),
                (
                    "zg361_b1_bank_ticket_owner",
                    "zg361_b1_bank_ticket_season",
                    "zg361_b1_bank_ticket_case",
                    "zg361_b1_bank_ticket_state",
                    "zg361_b1_ticket_owner",
                    "zg361_b1_ticket_cycle",
                    "zg361_b1_ticket_case",
                    "zg361_b1_ticket_state",
                    "zg361_b1_self_ticket_owner",
                    "zg361_b1_self_ticket_subject",
                    "zg361_b1_self_ticket_cycle",
                    "zg361_b1_self_ticket_case",
                    "zg361_b1_self_ticket_state",
                ),
                (
                    "zga_phase2_seed_player",
                    "zg361_b1_bank_ticket_owner",
                    "zg361_b1_bank_ticket_season",
                    "zg361_b1_bank_ticket_case",
                    "zg361_b1_bank_ticket_state",
                    "zg361_b1_ticket_owner",
                    "zg361_b1_ticket_cycle",
                    "zg361_b1_ticket_case",
                    "zg361_b1_ticket_state",
                    "zg361_b1_self_ticket_owner",
                    "zg361_b1_self_ticket_subject",
                    "zg361_b1_self_ticket_cycle",
                    "zg361_b1_self_ticket_case",
                    "zg361_b1_self_ticket_state",
                ),
            )
        ),
        "boolean_scopes": (),
        "option_count": 2,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361b1.126": {
        # Human-only subject-local publication notice. Its trigger has already
        # matched the frozen owner/subject/cycle/case/revision tuple and its
        # single option has no effect. Preserve every inherited ticket name,
        # bind all consumed value types and require all owner aliases to refer
        # to one non-player manager before acknowledging the notice.
        "date_raw": 53155368,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_b1_self_ticket_subject": 29037,
            "zg361_b1_shadow_ticket_subject": 29037,
            "zg361_b1_local_publish_notice_subject": 29037,
        },
        "unique_character_scope_excludes": {
            name: (29037,)
            for name in (
                "zg361_b1_ticket_owner",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_shadow_ticket_owner",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_pending_watch_owner",
                "zg361_b1_local_publish_notice_owner",
            )
        },
        "character_scope_matches_any": {
            name: ("zg361_b1_local_publish_notice_owner",)
            for name in (
                "zg361_b1_ticket_owner",
                "zg361_b1_self_ticket_owner",
                "zg361_b1_shadow_ticket_owner",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_pending_watch_owner",
            )
        },
        "scope_types": {
            name: "value"
            for name in (
                "zg361_b1_ticket_cycle",
                "zg361_b1_ticket_case",
                "zg361_b1_ticket_state",
                "zg361_b1_self_ticket_cycle",
                "zg361_b1_self_ticket_case",
                "zg361_b1_self_ticket_state",
                "zg361_b1_shadow_ticket_cycle",
                "zg361_b1_shadow_ticket_case",
                "zg361_b1_shadow_ticket_state",
                "zg361_b1_oversight_ticket_cycle",
                "zg361_b1_oversight_ticket_case",
                "zg361_b1_oversight_ticket_state",
                "zg361_b1_pending_watch_cycle",
                "zg361_b1_pending_watch_case",
                "zg361_b1_pending_watch_state",
                "zg361_b1_local_publish_notice_cycle",
                "zg361_b1_local_publish_notice_case",
                "zg361_b1_local_publish_notice_revision",
            )
        },
        "saved_scope_name_sets": ((
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
            "zg361_b1_self_ticket_owner",
            "zg361_b1_self_ticket_subject",
            "zg361_b1_self_ticket_cycle",
            "zg361_b1_self_ticket_case",
            "zg361_b1_self_ticket_state",
            "zg361_b1_shadow_ticket_owner",
            "zg361_b1_shadow_ticket_subject",
            "zg361_b1_shadow_ticket_cycle",
            "zg361_b1_shadow_ticket_case",
            "zg361_b1_shadow_ticket_state",
            "zg361_b1_oversight_ticket_owner",
            "zg361_b1_oversight_ticket_cycle",
            "zg361_b1_oversight_ticket_case",
            "zg361_b1_oversight_ticket_state",
            "zg361_b1_pending_watch_owner",
            "zg361_b1_pending_watch_cycle",
            "zg361_b1_pending_watch_case",
            "zg361_b1_pending_watch_state",
            "zg361_b1_local_publish_notice_owner",
            "zg361_b1_local_publish_notice_subject",
            "zg361_b1_local_publish_notice_cycle",
            "zg361_b1_local_publish_notice_case",
            "zg361_b1_local_publish_notice_revision",
        ),),
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361.1": {
        # Player-liege annual review summary. Its immediate block only copies
        # four already-published grade counts into event-local values, and its
        # sole acknowledgement has no effect. The window can inherit the B1
        # bank/reopen tickets from the publication call stack; bind that exact
        # observed shape without confusing the player manager with the outer
        # common-superior bank owner or reopened subject.
        "date_raw": 53156448,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_b1_ticket_owner": 29037,
            "zg361_b1_oversight_ticket_owner": 29037,
            "zg361_b1_reopen_ticket_owner": 29037,
        },
        "unique_character_scope_excludes": {
            "zg361_b1_bank_ticket_owner": (29037,),
            "zg361_b1_reopen_ticket_subject": (29037,),
        },
        "character_scope_differs_from": {
            "zg361_b1_bank_ticket_owner": (
                "zg361_b1_reopen_ticket_subject",
            ),
        },
        "scope_types": {
            name: "value"
            for name in (
                "zg361_b1_bank_ticket_season",
                "zg361_b1_bank_ticket_case",
                "zg361_b1_bank_ticket_state",
                "zg361_b1_ticket_cycle",
                "zg361_b1_ticket_case",
                "zg361_b1_ticket_state",
                "zg361_b1_oversight_ticket_cycle",
                "zg361_b1_oversight_ticket_case",
                "zg361_b1_oversight_ticket_state",
                "zg361_b1_reopen_ticket_cycle",
                "zg361_b1_reopen_ticket_case",
                "zg361_b1_reopen_ticket_state",
                "zg361_b1_reopen_ticket_object",
                "zg361_b1_reopen_ticket_route",
                "zg361_b1_reopen_ticket_hash",
                "zg361_b1_reopen_ticket_reward_hash",
                "zg361_b1_reopen_ticket_book_version",
                "zg361_n_375",
                "zg361_n_35",
                "zg361_n_325",
                "zg361_n_elim",
            )
        },
        "saved_scope_name_sets": ((
            "zg361_b1_bank_ticket_owner",
            "zg361_b1_bank_ticket_season",
            "zg361_b1_bank_ticket_case",
            "zg361_b1_bank_ticket_state",
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
            "zg361_b1_oversight_ticket_owner",
            "zg361_b1_oversight_ticket_cycle",
            "zg361_b1_oversight_ticket_case",
            "zg361_b1_oversight_ticket_state",
            "zg361_b1_reopen_ticket_subject",
            "zg361_b1_reopen_ticket_owner",
            "zg361_b1_reopen_ticket_cycle",
            "zg361_b1_reopen_ticket_case",
            "zg361_b1_reopen_ticket_state",
            "zg361_b1_reopen_ticket_object",
            "zg361_b1_reopen_ticket_route",
            "zg361_b1_reopen_ticket_hash",
            "zg361_b1_reopen_ticket_reward_hash",
            "zg361_b1_reopen_ticket_book_version",
            "zg361_n_375",
            "zg361_n_35",
            "zg361_n_325",
            "zg361_n_elim",
        ),),
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361ch.19": {
        # First player-manager career/HC business window opened from the real
        # Central publication hook. Route 1 is the generator's reference
        # evidence-first path and the same route used by its authorized AI
        # executor. Only the four zg361_ch_d_event_* scopes are consumed;
        # inherited B1/Central tickets are intentionally not contracted.
        "date_raw": 53156496,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361ch.20": {
        # Second D-lane player-manager business window.  The retained product
        # session exposes the same four case-bound scopes and all three
        # authored routes.  Route 1 continues the source generator's
        # evidence-first reference path to D+1 window .21.
        "date_raw": 53156520,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361ch.21": {
        # The retained D-lane manager lacks the treasury/gold predicates for
        # authored routes 1 and 2.  CK3 therefore renders only the always-on
        # defer route (native slot 2), while the active-event ABI still
        # reports all three authored slots.  Preserve that observed mapping.
        "date_raw": 53156544,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 1,
        "snapshot_option_count": 3,
        "native_option_indices": (2,),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
    },
    "zg361ch.22": {
        # Source-reviewed D-lane state-2 window: three unconditional routes,
        # with route 1 continuing the evidence-first reference path.
        "date_raw": 53156568,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361ch.23": {
        # Source-reviewed D-lane state-3 entry window.  All routes are
        # unconditional; route 1 keeps the reference evidence path.
        "date_raw": 53156592,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361ch.24": {
        # Source-reviewed D-lane state-3 decision window.  Its three routes
        # are unconditional and option 1 advances to the final .25 window.
        "date_raw": 53156616,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {"zg361_ch_d_event_owner": 29037},
        "unique_character_scope_excludes": {
            "zg361_ch_d_event_subject": (29037,),
        },
        "scope_types": {
            "zg361_ch_d_event_cycle": "value",
            "zg361_ch_d_event_case": "value",
        },
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361m.1": {
        # First player-facing mechanism policy card, dispatched by the
        # product immediately after an annual review is published.  Every
        # branch deliberately writes the organizational ledger, so this is
        # not a neutral modal to dismiss.  Option A is the product's
        # reference-charter choice (and its highest base AI weight): it adds
        # evidence/trust while recording mechanism choice 001 exactly once.
        # The event itself consumes no saved scopes.  R74 retained unrelated
        # B1 review-ticket scopes on the window; do not turn those inherited
        # implementation details into a false policy-card dependency.
        "date_raw": (53156376,),
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7200": {
        # Vanilla yearly-health onset of withering mind.  The event has no
        # saved scopes and exposes one mandatory acknowledgement whose sole
        # scripted effect adds the indicated withering_mind trait.  There is
        # no alternative branch to prefer; bind the complete one-option frame
        # before acknowledging it.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "health.7500": {
        # Vanilla yearly-health onset of fragile bones. Like health.7200, the
        # event has no saved scopes and one unavoidable acknowledgement. Its
        # sole scripted effect adds fragile_bones, so there is no alternative
        # branch to optimize; bind the complete one-option frame first.
        "date_raw": 53152296,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "spymaster_task.0381": {
        # Independent vanilla Find Secrets hook opportunity.  Option 1 spends
        # gold and fabricates a hook; option 2 only grants the one typed third
        # party a decaying opinion modifier toward root.  The same exact event
        # can recur on this seed.  The second council-task delivery moved by
        # ten days between R35 and R57 while every semantic field stayed
        # exact. Vanilla task progress/random discovery controls delivery;
        # neither selected effect checks the calendar. Use this run's existing
        # product observation window, independently of the two-occurrence cap.
        "date_raw": (53148768, 53152656),
        "date_raw_range": (53148768, 53152896),
        "date_policy": "product-observation-window",
        "max_occurrences": 2,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "unique_character_scope_excludes": {
            "character_to_hook": (29037, 32904),
        },
        "boolean_scopes": ("having_find_secrets_event",),
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "spymaster_task.0399": {
        # Vanilla Find Secrets "found nothing" delivery.  The event's
        # immediate random_list saves exactly one of two boolean scopes:
        # secrets_to_be_found when the Spymaster suspects a secret remains,
        # or no_secrets_here otherwise.  R60/R69 observed the two legitimate
        # branches with every character identity and option shape unchanged.
        # The task cadence also controls the delivery date, so bind it to the
        # same per-run product observation window as the other Find Secrets
        # notifications instead of freezing one RNG tick.
        "date_raw": (53148768, 53152896),
        "date_raw_range": (53148768, 53152896),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "boolean_scopes": (),
        "boolean_scope_name_sets": (
            ("no_secrets_here",),
            ("secrets_to_be_found",),
        ),
        "saved_scope_name_sets": (
            (
                "councillor",
                "councillor_liege",
                "target_character",
                "no_secrets_here",
            ),
            (
                "councillor",
                "councillor_liege",
                "target_character",
                "secrets_to_be_found",
            ),
        ),
        "option_count": 2,
        # Option 1 changes the councillor task.  Option 2 preserves the
        # current task and is the already-proven minimal side-effect path.
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "spymaster_task.0342": {
        # Vanilla Find Secrets discovery notification.  The secret and its
        # participants are already fixed when the window opens; there is one
        # authored acknowledgement, which reveals that exact secret to root.
        # R61 observed the same exact one-option/scope identity later in the
        # continuing Find Secrets task. The notification date is selected by
        # the vanilla discovery cadence, not by the revealed-secret contract.
        "date_raw": (53152896, 53157024),
        "date_raw_range": (53152896, 53157024),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
            "active_councillor": 27963,
            "secret_holder": 27051,
        },
        "scope_types": {"secret_to_reveal": "secret"},
        "boolean_scopes": ("having_find_secrets_event",),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "spymaster_task.0346": {
        # Vanilla Find Secrets lover-secret notification.  Like .0342, the
        # discovery is already fixed when the window opens and exposes one
        # acknowledgement, which reveals that exact secret to root.
        # R62 delivered the same exact scope/option identity one day later;
        # bind the observed Find Secrets cadence without changing semantics.
        "date_raw": (53152896, 53152920),
        "date_raw_range": (53152896, 53152920),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
            "active_councillor": 27963,
            "secret_holder": 27051,
            "lover": 45267,
        },
        "scope_types": {"secret_to_reveal": "secret"},
        "boolean_scopes": ("having_find_secrets_event",),
        "saved_scope_count": 8,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "chancellor_task.1104": {
        # Vanilla foreign-affairs success letter. The active chancellor has
        # already selected a neighboring ruler in .1103; this one-option
        # continuation only grants that neighbor a temporary positive opinion
        # of root. Bind source-defined role aliases instead of allocator IDs.
        "date_raw": 53149872,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "councillor": (29037,),
            "chancellor": (29037,),
            "active_councillor": (29037,),
            "neighbor": (29037,),
        },
        "character_scope_matches_any": {
            "chancellor": ("councillor",),
            "active_councillor": ("councillor",),
        },
        "character_scope_differs_from": {
            "neighbor": ("councillor", "chancellor", "active_councillor"),
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "bp1_yearly.9006": {
        # Friends & Foes narrow-yearly event. Immediate selects exactly one
        # unrelated courtier/vassal who shares a sinful trait with root. The
        # first option creates or advances friendship and also changes piety
        # and stress; option 2 changes only root's piety/stress and therefore
        # is the bounded minimum-external-side-effect path for this capture.
        # R72's frozen seed is not craven, so the conditional animal helper is
        # absent and the complete live frame contains only the courtier.
        "date_raw": 53147520,
        "date_raw_range": (53147520, 53147520),
        "date_policy": "product-observation-window",
        "max_occurrences": 2,
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "bp1_yearly_9006_sinful_courtier": (29037,),
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "yearly.1040": {
        # Vanilla yearly "suspicious letter" event. R85 froze the good-
        # surprise branch as one third-party Character plus two opaque flag
        # values. Option 1 changes that character's opinion once and enters
        # the immediate, one-option .1041 disclosure. Option 2 adds a duel and
        # may schedule .1044; option 3 is known-good here and always schedules
        # .1044, adding a later resource/relationship outcome. Bind the exact
        # live shape and choose the shorter deterministic continuation.
        "date_raw": (53147520,),
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "suspicious": (29037,),
        },
        "scope_types": {
            "suspicious_type": "flag",
            "surprise_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "yearly.1041": {
        # Source-direct continuation of yearly.1040 option 1. The event adds
        # no new scope, has one unavoidable acknowledgement, and on the R85
        # good-surprise branch only renders the already-frozen surprise.
        "date_raw": (53147520,),
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "suspicious": (29037,),
        },
        "scope_types": {
            "suspicious_type": "flag",
            "surprise_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 3,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "ep3_governor_yearly.8080": {
        # Roads to Power annual governor event.  The event creates exactly
        # one temporary magistrate.  Option 1 punishes the magistrate by
        # changing only root's governance and ten-year bureaucracy modifier;
        # unlike the alternatives it neither kills/recruits the character nor
        # embezzles gold, so it is the minimum external-side-effect path.
        "date_raw": 53147520,
        "date_raw_range": (53147520, 53147520),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "magistrate": (29037,),
        },
        "boolean_scopes": (),
        "saved_scope_count": 1,
        "option_count": 4,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "sway_ongoing.1002": {
        # Vanilla ongoing-sway compliment letter. The no-friend branch
        # randomizes three distinct compliment flags from the first twelve
        # authored options, so their concrete native indices are deliberately
        # dynamic. The thirteenth authored option is always available and has
        # no option effect; only the event-wide after block clears the
        # temporary compliment flags. Select that bounded fallback while
        # binding the exact scheme owner/target frame and source-defined
        # three-random-plus-final option shape.
        "date_raw": 53149920,
        "date_raw_range": (53149920, 53149920),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
            "compliment_receiver": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 4,
        "snapshot_option_count": 13,
        "native_option_prefix_range": (0, 11),
        "native_option_suffix": (12,),
        "selected_option_number": 13,
        "selected_native_option_index": 12,
    },
    "tgp_interaction_event.0016": {
        # Roads to Power military-aid order sent to the joining governor.
        # The interaction has already joined root to the recipient's wars
        # before this letter opens. The event immediate only adds a custom
        # tooltip and its single option has no scripted effect, so the sole
        # acknowledgement is the exact bounded path. Generic interaction
        # slots may retain typed weak Character scopes; bind their unavailable
        # identity explicitly instead of inventing character IDs.  Recipient
        # is selected dynamically by each interaction, then source line 6658
        # saves that same Character as governor_at_war.  Freeze that authored
        # role alias, not one allocator-specific historical ID.
        "date_raw": 53159976,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "actor": 30987,
            "secondary_recipient": 29037,
            "governor_joining": 29037,
        },
        "unique_character_scope_excludes": {
            "recipient": (29037, 30987),
            "governor_at_war": (29037, 30987),
        },
        "character_scope_matches_any": {
            "recipient": ("governor_at_war",),
            "governor_at_war": ("recipient",),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "intermediary",
        ),
        "boolean_scopes": (),
        "saved_scope_count": 7,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "scheme_critical_moments.1134": {
        # Vanilla slander target-reaction notice. Its immediate block has
        # already applied the influence/modifier outcome before the window is
        # rendered; the sole option is empty and the after block only clears
        # a temporary nickname flag. Bind the exact live scheme payload and
        # acknowledge the only branch so the product timeline can continue.
        "date_raw": 53189328,
        "root_character_id": 29037,
        "character_scopes": {"target": 29037},
        "unique_character_scope_excludes": {"owner": (29037,)},
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
            "follow_up_event": "flag",
            "discovery_chance": "value",
        },
        "boolean_scopes": ("scheme_discovered", "scheme_successful"),
        "saved_scope_count": 8,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "realm_maintenance.2001": {
        # Vanilla title-inheritance notice. The transfer has already happened
        # before this window opens and there is only one acknowledgement.
        # Preserve the full observed title/government and character-role shape
        # so the runner cannot mistake a different one-option event for it.
        "date_raw": 53199000,
        "root_character_id": 29037,
        "character_scopes": {
            "new_holder": 29037,
            "new_minister": 29037,
            "title_holder": 29037,
        },
        "unique_character_scope_excludes": {
            "previous_holder": (29037,),
            "councillor_liege": (29037,),
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "capital_county": "landed_title",
            "nf_gov_type": "government_type",
        },
        "boolean_scopes": (),
        "saved_scope_count": 9,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "sway_outcome.2001": {
        # Vanilla diplomatic-misunderstanding outcome for the seed's existing
        # sway scheme.  The event has one unavoidable acknowledgement: the
        # typed target loses 10 opinion of the played owner and the already
        # failed sway scheme ends.  Bind the complete live scope/option shape
        # before accepting that bounded outcome.
        "date_raw": 53153952,
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
        },
        "boolean_scopes": (),
        "saved_scope_count": 4,
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
}
KNOWN_TIMELINE_INTERRUPTS.update(CAREER_HC_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(COMPENSATION_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CENTRAL_TIMELINE_CONTRACTS)


class PromotionProductionEntryService(Protocol):
    def snapshot(self) -> dict[str, object]: ...
    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]: ...
    def query_zhongguo_promotion_source_progress_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]: ...
    def activate_zhongguo_review_now_v1(
        self, request_nonce: str, source_progress: dict[str, object], *,
        expected_revision: int,
    ) -> dict[str, object]: ...
    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...
    def select_event_option(
        self, option_number: int, *, event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]: ...


class PromotionProductionEntryError(RuntimeError):
    pass


def _accepted(value: object, step: str) -> dict[str, object]:
    result = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    status = result.get("status")
    accepted_statuses = {"submitted"}
    if step == "pause-map":
        accepted_statuses.add("already_paused")
    elif step == "resume-map":
        accepted_statuses.add("already_running")
    if not (
        result.get("accepted") is True
        and status in accepted_statuses
    ):
        raise PromotionProductionEntryError(
            f"{step} did not return an accepted ACK: {result!r}"
        )
    return result


def _map_control_from_latest_binding(
    service: PromotionProductionEntryService,
    *,
    step: str,
    player: int,
    connection_generation: int,
    rebind_audit: list[dict[str, object]],
) -> dict[str, object] | None:
    """Submit one idempotent map control after rebinding heartbeats.

    A progress query or the native heartbeat can publish a newer public
    revision after the outer loop sampled its paused frame. A
    ``PreSubmissionRevisionMismatchError`` proves that no input was submitted,
    so an idempotent pause/resume/speed request can bind the newest frame and
    retry. If the requested state already exists, or a modal appears before a
    resume/speed request, the outer loop owns the new state and no request is
    sent.
    """

    if step not in {"pause-map", "resume-map", "set-speed-5"}:
        raise ValueError(f"unsupported rebound map control: {step}")

    last_error: PreSubmissionRevisionMismatchError | None = None
    for attempt in range(1, MAX_PRE_SUBMISSION_REBIND_ATTEMPTS + 1):
        snapshot, event = _binding(
            service.snapshot(),
            player=player,
            connection_generation=connection_generation,
        )
        if step == "pause-map" and snapshot.get("paused") is True:
            return None
        if step == "resume-map" and (
            event is not None or snapshot.get("paused") is not True
        ):
            return None
        if step == "set-speed-5" and (
            event is not None or snapshot.get("speed") == 5
        ):
            return None
        revision = int(snapshot["revision"])
        try:
            return _accepted(
                service.execute_step(step, expected_revision=revision),
                step,
            )
        except PreSubmissionRevisionMismatchError as error:
            last_error = error
            rebind_audit.append({
                "step": step,
                "attempt": attempt,
                "stale_revision": revision,
                "error": f"{type(error).__name__}: {error}",
                "request_submitted": False,
            })
    assert last_error is not None
    raise last_error


def _resume_map_from_latest_binding(
    service: PromotionProductionEntryService,
    *,
    player: int,
    connection_generation: int,
    rebind_audit: list[dict[str, object]],
) -> dict[str, object] | None:
    return _map_control_from_latest_binding(
        service,
        step="resume-map",
        player=player,
        connection_generation=connection_generation,
        rebind_audit=rebind_audit,
    )


def _compact_progress_observation(
    query: object, *, date_raw: int, revision: int,
) -> dict[str, object]:
    """Reduce one native progress query to stable player-owned state bits."""

    result = copy.deepcopy(dict(query)) if isinstance(query, Mapping) else {}
    progress = result.get("zhongguo_promotion_source_progress")
    widgets = progress.get("widgets") if isinstance(progress, Mapping) else None
    if (
        result.get("status") != "available"
        or not isinstance(progress, dict)
        or not isinstance(widgets, list)
        or len(widgets) != 5
    ):
        raise PromotionProductionEntryError(
            "promotion progress observer became unavailable during product timeline"
        )
    for index, widget in enumerate(widgets):
        visible = widget.get("effective_visible") if isinstance(widget, Mapping) else None
        if not (
            isinstance(visible, Mapping)
            and visible.get("status") == "available"
            and isinstance(visible.get("value"), bool)
        ):
            raise PromotionProductionEntryError(
                "promotion progress observer returned an unavailable widget "
                f"during product timeline: index={index}"
            )
    return {
        "revision": revision,
        "date_raw": date_raw,
        "review_now_eligible": widget_visible(progress, 1),
        "b1_active": widget_visible(progress, 2),
        "central_active": widget_visible(progress, 3),
        "pp_active": widget_visible(progress, 4),
    }


def _binding(
    snapshot: object, *, player: int | None = None,
    connection_generation: int | None = None,
) -> tuple[dict[str, object], dict[str, object] | None]:
    value = copy.deepcopy(dict(snapshot)) if isinstance(snapshot, Mapping) else {}
    played = value.get("played_character")
    actual_player = played.get("character_id") if isinstance(played, Mapping) else None
    diagnostics = value.get("diagnostics")
    generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, Mapping)
        else None
    )
    revision = value.get("revision")
    date_raw = value.get("date_raw")
    if (
        value.get("map_ready") is not True
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not isinstance(actual_player, int)
        or actual_player <= 0
        or not isinstance(generation, int)
        or generation <= 0
        or (player is not None and actual_player != player)
        or (
            connection_generation is not None
            and generation != connection_generation
        )
    ):
        raise PromotionProductionEntryError(
            "promotion path crossed its played-owner/connection binding"
        )
    event_binding = None
    if isinstance(value.get("active_event"), Mapping):
        if value.get("paused") is not True:
            return value, None
        event_binding = _snapshot_binding(value, expected_event=True)
    return value, event_binding


def _event_definition(
    service: PromotionProductionEntryService,
    binding: Mapping[str, object],
    *,
    retry_attempts: int = 20,
    retry_interval_seconds: float = 0.05,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[str, dict[str, object]]:
    if retry_attempts <= 0 or retry_interval_seconds < 0:
        raise ValueError("current-event query retry timing is invalid")
    current_binding = copy.deepcopy(dict(binding))
    for attempt in range(retry_attempts):
        result = service.query_current_event_window_context_v1(
            int(current_binding["event_instance_id"]),
            expected_revision=int(current_binding["revision"]),
        )
        context = result.get("current_event_window_context")
        response_binding = result.get("binding")
        key = (
            context.get("event_definition_key")
            if isinstance(context, Mapping)
            else None
        )
        if (
            result.get("status") == "available"
            and isinstance(context, Mapping)
            and isinstance(response_binding, Mapping)
            and isinstance(key, str)
            and response_binding.get("snapshot_id")
            == current_binding.get("snapshot_id")
            and response_binding.get("revision")
            == current_binding.get("revision")
            and response_binding.get("native_revision")
            == current_binding.get("native_revision")
            and response_binding.get("event_instance_id")
            == current_binding.get("event_instance_id")
        ):
            evidence = copy.deepcopy(result)
            evidence["transient_event_window_retries"] = attempt
            return key, evidence

        transient_saved_scope_build = (
            result.get("status") == "unavailable"
            and isinstance(context, Mapping)
            and context.get("unavailable_reason") == "event_saved_scope_invalid"
            and context.get("current_event_instance_id")
            == current_binding.get("event_instance_id")
            and result.get("queried_snapshot_id")
            == current_binding.get("snapshot_id")
            and result.get("queried_native_revision")
            == current_binding.get("native_revision")
        )
        if not transient_saved_scope_build or attempt + 1 >= retry_attempts:
            break
        if retry_interval_seconds:
            sleeper(retry_interval_seconds)
        refreshed_snapshot, refreshed_event = _binding(
            service.snapshot(),
            player=int(current_binding["player_character_id"]),
            connection_generation=int(current_binding["connection_generation"]),
        )
        stable_fields = (
            "snapshot_id", "native_revision", "date_raw", "player_character_id",
            "connection_generation", "event_instance_id", "event_option_count",
        )
        if (
            refreshed_event is None
            or any(
                refreshed_event.get(field) != current_binding.get(field)
                for field in stable_fields
            )
            or refreshed_snapshot.get("paused") is not True
            or refreshed_event.get("revision") != result.get("queried_revision")
        ):
            break
        current_binding = refreshed_event
    raise PromotionProductionEntryError(
        "current-event query crossed the paused promotion frame"
    )


def _typed_character_id(value: object) -> int | None:
    scope = value if isinstance(value, Mapping) else {}
    identity_value = scope.get("typed_identity")
    identity = identity_value if isinstance(identity_value, Mapping) else {}
    character_id = identity.get("character_id")
    if (
        scope.get("status") != "available"
        or scope.get("type_key") != "character"
        or identity.get("status") != "available"
        or identity.get("kind") != "character"
        or isinstance(character_id, bool)
        or not isinstance(character_id, int)
        or character_id <= 0
    ):
        return None
    return character_id


def _timeline_contract_for_window(
    contract: Mapping[str, object], *, starting_date: int,
) -> dict[str, object]:
    """Bind source-reviewed random deliveries to this run, not old RNG dates.

    The only exact calendar anchor in this interrupt table is explicitly
    marked. Every other delivery is either vanilla/random or a product stage
    whose absolute date depends on the enrolled manager cycle; its semantic
    contract is the bounded observation window plus the unchanged event,
    scope, type, option and occurrence constraints.
    """
    bound = dict(contract)
    if contract.get("date_policy") != "exact-authored-anchor":
        bound["date_raw_range"] = (
            starting_date, starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY,
        )
    return bound


def _contract_date_matches(
    value: object, contract: Mapping[str, object]
) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    range_value = contract.get("date_raw_range")
    if (
        isinstance(range_value, tuple)
        and len(range_value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) for item in range_value)
    ):
        lower, upper = range_value
        if not lower <= value <= upper:
            return False
        if contract.get("date_policy") == "yearly-pulse-in-observation-window":
            anchor = contract.get("date_raw_anchor")
            period = contract.get("date_period_hours")
            return bool(
                isinstance(anchor, int)
                and not isinstance(anchor, bool)
                and isinstance(period, int)
                and not isinstance(period, bool)
                and period > 0
                and (value - anchor) % period == 0
            )
        return True
    date_raw_value = contract["date_raw"]
    date_raw_values = (
        date_raw_value if isinstance(date_raw_value, tuple) else (date_raw_value,)
    )
    return value in date_raw_values


def _known_interrupt_checks(
    *,
    snapshot: Mapping[str, object],
    event: Mapping[str, object],
    context: Mapping[str, object],
    event_key: str,
    contract: Mapping[str, object],
) -> dict[str, bool]:
    options_value = context.get("options")
    options = options_value if isinstance(options_value, list) else []
    option_count = contract["option_count"]
    snapshot_option_count = contract.get("snapshot_option_count", option_count)
    actual_native_option_indices: list[object] = []
    authored_options_exact = len(options) == option_count
    if authored_options_exact:
        for index, row_value in enumerate(options):
            row = row_value if isinstance(row_value, Mapping) else {}
            actual_native_option_indices.append(row.get("native_option_index"))
            if not (
                row.get("rendered_index") == index
                and row.get("shown") is True
                and row.get("enabled") is True
                and row.get("fallback") is False
                and row.get("cancel") is False
            ):
                authored_options_exact = False
                break
    native_option_prefix_range = contract.get("native_option_prefix_range")
    native_option_suffix = contract.get("native_option_suffix")
    if (
        authored_options_exact
        and isinstance(native_option_prefix_range, tuple)
        and len(native_option_prefix_range) == 2
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in native_option_prefix_range
        )
        and isinstance(native_option_suffix, tuple)
    ):
        lower, upper = native_option_prefix_range
        prefix = actual_native_option_indices[: -len(native_option_suffix)]
        suffix = actual_native_option_indices[-len(native_option_suffix) :]
        authored_options_exact = (
            bool(native_option_suffix)
            and lower <= upper
            and prefix == sorted(prefix)
            and len(prefix) == len(set(prefix))
            and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and lower <= value <= upper
                for value in prefix
            )
            and tuple(suffix) == native_option_suffix
        )
    elif authored_options_exact:
        native_option_indices_value = contract.get(
            "native_option_indices", tuple(range(int(option_count)))
        )
        native_option_indices = (
            native_option_indices_value
            if isinstance(native_option_indices_value, tuple)
            else ()
        )
        authored_options_exact = (
            len(native_option_indices) == option_count
            and tuple(actual_native_option_indices) == native_option_indices
        )

    scopes_value = context.get("saved_scopes")
    scopes = scopes_value if isinstance(scopes_value, list) else []

    def character_ids(name: str) -> set[int]:
        return {
            character_id
            for row_value in scopes
            if isinstance(row_value, Mapping)
            and row_value.get("name") == name
            and (character_id := _typed_character_id(row_value.get("scope")))
            is not None
        }

    character_scopes_value = contract["character_scopes"]
    character_scopes = (
        character_scopes_value
        if isinstance(character_scopes_value, Mapping)
        else {}
    )
    boolean_scopes_value = contract["boolean_scopes"]
    boolean_scopes = (
        boolean_scopes_value
        if isinstance(boolean_scopes_value, tuple)
        else ()
    )
    checks = {
        "context_schema": context.get("schema")
        == "current-event-window-context-v1",
        "context_schema_version": context.get("schema_version") == 1,
        "context_available": context.get("status") == "available",
        "unique_window": context.get("window_match_count") == 1,
        "event_definition_key": context.get("event_definition_key")
        == event_key,
        "event_instance_id": context.get("current_event_instance_id")
        == event.get("event_instance_id"),
        "snapshot_date_raw": _contract_date_matches(
            snapshot.get("date_raw"), contract
        ),
        "context_date_raw": _contract_date_matches(
            context.get("date_raw"), contract
        ),
        "root_character_id": _typed_character_id(context.get("root_scope"))
        == contract["root_character_id"],
        "snapshot_option_count": (
            snapshot.get("active_event", {}).get("option_count")
            if isinstance(snapshot.get("active_event"), Mapping)
            else None
        )
        == snapshot_option_count,
        "authored_options_exact": authored_options_exact,
        "selected_option_mapping": contract["selected_option_number"]
        == contract["selected_native_option_index"] + 1,
    }
    for name, expected_character_id in character_scopes.items():
        checks[f"scope:{name}"] = character_ids(str(name)) == {
            expected_character_id
        }
    optional_character_scopes_value = contract.get(
        "optional_character_scopes", {}
    )
    optional_character_scopes = (
        optional_character_scopes_value
        if isinstance(optional_character_scopes_value, Mapping)
        else {}
    )
    for name, expected_character_id in optional_character_scopes.items():
        ids = character_ids(str(name))
        checks[f"scope:{name}:optional"] = ids in (
            set(),
            {expected_character_id},
        )
    unavailable_character_scopes_value = contract.get(
        "unavailable_character_scopes", ()
    )
    unavailable_character_scopes = (
        unavailable_character_scopes_value
        if isinstance(unavailable_character_scopes_value, tuple)
        else ()
    )
    for name in unavailable_character_scopes:
        matches = [
            row_value
            for row_value in scopes
            if isinstance(row_value, Mapping) and row_value.get("name") == name
        ]
        checks[f"scope:{name}:unavailable_character"] = (
            len(matches) == 1
            and isinstance(matches[0].get("scope"), Mapping)
            and matches[0]["scope"].get("status") == "available"
            and matches[0]["scope"].get("type_key") == "character"
            and matches[0]["scope"].get("typed_identity")
            == {
                "status": "unavailable",
                "reason": "character_scope_identity_unavailable",
            }
        )
    scope_types_value = contract.get("scope_types", {})
    scope_types = (
        scope_types_value if isinstance(scope_types_value, Mapping) else {}
    )
    for name, expected_type in scope_types.items():
        matches = [
            row_value
            for row_value in scopes
            if isinstance(row_value, Mapping) and row_value.get("name") == name
        ]
        checks[f"scope:{name}:type"] = (
            len(matches) == 1
            and isinstance(matches[0].get("scope"), Mapping)
            and matches[0]["scope"].get("status") == "available"
            and matches[0]["scope"].get("type_key") == expected_type
        )
    optional_scope_types_value = contract.get("optional_scope_types", {})
    optional_scope_types = (
        optional_scope_types_value
        if isinstance(optional_scope_types_value, Mapping)
        else {}
    )
    for name, expected_type in optional_scope_types.items():
        matches = [
            row_value
            for row_value in scopes
            if isinstance(row_value, Mapping) and row_value.get("name") == name
        ]
        checks[f"scope:{name}:optional_type"] = not matches or (
            len(matches) == 1
            and isinstance(matches[0].get("scope"), Mapping)
            and matches[0]["scope"].get("status") == "available"
            and matches[0]["scope"].get("type_key") == expected_type
        )
    excluded_scopes_value = contract.get("unique_character_scope_excludes", {})
    excluded_scopes = (
        excluded_scopes_value
        if isinstance(excluded_scopes_value, Mapping)
        else {}
    )
    for name, excluded_character_ids_value in excluded_scopes.items():
        ids = character_ids(str(name))
        excluded_character_ids = (
            set(excluded_character_ids_value)
            if isinstance(excluded_character_ids_value, tuple)
            else set()
        )
        checks[f"scope:{name}:unique_third_party"] = (
            len(ids) == 1 and ids.isdisjoint(excluded_character_ids)
        )
    matches_any_value = contract.get("character_scope_matches_any", {})
    matches_any = (
        matches_any_value if isinstance(matches_any_value, Mapping) else {}
    )
    for name, candidate_names_value in matches_any.items():
        candidate_names = (
            candidate_names_value
            if isinstance(candidate_names_value, tuple)
            else ()
        )
        ids = character_ids(str(name))
        checks[f"scope:{name}:matches_any"] = len(ids) == 1 and any(
            ids == character_ids(str(candidate_name))
            for candidate_name in candidate_names
        )
    differs_from_value = contract.get("character_scope_differs_from", {})
    differs_from = (
        differs_from_value if isinstance(differs_from_value, Mapping) else {}
    )
    for name, other_names_value in differs_from.items():
        other_names = (
            other_names_value if isinstance(other_names_value, tuple) else ()
        )
        ids = character_ids(str(name))
        other_ids = [character_ids(str(other_name)) for other_name in other_names]
        checks[f"scope:{name}:differs_from"] = (
            len(ids) == 1
            and bool(other_ids)
            and all(len(values) == 1 and ids.isdisjoint(values) for values in other_ids)
        )
    for name in boolean_scopes:
        matches = [
            row_value
            for row_value in scopes
            if isinstance(row_value, Mapping) and row_value.get("name") == name
        ]
        checks[f"scope:{name}"] = (
            len(matches) == 1
            and isinstance(matches[0].get("scope"), Mapping)
            and matches[0]["scope"].get("status") == "available"
            and matches[0]["scope"].get("type_key") == "boolean"
        )
    boolean_scope_name_sets_value = contract.get(
        "boolean_scope_name_sets", ()
    )
    boolean_scope_name_sets = (
        boolean_scope_name_sets_value
        if isinstance(boolean_scope_name_sets_value, tuple)
        else ()
    )
    if boolean_scope_name_sets:
        expected_boolean_name_sets = [
            set(name_set)
            for name_set in boolean_scope_name_sets
            if isinstance(name_set, tuple)
        ]
        candidate_boolean_names = set().union(*expected_boolean_name_sets)
        boolean_matches = [
            row_value
            for row_value in scopes
            if isinstance(row_value, Mapping)
            and row_value.get("name") in candidate_boolean_names
        ]
        actual_boolean_names = [
            row_value.get("name") for row_value in boolean_matches
        ]
        checks["boolean_scope_names_exact"] = (
            len(actual_boolean_names) == len(set(actual_boolean_names))
            and set(actual_boolean_names) in expected_boolean_name_sets
            and all(
                isinstance(row_value.get("scope"), Mapping)
                and row_value["scope"].get("status") == "available"
                and row_value["scope"].get("type_key") == "boolean"
                for row_value in boolean_matches
            )
        )
    saved_scope_name_sets_value = contract.get("saved_scope_name_sets", ())
    saved_scope_name_sets = (
        saved_scope_name_sets_value
        if isinstance(saved_scope_name_sets_value, tuple)
        else ()
    )
    if saved_scope_name_sets:
        actual_names = [
            row_value.get("name")
            for row_value in scopes
            if isinstance(row_value, Mapping)
            and isinstance(row_value.get("name"), str)
        ]
        expected_name_sets = [
            set(name_set)
            for name_set in saved_scope_name_sets
            if isinstance(name_set, tuple)
        ]
        checks["saved_scope_names_exact"] = (
            len(actual_names) == len(scopes)
            and len(set(actual_names)) == len(actual_names)
            and set(actual_names) in expected_name_sets
        )
    if "saved_scope_count" in contract:
        checks["saved_scope_count"] = (
            len(scopes) == contract["saved_scope_count"]
        )
    return checks


def _drain_known_timeline_interrupt(
    service: PromotionProductionEntryService,
    *,
    snapshot: Mapping[str, object],
    event: Mapping[str, object],
    query: Mapping[str, object],
    event_key: str,
    contract: Mapping[str, object],
    player: int,
    connection_generation: int,
) -> dict[str, object]:
    context_value = query.get("current_event_window_context")
    context = context_value if isinstance(context_value, Mapping) else {}
    checks = _known_interrupt_checks(
        snapshot=snapshot,
        event=event,
        context=context,
        event_key=event_key,
        contract=contract,
    )
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise PromotionProductionEntryError(
            f"known promotion-timeline interrupt {event_key!r} drifted: {failed!r}"
        )

    # A context query publishes a newer driver revision.  Rebind the same
    # paused event immediately before mutation instead of reusing the query's
    # stale pre-command revision.
    selection_snapshot, selection_event = _binding(
        service.snapshot(),
        player=player,
        connection_generation=connection_generation,
    )
    pre_selection_checks = {
        "paused": selection_snapshot.get("paused") is True,
        "date_raw": _contract_date_matches(
            selection_snapshot.get("date_raw"), contract
        ),
        "event_present": selection_event is not None,
        "event_instance_id": (
            selection_event.get("event_instance_id")
            if isinstance(selection_event, Mapping)
            else None
        )
        == event.get("event_instance_id"),
        "option_count": (
            selection_snapshot.get("active_event", {}).get("option_count")
            if isinstance(selection_snapshot.get("active_event"), Mapping)
            else None
        )
        == contract.get("snapshot_option_count", contract["option_count"]),
    }
    if not all(pre_selection_checks.values()) or selection_event is None:
        failed = sorted(
            name for name, passed in pre_selection_checks.items() if not passed
        )
        raise PromotionProductionEntryError(
            f"known promotion-timeline interrupt {event_key!r} changed before "
            f"selection: {failed!r}"
        )

    option_number = int(contract["selected_option_number"])
    selection = service.select_event_option(
        option_number,
        event_instance_id=int(selection_event["event_instance_id"]),
        expected_revision=int(selection_event["revision"]),
    )
    submission = _accepted(selection, f"select-event-option-{option_number}")
    event_selection_value = submission.get("event_selection")
    event_selection = (
        event_selection_value
        if isinstance(event_selection_value, Mapping)
        else {}
    )
    selection_checks = {
        "option_number": submission.get("option_number") == option_number,
        "option_index": submission.get("option_index")
        == contract["selected_native_option_index"],
        "postcondition_verified": event_selection.get("postcondition_verified")
        is True,
        "old_event_instance_id": event_selection.get("old_event_instance_id")
        == selection_event["event_instance_id"],
        "selected_option_number": event_selection.get("selected_option_number")
        == option_number,
        "selected_native_option_index": event_selection.get(
            "selected_native_option_index"
        )
        == contract["selected_native_option_index"],
        "old_instance_not_retained": event_selection.get(
            "new_event_instance_id"
        )
        != selection_event["event_instance_id"],
    }
    if not all(selection_checks.values()):
        failed = sorted(
            name for name, passed in selection_checks.items() if not passed
        )
        raise PromotionProductionEntryError(
            f"known promotion-timeline interrupt {event_key!r} option "
            f"{option_number} did not close cleanly: {failed!r}"
        )
    return {
        "event_definition_key": event_key,
        "date_raw": selection_snapshot["date_raw"],
        "event_instance_id": selection_event["event_instance_id"],
        "identity_checks": checks,
        "pre_selection_checks": pre_selection_checks,
        "selection": submission,
        "selection_checks": selection_checks,
        "result": "GREEN",
    }


def enter_promotion_source_checkpoint_v1(
    service: PromotionProductionEntryService,
    *,
    timeout_seconds: float = 300.0,
    poll_interval_seconds: float = 0.05,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    evidence_out: dict[str, object] | None = None,
) -> dict[str, object]:
    """Open player B1, advance to .146, choose option 1, stop on D+1 .147."""
    if timeout_seconds <= 0 or poll_interval_seconds < 0:
        raise ValueError("promotion entry timing is invalid")
    initial, initial_event = _binding(service.snapshot())
    player = int(initial["played_character"]["character_id"])
    generation = int(initial["diagnostics"]["connection_generation"])
    starting_date = int(initial["date_raw"])
    # The caller retains this same object even if a later interrupt raises.
    # R59/R61 lost their accumulated timeline because only success returned it.
    evidence: dict[str, object] = {} if evidence_out is None else evidence_out
    evidence.update({
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_production_entry",
        "result": "RED",
        "readiness": "static-ready-live-pending",
        "player_character_id": player,
        "connection_generation": generation,
        "starting_date_raw": starting_date,
        "advance_bound": {
            "b1_authored_days": B1_AUTHORED_ADVANCE_DAYS,
            "post_publication_observation_days": (
                POST_PUBLICATION_OBSERVATION_DAYS
            ),
            "total_days": MAX_ADVANCE_DAYS,
        },
        "paused_progress_settle_seconds": PAUSED_PROGRESS_SETTLE_SECONDS,
        "review_action": None,
        "review_action_postcondition": None,
        "m146_option1_submission": None,
        "m146_date_raw": None,
        "timeline_interrupt_drains": [],
        "unexpected_event": None,
        "target_binding": None,
        "action_ack_used_as_state_evidence": False,
        "fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "observations": [],
        "progress_observations": [],
        "pre_submission_revision_rebinds": [],
        "progress_query_rebinds": [],
        "initial_known_interrupt": None,
    })
    if initial_event is not None:
        key, _ = _event_definition(service, initial_event, sleeper=sleeper)
        if key == M147:
            evidence["result"] = "GREEN"
            evidence["readiness"] = "paused-real-zg361pp.147"
            evidence["target_binding"] = initial_event
            return evidence
        if key not in KNOWN_TIMELINE_INTERRUPTS:
            raise PromotionProductionEntryError(
                f"promotion entry started on unexpected event {key!r}"
            )
        # A retained client can reconnect while the prior client was
        # validating a known modal.  Preserve that exact event and let the
        # normal loop query, validate and drain it after rebinding the query's
        # newer public revision.
        evidence["initial_known_interrupt"] = key
        initial, initial_event = _binding(
            service.snapshot(),
            player=player,
            connection_generation=generation,
        )
    if initial.get("paused") is not True:
        pause = _map_control_from_latest_binding(
            service,
            step="pause-map",
            player=player,
            connection_generation=generation,
            rebind_audit=evidence["pre_submission_revision_rebinds"],
        )
        # A retained client commonly attaches while speed 5 is still running.
        # The pause ACK only proves command dispatch; wait for the next native
        # heartbeat before binding the first strict paused-frame query, exactly
        # as the polling path below already does.
        sleeper(PAUSED_PROGRESS_SETTLE_SECONDS)
        initial, _ = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
    before = service.query_zhongguo_promotion_source_progress_v1(
        "promo.entry.before", expected_revision=int(initial["revision"])
    )
    evidence["initial_progress"] = copy.deepcopy(before)
    progress = before.get("zhongguo_promotion_source_progress")
    if before.get("status") != "available" or not isinstance(progress, dict):
        unavailable_reason = (
            progress.get("unavailable_reason")
            if isinstance(progress, Mapping)
            else "payload_missing"
        )
        widgets = progress.get("widgets") if isinstance(progress, Mapping) else None
        unavailable_widgets = []
        if isinstance(widgets, list):
            for widget in widgets:
                if not isinstance(widget, Mapping):
                    continue
                exists = widget.get("exists")
                if not (
                    isinstance(exists, Mapping)
                    and exists.get("status") == "available"
                    and exists.get("value") is True
                ):
                    runtime_name = widget.get("runtime_name")
                    unavailable_widgets.append(
                        runtime_name if isinstance(runtime_name, str) else "<unnamed>"
                    )
        raise PromotionProductionEntryError(
            "fixed promotion progress observer is unavailable: "
            f"reason={unavailable_reason!r}; "
            f"unavailable_widgets={unavailable_widgets!r}"
        )
    if not any(widget_visible(progress, index) for index in (2, 3, 4)):
        if not widget_visible(progress, 1):
            raise PromotionProductionEntryError(
                "real review-now product action is not eligible on this seed"
            )
        action = service.activate_zhongguo_review_now_v1(
            "promo.entry.review", before,
            expected_revision=int(initial["revision"]),
        )
        evidence["review_action"] = action
        after_snapshot, _ = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
        after = service.query_zhongguo_promotion_source_progress_v1(
            "promo.entry.after",
            expected_revision=int(after_snapshot["revision"]),
        )
        evidence["post_action_progress"] = copy.deepcopy(after)
        try:
            evidence["review_action_postcondition"] = (
                verify_review_now_independent_postcondition_v1(
                    action_result=action,
                    before_query_sequence=int(before["query_sequence"]),
                    after_result=after,
                    expected_connection_generation=generation,
                    expected_player_character_id=player,
                )
            )
        except ValueError as error:
            raise PromotionProductionEntryError(str(error)) from error

    deadline = clock() + timeout_seconds
    last_progress_date_raw = starting_date
    consecutive_progress_query_rebinds = 0
    while clock() < deadline:
        snapshot, event = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
        date_raw = int(snapshot["date_raw"])
        if date_raw > starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY:
            raise PromotionProductionEntryError(
                "promotion path exceeded its 550-day product observation "
                "bound (400-day authored B1 window plus 150-day "
                "post-publication window)"
            )
        # Do not immediately pause a speed-5 map again before even one native
        # date transition. R91 proved that 50 ms pause/resume churn can keep
        # the product on the same date and query the first, not-yet-settled
        # paused snapshot. A rendered event still forces an immediate pause.
        has_active_event_surface = isinstance(
            snapshot.get("active_event"), Mapping
        )
        if (
            snapshot.get("paused") is not True
            and not has_active_event_surface
            and date_raw <= last_progress_date_raw
        ):
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue

        # The fixed GUI-backed progress observer is a paused-frame query.
        # Once a new date/event boundary exists, pause and wait past one native
        # 250 ms heartbeat before binding the query.
        if snapshot.get("paused") is not True:
            _map_control_from_latest_binding(
                service,
                step="pause-map",
                player=player,
                connection_generation=generation,
                rebind_audit=evidence["pre_submission_revision_rebinds"],
            )
            sleeper(PAUSED_PROGRESS_SETTLE_SECONDS)
            snapshot, event = _binding(
                service.snapshot(), player=player,
                connection_generation=generation,
            )
            date_raw = int(snapshot["date_raw"])
            if date_raw > starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY:
                raise PromotionProductionEntryError(
                    "promotion path exceeded its 550-day product observation "
                    "bound (400-day authored B1 window plus 150-day "
                    "post-publication window)"
                )
            if snapshot.get("paused") is not True:
                if poll_interval_seconds:
                    sleeper(poll_interval_seconds)
                continue

        should_sample_progress = (
            date_raw > last_progress_date_raw or event is not None
        )
        if should_sample_progress:
            observations = evidence["observations"]
            assert isinstance(observations, list)
            progress_observations = evidence["progress_observations"]
            assert isinstance(progress_observations, list)
            try:
                progress_query = (
                    service.query_zhongguo_promotion_source_progress_v1(
                        f"promo.entry.poll.{len(progress_observations) + 1}",
                        expected_revision=int(snapshot["revision"]),
                    )
                )
            except BridgeUnavailableError as error:
                if not any(
                    marker in str(error)
                    for marker in _TRANSIENT_PROGRESS_BINDING_ERRORS
                ):
                    raise
                consecutive_progress_query_rebinds += 1
                rebinds = evidence["progress_query_rebinds"]
                assert isinstance(rebinds, list)
                rebinds.append({
                    "attempt": consecutive_progress_query_rebinds,
                    "stale_revision": int(snapshot["revision"]),
                    "date_raw": date_raw,
                    "active_event": event is not None,
                    "error": f"{type(error).__name__}: {error}",
                    "state_mutation_submitted": False,
                })
                if (
                    consecutive_progress_query_rebinds
                    >= MAX_PRE_SUBMISSION_REBIND_ATTEMPTS
                ):
                    raise
                sleeper(PAUSED_PROGRESS_SETTLE_SECONDS)
                continue
            consecutive_progress_query_rebinds = 0
            observations.append({
                "revision": snapshot["revision"],
                "date_raw": date_raw,
                "paused": snapshot.get("paused"),
                "active_event": event is not None,
            })
            progress_observations.append(
                _compact_progress_observation(
                    progress_query,
                    date_raw=date_raw,
                    revision=int(snapshot["revision"]),
                )
            )
            last_progress_date_raw = date_raw
        if isinstance(snapshot.get("active_event"), Mapping) and event is None:
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue
        if event is not None:
            key, event_query = _event_definition(service, event, sleeper=sleeper)
            if key == M147:
                m146_date = evidence.get("m146_date_raw")
                if not isinstance(m146_date, int) or date_raw < m146_date + HOURS_PER_DAY:
                    raise PromotionProductionEntryError(
                        "zg361pp.147 was not independently observed at D+1"
                    )
                evidence["result"] = "GREEN"
                evidence["readiness"] = "paused-real-zg361pp.147"
                evidence["target_binding"] = event
                return evidence
            contract = KNOWN_TIMELINE_INTERRUPTS.get(key)
            drains = evidence["timeline_interrupt_drains"]
            assert isinstance(drains, list)
            if contract is not None:
                contract = _timeline_contract_for_window(
                    contract, starting_date=starting_date,
                )
                occurrence_count = sum(
                    isinstance(row, Mapping)
                    and row.get("event_definition_key") == key
                    for row in drains
                )
                max_occurrences = int(contract.get("max_occurrences", 1))
                if occurrence_count >= max_occurrences:
                    raise PromotionProductionEntryError(
                        "known promotion-timeline interrupt exceeded its "
                        f"occurrence bound: {key!r}"
                    )
                drains.append(
                    _drain_known_timeline_interrupt(
                        service,
                        snapshot=snapshot,
                        event=event,
                        query=event_query,
                        event_key=key,
                        contract=contract,
                        player=player,
                        connection_generation=generation,
                    )
                )
                if poll_interval_seconds:
                    sleeper(poll_interval_seconds)
                continue
            if key != M146 or evidence.get("m146_option1_submission") is not None:
                evidence["unexpected_event"] = {
                    "event_definition_key": key,
                    "snapshot": copy.deepcopy(dict(snapshot)),
                    "event": copy.deepcopy(dict(event)),
                    "query": copy.deepcopy(dict(event_query)),
                }
                raise PromotionProductionEntryError(
                    f"promotion path encountered unexpected event {key!r}"
                )
            selection_snapshot, selection_event = _binding(
                service.snapshot(),
                player=player,
                connection_generation=generation,
            )
            if (
                selection_event is None
                or selection_event.get("event_instance_id")
                != event.get("event_instance_id")
                or selection_snapshot.get("date_raw") != date_raw
            ):
                raise PromotionProductionEntryError(
                    "zg361pp.146 changed before option selection"
                )
            submission = service.select_event_option(
                1,
                event_instance_id=int(selection_event["event_instance_id"]),
                expected_revision=int(selection_event["revision"]),
            )
            evidence["m146_option1_submission"] = _accepted(
                submission, "select-event-option-1"
            )
            evidence["m146_date_raw"] = date_raw
            # The option ACK proves dispatch only; the D+1 .147 event query
            # below is the result evidence.
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue
        if snapshot.get("speed") != 5:
            _map_control_from_latest_binding(
                service,
                step="set-speed-5",
                player=player,
                connection_generation=generation,
                rebind_audit=evidence["pre_submission_revision_rebinds"],
            )
            # Setting speed while paused is applied asynchronously by CK3.
            # R90 proved that leaving the map paused until the next loop can
            # expose the old cached snapshot to a second progress query while
            # the native speed field is already changing.  Resume in this
            # same loop so the next progress sample always follows a complete
            # running -> pause transition.
            snapshot, _ = _binding(
                service.snapshot(), player=player,
                connection_generation=generation,
            )
        if snapshot.get("paused") is True:
            rebind_audit = evidence["pre_submission_revision_rebinds"]
            assert isinstance(rebind_audit, list)
            _resume_map_from_latest_binding(
                service,
                player=player,
                connection_generation=generation,
                rebind_audit=rebind_audit,
            )
        if poll_interval_seconds:
            sleeper(poll_interval_seconds)
    raise PromotionProductionEntryError(
        "timed out before paused real zg361pp.147"
    )


__all__ = [
    "B1_AUTHORED_ADVANCE_DAYS",
    "MAX_ADVANCE_DAYS",
    "M146",
    "M147",
    "KNOWN_TIMELINE_INTERRUPTS",
    "MAX_PRE_SUBMISSION_REBIND_ATTEMPTS",
    "PAUSED_PROGRESS_SETTLE_SECONDS",
    "POST_PUBLICATION_OBSERVATION_DAYS",
    "PromotionProductionEntryError",
    "PromotionProductionEntryService",
    "enter_promotion_source_checkpoint_v1",
]
