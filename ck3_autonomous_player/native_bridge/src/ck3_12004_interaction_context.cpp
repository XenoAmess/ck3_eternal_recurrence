#include "xar_bridge/ck3_12004_interaction_context.hpp"

namespace xar::ck3_12004 {

InteractionContextBindings12004 BindInteractionContext12004(
    std::uintptr_t base, std::string_view actual_sha) noexcept {
  InteractionContextBindings12004 b{};
  if (base == 0 || actual_sha != kExecutableSha256) return b;
  b.context.core = BindCoreImage(base, actual_sha);
  if (!b.context.core.enabled) return b;
  b.module_base = base;
  auto &c = b.context;
  c.redirect_roles = reinterpret_cast<ck3_12002::MarriageRedirectInteractionRoles>(
      base + kInteractionRedirectRolesRva12004);
  c.construct_all_roles = reinterpret_cast<ck3_12002::MarriageConstructInteractionAllRoles>(
      base + kInteractionConstructAllRolesRva12004);
  c.refresh = reinterpret_cast<ck3_12002::MarriageRefreshInteractionContext>(
      base + kInteractionRefreshRva12004);
  c.finalize = reinterpret_cast<ck3_12002::MarriageFinalizeInteractionContext>(
      base + kInteractionFinalizeRva12004);
  c.validate = reinterpret_cast<ck3_12002::MarriageValidateInteractionContext>(
      base + kInteractionValidatorRva12004);
  c.destroy = reinterpret_cast<ck3_12002::MarriageDestroyInteractionContext>(
      base + kInteractionDestroyRva12004);
  c.recipient_answer_score = reinterpret_cast<ck3_12002::MarriageReadInteractionAnswerScore>(
      base + kInteractionRecipientAnswerScoreRva12004);
  c.evaluate_cost = reinterpret_cast<ck3_12002::MarriageEvaluateInteractionCost>(
      base + kInteractionCostEvaluatorRva12004);
  c.evaluate_trigger = reinterpret_cast<ck3_12002::MarriageEvaluateInteractionTrigger>(
      base + kInteractionTriggerEvaluatorRva12004);
  b.get_database = reinterpret_cast<ck3_12002::FactionGiftGetDatabaseV1>(
      base + kInteractionDatabaseGetterRva12004);
  b.stable_hash = reinterpret_cast<ck3_12002::FactionGiftStableHashV1>(
      base + kInteractionStableHashRva12004);
  b.lookup_definition = reinterpret_cast<ck3_12002::FactionGiftLookupDefinitionV1>(
      base + kInteractionDefinitionLookupRva12004);
  b.construct_two_role = reinterpret_cast<ck3_12002::FactionGiftConstructTwoRoleContextV1>(
      base + kInteractionConstructTwoRoleRva12004);
  b.get_script_identifier_table = reinterpret_cast<ck3_11906::GetScriptIdentifierTable>(
      base + kInteractionScriptIdTableRva12004);
  b.lookup_script_identifier_id = reinterpret_cast<ck3_11906::LookupScriptIdentifierId>(
      base + kInteractionLookupScriptIdRva12004);
  b.clear_local_options = reinterpret_cast<void (*)(void *)>(
      base + kInteractionClearOptionsRva12004);
  b.select_local_option = reinterpret_cast<void (*)(void *, std::int32_t)>(
      base + kInteractionSelectOptionRva12004);
  b.evaluate_answer = reinterpret_cast<ck3_11906::EvaluateCharacterInteractionAnswer>(
      base + kInteractionEvaluateAnswerRva12004);
  b.read_character_interaction_answer_score = c.recipient_answer_score;
  // Actual .4 admission: current4-context-release/ROOT-DELIVERY.json joins the
  // preserved finite spans, three cached full-body continuations, six consumed
  // definition operands, centrally owned script-ID proof and parent custody.
  c.enabled = true;
  b.enabled = true;
  return b;
}

} // namespace xar::ck3_12004
