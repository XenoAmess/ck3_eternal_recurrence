#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr char kDailyAssaultPreparationExecutableSha256[] =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
inline constexpr std::uint32_t kDailyAssaultPreparationCallsiteRva = 0x2A9A081;

enum class DailyAssaultPreparationStage12004 {
  current_query,
  pre_date_assault_call,
};

// Root supplies this alongside copied readonly values from the same entry.
// Matching it binds a source interface, not a claim of a live observation.
struct DailyAssaultPreparationBoundary12004 {
  std::string executable_sha256;
  DailyAssaultPreparationStage12004 stage = DailyAssaultPreparationStage12004::current_query;
  std::string frame_identity;
  std::optional<std::uint64_t> query_sequence;
  std::optional<std::int32_t> game_date_raw_i32, absolute_day_raw_i32;
  std::optional<std::uint8_t> calendar_flags_raw_u8;
  std::string primary_manager_identity;
  std::uint32_t callsite_rva = 0;
  std::optional<std::int32_t> native_occurrence_index;
  std::string original_roster_capture_identity;
  std::string selected_army_identity;
};

struct DailyAssaultPreparationAppendInput12004 {
  std::int32_t native_occurrence_index = 0;
  std::optional<std::uint32_t> requested_army_full_id_u32;
  std::optional<std::uint32_t> selected_siege_full_id_u32, selected_army_full_id_u32;
  std::optional<std::uint32_t> selected_siege_fnv1a_u32;
  bool army_append_input_ready = false;
  std::optional<bool> army_append;
  bool arrg_append_inputs_ready = false;
  std::optional<std::vector<std::uint32_t>> ordered_arrg_full_ids_u32;
};

struct DailyAssaultPreparationInput12004 {
  std::string source = "actual4_daily_assault_preparation_copied_readonly_input_binding";
  DailyAssaultPreparationBoundary12004 boundary{};
  bool boundary_binding_ready = false;
  std::string unavailable_reason;
  game::ArmyDailyAssaultRawReferencesV1 original_roster{}, removal_queue{};
  std::vector<game::ArmyDailyAssaultRosterAdmissionOccurrenceV1> occurrence_inputs;
  std::vector<DailyAssaultPreparationAppendInput12004> ordered_append_inputs;
  bool ordered_append_inputs_ready = false;
  std::optional<game::ArmyCurrentDailyAssaultTableV1> current_group_records;
  bool current_group_frame_matches = false;
  bool current_group_records_ready = false;
  // Physical placement/growth, prefix evolution and later writers are separate.
  bool actual_callback_execution_observed = false;
  bool full_future_table_placement_ready = false;
  bool full_daily_assault_ready = false;
  bool full_monthly_execution_ready = false;
};

// No native calls, memory access or writes occur here. The existing collectors
// remain the only readers and must be called at Root's selected capture entry.
DailyAssaultPreparationInput12004 BindDailyAssaultPreparationInputs12004(
    const DailyAssaultPreparationBoundary12004 &boundary,
    const game::ArmyCurrentDailyAssaultRosterAdmissionV1 &admission,
    const game::ArmyCurrentDailyAssaultTableV1 *current_group_records = nullptr,
    const std::string &group_records_frame_identity = {});

} // namespace xar::ck3_12004
