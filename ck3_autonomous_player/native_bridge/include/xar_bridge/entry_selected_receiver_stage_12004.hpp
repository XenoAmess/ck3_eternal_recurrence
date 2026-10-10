#pragma once

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

struct PersonSixStageCapture12004DTO;
struct KnightConsumedContext12004;

inline constexpr std::string_view kEntrySelectedReceiverStageSchema12004 =
    "xar.ck3.entry-selected-receiver-stage-12004-v1";

struct EntrySelectedReceiverCall12004 {
  std::optional<std::uint32_t> linked_character_id;
  std::optional<std::uintptr_t> linked_character_identity;
  std::uint32_t consumption_thread_id = 0;
};

// Owned facts from one actual consumed-Ci return. This is neither the current
// installed-model census nor an inference that physical Entry writeback ran.
struct EntrySelectedReceiverStage12004 {
  std::uint16_t property_key = 0;
  std::uint64_t consumed_return_rva = 0;
  bool exact_consumed_callsite = false;
  bool exact_capture_build = false;
  std::string_view observation_stage = "actual_effectiveness_context_return";
  std::string_view preparation_stage = "unobserved";
  std::optional<std::uint32_t> linked_character_id;
  std::optional<std::uintptr_t> linked_character_identity;
  std::optional<std::uint32_t> selected_character_id;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uintptr_t> getter_context_identity;
  bool preparation_capture_observed = false;
  bool preparation_capture_complete = false;
  bool preparation_raw_counts_ready = false;
  std::uint8_t preparation_stage_observed_mask = 0;
  std::uint64_t preparation_capture_sequence = 0;
  std::optional<std::uintptr_t> preparation_source_return_rva;
  std::optional<std::uint32_t> preparation_capture_thread_id;
  std::optional<std::uint32_t> preparation_completion_thread_id;
  std::uint32_t consumption_thread_id = 0;
  std::optional<std::uintptr_t> preparation_character_identity;
  std::optional<std::uintptr_t> preparation_model_identity;
  std::optional<std::uintptr_t> preparation_context_identity;
  std::optional<std::uintptr_t> preparation_owner_character_identity;
  std::optional<std::uint32_t> preparation_owner_character_id;
  std::optional<bool> capture_sequence_matches_record;
  std::optional<bool> exact_preparation_source_return;
  std::optional<bool> selected_matches_capture_identity;
  std::optional<bool> selected_matches_capture_id;
  std::optional<bool> selected_matches_model_owner_identity;
  std::optional<bool> selected_matches_model_owner_id;
  std::optional<bool> getter_matches_capture_context;
  std::optional<bool> getter_matches_preparation_model_inline;
  std::optional<bool> completion_on_consumption_thread;
  std::optional<bool> completed_post_pc_matches_consumed;
  bool completed_preparation_lineage_proven = false;
  std::string_view reason = "preparation_capture_unobserved";
  friend bool operator==(const EntrySelectedReceiverStage12004 &,
                         const EntrySelectedReceiverStage12004 &) = default;
};

// Call only in the existing InvokeKnightStatContext12004 observation, using its
// owned capture lookup and actual context-return record. No native call, copy,
// capture completion, queue read or new historical lookup is performed here.
EntrySelectedReceiverStage12004 ObserveEntrySelectedReceiverStage12004(
    const PersonSixStageCapture12004DTO &capture,
    const KnightConsumedContext12004 &consumed,
    const EntrySelectedReceiverCall12004 &call) noexcept;

} // namespace xar::ck3_12004
