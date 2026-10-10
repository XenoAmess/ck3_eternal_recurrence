#include "xar_bridge/lifestyle_perk_predicate_288b1b0_12004.hpp"
#include "xar_bridge/lifestyle_perk_final_31ebe50_readonly_12004.hpp"

namespace xar::ck3_12004::lifestyle {

LifestylePerkPredicateSource12004 ReadLifestylePerkPredicate288B1B012004(
    const LifestylePerkReadonlyAccess12004 &access,
    std::uintptr_t command_identity) noexcept {
  LifestylePerkPredicateSource12004 out{};
  out.inputs = ReadLifestylePerkPredicateInputs288B1B012004(access, command_identity);
  if (!out.inputs.prefix_admitted.has_value()) {
    out.unavailable_reason = out.inputs.unavailable_reason;
    return out;
  }
  if (!*out.inputs.prefix_admitted) {
    out.value = false;
    return out;
  }
  // The admitted literal path loaded both identities, then XORR8D selected
  // null diagnostic writer before the tail call. Missing child data remains
  // unavailable in the62 output and never becomes a predicate false.
  LifestylePerkTruthProducer37998D0Result12004 trace{};
  out.tail = ReadLifestylePerkFinal31EBE5012004(
      access, *out.inputs.selected_perk_identity,
      *out.inputs.selected_character_identity, 0, &trace);
  if (trace.selected_perk_identity == *out.inputs.selected_perk_identity &&
      trace.context_projection_available) {
    out.truth_trace = trace;
  }
  out.value = out.tail->value;
  out.unavailable_reason = out.tail->unavailable_reason;
  return out;
}

} // namespace xar::ck3_12004::lifestyle
