#include "xar_bridge/prisoner_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"
#include "xar_bridge/detail/source_auto_accept_trigger_condition_core_12004.hpp"

namespace xar::ck3_12004 {
PrisonerAutoAcceptTriggerRaw12004 ReadPrisonerAutoAcceptTriggerCondition12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, const PrisonerQuoteSourceFrame12004 &frame,
    const PrisonerQuoteInternalAliases12004 &aliases, std::optional<std::uintptr_t> trigger) {
  PrisonerAutoAcceptTriggerRaw12004 out{};
  out.frame = frame; out.aliases = aliases; out.trigger_identity = trigger;
  out.query_frame_ready = PrisonerQuoteSourceFrameReady12004(frame);
  if (aliases.primary_scope && aliases.secondary_scope && aliases.tertiary_scope) {
    out.parent_alias_shape_matches = *aliases.primary_scope == frame.original_scope_identity &&
        *aliases.secondary_scope == std::uintptr_t{0} &&
        *aliases.tertiary_scope == frame.original_scope_identity;
  }
  detail::CopyAutoAcceptTriggerFields12004(access, out, "quote_query_frame_not_ready");
  return out;
}

PrisonerAutoAcceptTriggerCondition12004 EvaluatePrisonerAutoAcceptTriggerCondition12004(
    const PrisonerAutoAcceptTriggerRaw12004 &raw, const PrisonerTriggerRootScopeGateResult12004 &gate) {
  const bool helper_matches = raw.trigger_identity && gate.frame == raw.frame &&
      gate.trigger_identity == *raw.trigger_identity && raw.aliases.primary_scope &&
      gate.primary_scope_identity == *raw.aliases.primary_scope &&
      gate.root_scope_kind_raw_u16 == raw.aliases.primary_scope_root_word;
  return detail::EvaluateAutoAcceptTriggerConditions12004<PrisonerAutoAcceptTriggerCondition12004>(
      raw, gate, PrisonerQuoteSourceFrameReady12004(raw.frame), helper_matches, "quote_query_frame_not_ready");
}
} // namespace xar::ck3_12004
