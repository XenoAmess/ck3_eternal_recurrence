#include "ck3_12002_construction.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <windows.h>

#include <array>

namespace xar::ck3_12002 {
namespace {

constexpr std::uintptr_t kStockPlayerCanConstructRva = 0x2C77D50;
constexpr std::uintptr_t kStockBuildingCostRva = 0x2C247C0;
constexpr std::size_t kBuildingCostContextOffset = 0x6F510;
constexpr std::size_t kBuildingCostFieldOffset = 0x6F518;

// Exact stock GUIPotentialBuildingItem.CanConstruct callback 0x12B3440 (and command validator 0x2982440) passes actor, Province, CBuildingType*, slot, true, null and
// consumes AL. This is the GUI's read-only final eligibility predicate.
using StockPlayerCanConstructV1 = bool (*)(
    std::int32_t, std::int32_t, const void *, std::int32_t, bool,
    const void *);

using StockBuildingCostV1 = std::int64_t *(*)(
    std::int64_t *output, const void *province,
    const void *building_cost_field, const void *building_context,
    const void *actor_character);

bool ReadStockPlayerCostV1(
    void *context, std::int32_t actor_character_id,
    std::int32_t province_id, std::uintptr_t province,
    std::int32_t building_type_id, std::uintptr_t building_definition,
    std::int32_t slot_index,
    std::array<std::int64_t, 10> &cost_raw_native) noexcept {
  const auto *access =
      static_cast<const PlayerWorldBuildingNativeCallAccessV1 *>(context);
  cost_raw_native = {};
  if (access == nullptr || !access->exact_build_admitted ||
      access->module_base == 0 || actor_character_id <= 0 ||
      province_id <= 0 || province == 0 || building_type_id < 0 ||
      building_definition == 0 || slot_index < 0) {
    return false;
  }
  auto *stock = reinterpret_cast<StockBuildingCostV1>(
      access->module_base + kStockBuildingCostRva);
#if defined(_MSC_VER)
  __try {
#endif
    if (*reinterpret_cast<const std::int32_t *>(province + 0x10) !=
            province_id ||
        *reinterpret_cast<const std::int32_t *>(
            building_definition + 0x10) != building_type_id) {
      return false;
    }
    const auto core=BindCoreImage(access->module_base,kExecutableSha256);
    const auto *actor=ResolveCoreCharacter(core,actor_character_id);
    if(actor==nullptr) return false;
    const auto building_context =
        *reinterpret_cast<const std::uintptr_t *>(
            building_definition + kBuildingCostContextOffset);
    if (stock(cost_raw_native.data(), reinterpret_cast<const void *>(province),
              reinterpret_cast<const void *>(
                  building_definition + kBuildingCostFieldOffset),
              reinterpret_cast<const void *>(building_context), actor) !=
        cost_raw_native.data()) {
      return false;
    }
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    cost_raw_native = {};
    return false;
  }
#endif
}

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

NativePlayerBuildingCostV1 BindCurrentProcessPlayerWorldBuildingCostV1(
    PlayerWorldBuildingNativeCallAccessV1 &access) noexcept {
  return access.module_base != 0 && access.exact_build_admitted
             ? &ReadStockPlayerCostV1
             : nullptr;
}

} // namespace xar::ck3_12002
