#include "xar_bridge/entry_final_outer_refresh_12004.hpp"

#include <utility>

namespace xar::ck3_12004 {
namespace {

bool MatchesOccurrence(const FinalOuterOriginalStatStage12004& source,
                       const PlannedFinalOccurrence12004& occurrence) {
  return source.side_index == occurrence.side_index &&
         source.bucket == occurrence.bucket &&
         source.bucket_index == occurrence.bucket_index &&
         source.physical_entry_identity == occurrence.physical_entry_identity &&
         source.native_carmy_id == occurrence.native_carmy_id &&
         source.regiment_id == occurrence.regiment_id;
}

template <class T>
std::optional<bool> ObservedMatch(const std::optional<T>& observed, T supplied) {
  if (!observed) return std::nullopt;
  return *observed == supplied;
}

}  // namespace

FinalOuterRefreshPlan12004 PlanFinalOuterRefresh12004(
    const FinalOuterRefreshInput12004& input) {
  FinalOuterRefreshPlan12004 result;
  std::vector<bool> associated(input.original_stat_stages.size(), false);
  for (std::uint32_t side_index = 0; side_index < 2; ++side_index) {
    auto side = input.sides[side_index];
    side.side_index = side_index;
    const auto& original_province = input.original_province_arguments[side_index];
    auto& call = result.calls[side_index];
    call.side_index = side_index;
    call.province_load_rva = kFinalOuterProvinceLoads12004[side_index];
    call.call_rva = kFinalOuterSideCalls12004[side_index];
    call.return_rva = kFinalOuterSideReturns12004[side_index];
    if (input.supplied_combat_identity) {
      call.conditional_side_identity = *input.supplied_combat_identity +
          (side_index == 0 ? 0x20 : 0x368);
    }
    call.supplied_final_province_id = side.final_combat_province_id;
    call.supplied_final_province_identity = side.final_combat_province_identity;
    call.original_province_argument = original_province;
    call.original_province_id_matches_supplied = ObservedMatch(
        original_province.province_id, side.final_combat_province_id);
    call.original_province_identity_matches_supplied = ObservedMatch(
        original_province.province_identity, side.final_combat_province_identity);
    for (const auto& occurrence : PlanFinalSideOccurrences12004(side)) {
      PlannedFinalOuterOccurrence12004 joined;
      joined.occurrence = occurrence;
      joined.outer_traversal_ordinal = result.occurrences.size();
      joined.outer_side_call_rva = call.call_rva;
      joined.outer_side_return_rva = call.return_rva;
      joined.combat_province_load_rva = call.province_load_rva;
      for (std::size_t index = 0; index < input.original_stat_stages.size(); ++index) {
        const auto& stage = input.original_stat_stages[index];
        if (!MatchesOccurrence(stage, occurrence)) continue;
        joined.original_stat_stages.push_back({
            stage,
            ObservedMatch(stage.getter_province_id, side.final_combat_province_id),
            ObservedMatch(stage.getter_province_identity,
                          side.final_combat_province_identity)});
        associated[index] = true;
      }
      result.occurrences.push_back(std::move(joined));
    }
  }
  for (std::size_t index = 0; index < input.original_stat_stages.size(); ++index) {
    if (!associated[index]) {
      result.unmatched_original_stat_stages.push_back(input.original_stat_stages[index]);
    }
  }
  return result;
}

}  // namespace xar::ck3_12004
