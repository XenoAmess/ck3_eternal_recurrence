#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include <array>
#include <string>
#include <string_view>
namespace xar::ck3_11906 {
inline constexpr std::string_view kWhiteRenderedTextV1Step="query-white-rendered-text-v1";
inline constexpr std::string_view kWhiteRenderedTextV1Capability="game.command.query-white-rendered-text-v1";
inline constexpr std::array<std::string_view,9> kWhiteRenderedTextNamesV1{{
  "ervc_cc_age_value_text","ervc_cc_diplomacy_value_text","ervc_cc_martial_value_text",
  "ervc_cc_stewardship_value_text","ervc_cc_intrigue_value_text","ervc_cc_learning_value_text",
  "ervc_cc_prowess_value_text","ervc_cc_price_value_text","ervc_cc_gold_value_text"}};
struct WhiteRenderedTextFieldV1 {
  std::string child_path,text_utf8;
  bool effective_visible=false,enabled=false;
  friend bool operator==(const WhiteRenderedTextFieldV1 &,const WhiteRenderedTextFieldV1 &)=default;
};
struct WhiteRenderedTextResultV1 {
  bool available=false,owner_thread_verified=false,source_abi_pins_verified=false;
  bool frame_verified=false,gui_owner_binding_verified=false,tree_complete=false;
  bool inner_modal_visible=false,stable_two_pass_text=false;
  std::uint32_t game_pid=0;
  std::uint64_t native_revision=0,connection_generation=0;
  std::int32_t played_character_id=-1,date_raw=0;
  std::size_t widget_count=0;
  std::array<WhiteRenderedTextFieldV1,9> fields{};
  std::string unavailable_reason;
};
struct WhiteRenderedTextContextV1 {
  const game::GameAdapter *game=nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision=0,connection_generation=0;
  WhiteRenderedTextResultV1 result{};
};
// Only fixed White widget values. No arbitrary name/path/pointer or callback.
// No variable projection, computed price or button.down observation.
bool ExecuteWhiteRenderedTextV1(WhiteRenderedTextContextV1 &,MainThreadQueryMailboxV1 &,
    const MainThreadExecutionStampV1 &,const ZhongguoScoreboardNativeEnvironmentV1 &) noexcept;
std::string SerializeWhiteRenderedTextV1(const WhiteRenderedTextResultV1 &);
}
