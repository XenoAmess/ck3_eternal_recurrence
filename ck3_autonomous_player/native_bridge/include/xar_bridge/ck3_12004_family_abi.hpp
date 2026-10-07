#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_family_projection.hpp"

#include <array>

namespace xar::ck3_12004 {

// Actual .4 finite context/obligations spans and rel/RIP operand pairs:
// actual4-native/function-map/FAMILY-MAP.json. These are independent bindings,
// not a whole-image alias to an older executable.
inline constexpr std::uintptr_t kMarriageInteractionDatabaseSlotRva = 0x5C67538;
inline constexpr std::uintptr_t kMarriageRedirectInteractionRolesRva = 0x3148DC0;
inline constexpr std::uintptr_t kMarriageConstructInteractionAllRolesRva = 0x3076E30;
inline constexpr std::uintptr_t kMarriageRefreshInteractionContextRva = 0x3078A40;
inline constexpr std::uintptr_t kMarriageFinalizeInteractionContextRva = 0x3078C70;
inline constexpr std::uintptr_t kMarriageValidateInteractionContextRva = 0x307C020;
inline constexpr std::uintptr_t kMarriageDestroyInteractionContextRva = 0x3077380;
inline constexpr std::uintptr_t kMarriageRecipientInteractionAnswerScoreRva = 0x307C440;
inline constexpr std::uintptr_t kMarriageIntermediaryInteractionAnswerScoreRva = 0x307C340;
inline constexpr std::uintptr_t kMarriageInteractionCostEvaluatorRva = 0x310CEC0;
inline constexpr std::uintptr_t kMarriageInteractionTriggerEvaluatorRva = 0x372DF10;
inline constexpr std::uintptr_t kFamilyEvaluateAnswerRva = 0x307BC60;
inline constexpr std::uintptr_t kFamilySetBooleanOptionRva = 0x30788C0;
inline constexpr std::uintptr_t kFamilyBreakDatabaseGetterRvaV1 = 0x89DA60;
inline constexpr std::uintptr_t kFamilyBreakStableHashRvaV1 = 0x3F7E220;
inline constexpr std::uintptr_t kFamilyBreakLookupDefinitionRvaV1 = 0xA055E0;
inline constexpr std::uintptr_t kFamilyBreakMissingDefinitionSlotRvaV1 = 0x5D1DD28;
// The frameless tier entry is rooted in the actual score-filter call operand,
// HIGHEST-TIER-FRAMELESS-MAP.json; no global address shift was inferred.
inline constexpr std::uintptr_t kFamilyHighestTierRva = 0x28AC690;
inline constexpr std::uintptr_t kFamilyMatchmakerRva = 0x2B94CF0;
inline constexpr std::uintptr_t kFamilyCloseFamilyRva = 0x2912080;
inline constexpr std::uintptr_t kFamilyCloseOrExtendedFamilyRva = 0x2912270;
inline constexpr std::uintptr_t kFamilyTraitFlagRva = 0x2BB0E90;
inline constexpr std::uintptr_t kFamilyYieldsAllianceRva = 0x2C7C630;
inline constexpr std::uintptr_t kFamilyRiteParameterSetContainsRva = 0xB9DE80;

// Unique sibling receipts: actual4-projection-map/PROJECTION-MAPPING.json and
// actual4-heir-lineage/function-map + constructor-map/FAMILY-MAP.json.
inline constexpr std::uintptr_t kFamilyProjectionPairWrapperRva = 0x2505550;
inline constexpr std::uintptr_t kFamilyProjectionPairGeneratorRva = 0x2C7C480;
inline constexpr std::uintptr_t kFamilyProjectionOwnerVtableRva = 0x454E6F8;
inline constexpr std::uintptr_t kFamilyProjectionReadOptionRva = 0x3078860;
inline constexpr std::uintptr_t kFamilyProjectionSetOptionRva = 0x30788C0;
inline constexpr std::uintptr_t kFamilyProjectionIsAlliedRva = 0x2911DD0;
inline constexpr std::uintptr_t kFamilyFertilityGateRva = 0x28BB4C0;
// Exact actual4 CMP 1A3C871 RIP operand, signed QWORD; runtime value is read.
inline constexpr std::uintptr_t kFamilyCandidateFertilityFloorRva = 0x5C6A1B0;
// Actual4 1A3C8A2 RIP-resolves the signed DWORD upper-age operand.
inline constexpr std::uintptr_t kFamilyCandidateScorerAgeUpperRva = 0x5C6A1A8;
inline constexpr std::uintptr_t kNativeChildHousePreviewParentRva = 0x1375380;
inline constexpr std::uintptr_t kNativeMarriageMatchOfferVtableRva = 0x454E470;
// Shared actual4 collection ledger and parent producer/outcome DETAIL receipts.
inline constexpr std::uintptr_t kFamilyHouseStoreSlotRva = 0x5D1DAF0;
inline constexpr std::uintptr_t kFamilyHouseFallbackSlotRva = 0x5D1DAE8;
inline constexpr std::uintptr_t kFamilyDynastyStoreSlotRva = 0x5D1DE78;
inline constexpr std::uintptr_t kFamilyDynastyFallbackSlotRva = 0x5D1DE28;
inline constexpr std::uintptr_t kFamilyAdultThresholdZeroRva = 0x5C6A15C;
inline constexpr std::uintptr_t kFamilyAdultThresholdOneRva = 0x5C69D10;
inline constexpr std::uintptr_t kFamilyGrandWeddingOptionRva = 0x5D4C0B4;
inline constexpr std::uintptr_t kFamilyProjectionMatrilinealSlotRva = 0x5D4BDBC;

// Explicit actual4 branch for the existing projection reader. Prefixes and all
// eight table entries come from the unique projection/owner-table receipts.
inline bridge::MarriageCandidateAllianceProjectionFailureV1
ValidateFamilyProjectionBindingsV1(
    const ck3_12002::FamilyProjectionBindings &bindings) noexcept {
  using Failure = bridge::MarriageCandidateAllianceProjectionFailureV1;
  if (!bindings.exact_build_admitted ||
      bindings.admitted_executable_sha256 != kExecutableSha256 ||
      (!bindings.offline_fixture && bindings.module_base == 0))
    return Failure::exact_build_not_admitted;
  if (bindings.read_memory == nullptr || bindings.project_pairs == nullptr ||
      bindings.read_boolean_option == nullptr || bindings.is_allied == nullptr ||
      bindings.matrilineal_option_id_slot == 0 || bindings.native_owner_vtable == 0)
    return Failure::binding_unavailable;
  if (bindings.offline_fixture) return Failure::none;
  if (reinterpret_cast<std::uintptr_t>(bindings.project_pairs) !=
          bindings.module_base + kFamilyProjectionPairWrapperRva ||
      reinterpret_cast<std::uintptr_t>(bindings.read_boolean_option) !=
          bindings.module_base + kFamilyProjectionReadOptionRva ||
      reinterpret_cast<std::uintptr_t>(bindings.is_allied) !=
          bindings.module_base + kFamilyProjectionIsAlliedRva ||
      bindings.matrilineal_option_id_slot !=
          bindings.module_base + kFamilyProjectionMatrilinealSlotRva ||
      bindings.native_owner_vtable !=
          bindings.module_base + kFamilyProjectionOwnerVtableRva)
    return Failure::binding_unavailable;
  struct Signature {
    std::uintptr_t rva;
    std::array<std::uint8_t, 16> bytes;
  };
  constexpr std::array<Signature, 4> signatures{{
      {kFamilyProjectionPairWrapperRva,
       {0x40, 0x55, 0x48, 0x83, 0xEC, 0x30, 0x4C, 0x8B,
        0x05, 0x0B, 0x20, 0x76, 0x03, 0x48, 0x8B, 0xEA}},
      {kFamilyProjectionReadOptionRva,
       {0x4C, 0x8B, 0x09, 0x33, 0xC0, 0x4C, 0x8B, 0xD9,
        0x45, 0x8B, 0x91, 0x64, 0x22, 0x00, 0x00, 0x45}},
      {kFamilyProjectionIsAlliedRva,
       {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74,
        0x24, 0x18, 0x57, 0x48, 0x83, 0xEC, 0x20, 0x48}},
      {kFamilyProjectionPairGeneratorRva,
       {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C,
        0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57}},
  }};
  for (const auto &signature : signatures) {
    std::array<std::uint8_t, 16> actual{};
    if (!bindings.read_memory(bindings.memory_context,
            bindings.module_base + signature.rva, actual.data(), actual.size()) ||
        actual != signature.bytes)
      return Failure::signature_mismatch;
  }
  constexpr std::array<std::uintptr_t, 8> owner_entries{
      0xE56110, 0x855AB0, 0x8522C0, 0x855AA0,
      0x855AC0, 0x855AC0, 0x855AB0, 0x855AB0};
  std::array<std::uintptr_t, 8> actual{};
  if (!bindings.read_memory(bindings.memory_context, bindings.native_owner_vtable,
          actual.data(), sizeof(actual))) return Failure::signature_mismatch;
  for (std::size_t index = 0; index < actual.size(); ++index)
    if (actual[index] != bindings.module_base + owner_entries[index])
      return Failure::signature_mismatch;
  return Failure::none;
}

} // namespace xar::ck3_12004
