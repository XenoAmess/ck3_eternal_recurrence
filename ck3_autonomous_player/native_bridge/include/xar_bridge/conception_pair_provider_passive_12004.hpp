#pragma once

#include "xar_bridge/conception_sample_passive_12004.hpp"
#include <atomic>
#include <array>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kConceptionPairProviderRva12004 = 0x2B95670;
inline constexpr std::uintptr_t kConceptionPairProviderReturnRva12004 = 0x2929C30;
inline constexpr std::size_t kConceptionPairProviderPatchBytes12004 = 16;
inline constexpr std::size_t kConceptionPairProviderJournalCapacity12004 = 256;
inline constexpr std::string_view kConceptionPairProviderSourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

using ConceptionPairProviderParentScope12004 = ConceptionSampleParentScope12004;
using ConceptionPairProviderOriginal12004 = void *(__fastcall *)(
    void *output, void *first, void *second, std::uint32_t mode, void *fifth);
using ConceptionPairProviderRead12004 = ConceptionSampleRead12004;
using ConceptionPairProviderReadParent12004 = ConceptionSampleReadParent12004;

struct ConceptionPairProviderObservation12004 {
  std::string_view source_pin = kConceptionPairProviderSourcePin12004;
  std::uint64_t journal_sequence = 0;
  ConceptionPairProviderParentScope12004 parent{};
  PersonInstalledTransferEvent12004 before_event{}, returned_event{};
  std::uint32_t process_id = 0, thread_id = 0;
  std::uintptr_t caller_return_pc = 0, caller_return_rva = 0;
  std::uintptr_t output_pointer = 0, first_character = 0, second_character = 0;
  std::uint32_t mode = 0;
  std::uintptr_t fifth_argument = 0;
  std::optional<std::int64_t> output_before, output_after;
  std::optional<std::uint32_t> first_full_id_before, second_full_id_before;
  std::optional<std::uint32_t> first_full_id_after, second_full_id_after;
  std::uintptr_t native_return_bits = 0;
  bool original_returned = false;
  bool native_return_matches_output = false;
  bool parent_extent_unchanged = false;
  bool event_clock_and_thread_match = false;
  // Captured actual callerout after an eligible natural original once.
  // No provider math, projected pair value or inferred 0 is accepted.
  bool actual_caller_input_ready = false;
  std::uint32_t capture_failure_flags = 0;
};

using ConceptionPairProviderChildReturn12004 = bool (*)(
    void *, const ConceptionPairProviderObservation12004 &) noexcept;

struct ConceptionPairProviderBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ConceptionPairProviderRead12004 read_memory = nullptr;
  void *parent_context = nullptr;
  ConceptionPairProviderReadParent12004 read_parent = nullptr;
  void *event_context = nullptr;
  PersonInstalledTransferEventReader12004 next_event = nullptr;
  void *child_return_context = nullptr;
  ConceptionPairProviderChildReturn12004 child_return = nullptr;
};

using ConceptionPairProviderAlloc12004 = ConceptionSampleAlloc12004;
using ConceptionPairProviderFree12004 = ConceptionSampleFree12004;
using ConceptionPairProviderProtect12004 = ConceptionSampleProtect12004;
using ConceptionPairProviderFlush12004 = ConceptionSampleFlush12004;
struct ConceptionPairProviderInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ConceptionPairProviderBindings12004 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ConceptionPairProviderAlloc12004 virtual_alloc_override = nullptr;
  ConceptionPairProviderFree12004 virtual_free_override = nullptr;
  ConceptionPairProviderProtect12004 virtual_protect_override = nullptr;
  ConceptionPairProviderFlush12004 flush_instruction_cache_override = nullptr;
};
struct ConceptionPairProviderDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kConceptionPairProviderPatchBytes12004> original{};
  void *memory_context = nullptr;
  ConceptionPairProviderFree12004 virtual_free = nullptr;
  ConceptionPairProviderProtect12004 virtual_protect = nullptr;
  ConceptionPairProviderFlush12004 flush_instruction_cache = nullptr;
};
enum ConceptionPairProviderInstallFailure12004 : std::uint32_t {
  conception_provider_install_exact_build = 1U << 0,
  conception_provider_install_quiescence = 1U << 1,
  conception_provider_install_binding = 1U << 2,
  conception_provider_install_already_installed = 1U << 3,
  conception_provider_install_anchor = 1U << 4,
  conception_provider_install_allocation = 1U << 5,
  conception_provider_install_protection = 1U << 6,
  conception_provider_install_flush = 1U << 7,
  conception_provider_install_rollback = 1U << 8,
};
enum ConceptionPairProviderCaptureFailure12004 : std::uint32_t {
  conception_provider_capture_output_before = 1U << 0,
  conception_provider_capture_output_after = 1U << 1,
  conception_provider_capture_identity_before = 1U << 2,
  conception_provider_capture_identity_after = 1U << 3,
  conception_provider_capture_parent_changed = 1U << 4,
  conception_provider_capture_event_coordinate = 1U << 5,
  conception_provider_capture_attach = 1U << 6,
};

struct ConceptionPairProviderObservations12004 {
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::vector<ConceptionPairProviderObservation12004> events;
};

ConceptionPairProviderBindings12004 BindConceptionPairProviderImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallConceptionPairProviderPassive12004(
    ConceptionPairProviderDetourState12004 &,
    const ConceptionPairProviderInstallEnvironment12004 &,
    std::string_view executable_sha256) noexcept;
bool UninstallConceptionPairProviderPassive12004(
    ConceptionPairProviderDetourState12004 &, bool primary_thread_suspended_proven) noexcept;
std::optional<ConceptionPairProviderObservations12004> ReadConceptionPairProviderObservations12004(
    std::uintptr_t clock_identity = 0, std::uint64_t parent_scope_id = 0) noexcept;
std::string SerializeConceptionPairProviderObservation12004(
    const ConceptionPairProviderObservation12004 &);
extern "C" void *__fastcall XarConceptionPairProviderHook12004(
    void *output, void *first, void *second, std::uint32_t mode, void *fifth) noexcept;

// A new connected local fixture supplies a typed stand-in original. It never
// installs a patch or executes/replays the CK3 provider body.
bool InitializeConceptionPairProviderFixture12004(
    const ConceptionPairProviderBindings12004 &, ConceptionPairProviderOriginal12004) noexcept;
void *InvokeConceptionPairProviderFixture12004(
    std::uintptr_t caller_return_rva, void *output, void *first, void *second,
    std::uint32_t mode, void *fifth) noexcept;
bool RunConceptionPairProviderPassiveFixture12004() noexcept;

} // namespace xar::ck3_12004
