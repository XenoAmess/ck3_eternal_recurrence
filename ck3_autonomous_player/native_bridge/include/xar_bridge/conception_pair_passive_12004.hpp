#pragma once

#include "xar_bridge/conception_sample_passive_12004.hpp"
#include "xar_bridge/conception_pair_provider_passive_12004.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#include <windows.h>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kConceptionPairPassiveRva12004 = 0x2929B40;
inline constexpr std::size_t kConceptionPairPassivePatchBytes12004 = 19;
inline constexpr std::size_t kConceptionPairPassiveAbsoluteJumpBytes12004 = 14;
inline constexpr std::size_t kConceptionPairPassiveJournalCapacity12004 = 256;
inline constexpr std::string_view kConceptionPairPassiveSourcePin12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

struct ConceptionPairCharacterFacts12004 {
  std::uintptr_t character = 0;
  std::optional<std::uint32_t> full_id, magic;
  std::optional<std::uint8_t> native_sex_1a1;
  std::optional<std::uintptr_t> extended_pointer;
  std::optional<std::uint64_t> extended_288_raw;
  std::optional<bool> extended_288_blocks;
  std::optional<std::uint8_t> pending_3e8_raw;
  std::optional<std::uintptr_t> pending_3f0_raw;
};
struct ConceptionPairSourceCopies12004 {
  std::optional<std::int64_t> scalar_5c69ec8_raw;
  std::optional<std::int64_t> lower_5c69f00_raw, upper_5c69f10_raw;
  // These copies do not sample the original MOV instruction's consumed value.
  bool actual_original_consumed_values = false;
};
struct ConceptionPairPassiveEvent12004 {
  std::string_view source_pin = kConceptionPairPassiveSourcePin12004;
  std::uint64_t journal_sequence = 0;
  std::uintptr_t caller_return_pc = 0;
  std::optional<std::uint64_t> caller_return_rva;
  std::uint32_t process_id = 0, thread_id = 0;
  PersonInstalledTransferEvent12004 before_event{}, completed_event{};
  std::uintptr_t first_character = 0, second_character = 0, sample_receiver = 0;
  std::int64_t original_r9_modifier = 0;
  ConceptionPairCharacterFacts12004 first_before{}, second_before{};
  ConceptionPairCharacterFacts12004 first_after{}, second_after{};
  std::optional<std::array<std::uint32_t, 2>> sample_state_before, sample_state_after;
  ConceptionPairSourceCopies12004 source_before{}, source_after{};
  bool original_called_once = false, original_returned = false;
  std::optional<std::uint64_t> original_rax_bits;
  std::optional<std::uint8_t> original_al;
  std::optional<bool> generation_unchanged;
  // Independent copied pattern, never a pregnancy or proof that value changed.
  std::optional<bool> first_post_pending_matches_write_pattern;
  bool event_clock_and_thread_match = false;
  std::optional<ConceptionPairProviderObservation12004> provider;
  std::optional<ConceptionSampleObservation12004> sample;
  std::uint32_t duplicate_provider_returns = 0, duplicate_sample_returns = 0;
  bool fixture_origin = false;
};
struct ConceptionPairPassiveJournal12004 {
  bool observer_installed = false, current_session_guard = false;
  std::uintptr_t clock_identity = 0;
  std::uintptr_t image_base = 0;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0, unattributed_identity_events = 0;
  std::vector<ConceptionPairPassiveEvent12004> events;
};

// AL-only source return; the wrapper preserves all unspecified RAX bits too.
using ConceptionPairPassiveOriginalV1 = std::uint64_t(__fastcall *)(
    void *, void *, void *, std::int64_t);
using ConceptionPairPassiveReadMemoryV1 = bool (*)(
    void *, const void *, void *, std::size_t) noexcept;
using ConceptionPairPassiveVirtualAllocV1 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ConceptionPairPassiveVirtualFreeV1 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ConceptionPairPassiveVirtualProtectV1 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ConceptionPairPassiveFlushV1 = bool (*)(void *, const void *, std::size_t) noexcept;
struct ConceptionPairPassiveBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ConceptionPairPassiveReadMemoryV1 read_memory = nullptr;
  void *event_context = nullptr;
  PersonInstalledTransferEventReader12004 next_event = nullptr;
};
struct ConceptionPairPassiveInstallEnvironmentV1 {
  bool primary_thread_suspended_proven = false;
  ConceptionPairPassiveBindingsV1 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ConceptionPairPassiveVirtualAllocV1 virtual_alloc_override = nullptr;
  ConceptionPairPassiveVirtualFreeV1 virtual_free_override = nullptr;
  ConceptionPairPassiveVirtualProtectV1 virtual_protect_override = nullptr;
  ConceptionPairPassiveFlushV1 flush_instruction_cache_override = nullptr;
};
struct ConceptionPairPassiveDetourStateV1 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kConceptionPairPassivePatchBytes12004> original{};
  void *memory_context = nullptr;
  ConceptionPairPassiveVirtualFreeV1 virtual_free = nullptr;
  ConceptionPairPassiveVirtualProtectV1 virtual_protect = nullptr;
  ConceptionPairPassiveFlushV1 flush_instruction_cache = nullptr;
};
enum ConceptionPairPassiveInstallFailureV1 : std::uint32_t {
  conception_pair_passive_install_none = 0,
  conception_pair_passive_install_exact_build = 1U << 0,
  conception_pair_passive_install_quiescence = 1U << 1,
  conception_pair_passive_install_already_installed = 1U << 2,
  conception_pair_passive_install_anchor = 1U << 3,
  conception_pair_passive_install_allocation = 1U << 4,
  conception_pair_passive_install_protection = 1U << 5,
  conception_pair_passive_install_flush = 1U << 6,
  conception_pair_passive_install_rollback = 1U << 7,
};
ConceptionPairPassiveBindingsV1 BindConceptionPairPassiveImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    ConceptionPairPassiveReadMemoryV1, void *read_context = nullptr) noexcept;
bool InstallConceptionPairPassiveObserver12004(
    ConceptionPairPassiveDetourStateV1 &,
    const ConceptionPairPassiveInstallEnvironmentV1 &,
    std::string_view executable_sha256) noexcept;

// Borrowed TLS scope exists only while the genuine native original executes.
// Shared18 scope is the single parent type; no independent event clock/TLS.
bool ReadConceptionPairParentScope12004(
    void *, ConceptionSampleParentScope12004 &) noexcept;
bool AttachConceptionPairProviderFacts12004(
    void *, const ConceptionPairProviderObservation12004 &) noexcept;
void AttachConceptionPairSampleFacts12004(
    void *, const ConceptionSampleObservation12004 &) noexcept;

// Owned copies only, filtered by full IDs in either native orientation.
// No native source read, clock advance, candidate/RNG or action is performed.
std::optional<ConceptionPairPassiveJournal12004> ReadConceptionPairPassiveForPair12004(
    std::uint32_t household_first_full_id, std::uint32_t household_second_full_id,
    std::uint64_t after_journal_sequence = 0) noexcept;
std::string SerializeConceptionPairPassiveJournal12004(
    const ConceptionPairPassiveJournal12004 &);
extern "C" std::uint64_t __fastcall XarConceptionPairPassiveHook12004V1(
    void *, void *, void *, std::int64_t) noexcept;

// Typed connected-fixture original seam. Native source is never replayed.
bool InitializeConceptionPairPassiveFixture12004(
    const ConceptionPairPassiveBindingsV1 &, ConceptionPairPassiveOriginalV1) noexcept;
std::uint64_t InvokeConceptionPairPassiveFixture12004(
    std::uintptr_t caller_return_pc, void *first, void *second,
    void *sample_receiver, std::int64_t modifier) noexcept;
bool RunConceptionPairPassiveOwnedFixture12004() noexcept;
} // namespace xar::ck3_12004
