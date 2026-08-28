#pragma once

#include "xar_bridge/ck3_11906.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string_view>

#include <windows.h>

namespace xar::ck3_11906 {

inline constexpr std::string_view kTacticalDailySentinelCapabilityV1 =
    "game.command.research-arm-tactical-daily-sentinel-v1-N";
inline constexpr std::string_view kTacticalDailySentinelStatusCapabilityV1 =
    "game.command.research-query-tactical-daily-sentinel-v1";
inline constexpr std::string_view kTacticalDailySentinelStatusStepV1 =
    "research-query-tactical-daily-sentinel-v1";
inline constexpr std::string_view kTacticalDailySentinelArmPrefixV1 =
    "research-arm-tactical-daily-sentinel-v1-";

inline constexpr std::uintptr_t kDailyTickFinalStageRvaV1 = 0x26D3E80;
inline constexpr std::uintptr_t kSetPausedWrapperRvaV1 = 0x346B910;
inline constexpr std::size_t kDailyTickFinalStagePatchBytesV1 = 15;
inline constexpr std::size_t kTacticalDailySentinelAbsoluteJumpBytesV1 = 14;
inline constexpr std::size_t kTacticalDailySentinelMaximumArmiesV1 = 64;
inline constexpr std::size_t kTacticalDailySentinelMaximumCombatsV1 = 64;
// Longest canonical arm step: two positive int32 dates, speed, terminal mode,
// a two-digit count, and 64 positive int32 ArmyIDs including delimiters.
inline constexpr std::size_t kTacticalDailySentinelMaximumArmStepBytesV1 =
    kTacticalDailySentinelArmPrefixV1.size() + 10U + 4U + 10U + 7U + 1U +
    6U + 8U + 3U + 2U +
    kTacticalDailySentinelMaximumArmiesV1 * (1U + 10U);

enum TacticalDailySentinelTriggerV1 : std::uint32_t {
  tactical_daily_trigger_none = 0,
  tactical_daily_trigger_date_deadline = 1U << 0,
  tactical_daily_trigger_army_unavailable = 1U << 1,
  tactical_daily_trigger_route_target_changed = 1U << 2,
  tactical_daily_trigger_combat_transition = 1U << 3,
  tactical_daily_trigger_retreat_transition = 1U << 4,
  tactical_daily_trigger_combat_unavailable = 1U << 5,
  tactical_daily_trigger_combat_phase_changed = 1U << 6,
  tactical_daily_trigger_combat_roster_changed = 1U << 7,
  tactical_daily_trigger_combat_terminal = 1U << 8,
  tactical_daily_trigger_date_sequence_failure = 1U << 9,
  tactical_daily_trigger_world_identity_changed = 1U << 10,
  tactical_daily_trigger_pause_not_observed = 1U << 11,
  tactical_daily_trigger_original_unavailable = 1U << 12,
  tactical_daily_trigger_native_pause = 1U << 13,
  tactical_daily_trigger_combat_winner_changed = 1U << 14,
  tactical_daily_trigger_evaluation_failure = 1U << 15,
};

enum class TacticalDailySentinelModeV1 : std::uint32_t {
  decision_epoch = 1,
  terminal_or_sentinel = 2,
};

enum class TacticalDailySentinelStateV1 : std::uint32_t {
  unavailable = 0,
  idle = 1,
  armed = 2,
  triggered = 3,
  failed = 4,
};

enum class TacticalDailySentinelArmStatusV1 : std::uint32_t {
  armed = 0,
  invalid_request = 1,
  requires_paused = 2,
  starting_date_mismatch = 3,
  army_unavailable = 4,
  combat_unavailable = 5,
  already_armed = 6,
  unavailable = 7,
};

struct TacticalDailySentinelArmRequestV1 {
  std::int32_t starting_date_raw = 0;
  std::int32_t target_date_raw = 0;
  std::int32_t speed = 0;
  TacticalDailySentinelModeV1 mode =
      TacticalDailySentinelModeV1::decision_epoch;
  std::uint32_t army_count = 0;
  std::array<std::int32_t, kTacticalDailySentinelMaximumArmiesV1> army_ids{};

  friend bool operator==(const TacticalDailySentinelArmRequestV1 &,
                         const TacticalDailySentinelArmRequestV1 &) = default;
};

struct TacticalDailySentinelStatusV1 {
  TacticalDailySentinelStateV1 state =
      TacticalDailySentinelStateV1::unavailable;
  std::uint64_t generation = 0;
  std::int32_t starting_date_raw = 0;
  std::int32_t target_date_raw = 0;
  std::int32_t last_observed_date_raw = 0;
  std::int32_t trigger_date_raw = 0;
  std::int32_t speed = 0;
  TacticalDailySentinelModeV1 mode =
      TacticalDailySentinelModeV1::decision_epoch;
  std::uint32_t army_count = 0;
  std::uint32_t combat_count = 0;
  std::uint32_t completed_daily_ticks = 0;
  std::uint32_t intermediate_pause_count = 0;
  std::uint32_t trigger_flags = tactical_daily_trigger_none;
  std::int32_t signed_date_delta_from_target_raw = 0;
  std::int32_t overshoot_days = -1;
  bool pause_wrapper_called = false;
  bool pause_observed = false;
  bool terminal_observed = false;
  bool abnormal = false;

  friend bool operator==(const TacticalDailySentinelStatusV1 &,
                         const TacticalDailySentinelStatusV1 &) = default;
};

bool ParseTacticalDailySentinelArmStepV1(
    std::string_view step, TacticalDailySentinelArmRequestV1 &request) noexcept;

TacticalDailySentinelArmStatusV1 ArmTacticalDailySentinelV1(
    const TacticalDailySentinelArmRequestV1 &request) noexcept;

TacticalDailySentinelStatusV1 ReadTacticalDailySentinelStatusV1() noexcept;

// This exact post-day evaluator is exposed for deterministic native fixtures.
// Production reaches it only after the original final-stage function returns.
void ProcessTacticalDailySentinelAfterTickV1() noexcept;

using TacticalDailyOriginalV1 = void(__fastcall *)();
using TacticalSetPausedV1 = void(__fastcall *)(void *jomini_state, bool paused,
                                               std::int32_t player_id);

using TacticalSentinelVirtualAllocV1 = void *(*)(void *context,
                                                 std::size_t size,
                                                 DWORD allocation_type,
                                                 DWORD protection) noexcept;
using TacticalSentinelVirtualFreeV1 = bool (*)(void *context, void *address,
                                               std::size_t size,
                                               DWORD free_type) noexcept;
using TacticalSentinelVirtualProtectV1 =
    bool (*)(void *context, void *address, std::size_t size,
             DWORD new_protection, DWORD &old_protection) noexcept;
using TacticalSentinelFlushInstructionCacheV1 =
    bool (*)(void *context, const void *address, std::size_t size) noexcept;

enum TacticalDailySentinelInstallFailureV1 : std::uint32_t {
  tactical_daily_install_failure_none = 0,
  tactical_daily_install_failure_exact_build = 1U << 0,
  tactical_daily_install_failure_quiescence = 1U << 1,
  tactical_daily_install_failure_already_installed = 1U << 2,
  tactical_daily_install_failure_anchor = 1U << 3,
  tactical_daily_install_failure_allocation = 1U << 4,
  tactical_daily_install_failure_protection = 1U << 5,
  tactical_daily_install_failure_flush = 1U << 6,
  tactical_daily_install_failure_rollback = 1U << 7,
};

struct TacticalDailySentinelInstallEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  std::uintptr_t module_base = 0;
  Bindings bindings{};
  std::uintptr_t final_stage_target_override = 0;
  TacticalSetPausedV1 set_paused_override = nullptr;
  void *memory_context = nullptr;
  TacticalSentinelVirtualAllocV1 virtual_alloc_override = nullptr;
  TacticalSentinelVirtualFreeV1 virtual_free_override = nullptr;
  TacticalSentinelVirtualProtectV1 virtual_protect_override = nullptr;
  TacticalSentinelFlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct TacticalDailySentinelDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{tactical_daily_install_failure_none};
  std::uintptr_t final_stage_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kDailyTickFinalStagePatchBytesV1> original{};
  void *memory_context = nullptr;
  TacticalSentinelVirtualFreeV1 virtual_free = nullptr;
  TacticalSentinelVirtualProtectV1 virtual_protect = nullptr;
  TacticalSentinelFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

bool InstallTacticalDailySentinelV1(
    TacticalDailySentinelDetourStateV1 &state,
    const TacticalDailySentinelInstallEnvironmentV1 &environment) noexcept;

bool TacticalDailySentinelInstalledV1() noexcept;

// Offline fixture initializer: no executable bytes are patched and no CK3
// function is called. The supplied fixed memory graph is consumed by the same
// arming/evaluation path as production.
bool InitializeTacticalDailySentinelFixtureV1(
    const Bindings &bindings, TacticalSetPausedV1 set_paused,
    TacticalDailyOriginalV1 original = nullptr) noexcept;

extern "C" void __fastcall XarTacticalDailySentinelHookV1() noexcept;

} // namespace xar::ck3_11906
