#pragma once

#include "xar_bridge/entry_final_side_scope_12004.hpp"
#include "xar_bridge/entry_final_writer_capture_12004.hpp"
#include "xar_bridge/entry_preceding_capture_12004.hpp"

#include <atomic>
#include <span>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kEntryFinalSideCaptureExeSha12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::size_t kEntryFinalSideCaptureCapacity12004 = 128;
using EntryFinalSideCaptureOriginal12004 =
    std::uintptr_t(__fastcall *)(void *, void *);
using EntryFinalSideCaptureClock12004 =
    PersonInstalledTransferEvent12004 (*)(void *) noexcept;
using EntryFinalSideCaptureClaim12004 =
    std::optional<EntryPrecedingRecord12004> (*)(
        std::uint32_t, std::uintptr_t, std::uintptr_t, std::uintptr_t,
        const PersonInstalledTransferEvent12004 &) noexcept;

struct EntryFinalSideCaptureBindings12004 {
  PersonInstalledTransferRead12004 read = nullptr;
  void *read_context = nullptr;
  EntryFinalSideCaptureClock12004 next_event = nullptr;
  void *event_context = nullptr;
  EntryFinalSideCaptureClaim12004 claim_preceding = nullptr;
  // Observer byte budget per bucket; never truncates a native count.
  std::size_t maximum_bucket_payload_bytes = 1024 * 1024;
};

enum EntryFinalSideCaptureFailure12004 : std::uint32_t {
  side_capture_none = 0, side_capture_exact_build = 1U << 0,
  side_capture_quiescence = 1U << 1, side_capture_already_installed = 1U << 2,
  side_capture_anchor = 1U << 3, side_capture_allocation = 1U << 4,
  side_capture_protection = 1U << 5, side_capture_flush = 1U << 6,
  side_capture_rollback = 1U << 7, side_capture_callback_active = 1U << 8,
  side_capture_memory_binding = 1U << 9,
};

struct EntryFinalSideCaptureInstall12004 {
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t target_override = 0;
  EntryFinalSideCaptureBindings12004 bindings;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_override = nullptr;
};

struct EntryFinalSideCaptureState12004 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, 20> original{};
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush = nullptr;
  DWORD original_target_protection = 0;
  bool target_protection_known = false;
};

struct EntryFinalSideCaptureRecord12004 {
  std::uint64_t record_sequence = 0;
  std::uint64_t install_epoch = 0;
  bool offline_fixture = false;
  EntryFinalSideScope12004 scope;
  std::optional<EntryPrecedingRecord12004> preceding;
  PersonInstalledTransferEvent12004 completed_event;
  bool original_called = false;
  bool original_returned = false;
  std::uintptr_t raw_return_bits = 0;
  std::vector<EntryFinalWriterCaptureRecord12004> writer_records;
  bool writer_retention_complete = true;
  std::optional<bool> writer_occurrences_cover_copied_slots;
  // This component never supplies an unobserved Combat outer invocation.
  std::optional<std::uint64_t> outer_invocation;
};

struct EntryFinalSideCaptureQuery12004 {
  bool configured = false;
  bool installed = false;
  bool request_filtered = false;
  std::uint32_t install_failure_flags = 0;
  std::uint64_t latest_record_sequence = 0;
  std::uint64_t overwritten_records = 0;
  std::uint64_t capture_retention_failures = 0;
  std::vector<EntryFinalSideCaptureRecord12004> records;
};

EntryFinalSideCaptureBindings12004 BindEntryFinalSideCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool InstallEntryFinalSideCapture12004(EntryFinalSideCaptureState12004 &,
    const EntryFinalSideCaptureInstall12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallEntryFinalSideCapture12004(EntryFinalSideCaptureState12004 &,
    bool primary_thread_suspended_proven) noexcept;

// Used by the installed thunk. Address and stack slot are intrinsic observations,
// not reconstructed from history. The original native ABI remains two arguments.
std::uintptr_t InvokeEntryFinalSideCapture12004(void *side, void *province,
    std::uintptr_t original_return_address,
    std::uintptr_t original_return_slot) noexcept;
EntryFinalSideCaptureQuery12004 ReadEntryFinalSideCapture12004();
EntryFinalSideCaptureQuery12004 CollectEntryFinalSideCaptureForCombats12004(
    std::span<const EntryPrecedingCombatOwner12004>);
std::string SerializeEntryFinalSideCapture12004(
    const EntryFinalSideCaptureQuery12004 &);

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarEntryFinalSideCaptureHook12004V1(void *side, void *province) noexcept;

} // namespace xar::ck3_12004
