#pragma once

#include "xar_bridge/ck3_12002_war_entry.hpp"
#include "xar_bridge/ck3_12003_war_occupation.hpp"
#include "xar_bridge/battle_current_warscore_caps_v1.hpp"
#include "xar_bridge/ck3_12004.hpp"

namespace xar::ck3_12004 {

// Actual .4 complete function spans in war-map/first01/FAMILY-MAP.json.
// Actor State16 and assessment/network scratch objects retain their concrete
// member operands; existing caller-owned software shapes are reused.
inline constexpr std::uintptr_t kWarEntryAssessmentRva12004 = 0x1A23220;
inline constexpr std::uintptr_t kWarEntryActorStateBuilderRva12004 = 0x1A22D10;
inline constexpr std::uintptr_t kWarEntryNetworkCollectorRva12004 = 0x1A23FF0;
inline constexpr std::uintptr_t kWarEntryEffectiveTargetResolverRva12004 = 0x2C13440;
inline constexpr std::uintptr_t kWarEntryCharacterFallbackSlotRva12004 = 0x5C67570;
// supplement01 actual dependency getter RIP operands at offsets 4 and 75.
inline constexpr std::uintptr_t kWarEntryActorStateDependencySlotRva12004 = 0x5D1DD50;

ck3_12002::WarEntryNativeEnvironmentV1 BindWarEntryNativeEnvironment12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Existing production reader's domain validator seam. It compares the
// complete actual .4 environment and never enables fixture function overrides.
bool IsWarEntryNativeEnvironment12004(
    const ck3_12002::WarEntryNativeEnvironmentV1 &) noexcept;

// Uses the shared result DTO/serializer and emits the actual mapped .4
// function provenance. The existing .4 renderer owns outer build identity.
std::string SerializeWarEntryAssessments12004(
    const game::WarEntryAssessmentsV1 &);

// Actual .4 complete collector bodies and the selected general allocator
// use witness. World and Province bindings come from their .4 domain owners.
inline constexpr std::uintptr_t kWarOccupationContextRva12004 = 0x2C13820;
inline constexpr std::uintptr_t kWarOccupationCollectParticipantsRva12004 = 0x2C0D370;
inline constexpr std::uintptr_t kWarOccupationCollectTitlesRva12004 = 0x2BA0DA0;
inline constexpr std::uintptr_t kWarOccupationCountHoldingRva12004 = 0x2C0D590;
inline constexpr std::uintptr_t kWarOccupationLiegeRelatedRva12004 = 0x24977A0;
inline constexpr std::uintptr_t kWarOccupationContextFallbackSlotRva12004 = 0x5D1DE08;
inline constexpr std::uintptr_t kWarOccupationVectorAllocatorRva12004 = 0x54DEBB8;

ck3_12003::WarOccupationTargetsBindingsV1 BindWarOccupationTargets12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256,
    const ck3_12002::WorldBindings &actual_world,
    const ck3_12002::ProvinceBindings &actual_provinces) noexcept;

// Actual .4 magnitude helper 2868670 retains signed qword loads and its
// fixed representation. RIP targets are observed at offsets 932 and 942.
inline constexpr std::uintptr_t kWarAttackerWinnerCapRva12004 = 0x5C69B60;
inline constexpr std::uintptr_t kWarDefenderWinnerCapRva12004 = 0x5C69B58;
ck3_12002::BattleCurrentWarscoreCapsBindings12003
BindBattleCurrentWarscoreCaps12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
