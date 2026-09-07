#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kNamedPath583ResolverCallRvaV1 = 0x3320A82;
inline constexpr std::uintptr_t kNamedPath583ResolverTargetRvaV1 = 0x3B96C70;
inline constexpr std::uintptr_t kNamedPath583MovePatchRvaV1 = 0x331F9E4;
inline constexpr std::uintptr_t kNamedPath583MoveContinueRvaV1 = 0x331F9EF;
inline constexpr std::uintptr_t kNamedPath583MoveTargetRvaV1 = 0x07E6C00;
inline constexpr std::size_t kNamedPath583ResolverPatchBytesV1 = 5;
inline constexpr std::size_t kNamedPath583MovePatchBytesV1 = 11;
inline constexpr std::size_t kNamedPath583StubAllocationBytesV1 = 4096;
inline constexpr std::size_t kNamedPath583CorrelationSlotsV1 = 16;
inline constexpr bool kNamedPath583RootObserverInstalledByDefaultV1 = false;

enum NamedPath583RootObserverFailureV1 : std::uint32_t {
  named_path_583_root_observer_failure_none = 0,
  named_path_583_root_observer_failure_exact_build = 1U << 0,
  named_path_583_root_observer_failure_primary_thread_suspended = 1U << 1,
  named_path_583_root_observer_failure_unsupported_override = 1U << 2,
  named_path_583_root_observer_failure_already_installed = 1U << 3,
  named_path_583_root_observer_failure_anchor = 1U << 4,
  named_path_583_root_observer_failure_allocation = 1U << 5,
  named_path_583_root_observer_failure_stub_range = 1U << 6,
  named_path_583_root_observer_failure_stub_protection = 1U << 7,
  named_path_583_root_observer_failure_target_protection = 1U << 8,
  named_path_583_root_observer_failure_target_identity = 1U << 9,
  named_path_583_root_observer_failure_flush = 1U << 10,
  named_path_583_root_observer_failure_rollback = 1U << 11,
};

using NamedPath583VirtualAllocNearV1 = void *(*) (
    void *context, std::uintptr_t lower_bound, std::uintptr_t upper_bound,
    std::size_t size, DWORD allocation_type, DWORD protection) noexcept;
using NamedPath583VirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using NamedPath583VirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using NamedPath583FlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct NamedPath583RootObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::array<std::uintptr_t, 2> patch_target_overrides{};
  std::uintptr_t move_continue_target_override = 0;
  std::uintptr_t resolver_target_override = 0;
  std::uintptr_t move_target_override = 0;
  void *memory_context = nullptr;
  NamedPath583VirtualAllocNearV1 virtual_alloc_near_override = nullptr;
  NamedPath583VirtualFreeV1 virtual_free_override = nullptr;
  NamedPath583VirtualProtectV1 virtual_protect_override = nullptr;
  NamedPath583FlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct NamedPath583StringObservationV1 {
  std::atomic<std::uint64_t> object{0};
  std::atomic<std::uint64_t> effective_data{0};
  std::atomic<std::uint64_t> length{0};
  std::atomic<std::uint64_t> capacity{0};
  std::atomic<std::uint64_t> word0{0};
  std::atomic<std::uint64_t> word1{0};
  std::atomic<std::uint32_t> null_result{0};
  std::atomic<std::uint32_t> read_fault{0};
};

struct NamedPath583CorrelationSlotV1 {
  std::atomic<std::uint64_t> published_sequence{0};
  std::atomic<std::uint32_t> thread_id{0};
  std::atomic<std::uint32_t> move_pre_seen{0};
  std::atomic<std::uint32_t> move_post_seen{0};
  std::atomic<std::uint64_t> move_result{0};
  NamedPath583StringObservationV1 resolver{};
  NamedPath583StringObservationV1 temporary_before{};
  NamedPath583StringObservationV1 root_before{};
  NamedPath583StringObservationV1 temporary_after{};
  NamedPath583StringObservationV1 root_after{};
};

struct NamedPath583HookStateV1 {
  std::uintptr_t patch_target = 0;
  std::size_t patch_size = 0;
  std::array<std::uint8_t, kNamedPath583MovePatchBytesV1> original{};
  std::array<std::uint8_t, kNamedPath583MovePatchBytesV1> installed_patch{};
};

struct NamedPath583RootObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> installed_mask{0};
  std::atomic<std::uint32_t> failure_flags{
      named_path_583_root_observer_failure_none};
  std::atomic<std::uint64_t> next_sequence{0};
  std::atomic<std::uint64_t> resolver_count{0};
  std::atomic<std::uint64_t> move_pre_count{0};
  std::atomic<std::uint64_t> move_post_count{0};
  std::atomic<std::uint64_t> correlation_miss_count{0};
  std::atomic<std::uint64_t> last_resolver_sequence{0};
  std::atomic<std::uint64_t> last_move_pre_sequence{0};
  std::atomic<std::uint64_t> last_move_post_sequence{0};
  std::array<NamedPath583CorrelationSlotV1,
             kNamedPath583CorrelationSlotsV1>
      slots{};

  std::uintptr_t module_base = 0;
  std::uintptr_t resolver_target = 0;
  std::uintptr_t move_target = 0;
  std::uintptr_t move_continue_target = 0;
  std::array<NamedPath583HookStateV1, 2> hooks{};
  void *stub_allocation = nullptr;
  void *memory_context = nullptr;
  NamedPath583VirtualFreeV1 virtual_free = nullptr;
  NamedPath583VirtualProtectV1 virtual_protect = nullptr;
  NamedPath583FlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct NamedPath583StringDiagnosticsV1 {
  std::uint64_t object = 0;
  std::uint64_t effective_data = 0;
  std::uint64_t length = 0;
  std::uint64_t capacity = 0;
  std::uint64_t word0 = 0;
  std::uint64_t word1 = 0;
  bool null_result = false;
  bool read_fault = false;
};

struct NamedPath583RootObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t installed_mask = 0;
  std::uint32_t failure_flags = 0;
  std::uint64_t resolver_count = 0;
  std::uint64_t move_pre_count = 0;
  std::uint64_t move_post_count = 0;
  std::uint64_t correlation_miss_count = 0;
  std::uint64_t sequence = 0;
  std::uint32_t thread_id = 0;
  bool move_pre_seen = false;
  bool move_post_seen = false;
  std::uint64_t move_result = 0;
  NamedPath583StringDiagnosticsV1 resolver{};
  NamedPath583StringDiagnosticsV1 temporary_before{};
  NamedPath583StringDiagnosticsV1 root_before{};
  NamedPath583StringDiagnosticsV1 temporary_after{};
  NamedPath583StringDiagnosticsV1 root_after{};
};

bool InstallNamedPath583RootObserverV1(
    NamedPath583RootObserverV1State &state,
    const NamedPath583RootObserverEnvironmentV1 &environment) noexcept;
bool UninstallNamedPath583RootObserverV1(
    NamedPath583RootObserverV1State &state) noexcept;
NamedPath583RootObserverV1Diagnostics
ReadNamedPath583RootObserverV1Diagnostics(
    const NamedPath583RootObserverV1State &state) noexcept;

void RecordNamedPath583ResolverV1(NamedPath583RootObserverV1State &state,
                                  std::uintptr_t resolver_result,
                                  std::uint32_t thread_id) noexcept;
void RecordNamedPath583MovePreV1(NamedPath583RootObserverV1State &state,
                                 std::uintptr_t root,
                                 std::uintptr_t temporary,
                                 std::uint32_t thread_id) noexcept;
void RecordNamedPath583MovePostV1(NamedPath583RootObserverV1State &state,
                                  std::uintptr_t root,
                                  std::uintptr_t temporary,
                                  std::uintptr_t move_result,
                                  std::uint32_t thread_id) noexcept;

} // namespace xar::bridge
