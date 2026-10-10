#pragma once

#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include "xar_bridge/person_installed_transfer_stage_12004.hpp"
#include "xar_bridge/lifestyle_trigger_frontier_types_12004.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12004 {
enum class SourceTriggerPreferredKindSource12004 { unknown, perk_allow_trigger_80 };
enum class SourceTriggerPreferredKindBasis12004 { unavailable, natural_original_return, specific_target_pure_read };

struct SourceTriggerPreferredKindRaw12004 {
  SourceLeafFrame12004 frame;
  SourceTriggerPreferredKindSource12004 source_kind = SourceTriggerPreferredKindSource12004::unknown;
  std::uintptr_t selected_perk_identity = 0;
  std::string selected_perk_key;
  std::uintptr_t command_identity = 0;
  std::uint32_t requested_full_character_id = 0xFFFFFFFFU;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uint32_t> selected_character_full_id;
  std::optional<std::uint64_t> source_context_full_id_payload;
  bool context_is_source_projection = false;
  std::optional<std::uintptr_t> trigger_receiver, trigger_vptr, slot58_address, slot58_target_va;
  std::optional<std::uint32_t> slot58_target_rva;
  std::optional<std::uint64_t> module_extent_bytes;
  std::optional<std::uint16_t> root_kind_raw_u16;
  // Copied only from a successor's real borrowed scope around existing
  // Validate. SourceReadFrame query_sequence/proof_epoch are never this clock.
  std::optional<PersonInstalledTransferEvent12004> validate_scope_entry_event;
  bool selection_source_qualified = false, raw_source_ready = false;
  std::string unavailable_reason;
};
// Exact operands already copied by the single before-Validate collector.
// Binding this carrier performs no second memory read and creates no AX.
struct SourceTriggerPreferredKindCopiedInputs12004 {
  SourceLeafFrame12004 frame;
  SourceTriggerPreferredKindSource12004 source_kind = SourceTriggerPreferredKindSource12004::unknown;
  std::uintptr_t selected_perk_identity = 0;
  std::string selected_perk_key;
  std::uintptr_t command_identity = 0;
  std::uint32_t requested_full_character_id = 0xFFFFFFFFU;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uint32_t> selected_character_full_id;
  std::optional<std::uint64_t> source_context_full_id_payload;
  bool context_is_source_projection = false;
  std::optional<std::uintptr_t> trigger_receiver, trigger_vptr, slot58_address, slot58_target_va;
  std::optional<std::uint32_t> slot58_target_rva;
  std::optional<std::uint64_t> module_extent_bytes;
  std::optional<std::uint16_t> root_kind_raw_u16;
  std::optional<PersonInstalledTransferEvent12004> validate_scope_entry_event;
  bool selection_source_qualified = false;
};
SourceTriggerPreferredKindRaw12004 BindSourceTriggerPreferredKindCopiedInputs12004(
    const SourceTriggerPreferredKindCopiedInputs12004 &);
SourceTriggerPreferredKindRaw12004 BindLifestyleRootKindFrontierInputs12004(
    const LifestyleTriggerFrontierInputs12004 &);
// This is the admission contract for a future actual native observer record,
// not an existing observer, invocation API, or permission to fabricate AX.
struct SourceTriggerPreferredKindNaturalReturn12004 {
  SourceLeafFrame12004 frame;
  SourceTriggerPreferredKindSource12004 source_kind = SourceTriggerPreferredKindSource12004::unknown;
  std::uintptr_t selected_perk_identity = 0;
  std::string selected_perk_key;
  std::uintptr_t command_identity = 0;
  std::uint32_t requested_full_character_id = 0xFFFFFFFFU;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uint32_t> selected_character_full_id;
  std::optional<std::uint64_t> source_context_full_id_payload;
  std::uintptr_t trigger_receiver = 0, trigger_vptr = 0, slot58_target_va = 0;
  std::uint32_t actual_call_rva = 0, actual_return_rva = 0;
  PersonInstalledTransferEvent12004 validate_scope_entry_event, before_original_event, returned_event;
  std::optional<std::uint64_t> returned_rax_bits;
  // The caller loads [original RDX] after the getter returns at372B4D6.
  // Retain that actual post-return rootWORD and its exact scope identity;
  // a before-Validate copy alone is not that load's returned-stage operand.
  std::uintptr_t root_after_return_scope_identity = 0;
  std::optional<std::uint16_t> root_after_return_raw_u16;
  bool actual_validate_scope_observed = false;
  bool actual_slot58_original_once_observed = false, original_returned = false;
  bool live_observer_binding_verified = false, root_after_return_observed = false;
};

struct SourceTriggerPreferredKindPureValue12004 {
  std::optional<std::uint16_t> preferred_kind_ax_u16;
  bool reached_readonly_source_ready = false;
};
using SourceTriggerPreferredKindPureReader12004 = SourceTriggerPreferredKindPureValue12004 (*)(
    const SourceLeafReadOnlyAccess12004 &, const SourceTriggerPreferredKindRaw12004 &) noexcept;
// A Root-owned specific target implementation must supply this registration
// only after its actual receiver/target and complete necessary source close.
// Closure includes every reached effect: the copied rootWORD must remain the
// caller's post-getter WORD, not merely an entry-stage assumption.
// Its callback is a C++ guarded-memory projector; no native getter pointer is
// cast or called by this leaf. There are currently no registered targets here.
struct SourceTriggerPreferredKindClosedTarget12004 {
  std::uint32_t actual_target_rva = 0;
  std::string complete_source_sha256;
  SourceTriggerPreferredKindSource12004 source_kind = SourceTriggerPreferredKindSource12004::unknown;
  bool exact_target_source_closed = false, native_invocation_free = false;
  SourceTriggerPreferredKindPureReader12004 read_pure = nullptr;
};

struct SourceTriggerPreferredKindResult12004 {
  SourceTriggerPreferredKindRaw12004 raw;
  std::optional<std::uint16_t> preferred_kind_ax_u16;
  SourceTriggerPreferredKindBasis12004 basis = SourceTriggerPreferredKindBasis12004::unavailable;
  bool preferred_kind_source_ready = false, actual_native_original_observed = false;
  bool caller_root_word_source_ready = false;
  std::optional<std::uint16_t> caller_root_word_raw_u16;
  std::string specific_target_source_sha256;
  std::optional<SourceTriggerPreferredKindNaturalReturn12004> natural_return_provenance;
  std::string unavailable_reason;
};
SourceTriggerPreferredKindResult12004 QualifySourceTriggerPreferredKindNaturalReturn12004(
    const SourceTriggerPreferredKindRaw12004 &, const SourceTriggerPreferredKindNaturalReturn12004 &);
SourceTriggerPreferredKindResult12004 ReadSourceTriggerPreferredKindClosedTarget12004(
    const SourceLeafReadOnlyAccess12004 &, const SourceTriggerPreferredKindRaw12004 &,
    const SourceTriggerPreferredKindClosedTarget12004 &);

struct SourceTriggerPreferredKindGate12004 {
  SourceLeafFrame12004 frame;
  std::optional<std::uint16_t> root_kind_raw_u16, preferred_kind_ax_u16;
  bool preferred_kind_source_ready = false, qualified_ready = false;
  std::optional<bool> preferred_kind_matches_root;
  std::optional<std::uint8_t> returned_byte;
  std::string source_branch, unavailable_reason;
};
// Concrete372B4C0 consumer: a qualified nonzero AX matching rootWORD returns
// AL1 before slot60. Zero/mismatch requires the independent mask lane and is
// not an invented rejection or getter-output qualification.
SourceTriggerPreferredKindGate12004 ProjectSourceTriggerPreferredKindGate12004(
    const SourceTriggerPreferredKindResult12004 &);
} // namespace xar::ck3_12004
