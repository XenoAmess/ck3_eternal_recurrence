#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003_default_raise_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_mercenary_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_mercenary_hire_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_assignment_mailbox.hpp"
#include <windows.h>
#include <utility>
#include <vector>
#include "xar_bridge/frontend_gui_route_v1.hpp"
#include "xar_bridge/steward_develop_county_candidates_v1.hpp"
#include "xar_bridge/projected_contact_scope_v1_serializer.hpp"

namespace xar::game {
namespace {
void ReplaceAll(std::string &value, std::string_view from, std::string_view to) {
  std::size_t at = 0;
  while ((at = value.find(from, at)) != std::string::npos) {
    value.replace(at, from.size(), to);
    at += to.size();
  }
}
} // namespace

const AdapterDescriptor &Ck3_12003AdapterDescriptor() noexcept {
  static const std::vector<std::string_view> capabilities = [] {
    const auto existing = Ck3_12002AdapterDescriptor().capabilities;
    std::vector<std::string_view> result(existing.begin(), existing.end());
    result.push_back(ck3_11906::kStewardDevelopCountyCandidatesV1Capability);
    result.push_back(ck3_12003::kArmyCommanderCandidatesCapability);
    result.push_back(ck3_12003::kPlayerDefaultRaiseCapabilityV1);
    result.push_back(ck3_12003::kPlayerMercenaryContextCapabilityV1);
    result.push_back(ck3_12003::kMercenaryHireCapabilityV1);
    result.push_back(kWarOccupationTargetsV1Capability);
    result.push_back(kTitleHolderV1Capability);
    result.push_back(kProjectedContactScopeV1Capability);
    result.push_back(ck3_12003::kArmyCommanderAssignmentCapability);
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1) && \
    defined(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
    // Restore the existing frontend tools for the migrated ordinary-seed route.
    result.push_back(ck3_11906::kFrontendGuiRouteV1Capability);
    result.push_back(ck3_11906::kFrontendGuiTreeInspectionV1Capability);
    result.push_back(ck3_11906::kGuiWindowTreeInspectionV1Capability);
    result.push_back(ck3_11906::kFrontendGuiOpenNewGameV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1)
    result.push_back(ck3_11906::kFrontendBookmarkModelProbeV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1)
    result.push_back(ck3_11906::kFrontendGuiSelectSupported1066CharacterV1Capability);
    result.push_back(ck3_11906::kFrontendGuiStartSelectedBookmarkV1Capability);
#endif
#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
    result.push_back(ck3_11906::kFrontendGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendOpenGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendGameRulesControlV1Capability);
    result.push_back(ck3_11906::kFrontendSelectGameRuleV1Capability);
    result.push_back(ck3_11906::kFrontendApplyGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendHideGameRulesV1Capability);
    result.push_back(ck3_11906::kFrontendAppliedGameRulesV1Capability);
#endif
    return result;
  }();
  static const AdapterDescriptor descriptor{
      ck3_12003::kAdapterId, ck3_12003::kGameVersion, ck3_12003::kExecutableSha256,
      ck3_12002::kCheckpointSaveName, capabilities};
  return descriptor;
}

Ck3_12003AdapterBindings BindCk3_12003AdapterImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  // core-comparison.json proves every production binding against this exact
  // .3 EXE. Reuse the reviewed layout without changing any .2 binder's gate.
  auto result = BindCk3_12002AdapterImage(image_base,
      executable_sha256 == ck3_12003::kExecutableSha256
          ? std::string_view(ck3_12002::kExecutableSha256) : std::string_view{});
  // These numeric GUI getter ABIs are closed only for exact .3. Do not install
  // them in BindArmyImage: that binder also serves the unchanged .2 adapter.
  if (result.armies.enabled) {
    result.armies.get_army_supply_capacity =
        reinterpret_cast<decltype(result.armies.get_army_supply_capacity)>(
            image_base + ck3_12002::kArmySupplyCapacityRva12003);
    result.armies.get_army_attrition_fraction =
        reinterpret_cast<decltype(result.armies.get_army_attrition_fraction)>(
            image_base + ck3_12002::kArmyAttritionFractionRva12003);
    result.armies.persistent_regiment_storage_slot = reinterpret_cast<void **>(
        image_base + ck3_12002::kPersistentRegimentStorageSlotRva12003);
    result.armies.can_regiment_replenish =
        reinterpret_cast<decltype(result.armies.can_regiment_replenish)>(
            image_base + ck3_12002::kRegimentCanReplenishRva12003);
    result.armies.can_chunk_replenish =
        reinterpret_cast<decltype(result.armies.can_chunk_replenish)>(
            image_base + ck3_12002::kChunkCanReplenishRva12003);
    result.armies.get_regiment_monthly_replenishment_fraction =
        reinterpret_cast<decltype(result.armies.get_regiment_monthly_replenishment_fraction)>(
            image_base + ck3_12002::kRegimentMonthlyReplenishmentRva12003);
    result.armies.get_army_monthly_supply_change =
        reinterpret_cast<decltype(result.armies.get_army_monthly_supply_change)>(
            image_base + ck3_12002::kArmyMonthlySupplyChangeRva12003);
    result.armies.get_army_gathering_days_left =
        reinterpret_cast<decltype(result.armies.get_army_gathering_days_left)>(
            image_base + ck3_12002::kArmyGatheringDaysLeftRva12003);
    result.armies.get_province_supply_limit =
        reinterpret_cast<decltype(result.armies.get_province_supply_limit)>(
            image_base + ck3_12002::kProvinceSupplyLimitRva12003);
    result.armies.get_province_supply_usage =
        reinterpret_cast<decltype(result.armies.get_province_supply_usage)>(
            image_base + ck3_12002::kProvinceSupplyUsageRva12003);
    result.armies.province_supply_character_fallback_slot =
        reinterpret_cast<void **>(
            image_base + ck3_12002::kCampaignRootCharacterFallbackSlotRva);
  }
  if (result.phase.advantage.enabled) {
    // Constructor-faith closure is proven only for exact .3. Keep the .2
    // binder's reviewed nonreligious contract unchanged.
    auto &religion = result.phase.advantage.constructor_religion;
    religion.enabled = true;
    religion.rite_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1E2F8);
    religion.faith_storage_slot = reinterpret_cast<void **>(image_base + 0x5D1E300);
    religion.null_rite_slot = reinterpret_cast<void **>(image_base + 0x5C67670);
    religion.null_faith_slot = reinterpret_cast<void **>(image_base + 0x5D1E2E0);
    religion.target_faith_is_unreformed =
        reinterpret_cast<decltype(religion.target_faith_is_unreformed)>(
            image_base + 0x2BD8960);
  }
  return result;
}

std::unique_ptr<GameAdapter> CreateCk3_12003Adapter(
    std::string_view executable_sha256) noexcept {
  return CreateCk3_12003AdapterFromBindings(BindCk3_12003AdapterImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)), executable_sha256));
}

std::string RenderCrozierBuildIdentity(
    std::string serialized, const AdapterDescriptor &descriptor) {
  if (IsCk3_12003Descriptor(descriptor)) {
    serialized = ck3_12002::RenderQueryBuildIdentity(std::move(serialized));
    // Includes typed DTO version fields, backend IDs, and versioned evidence
    // labels. Actual implementation source paths (ck3_12002*.cpp) stay true.
    for (const auto key : {"game_version", "exact_ck3_build", "exact_build",
                           "version", "build_version", "build"}) {
      ReplaceAll(serialized, std::string("\"") + key + "\":\"1.20.0.2\"",
                 std::string("\"") + key + "\":\"1.20.0.3\"");
    }
    for (const auto key : {"backend_id", "campaign_backend_id", "feature_backend_id"}) {
      ReplaceAll(serialized, std::string("\"") + key + "\":\"ck3-1.20.0.2-",
                 std::string("\"") + key + "\":\"ck3-1.20.0.3-");
    }
    ReplaceAll(serialized, "\"adapter_id\":\"ck3-1.20.0.2-msvc-x64\"",
                          "\"adapter_id\":\"ck3-1.20.0.3-msvc-x64\"");
    ReplaceAll(serialized, "\"schema\":\"ck3_12002_", "\"schema\":\"ck3_12003_");
    ReplaceAll(serialized, "\"played-character-event-icon-indicators-1.20.0.2-v1\"",
                          "\"played-character-event-icon-indicators-1.20.0.3-v1\"");
    ReplaceAll(serialized, std::string("\"") + ck3_12002::kExecutableSha256 + "\"",
                          std::string("\"") + ck3_12003::kExecutableSha256 + "\"");
    ReplaceAll(serialized,
        "\"ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d\"",
        "\"94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6\"");
  }
  return serialized;
}
} // namespace xar::game
