#include "xar_bridge/ck3_12003_current_assault_removal_reference.hpp"

#include <algorithm>
#include <utility>

namespace xar::ck3_12003 {
namespace {
using namespace daily_assault_table_detail;

game::ArmyCurrentAssaultRemovalTargetV1 Target(
    const CurrentDailyAssaultTableBindings12003 &b, const void *manager,
    std::int32_t index, std::uint32_t argument) {
  game::ArmyCurrentAssaultRemovalTargetV1 out{};
  out.native_index = index; out.argument_full_id_u32 = argument;
  const auto helper = Resolve(b, b.army_registry_slot, b.army_fallback_slot, argument, 0x10);
  out.helper_resolution = helper.observation;
  if (!helper.object || !out.helper_resolution.selected_full_id_u32) {
    out.unavailable_reason = "current_removal_helper_resolution_unavailable"; Finish(out, false); return out;
  }
  out.selected_bucket_index_u32 = *out.helper_resolution.selected_full_id_u32 % 30U;
  if (!manager) {
    out.unavailable_reason = "current_removal_manager_unavailable"; Finish(out, false); return out;
  }
  const auto offset = 0x198U + 0x18U * static_cast<std::size_t>(*out.selected_bucket_index_u32);
  const void *header = At(manager, offset);
  out.bucket_count_raw_i32 = Read<std::int32_t>(b, header, 0xC);
  if (!out.bucket_count_raw_i32) {
    out.unavailable_reason = "current_removal_bucket_count_unavailable"; Finish(out, false); return out;
  }
  if (*out.bucket_count_raw_i32 <= 0) {
    out.bucket_rows.emplace(); Finish(out, true); return out;
  }
  const auto data = Read<const void *>(b, header);
  if (data) out.bucket_data_present = *data != nullptr;
  if (!data || !*data) {
    out.unavailable_reason = "current_removal_bucket_data_unavailable"; Finish(out, false); return out;
  }
  out.bucket_rows.emplace();
  bool complete = true;
  for (std::int32_t i = 0; i < *out.bucket_count_raw_i32; ++i) {
    game::ArmyCurrentAssaultRemovalBucketRowV1 row{};
    row.native_index = i;
    const auto pointer = Read<const void *>(b, *data, static_cast<std::size_t>(i) * sizeof(const void *));
    if (pointer) {
      row.pointer_identity = Identity(*pointer);
      row.native_same_helper_pointer = *pointer == helper.object;
    } else {
      complete = false; Reason(out.unavailable_reason, "current_removal_bucket_pointer_unavailable");
    }
    out.bucket_rows->push_back(std::move(row));
  }
  Finish(out, complete); return out;
}
} // namespace

game::ArmyCurrentAssaultRemovalReferenceInputsV1 ReadCurrentAssaultRemovalReferenceInputs12003(
    const CurrentAssaultRemovalReferenceBindings12003 &bindings,
    const game::ArmyDailyQueueInputsV1 *queue,
    const game::ArmyFirstRemovalCleanupInputsV1 *global,
    const game::ArmyCurrentDailyAssaultTableV1 *table) noexcept {
  game::ArmyCurrentAssaultRemovalReferenceInputsV1 out{};
  for (const auto *offset : {"50", "68", "80", "98", "c8", "158"})
    out.manager_id_lists.push_back({offset, std::nullopt});
  if (!bindings.enabled) { out.unavailable_reason = "current_assault_removal_reference_unbound"; return out; }
  const auto &b = bindings.lookup;
  if (global) { out.manager_id_lists = global->id_lists; out.records_b0 = global->records_b0; }
  if (queue) out.observed_pending_ids_i32 = queue->manager_army_id_list_2a5a8;
  const auto state = Read<const void *>(b, b.game_state_slot);
  const auto data = state && *state ? Read<const void *>(b, *state, 0xA0) : std::nullopt;
  const void *manager = data && *data ? At(*data, 0x2A540) : nullptr;
  if (manager) out.manager_identity = Identity(manager);
  else Reason(out.unavailable_reason, "current_removal_manager_unavailable");

  const auto append = [&](game::ArmyCurrentAssaultRemovalReferenceV1 row,
                          const game::ArmyDailyQueueInitialResolutionRowV1 *pending) {
    row.native_index = static_cast<std::int32_t>(out.reference_occurrences.size());
    const auto passed = Resolve(b, b.army_registry_slot, b.army_fallback_slot, row.raw_full_id_u32, 0x10);
    row.resolution = passed.observation;
    if (row.reference_scope == "current_pending") {
      // The qualified queue capture already read this actual scalar.
      if (pending) row.army_magic_14_raw_u32 = pending->army_magic_14_raw;
      row.identity_scalar_basis = "copied_current_pending_magic";
    } else {
      row.army_magic_14_raw_u32 = Read<std::uint32_t>(b, passed.object, 0x14);
      row.identity_scalar_basis = "native_current_group_magic";
    }
    if (row.army_magic_14_raw_u32 && row.resolution.selected_full_id_u32)
      row.native_army_identity_valid = *row.army_magic_14_raw_u32 == 0x41726D79U &&
                                       *row.resolution.selected_full_id_u32 != 0xFFFFFFFFU;
    if (!row.resolution.ready) Reason(row.unavailable_reason, "current_removal_passed_resolution_unavailable");
    if (!row.army_magic_14_raw_u32) Reason(row.unavailable_reason, "current_removal_passed_magic_unavailable");
    if (row.native_army_identity_valid == true) {
      const auto argument = *row.resolution.selected_full_id_u32;
      const auto found = std::find_if(out.cleanup_targets.begin(), out.cleanup_targets.end(),
          [&](const auto &target) { return target.argument_full_id_u32 == argument; });
      if (found != out.cleanup_targets.end()) row.cleanup_target_index = found->native_index;
      else {
        row.cleanup_target_index = static_cast<std::int32_t>(out.cleanup_targets.size());
        out.cleanup_targets.push_back(Target(b, manager, *row.cleanup_target_index, argument));
      }
    }
    Finish(row, row.resolution.ready && row.native_army_identity_valid.has_value());
    if (!row.ready) Reason(out.unavailable_reason, row.unavailable_reason);
    out.reference_occurrences.push_back(std::move(row));
  };
  if (out.observed_pending_ids_i32) {
    for (std::size_t index = 0; index < out.observed_pending_ids_i32->size(); ++index) {
      game::ArmyCurrentAssaultRemovalReferenceV1 row{};
      row.reference_scope = "current_pending"; row.pending_native_index = static_cast<std::int32_t>(index);
      row.raw_full_id_u32 = static_cast<std::uint32_t>((*out.observed_pending_ids_i32)[index]);
      const auto *pending = queue && queue->initial_army_resolution_rows &&
              index < queue->initial_army_resolution_rows->size()
          ? &(*queue->initial_army_resolution_rows)[index] : nullptr;
      append(std::move(row), pending);
    }
  } else Reason(out.unavailable_reason, "current_removal_pending_capture_unavailable");
  if (table) {
    for (const auto &group : table->groups) for (const auto &occurrence : group.armies.occurrences) {
      game::ArmyCurrentAssaultRemovalReferenceV1 row{};
      row.reference_scope = "current_group_army"; row.group_native_index = group.native_index;
      row.group_physical_slot_i64 = group.physical_slot_i64; row.group_army_native_index = occurrence.native_index;
      row.raw_full_id_u32 = occurrence.raw_full_id_u32;
      append(std::move(row), nullptr);
    }
  } else Reason(out.unavailable_reason, "current_removal_group_reference_capture_unavailable");
  bool complete = out.observed_pending_ids_i32.has_value() && table != nullptr;
  if (table) {
    complete &= table->physical_scan_ready;
    for (const auto &group : table->groups) complete &= group.armies.references_ready;
    if (!table->physical_scan_ready || std::any_of(table->groups.begin(), table->groups.end(),
            [](const auto &group) { return !group.armies.references_ready; }))
      Reason(out.unavailable_reason, "current_removal_group_reference_capture_incomplete");
  }
  for (const auto &row : out.reference_occurrences) complete &= row.ready;
  for (const auto &target : out.cleanup_targets) {
    complete &= target.ready;
    if (!target.ready) Reason(out.unavailable_reason, target.unavailable_reason);
  }
  // Global arrays are independent operands for the selected top-helper prefix.
  // Their absence never changes a known invalid reference predicate.
  if (!out.cleanup_targets.empty()) {
    complete &= out.records_b0.has_value();
    if (!out.records_b0) Reason(out.unavailable_reason, "current_removal_global_records_unavailable");
    for (const auto &list : out.manager_id_lists) {
      complete &= list.ordered_army_ids.has_value();
      if (!list.ordered_army_ids) Reason(out.unavailable_reason, "current_removal_global_id_list_unavailable");
    }
  }
  if (complete) out.unavailable_reason.clear();
  Finish(out, complete); return out;
}
} // namespace xar::ck3_12003
