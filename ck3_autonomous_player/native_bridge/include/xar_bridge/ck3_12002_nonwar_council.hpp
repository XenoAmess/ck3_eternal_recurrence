#pragma once

#include "xar_bridge/ck3_12002_campaign.hpp"

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kCampaignRootActiveCouncilTaskStorageSlotRva =
    0x5D1DEA0;
inline constexpr std::uintptr_t kCampaignRootActiveCouncilTaskFallbackSlotRva =
    0x5D1DDF8;
inline constexpr std::uintptr_t kCampaignRootCouncilActiveTaskIdsEnumeratorRva =
    0x2916CE0;
inline constexpr std::uintptr_t kCampaignRootCouncilPositionLookupRva =
    0x2684F00;
inline constexpr std::uintptr_t kCampaignRootCouncilValueProgressCurrentRva =
    0x31AB520;
inline constexpr std::uintptr_t kCampaignRootCouncilValueProgressMaximumRva =
    0x31AB840;

// CCharacter's landed owner extension is +0x1C0 in this exact build.
// It is distinct from the unlanded state pointer at +0x1B8.
inline constexpr std::size_t kNonwarCouncilCharacterExtensionOffset12002 = 0x1C0;
inline constexpr std::size_t kNonwarCouncilTaskIdsOffset12002 = 0x230;
inline constexpr std::size_t kNonwarCouncilTaskCountOffset12002 = 0x23C;

void BindNonwarCouncil12002(CampaignRootNativeEnvironmentV1 &environment,
                           std::uintptr_t module_base) noexcept;

// Called only inside the campaign query's application-main, paused-frame
// capture. The caller supplies the existing standard-government scope test.
bool ReadNonwarCouncilProjection12002(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access, void *character,
    std::int32_t character_id, bool standard_scope_admitted,
    game::CampaignRootCouncilV1 &output, std::string_view &failure) noexcept;

} // namespace xar::ck3_12002
