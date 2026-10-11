#pragma once

#include "xar_bridge/rite_piety_price_term_2c628a0_readonly_12004.hpp"
#include "xar_bridge/rite_piety_observed_term_admission_12004.hpp"

#include <optional>

namespace xar::ck3_12004::piety_price_raw_inputs {

struct RitePietyObservedTermObservation12004 {
  RitePietyPriceTerm2C628A012004 source_term;
  std::optional<RitePietyObservedTermAdmission12004> admission;
  std::optional<RitePietyObservedTermExpected12004> expectation;
};

// The original readonly getter runs once. Only its complete dynamic prefix
// admits a value already observed in the same live query's native call journal.
// This overload invokes no native getter, evaluator or virtual function.
inline RitePietyObservedTermObservation12004 ReadRitePietyPriceTerm2C628A012004(
    const PietyPriceNumericAccess12004& access,
    std::uintptr_t current_rite,
    std::uintptr_t actor,
    std::uint64_t revision,
    const RitePietyObservedTermInputs12004& inputs) noexcept {
  RitePietyObservedTermObservation12004 out;
  out.source_term = ReadRitePietyPriceTerm2C628A012004(
      access, current_rite, actor, revision);
  const auto& term = out.source_term;
  if (term.source_ready ||
      term.route != RitePietyPriceTermRoute12004::dynamic_expression_value_unavailable ||
      !term.dynamic_context_operands_copied ||
      !term.dynamic_dispatch_operands_copied) return out;

  RitePietyObservedTermExpected12004 expected;
  expected.module_base = access.module_base;
  expected.actor = term.actor;
  expected.current_rite = term.current_rite;
  expected.revision = term.revision;
  expected.definition = term.definition;
  expected.expression = term.expression;
  expected.expression_receiver = term.expression_receiver;
  expected.expression_vtable = term.expression_vtable;
  expected.expression_virtual_30 = term.expression_virtual_30;
  expected.actor_full_id_raw_u32 = term.actor_full_id_raw_u32;
  expected.actor_context_key_raw_u32 = term.actor_context_key_raw_u32;
  expected.rite_full_id_raw_u32 = term.rite_full_id_raw_u32;
  expected.rite_context_key_raw_u32 = term.rite_context_key_raw_u32;
  expected.rite_link_full_id_raw_u32 = term.rite_link_full_id_raw_u32;
  expected.rite_link_context_key_raw_u32 = term.rite_link_context_key_raw_u32;
  expected.dynamic_prefix_copied = term.dynamic_context_operands_copied &&
      term.dynamic_dispatch_operands_copied;
  out.expectation = expected;
  out.admission = AdmitRitePietyObservedTerm12004(*out.expectation, inputs);
  const auto& admission = *out.admission;
  if (!admission.admitted || !admission.observed_q64_raw.has_value()) {
    out.source_term.reason = admission.admitted
        ? "actual_rite_dynamic_admitted_q64_missing" : admission.reason;
    return out;
  }

  out.source_term.native_term_raw_q64 = admission.observed_q64_raw;
  out.source_term.source_ready = true;
  out.source_term.route = RitePietyPriceTermRoute12004::dynamic_expression_observed_return;
  out.source_term.natural_dynamic_q64_observed = true;
  out.source_term.reason = admission.reason;
  // Keep actual_original_consumed_values unchanged: this individual observed
  // term does not turn the aggregate readonly source model into a native quote.
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
