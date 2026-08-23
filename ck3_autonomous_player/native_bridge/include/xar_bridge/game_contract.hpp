#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace xar::game {

// This file is the version-neutral semantic boundary between the pipe bridge
// and a CK3 executable adapter. Native pointers, RVAs, vtables and object
// layouts must not cross it.

// A generation-bound native declaration choice. The indexes are current
// database/evaluator ordinals, not persistent Casus Belli identifiers. An
// adapter must re-enumerate the full value before submission so a stale choice
// cannot silently become a different war.
struct DeclarableWarSnapshot {
  std::int32_t target_character_id = -1;
  std::int32_t casus_belli_index = -1;
  std::string casus_belli_key;
  std::int32_t configuration_index = -1;
  std::int32_t claimant_character_id = -1;
  std::vector<std::int32_t> target_title_ids;

  friend bool operator==(const DeclarableWarSnapshot &,
                         const DeclarableWarSnapshot &) = default;
};

// One directly sendable, generation-bound marriage choice for the minimal
// headless path. Exact CharacterID handles include the component generation;
// adapters must not resolve them by low-24-bit slot alone.
struct ArrangeMarriageChoice {
  std::int32_t played_character_id = -1;
  std::int32_t candidate_character_id = -1;

  friend bool operator==(const ArrangeMarriageChoice &,
                         const ArrangeMarriageChoice &) = default;
};

// Bounded, version-neutral evidence from one native marriage enumeration.
// Role IDs are captured after the interaction's redirect script has run, so a
// live empty result can be distinguished from storage traversal or context
// routing failures without requiring the CK3 window to be visible.
struct ArrangeMarriageValidationSample {
  std::int32_t slot_index = -1;
  std::int32_t candidate_character_id = -1;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t secondary_actor_character_id = -1;
  std::int32_t secondary_recipient_character_id = -1;
  std::int32_t intermediary_character_id = -1;

  friend bool operator==(const ArrangeMarriageValidationSample &,
                         const ArrangeMarriageValidationSample &) = default;
};

struct ArrangeMarriageQueryDiagnostics {
  std::int32_t storage_capacity = 0;
  std::int32_t slots_scanned = 0;
  std::int32_t empty_slots = 0;
  std::int32_t live_candidates = 0;
  std::int32_t dead_candidates = 0;
  std::int32_t self_candidates = 0;
  std::int32_t generation_mismatch_candidates = 0;
  std::int32_t contexts_constructed = 0;
  std::int32_t context_construct_failures = 0;
  std::int32_t native_validate_true = 0;
  std::int32_t native_validate_false = 0;
  std::vector<ArrangeMarriageValidationSample> validation_false_samples;

  friend bool operator==(const ArrangeMarriageQueryDiagnostics &,
                         const ArrangeMarriageQueryDiagnostics &) = default;
};

struct ArmySnapshot {
  std::int32_t army_id = -1;
  std::int32_t owner_character_id = -1;
  bool has_current_province = false;
  std::int32_t current_province_id = -1;
  bool controllable = false;

  friend bool operator==(const ArmySnapshot &, const ArmySnapshot &) = default;
};

enum class PlayerWarSide {
  attacker,
  defender,
};

struct ActiveWarSnapshot {
  std::int32_t war_id = -1;
  PlayerWarSide player_side = PlayerWarSide::attacker;
  std::int32_t player_relative_war_score = 0;
  std::vector<ArmySnapshot> allied_armies;
  std::vector<ArmySnapshot> enemy_armies;

  friend bool operator==(const ActiveWarSnapshot &,
                         const ActiveWarSnapshot &) = default;
};

struct Snapshot {
  std::int32_t date_raw = 0;
  std::int32_t speed = 0;
  bool paused = false;
  std::int32_t player_id = -1;
  bool map_ready = false;
  bool has_played_character = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
  std::int32_t played_character_betrothed_id = -1;
  std::int32_t played_character_primary_spouse_id = -1;
  std::vector<std::int32_t> played_character_spouse_ids;
  bool has_active_event = false;
  std::int32_t active_event_instance_id = -1;
  std::int32_t active_event_option_count = 0;
  bool has_pending_character_interaction = false;
  std::int32_t pending_character_interaction_id = -1;
  std::int32_t pending_sender_character_id = -1;
  bool pending_auto_accept_notification = false;
  std::vector<ActiveWarSnapshot> active_wars;
  std::vector<ArmySnapshot> player_armies;

  friend bool operator==(const Snapshot &, const Snapshot &) = default;
};

enum class PauseSubmitResult { submitted, already_paused, unavailable };
enum class ResumeSubmitResult { submitted, already_running, unavailable };
enum class SelectEventOptionResult {
  submitted,
  no_active_event,
  option_out_of_range,
  unavailable,
};
enum class SaveCheckpointStatus { submitted, map_not_ready, unavailable };

struct SaveCheckpointResult {
  SaveCheckpointStatus status = SaveCheckpointStatus::unavailable;
  std::int32_t date_raw = 0;
};

enum class PendingInteractionReply { accept = 0, reject = 1 };
enum class ReplyPendingInteractionResult {
  submitted,
  no_pending_interaction,
  acknowledgement_required,
  unavailable,
};
enum class RaiseTroopsResult {
  submitted,
  no_played_character,
  no_default_province,
  validation_failed,
  unavailable,
};
enum class MoveArmyResult {
  submitted,
  army_not_found,
  army_not_controllable,
  province_not_found,
  move_mode_unavailable,
  character_state_rejected,
  army_state_rejected,
  validation_failed,
  unavailable,
};
enum class DisbandArmyResult {
  submitted,
  army_not_found,
  army_not_controllable,
  unavailable,
};
enum class ReadDeclarableWarsResult {
  available,
  no_played_character,
  target_not_found,
  unavailable,
};
enum class DeclareWarResult {
  submitted,
  no_played_character,
  target_not_found,
  declaration_unavailable,
  validation_failed,
  unavailable,
};
enum class ReadArrangeMarriageChoicesResult {
  available,
  no_played_character,
  unavailable,
};
enum class ArrangeMarriageResult {
  submitted,
  no_played_character,
  candidate_not_found,
  choice_unavailable,
  unavailable,
};
enum class EnforceDemandsResult {
  submitted,
  no_played_character,
  war_not_found,
  player_not_participant,
  player_not_war_leader,
  validation_failed,
  unavailable,
};

} // namespace xar::game
