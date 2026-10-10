#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Actual4 literal source, sealed before this leaf was authored.
inline constexpr std::uintptr_t kPersonInstalledTransferRva12004 = 0x291CF30;
inline constexpr std::uintptr_t kPersonInstalledTransferCallerReturnRva12004 =
    0x2A3DC49;

using PersonInstalledTransferRead12004 = bool (*)(
    void *, std::uintptr_t, void *, std::size_t) noexcept;

// Root supplies one process-local natural-event clock. This leaf owns no clock
// or journal and does not compare its events with the Native65 capture counter.
struct PersonInstalledTransferEvent12004 {
  std::uintptr_t clock_identity = 0;
  std::uint64_t sequence = 0;
  std::optional<std::uint32_t> thread_id;
};

struct PersonInstalledTransferPreparation12004 {
  bool observed = false;
  bool preparation_capture_complete = false;
  std::uint64_t preparation_capture_sequence = 0;
  std::optional<std::uint32_t> preparation_capture_thread_id;
  std::optional<std::uint32_t> preparation_completion_thread_id;
  std::optional<std::uintptr_t> preparation_character_identity;
  std::optional<std::uintptr_t> preparation_model_identity;
  std::optional<std::uintptr_t> preparation_context_identity;
  std::optional<std::uintptr_t> preparation_owner_character_identity;
  std::optional<std::uint32_t> preparation_owner_character_id;
};

using PersonInstalledTransferPreparationReader12004 =
    PersonInstalledTransferPreparation12004 (*)(
        void *, std::uintptr_t, std::uint32_t) noexcept;
using PersonInstalledTransferEventReader12004 =
    PersonInstalledTransferEvent12004 (*)(void *) noexcept;

struct PersonInstalledTransferStage12004;
using PersonInstalledTransferObserver12004 = void (*)(
    void *, const PersonInstalledTransferStage12004 &) noexcept;

struct PersonInstalledTransferBindings12004 {
  void *read_context = nullptr;
  PersonInstalledTransferRead12004 read = nullptr;
  void *preparation_context = nullptr;
  PersonInstalledTransferPreparationReader12004 read_preparation = nullptr;
  void *event_context = nullptr;
  PersonInstalledTransferEventReader12004 next_event = nullptr;
  // Borrowed only for this invocation. Observers copy memory at the existing
  // original boundary; they own no native call, clock or retained global state.
  void *physical_observer_context = nullptr;
  PersonInstalledTransferObserver12004 before_original_observer = nullptr;
  PersonInstalledTransferObserver12004 after_original_observer = nullptr;
};

struct PersonInstalledTransferSnapshot12004 {
  std::optional<std::uintptr_t> model_a_owner_identity;
  std::optional<std::uint32_t> model_a_owner_character_id;
  std::optional<std::uintptr_t> model_b_owner_identity;
  std::optional<std::uint32_t> model_b_owner_character_id;
  // This is the immutable pre-transfer B owner, not a claimed Entry selection.
  std::optional<std::uintptr_t> observed_owner_identity;
  std::optional<std::uint32_t> observed_owner_character_id;
  std::optional<std::uintptr_t> carrier_identity;
  std::optional<std::uintptr_t> installed_model_identity;
  std::optional<std::uintptr_t> installed_model_owner_identity;
  std::optional<bool> installed_owner_matches_observed_owner;
  std::optional<bool> installed_model_is_a;
  std::optional<bool> installed_model_is_b;
  std::optional<std::uintptr_t> matching_installed_inline_context_identity;
};

struct PersonInstalledTransferStage12004 {
  bool observed = false;
  bool original_called = false;
  bool original_returned = false;
  std::string_view reason = "paired_transfer_unobserved";
  std::uintptr_t model_a_identity = 0;
  std::uintptr_t model_b_identity = 0;
  std::uintptr_t original_return_rva = 0;
  PersonInstalledTransferEvent12004 before_event;
  PersonInstalledTransferEvent12004 completed_event;
  PersonInstalledTransferPreparation12004 preparation;
  PersonInstalledTransferSnapshot12004 before;
  PersonInstalledTransferSnapshot12004 after;
  std::optional<bool> preparation_model_is_b;
  std::optional<bool> preparation_owner_matches_before;
  std::optional<bool> preparation_owner_matches_after;
  std::optional<bool> before_after_owner_generation_equal;
  std::optional<bool> event_clock_and_thread_match;
  std::optional<bool> completion_ordered_after_begin;
  // No generic-container or transfer-to-Entry success is inferred here.
};

#if defined(_MSC_VER)
using PersonInstalledTransferOriginal12004 =
    std::uintptr_t(__fastcall *)(void *, void *);
#else
using PersonInstalledTransferOriginal12004 =
    std::uintptr_t (*)(void *, void *);
#endif

struct PersonInstalledTransferInvocation12004 {
  std::uintptr_t raw_return_bits = 0;
  PersonInstalledTransferStage12004 stage;
};

// Called by Root's natural detour and its connected fixture. Copies identities
// around the original once, without invoking a getter/preparation/container.
// Root alone installs the detour and joins its record with the Entry stage.
PersonInstalledTransferInvocation12004 InvokePersonInstalledTransferStage12004(
    const PersonInstalledTransferBindings12004 &bindings,
    PersonInstalledTransferOriginal12004 original,
    void *model_a, void *model_b, std::uintptr_t original_return_rva) noexcept;

} // namespace xar::ck3_12004
