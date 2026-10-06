#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"

namespace xar::ck3_12004 {

// Only the existing internal gift route consumes this projection. It does not
// bind or publish the full campaign-root query or its unrelated readiness.
struct CampaignRootFactionBindings12004 {
  bool enabled = false;
  CoreBindings core{};
  void **character_fallback_slot = nullptr;
  void **title_storage_slot = nullptr;
  void **title_fallback_slot = nullptr;
  ck3_12002::NativeCampaignRootCharacterResolverV1 immediate_liege = nullptr;
  ck3_12002::NativeCampaignRootCharacterResolverV1 primary_title = nullptr;
};

CampaignRootFactionBindings12004 BindCampaignRootFactionImage12004(
    std::uintptr_t, std::string_view actual_executable_sha256) noexcept;
bool ReadCampaignRootFaction12004(
    const CampaignRootFactionBindings12004 &,
    const ck3_12002::CampaignRootAccessV1 &,
    const ck3_12002::CampaignRootContextRequestV1 &,
    game::CampaignRootContextV1 &) noexcept;

} // namespace xar::ck3_12004
