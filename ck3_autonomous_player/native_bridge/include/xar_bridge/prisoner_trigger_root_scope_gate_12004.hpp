#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include <array>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {
// Complete source372B4C0..372B550: slot58 returns AX, slot60 fills two
// QWORDS. Their actual receiver-specific getter implementations are not held.
struct PrisonerTriggerRootScopeGateConditionalInput12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  std::uintptr_t trigger_identity = 0, primary_scope_identity = 0;
  std::optional<std::uint16_t> root_scope_kind_raw_u16;
  std::optional<std::uint16_t> preferred_kind_return_ax_raw_u16;
  std::optional<std::array<std::uint64_t,2>> mask_return_words_raw_u64;
};
struct PrisonerTriggerRootScopeGateResult12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  std::uintptr_t trigger_identity = 0, primary_scope_identity = 0;
  std::optional<std::uintptr_t> trigger_vptr_raw, slot58_address_raw, slot60_address_raw;
  std::optional<std::uint16_t> root_scope_kind_raw_u16;
  std::optional<std::uint16_t> preferred_kind_return_ax_raw_u16;
  std::optional<std::array<std::uint64_t,2>> mask_return_words_raw_u64;
  bool raw_copy_ready = false, conditional_result_ready = false;
  // This component has no native getter-output producer or truth setter.
  // Conditional supplied values and copied slot addresses cannot qualify it.
  bool getter_output_source_ready = false, qualified_ready = false;
  std::optional<bool> conditional_allows;
  std::optional<std::uint8_t> returned_byte;
  std::string source_branch = "unknown";
  std::string unavailable_reason = "getter_outputs_source_unavailable";
};

// The same literal helper can be reached by other caller domains. Keep their
// existing snapshot identity instead of constructing prisoner role fields.
struct SourceTriggerRootScopeGateConditionalInput12004 {
  SourceLeafFrame12004 frame{};
  std::optional<std::uint16_t> root_scope_kind_raw_u16;
  std::optional<std::uint16_t> preferred_kind_return_ax_raw_u16;
  std::optional<std::array<std::uint64_t,2>> mask_return_words_raw_u64;
};
struct SourceTriggerRootScopeGateResult12004 {
  SourceLeafFrame12004 frame{};
  std::uintptr_t trigger_identity = 0, primary_scope_identity = 0;
  std::optional<std::uintptr_t> trigger_vptr_raw, slot58_address_raw, slot60_address_raw;
  std::optional<std::uint16_t> root_scope_kind_raw_u16;
  std::optional<std::uint16_t> preferred_kind_return_ax_raw_u16;
  std::optional<std::array<std::uint64_t,2>> mask_return_words_raw_u64;
  bool raw_copy_ready = false, conditional_result_ready = false;
  bool getter_output_source_ready = false, qualified_ready = false;
  std::optional<bool> conditional_allows;
  std::optional<std::uint8_t> returned_byte;
  std::string source_branch = "unknown";
  std::string unavailable_reason = "getter_outputs_source_unavailable";
};

namespace detail {
template<class Result>
inline void CopyTriggerRootScopeGateRaw12004(Result &out,
    const PrisonerQuoteReadOnlyAccess12004 &access) {
  out.root_scope_kind_raw_u16 = ReadPrisonerQuoteSource12004<std::uint16_t>(access,out.primary_scope_identity);
  out.trigger_vptr_raw = ReadPrisonerQuoteSource12004<std::uintptr_t>(access,out.trigger_identity);
  if (out.trigger_vptr_raw && *out.trigger_vptr_raw != 0) {
    out.slot58_address_raw = ReadPrisonerQuoteSource12004<std::uintptr_t>(access,*out.trigger_vptr_raw,0x58);
    out.slot60_address_raw = ReadPrisonerQuoteSource12004<std::uintptr_t>(access,*out.trigger_vptr_raw,0x60);
  }
  out.raw_copy_ready = out.root_scope_kind_raw_u16.has_value() &&
      out.trigger_vptr_raw.has_value() && out.slot58_address_raw.has_value() && out.slot60_address_raw.has_value();
  if (!out.raw_copy_ready) out.unavailable_reason = "root_or_trigger_slot_copy_partial";
}

template<class Result>
inline void ProjectTriggerRootScopeGateConditional12004(Result &out) {
  if (!out.root_scope_kind_raw_u16 || !out.preferred_kind_return_ax_raw_u16) {
    out.unavailable_reason = "conditional_scope_or_preferred_kind_missing"; return;
  }
  const auto root = *out.root_scope_kind_raw_u16;
  const auto preferred = *out.preferred_kind_return_ax_raw_u16;
  if (preferred != 0 && preferred == root) {
    out.conditional_allows = true; out.source_branch = "preferred_kind_match";
  } else if (!out.mask_return_words_raw_u64) {
    out.unavailable_reason = "conditional_mask_getter_output_missing"; return;
  } else {
    const auto &mask = *out.mask_return_words_raw_u64;
    if (mask[0] == 0 && mask[1] == 0) {
      out.conditional_allows = true; out.source_branch = "empty_mask";
    } else if (root == 0) {
      out.conditional_allows = false; out.source_branch = "zero_kind_nonempty_mask";
    } else if (root > 128) {
      // Native indexes beyond the source-proved two-word local mask here.
      // Preserve unknown; no out-of-bounds read and no invented rejection.
      out.unavailable_reason = "conditional_kind_outside_known_two_word_mask"; return;
    } else {
      const auto bit = static_cast<std::uint16_t>(root - 1);
      out.conditional_allows = ((mask[bit >> 6] >> (bit & 63)) & 1U) != 0;
      out.source_branch = "mask_bit";
    }
  }
  out.conditional_result_ready = out.conditional_allows.has_value();
  out.unavailable_reason = "conditional_only_getter_outputs_source_unavailable";
  // returned_byte remains null and both source readiness flags remain false.
}
} // namespace detail

inline bool PrisonerTriggerRootScopeGateIdentityReady12004(
    const PrisonerQuoteSourceFrame12004 &frame, std::uintptr_t trigger,
    std::uintptr_t primary_scope) noexcept {
  return PrisonerQuoteSourceFrameReady12004(frame) && trigger != 0 &&
      primary_scope != 0 && primary_scope == frame.original_scope_identity;
}

inline PrisonerTriggerRootScopeGateResult12004 ReadPrisonerTriggerRootScopeGate12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame,
    std::uintptr_t trigger_identity, std::uintptr_t primary_scope_identity) {
  PrisonerTriggerRootScopeGateResult12004 out{};
  out.frame = frame; out.trigger_identity = trigger_identity;
  out.primary_scope_identity = primary_scope_identity;
  if (!PrisonerTriggerRootScopeGateIdentityReady12004(frame,trigger_identity,primary_scope_identity)) {
    out.unavailable_reason = "source_frame_or_root_identity_unavailable"; return out;
  }
  detail::CopyTriggerRootScopeGateRaw12004(out,access);
  // Do not call58/60, infer outputs from addresses, fabricate a class layout,
  // or turn the current query into an observed native entry.
  return out;
}

inline PrisonerTriggerRootScopeGateResult12004 ProjectPrisonerTriggerRootScopeGate12004(
    const PrisonerTriggerRootScopeGateConditionalInput12004 &input) {
  PrisonerTriggerRootScopeGateResult12004 out{};
  out.frame = input.frame; out.trigger_identity = input.trigger_identity;
  out.primary_scope_identity = input.primary_scope_identity;
  out.root_scope_kind_raw_u16 = input.root_scope_kind_raw_u16;
  out.preferred_kind_return_ax_raw_u16 = input.preferred_kind_return_ax_raw_u16;
  out.mask_return_words_raw_u64 = input.mask_return_words_raw_u64;
  if (!PrisonerTriggerRootScopeGateIdentityReady12004(input.frame,input.trigger_identity,input.primary_scope_identity)) {
    out.unavailable_reason = "source_frame_or_root_identity_unavailable"; return out;
  }
  detail::ProjectTriggerRootScopeGateConditional12004(out);
  return out;
}

inline bool SourceTriggerRootScopeGateIdentityReady12004(const SourceLeafFrame12004 &frame) noexcept {
  return SourceLeafFrameReady12004(frame) && frame.producer_rva == 0x372B4C0;
}

inline SourceTriggerRootScopeGateResult12004 ReadPrisonerTriggerRootScopeGate12004(
    const SourceLeafReadOnlyAccess12004 &access, const SourceLeafFrame12004 &frame) {
  SourceTriggerRootScopeGateResult12004 out{};
  out.frame=frame; out.trigger_identity=frame.receiver_identity;
  out.primary_scope_identity=frame.primary_scope_identity;
  if (!SourceTriggerRootScopeGateIdentityReady12004(frame)) {
    out.unavailable_reason="source_leaf_frame_or_producer_identity_unavailable"; return out;
  }
  // Only the guarded callback adapter is shared; no prisoner Frame is created.
  const PrisonerQuoteReadOnlyAccess12004 guarded{access.context,access.read_memory};
  detail::CopyTriggerRootScopeGateRaw12004(out,guarded);
  if (frame.primary_scope_root_word && out.root_scope_kind_raw_u16 != frame.primary_scope_root_word) {
    out.raw_copy_ready=false;
    out.unavailable_reason="source_leaf_scope_word_mismatch_or_partial";
  }
  return out;
}

inline SourceTriggerRootScopeGateResult12004 ProjectPrisonerTriggerRootScopeGate12004(
    const SourceTriggerRootScopeGateConditionalInput12004 &input) {
  SourceTriggerRootScopeGateResult12004 out{};
  out.frame=input.frame; out.trigger_identity=input.frame.receiver_identity;
  out.primary_scope_identity=input.frame.primary_scope_identity;
  out.root_scope_kind_raw_u16=input.root_scope_kind_raw_u16;
  out.preferred_kind_return_ax_raw_u16=input.preferred_kind_return_ax_raw_u16;
  out.mask_return_words_raw_u64=input.mask_return_words_raw_u64;
  if (!SourceTriggerRootScopeGateIdentityReady12004(input.frame)) {
    out.unavailable_reason="source_leaf_frame_or_producer_identity_unavailable"; return out;
  }
  if (input.frame.primary_scope_root_word && input.root_scope_kind_raw_u16 != input.frame.primary_scope_root_word) {
    out.unavailable_reason="source_leaf_scope_word_mismatch_or_partial"; return out;
  }
  detail::ProjectTriggerRootScopeGateConditional12004(out);
  return out;
}
} // namespace xar::ck3_12004
