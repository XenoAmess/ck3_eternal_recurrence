#pragma once

#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPhysicalEntryWriterRva12004 = 0x2657AA0;
inline constexpr std::uintptr_t kPhysicalEntryWriterRegimentSlotRva12004 = 0x5D1F340;
inline constexpr std::size_t kPhysicalEntryWriterPatchBytes12004 = 16;
inline constexpr std::size_t kPhysicalEntryWriterTrampolineBytes12004 = 36;
using PhysicalEntryWriterOriginal12004 = std::uint64_t(__fastcall *)(void *, void *);

struct PhysicalEntryWritebackInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  KnightStatConsumptionBindings12004 bindings;
  std::uintptr_t writer_target_override = 0;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache_override = nullptr;
};
struct PhysicalEntryWritebackDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t writer_target = 0;
  void *writer_trampoline = nullptr;
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache = nullptr;
};

std::array<std::uint8_t, kPhysicalEntryWriterTrampolineBytes12004>
BuildPhysicalEntryWriterTrampoline12004(std::uintptr_t image_base) noexcept;
bool InstallPhysicalEntryWriteback12004(PhysicalEntryWritebackDetourState12004 &,
    const PhysicalEntryWritebackInstallEnvironment12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallPhysicalEntryWriteback12004(PhysicalEntryWritebackDetourState12004 &,
    bool primary_thread_suspended_proven) noexcept;
bool InitializePhysicalEntryWritebackFixture12004(PhysicalEntryWriterOriginal12004) noexcept;
std::uint64_t InvokePhysicalEntryWriter12004(void *entry, void *province) noexcept;
extern "C" __declspec(noinline) std::uint64_t __fastcall
XarPhysicalEntryWriterHook12004(void *entry, void *province) noexcept;
} // namespace xar::ck3_12004
