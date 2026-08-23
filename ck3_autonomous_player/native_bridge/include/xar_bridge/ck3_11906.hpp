#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr char kExecutableSha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr char kCheckpointSaveName[] = "xar_checkpoint";

using SubmitCommand = void (*)(void *manager, void *command,
                               std::uint32_t channel_flags);
using GetLocalPlayer = void *(*)(void *jomini_state);
using GetCurrentEvent = void *(*)(void *event_manager);
using ContainsWarParticipant = bool (*)(void *participant_container,
                                        std::int32_t character_id);
using GetWarScore = std::int32_t (*)(void *war, void *war_score_context);
using ResolveDefaultRaiseProvince = void *(*)(void *character);
using ConstructRaiseTroopsCommand = void *(*)(void *command,
                                              std::int32_t character_id,
                                              const void *raise_entry);
using ValidateRaiseTroopsCommand = bool (*)(void *command,
                                            void *validation_context);
using DestroyNativeCommand = void *(*)(void *command,
                                       std::int32_t delete_flags);
using GetArmyMoveMode = std::int32_t (*)(void *army, void *province,
                                        std::int32_t direct_target);
using CanMoveArmy = bool (*)(std::int32_t command_kind, void *army,
                            std::int32_t move_mode);
using InitializeArmyMovePath = void (*)(void *path_storage);

// Absolute addresses resolved only after the main executable matches the
// pinned 1.19.0.6 SHA-256. Tests may supply a small in-memory fixture instead.
struct Bindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void *command_manager = nullptr;
  std::uintptr_t pause_primary_vtable = 0;
  std::uintptr_t pause_secondary_vtable = 0;
  std::uintptr_t set_speed_primary_vtable = 0;
  std::uintptr_t set_speed_secondary_vtable = 0;
  std::uintptr_t select_event_option_primary_vtable = 0;
  std::uintptr_t select_event_option_secondary_vtable = 0;
  std::uintptr_t auto_save_primary_vtable = 0;
  std::uintptr_t auto_save_secondary_vtable = 0;
  std::uintptr_t reply_character_interaction_primary_vtable = 0;
  std::uintptr_t reply_character_interaction_secondary_vtable = 0;
  std::uintptr_t raise_troops_primary_vtable = 0;
  std::uintptr_t raise_troops_secondary_vtable = 0;
  std::uintptr_t move_army_primary_vtable = 0;
  std::uintptr_t move_army_secondary_vtable = 0;
  std::uintptr_t disband_army_primary_vtable = 0;
  std::uintptr_t disband_army_secondary_vtable = 0;
  void **pending_character_interaction_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **army_storage_slot = nullptr;
  std::size_t event_manager_offset = 0;
  std::size_t player_character_manager_offset = 0;
  std::size_t war_manager_offset = 0;
  SubmitCommand submit_command = nullptr;
  GetLocalPlayer get_local_player = nullptr;
  GetCurrentEvent get_current_event = nullptr;
  ContainsWarParticipant contains_war_participant = nullptr;
  GetWarScore get_war_score = nullptr;
  ResolveDefaultRaiseProvince resolve_default_raise_province = nullptr;
  ConstructRaiseTroopsCommand construct_raise_troops_command = nullptr;
  ValidateRaiseTroopsCommand validate_raise_troops_command = nullptr;
  DestroyNativeCommand destroy_raise_troops_command = nullptr;
  GetArmyMoveMode get_army_move_mode = nullptr;
  CanMoveArmy can_move_army = nullptr;
  InitializeArmyMovePath initialize_army_move_path = nullptr;
  DestroyNativeCommand destroy_move_army_command = nullptr;
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

enum class PauseSubmitResult {
  submitted,
  already_paused,
  unavailable,
};

enum class ResumeSubmitResult {
  submitted,
  already_running,
  unavailable,
};

// Hashes the current process image on disk. A mismatch returns disabled
// bindings and therefore cannot advertise or execute CK3 gameplay features.
Bindings BindCurrentProcess() noexcept;

bool ReadSnapshot(const Bindings &bindings, Snapshot &output) noexcept;

// pause-map is an idempotent action: it reports already_paused without adding
// a command, otherwise it submits the same 0x28-byte CPauseGameCommand shape
// used by CK3's own UI through the engine's locked command queue path.
PauseSubmitResult SubmitPauseMap(const Bindings &bindings) noexcept;

// resume-map is the inverse idempotent operation.  It is required for a
// freshly loaded headless map because changing the speed does not clear
// Jomini's paused bit.
ResumeSubmitResult SubmitResumeMap(const Bindings &bindings) noexcept;

// Fixed public speeds 1..5 deliberately map to separate advertised gameplay
// steps.  CK3's native CSetGameSpeedCommand payload is zero based (0..4).
bool SubmitSetSpeed(const Bindings &bindings, std::int32_t speed) noexcept;

enum class SelectEventOptionResult {
  submitted,
  no_active_event,
  option_out_of_range,
  unavailable,
};

// Selects a zero-based native option on the same current local-player event
// returned in Snapshot. The public select-event-option-1..N step is translated
// to this zero-based payload at the protocol boundary. CK3's executor performs
// the same 0 <= index < option_count check before dispatching the effect.
SelectEventOptionResult
SubmitSelectEventOption(const Bindings &bindings,
                        std::int32_t option_index) noexcept;

enum class SaveCheckpointStatus {
  submitted,
  map_not_ready,
  unavailable,
};

struct SaveCheckpointResult {
  SaveCheckpointStatus status = SaveCheckpointStatus::unavailable;
  std::int32_t date_raw = 0;
};

// Queues CK3's own CAutoSaveCommand with the fixed short save name
// `xar_checkpoint`. The result confirms queue submission, not asynchronous
// disk completion; the caller can correlate date_raw and the save name with
// the produced save file.
SaveCheckpointResult SubmitSaveCheckpoint(const Bindings &bindings) noexcept;

enum class PendingInteractionReply {
  accept = 0,
  reject = 1,
};

enum class ReplyPendingInteractionResult {
  submitted,
  no_pending_interaction,
  acknowledgement_required,
  unavailable,
};

// Replies to the first pending CK3 character interaction exposed by Snapshot.
// CPendingCharacterInteraction's component ID is the int32 payload consumed by
// CReplyCharacterInteractionCommand; accept/reject are native enum values 0/1.
ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const Bindings &bindings, PendingInteractionReply reply) noexcept;

enum class RaiseTroopsResult {
  submitted,
  no_played_character,
  no_default_province,
  validation_failed,
  unavailable,
};

// Raises the played character's troops at CK3's own default rally province.
// The native constructor owns an internal allocation, so the bridge validates,
// queues (which clones synchronously), and destroys the stack command in the
// same order as the original UI path.
RaiseTroopsResult SubmitRaiseTroopsDefault(const Bindings &bindings) noexcept;

enum class MoveArmyResult {
  submitted,
  army_not_found,
  army_not_controllable,
  province_not_found,
  cannot_move,
  unavailable,
};

MoveArmyResult SubmitMoveArmy(const Bindings &bindings,
                              std::int32_t army_id,
                              std::int32_t province_id) noexcept;

enum class DisbandArmyResult {
  submitted,
  army_not_found,
  army_not_controllable,
  unavailable,
};

DisbandArmyResult SubmitDisbandArmy(const Bindings &bindings,
                                    std::int32_t army_id) noexcept;

} // namespace xar::ck3_11906
