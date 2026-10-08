#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

namespace xar::ck3_12004 {

// Actual .4 RIP operands and full native entry bodies are frozen in the
// Province profile receipt. The existing software DTO/readers remain shared;
// no .3 image binder is called to construct this profile.
inline constexpr std::uintptr_t kProvinceSiegeStorageSlotRva = 0x5D1EC88;
inline constexpr std::uintptr_t kProvinceUnitStorageSlotRva = 0x5D1E380;
inline constexpr std::uintptr_t kProvinceFallbackSlotRva = 0x5D1E390;
inline constexpr std::uintptr_t kObjectiveTitleStorageSlotRva = 0x5D1DAF8;
inline constexpr std::uintptr_t kCurrentBesiegingArmyGetterRva = 0x247DC00;

// An empty Army DTO still permits objective/occupation/fort and independent
// Siege reads. Callers that have the actual .4 Army profile pass that same
// profile for current unit/regiment eligibility and commander inputs.
ck3_12002::ProvinceBindings BindProvinceImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ArmyBindings &actual_armies = {}) noexcept;

} // namespace xar::ck3_12004
