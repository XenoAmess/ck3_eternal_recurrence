#pragma once
#include "xar_bridge/lifestyle_perk_predicate_inputs_12004.hpp"
#include "xar_bridge/lifestyle_perk_truth_producer_12004.hpp"

namespace xar::ck3_12004::lifestyle {

// Source-equivalent output of the actual child reached by288B142. This remains
// separate from288AE00's earlier conditions and observed native can_select.
struct LifestylePerkPredicateSource12004 {
  LifestylePerkPredicateInputs12004 inputs{};
  std::optional<LifestylePerkReadonlyPredicate12004> tail{};
  // Same-demand copied09 inputs/output availability; vtable slots are raw
  // addresses, and the software scope identity is trace-only after return.
  std::optional<LifestylePerkTruthProducer37998D0Result12004> truth_trace{};
  std::optional<bool> value{};
  std::string unavailable_reason{};
};

LifestylePerkPredicateSource12004 ReadLifestylePerkPredicate288B1B012004(
    const LifestylePerkReadonlyAccess12004 &, std::uintptr_t command_identity) noexcept;

} // namespace xar::ck3_12004::lifestyle
