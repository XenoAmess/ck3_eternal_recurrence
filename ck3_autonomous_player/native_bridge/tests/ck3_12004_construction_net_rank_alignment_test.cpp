#include "../src/player_world_building_action_candidate_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

namespace {

using namespace xar::ck3_11906;

// All IDs, frames and rows below are synthetic DTO inputs. They are not an
// observed game state, native definition-registry IDs, or material evidence.
constexpr std::int32_t kBarony = 10001;
constexpr std::int32_t kProvince = 20001;
constexpr std::uint64_t kProof = 17;
constexpr std::int64_t kReserve = 20'000'000;

PlayerWorldBuildingSourceResultV1 Source() {
  PlayerWorldBuildingSourceResultV1 source{};
  source.source_available = true;
  source.native_final_legality_evaluated = true;
  source.native_cost_evaluated = true;
  source.player_gold_observed = true;
  source.player_gold_raw = 100'000'000;
  source.completed_buildings_observed = true;
  source.snapshot_revision = 7;
  source.date_raw = 123456;
  source.player_character_id = 1007;
  PlayerWorldActiveConstructionV1 idle{};
  idle.barony_title_id = kBarony;
  idle.province_id = kProvince;
  idle.active = false;
  source.active_constructions.push_back(idle);
  return source;
}

PlayerWorldBuildingLegalSampleV1 Sample(
    std::int32_t type, std::int32_t slot, std::string_view key) {
  PlayerWorldBuildingLegalSampleV1 sample{};
  sample.barony_title_id = kBarony;
  sample.province_id = kProvince;
  sample.building_type_id = type;
  sample.slot_index = slot;
  sample.building_key = std::string{key};
  sample.native_cost_observed = true;
  sample.cost_raw_native[0] = 10'000'000;
  return sample;
}

PlayerWorldCompletedBuildingV1 Occupant(
    std::int32_t type, std::int32_t slot, std::string_view key) {
  PlayerWorldCompletedBuildingV1 old{};
  old.barony_title_id = kBarony;
  old.province_id = kProvince;
  old.building_type_id = type;
  old.slot_index = slot;
  old.building_key = std::string{key};
  return old;
}

bool Check(bool condition, std::string_view message) {
  if (!condition) {
    std::cerr << "RED: " << message << '\n';
  }
  return condition;
}

bool Chosen(const PlayerWorldBuildingActionCandidateV1 &candidate,
            std::int32_t type, std::int32_t slot) {
  return candidate.ready && candidate.barony_title_id == kBarony &&
         candidate.province_id == kProvince &&
         candidate.building_type_id == type && candidate.slot_index == slot;
}

bool GrossVersusNetAndIncomeLosingReplacement() {
  auto source = Source();
  // Gross70 replacing50 gives delta20; observed empty gross50 gives delta50.
  // A different gross70 replacing farm_estates_02=115 must be excluded.
  source.legal_samples = {
      Sample(30001, 0, "farm_estates_01"),
      Sample(30002, 1, "cereal_fields_01"),
      Sample(30003, 2, "watermills_01"),
  };
  source.completed_buildings = {
      Occupant(31001, 0, "cereal_fields_01"),
      Occupant(31003, 2, "farm_estates_02"),
  };
  if (!Check(Chosen(SelectPlayerWorldBuildingActionCandidateV1(
                        source, kProof, kReserve),
                    30002, 1),
             "net50 must beat gross70/delta20 and the income-losing slot")) {
    return false;
  }
  // Independently keep only the income-losing replacement: there is no
  // positive-increment candidate even though target gross income is positive.
  source.legal_samples = {Sample(30003, 2, "watermills_01")};
  return Check(!SelectPlayerWorldBuildingActionCandidateV1(
                    source, kProof, kReserve).ready,
               "farm_estates_02=115 replacement by income70 must be excluded");
}

bool EqualNetAndCostPreferObservedEmpty() {
  auto source = Source();
  source.legal_samples = {
      Sample(30010, 0, "cereal_fields_01"),
      Sample(30011, 1, "hunting_grounds_01"),
  };
  source.completed_buildings = {
      Occupant(31010, 0, "hunting_grounds_01"),
  };
  // Both deltas are25 and both costs equal. The occupied numeric tuple sorts
  // first, so selecting the empty slot proves the earlier semantic tie break.
  return Check(Chosen(SelectPlayerWorldBuildingActionCandidateV1(
                          source, kProof, kReserve),
                      30011, 1),
               "equal net/cost must prefer the observed empty slot");
}

bool KnownZeroIsUsableAndUnknownOldIsExcluded() {
  auto source = Source();
  source.legal_samples = {
      Sample(30019, 0, "farm_estates_01"),
      Sample(30020, 1, "hunting_grounds_01"),
  };
  source.completed_buildings = {
      Occupant(31019, 0, "unvalued_fixture_building"),
      Occupant(31020, 1, "military_camps_01"),
  };
  // Unknown is not zero. Treating it as zero would choose the gross70 row;
  // treating known military_camps_01=0 as unavailable would leave no winner.
  return Check(Chosen(SelectPlayerWorldBuildingActionCandidateV1(
                          source, kProof, kReserve),
                      30020, 1),
               "known zero old income must be usable and unknown old excluded");
}

} // namespace

int main() {
  if (!GrossVersusNetAndIncomeLosingReplacement() ||
      !EqualNetAndCostPreferObservedEmpty() ||
      !KnownZeroIsUsableAndUnknownOldIsExcluded()) {
    return 1;
  }
  std::cout
      << "{\"status\":\"GREEN\","
         "\"fixture\":\"ck3_12004_construction_net_rank_alignment\","
         "\"scenario_count\":3,\"selector_calls\":4,"
         "\"input_origin\":\"synthetic_real_DTOs\","
         "\"type_ids_are_synthetic\":true,\"live\":false}\n";
  return 0;
}
