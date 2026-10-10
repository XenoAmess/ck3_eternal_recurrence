#pragma once

#include "xar_bridge/person_installed_transfer_stage_12004.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>
#include <windows.h>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kConceptionSampleRva12004 = 0xE46530;
inline constexpr std::uintptr_t kConceptionSampleReturnRva12004 = 0x2929D99;
inline constexpr std::size_t kConceptionSamplePatchBytes12004 = 15;
inline constexpr std::size_t kConceptionSampleJournalCapacity12004 = 256;
inline constexpr std::string_view kConceptionSampleSourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

// Supplied only by the active natural 2929B40 parent extent on this thread.
// Numeric modifier/threshold and monthly scheduling are not part of this scope.
struct ConceptionSampleParentScope12004 {
  bool active = false;
  std::uint64_t parent_scope_id = 0;
  std::uint32_t thread_id = 0;
  std::uint64_t process_clock = 0;
  std::uintptr_t clock_identity = 0;
  std::uintptr_t first_character = 0, second_character = 0;
  std::uint32_t first_full_id = UINT32_MAX, second_full_id = UINT32_MAX;
  std::uintptr_t sample_receiver = 0;
};

struct ConceptionSampleObservation12004 {
  std::uint64_t journal_sequence = 0;
  std::string_view source_pin = kConceptionSampleSourcePin12004;
  ConceptionSampleParentScope12004 parent{};
  PersonInstalledTransferEvent12004 before_event{}, returned_event{};
  std::uintptr_t caller_return_rva = 0, receiver = 0;
  std::int64_t original_lower = 0, original_upper = 0, returned_rax = 0;
  std::optional<std::int64_t> threshold_at_sample;
  bool threshold_capture_ready = false;
  std::optional<bool> comparison_at_sample_passed;
  std::optional<std::array<std::uint32_t, 2>> state_before, state_after;
  std::optional<bool> state_transition_matches_source;
  bool original_returned = false;
  bool parent_extent_and_generation_unchanged = false;
  bool event_clock_and_thread_match = false;
  bool sample_within_source_range = false;
  bool causal_sample_ready = false;
  std::uint32_t capture_failure_flags = 0;
};

struct ConceptionSampleObservations12004 {
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::vector<ConceptionSampleObservation12004> events;
};

using ConceptionSampleOriginal12004 = std::int64_t(__fastcall *)(
    void *, std::int64_t, std::int64_t);
using ConceptionSampleRead12004 = bool (*)(
    void *, const void *, void *, std::size_t) noexcept;
using ConceptionSampleReadParent12004 = bool (*)(
    void *, ConceptionSampleParentScope12004 &) noexcept;
using ConceptionSampleChildReturn12004 = void (*)(
    void *, const ConceptionSampleObservation12004 &) noexcept;

struct ConceptionSampleBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ConceptionSampleRead12004 read_memory = nullptr;
  void *parent_context = nullptr;
  ConceptionSampleReadParent12004 read_parent = nullptr;
  // Optional owned-record delivery; the callback must not invoke native code.
  void *child_return_context = nullptr;
  ConceptionSampleChildReturn12004 child_return = nullptr;
  void *event_context = nullptr;
  PersonInstalledTransferEventReader12004 next_event = nullptr;
};

using ConceptionSampleAlloc12004 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ConceptionSampleFree12004 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ConceptionSampleProtect12004 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ConceptionSampleFlush12004 = bool (*)(void *, const void *, std::size_t) noexcept;
struct ConceptionSampleInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ConceptionSampleBindings12004 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ConceptionSampleAlloc12004 virtual_alloc_override = nullptr;
  ConceptionSampleFree12004 virtual_free_override = nullptr;
  ConceptionSampleProtect12004 virtual_protect_override = nullptr;
  ConceptionSampleFlush12004 flush_instruction_cache_override = nullptr;
};
struct ConceptionSampleDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  void *entry_thunk = nullptr;
  std::array<std::uint8_t, kConceptionSamplePatchBytes12004> original{};
  void *memory_context = nullptr;
  ConceptionSampleFree12004 virtual_free = nullptr;
  ConceptionSampleProtect12004 virtual_protect = nullptr;
  ConceptionSampleFlush12004 flush_instruction_cache = nullptr;
};
enum ConceptionSampleInstallFailure12004 : std::uint32_t {
  conception_sample_install_none = 0,
  conception_sample_install_exact_build = 1U << 0,
  conception_sample_install_quiescence = 1U << 1,
  conception_sample_install_already_installed = 1U << 2,
  conception_sample_install_anchor = 1U << 3,
  conception_sample_install_allocation = 1U << 4,
  conception_sample_install_protection = 1U << 5,
  conception_sample_install_flush = 1U << 6,
  conception_sample_install_rollback = 1U << 7,
};
enum ConceptionSampleCaptureFailure12004 : std::uint32_t {
  conception_sample_capture_state_before = 1U << 0,
  conception_sample_capture_state_after = 1U << 1,
  conception_sample_capture_parent_changed = 1U << 2,
  conception_sample_capture_event_coordinate = 1U << 3,
  conception_sample_capture_return_domain = 1U << 4,
  conception_sample_capture_state_transition = 1U << 5,
  conception_sample_capture_threshold = 1U << 6,
};

ConceptionSampleBindings12004 BindConceptionSampleImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallConceptionSamplePassive12004(
    ConceptionSampleDetourState12004 &,
    const ConceptionSampleInstallEnvironment12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallConceptionSamplePassive12004(
    ConceptionSampleDetourState12004 &, bool primary_thread_suspended_proven) noexcept;

// Retained copies only. Zero/zero returns the retained journal; a nonzero pair
// selects one natural parent. Neither query invokes the helper or a native read.
std::optional<ConceptionSampleObservations12004> ReadConceptionSampleObservations12004(
    std::uintptr_t clock_identity = 0, std::uint64_t parent_scope_id = 0) noexcept;
extern "C" std::int64_t __fastcall XarConceptionSampleHook12004(
    void *receiver, std::int64_t lower, std::int64_t upper,
    std::int64_t caller_rbx) noexcept;

// Typed local compound-fixture seams: no patch, game call or machine-body replay.
bool InitializeConceptionSampleFixture12004(
    const ConceptionSampleBindings12004 &, ConceptionSampleOriginal12004) noexcept;
std::int64_t InvokeConceptionSampleFixture12004(
    std::uintptr_t caller_return_rva, void *receiver,
    std::int64_t lower, std::int64_t upper,
    std::optional<std::int64_t> caller_rbx = std::nullopt) noexcept;
bool RunConceptionSamplePassiveFixture12004() noexcept;

} // namespace xar::ck3_12004
