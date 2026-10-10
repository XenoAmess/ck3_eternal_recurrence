#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/keyed_query_completion_diagnostics_v1.hpp"
#include "xar_bridge/ingame_decision_outcome_contract_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include <string>

namespace xar::ck3_11906 {
inline constexpr std::string_view kIngameDecisionItemQueryV1Step = "query-ingame-decision-item-v1";
inline constexpr std::string_view kIngameDecisionItemQueryV1Capability = "game.command.query-ingame-decision-item-v1";
inline constexpr std::string_view kIngameDecisionItemSelectV1Step = "select-ingame-decision-item-v1";
inline constexpr std::string_view kIngameDecisionItemSelectV1Capability = "game.command.select-ingame-decision-item-v1";
inline constexpr std::string_view kIngameDecisionItemConfirmV1Step = "confirm-ingame-decision-item-v1";
inline constexpr std::string_view kIngameDecisionItemConfirmV1Capability = "game.command.confirm-ingame-decision-item-v1";
inline constexpr std::string_view kIngameDecisionOutcomeConfirmV1Step = "confirm-ingame-decision-outcome-v1";
inline constexpr std::string_view kIngameDecisionOutcomeConfirmV1Capability = "game.command.confirm-ingame-decision-outcome-v1";
struct IngameDecisionItemResultV1 {
  std::string game_version = "1.20.0.3";
  std::string executable_sha256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
  std::uint64_t native_revision=0, connection_generation=0;
  std::uint32_t game_pid=0, row_context_reference_key=0;
  std::int32_t played_character_id=-1, date_raw=0;
  std::int32_t detail_actor_reference_key=-1;
  std::size_t group_count=0, row_count=0, matching_row_count=0;
  bool available=false, owner_thread_verified=false, frame_verified=false;
  bool source_abi_pins_verified=false, gui_owner_binding_verified=false;
  bool decisions_tree_complete=false, decisions_root_visible=false;
  bool row_owner_verified=false, row_scope_reference_available=false;
  bool detail_tree_complete=false, detail_root_visible=false;
  bool detail_definition_available=false, detail_definition_matches_target=false;
  bool detail_actor_binding_verified=false;
  std::string decision_key, detail_decision_key, unavailable_reason;
  KeyedQueryCompletionDiagnosticsV1 completion_diagnostics{};
  // Failure-only diagnostics: never used as ownership, frame or action proof.
  std::string model_read_pass, model_failed_stage;
  std::uintptr_t model_observed_pointer=0, model_expected_pointer=0;
};
struct IngameDecisionItemContextV1 {
  const game::GameAdapter *game=nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0, connection_generation=0;
  std::string requested_key;
  IngameDecisionItemResultV1 result{};
};
bool ExecuteIngameDecisionItemQueryV1(IngameDecisionItemContextV1 &,
    MainThreadQueryMailboxV1 &, const MainThreadExecutionStampV1 &,
    const ZhongguoScoreboardNativeEnvironmentV1 &) noexcept;
std::string SerializeIngameDecisionItemV1(const IngameDecisionItemResultV1 &);
enum class IngameDecisionItemActionKindV1 { select, confirm, confirm_outcome };
struct IngameDecisionItemActionResultV1 {
  IngameDecisionItemResultV1 before{},after{};
  IngameDecisionItemActionKindV1 action=IngameDecisionItemActionKindV1::select;
  bool receiver_qualified=false,detail_actor_binding_verified=false,no_blocking_modal_verified=false,action_abi_pins_verified=false;
  bool before_already_selected=false,dispatch_invoked=false,native_call_completed=false,native_handled=false;
  bool gui_owner_binding_verified=false,frame_verified=false,native_after_read=false;
  bool selected_after_verified=false,inner_modal_visible=false,inner_modal_tree_complete=false;
  bool postcondition_verified=false;
  std::string target_child_path,status="unavailable",unavailable_reason;
  std::string expected_outcome,expected_event_definition_key;
};
struct IngameDecisionItemActionContextV1 {
  IngameDecisionItemContextV1 observation{};
  IngameDecisionItemActionKindV1 action=IngameDecisionItemActionKindV1::select;
  std::string expected_window_kind;
  std::string expected_outcome,expected_event_definition_key;
  IngameDecisionItemActionResultV1 result{};
};
bool ExecuteIngameDecisionItemActionV1(IngameDecisionItemActionContextV1 &,
    MainThreadQueryMailboxV1 &,const MainThreadExecutionStampV1 &,
    const ZhongguoScoreboardNativeEnvironmentV1 &,ZhongguoScoreboardActionDispatchEnvironmentV1 &) noexcept;
std::string SerializeIngameDecisionItemActionV1(const IngameDecisionItemActionResultV1 &);
} // namespace xar::ck3_11906
