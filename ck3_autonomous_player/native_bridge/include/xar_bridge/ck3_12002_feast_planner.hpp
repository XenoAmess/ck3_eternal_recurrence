#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

namespace xar::bridge {

inline constexpr std::string_view kActivityPlanner12002ExeSha256V1 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";

inline bool IsActivityPlanner12002V1(
    const ActivityPlannerDiagEnvironmentV1 &env) noexcept {
  return env.admitted_executable_sha256 == kActivityPlanner12002ExeSha256V1;
}

inline bool IsActivityPlannerSupportedBuildV1(
    const ActivityPlannerDiagEnvironmentV1 &env) noexcept {
  return IsActivityPlanner12002V1(env) ||
      env.admitted_executable_sha256 == kActivityPlannerDiagExeSha256V1;
}

// Version selection is semantic: these entries were recovered from the new
// image's RTTI, native getters and callers; there is no common RVA delta.
inline std::uintptr_t ActivityPlannerRvaV1(
    const ActivityPlannerDiagEnvironmentV1 &env,
    std::uintptr_t legacy_rva) noexcept {
  if (!IsActivityPlanner12002V1(env)) return legacy_rva;
  switch (legacy_rva) {
  case 0x570F7B8: return 0x5C6A520;
  case 0x4FE7EE0: return 0x54DBC00;
  case 0x570C130: return 0x5C67568;
  case 0x570C138: return 0x5C67570;
  case 0x501EF28: return 0x5514438;
  case 0x501EF50: return 0x5514460;
  case 0x40B1D30: return 0x44BC408;
  case 0x40AF630: return 0x44BA890;
  case 0x41205F0: return 0x45325C8;
  case 0x41206C8: return 0x45326A0;
  case 0x440E308: return 0x48BFE50;
  case 0x440E1D0: return 0x48BFD18;
  case 0x4166528: return 0x457A138;
  case 0x4166620: return 0x457A110;
  case 0x10AC480: return 0x11B2E30;
  case 0x1F30970: return 0x21603A0;
  case 0xAA33F0: return 0xB1F0A0;
  case 0x10AE180: return 0x11B5B30;
  case 0x10C8454: return 0x11D3404;
  case 0x3E631F4: return 0x4260E94;
  case 0x10AEAE0: return 0x11B64C0;
  case 0x971270: return 0x9DEA70;
  case 0x971370: return 0x9DEB70;
  case 0x10B0DA0: return 0x11B8670;
  case 0x10B1BD0: return 0x11B95D0;
  case 0x10ADFA0: return 0x11B5950;
  case 0x10AEC20: return 0x11B6550;
  case 0x10B1330: return 0x11B8CD0;
  case 0x10AF3D0: return 0x11B6C80;
  case 0x10AF6A0: return 0x11B6F50;
  case 0x570BE98: return 0x5C67208;
  case 0x57BFF28: return 0x5D1FB40;
  case 0x4FE3DB0: return 0x54D76F0;
  case 0x40DB298: return 0x44E6F38;
  case 0x80DCB0: return 0x878290;
  case 0xCAF920: return 0xD51E50;
  case 0xA79700: return 0xAF39E0;
  default: return legacy_rva;
  }
}

inline std::size_t ActivityPlannerObjectOffsetV1(
    const ActivityPlannerDiagEnvironmentV1 &env,
    std::size_t legacy_offset) noexcept {
  if (!IsActivityPlanner12002V1(env)) return legacy_offset;
  switch (legacy_offset) {
  case 0x78: return 0x60;
  case 0xD0: return 0xA0;
  case 0x1530: return 0x1500;
  case 0x1560: return 0x1598;
  case 0x156C: return 0x15A4;
  case 0x1578: return 0x15B0;
  case 0x1584: return 0x15BC;
  case 0x1AB0: return 0x1AE8;
  case 0x1AB4: return 0x1AEC;
  case 0x1AC0: return 0x1AF8;
  case 0x1AC8: return 0x1B00;
  case 0x1AD0: return 0x1B08;
  default: return legacy_offset;
  }
}

inline std::size_t ActivityPlannerTypeOffsetV1(
    const ActivityPlannerDiagEnvironmentV1 &env,
    std::size_t legacy_offset) noexcept {
  if (!IsActivityPlanner12002V1(env)) return legacy_offset;
  switch (legacy_offset) {
  case 0xA88: return 0x960;
  case 0x3C75: return 0x3BED;
  default: return legacy_offset;
  }
}

struct ActivityPlannerIdentityV1 {
  std::uintptr_t actor = 0;
  std::uintptr_t handler = 0;
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;
  std::int32_t stage = -1;
};

// Only caller-provided memory/frame callbacks are used; this helper never
// discovers a process. The production callback runs on application main.
// Handler slots +0x3C0 (planner) and +0x3D8 (HostView) are unchanged;
// new constructors install them at RVAs 0xB0AB48 and 0xB0AF25.
bool ResolveActivityPlannerIdentityV1(
    const ActivityPlannerDiagEnvironmentV1 &env,
    const ActivityPlannerDiagFrameV1 &expected,
    ActivityPlannerIdentityV1 &output) noexcept;

} // namespace xar::bridge
