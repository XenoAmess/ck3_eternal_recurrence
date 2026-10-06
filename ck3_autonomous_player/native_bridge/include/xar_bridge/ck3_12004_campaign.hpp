#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"

namespace xar::ck3_12004 {

// Shared software contracts; all native bindings are constructed for actual4.
using CampaignRootNativeEnvironmentV1 = ck3_12002::CampaignRootNativeEnvironmentV1;
using CampaignRootAccessV1 = ck3_12002::CampaignRootAccessV1;
using CampaignRootContextRequestV1 = ck3_12002::CampaignRootContextRequestV1;

CampaignRootNativeEnvironmentV1 BindCampaignRootNativeEnvironmentV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
game::ReadCampaignRootContextResultV1 ReadCampaignRootContextV1(
    const CampaignRootNativeEnvironmentV1 &environment,
    const CampaignRootAccessV1 &access,
    const CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output,
    ck3_12002::HeldTitlePartitionFailure12002 *failure_diagnostic = nullptr) noexcept;
std::string SerializeCampaignRootContextV1(
    const game::CampaignRootContextV1 &context);

} // namespace xar::ck3_12004
