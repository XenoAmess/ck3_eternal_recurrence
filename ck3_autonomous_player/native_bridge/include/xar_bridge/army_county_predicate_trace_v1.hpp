#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct ArmyCountyPredicateStageV1 {
  std::uint32_t call_count = 0;
  std::optional<std::uint64_t> actual_caller_return_rva;
  std::optional<bool> argument_identity_matched;
  std::optional<bool> returned;
  friend bool operator==(const ArmyCountyPredicateStageV1 &,
                         const ArmyCountyPredicateStageV1 &) = default;
};
struct ArmyCountyPredicateTraceV1 {
  bool available = false;
  std::string unavailable_reason = "county_predicate_trace_unavailable";
  bool hook_installed = false, scope_entered = false;
  bool same_thread = false, order_valid = true;
  bool native_predicate_returned = false;
  std::optional<bool> final_condition_passes;
  // Source P, first target P, second target P; fixed storage, no retained ring.
  std::array<ArmyCountyPredicateStageV1, 3> stages{};
  std::uint32_t ignored_foreign_calls = 0, ignored_nested_calls = 0;
  friend bool operator==(const ArmyCountyPredicateTraceV1 &,
                         const ArmyCountyPredicateTraceV1 &) = default;
};
}
