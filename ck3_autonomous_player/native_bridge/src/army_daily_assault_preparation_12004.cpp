#include "xar_bridge/army_daily_assault_preparation_12004.hpp"
#include "xar_bridge/ck3_12003_daily_assault_roster_admission.hpp"

#include <cstddef>
#include <utility>

namespace xar::ck3_12004 {

DailyAssaultPreparationInput12004 BindDailyAssaultPreparationInputs12004(
    const DailyAssaultPreparationBoundary12004 &boundary,
    const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &admission,
    const game::ArmyCurrentDailyAssaultTableV1 *current_group_records,
    const std::string &group_records_frame_identity) {
  DailyAssaultPreparationInput12004 out{};
  out.boundary = boundary;
  out.original_roster = admission.original_roster;
  out.removal_queue = admission.removal_queue;
  if (current_group_records) {
    out.current_group_records = *current_group_records;
    out.current_group_frame_matches = !boundary.frame_identity.empty() &&
        group_records_frame_identity == boundary.frame_identity &&
        current_group_records->manager_identity == boundary.primary_manager_identity;
    out.current_group_records_ready = out.current_group_frame_matches &&
        current_group_records->raw_groups_ready;
  }
  const auto fail = [&](const char *reason) {
    out.unavailable_reason = reason;
    return out;
  };
  if (boundary.executable_sha256 != kDailyAssaultPreparationExecutableSha256)
    return fail("preparation_exact4_input_identity_unbound");
  if (boundary.frame_identity.empty() || !boundary.query_sequence ||
      !boundary.game_date_raw_i32 || !boundary.absolute_day_raw_i32 ||
      !boundary.calendar_flags_raw_u8)
    return fail("preparation_frame_inputs_unavailable");
  if (boundary.primary_manager_identity.empty() ||
      admission.manager_identity != boundary.primary_manager_identity)
    return fail("preparation_primary_manager_input_mismatch");
  const auto &roster = admission.original_roster;
  if (!roster.references_ready || !roster.count_raw_i32 || *roster.count_raw_i32 < 0 ||
      roster.occurrences.size() != static_cast<std::size_t>(*roster.count_raw_i32) ||
      admission.occurrences.size() != roster.occurrences.size())
    return fail("preparation_original_roster_input_incomplete");
  for (std::size_t i = 0; i < roster.occurrences.size(); ++i) {
    const auto native_index = static_cast<std::int32_t>(i);
    if (roster.occurrences[i].native_index != native_index ||
        admission.occurrences[i].native_index != native_index ||
        !roster.occurrences[i].raw_full_id_u32 ||
        admission.occurrences[i].raw_full_id_u32 != roster.occurrences[i].raw_full_id_u32)
      return fail("preparation_raw_occurrence_input_mismatch");
  }
  if (boundary.stage == DailyAssaultPreparationStage12004::pre_date_assault_call) {
    if (boundary.callsite_rva != kDailyAssaultPreparationCallsiteRva ||
        !boundary.native_occurrence_index || *boundary.native_occurrence_index < 0 ||
        static_cast<std::size_t>(*boundary.native_occurrence_index) >= roster.occurrences.size())
      return fail("preparation_actual_call_boundary_input_unavailable");
    if (boundary.original_roster_capture_identity.empty() ||
        roster.data_identity != boundary.original_roster_capture_identity)
      return fail("preparation_original_roster_capture_input_mismatch");
    const auto &row = admission.occurrences[static_cast<std::size_t>(*boundary.native_occurrence_index)];
    if (boundary.selected_army_identity.empty() ||
        row.original_army_resolution.object_identity != boundary.selected_army_identity)
      return fail("preparation_selected_rsi_input_mismatch");
    out.occurrence_inputs.push_back(row);
  } else if (boundary.stage == DailyAssaultPreparationStage12004::current_query) {
    out.occurrence_inputs = admission.occurrences;
  } else {
    return fail("preparation_input_stage_unbound");
  }
  out.boundary_binding_ready = true;
  out.ordered_append_inputs_ready = true;
  for (const auto &row : out.occurrence_inputs) {
    DailyAssaultPreparationAppendInput12004 append{};
    append.native_occurrence_index = row.native_index;
    append.requested_army_full_id_u32 = row.raw_full_id_u32;
    append.army_append_input_ready = row.army_append_ready && row.army_append.has_value();
    append.army_append = row.army_append;
    append.arrg_append_inputs_ready = row.arrg_append_ready && row.arrg_append_full_ids_u32.has_value();
    append.ordered_arrg_full_ids_u32 = row.arrg_append_full_ids_u32;
    if (row.army_append == true) {
      append.selected_siege_full_id_u32 = row.army_append_siege_full_id_u32;
      append.selected_army_full_id_u32 = row.army_append_full_id_u32;
      append.army_append_input_ready = append.army_append_input_ready &&
          append.selected_siege_full_id_u32.has_value() && append.selected_army_full_id_u32.has_value();
      if (append.selected_siege_full_id_u32)
        append.selected_siege_fnv1a_u32 = ck3_12003::daily_assault_roster_detail::Hash(
            *append.selected_siege_full_id_u32);
    }
    if (!append.army_append_input_ready || !append.arrg_append_inputs_ready)
      out.ordered_append_inputs_ready = false;
    out.ordered_append_inputs.push_back(std::move(append));
  }
  if (!out.ordered_append_inputs_ready)
    out.unavailable_reason = "preparation_conditional_append_inputs_incomplete";
  return out;
}

} // namespace xar::ck3_12004
