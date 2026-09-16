#include "player_world_building_action_candidate_v1.hpp"

#include <cstdlib>
#include <iostream>

namespace {

void Require(bool value, const char *name) {
  if (!value) {
    std::cerr << "RED " << name << '\n';
    std::abort();
  }
}

xar::ck3_11906::PlayerWorldBuildingSourceResultV1 R746Shape() {
  using namespace xar::ck3_11906;
  PlayerWorldBuildingSourceResultV1 source{};
  source.source_available = true;
  source.native_final_legality_evaluated = true;
  source.native_cost_evaluated = true;
  source.player_gold_observed = true;
  source.player_gold_raw = 50035659;
  source.snapshot_revision = 3;
  source.date_raw = 53178312;
  source.player_character_id = 29829;
  source.active_constructions.push_back({2103, 2635, false, -1, -1, -1});
  for (const auto type : {12, 24}) {
    for (const auto slot : {1, 2, 3}) {
      PlayerWorldBuildingLegalSampleV1 sample{};
      sample.barony_title_id = 2103;
      sample.province_id = 2635;
      sample.building_type_id = type;
      sample.slot_index = slot;
      sample.native_cost_observed = true;
      sample.cost_raw_native[0] = type == 24 ? 15000000 : 40000000;
      source.legal_samples.push_back(sample);
    }
  }
  return source;
}

} // namespace

int main() {
  using namespace xar::ck3_11906;
  {
    const auto source = R746Shape();
    const auto choice =
        SelectPlayerWorldBuildingActionCandidateV1(source, 46, 20000000);
    Require(choice.ready && choice.failure ==
                PlayerWorldBuildingActionFailureV1::none &&
                choice.actor_character_id == 29829 &&
                choice.barony_title_id == 2103 && choice.province_id == 2635 &&
                choice.building_type_id == 24 && choice.slot_index == 1 &&
                choice.stock_gold_cost_raw == 15000000 &&
                choice.gold_reserve_after_raw == 35035659,
            "R746_stock_gold_only_candidate_reserves_350_gold");
    auto fresh = source;
    fresh.active_constructions[0] = {2103, 2635, true, 24, 1, 29829};
    Require(!ObservePlayerWorldBuildingMaterialResultV1(choice, fresh, 46),
            "same_application_main_proof_is_not_material_receipt");
    Require(ObservePlayerWorldBuildingMaterialResultV1(choice, fresh, 47),
            "fresh_stock_active_construction_is_material_receipt");
    fresh.active_constructions[0].building_type_id = 12;
    Require(!ObservePlayerWorldBuildingMaterialResultV1(choice, fresh, 47),
            "wrong_building_does_not_confirm_pending_command");
  }
  {
    auto source = R746Shape();
    for (auto &sample : source.legal_samples) sample.cost_raw_native[7] = 1;
    const auto choice =
        SelectPlayerWorldBuildingActionCandidateV1(source, 46, 20000000);
    Require(!choice.ready && choice.failure ==
                PlayerWorldBuildingActionFailureV1::resource_unknown,
            "unmapped_stock_raw7_cannot_be_ignored");
  }
  {
    auto source = R746Shape();
    source.active_constructions[0] = {2103, 2635, true, 12, 0, 29829};
    const auto choice =
        SelectPlayerWorldBuildingActionCandidateV1(source, 46, 20000000);
    Require(!choice.ready && choice.failure ==
                PlayerWorldBuildingActionFailureV1::active_construction,
            "already_active_province_cannot_receive_second_construction");
  }
  {
    const auto source = R746Shape();
    const auto choice =
        SelectPlayerWorldBuildingActionCandidateV1(source, 46, 40000000);
    Require(!choice.ready && choice.failure ==
                PlayerWorldBuildingActionFailureV1::no_budget_safe_candidate,
            "reserve_threshold_excludes_both_expensive_candidates");
  }
  std::cout << "GREEN private R746 cost-to-action candidate and material guard\n";
}
