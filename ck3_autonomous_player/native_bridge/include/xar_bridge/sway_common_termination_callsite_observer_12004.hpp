#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kSwayCommonTerminationObserverAnchorRva12004 = 0x2A48868;
inline constexpr std::uintptr_t kSwayCommonTerminationObserverCallRva12004 = 0x2A48877;
inline constexpr std::uintptr_t kSwayCommonTerminationObserverCalleeRva12004 = 0x2A4ADF0;
inline constexpr std::uintptr_t kSwayCommonTerminationObserverContinueRva12004 = 0x2A4887C;
inline constexpr std::size_t kSwayCommonTerminationObserverPatchBytes12004 = 5;
inline constexpr std::size_t kSwayCommonTerminationObserverStubCapacity12004 = 384;

// RCX and all RDX bits are copied from this one actual native CALL. The owning
// adapter interprets only the low byte as raw DL; it must not bool-normalize it.
// These callbacks neither receive a native return-address read nor create an
// observer session, invocation, Core frame, instance identity or terminal cause.
using SwayCommonTerminationCallsiteBefore12004 = void (*)(
    void *callback_context, std::uintptr_t actual_rcx,
    std::uint64_t actual_rdx) noexcept;
using SwayCommonTerminationCallsiteAfter12004 = void (*)(
    void *callback_context, std::uint64_t returned_rax_bits) noexcept;

struct SwayCommonTerminationCallsiteObserver12004Environment {
  bool exact_12004_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  std::uintptr_t module_base = 0;
  void *callback_context = nullptr;
  SwayCommonTerminationCallsiteBefore12004 before = nullptr;
  SwayCommonTerminationCallsiteAfter12004 after = nullptr;
};

enum SwayCommonTerminationCallsiteObserverFailure12004 : std::uint32_t {
  sway_common_observer_failure_none = 0,
  sway_common_observer_failure_exact_build = 1U << 0,
  sway_common_observer_failure_suspension = 1U << 1,
  sway_common_observer_failure_already_owned = 1U << 2,
  sway_common_observer_failure_callbacks = 1U << 3,
  sway_common_observer_failure_anchor = 1U << 4,
  sway_common_observer_failure_near_allocation = 1U << 5,
  sway_common_observer_failure_stub = 1U << 6,
  sway_common_observer_failure_target_identity = 1U << 7,
  sway_common_observer_failure_target_protection = 1U << 8,
  sway_common_observer_failure_flush = 1U << 9,
  sway_common_observer_failure_restore = 1U << 10,
};

// Caller-owned process-lifetime storage. Destruction performs no code write or
// backing release. Ordinary Stop supplies no suspended-primary-thread proof.
struct SwayCommonTerminationCallsiteObserver12004State {
  std::atomic<bool> installed{false};
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<std::uint64_t> before_count{0};
  std::atomic<std::uint64_t> returned_count{0};
  SwayCommonTerminationCallsiteObserver12004Environment environment{};
  std::uintptr_t patch_target = 0;
  std::uintptr_t native_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::size_t stub_bytes = 0;
  std::array<std::uint8_t, kSwayCommonTerminationObserverPatchBytes12004> original_patch{};
  std::array<std::uint8_t, kSwayCommonTerminationObserverPatchBytes12004> installed_patch{};
};

struct SwayCommonTerminationCallsiteObserver12004Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t before_count = 0;
  std::uint64_t returned_count = 0;
};

bool InstallSwayCommonTerminationCallsiteObserver12004(
    SwayCommonTerminationCallsiteObserver12004State &state,
    const SwayCommonTerminationCallsiteObserver12004Environment &environment) noexcept;
bool UninstallSwayCommonTerminationCallsiteObserver12004(
    SwayCommonTerminationCallsiteObserver12004State &state,
    bool primary_thread_suspended_proven) noexcept;
SwayCommonTerminationCallsiteObserver12004Diagnostics
ReadSwayCommonTerminationCallsiteObserver12004Diagnostics(
    const SwayCommonTerminationCallsiteObserver12004State &state) noexcept;

} // namespace xar::ck3_12004
