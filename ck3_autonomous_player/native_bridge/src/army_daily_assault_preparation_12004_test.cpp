#include "xar_bridge/army_daily_assault_preparation_12004.hpp"

#include <iostream>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace {
void Require(bool condition, const char *reason) {
  if (!condition) throw std::runtime_error(reason);
}
using namespace xar::ck3_12004;

DailyAssaultPreparationBoundary12004 Boundary() {
  DailyAssaultPreparationBoundary12004 out{};
  out.executable_sha256 = kDailyAssaultPreparationExecutableSha256;
  out.frame_identity = "synthetic-only-call-input-frame";
  out.query_sequence = 71;
  out.game_date_raw_i32 = 53289936;
  out.absolute_day_raw_i32 = 123;
  out.calendar_flags_raw_u8 = std::uint8_t{0}; // Daily assault remains present without bit2.
  out.primary_manager_identity = "synthetic-primary";
  return out;
}
xar::game::ArmyCurrentDailyAssaultRosterAdmissionV1 Admission() {
  xar::game::ArmyCurrentDailyAssaultRosterAdmissionV1 out{};
  out.manager_identity = "synthetic-primary";
  out.original_roster.references_ready = true;
  out.original_roster.count_raw_i32 = 3;
  out.original_roster.data_identity = "synthetic-original-roster";
  const std::vector<std::uint32_t> raw_ids{0xFE000011U, 0xFE000011U, 23U};
  for (std::int32_t i = 0; i != 3; ++i) {
    xar::game::ArmyDailyAssaultRawReferenceOccurrenceV1 raw{};
    raw.native_index = i; raw.raw_full_id_u32 = raw_ids[static_cast<std::size_t>(i)];
    out.original_roster.occurrences.push_back(raw);
    xar::game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 row{};
    row.native_index = i; row.raw_full_id_u32 = raw.raw_full_id_u32;
    row.original_army_resolution.object_identity = "synthetic-selected-army";
    row.army_append_ready = row.arrg_append_ready = true;
    row.army_append = i != 2;
    row.arrg_append_full_ids_u32 = i == 0
        ? std::vector<std::uint32_t>{42U, 42U, 0xFD000012U} : std::vector<std::uint32_t>{};
    if (i != 2) {
      row.army_append_siege_full_id_u32 = 0xFE000021U;
      row.army_append_full_id_u32 = 0xFE000011U;
    }
    if (i == 1) row.pending_selection.selected_control_raw_u8 = std::uint8_t{0xFF};
    out.occurrences.push_back(row);
  }
  return out;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2 && std::string_view(argv[1]) == "--preparation-stage-binding-only",
            "single new focus argv required");
    auto boundary = Boundary();
    const auto admission = Admission();
    xar::game::ArmyCurrentDailyAssaultTableV1 table{};
    table.raw_groups_ready = true;
    table.manager_identity = "synthetic-primary";
    table.header.occupied_count_raw_i32 = 1;
    xar::game::ArmyDailyAssaultGroupV1 group{};
    group.physical_slot_i64 = 7;
    group.siege_full_id_u32 = 0xFE000021U;
    table.groups.push_back(group);
    const auto original = admission;
    auto result = BindDailyAssaultPreparationInputs12004(boundary, admission, &table, boundary.frame_identity);
    Require(result.boundary_binding_ready && result.ordered_append_inputs_ready, "copied inputs unavailable");
    Require(result.ordered_append_inputs.size() == 3 &&
        result.ordered_append_inputs[0].requested_army_full_id_u32 == 0xFE000011U &&
        result.ordered_append_inputs[1].requested_army_full_id_u32 == 0xFE000011U,
        "native roster repetition lost");
    Require(result.ordered_append_inputs[0].ordered_arrg_full_ids_u32 ==
        std::vector<std::uint32_t>({42U, 42U, 0xFD000012U}), "ArRg order/repetition lost");
    Require(result.ordered_append_inputs[1].army_append == true &&
        result.ordered_append_inputs[1].ordered_arrg_full_ids_u32 == std::vector<std::uint32_t>{} &&
        result.current_group_records && result.current_group_records->groups.size() == 1,
        "pending FF became fake empty table");
    Require(result.ordered_append_inputs[2].army_append == false, "skip input lost");
    Require(!result.actual_callback_execution_observed && !result.full_future_table_placement_ready &&
        !result.full_daily_assault_ready && !result.full_monthly_execution_ready, "offline inputs granted execution credit");
    Require(result.current_group_records->groups[0].physical_slot_i64 == 7, "physical input reordered");
    Require(admission == original, "source input mutated");

    boundary.stage = DailyAssaultPreparationStage12004::pre_date_assault_call;
    boundary.callsite_rva = kDailyAssaultPreparationCallsiteRva;
    boundary.native_occurrence_index = 1;
    boundary.original_roster_capture_identity = "synthetic-original-roster";
    boundary.selected_army_identity = "synthetic-selected-army";
    result = BindDailyAssaultPreparationInputs12004(boundary, admission);
    Require(result.boundary_binding_ready && result.ordered_append_inputs.size() == 1 &&
        result.ordered_append_inputs[0].native_occurrence_index == 1 &&
        result.original_roster.occurrences.size() == 3 && !result.current_group_records &&
        !result.current_group_records_ready, "actual source interface/missing table binding lost");
    auto changed = boundary;
    changed.callsite_rva = 0x2A9A31C;
    Require(!BindDailyAssaultPreparationInputs12004(changed, admission).boundary_binding_ready,
            "later persistent call substituted for assault call");
    changed = boundary;
    changed.selected_army_identity = "different-selected-object";
    Require(!BindDailyAssaultPreparationInputs12004(changed, admission).boundary_binding_ready,
            "different selected RSI accepted");
    auto mismatch = admission;
    mismatch.occurrences[1].raw_full_id_u32 = 24;
    Require(!BindDailyAssaultPreparationInputs12004(boundary, mismatch).boundary_binding_ready,
            "different raw occurrence accepted");
    result = BindDailyAssaultPreparationInputs12004(boundary, admission, &table, "different-frame");
    Require(result.boundary_binding_ready && !result.current_group_records_ready &&
        result.current_group_records && result.current_group_records->groups.size() == 1,
        "wrong-frame table credited or erased");
    changed = boundary;
    changed.executable_sha256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6";
    Require(!BindDailyAssaultPreparationInputs12004(changed, admission).boundary_binding_ready,
            "old executable identity admitted");
    std::cout << "GREEN preparation-stage-binding-only: 7 input-boundary cases; new live evidence=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
