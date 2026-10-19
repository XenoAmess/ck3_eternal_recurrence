#pragma once

#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"
#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <array>
#include <iosfwd>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPersonCallbackEntryInputsExeSha12004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
inline constexpr std::array<std::uintptr_t, 9>
    kPersonCallbackEntryGetterReturns12004{
        0x2C06B03, 0x2C06B51, 0x2C06B8D, 0x2C06BC4, 0x2C06BFB,
        0x2C06C32, 0x2C06C69, 0x2C06CA0, 0x2C06CD7};

using PersonCallbackPreparationHistoryReader12004 =
    PersonSixStageCapture12004DTO (*)(
        void *, std::uintptr_t, std::uint32_t) noexcept;

struct PersonCallbackEntryInputsBindings12004 {
  bool exact_image_bound = false;
  void *history_context = nullptr;
  PersonCallbackPreparationHistoryReader12004 read_history = nullptr;
};

struct PersonCallbackEntryInputs12004 {
  std::uintptr_t selected_character_identity = 0;
  std::uint32_t selected_character_id = 0; // Full ID; no index masking.
  std::uintptr_t getter_caller_return_rva = 0;
  // Borrowed existing process clock token, never minted by this input leaf.
  PersonInstalledTransferEvent12004 getter_begin_event;
  bool exact_image_bound = false;
  bool getter_site_observed = false;
  bool entry_event_observed = false;
  // Owned reader result, including its unavailable reason if unobserved.
  // Presence does not mean a preparation occurred or completed.
  std::optional<PersonSixStageCapture12004DTO> preparation_at_entry;
  std::optional<bool> capture_identity_matches_selected;
  std::optional<bool> capture_thread_matches_entry;
  std::optional<bool> completion_thread_matches_entry;
  std::optional<bool> preparation_owner_matches_selected;
  std::string_view reason = "getter_entry_inputs_unobserved";
  friend bool operator==(const PersonCallbackEntryInputs12004 &a,
                         const PersonCallbackEntryInputs12004 &b) {
    return a.selected_character_identity == b.selected_character_identity &&
        a.selected_character_id == b.selected_character_id &&
        a.getter_caller_return_rva == b.getter_caller_return_rva &&
        a.getter_begin_event.clock_identity == b.getter_begin_event.clock_identity &&
        a.getter_begin_event.sequence == b.getter_begin_event.sequence &&
        a.getter_begin_event.thread_id == b.getter_begin_event.thread_id &&
        a.exact_image_bound == b.exact_image_bound &&
        a.getter_site_observed == b.getter_site_observed &&
        a.entry_event_observed == b.entry_event_observed &&
        a.preparation_at_entry == b.preparation_at_entry &&
        a.capture_identity_matches_selected == b.capture_identity_matches_selected &&
        a.capture_thread_matches_entry == b.capture_thread_matches_entry &&
        a.completion_thread_matches_entry == b.completion_thread_matches_entry &&
        a.preparation_owner_matches_selected == b.preparation_owner_matches_selected &&
        a.reason == b.reason;
  }
};

// Reads only the existing immutable Native65 history. No Game memory, native
// getter, Complete, current-query resolver or event-counter call is performed.
PersonCallbackEntryInputsBindings12004 BindPersonCallbackEntryInputs12004(
    std::string_view executable_sha256) noexcept;

// The actual Ci caller invokes this before its sole original getter, using the
// same existing begin token later retained with that getter's completed token.
// Native65 capture_sequence remains an independent history identity.
PersonCallbackEntryInputs12004 CapturePersonCallbackEntryInputs12004(
    const PersonCallbackEntryInputsBindings12004 &bindings,
    std::uintptr_t selected_character_identity,
    std::uint32_t selected_character_id,
    std::uintptr_t actual_getter_caller_return_rva,
    const PersonInstalledTransferEvent12004 &existing_begin_event) noexcept;

// Pure retained sidecar; no history lookup or current-query fallback.
std::string SerializePersonCallbackEntryInputs12004(
    const PersonCallbackEntryInputs12004 &inputs);
// The enclosing serializer supplies its default-format JSON stream. The
// retained preparation is emitted directly, with no temporary JSON string.
void WritePersonCallbackEntryInputs12004(
    std::ostream &out, const PersonCallbackEntryInputs12004 &inputs);

} // namespace xar::ck3_12004
