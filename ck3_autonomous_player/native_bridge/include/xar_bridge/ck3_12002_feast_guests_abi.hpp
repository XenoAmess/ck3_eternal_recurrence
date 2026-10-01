#pragma once

#include "xar_bridge/ck3_12002_feast_planner.hpp"

namespace xar::bridge {

// Native guest producers are versioned independently of their portable DTOs.
// The entries below are frozen in ck3_12002_feast_guests_abi.json.
inline std::uintptr_t ActivityFeastGuestRvaV1(
    std::string_view sha, std::uintptr_t legacy) noexcept {
  if (sha != kActivityPlanner12002ExeSha256V1) return legacy;
  switch (legacy) {
  case 0x4FE7EE0: return 0x54DBC00;
  case 0x570C130: return 0x5C67568;
  case 0x570C138: return 0x5C67570;
  case 0x570E068: return 0x5C68C50;
  case 0x57BFBA8: return 0x5D1E390;
  case 0x41205F0: return 0x45325C8;
  case 0x440E308: return 0x48BFE50;
  case 0x10B0A80: return 0x11B8350;
  case 0x10CDA10: return 0x11D8EC0;
  case 0x28CD180: return 0x2BBADE0;
  case 0x10AE220: return 0x11B5BE0;
  case 0x10AE286: return 0x11B5C46;
  case 0x10AE298: return 0x11B5C58;
  case 0x972827: return 0x9DFF87;
  case 0x9728CA: return 0x9E002A;
  case 0x10B0796: return 0x11B8066;
  case 0x10B07A3: return 0x11B8073;
  case 0x28D07A1: return 0x2BBE691;
  case 0x151CD75: return 0x165B655;
  case 0x28CF3A0: return 0x2BBD1B0;
  case 0x3380410: return 0x3765880;
  case 0x28CF51A: return 0x2BBD32A;
  case 0x10B0A61: return 0x11B8331;
  default: return legacy;
  }
}

inline std::size_t ActivityFeastGuestPlannerOffsetV1(
    std::string_view sha, std::size_t legacy) noexcept {
  if (sha != kActivityPlanner12002ExeSha256V1) return legacy;
  switch (legacy) {
  case 0x1530: return 0x1500;
  case 0x1538: return 0x1508;
  case 0x1550: return 0x1520;
  case 0x1578: return 0x15B0;
  case 0x1590: return 0x15C8;
  case 0x159C: return 0x15D4;
  case 0x1678: return 0x16B0;
  case 0x1684: return 0x16BC;
  case 0x1A18: return 0x1A50;
  case 0x1A24: return 0x1A5C;
  case 0x1A30: return 0x1A68;
  case 0x1AB0: return 0x1AE8;
  default: return legacy;
  }
}

bool InvokeActivityFeastNativePlannerGuestJoin12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner,
    std::uintptr_t character, std::int64_t &join_raw) noexcept;
std::uintptr_t InvokeActivityFeastNativePlannerActivity12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept;
bool InvokeActivityFeastNativeTravelDays12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t character,
    std::uintptr_t destination, std::int32_t &days) noexcept;

} // namespace xar::bridge
