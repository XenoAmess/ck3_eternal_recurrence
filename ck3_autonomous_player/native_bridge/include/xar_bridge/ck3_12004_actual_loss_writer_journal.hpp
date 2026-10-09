#pragma once

#include "xar_bridge/army_actual_loss_writer_observations_v1.hpp"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kActualLossWriterRva12004 = 0x2634190;
inline constexpr std::uintptr_t kActualLossWriterDataSelectorRva12004 = 0x260DB50;
inline constexpr std::size_t kActualLossWriterPatchBytes12004 = 15;
inline constexpr std::size_t kActualLossWriterAbsoluteJumpBytes12004 = 14;

using ActualLossWriterOriginalV1 = void(__fastcall *)(void *, std::int64_t);
using ActualLossWriterPhysicalSelectorV1 = void *(__fastcall *)(void *);
using ActualLossWriterReadMemoryV1 = bool (*)(void *context, const void *address,
                                            void *output, std::size_t size) noexcept;
using ActualLossWriterVirtualAllocV1 = void *(*)(void *context, std::size_t size,
                                                DWORD allocation_type,
                                                DWORD protection) noexcept;
using ActualLossWriterVirtualFreeV1 = bool (*)(void *context, void *address,
                                              std::size_t size, DWORD type) noexcept;
using ActualLossWriterVirtualProtectV1 = bool (*)(void *context, void *address,
                                                 std::size_t size, DWORD protection,
                                                 DWORD &old) noexcept;
using ActualLossWriterFlushV1 = bool (*)(void *context, const void *address,
                                        std::size_t size) noexcept;

struct ActualLossWriterJournalBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void **game_state_slot = nullptr;
  ActualLossWriterPhysicalSelectorV1 select_physical_slot = nullptr;
  // Fixture-local readers operate on a declared synthetic graph; no wire setter.
  void *read_context = nullptr;
  ActualLossWriterReadMemoryV1 read_memory = nullptr;
};

struct ActualLossWriterJournalInstallEnvironmentV1 {
  bool primary_thread_suspended_proven = false;
  ActualLossWriterJournalBindingsV1 bindings{};
  std::uintptr_t writer_target_override = 0;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache_override = nullptr;
};

struct ActualLossWriterJournalDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t writer_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kActualLossWriterPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache = nullptr;
};

enum ActualLossWriterJournalInstallFailureV1 : std::uint32_t {
  actual_loss_install_none = 0,
  actual_loss_install_exact_build = 1U << 0,
  actual_loss_install_quiescence = 1U << 1,
  actual_loss_install_already_installed = 1U << 2,
  actual_loss_install_anchor = 1U << 3,
  actual_loss_install_allocation = 1U << 4,
  actual_loss_install_protection = 1U << 5,
  actual_loss_install_flush = 1U << 6,
  actual_loss_install_rollback = 1U << 7,
};

ActualLossWriterJournalBindingsV1 BindActualLossWriterJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallActualLossWriterJournal12004(
    ActualLossWriterJournalDetourStateV1 &state,
    const ActualLossWriterJournalInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept;
bool UninstallActualLossWriterJournal12004(
    ActualLossWriterJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept;

// Initializes bridge-owned storage and typed local callbacks only; no patch,
// executable read, native mutation or wire command is performed.
bool InitializeActualLossWriterJournalFixture12004(
    const ActualLossWriterJournalBindingsV1 &bindings,
    ActualLossWriterOriginalV1 original) noexcept;

game::ArmyActualLossWriterCallerV1 ClassifyActualLossWriterCallerV1(
    std::uint64_t caller_return_rva) noexcept;

// Nullopt before configured. This copies only owned events and joins full IDs
// to current query membership; it never resolves native objects or calls CK3.
std::optional<game::ArmyActualLossWriterObservationsV1>
ReadActualLossWriterObservations12004(
    std::span<const std::int32_t> current_full_regiment_ids) noexcept;

extern "C" void __fastcall XarActualLossWriterHook12004V1(
    void *regiment, std::int64_t request_raw) noexcept;

} // namespace xar::ck3_12004
