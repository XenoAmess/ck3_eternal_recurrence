#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "ck3_12002_construction.hpp"

namespace xar::ck3_12004 {
// These are unchanged software DTOs and memory/callback interfaces. Their
// introduction namespace does not choose a native executable or image binder.
using ck3_12002::CampaignRootAccessV1;
using ck3_12002::PlayerHeldConstructionModelStatusV1;
using ck3_12002::PlayerHeldConstructionModelFailureV1;
using ck3_12002::PlayerHeldHoldingSourceV1;
using ck3_12002::PlayerHeldConstructionModelResultV1;
using ck3_12002::PlayerHeldConstructionModelRequestV1;
using ck3_12002::PlayerWorldBuildingFailureV1;
using ck3_12002::PlayerWorldDefinitionIdentityStageV1;
using ck3_12002::PlayerWorldDefinitionIdentityDiagnosticV1;
using ck3_12002::PlayerWorldActiveConstructionV1;
using ck3_12002::PlayerWorldCompletedBuildingV1;
using ck3_12002::PlayerWorldBuildingLegalSampleV1;
using ck3_12002::PlayerWorldBuildingSourceResultV1;
using ck3_12002::PlayerWorldBuildingSourceAccessV1;
using ck3_12002::PlayerWorldBuildingSourceRequestV1;
using ck3_12002::PlayerWorldBuildingNativeCallAccessV1;
using ck3_12002::NativePlayerBuildingFinalLegalityV1;
using ck3_12002::NativePlayerBuildingCostV1;

// All image operands are actual .4 source mappings, not old-hash aliases.
inline constexpr std::uintptr_t kConstructionBuildingManagerSlotRva = 0x5C67540;
inline constexpr std::uintptr_t kConstructionNullDefinitionSlotRva = 0x5D1E320;
inline constexpr std::uintptr_t kConstructionDefinitionPrimaryVtableRva = 0x48B6CD8;
inline constexpr std::uintptr_t kConstructionFinalLegalityRva = 0x2C77D30;
inline constexpr std::uintptr_t kConstructionCostRva = 0x2C247A0;
inline constexpr std::int32_t kConstructionWorldLegalSampleBudgetV1 = 512;
inline constexpr std::uintptr_t kCampaignRootGameStateSlotRva = kGameStateSlotRva;
inline constexpr std::uintptr_t kCampaignRootJominiStateSlotRva = kJominiStateSlotRva;
inline constexpr std::uintptr_t kCampaignRootCharacterStorageSlotRva = kCharacterStorageSlotRva;
inline constexpr std::uintptr_t kCampaignRootCharacterFallbackSlotRva = 0x5C67570;
inline constexpr std::uintptr_t kCampaignRootLandedTitleStorageSlotRva = 0x5D1DAF8;
inline constexpr std::uintptr_t kCampaignRootLandedTitleFallbackSlotRva = 0x5D1DAE0;

struct ConstructionBindings12004 final {
  CoreBindings core{};
  std::uintptr_t module_base = 0;
  std::uintptr_t building_manager_slot = 0;
  std::uintptr_t null_definition_slot = 0;
  std::uintptr_t definition_primary_vtable = 0;
  std::uintptr_t stock_final_legality = 0;
  std::uintptr_t stock_building_cost = 0;
  bool enabled = false;
};

ConstructionBindings12004 BindConstructionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
PlayerHeldConstructionModelResultV1 ReadPlayerHeldConstructionModelSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const CampaignRootAccessV1 &access,
    const PlayerHeldConstructionModelRequestV1 &request) noexcept;
PlayerWorldBuildingSourceResultV1 ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const PlayerWorldBuildingSourceAccessV1 &access,
    const PlayerWorldBuildingSourceRequestV1 &request) noexcept;
NativePlayerBuildingFinalLegalityV1 BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1 &access) noexcept;
NativePlayerBuildingCostV1 BindCurrentProcessPlayerWorldBuildingCostV1(
    PlayerWorldBuildingNativeCallAccessV1 &access) noexcept;
} // namespace xar::ck3_12004
