#pragma once
#include "player_world_building_definition_source_v1.hpp"
#include "player_world_building_definition_source_v1_process.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
namespace xar::ck3_12002 {
using ck3_11906::PlayerHeldConstructionModelStatusV1;
using ck3_11906::PlayerHeldConstructionModelFailureV1;
using ck3_11906::PlayerHeldHoldingSourceV1;
using ck3_11906::PlayerHeldConstructionModelResultV1;
using ck3_11906::PlayerHeldConstructionModelRequestV1;
using ck3_11906::PlayerWorldBuildingFailureV1;
using ck3_11906::PlayerWorldDefinitionIdentityStageV1;
using ck3_11906::PlayerWorldDefinitionIdentityDiagnosticV1;
using ck3_11906::PlayerWorldActiveConstructionV1;
using ck3_11906::PlayerWorldCompletedBuildingV1;
using ck3_11906::PlayerWorldBuildingLegalSampleV1;
using ck3_11906::PlayerWorldBuildingSourceResultV1;
using ck3_11906::PlayerWorldBuildingSourceAccessV1;
using ck3_11906::PlayerWorldBuildingSourceRequestV1;
using ck3_11906::PlayerWorldBuildingNativeCallAccessV1;
using ck3_11906::NativePlayerBuildingFinalLegalityV1;
using ck3_11906::NativePlayerBuildingCostV1;
inline constexpr std::uintptr_t kConstructionBuildingManagerSlotRva=0x5C67540;
inline constexpr std::uintptr_t kConstructionDefinitionPrimaryVtableRva=0x48B6CC8;
inline constexpr std::uintptr_t kConstructionFinalLegalityRva=0x2C77D50;
inline constexpr std::uintptr_t kConstructionCostRva=0x2C247C0;
// R6 has 23 directly-held slots: the existing 19 valued keys need at most
// 437 checks/quotes. Keep the 512-check budget and retain its full quote set.
inline constexpr std::int32_t kConstructionWorldLegalSampleBudgetV1 = 512;
PlayerHeldConstructionModelResultV1 ReadPlayerHeldConstructionModelSourcesV1(
    std::uintptr_t module_base,bool exact_build_admitted,
    const CampaignRootAccessV1& access,const PlayerHeldConstructionModelRequestV1& request) noexcept;
PlayerWorldBuildingSourceResultV1 ReadPlayerWorldBuildingDefinitionSourcesV1(
    std::uintptr_t module_base,bool exact_build_admitted,
    const PlayerWorldBuildingSourceAccessV1& access,const PlayerWorldBuildingSourceRequestV1& request) noexcept;
NativePlayerBuildingFinalLegalityV1 BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1& access) noexcept;
NativePlayerBuildingCostV1 BindCurrentProcessPlayerWorldBuildingCostV1(
    PlayerWorldBuildingNativeCallAccessV1& access) noexcept;
} // namespace xar::ck3_12002
