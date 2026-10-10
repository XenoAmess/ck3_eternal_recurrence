#pragma once
#include "xar_bridge/game_contract.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_11906 {
// Failure-only evidence. Never used as owner/frame/action qualification.
struct KeyedQueryCompletionDiagnosticsV1 {
  bool present=false, snapshot_read_succeeded=false;
  std::optional<bool> snapshot_equal, state_revision_equal;
  std::uint64_t expected_state_revision=0, post_guard_state_revision=0;
  std::optional<std::uint64_t> compared_state_revision;
  std::string first_failed_predicate;
  std::vector<std::string> changed_snapshot_fields;
};
inline KeyedQueryCompletionDiagnosticsV1 CaptureKeyedQueryCompletionFailureV1(
    bool read_ok, bool snapshot_equal, bool revision_equal,
    const game::Snapshot &expected, const game::Snapshot &completion,
    std::uint64_t expected_revision, std::uint64_t compared_revision,
    std::uint64_t post_guard_revision) {
  KeyedQueryCompletionDiagnosticsV1 out{};
  if(read_ok&&snapshot_equal&&revision_equal)return out;
  out.present=true;out.snapshot_read_succeeded=read_ok;
  out.expected_state_revision=expected_revision;out.post_guard_state_revision=post_guard_revision;
  if(read_ok)out.snapshot_equal=snapshot_equal;
  if(read_ok&&snapshot_equal){out.state_revision_equal=revision_equal;out.compared_state_revision=compared_revision;}
  out.first_failed_predicate=!read_ok?"snapshot_read":!snapshot_equal?"snapshot_equal":"state_revision_equal";
  if(read_ok&&!snapshot_equal){
    const auto changed=[&](const char *name,const auto &before,const auto &after){
      if(before!=after)out.changed_snapshot_fields.emplace_back(name);
    };
    changed("date_raw",expected.date_raw,completion.date_raw);
    changed("speed",expected.speed,completion.speed);
    changed("paused",expected.paused,completion.paused);
    changed("player_id",expected.player_id,completion.player_id);
    changed("map_ready",expected.map_ready,completion.map_ready);
    changed("has_played_character",expected.has_played_character,completion.has_played_character);
    changed("played_character_id",expected.played_character_id,completion.played_character_id);
    changed("played_character_alive",expected.played_character_alive,completion.played_character_alive);
    changed("played_character_stress_points",expected.played_character_stress_points,completion.played_character_stress_points);
    changed("played_character_event_trait_membership",expected.played_character_event_trait_membership,completion.played_character_event_trait_membership);
    changed("played_character_gold",expected.played_character_gold,completion.played_character_gold);
    changed("played_character_prestige",expected.played_character_prestige,completion.played_character_prestige);
    changed("played_character_piety",expected.played_character_piety,completion.played_character_piety);
    changed("played_character_betrothed_id",expected.played_character_betrothed_id,completion.played_character_betrothed_id);
    changed("played_character_primary_spouse_id",expected.played_character_primary_spouse_id,completion.played_character_primary_spouse_id);
    changed("played_character_spouse_ids",expected.played_character_spouse_ids,completion.played_character_spouse_ids);
    changed("has_active_event",expected.has_active_event,completion.has_active_event);
    changed("active_event_instance_id",expected.active_event_instance_id,completion.active_event_instance_id);
    changed("active_event_option_count",expected.active_event_option_count,completion.active_event_option_count);
    changed("has_pending_character_interaction",expected.has_pending_character_interaction,completion.has_pending_character_interaction);
    changed("pending_character_interaction_id",expected.pending_character_interaction_id,completion.pending_character_interaction_id);
    changed("pending_sender_character_id",expected.pending_sender_character_id,completion.pending_sender_character_id);
    changed("pending_auto_accept_notification",expected.pending_auto_accept_notification,completion.pending_auto_accept_notification);
    changed("active_wars",expected.active_wars,completion.active_wars);
    changed("player_armies",expected.player_armies,completion.player_armies);
    changed("has_one_life_settlement",expected.has_one_life_settlement,completion.has_one_life_settlement);
    changed("one_life_settlement",expected.one_life_settlement,completion.one_life_settlement);
  }
  return out;
}
} // namespace xar::ck3_11906
