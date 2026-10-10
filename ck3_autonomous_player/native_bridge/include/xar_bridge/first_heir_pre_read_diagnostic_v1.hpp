#pragma once
#include "xar_bridge/game_contract.hpp"
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge_detail {

// The original ordered PRE-read conjunction, with its first failure named.
// Read is called exactly once only when the prior owned snapshot exists.
template<class Read>
std::string_view FirstHeirPreReadFailureV1(
    const std::optional<game::Snapshot> &previous, game::Snapshot &before,
    Read &&read, bool &read_completed) {
  read_completed = false;
  if (!previous.has_value()) return "previous_snapshot_missing";
  read_completed = read(before);
  if (!read_completed) return "snapshot_read_failed";
  if (before != *previous) return "snapshot_not_equal";
  if (!before.paused) return "not_paused";
  if (!before.map_ready) return "map_not_ready";
  if (!before.has_played_character) return "played_character_missing";
  if (!before.played_character_alive) return "played_character_not_alive";
  return {};
}

inline std::string FirstHeirSnapshotDifferenceNamesV1(
    const game::Snapshot &before, const game::Snapshot &previous) {
  std::string out;
  const auto add = [&](std::string_view name, bool equal) {
    if (equal) return;
    if (!out.empty()) out += ',';
    out += name;
  };
  add("date_raw", before.date_raw == previous.date_raw);
  add("speed", before.speed == previous.speed);
  add("paused", before.paused == previous.paused);
  add("player_id", before.player_id == previous.player_id);
  add("map_ready", before.map_ready == previous.map_ready);
  add("has_played_character", before.has_played_character == previous.has_played_character);
  add("played_character_id", before.played_character_id == previous.played_character_id);
  add("played_character_alive", before.played_character_alive == previous.played_character_alive);
  add("played_character_stress_points", before.played_character_stress_points == previous.played_character_stress_points);
  add("played_character_event_trait_membership", before.played_character_event_trait_membership == previous.played_character_event_trait_membership);
  add("played_character_gold", before.played_character_gold == previous.played_character_gold);
  add("played_character_prestige", before.played_character_prestige == previous.played_character_prestige);
  add("played_character_piety", before.played_character_piety == previous.played_character_piety);
  add("played_character_betrothed_id", before.played_character_betrothed_id == previous.played_character_betrothed_id);
  add("played_character_primary_spouse_id", before.played_character_primary_spouse_id == previous.played_character_primary_spouse_id);
  add("played_character_spouse_ids", before.played_character_spouse_ids == previous.played_character_spouse_ids);
  add("has_active_event", before.has_active_event == previous.has_active_event);
  add("active_event_instance_id", before.active_event_instance_id == previous.active_event_instance_id);
  add("active_event_option_count", before.active_event_option_count == previous.active_event_option_count);
  add("has_pending_character_interaction", before.has_pending_character_interaction == previous.has_pending_character_interaction);
  add("pending_character_interaction_id", before.pending_character_interaction_id == previous.pending_character_interaction_id);
  add("pending_sender_character_id", before.pending_sender_character_id == previous.pending_sender_character_id);
  add("pending_auto_accept_notification", before.pending_auto_accept_notification == previous.pending_auto_accept_notification);
  add("active_wars", before.active_wars == previous.active_wars);
  add("player_armies", before.player_armies == previous.player_armies);
  add("has_one_life_settlement", before.has_one_life_settlement == previous.has_one_life_settlement);
  add("one_life_settlement", before.one_life_settlement == previous.one_life_settlement);
  return out;
}

// Only owned numeric scalars, presence and collection sizes are rendered.
// Complex field contents remain private; the difference labels still cover
// every member of Snapshot's existing default equality.
inline std::string FirstHeirSnapshotDiagnosticScalarsV1(const game::Snapshot &s) {
  std::string out;
  const auto add = [&](std::string_view name, auto value) {
    if (!out.empty()) out += ',';
    out += name;
    out += ':';
    out += std::to_string(value);
  };
  add("date_raw", s.date_raw);
  add("speed", s.speed);
  add("paused", s.paused);
  add("player_id", s.player_id);
  add("map_ready", s.map_ready);
  add("has_played_character", s.has_played_character);
  add("played_character_id", s.played_character_id);
  add("played_character_alive", s.played_character_alive);
  add("played_character_stress_points", s.played_character_stress_points);
  add("played_character_event_trait_membership_present", s.played_character_event_trait_membership.has_value());
  add("played_character_gold_raw", s.played_character_gold.raw);
  add("played_character_gold_scale", s.played_character_gold.scale);
  add("played_character_prestige_raw", s.played_character_prestige.raw);
  add("played_character_prestige_scale", s.played_character_prestige.scale);
  add("played_character_piety_raw", s.played_character_piety.raw);
  add("played_character_piety_scale", s.played_character_piety.scale);
  add("played_character_betrothed_id", s.played_character_betrothed_id);
  add("played_character_primary_spouse_id", s.played_character_primary_spouse_id);
  add("played_character_spouse_ids_count", s.played_character_spouse_ids.size());
  add("has_active_event", s.has_active_event);
  add("active_event_instance_id", s.active_event_instance_id);
  add("active_event_option_count", s.active_event_option_count);
  add("has_pending_character_interaction", s.has_pending_character_interaction);
  add("pending_character_interaction_id", s.pending_character_interaction_id);
  add("pending_sender_character_id", s.pending_sender_character_id);
  add("pending_auto_accept_notification", s.pending_auto_accept_notification);
  add("active_wars_count", s.active_wars.size());
  add("player_armies_count", s.player_armies.size());
  add("has_one_life_settlement", s.has_one_life_settlement);
  return out;
}

inline std::string FirstHeirPreReadErrorV1(
    std::string_view failure, bool read_completed,
    const std::optional<game::Snapshot> &previous, const game::Snapshot &before) {
  std::string error = "current first-heir relationship frame changed; pre_read_guard=";
  error += failure;
  error += "; snapshot_read_completed=";
  error += read_completed ? "true" : "false";
  if (failure == "snapshot_not_equal" && read_completed && previous.has_value()) {
    error += "; differing_fields=";
    error += FirstHeirSnapshotDifferenceNamesV1(before, *previous);
  }
  error += "; cached=";
  error += previous.has_value() ? FirstHeirSnapshotDiagnosticScalarsV1(*previous) : "unknown";
  error += "; observed=";
  error += read_completed ? FirstHeirSnapshotDiagnosticScalarsV1(before) : "unknown";
  error += "; complex_field_values=presence_or_count_only";
  return error;
}
} // namespace xar::bridge_detail
