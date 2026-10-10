#include "xar_bridge/ck3_12004_first_heir_conception_candidate_inputs.hpp"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>

using namespace xar::ck3_11906;
namespace {
CurrentFirstHeirRelationshipReadV1 Household() {
  CurrentFirstHeirRelationshipReadV1 read{};
  read.failure = CurrentFirstHeirRelationshipFailureV1::none;
  read.heir_character_id = 2;
  read.relationship.primary_spouse_character_id = 3;
  read.relationship.spouse_character_ids = {3};
  read.reproductive_inputs.emplace();
  auto &r = *read.reproductive_inputs;
  r.status = "available"; r.unavailable_reason = {};
  r.played_character_id = 1; r.heir_character_id = 2; r.date_raw = 123;
  for (const auto id : {2, 3}) {
    CurrentFirstHeirReproductiveRowV1 row{};
    row.character_id = id;
    row.roles = id == 2 ? std::vector<std::string_view>{"heir"} :
                         std::vector<std::string_view>{"primary_spouse", "spouse"};
    row.available = true; row.unavailable_reason = {};
    row.age_measure_raw = std::int16_t{32};
    row.sex_selector_raw = static_cast<std::uint8_t>(id == 2 ? 0 : 1);
    row.fertility.available = true;
    row.fertility.extension_present = true;
    row.fertility.native_gate_evaluated = true;
    row.fertility.native_gate_allows = true;
    row.fertility.effective_raw = 40000;
    row.native_pregnancy.status = "available";
    row.native_pregnancy.unavailable_reason = {};
    row.native_pregnancy.is_pregnant = false;
    r.rows.push_back(row);
  }
  return read;
}
CurrentFirstHeirConceptionCandidateInputsReadV1 Companion() {
  CurrentFirstHeirConceptionCandidateInputsReadV1 c{};
  c.status = "available"; c.unavailable_reason = {};
  for (const auto id : {2, 3}) {
    CurrentCharacterConceptionCandidateRowV1 row{};
    row.character_id = id;
    row.extended_gate.status = "available";
    row.extended_gate.unavailable_reason = {};
    row.extended_gate.extended_data_present = true;
    row.extended_gate.extended_288_raw_u64 = 0;
    row.extended_gate.blocks_pair_conception = false;
    row.pending_candidate.candidate_state_available = true;
    row.pending_candidate.candidate_state_unavailable_reason = {};
    row.pending_candidate.extended_data_present = true;
    row.pending_candidate.candidate_flag_raw = std::uint8_t{0};
    row.pending_candidate.target_status = "not_requested";
    row.pending_candidate.target_unavailable_reason = {};
    c.rows.push_back(row);
  }
  CurrentHouseholdConceptionPairInputsV1 p{};
  p.first_character_id = 2; p.second_character_id = 3;
  c.pairs.push_back(p);
  return c;
}
void Emit(std::string_view name, const CurrentFirstHeirRelationshipReadV1 &read,
          const CurrentFirstHeirConceptionCandidateInputsReadV1 *c) {
  const auto wire = CurrentFirstHeirRelationshipResultJsonV1(name, 7, 2, read, {}, nullptr, nullptr, c);
  assert(wire.find("\"native_pregnancy\"") != std::string::npos);
  assert(wire.find("\"is_pregnant\":false") != std::string::npos);
  if (c != nullptr && !c->rows.empty())
    assert(wire.find("\"native_conception_candidate_pending\"") != std::string::npos);
  std::cout << wire << '\n';
}
} // namespace

int main() {
  auto read = Household();
  Emit("legacy_absent", read, nullptr);
  auto c = Companion();
  c.rows[0].first_value.status = "available";
  c.rows[0].first_value.unavailable_reason = {};
  c.rows[0].first_value.seed_after_children_raw = 0;
  c.rows[0].first_value.adjusted_age_raw = 32;
  c.rows[0].first_value.selected_age_band_index = 0;
  c.rows[0].first_value.age_product_raw = 0;
  c.rows[0].first_value.first_output_raw = 0;
  c.rows[1].second_value.ready = true;
  c.rows[1].second_value.adjusted_age_raw = -1;
  c.rows[1].second_value.selected_band_index = 0;
  c.rows[1].second_value.prefinal_raw = -7;
  c.rows[1].second_value.value_raw = -7;
  c.pairs[0].base_stage.status = xar::ck3_12004::conception_pair_value_inputs::BaseStatus::available;
  c.pairs[0].base_stage.branch = xar::ck3_12004::conception_pair_value_inputs::BaseBranch::signed_minimum;
  c.pairs[0].base_stage.raw = -7;
  Emit("zero_and_negative", read, &c);
  c.rows[0].extended_gate.extended_288_raw_u64 = std::numeric_limits<std::uint64_t>::max();
  c.rows[0].extended_gate.blocks_pair_conception = true;
  auto &pending = c.rows[0].pending_candidate;
  pending.candidate_flag_raw = std::uint8_t{255};
  pending.target_status = "generation_mismatch";
  pending.target_unavailable_reason = "conception_candidate_target_generation_unavailable";
  pending.target_pointer_raw = 1;
  pending.target_full_id_raw = 0x80000001U;
  Emit("independent_target_failure", read, &c);
  pending.target_status = "resolved";
  pending.target_unavailable_reason = {};
  pending.resolved_target_character_id = std::numeric_limits<std::int32_t>::min() + 1;
  Emit("full_generation_target", read, &c);
  c = {};
  c.unavailable_reason = "current_household_conception_frame_changed";
  Emit("local_changed_frame", read, &c);
}
