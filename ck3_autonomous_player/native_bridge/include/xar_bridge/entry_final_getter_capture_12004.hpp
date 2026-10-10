#pragma once

#include "xar_bridge/person_installed_transfer_stage_12004.hpp"
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kEntryFinalGetterRva12004 = 0x26344A0;
inline constexpr std::uintptr_t kEntryFinalGetterWriterReturn12004 = 0x2657AF4;
inline constexpr std::array<std::uint8_t, 15> kEntryFinalGetterPrologue12004{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x10,
    0x57,0x48,0x83,0xEC,0x60};

// Exact existing CombatBindings::evaluate_regiment_stats_at_province ABI.
// RCX=resolved Regiment, RDX=output record, R8=actual Province, RAX=record.
using EntryFinalGetterOriginal12004 = void *(*)(void *, void *, void *);

struct EntryFinalGetterCaptureBindings12004 {
  bool exact_build_admitted = false;
  std::uintptr_t module_base = 0;
  void *read_context = nullptr;
  PersonInstalledTransferRead12004 read = nullptr;
  void *event_context = nullptr;
  PersonInstalledTransferEventReader12004 next_event = nullptr;
};

EntryFinalGetterCaptureBindings12004 BindEntryFinalGetterCapture12004(
    std::string_view build, std::string_view executable_sha256,
    std::uintptr_t module_base, PersonInstalledTransferRead12004 read,
    void *read_context, PersonInstalledTransferEventReader12004 next_event,
    void *event_context) noexcept;

// The installed hook passes its original trampoline and actual three arguments.
// This always forwards a nonnull original once. Capture is source-restricted to
// the genuine writer caller while its lexical EnterOriginal scope is active.
// No observation query invokes this getter, and no old arithmetic is emulated.
void *CaptureNaturalEntryFinalGetterReturn12004(
    const EntryFinalGetterCaptureBindings12004 &, EntryFinalGetterOriginal12004,
    void *actual_resolved_regiment, void *actual_output, void *actual_province,
    std::uintptr_t actual_caller_return_address);

// The owning 32c writer defines the copyable return record and validates Notify.
// The serializer reads that owned value only; it never reads native pointers.
struct EntryFinalGetterReturnedRecord12004;
std::string EntryFinalGetterReturnedRecordJson12004(
    const EntryFinalGetterReturnedRecord12004 &);

} // namespace xar::ck3_12004


namespace xar::ck3_12004 {
inline constexpr std::size_t kEntryFinalGetterTrampolineBytes12004 = 29;
enum EntryFinalGetterCaptureFailure12004 : std::uint32_t {
  getter_capture_none = 0, getter_capture_exact_build = 1U << 0,
  getter_capture_quiescence = 1U << 1, getter_capture_already_installed = 1U << 2,
  getter_capture_anchor = 1U << 3, getter_capture_allocation = 1U << 4,
  getter_capture_protection = 1U << 5, getter_capture_flush = 1U << 6,
  getter_capture_rollback = 1U << 7, getter_capture_callback_active = 1U << 8,
};
struct EntryFinalGetterCaptureInstall12004 {
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0, target_override = 0;
  EntryFinalGetterCaptureBindings12004 bindings;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_override = nullptr;
};
struct EntryFinalGetterCaptureState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t target = 0;
  void *trampoline = nullptr, *memory_context = nullptr;
  std::array<std::uint8_t, 15> original{};
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush = nullptr;
  DWORD original_target_protection = 0;
  bool target_protection_known = false;
};
EntryFinalGetterCaptureBindings12004 BindEntryFinalGetterCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool InstallEntryFinalGetterCapture12004(EntryFinalGetterCaptureState12004 &,
    const EntryFinalGetterCaptureInstall12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallEntryFinalGetterCapture12004(EntryFinalGetterCaptureState12004 &,
    bool primary_thread_suspended_proven) noexcept;
extern "C" __declspec(noinline) void *
XarEntryFinalGetterCaptureHook12004V1(void *regiment, void *output, void *province);
} // namespace xar::ck3_12004
