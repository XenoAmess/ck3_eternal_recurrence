#pragma once

#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"
#include "xar_bridge/person_transfer_postimage_capture_12004.hpp"

#include <array>
#include <atomic>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

struct PersonSixStageQuery12004DTO;

inline constexpr std::string_view kPersonInstalledTransferCaptureSchema12004 =
    "xar.ck3.person-installed-transfer-capture-12004-v1";
inline constexpr std::string_view kPersonInstalledTransferCaptureExeSha12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::size_t kPersonInstalledTransferCapturePatchBytes12004 = 15;
inline constexpr std::size_t kPersonInstalledTransferCaptureCapacity12004 = 128;

enum PersonInstalledTransferCaptureFailure12004 : std::uint32_t {
  transfer_capture_none = 0,
  transfer_capture_exact_build = 1U << 0,
  transfer_capture_quiescence = 1U << 1,
  transfer_capture_already_installed = 1U << 2,
  transfer_capture_anchor = 1U << 3,
  transfer_capture_allocation = 1U << 4,
  transfer_capture_protection = 1U << 5,
  transfer_capture_flush = 1U << 6,
  transfer_capture_rollback = 1U << 7,
  transfer_capture_callback_active = 1U << 8,
  transfer_capture_memory_binding = 1U << 9,
};

struct PersonInstalledTransferCaptureInstall12004 {
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  // Production target is always module_base+291CF30. Override is fixture-only.
  std::uintptr_t target_override = 0;
  PersonInstalledTransferBindings12004 bindings;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_override = nullptr;
};

struct PersonInstalledTransferCaptureState12004 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kPersonInstalledTransferCapturePatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush = nullptr;
  DWORD original_target_protection = 0;
  bool target_protection_known = false;
};

struct PersonInstalledTransferCaptureRecord12004 {
  std::uint64_t record_sequence = 0; // Retention ordinal, not an event clock.
  bool offline_fixture = false;
  PersonInstalledTransferStage12004 stage;
  // Same original occurrence, owned before/return copies. Absence and each
  // independently partial operand remain distinct from a completed exchange.
  std::optional<PersonTransferPhysicalPostimage12004> physical_postimage;
};

struct PersonInstalledTransferCaptureQuery12004 {
  bool configured = false;
  bool installed = false;
  std::uint32_t install_failure_flags = 0;
  bool request_filtered = false;
  std::optional<std::uint64_t> snapshot_revision;
  std::optional<std::int64_t> observed_date_raw;
  std::size_t requested_receiver_count = 0;
  std::size_t unresolved_receiver_count = 0;
  std::uint64_t latest_record_sequence = 0;
  std::uint64_t overwritten_records = 0;
  std::vector<PersonInstalledTransferCaptureRecord12004> records;
};

// No getter or Game call: returns a fault-bounded reader, owned Native65
// history adapter and the shared clock only for the exact admitted image pin.
PersonInstalledTransferBindings12004 BindPersonInstalledTransferCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

bool InstallPersonInstalledTransferCapture12004(
    PersonInstalledTransferCaptureState12004 &,
    const PersonInstalledTransferCaptureInstall12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallPersonInstalledTransferCapture12004(
    PersonInstalledTransferCaptureState12004 &,
    bool primary_thread_suspended_proven) noexcept;

// Same dispatch used by the installed entry replacement and the new fixture.
// Original trampoline executes once. Records copy the original pre-B owner;
// they never call Complete, native getters or preparation/container helpers.
std::uintptr_t InvokePersonInstalledTransferCapture12004(
    void *a, void *b, std::uintptr_t original_return_address) noexcept;

PersonInstalledTransferCaptureQuery12004 ReadPersonInstalledTransferCapture12004();
// Uses only identities already resolved by the same paused native batch. An
// empty/unresolved batch never falls back to unfiltered global history.
PersonInstalledTransferCaptureQuery12004 CollectPersonInstalledTransferCaptureForOwners12004(
    const PersonSixStageQuery12004DTO &);
std::optional<PersonInstalledTransferCaptureRecord12004>
ReadPersonInstalledTransferCaptureForOwner12004(
    std::uintptr_t owner, std::uint32_t full_character_id);

// Standalone retained wire. Root embeds it in the native query response; this
// module does not claim existing public serializers already expose it.
std::string SerializePersonInstalledTransferCapture12004(
    const PersonInstalledTransferCaptureQuery12004 &);

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonInstalledTransferHook12004V1(void *a, void *b) noexcept;

} // namespace xar::ck3_12004
