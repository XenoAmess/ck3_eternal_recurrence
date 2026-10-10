#include "xar_bridge/entry_final_outer_refresh_12004.hpp"

#include <iostream>
#include <stdexcept>

namespace {
void Check(bool value, const char* message) {
  if (!value) throw std::runtime_error(message);
}

void NewOuterStageCompositionCase() {
  using namespace xar::ck3_12004;
  const std::array<FinalOccurrenceSourceRow12004, 2> levy0{{
      {41, 0xA000001, 11, 0xA110, 0},
      {41, 0xA000001, 11, 0xA110, -5},
  }};
  const std::array<FinalOccurrenceSourceRow12004, 1> maa0{{
      {42, 0xB000002, 12, 0xA120, 17},
  }};
  const std::array<FinalOccurrenceSourceRow12004, 1> levy1{{
      {51, 0xA000001, 21, 0xA210, 9},
  }};
  const std::array<FinalOccurrenceSourceRow12004, 1> maa1{{
      {52, 0xB000002, 22, 0xA220, 11},
  }};
  std::array<FinalOuterOriginalStatStage12004, 4> stages{};
  stages[0].side_index = 0;
  stages[0].bucket = FinalOccurrenceBucket12004::levy;
  stages[0].bucket_index = 0;
  stages[0].physical_entry_identity = 0x1000;
  stages[0].native_carmy_id = 41;
  stages[0].regiment_id = 0xA000001;
  stages[0].getter_stage = "frozen_current_character_values";
  stages[0].original_origin = "bridge_query_scratch";
  stages[0].original_source_ledger = "original-current-ledger";
  stages[0].consumption_sequence = 70;
  stages[0].getter_province_id = 11;
  stages[0].getter_province_identity = 0xA110;
  stages[0].entry_association_proven = false;
  stages[1] = stages[0];
  stages[1].bucket_index = 1;
  stages[1].physical_entry_identity = 0x1060;
  stages[1].getter_stage = "actual4_consumed_ci_with_owned_six_stage_postimage";
  stages[1].original_origin = "native_physical_entry_writer";
  stages[1].original_source_ledger = "original-continuation14-ledger";
  stages[1].consumption_sequence = 71;
  stages[1].getter_province_id = 101;
  stages[1].getter_province_identity = 0xC000;
  stages[1].entry_association_proven = true;
  stages[1].completed_preparation_lineage_proven = true;
  stages[1].preparation_model_identity = 0x7000;
  stages[1].installed_model_identity = 0x8000;
  stages[2] = stages[1];
  stages[2].side_index = 1;
  stages[2].bucket_index = 0;
  stages[2].physical_entry_identity = 0x3000;
  stages[2].native_carmy_id = 51;
  stages[2].getter_stage = "native_wrapper_consumed_per_ci_contexts";
  stages[2].consumption_sequence = 72;
  stages[2].getter_province_id = 202;
  stages[2].getter_province_identity = 0xD000;
  stages[2].completed_preparation_lineage_proven.reset();
  stages[2].installed_model_transfer_observed = false;
  stages[3] = stages[2];
  stages[3].physical_entry_identity = 0x9900;
  stages[3].original_source_ledger = "unmatched-original-stage-ledger";

  FinalOuterRefreshInput12004 input{};
  input.sides[0] = {0, 101, 0xC000, {0x1000, levy0}, {0x2000, maa0}};
  input.sides[1] = {1, 202, 0xD000, {0x3000, levy1}, {0x4000, maa1}};
  input.supplied_combat_identity = 0x9000;
  input.original_province_arguments[0] = {101, 0xC000, 880};
  input.original_stat_stages = stages;
  const auto result = PlanFinalOuterRefresh12004(input);
  Check(result.calls[0].call_rva == 0x247AB12 &&
        result.calls[1].call_rva == 0x247AB21,
        "actual outer source order not represented");
  Check(result.calls[0].province_load_rva == 0x247AB07 &&
        result.calls[1].province_load_rva == 0x247AB17,
        "independent original Province loads collapsed");
  Check(result.calls[0].conditional_side_identity == 0x9020 &&
        result.calls[1].conditional_side_identity == 0x9368,
        "source-bound Side roles not retained");
  Check(result.calls[0].original_province_id_matches_supplied == true &&
        !result.calls[1].original_province_id_matches_supplied.has_value() &&
        !result.calls[1].original_province_argument.province_identity.has_value(),
        "missing second original argument borrowed the first argument");
  Check(result.occurrences.size() == 5, "two Side plans not composed");
  for (std::size_t index = 0; index < result.occurrences.size(); ++index) {
    const auto& row = result.occurrences[index];
    Check(row.outer_traversal_ordinal == index, "outer ordinal missing");
    Check(row.occurrence.side_index == (index < 3 ? 0u : 1u),
          "Side0/Side1 occurrence order changed");
    Check(row.occurrence.traversal_ordinal == (index < 3 ? index : index - 3),
          "single-Side ordinal was reinterpreted as outer ordinal");
    Check(row.occurrence.final_combat_province_id == (index < 3 ? 101 : 202),
          "per-call supplied final Province substituted");
  }
  Check(result.occurrences[0].occurrence.initial_army_province_id == 11 &&
        result.occurrences[3].occurrence.initial_army_province_id == 21,
        "initial Army Province lost its independent role");
  const auto& current = result.occurrences[0].original_stat_stages.at(0);
  Check(current.original.getter_stage == stages[0].getter_stage &&
        current.original.original_origin == "bridge_query_scratch" &&
        current.original.entry_association_proven == false &&
        current.getter_province_id_matches_supplied == false,
        "current stage was relabelled as original final-stage observation");
  const auto& historical = result.occurrences[1].original_stat_stages.at(0);
  Check(historical.original.original_source_ledger == stages[1].original_source_ledger &&
        historical.original.completed_preparation_lineage_proven == true &&
        !historical.original.installed_model_transfer_observed.has_value() &&
        !historical.original.original_outer_invocation_associated.has_value(),
        "original preparation/outer transfer facts were inferred");
  Check(result.occurrences[3].original_stat_stages.at(0).original.
            installed_model_transfer_observed == false,
        "observed false transfer was changed");
  Check(result.occurrences[2].original_stat_stages.empty() &&
        result.occurrences[4].original_stat_stages.empty(),
        "unobserved stat stages were substituted");
  Check(result.unmatched_original_stat_stages.size() == 1 &&
        result.unmatched_original_stat_stages[0].original_source_ledger ==
            "unmatched-original-stage-ledger" &&
        !result.original_outer_invocation_inferred,
        "unmatched facts or original invocation boundary lost");
}
}  // namespace

int main() {
  try {
    NewOuterStageCompositionCase();
    std::cout << "entry_final_outer_refresh_12004: 1/1 GREEN (conditional outer/stage compound)\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "entry_final_outer_refresh_12004: " << error.what() << '\n';
    return 1;
  }
}
