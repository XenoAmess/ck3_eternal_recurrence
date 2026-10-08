#pragma once

#include <cstdint>
#include <string_view>
#include <vector>

#include "xar_bridge/siege_membership_v1.hpp"
#include "xar_bridge/province_besieging_army_selection_v1.hpp"

namespace xar::game {

inline constexpr std::string_view kWarOccupationTargetsV1Capability =
    "game.command.query-war-occupation-targets-v1-N";

struct WarOccupationActiveSiegeV1 {
  std::int32_t siege_id = -1;
  std::int32_t besieging_army_id = -1;
  bool player_army_besieging = false;
  std::int64_t progress_fraction_raw = 0;
  std::int64_t current_work_raw = 0;
  std::int64_t total_work_raw = 0;
  bool days_left_observable = false;
  std::int32_t days_left = 0;
  bool ordinary_daily_progress_observable = false;
  std::int64_t ordinary_daily_progress_raw = 0;
  // Independent current native eligible-regiment inputs, before modifiers.
  bool eligible_regiment_siege_work_observable = false;
  std::int64_t eligible_regiment_siege_work_raw = 0;
  bool highest_eligible_siege_tier_observable = false;
  std::int32_t highest_eligible_siege_tier = 0;
  bool province_unit_occurrences_observable = false;
  std::vector<SiegeProvinceUnitOccurrenceV1> province_unit_occurrences;
  // Fresh getter output and the last prepared cache are separate observations.
  bool current_phase_length_observable = false;
  std::int64_t current_phase_length_raw = 0;
  bool prepared_phase_length_observable = false;
  std::int64_t prepared_phase_length_raw = 0;
  bool phase_counter_observable = false;
  std::int32_t phase_counter = 0;
  bool can_advance_observable = false;
  bool can_advance = false;
  bool phase_event_breach_level_observable = false;
  std::int32_t phase_event_breach_level = 0;
  bool phase_event_starvation_level_observable = false;
  std::int32_t phase_event_starvation_level = 0;
  bool phase_event_disease_level_observable = false;
  std::int32_t phase_event_disease_level = 0;
  bool phase_event_desertion_count_observable = false;
  std::int32_t phase_event_desertion_count = 0;
  bool phase_event_stalemate_count_observable = false;
  std::int32_t phase_event_stalemate_count = 0;
  // Last prepare cache only; it is not a prediction of the next random draw.
  bool prepared_selected_phase_event_enum_observable = false;
  std::int32_t prepared_selected_phase_event_enum = 0;
  bool assault_observable = false;
  std::int32_t breach_level = 0;
  bool assault_in_progress = false;
  bool can_start_assault = false;
  bool can_stop_assault = false;
  std::int64_t assault_daily_progress_raw = 0;
  std::int32_t assault_daily_casualties = 0;
};

struct WarOccupationTargetRowV1 {
  // The native collector returns barony CLandedTitle pointers. This full title
  // ID is the holding identity; no invented second CHolding ID is published.
  std::int32_t holding_title_id = -1;
  // Optional resolved de-jure county full TitleID; -1 serializes as null.
  std::int32_t county_title_id = -1;
  std::int32_t province_id = -1;
  ProvinceBesiegingArmySelectionV1 current_besieging_army_selection;
  std::int32_t legal_holder_character_id = -1;
  std::string_view territory_side = "unavailable"; // attacker / defender
  bool occupation_observable = false;
  bool is_occupied = false;
  std::int32_t occupying_character_id = -1; // absent iff not occupied
  std::string_view occupier_side = "unavailable";
  // occupier_side: attacker / defender / outside_war / none / unavailable.
  bool counted_occupied_by_opposing_side = false;
  bool fort_level_observable = false;
  std::int32_t fort_level = 0;
  bool garrison_size_observable = false;
  std::int32_t garrison_size = 0;
  bool besieging_strength_observable = false;
  std::int32_t besieging_strength = 0;
  bool siege_observable = false;
  bool has_active_siege = false;
  WarOccupationActiveSiegeV1 active_siege;
};

struct WarOccupationSideCountsV1 {
  // This names the territory side, whose land is eligible. "occupied" counts
  // eligible land occupied by the opposing participant side in the real native
  // counter, rather than every geographically occupied province.
  std::string_view territory_side = "unavailable";
  std::int32_t eligible = 0;
  std::int32_t occupied = 0;
  std::int32_t native_candidate_count = 0;
  bool collection_complete = false;
};

struct WarOccupationTargetsSnapshotV1 {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t war_id = -1;
  std::string_view player_side = "unavailable";
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  bool collection_complete = false;
  std::vector<WarOccupationSideCountsV1> side_counts;
  std::vector<WarOccupationTargetRowV1> rows;
};

using WarOccupationTargetsV1 = WarOccupationTargetsSnapshotV1;
enum class ReadWarOccupationTargetsV1Result { unavailable, available };

} // namespace xar::game
