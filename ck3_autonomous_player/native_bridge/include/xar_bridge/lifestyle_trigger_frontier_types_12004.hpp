#pragma once

#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include "xar_bridge/trigger_scope_table_provider_3795a60_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {

inline constexpr const char *kLifestyleTriggerFrontierKey12004 =
    "lifestyle_perk_trigger_frontier_12004";
inline constexpr const char *kLifestyleTriggerFrontierSchema12004 =
    "lifestyle-perk-trigger-frontier-12004-v1";

// Owned copies from the existing ReadOne command before its existing Validate.
// The Perk key is the full pointer identity used by the reached native source.
// No numeric Perk ID or natural scope address is inferred from it.
struct LifestyleTriggerTargetCopy12004 {
  std::optional<std::uintptr_t> slot_identity, target_identity, target_rva;
  bool copied = false;
  std::string unavailable_reason;
  friend bool operator==(const LifestyleTriggerTargetCopy12004 &,
                         const LifestyleTriggerTargetCopy12004 &) = default;
};

struct LifestyleTriggerFrontierInputs12004 {
  SourceReadFrame12004 read_frame;
  std::optional<std::uint32_t> module_image_size, module_time_date_stamp;
  std::uint64_t public_revision = 0;
  std::optional<bool> mailbox_before_accepted, mailbox_after_accepted;
  std::string target_key;
  // Copied from the existing producer's offline_fixture scope. Populated
  // owned-memory test addresses are not actual application target evidence.
  std::string capture_scope = "unavailable";
  std::uintptr_t command_identity = 0, selected_perk_identity = 0;
  std::uint32_t requested_full_character_id = 0xFFFFFFFFU;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uint32_t> selected_character_full_id;
  std::optional<std::uintptr_t> receiver_identity, vtable_identity, vtable_rva;
  LifestyleTriggerTargetCopy12004 slot58, slot60, slotc8;
  // These scalar values are copied from the SAME reached source trace only.
  // A source-equivalent constructor does not supply natural aliases.
  std::optional<std::uint16_t> source_context_root_word;
  std::optional<std::uint64_t> source_context_full_id_payload;
  bool context_is_source_projection = false;
  std::optional<TriggerScopeTableProviderRaw3795A6012004> descriptor_provider;
  bool caller_before_after_confirmed = false;
  bool repeated_raw_match = false;
  std::optional<bool> native_before, native_after;
  std::string unavailable_reason;
};

// No current generic query producer supplies an original return-event witness.
// This typed plane is reserved for a real original-once observer; no leaf may
// allocate a clock or substitute query_sequence/proof_epoch for these events.
struct LifestyleTriggerNaturalEvent12004 {
  std::uint64_t clock_identity = 0, sequence = 0;
  std::optional<std::uint32_t> thread_id;
  friend bool operator==(const LifestyleTriggerNaturalEvent12004 &,
                         const LifestyleTriggerNaturalEvent12004 &) = default;
};
struct LifestyleTriggerNaturalWitness12004 {
  SourceReadFrame12004 read_frame;
  LifestyleTriggerNaturalEvent12004 query_cursor, call_event, return_event;
  std::uintptr_t call_rva = 0, return_rva = 0;
  std::uintptr_t selected_perk_identity = 0, receiver_identity = 0, target_identity = 0;
  std::uintptr_t original_rcx = 0, original_rdx = 0;
  std::optional<std::uint16_t> original_root_word;
  std::optional<std::uint64_t> original_full_id_payload;
  std::optional<std::uint8_t> returned_raw_u8;
  std::optional<std::uint16_t> returned_raw_u16;
  std::optional<std::uint64_t> returned_qword0, returned_qword1;
  std::uint32_t original_matching_call_count = 0;
  bool original_call_observed = false, original_return_observed = false;
};

struct LifestyleTriggerClosedTargetProof12004 {
  std::uintptr_t target_rva = 0;
  std::string exact_source_sha256, producer_key;
  bool complete_pure_readonly_body = false;
};

// Each lane owns its actual output producer. Raw target readiness only permits
// a bounded source claim. A returned value requires its own concrete proof.
struct LifestyleTriggerLaneSource12004 {
  std::string lane;
  std::uintptr_t call_rva = 0, return_rva = 0;
  LifestyleTriggerTargetCopy12004 target;
  bool raw_target_ready = false, source_value_ready = false;
  std::optional<std::uint8_t> returned_raw_u8;
  std::optional<std::uint16_t> returned_raw_u16;
  std::optional<std::uint64_t> returned_qword0, returned_qword1;
  std::string result_source = "unavailable";
  std::optional<LifestyleTriggerClosedTargetProof12004> closed_target_proof;
  std::optional<LifestyleTriggerNaturalWitness12004> natural_witness;
  std::string unavailable_reason;
};

struct LifestyleTriggerFrontierPacket12004 {
  LifestyleTriggerFrontierInputs12004 inputs;
  LifestyleTriggerLaneSource12004 descriptor_al, root_kind_ax, root_mask_qwords, final_c8_al;
  // Independent of native can_select and of all four returned output planes.
  bool copied_input_binding_ready = false;
};

// Unique lane owners implement these adapters. They consume the one copied
// class/slot packet. The reader is for concrete source-closed target operands,
// never for a second vptr/slot capture or an active target invocation.
LifestyleTriggerLaneSource12004 ReadLifestyleDescriptorFrontier12004(
    const SourceLeafReadOnlyAccess12004 &, const LifestyleTriggerFrontierInputs12004 &) noexcept;
LifestyleTriggerLaneSource12004 ReadLifestyleRootKindFrontier12004(
    const SourceLeafReadOnlyAccess12004 &, const LifestyleTriggerFrontierInputs12004 &) noexcept;
LifestyleTriggerLaneSource12004 ReadLifestyleRootMaskFrontier12004(
    const SourceLeafReadOnlyAccess12004 &, const LifestyleTriggerFrontierInputs12004 &) noexcept;
LifestyleTriggerLaneSource12004 ReadLifestyleFinalC8Frontier12004(
    const SourceLeafReadOnlyAccess12004 &, const LifestyleTriggerFrontierInputs12004 &) noexcept;

// Does not read objects or request an event. An actual mailbox refusal clears
// admission/output credit while retaining all copied raw facts.
void FinalizeLifestylePerkTriggerFrontier12004(
    LifestyleTriggerFrontierPacket12004 &, bool actual_mailbox_accepted) noexcept;
std::string SerializeLifestylePerkTriggerFrontier12004(
    const std::optional<LifestyleTriggerFrontierPacket12004> &);

} // namespace xar::ck3_12004
