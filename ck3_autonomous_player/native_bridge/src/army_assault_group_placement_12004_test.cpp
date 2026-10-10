#include "xar_bridge/army_assault_group_placement_12004.hpp"

#include <cassert>
#include <bit>
#include <cstring>
#include <iostream>

using namespace xar::ck3_12004;

namespace {

std::uint32_t Hash(std::uint32_t key) {
  std::uint32_t result = 0x811C9DC5;
  for (int shift : {0, 8, 16, 24})
    result = (result ^ ((key >> shift) & 255)) * 0x01000193;
  return result;
}

xar::game::ArmyDailyAssaultAllocatorWitnessV1 Witness(std::uint32_t rva) {
  xar::game::ArmyDailyAssaultAllocatorWitnessV1 proof;
  proof.ready = proof.actual_read_ready = true;
  proof.expected_rva_u32 = rva;
  proof.matches_expected = true;
  return proof;
}

xar::game::ArmyDailyAssaultGroupV1 Group(std::int64_t slot, std::uint8_t control,
                                      std::uint32_t key) {
  xar::game::ArmyDailyAssaultGroupV1 result;
  result.physical_slot_i64 = slot;
  result.control_raw_u8 = control;
  result.hash_raw_u32 = Hash(key);
  result.siege_full_id_u32 = key;
  result.armies.ready = result.armies.references_ready = true;
  result.arrgs.ready = result.arrgs.references_ready = true;
  result.armies.allocator_witness = Witness(0x54E0570);
  result.arrgs.allocator_witness = Witness(0x54DEB68);
  for (std::uint32_t id : {101u, 101u}) {
    xar::game::ArmyDailyAssaultOccurrenceV1 occurrence;
    occurrence.native_index = static_cast<std::int32_t>(result.armies.occurrences.size());
    occurrence.raw_full_id_u32 = id;
    result.armies.occurrences.push_back(occurrence);
  }
  for (std::uint32_t id : {7u, 9u, 7u}) {
    xar::game::ArmyDailyAssaultArRgOccurrenceV1 occurrence;
    occurrence.native_index = static_cast<std::int32_t>(result.arrgs.occurrences.size());
    occurrence.raw_full_id_u32 = id;
    result.arrgs.occurrences.push_back(occurrence);
  }
  result.armies.count_raw_i32 = 2;
  result.arrgs.count_raw_i32 = 3;
  return result;
}

DailyAssaultPreparationAppendInput12004 Request(std::int32_t index, std::uint32_t key) {
  DailyAssaultPreparationAppendInput12004 request;
  request.native_occurrence_index = index;
  request.selected_siege_full_id_u32 = key;
  request.selected_siege_fnv1a_u32 = Hash(key);
  request.selected_army_full_id_u32 = 202;
  request.army_append_input_ready = true;
  request.army_append = true;
  request.arrg_append_inputs_ready = true;
  request.ordered_arrg_full_ids_u32 = std::vector<std::uint32_t>{9, 9, 7};
  return request;
}

DailyAssaultPreparationInput12004 Preparation() {
  DailyAssaultPreparationInput12004 input;
  input.boundary_binding_ready = true;
  input.boundary.executable_sha256 = kDailyAssaultPreparationExecutableSha256;
  input.boundary.frame_identity = "new-focus36-frame";
  input.current_group_frame_matches = true;
  input.ordered_append_inputs_ready = true;
  xar::game::ArmyCurrentDailyAssaultTableV1 table;
  table.header.occupied_count_raw_i32 = 2;
  table.header.mask_raw_i32 = 3;
  table.header.tail_distance_raw_u8 = std::uint8_t{3};
  table.header.load_factor_f32_bits_u32 = std::bit_cast<std::uint32_t>(0.5f);
  table.header.end_slot_raw_i32 = 7;
  table.header.end_marker_control_raw_u8 = std::uint8_t{255};
  table.physical_scan_ready = table.raw_groups_ready = true;
  for (std::int64_t slot = 0; slot < 7; ++slot)
    table.physical_controls.push_back({slot, static_cast<std::uint8_t>(slot == 0 ? 1 : slot == 1 ? 2 : 0), {}});
  table.groups = {Group(0, 1, 13), Group(1, 2, 5)};
  input.current_group_records = table;
  input.ordered_append_inputs = {Request(0, 1)};
  return input;
}

AssaultPlacementBaseline12004 Baseline() {
  AssaultPlacementBaseline12004 baseline;
  baseline.frame_identity = "new-focus36-frame";
  baseline.source_provenance = "explicit fresh conditional fixture, not a runtime capture";
  baseline.native_empty_storage_matches = false;
  return baseline;
}

const AssaultPlacementGroup12004 &Find(const AssaultPlacementResult12004 &result, std::uint32_t key) {
  for (const auto &group : result.projected_groups)
    if (group.value.siege_full_id_u32 == key) return group;
  assert(false);
  return result.projected_groups.front();
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 2 && std::strcmp(argv[1], "--growth-physical-order-only") == 0);
  auto input = Preparation();
  const auto retained = *input.current_group_records;
  const auto result = ProjectAssaultGroupPlacement12004(input, Baseline());
  assert(result.ready && result.applied_request_count == 1);
  assert(result.projected_header.mask_raw_i32 == 7);
  assert(result.projected_header.tail_distance_raw_u8 == 5);
  assert(result.projected_header.occupied_count_raw_i32 == 3);
  assert(result.projected_header.end_slot_raw_i32 == 13);
  assert(result.growth.size() == 1 && result.growth[0].allocated_bytes == 14 * 64);
  assert((result.growth[0].old_reinsert_physical_order == std::vector<std::int64_t>{0, 1}));
  assert(result.projected_groups[0].value.siege_full_id_u32 == std::uint32_t{13});
  assert(result.projected_groups[1].value.siege_full_id_u32 == std::uint32_t{5});
  assert(Find(result, 1).value.physical_slot_i64 == 4);
  assert(Find(result, 13).value.armies.occurrences.size() == 2);
  assert(Find(result, 13).value.arrgs.occurrences[0].raw_full_id_u32 == std::uint32_t{7});
  assert(Find(result, 13).value.arrgs.occurrences[2].raw_full_id_u32 == std::uint32_t{7});
  assert(Find(result, 1).value.arrgs.occurrences[0].raw_full_id_u32 == std::uint32_t{9});
  assert(Find(result, 1).value.arrgs.occurrences[1].raw_full_id_u32 == std::uint32_t{9});
  assert(result.growth_release_inputs.size() == 2);
  for (const auto &release : result.growth_release_inputs) {
    assert(release.source_value_moved);
    assert(release.armies_after_transfer.data_present == false);
    assert(release.armies_after_transfer.release_header_v1->capacity_raw_i32 == 0);
    assert(release.arrgs_after_transfer.release_header_v1->count_raw_i32 == 0);
  }
  assert(*input.current_group_records == retained && *result.observed_current_table == retained);
  assert(!result.actual_callback_execution_observed && !result.full_future_table_placement_ready);
  assert(!result.full_daily_assault_ready && !result.full_monthly_execution_ready);

  // Key comparison wins before density growth; repeated references append.
  input = Preparation();
  input.ordered_append_inputs = {Request(0, 13)};
  input.current_group_records->groups[0].hash_raw_u32.reset();
  auto hit = ProjectAssaultGroupPlacement12004(input, Baseline());
  assert(hit.ready && hit.growth.empty() && hit.requests[0].inserted == false);
  assert(hit.projected_header.occupied_count_raw_i32 == 2);
  assert(Find(hit, 13).value.armies.occurrences.size() == 3);
  assert(Find(hit, 13).value.arrgs.occurrences.size() == 6);
  assert(!Find(hit, 13).value.armies.release_header_v1);

  // Carry overflow rolls back the first slot before growth. The recursive
  // returned slot is 0, whereas the pre-growth first selected slot was 1.
  input = Preparation();
  auto &table = *input.current_group_records;
  table.header.mask_raw_i32 = 7;
  table.header.tail_distance_raw_u8 = std::uint8_t{2};
  table.header.occupied_count_raw_i32 = 3;
  table.header.load_factor_f32_bits_u32 = 0x7FC00000;
  table.header.end_slot_raw_i32 = 10;
  table.groups = {Group(0, 1, 13), Group(1, 1, 4), Group(2, 2, 12)};
  table.physical_controls.clear();
  for (std::int64_t slot = 0; slot < 10; ++slot)
    table.physical_controls.push_back({slot, static_cast<std::uint8_t>(slot < 2 ? 1 : slot == 2 ? 2 : 0), {}});
  input.ordered_append_inputs = {Request(0, 5)};
  const auto overflow = ProjectAssaultGroupPlacement12004(input, Baseline());
  assert(overflow.ready && overflow.growth.size() == 1);
  assert(overflow.projected_header.mask_raw_i32 == 15);
  assert(overflow.projected_header.occupied_count_raw_i32 == 4);
  assert(overflow.requests[0].returned_physical_slot_i64 == 0);
  assert(Find(overflow, 5).value.armies.occurrences.size() == 1);
  assert(Find(overflow, 4).value.armies.occurrences.size() == 2);
  assert((overflow.growth[0].old_reinsert_physical_order == std::vector<std::int64_t>{0, 1, 2}));

  // Raw occupied count, not observed group count, drives growth scanning.
  input = Preparation();
  input.current_group_records->header.occupied_count_raw_i32 = 3;
  const auto mismatch = ProjectAssaultGroupPlacement12004(input, Baseline());
  assert(!mismatch.ready && mismatch.applied_request_count == 0);
  assert(mismatch.unavailable_reason == "demanded_physical_record_unavailable");
  assert(mismatch.growth.empty() && mismatch.projected_header.mask_raw_i32 == 3);

  input = Preparation();
  input.current_group_records->groups[0].armies.allocator_witness.reset();
  const auto missing = ProjectAssaultGroupPlacement12004(input, Baseline());
  assert(!missing.ready && missing.applied_request_count == 0);
  assert(missing.unavailable_reason == "army_allocator_transfer_branch_unavailable");

  input = Preparation();
  auto baseline = Baseline();
  baseline.stage = AssaultPlacementBaselineStage12004::pre_date_copied_table;
  const auto stage = ProjectAssaultGroupPlacement12004(input, baseline);
  assert(!stage.ready && stage.unavailable_reason == "pre_date_baseline_requires_actual_source_entry_binding");
  input.boundary.stage = DailyAssaultPreparationStage12004::pre_date_assault_call;
  input.boundary.callsite_rva = kDailyAssaultPreparationCallsiteRva;
  input.boundary.native_occurrence_index = 2;
  const auto earlier = ProjectAssaultGroupPlacement12004(input, baseline);
  assert(!earlier.ready && earlier.unavailable_reason == "request_precedes_bound_placement_baseline");
  input.ordered_append_inputs = {Request(2, 1)};
  const auto suffix = ProjectAssaultGroupPlacement12004(input, baseline);
  assert(suffix.ready && !suffix.actual_callback_execution_observed);
  baseline = Baseline();
  baseline.native_empty_storage_matches.reset();
  const auto unbound = ProjectAssaultGroupPlacement12004(input, baseline);
  assert(!unbound.ready && unbound.unavailable_reason == "native_empty_storage_comparison_unbound");

  std::cout << "GREEN: new actual4 growth order, carried return slot, repeated references, post-move release headers and unavailable bindings\n";
}
