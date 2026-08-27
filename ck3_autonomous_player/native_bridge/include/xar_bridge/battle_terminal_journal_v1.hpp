#pragma once

#include "xar_bridge/ck3_11906.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::ck3_11906 {

inline constexpr std::uintptr_t kBattleTerminalFinalizerRvaV1 = 0x230A590;
inline constexpr std::uintptr_t kBattleWarscoreWriterRvaV1 = 0x222A5A0;
inline constexpr std::size_t kBattleTerminalFinalizerPatchBytesV1 = 19;
inline constexpr std::size_t kBattleWarscoreWriterPatchBytesV1 = 16;
inline constexpr std::size_t kBattleTerminalAbsoluteJumpBytesV1 = 14;
inline constexpr std::size_t kBattleTerminalJournalCapacityV1 = 4'096;
inline constexpr std::size_t kBattleTerminalMaximumSideCunitsV1 = 128;

enum BattleTerminalJournalCaptureFailureV1 : std::uint32_t {
  battle_terminal_capture_failure_none = 0,
  battle_terminal_capture_failure_memory = 1U << 0,
  battle_terminal_capture_failure_identity = 1U << 1,
  battle_terminal_capture_failure_bounds = 1U << 2,
  battle_terminal_capture_failure_reentry = 1U << 3,
};

struct BattleTerminalJournalEventV1 {
  std::uint64_t sequence = 0;
  std::int32_t observed_date_raw = 0;
  std::int32_t combat_id = -1;
  std::int32_t battle_result_id = -1;
  std::int32_t province_id = -1;
  bool suppress_normal_result_envelopes = false;
  std::int32_t phase_raw = -1;
  std::int32_t phase_day = -1;
  std::int32_t winner_raw = -1;
  bool finalized_before = false;
  std::uint8_t daily_guard_raw = 0;
  bool wipe_raw_observable = false;
  bool wipe_raw = false;
  std::int32_t attacker_primary_participant_character_id = -1;
  std::int32_t defender_primary_participant_character_id = -1;
  std::uint32_t attacker_public_cunit_count = 0;
  std::uint32_t defender_public_cunit_count = 0;
  std::array<std::int32_t, kBattleTerminalMaximumSideCunitsV1>
      attacker_public_cunit_ids_in_stored_order{};
  std::array<std::int32_t, kBattleTerminalMaximumSideCunitsV1>
      defender_public_cunit_ids_in_stored_order{};
  std::uint32_t capture_failure_flags =
      battle_terminal_capture_failure_none;
};

struct BattleWarscoreJournalEventV1 {
  std::uint64_t sequence = 0;
  std::int32_t observed_date_raw = 0;
  std::int32_t combat_id = -1;
  std::int32_t war_id = -1;
  std::int32_t war_battle_row_index = -1;
  std::int64_t battle_warscore_value_raw = 0;
  bool winner_is_war_attacker = false;
  bool combat_side0_is_war_attacker = false;
  std::uint32_t capture_failure_flags =
      battle_terminal_capture_failure_none;
};

enum class BattleTerminalJournalLookupStatusV1 : std::uint32_t {
  not_observed = 0,
  observed = 1,
  journal_gap = 2,
  invalid_cursor = 3,
  unavailable = 4,
};

struct BattleTerminalJournalLookupV1 {
  BattleTerminalJournalLookupStatusV1 status =
      BattleTerminalJournalLookupStatusV1::unavailable;
  std::uint64_t requested_after_sequence = 0;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  BattleTerminalJournalEventV1 event{};
};

enum class BattleWarscoreJournalLookupStatusV1 : std::uint32_t {
  not_observed = 0,
  observed = 1,
  journal_gap = 2,
  unavailable = 3,
};

struct BattleWarscoreJournalLookupV1 {
  BattleWarscoreJournalLookupStatusV1 status =
      BattleWarscoreJournalLookupStatusV1::unavailable;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  BattleWarscoreJournalEventV1 event{};
};

using BattleTerminalVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using BattleTerminalVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size,
    DWORD free_type) noexcept;
using BattleTerminalVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using BattleTerminalFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

enum BattleTerminalJournalInstallFailureV1 : std::uint32_t {
  battle_terminal_install_failure_none = 0,
  battle_terminal_install_failure_exact_build = 1U << 0,
  battle_terminal_install_failure_quiescence = 1U << 1,
  battle_terminal_install_failure_already_installed = 1U << 2,
  battle_terminal_install_failure_anchor = 1U << 3,
  battle_terminal_install_failure_allocation = 1U << 4,
  battle_terminal_install_failure_protection = 1U << 5,
  battle_terminal_install_failure_flush = 1U << 6,
  battle_terminal_install_failure_rollback = 1U << 7,
};

struct BattleTerminalJournalInstallEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  Bindings bindings{};
  std::uintptr_t terminal_target_override = 0;
  std::uintptr_t warscore_target_override = 0;
  void *memory_context = nullptr;
  BattleTerminalVirtualAllocV1 virtual_alloc_override = nullptr;
  BattleTerminalVirtualFreeV1 virtual_free_override = nullptr;
  BattleTerminalVirtualProtectV1 virtual_protect_override = nullptr;
  BattleTerminalFlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct BattleTerminalJournalDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      battle_terminal_install_failure_none};
  std::uintptr_t terminal_target = 0;
  std::uintptr_t warscore_target = 0;
  void *terminal_trampoline = nullptr;
  void *warscore_trampoline = nullptr;
  std::array<std::uint8_t, kBattleTerminalFinalizerPatchBytesV1>
      terminal_original{};
  std::array<std::uint8_t, kBattleWarscoreWriterPatchBytesV1>
      warscore_original{};
  void *memory_context = nullptr;
  BattleTerminalVirtualFreeV1 virtual_free = nullptr;
  BattleTerminalVirtualProtectV1 virtual_protect = nullptr;
  BattleTerminalFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

// Installation happens only while the managed launch still holds CK3's
// primary thread suspended.  The hooks merely observe natural native calls,
// invoke their original trampolines exactly once and never call either native
// entry as a query/effect.
bool InstallBattleTerminalJournalV1(
    BattleTerminalJournalDetourStateV1 &state,
    const BattleTerminalJournalInstallEnvironmentV1 &environment) noexcept;

bool BattleTerminalJournalInstalledV1() noexcept;

BattleTerminalJournalLookupV1 LookupBattleTerminalJournalV1(
    std::int32_t prior_combat_id,
    std::uint64_t after_terminal_sequence) noexcept;

BattleWarscoreJournalLookupV1 LookupBattleWarscoreJournalV1(
    std::int32_t combat_id) noexcept;

// Deterministic native fixture surface. It initializes only bridge-owned
// rings/bindings and executes the same bounded capture routine used by the
// detour; it does not patch or call a CK3 function.
bool InitializeBattleTerminalJournalStorageV1(
    const Bindings &bindings) noexcept;
bool CaptureBattleTerminalJournalEntryV1(
    void *combat, bool suppress_normal_result_envelopes) noexcept;

using BattleTerminalOriginalV1 = void(__fastcall *)(void *, bool);
using BattleWarscoreWriterOriginalV1 = void(__fastcall *)(void *, void *);

extern "C" void __fastcall XarBattleTerminalHookV1(
    void *combat, bool suppress_normal_result_envelopes) noexcept;
extern "C" void __fastcall XarBattleWarscoreWriterHookV1(
    void *war, void *combat) noexcept;

} // namespace xar::ck3_11906
