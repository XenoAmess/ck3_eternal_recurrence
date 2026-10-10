#pragma once

#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include "xar_bridge/person_installed_transfer_stage_12004.hpp"

#include <cstdint>
#include <limits>
#include <optional>
#include <string>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kLifestyleFinalC8CallRva12004 = 0x372E34D;
inline constexpr std::uintptr_t kLifestyleFinalC8ReturnRva12004 = 0x372E353;
inline constexpr std::uintptr_t kLifestyleFinalC8ConsumerReturnRva12004 = 0x31EC060;

// Copies supplied by the existing guarded same-query producer. This helper does
// not read a native object, invoke a virtual function or allocate an event.
// A source-projected scope can accompany an actual Perk+80 class/slot copy; it
// cannot claim the original RDX internal aliases or a natural call.
struct LifestyleFinalC8CopiedInputs12004 {
  SourceReadFrame12004 query_frame;
  std::optional<std::uint32_t> module_image_size;
  std::uintptr_t selected_perk_identity = 0;
  std::optional<std::uint32_t> character_full_id;
  std::optional<std::uintptr_t> receiver_identity, vtable_identity, target_identity;
  std::optional<std::uint16_t> scope_root_word;
  std::optional<std::uint64_t> scope_full_id_payload;
  std::optional<std::uintptr_t> scope_payload_identity;
  std::optional<PrisonerQuoteInternalAliases12004> physical_aliases;
  bool class_slot_copied = false;
  bool scope_is_source_projection = false;
  friend bool operator==(const LifestyleFinalC8CopiedInputs12004 &,
                         const LifestyleFinalC8CopiedInputs12004 &) = default;
};

struct LifestyleFinalC8RawSource12004 {
  LifestyleFinalC8CopiedInputs12004 copied;
  std::optional<std::uintptr_t> vtable_rva, slot_identity, target_rva;
  bool query_frame_bound = false;
  bool receiver_is_selected_perk_plus80 = false;
  bool raw_target_source_capture_ready = false;
  bool physical_aliases_complete = false;
  bool physical_character_scope_matches = false;
  std::string unavailable_reason;
  friend bool operator==(const LifestyleFinalC8RawSource12004 &,
                         const LifestyleFinalC8RawSource12004 &) = default;
};

namespace lifestyle_final_c8_detail {
inline std::optional<std::uintptr_t> ImageRva(
    const SourceReadFrame12004 &frame, std::optional<std::uint32_t> image_size,
    std::optional<std::uintptr_t> address, std::size_t width) noexcept {
  if (!image_size || *image_size == 0 || !address || *address < frame.module_base)
    return {};
  const auto rva = *address - frame.module_base;
  if (rva >= *image_size || width > static_cast<std::size_t>(*image_size) - rva)
    return {};
  return rva;
}
inline bool QueryReady(const SourceReadFrame12004 &frame) noexcept {
  return SourceReadFrameReady12004(frame) && frame.native_revision != 0 &&
      frame.query_sequence != 0 && frame.proof_epoch != 0 && frame.date_raw.has_value();
}
inline bool CharacterScopeMatches(const LifestyleFinalC8CopiedInputs12004 &in) noexcept {
  return in.character_full_id && *in.character_full_id != 0 &&
      *in.character_full_id != 0xFFFFFFFFU && in.scope_root_word &&
      *in.scope_root_word == 4 && in.scope_full_id_payload &&
      *in.scope_full_id_payload == static_cast<std::uint64_t>(*in.character_full_id);
}
inline bool PhysicalAliasesComplete(const LifestyleFinalC8CopiedInputs12004 &in) noexcept {
  if (!in.physical_aliases || in.scope_is_source_projection) return false;
  const auto &a = *in.physical_aliases;
  return a.physical_aliases_copied && a.internal_identity && *a.internal_identity != 0 &&
      a.primary_scope && *a.primary_scope != 0 && a.secondary_scope &&
      *a.secondary_scope == 0 && a.tertiary_scope && *a.tertiary_scope == *a.primary_scope &&
      a.support118_identity && *a.support118_identity != 0 &&
      a.evaluation_flag_raw_u8.has_value() && a.primary_scope_root_word &&
      in.scope_root_word && *a.primary_scope_root_word == *in.scope_root_word &&
      *a.primary_scope <= (std::numeric_limits<std::uintptr_t>::max)() - 8 &&
      in.scope_payload_identity && *in.scope_payload_identity == *a.primary_scope + 8;
}
inline bool EventReady(const PersonInstalledTransferEvent12004 &event) noexcept {
  return event.clock_identity != 0 && event.sequence != 0 &&
      event.thread_id.has_value() && *event.thread_id != 0;
}
inline bool SameEvent(const PersonInstalledTransferEvent12004 &left,
                      const PersonInstalledTransferEvent12004 &right) noexcept {
  return left.clock_identity == right.clock_identity &&
      left.sequence == right.sequence && left.thread_id == right.thread_id;
}
inline bool OrderedEvent(const PersonInstalledTransferEvent12004 &left,
                         const PersonInstalledTransferEvent12004 &right) noexcept {
  return EventReady(left) && EventReady(right) &&
      left.clock_identity == right.clock_identity && left.thread_id == right.thread_id &&
      left.sequence < right.sequence;
}
} // namespace lifestyle_final_c8_detail

// Raw target eligibility is useful for the separately assigned bounded source
// claim. It says nothing about whether the C8 call was reached or returned true.
inline LifestyleFinalC8RawSource12004 BindLifestyleFinalC8RawSource12004(
    const LifestyleFinalC8CopiedInputs12004 &in) noexcept {
  LifestyleFinalC8RawSource12004 out{};
  try {
    out.copied = in;
    out.query_frame_bound = lifestyle_final_c8_detail::QueryReady(in.query_frame);
    out.receiver_is_selected_perk_plus80 = in.selected_perk_identity != 0 &&
        in.selected_perk_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 0x80 &&
        in.receiver_identity && *in.receiver_identity == in.selected_perk_identity + 0x80;
    if (in.vtable_identity && *in.vtable_identity != 0 &&
        *in.vtable_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 0xC8)
      out.slot_identity = *in.vtable_identity + 0xC8;
    out.vtable_rva = lifestyle_final_c8_detail::ImageRva(
        in.query_frame, in.module_image_size, in.vtable_identity, 0xD0);
    out.target_rva = lifestyle_final_c8_detail::ImageRva(
        in.query_frame, in.module_image_size, in.target_identity, 1);
    out.raw_target_source_capture_ready = out.query_frame_bound &&
        out.receiver_is_selected_perk_plus80 && in.class_slot_copied &&
        in.character_full_id && *in.character_full_id != 0 &&
        *in.character_full_id != 0xFFFFFFFFU && out.vtable_rva && out.target_rva;
    out.physical_aliases_complete = lifestyle_final_c8_detail::PhysicalAliasesComplete(in);
    out.physical_character_scope_matches = out.physical_aliases_complete &&
        lifestyle_final_c8_detail::CharacterScopeMatches(in);
    out.unavailable_reason = out.raw_target_source_capture_ready
        ? "final_c8_raw_target_only_return_witness_unavailable"
        : "final_c8_same_query_class_target_copy_incomplete";
  } catch (...) {
    out.raw_target_source_capture_ready = false;
    out.physical_aliases_complete = false;
    out.physical_character_scope_matches = false;
    out.unavailable_reason = "final_c8_copied_input_binding_failed";
  }
  return out;
}

// This carrier belongs to an actual original-call boundary producer. That
// producer must copy the current borrowed query cursor and shared13 events.
// No currently held47d/16d packet supplies it. A query snapshot, a software18
// scope, a parent can_select bool or an unrelated Person event cannot supply it.
struct LifestyleFinalC8NaturalWitness12004 {
  LifestyleFinalC8CopiedInputs12004 entry_inputs;
  PersonInstalledTransferEvent12004 query_cursor, call_event, return_event, consumer_event;
  std::uintptr_t call_rva = 0, return_rva = 0, consumer_return_rva = 0;
  std::uintptr_t original_rcx_receiver = 0, original_rdx_aliases = 0;
  std::uintptr_t original_rax_vtable = 0, original_c8_target_identity = 0;
  std::optional<std::uint8_t> original_returned_al, original_consumer_al;
  std::uint32_t original_matching_call_count = 0;
  bool original_call_observed = false;
  bool original_return_observed = false;
  bool original_consumer_observed = false;
};

struct LifestyleFinalC8ReturnedSource12004 {
  std::optional<std::uint8_t> returned_raw_u8;
  std::optional<bool> consumer_test_al_value;
  bool actual_original_call_observed = false;
  bool source_value_ready = false;
  std::string unavailable_reason;
};

// expected_query_cursor is copied by the actual query owner from the shared13
// domain at this borrowed original Validate invocation. The function does not
// request an event and does not accept a boolean substitute for original AL.
inline LifestyleFinalC8ReturnedSource12004 BindLifestyleFinalC8NaturalReturn12004(
    const LifestyleFinalC8RawSource12004 &raw,
    const PersonInstalledTransferEvent12004 &expected_query_cursor,
    const LifestyleFinalC8NaturalWitness12004 &witness) noexcept {
  LifestyleFinalC8ReturnedSource12004 out{};
  try {
    if (!raw.raw_target_source_capture_ready || !raw.physical_character_scope_matches ||
        raw.copied != witness.entry_inputs ||
        !lifestyle_final_c8_detail::EventReady(expected_query_cursor) ||
        !lifestyle_final_c8_detail::SameEvent(expected_query_cursor, witness.query_cursor) ||
        !lifestyle_final_c8_detail::OrderedEvent(witness.query_cursor, witness.call_event) ||
        !lifestyle_final_c8_detail::OrderedEvent(witness.call_event, witness.return_event) ||
        !lifestyle_final_c8_detail::OrderedEvent(witness.return_event, witness.consumer_event) ||
        witness.call_rva != kLifestyleFinalC8CallRva12004 ||
        witness.return_rva != kLifestyleFinalC8ReturnRva12004 ||
        witness.consumer_return_rva != kLifestyleFinalC8ConsumerReturnRva12004 ||
        witness.original_matching_call_count != 1 ||
        !witness.original_call_observed || !witness.original_return_observed ||
        !witness.original_consumer_observed || !raw.copied.receiver_identity ||
        witness.original_rcx_receiver != *raw.copied.receiver_identity ||
        !raw.copied.vtable_identity || !raw.copied.target_identity ||
        witness.original_rax_vtable != *raw.copied.vtable_identity ||
        witness.original_c8_target_identity != *raw.copied.target_identity ||
        !raw.copied.physical_aliases || !raw.copied.physical_aliases->internal_identity ||
        witness.original_rdx_aliases != *raw.copied.physical_aliases->internal_identity ||
        !witness.original_returned_al || !witness.original_consumer_al ||
        *witness.original_returned_al != *witness.original_consumer_al) {
      out.unavailable_reason = "final_c8_original_call_return_consumer_provenance_unavailable";
      return out;
    }
    out.returned_raw_u8 = witness.original_returned_al;
    // Closed MOVZX/DIL/BL forwarding preserves the byte; only31EC060 TEST AL
    // converts it. This is the selected child output, not whole288AE00 legality.
    out.consumer_test_al_value = *out.returned_raw_u8 != std::uint8_t{0};
    out.actual_original_call_observed = true;
    out.source_value_ready = true;
  } catch (...) {
    out.returned_raw_u8.reset();
    out.consumer_test_al_value.reset();
    out.actual_original_call_observed = false;
    out.source_value_ready = false;
    out.unavailable_reason = "final_c8_original_witness_binding_failed";
  }
  return out;
}

} // namespace xar::ck3_12004
