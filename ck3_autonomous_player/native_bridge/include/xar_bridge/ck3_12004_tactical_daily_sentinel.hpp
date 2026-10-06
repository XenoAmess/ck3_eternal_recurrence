#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"

namespace xar::ck3_12004 {

// Actual source uses in the complete named2A99DC0 ->2A99DA0 cache:
// CArmy+243, Combat+300 and public CUnit+507/+915. These are actual4
// reference addresses, rather than an admission of an older image binder.
inline constexpr std::uintptr_t kTacticalSentinelUnitStorageSlotRva12004 =
    0x5D1E380;
inline constexpr std::uintptr_t kTacticalSentinelArmyStorageSlotRva12004 =
    0x5D1DE48;
inline constexpr std::uintptr_t kTacticalSentinelCombatStorageSlotRva12004 =
    0x5D1DE70;
inline constexpr std::uintptr_t kTacticalSentinelFinalStageRva12004 =
    0x2988FB0;
inline constexpr std::uintptr_t kTacticalSentinelSetPausedWrapperRva12004 =
    0x383E3E0;

// Existing collector member roles. Owner and commander are distinct from
// the CUnit/CArmy identity pair; a synthetic watched graph uses these roles.
inline constexpr std::size_t kTacticalSentinelUnitIdOffset12004 = 0x10;
inline constexpr std::size_t kTacticalSentinelUnitKindOffset12004 = 0x18;
inline constexpr std::size_t kTacticalSentinelUnitDirectTargetOffset12004 = 0x30;
inline constexpr std::size_t kTacticalSentinelUnitRetreatOffset12004 = 0x170;
inline constexpr std::size_t kTacticalSentinelUnitOwnerOffset12004 = 0x174;
inline constexpr std::size_t kTacticalSentinelUnitInternalArmyIdOffset12004 =
    0x178;
inline constexpr std::size_t kTacticalSentinelInternalArmyIdOffset12004 = 0x10;
inline constexpr std::size_t kTacticalSentinelInternalArmyCommanderOffset12004 =
    0x120;
inline constexpr std::size_t kTacticalSentinelInternalArmyUnitIdOffset12004 =
    0x124;
inline constexpr std::size_t kTacticalSentinelInternalArmyCombatIdOffset12004 =
    0x128;

// Reuses only the established software Bindings DTO. All native addresses are
// admitted under the actual4 SHA and Core profile; no old SHA is substituted.
ck3_11906::Bindings BindTacticalDailySentinelImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Synthetic memory/callbacks use the genuine existing Arm/Cancel/evaluator.
// A fixture passes the actual4-created binding graph, replacing only its raw
// object slots and native callback receivers with the declared synthetic graph.
bool InitializeTacticalDailySentinelFixture12004(
    const ck3_11906::Bindings &bindings, std::string_view executable_sha256,
    ck3_11906::TacticalSetPausedV1 set_paused,
    ck3_11906::TacticalDailyOriginalV1 original = nullptr) noexcept;

// The actual4 post body retains the existing fifteen-byte patch anchor.
// Native target/pause defaults are explicit actual4 source-mapped addresses;
// caller-owned memory/fixture overrides and the software installer are reused.
bool InstallTacticalDailySentinel12004(
    ck3_11906::TacticalDailySentinelDetourStateV1 &state,
    const ck3_11906::TacticalDailySentinelInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
