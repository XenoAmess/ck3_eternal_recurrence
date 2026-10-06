#pragma once

#include "xar_bridge/ck3_12002_feast_planner.hpp"
#include "xar_bridge/ck3_12004_activity_migration_v1.hpp"

namespace xar::bridge {

inline bool IsActivityFeastModernBuildV1(std::string_view sha) noexcept {
  return sha == kActivityPlanner12002ExeSha256V1 || IsActivity12004BuildV1(sha);
}

// An explicit callback context is the admitted SHA, borrowed for this call.
// Existing null-context callers keep their historical .2 binding.
inline std::string_view ActivityFeastNativeCallbackShaV1(void *opaque) noexcept {
  return opaque == nullptr ? kActivityPlanner12002ExeSha256V1
      : *static_cast<const std::string_view *>(opaque);
}

inline void *ActivityFeastNativeCallbackContextV1(
    const std::string_view &sha) noexcept {
  return const_cast<std::string_view *>(&sha);
}

// Native guest producers are versioned independently of their portable DTOs.
// The entries below are frozen in ck3_12002_feast_guests_abi.json.
inline std::uintptr_t ActivityFeastGuestRvaV1(
    std::string_view sha, std::uintptr_t legacy) noexcept {
  if (!IsActivityFeastModernBuildV1(sha)) return legacy;
  switch (legacy) {
  case 0x4FE7EE0: return Activity12004RvaV1(sha, 0x54DBC00);
  case 0x570C130: return Activity12004RvaV1(sha, 0x5C67568);
  case 0x570C138: return Activity12004RvaV1(sha, 0x5C67570);
  case 0x570E068: return Activity12004RvaV1(sha, 0x5C68C50);
  case 0x57BFBA8: return Activity12004RvaV1(sha, 0x5D1E390);
  case 0x41205F0: return Activity12004RvaV1(sha, 0x45325C8);
  case 0x440E308: return Activity12004RvaV1(sha, 0x48BFE50);
  case 0x10B0A80: return Activity12004RvaV1(sha, 0x11B8350);
  case 0x10CDA10: return Activity12004RvaV1(sha, 0x11D8EC0);
  case 0x28CD180: return Activity12004RvaV1(sha, 0x2BBADE0);
  case 0x10AE220: return Activity12004RvaV1(sha, 0x11B5BE0);
  case 0x10AE286: return Activity12004RvaV1(sha, 0x11B5C46);
  case 0x10AE298: return Activity12004RvaV1(sha, 0x11B5C58);
  case 0x972827: return Activity12004RvaV1(sha, 0x9DFF87);
  case 0x9728CA: return Activity12004RvaV1(sha, 0x9E002A);
  case 0x10B0796: return Activity12004RvaV1(sha, 0x11B8066);
  case 0x10B07A3: return Activity12004RvaV1(sha, 0x11B8073);
  case 0x28D07A1: return Activity12004RvaV1(sha, 0x2BBE691);
  case 0x151CD75: return Activity12004RvaV1(sha, 0x165B655);
  case 0x28CF3A0: return Activity12004RvaV1(sha, 0x2BBD1B0);
  case 0x3380410: return Activity12004RvaV1(sha, 0x3765880);
  case 0x28CF51A: return Activity12004RvaV1(sha, 0x2BBD32A);
  case 0x10B0A61: return Activity12004RvaV1(sha, 0x11B8331);
  default: return legacy;
  }
}

inline std::size_t ActivityFeastGuestPlannerOffsetV1(
    std::string_view sha, std::size_t legacy) noexcept {
  if (!IsActivityFeastModernBuildV1(sha)) return legacy;
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

// The first parameter is optional const std::string_view* admitted SHA.
// nullptr selects historical .2; actual4 selects the finite mapped entry.
bool InvokeActivityFeastNativePlannerGuestJoin12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner,
    std::uintptr_t character, std::int64_t &join_raw) noexcept;
std::uintptr_t InvokeActivityFeastNativePlannerActivity12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept;
bool InvokeActivityFeastNativeTravelDays12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t character,
    std::uintptr_t destination, std::int32_t &days) noexcept;

} // namespace xar::bridge
