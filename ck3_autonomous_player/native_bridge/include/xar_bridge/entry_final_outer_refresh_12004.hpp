#pragma once

#include "xar_bridge/entry_final_occurrence_12004.hpp"

#include <array>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::uint32_t kFinalOuterPriorStageCall12004 = 0x0247AB02;
inline constexpr std::uint32_t kFinalOuterPriorStageTarget12004 = 0x02586EB0;
inline constexpr std::array<std::uint32_t, 2> kFinalOuterProvinceLoads12004{
    0x0247AB07, 0x0247AB17};
inline constexpr std::array<std::uint32_t, 2> kFinalOuterSideCalls12004{
    0x0247AB12, 0x0247AB21};
inline constexpr std::array<std::uint32_t, 2> kFinalOuterSideReturns12004{
    0x0247AB17, 0x0247AB26};
inline constexpr std::uint32_t kFinalOuterSideTarget12004 = 0x02651050;

// Optional original argument observations are independent for the two CALLs.
// Missing observations never borrow the initial Army Province or the other CALL.
struct FinalOuterOriginalProvince12004 {
  std::optional<std::int32_t> province_id;
  std::optional<std::uintptr_t> province_identity;
  std::optional<std::uint64_t> original_invocation_sequence;
};

// The caller supplies the unchanged original stat-stage ledger (for example
// continuation14's numerical join). This leaf computes neither a getter nor
// Model lineage. An observed writer is not silently assigned an outer origin.
struct FinalOuterOriginalStatStage12004 {
  std::uint32_t side_index{};
  FinalOccurrenceBucket12004 bucket{};
  std::size_t bucket_index{};
  std::uintptr_t physical_entry_identity{};
  std::uint32_t native_carmy_id{};
  std::uint32_t regiment_id{};
  std::string_view getter_stage;
  std::string_view original_origin;
  std::string_view original_source_ledger;
  std::optional<std::uint64_t> consumption_sequence;
  std::optional<std::int32_t> getter_province_id;
  std::optional<std::uintptr_t> getter_province_identity;
  std::optional<bool> entry_association_proven;
  std::optional<bool> completed_preparation_lineage_proven;
  std::optional<std::uintptr_t> preparation_model_identity;
  std::optional<std::uintptr_t> installed_model_identity;
  std::optional<bool> installed_model_transfer_observed;
  std::optional<bool> original_outer_invocation_associated;
};

struct FinalOuterRefreshInput12004 {
  // Slots are source-bound Side0/Side1; each retains its independent supplied
  // final Province and original row inputs from the already closed Side leaf.
  std::array<FinalSideOccurrenceInput12004, 2> sides;
  std::optional<std::uintptr_t> supplied_combat_identity;
  std::array<FinalOuterOriginalProvince12004, 2> original_province_arguments;
  std::span<const FinalOuterOriginalStatStage12004> original_stat_stages;
};

struct FinalOuterSideCallPlan12004 {
  std::uint32_t side_index{};
  std::uint32_t province_load_rva{};
  std::uint32_t call_rva{};
  std::uint32_t return_rva{};
  std::optional<std::uintptr_t> conditional_side_identity;
  std::int32_t supplied_final_province_id{};
  std::uintptr_t supplied_final_province_identity{};
  FinalOuterOriginalProvince12004 original_province_argument;
  std::optional<bool> original_province_id_matches_supplied;
  std::optional<bool> original_province_identity_matches_supplied;
};

struct FinalOuterJoinedStatStage12004 {
  FinalOuterOriginalStatStage12004 original;
  std::optional<bool> getter_province_id_matches_supplied;
  std::optional<bool> getter_province_identity_matches_supplied;
};

struct PlannedFinalOuterOccurrence12004 {
  PlannedFinalOccurrence12004 occurrence;  // Local ordinal remains unchanged.
  std::size_t outer_traversal_ordinal{};
  std::uint32_t outer_side_call_rva{};
  std::uint32_t outer_side_return_rva{};
  std::uint32_t combat_province_load_rva{};
  std::vector<FinalOuterJoinedStatStage12004> original_stat_stages;
};

struct FinalOuterRefreshPlan12004 {
  std::array<FinalOuterSideCallPlan12004, 2> calls;
  std::vector<PlannedFinalOuterOccurrence12004> occurrences;
  std::vector<FinalOuterOriginalStatStage12004> unmatched_original_stat_stages;
  bool original_outer_invocation_inferred = false;
};

// Source-bound conditional assembly only. Original event/model observations
// and their missing facts are carried unchanged, not inferred from static order.
FinalOuterRefreshPlan12004 PlanFinalOuterRefresh12004(
    const FinalOuterRefreshInput12004& input);

}  // namespace xar::ck3_12004
