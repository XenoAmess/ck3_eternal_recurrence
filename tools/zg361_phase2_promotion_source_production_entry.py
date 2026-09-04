#!/usr/bin/env python3
"""Drive the exact product path to paused ``zg361pp.147`` without CK3 launch."""

from __future__ import annotations

import copy
import time
from collections.abc import Callable, Mapping
from typing import Protocol

from xar_autoplayer.bridge.zhongguo_promotion_source_progress_contract import (
    verify_review_now_independent_postcondition_v1,
    widget_visible,
)
from zg361_phase2_promotion_compensation_action_cell import _snapshot_binding


M146 = "zg361pp.146"
M147 = "zg361pp.147"
MAX_ADVANCE_DAYS = 400
HOURS_PER_DAY = 24

# These are not namespace-wide allowlists.  They are exact pending events
# already proven on the immutable phase-two seed lineage.  Each contract binds
# the paused date, played root, typed saved scopes and complete enabled option
# shape before one fixed, source-reviewed option is sent.
KNOWN_TIMELINE_INTERRUPTS: dict[str, dict[str, object]] = {
    "zg361b2.40": {
        "date_raw": 53147040,
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
        # Vanilla governor-removal letter emitted after the interaction has
        # already resolved.  It exposes one acknowledgement option only.
        # Three generic interaction slots retain their names/type after the
        # referenced characters have gone stale; bind that exact degraded
        # identity shape instead of fabricating character IDs.
        "date_raw": (53147256, 53151600),
        # Two live runs delivered the same already-resolved interaction
        # letter on different ticks while every semantic field stayed exact.
        "date_raw_range": (53147256, 53151600),
        "root_character_id": 29037,
        "character_scopes": {
            "actor": 32904,
            "recipient": 29037,
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
            "previous_holder": 28557,
            "new_holder": 29037,
            "previous_governor": 28557,
        },
        "scope_types": {
            "title": "landed_title",
            "transfer_type": "flag",
            "nf_gov_type": "government_type",
            "governor_title": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_count": 7,
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
        "character_scopes": {
            "grieving_child": 16780023,
            "orphan_mother": 16780148,
            "orphan_father": 16780149,
            "parent": 16780149,
            "guardian": 31647,
            "messenger": 31647,
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
        "character_scopes": {
            "market_vendor": 16780002,
            "traveling_merchant": 16780004,
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
        "date_raw": (53148048, 53149416, 53152368),
        # Multiple live runs place this exact succession notice on adjacent
        # day ticks.  Bind it to the observed product window rather than an
        # ever-growing set of discrete timestamps; every other identity and
        # option-shape check remains exact.
        "date_raw_range": (53148048, 53152368),
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
            "administrator": 16780148,
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
        # Product Jingcha mandate at D+161.  The legal default opens the
        # activity planner and schedules its hidden compliance deadline 300
        # days later, beyond the D+330 promotion target.  Refusal would write
        # manager-governance facts and a next-review KPI penalty, so it is not
        # neutral for this capture lineage.
        "date_raw": 53150880,
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "saved_scope_count": 0,
        "option_count": 2,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361b1.200": {
        # Product B1 self-review receipt at D+238.  The honest branch records
        # the already frozen mid-cycle evidence without the +15/-15 bias of
        # the exaggerated/conservative branches, while advancing the same
        # ticket-guarded review state machine.
        "date_raw": 53152728,
        "root_character_id": 29037,
        "character_scopes": {
            "zga_phase2_seed_player": 29037,
            "zg361_b1_ticket_owner": 29628,
            "zg361_b1_self_ticket_owner": 29628,
            "zg361_b1_self_ticket_subject": 29037,
        },
        "scope_types": {
            "zg361_b1_ticket_cycle": "value",
            "zg361_b1_ticket_case": "value",
            "zg361_b1_ticket_state": "value",
            "zg361_b1_self_ticket_cycle": "value",
            "zg361_b1_self_ticket_case": "value",
            "zg361_b1_self_ticket_state": "value",
        },
        "boolean_scopes": (),
        "saved_scope_count": 10,
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "spymaster_task.0381": {
        # Independent vanilla Find Secrets hook opportunity.  Option 1 spends
        # gold and fabricates a hook; option 2 only grants the one typed third
        # party a decaying opinion modifier toward root.  The same exact event
        # can recur on this seed; two distinct live dates have been observed,
        # so only two contract-matching occurrences are admitted.
        "date_raw": (53148768, 53152656),
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
        "date_raw": 53148768,
        "root_character_id": 29037,
        "character_scopes": {
            "councillor": 27963,
            "councillor_liege": 29037,
            "target_character": 27051,
        },
        "boolean_scopes": ("no_secrets_here",),
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
        "date_raw": 53152896,
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
        "date_raw": 53152896,
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
        return lower <= value <= upper
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
    native_option_indices_value = contract.get(
        "native_option_indices", tuple(range(int(option_count)))
    )
    native_option_indices = (
        native_option_indices_value
        if isinstance(native_option_indices_value, tuple)
        else ()
    )
    authored_options_exact = (
        len(options) == option_count
        and len(native_option_indices) == option_count
    )
    if authored_options_exact:
        for index, row_value in enumerate(options):
            row = row_value if isinstance(row_value, Mapping) else {}
            if not (
                row.get("rendered_index") == index
                and row.get("native_option_index")
                == native_option_indices[index]
                and row.get("shown") is True
                and row.get("enabled") is True
                and row.get("fallback") is False
                and row.get("cancel") is False
            ):
                authored_options_exact = False
                break

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
) -> dict[str, object]:
    """Open player B1, advance to .146, choose option 1, stop on D+1 .147."""
    if timeout_seconds <= 0 or poll_interval_seconds < 0:
        raise ValueError("promotion entry timing is invalid")
    initial, initial_event = _binding(service.snapshot())
    player = int(initial["played_character"]["character_id"])
    generation = int(initial["diagnostics"]["connection_generation"])
    starting_date = int(initial["date_raw"])
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_production_entry",
        "result": "RED",
        "readiness": "static-ready-live-pending",
        "player_character_id": player,
        "connection_generation": generation,
        "starting_date_raw": starting_date,
        "review_action": None,
        "review_action_postcondition": None,
        "m146_option1_submission": None,
        "m146_date_raw": None,
        "timeline_interrupt_drains": [],
        "target_binding": None,
        "action_ack_used_as_state_evidence": False,
        "fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "observations": [],
    }
    if initial_event is not None:
        key, _ = _event_definition(service, initial_event, sleeper=sleeper)
        if key == M147:
            evidence["result"] = "GREEN"
            evidence["readiness"] = "paused-real-zg361pp.147"
            evidence["target_binding"] = initial_event
            return evidence
        raise PromotionProductionEntryError(
            f"promotion entry started on unexpected event {key!r}"
        )
    if initial.get("paused") is not True:
        pause = service.execute_step(
            "pause-map", expected_revision=int(initial["revision"])
        )
        _accepted(pause, "pause-map")
        initial, _ = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
    before = service.query_zhongguo_promotion_source_progress_v1(
        "promo.entry.before", expected_revision=int(initial["revision"])
    )
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
    while clock() < deadline:
        snapshot, event = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
        date_raw = int(snapshot["date_raw"])
        if date_raw > starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY:
            raise PromotionProductionEntryError(
                "promotion path exceeded its 400-day product bound"
            )
        observations = evidence["observations"]
        assert isinstance(observations, list)
        observations.append({
            "revision": snapshot["revision"],
            "date_raw": date_raw,
            "paused": snapshot.get("paused"),
            "active_event": event is not None,
        })
        if isinstance(snapshot.get("active_event"), Mapping) and event is None:
            _accepted(
                service.execute_step(
                    "pause-map", expected_revision=int(snapshot["revision"])
                ),
                "pause-map",
            )
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
        if snapshot.get("speed") != 1:
            _accepted(
                service.execute_step(
                    "set-speed-1", expected_revision=int(snapshot["revision"])
                ),
                "set-speed-1",
            )
        elif snapshot.get("paused") is True:
            _accepted(
                service.execute_step(
                    "resume-map", expected_revision=int(snapshot["revision"])
                ),
                "resume-map",
            )
        if poll_interval_seconds:
            sleeper(poll_interval_seconds)
    raise PromotionProductionEntryError(
        "timed out before paused real zg361pp.147"
    )


__all__ = [
    "MAX_ADVANCE_DAYS",
    "M146",
    "M147",
    "KNOWN_TIMELINE_INTERRUPTS",
    "PromotionProductionEntryError",
    "PromotionProductionEntryService",
    "enter_promotion_source_checkpoint_v1",
]
