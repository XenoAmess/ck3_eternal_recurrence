#pragma once

#include "xar_bridge/ck3_12003_army_reserve.hpp"
#include "xar_bridge/ck3_12003_commander.hpp"
#include "xar_bridge/ck3_12003_commander_target_roll.hpp"

namespace xar::ck3_12004 {

// The names of the caller-owned DTOs retain their established lineage.
// Addresses and native receiver contracts are qualified for the actual .4 image.
inline constexpr std::uintptr_t kArmyDisembarkPenaltyDaysRva12004 = 0x24AA220;
inline constexpr std::uintptr_t kCommanderLandMovementRateRva12004 = 0x24AA920;
inline constexpr std::uintptr_t kCommanderNavalMovementRateRva12004 = 0x24AABE0;
inline constexpr std::uintptr_t kCommanderCurrentEdgeMovementRateRva12004 = 0x24AB5A0;
inline constexpr std::string_view kCommanderLandMovementRateRvaText12004 = "0x24AA920";
inline constexpr std::string_view kCommanderNavalMovementRateRvaText12004 = "0x24AABE0";
inline constexpr std::string_view kCommanderCurrentEdgeMovementRateRvaText12004 = "0x24AB5A0";

void PopulateArmySupportBindings12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    ck3_12002::ArmyBindings &bindings) noexcept;

ck3_12003::CommanderBindings BindCommanderImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

ck3_12003::PlayerArmyReserveBindingsV1 BindPlayerArmyReserveImage12004V1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Province and Combat are supplied by their actual .4 family owners. This
// wrapper never admits an old-image binder under a substituted hash.
ck3_12003::CommanderTargetRollBindings BindCommanderTargetRollImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ProvinceBindings &provinces,
    const ck3_12002::CombatBindings &combat) noexcept;

} // namespace xar::ck3_12004
