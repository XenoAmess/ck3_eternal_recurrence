#pragma once

#include "xar_bridge/ck3_12004.hpp"

#include <array>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

enum class PrewarAdditionalSupportSource12004 : std::uint8_t {
  immediate_liege, top_liege, diarch, religious_authority,
  religious_follower, forced_initial_participant
};

using PrewarAdditionalObjectGetter12004 = void *(*)(void *);
using PrewarAdditionalFullIdGetter12004 =
    std::uint32_t *(*)(void *, std::uint32_t *);
using PrewarAdditionalPredicate12004 = bool (*)(void *);

enum class PrewarAdditionalRoleStatus12004 : std::uint8_t {
  unavailable, known_empty, living_character, dead_character
};
enum class PrewarAdditionalLookupStatus12004 : std::uint8_t {
  unobserved, root_unavailable, absent_id, index_out_of_bounds,
  entry_unavailable, full_id_mismatch, type_mismatch, resolved
};

struct PrewarAdditionalSupportersBindings12004 {
  bool enabled = false;
  CoreBindings core{};
  void **character_fallback_slot = nullptr;
  PrewarAdditionalObjectGetter12004 immediate_liege = nullptr;
  PrewarAdditionalObjectGetter12004 top_liege = nullptr;
  PrewarAdditionalObjectGetter12004 character_faith = nullptr;
  PrewarAdditionalObjectGetter12004 faith_head = nullptr;
  PrewarAdditionalObjectGetter12004 religious_authority = nullptr;
  void **subject_contract_storage_slot = nullptr;
  void **subject_contract_fallback_slot = nullptr;
  void **subject_contract_database_slot = nullptr;
  const void *compiled_effect_vtable = nullptr;
  const void *compiled_effect_execute = nullptr;
  void **event_manager_slot = nullptr;
  // Different typed receivers: Character -> full DiarchyID, then the
  // resolved Diarchy -> full CharacterID. Native pointer types omit noexcept.
  PrewarAdditionalFullIdGetter12004 character_diarchy_full_id = nullptr;
  PrewarAdditionalFullIdGetter12004 diarchy_diarch_full_id = nullptr;
  PrewarAdditionalPredicate12004 has_active_diarchy = nullptr;
  void **diarchy_storage_slot = nullptr;
  void **diarchy_fallback_slot = nullptr;
  PrewarAdditionalObjectGetter12004 religious_challenger = nullptr;
  std::array<void **, 3> formal_head_storage_slots{};
  std::array<void **, 3> formal_head_fallback_slots{};
};

// Borrowed only during the owning query. These are the actual fresh finalized
// selected-CB roles, never generic war-entry effective-target substitutes.
// additional/recipient are the selected primary inputs supplied by the caller;
// actor remains independent. The caller owns their selected-CB provenance.
struct PrewarAdditionalSupportersNativeScope12004 {
  const void *actual_cb = nullptr;
  void *actor = nullptr;
  void *additional = nullptr;
  void *recipient = nullptr;
  // Qualification of the actual selected flag15 collector supplied by the
  // same owning callback. False is the default when that branch is unknown.
  bool holy_initial_participants_complete = false;
};

struct PrewarAdditionalSupporter12004 {
  std::int32_t source_root_character_id = -1;
  std::int32_t character_id = -1;
  PrewarAdditionalSupportSource12004 source =
      PrewarAdditionalSupportSource12004::immediate_liege;
  bool operator==(const PrewarAdditionalSupporter12004 &) const = default;
};

struct PrewarForcedInitialParticipant12004 {
  std::int32_t character_id = -1;
  bool attacker_side = false;
  std::int32_t source_primary_character_id = -1;
  std::int32_t subject_contract_id = -1;
  std::uint32_t source_contract_native_order = 0;
  std::uint8_t active_level_index_raw = 0;
  std::uint8_t default_level_index_raw = 0;
  bool operator==(const PrewarForcedInitialParticipant12004 &) const = default;
};

struct PrewarAdditionalDiarchObservation12004 {
  std::int32_t source_root_character_id = -1;
  bool auxiliary_observed = false;
  bool auxiliary_present = false;
  bool association_id_observed = false;
  bool association_out_pointer_echo = false;
  std::uint32_t association_full_id_raw = 0xFFFFFFFFU;
  bool active_predicate_observed = false;
  bool active_predicate_value = false;
  PrewarAdditionalLookupStatus12004 diarchy_lookup =
      PrewarAdditionalLookupStatus12004::unobserved;
  bool diarchy_fallback_observed = false;
  std::uint32_t diarchy_full_id_raw = 0xFFFFFFFFU;
  std::uint32_t diarchy_magic_raw = 0;
  bool diarch_id_observed = false;
  bool diarch_out_pointer_echo = false;
  std::uint32_t diarch_full_id_raw = 0xFFFFFFFFU;
  bool character_fields_observed = false;
  std::uint32_t character_full_id_raw = 0xFFFFFFFFU;
  std::uint32_t character_magic_raw = 0;
  bool character_core_identity_verified = false;
  bool character_alive = false;
  PrewarAdditionalRoleStatus12004 status =
      PrewarAdditionalRoleStatus12004::unavailable;
  bool operator==(const PrewarAdditionalDiarchObservation12004 &) const = default;
};

struct PrewarAdditionalAuthorityObservation12004 {
  std::int32_t source_root_character_id = -1;
  bool getter_observed = false;
  bool returned_object_present = false;
  bool returned_fields_observed = false;
  std::uint32_t returned_full_id_raw = 0xFFFFFFFFU;
  std::uint32_t returned_magic_raw = 0;
  bool returned_core_identity_verified = false;
  bool returned_alive = false;
  bool challenger_getter_observed = false;
  bool challenger_fields_observed = false;
  std::uint32_t challenger_full_id_raw = 0xFFFFFFFFU;
  std::uint32_t challenger_magic_raw = 0;
  bool returned_matches_observed_challenger = false;
  std::array<bool, 4> formal_chain_id_observed{};
  std::array<std::uint32_t, 4> formal_chain_full_ids_raw{};
  std::array<PrewarAdditionalLookupStatus12004, 4> formal_chain_lookup{};
  std::array<bool, 4> formal_chain_fallback_observed{};
  // FF/invalid return stays unavailable until the challenger empty branch
  // and every required native root are independently qualified.
  PrewarAdditionalRoleStatus12004 status =
      PrewarAdditionalRoleStatus12004::unavailable;
  bool operator==(const PrewarAdditionalAuthorityObservation12004 &) const = default;
};

struct PrewarAdditionalSupportersSnapshot12004 {
  bool sampled = false;
  std::int32_t actor_character_id = -1;
  std::int32_t additional_character_id = -1;
  std::int32_t recipient_character_id = -1;
  bool immediate_liege_complete = false;
  bool top_liege_complete = false;
  bool diarch_complete = false;
  bool religious_authority_complete = false;
  bool religious_follower_complete = false;
  bool forced_contract_subset_complete = false;
  bool cb_flags_observed = false;
  std::uint32_t cb_flags_raw = 0;
  bool cb_start_effect_observed = false;
  bool cb_start_effect_receiver_type_matches = false;
  bool cb_start_effect_execute_matches = false;
  bool cb_start_effect_child_data_present = false;
  std::int32_t cb_start_effect_child_count = -1;
  // Owned equality witness for data+30 and count+3C. These opaque bytes are
  // never dereferenced or published as a native pointer by the consumer.
  std::array<std::uint8_t, 12> cb_start_effect_header_identity_bytes{};
  bool cb_start_effect_known_empty = false;
  bool war_started_on_action_observed = false;
  bool war_started_on_action_known_empty = false;
  bool holy_initial_participants_applicable = false;
  bool holy_initial_participants_complete = false;
  // Current selected builder branches only. Nonempty compiled/event trees
  // require their own qualification; neither is executed by this reader.
  bool complete_initial_participants_ready = false;
  bool complete_all_potential_supporters = false;
  std::int32_t character_storage_slot_count = -1;
  std::int32_t character_storage_visited_count = 0;
  std::uint32_t attacker_source_contract_count = 0;
  std::uint32_t defender_source_contract_count = 0;
  std::vector<std::int32_t> unresolved_source_character_ids;
  std::vector<std::int32_t> dead_source_character_ids;
  std::vector<PrewarAdditionalSupporter12004> candidates;
  std::vector<PrewarForcedInitialParticipant12004> forced_participants;
  std::vector<PrewarForcedInitialParticipant12004> excluded_primary_defender_collisions;
  std::vector<PrewarAdditionalDiarchObservation12004> diarch_observations;
  // One qualified observer is shared by root adjacency and follower selection.
  // Rows retain native order; followers reuse an already observed root row.
  std::vector<PrewarAdditionalAuthorityObservation12004> authority_observations;
  std::string_view reason;
  bool operator==(const PrewarAdditionalSupportersSnapshot12004 &) const = default;
};

PrewarAdditionalSupportersBindings12004 BindPrewarAdditionalSupportersImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// One round, owning paused thread only. The caller supplies actual selected
// roles, compares two complete DTOs and seals its full-snapshot mailbox frame.
// True retains sampled partial domains. Unknown callbacks are not native false.
// Candidate adjacency gives no future CanSend, acceptance or actual join result.
bool ReadPrewarAdditionalSupporters12004(
    const PrewarAdditionalSupportersBindings12004 &bindings,
    const CoreSnapshotPrefix &frame,
    const PrewarAdditionalSupportersNativeScope12004 &selected_scope,
    PrewarAdditionalSupportersSnapshot12004 &output,
    std::string_view *reason = nullptr) noexcept;

} // namespace xar::ck3_12004
