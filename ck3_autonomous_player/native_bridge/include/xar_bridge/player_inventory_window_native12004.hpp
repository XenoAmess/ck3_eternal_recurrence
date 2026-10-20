#pragma once
#include "xar_bridge/artifact_personal_use12004.hpp"
#include "xar_bridge/player_inventory_open_post12004.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include <string>
namespace xar::ck3_11906 {
// Internal adapters only. Frame/eligibility and final native witness originate
// from the actual application owner. No caller supplies a native address.
struct PlayerInventoryWindowNativeInputs12004 {
  void* context=nullptr;
  bool (*read_admission)(void*,ck3_12004::artifact_personal_use::Frame&,
                         bool& active_event,bool& pending_interaction) noexcept=nullptr;
  bool (*claim_once)(void*,std::uint64_t,
                    const ck3_12004::PlayerInventoryOpenPost12004&) noexcept=nullptr;
  std::uint64_t owner_mailbox_sequence=0;
  bool open_enabled=false,loaded_gui_sources_verified=false;
  // Provider-owned fixed close/close-post mode; never a caller RVA or callback.
  bool close_enabled=false;
};
struct PlayerInventoryWindowNativeResult12004 {
  ck3_12004::PlayerInventoryOpenPost12004 before{};
  bool code_pins_verified=false,once_consumed=false,invoked=false,call_returned=false,
       needs_recovery=false;
  std::string status="inventory_open_private_disabled";
};
bool ReadPlayerInventoryWindowNative12004(const ZhongguoScoreboardNativeEnvironmentV1&,
    const PlayerInventoryWindowNativeInputs12004&,
    ck3_12004::PlayerInventoryOpenPost12004& out,bool& code_pins_verified,
    std::string& reason) noexcept;
PlayerInventoryWindowNativeResult12004 OpenPlayerInventoryWindowNative12004(
    const ZhongguoScoreboardNativeEnvironmentV1&,
    const PlayerInventoryWindowNativeInputs12004&) noexcept;
PlayerInventoryWindowNativeResult12004 ClosePlayerInventoryWindowNative12004(
    const ZhongguoScoreboardNativeEnvironmentV1&,
    const PlayerInventoryWindowNativeInputs12004&) noexcept;
}
