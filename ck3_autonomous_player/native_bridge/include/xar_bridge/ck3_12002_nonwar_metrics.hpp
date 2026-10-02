#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kCampaignRootMonthlyGoldIncomeRva = 0x2BCA960;
// Exact 1.20.0.3 resource-vector getter. Only its gold slot is projected.
inline constexpr std::uintptr_t kCampaignRootMaxMonthlyMaintenanceRva12003 =
    0x2C152D0;
inline constexpr std::uintptr_t kCampaignRootHealthRva = 0x28C6500;
inline constexpr std::uintptr_t kCampaignRootDomainSizeRva = 0x28B7200;
inline constexpr std::uintptr_t kCampaignRootDomainLimitRva = 0x28B71D0;
inline constexpr std::uintptr_t kCampaignRootHasTargetingFactionTriggerRva =
    0x2B250D0;
inline constexpr std::size_t kCampaignRootCharacterLandStateOffset12002 =
    0x1C0;
inline constexpr std::size_t kCampaignRootTargetingFactionCountOffset12002 =
    0x12C;
inline constexpr std::size_t kCampaignRootCharacterLegitimacyDataOffset12002 =
    0x1C8;
inline constexpr std::size_t kCampaignRootLegitimacyBalanceOffset12002 = 0x28;

struct NonwarMetricsProjection12002 {
  std::int64_t monthly_gold_income_raw = 0;
  std::int64_t health_raw = 0;
  std::int32_t domain_size = 0;
  std::int32_t domain_limit = 0;
  std::int32_t targeting_faction_count = 0;
  game::CampaignRootLegitimacyV1 legitimacy;
  game::CampaignRootMaxMonthlyGoldMaintenanceV1 max_monthly_gold_maintenance;

  friend bool operator==(const NonwarMetricsProjection12002 &,
                         const NonwarMetricsProjection12002 &) = default;
};

// Assigns only these migrated callbacks. Exact-build/thread/frame admission
// remains the enclosing campaign-root reader's responsibility.
void BindNonwarMetrics12002(
    ck3_11906::CampaignRootNativeEnvironmentV1 &environment,
    std::uintptr_t module_base) noexcept;

// Called only by the enclosing exact 1.20.0.3 descriptor branch; the .2
// metrics binder leaves this optional callback absent.
void BindNonwarFinance12003(
    ck3_11906::CampaignRootNativeEnvironmentV1 &environment,
    std::uintptr_t module_base) noexcept;

// Native output is ten int64 resource slots even though only gold slot zero
// is published. Missing/failed/negative reads remain optional diagnostics.
game::CampaignRootMaxMonthlyGoldMaintenanceV1
ReadOptionalMaxMonthlyGoldMaintenance12003(
    ck3_11906::NativeCampaignRootMaxMonthlyMaintenanceV1 function,
    void *character) noexcept;

// The caller supplies the already resolved played Character and retains its
// existing generation revalidation and paused two-sample equality check.
// Missing legitimacy is diagnostic and does not fail the required metrics.
bool ReadNonwarMetrics12002(
    const ck3_11906::CampaignRootNativeEnvironmentV1 &environment,
    const ck3_11906::CampaignRootAccessV1 &access, void *character,
    NonwarMetricsProjection12002 &output,
    std::string_view &failure) noexcept;

} // namespace xar::ck3_12002
