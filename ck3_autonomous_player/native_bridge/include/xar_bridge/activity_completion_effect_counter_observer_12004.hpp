#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace xar::bridge {

// Borrowed physical operands from one naturally reached original CALL. The
// callback must copy its own fields before returning; this is no context DTO.
struct ActivityCompletionEffectOperands12004 {
  std::uintptr_t activity = 0;
  std::uintptr_t participant = 0;
  std::uintptr_t effect = 0;
  std::uintptr_t native_context = 0;
  std::uintptr_t original_parent_rsp = 0;
  std::uint64_t invocation_sequence = 0;
  std::uint32_t thread_id = 0;
};

} // namespace xar::bridge

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kActivityCompletionEffectCounterAnchorRva12004 = 0x23F6B75;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterPreRva12004 = 0x23F6B7D;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterCallRva12004 = 0x23F6B82;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterCalleeRva12004 = 0x3765760;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterPostRva12004 = 0x23F6B87;
inline constexpr std::uintptr_t kActivityCompletionEffectCounterContinueRva12004 = 0x23F6B8E;
inline constexpr std::size_t kActivityCompletionEffectCounterStubCapacity12004 = 384;

using ActivityCompletionEffectCounterCapture12004 = void (*)(
    void *, const xar::bridge::ActivityCompletionEffectOperands12004 &) noexcept;

struct ActivityCompletionEffectCounterObserver12004Environment {
  bool exact_12004_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  std::uintptr_t module_base = 0;
  void *callback_context = nullptr;
  ActivityCompletionEffectCounterCapture12004 before = nullptr;
  ActivityCompletionEffectCounterCapture12004 after = nullptr;
};

enum ActivityCompletionEffectCounterObserverFailure12004 : std::uint32_t {
  activity_completion_effect_counter_failure_none = 0,
  activity_completion_effect_counter_failure_exact_build = 1U << 0,
  activity_completion_effect_counter_failure_suspension = 1U << 1,
  activity_completion_effect_counter_failure_already_owned = 1U << 2,
  activity_completion_effect_counter_failure_callbacks = 1U << 3,
  activity_completion_effect_counter_failure_anchor = 1U << 4,
  activity_completion_effect_counter_failure_near_allocation = 1U << 5,
  activity_completion_effect_counter_failure_stub = 1U << 6,
  activity_completion_effect_counter_failure_target_identity = 1U << 7,
  activity_completion_effect_counter_failure_target_protection = 1U << 8,
  activity_completion_effect_counter_failure_flush = 1U << 9,
  activity_completion_effect_counter_failure_restore = 1U << 10,
};

struct ActivityCompletionEffectCounterObserver12004Window {
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::size_t stub_bytes = 0;
  std::size_t patch_bytes = 0;
  bool patch_owned_or_uncertain = false;
  std::array<std::uint8_t, 7> original_patch{};
  std::array<std::uint8_t, 7> installed_patch{};
};

// Process-lifetime state. Ordinary Stop calls Uninstall(false), retaining the
// owned patches and backing exactly as the adopted fixed observer pattern.
struct ActivityCompletionEffectCounterObserver12004State {
  std::atomic<bool> installed{false};
  std::atomic<bool> callbacks_enabled{false};
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<std::uint64_t> before_count{0};
  std::atomic<std::uint64_t> returned_count{0};
  std::atomic<std::uint64_t> bypass_post_count{0};
  std::atomic<std::uint64_t> uncorrelated_post_count{0};
  std::atomic<std::uint64_t> dropped_before_count{0};
  ActivityCompletionEffectCounterObserver12004Environment environment{};
  std::uintptr_t native_return_target = 0;
  std::array<ActivityCompletionEffectCounterObserver12004Window, 2> windows{};
};

struct ActivityCompletionEffectCounterObserver12004Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t before_count = 0;
  std::uint64_t returned_count = 0;
  std::uint64_t bypass_post_count = 0;
  std::uint64_t uncorrelated_post_count = 0;
  std::uint64_t dropped_before_count = 0;
};

bool InstallActivityCompletionEffectCounterObserver12004(
    ActivityCompletionEffectCounterObserver12004State &,
    const ActivityCompletionEffectCounterObserver12004Environment &) noexcept;
bool UninstallActivityCompletionEffectCounterObserver12004(
    ActivityCompletionEffectCounterObserver12004State &,
    bool primary_thread_suspended_proven) noexcept;
ActivityCompletionEffectCounterObserver12004Diagnostics
ReadActivityCompletionEffectCounterObserver12004Diagnostics(
    const ActivityCompletionEffectCounterObserver12004State &) noexcept;

} // namespace xar::ck3_12004
