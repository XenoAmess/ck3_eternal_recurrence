#!/usr/bin/env python3
"""Drive a bounded exact-product path to a requested paused event."""

from __future__ import annotations

import copy
import importlib
import sys
import time
from collections.abc import Callable, Mapping
from typing import Protocol


# The live recovery wrapper reloads this entry module while CK3 remains
# paused on the same event. Contract shards imported below are separate
# modules, so Python would otherwise retain their pre-fix objects in
# sys.modules. Refresh already-loaded data-only shards before rebinding the
# exported mappings; a cold first import has nothing to refresh.
for _module_name, _module in tuple(sys.modules.items()):
    _module_leaf = _module_name.rsplit(".", 1)[-1]
    if (
        _module_leaf.startswith("zg361_phase")
        and _module_leaf.endswith("_contracts")
        and _module is not None
    ):
        importlib.reload(_module)

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
from zg361_phase2_promotion_credit_project_portfolio_contracts import (
    CREDIT_PROJECT_PORTFOLIO_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_credit_project_resource_race_contracts import (
    CREDIT_PROJECT_RESOURCE_RACE_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_credit_project_reporting_policy_contracts import (
    CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_credit_project_matrix_handoff_contracts import (
    CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_credit_project_governance_contracts import (
    CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_credit_project_stop_loss_postmortem_contracts import (
    CREDIT_PROJECT_STOP_LOSS_POSTMORTEM_TIMELINE_CONTRACTS,
)
from zg361_phase3_metrics_delivery_aa_contracts import (
    PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS,
)
from zg361_phase3_metrics_delivery_ag_contracts import (
    PHASE3_METRICS_DELIVERY_AG_TIMELINE_CONTRACTS,
)
from zg361_phase3_metrics_delivery_aj_contracts import (
    PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_vanilla_secret_interrupt_contracts import (
    VANILLA_SECRET_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_vanilla_intrigue_temptation_interrupt_contracts import (
    VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_vanilla_natural_disaster_interrupt_contracts import (
    VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_vanilla_ep3_emperor_interrupt_contracts import (
    VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_vanilla_seduce_interrupt_contracts import (
    VANILLA_SEDUCE_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_vanilla_ep1_flavor_interrupt_contracts import (
    VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_pp_bargaining_contracts import (
    PP_BARGAINING_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_pp_action_item_contracts import (
    PP_ACTION_ITEM_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_pp_feedback_completion_contracts import (
    PP_FEEDBACK_COMPLETION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_pp_public_private_contracts import (
    PP_PUBLIC_PRIVATE_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_pp_receipt_contracts import (
    PP_RECEIPT_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_central_contracts import CENTRAL_TIMELINE_CONTRACTS
from zg361_phase2_promotion_career_learning_contracts import (
    CAREER_LEARNING_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_imperial_contracts import (
    MANAGER_IMPERIAL_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_court_contracts import (
    MANAGER_COURT_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_health_contracts import (
    MANAGER_HEALTH_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_health_aging_contracts import (
    MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_death_contracts import (
    MANAGER_DEATH_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_parent_contracts import (
    MANAGER_PARENT_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_birth_contracts import (
    MANAGER_BIRTH_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_chancellor_contracts import (
    MANAGER_CHANCELLOR_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_debate_contracts import (
    MANAGER_DEBATE_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tgp_petition_contracts import (
    MANAGER_TGP_PETITION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tgp_interaction_contracts import (
    MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tgp_ministry_contracts import (
    MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_tribute_contracts import (
    MANAGER_TRIBUTE_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_nickname_contracts import (
    MANAGER_NICKNAME_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_spymaster_contracts import (
    MANAGER_SPYMASTER_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_befriend_contracts import (
    MANAGER_BEFRIEND_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_annual_summary_contracts import (
    MANAGER_ANNUAL_SUMMARY_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_elimination_contracts import (
    MANAGER_ELIMINATION_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_holy_war_contracts import (
    MANAGER_HOLY_WAR_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_council_claim_contracts import (
    MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS,
)
from zg361_phase2_promotion_manager_trait_contracts import (
    MANAGER_TRAIT_TIMELINE_CONTRACTS,
)


M146 = "zg361pp.146"
M147 = "zg361pp.147"
# The managed product episode always starts from the immutable phase-two seed.
# A retained Python client may reconnect much later, but reconnecting must not
# grant the same CK3 process another full authored observation window.
PRODUCT_TIMELINE_ORIGIN_DATE_RAW = 53147016
B1_AUTHORED_ADVANCE_DAYS = 400
# R182 proved that the post-publication path is not a short D+2 handoff.  The
# fixed acceptance route must naturally cross Compensation L's D+365 deferred
# journal and AF's D+365 cliff plus eleven D+30 cadence ticks before Central
# can reach the player-visible PP source event.  Keep one finite tail from the
# canonical seed; do not renew it on retained-client reconnects.
# R245 reached the healthy stage-nine tail after 1,962 days, proving that the
# original 1,900-day whole-product window could reject the retained session
# before the source-authored stage-nine through stage-eleven chain completed.
# Keep a finite two-cycle bound while allowing that long tail to finish.
POST_PUBLICATION_OBSERVATION_DAYS = 4200
PRODUCT_CYCLE_OPPORTUNITIES = 2
# R116 proved that the first Central portfolio can finish while a second real
# player B1 cycle is already active.  A one-cycle absolute cap stopped only 25
# days into that second cycle.  Keep one canonical absolute deadline, rather
# than granting time per retained client, but cover two complete finite
# B1 -> post-publication opportunities from the immutable seed.
PRE_WORKFORCE_MAX_ADVANCE_DAYS = (
    PRODUCT_CYCLE_OPPORTUNITIES * B1_AUTHORED_ADVANCE_DAYS
    + POST_PUBLICATION_OBSERVATION_DAYS
)
# The cross-cycle source contract intentionally pauses on the third real
# zg361we.356 occurrence. R355 reached the first Workforce AB entry at D+4950,
# proving that the former D+5000 cap covered only the pre-Workforce critical
# path. The exact-build endgame seam already bounds one natural Workforce
# receipt/history opportunity to 730 days. Reserve three such finite windows
# from the same canonical seed; retained-client reconnects still cannot renew
# any part of the budget.
WORKFORCE_CYCLE_OBSERVATION_DAYS = 730
ENDGAME_TARGET_WORKFORCE_CYCLES = 3
MAX_ADVANCE_DAYS = (
    PRE_WORKFORCE_MAX_ADVANCE_DAYS
    + ENDGAME_TARGET_WORKFORCE_CYCLES
    * WORKFORCE_CYCLE_OBSERVATION_DAYS
)
HOURS_PER_DAY = 24
# Native bridge snapshots publish on a 250 ms heartbeat. A just-submitted
# pause can become visible to Python before the next heartbeat has replaced
# every cached Snapshot field used by the query's direct-read equality gate.
PAUSED_PROGRESS_SETTLE_SECONDS = 0.35
MAX_PRE_SUBMISSION_REBIND_ATTEMPTS = 4
ZG361_6_RETAIN_WAIT_DAYS = 365
ZG361_6_MODAL_ADVANCE_TIMEOUT_SECONDS = 10.0
_TRANSIENT_PROGRESS_BINDING_ERRORS = (
    "promotion source progress lacks a stable paused player binding",
    "ZhongGuo promotion source progress binding changed or is not ready",
    "promotion source progress is not bound to the requested frame",
)


def _optional_scope_name_sets(
    required: tuple[str, ...], optional: tuple[str, ...]
) -> tuple[tuple[str, ...], ...]:
    """Expand one finite optional-scope envelope to exact name sets."""

    return tuple(
        required
        + tuple(
            name
            for index, name in enumerate(optional)
            if mask & (1 << index)
        )
        for mask in range(1 << len(optional))
    )

# Source-reviewed, player-visible Workforce events on the non-debt route from
# Central stage 11 through the cross-cycle endgame.  The generated product
# gives every ordinary card three authored routes, except the one-option
# appointment acknowledgement.  M264 and its three handoff cards have
# trigger-filtered projections handled explicitly below.  Repetition is
# bounded to the three real Workforce cycles required by the endgame source.
_MANAGER_RECOVERY_WORKFORCE_OPTION_COUNTS: dict[int, int] = {
    **{event_id: 3 for event_id in range(242, 254)},
    **{event_id: 3 for event_id in range(254, 274)},
    274: 1,
    275: 3,
    276: 3,
    277: 3,
    355: 3,
    356: 3,
    360: 3,
    361: 3,
    5264: 4,
    5265: 4,
    5266: 4,
}

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
    "bp1_yearly.5725": {
        # Vanilla Khutulun matchmaking invitation.  Exact CK3 1.19.0.6 source
        # gives option 1 a seven-day follow-up chain, while option 2 ends the
        # encounter immediately with only matchmaker opinion/stress effects.
        # Bind both generated character scopes and select the terminal branch
        # so this unrelated yearly story cannot occupy the Phase-2 timeline.
        "date_raw": 53147520,
        "root_character_id": 29037,
        "character_scopes": {
            "matchmaker_courtier": 31003,
            "khutulun": 16779972,
        },
        "boolean_scopes": (),
        "saved_scope_count": 2,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
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
    "culture_notification.1111": {
        # CK3 1.19.0.6 culture divergence notification. Its two authored
        # options are mutually exclusive founder/non-founder acknowledgements;
        # both contain only the same custom tooltip and no gameplay effect.
        # R135 observed the played manager as a non-founder, so exactly one
        # rendered button mapped to native option index 1. Bind the complete
        # five-scope frame before dismissing that acknowledgement.
        "date_raw": 53148048,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "founder": 35761,
        },
        "scope_types": {
            "parent_culture_1": "culture",
            "new_culture": "culture",
            "parent_1": "culture",
            "ethos": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "intrigue_scheming.1202": {
        # CK3 1.19.0.6 hired-spy follow-up. The temporary spy is created in
        # immediate. Option 1 removes that generated courtier and grants only
        # minor intrigue-lifestyle XP; options 2/3 respectively retain the
        # spy with a decade-long county modifier or kill them for dread/XP.
        # R316 observed the exact root, quarter value, generated spy and dense
        # three-option frame. Take the terminal, least-durable option 1.
        "date_raw": 53156712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "hired_spy": (29037, 32904),
        },
        "scope_types": {
            "quarter": "value",
            "hired_spy": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (("quarter", "hired_spy"),),
        "saved_scope_count": 2,
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "chancellor_task.1102": {
        # CK3 1.19.0.6 chancellor side effect. The immediate block has already
        # selected one current truce target; its sole authored option cancels
        # that one-way truce. There is no acknowledgement-only alternative,
        # so bind the exact manager root, three typed scopes and one-button
        # shape before selecting the only route needed to continue the line.
        "date_raw": 53151120,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "councillor_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "councillor": (29037,),
            "target": (29037,),
        },
        "scope_types": {
            "councillor": "character",
            "target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "councillor",
            "councillor_liege",
            "target",
        ),),
        "saved_scope_count": 3,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0070": {
        # CK3 1.19.0.6 celestial-government study event. Option 2 mutates the
        # selected councillor's skill by two points; option 3 mutates both the
        # played ruler and councillor. Option 1 has no player resource or skill
        # mutation and confines the unrelated event to friendship progress and
        # trait-dependent stress, making it the least invasive authored route.
        "date_raw": 53150712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "councillor": (29037,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "councillor": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "my_movement",
            "councillor",
        ),),
        "saved_scope_count": 2,
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0080": {
        # CK3 1.19.0.6 celestial family-subsidy request.  The played manager
        # is not in the conservative movement in R288, so native option 0 is
        # hidden and the three rendered choices map exactly to 1/2/3.  The
        # first two visible routes transfer family gold and either install a
        # durable estate modifier or mutate movement influence/power.  Native
        # option 3 ends the event without those estate or movement mutations,
        # confining the result to authored friendship/stress and conditional
        # opinion/resource effects.  Bind the generated family member and the
        # complete hidden-option projection before taking that terminal route.
        "date_raw": 53205336,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "root_scope": 29037,
        },
        "unique_character_scope_excludes": {
            "family_member": (29037,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "family_member": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "root_scope",
            "my_movement",
            "family_member",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0050": {
        # CK3 1.19.0.6 merit elder invitation. R154 had no old_elder scope,
        # so authored option 2 was hidden and the two rendered buttons mapped
        # to native indices 0/2. Option 0 installs a new elder relation and
        # changes merit; native option 2 is terminal and only grants the
        # source-authored lifestyle XP plus trait-dependent stress relief.
        # Bind the movement group, generated elder and complete two-of-three
        # option projection before taking that least invasive route.
        "date_raw": 53150712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "new_elder": (29037,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "new_elder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "my_movement",
            "new_elder",
        ),),
        "saved_scope_count": 2,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0060": {
        # CK3 1.19.0.6 celestial movement-rival event. R331 exposed native
        # options 1/2/3 while the intrigue-focus-only option 0 was hidden.
        # Native option 1 starts or strengthens a hostile scheme and reduces
        # the rival movement; option 3 enters a faith-dependent branch. Native
        # option 2 only grants the player's own movement a medium power gain,
        # so it is the narrow non-religious, non-hostile continuation route.
        # Bind both movement groups and the generated rival before selecting.
        "date_raw": 53219640,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "rival": (32904,),
        },
        "scope_types": {
            "my_movement": "situation_participant_group",
            "rival_movement": "situation_participant_group",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "my_movement",
            "rival_movement",
            "rival",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "tgp_movement_events.0150": {
        # CK3 1.19.0.6 Shinto-monk visit. The diplomat-only alliance route is
        # hidden in the R152 manager frame, leaving authored native options
        # 1/2/3. Option 1 installs a durable conversion discount and penalizes
        # zealot vassal opinion; option 2 runs a random conversion duel.
        # Option 3 has no RNG or follow-up event: it welcomes the monk, grants
        # medium diplomacy XP or prestige, and gives the sending ruler a small
        # opinion increase. Bind both generated characters and select that
        # deterministic, least invasive route.
        "date_raw": 53150712,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "other_ruler": (29037,),
            "monk": (29037,),
        },
        "character_scope_differs_from": {
            "other_ruler": ("monk",),
            "monk": ("other_ruler",),
        },
        "scope_types": {
            "other_ruler": "character",
            "monk": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "other_ruler",
            "monk",
        ),),
        "saved_scope_count": 2,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
    "ep3_decisions_event.2001": {
        # CK3 1.19.0.6 administrative-vassal confirmation request.  Option 1
        # begins the multi-event confirmation ceremony; option 2 terminates
        # the request immediately through the authored refusal effect.  The
        # refusal can change only this unrelated administrator relationship
        # and trait-dependent stress, while avoiding a new blocking event
        # chain during the bounded Phase-2 observation window. R163 observed
        # the complete two-character/two-option letter frame. R329 then
        # reached a second independent request on the bounded three-cycle
        # endgame lineage. R345 then observed three distinct confirmation
        # vassals at 53204640, 53226000, and 53246304 in one replay; all use
        # this exact terminal-refusal contract.
        "date_raw": 53157888,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "confirmation_liege": 29037,
        },
        "unique_character_scope_excludes": {
            "confirmation_vassal": (29037,),
        },
        "scope_types": {
            "confirmation_vassal": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "confirmation_vassal",
            "confirmation_liege",
        ),),
        "saved_scope_count": 2,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 3,
    },
    "adultery.0002": {
        # CK3 1.19.0.6 spouse-suspicion event. Confrontation opens a new event
        # chain, investigation runs a duel, and spying mutates the spymaster's
        # council task. Authored option 4 does nothing and is the only bounded
        # terminal route without those state changes. The hidden yearly picker
        # suppresses only the selected partner for five years; it has no
        # campaign-global one-shot gate, so validate every occurrence.
        "date_raw": 53169888,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "spouse": 29037,
        },
        "unique_character_scope_excludes": {
            "lover_spouse": (29037,),
        },
        "scope_types": {
            "lover_spouse": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "spouse",
            "lover_spouse",
        ),),
        "saved_scope_count": 2,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "stress_threshold.2202": {
        # CK3 1.19.0.6 response to another character's boiling-anger mental
        # break. R147 observed the played manager as the yelled-at root and
        # no pre-existing rival scope, so authored option 1 was hidden and the
        # sole rendered button mapped to native option index 1. The immediate
        # block is inert without rival; this remaining route only reduces the
        # player's stress. Bind both typed character scopes and the complete
        # one-of-two option shape before selecting that source-authored route.
        "date_raw": 53148288,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "character_to_yell_at": 29037,
        },
        "unique_character_scope_excludes": {
            "stress_character": (29037,),
        },
        "scope_types": {
            "stress_character": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "stress_character",
            "character_to_yell_at",
        ),),
        "saved_scope_count": 2,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (1,),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "ep1_flavor.0021": {
        # CK3 1.19.0.6 royal-court language quarrel. Route A applies mutual
        # dislike/cultural loss and adds a random diplomacy duel; route C
        # applies the same negative court/culture effects plus a ten-year
        # character modifier. Route B has no random duel or durable modifier
        # and confines the unrelated event to positive court opinions,
        # friendship progress, cultural acceptance and trait-dependent stress.
        # Bind the rival title, the generated rival/nitpicker relationship and
        # all three rendered options before taking that non-random route.
        "date_raw": 53215344,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "rival_monarch": (32904,),
            "nitpicker": (32904,),
        },
        "character_scope_differs_from": {
            "rival_monarch": ("nitpicker",),
            "nitpicker": ("rival_monarch",),
        },
        "scope_types": {
            "rival_realm": "landed_title",
            "rival_monarch": "character",
            "nitpicker": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "rival_realm",
            "rival_monarch",
            "nitpicker",
        ),),
        "saved_scope_count": 3,
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "ep1_flavor.2040": {
        # CK3 1.19.0.6 exotic-arms delivery. The R183 frame has no eligible
        # player artifact to trade, so authored option 1 is hidden and the
        # rendered buttons map to native indices 1/2. Authored option 2 spends
        # major gold and transfers the generated blade; authored option 3 is
        # the terminal refusal and adds no gameplay effect. Bind the complete
        # exact frame, including the source-defined holder/owner and generated
        # merchant lineage, before selecting that least-disruptive terminal
        # route. R286 proved the R183 holder and merchant IDs were allocator
        # output, while their relationships stayed exact. R330 observed the
        # source-authored poor-quality branch: its artifact helper additionally
        # saves the boolean ``exotic_blade_quality``. R350 exercised the other
        # source-authored artifact branch: the weapon/armor helpers save the
        # mutually exclusive flags ``weapon_type`` and ``armor_type``.
        "date_raw": 53174184,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "exotic_arms_target": 32904,
        },
        "character_scope_matches_any": {
            "exotic_blade_holder": ("owner",),
            "owner": ("exotic_blade_holder",),
        },
        "character_scope_differs_from": {
            "exotic_blade_holder": (
                "exotic_arms_target", "foreign_merchant",
            ),
            "foreign_merchant": (
                "exotic_blade_holder", "exotic_arms_target", "owner",
            ),
        },
        "scope_types": {
            "exotic_blade_holder": "character",
            "exotic_arms_target": "character",
            "owner": "character",
            "random_quality_bonus": "value",
            "quality": "value",
            "wealth": "value",
            "newly_created_artifact": "artifact",
            "merchant_county": "landed_title",
            "foreign_merchant": "character",
            "exotic_blade": "artifact",
        },
        "optional_scope_types": {
            "weapon_type": "flag",
            "armor_type": "flag",
            "exotic_blade_quality": "boolean",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "owner",
                "weapon_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "exotic_blade_quality",
                "owner",
                "weapon_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "owner",
                "armor_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
            (
                "exotic_blade_holder",
                "exotic_arms_target",
                "exotic_blade_quality",
                "owner",
                "armor_type",
                "random_quality_bonus",
                "quality",
                "wealth",
                "newly_created_artifact",
                "merchant_county",
                "foreign_merchant",
                "exotic_blade",
            ),
        ),
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "epidemic_events.1100": {
        # CK3 1.19.0.6 outbreak notification. Its immediate block has already
        # recorded the notified epidemic and installed county-side outbreak
        # effects before the modal opens. In R151 the manager had no court
        # physician, so the rendered buttons mapped to native indices 0/2; in
        # R289 the manager had a physician and they mapped to 0/1 instead.
        # Native options 1/2 both start a later physician/health event chain;
        # option 0 only applies the source-authored -2 governor trait XP when
        # eligible. Select option 0 as the smallest unrelated mutation, after
        # binding all three typed saved scopes and either exact mutually
        # exclusive physician-dependent option projection. Vanilla invokes
        # this once for each newly encountered epidemic and only suppresses
        # repeat notices for the same epidemic, so multiple independently
        # typed deliveries are valid inside the product observation window.
        "date_raw": 53148360,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {
            "epidemic": "epidemic",
            "province": "province",
            "infected_county": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "province",
            "infected_county",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (0, 1),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "option_count": 2,
                "native_option_indices": (0, 2),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "epidemic_events.1060": {
        # CK3 1.19.0.6 plague-scapegoat response. The immediate block has
        # already created the plague-witch-hunt story before the modal opens.
        # Native option 0 is hidden unless the player has very high piety. In
        # the observed manager frame the complete rendered projection is
        # therefore native options 1/2. Both install a ten-year county
        # modifier, but option 1 permits rampant witch trials while option 2
        # explicitly slows them and starts no additional event. Bind the two
        # epidemic aliases plus the source-created story before selecting the
        # deterministic option 2 route.
        "date_raw": 53225568,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "story_scope": "story",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "story_scope",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "max_occurrences": 1,
    },
    "faction_demand.1001": {
        # CK3 1.19.0.6 populist ultimatum. Native option 0 (culture/faith
        # conversion) may be visible when the 30-percent realm thresholds and
        # non-State-Faith gate pass; native option 1 is a distinct State Faith
        # route. Native option 2 immediately grants independence/transfers
        # titles, while native option 3 refuses and starts the faction war.
        # Conversion and immediate surrender both destroy invariants used by
        # this bounded manager observation. Refusal preserves the current
        # titles and roster while handing the war to the existing gameplay
        # state surface. Bind either observed rendered-option projection and
        # either exact source-authored saved-scope shape before refusing.
        "date_raw": 53229048,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "faction_target": 32904,
        },
        "unique_character_scope_excludes": {
            "peasant_leader": (32904,),
        },
        "scope_types": {
            "faction": "faction",
            "peasant_county": "landed_title",
            "target_title": "landed_title",
            "peasant_leader": "character",
        },
        "optional_scope_types": {
            "new_title": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": (
            (
                "faction",
                "peasant_county",
                "faction_target",
                "target_title",
                "peasant_leader",
            ),
            (
                "faction",
                "peasant_county",
                "faction_target",
                "target_title",
                "peasant_leader",
                "new_title",
            ),
        ),
        "option_count": 2,
        "snapshot_option_count": 4,
        "native_option_indices": (2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 2, 3),
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ),
        "max_occurrences": 1,
    },
    "char_interaction.0370": {
        # CK3 1.19.0.6 cease-paying-tribute notification. Its immediate block
        # has already ended the actor's tributary relation before this letter
        # opens. The retaliation route (native option 1) is hidden in the
        # observed frame because can_retaliate_trigger is false; that same
        # condition also makes the optional legitimacy loss in native option
        # 0 inert. Bind the sender/recipient and the exact three unavailable
        # generic interaction slots before acknowledging the sole rendered
        # no-op option.
        "date_raw": 53229720,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "recipient": 32904,
        },
        "unique_character_scope_excludes": {
            "actor": (32904,),
        },
        "unavailable_character_scopes": (
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "actor",
            "recipient",
            "secondary_actor",
            "secondary_recipient",
            "intermediary",
        ),),
        "saved_scope_count": 5,
        "option_count": 1,
        "snapshot_option_count": 2,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "physician_epidemic_events.1040": {
        # CK3 1.19.0.6 royal-alms proposal during a major epidemic. Native
        # option 0 installs a ten-year modifier across infected counties and
        # runs a disease-dependent five-percent infection roll against the
        # player. Native option 1 refuses with only minor piety loss and
        # trait-dependent stress, adding no modifier, RNG disease effect or
        # follow-up event. Bind both epidemic aliases and the generated court
        # physician before taking that deterministic terminal route.
        "date_raw": 53237808,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "physician": (32904,),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "physician": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "physician",
        ),),
        "saved_scope_count": 3,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "epidemic_events.5007": {
        # CK3 1.19.0.6 plague-yearly accusation against a court herbalist.
        # Native option 0 is visible only when root has a related lifestyle
        # trait. Native option 1 brands the herbalist a witch and imprisons
        # them; native option 2 only applies the authored opinion/stress and
        # possible potential-friend relation, making it the least invasive
        # available route in either exact projection. Bind the independently
        # selected accuser and herbalist before taking that terminal route.
        "date_raw": 53270256,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "herbalist": (32904,),
            "accuser": (32904,),
        },
        "character_scope_differs_from": {
            "herbalist": ("accuser",),
            "accuser": ("herbalist",),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "herbalist": "character",
            "accuser": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "herbalist",
            "accuser",
        ),),
        "saved_scope_count": 4,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "option_variants": (
            {
                "option_count": 2,
                "native_option_indices": (1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
            {
                "option_count": 3,
                "native_option_indices": (0, 1, 2),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "epidemic_events.5009": {
        # CK3 1.19.0.6 plague-market herbal-sachet offer. Native routes 0/1
        # transfer the generated artifact, spend gold and install long-lived
        # modifiers; native 2 still installs the protection modifier. Native
        # 3 buys nothing and only applies trait-dependent stress before the
        # merchant cleanup shared by every route. Bind the generated artifact
        # metadata and merchant/owner/creator identity before selecting it.
        "date_raw": 53254032,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "merchant": (32904,),
        },
        "character_scope_matches_any": {
            "owner": ("merchant",),
            "creator": ("merchant",),
        },
        "scope_types": {
            "epidemic": "epidemic",
            "epidemic_scope": "epidemic",
            "merchant": "character",
            "flower_species": "flag",
            "owner": "character",
            "creator": "character",
            "random_quality_bonus": "value",
            "quality": "value",
            "wealth": "value",
            "location": "province",
            "newly_created_artifact": "artifact",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "epidemic",
            "epidemic_scope",
            "merchant",
            "flower_species",
            "owner",
            "creator",
            "random_quality_bonus",
            "quality",
            "wealth",
            "location",
            "newly_created_artifact",
        ),),
        "saved_scope_count": 11,
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (1, 2, 3),
        "selected_option_number": 4,
        "selected_native_option_index": 3,
        "max_occurrences": 1,
    },
    "learn_language_outcome.1001": {
        # CK3 1.19.0.6 response after another character successfully learns
        # the player's language. Both routes alter mutual opinion/progress;
        # native 0 creates positive respect/friend progress, while native 1
        # creates insult/rival progress plus player prestige. Neither starts
        # a follow-up event, so take the non-hostile positive response after
        # binding the completed scheme, dynamic owner and played target.
        "date_raw": 53257296,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "target": 32904,
        },
        "unique_character_scope_excludes": {
            "owner": (32904,),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
        },
        "boolean_scopes": ("scheme_successful",),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "scheme_successful",
        ),),
        "saved_scope_count": 5,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "hostile_scheme_discovery.2001": {
        # CK3 1.19.0.6 notification that a hostile scheme at another
        # character in the player's court has gained a discovery breach.
        # The sole authored option exposes that already-discovered scheme and
        # notifies its dynamic owner; there is no acknowledgement-only or
        # alternate route. Bind the source-authored scheme/owner/target/
        # spymaster frame, the generic artifact slot and discovery value
        # before selecting that required route. The dynamic characters must
        # remain distinct non-player parties in this observed lineage.
        "date_raw": 53216088,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "owner": (32904,),
            "target": (32904,),
            "spymaster": (32904,),
        },
        "character_scope_differs_from": {
            "owner": ("target", "spymaster"),
            "target": ("owner", "spymaster"),
            "spymaster": ("owner", "target"),
        },
        "scope_types": {
            "scheme": "scheme",
            "owner": "character",
            "artifact": "artifact",
            "target": "character",
            "spymaster": "character",
            "discovery_chance": "value",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "scheme",
            "owner",
            "artifact",
            "target",
            "spymaster",
            "discovery_chance",
        ),),
        "saved_scope_count": 6,
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.1001": {
        # CK3 1.19.0.6 administrative-eunuch story opener. Its immediate
        # block has already employed and upgraded the dynamic eunuch and
        # granted the starting influence bonus before the modal is shown.
        # Native option 0 additionally replaces/grants the chief-eunuch court
        # position and changes opinion; native option 1 has no effect. Bind
        # the generated story lineage and choose the terminal no-op route so
        # this incidental story does not mutate the manager's court roster.
        "date_raw": 53219664,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
        },
        "character_scope_matches_any": {
            "candidate": ("eunuch",),
        },
        "scope_types": {
            "eunuch": "character",
            "origin": "landed_title",
            "story": "story",
            "liege": "character",
            "candidate": "character",
            "modifier_type": "flag",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "eunuch",
            "origin",
            "story",
            "liege",
            "candidate",
            "modifier_type",
        ),),
        "saved_scope_count": 6,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.2050": {
        # CK3 1.19.0.6 eunuch-story boon proposal. The immediate block has
        # already selected the boon and any associated target. Option 1
        # applies that external boon and upgrades the story; option 2 only
        # applies the authored story downgrade/stress result. Bind the exact
        # R295 no-target frame and the source-authored target branch shapes,
        # then choose option 2 so the incidental story cannot mutate taxes,
        # succession, hooks or imprisonment state.
        "date_raw": 53245848,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "boon_victim": (32904,),
            "boon_target": (32904,),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "eunuch_boon": "flag",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "boon_faction": "faction",
            "boon_victim": "character",
            "boon_title": "landed_title",
            "boon_target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": tuple(
            names + boon_branch
            for names in _optional_scope_name_sets(
                (
                    "story",
                    "emperor",
                    "eunuch",
                    "admin_title",
                    "eunuch_boon",
                ),
                ("protege", "student", "rival"),
            )
            for boon_branch in (
                (),
                ("boon_victim",),
                ("boon_faction", "boon_victim"),
                ("boon_title", "boon_victim", "boon_target"),
            )
        ),
        "saved_scope_counts": (5, 6, 7, 8, 9, 10, 11),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2051": {
        # CK3 1.19.0.6 eunuch-story secret proposal. The immediate block may
        # already reveal the selected secret to the eunuch. Native option 0
        # also reveals it to the player, upgrades the eunuch story and harms
        # the dynamic owner's opinion. Native option 1 does not reveal the
        # secret to the player or start a follow-up event; it only applies the
        # authored downgrade/opinion/stress result. The native immediate block
        # saves secret_target only when the selected secret has one. The
        # shared story frame independently carries protege/student/rival when
        # those roles exist. Bind their finite optional envelope before
        # choosing that narrower route.
        "date_raw": 53223312,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "secret_owner": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "secret_target": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("secret_owner",),
            "secret_owner": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "secret": "secret",
            "secret_owner": "character",
        },
        "optional_scope_types": {
            "secret_target": "character",
            "protege": "character",
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "secret",
                "secret_owner",
            ),
            ("protege", "student", "rival", "secret_target"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2052": {
        # CK3 1.19.0.6 hostile-scheme proposal. Native option 0 exposes the
        # selected scheme, upgrades the eunuch story and upsets its owner.
        # Native option 1 leaves the hostile scheme untouched and applies only
        # the authored story downgrade/opinion/stress result. Choose that
        # narrower terminal route after binding the exact combinations of the
        # story's optional protege/student/rival roles and the scheme's
        # optional defender target.
        # Prove the owner is neither player nor eunuch, and any target is also
        # neither player nor eunuch, before selecting it. The event has no
        # cooldown or one-shot flag and remains eligible while the story and
        # a qualifying hostile scheme both exist, so validate every delivery
        # independently inside the bounded product observation window.
        "date_raw": 53236512,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "scheme_owner": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "rival": (32904,),
            "scheme_target": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("scheme_owner",),
            "scheme_owner": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "scheme_target": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "scheme": "scheme",
            "scheme_owner": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "scheme_target": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "scheme",
                "scheme_owner",
            ),
            ("protege", "student", "rival", "scheme_target"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2060": {
        # CK3 1.19.0.6 court-position demand from the story eunuch. Native
        # option 0 assigns the generated position and can remove its existing
        # holder. Native option 1 refuses the demand and applies only the
        # authored story downgrade, opinion and stress result. The shared
        # story effect independently carries protege/student/rival when they
        # exist, while the position generator independently saves old_holder.
        # Bind the finite optional envelope and choose the refusing route.
        "date_raw": 53225016,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
        },
        "character_scope_matches_any": {
            "candidate": ("eunuch",),
            "eunuch": ("candidate",),
        },
        "optional_character_scope_differs_from": {
            "old_holder": ("candidate",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "candidate": "character",
            "liege": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "old_holder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "candidate",
                "liege",
            ),
            ("protege", "student", "rival", "old_holder"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2061": {
        # CK3 1.19.0.6 family court-position demand. The immediate block moves
        # a dynamic close family member to the player's court and runs the
        # same position generator as .2060. Native option 0 appoints that
        # person and can remove an old holder. Native option 1 refuses, then
        # returns the person to the eunuch's house head or the pool. Bind the
        # exact family/candidate alias and finite shared-story envelope before
        # taking that narrower refusal route.
        "date_raw": 53239872,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "positioner": (32904,),
        },
        "character_scope_matches_any": {
            "candidate": ("positioner",),
            "positioner": ("candidate",),
        },
        "character_scope_differs_from": {
            "eunuch": ("positioner",),
            "positioner": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "old_holder": ("candidate",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "positioner": "character",
            "candidate": "character",
            "liege": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "old_holder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "positioner",
                "candidate",
                "liege",
            ),
            ("protege", "student", "rival", "old_holder"),
        ),
        "saved_scope_counts": (7, 8, 9, 10, 11),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2040": {
        # CK3 1.19.0.6 eunuch council-seat demand. The immediate block has
        # already bound the player as petition liege, the eunuch as petition
        # vassal and, only when the selected seat is occupied, its incumbent
        # as second_party. Native option 0 fires that incumbent, installs and
        # protects the eunuch, and upgrades the story. Native option 1 keeps
        # the council roster intact and only applies the authored downgrade,
        # opinion and stress. Bind the finite shared-story/incumbent envelope
        # before taking the narrower refusal route.
        "date_raw": 53258328,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "petition_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "petition_vassal": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "second_party": (32904,),
        },
        "character_scope_matches_any": {
            "eunuch": ("petition_vassal",),
            "petition_vassal": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "second_party": ("eunuch", "petition_vassal"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "petition_liege": "character",
            "petition_vassal": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "second_party": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "petition_liege",
                "petition_vassal",
            ),
            ("protege", "student", "rival", "second_party"),
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2041": {
        # CK3 1.19.0.6 eunuch-family council-seat petition. The immediate
        # block has already selected/recruited the family candidate and saved
        # both the candidate and any incumbent councillor. Native option 0
        # fires the incumbent, assigns the family candidate, blocks firing
        # them and upgrades the eunuch story. Native option 1 leaves the
        # council roster intact and applies only the authored downgrade plus
        # opinion/stress. Bind the candidate alias and incumbent before taking
        # that narrower refusal route. Vanilla applies a five-year event
        # cooldown rather than a campaign-global one-shot gate, so validate
        # every occurrence inside the product observation window.
        "date_raw": 53239224,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
            "petition_liege": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "councillor": (32904,),
            "petition_vassal": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "protege": (32904,),
            "student": (32904,),
            "rival": (32904,),
            "second_party": (32904,),
        },
        "character_scope_matches_any": {
            "councillor": ("petition_vassal",),
            "petition_vassal": ("councillor",),
        },
        "character_scope_differs_from": {
            "councillor": ("eunuch",),
            "petition_vassal": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "second_party": ("councillor", "petition_vassal"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "petition_liege": "character",
            "councillor": "character",
            "petition_vassal": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "second_party": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "petition_liege",
                "councillor",
                "petition_vassal",
            ),
            ("protege", "student", "rival", "second_party"),
        ),
        "saved_scope_counts": (7, 8, 9, 10, 11),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.2021": {
        # CK3 1.19.0.6 eunuch-family governorship request. Native option 0
        # transfers a title or changes its appointment investment, mutates
        # the title heir's opinion and adds a five-year family-boon flag.
        # Native option 1 performs none of those roster/title changes and has
        # no follow-up event; it only applies the story downgrade plus
        # opinion/stress. Bind the selected family member, title and explicit
        # non-root heir before taking that narrower refusal route.
        "date_raw": 53227128,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "governor": (32904,),
            "title_heir": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("governor", "title_heir"),
            "governor": ("eunuch", "title_heir"),
            "title_heir": ("eunuch", "governor"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "governor": "character",
            "title": "landed_title",
            "title_heir": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "story",
            "emperor",
            "eunuch",
            "admin_title",
            "governor",
            "title",
            "title_heir",
        ),),
        "saved_scope_count": 7,
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 2,
        "selected_native_option_index": 1,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.3010": {
        # CK3 1.19.0.6 eunuch-rival story node. The immediate block creates
        # or recruits the dynamic rival, stores it on the story and installs
        # the rivalry before the modal opens. Its sole option contains only
        # show_as_tooltip for that already-applied relation. Bind the complete
        # source-authored frame before acknowledging it. The origin helper
        # chooses either a neighboring top-liege realm owner or root as its
        # origin_liege; only its character type is visible through this bridge.
        # The shared story frame can independently retain protege/student.
        "date_raw": 53229168,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("rival",),
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "origin_liege": "character",
            "origin": "landed_title",
            "rival": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "origin_liege",
                "origin",
                "rival",
            ),
            ("protege", "student"),
        ),
        "saved_scope_counts": (7, 8, 9),
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.3001": {
        # CK3 1.19.0.6 eunuch-student node. Before the modal opens, the
        # immediate block has already selected/created and recruited the
        # student, installed the mentor relation, granted two skill points and
        # stored the student on the story. The sole authored option is empty.
        # The origin helper runs only when a new student must be created. In
        # that branch origin_liege is either the eunuch-scope fallback or a
        # dynamic neighboring top-liege owner, and origin accompanies it.
        # Bind the exact create/existing-student frames, then acknowledge the
        # already-applied result.
        "date_raw": 53243184,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "student": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "rival": (32904,),
            "origin_liege": (32904,),
        },
        "character_scope_differs_from": {
            "student": ("eunuch",),
        },
        "optional_character_scope_differs_from": {
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "student": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "rival": "character",
            "origin_liege": "character",
            "origin": "landed_title",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": tuple(
            names + origin_names
            for names in _optional_scope_name_sets(
                (
                    "story",
                    "emperor",
                    "eunuch",
                    "admin_title",
                    "student",
                ),
                ("protege", "rival"),
            )
            for origin_names in ((), ("origin_liege", "origin"))
        ),
        "saved_scope_counts": (5, 6, 7, 8, 9),
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.5010": {
        # CK3 1.19.0.6 upset-family node. Its immediate block has already
        # selected a dynamic family rival, installed the eunuch rivalry and
        # stored that character in the story's upset-courtiers list. Native
        # option 0 adds only authored opinion/stress; native option 1 also
        # downgrades the eunuch story. Choose option 0 to avoid that extra
        # durable story mutation after binding both non-player parties.
        "date_raw": 53230152,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("rival",),
            "rival": ("eunuch",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "rival": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            ("story", "emperor", "eunuch", "admin_title", "rival"),
            ("protege", "student"),
        ),
        "saved_scope_counts": (5, 6, 7),
        "option_count": 2,
        "native_option_indices": (0, 1),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.4000": {
        # CK3 1.19.0.6 spouse-accusation node. In the observed source shape,
        # native option 1 is hidden because the player does not already know a
        # qualifying lover secret, leaving native options 0 and 2 rendered.
        # Native option 2 imprisons both the spouse and alleged cuckolder and
        # adds tyranny. Choose native option 0's intrigue investigation: it may
        # reveal the actual secret (or report innocence/failure), but avoids
        # the unconditional double imprisonment and tyranny mutation. Bind the
        # complete seven-scope frame and the authored hidden-option gap first.
        "date_raw": 53232552,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "rival": (32904,),
            "spouse": (32904,),
            "cuckolder": (32904,),
        },
        "character_scope_differs_from": {
            "eunuch": ("spouse", "cuckolder"),
            "spouse": ("eunuch", "cuckolder"),
            "cuckolder": ("eunuch", "spouse"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "rival": "character",
            "spouse": "character",
            "cuckolder": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": ((
            "story",
            "emperor",
            "eunuch",
            "admin_title",
            "rival",
            "spouse",
            "cuckolder",
        ),),
        "saved_scope_count": 7,
        "option_count": 2,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_story_cycle_admin_eunuch.4010": {
        # CK3 1.19.0.6 seduction/murder-plot node. Its immediate block has
        # already selected the spouse and eunuch-family seducer and may already
        # have installed their lover relation or placed them in a murder
        # scheme. Native option 0 runs an intrigue duel, while native option 1
        # imprisons all three characters and adds major tyranny. Native option
        # 2 only applies the authored prestige/stress cost. Bind both immediate
        # had-sex aliases, the generated memory/secret and the full story frame
        # before taking that narrow terminal route.
        "date_raw": 53243328,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "spouse": (32904,),
            "seducer": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "protege": (32904,),
            "student": (32904,),
            "rival": (32904,),
            "had_sex_root_character": (32904,),
            "had_sex_with_effect_partner": (32904,),
        },
        "optional_character_scope_matches_any": {
            "had_sex_root_character": ("seducer",),
            "had_sex_with_effect_partner": ("spouse",),
        },
        "character_scope_differs_from": {
            "eunuch": ("spouse", "seducer"),
            "spouse": ("eunuch", "seducer"),
            "seducer": ("eunuch", "spouse"),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "spouse": "character",
            "seducer": "character",
        },
        "optional_scope_types": {
            "protege": "character",
            "student": "character",
            "rival": "character",
            "had_sex_root_character": "character",
            "had_sex_with_effect_partner": "character",
            "new_memory": "character_memory",
            "secret": "secret",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": tuple(
            names + random_branch
            for names in _optional_scope_name_sets(
                (
                    "story",
                    "emperor",
                    "eunuch",
                    "admin_title",
                    "spouse",
                    "seducer",
                ),
                ("protege", "student", "rival"),
            )
            for random_branch in (
                (),
                (
                    "had_sex_root_character",
                    "had_sex_with_effect_partner",
                    "new_memory",
                    "secret",
                ),
            )
        ),
        "saved_scope_counts": (6, 7, 8, 9, 10, 11, 12, 13),
        "option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "ep3_story_cycle_admin_eunuch.5020": {
        # CK3 1.19.0.6 puppet-heir node. The immediate block has already made
        # the selected close-family puppet a friend of the eunuch and stored
        # it on the story. The sole option then grants the ten-year puppet
        # modifier and increases that character's appointment investment.
        # There is no decline route, so acknowledge only the exact source-
        # authored frame while proving the puppet is not the current heir.
        "date_raw": 53235120,
        "date_policy": "product-observation-window",
        "root_character_id": 32904,
        "character_scopes": {
            "emperor": 32904,
        },
        "unique_character_scope_excludes": {
            "eunuch": (32904,),
            "current_heir": (32904,),
            "puppet": (32904,),
        },
        "optional_unique_character_scope_excludes": {
            "rival": (32904,),
        },
        "character_scope_differs_from": {
            "current_heir": ("puppet",),
            "puppet": ("current_heir",),
        },
        "scope_types": {
            "story": "story",
            "emperor": "character",
            "eunuch": "character",
            "admin_title": "landed_title",
            "current_heir": "character",
            "puppet": "character",
        },
        "optional_scope_types": {
            "student": "character",
            "rival": "character",
        },
        "boolean_scopes": (),
        "saved_scope_name_sets": _optional_scope_name_sets(
            (
                "story",
                "emperor",
                "eunuch",
                "admin_title",
                "current_heir",
                "puppet",
            ),
            ("student", "rival"),
        ),
        "saved_scope_counts": (6, 7, 8),
        "option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "max_occurrences": 1,
    },
    "ep3_interactions_events.0630": {
        # Vanilla governor-removal letter with one option. IMPORTANT: that
        # option executes governor_resignation_title_transfer_effect; it is
        # not a no-op acknowledgement of a previously completed title change.
        # Selecting it removes the played manager's governor position and
        # invalidates the stable manager/direct-vassal roster required by this
        # acceptance scenario.  Recognize the exact frame, preserve it paused,
        # and classify the scenario as invalid instead of mutating gameplay or
        # reporting a product RED.
        "handling_policy": "scenario-invalidating-fail-closed",
        "scenario_invalidation_reason_code": (
            "governor_resignation_title_transfer_breaks_manager_roster"
        ),
        "scenario_invalidation_reason": (
            "the event's only enabled option executes "
            "governor_resignation_title_transfer_effect and removes the "
            "played manager's governor position/direct-vassal roster"
        ),
        "invalidated_precondition": (
            "stable_player_manager_governor_position_and_direct_vassal_roster"
        ),
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
            (
                "title",
                "previous_holder",
                "new_holder",
                "transfer_type",
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
        "character_scopes": {},
        # The event immediate reads root.liege at delivery time and chooses a
        # current councillor from that liege.  Both character IDs therefore
        # legitimately change as the seed timeline advances; the stable
        # source contract is two distinct non-player Character roles.
        "unique_character_scope_excludes": {
            "tax_official": (29037,),
            "tax_liege": (29037,),
        },
        "character_scope_differs_from": {
            "tax_official": ("tax_liege",),
            "tax_liege": ("tax_official",),
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
    "zg361.30": {
        # Player-liege value-track card authored three days after annual
        # review publication whenever that cycle contains a wild-dog or
        # rabbit row.  Option 2 changes prestige/merit, starts PIP state and
        # can force title holders to step down.  Option 1 is the bounded
        # continuation: it only applies the authored merciful-opinion result
        # to current-cycle rabbit rows, leaving promotion-source state alone.
        # R116 observed this exact two-option frame at D+411 while Central was
        # active.  Bind the two event-local count values but permit inherited
        # review/PIP call-stack scopes, which the event does not consume.
        "date_raw": 53156880,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {
            "zg361_n_dog": "value",
            "zg361_n_rabbit": "value",
        },
        "boolean_scopes": (),
        "option_count": 2,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361.40": {
        # Product Jingcha mandate at D+161 and on later exact yearly pulses
        # inside the finite product observation window.  The legal default opens the
        # activity planner and schedules its hidden compliance deadline 300
        # days later.  Refusal would write manager-governance facts and a
        # next-review KPI penalty, so it is not neutral for this capture
        # lineage.  R59 observed the second delivery exactly 8,760 hours
        # after the first, matching the yearly playable pulse source.
        "date_raw": (53150880, 53159640),
        "date_policy": "yearly-pulse-in-observation-window",
        "date_raw_anchor": 53150880,
        "date_period_hours": 8760,
        # A two-cycle 1,100-day window contains the exact D+161, D+526 and
        # D+891 pulses.  No fourth pulse fits before the absolute deadline.
        "max_occurrences": 3,
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
        # single option has no effect. Bind all consumed ticket/oversight/watch
        # and publication-notice value types, and require their owner aliases
        # to refer to one non-player manager. The first observed cycle retained
        # the outer bank tuple after .200/.201 had expired; a later cycle
        # retained the completed self/shadow ticket names instead, without the
        # bank tuple. Those inherited names are not consumed by .126, so bind
        # both complete observed name sets without promoting either one into
        # the event's semantic ABI.
        "date_raw": 53155368,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_b1_local_publish_notice_subject": 29037,
        },
        "unique_character_scope_excludes": {
            name: (29037,)
            for name in (
                "zg361_b1_ticket_owner",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_pending_watch_owner",
                "zg361_b1_local_publish_notice_owner",
            )
        },
        "character_scope_matches_any": {
            name: ("zg361_b1_local_publish_notice_owner",)
            for name in (
                "zg361_b1_ticket_owner",
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
        "saved_scope_name_sets": (
            (
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
                "zg361_b1_pending_watch_owner",
                "zg361_b1_pending_watch_cycle",
                "zg361_b1_pending_watch_case",
                "zg361_b1_pending_watch_state",
                "zg361_b1_local_publish_notice_owner",
                "zg361_b1_local_publish_notice_subject",
                "zg361_b1_local_publish_notice_cycle",
                "zg361_b1_local_publish_notice_case",
                "zg361_b1_local_publish_notice_revision",
            ),
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
            ),
        ),
        "boolean_scopes": (),
        "option_count": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361.50": {
        # Player-only 3.25 result notice. Option 1 acknowledges the immutable
        # result and executes the shared idempotent delivery settlement. Bind
        # the prompt tuple and values consumed by this window. The first cycle
        # inherited an outer bank tuple; the later cycle inherited completed
        # self/shadow ticket names instead. Preserve both complete observed
        # name sets without treating either unrelated payload as part of this
        # event's semantic ABI.
        "date_raw": 53156952,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "zg361_notice_prompt_subject": 29037,
        },
        "unique_character_scope_excludes": {
            name: (29037,)
            for name in (
                "zg361_b1_ticket_owner",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_pending_continue_owner",
                "zg361_b1_pending_continue_subject",
                "zg361_b1_reopen_ticket_owner",
                "zg361_b1_reopen_ticket_subject",
                "zg361_notice_prompt_owner",
                "zg361_reviewing_superior",
            )
        },
        "character_scope_matches_any": {
            name: ("zg361_notice_prompt_owner",)
            for name in (
                "zg361_b1_ticket_owner",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_pending_continue_owner",
                "zg361_b1_reopen_ticket_owner",
                "zg361_reviewing_superior",
            )
        },
        "scope_types": {
            name: "value"
            for name in (
                "zg361_notice_prompt_cycle",
                "zg361_notice_prompt_case",
                "zg361_notice_prompt_state",
                "zg361_notice_kpi",
                "zg361_notice_rank",
                "zg361_notice_cohort",
                "zg361_notice_absolute_grade",
            )
        },
        "saved_scope_name_sets": (
            (
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
                "zg361_b1_pending_continue_owner",
                "zg361_b1_pending_continue_subject",
                "zg361_b1_pending_continue_cycle",
                "zg361_b1_pending_continue_case",
                "zg361_b1_pending_continue_state",
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
                "zg361_notice_prompt_owner",
                "zg361_notice_prompt_subject",
                "zg361_notice_prompt_cycle",
                "zg361_notice_prompt_case",
                "zg361_notice_prompt_state",
                "zg361_reviewing_superior",
                "zg361_notice_kpi",
                "zg361_notice_rank",
                "zg361_notice_cohort",
                "zg361_notice_absolute_grade",
            ),
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
                "zg361_b1_shadow_ticket_owner",
                "zg361_b1_shadow_ticket_subject",
                "zg361_b1_shadow_ticket_cycle",
                "zg361_b1_shadow_ticket_case",
                "zg361_b1_shadow_ticket_state",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_oversight_ticket_cycle",
                "zg361_b1_oversight_ticket_case",
                "zg361_b1_oversight_ticket_state",
                "zg361_b1_pending_continue_owner",
                "zg361_b1_pending_continue_subject",
                "zg361_b1_pending_continue_cycle",
                "zg361_b1_pending_continue_case",
                "zg361_b1_pending_continue_state",
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
                "zg361_notice_prompt_owner",
                "zg361_notice_prompt_subject",
                "zg361_notice_prompt_cycle",
                "zg361_notice_prompt_case",
                "zg361_notice_prompt_state",
                "zg361_reviewing_superior",
                "zg361_notice_kpi",
                "zg361_notice_rank",
                "zg361_notice_cohort",
                "zg361_notice_absolute_grade",
            ),
        ),
        "boolean_scopes": (),
        "option_count": 3,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361.4": {
        # Player-only reaction after the 3.25 notice. Option 1 changes only the
        # played character's stress and does not open an appeal or write a
        # next-cycle stance. The window consumes no saved scope, so bind only
        # its exact inherited seed shapes instead of assigning semantic meaning
        # to the older B1/result-notice payloads. The recurring window replaces
        # the first cycle's bank tuple with completed self/shadow ticket names.
        "date_raw": 53156976,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "saved_scope_name_sets": (
            (
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
                "zg361_b1_pending_continue_owner",
                "zg361_b1_pending_continue_subject",
                "zg361_b1_pending_continue_cycle",
                "zg361_b1_pending_continue_case",
                "zg361_b1_pending_continue_state",
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
                "zg361_notice_prompt_owner",
                "zg361_notice_prompt_subject",
                "zg361_notice_prompt_cycle",
                "zg361_notice_prompt_case",
                "zg361_notice_prompt_state",
                "zg361_reviewing_superior",
                "zg361_notice_kpi",
                "zg361_notice_rank",
                "zg361_notice_cohort",
                "zg361_notice_absolute_grade",
                "zg361_notice_deadline_owner",
                "zg361_notice_deadline_subject",
                "zg361_notice_deadline_cycle",
                "zg361_notice_deadline_case",
                "zg361_notice_deadline_state",
                "zg361_result_kpi",
                "zg361_result_rank",
                "zg361_result_cohort_n",
            ),
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
                "zg361_b1_shadow_ticket_owner",
                "zg361_b1_shadow_ticket_subject",
                "zg361_b1_shadow_ticket_cycle",
                "zg361_b1_shadow_ticket_case",
                "zg361_b1_shadow_ticket_state",
                "zg361_b1_oversight_ticket_owner",
                "zg361_b1_oversight_ticket_cycle",
                "zg361_b1_oversight_ticket_case",
                "zg361_b1_oversight_ticket_state",
                "zg361_b1_pending_continue_owner",
                "zg361_b1_pending_continue_subject",
                "zg361_b1_pending_continue_cycle",
                "zg361_b1_pending_continue_case",
                "zg361_b1_pending_continue_state",
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
                "zg361_notice_prompt_owner",
                "zg361_notice_prompt_subject",
                "zg361_notice_prompt_cycle",
                "zg361_notice_prompt_case",
                "zg361_notice_prompt_state",
                "zg361_reviewing_superior",
                "zg361_notice_kpi",
                "zg361_notice_rank",
                "zg361_notice_cohort",
                "zg361_notice_absolute_grade",
                "zg361_notice_deadline_owner",
                "zg361_notice_deadline_subject",
                "zg361_notice_deadline_cycle",
                "zg361_notice_deadline_case",
                "zg361_notice_deadline_state",
                "zg361_result_kpi",
                "zg361_result_rank",
                "zg361_result_cohort_n",
            ),
        ),
        "boolean_scopes": (),
        "option_count": 4,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
    },
    "zg361pp.9100": {
        # R108's player portfolio-mode card precedes the PP numbered windows.
        # The selected mode is stored on the player and the event consumes no
        # saved scopes; inherited B1/Central scopes are therefore irrelevant.
        # This focused source-capture entry must select route D (itemized): its
        # immutable downstream contract begins at visible zg361pp.146 option 1
        # and captures paused zg361pp.147.  Routes A-C intentionally batch
        # both source windows, so selecting them makes that checkpoint
        # unreachable even though the product is behaving correctly.
        "date_raw": 53169192,
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "option_count": 4,
        "selected_option_number": 4,
        "selected_native_option_index": 3,
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
        # CK3 always reports all three authored slots, but the rendered set is
        # resource-dependent. R92 observed only the always-on defer route
        # (native slot 2); R107 had enough treasury/gold and exposed all three
        # routes. Preserve both exact projections. Prefer the source-reviewed
        # funded matrix route when available, otherwise use defer.
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
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "option_variants": (
            {
                "option_count": 3,
                "native_option_indices": (0, 1, 2),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "option_count": 1,
                "native_option_indices": (2,),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        ),
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
    "zg361m.2": {
        # Second player-facing mechanism policy card. Like .1, all branches
        # intentionally write the organization ledger; option A is the
        # reference-charter route and highest-base-weight authored choice.
        # The card consumes no saved scopes, so inherited B1 names are not a
        # semantic dependency and are deliberately left unconstrained.
        "date_raw": (53168304,),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {},
        "boolean_scopes": (),
        "option_count": 3,
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
    "sway_ongoing.5011": {
        # Vanilla ongoing-sway visit opening. Option 1 starts a multi-event
        # delayed exploration chain; option 2 only grants a minor stress loss
        # to the player and ends this branch. Bind the exact live scheme,
        # owner, target, artifact and target-capital frame, then choose the
        # bounded no-follow-up path so unrelated sway gameplay cannot consume
        # the promotion observation window.
        "date_raw": 53149200,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
            "capital": "province",
        },
        "boolean_scopes": (),
        "saved_scope_count": 5,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
    },
    "sway_outcome.1001": {
        # Vanilla successful-sway outcome reached by the same exact scheme.
        # Option 1 starts a diplomacy duel with random prestige and opinion
        # results; option 2 deterministically applies the smaller opinion
        # gain (plus any authored conditional piety) and ends the scheme.
        # Bind the live owner/target and boolean success marker so this does
        # not become a generic handler for unrelated outcome windows.
        "date_raw": 53153952,
        "date_raw_range": (53147016, 53160216),
        "date_policy": "product-observation-window",
        "root_character_id": 29037,
        "character_scopes": {
            "owner": 29037,
            "target": 27051,
        },
        "scope_types": {
            "scheme": "scheme",
            "artifact": "artifact",
        },
        "boolean_scopes": ("scheme_successful",),
        "saved_scope_count": 5,
        "option_count": 2,
        "selected_option_number": 2,
        "selected_native_option_index": 1,
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
    "tgp_interaction_event.0030": {
        # Vanilla elder-break notification. The disciple/elder relationship
        # changes in immediate before the letter is rendered; its sole option
        # is empty. Bind the R103 interaction payload, including weak generic
        # interaction slots, the old/new elder identities and the authored
        # actor/new-disciple alias before acknowledging it.
        "date_raw": 53177256,
        "root_character_id": 29037,
        "character_scopes": {
            "recipient": 29037,
            "old_elder": 29037,
        },
        "unique_character_scope_excludes": {
            "actor": (29037,),
            "new_disciple": (29037,),
            "new_elder": (29037,),
        },
        "character_scope_matches_any": {
            "actor": ("new_disciple",),
            "new_disciple": ("actor",),
        },
        "character_scope_differs_from": {
            "actor": ("new_elder",),
            "new_elder": ("actor",),
        },
        # R103 exposed the generic interaction payload.  R108 reached the
        # same empty acknowledgement through a dynastic-cycle activity and
        # exposed the activity candidates instead.  Bind both exact name
        # sets while retaining the shared actor/elder identity constraints.
        "saved_scope_name_sets": (
            (
                "actor",
                "recipient",
                "secondary_actor",
                "secondary_recipient",
                "intermediary",
                "prestige",
                "gift",
                "gift_significant",
                "offer_hook",
                "offer_hook_strong",
                "influence",
                "piety",
                "hook",
                "actors_movement",
                "new_disciple",
                "old_elder",
                "new_elder",
            ),
            (
                "activity",
                "host",
                "province",
                "elder_candidate",
                "rival_candidate",
                "my_movement",
                "new_disciple",
                "old_elder",
                "new_elder",
                "actor",
                "recipient",
            ),
        ),
        "scope_types": {},
        "boolean_scopes": (),
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
        # The event source writes scheme_successful whenever this branch
        # opens, while scheme_discovered is conditional on the live scheme
        # outcome. R102 observed both flags; R103 observed only success.
        "boolean_scopes": (),
        "boolean_scope_name_sets": (
            ("scheme_successful",),
            ("scheme_discovered", "scheme_successful"),
        ),
        "saved_scope_name_sets": (
            (
                "scheme",
                "owner",
                "artifact",
                "target",
                "follow_up_event",
                "discovery_chance",
                "scheme_successful",
            ),
            (
                "scheme",
                "owner",
                "artifact",
                "target",
                "follow_up_event",
                "discovery_chance",
                "scheme_discovered",
                "scheme_successful",
            ),
        ),
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
KNOWN_TIMELINE_INTERRUPTS.update(CREDIT_PROJECT_PORTFOLIO_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CREDIT_PROJECT_RESOURCE_RACE_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CREDIT_PROJECT_REPORTING_POLICY_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CREDIT_PROJECT_MATRIX_HANDOFF_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CREDIT_PROJECT_GOVERNANCE_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(
    CREDIT_PROJECT_STOP_LOSS_POSTMORTEM_TIMELINE_CONTRACTS
)
KNOWN_TIMELINE_INTERRUPTS.update(
    PHASE3_METRICS_DELIVERY_AA_TIMELINE_CONTRACTS
)
KNOWN_TIMELINE_INTERRUPTS.update(
    PHASE3_METRICS_DELIVERY_AG_TIMELINE_CONTRACTS
)
KNOWN_TIMELINE_INTERRUPTS.update(
    PHASE3_METRICS_DELIVERY_AJ_TIMELINE_CONTRACTS
)
KNOWN_TIMELINE_INTERRUPTS.update(VANILLA_SECRET_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(
    VANILLA_INTRIGUE_TEMPTATION_TIMELINE_CONTRACTS
)
KNOWN_TIMELINE_INTERRUPTS.update(
    VANILLA_NATURAL_DISASTER_TIMELINE_CONTRACTS
)
KNOWN_TIMELINE_INTERRUPTS.update(VANILLA_EP3_EMPEROR_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(VANILLA_SEDUCE_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(VANILLA_EP1_FLAVOR_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(PP_BARGAINING_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(PP_RECEIPT_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(PP_ACTION_ITEM_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(PP_PUBLIC_PRIVATE_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(PP_FEEDBACK_COMPLETION_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CENTRAL_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(CAREER_LEARNING_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_IMPERIAL_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_COURT_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_HEALTH_AGING_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_HEALTH_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_DEATH_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_PARENT_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_BIRTH_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_CHANCELLOR_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_DEBATE_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_TGP_PETITION_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_TGP_INTERACTION_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_TGP_MINISTRY_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_TRIBUTE_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_NICKNAME_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_SPYMASTER_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_BEFRIEND_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_ANNUAL_SUMMARY_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_ELIMINATION_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_HOLY_WAR_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_COUNCIL_CLAIM_TIMELINE_CONTRACTS)
KNOWN_TIMELINE_INTERRUPTS.update(MANAGER_TRAIT_TIMELINE_CONTRACTS)


class PromotionProductionEntryService(Protocol):
    def snapshot(self) -> dict[str, object]: ...
    def execute_step(
        self, step: str, *, expected_revision: int | None
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


class PromotionBindingError(PromotionProductionEntryError):
    """A compact, durable description of a rejected native frame binding."""

    def __init__(self, evidence: Mapping[str, object]) -> None:
        self.evidence = copy.deepcopy(dict(evidence))
        super().__init__(
            "promotion path crossed its played-owner/connection binding"
        )


class PromotionKnownInterruptContractError(PromotionProductionEntryError):
    """An input-free known-event mismatch that a new client can repair."""

    def __init__(
        self, evidence: Mapping[str, object], message: str,
    ) -> None:
        self.evidence = copy.deepcopy(dict(evidence))
        super().__init__(message)


class PromotionScenarioInvalidatingInterrupt(PromotionProductionEntryError):
    """A recognized vanilla modal whose only route invalidates the scenario."""

    def __init__(self, evidence: Mapping[str, object]) -> None:
        self.evidence = copy.deepcopy(dict(evidence))
        super().__init__(
            "promotion scenario invalidated by fail-closed interrupt "
            f"{self.evidence.get('event_definition_key')!r}: "
            f"{self.evidence.get('reason_code')!r}"
        )


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
    if step == "pause-map":
        # R244/R246 proved that speed five can publish a new revision between
        # every Python snapshot and submission indefinitely.  The exact-build
        # native pause handler fresh-reads CK3 and is idempotent; unlike an
        # event choice, it does not consume the wire expected_revision.  Use
        # that narrow primitive only after every strict, input-free retry was
        # rejected, and retain the fallback in the audit trail.
        snapshot, _ = _binding(
            service.snapshot(),
            player=player,
            connection_generation=connection_generation,
        )
        if snapshot.get("paused") is True:
            return None
        fallback_revision = int(snapshot["revision"])
        result = _accepted(
            service.execute_step(step, expected_revision=None),
            step,
        )
        rebind_audit.append({
            "step": step,
            "attempt": "native-fresh-idempotent-fallback",
            "stale_revision": fallback_revision,
            "request_submitted": True,
            "binding_mode": "exact-build-native-fresh-idempotent-pause",
            "ack_status": result.get("status"),
        })
        return result
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


def _snapshot_bridge_pid(snapshot: Mapping[str, object]) -> int | None:
    diagnostics = snapshot.get("diagnostics")
    value = diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _retained_modal_map_control(
    service: PromotionProductionEntryService,
    *,
    step: str,
    player: int,
    connection_generation: int,
    bridge_pid: int,
    event_instance_id: int,
    rebind_audit: list[dict[str, object]],
) -> dict[str, object] | None:
    """Control time while retaining one exact modal in one CK3 process."""

    if step not in {"set-speed-5", "resume-map"}:
        raise ValueError(f"unsupported retained-modal map control: {step}")
    last_error: PreSubmissionRevisionMismatchError | None = None
    for attempt in range(1, MAX_PRE_SUBMISSION_REBIND_ATTEMPTS + 1):
        snapshot, _ = _binding(
            service.snapshot(),
            player=player,
            connection_generation=connection_generation,
        )
        active_event = snapshot.get("active_event")
        actual_instance_id = (
            active_event.get("instance_id")
            if isinstance(active_event, Mapping)
            else None
        )
        if (
            _snapshot_bridge_pid(snapshot) != bridge_pid
            or actual_instance_id != event_instance_id
        ):
            raise PromotionProductionEntryError(
                "zg361.6 retain wait crossed its CK3 PID/event identity"
            )
        if step == "set-speed-5" and snapshot.get("speed") == 5:
            return None
        if step == "resume-map" and snapshot.get("paused") is not True:
            return None
        revision = int(snapshot["revision"])
        try:
            return _accepted(
                service.execute_step(step, expected_revision=revision), step
            )
        except PreSubmissionRevisionMismatchError as error:
            last_error = error
            rebind_audit.append({
                "step": step,
                "attempt": attempt,
                "stale_revision": revision,
                "error": f"{type(error).__name__}: {error}",
                "request_submitted": False,
                "retained_event_instance_id": event_instance_id,
                "tracked_ck3_pid": bridge_pid,
            })
    if last_error is None:
        raise PromotionProductionEntryError(
            "zg361.6 retain wait could not bind its modal map control"
        )
    raise last_error


def _zg361_6_retain_option_ready(query: Mapping[str, object]) -> bool:
    context = query.get("current_event_window_context")
    options_value = context.get("options") if isinstance(context, Mapping) else None
    options = options_value if isinstance(options_value, list) else []
    return any(
        isinstance(row, Mapping)
        and row.get("native_option_index") == 1
        and row.get("shown") is True
        and row.get("enabled") is True
        and row.get("fallback") is False
        and row.get("cancel") is False
        for row in options
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


def _post_interrupt_seed_is_invalid(
    observation: Mapping[str, object],
    *,
    stop_at_clean_review_boundary: bool = False,
) -> bool:
    return (
        not stop_at_clean_review_boundary
        and not any(
            observation.get(name) is True
            for name in ("b1_active", "central_active", "pp_active")
        )
        and observation.get("review_now_eligible") is not True
    )


def _activate_review_now_from_progress(
    service: PromotionProductionEntryService,
    *,
    source_progress: dict[str, object],
    source_revision: int,
    player: int,
    connection_generation: int,
    evidence: dict[str, object],
    nonce: str,
    sleeper: Callable[[float], None],
) -> None:
    action = service.activate_zhongguo_review_now_v1(
        nonce,
        source_progress,
        expected_revision=source_revision,
    )
    evidence["review_action"] = action
    # The accepted native ACK proves dispatch, not the scripted effect.  Wait
    # for the next bridge heartbeat before binding the independent paused
    # product query; otherwise it can still expose the cached pre-action GUI
    # frame, as the retained R162 session demonstrated.
    sleeper(PAUSED_PROGRESS_SETTLE_SECONDS)
    after_snapshot, _ = _binding(
        service.snapshot(),
        player=player,
        connection_generation=connection_generation,
    )
    after = service.query_zhongguo_promotion_source_progress_v1(
        f"{nonce}.after",
        expected_revision=int(after_snapshot["revision"]),
    )
    evidence["post_action_progress"] = copy.deepcopy(after)
    try:
        evidence["review_action_postcondition"] = (
            verify_review_now_independent_postcondition_v1(
                action_result=action,
                before_query_sequence=int(source_progress["query_sequence"]),
                after_result=after,
                expected_connection_generation=connection_generation,
                expected_player_character_id=player,
            )
        )
    except ValueError as error:
        raise PromotionProductionEntryError(str(error)) from error


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
        active_event = value.get("active_event")
        active_event_row = (
            {
                "event_instance_id": active_event.get("event_instance_id"),
                "event_definition_key": active_event.get("event_definition_key"),
            }
            if isinstance(active_event, Mapping)
            else None
        )
        raise PromotionBindingError(
            {
                "snapshot_id": value.get("snapshot_id"),
                "revision": revision,
                "native_revision": value.get("native_revision"),
                "date_raw": date_raw,
                "paused": value.get("paused"),
                "speed": value.get("speed"),
                "map_ready": value.get("map_ready"),
                "actual_player_character_id": actual_player,
                "expected_player_character_id": player,
                "actual_connection_generation": generation,
                "expected_connection_generation": connection_generation,
                "bridge_pid": diagnostics.get("bridge_pid"),
                "one_life_terminal": value.get("one_life_terminal"),
                "one_life_terminal_reason": value.get(
                    "one_life_terminal_reason"
                ),
                "active_event": active_event_row,
            }
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


def _manager_recovery_contract(
    contract: Mapping[str, object], *, player: int,
    event_key: str | None = None,
) -> dict[str, object]:
    """Rebind a reviewed interrupt shape to the switched human manager.

    The normal production-entry contracts freeze the original seed's exact
    character IDs because those drains are product evidence. Manager-cycle
    recovery has a narrower purpose: preserve the switched player and drain
    the already-running product cycle without claiming those incidental cards
    as acceptance evidence. It therefore retains the event/date/option/scope
    shape while replacing old-world non-root character IDs with required
    character types.
    """

    rebound = copy.deepcopy(dict(contract))
    original_root = rebound.get("root_character_id")
    rebound["root_character_id"] = player
    scope_types_value = rebound.get("scope_types")
    scope_types = (
        dict(scope_types_value)
        if isinstance(scope_types_value, Mapping)
        else {}
    )
    character_scopes_value = rebound.get("character_scopes")
    character_scopes = (
        dict(character_scopes_value)
        if isinstance(character_scopes_value, Mapping)
        else {}
    )
    rebound_character_scopes: dict[str, object] = {}
    for name, expected in character_scopes.items():
        if expected == original_root:
            rebound_character_scopes[str(name)] = player
        else:
            scope_types.setdefault(str(name), "character")
    rebound["character_scopes"] = rebound_character_scopes
    rebound["scope_types"] = scope_types

    if event_key == "zg361.40":
        # A newly switched human manager can receive the one-day Jingcha
        # mandate after the canonical seed's original annual anchor.  The
        # product still owns the exact event/root/options, but the old
        # character's calendar congruence is not the new manager's identity.
        rebound["date_policy"] = "manager-recovery-product-window"
        rebound.pop("date_raw_anchor", None)
        rebound.pop("date_period_hours", None)

    optional_scope_types_value = rebound.get("optional_scope_types")
    optional_scope_types = (
        dict(optional_scope_types_value)
        if isinstance(optional_scope_types_value, Mapping)
        else {}
    )
    optional_characters = rebound.get("optional_character_scopes")
    if isinstance(optional_characters, Mapping):
        for name in optional_characters:
            optional_scope_types.setdefault(str(name), "character")
        rebound["optional_character_scopes"] = {}
    rebound["optional_scope_types"] = optional_scope_types
    excludes_value = rebound.get("unique_character_scope_excludes")
    if isinstance(excludes_value, Mapping):
        rebound["unique_character_scope_excludes"] = {
            str(name): tuple(
                player if value == original_root else value
                for value in values
            )
            for name, values in excludes_value.items()
            if isinstance(values, tuple)
        }
    optional_excludes_value = rebound.get(
        "optional_unique_character_scope_excludes"
    )
    if isinstance(optional_excludes_value, Mapping):
        rebound["optional_unique_character_scope_excludes"] = {
            str(name): tuple(
                player if value == original_root else value
                for value in values
            )
            for name, values in optional_excludes_value.items()
            if isinstance(values, tuple)
        }
    scope_variants_value = rebound.get("scope_variants")
    if isinstance(scope_variants_value, tuple):
        rebound_variants: list[object] = []
        for variant_value in scope_variants_value:
            if not isinstance(variant_value, Mapping):
                rebound_variants.append(variant_value)
                continue
            variant = copy.deepcopy(dict(variant_value))
            variant_scope_types_value = variant.get("scope_types")
            variant_scope_types = (
                dict(variant_scope_types_value)
                if isinstance(variant_scope_types_value, Mapping)
                else {}
            )
            variant_character_scopes_value = variant.get("character_scopes")
            if isinstance(variant_character_scopes_value, Mapping):
                variant_character_scopes: dict[str, object] = {}
                for name, expected in variant_character_scopes_value.items():
                    if expected == original_root:
                        variant_character_scopes[str(name)] = player
                    else:
                        variant_scope_types.setdefault(str(name), "character")
                variant["character_scopes"] = variant_character_scopes
            variant["scope_types"] = variant_scope_types
            variant_excludes_value = variant.get(
                "unique_character_scope_excludes"
            )
            if isinstance(variant_excludes_value, Mapping):
                variant["unique_character_scope_excludes"] = {
                    str(name): tuple(
                        player if value == original_root else value
                        for value in values
                    )
                    for name, values in variant_excludes_value.items()
                    if isinstance(values, tuple)
                }
            rebound_variants.append(variant)
        rebound["scope_variants"] = tuple(rebound_variants)
    if event_key == "zg361pp.9100":
        # Recovery needs the shortest real product closure, not the itemized
        # route deliberately used by promotion-source capture.
        rebound["selected_option_number"] = 1
        rebound["selected_native_option_index"] = 0
    rebound["manager_recovery_only"] = True
    return rebound


def _manager_recovery_pp_contract(
    event_key: str, *, player: int, starting_date: int,
) -> dict[str, object] | None:
    """Return the minimal authored option shape for a PP card being drained."""

    try:
        event_number = int(event_key.removeprefix("zg361pp."))
    except ValueError:
        return None
    if 146 <= event_number <= 191:
        option_count = 3
        # Each authored route has a business/resource trigger.  CK3 projects
        # only the currently visible native slots, so recovery must accept any
        # non-empty authored-order subset and click its first visible route.
        option_variants: tuple[dict[str, object], ...] = tuple(
            {
                "option_count": len(indices),
                "native_option_indices": indices,
                "snapshot_option_counts": tuple(
                    dict.fromkeys((len(indices), option_count))
                ),
                "selected_option_number": indices[0] + 1,
                "selected_native_option_index": indices[0],
            }
            for indices in (
                (0,),
                (1,),
                (2,),
                (0, 1),
                (0, 2),
                (1, 2),
                (0, 1, 2),
            )
        )
    elif 9001 <= event_number <= 9004:
        option_count = 1
        option_variants = ()
    else:
        return None
    scope_types = (
        {"zg361_pp_completion_subject": "character"}
        if 9001 <= event_number <= 9004
        else {}
    )
    return {
        "date_raw": starting_date,
        "date_policy": "manager-recovery-product-window",
        "date_raw_range": (
            starting_date,
            starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY,
        ),
        "root_character_id": player,
        "character_scopes": {},
        "scope_types": scope_types,
        "boolean_scopes": (),
        "option_count": option_count,
        "native_option_indices": tuple(range(option_count)),
        "option_variants": option_variants,
        "max_occurrences": 1,
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "manager_recovery_only": True,
    }


def _manager_recovery_workforce_contract(
    event_key: str, *, player: int, starting_date: int,
) -> dict[str, object] | None:
    """Return the reviewed non-debt route for one visible Workforce card."""

    try:
        event_number = int(event_key.removeprefix("zg361we."))
    except ValueError:
        return None
    option_count = _MANAGER_RECOVERY_WORKFORCE_OPTION_COUNTS.get(event_number)
    if option_count is None:
        return None
    option_variants: tuple[dict[str, object], ...] = ()
    selected_option_number = 1
    selected_native_option_index = 0
    snapshot_option_counts: tuple[int, ...] | None = None
    if event_number == 264:
        # Route C is the debt fallback.  Admit only the two source-authored
        # response projections that expose A or B alongside C, and select the
        # first visible non-debt route.
        option_variants = (
            {
                "option_count": 2,
                "native_option_indices": (0, 2),
                "snapshot_option_counts": (2, 3),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "option_count": 2,
                "native_option_indices": (1, 2),
                "snapshot_option_counts": (2, 3),
                "selected_option_number": 2,
                "selected_native_option_index": 1,
            },
        )
    elif event_number in (5264, 5265, 5266):
        # Each handoff authors subject complete/refuse followed by owner
        # complete/refuse.  Exactly one pair is rendered; always take the
        # matching complete route.
        option_variants = (
            {
                "option_count": 2,
                "native_option_indices": (0, 1),
                "snapshot_option_counts": (2, 4),
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
            {
                "option_count": 2,
                "native_option_indices": (2, 3),
                "snapshot_option_counts": (2, 4),
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        )
        snapshot_option_counts = (2, 4)
    contract: dict[str, object] = {
        "date_raw": starting_date,
        "date_policy": "manager-recovery-product-window",
        "date_raw_range": (
            starting_date,
            starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY,
        ),
        "root_character_id": player,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "option_count": option_count,
        "native_option_indices": tuple(range(option_count)),
        "option_variants": option_variants,
        "max_occurrences": 3,
        "selected_option_number": selected_option_number,
        "selected_native_option_index": selected_native_option_index,
        "manager_recovery_only": True,
        "workforce_three_cycle_route": "shortest-reviewed-non-debt",
    }
    if snapshot_option_counts is not None:
        contract["snapshot_option_counts"] = snapshot_option_counts
    return contract


def _manager_recovery_authored_event_contract(
    contract: Mapping[str, object],
    *,
    player: int,
    starting_date: int,
) -> dict[str, object]:
    """Keep authored choice semantics while dropping stale checkpoint actors."""

    minimal: dict[str, object] = {
        "date_raw": starting_date,
        "date_policy": "manager-recovery-product-window",
        "date_raw_range": (
            starting_date,
            starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY,
        ),
        "root_character_id": player,
        "character_scopes": {},
        "scope_types": {},
        "boolean_scopes": (),
        "manager_recovery_only": True,
    }
    for name in (
        "option_count",
        "snapshot_option_count",
        "snapshot_option_counts",
        "native_option_indices",
        "native_option_prefix_range",
        "native_option_suffix",
        "option_variants",
        "selected_option_number",
        "selected_native_option_index",
        "selection_deferred",
        "occurrence_policy",
        "max_occurrences",
    ):
        if name in contract:
            minimal[name] = copy.deepcopy(contract[name])
    return minimal


def _resolve_timeline_interrupt_contract(
    event_key: str,
    *,
    player: int,
    starting_date: int,
    stop_at_clean_review_boundary: bool,
    continue_to_pause_target: bool = False,
) -> dict[str, object] | None:
    """Keep reviewed vanilla contracts when manager recovery is active.

    Generated ``zg361pp`` cards use the minimal manager-recovery shape even
    when a stricter capture-route contract exists.  The recovery client only
    needs their authored option count/index and must tolerate unrelated saved
    scopes introduced by later product stages.  Reviewed vanilla contracts
    still retain their exact scope and option checks.
    """

    manager_recovery = (
        stop_at_clean_review_boundary or continue_to_pause_target
    )
    contract = (
        _manager_recovery_pp_contract(
            event_key, player=player, starting_date=starting_date,
        )
        if manager_recovery
        else None
    )
    if contract is None and manager_recovery:
        contract = _manager_recovery_workforce_contract(
            event_key,
            player=player,
            starting_date=starting_date,
        )
    if contract is None:
        contract = KNOWN_TIMELINE_INTERRUPTS.get(event_key)
    if (
        contract is not None
        and manager_recovery
        and event_key.startswith(("zg361cp.", "zg361p3."))
    ):
        contract = _manager_recovery_authored_event_contract(
            contract,
            player=player,
            starting_date=starting_date,
        )
    elif contract is not None and contract.get("root_character_id") != player:
        contract = _manager_recovery_contract(
            contract, player=player, event_key=event_key,
        )
    if contract is None:
        return None
    return _timeline_contract_for_window(contract, starting_date=starting_date)


def _manager_recovery_occurrence_contract(
    event_key: str,
    contract: Mapping[str, object],
    *,
    occurrence_count: int,
) -> dict[str, object]:
    """Bind occurrence-sensitive cards to their current rendered projection.

    A route-1 compensation stage may remain pending and reopen on the next
    cadence tick; R317 demonstrated fourteen repeats of the first visible
    stage. Manager recovery does not collect portfolio evidence, so it takes
    route 3 for every exact visible stage. R318 proved that route 3 advanced
    the repeated first stage to the next authored 3/4/5 projection. Preserve
    the global authored indices and choose the last index in every reviewed
    projection, including resource-gated AF5.
    """

    bound = copy.deepcopy(dict(contract))
    if event_key != "zg361comp.1":
        return bound
    if occurrence_count < 0 or occurrence_count >= 14:
        raise ValueError("compensation occurrence is outside the 14-card portfolio")
    bound["manager_recovery_portfolio_ordinal"] = occurrence_count + 1
    variants_value = bound.get("option_variants")
    variants = variants_value if isinstance(variants_value, tuple) else ()
    route_three_variants: list[dict[str, object]] = []
    for variant_value in variants:
        variant = variant_value if isinstance(variant_value, Mapping) else {}
        indices_value = variant.get("native_option_indices")
        indices = indices_value if isinstance(indices_value, tuple) else ()
        if not indices:
            continue
        selected_native_index = int(indices[-1])
        route_three_variants.append({
            **copy.deepcopy(dict(variant)),
            "selected_option_number": selected_native_index + 1,
            "selected_native_option_index": selected_native_index,
        })
    if not route_three_variants:
        raise ValueError("compensation contract lacks reviewed option variants")
    bound["option_variants"] = tuple(route_three_variants)
    bound["selected_option_number"] = 3
    bound["selected_native_option_index"] = 2
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


def _option_contract_for_context(
    options: list[object], contract: Mapping[str, object]
) -> Mapping[str, object]:
    """Resolve an exact resource-dependent rendered-option projection."""

    variants_value = contract.get("option_variants")
    variants = variants_value if isinstance(variants_value, tuple) else ()
    if not variants:
        return contract
    actual_native_indices = tuple(
        row.get("native_option_index") if isinstance(row, Mapping) else None
        for row in options
    )
    for variant_value in variants:
        if not isinstance(variant_value, Mapping):
            continue
        expected_indices = variant_value.get("native_option_indices")
        if (
            variant_value.get("option_count") == len(options)
            and isinstance(expected_indices, tuple)
            and actual_native_indices == expected_indices
        ):
            return {**contract, **variant_value}
    return contract


def _snapshot_option_counts(contract: Mapping[str, object]) -> tuple[object, ...]:
    """Return the exact authored/rendered counts admitted by one projection."""

    values = contract.get("snapshot_option_counts")
    if isinstance(values, tuple):
        return values
    return (contract.get("snapshot_option_count", contract.get("option_count")),)


def _scope_contract_for_context(
    scopes: list[object], contract: Mapping[str, object]
) -> Mapping[str, object]:
    """Resolve a source-reviewed contract for an exact saved-scope shape."""

    variants_value = contract.get("scope_variants")
    variants = variants_value if isinstance(variants_value, tuple) else ()
    if not variants:
        return contract
    actual_names = [
        row_value.get("name")
        for row_value in scopes
        if isinstance(row_value, Mapping)
        and isinstance(row_value.get("name"), str)
    ]
    if len(actual_names) != len(scopes) or len(set(actual_names)) != len(
        actual_names
    ):
        return contract
    for variant_value in variants:
        if not isinstance(variant_value, Mapping):
            continue
        expected_names_value = variant_value.get("saved_scope_names")
        expected_names = (
            expected_names_value
            if isinstance(expected_names_value, tuple)
            else ()
        )
        if expected_names and set(actual_names) == set(expected_names):
            resolved = {**contract, **variant_value}
            resolved.pop("saved_scope_names", None)
            resolved["saved_scope_name_sets"] = (expected_names,)
            return resolved
    return contract


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
    scopes_value = context.get("saved_scopes")
    scopes = scopes_value if isinstance(scopes_value, list) else []
    effective_contract = _option_contract_for_context(
        options,
        _scope_contract_for_context(scopes, contract),
    )
    contract = effective_contract
    option_count = effective_contract["option_count"]
    snapshot_option_counts = _snapshot_option_counts(effective_contract)
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
    native_option_prefix_range = effective_contract.get(
        "native_option_prefix_range"
    )
    native_option_suffix = effective_contract.get("native_option_suffix")
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
        native_option_indices_value = effective_contract.get(
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
        in snapshot_option_counts,
        "authored_options_exact": authored_options_exact,
        "selected_option_mapping": (
            effective_contract.get("selection_deferred") is True
            or effective_contract["selected_option_number"]
            == effective_contract["selected_native_option_index"] + 1
        ),
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
    optional_excluded_scopes_value = contract.get(
        "optional_unique_character_scope_excludes", {}
    )
    optional_excluded_scopes = (
        optional_excluded_scopes_value
        if isinstance(optional_excluded_scopes_value, Mapping)
        else {}
    )
    for name, excluded_character_ids_value in optional_excluded_scopes.items():
        ids = character_ids(str(name))
        excluded_character_ids = (
            set(excluded_character_ids_value)
            if isinstance(excluded_character_ids_value, tuple)
            else set()
        )
        checks[f"scope:{name}:optional_unique_third_party"] = (
            not ids
            or (len(ids) == 1 and ids.isdisjoint(excluded_character_ids))
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
    optional_matches_any_value = contract.get(
        "optional_character_scope_matches_any", {}
    )
    optional_matches_any = (
        optional_matches_any_value
        if isinstance(optional_matches_any_value, Mapping)
        else {}
    )
    for name, candidate_names_value in optional_matches_any.items():
        candidate_names = (
            candidate_names_value
            if isinstance(candidate_names_value, tuple)
            else ()
        )
        ids = character_ids(str(name))
        checks[f"scope:{name}:optional_matches_any"] = not ids or (
            len(ids) == 1
            and any(
                ids == character_ids(str(candidate_name))
                for candidate_name in candidate_names
            )
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
    optional_differs_from_value = contract.get(
        "optional_character_scope_differs_from", {}
    )
    optional_differs_from = (
        optional_differs_from_value
        if isinstance(optional_differs_from_value, Mapping)
        else {}
    )
    for name, other_names_value in optional_differs_from.items():
        other_names = (
            other_names_value if isinstance(other_names_value, tuple) else ()
        )
        ids = character_ids(str(name))
        other_ids = [
            character_ids(str(other_name)) for other_name in other_names
        ]
        checks[f"scope:{name}:optional_differs_from"] = (
            not ids
            or (
                len(ids) == 1
                and bool(other_ids)
                and all(
                    len(values) == 1 and ids.isdisjoint(values)
                    for values in other_ids
                )
            )
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
    elif "saved_scope_counts" in contract:
        saved_scope_counts = contract["saved_scope_counts"]
        checks["saved_scope_count"] = (
            isinstance(saved_scope_counts, tuple)
            and len(scopes) in saved_scope_counts
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
        diagnostic = ""
        if "authored_options_exact" in failed:
            options_value = context.get("options")
            actual_options = options_value if isinstance(options_value, list) else []
            option_projection = [
                {
                    key: row.get(key)
                    for key in (
                        "rendered_index",
                        "native_option_index",
                        "shown",
                        "enabled",
                        "fallback",
                        "cancel",
                    )
                }
                for row in actual_options
                if isinstance(row, Mapping)
            ]
            diagnostic += (
                f"; actual_options={option_projection!r}; "
                f"expected_option_count={contract.get('option_count')!r}; "
                "expected_native_option_indices="
                f"{contract.get('native_option_indices')!r}; "
                f"allowed_option_variants={contract.get('option_variants')!r}"
            )
        if "saved_scope_names_exact" in failed:
            scopes_value = context.get("saved_scopes")
            scopes = scopes_value if isinstance(scopes_value, list) else []
            actual_scope_names = sorted(
                row.get("name")
                for row in scopes
                if isinstance(row, Mapping) and isinstance(row.get("name"), str)
            )
            expected_scope_name_sets_value = contract.get(
                "saved_scope_name_sets", ()
            )
            expected_scope_name_sets = (
                expected_scope_name_sets_value
                if isinstance(expected_scope_name_sets_value, tuple)
                else ()
            )
            diagnostic += (
                f"; actual_saved_scope_names={actual_scope_names!r}; "
                "allowed_saved_scope_name_sets="
                f"{[sorted(names) for names in expected_scope_name_sets]!r}"
            )
        raise PromotionKnownInterruptContractError(
            {
                "classification": "known-interrupt-contract-drift",
                "event_definition_key": event_key,
                "date_raw": snapshot.get("date_raw"),
                "event_instance_id": event.get("event_instance_id"),
                "failed_checks": failed,
                "identity_checks": copy.deepcopy(checks),
                "snapshot": copy.deepcopy(dict(snapshot)),
                "event": copy.deepcopy(dict(event)),
                "query": copy.deepcopy(dict(query)),
                "selection_attempted": False,
            },
            f"known promotion-timeline interrupt {event_key!r} drifted: "
            f"{failed!r}{diagnostic}",
        )

    if contract.get("handling_policy") == "scenario-invalidating-fail-closed":
        scopes_value = context.get("saved_scopes")
        scopes = scopes_value if isinstance(scopes_value, list) else []

        def one_character_id(name: str) -> int | None:
            ids = {
                character_id
                for row_value in scopes
                if isinstance(row_value, Mapping)
                and row_value.get("name") == name
                and (
                    character_id := _typed_character_id(row_value.get("scope"))
                )
                is not None
            }
            return next(iter(ids)) if len(ids) == 1 else None

        raise PromotionScenarioInvalidatingInterrupt({
            "classification": "scenario-invalidating-interrupt",
            "handling": "fail-closed-no-selection",
            "product_result": "NOT_EVALUATED",
            "product_red": False,
            "event_definition_key": event_key,
            "date_raw": snapshot.get("date_raw"),
            "event_instance_id": event.get("event_instance_id"),
            "reason_code": contract.get("scenario_invalidation_reason_code"),
            "reason": contract.get("scenario_invalidation_reason"),
            "invalidated_precondition": contract.get(
                "invalidated_precondition"
            ),
            "actor_character_id": one_character_id("actor"),
            "recipient_character_id": one_character_id("recipient"),
            "identity_checks": checks,
            "selection_attempted": False,
        })

    options_value = context.get("options")
    options = options_value if isinstance(options_value, list) else []
    effective_contract = _option_contract_for_context(options, contract)
    if effective_contract.get("selection_deferred") is True:
        raise PromotionProductionEntryError(
            f"known promotion-timeline interrupt {event_key!r} requires a "
            "deterministic option before it may be drained"
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
        in _snapshot_option_counts(effective_contract),
    }
    if not all(pre_selection_checks.values()) or selection_event is None:
        failed = sorted(
            name for name, passed in pre_selection_checks.items() if not passed
        )
        raise PromotionProductionEntryError(
            f"known promotion-timeline interrupt {event_key!r} changed before "
            f"selection: {failed!r}"
        )

    option_number = int(effective_contract["selected_option_number"])
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
        == effective_contract["selected_native_option_index"],
        "postcondition_verified": event_selection.get("postcondition_verified")
        is True,
        "old_event_instance_id": event_selection.get("old_event_instance_id")
        == selection_event["event_instance_id"],
        "selected_option_number": event_selection.get("selected_option_number")
        == option_number,
        "selected_native_option_index": event_selection.get(
            "selected_native_option_index"
        )
        == effective_contract["selected_native_option_index"],
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


def _initial_event_is_supported(
    key: str,
    *,
    player: int,
    timeline_origin_date: int,
    stop_at_clean_review_boundary: bool,
    clean_boundary_event_definition_key: str | None,
    pause_on_event_definition_key: str | None = None,
) -> bool:
    if key == pause_on_event_definition_key:
        return True
    if key == M146 or key in KNOWN_TIMELINE_INTERRUPTS:
        return True
    if not stop_at_clean_review_boundary:
        return False
    if key == clean_boundary_event_definition_key:
        return True
    return (
        _manager_recovery_pp_contract(
            key,
            player=player,
            starting_date=timeline_origin_date,
        )
        is not None
    )


def _pause_target_occurrence_index(
    event_key: str,
    *,
    pause_on_event_definition_key: str | None,
    timeline_interrupt_drains: object,
) -> int | None:
    """Return this target event's one-based occurrence in the current run."""

    if event_key != pause_on_event_definition_key:
        return None
    drains = (
        timeline_interrupt_drains
        if isinstance(timeline_interrupt_drains, list)
        else []
    )
    return 1 + sum(
        isinstance(row, Mapping)
        and row.get("event_definition_key") == event_key
        for row in drains
    )


def enter_promotion_source_checkpoint_v1(
    service: PromotionProductionEntryService,
    *,
    timeout_seconds: float = 300.0,
    poll_interval_seconds: float = 0.05,
    prefer_natural_cycle: bool = False,
    stop_at_clean_review_boundary: bool = False,
    clean_boundary_event_definition_key: str | None = None,
    pause_on_event_definition_key: str | None = None,
    pause_on_event_occurrence: int = 1,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    evidence_out: dict[str, object] | None = None,
    runtime_diagnostic_probe: Callable[[], str | None] | None = None,
) -> dict[str, object]:
    """Drive the product timeline and stop before the requested target."""
    if timeout_seconds <= 0 or poll_interval_seconds < 0:
        raise ValueError("promotion entry timing is invalid")
    if pause_on_event_definition_key is not None and not (
        isinstance(pause_on_event_definition_key, str)
        and pause_on_event_definition_key.strip()
        and not any(character.isspace() for character in pause_on_event_definition_key)
    ):
        raise ValueError("pause target must be one non-empty event key")
    if (
        isinstance(pause_on_event_occurrence, bool)
        or not isinstance(pause_on_event_occurrence, int)
        or pause_on_event_occurrence <= 0
        or (
            pause_on_event_definition_key is None
            and pause_on_event_occurrence != 1
        )
    ):
        raise ValueError("pause target occurrence must be a positive integer")
    continue_to_pause_target = (
        pause_on_event_definition_key not in (None, M147)
    )
    initial, initial_event = _binding(service.snapshot())
    player = int(initial["played_character"]["character_id"])
    generation = int(initial["diagnostics"]["connection_generation"])
    starting_date = int(initial["date_raw"])
    timeline_origin_date = PRODUCT_TIMELINE_ORIGIN_DATE_RAW
    absolute_end_date = (
        timeline_origin_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY
    )
    # The caller retains this same object even if a later interrupt raises.
    # R59/R61 lost their accumulated timeline because only success returned it.
    evidence: dict[str, object] = {} if evidence_out is None else evidence_out
    retained_timeline_interrupt_drains = copy.deepcopy(
        evidence.get("timeline_interrupt_drains")
        if isinstance(evidence.get("timeline_interrupt_drains"), list)
        else []
    )
    evidence.update({
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_production_entry",
        "result": "RED",
        "readiness": "static-ready-live-pending",
        "player_character_id": player,
        "connection_generation": generation,
        "starting_date_raw": starting_date,
        "timeline_origin_date_raw": timeline_origin_date,
        "absolute_end_date_raw": absolute_end_date,
        "advance_bound": {
            "cycle_opportunities": PRODUCT_CYCLE_OPPORTUNITIES,
            "b1_authored_days": B1_AUTHORED_ADVANCE_DAYS,
            "post_publication_observation_days": (
                POST_PUBLICATION_OBSERVATION_DAYS
            ),
            "pre_workforce_total_days": PRE_WORKFORCE_MAX_ADVANCE_DAYS,
            "endgame_target_workforce_cycles": (
                ENDGAME_TARGET_WORKFORCE_CYCLES
            ),
            "workforce_cycle_observation_days": (
                WORKFORCE_CYCLE_OBSERVATION_DAYS
            ),
            "total_days": MAX_ADVANCE_DAYS,
        },
        "paused_progress_settle_seconds": PAUSED_PROGRESS_SETTLE_SECONDS,
        "review_action": None,
        "review_action_postcondition": None,
        "prefer_natural_cycle": prefer_natural_cycle,
        "natural_cycle_wait": None,
        "m146_option1_submission": None,
        "m146_date_raw": None,
        "timeline_interrupt_drains": retained_timeline_interrupt_drains,
        "retained_timeline_interrupt_drain_count": len(
            retained_timeline_interrupt_drains
        ),
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
        "zg361_6_retain_wait": None,
        "seed_invalid": None,
        "annual_cooldown_wait": None,
        "clean_review_boundary": None,
        "pause_on_event_definition_key": pause_on_event_definition_key,
        "pause_on_event_occurrence": pause_on_event_occurrence,
    })
    if runtime_diagnostic_probe is not None:
        diagnostic = runtime_diagnostic_probe()
        if diagnostic:
            raise PromotionProductionEntryError(
                f"product runtime diagnostic: {diagnostic}"
            )
    if starting_date > absolute_end_date:
        raise PromotionProductionEntryError(
            "promotion path already exceeded its absolute "
            f"{MAX_ADVANCE_DAYS}-day product observation bound before this "
            "retained-client reconnect"
        )
    initial_clean_boundary_event = False
    if initial_event is not None:
        key, _ = _event_definition(service, initial_event, sleeper=sleeper)
        target_occurrence_index = _pause_target_occurrence_index(
            key,
            pause_on_event_definition_key=pause_on_event_definition_key,
            timeline_interrupt_drains=evidence["timeline_interrupt_drains"],
        )
        if target_occurrence_index == pause_on_event_occurrence:
            evidence["result"] = "GREEN"
            evidence["readiness"] = f"paused-real-{key}"
            evidence["target_binding"] = initial_event
            evidence["target_occurrence_index"] = target_occurrence_index
            return evidence
        if (
            key == M147
            and not stop_at_clean_review_boundary
            and not continue_to_pause_target
        ):
            evidence["result"] = "GREEN"
            evidence["readiness"] = "paused-real-zg361pp.147"
            evidence["target_binding"] = initial_event
            return evidence
        if (
            stop_at_clean_review_boundary
            and key == clean_boundary_event_definition_key
        ):
            initial_clean_boundary_event = True
        elif not _initial_event_is_supported(
            key,
            player=player,
            timeline_origin_date=timeline_origin_date,
            stop_at_clean_review_boundary=stop_at_clean_review_boundary,
            clean_boundary_event_definition_key=(
                clean_boundary_event_definition_key
            ),
            pause_on_event_definition_key=pause_on_event_definition_key,
        ):
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
        initial, initial_event = _binding(
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
    initial_progress_observation = _compact_progress_observation(
        before,
        date_raw=int(initial["date_raw"]),
        revision=int(initial["revision"]),
    )
    evidence["initial_progress_observation"] = copy.deepcopy(
        initial_progress_observation
    )
    if (
        (initial_event is None or initial_clean_boundary_event)
        and not any(
            initial_progress_observation[name]
            for name in ("b1_active", "central_active", "pp_active")
        )
    ):
        if (
            stop_at_clean_review_boundary
            and initial_progress_observation["review_now_eligible"] is True
        ):
            evidence["result"] = "GREEN"
            evidence["readiness"] = "paused-clean-review-boundary"
            evidence["clean_review_boundary"] = copy.deepcopy(
                initial_progress_observation
            )
            if initial_clean_boundary_event:
                evidence["target_binding"] = copy.deepcopy(initial_event)
            return evidence
        if stop_at_clean_review_boundary:
            evidence["annual_cooldown_wait"] = {
                "starting_date_raw": starting_date,
                "reason": "same-year-review-gate-after-completed-product-cycle",
                "state_mutation_submitted": False,
            }
        elif prefer_natural_cycle:
            evidence["natural_cycle_wait"] = {
                "starting_date_raw": starting_date,
                "reason": "caller_requested_product_annual_pulse",
                "initial_progress": copy.deepcopy(initial_progress_observation),
                "state_mutation_submitted": False,
            }
        else:
            if initial_progress_observation["review_now_eligible"] is not True:
                raise PromotionProductionEntryError(
                    "real review-now product action is not eligible on this seed"
                )
            _activate_review_now_from_progress(
                service,
                source_progress=before,
                source_revision=int(initial["revision"]),
                player=player,
                connection_generation=generation,
                evidence=evidence,
                nonce="promo.entry.review",
                sleeper=sleeper,
            )

    deadline = clock() + timeout_seconds
    last_progress_date_raw = starting_date
    consecutive_progress_query_rebinds = 0
    zg361_6_wait_state: dict[str, object] | None = None
    post_interrupt_progress_due = False
    while clock() < deadline:
        snapshot, event = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
        if runtime_diagnostic_probe is not None:
            diagnostic = runtime_diagnostic_probe()
            if diagnostic:
                raise PromotionProductionEntryError(
                    f"product runtime diagnostic: {diagnostic}"
                )
        date_raw = int(snapshot["date_raw"])
        if date_raw > absolute_end_date:
            raise PromotionProductionEntryError(
                "promotion path exceeded its "
                f"{MAX_ADVANCE_DAYS}-day product observation bound "
                f"({PRODUCT_CYCLE_OPPORTUNITIES} complete "
                f"{B1_AUTHORED_ADVANCE_DAYS}-day authored B1 opportunities "
                f"plus one {POST_PUBLICATION_OBSERVATION_DAYS}-day "
                "post-publication critical-path tail plus "
                f"{ENDGAME_TARGET_WORKFORCE_CYCLES} finite "
                f"{WORKFORCE_CYCLE_OBSERVATION_DAYS}-day Workforce windows)"
            )
        if zg361_6_wait_state is not None:
            active_event = snapshot.get("active_event")
            current_instance_id = (
                active_event.get("instance_id")
                if isinstance(active_event, Mapping)
                else None
            )
            if (
                _snapshot_bridge_pid(snapshot)
                != zg361_6_wait_state["tracked_ck3_pid"]
                or current_instance_id
                != zg361_6_wait_state["event_instance_id"]
            ):
                raise PromotionProductionEntryError(
                    "zg361.6 retain wait crossed its CK3 PID/event identity"
                )
            date_advanced = date_raw > int(
                zg361_6_wait_state["last_date_raw"]
            )
            if date_advanced:
                zg361_6_wait_state["last_date_raw"] = date_raw
                zg361_6_wait_state["advance_deadline"] = (
                    clock() + ZG361_6_MODAL_ADVANCE_TIMEOUT_SECONDS
                )
            elif clock() >= float(zg361_6_wait_state["advance_deadline"]):
                raise PromotionProductionEntryError(
                    "zg361.6 deterministic retain option is unavailable and "
                    "the native modal cannot advance at speed 5"
                )
            if snapshot.get("paused") is not True and not date_advanced:
                if poll_interval_seconds:
                    sleeper(poll_interval_seconds)
                continue
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
            if date_raw > absolute_end_date:
                raise PromotionProductionEntryError(
                    "promotion path exceeded its "
                    f"{MAX_ADVANCE_DAYS}-day product observation bound "
                    f"({PRODUCT_CYCLE_OPPORTUNITIES} complete "
                    f"{B1_AUTHORED_ADVANCE_DAYS}-day authored B1 "
                    f"opportunities plus one "
                    f"{POST_PUBLICATION_OBSERVATION_DAYS}-day "
                    "post-publication critical-path tail plus "
                    f"{ENDGAME_TARGET_WORKFORCE_CYCLES} finite "
                    f"{WORKFORCE_CYCLE_OBSERVATION_DAYS}-day Workforce "
                    "windows)"
                )
            if snapshot.get("paused") is not True:
                if poll_interval_seconds:
                    sleeper(poll_interval_seconds)
                continue

        should_sample_progress = (
            date_raw > last_progress_date_raw
            or event is not None
            or post_interrupt_progress_due
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
            progress_observation = _compact_progress_observation(
                progress_query,
                date_raw=date_raw,
                revision=int(snapshot["revision"]),
            )
            progress_observations.append(progress_observation)
            last_progress_date_raw = date_raw
            if (
                stop_at_clean_review_boundary
                and event is None
                and progress_observation["review_now_eligible"] is True
                and not any(
                    progress_observation[name]
                    for name in ("b1_active", "central_active", "pp_active")
                )
            ):
                evidence["result"] = "GREEN"
                evidence["readiness"] = "paused-clean-review-boundary"
                evidence["clean_review_boundary"] = copy.deepcopy(
                    progress_observation
                )
                return evidence
            if post_interrupt_progress_due and event is None:
                post_interrupt_progress_due = False
                active_witness = any(
                    progress_observation[name]
                    for name in ("b1_active", "central_active", "pp_active")
                )
                if not active_witness:
                    if (
                        stop_at_clean_review_boundary
                        and progress_observation["review_now_eligible"] is not True
                        and evidence.get("annual_cooldown_wait") is None
                    ):
                        evidence["annual_cooldown_wait"] = {
                            "starting_date_raw": date_raw,
                            "reason": (
                                "same-year-review-gate-after-completed-product-cycle"
                            ),
                            "state_mutation_submitted": False,
                        }
                    if (
                        not prefer_natural_cycle
                        and _post_interrupt_seed_is_invalid(
                            progress_observation,
                            stop_at_clean_review_boundary=(
                                stop_at_clean_review_boundary
                            ),
                        )
                    ):
                        evidence["seed_invalid"] = {
                            "date_raw": date_raw,
                            "reason": (
                                "no active B1/Central/PP witness and review-now "
                                "is not eligible after a known interrupt"
                            ),
                            "progress": copy.deepcopy(progress_observation),
                        }
                        raise PromotionProductionEntryError(
                            "promotion seed invalid after known interrupt: no "
                            "active B1/Central/PP witness and review-now is not "
                            "eligible"
                        )
                    if (
                        not prefer_natural_cycle
                        and not stop_at_clean_review_boundary
                        and evidence.get("review_action") is None
                    ):
                        _activate_review_now_from_progress(
                            service,
                            source_progress=progress_query,
                            source_revision=int(snapshot["revision"]),
                            player=player,
                            connection_generation=generation,
                            evidence=evidence,
                            nonce="promo.entry.review.after-interrupt",
                            sleeper=sleeper,
                        )
                        continue
        if isinstance(snapshot.get("active_event"), Mapping) and event is None:
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue
        if event is not None:
            key, event_query = _event_definition(service, event, sleeper=sleeper)
            target_occurrence_index = _pause_target_occurrence_index(
                key,
                pause_on_event_definition_key=pause_on_event_definition_key,
                timeline_interrupt_drains=evidence["timeline_interrupt_drains"],
            )
            if target_occurrence_index == pause_on_event_occurrence:
                evidence["result"] = "GREEN"
                evidence["readiness"] = f"paused-real-{key}"
                evidence["target_binding"] = copy.deepcopy(event)
                evidence["target_occurrence_index"] = target_occurrence_index
                return evidence
            if (
                stop_at_clean_review_boundary
                and key == clean_boundary_event_definition_key
            ):
                progress_observations = evidence["progress_observations"]
                assert isinstance(progress_observations, list)
                latest_progress = (
                    progress_observations[-1]
                    if progress_observations
                    else evidence.get("initial_progress_observation")
                )
                if not (
                    isinstance(latest_progress, Mapping)
                    and latest_progress.get("date_raw") == date_raw
                    and latest_progress.get("review_now_eligible") is True
                    and not any(
                        latest_progress.get(name) is True
                        for name in ("b1_active", "central_active", "pp_active")
                    )
                ):
                    raise PromotionProductionEntryError(
                        "manager seed modal appeared outside a clean review boundary"
                    )
                evidence["result"] = "GREEN"
                evidence["readiness"] = "paused-clean-review-boundary"
                evidence["clean_review_boundary"] = copy.deepcopy(
                    dict(latest_progress)
                )
                evidence["target_binding"] = copy.deepcopy(event)
                return evidence
            if (
                key == M147
                and not stop_at_clean_review_boundary
                and not continue_to_pause_target
            ):
                m146_date = evidence.get("m146_date_raw")
                if not isinstance(m146_date, int) or date_raw < m146_date + HOURS_PER_DAY:
                    raise PromotionProductionEntryError(
                        "zg361pp.147 was not independently observed at D+1"
                    )
                evidence["result"] = "GREEN"
                evidence["readiness"] = "paused-real-zg361pp.147"
                evidence["target_binding"] = event
                return evidence
            contract = _resolve_timeline_interrupt_contract(
                key,
                player=player,
                starting_date=timeline_origin_date,
                stop_at_clean_review_boundary=stop_at_clean_review_boundary,
                continue_to_pause_target=continue_to_pause_target,
            )
            drains = evidence["timeline_interrupt_drains"]
            assert isinstance(drains, list)
            if contract is not None:
                occurrence_count = sum(
                    isinstance(row, Mapping)
                    and row.get("event_definition_key") == key
                    for row in drains
                )
                occurrence_policy = contract.get(
                    "occurrence_policy", "finite"
                )
                max_occurrences = (
                    None
                    if occurrence_policy
                    == "repeatable-within-product-observation-window"
                    else int(contract.get("max_occurrences", 1))
                )
                if (
                    max_occurrences is not None
                    and occurrence_count >= max_occurrences
                ):
                    raise PromotionKnownInterruptContractError(
                        {
                            "classification": "known-interrupt-occurrence-bound",
                            "event_definition_key": key,
                            "date_raw": snapshot.get("date_raw"),
                            "event_instance_id": event.get("event_instance_id"),
                            "occurrence_count": occurrence_count,
                            "max_occurrences": max_occurrences,
                            "snapshot": copy.deepcopy(dict(snapshot)),
                            "event": copy.deepcopy(dict(event)),
                            "query": copy.deepcopy(dict(event_query)),
                            "selection_attempted": False,
                        },
                        "known promotion-timeline interrupt exceeded its "
                        f"occurrence bound: {key!r}",
                    )
                if stop_at_clean_review_boundary:
                    contract = _manager_recovery_occurrence_contract(
                        key,
                        contract,
                        occurrence_count=occurrence_count,
                    )
                if key == "zg361.6" and not _zg361_6_retain_option_ready(
                    event_query
                ):
                    context_value = event_query.get(
                        "current_event_window_context"
                    )
                    context = (
                        context_value
                        if isinstance(context_value, Mapping)
                        else {}
                    )
                    wait_checks = _known_interrupt_checks(
                        snapshot=snapshot,
                        event=event,
                        context=context,
                        event_key=key,
                        contract=contract,
                    )
                    if not all(wait_checks.values()):
                        failed = sorted(
                            name for name, passed in wait_checks.items()
                            if not passed
                        )
                        raise PromotionProductionEntryError(
                            "known promotion-timeline interrupt 'zg361.6' "
                            f"drifted before retain wait: {failed!r}"
                        )
                    tracked_ck3_pid = _snapshot_bridge_pid(snapshot)
                    if tracked_ck3_pid is None:
                        raise PromotionProductionEntryError(
                            "zg361.6 retain wait lacks a positive tracked CK3 PID"
                        )
                    if zg361_6_wait_state is None:
                        wait_end_date = min(
                            absolute_end_date,
                            date_raw
                            + ZG361_6_RETAIN_WAIT_DAYS * HOURS_PER_DAY,
                        )
                        zg361_6_wait_state = {
                            "event_instance_id": int(event["event_instance_id"]),
                            "tracked_ck3_pid": tracked_ck3_pid,
                            "starting_date_raw": date_raw,
                            "last_date_raw": date_raw,
                            "end_date_raw": wait_end_date,
                            "advance_deadline": (
                                clock()
                                + ZG361_6_MODAL_ADVANCE_TIMEOUT_SECONDS
                            ),
                        }
                    if date_raw >= int(zg361_6_wait_state["end_date_raw"]):
                        raise PromotionProductionEntryError(
                            "zg361.6 deterministic retain option 2 did not "
                            "become enabled within its finite product window"
                        )
                    evidence["zg361_6_retain_wait"] = {
                        key: value
                        for key, value in zg361_6_wait_state.items()
                        if key != "advance_deadline"
                    }
                    rebind_audit = evidence["pre_submission_revision_rebinds"]
                    if not isinstance(rebind_audit, list):
                        raise PromotionProductionEntryError(
                            "promotion entry rebind audit storage is invalid"
                        )
                    _retained_modal_map_control(
                        service,
                        step="set-speed-5",
                        player=player,
                        connection_generation=generation,
                        bridge_pid=tracked_ck3_pid,
                        event_instance_id=int(event["event_instance_id"]),
                        rebind_audit=rebind_audit,
                    )
                    _retained_modal_map_control(
                        service,
                        step="resume-map",
                        player=player,
                        connection_generation=generation,
                        bridge_pid=tracked_ck3_pid,
                        event_instance_id=int(event["event_instance_id"]),
                        rebind_audit=rebind_audit,
                    )
                    if poll_interval_seconds:
                        sleeper(poll_interval_seconds)
                    continue
                try:
                    drained = _drain_known_timeline_interrupt(
                        service,
                        snapshot=snapshot,
                        event=event,
                        query=event_query,
                        event_key=key,
                        contract=contract,
                        player=player,
                        connection_generation=generation,
                    )
                except PromotionScenarioInvalidatingInterrupt as error:
                    evidence["result"] = "SCENARIO_INVALID"
                    evidence["readiness"] = (
                        "scenario-invalid-manager-roster-precondition"
                    )
                    evidence["product_result"] = "NOT_EVALUATED"
                    evidence["product_red"] = False
                    evidence["scenario_invalidating_interrupt"] = (
                        copy.deepcopy(error.evidence)
                    )
                    raise
                drains.append(drained)
                if key == "zg361.6":
                    selection = drains[-1].get("selection")
                    if not (
                        isinstance(selection, Mapping)
                        and selection.get("option_number") == 2
                    ):
                        raise PromotionProductionEntryError(
                            "zg361.6 did not use deterministic retain option 2"
                        )
                    zg361_6_wait_state = None
                post_interrupt_progress_due = True
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
    if runtime_diagnostic_probe is not None:
        diagnostic = runtime_diagnostic_probe()
        if diagnostic:
            raise PromotionProductionEntryError(
                f"product runtime diagnostic: {diagnostic}"
            )
    target_label = pause_on_event_definition_key or M147
    target_suffix = (
        f" occurrence {pause_on_event_occurrence}"
        if pause_on_event_occurrence != 1
        else ""
    )
    raise PromotionProductionEntryError(
        f"timed out before paused real {target_label}{target_suffix}"
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
    "PRODUCT_CYCLE_OPPORTUNITIES",
    "PromotionProductionEntryError",
    "PromotionScenarioInvalidatingInterrupt",
    "PromotionProductionEntryService",
    "enter_promotion_source_checkpoint_v1",
]
