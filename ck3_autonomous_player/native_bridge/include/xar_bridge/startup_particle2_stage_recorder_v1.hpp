#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
inline constexpr std::uintptr_t kStartupParticle2FactoryFunctionRvaV1 =
    0x3A866D0;

inline constexpr std::uintptr_t kStartupParticle2SourcePatchRvaV1 =
    0x3A86769;
inline constexpr std::uintptr_t kStartupParticle2SourceHealthyRvaV1 =
    0x3A8677A;
inline constexpr std::uintptr_t kStartupParticle2SourceNullRvaV1 =
    0x3A8690C;
inline constexpr std::size_t kStartupParticle2SourcePatchBytesV1 = 17;
inline constexpr std::size_t kStartupParticle2SourceStubBytesV1 = 56;

inline constexpr std::uintptr_t kStartupParticle2VariantPatchRvaV1 =
    0x3A867B0;
inline constexpr std::uintptr_t kStartupParticle2VariantNullRvaV1 =
    0x3A868DD;
inline constexpr std::size_t kStartupParticle2VariantPatchBytesV1 = 16;
inline constexpr std::size_t kStartupParticle2VariantStubBytesV1 = 38;

inline constexpr std::uintptr_t kStartupParticle2BackendPatchRvaV1 =
    0x3A867EC;
inline constexpr std::uintptr_t kStartupParticle2BackendNullRvaV1 =
    0x3A867FB;
inline constexpr std::size_t kStartupParticle2BackendPatchBytesV1 = 15;
inline constexpr std::size_t kStartupParticle2BackendStubBytesV1 = 42;

inline constexpr std::size_t kStartupParticle2StageRecorderStubBytesV1 =
    kStartupParticle2SourceStubBytesV1 +
    kStartupParticle2VariantStubBytesV1 +
    kStartupParticle2BackendStubBytesV1;
inline constexpr std::uint32_t kStartupParticle2SourcePatchMaskV1 = 1U << 0;
inline constexpr std::uint32_t kStartupParticle2VariantPatchMaskV1 = 1U << 1;
inline constexpr std::uint32_t kStartupParticle2BackendPatchMaskV1 = 1U << 2;
inline constexpr std::uint32_t kStartupParticle2AllPatchMaskV1 =
    kStartupParticle2SourcePatchMaskV1 |
    kStartupParticle2VariantPatchMaskV1 |
    kStartupParticle2BackendPatchMaskV1;
inline constexpr bool kStartupParticle2StageRecorderInstalledByDefaultV1 =
    false;

enum StartupParticle2StageRecorderFailureV1 : std::uint32_t {
  startup_particle2_stage_recorder_failure_none = 0,
  startup_particle2_stage_recorder_failure_exact_build = 1U << 0,
  startup_particle2_stage_recorder_failure_primary_thread_suspended = 1U << 1,
  startup_particle2_stage_recorder_failure_unsupported_override = 1U << 2,
  startup_particle2_stage_recorder_failure_already_installed = 1U << 3,
  startup_particle2_stage_recorder_failure_anchor = 1U << 4,
  startup_particle2_stage_recorder_failure_allocation = 1U << 5,
  startup_particle2_stage_recorder_failure_stub_protection = 1U << 6,
  startup_particle2_stage_recorder_failure_target_protection = 1U << 7,
  startup_particle2_stage_recorder_failure_target_identity = 1U << 8,
  startup_particle2_stage_recorder_failure_flush = 1U << 9,
  startup_particle2_stage_recorder_failure_rollback = 1U << 10,
};

using StartupParticle2StageVirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupParticle2StageVirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size,
    DWORD free_type) noexcept;
using StartupParticle2StageVirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupParticle2StageFlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

// Address and memory-operation overrides are an offline-test seam only.
// Production accepts only the frozen module base while the newly-created
// primary thread is still suspended.
struct StartupParticle2StageRecorderV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t source_patch_target_override = 0;
  std::uintptr_t source_healthy_target_override = 0;
  std::uintptr_t source_null_target_override = 0;
  std::uintptr_t variant_patch_target_override = 0;
  std::uintptr_t variant_null_target_override = 0;
  std::uintptr_t backend_patch_target_override = 0;
  std::uintptr_t backend_null_target_override = 0;

  void *memory_context = nullptr;
  StartupParticle2StageVirtualAllocV1 virtual_alloc_override = nullptr;
  StartupParticle2StageVirtualFreeV1 virtual_free_override = nullptr;
  StartupParticle2StageVirtualProtectV1 virtual_protect_override = nullptr;
  StartupParticle2StageFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable for the process lifetime after a
// successful install. Generated stubs embed the three atomic counter addresses.
struct StartupParticle2StageRecorderV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> patch_mask{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_particle2_stage_recorder_failure_none};
  alignas(8) std::atomic<std::uint64_t> source_lookup_null_count{0};
  alignas(8) std::atomic<std::uint64_t> variant_lookup_null_count{0};
  alignas(8) std::atomic<std::uint64_t> backend_creation_null_count{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t source_patch_target = 0;
  std::uintptr_t source_healthy_target = 0;
  std::uintptr_t source_null_target = 0;
  std::uintptr_t variant_patch_target = 0;
  std::uintptr_t variant_null_target = 0;
  std::uintptr_t backend_patch_target = 0;
  std::uintptr_t backend_null_target = 0;
  void *stub_allocation = nullptr;
  DWORD source_original_protection = 0;
  DWORD variant_original_protection = 0;
  DWORD backend_original_protection = 0;

  std::array<std::uint8_t, kStartupParticle2SourcePatchBytesV1>
      original_source_bytes{};
  std::array<std::uint8_t, kStartupParticle2SourcePatchBytesV1>
      installed_source_bytes{};
  std::array<std::uint8_t, kStartupParticle2VariantPatchBytesV1>
      original_variant_bytes{};
  std::array<std::uint8_t, kStartupParticle2VariantPatchBytesV1>
      installed_variant_bytes{};
  std::array<std::uint8_t, kStartupParticle2BackendPatchBytesV1>
      original_backend_bytes{};
  std::array<std::uint8_t, kStartupParticle2BackendPatchBytesV1>
      installed_backend_bytes{};

  void *memory_context = nullptr;
  StartupParticle2StageVirtualFreeV1 virtual_free = nullptr;
  StartupParticle2StageVirtualProtectV1 virtual_protect = nullptr;
  StartupParticle2StageFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct StartupParticle2StageRecorderV1Diagnostics {
  bool installed = false;
  std::uint32_t patch_mask = 0;
  std::uint32_t failure_flags =
      startup_particle2_stage_recorder_failure_none;
  std::uint64_t source_lookup_null_count = 0;
  std::uint64_t variant_lookup_null_count = 0;
  std::uint64_t backend_creation_null_count = 0;
};

bool InstallStartupParticle2StageRecorderV1(
    StartupParticle2StageRecorderV1State &state,
    const StartupParticle2StageRecorderV1Environment &environment) noexcept;

// The caller must prove quiescence externally before uninstalling. If any
// target cannot be restored exactly, RX stub storage is retained.
bool UninstallStartupParticle2StageRecorderV1(
    StartupParticle2StageRecorderV1State &state) noexcept;

StartupParticle2StageRecorderV1Diagnostics
ReadStartupParticle2StageRecorderV1Diagnostics(
    const StartupParticle2StageRecorderV1State &state) noexcept;

} // namespace xar::bridge
