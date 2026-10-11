#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_12004 {

struct RiteDynamicPrecallRegisters12004;
using RiteNamedFixedQ64PreCapture12004 = void (*)(
    void *, const RiteDynamicPrecallRegisters12004 &) noexcept;
using RiteNamedFixedQ64PostCapture12004 = void (*)(
    void *, std::uintptr_t helper_rbp, std::uint64_t raw_returned_rax) noexcept;

inline constexpr std::uintptr_t kRiteNamedFixedQ64PrePatchRva12004 = 0x375437C;
inline constexpr std::uintptr_t kRiteNamedFixedQ64PreResumeRva12004 = 0x3754385;
inline constexpr std::uintptr_t kRiteNamedFixedQ64OriginalCallRva12004 = 0x375438F;
inline constexpr std::uintptr_t kRiteNamedFixedQ64PostPatchRva12004 = 0x3754392;
inline constexpr std::uintptr_t kRiteNamedFixedQ64PostResumeRva12004 = 0x3754399;
inline constexpr std::size_t kRiteNamedFixedQ64PrePatchBytes12004 = 9;
inline constexpr std::size_t kRiteNamedFixedQ64PostPatchBytes12004 = 7;
inline constexpr std::size_t kRiteNamedFixedQ64RelayCapacity12004 = 1024;
inline constexpr std::size_t kRiteNamedFixedQ64BackingBytes12004 = 2048;

struct RiteNamedFixedQ64Observer12004Environment {
  // Existing exact descriptor admission; no independent SHA spelling test.
  bool exact_12004_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  std::uintptr_t module_base = 0;
  void *capture_context = nullptr;
  RiteNamedFixedQ64PreCapture12004 pre_capture = nullptr;
  RiteNamedFixedQ64PostCapture12004 post_capture = nullptr;
};

enum RiteNamedFixedQ64ObserverFailure12004 : std::uint32_t {
  rite_q64_failure_none = 0,
  rite_q64_failure_exact_build = 1U << 0,
  rite_q64_failure_suspension = 1U << 1,
  rite_q64_failure_already_owned = 1U << 2,
  rite_q64_failure_callbacks = 1U << 3,
  rite_q64_failure_anchor = 1U << 4,
  rite_q64_failure_near_allocation = 1U << 5,
  rite_q64_failure_relay = 1U << 6,
  rite_q64_failure_target_identity = 1U << 7,
  rite_q64_failure_target_protection = 1U << 8,
  rite_q64_failure_flush = 1U << 9,
  rite_q64_failure_restore = 1U << 10,
  rite_q64_failure_module_pin = 1U << 11,
  rite_q64_failure_quiescence = 1U << 12,
};

// Process-lifetime caller-owned storage, including failure paths. There is no
// destructor cleanup. installed also remains true for a possibly live partial
// patch. owned_patch_mask bit0=pre, bit1=post; these bits do not count events.
// Ordinary Stop/DllMain must retain this state, callback context and backing.
struct RiteNamedFixedQ64Observer12004State {
  std::atomic<bool> installed{false};
  std::atomic<std::uint8_t> owned_patch_mask{0};
  std::atomic<std::uint32_t> failure_flags{0};
  RiteNamedFixedQ64Observer12004Environment environment{};
  std::uintptr_t pre_target = 0;
  std::uintptr_t pre_resume = 0;
  std::uintptr_t post_target = 0;
  std::uintptr_t post_resume = 0;
  void *backing = nullptr;
  std::size_t backing_bytes = 0;
  std::size_t pre_relay_bytes = 0;
  std::size_t post_relay_bytes = 0;
  std::uint32_t pre_original_protection = 0;
  std::uint32_t post_original_protection = 0;
  bool callback_modules_pinned = false;
  std::array<std::uint8_t, kRiteNamedFixedQ64PrePatchBytes12004> original_pre{};
  std::array<std::uint8_t, kRiteNamedFixedQ64PostPatchBytes12004> original_post{};
  std::array<std::uint8_t, kRiteNamedFixedQ64PrePatchBytes12004> installed_pre{};
  std::array<std::uint8_t, kRiteNamedFixedQ64PostPatchBytes12004> installed_post{};
};

struct RiteNamedFixedQ64Observer12004Diagnostics {
  bool installed = false;
  std::uint8_t owned_patch_mask = 0;
  std::uint32_t failure_flags = 0;
  bool backing_retained = false;
  bool callback_modules_pinned = false;
};

// Cold startup only. Before the first patch this permanently pins the observer
// thunk and both callback modules. False propagates to the startup owner.
bool InstallRiteNamedFixedQ64Observer12004(
    RiteNamedFixedQ64Observer12004State &state,
    const RiteNamedFixedQ64Observer12004Environment &environment) noexcept;
// Two-argument calls lack relay quiescence proof and cannot free live backing.
bool UninstallRiteNamedFixedQ64Observer12004(
    RiteNamedFixedQ64Observer12004State &state,
    bool primary_thread_suspended_proven,
    bool observer_execution_quiescent_proven = false) noexcept;
RiteNamedFixedQ64Observer12004Diagnostics ReadRiteNamedFixedQ64Observer12004Diagnostics(
    const RiteNamedFixedQ64Observer12004State &state) noexcept;

} // namespace xar::ck3_12004
