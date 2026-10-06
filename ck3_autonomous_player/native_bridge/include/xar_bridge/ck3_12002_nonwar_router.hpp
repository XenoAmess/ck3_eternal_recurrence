#pragma once

#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#if defined(XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
#include "xar_bridge/ordinary_holy_war_declaration_context12003_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12003_confucian_assembly_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12003_confucian_religious_title_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12003_confucian_challenger_graph_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_rite_governance12002_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_rite_governance12002_clergy_mailbox.hpp"
#include "xar_bridge/ck3_12003_county_conversion_task_action_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_conversion_mailbox.hpp"
#include "xar_bridge/ck3_12003_religion_conversion_action_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_rite_governance12002_members_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_conversion_choices_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_conversion_inputs_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#include "xar_bridge/ck3_12002_sway_completion_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_hostility_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_choices_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_tenet_rows_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_mailbox.hpp"
#include "xar_bridge/ck3_12003_holy_order_loan_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_hof_gold_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_seek_indulgences_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_repentance_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_holy_order_mailbox.hpp"
#include "xar_bridge/ck3_12003_holy_order_selected_title_terms_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_epidemic_treatment_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_epidemic_recovery_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_religion_conversion_reasons_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#include "xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_reform12002_query_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_catalogue_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
#include "xar_bridge/conversion_outcome12002_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_numeric_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#include "xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_doctrine12002_personal_parameters_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_reform12002_group_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_reform12002_fullchoices_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_reform12002_tenet_sources_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_reform12002_resource_costs_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1)
#include "xar_bridge/religion_reform12002_ai_inputs_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_sway_outcome_mailbox.hpp"
#endif
#include "xar_bridge/game_adapter.hpp"
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
#include "xar_bridge/ck3_12002_council_transport.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
#include "xar_bridge/ck3_12002_faction_gift_router.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_prisoner_mailbox.hpp"
#include "xar_bridge/ck3_12004_prisoner_mailbox.hpp"
#endif

namespace xar::bridge {
struct ActivityCostSlot12ObserverV1;
struct ActivityGuestRuleProvenanceObserverV1;
}

namespace xar::ck3_12002 {

// One worker owns these existing domain ledgers across MCP reconnections.
struct NonwarPrivateState12002 {
  std::uint64_t faction_query_sequence = 0;
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  PlayerCountyConversionTaskActionMailboxState12003 county_conversion_task_action{};
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  PlayerReligionConversionActionMailboxState12003 religion_conversion_action{};
#endif
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  CouncilTransportState12002 council{};
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  FactionGiftPrivateState12002 gift{};
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  ActiveSwayState12002 sway{};
  const SwayTerminationRecorder12002 *sway_termination_recorder = nullptr;
  const SwayInvalidationReasonRecorder12002 *sway_invalidation_reason_recorder = nullptr;
  const SwayExecutionRecorder12002 *sway_execution_recorder = nullptr;
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  PrisonerPrivateWorkerState12002 prisoner{};
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  ck3_12004::PrisonerPrivateWorkerState12004 prisoner12004{};
#endif
};

void PopulateNonwarRouterExecutors12002(NonwarMailboxExecutorsV1 &) noexcept;
void PopulateNonwarRouterExecutors12004(NonwarMailboxExecutorsV1 &) noexcept;
bool IsNonwarPrivateStep12002(std::string_view step) noexcept;
bool IsNonwarPrivateStep12004(const game::GameAdapter &,
                             std::string_view step) noexcept;
void PollNonwarPrivateState12002(NonwarPrivateState12002 &) noexcept;
bool HandleNonwarPrivate12002(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t revision, std::string_view step,
    std::string_view payload, std::string_view request_id,
    NonwarPrivateState12002 &, std::string &serialized, std::string &failure,
    bridge::ActivityCostSlot12ObserverV1 *cost = nullptr,
    bridge::ActivityGuestRuleProvenanceObserverV1 *provenance = nullptr) noexcept;

} // namespace xar::ck3_12002
