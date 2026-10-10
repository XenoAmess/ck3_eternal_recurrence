#include "xar_bridge/current_first_heir_conception_candidate_inputs_v1.hpp"
#include "xar_bridge/conception_pair_shortcircuit_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <vector>
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

struct GuardedMemory {
  std::map<std::uintptr_t, std::vector<std::byte>> fields;
  template<class T> void Put(std::uintptr_t address, T value) {
    auto &bytes = fields[address]; bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  static bool Read(void *context, const void *source, void *output,
                   std::size_t size) noexcept {
    const auto &memory = *static_cast<GuardedMemory *>(context);
    const auto found = memory.fields.find(reinterpret_cast<std::uintptr_t>(source));
    if (found == memory.fields.end() || found->second.size() != size) return false;
    std::memcpy(output, found->second.data(), size); return true;
  }
};
} // namespace
int main() {
  constexpr std::uintptr_t image = 0x10000000;
  constexpr std::uintptr_t first = 0x20000000;
  constexpr std::uintptr_t second = 0x20001000;
  GuardedMemory memory;
  memory.Put(first + 0x18, std::uint32_t{2});
  memory.Put(first + 0x1C, std::uint32_t{0x43686172});
  memory.Put(first + 0x1A1, std::uint8_t{0});
  memory.Put(first + 0x6C, std::int16_t{15});
  memory.Put(image + 0x5C69EA4, std::int32_t{16});
  const auto bindings = xar::ck3_12004::BindConceptionPairShortCircuit12004(
      image, "1.20.0.4", xar::ck3_12004::kExecutableSha256,
      &GuardedMemory::Read, &memory);
  auto companion = Companion();
  auto &pair = companion.pairs[0];
  pair.short_circuit = xar::ck3_12004::ReadConceptionPairShortCircuit12004(
      bindings, first, std::uint32_t{2}, second, std::uint32_t{3});
  assert(pair.short_circuit.source == "guarded_current_actual4_pair_provider_shortcircuit");
  assert(pair.short_circuit.status == "available");
  assert(pair.short_circuit.short_circuits_to_zero == true);
  assert(pair.short_circuit.first_output_raw == 0);
  assert(!pair.short_circuit.second_evaluated);
  // Preserve unrelated default observations; this cell adds no full-provider claim.
  const auto wire = CurrentFirstHeirRelationshipResultJsonV1(
      "actual_guarded_source", 7, 2, Household(), {}, nullptr, nullptr, &companion);
  assert(wire.find("guarded_current_actual4_pair_provider_shortcircuit") != std::string::npos);
  std::cout << wire << '\n';
}
