#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kActivityInvalidationPrecallObserverAnchorRva12004 = 0x29BF660;
inline constexpr std::uintptr_t kActivityInvalidationPrecallObserverPatchRva12004 = 0x29BF68C;
inline constexpr std::uintptr_t kActivityInvalidationPrecallObserverCallRva12004 = 0x29BF691;
inline constexpr std::uintptr_t kActivityInvalidationPrecallObserverCalleeRva12004 = 0x2BBA520;
inline constexpr std::uintptr_t kActivityInvalidationPrecallObserverContinueRva12004 = 0x29BF691;
inline constexpr std::size_t kActivityInvalidationPrecallObserverPatchBytes12004 = 5;
inline constexpr std::size_t kActivityInvalidationPrecallObserverStubCapacity12004 = 384;

// Runs after the native Activity+422 store and before its first natural CALL.
// Manager and Activity are borrowed original RSI/RBX identities only. The
// owning callback copies its source fields before returning; it supplies its
// own actual frame/host limiter and journal. No object is read after the CALL.
using ActivityInvalidationPrecallCapture12004 = void (*)(
    void *callback_context, std::uintptr_t actual_manager,
    std::uintptr_t actual_activity) noexcept;

struct ActivityInvalidationPrecallObserver12004Environment {
  bool exact_12004_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  std::uintptr_t module_base = 0;
  void *callback_context = nullptr;
  ActivityInvalidationPrecallCapture12004 capture = nullptr;
};

enum ActivityInvalidationPrecallObserverFailure12004 : std::uint32_t {
  activity_invalidation_precall_failure_none = 0,
  activity_invalidation_precall_failure_exact_build = 1U << 0,
  activity_invalidation_precall_failure_suspension = 1U << 1,
  activity_invalidation_precall_failure_already_owned = 1U << 2,
  activity_invalidation_precall_failure_callbacks = 1U << 3,
  activity_invalidation_precall_failure_anchor = 1U << 4,
  activity_invalidation_precall_failure_near_allocation = 1U << 5,
  activity_invalidation_precall_failure_stub = 1U << 6,
  activity_invalidation_precall_failure_target_identity = 1U << 7,
  activity_invalidation_precall_failure_target_protection = 1U << 8,
  activity_invalidation_precall_failure_flush = 1U << 9,
  activity_invalidation_precall_failure_restore = 1U << 10,
};

// Caller-owned process-lifetime storage. Destruction does not patch code or
// release backing. Ordinary Stop has no suspended-primary-thread proof and
// must call Uninstall(false), which keeps the owned code and backing intact.
struct ActivityInvalidationPrecallObserver12004State {
  std::atomic<bool> installed{false};
  std::atomic<std::uint32_t> failure_flags{0};
  // Counts callback entries, not successful owned copies or release effects.
  std::atomic<std::uint64_t> capture_count{0};
  ActivityInvalidationPrecallObserver12004Environment environment{};
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::size_t stub_bytes = 0;
  std::array<std::uint8_t, kActivityInvalidationPrecallObserverPatchBytes12004> original_patch{};
  std::array<std::uint8_t, kActivityInvalidationPrecallObserverPatchBytes12004> installed_patch{};
};

struct ActivityInvalidationPrecallObserver12004Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t capture_count = 0;
};

bool InstallActivityInvalidationPrecallObserver12004(
    ActivityInvalidationPrecallObserver12004State &state,
    const ActivityInvalidationPrecallObserver12004Environment &environment) noexcept;
bool UninstallActivityInvalidationPrecallObserver12004(
    ActivityInvalidationPrecallObserver12004State &state,
    bool primary_thread_suspended_proven) noexcept;
ActivityInvalidationPrecallObserver12004Diagnostics
ReadActivityInvalidationPrecallObserver12004Diagnostics(
    const ActivityInvalidationPrecallObserver12004State &state) noexcept;

} // namespace xar::ck3_12004
