#pragma once

#include "xar_bridge/conception_pair_value_inputs_12004.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

enum class ConceptionProviderCountRole12004 { first, second };

// Each scalar stays independently optional. A loaded value of0/negative is
// valid; an unconsumed missing scalar does not block an earlier known result.
struct ConceptionProviderNumericInputs12004 {
  std::optional<std::int64_t> base_average_floor;
  std::optional<std::int64_t> linked_pair_addend;
  std::optional<std::int64_t> linked_pair_title_state_addend;
  std::optional<std::int64_t> both_title_state_absent_multiplier;
  std::optional<std::int64_t> first_relation_multiplier;
  std::optional<std::int64_t> second_relation_multiplier;
  std::optional<std::int64_t> alternate_relation_multiplier;
};

ConceptionProviderNumericInputs12004 ConceptionProviderNumericInputsFromLoaded12004(
    const std::optional<conception_pair_value_inputs::LoadedNumericInputs>& loaded) noexcept;

// Source-closed input semantics for actual2B95670 withmode3/fifthargument0.
// Inputs belong to the caller's same-query, full-generation-qualified first and
// second Character receivers. This pure join reads no memory/calls no getter.
struct ConceptionPairProviderInputs12004 {
  std::optional<bool> first_excluded;
  std::optional<bool> second_excluded;
  std::optional<bool> first_pregnancy_record_present;
  // Includes the firstFamily absent/count0 bypass and the actualsigned dategate.
  std::optional<bool> recent_child_gate_passes;

  std::optional<bool> first_title_state_present;
  std::optional<std::int32_t> first_own_tier_raw;
  std::optional<std::int32_t> second_own_tier_raw;
  // Provenance is the role actually used for both count andchildlimit inputs.
  // It is independently checked against the source stack48 selection below.
  std::optional<ConceptionProviderCountRole12004> observed_count_role;
  std::optional<std::int32_t> selected_offspring_count_raw;
  std::optional<std::int32_t> selected_child_limit_raw;

  std::optional<std::int64_t> second_raw;
  std::optional<std::int64_t> first_raw;
  ConceptionProviderNumericInputs12004 numeric;

  std::optional<bool> primary_relation_match;
  std::optional<std::int32_t> first_child_count_raw;
  std::optional<std::int32_t> second_child_count_raw;
  std::optional<bool> first_list_has_second_parent_witness;
  std::optional<bool> second_list_has_first_parent_witness;
  std::optional<bool> second_title_state_present;

  std::optional<bool> first_selects_alternate;
  std::optional<bool> second_selects_alternate;
  std::optional<bool> normal_close_family;
  std::optional<bool> normal_related_pair;
  std::optional<bool> second_family_present;
  std::optional<bool> second_family20_contains_first;
  std::optional<bool> alternate_close_or_extended;
};

enum class ConceptionProviderStage12004 : std::uint8_t {
  first_exclusion, second_exclusion, pregnancy, recent_child,
  count_role, count_limit, second_raw, first_raw, base_numeric,
  linked_pair, linked_lists, linked_addends, title_state_multiplier,
  first_receiver, second_receiver, normal_close_family, normal_related_pair,
  alternate_family, alternate_membership, alternate_close_or_extended,
  complete,
};

struct ConceptionProviderRoleSelection12004 {
  std::optional<ConceptionProviderCountRole12004> role;
  std::string_view missing_input;
};

ConceptionProviderRoleSelection12004 SelectConceptionProviderCountRole12004(
    std::optional<bool> first_title_state_present,
    std::optional<std::int32_t> first_own_tier_raw,
    std::optional<std::int32_t> second_own_tier_raw) noexcept;

struct ConceptionPairProviderResult12004 {
  std::optional<std::int64_t> first_output_raw;
  // Only the actualcallerTEST/JE zero gate at2929C35/C38, not its later math.
  std::optional<bool> actual_caller_zero_rejection;
  std::optional<ConceptionProviderCountRole12004> selected_count_role;
  ConceptionProviderStage12004 stop_stage{ConceptionProviderStage12004::first_exclusion};
  std::uint64_t reached_stages{};
  std::uint32_t source_pc{};
  std::uint32_t terminal_writer_rva{};
  std::string_view unavailable_input;
};

// Nativeorder/short-circuit, onefirstQ64 only. No naturaltrigger, probability,
// monthly eligibility, activepregnancy or candidate-slot lifecycle is inferred.
ConceptionPairProviderResult12004 EvaluateConceptionPairProvider12004(
    const ConceptionPairProviderInputs12004& inputs) noexcept;

}  // namespace xar::ck3_12004
