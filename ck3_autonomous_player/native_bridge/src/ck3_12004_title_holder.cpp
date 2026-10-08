#include "xar_bridge/ck3_12004_title_holder.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/ck3_12004_title_map.hpp"

namespace xar::ck3_12004 {
namespace {
// Adopted actual4 FullCampaign environment and Core/Faction collection proof.
constexpr std::uintptr_t kCharacterFallbackSlotRva = 0x5C67570;
constexpr std::uintptr_t kImmediateLiegeRva = 0x28BFC50;
constexpr std::uintptr_t kTopLiegeRva = 0x28BFD80;
bool ReadTitleKey(const void *title, std::string &output) noexcept {
  return ReadLandedTitleStableKeyV1({}, title, output, true);
}
} // namespace

ck3_12003::TitleHolderBindingsV1 BindTitleHolderImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_12003::TitleHolderBindingsV1 bindings{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return bindings;
  bindings.provinces = BindProvinceImage12004(image_base, executable_sha256);
  if (!bindings.provinces.enabled) return bindings;
  bindings.character_storage_slot =
      reinterpret_cast<void **>(image_base + kCharacterStorageSlotRva);
  bindings.character_fallback_slot =
      reinterpret_cast<void **>(image_base + kCharacterFallbackSlotRva);
  bindings.immediate_liege =
      reinterpret_cast<decltype(bindings.immediate_liege)>(
          image_base + kImmediateLiegeRva);
  bindings.top_liege = reinterpret_cast<decltype(bindings.top_liege)>(
      image_base + kTopLiegeRva);
  bindings.read_title_key = &ReadTitleKey;
  bindings.enabled = true;
  return bindings;
}

} // namespace xar::ck3_12004
