#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace xar::game {

struct ProjectedContactScopeRequest {
  std::int32_t subject_army_id = -1;
  std::int32_t target_province_id = -1;
  std::int32_t incoming_entry_province_id = -1;

  friend bool operator==(const ProjectedContactScopeRequest &,
                         const ProjectedContactScopeRequest &) = default;
};

enum class ProjectedContactScopeStatus {
  available,
  requires_paused,
  subject_army_not_found,
  subject_army_not_controllable,
  subject_in_combat,
  subject_not_contact_eligible,
  target_province_not_found,
  incoming_entry_province_not_found,
  invalid_entry_target_adjacency,
  relation_unavailable,
  state_changed,
  unavailable,
};

struct ProjectedContactScopeSnapshot {
  ProjectedContactScopeStatus status = ProjectedContactScopeStatus::unavailable;
  std::string scope_kind = "hypothetical_arrival_against_current_target_state";
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t subject_army_id = -1;
  std::int32_t subject_native_carmy_id = -1;
  std::int32_t subject_owner_character_id = -1;
  std::int32_t subject_current_province_id = -1;
  std::int32_t target_province_id = -1;
  std::int32_t incoming_entry_province_id = -1;
  std::vector<std::int32_t> observed_target_public_cunit_ids;
  std::vector<std::int32_t> observed_target_combat_ids;
  std::string transition_kind = "none";
  std::int32_t selected_current_combat_id = -1;
  std::int32_t selected_current_combat_array_index = -1;
  std::string projected_subject_side = "none";
  bool projected_initiator_is_defender_observable = false;
  bool projected_initiator_is_defender = false;
  std::int32_t incoming_adjacency_kind_raw = -1;
  std::vector<std::int32_t> projected_attacker_army_ids;
  std::vector<std::int32_t> projected_defender_army_ids;
  bool contact_projection_inputs_complete = false;

  friend bool operator==(const ProjectedContactScopeSnapshot &,
                         const ProjectedContactScopeSnapshot &) = default;
};

} // namespace xar::game
