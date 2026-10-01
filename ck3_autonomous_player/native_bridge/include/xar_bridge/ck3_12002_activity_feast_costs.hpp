#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"

namespace xar::bridge {

inline constexpr std::string_view kActivityFeastCosts12002ExeSha256V1 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::uintptr_t kActivityCostRefresh12002RvaV1 = 0x11BA6D0;
inline constexpr std::uintptr_t kActivityCostSlot12Return12002RvaV1 = 0x11B5B5F;
inline constexpr std::uintptr_t kActivityGetCostByName12002RvaV1 = 0x310AE10;
inline constexpr std::uintptr_t kActivityGetCostIndexed12002RvaV1 = 0x310AEE5;
inline constexpr std::uintptr_t kActivityGoldLeaf12002RvaV1 = 0xC86146;

struct ActivityFeastCostLayoutV1 {
  std::uintptr_t refresh_rva;
  std::uintptr_t slot12_return_rva;
  std::uintptr_t planner_vtable_rva;
  std::uintptr_t type_vtable_rva;
  std::size_t owner_offset;
  std::size_t type_offset;
  std::size_t stage_offset;
  std::size_t breakdown_offset;
  std::size_t category_rows_offset;
  std::size_t category_count_offset;
  std::size_t option_rows_offset;
  std::size_t option_count_offset;
};

inline const ActivityFeastCostLayoutV1 *ActivityFeastCostLayoutForBuildV1(
    std::string_view sha) noexcept {
  static constexpr ActivityFeastCostLayoutV1 old_layout{
      kActivityCostRefreshRvaV1, kActivityCostSlot12ReturnRvaV1,
      0x41205F0, 0x440E308, 0xD0, 0x1530, 0x1AB0, 0x1AD8,
      0x1560, 0x156C, 0x1578, 0x1584};
  static constexpr ActivityFeastCostLayoutV1 new_layout{
      kActivityCostRefresh12002RvaV1, kActivityCostSlot12Return12002RvaV1,
      0x45325C8, 0x48BFE50, 0xA0, 0x1500, 0x1AE8, 0x1B10,
      0x1598, 0x15A4, 0x15B0, 0x15BC};
  if (sha == kActivityCostSlot12ExeSha256V1) return &old_layout;
  if (sha == kActivityFeastCosts12002ExeSha256V1) return &new_layout;
  return nullptr;
}

} // namespace xar::bridge
