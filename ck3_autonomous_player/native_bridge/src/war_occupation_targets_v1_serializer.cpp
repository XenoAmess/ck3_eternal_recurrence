#include "xar_bridge/war_occupation_targets_v1_serializer.hpp"

#include "xar_bridge/ck3_12003.hpp"

namespace xar::game {
namespace {

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      out += '\\';
      out += static_cast<char>(byte);
    } else if (byte < 0x20) {
      out += "\\u00";
      out += hex[byte >> 4];
      out += hex[byte & 15];
    } else {
      out += static_cast<char>(byte);
    }
  }
  return out + '"';
}

std::string NullableId(std::int32_t value) {
  return value < 0 ? "null" : std::to_string(value);
}

const char *Bool(bool value) noexcept { return value ? "true" : "false"; }

std::string ObservableBool(bool observable, bool value) {
  return observable ? Bool(value) : "null";
}

std::string ObservableInt(bool observable, std::int32_t value) {
  return observable ? std::to_string(value) : std::string("null");
}

std::string FixedPoint(std::int64_t raw) {
  return "{\"raw\":" + std::to_string(raw) + ",\"scale\":100000}";
}

std::string ActiveSiege(const WarOccupationTargetRowV1 &row) {
  if (!row.siege_observable || !row.has_active_siege) return "null";
  const auto &siege = row.active_siege;
  const auto remaining = siege.total_work_raw >= siege.current_work_raw
      ? siege.total_work_raw - siege.current_work_raw : 0;
  return "{\"siege_id\":" + NullableId(siege.siege_id) +
      ",\"besieging_army_id\":" + NullableId(siege.besieging_army_id) +
      ",\"player_army_besieging\":" + Bool(siege.player_army_besieging) +
      ",\"progress_fraction\":" + FixedPoint(siege.progress_fraction_raw) +
      ",\"current_work\":" + FixedPoint(siege.current_work_raw) +
      ",\"total_work\":" + FixedPoint(siege.total_work_raw) +
      ",\"remaining_work\":" + FixedPoint(remaining) +
      ",\"days_left\":" + ObservableInt(
          siege.days_left_observable, siege.days_left) +
      ",\"ordinary_daily_progress\":" +
      (siege.ordinary_daily_progress_observable
          ? FixedPoint(siege.ordinary_daily_progress_raw) : std::string("null")) +
      ",\"eligible_regiment_siege_work\":" +
      (siege.eligible_regiment_siege_work_observable
          ? FixedPoint(siege.eligible_regiment_siege_work_raw) : std::string("null")) +
      ",\"highest_eligible_siege_tier\":" + ObservableInt(
          siege.highest_eligible_siege_tier_observable,
          siege.highest_eligible_siege_tier) +
      ",\"current_phase_length\":" +
      (siege.current_phase_length_observable
          ? FixedPoint(siege.current_phase_length_raw) : std::string("null")) +
      ",\"prepared_phase_length\":" +
      (siege.prepared_phase_length_observable
          ? FixedPoint(siege.prepared_phase_length_raw) : std::string("null")) +
      ",\"phase_counter\":" + ObservableInt(
          siege.phase_counter_observable, siege.phase_counter) +
      ",\"can_advance\":" + ObservableBool(
          siege.can_advance_observable, siege.can_advance) +
      ",\"phase_event_state\":{\"breach_level\":" + ObservableInt(
          siege.phase_event_breach_level_observable, siege.phase_event_breach_level) +
      ",\"starvation_level\":" + ObservableInt(
          siege.phase_event_starvation_level_observable, siege.phase_event_starvation_level) +
      ",\"disease_level\":" + ObservableInt(
          siege.phase_event_disease_level_observable, siege.phase_event_disease_level) +
      ",\"desertion_count\":" + ObservableInt(
          siege.phase_event_desertion_count_observable, siege.phase_event_desertion_count) +
      ",\"stalemate_count\":" + ObservableInt(
          siege.phase_event_stalemate_count_observable, siege.phase_event_stalemate_count) +
      "},\"prepared_selected_phase_event_enum\":" + ObservableInt(
          siege.prepared_selected_phase_event_enum_observable,
          siege.prepared_selected_phase_event_enum) +
      ",\"assault_observable\":" + Bool(siege.assault_observable) +
      ",\"breach_level\":" + ObservableInt(
          siege.assault_observable, siege.breach_level) +
      ",\"walls_breached\":" + ObservableBool(
          siege.assault_observable, siege.breach_level > 0) +
      ",\"assault_in_progress\":" + ObservableBool(
          siege.assault_observable, siege.assault_in_progress) +
      ",\"can_start_assault\":" + ObservableBool(
          siege.assault_observable, siege.can_start_assault) +
      ",\"can_stop_assault\":" + ObservableBool(
          siege.assault_observable, siege.can_stop_assault) +
      ",\"assault_daily_progress\":" +
      (siege.assault_observable ? FixedPoint(siege.assault_daily_progress_raw)
                               : std::string("null")) +
      ",\"assault_daily_casualties\":" + ObservableInt(
          siege.assault_observable, siege.assault_daily_casualties) + '}';
}

} // namespace

std::string SerializeWarOccupationTargetsV1(
    const WarOccupationTargetsV1 &observation,
    ReadWarOccupationTargetsV1Result read_result, std::uint64_t query_sequence,
    std::uint64_t snapshot_revision, std::string_view step) {
  const bool available =
      read_result == ReadWarOccupationTargetsV1Result::available &&
      observation.available && observation.collection_complete;
  const std::string_view status = available ? "available" : "unavailable";
  const auto reason = available ? std::string("null") : Quote(
      observation.unavailable_reason.empty()
          ? std::string_view("native_reader_unavailable")
          : observation.unavailable_reason);
  std::string out = "{\"step\":" + Quote(step) +
      ",\"accepted\":true,\"status\":" + Quote(status) +
      ",\"read_only\":true,\"query_sequence\":" +
      std::to_string(query_sequence) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(observation.date_raw) +
      ",\"backend_id\":\"native-headless\",\"war_occupation_targets_v1\":{"
      "\"schema\":\"xar.ck3.war-occupation-targets.v1\",\"schema_version\":1,"
      "\"game_version\":\"1.20.0.3\",\"executable_sha256\":" +
      Quote(ck3_12003::kExecutableSha256) +
      ",\"status\":" + Quote(status) +
      ",\"snapshot_revision\":" + std::to_string(snapshot_revision) +
      ",\"date_raw\":" + std::to_string(observation.date_raw) +
      ",\"actor_character_id\":" + NullableId(observation.actor_character_id) +
      ",\"war_id\":" + NullableId(observation.war_id) +
      ",\"player_side\":" + Quote(observation.player_side) +
      ",\"primary_attacker_character_id\":" +
      NullableId(observation.primary_attacker_character_id) +
      ",\"primary_defender_character_id\":" +
      NullableId(observation.primary_defender_character_id) +
      ",\"available\":" + Bool(available) +
      ",\"unavailable_reason\":" + reason +
      ",\"collection_complete\":" + Bool(
          available && observation.collection_complete) +
      ",\"side_counts\":[";
  bool first = true;
  for (const auto &side : observation.side_counts) {
    if (!first) out += ',';
    first = false;
    out += "{\"territory_side\":" + Quote(side.territory_side) +
        ",\"eligible\":" + std::to_string(side.eligible) +
        ",\"occupied\":" + std::to_string(side.occupied) +
        ",\"native_candidate_count\":" +
        std::to_string(side.native_candidate_count) +
        ",\"collection_complete\":" + Bool(side.collection_complete) + '}';
  }
  out += "],\"rows\":[";
  first = true;
  for (const auto &row : observation.rows) {
    if (!first) out += ',';
    first = false;
    out += "{\"holding_title_id\":" + NullableId(row.holding_title_id) +
        ",\"county_title_id\":" + NullableId(row.county_title_id) +
        ",\"province_id\":" + NullableId(row.province_id) +
        ",\"legal_holder_character_id\":" +
        NullableId(row.legal_holder_character_id) +
        ",\"territory_side\":" + Quote(row.territory_side) +
        ",\"occupation_observable\":" + Bool(row.occupation_observable) +
        ",\"is_occupied\":" + ObservableBool(
            row.occupation_observable, row.is_occupied) +
        ",\"occupying_character_id\":" +
        (row.occupation_observable && row.is_occupied
            ? NullableId(row.occupying_character_id) : std::string("null")) +
        ",\"occupier_side\":" + Quote(row.occupier_side) +
        ",\"counted_occupied_by_opposing_side\":" + ObservableBool(
            row.occupation_observable,
            row.counted_occupied_by_opposing_side) +
        ",\"fort_level\":" +
        (row.fort_level_observable
            ? std::to_string(row.fort_level) : std::string("null")) +
        ",\"garrison_size\":" +
        (row.garrison_size_observable
            ? std::to_string(row.garrison_size) : std::string("null")) +
        ",\"besieging_strength\":" + ObservableInt(
            row.besieging_strength_observable, row.besieging_strength) +
        ",\"siege_observable\":" + Bool(row.siege_observable) +
        ",\"active_siege\":" + ActiveSiege(row) + '}';
  }
  return out + "]}}";
}

} // namespace xar::game
