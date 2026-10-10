#include "xar_bridge/ck3_12004_first_heir_conception_candidate_inputs.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
using namespace xar::ck3_11906;
namespace {
CurrentFirstHeirRelationshipReadV1 Household() {
  CurrentFirstHeirRelationshipReadV1 read{};
  read.failure = CurrentFirstHeirRelationshipFailureV1::none;
  read.heir_character_id = 38822;
  read.relationship.primary_spouse_character_id = 38718;
  read.relationship.spouse_character_ids = {38718};
  read.reproductive_inputs.emplace();
  auto &r = *read.reproductive_inputs;
  r.status = "available"; r.unavailable_reason = {};
  r.played_character_id = 1; r.heir_character_id = 38822; r.date_raw = 123;
  for (const auto id : {38822, 38718}) {
    CurrentFirstHeirReproductiveRowV1 row{};
    row.character_id = id;
    row.roles = id == 38822 ? std::vector<std::string_view>{"heir"} :
                         std::vector<std::string_view>{"primary_spouse", "spouse"};
    row.available = true; row.unavailable_reason = {};
    row.age_measure_raw = std::int16_t{32};
    row.sex_selector_raw = static_cast<std::uint8_t>(id == 38822 ? 0 : 1);
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
  for (const auto id : {38822, 38718}) {
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
  p.first_character_id = 38822; p.second_character_id = 38718;
  c.pairs.push_back(p);
  return c;
}

void Emit(std::string_view name, const CurrentFirstHeirConceptionCandidateInputsReadV1 &c) {
  std::cout << CurrentFirstHeirRelationshipResultJsonV1(
      name, 7, 38822, Household(), {}, nullptr, nullptr, &c) << '\n';
}
} // namespace
int main() {
  const auto fixture_path = std::filesystem::path(__FILE__).parent_path() /
      "fixtures" / "conception_pair_passive_12004_joined_journal.json";
  std::ifstream fixture(fixture_path, std::ios::binary);
  assert(fixture.is_open());
  // The retained pretty JSON has physical line breaks outside strings.
  // Match the native journal serializer's single-line transport fragment.
  std::string journal;
  for (char byte{}; fixture.get(byte);)
    if (byte != '\n' && byte != '\r') journal.push_back(byte);
  assert(journal.find("\"first_qword_raw\"") == std::string::npos);
  auto c = Companion();
  Emit("legacy_natural_absent", c);
  c.pairs[0].natural_conception_observations_json = journal;
  Emit("owned_retained_native_orientation", c);
  c.pairs[0].natural_conception_observations_json = "null";
  Emit("owned_journal_unavailable", c);
}
