#pragma once
#include "xar_bridge/player_control_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"

namespace xar::ck3_12003 {
struct PlayerControlIdentitySourceContextV1 {
  const game::GameAdapter *game = nullptr;
  const PlayerControlRequestV1 *request = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0, connection_generation=0;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  void *owner_executor_context = nullptr;
};
// An actual read-only source component, executed only by the existing owner
// mailbox. It never creates a flow, clears claims, admits a stock action, or
// equates played-history records with current human control. The actual stock
// current-player array is bound across both global owners and read twice; only
// exact stock player objects are supported. Local membership needs the exact
// current character, actual human membership and nonobserver flag. Unknown
// objects/tuples, observers and other-human mapping remain NULL. GUI and action
// target fields remain unavailable.
// The complete actual CCharacterManager living source universe is enumerated
// twice with full ID/storage equality, liveness and stock IsRuler, then filtered
// to living ruler playables. candidates_complete describes that source-derived
// set, never stock chooser eligibility, CanControl, selection GUI completeness
// or action admission. Scan, candidate publication and actual encoded wire size
// each have fail-closed limits. Above a bound or an invalid/unread row it remains
// false; the actual selected living member can still supply a partial row.
// CanControl and selection GUI fields stay NULL. Stock ironman and
// multiplayer flags, and selected character from a fixed RTTI-checked current
// PauseMenu/Lobby owner chain, are read only when their actual sources exist.
// Actual preparation-lobby mode is rejected; model allocation alone never
// produces a GUI phase, visible target or admitted action.
// Internal owner-bound borrow, never transport input or serialized pointers.
// This stamp is valid only inside the same paused mailbox execution. A consumer
// must fresh-read again before any stock callback; it must not retain the model
// pointers across pumps. No GUI, callback or datatype admission is implied.
struct PlayerControlOwnedIdentityBindingV1 {
  std::uint64_t mailbox_sequence=0, pump_epoch=0;
  std::uint32_t owner_thread_id=0;
  std::int32_t date_raw=0;
  std::uintptr_t handler=0, pause_menu=0, lobby=0, playable_supplier=0;
  std::optional<std::uint64_t> selected_character_id;
  std::optional<std::uintptr_t> selected_character, selected_character_vtable;
  std::optional<bool> selected_character_alive, selected_character_is_ruler;
  // The actual Character initial-context datatype has no proven binding yet.
  std::optional<std::uint32_t> selected_character_context_datatype;
  bool source_complete=false;
  friend bool operator==(const PlayerControlOwnedIdentityBindingV1 &,
      const PlayerControlOwnedIdentityBindingV1 &)=default;
};
bool ReadPlayerControlOwnedIdentitySourceV1(
    const PlayerControlIdentitySourceContextV1 &context,
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
    PlayerControlObservationV1 &observation,
    PlayerControlOwnedIdentityBindingV1 &owned) noexcept;
bool ReadPlayerControlIdentitySourceV1(
    const PlayerControlIdentitySourceContextV1 &context,
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
    PlayerControlObservationV1 &observation) noexcept;
// Actual fixed-source anonymous Control callback qualification, never dispatch.
// The seven source proofs must originate from the owner provider's independently
// verified manifest/build/frame. This function cannot create or bless them.
// It obtains all model/character addresses itself, binds actual AST argument keys,
// proves the exact three actions and empty prehandler/priority groups, and checks
// all raw reads and complete census twice. Transport inputs contain no address,
// datatype, source proof boolean or callback selector. CanControl stays NULL.
bool ReadPlayerControlControlGuiSourceV1(
    const PlayerControlIdentitySourceContextV1 &context,
    const ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,
    const PlayerControlObservationV1 &actual_source_proofs,
    PlayerControlTargetV1 &target,
    std::optional<std::uintptr_t> &internal_widget,
    std::string &reason) noexcept;
// Private owner-only partial runtime provider. No mutation, flow or signature.
struct PlayerControlReadonlyContextV1 {
  const game::GameAdapter *game=nullptr;
  PlayerControlRequestV1 request{};
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0,connection_generation=0;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  void *owner_executor_context=nullptr;
  PlayerControlObservationV1 observation{};
};
bool ExecutePlayerControlReadonlyV1(PlayerControlReadonlyContextV1 &context,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment) noexcept;
} // namespace xar::ck3_12003
