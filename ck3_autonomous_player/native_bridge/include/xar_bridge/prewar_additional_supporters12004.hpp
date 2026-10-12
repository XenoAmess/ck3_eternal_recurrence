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

struct PrewarAdditionalSupportersBindings12004 {
  bool enabled = false;
  CoreBindings core{};
  void **character_fallback_slot = nullptr;
  PrewarAdditionalObjectGetter12004 immediate_liege = nullptr;
  PrewarAdditionalObjectGetter12004 top_liege = nullptr;
  // Unmapped callbacks stay null. No guessed image RVA is admitted.
  PrewarAdditionalObjectGetter12004 diarch = nullptr;
  PrewarAdditionalObjectGetter12004 character_faith = nullptr;
  PrewarAdditionalObjectGetter12004 faith_head = nullptr;
  PrewarAdditionalObjectGetter12004 religious_authority = nullptr;
  void **subject_contract_storage_slot = nullptr;
  void **subject_contract_fallback_slot = nullptr;
  void **subject_contract_database_slot = nullptr;
  const void *compiled_effect_vtable = nullptr;
  const void *compiled_effect_execute = nullptr;
  void **event_manager_slot = nullptr;
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
