#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr char kExecutableSha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr char kCheckpointSaveName[] = "xar_checkpoint";

using SubmitCommand = void (*)(void *manager, void *command,
                               std::uint32_t channel_flags);
using GetLocalPlayer = void *(*)(void *jomini_state);
using GetCurrentEvent = void *(*)(void *event_manager);
using IsPendingCharacterInteractionForCharacter = bool (*)(
    void *pending_interaction, void *character);
using ValidateReplyCharacterInteractionCommand = bool (*)(void *command);
using ContainsWarParticipant = bool (*)(void *participant_container,
                                        std::int32_t character_id);
using GetWarScore = std::int32_t (*)(void *war, void *war_score_context);
using ResolveDefaultRaiseProvince = void *(*)(void *character);
using GetUnitState = std::int32_t (*)(void *unit);
using ConstructRaiseTroopsCommand = void *(*)(void *command,
                                              std::int32_t character_id,
                                              const void *raise_entry);
using ValidateRaiseTroopsCommand = bool (*)(void *command,
                                            void *validation_context);
using DestroyNativeCommand = void *(*)(void *command,
                                       std::int32_t delete_flags);
using GetArmyMoveMode = std::int32_t (*)(void *army, void *province,
                                        std::int32_t direct_target);
using CanCharacterUseCommandKind = bool (*)(void *character,
                                            std::int32_t command_kind);
using CanArmyUseMoveMode = bool (*)(void *army, std::int32_t move_mode);
using CanMoveArmy = bool (*)(std::int32_t command_kind, void *army,
                            std::int32_t move_mode);
using InitializeArmyMovePath = void (*)(void *path_storage);
using ValidateDisbandArmyCommand = bool (*)(
    std::int32_t command_kind, std::int32_t command_target_id,
    void *error_output);
using GetCasusBelliTypeDatabase = void *(*)();
using GetCharacterInteractionDatabase = void *(*)();
using EvaluateCasusBelli = bool (*)(void *casus_belli_type,
                                    void *attacker_character,
                                    void *defender_character,
                                    void *output_configurations,
                                    bool include_blocked,
                                    bool unknown_flag,
                                    void *evaluation_context);
using DestroyValidCasusBelliConfiguration = void (*)(void *configuration);
using ConstructCharacterInteractionContext = void *(*)(
    void *context, void *interaction, std::int32_t actor_character_id,
    std::int32_t recipient_character_id, void *extra_context,
    bool initialize_special_data);
using RedirectCharacterInteractionRoles = void (*)(
    void *interaction, std::int32_t *actor_character_id,
    std::int32_t *recipient_character_id,
    std::int32_t *secondary_actor_character_id,
    std::int32_t *secondary_recipient_character_id,
    std::int32_t *intermediary_character_id);
using ConstructCharacterInteractionContextAllRoles = void *(*)(
    void *context, void *interaction, std::int32_t actor_character_id,
    std::int32_t recipient_character_id,
    std::int32_t secondary_actor_character_id,
    std::int32_t secondary_recipient_character_id,
    std::int32_t intermediary_character_id, void *extra_context);
using CopyNativeIntArray = void (*)(void *destination, const void *source);
using AppendNativeIntArrayRange = void (*)(void *destination,
                                           std::int32_t current_count,
                                           const std::int32_t *begin,
                                           const std::int32_t *end);
using RefreshCharacterInteractionContext = void (*)(void *context,
                                                     bool refresh);
using FinalizeCharacterInteractionContext = void (*)(void *context);
using ValidateCharacterInteractionContext = bool (*)(void *context,
                                                      void *error_output);
using ConstructSendCharacterInteractionCommand = void *(*)(
    void *command, const void *context);
using DestroyCharacterInteractionContext = void (*)(void *context);
using DefaultConstructCharacterInteractionContext = void *(*)(void *context);
using ConstructWarResolutionInteractionContext = void (*)(void *context,
                                                           void *war,
                                                           bool surrender);
using GetGlobalVariableContainer = void *(*)();
using GetScriptIdentifierTable = void *(*)();
using LookupScriptIdentifierId = std::int32_t *(*)(
    void *table, std::int32_t *output, const void *string_view);
using IsEventTargetValid = bool (*)(const void *event_target);
using ResolveEventTargetObject = void *(*)(const void *event_target);

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
  std::uintptr_t send_character_interaction_primary_vtable = 0;
  std::uintptr_t send_character_interaction_secondary_vtable = 0;
  std::uintptr_t war_declaration_vtable = 0;
  void **pending_character_interaction_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **army_storage_slot = nullptr;
  GetGlobalVariableContainer *global_variable_container_accessor_slot =
      nullptr;
  void *valid_casus_belli_configuration_scratch = nullptr;
  std::size_t event_manager_offset = 0;
  std::size_t player_character_manager_offset = 0;
  std::size_t war_manager_offset = 0;
  std::size_t landed_title_manager_offset = 0;
  std::size_t arrange_marriage_interaction_offset = 0;
  std::size_t declare_war_interaction_offset = 0;
  SubmitCommand submit_command = nullptr;
  GetLocalPlayer get_local_player = nullptr;
  GetCurrentEvent get_current_event = nullptr;
  IsPendingCharacterInteractionForCharacter
      is_pending_character_interaction_for_character = nullptr;
  ValidateReplyCharacterInteractionCommand
      validate_reply_character_interaction_command = nullptr;
  ContainsWarParticipant contains_war_participant = nullptr;
  GetWarScore get_war_score = nullptr;
  ResolveDefaultRaiseProvince resolve_default_raise_province = nullptr;
  GetUnitState get_unit_state = nullptr;
  ConstructRaiseTroopsCommand construct_raise_troops_command = nullptr;
  ValidateRaiseTroopsCommand validate_raise_troops_command = nullptr;
  DestroyNativeCommand destroy_raise_troops_command = nullptr;
  GetArmyMoveMode get_army_move_mode = nullptr;
  CanCharacterUseCommandKind can_character_use_command_kind = nullptr;
  CanArmyUseMoveMode can_army_use_move_mode = nullptr;
  CanMoveArmy can_move_army = nullptr;
  InitializeArmyMovePath initialize_army_move_path = nullptr;
  DestroyNativeCommand destroy_move_army_command = nullptr;
  ValidateDisbandArmyCommand validate_disband_army_command = nullptr;
  GetCasusBelliTypeDatabase get_casus_belli_type_database = nullptr;
  GetCharacterInteractionDatabase get_character_interaction_database =
      nullptr;
  EvaluateCasusBelli evaluate_casus_belli = nullptr;
  DestroyValidCasusBelliConfiguration
      destroy_valid_casus_belli_configuration = nullptr;
  ConstructCharacterInteractionContext
      construct_character_interaction_context = nullptr;
  RedirectCharacterInteractionRoles redirect_character_interaction_roles =
      nullptr;
  ConstructCharacterInteractionContextAllRoles
      construct_character_interaction_context_all_roles = nullptr;
  CopyNativeIntArray copy_native_int_array = nullptr;
  AppendNativeIntArrayRange append_native_int_array_range = nullptr;
  RefreshCharacterInteractionContext
      refresh_character_interaction_context = nullptr;
  FinalizeCharacterInteractionContext
      finalize_character_interaction_context = nullptr;
  ValidateCharacterInteractionContext
      validate_character_interaction_context = nullptr;
  ConstructSendCharacterInteractionCommand
      construct_send_character_interaction_command = nullptr;
  DestroyCharacterInteractionContext
      destroy_character_interaction_context = nullptr;
  DefaultConstructCharacterInteractionContext
      default_construct_character_interaction_context = nullptr;
  ConstructWarResolutionInteractionContext
      construct_war_resolution_interaction_context = nullptr;
  GetScriptIdentifierTable get_script_identifier_table = nullptr;
  LookupScriptIdentifierId lookup_script_identifier_id = nullptr;
  IsEventTargetValid is_event_target_valid = nullptr;
  ResolveEventTargetObject resolve_event_target_object = nullptr;
};

using game::ActiveWarSnapshot;
using game::ArrangeMarriageChoice;
using game::ArrangeMarriageQueryDiagnostics;
using game::ArrangeMarriageValidationSample;
using game::ArmySnapshot;
using game::DeclarableWarSnapshot;
using game::FixedPointValue;
using game::OneLifeSettlementSnapshot;
using game::PlayerWarSide;
using game::Snapshot;
using game::PauseSubmitResult;
using game::ResumeSubmitResult;

// The generic registry hashes the process image once and passes an exact-match
// decision into the selected version adapter. False returns disabled bindings.
Bindings BindCurrentProcess(bool executable_matches) noexcept;

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

using game::SelectEventOptionResult;

// Selects a zero-based native option on the same current local-player event
// returned in Snapshot. The public select-event-option-1..N step is translated
// to this zero-based payload at the protocol boundary. CK3's executor performs
// the same 0 <= index < option_count check before dispatching the effect.
SelectEventOptionResult
SubmitSelectEventOption(const Bindings &bindings,
                        std::int32_t option_index) noexcept;

using game::SaveCheckpointResult;
using game::SaveCheckpointStatus;

// Queues CK3's own CAutoSaveCommand with the fixed short save name
// `xar_checkpoint`. The result confirms queue submission, not asynchronous
// disk completion; the caller can correlate date_raw and the save name with
// the produced save file.
SaveCheckpointResult SubmitSaveCheckpoint(const Bindings &bindings) noexcept;

using game::PendingInteractionReply;
using game::ReplyPendingInteractionResult;

// Replies to the first locally addressed and natively actionable CK3 character
// interaction exposed by Snapshot. CPendingCharacterInteraction's component ID
// is the int32 payload consumed by CReplyCharacterInteractionCommand;
// accept/reject are native enum values 0/1.
ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const Bindings &bindings, PendingInteractionReply reply) noexcept;

using game::RaiseTroopsResult;

// Raises the played character's troops at CK3's own default rally province.
// The native constructor owns an internal allocation, so the bridge validates,
// queues (which clones synchronously), and destroys the stack command in the
// same order as the original UI path.
RaiseTroopsResult SubmitRaiseTroopsDefault(const Bindings &bindings) noexcept;

using game::MoveArmyResult;

MoveArmyResult SubmitMoveArmy(const Bindings &bindings,
                              std::int32_t army_id,
                              std::int32_t province_id) noexcept;

using game::DisbandArmyResult;

DisbandArmyResult SubmitDisbandArmy(const Bindings &bindings,
                                    std::int32_t army_id) noexcept;

using game::ReadDeclarableWarsResult;

// Runs CK3's own CB evaluator against one explicit target. This is the cheap
// path for a planner that already knows a CharacterID. The global overload is
// intentionally separate because scanning every live Character is a much
// heavier strategic query and should not run on every heartbeat snapshot.
ReadDeclarableWarsResult ReadDeclarableWarsForTarget(
    const Bindings &bindings, std::int32_t target_character_id,
    std::vector<DeclarableWarSnapshot> &output) noexcept;

bool ReadDeclarableWars(
    const Bindings &bindings,
    std::vector<DeclarableWarSnapshot> &output) noexcept;

using game::DeclareWarResult;

// Re-runs native enumeration and requires an exact match of every choice
// field before constructing CSendCharacterInteractionCommand. Queue cloning
// is synchronous; both the copied command context and the original temporary
// context are destroyed after submission in CK3's native order.
DeclareWarResult SubmitDeclareWar(
    const Bindings &bindings,
    const DeclarableWarSnapshot &declaration) noexcept;

using game::ReadArrangeMarriageChoicesResult;

// Explicit strategic query; it is intentionally not part of the heartbeat
// snapshot. Every returned candidate has passed CK3's own arrange-marriage
// context refresh/finalize/validation chain for the currently played
// Character. Minors naturally produce a betrothal through the same native
// interaction.
ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const Bindings &bindings,
    std::vector<ArrangeMarriageChoice> &output,
    ArrangeMarriageQueryDiagnostics &diagnostics) noexcept;

using game::ArrangeMarriageResult;

// Rebuilds the context from both exact CharacterID handles and validates it
// again before sending CSendCharacterInteractionCommand. This first slice is
// deliberately the useful direct path (played Character <-> candidate), not
// the wider four-role courtier matchmaking surface.
ArrangeMarriageResult SubmitArrangeMarriage(
    const Bindings &bindings,
    const ArrangeMarriageChoice &choice) noexcept;

using game::EnforceDemandsResult;

// Builds the same victory interaction context as WarOverviewWindow's victory
// tab for one live CWar led by the played character, then sends the common
// native character-interaction command. The visual confirmation wrapper is
// intentionally not part of the gameplay command and is not needed in
// headless mode.
EnforceDemandsResult SubmitEnforceDemands(const Bindings &bindings,
                                          std::int32_t war_id) noexcept;

} // namespace xar::ck3_11906
