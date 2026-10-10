#include "xar_bridge/source_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"
#include "xar_bridge/detail/source_auto_accept_trigger_condition_core_12004.hpp"

namespace xar::ck3_12004 {
namespace {
bool WrapperFrameReady(const SourceLeafFrame12004 &frame) noexcept {
  return SourceLeafFrameReady12004(frame) && frame.producer_rva == kPrisonerAutoAcceptTriggerWrapperRva12004;
}
} // namespace

SourceAutoAcceptTriggerRaw12004 ReadPrisonerAutoAcceptTriggerCondition12004(
    const SourceLeafReadOnlyAccess12004 &access, const SourceLeafFrame12004 &frame,
    const PrisonerQuoteInternalAliases12004 &aliases) {
  SourceAutoAcceptTriggerRaw12004 out{};
  out.frame = frame; out.aliases = aliases; out.trigger_identity = frame.receiver_identity;
  out.query_frame_ready = WrapperFrameReady(frame);
  if (aliases.primary_scope && aliases.secondary_scope && aliases.tertiary_scope) {
    out.parent_alias_shape_matches = *aliases.primary_scope == frame.primary_scope_identity &&
        *aliases.secondary_scope == std::uintptr_t{0} && *aliases.tertiary_scope == frame.primary_scope_identity;
  }
  if (frame.primary_scope_root_word && aliases.primary_scope_root_word)
    out.source_leaf_scope_word_matches = frame.primary_scope_root_word == aliases.primary_scope_root_word;
  // Share the callback carrier only. This does not create or qualify a prisoner
  // role Frame, nor call a native getter/evaluator.
  const PrisonerQuoteReadOnlyAccess12004 guarded{access.context, access.read_memory};
  detail::CopyAutoAcceptTriggerFields12004(guarded, out, "source_leaf_frame_or_wrapper_producer_not_ready");
  out.scope_table_provider.frame = frame.read_frame;
  out.scope_table_provider.caller_copied_root_kind_raw_u16 = aliases.primary_scope_root_word;
  if (out.query_frame_ready) {
    out.scope_table_provider = ReadTriggerScopeTableProvider3795A6012004(access, frame.read_frame,
        aliases.primary_scope_root_word);
    const auto &provider = out.scope_table_provider;
    if (provider.any_native_field_read_attempted) {
      out.any_native_field_read_attempted = true;
      out.all_attempted_native_reads_complete = out.all_attempted_native_reads_complete &&
          provider.all_attempted_native_reads_complete;
      for (const auto &field : provider.missing_fields) out.missing_fields.emplace_back("scope_table." + field);
      if (!provider.all_attempted_native_reads_complete)
        out.unavailable_reason = "scope_table_readonly_copy_partial";
    }
  }
  return out;
}

SourceAutoAcceptTriggerCondition12004 EvaluatePrisonerAutoAcceptTriggerCondition12004(
    const SourceAutoAcceptTriggerRaw12004 &raw, const SourceTriggerRootScopeGateResult12004 &gate) {
  const bool word_matches_frame = !raw.frame.primary_scope_root_word ||
      raw.frame.primary_scope_root_word == raw.aliases.primary_scope_root_word;
  const bool helper_matches = raw.trigger_identity &&
      gate.frame.read_frame == raw.frame.read_frame && gate.frame.producer_rva == std::uintptr_t{0x372B4C0} &&
      gate.frame.receiver_identity == raw.frame.receiver_identity &&
      gate.frame.primary_scope_identity == raw.frame.primary_scope_identity &&
      gate.frame.primary_scope_root_word == raw.frame.primary_scope_root_word &&
      gate.trigger_identity == *raw.trigger_identity && raw.aliases.primary_scope &&
      gate.primary_scope_identity == *raw.aliases.primary_scope &&
      gate.root_scope_kind_raw_u16 == raw.aliases.primary_scope_root_word;
  auto out = detail::EvaluateAutoAcceptTriggerConditions12004<SourceAutoAcceptTriggerCondition12004>(
      raw, gate, WrapperFrameReady(raw.frame) && word_matches_frame, helper_matches,
      word_matches_frame ? "source_leaf_frame_or_wrapper_producer_not_ready" : "source_leaf_scope_word_mismatch_or_partial");
  out.scope_table_matches_query = raw.scope_table_provider.frame == raw.frame.read_frame &&
      raw.scope_table_provider.caller_copied_root_kind_raw_u16 == raw.aliases.primary_scope_root_word;
  // Copied descriptor/init fields are retained in raw.scope_table_provider.
  // They never supply a validator return or make the final +C8 result ready.
  return out;
}
} // namespace xar::ck3_12004
