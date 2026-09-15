#include "player_world_building_definition_source_v1_process.hpp"

#include <windows.h>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kStockPlayerCanConstructRva = 0x295CD60;

// Exact stock GUIPotentialBuildingItem.CanConstruct callback 0x11A6308..
// 0x11A632E passes actor, Province, CBuildingType*, slot, true, null and
// consumes AL. This is the GUI's read-only final eligibility predicate.
using StockPlayerCanConstructV1 = bool (*)(
    std::int32_t, std::int32_t, const void *, std::int32_t, bool,
    const void *);

bool ReadStockPlayerFinalLegalityV1(
    void *context, std::int32_t actor_character_id,
    std::int32_t province_id, std::uintptr_t building_definition,
    std::int32_t slot_index, bool &allowed) noexcept {
  const auto *access =
      static_cast<const PlayerWorldBuildingNativeCallAccessV1 *>(context);
  allowed = false;
  if (access == nullptr || !access->exact_build_admitted ||
      access->module_base == 0 || actor_character_id <= 0 ||
      province_id <= 0 || building_definition == 0 || slot_index < 0) {
    return false;
  }
  auto *stock = reinterpret_cast<StockPlayerCanConstructV1>(
      access->module_base + kStockPlayerCanConstructRva);
#if defined(_MSC_VER)
  __try {
    allowed = stock(actor_character_id, province_id,
                    reinterpret_cast<const void *>(building_definition),
                    slot_index, true, nullptr);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  allowed = stock(actor_character_id, province_id,
                  reinterpret_cast<const void *>(building_definition),
                  slot_index, true, nullptr);
  return true;
#endif
}

} // namespace

NativePlayerBuildingFinalLegalityV1
BindCurrentProcessPlayerWorldBuildingFinalLegalityV1(
    PlayerWorldBuildingNativeCallAccessV1 &access) noexcept {
  return access.module_base != 0 && access.exact_build_admitted
             ? &ReadStockPlayerFinalLegalityV1
             : nullptr;
}

} // namespace xar::ck3_11906
