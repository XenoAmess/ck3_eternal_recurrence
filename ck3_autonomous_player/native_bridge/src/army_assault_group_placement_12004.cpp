#include "xar_bridge/army_assault_group_placement_12004.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <map>
#include <stdexcept>
#include <utility>

namespace xar::ck3_12004 {
namespace {

constexpr std::uint32_t kArmyAllocator = 0x54E0570;
constexpr std::uint32_t kArRgAllocator = 0x54DEB68;

void Need(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}

std::int32_t I32(std::uint32_t value) { return std::bit_cast<std::int32_t>(value); }
std::int32_t Add(std::int32_t value, std::uint32_t increment) {
  return I32(std::bit_cast<std::uint32_t>(value) + increment);
}
std::uint32_t Hash(std::uint32_t key) {
  std::uint32_t hash = 0x811C9DC5;
  for (int shift : {0, 8, 16, 24})
    hash = (hash ^ ((key >> shift) & 0xFF)) * 0x01000193;
  return hash;
}

bool Canonical(const std::optional<game::ArmyDailyAssaultAllocatorWitnessV1> &proof,
               std::uint32_t rva) {
  return proof && proof->ready && proof->actual_read_ready &&
      proof->matches_expected == true && proof->expected_rva_u32 == rva;
}

template <class References> void MovedEmpty(References &refs) {
  refs.status = "source_derived_moved_empty";
  refs.ready = refs.references_ready = true;
  refs.unavailable_reason.clear();
  refs.count_raw_i32 = 0;
  refs.data_identity = "null";
  refs.data_present = false;
  refs.occurrences.clear();
  refs.observed_occurrence_count = 0;
  game::ArmyDailyAssaultReleaseHeaderV1 header;
  header.status = "source_derived_null_zero_header";
  header.ready = true;
  header.data_identity = "null";
  header.data_present = false;
  header.count_raw_i32 = header.capacity_raw_i32 = 0;
  refs.release_header_v1 = header;
}

template <class References> void AppendHeaderUnknown(References &refs) {
  refs.status = "source_bound_projected_reference_occurrences";
  refs.ready = refs.references_ready = true;
  refs.unavailable_reason.clear();
  refs.count_raw_i32 = static_cast<std::int32_t>(refs.occurrences.size());
  refs.observed_occurrence_count = *refs.count_raw_i32;
  // Appends retain raw logical order. Their allocation postimage is a
  // separate source stage and is not supplied to a release observer.
  refs.data_identity.reset();
  refs.data_present.reset();
  refs.release_header_v1.reset();
}

struct State {
  game::ArmyDailyAssaultTableHeaderV1 header;
  std::map<std::int64_t, std::uint8_t> controls;
  std::map<std::int64_t, AssaultPlacementGroup12004> groups;
  bool implicit_zero = false, order_ready = false;
  std::int64_t zero_end = 0;
  std::optional<bool> empty_storage_matches;
  std::vector<AssaultPlacementGrowth12004> growth;
  std::vector<AssaultPlacementGrowthRelease12004> releases;
  std::size_t operations = 0, operation_limit = 0;

  void Step() { Need(operations++ < operation_limit, "projection_operation_limit"); }
  std::uint8_t Control(std::int64_t slot) {
    Step();
    if (auto found = controls.find(slot); found != controls.end()) return found->second;
    if (implicit_zero && slot >= 0 && slot < zero_end) return 0;
    throw std::runtime_error("demanded_physical_control_unavailable");
  }
  AssaultPlacementGroup12004 &Group(std::int64_t slot) {
    auto found = groups.find(slot);
    Need(found != groups.end(), "demanded_physical_record_unavailable");
    Need(found->second.value.siege_full_id_u32.has_value(), "demanded_full_key_unavailable");
    return found->second;
  }
  void RequireMovable(const AssaultPlacementGroup12004 &record) {
    const auto &v = record.value;
    Need(v.hash_raw_u32.has_value(), "demanded_hash_unavailable");
    Need(v.siege_full_id_u32.has_value(), "demanded_full_key_unavailable");
    Need(v.armies.references_ready && v.arrgs.references_ready,
         "demanded_reference_occurrences_unavailable");
    for (const auto &x : v.armies.occurrences)
      Need(x.raw_full_id_u32.has_value(), "demanded_army_full_reference_unavailable");
    for (const auto &x : v.arrgs.occurrences)
      Need(x.raw_full_id_u32.has_value(), "demanded_arrg_full_reference_unavailable");
    Need(record.army_allocator_canonical_by_source || Canonical(v.armies.allocator_witness, kArmyAllocator),
         "army_allocator_transfer_branch_unavailable");
    Need(record.arrg_allocator_canonical_by_source || Canonical(v.arrgs.allocator_witness, kArRgAllocator),
         "arrg_allocator_transfer_branch_unavailable");
  }
  void Store(std::int64_t slot, std::uint8_t distance,
             AssaultPlacementGroup12004 record) {
    record.value.physical_slot_i64 = slot;
    record.value.control_raw_u8 = distance;
    record.army_allocator_canonical_by_source = true;
    record.arrg_allocator_canonical_by_source = true;
    // Moving a copied witness to another receiver is not a new actual read.
    record.value.armies.allocator_witness.reset();
    record.value.arrgs.allocator_witness.reset();
    groups[slot] = std::move(record);
    controls[slot] = distance;
  }
  std::int32_t GrowthIndex() {
    Need(header.mask_raw_i32.has_value(), "growth_mask_unavailable");
    const auto operand = Add(*header.mask_raw_i32, 1);
    const auto index = operand <= 1 ? 3 :
        std::max(3, static_cast<int>(std::bit_width(static_cast<std::uint32_t>(operand - 1))) + 1);
    Need(index < 31, "native_nonreturning_growth_index_boundary");
    return index;
  }
  bool DensityGrowth() {
    Need(header.occupied_count_raw_i32 && header.mask_raw_i32 && header.load_factor_f32_bits_u32,
         "growth_density_operands_unavailable");
    const float numerator = static_cast<float>(Add(*header.occupied_count_raw_i32, 1));
    const float denominator = static_cast<float>(*header.mask_raw_i32);
    const float ratio = numerator / denominator;
    const float threshold = std::bit_cast<float>(*header.load_factor_f32_bits_u32);
    return ratio > threshold; // ordered strictly greater, actual COMISS/JA
  }
  struct Return { std::int64_t slot; bool inserted; std::string branch; };
  Return Insert(AssaultPlacementGroup12004 incoming, bool &source_moved,
                bool empty_constructor);
  void Grow();
};

void State::Grow() {
  Step();
  const auto index = GrowthIndex();
  Need(header.occupied_count_raw_i32.has_value(), "growth_old_occupied_count_unavailable");
  const auto saved_count = *header.occupied_count_raw_i32;
  // Native equality is demanded only when a positive old count would enter
  // reinsertion. It is independent from current raw group availability.
  if (saved_count > 0)
    Need(empty_storage_matches.has_value(), "native_empty_storage_comparison_unbound");
  State old = *this;
  const auto event_index = growth.size();
  AssaultPlacementGrowth12004 event;
  event.index_i32 = index;
  event.old_occupied_count_i32 = saved_count;
  const std::uint32_t main_records = std::uint32_t{1} << index;
  event.new_mask_i32 = I32(main_records - 1);
  event.new_tail_u8 = static_cast<std::uint8_t>(index + 2);
  event.new_end_slot_i32 = static_cast<std::int32_t>(main_records + event.new_tail_u8);
  event.allocated_record_count = std::uint64_t{main_records} + event.new_tail_u8 + 1;
  event.allocated_bytes = event.allocated_record_count << 6;
  event.symbolic_storage_identity = "source_derived_growth_storage_" + std::to_string(event_index);
  if (empty_storage_matches) event.old_table_release_selected = !*empty_storage_matches;
  growth.push_back(event);
  header.mask_raw_i32 = event.new_mask_i32;
  header.tail_distance_raw_u8 = event.new_tail_u8;
  header.occupied_count_raw_i32 = 0;
  header.entries_identity = event.symbolic_storage_identity;
  header.entries_present = true;
  header.end_slot_raw_i32 = event.new_end_slot_i32;
  header.end_marker_control_raw_u8 = std::uint8_t{0xFF};
  header.status = "source_derived_normal_return_growth";
  header.ready = true;
  controls.clear();
  groups.clear();
  implicit_zero = true;
  zero_end = event.new_end_slot_i32;
  controls[zero_end] = 0xFF;
  order_ready = true;
  empty_storage_matches = false; // normal allocator result is separate storage
  if (saved_count <= 0 || old.empty_storage_matches == true) return;

  std::int32_t remaining = saved_count;
  for (std::int64_t slot = 0; remaining > 0; ++slot) {
    const auto control = old.Control(slot);
    operations = std::max(operations, old.operations);
    if (control == 0) continue;
    auto record = old.Group(slot);
    record.value.control_raw_u8 = control;
    bool moved = false;
    Insert(record, moved, false);
    growth[event_index].old_reinsert_physical_order.push_back(slot);
    AssaultPlacementGrowthRelease12004 release;
    release.growth_index = event_index;
    release.old_physical_slot_i64 = slot;
    release.source_value_moved = moved;
    release.armies_after_transfer = record.value.armies;
    release.arrgs_after_transfer = record.value.arrgs;
    if (moved) {
      MovedEmpty(release.armies_after_transfer);
      MovedEmpty(release.arrgs_after_transfer);
    }
    releases.push_back(std::move(release));
    remaining = Add(remaining, 0xFFFFFFFF);
  }
}

State::Return State::Insert(AssaultPlacementGroup12004 incoming, bool &source_moved,
                           bool empty_constructor) {
  Step();
  Need(header.mask_raw_i32.has_value(), "probe_mask_unavailable");
  Need(incoming.value.hash_raw_u32 && incoming.value.siege_full_id_u32,
       "incoming_key_hash_unavailable");
  const auto hash = *incoming.value.hash_raw_u32;
  const auto key = *incoming.value.siege_full_id_u32;
  auto slot = static_cast<std::int64_t>(I32(hash & std::bit_cast<std::uint32_t>(*header.mask_raw_i32)));
  std::uint8_t distance = 1;
  std::uint8_t control;
  for (;;) {
    control = Control(slot);
    if (control < distance) break;
    if (*Group(slot).value.siege_full_id_u32 == key)
      return {slot, false, "full_key_hit"};
    distance = static_cast<std::uint8_t>(distance + 1);
    ++slot;
  }
  Need(header.tail_distance_raw_u8.has_value(), "probe_tail_unavailable");
  if (distance > *header.tail_distance_raw_u8 || DensityGrowth()) {
    Grow();
    auto result = Insert(std::move(incoming), source_moved, empty_constructor);
    result.branch = "initial_growth_then_" + result.branch;
    return result;
  }
  if (!empty_constructor) RequireMovable(incoming);
  if (control == 0) {
    Store(slot, distance, std::move(incoming));
    if (!empty_constructor) source_moved = true;
    header.occupied_count_raw_i32 = Add(*header.occupied_count_raw_i32, 1);
    return {slot, true, "direct_empty"};
  }
  const auto first_slot = slot;
  auto carried = Group(slot);
  RequireMovable(carried);
  auto carried_distance = static_cast<std::uint8_t>(control + 1);
  Store(first_slot, distance, std::move(incoming));
  if (!empty_constructor) source_moved = true;
  for (;;) {
    ++slot;
    control = Control(slot);
    if (control == 0) {
      Store(slot, carried_distance, std::move(carried));
      header.occupied_count_raw_i32 = Add(*header.occupied_count_raw_i32, 1);
      return {first_slot, true, "carried_empty_completion"};
    }
    if (control < carried_distance) {
      auto resident = Group(slot);
      RequireMovable(resident);
      Store(slot, carried_distance, std::move(carried));
      carried = std::move(resident);
      carried_distance = static_cast<std::uint8_t>(control + 1);
      // Actual lower-distance arm increments swapped-in resident control
      // and advances without comparing tail.
      continue;
    }
    carried_distance = static_cast<std::uint8_t>(carried_distance + 1);
    if (carried_distance <= *header.tail_distance_raw_u8) continue;
    auto original = Group(first_slot);
    Store(first_slot, carried_distance, std::move(carried));
    bool original_moved = false;
    Grow();
    auto result = Insert(std::move(original), original_moved, false);
    result.branch = "carried_overflow_growth_then_" + result.branch;
    return result;
  }
}

AssaultPlacementGroup12004 Empty(std::uint32_t hash, std::uint32_t key) {
  AssaultPlacementGroup12004 record;
  record.value.status = "source_bound_projected_group";
  record.value.hash_raw_u32 = hash;
  record.value.siege_full_id_u32 = key;
  record.army_allocator_canonical_by_source = record.arrg_allocator_canonical_by_source = true;
  MovedEmpty(record.value.armies);
  MovedEmpty(record.value.arrgs);
  return record;
}

void Append(AssaultPlacementGroup12004 &record,
            const DailyAssaultPreparationAppendInput12004 &request) {
  Need(record.value.armies.references_ready && record.value.arrgs.references_ready,
       "append_existing_references_unavailable");
  game::ArmyDailyAssaultOccurrenceV1 army;
  army.native_index = static_cast<std::int32_t>(record.value.armies.occurrences.size());
  army.raw_full_id_u32 = *request.selected_army_full_id_u32;
  record.value.armies.occurrences.push_back(army);
  AppendHeaderUnknown(record.value.armies);
  for (auto id : *request.ordered_arrg_full_ids_u32) {
    game::ArmyDailyAssaultArRgOccurrenceV1 arrg;
    arrg.native_index = static_cast<std::int32_t>(record.value.arrgs.occurrences.size());
    arrg.raw_full_id_u32 = id;
    record.value.arrgs.occurrences.push_back(arrg);
  }
  if (!request.ordered_arrg_full_ids_u32->empty()) AppendHeaderUnknown(record.value.arrgs);
}

} // namespace

AssaultPlacementResult12004 ProjectAssaultGroupPlacement12004(
    const DailyAssaultPreparationInput12004 &preparation,
    const AssaultPlacementBaseline12004 &baseline) {
  AssaultPlacementResult12004 result;
  result.frame_identity = baseline.frame_identity;
  result.source_provenance = baseline.source_provenance;
  result.observed_current_table = preparation.current_group_records;
  State state;
  state.operation_limit = baseline.operation_limit;
  try {
    Need(preparation.boundary_binding_ready, "preparation_boundary_unbound");
    Need(preparation.boundary.executable_sha256 == kDailyAssaultPreparationExecutableSha256,
         "placement_executable_pin_mismatch");
    Need(!baseline.source_provenance.empty() && !baseline.frame_identity.empty(), "placement_baseline_unbound");
    Need(baseline.frame_identity == preparation.boundary.frame_identity && preparation.current_group_frame_matches,
         "placement_baseline_frame_mismatch");
    if (baseline.stage == AssaultPlacementBaselineStage12004::pre_date_copied_table) {
      Need(preparation.boundary.stage == DailyAssaultPreparationStage12004::pre_date_assault_call,
           "pre_date_baseline_requires_actual_source_entry_binding");
      Need(preparation.boundary.callsite_rva == kDailyAssaultPreparationCallsiteRva &&
           preparation.boundary.native_occurrence_index.has_value(),
           "pre_date_occurrence_boundary_unavailable");
      result.stage = "pre_date_source_bound_conditional_projection";
    }
    Need(preparation.current_group_records.has_value(), "current_group_records_unavailable");
    const auto &table = *preparation.current_group_records;
    Need(table.source == "native_current_daily_assault_table" && table.stage == "observed_current_daily_assault_table",
         "placement_baseline_requires_copied_current_table");
    state.header = table.header;
    state.order_ready = table.physical_scan_ready;
    state.empty_storage_matches = baseline.native_empty_storage_matches;
    for (const auto &control : table.physical_controls) {
      if (!control.control_raw_u8) continue;
      Need(state.controls.emplace(control.physical_slot_i64, *control.control_raw_u8).second,
           "duplicate_physical_control_input");
    }
    if (table.header.end_slot_raw_i32 && table.header.end_marker_control_raw_u8)
      state.controls.emplace(*table.header.end_slot_raw_i32, *table.header.end_marker_control_raw_u8);
    for (const auto &group : table.groups)
      Need(state.groups.emplace(group.physical_slot_i64, AssaultPlacementGroup12004{group}).second,
           "duplicate_physical_group_input");
    Need(preparation.ordered_append_inputs_ready, "ordered_append_inputs_unavailable");
  } catch (const std::runtime_error &error) {
    result.unavailable_reason = error.what();
    return result;
  }

  std::int32_t previous_index = -1;
  for (const auto &input : preparation.ordered_append_inputs) {
    AssaultPlacementRequestResult12004 request;
    request.native_occurrence_index = input.native_occurrence_index;
    auto trial = state;
    try {
      Need(input.native_occurrence_index > previous_index, "original_roster_occurrence_order_unbound");
      if (baseline.stage == AssaultPlacementBaselineStage12004::pre_date_copied_table) {
        Need(input.native_occurrence_index >= *preparation.boundary.native_occurrence_index,
             "request_precedes_bound_placement_baseline");
        if (result.applied_request_count == 0)
          Need(input.native_occurrence_index == *preparation.boundary.native_occurrence_index,
               "first_request_does_not_match_bound_occurrence");
      }
      Need(input.army_append_input_ready && input.army_append.has_value(), "army_append_selection_unavailable");
      if (!*input.army_append) {
        request.status = "available";
        request.branch = "source_admission_does_not_append";
      } else {
        Need(input.selected_siege_full_id_u32 && input.selected_siege_fnv1a_u32 && input.selected_army_full_id_u32,
             "selected_full_key_hash_army_unavailable");
        Need(*input.selected_siege_fnv1a_u32 == Hash(*input.selected_siege_full_id_u32),
             "selected_full_key_hash_mismatch");
        Need(input.arrg_append_inputs_ready && input.ordered_arrg_full_ids_u32,
             "ordered_arrg_append_inputs_unavailable");
        bool moved = false;
        const auto selected = trial.Insert(Empty(*input.selected_siege_fnv1a_u32, *input.selected_siege_full_id_u32), moved, true);
        Append(trial.Group(selected.slot), input);
        request.status = "available";
        request.branch = selected.branch;
        request.returned_physical_slot_i64 = selected.slot;
        request.inserted = selected.inserted;
      }
      previous_index = input.native_occurrence_index;
      state = std::move(trial);
      ++result.applied_request_count;
    } catch (const std::runtime_error &error) {
      request.status = "unavailable";
      request.unavailable_reason = error.what();
      result.unavailable_reason = error.what();
    }
    result.requests.push_back(std::move(request));
    if (!result.unavailable_reason.empty()) break;
  }
  result.ready = result.unavailable_reason.empty();
  result.projected_header = state.header;
  for (const auto &[slot, control] : state.controls)
    result.projected_physical_controls.push_back({slot, control, {}});
  result.unspecified_controls_zero = state.implicit_zero;
  if (state.implicit_zero) result.zero_control_extent_end_i64 = state.zero_end;
  for (auto &[slot, group] : state.groups) {
    group.value.native_index = static_cast<std::int32_t>(result.projected_groups.size());
    result.projected_groups.push_back(std::move(group));
  }
  result.projected_physical_group_order_ready = state.order_ready;
  result.growth = std::move(state.growth);
  result.growth_release_inputs = std::move(state.releases);
  return result;
}

} // namespace xar::ck3_12004
