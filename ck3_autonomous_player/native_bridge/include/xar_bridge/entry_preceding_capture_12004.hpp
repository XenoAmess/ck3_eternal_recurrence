#pragma once

#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <array>
#include <atomic>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kEntryPrecedingRva12004 = 0x2586EB0;
inline constexpr std::uintptr_t kEntryPrecedingReturnRva12004 = 0x247AB07;
inline constexpr std::string_view kEntryPrecedingExeSha12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::size_t kEntryPrecedingPatchBytes12004 = 15;
inline constexpr std::size_t kEntryPrecedingCapacity12004 = 128;
using EntryPrecedingOriginal12004 = std::uintptr_t (*)(void *);
using EntryPrecedingRead12004 =
    bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
using EntryPrecedingClock12004 = PersonInstalledTransferEvent12004 (*)(void *) noexcept;

struct EntryPrecedingBindings12004 {
  EntryPrecedingRead12004 read = nullptr;
  void *read_context = nullptr;
  EntryPrecedingClock12004 next_event = nullptr;
  void *event_context = nullptr;
};

enum EntryPrecedingFailure12004 : std::uint32_t {
  preceding_none = 0, preceding_exact_build = 1U << 0,
  preceding_quiescence = 1U << 1, preceding_already_installed = 1U << 2,
  preceding_anchor = 1U << 3, preceding_allocation = 1U << 4,
  preceding_protection = 1U << 5, preceding_flush = 1U << 6,
  preceding_rollback = 1U << 7, preceding_callback_active = 1U << 8,
  preceding_memory_binding = 1U << 9,
};

struct EntryPrecedingInstall12004 {
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t target_override = 0; // Fixture only.
  EntryPrecedingBindings12004 bindings;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_override = nullptr;
};
struct EntryPrecedingState12004 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kEntryPrecedingPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush = nullptr;
  DWORD original_target_protection = 0;
  bool target_protection_known = false;
};

struct EntryPrecedingRecord12004 {
  std::uint64_t record_sequence = 0; // Retention ordinal, not shared clock.
  std::uint64_t install_epoch = 0; // Installation lifetime, not outer invocation.
  bool offline_fixture = false;
  bool original_returned = false;
  bool identity_stable = false;
  std::uintptr_t combat_identity = 0;
  std::optional<std::uint32_t> combat_full_id_before;
  std::optional<std::uint32_t> combat_full_id_after;
  std::uintptr_t caller_return_rva = 0;
  std::uintptr_t caller_return_slot = 0; // Direct intrinsic observation.
  PersonInstalledTransferEvent12004 original_begin;
  PersonInstalledTransferEvent12004 original_completion;
  std::uintptr_t raw_return_bits = 0; // No semantic interpretation.
  std::optional<std::uint64_t> outer_invocation; // Absent actual outer entry.
};
struct EntryPrecedingCombatOwner12004 {
  std::uintptr_t combat_identity = 0;
  std::uint32_t full_combat_id = 0xFFFFFFFFU;
};
struct EntryPrecedingQuery12004 {
  bool configured = false;
  bool installed = false;
  bool request_filtered = false;
  std::uint32_t install_failure_flags = 0;
  std::uint64_t latest_record_sequence = 0;
  std::uint64_t overwritten_records = 0;
  std::vector<EntryPrecedingRecord12004> records;
};

EntryPrecedingBindings12004 BindEntryPrecedingCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool InstallEntryPrecedingCapture12004(EntryPrecedingState12004 &,
    const EntryPrecedingInstall12004 &, std::string_view executable_sha256) noexcept;
bool UninstallEntryPrecedingCapture12004(EntryPrecedingState12004 &,
    bool primary_thread_suspended_proven) noexcept;

// One naturally reached original call. Completion is published only after it
// returns. Caller stack token is supplied by the installed wrapper intrinsic.
std::uintptr_t InvokeEntryPrecedingCapture12004(void *combat,
    std::uintptr_t original_return_address,
    std::uintptr_t original_return_slot) noexcept;
std::optional<EntryPrecedingRecord12004>
ReadCurrentEntryPrecedingCompletion12004() noexcept;

// Source-ordered natural Side0/Side1 claims. This token is a completed
// preceding call in a directly observed caller stack slot, not a complete
// Combat outer invocation. Any wrong boundary/order invalidates it.
std::optional<EntryPrecedingRecord12004> ClaimEntryPrecedingForFinalSide12004(
    std::uint32_t side_index, std::uintptr_t actual_side,
    std::uintptr_t actual_return_rva, std::uintptr_t actual_return_slot,
    const PersonInstalledTransferEvent12004 &side_begin) noexcept;
EntryPrecedingQuery12004 ReadEntryPrecedingCapture12004();
EntryPrecedingQuery12004 CollectEntryPrecedingCaptureForCombats12004(
    std::span<const EntryPrecedingCombatOwner12004>);
std::string SerializeEntryPrecedingCapture12004(const EntryPrecedingQuery12004 &);

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarEntryPrecedingHook12004V1(void *combat) noexcept;

} // namespace xar::ck3_12004
