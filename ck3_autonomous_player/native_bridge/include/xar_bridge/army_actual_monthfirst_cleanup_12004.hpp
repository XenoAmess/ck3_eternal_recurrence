#pragma once

#define XAR_ARMY_ACTUAL_MONTHFIRST_CLEANUP_12004 1

#include "xar_bridge/army_natural_phase_scope_12004.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kArmyActualMonthfirstCleanupRva12004 = 0x2A98C90;
inline constexpr std::uintptr_t kArmyActualMonthfirstCleanupReturnRva12004 = 0x2A9A672;
inline constexpr std::size_t kArmyActualMonthfirstCleanupDisplacedBytes12004 = 19;
inline constexpr std::size_t kArmyActualMonthfirstCleanupMaximumRecords12004 = 256;
inline constexpr std::size_t kArmyActualMonthfirstCleanupJournalCapacity12004 = 32;

enum class ArmyActualMonthfirstCleanupSelection12004 : std::uint8_t {
  unavailable, registry_full_generation, native_fallback
};

struct ArmyActualMonthfirstCleanupSlot12004 {
  std::int32_t physical_index = 0;
  std::uintptr_t record_identity = 0;
  std::optional<std::uintptr_t> vtable_identity, slot0_target_identity;
  std::optional<bool> slot0_matches_known_mode0_source;
  std::optional<std::uint32_t> requested_regi_full_id, indexed_regi_full_id,
      selected_regi_full_id, selected_magic_14;
  std::optional<std::int32_t> ordinal;
  ArmyActualMonthfirstCleanupSelection12004 selection =
      ArmyActualMonthfirstCleanupSelection12004::unavailable;
  std::optional<std::uintptr_t> selected_regi_identity, computed_chunk_identity;
  std::optional<bool> selected_regi_valid;
  std::optional<std::uint64_t> date_1c_raw64;
  bool complete = false;
  std::string unavailable_reason;
};

struct ArmyActualMonthfirstCleanupFrame12004 {
  std::uintptr_t primary_manager_identity = 0, header_identity = 0,
      passed_date_pointer_identity = 0;
  std::optional<std::uint64_t> passed_date_raw64;
  std::optional<std::uintptr_t> buffer_identity;
  std::optional<std::int32_t> live_count_raw_i32;
  std::size_t copied_physical_extent = 0;
  bool header_complete = false, physical_copy_complete = false, complete = false;
  bool truncated = false;
  // false at return when the original buffer cannot be joined by address.
  // A changed buffer's actual live slots can still be independently copied.
  std::optional<bool> original_backing_address_preserved;
  std::vector<ArmyActualMonthfirstCleanupSlot12004> physical_slots;
  std::string unavailable_reason;
};

struct ArmyActualMonthfirstCleanupRecord12004 {
  std::uint64_t journal_ordinal = 0;
  std::uintptr_t actual_entry_rva = kArmyActualMonthfirstCleanupRva12004;
  std::uintptr_t caller_return_rva = 0;
  bool source_call_admitted = false;
  std::optional<bool> saved_mask02_admitted_by_literal_call;
  ArmyNaturalPhaseScope12004 phase;
  ArmyNaturalPhaseEvent12004 before_event, before_copied_event,
      returned_event, after_copied_event;
  ArmyActualMonthfirstCleanupFrame12004 before, after;
  bool original_called = false, original_returned = false;
  std::optional<std::uintptr_t> raw_return_bits;
  std::optional<bool> same_clock_thread_order, phase_date_matches_passed_date;
  std::uint32_t capture_failure_flags = 0;
};

struct ArmyActualMonthfirstCleanupJournal12004 {
  bool observer_installed = false, owned_copy_complete = true;
  std::uint64_t oldest_available_ordinal = 0, latest_ordinal = 0,
      overwritten_records = 0, unattributed_invocations = 0, dropped_record_copies = 0;
  std::vector<ArmyActualMonthfirstCleanupRecord12004> events;
};

struct ArmyActualMonthfirstCleanupBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ArmyNaturalPhaseRead12004 read = nullptr;
  void *event_context = nullptr;
  ArmyNaturalPhaseEventReader12004 next_event = nullptr;
};

#if defined(_MSC_VER)
using ArmyActualMonthfirstCleanupOriginal12004 =
    std::uintptr_t(__fastcall *)(void *, const void *);
#else
using ArmyActualMonthfirstCleanupOriginal12004 =
    std::uintptr_t (*)(void *, const void *);
#endif

ArmyActualMonthfirstCleanupBindings12004 BindArmyActualMonthfirstCleanup12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// The original is forwarded once outside observation fault boundaries. RAX is
// opaque. Actual returned copies do not invoke a conditional cleanup predictor.
ArmyActualMonthfirstCleanupRecord12004 InvokeArmyActualMonthfirstCleanup12004(
    const ArmyActualMonthfirstCleanupBindings12004 &, ArmyActualMonthfirstCleanupOriginal12004,
    void *primary_manager, const void *passed_date, std::uintptr_t caller_return_rva) noexcept;

ArmyActualMonthfirstCleanupJournal12004 ReadArmyActualMonthfirstCleanupJournal12004() noexcept;
void ClearArmyActualMonthfirstCleanupJournalFixture12004() noexcept;

using ArmyActualMonthfirstCleanupAlloc12004 =
    void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ArmyActualMonthfirstCleanupFree12004 =
    bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ArmyActualMonthfirstCleanupProtect12004 =
    bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ArmyActualMonthfirstCleanupFlush12004 =
    bool (*)(void *, const void *, std::size_t) noexcept;

struct ArmyActualMonthfirstCleanupInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ArmyActualMonthfirstCleanupBindings12004 bindings;
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ArmyActualMonthfirstCleanupAlloc12004 allocate = nullptr;
  ArmyActualMonthfirstCleanupFree12004 free = nullptr;
  ArmyActualMonthfirstCleanupProtect12004 protect = nullptr;
  ArmyActualMonthfirstCleanupFlush12004 flush = nullptr;
};

struct ArmyActualMonthfirstCleanupDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kArmyActualMonthfirstCleanupDisplacedBytes12004> original{};
  void *memory_context = nullptr;
  ArmyActualMonthfirstCleanupFree12004 free = nullptr;
  ArmyActualMonthfirstCleanupProtect12004 protect = nullptr;
  ArmyActualMonthfirstCleanupFlush12004 flush = nullptr;
};

enum ArmyActualMonthfirstCleanupInstallFailure12004 : std::uint32_t {
  cleanup_install_exact_build = 1U << 0,
  cleanup_install_quiescence = 1U << 1,
  cleanup_install_already_active = 1U << 2,
  cleanup_install_anchor = 1U << 3,
  cleanup_install_allocation = 1U << 4,
  cleanup_install_protection = 1U << 5,
  cleanup_install_flush = 1U << 6,
  cleanup_install_rollback = 1U << 7
};

bool InstallArmyActualMonthfirstCleanup12004(ArmyActualMonthfirstCleanupDetourState12004 &,
    const ArmyActualMonthfirstCleanupInstallEnvironment12004 &,
    std::string_view executable_sha256) noexcept;

// Process-lifetime installation/backing: Stop/DllMain never detach this hook or
// clear retained observations. Root's cold PrepareStartup owns the install.
extern "C" std::uintptr_t __fastcall XarArmyActualMonthfirstCleanupHook12004(
    void *primary_manager, const void *passed_date) noexcept;

} // namespace xar::ck3_12004
