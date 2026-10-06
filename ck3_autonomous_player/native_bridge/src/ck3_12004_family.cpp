#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12004_family_abi.hpp"
#include "xar_bridge/ck3_12004_family_break_penalty.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {
bool LocalFamilyRead(void *, std::uintptr_t address, void *output,
                     std::size_t size) noexcept {
  if (address == 0 || output == nullptr) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}
} // namespace

ck3_12002::ContextBindings BindFamilyContextImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::ContextBindings bindings{};
  bindings.core = BindCoreImage(base, sha);
  if (!bindings.core.enabled) return bindings;
  bindings.enabled = true;
  bindings.interaction_database_slot =
      reinterpret_cast<void **>(base + kMarriageInteractionDatabaseSlotRva);
  bindings.redirect_roles =
      reinterpret_cast<ck3_12002::MarriageRedirectInteractionRoles>(
          base + kMarriageRedirectInteractionRolesRva);
  bindings.construct_all_roles =
      reinterpret_cast<ck3_12002::MarriageConstructInteractionAllRoles>(
          base + kMarriageConstructInteractionAllRolesRva);
  bindings.refresh =
      reinterpret_cast<ck3_12002::MarriageRefreshInteractionContext>(
          base + kMarriageRefreshInteractionContextRva);
  bindings.finalize =
      reinterpret_cast<ck3_12002::MarriageFinalizeInteractionContext>(
          base + kMarriageFinalizeInteractionContextRva);
  bindings.validate =
      reinterpret_cast<ck3_12002::MarriageValidateInteractionContext>(
          base + kMarriageValidateInteractionContextRva);
  bindings.destroy =
      reinterpret_cast<ck3_12002::MarriageDestroyInteractionContext>(
          base + kMarriageDestroyInteractionContextRva);
  bindings.recipient_answer_score =
      reinterpret_cast<ck3_12002::MarriageReadInteractionAnswerScore>(
          base + kMarriageRecipientInteractionAnswerScoreRva);
  bindings.intermediary_answer_score =
      reinterpret_cast<ck3_12002::MarriageReadInteractionAnswerScore>(
          base + kMarriageIntermediaryInteractionAnswerScoreRva);
  bindings.evaluate_cost =
      reinterpret_cast<ck3_12002::MarriageEvaluateInteractionCost>(
          base + kMarriageInteractionCostEvaluatorRva);
  bindings.evaluate_trigger =
      reinterpret_cast<ck3_12002::MarriageEvaluateInteractionTrigger>(
          base + kMarriageInteractionTriggerEvaluatorRva);
  return bindings;
}

ck3_12002::FamilyObligationsBreakBindingsV1 BindFamilyObligationsBreakImageV1(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::FamilyObligationsBreakBindingsV1 bindings{};
  bindings.interaction = BindFamilyContextImage(base, sha);
  if (!bindings.interaction.enabled) return bindings;
  bindings.enabled = true;
  bindings.penalty = BindFamilyBreakPenaltyImage(base, sha);
  bindings.get_database =
      reinterpret_cast<ck3_12002::FamilyBreakDatabaseGetterV1>(
          base + kFamilyBreakDatabaseGetterRvaV1);
  bindings.stable_hash = reinterpret_cast<ck3_12002::FamilyBreakStableHashV1>(
      base + kFamilyBreakStableHashRvaV1);
  bindings.lookup_definition =
      reinterpret_cast<ck3_12002::FamilyBreakLookupDefinitionV1>(
          base + kFamilyBreakLookupDefinitionRvaV1);
  bindings.missing_definition_slot =
      reinterpret_cast<void **>(base + kFamilyBreakMissingDefinitionSlotRvaV1);
  return bindings;
}

ck3_12002::FamilyProjectionBindings BindFamilyProjectionImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::FamilyProjectionBindings bindings{};
  if (base == 0 || sha != kExecutableSha256 ||
      kFamilyProjectionMatrilinealSlotRva >
          (std::numeric_limits<std::uintptr_t>::max)() - base) return bindings;
  bindings.module_base = base;
  bindings.exact_build_admitted = true;
  bindings.admitted_executable_sha256 = sha;
  bindings.read_memory = &LocalFamilyRead;
  bindings.project_pairs =
      reinterpret_cast<bridge::ProjectMarriageCandidateAlliancePairsV1>(
          base + kFamilyProjectionPairWrapperRva);
  bindings.read_boolean_option =
      reinterpret_cast<bridge::ReadMarriageCandidateBooleanOptionV1>(
          base + kFamilyProjectionReadOptionRva);
  bindings.set_boolean_option =
      reinterpret_cast<bridge::SetMarriageCandidateBooleanOptionV1>(
          base + kFamilyProjectionSetOptionRva);
  bindings.is_allied =
      reinterpret_cast<bridge::ReadMarriageCandidateIsAlliedV1>(
          base + kFamilyProjectionIsAlliedRva);
  bindings.matrilineal_option_id_slot = base + kFamilyProjectionMatrilinealSlotRva;
  bindings.native_owner_vtable = base + kFamilyProjectionOwnerVtableRva;
  return bindings;
}

ck3_12002::family_value::Bindings BindFamilyValuesImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::family_value::Bindings bindings{};
  bindings.core = BindCoreImage(base, sha);
  if (!bindings.core.enabled) return bindings;
  bindings.enabled = true;
  bindings.house_store =
      reinterpret_cast<void **>(base + kFamilyHouseStoreSlotRva);
  bindings.house_fallback =
      reinterpret_cast<void **>(base + kFamilyHouseFallbackSlotRva);
  bindings.dynasty_store =
      reinterpret_cast<void **>(base + kFamilyDynastyStoreSlotRva);
  bindings.dynasty_fallback =
      reinterpret_cast<void **>(base + kFamilyDynastyFallbackSlotRva);
  bindings.fertility_gate =
      reinterpret_cast<ck3_12002::family_value::FertilityGate>(
          base + kFamilyFertilityGateRva);
  return bindings;
}

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
ck3_12002::FamilyBindings BindFamilyImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::FamilyBindings bindings{};
  bindings.context = BindFamilyContextImage(base, sha);
  bindings.values = BindFamilyValuesImage(base, sha);
  if (!bindings.context.enabled) return bindings;
  bindings.enabled = true;
  bindings.evaluate_answer =
      reinterpret_cast<ck3_12002::FamilyEvaluateAnswer>(
          base + kFamilyEvaluateAnswerRva);
  bindings.read_boolean_option =
      reinterpret_cast<ck3_12002::FamilyReadBooleanOption>(
          base + kFamilyProjectionReadOptionRva);
  bindings.set_boolean_option =
      reinterpret_cast<ck3_12002::FamilySetBooleanOption>(
          base + kFamilySetBooleanOptionRva);
  bindings.adult_threshold_zero =
      reinterpret_cast<const std::int32_t *>(base + kFamilyAdultThresholdZeroRva);
  bindings.adult_threshold_one =
      reinterpret_cast<const std::int32_t *>(base + kFamilyAdultThresholdOneRva);
  bindings.grand_wedding_option =
      reinterpret_cast<const std::uint32_t *>(base + kFamilyGrandWeddingOptionRva);
  bindings.matrilineal_option =
      reinterpret_cast<const std::uint32_t *>(base + kFamilyProjectionMatrilinealSlotRva);
  return bindings;
}

ck3_12002::family_obligations_lineage::Bindings BindFamilyLineageImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  ck3_12002::family_obligations_lineage::Bindings bindings{};
  bindings.family = BindFamilyImage(base, sha);
  bindings.projection = BindFamilyProjectionImage(base, sha);
  if (!bindings.family.enabled || !bindings.projection.exact_build_admitted)
    return bindings;
  bindings.enabled = true;
  bindings.native_preview_parent =
      reinterpret_cast<ck3_12002::family_obligations_lineage::ReadChildHousePreviewParent>(
          base + kNativeChildHousePreviewParentRva);
  bindings.native_offer_vtable = base + kNativeMarriageMatchOfferVtableRva;
  return bindings;
}
#endif

} // namespace xar::ck3_12004
