#include "xar_bridge/conception_pair_provider_12004.hpp"

#include <limits>

namespace provider = xar::ck3_12004;
namespace {

unsigned checks = 0;
unsigned scenarios = 0;
#define CHECK(condition) do { ++checks; if (!(condition)) return __LINE__; } while (false)

provider::ConceptionPairProviderInputs12004 NormalPair() {
  provider::ConceptionPairProviderInputs12004 i;
  i.first_excluded = false;
  i.second_excluded = false;
  i.first_pregnancy_record_present = false;
  i.recent_child_gate_passes = true;
  i.first_title_state_present = false;
  i.observed_count_role = provider::ConceptionProviderCountRole12004::second;
  i.selected_offspring_count_raw = 0;
  i.selected_child_limit_raw = 4;
  i.second_raw = 25000;
  i.first_raw = 40000;
  i.numeric.base_average_floor = 40000;
  i.numeric.both_title_state_absent_multiplier = 100000;
  i.primary_relation_match = false;
  i.second_title_state_present = false;
  i.first_selects_alternate = false;
  i.second_selects_alternate = false;
  i.normal_close_family = false;
  i.normal_related_pair = false;
  return i;
}

bool Reached(const provider::ConceptionPairProviderResult12004& result,
             provider::ConceptionProviderStage12004 stage) {
  return (result.reached_stages & (std::uint64_t{1} << static_cast<unsigned>(stage))) != 0;
}

provider::ConceptionPairProviderResult12004 Evaluate(
    const provider::ConceptionPairProviderInputs12004& i) {
  ++scenarios;
  return provider::EvaluateConceptionPairProvider12004(i);
}

}  // namespace

// Called once by central10's new fullprovider compound; no independent run.
extern "C" int RunConceptionPairProviderScenario12004() {
  checks = 0;
  scenarios = 0;
  auto i = NormalPair();
  auto r = Evaluate(i);
  CHECK(r.first_output_raw == 25000);
  CHECK(r.actual_caller_zero_rejection == false);
  CHECK(r.selected_count_role == provider::ConceptionProviderCountRole12004::second);
  CHECK(Reached(r, provider::ConceptionProviderStage12004::complete));
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::alternate_family));

  i = {};
  i.first_excluded = true;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0 && r.actual_caller_zero_rejection == true);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::second_exclusion));
  CHECK(r.terminal_writer_rva == 0x2B956D3);
  i.first_excluded = false;
  i.second_excluded = true;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::pregnancy));
  i = NormalPair();
  i.first_pregnancy_record_present = true;
  i.recent_child_gate_passes.reset();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::recent_child));
  i = NormalPair();
  i.recent_child_gate_passes = false;
  i.first_title_state_present.reset();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0 && r.terminal_writer_rva == 0x2B95AF1);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::count_role));
  i = NormalPair();
  i.selected_child_limit_raw = 0;
  i.second_raw.reset();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::second_raw));

  i = NormalPair();
  i.first_title_state_present = true;
  i.first_own_tier_raw = 3;
  i.second_own_tier_raw = 3;
  i.numeric.both_title_state_absent_multiplier.reset();
  r = Evaluate(i);
  CHECK(r.selected_count_role == provider::ConceptionProviderCountRole12004::second);
  CHECK(r.first_output_raw == 25000);
  i.first_own_tier_raw = 4;
  i.observed_count_role = provider::ConceptionProviderCountRole12004::first;
  r = Evaluate(i);
  CHECK(r.selected_count_role == provider::ConceptionProviderCountRole12004::first);
  CHECK(r.first_output_raw == 25000);
  i.observed_count_role = provider::ConceptionProviderCountRole12004::second;
  r = Evaluate(i);
  CHECK(!r.first_output_raw && r.unavailable_input == "observed_count_role_mismatch");

  i = NormalPair();
  i.second_raw = 0;
  i.first_raw.reset();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::first_raw));
  i = NormalPair();
  i.first_raw = -1;
  i.numeric.base_average_floor.reset();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::base_numeric));

  i = NormalPair();
  i.primary_relation_match = true;
  i.first_child_count_raw = 0;
  i.numeric.linked_pair_addend = 1000;
  i.numeric.both_title_state_absent_multiplier = 200000;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 52000);
  CHECK(!i.second_child_count_raw && !i.first_list_has_second_parent_witness);
  i = NormalPair();
  i.primary_relation_match = true;
  i.first_child_count_raw = 1;
  i.second_child_count_raw = 1;
  i.first_list_has_second_parent_witness = true;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 25000);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::linked_addends));
  CHECK(!i.second_list_has_first_parent_witness && !i.numeric.linked_pair_addend);
  i.first_list_has_second_parent_witness = false;
  i.second_list_has_first_parent_witness = true;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 25000);
  i.second_list_has_first_parent_witness = false;
  i.numeric.linked_pair_addend = 1000;
  i.second_title_state_present = true;
  i.numeric.linked_pair_title_state_addend = 2000;
  i.numeric.both_title_state_absent_multiplier.reset();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 28000);

  i = NormalPair();
  i.normal_close_family = true;
  i.normal_related_pair.reset();
  i.numeric.first_relation_multiplier = 120000;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 30000);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::normal_related_pair));
  i = NormalPair();
  i.normal_related_pair = true;
  i.numeric.second_relation_multiplier = 75000;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 18750);

  i = NormalPair();
  i.first_selects_alternate = true;
  i.second_selects_alternate.reset();
  i.normal_close_family.reset();
  i.normal_related_pair.reset();
  i.second_family_present = false;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 25000);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::second_receiver));
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::normal_close_family));
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::alternate_membership));
  i.second_family_present = true;
  i.second_family20_contains_first = false;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 25000);
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::alternate_close_or_extended));
  i.second_family20_contains_first = true;
  i.alternate_close_or_extended = false;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 25000);
  i.alternate_close_or_extended = true;
  i.numeric.alternate_relation_multiplier = 50000;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 12500);
  i.numeric.alternate_relation_multiplier.reset();
  r = Evaluate(i);
  CHECK(!r.first_output_raw && r.unavailable_input == "numeric.alternate_relation_multiplier");
  CHECK(!r.actual_caller_zero_rejection);
  i = NormalPair();
  i.first_selects_alternate.reset();
  i.second_selects_alternate = true;
  r = Evaluate(i);
  CHECK(!r.first_output_raw && r.unavailable_input == "first_selects_alternate");
  CHECK(!Reached(r, provider::ConceptionProviderStage12004::second_receiver));

  i = NormalPair();
  i.numeric.both_title_state_absent_multiplier = -100000;
  r = Evaluate(i);
  CHECK(r.first_output_raw == -25000 && r.actual_caller_zero_rejection == false);
  i.numeric.both_title_state_absent_multiplier = 0;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0 && r.actual_caller_zero_rejection == true);
  i.numeric.both_title_state_absent_multiplier = std::numeric_limits<std::int64_t>::min();
  r = Evaluate(i);
  CHECK(r.first_output_raw == 0);  // Source wraps25000*INT64_MIN, unlike wide product.
  i = NormalPair();
  i.primary_relation_match = true;
  i.first_child_count_raw = 0;
  i.numeric.linked_pair_addend = std::numeric_limits<std::int64_t>::max();
  r = Evaluate(i);
  CHECK(r.first_output_raw == std::numeric_limits<std::int64_t>::min() + 24999);
  CHECK(r.actual_caller_zero_rejection == false);
  i = NormalPair();
  i.first_raw = 4000000000LL;
  i.second_raw = 4000000000LL;
  i.numeric.base_average_floor = 0;
  i.numeric.both_title_state_absent_multiplier = 4000000000LL;
  r = Evaluate(i);
  CHECK(r.first_output_raw == 160000000000000LL);
  i = NormalPair();
  i.first_raw = 40000;
  i.second_raw = 25001;
  i.numeric.both_title_state_absent_multiplier = -50000;
  r = Evaluate(i);
  CHECK(r.first_output_raw == -12500);
  i = NormalPair();
  i.first_raw = std::numeric_limits<std::int64_t>::max();
  i.second_raw = std::numeric_limits<std::int64_t>::max();
  r = Evaluate(i);
  CHECK(r.first_output_raw == -1);
  CHECK(r.actual_caller_zero_rejection == false);
  return 0;
}

extern "C" unsigned ConceptionPairProviderScenarioCheckCount12004() { return checks; }
extern "C" unsigned ConceptionPairProviderScenarioCount12004() { return scenarios; }
