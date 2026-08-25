#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// This is the first live-crashing CGfxDX11RenderContext draw wrapper only.
// A suppressed call returns before its unwind prologue executes. A healthy
// call replays every overwritten instruction and resumes at 0x3B0B0FF.
inline constexpr std::uintptr_t kStartupDx11RenderContextDrawFunctionRvaV1 =
    0x3B0B0F0;
inline constexpr std::uintptr_t kStartupDx11RenderContextDrawContinueRvaV1 =
    0x3B0B0FF;
inline constexpr std::size_t kStartupDx11RenderContextDrawDirtyOffsetV1 =
    0x1938;
inline constexpr std::size_t kStartupDx11RenderContextDrawShaderStateOffsetV1 =
    0x1940;

inline constexpr std::size_t kStartupDx11RenderContextDrawPatchBytesV1 = 15;
inline constexpr std::size_t
    kStartupDx11RenderContextDrawProductionAnchorBytesV1 = 46;
inline constexpr std::size_t kStartupDx11RenderContextDrawStubBytesV1 = 62;
inline constexpr bool kStartupDx11RenderContextDrawGuardInstalledByDefaultV1 =
    false;

enum StartupDx11RenderContextDrawGuardFailureV1 : std::uint32_t {
  startup_dx11_render_context_draw_guard_failure_none = 0,
  startup_dx11_render_context_draw_guard_failure_exact_build = 1U << 0,
  startup_dx11_render_context_draw_guard_failure_primary_thread_suspended =
      1U << 1,
  startup_dx11_render_context_draw_guard_failure_unsupported_override =
      1U << 2,
  startup_dx11_render_context_draw_guard_failure_already_installed = 1U << 3,
  startup_dx11_render_context_draw_guard_failure_anchor = 1U << 4,
  startup_dx11_render_context_draw_guard_failure_allocation = 1U << 5,
  startup_dx11_render_context_draw_guard_failure_stub_protection = 1U << 6,
  startup_dx11_render_context_draw_guard_failure_target_protection = 1U << 7,
  startup_dx11_render_context_draw_guard_failure_target_identity = 1U << 8,
  startup_dx11_render_context_draw_guard_failure_flush = 1U << 9,
  startup_dx11_render_context_draw_guard_failure_rollback = 1U << 10,
};

using StartupDx11RenderContextDrawVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupDx11RenderContextDrawVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using StartupDx11RenderContextDrawVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupDx11RenderContextDrawFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

// Overrides are an offline executable-fixture seam only. Production must pass
// the admitted module base while its newly-created primary thread is suspended.
struct StartupDx11RenderContextDrawGuardV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;

  void *memory_context = nullptr;
  StartupDx11RenderContextDrawVirtualAllocV1 virtual_alloc_override = nullptr;
  StartupDx11RenderContextDrawVirtualFreeV1 virtual_free_override = nullptr;
  StartupDx11RenderContextDrawVirtualProtectV1 virtual_protect_override =
      nullptr;
  StartupDx11RenderContextDrawFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable through uninstall. The generated stub
// embeds the diagnostic atomic address.
struct StartupDx11RenderContextDrawGuardV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_dx11_render_context_draw_guard_failure_none};
  alignas(8) std::atomic<std::uint64_t> suppressed_count{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kStartupDx11RenderContextDrawPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kStartupDx11RenderContextDrawPatchBytesV1>
      installed_patch_bytes{};

  void *memory_context = nullptr;
  StartupDx11RenderContextDrawVirtualFreeV1 virtual_free = nullptr;
  StartupDx11RenderContextDrawVirtualProtectV1 virtual_protect = nullptr;
  StartupDx11RenderContextDrawFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct StartupDx11RenderContextDrawGuardV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags =
      startup_dx11_render_context_draw_guard_failure_none;
  std::uint64_t suppressed_count = 0;
};

bool InstallStartupDx11RenderContextDrawGuardV1(
    StartupDx11RenderContextDrawGuardV1State &state,
    const StartupDx11RenderContextDrawGuardV1Environment &environment) noexcept;

// The caller must again prove quiescence externally before uninstalling. A
// failed restore retains the executable stub and reports rollback failure.
bool UninstallStartupDx11RenderContextDrawGuardV1(
    StartupDx11RenderContextDrawGuardV1State &state) noexcept;

StartupDx11RenderContextDrawGuardV1Diagnostics
ReadStartupDx11RenderContextDrawGuardV1Diagnostics(
    const StartupDx11RenderContextDrawGuardV1State &state) noexcept;

} // namespace xar::bridge
