#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kColdMapVfsCtorPatchRvaV1 = 0x3B55A40;
inline constexpr std::uintptr_t kColdMapVfsCtorContinueRvaV1 = 0x3B55A4F;
inline constexpr std::uintptr_t kColdMapVfsVariantPatchRvaV1 = 0x3B55ADE;
inline constexpr std::uintptr_t kColdMapVfsVariantContinueRvaV1 = 0x3B55AEC;
inline constexpr std::uintptr_t kColdMapVfsVariantMoveRvaV1 = 0x3B56830;
inline constexpr std::uintptr_t kColdMapVfsPollPatchRvaV1 = 0x3B55D50;
inline constexpr std::uintptr_t kColdMapVfsPollContinueRvaV1 = 0x3B55D5F;
inline constexpr std::size_t kColdMapVfsCtorPatchBytesV1 = 15;
inline constexpr std::size_t kColdMapVfsVariantPatchBytesV1 = 14;
inline constexpr std::size_t kColdMapVfsPollPatchBytesV1 = 15;
inline constexpr bool kColdMapVfsObserverInstalledByDefaultV1 = false;

enum ColdMapVfsObserverFailureV1 : std::uint32_t {
  cold_map_vfs_observer_failure_none = 0,
  cold_map_vfs_observer_failure_exact_build = 1U << 0,
  cold_map_vfs_observer_failure_primary_thread_suspended = 1U << 1,
  cold_map_vfs_observer_failure_unsupported_override = 1U << 2,
  cold_map_vfs_observer_failure_already_installed = 1U << 3,
  cold_map_vfs_observer_failure_anchor = 1U << 4,
  cold_map_vfs_observer_failure_allocation = 1U << 5,
  cold_map_vfs_observer_failure_stub_protection = 1U << 6,
  cold_map_vfs_observer_failure_target_protection = 1U << 7,
  cold_map_vfs_observer_failure_target_identity = 1U << 8,
  cold_map_vfs_observer_failure_flush = 1U << 9,
  cold_map_vfs_observer_failure_rollback = 1U << 10,
};

using ColdMapVfsVirtualAllocV1 = void *(*) (
    void *, std::size_t, DWORD, DWORD) noexcept;
using ColdMapVfsVirtualFreeV1 = bool (*) (
    void *, void *, std::size_t, DWORD) noexcept;
using ColdMapVfsVirtualProtectV1 = bool (*) (
    void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ColdMapVfsFlushInstructionCacheV1 = bool (*) (
    void *, const void *, std::size_t) noexcept;

struct ColdMapVfsObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::array<std::uintptr_t, 3> patch_target_overrides{};
  std::array<std::uintptr_t, 3> continue_target_overrides{};
  std::uintptr_t variant_move_target_override = 0;
  void *memory_context = nullptr;
  ColdMapVfsVirtualAllocV1 virtual_alloc_override = nullptr;
  ColdMapVfsVirtualFreeV1 virtual_free_override = nullptr;
  ColdMapVfsVirtualProtectV1 virtual_protect_override = nullptr;
  ColdMapVfsFlushInstructionCacheV1 flush_instruction_cache_override = nullptr;
};

struct ColdMapVfsHookStateV1 {
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::size_t patch_size = 0;
  std::array<std::uint8_t, 15> original{};
  std::array<std::uint8_t, 15> installed_patch{};
};

struct ColdMapVfsObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> installed_mask{0};
  std::atomic<std::uint32_t> failure_flags{cold_map_vfs_observer_failure_none};

  std::atomic<std::uint64_t> ctor_count{0};
  std::atomic<std::uint64_t> ctor_descriptor{0};
  std::atomic<std::uint64_t> ctor_data{0};
  std::atomic<std::uint32_t> ctor_length{0};
  std::atomic<std::uint32_t> ctor_flag{0};
  std::atomic<std::uint64_t> ctor_word0{0};
  std::atomic<std::uint64_t> ctor_word1{0};

  std::atomic<std::uint64_t> variant_count{0};
  std::atomic<std::uint64_t> variant_address{0};
  std::atomic<std::uint32_t> variant_tag{0};
  std::atomic<std::uint64_t> variant_payload{0};
  std::atomic<std::uint32_t> variant_length{0};
  std::atomic<std::uint32_t> variant_capacity{0};
  std::atomic<std::uint64_t> variant_word0{0};
  std::atomic<std::uint64_t> variant_word1{0};

  std::atomic<std::uint64_t> poll_count{0};
  std::atomic<std::uint64_t> poll_object{0};
  std::atomic<std::uint32_t> poll_state{0};
  std::atomic<std::uint32_t> poll_aux_state{0};
  std::atomic<std::uint32_t> poll_variant_tag{0};
  std::atomic<std::uint64_t> poll_payload{0};
  std::atomic<std::uint32_t> poll_length{0};
  std::atomic<std::uint32_t> poll_capacity{0};
  std::atomic<std::uint64_t> poll_word0{0};
  std::atomic<std::uint64_t> poll_word1{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t variant_move_target = 0;
  std::array<ColdMapVfsHookStateV1, 3> hooks{};
  void *memory_context = nullptr;
  ColdMapVfsVirtualFreeV1 virtual_free = nullptr;
  ColdMapVfsVirtualProtectV1 virtual_protect = nullptr;
  ColdMapVfsFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct ColdMapVfsObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t installed_mask = 0;
  std::uint32_t failure_flags = 0;
  std::uint64_t ctor_count = 0, ctor_descriptor = 0, ctor_data = 0;
  std::uint32_t ctor_length = 0, ctor_flag = 0;
  std::uint64_t ctor_word0 = 0, ctor_word1 = 0;
  std::uint64_t variant_count = 0, variant_address = 0, variant_payload = 0;
  std::uint32_t variant_tag = 0, variant_length = 0, variant_capacity = 0;
  std::uint64_t variant_word0 = 0, variant_word1 = 0;
  std::uint64_t poll_count = 0, poll_object = 0, poll_payload = 0;
  std::uint32_t poll_state = 0, poll_aux_state = 0, poll_variant_tag = 0;
  std::uint32_t poll_length = 0, poll_capacity = 0;
  std::uint64_t poll_word0 = 0, poll_word1 = 0;
};

bool InstallColdMapVfsObserverV1(ColdMapVfsObserverV1State &,
                                 const ColdMapVfsObserverEnvironmentV1 &) noexcept;
bool UninstallColdMapVfsObserverV1(ColdMapVfsObserverV1State &) noexcept;
ColdMapVfsObserverV1Diagnostics ReadColdMapVfsObserverV1Diagnostics(
    const ColdMapVfsObserverV1State &) noexcept;
void RecordColdMapVfsCtorV1(ColdMapVfsObserverV1State &, std::uintptr_t) noexcept;
void RecordColdMapVfsVariantV1(ColdMapVfsObserverV1State &, std::uintptr_t) noexcept;
void RecordColdMapVfsPollV1(ColdMapVfsObserverV1State &, std::uintptr_t) noexcept;

} // namespace xar::bridge
