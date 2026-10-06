#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_nonwar_router.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/faction_gift_mitigation_async_glue_v1.hpp"
#include "active_scheme_sway_private_transport_v1.hpp"
#include "active_scheme_sway_formal_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_router.hpp"
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_faction_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_realm_law.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1)
#include "xar_bridge/ck3_12002_realm_law_action_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_government_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_family_obligations_mailbox.hpp"
#endif
#include "ck3_12002_feast_planner_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_private_transport_v1.hpp"
#include "ck3_12002_activity_stage5_canstart_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_cost_private_transport_v1.hpp"
#include "ck3_12002_activity_feast_guest_transport.hpp"

namespace xar::ck3_12002 {
namespace {
[[maybe_unused]] void AppendString(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) {
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  out += '"';
}

[[maybe_unused]] std::string ReadOnlyFrame(
    std::string_view id, std::string_view step, std::string_view key,
    std::string_view native, std::uint64_t revision,
    std::uint64_t sequence = 0) {
  std::string status;
  if (!bridge::JsonStringField(native, "status", status, 128)) status = "available";
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(out, id);
  out += ",\"ok\":true,\"result\":{\"step\":";
  AppendString(out, step);
  out += ",\"accepted\":true,\"status\":";
  AppendString(out, status);
  out += ",\"snapshot_revision\":" + std::to_string(revision);
  if (sequence != 0) out += ",\"query_sequence\":" + std::to_string(sequence);
  if (key == "player_faction_alerts") {
    bool alert_ready = false;
    (void)bridge::JsonBooleanField(native, "alert_ready", alert_ready);
    out += ",\"player_faction_alerts_ready\":";
    out += alert_ready ? "true" : "false";
  } else {
    out += ",\"private_build\":true,\"read_only\":true,\"advertised\":false";
  }
  out += ',';
  AppendString(out, key); out += ':'; out += native;
  out += ",\"backend_id\":\"native-headless\"}}";
  return out;
}
}

void PopulateNonwarRouterExecutors12002(NonwarMailboxExecutorsV1 &out) noexcept {
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  out.council = &ExecuteCouncilMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  out.faction_gift = &ExecuteFactionGiftPrivateMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  out.sway_state = &ExecuteActiveSwayMailbox12002;
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
  out.sway_action = &ExecuteActiveSwayMailbox12002;
#endif
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
  out.law_final_terms = &ExecuteRealmLawPausedPrivateQuery12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1)
  out.law_action = &ExecuteRealmLawPrivateAction12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_PLANNER_OPEN_PRIVATE_V1)
  out.feast_open = &ExecuteActivityFeastPlannerOpenPrivate12002V1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_OPTION_READ_PRIVATE_V1)
  out.feast_options = &ExecuteActivityStage1OptionReadPrivate12002V1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_CANSTART_PRIVATE_V1)
  out.feast_can_start = &ExecuteActivityStage5CanStartPrivate12002V1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_GOLD_COST_PRIVATE_V1)
  out.feast_gold = &ExecuteActivityStage5GoldCostPrivateV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE5_FEAST_FULL_COST_PRIVATE_V1)
  out.feast_full_costs = &ExecuteActivityStage5FeastFullCostPrivateV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_DESTINATION_PRIVATE_V1)
  out.feast_destination = &ExecuteActivityStage2DestinationSelectPrivate12002V1;
  out.feast_stage2_confirm = &ExecuteActivityStage2ConfirmPrivate12002V1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1)
  out.feast_start = &ExecuteActivityFeastStage5Private12002V1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_CANDIDATE_PRIVATE_V1)
  out.feast_guest = &ExecuteActivityFeastGuestCandidatePrivateV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_TOGGLE_PRIVATE_V1)
  out.feast_guest_rules = &ExecuteActivityFeastGuestRulePrivateV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_OPINION_PRIVATE_V1)
  out.feast_guest_opinion = &ExecuteActivityFeastGuestOpinionPrivateV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  out.prisoner_collection = &ExecutePlayerPrisonerCollection12002;
#if defined(XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1)
  out.prisoner_ransom = &ExecutePlayerPrisonerRansom12002;
#endif
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
  out.factions = &ExecutePlayerFactionAlertsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1)
  out.government = &bridge::private_observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  out.religion = &ExecutePlayerReligionMailbox12002;
  out.holy_order_loan = &ExecutePlayerHolyOrderLoanMailbox12003;
  out.head_of_faith_gold = &ck3_12003::ExecutePlayerHeadOfFaithGoldMailbox12003;
  out.seek_indulgences_terms = &ck3_12003::ExecutePlayerSeekIndulgencesTermsMailbox12003;
  out.repentance = &ck3_12003::ExecutePlayerRepentanceMailbox12003;
  out.holy_order_context = &ck3_12003::ExecutePlayerHolyOrderContextMailbox12003;
  out.holy_order_selected_title_terms =
      &ck3_12003::ExecutePlayerHolyOrderSelectedTitleTermsMailbox12003;
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1)
  out.family_obligations = &ExecuteFamilyObligationsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
  out.rite_governance = &ExecutePlayerRiteGovernanceMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  out.clergy = &ExecutePlayerClergyAppointmentMailbox12002;
  out.county_conversion_task_action = &ExecutePlayerCountyConversionTaskActionMailbox12003;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  out.religion_conversion = &ExecutePlayerReligionConversionTermsMailbox12002;
  out.religion_conversion_action = &ExecutePlayerReligionConversionActionMailbox12003;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
  out.religion_doctrines = &ExecutePlayerReligionDoctrinesMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  out.rite_members = &ExecutePlayerRiteMembersMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  out.religion_conversion_choices = &ExecutePlayerReligionConversionChoicesMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  out.religion_conversion_inputs = &ExecutePlayerReligionConversionInputsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  out.sway_completion = &ExecuteSwayCompletionMailboxV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
  out.religion_hostility = &ExecutePlayerReligionHostilityMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
  out.religion_doctrine_knowledge = &ExecutePlayerReligionDoctrineKnowledgeMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  out.religion_tenets = &ExecutePlayerReligionTenetsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
  out.epidemic_treatment = &ExecutePlayerEpidemicTreatmentMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  out.epidemic_recovery = &ExecutePlayerEpidemicRecoveryMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  out.religion_conversion_reasons = &ExecutePlayerReligionConversionReasonsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  out.sway_completion_execution = &ExecuteSwayCompletionExecutionMailboxV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  out.religion_reform = &ExecutePlayerReligionReformMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
  out.religion_doctrine_catalogue = &ExecutePlayerReligionDoctrineCatalogueMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  out.religion_conversion_outcome = &ExecutePlayerReligionConversionOutcomeMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
  out.religion_numeric_special_parameters = &ExecutePlayerReligionNumericSpecialParametersMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  out.sway_completion_termination = &ExecuteSwayCompletionTerminationMailboxV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1)
  out.religion_personal_parameters = &ExecutePlayerReligionPersonalParametersMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  out.sway_completion_invalidation_reason = &ExecuteSwayCompletionInvalidationReasonMailboxV1;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1)
  out.religion_draft_groups = &ExecutePlayerReligionDraftGroupsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1)
  out.religion_draft_doctrine_choices = &ExecutePlayerReligionDraftDoctrineChoicesMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1)
  out.religion_draft_tenet_choices = &ExecutePlayerReligionDraftTenetChoicesMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
  out.religion_draft_resource_costs = &ExecutePlayerReligionDraftResourceCostsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1)
  out.religion_ai_reform_inputs = &ExecutePlayerReligionAIReformInputsMailbox12002;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1)
  out.sway_outcome_opinion = &ExecuteSwayOutcomeMailboxV1;
#endif
  (void)out;
}

bool IsNonwarPrivateStep12002(std::string_view step) noexcept {
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  if (IsCouncilPrivate12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  if (step == ck3_11906::kFactionGiftPrivateQueryStepV1 ||
      step == ck3_11906::kFactionGiftPrivateSubmitStepV1 ||
      step == ck3_11906::kFactionGiftPrivateReceiptStepV1 ||
      step == ck3_11906::kFactionGiftPrivateColdRecoveryStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  if (step.starts_with(ck3_11906::kActiveSchemeSwayPrivateQueryPrefixV1)) return true;
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1)
  if (step.starts_with(ck3_11906::kActiveSchemeSwayFormalSubmitPrefixV1) ||
      step.starts_with(ck3_11906::kActiveSchemeSwayFormalReceiptPrefixV1)) return true;
#endif
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
  if (step == kRealmLawPausedPrivateQueryStep12002) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1)
  if (IsRealmLawPrivateActionStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  if (step.starts_with("query-player-prisoner-collection-private-v1") ||
      step == "submit-player-prisoner-ransom-private-v1" ||
      step.starts_with(kPrisonerWarRetentionStepPrefix12002)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
  if (step == "query-player-faction-alerts-v1") return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1)
  if (IsGovernmentRuntimeAdapterQuery12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  if (IsPlayerReligionPrivateStep12002(step)) return true;
  if (IsPlayerHolyOrderLoanPrivateStep12003(step)) return true;
  if (ck3_12003::IsPlayerHeadOfFaithGoldPrivateStep12003(step)) return true;
  if (ck3_12003::IsPlayerSeekIndulgencesTermsPrivateStep12003(step)) return true;
  if (ck3_12003::IsPlayerRepentancePrivateStep12003(step)) return true;
  if (ck3_12003::IsPlayerHolyOrderContextPrivateStep12003(step)) return true;
  if (ck3_12003::IsPlayerHolyOrderSelectedTitleTermsPrivateStep12003(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1)
  if (IsFamilyObligationsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
  if (IsPlayerRiteGovernancePrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  if (IsPlayerClergyAppointmentPrivateStep12002(step)) return true;
  if (IsPlayerCountyConversionTaskActionPrivateStep12003(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  if (IsPlayerReligionConversionTermsPrivateStep12002(step)) return true;
  if (IsPlayerReligionConversionActionPrivateStep12003(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDoctrinesPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  if (IsPlayerRiteMembersPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1)
  if (ck3_12003::IsConfucianAssemblyPrivateStep12003(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1)
  if (ck3_12003::IsConfucianReligiousTitlePrivateStep12003(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1)
  if (ck3_12003::IsConfucianChallengerGraphPrivateStep12003(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  if (IsPlayerReligionConversionChoicesPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  if (IsPlayerReligionConversionInputsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  if (step == kSwayCompletionStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
  if (IsPlayerReligionHostilityPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDoctrineKnowledgePrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  if (IsPlayerReligionTenetsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
  if (IsPlayerEpidemicTreatmentPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
  if (IsEpidemicRecoveryPrivate12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  if (IsPlayerReligionConversionReasonsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  if (step == kSwayCompletionExecutionStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  if (IsPlayerReligionReformPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDoctrineCataloguePrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  if (IsPlayerReligionConversionOutcomePrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
  if (IsPlayerReligionNumericSpecialParametersPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  if (step == kSwayCompletionTerminationStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1)
  if (IsPlayerReligionPersonalParametersPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  if (step == kSwayCompletionInvalidationReasonStepV1) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDraftGroupsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDraftDoctrineChoicesPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDraftTenetChoicesPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
  if (IsPlayerReligionDraftResourceCostsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1)
  if (IsPlayerReligionAIReformInputsPrivateStep12002(step)) return true;
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1)
  if (step == kSwayOutcomeOpinionStepV1) return true;
#endif
  return IsActivityFeastPrivateStep12002(step);
}

void PollNonwarPrivateState12002(NonwarPrivateState12002 &state) noexcept {
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  PollCouncilTransport12002(state.council);
#endif
  (void)state;
}

bool HandleNonwarPrivate12002(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    NonwarPrivateState12002 &state, std::string &serialized, std::string &failure,
    bridge::ActivityCostSlot12ObserverV1 *cost,
    bridge::ActivityGuestRuleProvenanceObserverV1 *provenance) noexcept {
  serialized.clear(); failure.clear();
  try {
    const auto &native = NativeAdapter12002(adapter);
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1)
    if (step == kSwayOutcomeOpinionStepV1)
      return HandleSwayOutcomeEventV1(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1)
    if (IsPlayerReligionAIReformInputsPrivateStep12002(step))
      return HandlePlayerReligionAIReformInputsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDraftDoctrineChoicesPrivateStep12002(step))
      return HandlePlayerReligionDraftDoctrineChoicesPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDraftTenetChoicesPrivateStep12002(step))
      return HandlePlayerReligionDraftTenetChoicesPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDraftResourceCostsPrivateStep12002(step))
      return HandlePlayerReligionDraftResourceCostsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDraftGroupsPrivateStep12002(step))
      return HandlePlayerReligionDraftGroupsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1)
    if (IsPlayerReligionPersonalParametersPrivateStep12002(step))
      return HandlePlayerReligionPersonalParametersPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    if (step == kSwayCompletionInvalidationReasonStepV1) {
      if (state.sway_invalidation_reason_recorder == nullptr) {
        failure = "sway_invalidation_reason_observer_not_installed"; return false;
      }
      return HandleSwayCompletionInvalidationReasonV1(native, mailbox, *state.sway_invalidation_reason_recorder,
          published, revision, step, payload, request_id, serialized, failure);
    }
#endif

#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    if (IsPlayerReligionConversionActionPrivateStep12003(step))
      return HandlePlayerReligionConversionActionPrivate12003(state.religion_conversion_action,
          native, mailbox, published, revision, step, payload, request_id, serialized, failure);
    if (IsPlayerReligionConversionOutcomePrivateStep12002(step))
      return HandlePlayerReligionConversionOutcomePrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1)
    if (IsPlayerReligionNumericSpecialParametersPrivateStep12002(step))
      return HandlePlayerReligionNumericSpecialParametersPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    if (step == kSwayCompletionTerminationStepV1) {
      if (state.sway_termination_recorder == nullptr) {
        failure = "sway_termination_observer_not_installed"; return false;
      }
      return HandleSwayCompletionTerminationV1(native, mailbox, *state.sway_termination_recorder,
          published, revision, step, payload, request_id, serialized, failure);
    }
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1)
    if (IsPlayerEpidemicTreatmentPrivateStep12002(step))
      return HandlePlayerEpidemicTreatmentPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_RECOVERY_PRIVATE_QUERY_V1)
    if (IsEpidemicRecoveryPrivate12002(step))
      return HandleEpidemicRecoveryPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    if (IsPlayerReligionConversionReasonsPrivateStep12002(step))
      return HandlePlayerReligionConversionReasonsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    if (step == kSwayCompletionExecutionStepV1) {
      if (state.sway_execution_recorder == nullptr) {
        failure = "sway_execution_observer_not_installed"; return false;
      }
      return HandleSwayCompletionExecutionV1(native, mailbox, *state.sway_execution_recorder,
          published, revision, step, payload, request_id, serialized, failure);
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
    if (IsPlayerReligionReformPrivateStep12002(step))
      return HandlePlayerReligionReformPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDoctrineCataloguePrivateStep12002(step))
      return HandlePlayerReligionDoctrineCataloguePrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif

#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1)
    if (IsPlayerRiteGovernancePrivateStep12002(step))
      return HandlePlayerRiteGovernancePrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
    if (IsPlayerCountyConversionTaskActionPrivateStep12003(step))
      return HandlePlayerCountyConversionTaskActionPrivate12003(state.county_conversion_task_action,
          native, mailbox, published, revision, step, payload, request_id, serialized, failure);
    if (IsPlayerClergyAppointmentPrivateStep12002(step))
      return HandlePlayerClergyAppointmentPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    if (IsPlayerReligionConversionTermsPrivateStep12002(step))
      return HandlePlayerReligionConversionTermsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDoctrinesPrivateStep12002(step))
      return HandlePlayerReligionDoctrinesPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
    if (IsPlayerRiteMembersPrivateStep12002(step))
      return HandlePlayerRiteMembersPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1)
    if (ck3_12003::IsConfucianAssemblyPrivateStep12003(step))
      return ck3_12003::HandleConfucianAssemblyPrivate12003(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1)
    if (ck3_12003::IsConfucianReligiousTitlePrivateStep12003(step))
      return ck3_12003::HandleConfucianReligiousTitlePrivate12003(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1)
    if (ck3_12003::IsConfucianChallengerGraphPrivateStep12003(step))
      return ck3_12003::HandleConfucianChallengerGraphPrivate12003(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    if (IsPlayerReligionConversionChoicesPrivateStep12002(step))
      return HandlePlayerReligionConversionChoicesPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
    if (IsPlayerReligionConversionInputsPrivateStep12002(step))
      return HandlePlayerReligionConversionInputsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    if (step == kSwayCompletionStepV1)
      return HandleSwayCompletionV1(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1)
    if (IsPlayerReligionHostilityPrivateStep12002(step))
      return HandlePlayerReligionHostilityPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1)
    if (IsPlayerReligionDoctrineKnowledgePrivateStep12002(step))
      return HandlePlayerReligionDoctrineKnowledgePrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
    if (IsPlayerReligionTenetsPrivateStep12002(step))
      return HandlePlayerReligionTenetsPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
    if (IsCouncilPrivate12002(step)) {
      if (!state.council.configured && !ConfigureCouncilTransport12002(
          state.council, mailbox,
          reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
          xar::game::ReviewedCrozierAbiSha256(native.descriptor()),
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1)
          true,
#else
          false,
#endif
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1)
          true)) {
#else
          false)) {
#endif
        failure = "exact-build council private binding unavailable"; return false;
      }
      return HandleCouncilPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, state.council, serialized, failure);
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
    if (step.find("faction-gift-") != std::string_view::npos)
      return HandleFactionGiftPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, state.gift, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
    if (step.find("active-scheme-sway") != std::string_view::npos)
      return HandleActiveSwayPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, state.sway, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1)
    if (step == kRealmLawPausedPrivateQueryStep12002) {
      std::string dto;
      if (!ReadRealmLawOnApplicationMain12002(native, mailbox, published,
                                            revision, dto, failure)) return false;
      serialized = ReadOnlyFrame(request_id, step, "realm_law_final_terms", dto, revision);
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
    if (step.find("player-prisoner-") != std::string_view::npos ||
        step.starts_with(kPrisonerWarRetentionStepPrefix12002))
      return HandlePlayerPrisonerPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, state.prisoner, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_REALM_LAW_ENACT_PRIVATE_V1)
    if (IsRealmLawPrivateActionStep12002(step))
      return HandleRealmLawPrivate12002(native, mailbox, published, revision,
          step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_FACTION_ALERTS_PRIVATE_QUERY_V1)
    if (step == "query-player-faction-alerts-v1") {
      std::string dto;
      if (!ReadPlayerFactionAlertsOnApplicationMain12002(native, mailbox,
              published, revision, dto, failure)) return false;
      serialized = ReadOnlyFrame(request_id, step, "player_faction_alerts", dto,
                                revision, ++state.faction_query_sequence);
      return true;
    }
#endif
#if defined(XAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_PRIVATE_QUERY_V1)
    if (IsGovernmentRuntimeAdapterQuery12002(step))
      return ReadGovernmentRuntimeAdapterOnApplicationMain12002(native, mailbox,
          published, revision, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
    if (IsPlayerReligionPrivateStep12002(step))
      return HandlePlayerReligionPrivate12002(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
    if (IsPlayerHolyOrderLoanPrivateStep12003(step))
      return HandlePlayerHolyOrderLoanPrivate12003(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
    if (ck3_12003::IsPlayerHeadOfFaithGoldPrivateStep12003(step))
      return ck3_12003::HandlePlayerHeadOfFaithGoldPrivate12003(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
    if (ck3_12003::IsPlayerSeekIndulgencesTermsPrivateStep12003(step))
      return ck3_12003::HandlePlayerSeekIndulgencesTermsPrivate12003(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
    if (ck3_12003::IsPlayerRepentancePrivateStep12003(step))
      return ck3_12003::HandlePlayerRepentancePrivate12003(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
    if (ck3_12003::IsPlayerHolyOrderContextPrivateStep12003(step))
      return ck3_12003::HandlePlayerHolyOrderContextPrivate12003(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
    if (ck3_12003::IsPlayerHolyOrderSelectedTitleTermsPrivateStep12003(step))
      return ck3_12003::HandlePlayerHolyOrderSelectedTitleTermsPrivate12003(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
#endif
#if defined(XAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1)
    if (IsFamilyObligationsPrivateStep12002(step))
      return HandleFamilyObligationsPrivate12002(native, mailbox, published,
          revision, step, payload, request_id, serialized, failure);
#endif
    (void)state;
    return HandleActivityFeastPrivate12002(native, mailbox, published, revision,
        step, payload, request_id, serialized, failure, cost, provenance);
  } catch (...) { failure = "exact-build nonwar private query failed"; return false; }
}

} // namespace xar::ck3_12002
