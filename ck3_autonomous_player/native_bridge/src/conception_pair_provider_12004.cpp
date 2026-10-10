#include "xar_bridge/conception_pair_provider_12004.hpp"

namespace xar::ck3_12004 {
namespace {

using Stage = ConceptionProviderStage12004;
using Result = ConceptionPairProviderResult12004;
using Role = ConceptionProviderCountRole12004;
namespace math = conception_pair_value_inputs::detail;

void Reach(Result& result, Stage stage, std::uint32_t pc) noexcept {
  result.stop_stage = stage;
  result.source_pc = pc;
  result.reached_stages |= std::uint64_t{1} << static_cast<unsigned>(stage);
}

Result Missing(Result result, std::string_view input) noexcept {
  result.unavailable_input = input;
  return result;
}

Result Output(Result result, std::int64_t raw, std::uint32_t writer) noexcept {
  result.first_output_raw = raw;
  result.actual_caller_zero_rejection = raw == 0;
  result.terminal_writer_rva = writer;
  return result;
}

bool FastScaleOperand(std::int64_t raw) noexcept {
  return std::bit_cast<std::uint64_t>(raw) + 0xB504F333ULL <= 0x16A09E666ULL;
}

// Actual2B96117..1BB and2B962D9..6478: signedscale100000, exact64bitwrap.
std::int64_t MultiplyScale(std::int64_t first, std::int64_t second) noexcept {
  if (FastScaleOperand(first) && FastScaleOperand(second)) {
    return math::WrapMultiply(first, second) / 100000;
  }
  const auto maximum = first > second ? first : second;
  const auto minimum = first < second ? first : second;
  const auto quotient = maximum / 100000;
  const auto remainder = maximum - quotient * 100000;
  const auto fractional = math::WrapMultiply(remainder, minimum) / 100000;
  return math::WrapAdd(fractional, math::WrapMultiply(minimum, quotient));
}

}  // namespace

ConceptionProviderNumericInputs12004 ConceptionProviderNumericInputsFromLoaded12004(
    const std::optional<conception_pair_value_inputs::LoadedNumericInputs>& loaded) noexcept {
  if (!loaded) return {};
  return {loaded->base_average_floor, loaded->linked_pair_addend,
          loaded->linked_pair_title_state_addend,
          loaded->both_title_state_absent_multiplier,
          loaded->first_relation_multiplier, loaded->second_relation_multiplier,
          loaded->alternate_relation_multiplier};
}

ConceptionProviderRoleSelection12004 SelectConceptionProviderCountRole12004(
    std::optional<bool> first_title_state_present,
    std::optional<std::int32_t> first_own_tier_raw,
    std::optional<std::int32_t> second_own_tier_raw) noexcept {
  if (!first_title_state_present) return {{}, "first_title_state_present"};
  if (!*first_title_state_present) return {Role::second, {}};
  if (!first_own_tier_raw) return {{}, "first_own_tier_raw"};
  if (!second_own_tier_raw) return {{}, "second_own_tier_raw"};
  return {*first_own_tier_raw > *second_own_tier_raw ? Role::first : Role::second, {}};
}

ConceptionPairProviderResult12004 EvaluateConceptionPairProvider12004(
    const ConceptionPairProviderInputs12004& i) noexcept {
  Result result;
  Reach(result, Stage::first_exclusion, 0x2B956BD);
  if (!i.first_excluded) return Missing(result, "first_excluded");
  if (*i.first_excluded) return Output(result, 0, 0x2B956D3);
  Reach(result, Stage::second_exclusion, 0x2B956E5);
  if (!i.second_excluded) return Missing(result, "second_excluded");
  if (*i.second_excluded) return Output(result, 0, 0x2B956D3);

  Reach(result, Stage::pregnancy, 0x2B95738);
  if (!i.first_pregnancy_record_present) return Missing(result, "first_pregnancy_record_present");
  if (*i.first_pregnancy_record_present) return Output(result, 0, 0x2B956D3);
  Reach(result, Stage::recent_child, 0x2B95947);
  if (!i.recent_child_gate_passes) return Missing(result, "recent_child_gate_passes");
  if (!*i.recent_child_gate_passes) return Output(result, 0, 0x2B95AF1);

  Reach(result, Stage::count_role, 0x2B95AB4);
  const auto selection = SelectConceptionProviderCountRole12004(
      i.first_title_state_present, i.first_own_tier_raw, i.second_own_tier_raw);
  if (!selection.role) return Missing(result, selection.missing_input);
  result.selected_count_role = selection.role;
  if (!i.observed_count_role) return Missing(result, "observed_count_role");
  if (*i.observed_count_role != *selection.role)
    return Missing(result, "observed_count_role_mismatch");
  Reach(result, Stage::count_limit, 0x2B95BAF);
  if (!i.selected_offspring_count_raw) return Missing(result, "selected_offspring_count_raw");
  if (!i.selected_child_limit_raw) return Missing(result, "selected_child_limit_raw");
  if (*i.selected_offspring_count_raw >= *i.selected_child_limit_raw)
    return Output(result, 0, 0x2B956D3);

  Reach(result, Stage::second_raw, 0x2B95C52);
  if (!i.second_raw) return Missing(result, "second_raw");
  if (*i.second_raw <= 0) return Output(result, 0, 0x2B9647B);
  Reach(result, Stage::first_raw, 0x2B95DF2);
  if (!i.first_raw) return Missing(result, "first_raw");
  if (*i.first_raw <= 0) return Output(result, 0, 0x2B9647B);

  Reach(result, Stage::base_numeric, 0x2B95FC6);
  const auto base = conception_pair_value_inputs::EvaluateBaseStage(
      i.first_raw, i.second_raw, i.numeric.base_average_floor);
  if (!base.raw) return Missing(result, "numeric.base_average_floor");
  auto raw = *base.raw;

  Reach(result, Stage::linked_pair, 0x2B9606E);
  if (!i.primary_relation_match) return Missing(result, "primary_relation_match");
  bool apply_linked_addend = false;
  if (*i.primary_relation_match) {
    Reach(result, Stage::linked_lists, 0x2B960B1);
    if (!i.first_child_count_raw) return Missing(result, "first_child_count_raw");
    if (*i.first_child_count_raw == 0) {
      apply_linked_addend = true;
    } else {
      if (!i.second_child_count_raw) return Missing(result, "second_child_count_raw");
      if (*i.second_child_count_raw == 0) {
        apply_linked_addend = true;
      } else {
        if (!i.first_list_has_second_parent_witness)
          return Missing(result, "first_list_has_second_parent_witness");
        if (!*i.first_list_has_second_parent_witness) {
          if (!i.second_list_has_first_parent_witness)
            return Missing(result, "second_list_has_first_parent_witness");
          apply_linked_addend = !*i.second_list_has_first_parent_witness;
        }
      }
    }
  }
  if (apply_linked_addend) {
    Reach(result, Stage::linked_addends, 0x2B960D9);
    if (!i.numeric.linked_pair_addend) return Missing(result, "numeric.linked_pair_addend");
    raw = math::WrapAdd(raw, *i.numeric.linked_pair_addend);
    if (!i.second_title_state_present) return Missing(result, "second_title_state_present");
    if (*i.second_title_state_present || *i.first_title_state_present) {
      if (!i.numeric.linked_pair_title_state_addend)
        return Missing(result, "numeric.linked_pair_title_state_addend");
      raw = math::WrapAdd(raw, *i.numeric.linked_pair_title_state_addend);
    }
  }

  Reach(result, Stage::title_state_multiplier, 0x2B960FB);
  if (!i.second_title_state_present) return Missing(result, "second_title_state_present");
  if (!*i.second_title_state_present && !*i.first_title_state_present) {
    if (!i.numeric.both_title_state_absent_multiplier)
      return Missing(result, "numeric.both_title_state_absent_multiplier");
    raw = MultiplyScale(raw, *i.numeric.both_title_state_absent_multiplier);
  }

  Reach(result, Stage::first_receiver, 0x2B96241);
  if (!i.first_selects_alternate) return Missing(result, "first_selects_alternate");
  bool alternate = *i.first_selects_alternate;
  if (!alternate) {
    Reach(result, Stage::second_receiver, 0x2B962BD);
    if (!i.second_selects_alternate) return Missing(result, "second_selects_alternate");
    alternate = *i.second_selects_alternate;
  }
  if (!alternate) {
    Reach(result, Stage::normal_close_family, 0x2B962D0);
    if (!i.normal_close_family) return Missing(result, "normal_close_family");
    if (*i.normal_close_family) {
      if (!i.numeric.first_relation_multiplier)
        return Missing(result, "numeric.first_relation_multiplier");
      raw = MultiplyScale(raw, *i.numeric.first_relation_multiplier);
    } else {
      Reach(result, Stage::normal_related_pair, 0x2B96325);
      if (!i.normal_related_pair) return Missing(result, "normal_related_pair");
      if (*i.normal_related_pair) {
        if (!i.numeric.second_relation_multiplier)
          return Missing(result, "numeric.second_relation_multiplier");
        raw = MultiplyScale(raw, *i.numeric.second_relation_multiplier);
      }
    }
  } else {
    Reach(result, Stage::alternate_family, 0x2B96378);
    if (!i.second_family_present) return Missing(result, "second_family_present");
    if (*i.second_family_present) {
      Reach(result, Stage::alternate_membership, 0x2B9639B);
      if (!i.second_family20_contains_first) return Missing(result, "second_family20_contains_first");
      if (*i.second_family20_contains_first) {
        Reach(result, Stage::alternate_close_or_extended, 0x2B963C7);
        if (!i.alternate_close_or_extended) return Missing(result, "alternate_close_or_extended");
        if (*i.alternate_close_or_extended) {
          if (!i.numeric.alternate_relation_multiplier)
            return Missing(result, "numeric.alternate_relation_multiplier");
          raw = MultiplyScale(raw, *i.numeric.alternate_relation_multiplier);
        }
      }
    }
  }
  Reach(result, Stage::complete, 0x2B9647B);
  return Output(result, raw, 0x2B9647B);
}

}  // namespace xar::ck3_12004
