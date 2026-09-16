#include "player_world_building_action_candidate_v1.hpp"

#include <algorithm>
#include <limits>
#include <tuple>

namespace xar::ck3_11906 {
namespace {

bool GoldOnlyStockCost(
    const PlayerWorldBuildingLegalSampleV1 &sample) noexcept {
  if (!sample.native_cost_observed || sample.cost_raw_native[0] <= 0) {
    return false;
  }
  // Stock 0x2CDD09D can add raw[7] to gold conditionally. Requiring every
  // non-gold raw slot to be zero makes that flag and all unmapped resources
  // immaterial for this bounded candidate, without guessing their identities.
  return std::all_of(sample.cost_raw_native.begin() + 1,
                     sample.cost_raw_native.end(),
                     [](std::int64_t amount) { return amount == 0; });
}

bool HoldingIdle(const PlayerWorldBuildingSourceResultV1 &source,
                 const PlayerWorldBuildingLegalSampleV1 &sample) noexcept {
  const auto found = std::find_if(
      source.active_constructions.begin(), source.active_constructions.end(),
      [&sample](const auto &state) {
        return state.barony_title_id == sample.barony_title_id &&
               state.province_id == sample.province_id;
      });
  return found != source.active_constructions.end() && !found->active;
}

} // namespace

PlayerWorldBuildingActionCandidateV1
SelectPlayerWorldBuildingActionCandidateV1(
    const PlayerWorldBuildingSourceResultV1 &source,
    const std::uint64_t proof_epoch,
    const std::int64_t minimum_gold_reserve_raw) noexcept {
  PlayerWorldBuildingActionCandidateV1 result{};
  if (!source.source_available ||
      source.failure != PlayerWorldBuildingFailureV1::none ||
      !source.native_final_legality_evaluated ||
      !source.native_cost_evaluated || source.legal_samples.empty()) {
    return result;
  }
  if (source.snapshot_revision == 0 || proof_epoch == 0 ||
      source.date_raw <= 0 || source.player_character_id <= 0) {
    result.failure = PlayerWorldBuildingActionFailureV1::frame_binding;
    return result;
  }
  if (!source.player_gold_observed || source.player_gold_raw < 0 ||
      minimum_gold_reserve_raw < 0) {
    result.failure = PlayerWorldBuildingActionFailureV1::resource_unknown;
    return result;
  }
  const PlayerWorldBuildingLegalSampleV1 *selected = nullptr;
  bool saw_gold_only = false;
  bool saw_active = false;
  for (const auto &sample : source.legal_samples) {
    if (!GoldOnlyStockCost(sample)) continue;
    saw_gold_only = true;
    if (!HoldingIdle(source, sample)) {
      saw_active = true;
      continue;
    }
    const auto cost = sample.cost_raw_native[0];
    // Stock affordability uses a strict comparison. The reserve protects
    // normal governance spending rather than optimizing the whole campaign.
    if (cost >= source.player_gold_raw ||
        minimum_gold_reserve_raw > source.player_gold_raw - cost) {
      continue;
    }
    if (selected == nullptr ||
        std::tie(cost, sample.barony_title_id, sample.province_id,
                 sample.building_type_id, sample.slot_index) <
            std::tie(selected->cost_raw_native[0],
                     selected->barony_title_id, selected->province_id,
                     selected->building_type_id, selected->slot_index)) {
      selected = &sample;
    }
  }
  if (selected == nullptr) {
    result.failure =
        saw_active && saw_gold_only
            ? PlayerWorldBuildingActionFailureV1::active_construction
            : saw_gold_only
                  ? PlayerWorldBuildingActionFailureV1::no_budget_safe_candidate
                  : PlayerWorldBuildingActionFailureV1::resource_unknown;
    return result;
  }
  result.ready = true;
  result.failure = PlayerWorldBuildingActionFailureV1::none;
  result.snapshot_revision = source.snapshot_revision;
  result.proof_epoch = proof_epoch;
  result.date_raw = source.date_raw;
  result.actor_character_id = source.player_character_id;
  result.barony_title_id = selected->barony_title_id;
  result.province_id = selected->province_id;
  result.building_type_id = selected->building_type_id;
  result.slot_index = selected->slot_index;
  result.player_gold_before_raw = source.player_gold_raw;
  result.stock_gold_cost_raw = selected->cost_raw_native[0];
  result.gold_reserve_after_raw =
      source.player_gold_raw - selected->cost_raw_native[0];
  result.stock_cost_raw_native = selected->cost_raw_native;
  return result;
}

bool ObservePlayerWorldBuildingMaterialResultV1(
    const PlayerWorldBuildingActionCandidateV1 &submitted,
    const PlayerWorldBuildingSourceResultV1 &fresh,
    const std::uint64_t fresh_proof_epoch) noexcept {
  if (!submitted.ready || !fresh.source_available ||
      fresh.failure != PlayerWorldBuildingFailureV1::none ||
      fresh_proof_epoch <= submitted.proof_epoch ||
      fresh.snapshot_revision < submitted.snapshot_revision ||
      fresh.date_raw < submitted.date_raw ||
      fresh.player_character_id != submitted.actor_character_id) {
    return false;
  }
  return std::any_of(
      fresh.active_constructions.begin(), fresh.active_constructions.end(),
      [&submitted](const auto &state) {
        return state.active &&
               state.barony_title_id == submitted.barony_title_id &&
               state.province_id == submitted.province_id &&
               state.building_type_id == submitted.building_type_id &&
               state.slot_index == submitted.slot_index &&
               state.initiator_character_id == submitted.actor_character_id;
      });
}

} // namespace xar::ck3_11906
