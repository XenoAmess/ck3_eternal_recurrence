#include "xar_bridge/ck3_12004_prisoner_war_retention.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/ck3_12004_world.hpp"

namespace xar::ck3_12004 {

ck3_12002::PrisonerWarRetentionBindings BindPrisonerWarRetentionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_12002::PrisonerWarRetentionBindings result{};
  if (!image_base || executable_sha256 != kExecutableSha256) return result;
  result.core = xar::ck3_12004::BindCoreImage(image_base, executable_sha256);
  result.world = BindWorldImage12004(image_base, executable_sha256);
  result.titles = BindProvinceImage12004(image_base, executable_sha256);
  result.primary_title =
      reinterpret_cast<ck3_12002::WarRetentionCharacterGetter12002>(
          image_base + kWarRetentionPrimaryTitleRva12004);
  result.imprisoned_by =
      reinterpret_cast<ck3_12002::WarRetentionCharacterGetter12002>(
          image_base + kWarRetentionImprisonedByRva12004);
  result.enabled = result.core.enabled && result.world.enabled &&
      result.titles.enabled;
  return result;
}

} // namespace xar::ck3_12004
