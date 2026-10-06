#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12003 {
inline constexpr std::string_view kGrantTitlePickerQueryV1Step="query-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerPrepareV1Step="prepare-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerSelectV1Step="select-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerSendV1Step="send-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerQueryV1Capability="game.command.query-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerPrepareV1Capability="game.command.prepare-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerSelectV1Capability="game.command.select-grant-title-picker-v1";
inline constexpr std::string_view kGrantTitlePickerSendV1Capability="game.command.send-grant-title-picker-v1";
enum class GrantTitlePickerOperationV1 {query,prepare,select,send};
struct GrantTitlePickerRowV1 {
  std::uint32_t title_full_id=UINT32_MAX;
  std::optional<std::uint32_t> holder_character_full_id;
  bool selected=false,selectable=false;
  bool operator==(const GrantTitlePickerRowV1 &) const=default;
};
struct GrantTitlePickerHolderV1 {
  std::uint32_t title_full_id=UINT32_MAX;
  bool available=false;
  std::optional<std::uint32_t> holder_character_full_id;
  bool operator==(const GrantTitlePickerHolderV1 &) const=default;
};
struct GrantTitlePickerObservationV1 {
  bool available=false,window_visible=false,window_binding_verified=false,rows_complete=false;
  std::optional<bool> native_can_send,warning_confirmation_required;
  std::vector<GrantTitlePickerRowV1> rows;
  std::vector<std::uint32_t> selected_title_full_ids;
  std::vector<GrantTitlePickerHolderV1> requested_title_holders;
  bool operator==(const GrantTitlePickerObservationV1 &) const=default;
};
struct GrantTitlePickerResultV1 {
  std::uint64_t native_revision=0,connection_generation=0;
  std::uint32_t game_pid=0,recipient_character_full_id=UINT32_MAX;
  std::int32_t played_character_id=-1,date_raw=0;
  GrantTitlePickerOperationV1 operation=GrantTitlePickerOperationV1::query;
  bool owner_thread_verified=false,frame_verified=false,source_abi_pins_verified=false;
  bool dispatch_invoked=false,native_call_completed=false,selection_verified=false,transfer_verified=false;
  GrantTitlePickerObservationV1 before{},after{};
  std::string status="unavailable",unavailable_reason;
};
struct GrantTitlePickerContextV1 {
  const game::GameAdapter *game=nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0,connection_generation=0;
  std::uint32_t recipient_character_full_id=UINT32_MAX,title_full_id=UINT32_MAX;
  bool desired_selected=false;
  GrantTitlePickerOperationV1 operation=GrantTitlePickerOperationV1::query;
  // Full IDs are exact values; low24 indices are never protocol identities.
  std::vector<std::uint32_t> requested_title_full_ids,expected_selected_title_full_ids;
  GrantTitlePickerResultV1 result{};
};
bool ParseGrantTitlePickerIdsV1(std::string_view,std::vector<std::uint32_t> &,bool allow_empty) noexcept;
bool ParseGrantTitlePickerIdsFieldV1(std::string_view,std::string_view,std::vector<std::uint32_t> &,bool allow_empty) noexcept;
bool ExecuteGrantTitlePickerV1(GrantTitlePickerContextV1 &,ck3_11906::MainThreadQueryMailboxV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &,const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &) noexcept;
std::string SerializeGrantTitlePickerV1(const GrantTitlePickerResultV1 &);
} // namespace xar::ck3_12003
